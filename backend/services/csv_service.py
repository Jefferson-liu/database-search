import pandas as pd
import io
from fastapi import UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
from backend.models.csv_row import CsvRow
import re

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

async def store_csv_to_db(file: UploadFile, db: Session):
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode()))

    # Rename CSV headers to match model field names
    df.rename(columns=COLUMN_MAP, inplace=True)

    records = df.to_dict(orient="records")
    saved = 0

    for record in records:
        record = clean_nulls(record)

        # Parse dates
        record["promo_start_date"] = parse_date(record.get("promo_start_date") or "")
        record["promo_end_date"] = parse_date(record.get("promo_end_date") or "")

        # Clean prices
        record["promotion_price"] = clean_price(record.get("promotion_price"))
        record["original_price"] = clean_price(record.get("original_price"))
        record["activation_fee"] = clean_price(record.get("activation_fee"))
        record["overage_rate"] = parse_overage_rate(record.get("overage_rate"))

        try:
            row = CsvRow(**record)
            db.add(row)
            saved += 1
        except Exception as e:
            print(f"❌ Error inserting record: {record}")
            print(f"➡️ {e}")

    db.commit()
    return saved
