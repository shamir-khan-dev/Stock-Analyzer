import json
import time
from pathlib import Path
from typing import Dict, Any, List

STORAGE_FILE = Path(__file__).resolve().parent.parent / "paper_portfolio.json"

DEFAULT_PORTFOLIO = {
    "cash_balance": 100000.0,
    "initial_capital": 100000.0,
    "open_positions": [],
    "closed_trades": [],
    "updated_at": time.time()
}

def load_portfolio() -> Dict[str, Any]:
    """Loads portfolio state from storage file or initializes default."""
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, "r") as f:
                data = json.load(f)
                return data
        except Exception:
            pass
    save_portfolio(DEFAULT_PORTFOLIO)
    return DEFAULT_PORTFOLIO

def save_portfolio(data: Dict[str, Any]):
    """Persists portfolio state to file."""
    data["updated_at"] = time.time()
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def execute_paper_trade(symbol: str, action: str, shares: float, price: float, stop_loss: float = 0.0, take_profit: float = 0.0) -> Dict[str, Any]:
    """
    Executes a virtual paper trade (BUY or SELL).
    Updates cash balance, calculates position sizing, and logs trade execution.
    """
    portfolio = load_portfolio()
    sym = symbol.strip().upper()
    total_cost = round(shares * price, 2)

    if action == "BUY":
        if total_cost > portfolio["cash_balance"]:
            return {
                "success": False,
                "error": f"Insufficient buying power. Required: ${total_cost:,.2f}, Available: ${portfolio['cash_balance']:,.2f}"
            }
        
        portfolio["cash_balance"] = round(portfolio["cash_balance"] - total_cost, 2)
        
        # Check if already holding position
        existing = next((p for p in portfolio["open_positions"] if p["symbol"] == sym), None)
        if existing:
            new_shares = existing["shares"] + shares
            new_avg = round(((existing["shares"] * existing["avg_price"]) + total_cost) / new_shares, 2)
            existing["shares"] = new_shares
            existing["avg_price"] = new_avg
            existing["stop_loss"] = stop_loss
            existing["take_profit"] = take_profit
        else:
            portfolio["open_positions"].append({
                "symbol": sym,
                "shares": shares,
                "avg_price": price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "entered_at": time.time()
            })

        save_portfolio(portfolio)
        return {
            "success": True,
            "message": f"Successfully BOUGHT {shares} shares of {sym} at ${price:,.2f}",
            "portfolio": portfolio
        }

    elif action == "SELL":
        existing = next((p for p in portfolio["open_positions"] if p["symbol"] == sym), None)
        if not existing or existing["shares"] < shares:
            curr_shares = existing["shares"] if existing else 0
            return {
                "success": False,
                "error": f"Cannot sell {shares} shares of {sym}. Currently holding: {curr_shares} shares."
            }

        proceeds = round(shares * price, 2)
        cost_basis = round(shares * existing["avg_price"], 2)
        realized_pnl = round(proceeds - cost_basis, 2)

        portfolio["cash_balance"] = round(portfolio["cash_balance"] + proceeds, 2)
        existing["shares"] = round(existing["shares"] - shares, 2)

        if existing["shares"] <= 0:
            portfolio["open_positions"] = [p for p in portfolio["open_positions"] if p["symbol"] != sym]

        portfolio["closed_trades"].append({
            "symbol": sym,
            "shares": shares,
            "entry_price": existing["avg_price"],
            "exit_price": price,
            "realized_pnl": realized_pnl,
            "pnl_pct": round((realized_pnl / cost_basis) * 100, 2) if cost_basis else 0.0,
            "closed_at": time.time()
        })

        save_portfolio(portfolio)
        return {
            "success": True,
            "message": f"Successfully SOLD {shares} shares of {sym} at ${price:,.2f}. Realized P&L: ${realized_pnl:+,.2f}",
            "portfolio": portfolio
        }

    return {"success": False, "error": "Invalid action. Use BUY or SELL."}

def reset_paper_portfolio() -> Dict[str, Any]:
    """Resets portfolio back to initial $100,000 cash."""
    save_portfolio(DEFAULT_PORTFOLIO)
    return DEFAULT_PORTFOLIO
