from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

async def filters_to_search_prompt(filters: dict, providers: list) -> tuple[str, list]:
    """
    Translates structured filter dictionary into a prompt string
    and performs a SQL query to pre-filter rows.

    Returns:
        - a structured prompt string
        - a list of filtered rows from SQL
    """
    parts = []

    # Construct provider list
    exclude = set(filters.get("exclude_providers", []))
    preferred = filters.get("preferred_providers", [])
    tolerance = 0.2
    target_price = filters.get("target_price")
    target_data = filters.get("target_data")
    target_providers = [p for p in providers if p not in exclude]
    target_providers += preferred * 2  # Weight preferred ones more

    parts.append(f"provider: {', '.join(target_providers)}")

    if min_data := filters.get("min_data_gb"):
        parts.append(f"min_data_gb: {min_data}")

    if filters.get("wants_roaming"):
        parts.append("roaming: true")

    if filters.get("byod"):
        parts.append("byod: true")
    
    if filters.get("target_price"):
        parts.append(f"target_price: {filters['target_price']}")

    if intent := filters.get("intent"):
        parts.append(f"intent: {intent}")

    # SQL filtering
    base_sql = """
        SELECT *
        FROM phone_plans_db
        WHERE 1=1
    """
    params = {}

    if target_price:
        max_price = target_price * (1 + tolerance)
        base_sql += " AND promotion_price <= :max_price"
        params["max_price"] = max_price
        #min_price = target_price * (1 - tolerance)
        #base_sql += " AND promotion_price >= :min_price"
        #params["min_price"] = min_price

    if target_data:
        min_data = target_data * (1 - tolerance)
        base_sql += " AND data >= :min_data"
        params["min_data"] = min_data
        #max_data = target_data * (1 + tolerance)
        #base_sql += " AND data <= :max_data"
        #params["max_data"] = max_data


    if exclude:
        placeholders = ", ".join([f":p{i}" for i in range(len(exclude))])
        base_sql += f" AND provider NOT IN ({placeholders})"
        for i, p in enumerate(exclude):
            params[f"p{i}"] = p.lower()
    
    if target_price:
        min_price = target_price * (1 - tolerance)
        max_price = target_price * (1 + tolerance)

    base_sql += " LIMIT 20"

    return " ".join(parts), base_sql.strip(), params
