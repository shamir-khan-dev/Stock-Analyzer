import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.core.data_fetcher import fetch_history_data, fetch_live_quote
from app.core.quant_engine import analyze_ticker_confluence
from app.core.backtester import run_strategy_backtest
from app.vision.chart_vision import process_chart_image
import numpy as np
from PIL import Image
import io
import base64

def test_pipeline():
    print("Testing data fetch for AAPL...")
    df = fetch_history_data("AAPL", period="3mo", interval="1d")
    assert df is not None and not df.empty, "DataFrame should not be empty"
    print(f"Data fetched successfully: {len(df)} candles.")

    print("Testing quant confluence analysis...")
    analysis = analyze_ticker_confluence(df, "AAPL")
    assert "verdict" in analysis, "Analysis must have verdict"
    print(f"Verdict: {analysis['verdict']} | Score: {analysis['confluence_score']} | Action: {analysis['action']}")
    print(f"Trade setup: Entry={analysis['trade_setup']['entry_price']}, StopLoss={analysis['trade_setup']['stop_loss']}, TP1={analysis['trade_setup']['take_profit_1']}")

    print("Testing backtesting engine...")
    bt = run_strategy_backtest(df)
    assert "win_rate_pct" in bt, "Backtest must return win rate"
    print(f"Backtest completed: Total Trades={bt['total_trades']}, Win Rate={bt['win_rate_pct']}%, Net Return={bt['net_return_pct']}%")

    print("Testing chart vision with synthetic candlestick image...")
    # Generate a small synthetic chart image (green and red bars)
    synth = np.zeros((300, 500, 3), dtype=np.uint8)
    # Green candle
    synth[100:200, 150:180] = [0, 230, 118]
    # Red candle
    synth[150:240, 250:280] = [255, 23, 68]
    
    img = Image.fromarray(synth)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    vision_res = process_chart_image(b64_str)
    assert "verdict" in vision_res, "Vision analysis must return verdict"
    print(f"Vision Verdict: {vision_res['verdict']} | Confidence: {vision_res['confidence_pct']}%")
    print("All core engine unit tests passed successfully!")

if __name__ == "__main__":
    test_pipeline()
