from fastapi import FastAPI
from backend.api import csv_routes

from backend.db.base import Base
from backend.models.csv_row import CsvRow
from backend.db.session import engine

app = FastAPI()

app.include_router(csv_routes.router, prefix="/api")

# 👇 Create tables if they don't exist
Base.metadata.create_all(bind=engine)
