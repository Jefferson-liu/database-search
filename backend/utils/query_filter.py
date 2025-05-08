from sqlalchemy import select, and_, bindparam
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
from backend.models.csv_row import CsvRow


def filters_to_search_prompt(filters: dict, providers: list):
    parts = []
    exclude = set(filters.get("exclude_providers", []))
    preferred = filters.get("preferred_providers", [])
    tolerance = 0.2
    target_price = filters.get("target_price")
    target_data = filters.get("target_data")
    roaming = filters.get("roaming")
    target_providers = [p for p in providers if p not in exclude]
    if target_providers:
        target_providers += preferred * 2  # soft weight

    parts.append(f"provider: {', '.join(target_providers)}")
    if filters.get("min_data_gb"):
        parts.append(f"min_data_gb: {filters['min_data_gb']}")
    if roaming:
        parts.append("roaming: " + ", ".join(roaming))
    if filters.get("byod"):
        parts.append("byod: true")
    if target_price:
        parts.append(f"target_price: {target_price}")
    if intent := filters.get("intent"):
        parts.append(f"intent: {intent}")

    # Build WHERE clause
    conditions = []

    if target_price:
        conditions.append(CsvRow.promotion_price <= bindparam("max_price"))
    if target_data:
        conditions.append(CsvRow.data >= bindparam("min_data"))
    if exclude:
        conditions.append(CsvRow.provider.not_in([bindparam(f"p{i}") for i in range(len(exclude))]))
    if roaming:
        conditions.append(CsvRow.roaming.op("@>")(bindparam("roaming", type_=ARRAY(VARCHAR))))

    stmt = select(CsvRow).where(and_(*conditions)).limit(20)

    # Params
    params = {}
    if target_price:
        params["max_price"] = target_price * (1 + tolerance)
    if target_data:
        params["min_data"] = target_data * (1 - tolerance)
    if exclude:
        for i, p in enumerate(exclude):
            params[f"p{i}"] = p.lower()
    if roaming:
        params["roaming"] = [r.lower() for r in roaming]

    return " ".join(parts), stmt, params
