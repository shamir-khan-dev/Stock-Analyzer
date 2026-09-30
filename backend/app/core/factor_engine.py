"""
Factor-Neutral Quantitative Residual Engine
Implements cross-sectional factor neutralization and Ornstein-Uhlenbeck (OU) s-score calculation
to isolate idiosyncratic stock alpha from broader Market Beta (SPY) and Sector Beta.
Reference: Avellaneda & Lee (2010) 'Statistical Arbitrage in the US Equities Market'.
"""
import time
import logging
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from .data_fetcher import fetch_history_data, get_clean_ticker

logger = logging.getLogger(__name__)

# Sector ETF universe mapping
SECTOR_MAP = {
    # Semiconductor / Hardware
    "NVDA": "SOXX", "AMD": "SOXX", "TSM": "SOXX", "AVGO": "SOXX", "INTC": "SOXX",
    "QCOM": "SOXX", "MU": "SOXX", "ASML": "SOXX", "ARM": "SOXX", "TXN": "SOXX",
    # Enterprise Tech / Software / Communication
    "AAPL": "XLK", "MSFT": "XLK", "GOOGL": "XLK", "GOOG": "XLK", "META": "XLK",
    "CRM": "XLK", "ADBE": "XLK", "ORCL": "XLK", "NOW": "XLK", "PLTR": "XLK",
    # Consumer Discretionary & Auto
    "TSLA": "XLY", "AMZN": "XLY", "NKE": "XLY", "SBUX": "XLY", "HD": "XLY", "MCD": "XLY",
    # Financials
    "JPM": "XLF", "BAC": "XLF", "GS": "XLF", "MS": "XLF", "WFC": "XLF", "V": "XLF", "MA": "XLF",
    # Healthcare / Biotech
    "LLY": "XLV", "JNJ": "XLV", "UNH": "XLV", "PFE": "XLV", "ABBV": "XLV", "MRK": "XLV",
    # Energy
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE", "SLB": "XLE", "OXY": "XLE",
    # Industrials & Defense
    "BA": "XLI", "CAT": "XLI", "GE": "XLI", "RTX": "XLI", "LMT": "XLI"
}

_FACTOR_CACHE: Dict[str, Dict[str, Any]] = {}
_FACTOR_CACHE_TTL = 300  # 5 minutes


def calculate_factor_neutral_residual(ticker: str, stock_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Regresses the stock's returns against SPY (Market Beta) and its primary Sector ETF (Sector Beta).
    Computes the residual idiosyncratic spread and the statistical arbitrage s-score.
    """
    clean_sym = get_clean_ticker(ticker)
    now = time.time()

    # Check cache
    if clean_sym in _FACTOR_CACHE:
        cached_entry = _FACTOR_CACHE[clean_sym]
        if now - cached_entry["timestamp"] < _FACTOR_CACHE_TTL:
            return cached_entry["data"]

    # Default fallback response for illiquid/crypto/insufficient data
    fallback_res = {
        "status": "UNAVAILABLE",
        "ticker": clean_sym,
        "sector_etf": "SPY",
        "beta_spy": 1.0,
        "beta_sector": 0.0,
        "s_score": 0.0,
        "regime": "NEUTRAL / MARKET LOCKSTEP",
        "regime_badge": "BETA NEUTRAL",
        "regime_color": "#94a3b8",
        "alpha_spread_pct": 0.0,
        "summary": "Factor neutralization unavailable or ticker is non-equity benchmark."
    }

    if stock_df is None or len(stock_df) < 25:
        return fallback_res

    sector_etf = SECTOR_MAP.get(clean_sym, "SPY")
    
    try:
        # Fetch SPY and Sector ETF daily historical closes
        spy_df = fetch_history_data("SPY", period="6mo", interval="1d")
        sec_df = fetch_history_data(sector_etf, period="6mo", interval="1d") if sector_etf != "SPY" else spy_df

        if spy_df is None or spy_df.empty or len(spy_df) < 25:
            return fallback_res

        # Extract closing prices and normalize indices to date strings
        stock_closes = stock_df['Close'].copy()
        spy_closes = spy_df['Close'].copy()
        sec_closes = sec_df['Close'].copy() if sec_df is not None and not sec_df.empty else spy_closes

        stock_closes.index = pd.to_datetime(stock_closes.index).date
        spy_closes.index = pd.to_datetime(spy_closes.index).date
        sec_closes.index = pd.to_datetime(sec_closes.index).date

        # Align series across common trading dates
        combined = pd.DataFrame({
            "stock": stock_closes,
            "spy": spy_closes,
            "sector": sec_closes
        }).dropna()

        if len(combined) < 20:
            return fallback_res

        # Compute log returns
        ret_stock = np.log(combined["stock"] / combined["stock"].shift(1)).dropna()
        ret_spy = np.log(combined["spy"] / combined["spy"].shift(1)).dropna()
        ret_sec = np.log(combined["sector"] / combined["sector"].shift(1)).dropna()

        aligned_rets = pd.DataFrame({
            "stock": ret_stock,
            "spy": ret_spy,
            "sector": ret_sec
        }).dropna()

        # Design matrix for OLS: [intercept, SPY, Sector]
        n_samples = len(aligned_rets)
        if sector_etf != "SPY":
            X = np.column_stack([np.ones(n_samples), aligned_rets["spy"].values, aligned_rets["sector"].values])
        else:
            X = np.column_stack([np.ones(n_samples), aligned_rets["spy"].values])

        Y = aligned_rets["stock"].values

        # Solve Normal Equations (X^T X)^-1 X^T Y
        try:
            coeffs, residuals, rank, s_vals = np.linalg.lstsq(X, Y, rcond=None)
            alpha_intercept = coeffs[0]
            beta_spy = float(coeffs[1])
            beta_sector = float(coeffs[2]) if sector_etf != "SPY" else 0.0
        except Exception:
            beta_spy = float(np.cov(aligned_rets["stock"], aligned_rets["spy"])[0, 1] / max(0.00001, np.var(aligned_rets["spy"])))
            beta_sector = 0.0

        # Predict systematic factor return & isolate idiosyncratic residuals
        if sector_etf != "SPY":
            predicted = alpha_intercept + (beta_spy * aligned_rets["spy"]) + (beta_sector * aligned_rets["sector"])
        else:
            predicted = alpha_intercept + (beta_spy * aligned_rets["spy"])

        idiosyncratic_res = (aligned_rets["stock"] - predicted).values
        cum_res = np.cumsum(idiosyncratic_res)

        # Ornstein-Uhlenbeck s-score over trailing 20-day window
        window = min(20, len(cum_res))
        rolling_slice = cum_res[-window:]
        mu_res = float(np.mean(rolling_slice))
        sigma_res = float(np.std(rolling_slice))
        
        if sigma_res > 1e-6:
            s_score = float((cum_res[-1] - mu_res) / sigma_res)
        else:
            s_score = 0.0

        # 30-day idiosyncratic spread in percent
        alpha_spread_pct = float(cum_res[-1] * 100)

        # Interpret s-Score
        if s_score < -1.5:
            regime = "STAT-ARB OVERSOLD (BULLISH DIVERGENCE)"
            regime_badge = "OVERSOLD DIVERGENCE"
            regime_color = "#00e676"  # Emerald green
            summary = (
                f"{clean_sym} is lagging its sector ({sector_etf}) and SPY by {abs(s_score):.2f} standard deviations (s-score: {s_score:.2f}). "
                f"Stat-Arb models classify this as temporary idiosyncratic undervaluation primed for mean-reversion catch-up."
            )
        elif s_score > 1.5:
            regime = "STAT-ARB OVERBOUGHT (BEARISH EXHAUSTION)"
            regime_badge = "OVERBOUGHT EXHAUSTION"
            regime_color = "#ff1744"  # Coral red
            summary = (
                f"{clean_sym} has outrun its sector ({sector_etf}) by +{s_score:.2f} standard deviations (s-score: +{s_score:.2f}). "
                f"Stat-Arb models caution that relative performance is stretched and susceptible to sector mean-reversion."
            )
        else:
            regime = "FACTOR NEUTRAL / FAIR VALUE"
            regime_badge = "SECTOR IN-LINE"
            regime_color = "#4facfe"  # Cyan blue
            summary = (
                f"{clean_sym} is trading in equilibrium with {sector_etf} and SPY (s-score: {s_score:+.2f} std dev). "
                f"Price action is driven primarily by systematic sector beta (Beta={beta_sector:.2f}) rather than company-specific divergence."
            )

        res_data = {
            "status": "ACTIVE",
            "ticker": clean_sym,
            "sector_etf": sector_etf,
            "beta_spy": round(beta_spy, 2),
            "beta_sector": round(beta_sector, 2),
            "s_score": round(s_score, 2),
            "regime": regime,
            "regime_badge": regime_badge,
            "regime_color": regime_color,
            "alpha_spread_pct": round(alpha_spread_pct, 2),
            "summary": summary
        }

        # Cache result
        _FACTOR_CACHE[clean_sym] = {
            "timestamp": now,
            "data": res_data
        }
        return res_data

    except Exception as e:
        logger.warning(f"Error computing factor neutralization for {clean_sym}: {e}")
        return fallback_res
