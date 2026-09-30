import time
import logging
from typing import Dict, Any, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

# In-memory cache to prevent spamming APIs and avoid rate-limits
_QUOTE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_HISTORY_CACHE: Dict[str, Tuple[float, Any]] = {}
CACHE_EXPIRY_SECONDS = 60  # 1 minute cache for real-time OHLCV

def get_clean_ticker(ticker: str) -> str:
    """Normalizes ticker symbol (e.g. btc -> BTC-USD, apple -> AAPL)."""
    t = ticker.strip().upper()
    crypto_aliases = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "SOL": "SOL-USD",
        "DOGE": "DOGE-USD",
        "XRP": "XRP-USD",
        "ADA": "ADA-USD"
    }
    return crypto_aliases.get(t, t)

def fetch_history_data(ticker: str, period: str = "6mo", interval: str = "1d"):
    """
    Fetches historical OHLCV data using yfinance, with fallback to direct Yahoo Finance query.
    Returns a pandas DataFrame with columns: Open, High, Low, Close, Volume.
    """
    clean_symbol = get_clean_ticker(ticker)
    cache_key = f"{clean_symbol}_{period}_{interval}"
    now = time.time()
    
    if cache_key in _HISTORY_CACHE:
        timestamp, df = _HISTORY_CACHE[cache_key]
        if now - timestamp < CACHE_EXPIRY_SECONDS:
            return df

    df = None
    try:
        import yfinance as yf
        t = yf.Ticker(clean_symbol)
        df = t.history(period=period, interval=interval)
        if df is not None and not df.empty:
            _HISTORY_CACHE[cache_key] = (now, df)
            return df
    except Exception as e:
        logger.warning(f"yfinance fetch failed for {clean_symbol}: {e}. Trying fallback...")

    # Fallback to direct Yahoo Finance v8 API
    try:
        import pandas as pd
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_symbol}?range={period}&interval={interval}"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                item = result[0]
                timestamps = item.get("timestamp", [])
                quote = item.get("indicators", {}).get("quote", [{}])[0]
                opens = quote.get("open", [])
                highs = quote.get("high", [])
                lows = quote.get("low", [])
                closes = quote.get("close", [])
                volumes = quote.get("volume", [])
                
                records = []
                for ts, o, h, l, c, v in zip(timestamps, opens, highs, lows, closes, volumes):
                    if None not in (o, h, l, c):
                        records.append({
                            "Date": pd.to_datetime(ts, unit='s'),
                            "Open": float(o),
                            "High": float(h),
                            "Low": float(l),
                            "Close": float(c),
                            "Volume": float(v or 0)
                        })
                if records:
                    df = pd.DataFrame(records)
                    df.set_index("Date", inplace=True)
                    _HISTORY_CACHE[cache_key] = (now, df)
                    return df
    except Exception as e:
        logger.error(f"Fallback fetch failed for {clean_symbol}: {e}")

    return df

def fetch_live_quote(ticker: str) -> Dict[str, Any]:
    """
    Fetches real-time price snapshot, 24h change, day high/low, and market stats.
    """
    clean_symbol = get_clean_ticker(ticker)
    cache_key = f"quote_{clean_symbol}"
    now = time.time()
    
    if cache_key in _QUOTE_CACHE:
        timestamp, quote = _QUOTE_CACHE[cache_key]
        if now - timestamp < 20:  # 20 second quote cache
            return quote

    quote = {
        "symbol": clean_symbol,
        "name": clean_symbol,
        "current_price": 0.0,
        "previous_close": 0.0,
        "change": 0.0,
        "change_percent": 0.0,
        "day_high": 0.0,
        "day_low": 0.0,
        "volume": 0,
        "market_cap": 0,
        "currency": "USD"
    }

    try:
        import yfinance as yf
        t = yf.Ticker(clean_symbol)
        info = t.info or {}
        price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose", 0.0)
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", price)
        
        # If info is sparse, check fast_info or latest history
        if not price or price == 0:
            hist = t.history(period="2d", interval="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[0]) if len(hist) > 1 else price

        change = price - prev_close if prev_close else 0.0
        change_pct = (change / prev_close * 100) if prev_close else 0.0

        quote.update({
            "name": info.get("shortName") or clean_symbol,
            "current_price": round(float(price), 2) if price < 10000 else round(float(price), 4),
            "previous_close": round(float(prev_close), 2),
            "change": round(float(change), 2),
            "change_percent": round(float(change_pct), 2),
            "day_high": round(float(info.get("dayHigh") or info.get("regularMarketDayHigh", price)), 2),
            "day_low": round(float(info.get("dayLow") or info.get("regularMarketDayLow", price)), 2),
            "volume": info.get("regularMarketVolume") or info.get("volume", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": round(float(info.get("trailingPE") or 0.0), 1) if info.get("trailingPE") else None,
            "forward_pe": round(float(info.get("forwardPE") or 0.0), 1) if info.get("forwardPE") else None,
            "eps": round(float(info.get("trailingEps") or 0.0), 2) if info.get("trailingEps") else None,
            "target_mean_price": round(float(info.get("targetMeanPrice") or 0.0), 2) if info.get("targetMeanPrice") else None,
            "fifty_two_week_high": round(float(info.get("fiftyTwoWeekHigh") or 0.0), 2) if info.get("fiftyTwoWeekHigh") else None,
            "fifty_two_week_low": round(float(info.get("fiftyTwoWeekLow") or 0.0), 2) if info.get("fiftyTwoWeekLow") else None
        })
        _QUOTE_CACHE[cache_key] = (now, quote)
        return quote
    except Exception as e:
        logger.warning(f"Error fetching quote for {clean_symbol}: {e}")

    # Fallback to history close
    df = fetch_history_data(clean_symbol, period="5d", interval="1d")
    if df is not None and not df.empty:
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        c = float(latest["Close"])
        pc = float(prev["Close"])
        chg = c - pc
        pct = (chg / pc * 100) if pc else 0.0
        quote.update({
            "current_price": round(c, 2),
            "previous_close": round(pc, 2),
            "change": round(chg, 2),
            "change_percent": round(pct, 2),
            "day_high": round(float(latest["High"]), 2),
            "day_low": round(float(latest["Low"]), 2),
            "volume": int(latest["Volume"])
        })
        _QUOTE_CACHE[cache_key] = (now, quote)
    
    return quote

def fetch_multi_timeframe_data(ticker: str) -> Dict[str, Any]:
    """
    Concurrently fetches historical data across multiple timeframes (15m, 1h, 1d)
    to perform multi-timeframe trend alignment matrix calculation.
    """
    clean_symbol = get_clean_ticker(ticker)
    mtf_data = {
        "15m": fetch_history_data(clean_symbol, period="5d", interval="15m"),
        "1h": fetch_history_data(clean_symbol, period="1mo", interval="1h"),
        "1d": fetch_history_data(clean_symbol, period="6mo", interval="1d")
    }
    return mtf_data

