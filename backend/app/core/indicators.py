import numpy as np
import pandas as pd
from typing import Dict, Any

def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Calculates Exponential Moving Average."""
    return series.ewm(span=span, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Relative Strength Index."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    
    # Wilder's smoothing
    gain_wilder = (delta.where(delta > 0, 0.0)).ewm(alpha=1/period, adjust=False).mean()
    loss_wilder = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/period, adjust=False).mean()
    
    rs = gain_wilder / (loss_wilder + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculates MACD line, Signal line, and Histogram."""
    fast_ema = calculate_ema(series, fast)
    slow_ema = calculate_ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Calculates Upper, Middle, Lower Bollinger Bands, Bandwidth, and %B."""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    bandwidth = ((upper - lower) / (middle + 1e-10)) * 100
    percent_b = (series - lower) / (upper - lower + 1e-10)
    return upper, middle, lower, bandwidth, percent_b

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR) for volatility and stop-loss sizing."""
    high = df['High']
    low = df['Low']
    close_prev = df['Close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_stochastic_rsi(rsi_series: pd.Series, period: int = 14, smooth_k: int = 3, smooth_d: int = 3):
    """Calculates Stochastic RSI (%K and %D lines)."""
    min_rsi = rsi_series.rolling(window=period).min()
    max_rsi = rsi_series.rolling(window=period).max()
    stoch_rsi = (rsi_series - min_rsi) / (max_rsi - min_rsi + 1e-10) * 100
    fast_k = stoch_rsi.rolling(window=smooth_k).mean()
    fast_d = fast_k.rolling(window=smooth_d).mean()
    return fast_k, fast_d

def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    """
    Calculates Supertrend indicator line and trend direction (+1 for Bullish, -1 for Bearish).
    """
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values
    atr = calculate_atr(df, period).bfill().values
    
    n = len(df)
    upper_band = np.zeros(n)
    lower_band = np.zeros(n)
    trend = np.ones(n)  # 1 = bullish, -1 = bearish
    supertrend = np.zeros(n)
    
    hl2 = (high + low) / 2.0
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)
    
    for i in range(1, n):
        if basic_upper[i] < upper_band[i-1] or close[i-1] > upper_band[i-1]:
            upper_band[i] = basic_upper[i]
        else:
            upper_band[i] = upper_band[i-1]
            
        if basic_lower[i] > lower_band[i-1] or close[i-1] < lower_band[i-1]:
            lower_band[i] = basic_lower[i]
        else:
            lower_band[i] = lower_band[i-1]
            
        if trend[i-1] == 1:
            if close[i] < lower_band[i]:
                trend[i] = -1
                supertrend[i] = upper_band[i]
            else:
                trend[i] = 1
                supertrend[i] = lower_band[i]
        else:
            if close[i] > upper_band[i]:
                trend[i] = 1
                supertrend[i] = lower_band[i]
            else:
                trend[i] = -1
                supertrend[i] = upper_band[i]
                
    return pd.Series(supertrend, index=df.index), pd.Series(trend, index=df.index)

def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """Calculates On-Balance Volume (OBV)."""
    close = df['Close']
    volume = df['Volume']
    obv = np.where(close > close.shift(1), volume, np.where(close < close.shift(1), -volume, 0)).cumsum()
    return pd.Series(obv, index=df.index)

def calculate_pivot_points(df: pd.DataFrame) -> Dict[str, float]:
    """Calculates Standard Pivot Points (P, S1, S2, S3, R1, R2, R3) from recent price action."""
    if len(df) < 2:
        last = df.iloc[-1]
        p = float(last['Close'])
        return {"P": p, "R1": p, "R2": p, "R3": p, "S1": p, "S2": p, "S3": p}
        
    recent = df.iloc[-2] # previous candle
    h = float(recent['High'])
    l = float(recent['Low'])
    c = float(recent['Close'])
    
    p = (h + l + c) / 3.0
    r1 = (2 * p) - l
    s1 = (2 * p) - h
    r2 = p + (h - l)
    s2 = p - (h - l)
    r3 = h + 2 * (p - l)
    s3 = l - 2 * (h - p)
    
    return {
        "P": round(p, 2),
        "R1": round(r1, 2),
        "R2": round(r2, 2),
        "R3": round(r3, 2),
        "S1": round(s1, 2),
        "S2": round(s2, 2),
        "S3": round(s3, 2)
    }

def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes all standard technical indicators and appends them to the dataframe.
    """
    d = df.copy()
    close = d['Close']
    
    d['EMA_9'] = calculate_ema(close, 9)
    d['EMA_21'] = calculate_ema(close, 21)
    d['EMA_50'] = calculate_ema(close, 50)
    d['EMA_200'] = calculate_ema(close, 200)
    
    d['RSI'] = calculate_rsi(close, 14)
    macd, signal, hist = calculate_macd(close)
    d['MACD'] = macd
    d['MACD_Signal'] = signal
    d['MACD_Hist'] = hist
    
    bb_upper, bb_mid, bb_lower, bb_width, bb_pct_b = calculate_bollinger_bands(close)
    d['BB_Upper'] = bb_upper
    d['BB_Middle'] = bb_mid
    d['BB_Lower'] = bb_lower
    d['BB_Width'] = bb_width
    d['BB_PctB'] = bb_pct_b
    
    d['ATR'] = calculate_atr(d, 14)
    stoch_k, stoch_d = calculate_stochastic_rsi(d['RSI'])
    d['Stoch_K'] = stoch_k
    d['Stoch_D'] = stoch_d
    
    st_line, st_trend = calculate_supertrend(d)
    d['Supertrend'] = st_line
    d['Supertrend_Trend'] = st_trend
    
    d['OBV'] = calculate_obv(d)
    d['Vol_SMA20'] = d['Volume'].rolling(window=20).mean()
    d['Vol_Ratio'] = d['Volume'] / (d['Vol_SMA20'] + 1e-10)
    
    return d
