import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .indicators import enrich_dataframe

def run_strategy_backtest(df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
    """
    Backtests the confluence strategy against historical OHLCV data.
    Simulates ATR-based stop-loss and 1:2 risk-reward take-profit executions.
    """
    if df is None or len(df) < 50:
        return {
            "error": "Not enough historical bars to perform backtesting (minimum 50 bars required)."
        }
        
    df_en = enrich_dataframe(df)
    
    in_position = False
    pos_type = None # 'LONG'
    entry_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    entry_date = None
    
    trades: List[Dict[str, Any]] = []
    equity = initial_capital
    equity_curve = [initial_capital]
    
    # Iterate through candles starting from index 30 to allow indicator warmup
    for i in range(30, len(df_en)):
        row = df_en.iloc[i]
        date_str = str(df_en.index[i])[:10]
        c = float(row['Close'])
        h = float(row['High'])
        l = float(row['Low'])
        atr = float(row['ATR']) if not pd.isna(row['ATR']) else (c * 0.02)
        
        # If in position, check for TP or SL hit
        if in_position:
            pnl_pct = 0.0
            closed = False
            outcome = ""
            exit_price = c
            
            if pos_type == 'LONG':
                # Check Stop Loss first (worst case intra-candle)
                if l <= stop_loss:
                    exit_price = stop_loss
                    pnl_pct = (exit_price - entry_price) / entry_price
                    outcome = "STOP_LOSS"
                    closed = True
                # Check Take Profit
                elif h >= take_profit:
                    exit_price = take_profit
                    pnl_pct = (exit_price - entry_price) / entry_price
                    outcome = "TAKE_PROFIT"
                    closed = True
                    
            if closed:
                trade_pnl = equity * pnl_pct
                equity += trade_pnl
                equity_curve.append(round(equity, 2))
                trades.append({
                    "entry_date": entry_date,
                    "exit_date": date_str,
                    "type": pos_type,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "pnl_pct": round(pnl_pct * 100, 2),
                    "pnl_amount": round(trade_pnl, 2),
                    "outcome": outcome,
                    "equity": round(equity, 2)
                })
                in_position = False
                pos_type = None
                continue

        # If not in position, check for entry signals
        if not in_position:
            # Entry condition: Supertrend bullish + EMA21 > EMA50 + RSI between 45 and 68 + MACD Hist > 0
            st_trend = row['Supertrend_Trend']
            ema21 = row['EMA_21']
            ema50 = row['EMA_50']
            rsi = row['RSI']
            macd_h = row['MACD_Hist']
            
            if st_trend == 1 and ema21 > ema50 and 45 <= rsi <= 68 and macd_h > 0:
                in_position = True
                pos_type = 'LONG'
                entry_price = c
                entry_date = date_str
                stop_loss = entry_price - (1.5 * atr)
                risk = entry_price - stop_loss
                take_profit = entry_price + (2.0 * risk) # 1:2 R/R

    # Compute aggregate stats
    total_trades = len(trades)
    winning_trades = [t for t in trades if t['pnl_amount'] > 0]
    losing_trades = [t for t in trades if t['pnl_amount'] < 0]
    
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
    total_gain = sum(t['pnl_amount'] for t in winning_trades)
    total_loss = abs(sum(t['pnl_amount'] for t in losing_trades))
    profit_factor = (total_gain / total_loss) if total_loss > 0 else (99.0 if total_gain > 0 else 1.0)
    net_return_pct = ((equity - initial_capital) / initial_capital) * 100
    
    # Buy & hold benchmark
    first_close = float(df_en.iloc[30]['Close'])
    last_close = float(df_en.iloc[-1]['Close'])
    buy_and_hold_return_pct = ((last_close - first_close) / first_close) * 100

    # Max drawdown
    peak = initial_capital
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd

    return {
        "initial_capital": initial_capital,
        "final_capital": round(equity, 2),
        "net_return_pct": round(net_return_pct, 2),
        "buy_and_hold_return_pct": round(buy_and_hold_return_pct, 2),
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate_pct": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "recent_trades": trades[-20:],   # Last 20 for display
        "all_trades": trades,            # Full trade log
        "equity_curve": equity_curve     # Full equity curve for chart
    }
