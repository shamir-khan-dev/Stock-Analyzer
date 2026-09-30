import pandas as pd
from typing import List, Dict, Any

def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Analyzes recent candles to detect high-probability price action patterns.
    Returns a list of detected patterns with type, bias (BULLISH/BEARISH/NEUTRAL), and description.
    """
    if len(df) < 5:
        return []
        
    patterns = []
    
    # Analyze the last 3 candles
    c1 = df.iloc[-1] # current / latest candle
    c2 = df.iloc[-2] # previous candle
    c3 = df.iloc[-3] # 2 candles ago
    
    def candle_parts(row):
        body = abs(row['Close'] - row['Open'])
        candle_range = row['High'] - row['Low'] + 1e-10
        is_green = row['Close'] >= row['Open']
        upper_shadow = row['High'] - max(row['Close'], row['Open'])
        lower_shadow = min(row['Close'], row['Open']) - row['Low']
        return body, candle_range, is_green, upper_shadow, lower_shadow
        
    b1, r1, g1, u1, l1 = candle_parts(c1)
    b2, r2, g2, u2, l2 = candle_parts(c2)
    b3, r3, g3, u3, l3 = candle_parts(c3)
    
    # 1. Bullish Engulfing
    if (not g2) and g1 and (c1['Close'] > c2['Open']) and (c1['Open'] < c2['Close']) and (b1 > b2):
        patterns.append({
            "name": "Bullish Engulfing",
            "bias": "BULLISH",
            "significance": "HIGH",
            "description": "Strong green body completely engulfs prior red candle, indicating aggressive buyer takeover."
        })
        
    # 2. Bearish Engulfing
    if g2 and (not g1) and (c1['Close'] < c2['Open']) and (c1['Open'] > c2['Close']) and (b1 > b2):
        patterns.append({
            "name": "Bearish Engulfing",
            "bias": "BEARISH",
            "significance": "HIGH",
            "description": "Strong red body engulfs prior green candle, signaling institutional distribution."
        })
        
    # 3. Hammer (Bullish Reversal)
    if (l1 > 2.0 * b1) and (u1 < 0.25 * b1):
        patterns.append({
            "name": "Bullish Hammer / Pinbar",
            "bias": "BULLISH",
            "significance": "MEDIUM-HIGH",
            "description": "Long lower shadow shows strong rejection of lower prices with buyers stepping in."
        })
        
    # 4. Shooting Star / Inverted Hammer (Bearish Reversal)
    if (u1 > 2.0 * b1) and (l1 < 0.25 * b1):
        patterns.append({
            "name": "Shooting Star / Bearish Pinbar",
            "bias": "BEARISH",
            "significance": "MEDIUM-HIGH",
            "description": "Long upper shadow demonstrates upper price rejection and seller exhaustion."
        })
        
    # 5. Morning Star (Bullish 3-candle)
    if (not g3) and (b2 < 0.3 * b3) and g1 and (c1['Close'] > (c3['Open'] + c3['Close']) / 2):
        patterns.append({
            "name": "Morning Star",
            "bias": "BULLISH",
            "significance": "HIGH",
            "description": "Classic 3-candle bottom reversal formation signaling impending upward breakout."
        })

    # 6. Evening Star (Bearish 3-candle)
    if g3 and (b2 < 0.3 * b3) and (not g1) and (c1['Close'] < (c3['Open'] + c3['Close']) / 2):
        patterns.append({
            "name": "Evening Star",
            "bias": "BEARISH",
            "significance": "HIGH",
            "description": "Classic 3-candle top reversal formation warning of trend rollover."
        })

    # 7. Doji (Indecision)
    if (b1 / r1) < 0.1:
        patterns.append({
            "name": "Doji (Market Indecision)",
            "bias": "NEUTRAL",
            "significance": "MEDIUM",
            "description": "Equal open and close reflects consolidation and potential impending volatility expansion."
        })
        
    # 8. 20-Day Range Breakout
    if len(df) >= 20:
        high_20 = df['High'].iloc[-21:-1].max()
        low_20 = df['Low'].iloc[-21:-1].min()
        vol_ratio = c1.get('Vol_Ratio', 1.0)
        
        if c1['Close'] > high_20 and vol_ratio > 1.3:
            patterns.append({
                "name": "High-Volume Range Breakout",
                "bias": "BULLISH",
                "significance": "VERY HIGH",
                "description": f"Price broke above 20-candle high ({high_20:.2f}) on elevated volume ({vol_ratio:.1f}x avg)."
            })
        elif c1['Close'] < low_20 and vol_ratio > 1.3:
            patterns.append({
                "name": "High-Volume Breakdown",
                "bias": "BEARISH",
                "significance": "VERY HIGH",
                "description": f"Price broke below 20-candle low ({low_20:.2f}) on heavy sell volume."
            })

    return patterns
