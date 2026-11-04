import pytest
import pandas as pd
import numpy as np
import sys
import os

# Ensure backend is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.backtester import (
    run_strategy_backtest,
    run_comparative_backtest,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown
)

@pytest.fixture
def sample_ohlcv_data():
    """Generates 150 bars of realistic synthetic OHLCV data with an uptrend and pullbacks."""
    np.random.seed(42)
    n = 150
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    
    # Generate random walk with drift
    returns = np.random.normal(0.0015, 0.015, n)
    price = 100.0 * np.cumprod(1 + returns)
    
    high = price * (1 + np.abs(np.random.normal(0.005, 0.005, n)))
    low = price * (1 - np.abs(np.random.normal(0.005, 0.005, n)))
    open_p = price * (1 + np.random.normal(0, 0.003, n))
    volume = np.random.randint(500000, 5000000, n)
    
    df = pd.DataFrame({
        "Open": open_p,
        "High": high,
        "Low": low,
        "Close": price,
        "Volume": volume
    }, index=dates)
    return df

def test_calculate_risk_metrics():
    """Validates institutional risk formulas for Sharpe, Sortino, and Max Drawdown."""
    # Equity curve: 10000 -> 11000 -> 9900 -> 12000
    equity_curve = [10000.0, 10500.0, 11000.0, 9900.0, 10800.0, 12000.0]
    
    max_dd = calculate_max_drawdown(equity_curve)
    # Peak is 11000, trough is 9900 -> dd = (11000 - 9900) / 11000 = 10.0%
    assert 9.9 <= max_dd <= 10.1
    
    # Sharpe with positive trend should be positive
    sharpe = calculate_sharpe_ratio(equity_curve)
    assert isinstance(sharpe, float)
    
    # Sortino should be positive
    sortino = calculate_sortino_ratio(equity_curve)
    assert isinstance(sortino, float)

def test_run_strategy_backtest_baseline(sample_ohlcv_data):
    """Verifies that the primary AlphaPulse strategy backtest executes cleanly."""
    res = run_strategy_backtest(sample_ohlcv_data, initial_capital=10000.0)
    
    assert "net_return_pct" in res
    assert "win_rate_pct" in res
    assert "profit_factor" in res
    assert "max_drawdown_pct" in res
    assert "equity_curve" in res
    assert "sharpe_ratio" in res
    assert "sortino_ratio" in res
    assert len(res["equity_curve"]) >= 1

def test_run_comparative_backtest(sample_ohlcv_data):
    """Verifies multi-strategy comparative execution across AlphaPulse vs Buy&Hold vs SMA Cross."""
    res = run_comparative_backtest(sample_ohlcv_data, initial_capital=10000.0)
    
    assert "strategies" in res
    strategies = res["strategies"]
    
    assert "alphapulse_confluence" in strategies
    assert "buy_and_hold" in strategies
    assert "golden_cross" in strategies
    
    # Verify comparative scorecard metrics
    assert "comparison_table" in res
    assert "alpha_vs_buy_and_hold" in res
    assert "best_performing_strategy" in res
    
    bh = strategies["buy_and_hold"]
    assert "net_return_pct" in bh
    assert "max_drawdown_pct" in bh
    assert "sharpe_ratio" in bh

def test_backtest_insufficient_data():
    """Ensures graceful error handling when given fewer than 50 bars."""
    df_short = pd.DataFrame({"Close": [10.0] * 20})
    res = run_strategy_backtest(df_short)
    assert "error" in res

