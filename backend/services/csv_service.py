import pandas as pd
import io
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from backend.models.csv_row import CsvRow
import re
from backend.services.embedding_service import update_embeddings
from sqlalchemy import text

# Header mapping from CSV → DB model
COLUMN_MAP = {
    "Timestamp": "timestamp",
    "Item Name": "item_name",
    "Provider": "provider",
    "Prom start Date": "promo_start_date",
    "Prom Ending Date": "promo_end_date",
    "Channel": "channel",
    "Region": "region",
    "Condition": "condition",
    "Line type": "line_type",
    "Promotion Price": "promotion_price",
    "Data": "data",
    "GB": "gb",
    "Original Price": "original_price",
    "Rate after overage": "overage_rate",
    "Roaming": "roaming",
    "BYOD or Term": "byod_or_term",
    "Free LD": "free_ld",
    "Activation Fee": "activation_fee",
    "Code": "code",
    "Tier": "tier"
}


def parse_overage_rate(value):
    if value:
        value = re.sub(r"[^\d]", "", value)
        return float(value) if value else 0.0
    return 0.0

def parse_date(value):
    try:
        return datetime.strptime(value.strip(), "%m/%d/%Y").date()
    except Exception:
        return None


def clean_price(value):
    if isinstance(value, str):
        value = value.strip().replace("$", "").replace(",", "")
        try:
            return float(value)
        except ValueError:
            return None
    return value if pd.notna(value) else None


def clean_nulls(record: dict) -> dict:
    for k, v in record.items():
        if isinstance(v, str) and not v.strip():
            record[k] = None
        elif pd.isna(v):
            record[k] = None
    return record

def parse_data(data, gb):
    if data and gb.lower() == 'mb':
        return data * 0.001
    elif data and gb.lower() == 'gb':
        return data
    return None


async def store_csv_to_db(file: UploadFile, db: AsyncSession) -> str:
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode()), keep_default_na=True, na_values=[""])
        df.fillna(value=pd.NA, inplace=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {e}")

    # Rename columns to match DB fields
    df.rename(columns=COLUMN_MAP, inplace=True)
    records = df.to_dict(orient="records")

    try:

        await db.execute(text("DELETE FROM phone_plans_db"))
        saved = 0
        for record in records:
            record = clean_nulls(record)
            record["promo_start_date"] = parse_date(record.get("promo_start_date") or "")
            record["promo_end_date"] = parse_date(record.get("promo_end_date") or "")
            record["promotion_price"] = clean_price(record.get("promotion_price"))
            record["original_price"] = clean_price(record.get("original_price"))
            record["activation_fee"] = clean_price(record.get("activation_fee"))
            record["overage_rate"] = parse_overage_rate(record.get("overage_rate"))
            record["data"] = parse_data(record.get("data"), record.get("gb", ""))
            record.pop("gb", None)
            row = CsvRow(**record)
            db.add(row)
            saved += 1

        await update_embeddings(db)

        await db.commit()
        return f"✅ {saved} rows saved and embedded."

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"CSV upload failed. Rolled back. Reason: {e}")
