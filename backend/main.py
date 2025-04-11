from fastapi import FastAPI
from backend.api import csv_routes

app = FastAPI()
app.include_router(csv_routes.router, prefix="/api")
