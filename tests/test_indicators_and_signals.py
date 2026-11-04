import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_supertrend,
    enrich_dataframe,
    calculate_pivot_points
)

@pytest.fixture
def synthetic_series():
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    prices = 100.0 + np.cumsum(np.random.normal(0.2, 1.0, n))
    highs = prices + np.abs(np.random.normal(0.5, 0.3, n))
    lows = prices - np.abs(np.random.normal(0.5, 0.3, n))
    opens = prices + np.random.normal(0, 0.2, n)
    volumes = np.random.randint(100000, 1000000, n)
    
    df = pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": prices,
        "Volume": volumes
    }, index=dates)
    return df

def test_ema_computation(synthetic_series):
    close = synthetic_series["Close"]
    ema20 = calculate_ema(close, 20)
    assert len(ema20) == len(close)
    assert not ema20.isna().all()
    # EMA follows close price direction
    assert np.isclose(ema20.iloc[-1], close.iloc[-1], atol=10.0)

def test_rsi_bounds(synthetic_series):
    close = synthetic_series["Close"]
    rsi = calculate_rsi(close, 14)
    valid_rsi = rsi.dropna()
    assert len(valid_rsi) > 0
    assert (valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all()

def test_macd_calculation(synthetic_series):
    close = synthetic_series["Close"]
    macd, signal, hist = calculate_macd(close)
    assert len(macd) == len(close)
    assert len(signal) == len(close)
    assert len(hist) == len(close)
    # Histogram equals MACD minus Signal
    diff = hist.dropna() - (macd.dropna() - signal.dropna())
    assert np.allclose(diff, 0.0, atol=1e-5)

def test_bollinger_bands(synthetic_series):
    close = synthetic_series["Close"]
    upper, mid, lower, bw, pct_b = calculate_bollinger_bands(close)
    valid_idx = ~(upper.isna() | lower.isna())
    # Upper band must be greater than lower band
    assert (upper[valid_idx] >= lower[valid_idx]).all()

def test_atr_volatility(synthetic_series):
    atr = calculate_atr(synthetic_series, 14)
    valid_atr = atr.dropna()
    assert (valid_atr > 0.0).all()

def test_supertrend(synthetic_series):
    st_val, st_trend = calculate_supertrend(synthetic_series)
    assert len(st_val) == len(synthetic_series)
    # Supertrend trend flag must be 1 (bullish) or -1 (bearish)
    valid_trends = st_trend.dropna().unique()
    for val in valid_trends:
        assert val in [1, -1]

def test_enrich_dataframe_schema(synthetic_series):
    enriched = enrich_dataframe(synthetic_series)
    required_cols = [
        "EMA_21", "EMA_50", "EMA_200", "RSI", "MACD", "MACD_Signal",
        "MACD_Hist", "BB_Upper", "BB_Lower", "ATR", "Supertrend", "Supertrend_Trend"
    ]
    for col in required_cols:
        assert col in enriched.columns, f"Missing required column: {col}"

def test_pivot_points(synthetic_series):
    pivots = calculate_pivot_points(synthetic_series)
    assert "P" in pivots
    assert "R1" in pivots
    assert "S1" in pivots
    assert pivots["R1"] >= pivots["P"]
    assert pivots["S1"] <= pivots["P"]
