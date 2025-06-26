from openai import OpenAI
import os
import json
from fastapi import HTTPException
from sqlalchemy import select, and_, bindparam
from backend.models.csv_row import CsvRow
from backend.schemas.user_requirements import UserRequirements
from typing import Optional
from backend.utils.search_query_utils import generate_followup_question, merge_requirements
from backend.prompts.prompt_registry import get_prompt
from backend.utils.text_formatter import row_to_dict
from backend.schemas.search_results import SearchResults, PlanInfo


client = OpenAI()
gpt_model = os.getenv("GPT_MODEL")

async def get_matching_plans(db, req, k=10) -> list[PlanInfo]:
    conditions = []
    params = {}

    if req.target_price:
        conditions.append(CsvRow.promotion_price <= bindparam("max_price"))
        params["max_price"] = req.target_price * 1.1  # slight tolerance

    if req.target_data:
        conditions.append(CsvRow.data >= bindparam("min_data"))
        params["min_data"] = req.target_data * 0.9  # slight tolerance

    if req.current_provider:
        conditions.append(CsvRow.provider != bindparam("exclude_provider"))
        params["exclude_provider"] = req.current_provider.lower()

    if req.roaming:
        conditions.append(CsvRow.roaming.op("@>")(bindparam("roaming")))
        params["roaming"] = [r.lower() for r in req.roaming]

    if req.byod is True:
        conditions.append(CsvRow.byod_or_term == True)

    stmt = select(CsvRow).where(and_(*conditions)).limit(k)
    result = await db.execute(stmt.params(**params))
    rows = result.scalars().all()
    print(f"rows: {rows}")
    print([row_to_dict(r) for r in rows])
    plans = [PlanInfo(**row_to_dict(r)) for r in rows]
    if not plans:
        raise HTTPException(status_code=404, detail="No matching plans found.")
    return plans


async def extract_user_requirements(user_input: str) -> dict:
    prompt = get_prompt("extract_user_requirements", user_input=user_input)

    response = client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    raw = response.choices[0].message.content
    print("LLM extraction output:", raw)

    try:
        parsed = json.loads(raw)
        print("Parsed extraction:", parsed)
        return parsed
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"GPT returned invalid JSON: {e}")

async def get_search_results(db, user_input: str, requirements: UserRequirements, k: int = 10):
    # Fetch matching plans
    if not requirements.is_valid():
        return []
    else:
        try:
            matching_plans = await get_matching_plans(db, requirements, k)
        except HTTPException as e:
            # Fallback: try relaxing requirements in order: price, then data, then provider
            relax_fields_order = [
                ["target_price"],
                ["target_data"],
                ["current_provider"],
                ["target_price", "target_data"],
                ["target_price", "current_provider"],
                ["target_data", "current_provider"],
                ["target_price", "target_data", "current_provider"]
            ]
            fallback_found = False
            relaxed_fields = None
            for fields in relax_fields_order:
                relaxed_req = requirements.model_copy()
                for field in fields:
                    setattr(relaxed_req, field, None)
                if relaxed_req.is_valid():
                    try:
                        matching_plans = await get_matching_plans(db, relaxed_req, k)
                        fallback_found = True
                        relaxed_fields = fields
                        break
                    except HTTPException:
                        continue
            if not fallback_found:
                print("[ERROR] Failed in get_matching_plans (even after relaxing):", e)
                raise e
            else:
                missing_fields = requirements.get_missing_fields()
                print("Missing fields (fallback):", missing_fields)
                followup_question = f"No exact matches found. We relaxed the following requirement(s) to find similar plans: {', '.join(relaxed_fields)}."
                followup_question += " " + await generate_followup_question(missing_fields)
                results = SearchResults(
                    plans=matching_plans,
                    followup=followup_question
                )
                return results

    followup_question = None
    # Check for missing fields
    missing_fields = requirements.get_missing_fields()
    print("Missing fields:", missing_fields)
    if missing_fields:
        try:
            followup_question = await generate_followup_question(missing_fields)
        except HTTPException as e:
            raise e
    results = SearchResults(
        plans=matching_plans,
        followup=followup_question
    )
    return results