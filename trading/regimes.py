from __future__ import annotations
from typing import Dict, Any
import numpy as np
import pandas as pd

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    rs = _ema(up, period) / (_ema(down, period) + 1e-9)
    return 100 - (100 / (1 + rs))

def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['high']
    low = df['low']
    close_prev = df['close'].shift(1)
    
    tr = pd.concat([
        high - low,
        (high - close_prev).abs(),
        (low - close_prev).abs()
    ], axis=1).max(axis=1)
    return _ema(tr, period)

def _adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['high']
    low = df['low']
    close_prev = df['close'].shift(1)
    
    up = high - high.shift(1)
    down = low.shift(1) - low
    
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    
    tr = pd.concat([
        high - low,
        (high - close_prev).abs(),
        (low - close_prev).abs()
    ], axis=1).max(axis=1)
    
    atr = _ema(tr, period)
    plus_di = 100 * (_ema(pd.Series(plus_dm, index=df.index), period) / (atr + 1e-9))
    minus_di = 100 * (_ema(pd.Series(minus_dm, index=df.index), period) / (atr + 1e-9))
    
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
    return _ema(dx, period)

def compute_regime_tags(micro_slice: pd.DataFrame, macro_slice: pd.DataFrame) -> Dict[str, str]:
    """
    Computes Regime Tags from micro (5m) and macro (1h) data directly before the trade.
    """
    if len(macro_slice) < 50 or len(micro_slice) < 50:
        return {"vol_regime": "NORMAL", "trend_regime": "RANGE", "liquidity_regime": "NORMAL", "direction_bias": "NEUTRAL"}
        
    # Volatility Regime (Macro ATR Z-Score)
    macro_atr = _atr(macro_slice, 14)
    current_atr = macro_atr.iloc[-1]
    hist_atr = macro_atr.iloc[-50:-1]
    atr_z = (current_atr - hist_atr.mean()) / (hist_atr.std() + 1e-9)
    
    if atr_z > 1.5:
        vol_regime = "HIGH"
    elif atr_z < -1.0:
        vol_regime = "LOW"
    else:
        vol_regime = "NORMAL"
        
    # Trend Regime (Macro ADX & EMA)
    macro_close = macro_slice['close']
    macro_adx = _adx(macro_slice, 14).iloc[-1]
    macro_ema_fast = _ema(macro_close, 9).iloc[-1]
    macro_ema_slow = _ema(macro_close, 21).iloc[-1]
    
    ema_diff = macro_ema_fast - macro_ema_slow
    
    if macro_adx > 25:
        trend_regime = "TREND"
        direction_bias = "LONG_BIAS" if ema_diff > 0 else "SHORT_BIAS"
    else:
        trend_regime = "RANGE"
        direction_bias = "NEUTRAL"
        
    # Liquidity Regime (Micro Volume Z-Score)
    micro_vol = micro_slice['volume']
    vol_z = (micro_vol.iloc[-1] - micro_vol.iloc[-50:-1].mean()) / (micro_vol.iloc[-50:-1].std() + 1e-9)
    
    if vol_z > 2.0:
        liquidity_regime = "THICK"
    elif vol_z < -1.0:
        liquidity_regime = "THIN"
    else:
        liquidity_regime = "NORMAL"

    return {
        "vol_regime": vol_regime,
        "trend_regime": trend_regime,
        "liquidity_regime": liquidity_regime,
        "direction_bias": direction_bias
    }

def compute_features(micro_slice: pd.DataFrame, macro_slice: pd.DataFrame) -> Dict[str, float]:
    """
    Computes expanding features from micro (5m) and macro (1h) data.
    """
    if len(macro_slice) < 50 or len(micro_slice) < 50:
        return {}
        
    # Micro features (5m)
    close = micro_slice['close'].iloc[-1]
    micro_atr = _atr(micro_slice, 14).iloc[-1]
    micro_rsi = _rsi(micro_slice['close'], 14)
    
    atr_pct = micro_atr / close
    range_pct = (micro_slice['high'].iloc[-1] - micro_slice['low'].iloc[-1]) / close
    
    micro_vol = micro_slice['volume']
    vol_z = (micro_vol.iloc[-1] - micro_vol.iloc[-50:-1].mean()) / (micro_vol.iloc[-50:-1].std() + 1e-9)
    
    tbr = micro_slice['taker_buy_base'] / (micro_slice['volume'] + 1e-9)
    tbr_delta = tbr.iloc[-1] - tbr.iloc[-5] if len(tbr) >= 5 else 0.0
    
    rsi_val = micro_rsi.iloc[-1]
    rsi_slope = rsi_val - micro_rsi.iloc[-3] if len(micro_rsi) >= 3 else 0.0
    
    ema_fast = _ema(micro_slice['close'], 9).iloc[-1]
    ema_slow = _ema(micro_slice['close'], 21).iloc[-1]
    ema_fast_minus_slow = (ema_fast - ema_slow) / close
    
    # Macro features (1h)
    macro_close = macro_slice['close'].iloc[-1]
    macro_atr_val = _atr(macro_slice, 14).iloc[-1]
    atr_1h_pct = macro_atr_val / macro_close
    macro_ema_diff = (_ema(macro_slice['close'], 9).iloc[-1] - _ema(macro_slice['close'], 21).iloc[-1]) / macro_close
    macro_adx_val = _adx(macro_slice, 14).iloc[-1]

    return {
        "atr_pct": atr_pct,
        "range_pct": range_pct,
        "vol_z": vol_z,
        "tbr_delta": tbr_delta,
        "rsi_slope": rsi_slope,
        "ema_fast_minus_slow": ema_fast_minus_slow,
        "adx_14": macro_adx_val,
        "ema_trend_dir": 1.0 if macro_ema_diff > 0 else (-1.0 if macro_ema_diff < 0 else 0.0),
        "atr_1h_pct": atr_1h_pct
    }
