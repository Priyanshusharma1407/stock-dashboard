"""
Part 2: Backend API Development
REST endpoints for stock data using FastAPI.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db, StockPrice
from datetime import date, timedelta
from typing import Optional
import numpy as np

router = APIRouter()


# ─────────────────────────────────────────────
# GET /companies
# Returns all available companies
# ─────────────────────────────────────────────
@router.get("/companies", summary="List all available companies")
def get_companies(db: Session = Depends(get_db)):
    rows = (
        db.query(StockPrice.symbol, StockPrice.company_name)
        .distinct(StockPrice.symbol)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No companies found. Run ingest first.")
    return [{"symbol": r.symbol, "name": r.company_name} for r in rows]


# ─────────────────────────────────────────────
# GET /data/{symbol}
# Last 30 days of OHLCV + metrics
# ─────────────────────────────────────────────
@router.get("/data/{symbol}", summary="Get last 30 days of stock data")
def get_stock_data(
    symbol: str,
    days: int = Query(default=30, ge=7, le=365, description="Number of days to fetch"),
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol, StockPrice.date >= cutoff)
        .order_by(StockPrice.date.asc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")

    return {
        "symbol": symbol,
        "company": rows[0].company_name,
        "days": days,
        "data": [
            {
                "date": str(r.date),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
                "daily_return": r.daily_return,
                "ma_7": r.ma_7,
            }
            for r in rows
        ],
    }


# ─────────────────────────────────────────────
# GET /summary/{symbol}
# 52-week high, low, avg close
# ─────────────────────────────────────────────
@router.get("/summary/{symbol}", summary="Get 52-week summary for a stock")
def get_summary(symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper()
    cutoff = date.today() - timedelta(weeks=52)
    rows = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol, StockPrice.date >= cutoff)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for symbol: {symbol}")

    closes = [r.close for r in rows]
    returns = [r.daily_return for r in rows if r.daily_return is not None]
    volatility = float(np.std(returns)) if returns else None

    return {
        "symbol": symbol,
        "company": rows[0].company_name,
        "52_week_high": max(r.high for r in rows),
        "52_week_low": min(r.low for r in rows),
        "avg_close": round(sum(closes) / len(closes), 2),
        "volatility_score": round(volatility, 6) if volatility else None,
        "total_trading_days": len(rows),
    }


# ─────────────────────────────────────────────
# GET /compare?symbol1=INFY.NS&symbol2=TCS.NS
# Compare two stocks (Bonus endpoint)
# ─────────────────────────────────────────────
@router.get("/compare", summary="Compare performance of two stocks")
def compare_stocks(
    symbol1: str = Query(..., description="First stock symbol"),
    symbol2: str = Query(..., description="Second stock symbol"),
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    symbol1, symbol2 = symbol1.upper(), symbol2.upper()
    cutoff = date.today() - timedelta(days=days)

    def fetch(sym):
        return (
            db.query(StockPrice)
            .filter(StockPrice.symbol == sym, StockPrice.date >= cutoff)
            .order_by(StockPrice.date.asc())
            .all()
        )

    rows1, rows2 = fetch(symbol1), fetch(symbol2)

    if not rows1:
        raise HTTPException(status_code=404, detail=f"No data for {symbol1}")
    if not rows2:
        raise HTTPException(status_code=404, detail=f"No data for {symbol2}")

    def stats(rows):
        closes = [r.close for r in rows]
        returns = [r.daily_return for r in rows if r.daily_return is not None]
        pct_change = ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] else 0
        return {
            "company": rows[0].company_name,
            "start_price": closes[0],
            "end_price": closes[-1],
            "pct_change": round(pct_change, 2),
            "avg_daily_return": round(sum(returns) / len(returns), 6) if returns else None,
            "52_week_high": max(r.high for r in rows),
            "52_week_low": min(r.low for r in rows),
        }

    # Correlation between closing prices
    import pandas as pd
    df1 = pd.Series([r.close for r in rows1], name=symbol1)
    df2 = pd.Series([r.close for r in rows2], name=symbol2)
    min_len = min(len(df1), len(df2))
    corr = round(float(df1.iloc[-min_len:].corr(df2.iloc[-min_len:])), 4)

    return {
        "period_days": days,
        symbol1: stats(rows1),
        symbol2: stats(rows2),
        "correlation": corr,
        "correlation_note": (
            "Strong positive correlation" if corr > 0.7
            else "Moderate correlation" if corr > 0.4
            else "Low correlation"
        ),
    }


# ─────────────────────────────────────────────
# GET /gainers-losers
# Top 5 gainers and losers today
# ─────────────────────────────────────────────
@router.get("/gainers-losers", summary="Top gainers and losers")
def gainers_losers(db: Session = Depends(get_db)):
    cutoff = date.today() - timedelta(days=5)  # handle weekends
    subq = (
        db.query(StockPrice.symbol, func.max(StockPrice.date).label("max_date"))
        .filter(StockPrice.date >= cutoff)
        .group_by(StockPrice.symbol)
        .subquery()
    )
    rows = (
        db.query(StockPrice)
        .join(subq, (StockPrice.symbol == subq.c.symbol) & (StockPrice.date == subq.c.max_date))
        .all()
    )
    sorted_rows = sorted(
        [r for r in rows if r.daily_return is not None],
        key=lambda x: x.daily_return,
        reverse=True,
    )
    def fmt(r):
        return {
            "symbol": r.symbol,
            "company": r.company_name,
            "date": str(r.date),
            "daily_return_pct": round(r.daily_return * 100, 2),
            "close": r.close,
        }

    return {
        "top_gainers": [fmt(r) for r in sorted_rows[:5]],
        "top_losers": [fmt(r) for r in sorted_rows[-5:][::-1]],
    }
