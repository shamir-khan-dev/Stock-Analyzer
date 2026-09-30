from fastapi import APIRouter
from typing import List, Dict, Any
from ..core.data_fetcher import fetch_live_quote

router = APIRouter()

POPULAR_TICKERS = [
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "category": "Semiconductors"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "category": "EV / Tech"},
    {"symbol": "AAPL", "name": "Apple Inc.", "category": "Mega Tech"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "category": "Cloud / AI"},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "category": "E-Commerce / Cloud"},
    {"symbol": "BTC-USD", "name": "Bitcoin (USD)", "category": "Crypto"},
    {"symbol": "ETH-USD", "name": "Ethereum (USD)", "category": "Crypto"},
    {"symbol": "SOL-USD", "name": "Solana (USD)", "category": "Crypto"},
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "category": "Index ETF"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "category": "Index ETF"}
]

@router.get("/market/popular")
async def get_popular_tickers():
    """Returns curated list of popular market assets."""
    return POPULAR_TICKERS

@router.get("/market/quote/{ticker}")
async def get_quote(ticker: str):
    """Returns real-time quote for a given ticker."""
    return fetch_live_quote(ticker)
