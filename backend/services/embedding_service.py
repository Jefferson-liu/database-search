import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.db.session import SessionLocal
from backend.models.csv_row import CsvRow

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def row_to_text(row):
    return (
        f"产品名称/Product: {row.item_name or ''}，"
        f"供应商/Provider: {row.provider or ''}，"
        f"条件/Condition: {row.condition or ''}，"
        f"渠道/Channel: {row.channel or ''}，"
        f"促销期/Promo: {row.promo_start_date} 至 {row.promo_end_date}，"
        f"促销价/Price: {row.promotion_price or ''}"
    )

def build_index():
    db = SessionLocal()
    rows = db.query(CsvRow).all()
    texts = [row_to_text(row) for row in rows]
    embeddings = model.encode(texts, convert_to_numpy=True)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    id_map = {i: row.id for i, row in enumerate(rows)}
    return index, id_map

# One-time build at module load
index, id_map = build_index()

def search(query, top_k=5):
    query_vec = model.encode([query], convert_to_numpy=True)
    D, I = index.search(query_vec, top_k)

    db = SessionLocal()
    result_rows = [db.query(CsvRow).get(id_map[i]) for i in I[0]]
    return result_rows
