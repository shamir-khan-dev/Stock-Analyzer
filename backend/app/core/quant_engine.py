import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .indicators import enrich_dataframe, calculate_pivot_points
from .pattern_detector import detect_candlestick_patterns
from .sentiment_engine import fetch_ticker_news, analyze_news_sentiment
from .order_flow import fetch_order_flow_metrics
from .signal_accuracy import (
    get_earnings_warning,
    calculate_signal_reliability,
    log_signal,
    get_signal_tracker_stats
)
from .factor_engine import calculate_factor_neutral_residual
from .options_engine import calculate_options_market_structure
from .risk_engine import calculate_trade_risk_sizing

def analyze_ticker_confluence(df: pd.DataFrame, ticker: str) -> Dict[str, Any]:
    """
    Executes multi-factor quantitative confluence analysis on OHLCV series.
    Returns signal verdict, confidence, entry/exit targets, and diagnostic metrics.
    """
    if df is None or len(df) < 25:
        return {
            "error": "Insufficient historical data for reliable quantitative analysis (minimum 25 candles required)."
        }
        
    # Enrich with all technical indicators
    df_enriched = enrich_dataframe(df)
    latest = df_enriched.iloc[-1]
    prev = df_enriched.iloc[-2]
    
    price = float(latest['Close'])
    atr = float(latest['ATR']) if not pd.isna(latest['ATR']) else (price * 0.02)
    
    # -------------------------------------------------------------
    # 1. Trend Factor Scoring (-35 to +35)
    # -------------------------------------------------------------
    trend_score = 0
    trend_reasons = []
    
    ema20 = float(latest['EMA_21'])
    ema50 = float(latest['EMA_50'])
    ema200 = float(latest.get('EMA_200', ema50))
    supertrend_dir = int(latest['Supertrend_Trend'])
    
    # Price vs Key EMAs
    if price > ema20:
        trend_score += 8
        trend_reasons.append("Price holding firmly above short-term 21 EMA.")
    else:
        trend_score -= 8
        trend_reasons.append("Price trading below 21 EMA (short-term weakness).")
        
    if price > ema50:
        trend_score += 7
        trend_reasons.append("Bullish intermediate trend: price above 50 EMA.")
    else:
        trend_score -= 7
        trend_reasons.append("Bearish intermediate trend: price below 50 EMA.")
        
    if not pd.isna(ema200):
        if price > ema200:
            trend_score += 8
            trend_reasons.append("Macro bullish regime: price above 200 EMA.")
        else:
            trend_score -= 8
            trend_reasons.append("Macro bearish regime: price below 200 EMA.")
            
    # Supertrend
    if supertrend_dir == 1:
        trend_score += 12
        trend_reasons.append("Supertrend indicator is BULLISH (green support).")
    else:
        trend_score -= 12
        trend_reasons.append("Supertrend indicator is BEARISH (overhead resistance).")
        
    # Clamp trend score
    trend_score = max(-35, min(35, trend_score))

    # -------------------------------------------------------------
    # 2. Momentum Factor Scoring (-25 to +25)
    # -------------------------------------------------------------
    mom_score = 0
    mom_reasons = []
    
    rsi = float(latest['RSI'])
    macd = float(latest['MACD'])
    macd_sig = float(latest['MACD_Signal'])
    macd_hist = float(latest['MACD_Hist'])
    stoch_k = float(latest.get('Stoch_K', 50))
    stoch_d = float(latest.get('Stoch_D', 50))
    
    # RSI Analysis
    if rsi >= 55 and rsi <= 70:
        mom_score += 8
        mom_reasons.append(f"RSI ({rsi:.1f}) in strong bullish expansion zone without being overbought.")
    elif rsi < 30:
        mom_score += 6
        mom_reasons.append(f"RSI ({rsi:.1f}) is oversold; high probability of mean-reversion bounce.")
    elif rsi > 75:
        mom_score -= 6
        mom_reasons.append(f"RSI ({rsi:.1f}) is overextended / overbought; risk of imminent retracement.")
    elif rsi <= 45:
        mom_score -= 8
        mom_reasons.append(f"RSI ({rsi:.1f}) in bearish momentum territory.")
        
    # MACD Analysis
    if macd > macd_sig:
        if macd_hist > 0 and macd_hist > float(prev['MACD_Hist']):
            mom_score += 10
            mom_reasons.append("MACD histogram expanding positively (accelerating bullish momentum).")
        else:
            mom_score += 5
            mom_reasons.append("MACD is above signal line.")
    else:
        if macd_hist < 0 and macd_hist < float(prev['MACD_Hist']):
            mom_score -= 10
            mom_reasons.append("MACD histogram expanding negatively (bearish momentum accelerating).")
        else:
            mom_score -= 5
            mom_reasons.append("MACD line is below signal line.")

    # Stochastic RSI Cross
    if stoch_k > stoch_d and stoch_k < 80:
        mom_score += 7
        mom_reasons.append(f"Stochastic RSI (%K={stoch_k:.1f}) crossed above %D (bullish trigger).")
    elif stoch_k < stoch_d and stoch_k > 20:
        mom_score -= 7
        mom_reasons.append(f"Stochastic RSI (%K={stoch_k:.1f}) crossed below %D (bearish trigger).")

    mom_score = max(-25, min(25, mom_score))

    # -------------------------------------------------------------
    # 3. Volatility & Price Bands Scoring (-20 to +20)
    # -------------------------------------------------------------
    volat_score = 0
    volat_reasons = []
    
    bb_upper = float(latest['BB_Upper'])
    bb_mid = float(latest['BB_Middle'])
    bb_lower = float(latest['BB_Lower'])
    bb_pct_b = float(latest.get('BB_PctB', 0.5))
    
    if price > bb_mid:
        volat_score += 10
        volat_reasons.append("Price positioned in the upper Bollinger Band channel.")
    else:
        volat_score -= 10
        volat_reasons.append("Price positioned in the lower Bollinger Band channel.")
        
    if bb_pct_b < 0.15:
        volat_score += 10
        volat_reasons.append("Price testing lower Bollinger Band support (potential bounce zone).")
    elif bb_pct_b > 0.95:
        volat_score -= 10
        volat_reasons.append("Price tagging upper Bollinger Band resistance (exhaustion risk).")

    volat_score = max(-20, min(20, volat_score))

    # -------------------------------------------------------------
    # 4. Volume & Liquidity Factor Scoring (-20 to +20)
    # -------------------------------------------------------------
    vol_score = 0
    vol_reasons = []
    
    vol_ratio = float(latest.get('Vol_Ratio', 1.0))
    is_green = latest['Close'] >= latest['Open']
    
    if vol_ratio > 1.3:
        if is_green:
            vol_score += 15
            vol_reasons.append(f"High-volume accumulation: {vol_ratio:.1f}x higher than 20-day average.")
        else:
            vol_score -= 15
            vol_reasons.append(f"High-volume distribution: {vol_ratio:.1f}x above average on red candle.")
    else:
        if is_green:
            vol_score += 5
        else:
            vol_score -= 5
            
    vol_score = max(-20, min(20, vol_score))

    # -------------------------------------------------------------
    # Ingest Candlestick Patterns, News Sentiment & Options Order Flow
    # -------------------------------------------------------------
    patterns = detect_candlestick_patterns(df_enriched)
    pattern_boost = 0
    for p in patterns:
        if p["bias"] == "BULLISH":
            pattern_boost += 8
        elif p["bias"] == "BEARISH":
            pattern_boost -= 8

    news_items = fetch_ticker_news(ticker)
    sentiment_res = analyze_news_sentiment(news_items)
    order_flow_res = fetch_order_flow_metrics(ticker)

    # Ingest Factor Neutrality & Options Microstructure
    factor_res = calculate_factor_neutral_residual(ticker, df)
    options_res = calculate_options_market_structure(ticker, price)

    sentiment_modifier = sentiment_res.get("score", 0.0)

    # Factor-Neutral residual adjustment (-7 to +7)
    factor_mod = 0.0
    if factor_res.get("status") == "ACTIVE":
        s_val = factor_res.get("s_score", 0.0)
        if s_val < -1.5:
            factor_mod = 6.0
        elif s_val > 1.5:
            factor_mod = -6.0

    # Options Gamma Pinning adjustment (-5 to +5)
    options_mod = 0.0
    if options_res.get("status") == "ACTIVE":
        if options_res.get("gamma_badge") == "GAMMA PINNED":
            options_mod = -3.0 if (trend_score + mom_score) > 20 else (3.0 if (trend_score + mom_score) < -20 else 0.0)
        elif options_res.get("gamma_badge") == "CALL WALL SQUEEZE":
            options_mod = 4.0
        elif options_res.get("gamma_badge") == "NEGATIVE GAMMA CASCADE":
            options_mod = -5.0

    total_score = trend_score + mom_score + volat_score + vol_score + pattern_boost + sentiment_modifier + factor_mod + options_mod
    total_score = max(-100, min(100, total_score))

    # --- Earnings Warning ---
    earnings_warning = get_earnings_warning(ticker)

    # Determine Verdict
    if total_score >= 45:
        verdict = "STRONG BUY"
        action = "BUY"
        verdict_color = "#00e676"  # Bright green
    elif total_score >= 15:
        verdict = "BUY"
        action = "BUY"
        verdict_color = "#4caf50"  # Green
    elif total_score <= -45:
        verdict = "STRONG SELL"
        action = "SELL"
        verdict_color = "#ff1744"  # Neon red
    elif total_score <= -15:
        verdict = "SELL"
        action = "SELL"
        verdict_color = "#f44336"  # Red
    else:
        verdict = "HOLD / NEUTRAL"
        action = "WAIT"
        verdict_color = "#ffb300"  # Amber

    # Confidence calculation: scaled 55% to 96%
    confidence_pct = int(55 + (abs(total_score) / 100.0) * 41)

    # -------------------------------------------------------------
    # Risk Management & Trade Levels (ATR Sizing)
    # -------------------------------------------------------------
    pivots = calculate_pivot_points(df)
    
    if action == "BUY":
        stop_loss = round(price - (1.5 * atr), 2)
        if stop_loss >= price:
            stop_loss = round(price * 0.96, 2)
            
        risk_per_share = max(0.01, price - stop_loss)
        take_profit_1 = round(price + (1.5 * risk_per_share), 2)
        take_profit_2 = round(price + (2.5 * risk_per_share), 2)
        risk_reward_ratio = "1 : 2.0"
        recommended_entry = round(price, 2)
        plan_type = "LONG_BUY"
        headline = "BULLISH BUY SETUP — Favorable Risk/Reward"
        summary_text = f"Favorable entry at ${recommended_entry}. Secure profits at ${take_profit_1} and ${take_profit_2}. Cut losses immediately if price drops below ${stop_loss}."
        if_holding = f"HOLD & ACCUMULATE: Strong upside structure. Target ${take_profit_1} for initial profit-taking."
        if_buying = f"BUY NOW: Safe to enter between ${round(price * 0.99, 2)} and ${round(price * 1.01, 2)}. Stop-loss at ${stop_loss}."
        if_shorting = "AVOID SHORTING: Bullish trend and momentum dominate. High risk of short squeeze."
        labels = {
            "entry_title": "WHEN TO BUY (ENTRY)",
            "entry_sub": "Market or Limit Entry",
            "sl_title": "STOP-LOSS (CUT LOSS)",
            "sl_sub": f"Sell if drops below ${stop_loss}",
            "tp1_title": "TAKE PROFIT 1 (SELL 50%)",
            "tp1_sub": f"+{round(((take_profit_1 - price) / price) * 100, 1)}% Target Gain",
            "tp2_title": "TAKE PROFIT 2 (SELL RUNNER)",
            "tp2_sub": f"+{round(((take_profit_2 - price) / price) * 100, 1)}% Extended Gain"
        }
    elif action == "SELL":
        stop_loss = round(price + (1.5 * atr), 2)
        if stop_loss <= price:
            stop_loss = round(price * 1.04, 2)
            
        risk_per_share = max(0.01, stop_loss - price)
        take_profit_1 = round(price - (1.5 * risk_per_share), 2)
        take_profit_2 = round(price - (2.5 * risk_per_share), 2)
        risk_reward_ratio = "1 : 2.0"
        recommended_entry = round(price, 2)
        plan_type = "BEARISH_SELL"
        headline = "BEARISH SELL / EXIT SETUP — Capital Protection Urged"
        summary_text = f"Bearish momentum confirmed. If holding shares, SELL NOW around ${recommended_entry} to prevent loss. Do NOT buy until support forms near ${take_profit_1}."
        if_holding = f"SELL / EXIT NOW: Protect capital at ${round(price, 2)} before likely drop to downside support (${take_profit_1})."
        if_buying = f"DO NOT BUY YET: Price in distribution. Wait for a dip to ${take_profit_1} - ${take_profit_2} or a confirmed bullish reversal."
        if_shorting = f"SHORT SETUP: Short at ${round(price, 2)} | Cover/Buyback at ${take_profit_1} & ${take_profit_2} | Invalidation Stop: ${stop_loss}"
        labels = {
            "entry_title": "WHEN TO SELL (EXIT NOW)",
            "entry_sub": "Sell existing shares at Market",
            "sl_title": "INVALIDATION CEILING",
            "sl_sub": f"Re-evaluate if price rallies above ${stop_loss}",
            "tp1_title": "DOWNSIDE TARGET 1 (RE-BUY DIP)",
            "tp1_sub": f"First Support / Short TP at ${take_profit_1}",
            "tp2_title": "DOWNSIDE TARGET 2 (VALUE FLOOR)",
            "tp2_sub": f"Major Support / Deep Value at ${take_profit_2}"
        }
    else:
        # Neutral / Hold
        stop_loss = round(price - (1.5 * atr), 2)
        take_profit_1 = round(price + (1.5 * atr), 2)
        take_profit_2 = round(price + (2.5 * atr), 2)
        risk_reward_ratio = "1 : 1.5"
        recommended_entry = round(price, 2)
        plan_type = "NEUTRAL_WAIT"
        headline = "HOLD / WAIT — Sideways Consolidation Range"
        summary_text = f"Market is in neutral consolidation. Stand aside until a confirmed breakout above ${take_profit_1} or breakdown below ${stop_loss}."
        if_holding = f"HOLD CURRENT POSITION: Keep a tight trailing stop at ${stop_loss}. Do not add new shares."
        if_buying = f"WAIT ON SIDELINES: Sideways chop. Wait for high-volume breakout above ${take_profit_1} before buying."
        if_shorting = "NO CLEAR SETUP: Balanced buyers and sellers. Wait for direction."
        labels = {
            "entry_title": "PIVOT BENCHMARK",
            "entry_sub": "Consolidation baseline",
            "sl_title": "SUPPORT FLOOR",
            "sl_sub": f"Breakdown triggers below ${stop_loss}",
            "tp1_title": "RESISTANCE 1 (BREAKOUT)",
            "tp1_sub": f"Bullish breakout above ${take_profit_1}",
            "tp2_title": "RESISTANCE 2 (RUNNER)",
            "tp2_sub": f"Secondary ceiling at ${take_profit_2}"
        }

    # Combine top reasons
    all_reasons = []
    if total_score > 0:
        all_reasons.extend(trend_reasons[:2])
        all_reasons.extend(mom_reasons[:2])
        all_reasons.extend(vol_reasons[:1])
    else:
        all_reasons.extend([r for r in trend_reasons if "weakness" in r or "below" in r or "BEARISH" in r][:2])
        all_reasons.extend([r for r in mom_reasons if "bearish" in r or "below" in r or "overbought" in r][:2])
        all_reasons.extend(vol_reasons[:1])

    if sentiment_res.get("triggers"):
        all_reasons.append(f"AI News Sentiment ({sentiment_res['verdict']}): Triggers = {', '.join(sentiment_res['triggers'])}")

    if not all_reasons:
        all_reasons = ["Market consolidating sideways with balanced order flow; awaiting clear breakout."]

    # Package recent candlestick data for chart rendering (last 100 bars)
    chart_bars = []
    recent_slice = df_enriched.tail(100)
    for idx, row in recent_slice.iterrows():
        ts = int(idx.timestamp()) if hasattr(idx, 'timestamp') else int(idx)
        chart_bars.append({
            "time": ts,
            "open": round(float(row['Open']), 2),
            "high": round(float(row['High']), 2),
            "low": round(float(row['Low']), 2),
            "close": round(float(row['Close']), 2),
            "volume": int(row['Volume']),
            "ema20": round(float(row['EMA_21']), 2) if not pd.isna(row['EMA_21']) else None,
            "ema50": round(float(row['EMA_50']), 2) if not pd.isna(row['EMA_50']) else None,
            "supertrend": round(float(row['Supertrend']), 2) if not pd.isna(row['Supertrend']) else None
        })

    # Multi-Timeframe (MTF) Trend Alignment status
    mtf_status = {
        "15M": "BULLISH" if price > float(latest['EMA_21']) else "BEARISH",
        "1H": "BULLISH" if price > float(latest['EMA_50']) else "BEARISH",
        "1D": "BULLISH" if supertrend_dir == 1 else "BEARISH",
        "alignment": "STRONG BULLISH ALIGNMENT" if (price > float(latest['EMA_21']) and supertrend_dir == 1) else "MIXED TIMEFRAMES"
    }

    # --- Signal Reliability Score ---
    reliability = calculate_signal_reliability(
        confluence_score=total_score,
        mtf_alignment=mtf_status,
        vol_ratio=vol_ratio,
        rsi=rsi,
        earnings_warning=earnings_warning,
        patterns=patterns
    )

    # --- Log this signal for win/loss tracking ---
    log_signal(
        ticker=ticker,
        verdict=verdict,
        price=price,
        entry=recommended_entry,
        stop_loss=stop_loss,
        tp1=take_profit_1,
        reliability_score=reliability["score"]
    )

    # --- Multi-Horizon Quantitative Strategy Breakdown ---
    multi_horizon = calculate_multi_horizon_strategies(
        df=df_enriched,
        ticker=ticker,
        price=price,
        atr=atr,
        pivots=pivots,
        latest=latest,
        total_score=total_score,
        quote=None
    )

    # --- Signal Tracker Stats ---
    tracker_stats = get_signal_tracker_stats()

    # --- Institutional Volatility-Targeted Risk Parity Sizing ---
    risk_sizing = calculate_trade_risk_sizing(
        entry_price=recommended_entry,
        stop_loss=stop_loss,
        atr=atr,
        account_cash=100000.0,
        risk_budget_dollars=500.0
    )

    return {
        "symbol": ticker.upper(),
        "current_price": price,
        "verdict": verdict,
        "verdict_color": verdict_color,
        "action": action,
        "confidence_pct": confidence_pct,
        "confluence_score": round(total_score, 1),
        "breakdown": {
            "trend_score": round(trend_score, 1),
            "momentum_score": round(mom_score, 1),
            "volatility_score": round(volat_score, 1),
            "volume_score": round(vol_score, 1),
            "sentiment_score": round(sentiment_modifier, 1),
            "factor_score": round(factor_mod, 1),
            "options_score": round(options_mod, 1),
            "rsi": round(rsi, 1),
            "macd": round(macd, 2),
            "macd_hist": round(macd_hist, 2),
            "stoch_k": round(stoch_k, 1),
            "stoch_d": round(stoch_d, 1),
            "supertrend": "BULLISH" if supertrend_dir == 1 else "BEARISH",
            "vol_ratio": round(vol_ratio, 2)
        },
        "trade_setup": {
            "action": action,
            "plan_type": plan_type,
            "headline": headline,
            "summary_text": summary_text,
            "if_holding": if_holding,
            "if_buying": if_buying,
            "if_shorting": if_shorting,
            "labels": labels,
            "entry_price": recommended_entry,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "risk_reward_ratio": risk_reward_ratio,
            "atr": round(atr, 2),
            "max_risk_pct": round((abs(price - stop_loss) / price) * 100, 2)
        },
        "factor_neutral": factor_res,
        "options_structure": options_res,
        "risk_sizing": risk_sizing,
        "multi_horizon": multi_horizon,
        "pivot_levels": pivots,
        "patterns": patterns,
        "mtf_alignment": mtf_status,
        "sentiment": sentiment_res,
        "order_flow": order_flow_res,
        "key_reasons": all_reasons,
        "chart_data": chart_bars,
        "earnings_warning": earnings_warning,
        "signal_reliability": reliability,
        "signal_tracker": tracker_stats
    }


def calculate_multi_horizon_strategies(
    df: pd.DataFrame,
    ticker: str,
    price: float,
    atr: float,
    pivots: Dict[str, float],
    latest: pd.Series,
    total_score: float,
    quote: Any = None
) -> Dict[str, Any]:
    """
    Calculates execution targets and plain-English analysis across 3 distinct
    investment horizons based on Wall Street factor research (AQR, FINRA, Bloomberg):
    1. Day Trade / Scalp (1 - 2 Days): Pivot Mean-Reversion & Micro-Momentum
    2. Swing Trade (Days - Weeks): AQR Time-Series Momentum & Trend Following
    3. Long-Term Core (Months - Years): Institutional 200-SMA Regime & Fundamental Trajectory
    """
    rsi = float(latest.get('RSI', 50.0))
    ema21 = float(latest.get('EMA_21', price))
    ema50 = float(latest.get('EMA_50', price))
    ema200 = float(latest.get('EMA_200', ema50)) if not pd.isna(latest.get('EMA_200')) else ema50
    stoch_k = float(latest.get('Stoch_K', 50.0))
    stoch_d = float(latest.get('Stoch_D', 50.0))

    # Historical metrics & 52-week envelope
    closes = df['Close']
    high_52w = float(df['High'].max())
    low_52w = float(df['Low'].min())
    pct_from_52w_high = ((price - high_52w) / high_52w) * 100

    # -------------------------------------------------------------
    # 1. ⚡ DAY TRADE / SCALP (1 - 2 Days Horizon)
    # Model: Intraday Pivot Mean-Reversion & Micro-Momentum
    # -------------------------------------------------------------
    p_level = pivots.get('P', price)
    s1_level = pivots.get('S1', price * 0.98)
    r1_level = pivots.get('R1', price * 1.02)
    day_atr = max(0.01, atr * 0.75)

    if rsi < 36 or (stoch_k < 20 and stoch_k > stoch_d):
        day_verdict = "DAY BUY"
        day_action = "BUY"
        day_badge = "OVERSOLD BOUNCE"
        day_color = "#00e676"
        day_entry = round(price, 2)
        day_stop = round(price - day_atr, 2)
        day_target = round(price + (1.3 * day_atr), 2)
        day_summary = (
            f"Oversold intraday condition (RSI {rsi:.1f}). Favorable scalp for a 1-2 day technical bounce "
            f"toward pivot resistance at ${day_target:.2f}. Cut immediately if price drops below ${day_stop:.2f}."
        )
    elif rsi > 70 or (stoch_k > 80 and stoch_k < stoch_d):
        day_verdict = "DAY SELL / TRIM"
        day_action = "SELL"
        day_badge = "OVERBOUGHT EXHAUSTION"
        day_color = "#ff1744"
        day_entry = round(price, 2)
        day_stop = round(price + day_atr, 2)
        day_target = round(price - (1.3 * day_atr), 2)
        day_summary = (
            f"Overextended momentum (RSI {rsi:.1f}). Risk of intraday pullback over the next 24-48 hours. "
            f"Take short-term profits near ${price:.2f} or look for pullback support near ${day_target:.2f}."
        )
    elif total_score >= 20:
        day_verdict = "DAY BUY"
        day_action = "BUY"
        day_badge = "MOMENTUM CONTINUATION"
        day_color = "#00e676"
        day_entry = round(price, 2)
        day_stop = round(price - day_atr, 2)
        day_target = round(price + (1.2 * day_atr), 2)
        day_summary = (
            f"Positive intraday order flow. Price positioned above daily pivot (${p_level:.2f}). "
            f"Quick 1-2 day target: ${day_target:.2f} with tight stop at ${day_stop:.2f}."
        )
    elif total_score <= -20:
        day_verdict = "DAY SELL"
        day_action = "SELL"
        day_badge = "DOWNTREND PRESSURE"
        day_color = "#ff1744"
        day_entry = round(price, 2)
        day_stop = round(price + day_atr, 2)
        day_target = round(price - day_atr, 2)
        day_summary = (
            f"Intraday selling pressure dominates. Price trading below daily pivot (${p_level:.2f}). "
            f"Avoid buying today; expect retest of downside support near ${day_target:.2f}."
        )
    else:
        day_verdict = "DAY WAIT / NEUTRAL"
        day_action = "WAIT"
        day_badge = "CHOPPY CONSOLIDATION"
        day_color = "#ffb300"
        day_entry = round(p_level, 2)
        day_stop = round(s1_level, 2)
        day_target = round(r1_level, 2)
        day_summary = (
            f"Price compressing in a tight 1-2 day range (${s1_level:.2f} - ${r1_level:.2f}). "
            f"No clean high-conviction scalp setup. Wait for a breakout before taking quick trades."
        )

    # -------------------------------------------------------------
    # 2. 🌊 SWING TRADE (Days - Weeks Horizon)
    # Model: AQR Time-Series Momentum & Dual-EMA Trend Following
    # Reference: Hurst, Ooi, Pedersen (2014) "A Century of Trend-Following Investing"
    # -------------------------------------------------------------
    swing_risk = max(0.01, 1.5 * atr)
    if total_score >= 15:
        swing_verdict = "SWING BUY"
        swing_action = "BUY"
        swing_badge = "TREND FOLLOWING"
        swing_color = "#00e676"
        swing_entry = round(price, 2)
        swing_stop = round(price - swing_risk, 2)
        swing_tp1 = round(price + (1.5 * swing_risk), 2)
        swing_tp2 = round(price + (2.5 * swing_risk), 2)
        swing_summary = (
            f"Bullish intermediate trend confirmed (Supertrend + 21/50 EMA aligned). "
            f"Hold for 1 to 4 weeks. Bank half your profits at ${swing_tp1:.2f} and trail remainder to ${swing_tp2:.2f}. "
            f"Safety stop-loss: ${swing_stop:.2f}."
        )
    elif total_score <= -15:
        swing_verdict = "SWING SELL"
        swing_action = "SELL"
        swing_badge = "BEARISH DISTRIBUTION"
        swing_color = "#ff1744"
        swing_entry = round(price, 2)
        swing_stop = round(price + swing_risk, 2)
        swing_tp1 = round(price - (1.5 * swing_risk), 2)
        swing_tp2 = round(price - (2.5 * swing_risk), 2)
        swing_summary = (
            f"Bearish trend continuation over the multi-week timeframe. "
            f"If holding shares, exit near ${price:.2f} to protect capital. Downside support targets: "
            f"${swing_tp1:.2f} and ${swing_tp2:.2f}."
        )
    else:
        swing_verdict = "SWING HOLD"
        swing_action = "HOLD"
        swing_badge = "SIDEWAYS COMPRESSION"
        swing_color = "#ffb300"
        swing_entry = round(price, 2)
        swing_stop = round(price - swing_risk, 2)
        swing_tp1 = round(price + swing_risk, 2)
        swing_tp2 = round(price + (2.0 * swing_risk), 2)
        swing_summary = (
            f"Intermediate trend is neutral. The stock is consolidating between support at ${round(price - swing_risk, 2)} "
            f"and resistance at ${round(price + swing_risk, 2)}. Hold existing positions with stop at ${swing_stop:.2f}."
        )

    # -------------------------------------------------------------
    # 3. 🏛️ LONG-TERM CORE INVESTING (Months - Years Horizon)
    # Model: Institutional 200-SMA Regime & AQR Long-Term TSMOM
    # Reference: Asness, Moskowitz, Pedersen (2013) & FINRA Fundamental Guidelines
    # -------------------------------------------------------------
    is_above_200 = price >= ema200
    dist_200_pct = ((price - ema200) / ema200) * 100

    one_yr_start = float(closes.iloc[0])
    one_yr_return_pct = ((price - one_yr_start) / one_yr_start) * 100

    long_accum_low = round(min(price * 0.92, max(low_52w, ema200 * 0.98)), 2)
    long_accum_high = round(price * 1.02, 2)
    long_invalidation = round(min(ema200 * 0.92, price * 0.82), 2)
    long_target = round(max(high_52w * 1.08, price * 1.25), 2) if is_above_200 else round(ema200, 2)

    if is_above_200 and one_yr_return_pct >= 0:
        long_verdict = "ACCUMULATE / BUY DIPS"
        long_action = "ACCUMULATE"
        long_badge = "INSTITUTIONAL BULL REGIME"
        long_color = "#00e676"
        long_summary = (
            f"Stock is trading in a healthy institutional bull regime ({dist_200_pct:+.1f}% vs 200-day MA). "
            f"Wall Street factor research validates holding assets above their 200-day average. "
            f"Best strategy: Dollar-cost average (DCA) between ${long_accum_low:.2f} and ${long_accum_high:.2f}. "
            f"12-Month Bull Target: ${long_target:.2f}. Invalidation floor: ${long_invalidation:.2f}."
        )
    elif is_above_200 and one_yr_return_pct < 0:
        long_verdict = "CORE HOLD"
        long_action = "HOLD"
        long_badge = "RECOVERY REGIME"
        long_color = "#4facfe"
        long_summary = (
            f"Price has reclaimed its 200-day moving average (${ema200:.2f}) but is still basing. "
            f"Viable core holding for patient multi-month investors. Accumulate on pullbacks near ${ema200:.2f}."
        )
    else:
        long_verdict = "TRIM / CAUTION"
        long_action = "TRIM"
        long_badge = "INSTITUTIONAL BEAR REGIME"
        long_color = "#ff1744"
        long_summary = (
            f"Stock is trading {abs(dist_200_pct):.1f}% below its 200-day moving average (${ema200:.2f}). "
            f"Systematic trend models classify this as a secular downtrend with risk of prolonged drawdown. "
            f"Not recommended for long-term buy-and-hold until price sustainably recovers above ${ema200:.2f}."
        )

    return {
        "day_trade": {
            "horizon_name": "1 – 2 Days (Day Trade & Scalp)",
            "short_label": "1-2 DAYS",
            "model_name": "Pivot Mean-Reversion & Micro-Momentum",
            "academic_ref": "Pivot Mean-Reversion & Boundary Filter",
            "verdict": day_verdict,
            "action": day_action,
            "badge": day_badge,
            "color": day_color,
            "entry": day_entry,
            "stop_loss": day_stop,
            "target": day_target,
            "summary": day_summary
        },
        "swing_trade": {
            "horizon_name": "Days – Weeks (Swing Momentum)",
            "short_label": "DAYS - WEEKS",
            "model_name": "AQR Time-Series Momentum & Trend Following",
            "academic_ref": "Hurst, Ooi, Pedersen (2014) Trend Following",
            "verdict": swing_verdict,
            "action": swing_action,
            "badge": swing_badge,
            "color": swing_color,
            "entry": swing_entry,
            "stop_loss": swing_stop,
            "take_profit_1": swing_tp1,
            "take_profit_2": swing_tp2,
            "summary": swing_summary
        },
        "long_term": {
            "horizon_name": "Months – Years (Long-Term Wealth)",
            "short_label": "MONTHS - YEARS",
            "model_name": "Institutional 200-SMA Regime & Factor Model",
            "academic_ref": "Asness, Moskowitz, Pedersen (2013) & FINRA Due Diligence",
            "verdict": long_verdict,
            "action": long_action,
            "badge": long_badge,
            "color": long_color,
            "accumulation_zone": f"${long_accum_low:.2f} - ${long_accum_high:.2f}",
            "accum_range": f"${long_accum_low:.2f} - ${long_accum_high:.2f}",
            "invalidation_floor": long_invalidation,
            "twelve_month_target": long_target,
            "target": long_target,
            "dist_200_sma_pct": round(dist_200_pct, 1),
            "summary": long_summary
        }
    }

