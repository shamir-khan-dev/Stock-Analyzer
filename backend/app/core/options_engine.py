"""
Options Market Structure & Dealer Gamma Exposure (GEX) Engine
Calculates institutional options positioning: Max Pain, Call/Put Walls, Put-Call Open Interest Ratio,
and Dealer Gamma Regimes (Volatility Pinning vs Volatility Expansion).
"""
import time
import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from .data_fetcher import get_clean_ticker

logger = logging.getLogger(__name__)

_OPTIONS_CACHE: Dict[str, Dict[str, Any]] = {}
_OPTIONS_CACHE_TTL = 600  # 10 minutes cache for options chains


def calculate_options_market_structure(ticker: str, current_price: float) -> Dict[str, Any]:
    """
    Retrieves the near-term options chain for ticker and computes:
    - Max Pain strike (institutional settlement magnet)
    - Call Wall (primary dealer overhead resistance)
    - Put Wall (primary dealer downside support floor)
    - Put/Call Open Interest Ratio (PCR OI)
    - Dealer Gamma Regime (Volatility Pinning vs Volatility Cascade)
    """
    clean_sym = get_clean_ticker(ticker)
    now = time.time()

    # Check cache
    if clean_sym in _OPTIONS_CACHE:
        cached_entry = _OPTIONS_CACHE[clean_sym]
        if now - cached_entry["timestamp"] < _OPTIONS_CACHE_TTL:
            return cached_entry["data"]

    fallback_res = {
        "status": "UNAVAILABLE",
        "ticker": clean_sym,
        "max_pain": round(current_price, 2) if current_price else 0.0,
        "call_wall": round(current_price * 1.05, 2) if current_price else 0.0,
        "put_wall": round(current_price * 0.95, 2) if current_price else 0.0,
        "pcr_oi": 1.0,
        "pcr_sentiment": "NEUTRAL",
        "gamma_regime": "NEUTRAL GAMMA",
        "gamma_badge": "N/A",
        "gamma_color": "#94a3b8",
        "pin_distance_pct": 0.0,
        "summary": "Options market structure is not available for this instrument (crypto, index, or non-optionable equity)."
    }

    # Crypto or index aliases do not have standardized US equity options chains on yfinance
    if "-USD" in clean_sym or current_price <= 0:
        return fallback_res

    try:
        import yfinance as yf
        t = yf.Ticker(clean_sym)
        expirations = t.options

        if not expirations or len(expirations) == 0:
            return fallback_res

        # Select the nearest expiration (front-month / front-week)
        target_exp = expirations[0]
        chain = t.option_chain(target_exp)

        calls = chain.calls.copy()
        puts = chain.puts.copy()

        if calls.empty and puts.empty:
            return fallback_res

        # Clean columns & fill NA
        calls['openInterest'] = calls['openInterest'].fillna(0).astype(float)
        puts['openInterest'] = puts['openInterest'].fillna(0).astype(float)
        
        # Filter out strikes far away from current price (> 40% away) to eliminate deep OTM junk
        low_bound = current_price * 0.60
        high_bound = current_price * 1.40

        calls_filtered = calls[(calls['strike'] >= low_bound) & (calls['strike'] <= high_bound)]
        puts_filtered = puts[(puts['strike'] >= low_bound) & (puts['strike'] <= high_bound)]

        total_call_oi = float(calls['openInterest'].sum())
        total_put_oi = float(puts['openInterest'].sum())
        pcr_oi = total_put_oi / max(1.0, total_call_oi)

        # Call Wall (strike with highest Call OI)
        call_wall = float(calls_filtered.loc[calls_filtered['openInterest'].idxmax()]['strike']) if not calls_filtered.empty else round(current_price * 1.05, 2)

        # Put Wall (strike with highest Put OI)
        put_wall = float(puts_filtered.loc[puts_filtered['openInterest'].idxmax()]['strike']) if not puts_filtered.empty else round(current_price * 0.95, 2)

        # Calculate Max Pain
        # Max Pain is the strike K that minimizes total option payout:
        # Sum [Call_OI * max(0, K - Call_Strike)] + Sum [Put_OI * max(0, Put_Strike - K)]
        all_strikes = np.unique(np.concatenate([
            calls_filtered['strike'].values,
            puts_filtered['strike'].values
        ]))

        if len(all_strikes) > 0:
            payouts = []
            for k in all_strikes:
                # Call intrinsic value at settlement price k
                call_losses = calls_filtered['openInterest'] * np.maximum(0.0, k - calls_filtered['strike'])
                # Put intrinsic value at settlement price k
                put_losses = puts_filtered['openInterest'] * np.maximum(0.0, puts_filtered['strike'] - k)
                total_loss = call_losses.sum() + put_losses.sum()
                payouts.append(total_loss)

            min_idx = np.argmin(payouts)
            max_pain = float(all_strikes[min_idx])
        else:
            max_pain = round(current_price, 2)

        # Distance from Max Pain in percent
        pin_dist_pct = ((current_price - max_pain) / max_pain) * 100

        # PCR Sentiment
        if pcr_oi < 0.65:
            pcr_sentiment = "BULLISH (HEAVY CALL POSITIONING)"
        elif pcr_oi > 1.15:
            pcr_sentiment = "BEARISH / HEDGED (PUT DOMINANCE)"
        else:
            pcr_sentiment = "BALANCED"

        # Dealer Gamma Regime Determination
        # When price is between Put Wall and Call Wall and near Max Pain -> Positive Gamma (Pinning)
        # When price breaks outside Put Wall or Call Wall -> Negative Gamma (Acceleration)
        if abs(pin_dist_pct) <= 2.5:
            gamma_regime = "POSITIVE GAMMA (MAGNET PINNING)"
            gamma_badge = "GAMMA PINNED"
            gamma_color = "#00e676"  # Emerald
            summary = (
                f"Price (${current_price:.2f}) is hovering within {abs(pin_dist_pct):.1f}% of institutional Max Pain (${max_pain:.2f}). "
                f"Dealers are in positive gamma: market maker hedging suppresses volatility and acts as a price magnet into expiration ({target_exp}). "
                f"Call Wall resistance sits at ${call_wall:.2f}; Put Wall floor is at ${put_wall:.2f}."
            )
        elif current_price < put_wall:
            gamma_regime = "NEGATIVE GAMMA (EXPANSION RISK)"
            gamma_badge = "NEGATIVE GAMMA CASCADE"
            gamma_color = "#ff1744"  # Red
            summary = (
                f"Price has breached below the primary Put Wall (${put_wall:.2f}). "
                f"Dealers transition to short gamma, forcing them to sell delta as price falls. Expect volatility expansion and wide daily swings."
            )
        elif current_price > call_wall:
            gamma_regime = "CALL SQUEEZE REGIME (MOMENTUM ACCELERATION)"
            gamma_badge = "CALL WALL SQUEEZE"
            gamma_color = "#f59e0b"  # Amber
            summary = (
                f"Price has broken above the major Call Wall (${call_wall:.2f}). "
                f"Short-call gamma squeezes can trigger aggressive dealer re-hedging buying, driving rapid momentum."
            )
        else:
            gamma_regime = "BALANCED GAMMA CONSOLIDATION"
            gamma_badge = "GAMMA BOUND"
            gamma_color = "#4facfe"  # Cyan
            summary = (
                f"Price is trading inside the options corridor: Put Wall support at ${put_wall:.2f} and Call Wall ceiling at ${call_wall:.2f}. "
                f"Institutional Max Pain is ${max_pain:.2f} ({pin_dist_pct:+.1f}% vs current price). Target expiration: {target_exp}."
            )

        res_data = {
            "status": "ACTIVE",
            "ticker": clean_sym,
            "expiration": target_exp,
            "max_pain": round(max_pain, 2),
            "call_wall": round(call_wall, 2),
            "put_wall": round(put_wall, 2),
            "total_call_oi": int(total_call_oi),
            "total_put_oi": int(total_put_oi),
            "pcr_oi": round(pcr_oi, 2),
            "pcr_sentiment": pcr_sentiment,
            "gamma_regime": gamma_regime,
            "gamma_badge": gamma_badge,
            "gamma_color": gamma_color,
            "pin_distance_pct": round(pin_dist_pct, 1),
            "summary": summary
        }

        _OPTIONS_CACHE[clean_sym] = {
            "timestamp": now,
            "data": res_data
        }
        return res_data

    except Exception as e:
        logger.warning(f"Error computing options structure for {clean_sym}: {e}")
        return fallback_res
