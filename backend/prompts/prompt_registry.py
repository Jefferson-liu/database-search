# backend/prompts/prompt_registry.py

PROMPTS = {
    "extract_user_requirements": """
You are a smart assistant helping a salesperson understand customer requirements for a phone plan. Extract the following fields from the text below and return them as a JSON object. If a field is not mentioned, omit it entirely.

Fields:
- current_provider (string)
- target_price (number)
- target_data (number, in GB)
- roaming (list of country names, lowercased)
- byod (true if 'bring your own device' or 'no contract' is mentioned)
- min_data_gb (number, if any minimum data is implied)

Example:
User: The customer is using Rogers and pays $45 for 20GB. They need roaming in China and the U.S.

Output:
{{
  "current_provider": "rogers",
  "target_price": 45,
  "target_data": 20,
  "byod": true,
  "roaming": ["china", "united states"]
}}

Now process this:

User: {user_input}
""",
    "clarify_missing": """
You're an assistant helping a salesperson gather missing information from a customer before suggesting a phone plan.

Based on the fields missing, generate a friendly and clear follow-up question that asks for the following: {fields}.

The tone should be helpful and concise. Do not assume anything. Only ask for the missing fields.

Examples:
Missing fields: target_price → "What is the customer's preferred price range?"
Missing fields: target_price, target_data → "What is the customer's preferred price and how much data do they need?"

Now generate the follow-up question:
Missing fields: {fields}
""",
    "query_filter": """
You are an intelligent assistant that extracts structured filters from customer questions about phone plans.
If the customer provides an example phone plan and mentions finding a similar plan, take the target data and price from that plan.
Extract the following fields as a JSON object:
- `preferred_providers`: list of providers the customer wants (if mentioned)
- `exclude_providers`: list of providers the customer currently uses or dislikes
- `roaming`: list of full names of countries the customer wants to roam in, this means vacationing or business or any forms of roaming (if mentioned)
- `byod`: true if they mention "bring your own device" or "no contract"
- `target_price`: the price that the customer is looking for (if mentioned), this can ONLY be an integer or float, do not include the dollar sign or any other characters or descriptors like "cheapest"
- `target_data`: the data that the customer is looking for, convert the value to GB (if mentioned) this can ONLY be an integer or float, do not include the dollar sign or any other characters or descriptors like "cheapest" or "expensive"

If the provider names are misspelled, correct them to the closest match from the list of providers:
{providers}

Omit fields that are not specified. Output only a **valid JSON object**.
---

**Example 1**

User: I am using bell and I am going on a trip to Las Vegas and then beijing. I want at 100GB of data

Assistant:
{{
  "exclude_providers": ["Bell"],
  "roaming": ["united states", "china"]
}}

**Example 2**

User: I am using a Rogers plan with 10GB of data and $50 a month. I want to find a plan with similar data and price.

Assistant:
{{
  "exclude_providers": ["Rogers"],
  "target_price": 50,
  "target_data": 10
}}

**Example 3**

User: I am buying my friend a phone plan for their birthday. They are going to come to Canada for a month and I want to get them a plan with 20GB of data.

Assistant:
{{
  "target_data": 20,
  "roaming": ["canada"]
}}

**Example 4**

User: I am using Bell give me the cheapest plans

Assistant:
{{
  "exclude_providers": ["Bell"]
}}

**Example 5**

User: I am using Rogers give me the cheapest plans

Assistant:
{{
  "exclude_providers": ["Rogers"]
}}

Now extract filters from this user request:
User: {user_input}
""",
    "recommend_plans_response": """
Use the following data to answer the user's question.
You must return **exactly {k} plans** from the list below. Use this strict logic:

If the user says that they are currently using a provider, exclude all plans from that provider before any filtering is done.

Then apply the following ranking logic:
1. If fewer than 3 valid plans are found, list all and state clearly: "Only X plans met the criteria."
2. If more than 3 valid plans are found, choose the 3 with:
    - Lowest promotion price first
    - Then highest data
    - Then most countries in the roaming list
3. Each plan must be **clearly listed**, and followed by 2-3 point-form reasons the user would like it.
4. Do NOT skip any matching plans. Do NOT combine similar plans. Do NOT hallucinate.

- If the user says that they are currently using a provider, ignore and do not let it influence your answer besides filtering the plans out.

---
Phone Plans:
{context}

Question:
{question}

Now generate your response following your previously given logic:
"""
}


def get_prompt(name: str, **kwargs) -> str:
    try:
        raw = PROMPTS[name]
        return raw.format(**kwargs)
    except KeyError:
        raise ValueError(f"Prompt '{name}' not found.")
    except KeyError as e:
        raise ValueError(f"Missing placeholder {str(e)} in prompt '{name}'.")
