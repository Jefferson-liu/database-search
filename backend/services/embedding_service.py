import faiss
import numpy as np
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from backend.db.session import AsyncSessionLocal
from backend.models.csv_row import CsvRow
from fastapi.concurrency import run_in_threadpool
from backend.utils.text_formatter import row_to_text_orm_weighted

load_dotenv()
embedding_model = os.getenv("EMBEDDING_MODEL")

model = SentenceTransformer(embedding_model)

async def update_embeddings(db: AsyncSession, batch_size=500):
    offset = 0
    total_updated = 0

    while True:
        result = await db.execute(
            select(CsvRow)
            .where(CsvRow.embedding == None)
            .offset(offset)
            .limit(batch_size)
        )
        rows = result.scalars().all()

        if not rows:
            break

        weighted_texts = [row_to_text_orm_weighted(r) for r in rows]

        # Run in threadpool to avoid blocking event loop
        embeddings = await run_in_threadpool(model.encode, weighted_texts)

        for row, emb in zip(rows, embeddings):
            row.embedding = emb.tolist()

        await db.commit()
        total_updated += len(rows)
        offset += batch_size

    return total_updated


#NOT USED YET
def search(query, top_k=5):
    index = faiss.read_index("faiss_store/phone_index.faiss")
    with open("faiss_store/id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)
        id_map = {int(k): v for k, v in id_map.items()}

    query_vec = model.encode([query], convert_to_numpy=True)
    D, I = index.search(query_vec, top_k)

    db = AsyncSessionLocal()
    return [db.query(CsvRow).get(id_map[i]) for i in I[0]]
