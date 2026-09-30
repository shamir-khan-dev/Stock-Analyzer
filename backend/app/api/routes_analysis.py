from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..core.data_fetcher import fetch_history_data, fetch_live_quote
from ..core.quant_engine import analyze_ticker_confluence

router = APIRouter()

@router.get("/analyze/{ticker}")
async def analyze_ticker(
    ticker: str,
    period: str = Query("6mo", description="Historical period: 1mo, 3mo, 6mo, 1y, 2y"),
    interval: str = Query("1d", description="Bar interval: 5m, 15m, 1h, 1d")
):
    """
    Returns full quantitative analysis, confluence score, buy/sell verdict,
    ATR-based stop-loss/take-profit, candlestick patterns, and chart bars.
    """
    clean_sym = ticker.strip().upper()
    df = fetch_history_data(clean_sym, period=period, interval=interval)
    
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Could not retrieve market data for symbol '{clean_sym}'. Please check symbol spelling."
        )
        
    analysis = analyze_ticker_confluence(df, clean_sym)
    if "error" in analysis:
        raise HTTPException(status_code=400, detail=analysis["error"])
        
    quote = fetch_live_quote(clean_sym)
    analysis["quote"] = quote
    return analysis
