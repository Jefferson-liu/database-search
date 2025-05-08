from openai import OpenAI
import uuid

client = OpenAI()

async def log_response(messages, filters, gpt_response, user_id="anonymous"):
    try:
        # Submit to Responses API
        response_log = client.responses.create(
            run_id=str(uuid.uuid4()),  # unique identifier per query
            messages=messages,
            metadata={
                "user_id": user_id,
                "intent": "phone_plan_recommendation",
                "filters_used": str(filters)[:100]  # truncate if needed
            }
        )
        return response_log
    except Exception as e:
        print(f"❌ Failed to log to Responses API: {e}")
