import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import patch
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_ohlcv():
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    prices = 150.0 + np.cumsum(np.random.normal(0.5, 2.0, n))
    return pd.DataFrame({
        "Open": prices,
        "High": prices + 2.0,
        "Low": prices - 2.0,
        "Close": prices,
        "Volume": [1000000] * n
    }, index=dates)

def test_backtest_endpoint_success(mock_ohlcv):
    with patch("app.api.routes_backtest.fetch_history_data", return_value=mock_ohlcv):
        response = client.get("/api/backtest/NVDA?period=1y&capital=10000")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "NVDA"
        assert "net_return_pct" in data
        assert "sharpe_ratio" in data
        assert "sortino_ratio" in data
        assert "win_rate_pct" in data

def test_comparative_backtest_endpoint_success(mock_ohlcv):
    with patch("app.api.routes_backtest.fetch_history_data", return_value=mock_ohlcv):
        response = client.get("/api/backtest/NVDA/comparative?period=1y&capital=10000")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "NVDA"
        assert "strategies" in data
        assert "comparison_table" in data
        assert "alpha_vs_buy_and_hold" in data
        assert "best_performing_strategy" in data

def test_backtest_endpoint_not_found():
    with patch("app.api.routes_backtest.fetch_history_data", return_value=None):
        response = client.get("/api/backtest/INVALID?period=1y")
        assert response.status_code == 404

