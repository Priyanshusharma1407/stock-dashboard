"""
Part 1: Data Collection & Preparation
Fetches real stock data using yfinance, cleans it with Pandas,
and stores it in SQLite with calculated metrics.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.database import SessionLocal, StockPrice, init_db
from datetime import datetime, timedelta

# Indian + Global stocks to track
COMPANIES = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "WIPRO.NS": "Wipro",
    "BAJFINANCE.NS": "Bajaj Finance",
    "SBIN.NS": "State Bank of India",
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
}


def fetch_and_clean(symbol: str, period: str = "1y") -> pd.DataFrame:
    """Fetch stock data from yfinance and apply cleaning + metrics."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period)

    if df.empty:
        print(f"  ⚠️  No data for {symbol}, skipping.")
        return pd.DataFrame()

    # --- Cleaning ---
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.dropna(subset=["Open", "Close"], inplace=True)        # drop rows missing OHLC
    df = df[df["Close"] > 0]                                  # remove bad prices
    df.index = pd.to_datetime(df.index).tz_localize(None)    # strip timezone

    # --- Calculated Metrics ---
    df["daily_return"] = (df["Close"] - df["Open"]) / df["Open"]  # % gain/loss per day
    df["ma_7"] = df["Close"].rolling(window=7).mean()              # 7-day moving average

    # Custom metric: Volatility Score (rolling 14-day std of daily return)
    df["volatility_score"] = df["daily_return"].rolling(window=14).std()

    df.reset_index(inplace=True)
    df.rename(columns={"index": "Date"}, inplace=True)
    if "Date" not in df.columns and "Datetime" in df.columns:
        df.rename(columns={"Datetime": "Date"}, inplace=True)

    return df


def load_to_db(symbol: str, company_name: str, df: pd.DataFrame, db: Session):
    """Insert cleaned data into the SQLite database."""
    # Clear old records for this symbol
    db.query(StockPrice).filter(StockPrice.symbol == symbol).delete()

    for _, row in df.iterrows():
        record = StockPrice(
            symbol=symbol,
            company_name=company_name,
            date=row["Date"].date() if hasattr(row["Date"], "date") else row["Date"],
            open=round(float(row["Open"]), 4),
            high=round(float(row["High"]), 4),
            low=round(float(row["Low"]), 4),
            close=round(float(row["Close"]), 4),
            volume=float(row["Volume"]),
            daily_return=round(float(row["daily_return"]), 6) if not np.isnan(row["daily_return"]) else None,
            ma_7=round(float(row["ma_7"]), 4) if not np.isnan(row["ma_7"]) else None,
        )
        db.add(record)
    db.commit()


def ingest_all():
    """Main ingestion pipeline — fetch, clean, store all companies."""
    init_db()
    db = SessionLocal()
    print("🚀 Starting data ingestion...\n")

    for symbol, name in COMPANIES.items():
        print(f"  📥 Fetching {name} ({symbol})...")
        df = fetch_and_clean(symbol)
        if not df.empty:
            load_to_db(symbol, name, df, db)
            print(f"  ✅ Stored {len(df)} rows for {symbol}")

    db.close()
    print("\n✅ Data ingestion complete!")


if __name__ == "__main__":
    ingest_all()
