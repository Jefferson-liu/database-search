from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import select, bindparam
from pgvector.sqlalchemy import Vector
import textwrap
import json
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
import os
from backend.schemas.query import QueryRequest
from backend.utils.text_formatter import row_to_text_dict
from backend.utils.query_filter import filters_to_search_prompt
from backend.services.provider_name_service import get_unique_providers

load_dotenv()

client = OpenAI()
embedding_model = os.getenv("EMBEDDING_MODEL")
gpt_model = os.getenv("GPT_MODEL")
model = SentenceTransformer(embedding_model)  # same model as used in embedding

async def filter_model(request: QueryRequest, providers: list):
    try:
        prompt = textwrap.dedent(f"""
            You are an intelligent assistant that extracts structured filters from customer questions about phone plans.
            If the customer provides an example phone plan and mentions finding a similar plan, take the target data and price from that plan.
            Extract the following fields as a JSON object:
            - `preferred_providers`: list of providers the customer wants (if mentioned)
            - `exclude_providers`: list of providers the customer currently uses or dislikes
            - `roaming`: list of full names of countries the customer wants to roam in, this means vacationing or business or any forms of roaming (if mentioned)
            - `byod`: true if they mention "bring your own device" or "no contract"
            - `target_price`: the price that the customer is looking for (if mentioned), this can ONLY be an integer or float, do not include the dollar sign or any other characters or descriptors like "cheapest"
            - `target_data`: the data that the customer is looking for, convert the value to GB (if mentioned) this can ONLY be an integer or float, do not include the dollar sign or any other characters or descriptors like "cheapest" or "expensive"
            
            If the provider names are mispelled, correct them to the closest match from the list of providers:
            {providers}
            """
            +

            """

            Omit fields that are not specified. Output only a **valid JSON object**.
            ---

            **Example 1**

            User: I am using bell and I am going on a trip to Las Vegas and then beijing. I want at 100GB of data

            Assistant:
            {
            "exclude_providers": ["Bell"],
            "roaming": ["united states", "china"]
            }

            **Example 2**

            User: I am using a Rogers plan with 10GB of data and $50 a month. I want to find a plan with similar data and price.

            Assistant:
            {
            "exclude_providers": ["Rogers"],
            "target_price": 50,
            "target_data": 10,
            }

            **Example 3**

            User: I am buying my friend a phone plan for their birthday. They are going to come to Canada for a month and I want to get them a plan with 20GB of data.

            Assistant:
            {
            "target_data": 20,
            "roaming": ["canada"],
            }

            **Example 4**

            User: I am using Bell give me the cheapest plans

            Assistant:
            {
            "exclude_providers": ["Bell"],
            }

            **Example 5**

            User: I am using Rogers give me the cheapest plans

            Assistant:
            {
            "exclude_providers": ["Rogers"],
            }

            Now extract filters from this user request:
        """ + "User: " + request.question)
        
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model=gpt_model,
            messages= messages,
            temperature=0.2,
            store=True,
        )
        string_response = response.choices[0].message.content

        #await log_response(messages = messages, user_id = request.user_id)
        try:
            filters = json.loads(string_response)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Filter failed: Invalid JSON from model - {e}")
        return filters  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter failed: {e}")
    



async def query_model(db: AsyncSession, request: QueryRequest, k: int = 5, message_history: list = None):
    try:
        providers = (await get_unique_providers(db))["providers"]
        print("Providers: ", providers)
        filter_model_response = await filter_model(request, providers)
        print(filter_model_response)

        # Generate prompt and Core filter subquery
        filtered_prompt, filtered_stmt, filtered_params = filters_to_search_prompt(filter_model_response, providers)
        print("Filtered Prompt: ", filtered_prompt)
        print("Filtered SQL: ", str(filtered_stmt))

        # Vector embedding
        query_embedding = model.encode([filtered_prompt])[0].tolist()

        filtered_subquery = filtered_stmt.subquery("filtered")
        order_expr = filtered_subquery.c.embedding.op("<->")(bindparam("embedding", type_=Vector(384)))
        final_stmt = (
            select(filtered_subquery)
            .order_by(order_expr)
            .limit(bindparam("k"))
        )

        result = await db.execute(final_stmt, {
            **filtered_params,
            "embedding": query_embedding,
            "k": k
        })
        rows = result.mappings().all()

        if not rows:
            raise HTTPException(status_code=404, detail="No results found.")
        context = "\n".join([row_to_text_dict(r) for r in rows])

        # I use dedent here to just remove the indents from the prompt but keep the new lines
        # This is just for readability for developers, but the indentation can only complicate the model so I remove it
        prompt = textwrap.dedent(f"""
            Use the following data to answer the user's question.
            You must return **exactly {request.k} plans** from the list below. Use this strict logic:
            If the user says that they are currently using a provider, exclude all plans from that provider before any filtering is done.
            Then apply the following ranking logic:
            1. If fewer than 3 valid plans are found, list all and state clearly: "Only X plans met the criteria."
            2. If more than 3 valid plans are found, choose the 3 with:
                - Lowest promotion price first
                - Then highest data
                - Then most countries in the roaming list
            3. Each plan must be **clearly listed**, and followed by 2-3 point-form reasons the user would like it.
            4. Do NOT skip any matching plans. Do NOT combine similar plans. Do NOT hallucinate.

            - If the user says that they are currently using a provider, ignore and do not let it influence your answer besides filtering the plans out

            ---
            Phone Plans:
            {context}

            Question:
            {request.question}

            Answer:
        """)

        if not message_history:
            messages = [{"role": "system", "content": "You are a helpful business assistant. Do not answer anything unless it can be backed up with retrieved knowledge or structured data. If unsure, say 'I don't know based on the available data.' Do not make assumptions, do not hallucinate. Respond in the language you are asked in"},
                        {"role": "user", "content": prompt}]
        else:
            cleaned_history = [{"role": m["role"], "content": m["content"]} for m in message_history if m["content"]]
            messages = [{"role": "system", "content": "You are a helpful business assistant. Do not answer anything unless it can be backed up with retrieved knowledge or structured data. If unsure, say 'I don't know based on the available data.' Do not make assumptions, do not hallucinate."},
                        *cleaned_history,
                        {"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            temperature=0.3,
            store=True,
        )

        answer = response.choices[0].message.content
        messages.append({"role": "assistant", "content": answer})
        #await log_response(request.question, prompt, answer, request.user_id)
        #print(str(final_stmt), str(filtered_subquery), filtered_params)
        return {"answer": answer, "filtered_model": filter_model_response, "filtered_sql": str(filtered_subquery), "context": context, "prompt": prompt, "messages": messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

async def search_query_model(db: AsyncSession, request: QueryRequest, k: int = 5, requirements: list = None):
    try:
        providers = (await get_unique_providers(db))["providers"]
        filter_model_response = await filter_model(request, providers)
        #the model needs to have a minimum amount of information to work with, so we check if the user has provided any filters
        
        # Generate prompt and Core filter subquery
        filtered_prompt, filtered_stmt, filtered_params = filters_to_search_prompt(filter_model_response, providers)

        # Vector embedding
        query_embedding = model.encode([filtered_prompt])[0].tolist()

        filtered_subquery = filtered_stmt.subquery("filtered")
        order_expr = filtered_subquery.c.embedding.op("<->")(bindparam("embedding", type_=Vector(384)))
        final_stmt = (
            select(filtered_subquery)
            .order_by(order_expr)
            .limit(bindparam("k"))
        )

        result = await db.execute(final_stmt, {
            **filtered_params,
            "embedding": query_embedding,
            "k": k
        })
        rows = result.mappings().all()

        if not rows:
            raise HTTPException(status_code=404, detail="No results found.")
        results = "\n".join([row_to_text_dict(r) for r in rows])

    
        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")