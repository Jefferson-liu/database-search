from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import textwrap
import json
from backend.models.csv_row import CsvRow
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
router = APIRouter()
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
            - `roaming`: list of countries the customer wants to roam in, this means vacationing or business or any forms of roaming (if mentioned)
            - `byod`: true if they mention "bring your own device" or "no contract"
            - `target_price`: the price that the customer is looking for (if mentioned)
            - `target_data`: the data that the customer is looking for, convert the value to GB (if mentioned)
            
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
            "roaming": USA,
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
            "roaming": ["Canada"],
            }

            Now extract filters from this user request:
        """ + "User: " + request.question)
        
        response = client.chat.completions.create(
            model=gpt_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        string_response = response.choices[0].message.content
        try:
            filters = json.loads(string_response)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Filter failed: Invalid JSON from model - {e}")
        return filters  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter failed: {e}")
    



async def query_model(db: AsyncSession, request: QueryRequest, k: int = 5):
    try:
        providers = await get_unique_providers(db)
        providers = providers["providers"]
        filter_model_response = await filter_model(request, providers)
        filtered_query, filtered_sql, params = await filters_to_search_prompt(filter_model_response, providers)
        query_embedding = model.encode([filtered_query])[0].tolist()
        vector_string = f"[{', '.join(str(x) for x in query_embedding)}]"
        sql = text(f"""
            WITH filtered AS (
                   {filtered_sql}  
            )
            SELECT *
            FROM phone_plans_db
            ORDER BY embedding <-> :embedding
            LIMIT :k
        """).columns(*CsvRow.__table__.columns)
        result = await db.execute(sql, {"embedding": vector_string, "k": k, **params})
        rows = result.mappings().all()

        if not rows:
            raise HTTPException(status_code=404, detail="No results found.")
        context = "\n".join([row_to_text_dict(r) for r in rows])
        columns = "|".join([col.name for col in CsvRow.__table__.columns])

        # I use dedent here to just remove the indents from the prompt but keep the new lines
        # This is just for readability for developers, but the indentation can only complicate the model so I remove it
        prompt = textwrap.dedent(f"""
            Use the following phone plan data to answer the user's question.
            Provide 2 or 3 point form reasons why the customer would like the recommended plans with priority to things listed in the question.
            Do not include any other information unless asked in the prompt.
            Use the data to find the top {request.k} phone plans for the user.
            Do not hallucinate or make up any information. Only use and return the data provided 
            Notes:
            - The roaming column denotes that the countries in that column have free roaming.
            - The byod column denotes that the plan is a "bring your own device" plan.
            - Assume the user is in Canada so overseas means outside of Canada.
            Each row is a phone plan with fields in this order:
            {columns}

            Phone Plans:
            {columns}
            {context}

            Question:
            {request.question}

            Answer:
        """)

        # Example with OpenAI
        response = client.chat.completions.create(
            model=gpt_model,
            messages=[{"role": "system", "content": "You are a helpful business assistant. Do not answer anything unless it can be backed up with retrieved knowledge or structured data. If unsure, say 'I don’t know based on the available data.' Do not make assumptions, do not hallucinate."},
                      {"role": "user", "content": prompt}],
            temperature=0.3,
        )

        answer = response.choices[0].message.content
        return {"answer": answer, "filtered_model": filter_model_response, "filtered_sql": filtered_sql, context: context, "prompt": prompt}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")
