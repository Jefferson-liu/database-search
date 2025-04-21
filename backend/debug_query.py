import asyncio
from backend.db.session import AsyncSessionLocal
from backend.models.csv_row import CsvRow
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from backend.utils.text_formatter import row_to_text_dict
import os
load_dotenv()

embedding_model = os.getenv("EMBEDDING_MODEL")

model = SentenceTransformer(embedding_model)

def row_to_text(row):
    return (
        f"Item: {row['item_name'] or ''}, "
        f"Provider: {row['provider'] or ''}, "
        f"Region: {row['region'] or ''}, "
        f"Condition: {row['condition'] or ''}, "
        f"Channel: {row['channel'] or ''}, "
        f"Line Type: {row['line_type'] or ''}, "
        f"Promotion Price: {row['promotion_price'] or ''}, "
        f"Original Price: {row['original_price'] or ''}, "
        f"Overage Rate: {row['overage_rate'] or ''}, "
        f"Data: {row['data'] or ''}, "
        f"GB: {row['gb'] or ''}, "
        f"Roaming: {row['roaming'] or ''}, "
        f"BYOD/Term: {row['byod_or_term'] or ''}, "
        f"Free LD: {row['free_ld'] or ''}, "
        f"Activation Fee: {row['activation_fee'] or ''}, "
        f"Promo start: {row['promo_start_date'] or ''}, "
        f"Promo end: {row['promo_end_date'] or ''}, "
        f"Code: {row['code'] or ''}, "
        f"Tier: {row['tier'] or ''}"
    )

async def test_query():
    async with AsyncSessionLocal() as db:
        query = "cheap unlimited data plan"
        embedding = model.encode([query])[0].tolist()
        vector_string = f"[{', '.join(str(x) for x in embedding)}]"

        sql = text("""
            SELECT * FROM phone_plans_db
            ORDER BY embedding <-> :embedding
            LIMIT :k
        """).columns(*CsvRow.__table__.columns)

        result = await db.execute(sql, {"embedding": vector_string, "k": 3})
        rows = result.mappings().all()

        for row in rows:
            print(row_to_text_dict(row))

asyncio.run(test_query())
