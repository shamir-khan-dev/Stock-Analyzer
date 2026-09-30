"""
Signal Reliability & Accuracy Enhancement Module
- Earnings date warnings (high-risk periods)
- Signal strength / reliability scoring
- Confirmation Required mode (MTF alignment gate)
- Signal log tracker (win/loss history)
"""
import json
import os
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

# File-based signal log — persists in isolated data directory
_DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
os.makedirs(_DATA_DIR, exist_ok=True)
_SIGNAL_LOG_PATH = os.path.join(_DATA_DIR, "signal_log.json")


def get_earnings_warning(ticker: str) -> Dict[str, Any]:
    """
    Checks if there is an upcoming earnings date within 7 days for the ticker.
    Returns a warning dict if so.
    """
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        cal = t.calendar
        
        if cal is None or cal.empty:
            return {"has_warning": False}
        
        # Calendar may have 'Earnings Date' as a row
        earnings_dates = []
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if ed:
                earnings_dates = [ed] if not isinstance(ed, list) else ed
        else:
            # DataFrame format
            if "Earnings Date" in cal.index:
                val = cal.loc["Earnings Date"]
                if hasattr(val, '__iter__') and not isinstance(val, str):
                    earnings_dates = list(val)
                else:
                    earnings_dates = [val]
        
        today = date.today()
        for ed in earnings_dates:
            try:
                if hasattr(ed, 'date'):
                    ed_date = ed.date()
                elif isinstance(ed, str):
                    ed_date = datetime.strptime(ed[:10], "%Y-%m-%d").date()
                else:
                    ed_date = ed
                    
                days_away = (ed_date - today).days
                if -2 <= days_away <= 10:
                    urgency = "IMMINENT" if days_away <= 3 else "UPCOMING"
                    return {
                        "has_warning": True,
                        "earnings_date": str(ed_date),
                        "days_away": days_away,
                        "urgency": urgency,
                        "message": f"⚠️ EARNINGS {urgency}: {ed_date.strftime('%b %d')} ({days_away}d away). Signals are UNRELIABLE near earnings — volatility spikes expected. Consider waiting.",
                        "risk_level": "HIGH"
                    }
            except Exception:
                continue
                
        return {"has_warning": False}
    except Exception as e:
        logger.debug(f"Could not fetch earnings for {ticker}: {e}")
        return {"has_warning": False}


def calculate_signal_reliability(
    confluence_score: float,
    mtf_alignment: Dict[str, str],
    vol_ratio: float,
    rsi: float,
    earnings_warning: Dict,
    patterns: List[Dict]
) -> Dict[str, Any]:
    """
    Calculates a Signal Reliability score (0-100) that indicates HOW MUCH to trust
    the current BUY/SELL verdict.
    
    High reliability = multiple timeframes aligned + strong volume + no earnings risk
    Low reliability = conflicting signals, low volume, earnings imminent
    """
    reliability = 50  # Start at neutral
    reasons = []
    warnings = []

    # 1. MTF Alignment — most important factor
    mtf_values = [mtf_alignment.get("15M", "NEUTRAL"), mtf_alignment.get("1H", "NEUTRAL"), mtf_alignment.get("1D", "NEUTRAL")]
    bull_count = sum(1 for v in mtf_values if v == "BULLISH")
    bear_count = sum(1 for v in mtf_values if v == "BEARISH")
    
    if bull_count == 3 or bear_count == 3:
        reliability += 25
        reasons.append("All 3 timeframes (15M/1H/1D) are fully aligned — strong directional conviction.")
    elif bull_count == 2 or bear_count == 2:
        reliability += 10
        reasons.append("2 of 3 timeframes agree — moderate directional confidence.")
    else:
        reliability -= 15
        warnings.append("Timeframes are conflicting — 15M, 1H, and 1D disagree. Wait for alignment.")

    # 2. Volume confirmation
    if vol_ratio >= 1.5:
        reliability += 15
        reasons.append(f"Strong volume confirmation ({vol_ratio:.1f}x average) — institutional participation likely.")
    elif vol_ratio >= 1.1:
        reliability += 5
        reasons.append("Above-average volume — moderate confirmation.")
    elif vol_ratio < 0.7:
        reliability -= 15
        warnings.append("Very low volume — signal lacks institutional conviction. High false-signal risk.")

    # 3. Confluence score strength
    abs_score = abs(confluence_score)
    if abs_score >= 60:
        reliability += 15
        reasons.append(f"Confluence score of {confluence_score:+.0f}/100 is very strong.")
    elif abs_score >= 35:
        reliability += 7
        reasons.append(f"Confluence score of {confluence_score:+.0f}/100 is moderately strong.")
    elif abs_score < 20:
        reliability -= 10
        warnings.append(f"Weak confluence score ({confluence_score:+.0f}/100) — market is indecisive.")

    # 4. RSI extremes (signal less reliable at extremes)
    if rsi > 80:
        reliability -= 10
        warnings.append(f"RSI={rsi:.1f} is extremely overbought — BUY signals less reliable at this level.")
    elif rsi < 20:
        reliability -= 10
        warnings.append(f"RSI={rsi:.1f} is extremely oversold — potential for continued selling.")

    # 5. Earnings risk — kills reliability
    if earnings_warning.get("has_warning"):
        penalty = 30 if earnings_warning.get("urgency") == "IMMINENT" else 15
        reliability -= penalty
        warnings.append(earnings_warning.get("message", "Earnings approaching — elevated risk."))

    # 6. Candlestick pattern confirmation
    bullish_patterns = [p for p in patterns if p.get("bias") == "BULLISH"]
    bearish_patterns = [p for p in patterns if p.get("bias") == "BEARISH"]
    if len(bullish_patterns) >= 2:
        reliability += 8
        reasons.append(f"{len(bullish_patterns)} bullish candlestick formations confirm the setup.")
    elif len(bearish_patterns) >= 2:
        reliability += 8
        reasons.append(f"{len(bearish_patterns)} bearish candlestick formations confirm the setup.")

    # Clamp
    reliability = max(5, min(98, reliability))

    # Grade
    if reliability >= 75:
        grade = "A"
        label = "HIGH RELIABILITY"
        color = "#00e676"
    elif reliability >= 55:
        grade = "B"
        label = "MODERATE RELIABILITY"
        color = "#ffb300"
    elif reliability >= 35:
        grade = "C"
        label = "LOW RELIABILITY"
        color = "#ff7043"
    else:
        grade = "D"
        label = "DO NOT TRADE"
        color = "#ff1744"

    # Confirmation mode: require ALL 3 timeframes aligned
    mtf_confirmed = (bull_count == 3 or bear_count == 3)

    return {
        "score": reliability,
        "grade": grade,
        "label": label,
        "color": color,
        "mtf_confirmed": mtf_confirmed,
        "bull_tf_count": bull_count,
        "bear_tf_count": bear_count,
        "reasons": reasons[:3],
        "warnings": warnings[:3]
    }


# ─────────────────────────────────────────────────────
# Signal Log Tracker (persisted to JSON file)
# ─────────────────────────────────────────────────────

def _load_signal_log() -> List[Dict]:
    try:
        if os.path.exists(_SIGNAL_LOG_PATH):
            with open(_SIGNAL_LOG_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_signal_log(log: List[Dict]):
    try:
        with open(_SIGNAL_LOG_PATH, "w") as f:
            json.dump(log, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Could not save signal log: {e}")


def log_signal(ticker: str, verdict: str, price: float, entry: float, stop_loss: float, tp1: float, reliability_score: int):
    """Records a new signal to the signal log for future win/loss tracking."""
    log = _load_signal_log()
    signal = {
        "id": f"{ticker}_{int(time.time())}",
        "ticker": ticker,
        "verdict": verdict,
        "price_at_signal": round(price, 2),
        "entry_price": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit_1": round(tp1, 2),
        "reliability_score": reliability_score,
        "signal_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "OPEN",   # OPEN -> WIN / LOSS / EXPIRED
        "outcome_price": None,
        "pnl_pct": None
    }
    # Don't duplicate — deduplicate by ticker + verdict + same-day
    today_str = datetime.now().strftime("%Y-%m-%d")
    existing = [s for s in log if s["ticker"] == ticker and s["signal_date"][:10] == today_str and s["verdict"] == verdict]
    if not existing:
        log.insert(0, signal)
        log = log[:200]  # Keep last 200 signals max
        _save_signal_log(log)
    return signal


def update_signal_outcomes(current_prices: Dict[str, float]):
    """
    Called periodically to check open signals against current prices
    and mark them WIN/LOSS if TP or SL was hit.
    """
    log = _load_signal_log()
    changed = False
    for sig in log:
        if sig["status"] != "OPEN":
            continue
        ticker = sig["ticker"]
        cur_price = current_prices.get(ticker)
        if not cur_price:
            continue
        entry = sig["entry_price"]
        sl = sig["stop_loss"]
        tp = sig["take_profit_1"]
        verdict = sig.get("verdict", "")
        
        is_buy = "BUY" in verdict
        if is_buy:
            if cur_price >= tp:
                sig["status"] = "WIN"
                sig["outcome_price"] = cur_price
                sig["pnl_pct"] = round((tp - entry) / entry * 100, 2)
                changed = True
            elif cur_price <= sl:
                sig["status"] = "LOSS"
                sig["outcome_price"] = cur_price
                sig["pnl_pct"] = round((sl - entry) / entry * 100, 2)
                changed = True
        else:  # SELL signal
            if cur_price <= tp:
                sig["status"] = "WIN"
                sig["outcome_price"] = cur_price
                sig["pnl_pct"] = round((entry - tp) / entry * 100, 2)
                changed = True
            elif cur_price >= sl:
                sig["status"] = "LOSS"
                sig["outcome_price"] = cur_price
                sig["pnl_pct"] = round((entry - sl) / entry * 100, 2)
                changed = True
    
    if changed:
        _save_signal_log(log)
    return log


def get_signal_tracker_stats() -> Dict[str, Any]:
    """Returns aggregated win/loss stats for the signal log dashboard."""
    log = _load_signal_log()
    closed = [s for s in log if s["status"] in ("WIN", "LOSS")]
    open_signals = [s for s in log if s["status"] == "OPEN"]
    wins = [s for s in closed if s["status"] == "WIN"]
    losses = [s for s in closed if s["status"] == "LOSS"]
    
    total = len(closed)
    win_rate = round(len(wins) / total * 100, 1) if total > 0 else 0.0
    avg_win_pct = round(sum(s.get("pnl_pct", 0) for s in wins) / len(wins), 2) if wins else 0.0
    avg_loss_pct = round(sum(abs(s.get("pnl_pct", 0)) for s in losses) / len(losses), 2) if losses else 0.0
    
    return {
        "total_signals": len(log),
        "closed_signals": total,
        "open_signals": len(open_signals),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": win_rate,
        "avg_win_pct": avg_win_pct,
        "avg_loss_pct": avg_loss_pct,
        "recent_signals": log[:15]  # Last 15 for display
    }
