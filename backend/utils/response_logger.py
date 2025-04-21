from openai import OpenAI
import uuid

client = OpenAI()

async def log_to_openai_responses(user_question, filtered_sql, filtered_context, gpt_response, user_id="anonymous"):
    try:
        # Construct full message chain (must match what you sent to GPT)
        messages = [
            {"role": "system", "content": "You are a helpful business assistant..."},
            {"role": "user", "content": f"""
            SQL: {filtered_sql}
            Context: {filtered_context}
            Question: {user_question}
            """}
        ]

        # Submit to Responses API
        response_log = client.responses.create(
            run_id=str(uuid.uuid4()),  # unique identifier per query
            messages=messages,
            response={"role": "assistant", "content": gpt_response},
            metadata={
                "user_id": user_id,
                "intent": "phone_plan_recommendation",
                "filters_used": str(filtered_sql)[:100]  # truncate if needed
            }
        )
        return response_log
    except Exception as e:
        print(f"❌ Failed to log to Responses API: {e}")
