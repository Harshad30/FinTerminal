import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


PERIOD_MAP = {
    "1D": ("1d", "5m"),
    "1W": ("5d", "30m"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
}

def search_tickers(query: str) -> list[dict]:
    """Search for tickers by company name."""
    try:
        results = yf.Search(query, max_results=6)
        quotes = results.quotes
        return [
            {
                "symbol": q.get("symbol", ""),
                "name": q.get("longname") or q.get("shortname", ""),
                "exchange": q.get("exchange", ""),
                "type": q.get("quoteType", ""),
            }
            for q in quotes
            if q.get("symbol")
        ]
    except Exception:
        return []

def get_ticker_info(ticker: str) -> dict:
    """Fetch company info and key stats."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", None),
            "pe_ratio": info.get("trailingPE", None),
            "eps": info.get("trailingEps", None),
            "dividend_yield": info.get("trailingAnnualDividendYield", None),
            "week_52_high": info.get("fiftyTwoWeekHigh", None),
            "week_52_low": info.get("fiftyTwoWeekLow", None),
            "avg_volume": info.get("averageVolume", None),
            "current_price": info.get("currentPrice", None),
            "previous_close": info.get("previousClose", None),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", "N/A"),
            "description": info.get("longBusinessSummary", "N/A"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_price_history(ticker: str, period_label: str) -> pd.DataFrame:
    """Fetch OHLCV price history for given period."""
    try:
        period, interval = PERIOD_MAP.get(period_label, ("1mo", "1d"))
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        return pd.DataFrame()


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Add 20, 50, 200 day moving averages if enough data."""
    if len(df) >= 20:
        df["MA20"] = df["Close"].rolling(window=20).mean()
    if len(df) >= 50:
        df["MA50"] = df["Close"].rolling(window=50).mean()
    if len(df) >= 200:
        df["MA200"] = df["Close"].rolling(window=200).mean()
    return df


def detect_golden_death_cross(df: pd.DataFrame) -> dict | None:
    """
    Detect golden cross (MA50 crosses above MA200) or
    death cross (MA50 crosses below MA200).
    Returns signal dict or None.
    """
    if "MA50" not in df.columns or "MA200" not in df.columns:
        return None
    if df["MA50"].isna().all() or df["MA200"].isna().all():
        return None

    # get last two valid rows for both MAs
    valid = df[["MA50", "MA200"]].dropna()
    if len(valid) < 2:
        return None

    prev_50 = valid["MA50"].iloc[-2]
    curr_50 = valid["MA50"].iloc[-1]
    prev_200 = valid["MA200"].iloc[-2]
    curr_200 = valid["MA200"].iloc[-1]

    if prev_50 <= prev_200 and curr_50 > curr_200:
        return {
            "signal": "GOLDEN CROSS",
            "description": "50-day MA crossed above 200-day MA — bullish signal",
            "color": "#00aa44",
            "icon": "🟢"
        }
    elif prev_50 >= prev_200 and curr_50 < curr_200:
        return {
            "signal": "DEATH CROSS",
            "description": "50-day MA crossed below 200-day MA — bearish signal",
            "color": "#cc0000",
            "icon": "🔴"
        }
    return None


def format_large_number(n) -> str:
    """Format large numbers to readable form."""
    if n is None:
        return "N/A"
    if n >= 1e12:
        return f"${n/1e12:.2f}T"
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"