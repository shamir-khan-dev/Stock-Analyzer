from fastapi import APIRouter, HTTPException, Query
from ..core.data_fetcher import fetch_history_data
from ..core.backtester import run_strategy_backtest

router = APIRouter()

@router.get("/backtest/{ticker}")
async def backtest_ticker(
    ticker: str,
    period: str = Query("1y", description="Backtest history: 6mo, 1y, 2y"),
    capital: float = Query(10000.0, description="Initial backtest capital")
):
    """
    Executes historical backtest of the confluence strategy on the ticker.
    Returns Win Rate, Profit Factor, Max Drawdown, and recent trade logs.
    """
    clean_sym = ticker.strip().upper()
    df = fetch_history_data(clean_sym, period=period, interval="1d")
    
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Could not retrieve historical data for symbol '{clean_sym}'."
        )
        
    result = run_strategy_backtest(df, initial_capital=capital)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    result["symbol"] = clean_sym
    result["period"] = period
    return result
