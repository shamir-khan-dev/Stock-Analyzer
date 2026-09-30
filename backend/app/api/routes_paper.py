from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..core.paper_trading import load_portfolio, execute_paper_trade, reset_paper_portfolio
from ..core.data_fetcher import fetch_live_quote

router = APIRouter()

class TradeRequest(BaseModel):
    symbol: str
    action: str  # BUY or SELL
    shares: float
    stop_loss: Optional[float] = 0.0
    take_profit: Optional[float] = 0.0

@router.get("/paper/portfolio")
async def get_portfolio_summary():
    portfolio = load_portfolio()
    
    # Calculate live mark-to-market total portfolio value
    positions_eval = []
    total_positions_value = 0.0
    total_unrealized_pnl = 0.0

    for pos in portfolio.get("open_positions", []):
        sym = pos["symbol"]
        quote = fetch_live_quote(sym)
        curr_price = quote.get("current_price", pos["avg_price"])
        market_val = round(pos["shares"] * curr_price, 2)
        cost_val = round(pos["shares"] * pos["avg_price"], 2)
        unrealized = round(market_val - cost_val, 2)
        unrealized_pct = round((unrealized / cost_val) * 100, 2) if cost_val else 0.0

        positions_eval.append({
            "symbol": sym,
            "shares": pos["shares"],
            "avg_price": pos["avg_price"],
            "current_price": curr_price,
            "market_value": market_val,
            "unrealized_pnl": unrealized,
            "unrealized_pnl_pct": unrealized_pct,
            "stop_loss": pos.get("stop_loss", 0.0),
            "take_profit": pos.get("take_profit", 0.0)
        })
        
        total_positions_value += market_val
        total_unrealized_pnl += unrealized

    total_account_value = round(portfolio["cash_balance"] + total_positions_value, 2)
    net_profit = round(total_account_value - portfolio["initial_capital"], 2)
    net_profit_pct = round((net_profit / portfolio["initial_capital"]) * 100, 2)

    return {
        "cash_balance": portfolio["cash_balance"],
        "positions_value": round(total_positions_value, 2),
        "total_account_value": total_account_value,
        "net_profit": net_profit,
        "net_profit_pct": net_profit_pct,
        "open_positions": positions_eval,
        "closed_trades": portfolio.get("closed_trades", [])
    }

@router.post("/paper/execute")
async def execute_trade(req: TradeRequest):
    quote = fetch_live_quote(req.symbol)
    price = quote.get("current_price", 0.0)
    if price <= 0:
        raise HTTPException(status_code=400, detail=f"Could not fetch live price for symbol {req.symbol}")

    res = execute_paper_trade(
        symbol=req.symbol,
        action=req.action.upper(),
        shares=req.shares,
        price=price,
        stop_loss=req.stop_loss or 0.0,
        take_profit=req.take_profit or 0.0
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))

    return res

@router.post("/paper/reset")
async def reset_portfolio():
    res = reset_paper_portfolio()
    return {"message": "Portfolio reset to initial $100,000 balance.", "portfolio": res}
