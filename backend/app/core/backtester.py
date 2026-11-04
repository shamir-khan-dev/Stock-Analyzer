import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .indicators import enrich_dataframe

def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calculates peak-to-trough maximum drawdown percentage."""
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        if peak > 0:
            dd = (peak - eq) / peak * 100.0
            if dd > max_dd:
                max_dd = dd
    return round(float(max_dd), 2)

def calculate_sharpe_ratio(equity_curve: List[float], risk_free_rate: float = 0.04) -> float:
    """Calculates annualized Sharpe ratio from an equity series."""
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    arr = np.array(equity_curve, dtype=np.float64)
    returns = np.diff(arr) / arr[:-1]
    if len(returns) == 0:
        return 0.0
    std = float(np.std(returns))
    if std == 0 or np.isnan(std):
        return 0.0
    rf_daily = risk_free_rate / 252.0
    excess_mean = float(np.mean(returns) - rf_daily)
    sharpe = (excess_mean / std) * np.sqrt(252.0)
    return round(float(sharpe), 2)

def calculate_sortino_ratio(equity_curve: List[float], risk_free_rate: float = 0.04) -> float:
    """Calculates annualized Sortino ratio penalizing only downside volatility."""
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    arr = np.array(equity_curve, dtype=np.float64)
    returns = np.diff(arr) / arr[:-1]
    if len(returns) == 0:
        return 0.0
    rf_daily = risk_free_rate / 252.0
    excess_returns = returns - rf_daily
    downside = excess_returns[excess_returns < 0]
    if len(downside) == 0:
        return 99.0 if np.mean(excess_returns) > 0 else 0.0
    downside_dev = float(np.sqrt(np.mean(np.square(downside))))
    if downside_dev == 0 or np.isnan(downside_dev):
        return 0.0
    sortino = (float(np.mean(excess_returns)) / downside_dev) * np.sqrt(252.0)
    return round(float(sortino), 2)

def run_strategy_backtest(df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
    """
    Backtests the AlphaPulse confluence strategy against historical OHLCV data.
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
                if l <= stop_loss:
                    exit_price = stop_loss
                    pnl_pct = (exit_price - entry_price) / entry_price
                    outcome = "STOP_LOSS"
                    closed = True
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

    max_dd = calculate_max_drawdown(equity_curve)
    sharpe = calculate_sharpe_ratio(equity_curve)
    sortino = calculate_sortino_ratio(equity_curve)
    calmar = round(net_return_pct / max_dd, 2) if max_dd > 0 else (99.0 if net_return_pct > 0 else 0.0)

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
        "max_drawdown_pct": max_dd,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "recent_trades": trades[-20:],
        "all_trades": trades,
        "equity_curve": equity_curve
    }

def run_comparative_backtest(df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
    """
    Simulates and compares 3 systematic strategies side-by-side:
    1. AlphaPulse Multi-Factor Confluence (Supertrend + EMA21/50 + ATR dynamic risk)
    2. Buy & Hold Benchmark (Passive index buy at bar 30)
    3. Golden Cross / Moving Average Trend (Fast SMA vs Slow SMA with ATR exit)
    """
    if df is None or len(df) < 50:
        return {
            "error": "Not enough historical bars to perform comparative backtesting (minimum 50 bars required)."
        }

    # 1. Run AlphaPulse Confluence
    strat_alphapulse = run_strategy_backtest(df, initial_capital=initial_capital)
    
    # 2. Run Buy & Hold Benchmark
    df_en = enrich_dataframe(df)
    first_close = float(df_en.iloc[30]['Close'])
    bh_closes = df_en.iloc[30:]['Close'].values
    bh_equity_curve = [round(float(initial_capital * (c / first_close)), 2) for c in bh_closes]
    bh_final = bh_equity_curve[-1]
    bh_net_return = round(((bh_final - initial_capital) / initial_capital) * 100.0, 2)
    bh_max_dd = calculate_max_drawdown(bh_equity_curve)
    bh_sharpe = calculate_sharpe_ratio(bh_equity_curve)
    bh_sortino = calculate_sortino_ratio(bh_equity_curve)

    strat_buy_and_hold = {
        "strategy_name": "Buy & Hold (Passive Benchmark)",
        "initial_capital": initial_capital,
        "final_capital": bh_final,
        "net_return_pct": bh_net_return,
        "max_drawdown_pct": bh_max_dd,
        "sharpe_ratio": bh_sharpe,
        "sortino_ratio": bh_sortino,
        "total_trades": 1,
        "win_rate_pct": 100.0 if bh_net_return > 0 else 0.0,
        "profit_factor": 99.0 if bh_net_return > 0 else 0.0,
        "equity_curve": bh_equity_curve
    }

    # 3. Run Golden Cross Strategy (EMA 21 > EMA 50 trend following)
    gc_equity = initial_capital
    gc_equity_curve = [initial_capital]
    gc_trades = []
    gc_in_pos = False
    gc_entry = 0.0

    for i in range(30, len(df_en)):
        row = df_en.iloc[i]
        c = float(row['Close'])
        fast_ma = float(row['EMA_21'])
        slow_ma = float(row['EMA_50'])

        if gc_in_pos:
            # Exit condition: Bearish cross fast below slow
            if fast_ma < slow_ma:
                pnl_pct = (c - gc_entry) / gc_entry
                trade_pnl = gc_equity * pnl_pct
                gc_equity += trade_pnl
                gc_equity_curve.append(round(gc_equity, 2))
                gc_trades.append({"pnl_pct": round(pnl_pct * 100, 2), "pnl_amount": round(trade_pnl, 2)})
                gc_in_pos = False
        else:
            # Entry condition: Bullish cross fast above slow
            if fast_ma > slow_ma:
                gc_in_pos = True
                gc_entry = c

    gc_wins = [t for t in gc_trades if t['pnl_amount'] > 0]
    gc_losses = [t for t in gc_trades if t['pnl_amount'] < 0]
    gc_win_rate = (len(gc_wins) / len(gc_trades) * 100.0) if gc_trades else 0.0
    gc_gain = sum(t['pnl_amount'] for t in gc_wins)
    gc_loss = abs(sum(t['pnl_amount'] for t in gc_losses))
    gc_pf = (gc_gain / gc_loss) if gc_loss > 0 else (99.0 if gc_gain > 0 else 1.0)
    gc_return = round(((gc_equity - initial_capital) / initial_capital) * 100.0, 2)
    gc_max_dd = calculate_max_drawdown(gc_equity_curve)
    gc_sharpe = calculate_sharpe_ratio(gc_equity_curve)
    gc_sortino = calculate_sortino_ratio(gc_equity_curve)

    strat_golden_cross = {
        "strategy_name": "Moving Average Trend Following",
        "initial_capital": initial_capital,
        "final_capital": round(gc_equity, 2),
        "net_return_pct": gc_return,
        "max_drawdown_pct": gc_max_dd,
        "sharpe_ratio": gc_sharpe,
        "sortino_ratio": gc_sortino,
        "total_trades": len(gc_trades),
        "win_rate_pct": round(gc_win_rate, 1),
        "profit_factor": round(gc_pf, 2),
        "equity_curve": gc_equity_curve
    }

    strategies = {
        "alphapulse_confluence": strat_alphapulse,
        "buy_and_hold": strat_buy_and_hold,
        "golden_cross": strat_golden_cross
    }

    # Comparison summary scorecard
    comparison_table = [
        {
            "strategy": "AlphaPulse Confluence",
            "net_return_pct": strat_alphapulse["net_return_pct"],
            "sharpe_ratio": strat_alphapulse["sharpe_ratio"],
            "sortino_ratio": strat_alphapulse["sortino_ratio"],
            "max_drawdown_pct": strat_alphapulse["max_drawdown_pct"],
            "win_rate_pct": strat_alphapulse["win_rate_pct"],
            "trades": strat_alphapulse["total_trades"]
        },
        {
            "strategy": "Buy & Hold (Benchmark)",
            "net_return_pct": strat_buy_and_hold["net_return_pct"],
            "sharpe_ratio": strat_buy_and_hold["sharpe_ratio"],
            "sortino_ratio": strat_buy_and_hold["sortino_ratio"],
            "max_drawdown_pct": strat_buy_and_hold["max_drawdown_pct"],
            "win_rate_pct": strat_buy_and_hold["win_rate_pct"],
            "trades": strat_buy_and_hold["total_trades"]
        },
        {
            "strategy": "Moving Average Trend",
            "net_return_pct": strat_golden_cross["net_return_pct"],
            "sharpe_ratio": strat_golden_cross["sharpe_ratio"],
            "sortino_ratio": strat_golden_cross["sortino_ratio"],
            "max_drawdown_pct": strat_golden_cross["max_drawdown_pct"],
            "win_rate_pct": strat_golden_cross["win_rate_pct"],
            "trades": strat_golden_cross["total_trades"]
        }
    ]

    alpha = round(strat_alphapulse["net_return_pct"] - bh_net_return, 2)
    dd_mitigation = round(bh_max_dd - strat_alphapulse["max_drawdown_pct"], 2)

    # Determine best performing strategy by Sharpe (risk-adjusted return)
    best_strat = max(comparison_table, key=lambda s: s["sharpe_ratio"])["strategy"]

    return {
        "strategies": strategies,
        "comparison_table": comparison_table,
        "alpha_vs_buy_and_hold": alpha,
        "drawdown_mitigation_vs_benchmark": dd_mitigation,
        "best_performing_strategy": best_strat
    }
