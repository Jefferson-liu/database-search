from fastapi import APIRouter
from backend.services.embedding_service import search, row_to_text
import openai
import os

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_gpt_answer(query, context_texts):
    prompt = f"""You are a helpful assistant. Use the following context to answer the question.

Context:
{context_texts}

Question:
{query}

Answer:"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

@router.get("/ask")
def ask_gpt(query: str):
    rows = search(query)
    context = "\n".join([row_to_text(r) for r in rows])
    answer = get_gpt_answer(query, context)
    return {"answer": answer}
