from openai import OpenAI
import os
from backend.schemas.user_requirements import UserRequirements
from backend.prompts.prompt_registry import get_prompt

client = OpenAI()
gpt_model = os.getenv("GPT_MODEL")

def merge_requirements(existing: UserRequirements, new: dict) -> UserRequirements:
    existing = UserRequirements(**new)
    return existing


async def generate_followup_question(missing_fields: list[str]) -> str:
    prompt = get_prompt("clarify_missing", fields=", ".join(missing_fields))

    response = client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()