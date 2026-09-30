"""
API routes for signal tracker, reliability stats, and earnings warnings.
"""
from fastapi import APIRouter
from ..core.signal_accuracy import get_signal_tracker_stats, update_signal_outcomes
from ..core.data_fetcher import fetch_live_quote

router = APIRouter()

@router.get("/signals/tracker")
async def get_signal_tracker():
    """
    Returns the live signal tracker with win/loss history.
    Also refreshes outcomes for open signals before returning.
    """
    stats = get_signal_tracker_stats()

    # Try to update open signal outcomes with current prices
    open_sigs = [s for s in stats.get("recent_signals", []) if s["status"] == "OPEN"]
    if open_sigs:
        tickers = list({s["ticker"] for s in open_sigs})
        prices = {}
        for t in tickers[:10]:  # Limit to 10 to avoid slowdowns
            try:
                q = fetch_live_quote(t)
                prices[t] = q.get("current_price", 0)
            except Exception:
                pass
        if prices:
            update_signal_outcomes(prices)
            stats = get_signal_tracker_stats()  # Refresh after updates

    return stats
