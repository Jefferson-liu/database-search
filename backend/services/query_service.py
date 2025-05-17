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
from backend.prompts.prompt_registry import get_prompt

load_dotenv()

client = OpenAI()
embedding_model = os.getenv("EMBEDDING_MODEL")
gpt_model = os.getenv("GPT_MODEL")
model = SentenceTransformer(embedding_model)  # same model as used in embedding

async def filter_model(request: QueryRequest, providers: list):
    try:
        prompt = get_prompt("query_filter", user_input=request.question, providers=", ".join(providers))
        
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
        prompt = get_prompt("recommend_plans_response", k=request.k, context=context, question=request.question)

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