from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import csv_routes, gpt_routes, wechat_routes, sales_routes, webhook_routes
from backend.db.base import Base
from backend.db.session import engine
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import text
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


# Async DB init for dev mode
async def init_db(engine: AsyncEngine):
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)   # DANGER
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

def run_async_if_needed(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in an event loop (e.g., uvicorn with reload)
        asyncio.create_task(coro)
    else:
        asyncio.run(coro)


if os.getenv("ENV") == "dev":
    #print("Dev mode: dropping and creating tables")
    run_async_if_needed(init_db(engine))
    print("Dev mode: skipping DB init")


app = FastAPI()
# Allow frontend (localhost:5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",  # optional if you switch
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(csv_routes.router, prefix="/api/csv")
app.include_router(gpt_routes.router, prefix="/api/query")
app.include_router(wechat_routes.router, prefix="/api/wechat")
app.include_router(sales_routes.router, prefix="/api/sales")
app.include_router(webhook_routes.router, prefix="/webhook")
