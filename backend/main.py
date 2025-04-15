from fastapi import FastAPI
from backend.api import csv_routes
import os

from backend.db.base import Base
from backend.models.csv_row import CsvRow
from backend.db.session import engine


if os.getenv("ENV") == "dev":
    # Drop all tables in dev mode for testing purposes
    print("Dropping all tables...")
    # WARNING: This will drop all tables in the database, use with caution!
    Base.metadata.drop_all(bind=engine)    # DANGER: Drops all tables
    Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(csv_routes.router, prefix="/api")