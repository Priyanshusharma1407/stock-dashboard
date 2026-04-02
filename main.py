"""
StockIQ — Stock Data Intelligence Dashboard
JarNox Software Internship Assignment

Run with:
    python main.py
or:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import stocks
from app.database import init_db
from app.ingest import ingest_all
import os

app = FastAPI(
    title="StockIQ — Stock Data Intelligence Dashboard",
    description="A mini financial data platform built with FastAPI, yfinance, and SQLite.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(stocks.router, tags=["Stock Data"])


@app.on_event("startup")
async def startup():
    """Initialize DB and ingest data on first run."""
    init_db()
    db_path = "stocks.db"
    # Only ingest if DB is empty or missing
    if not os.path.exists(db_path) or os.path.getsize(db_path) < 10_000:
        print("📥 First run detected — ingesting stock data...")
        ingest_all()
    else:
        print("✅ Database already populated — skipping ingest.")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serve the frontend dashboard."""
    return FileResponse("templates/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
