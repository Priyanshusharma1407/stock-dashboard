# 📈 StockIQ — Stock Data Intelligence Dashboard

> **JarNox Software Internship Assignment**  
> Built with FastAPI · yfinance · SQLite · Pandas · Chart.js

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/stock-dashboard.git
cd stock-dashboard

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
```

Then open **http://localhost:8000** in your browser.

> ⚡ On first run, the app automatically fetches ~1 year of stock data for 10 companies. This takes ~30 seconds.

---

## 🧩 Project Structure

```
stock-dashboard/
├── main.py                  # FastAPI app entry point
├── requirements.txt
├── README.md
├── app/
│   ├── database.py          # SQLAlchemy models + SQLite setup
│   ├── ingest.py            # Part 1: Data collection & cleaning
│   └── routers/
│       └── stocks.py        # Part 2: REST API endpoints
└── templates/
    └── index.html           # Part 3: Frontend dashboard
```

---

## 📊 Assignment Coverage

### Part 1 — Data Collection & Preparation (`app/ingest.py`)

- Fetches **1 year** of OHLCV data using `yfinance` for 10 companies (NSE + US stocks)
- **Cleaning:**
  - Drops rows with missing Open/Close values
  - Removes prices ≤ 0
  - Strips timezone from datetime index
- **Calculated Metrics:**
  - `daily_return` = (CLOSE − OPEN) / OPEN
  - `ma_7` = 7-day rolling average of Close
  - `volatility_score` = 14-day rolling std of daily return *(custom metric)*
- **Storage:** SQLite via SQLAlchemy ORM

### Part 2 — Backend API (`app/routers/stocks.py`)

| Endpoint | Method | Description |
|---|---|---|
| `/companies` | GET | All available companies |
| `/data/{symbol}` | GET | Last N days of OHLCV + metrics (default 30) |
| `/summary/{symbol}` | GET | 52-week high, low, avg close, volatility |
| `/compare` | GET | Compare two stocks with correlation |
| `/gainers-losers` | GET | Top 5 daily gainers and losers |

**Swagger UI:** http://localhost:8000/docs

### Part 3 — Visualization Dashboard (`templates/index.html`)

- Sidebar with all tracked companies
- **Closing Price chart** with 7-day MA overlay
- **Daily Return bar chart** (green/red for gain/loss)
- **Period filters:** 7D / 30D / 90D / 180D / 365D
- **Stat cards:** Close, period change, 52W high/low, avg, volatility
- **Stock comparison tool** with correlation analysis
- **Top Gainers / Losers** on the home screen

---

## 🏢 Companies Tracked

| Symbol | Company |
|---|---|
| RELIANCE.NS | Reliance Industries |
| TCS.NS | Tata Consultancy Services |
| INFY.NS | Infosys |
| HDFCBANK.NS | HDFC Bank |
| ICICIBANK.NS | ICICI Bank |
| WIPRO.NS | Wipro |
| BAJFINANCE.NS | Bajaj Finance |
| SBIN.NS | State Bank of India |
| AAPL | Apple Inc. |
| GOOGL | Alphabet Inc. |

---

## 🔬 Custom Metric: Volatility Score

Beyond the required metrics, I added a **Volatility Score** — a 14-day rolling standard deviation of daily returns. This gives a sense of how "risky" or "unstable" a stock has been recently. A higher volatility score means wider price swings.

This is surfaced in both the `/summary` API and the dashboard stat cards.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Backend | FastAPI + Uvicorn |
| Database | SQLite (via SQLAlchemy ORM) |
| Data Source | yfinance |
| Data Processing | Pandas, NumPy |
| Frontend | HTML + Vanilla JS + Chart.js |

---

## 📬 Submission

- **Email:** support@jarnox.com  
- **GitHub:** [link to your repo]  
- Built by: **Priyanshu**
