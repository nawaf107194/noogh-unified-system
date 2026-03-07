"""
V2 - Futures Technical Indicators & Signal Engine (Macro/Micro + SMC + Risk)
Fixes & upgrades:
- RSI uses Wilder smoothing (classic RSI)
- MACD crossover safe-guards
- Fractals without lookahead (no center=True / no future leak)
- FVG with minimum gap filter
- Liquidity score uses tanh normalization (less extreme)
- Adds ATR (for dynamic SL/TP)
- Cleaner scoring model + configurable weights
- Input validation + NaN safety

Expected DF columns:
- df_macro: ['open','high','low','close','volume'] indexed by datetime (recommended)
- df_micro: ['open','high','low','close','volume']
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Literal, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SignalType = Optional[Literal["LONG", "SHORT"]]


# ----------------------------- Configs -----------------------------

@dataclass(frozen=True)
class IndicatorConfig:
    sma_period: int = 50
    ema_period: int = 20
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    atr_period: int = 14

    doji_threshold_pct_of_range: float = 0.10  # Doji if body <= 0.10% of range (tight)
    fractal_window: int = 2                    # Williams fractal "w" (needs 2w+1 bars)
    fib_lookback: int = 120
    sweep_window: int = 20
    fvg_min_gap_atr_mult: float = 0.25         # require gap >= 0.25 * ATR by default
    cvd_divergence_lookback: int = 20          # lookback for divergence / impulses


@dataclass(frozen=True)
class ScoreWeights:
    # Micro confirmation weights
    macd_cross: int = 28
    rsi_extreme: int = 18
    doji: int = 10
    bullish_engulfing: int = 20
    bearish_engulfing: int = 20
    hammer: int = 14
    fractal: int = 16
    fvg: int = 22
    sweep: int = 26
    orderflow_impulse: int = 30
    cvd_trend: int = 15

    # Threshold to trigger signal
    min_score_to_trade: int = 60


@dataclass(frozen=True)
class RiskConfig:
    # ATR based stop
    base_sl_atr_mult: float = 2.0
    # widen SL when conditions are strong
    strong_sl_atr_mult: float = 2.6
    # tighten SL when weak
    weak_sl_atr_mult: float = 1.6

    # RRR ladder
    min_rrr: float = 2.0
    tp2_mult: float = 1.5
    tp3_mult: float = 2.0


# ----------------------------- Helpers -----------------------------

def _require_cols(df: pd.DataFrame, cols: tuple[str, ...], name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}. Required: {cols}")


def _last_timestamp(df: pd.DataFrame) -> Optional[str]:
    try:
        ts = df.index[-1]
        return ts.isoformat() if hasattr(ts, "isoformat") else None
    except Exception:
        return None


# ----------------------------- Indicators -----------------------------

class TechnicalIndicatorsV2:
    """V2 indicators without lookahead leakage and with better smoothing/normalization."""

    @staticmethod
    def sma(df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        return df[column].rolling(window=period, min_periods=period).mean()

    @staticmethod
    def ema(df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        return df[column].ewm(span=period, adjust=False, min_periods=period).mean()

    @staticmethod
    def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        close = df["close"]
        ema_fast = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
        histogram = macd_line - signal_line
        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    @staticmethod
    def rsi_wilder(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
        close = df[column]
        delta = close.diff()

        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)

        # Wilder smoothing
        avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close_prev = df["close"].shift(1)

        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        return atr

    @staticmethod
    def doji(df: pd.DataFrame, threshold_pct_of_range: float = 0.10) -> pd.Series:
        # body / range * 100 <= threshold (%)
        body = (df["close"] - df["open"]).abs()
        rng = (df["high"] - df["low"]).replace(0, np.nan)
        body_pct = (body / rng) * 100
        return (body_pct <= threshold_pct_of_range).fillna(False)

    @staticmethod
    def fractals_no_lookahead(df: pd.DataFrame, window: int = 2) -> Dict[str, pd.Series]:
        """
        Williams fractal without future leak:
        - A bearish fractal at i means: high[i] is the max of [i-2w .. i] (past-only at time i),
          BUT this will detect "candidate fractals" earlier than classic definition.
        Practical trading approach: confirm fractal after w bars pass.
        So we compute classic centered fractal and shift forward by window to make it usable in real-time.
        """
        w = window
        length = 2 * w + 1

        # Classic centered logic (uses future), then shift by +w to make it "confirmed" in real time.
        high_roll = df["high"].rolling(window=length, center=True).max()
        low_roll = df["low"].rolling(window=length, center=True).min()

        bearish_center = (df["high"] == high_roll)
        bullish_center = (df["low"] == low_roll)

        bearish_confirmed = bearish_center.shift(w).fillna(False).astype(bool)
        bullish_confirmed = bullish_center.shift(w).fillna(False).astype(bool)

        return {"bearish": bearish_confirmed, "bullish": bullish_confirmed}

    @staticmethod
    def candlestick_patterns(df: pd.DataFrame) -> Dict[str, pd.Series]:
        prev_close = df["close"].shift(1)
        prev_open = df["open"].shift(1)
        close = df["close"]
        open_ = df["open"]

        prev_bear = prev_close < prev_open
        prev_bull = prev_close > prev_open
        curr_bull = close > open_
        curr_bear = close < open_

        bullish_engulf = prev_bear & curr_bull & (open_ <= prev_close) & (close >= prev_open)
        bearish_engulf = prev_bull & curr_bear & (open_ >= prev_close) & (close <= prev_open)

        body = (close - open_).abs()
        upper_shadow = df["high"] - df[["open", "close"]].max(axis=1)
        lower_shadow = df[["open", "close"]].min(axis=1) - df["low"]

        # hammer: small upper shadow, long lower shadow; allow either bull/neutral body, but prefer bullish close later in scoring
        hammer = (lower_shadow > 2 * body) & (upper_shadow <= body * 0.5)

        return {
            "bullish_engulfing": bullish_engulf.fillna(False),
            "bearish_engulfing": bearish_engulf.fillna(False),
            "hammer": hammer.fillna(False),
        }

    @staticmethod
    def fib_levels(df: pd.DataFrame, lookback: int = 120) -> Dict[str, float]:
        recent = df.tail(lookback)
        hi = float(recent["high"].max())
        lo = float(recent["low"].min())
        diff = hi - lo if hi > lo else 0.0

        return {
            "0.0": hi,
            "0.236": hi - 0.236 * diff,
            "0.382": hi - 0.382 * diff,
            "0.5": hi - 0.5 * diff,
            "0.618": hi - 0.618 * diff,
            "1.0": lo,
        }

    @staticmethod
    def fvg(df: pd.DataFrame, atr: pd.Series, min_gap_atr_mult: float = 0.25) -> Dict[str, pd.Series]:
        """
        Bullish FVG: low[i] > high[i-2]
        Bearish FVG: high[i] < low[i-2]
        With minimum gap filter using ATR to avoid tiny gaps.
        """
        high_prev2 = df["high"].shift(2)
        low_prev2 = df["low"].shift(2)

        gap_bull = (df["low"] - high_prev2)
        gap_bear = (low_prev2 - df["high"])

        min_gap = atr * float(min_gap_atr_mult)

        bullish = (df["low"] > high_prev2) & (gap_bull >= min_gap)
        bearish = (df["high"] < low_prev2) & (gap_bear >= min_gap)

        return {"bullish_fvg": bullish.fillna(False), "bearish_fvg": bearish.fillna(False)}

    @staticmethod
    def liquidity_sweeps(df: pd.DataFrame, window: int = 20) -> Dict[str, pd.Series]:
        prev_lows = df["low"].rolling(window=window, min_periods=window).min().shift(1)
        prev_highs = df["high"].rolling(window=window, min_periods=window).max().shift(1)

        bullish = (df["low"] < prev_lows) & (df["close"] > prev_lows)
        bearish = (df["high"] > prev_highs) & (df["close"] < prev_highs)

        return {"bullish_sweep": bullish.fillna(False), "bearish_sweep": bearish.fillna(False)}

    @staticmethod
    def trend_direction(df: pd.DataFrame, sma_period: int = 50, ema_period: int = 20) -> Literal["BULLISH", "BEARISH", "NEUTRAL"]:
        if len(df) < max(sma_period, ema_period):
            return "NEUTRAL"

        sma = TechnicalIndicatorsV2.sma(df, sma_period)
        ema = TechnicalIndicatorsV2.ema(df, ema_period)

        price = df["close"].iloc[-1]
        sma_v = sma.iloc[-1]
        ema_v = ema.iloc[-1]

        if pd.isna(sma_v) or pd.isna(ema_v):
            return "NEUTRAL"
            
        trend_strength = abs(ema_v - sma_v) / price
        if trend_strength <= 0.002:
            return "NEUTRAL"

        if price > ema_v > sma_v:
            return "BULLISH"
        if price < ema_v < sma_v:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def macd_crossover(macd_data: Dict[str, pd.Series], lookback: int = 3) -> Optional[Literal["BULLISH_CROSS", "BEARISH_CROSS"]]:
        macd = macd_data["macd"].dropna()
        sig = macd_data["signal"].dropna()

        if len(macd) < 2 or len(sig) < 2:
            return None

        # Align last points safely
        macd_last = macd.iloc[-min(lookback, len(macd)):]
        sig_last = sig.iloc[-min(lookback, len(sig)):]
        # Ensure same length
        n = min(len(macd_last), len(sig_last))
        macd_last = macd_last.iloc[-n:]
        sig_last = sig_last.iloc[-n:]

        if n < 2:
            return None

        if (macd_last.iloc[-2] < sig_last.iloc[-2]) and (macd_last.iloc[-1] > sig_last.iloc[-1]):
            return "BULLISH_CROSS"
        if (macd_last.iloc[-2] > sig_last.iloc[-2]) and (macd_last.iloc[-1] < sig_last.iloc[-1]):
            return "BEARISH_CROSS"
        return None

    @staticmethod
    def rsi_condition(rsi: pd.Series, overbought: float = 70, oversold: float = 30) -> Optional[Literal["OVERBOUGHT", "OVERSOLD"]]:
        r = float(rsi.dropna().iloc[-1]) if rsi.notna().any() else np.nan
        if np.isnan(r):
            return None
        if r > overbought:
            return "OVERBOUGHT"
        if r < oversold:
            return "OVERSOLD"
        return None

    @staticmethod
    def liquidity_score(df: pd.DataFrame, period: int = 20) -> float:
        if len(df) < period:
            return 50.0
        vol = df["volume"].replace(0, np.nan)
        avg = vol.rolling(window=period, min_periods=period).mean().iloc[-1]
        cur = vol.iloc[-1]
        if pd.isna(avg) or avg <= 0 or pd.isna(cur):
            return 50.0
        ratio = float(cur / avg)
        # normalize with tanh for stability
        score = 50.0 + np.tanh(ratio - 1.0) * 50.0
        return float(np.clip(score, 0, 100))

    @staticmethod
    def real_delta(df: pd.DataFrame) -> pd.DataFrame:
        """
        Uses Binance 'taker_buy_base' (which is the volume of aggressive buys).
        Total volume - taker_buy_base = aggressive sells.
        Returns DF with buy_vol, sell_vol, delta, cvd.
        """
        out = df.copy()
        if "taker_buy_base" not in df.columns:
            # Fallback to zeros if missing
            out["buy_vol"] = 0.0
            out["sell_vol"] = 0.0
            out["delta"] = 0.0
            out["cvd"] = 0.0
            return out

        buy = out["taker_buy_base"].fillna(0.0)
        sell = (out["volume"].fillna(0.0) - buy).clip(lower=0.0)
        
        delta = buy - sell
        cvd = delta.cumsum()
        
        out["buy_vol"] = buy
        out["sell_vol"] = sell
        out["delta"] = delta
        out["cvd"] = cvd
        return out

    @staticmethod
    def orderflow_signals(df: pd.DataFrame) -> Dict[str, bool]:
        """
        Takes DF with 'delta' and 'cvd' and returns signals.
        - delta_impulse: last bar delta bigger than rolling avg by factor
        - cvd_up / cvd_down: short term cvd trend
        """
        if "delta" not in df.columns or "cvd" not in df.columns:
             return {"delta_impulse_up": False, "delta_impulse_dn": False, "cvd_up": False, "cvd_down": False}

        d = df["delta"]
        cvd = df["cvd"]

        avg = d.abs().rolling(20, min_periods=20).mean() # Compare against absolute average volume
        last = d.iloc[-1]
        last_avg = avg.iloc[-1] if len(avg) else np.nan

        delta_impulse_up = np.isfinite(last_avg) and last > (1.5 * last_avg) and last > 0
        delta_impulse_dn = np.isfinite(last_avg) and last < (-1.5 * last_avg) and last < 0

        cvd_up = cvd.iloc[-1] > cvd.iloc[-5] if len(cvd) >= 5 else False
        cvd_down = cvd.iloc[-1] < cvd.iloc[-5] if len(cvd) >= 5 else False

        return {
            "delta_impulse_up": bool(delta_impulse_up),
            "delta_impulse_dn": bool(delta_impulse_dn),
            "cvd_up": bool(cvd_up),
            "cvd_down": bool(cvd_down),
        }


# ----------------------------- Signal + Risk Engine -----------------------------

class SignalEngineV2:
    @staticmethod
    def generate_entry_signal(
        df_macro: pd.DataFrame,
        df_micro: pd.DataFrame,
        cfg: IndicatorConfig = IndicatorConfig(),
        w: ScoreWeights = ScoreWeights(),
        risk_cfg: RiskConfig = RiskConfig(),
        macro_timeframe: str = "1h",
        micro_timeframe: str = "5m",
    ) -> Dict[str, Any]:
        """
        Returns dict with:
        - signal: LONG/SHORT/None
        - score, strength (0-100-ish)
        - reasons
        - trend + indicator snapshots
        - stop_loss, tp targets if signal exists
        """
        try:
            _require_cols(df_macro, ("open", "high", "low", "close", "volume"), "df_macro")
            _require_cols(df_micro, ("open", "high", "low", "close", "volume", "taker_buy_base"), "df_micro")

            if len(df_micro) < max(cfg.rsi_period, cfg.macd_slow, cfg.atr_period) + 5:
                return {"signal": None, "score": 0, "strength": 0, "reason": "Not enough micro data"}

            if len(df_macro) < max(cfg.sma_period, cfg.ema_period) + 5:
                return {"signal": None, "score": 0, "strength": 0, "reason": "Not enough macro data"}

            # 1) Macro trend
            macro_trend = TechnicalIndicatorsV2.trend_direction(df_macro, cfg.sma_period, cfg.ema_period)

            # 2) Micro indicators
            macd = TechnicalIndicatorsV2.macd(df_micro, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)
            rsi = TechnicalIndicatorsV2.rsi_wilder(df_micro, cfg.rsi_period)
            atr = TechnicalIndicatorsV2.atr(df_micro, cfg.atr_period)

            doji = TechnicalIndicatorsV2.doji(df_micro, cfg.doji_threshold_pct_of_range)
            fr = TechnicalIndicatorsV2.fractals_no_lookahead(df_micro, cfg.fractal_window)
            candles = TechnicalIndicatorsV2.candlestick_patterns(df_micro)

            sweeps = TechnicalIndicatorsV2.liquidity_sweeps(df_micro, cfg.sweep_window)
            fvgs = TechnicalIndicatorsV2.fvg(df_micro, atr, cfg.fvg_min_gap_atr_mult)

            # Order Flow
            df_micro_of = TechnicalIndicatorsV2.real_delta(df_micro)
            of_signals = TechnicalIndicatorsV2.orderflow_signals(df_micro_of)

            fib = TechnicalIndicatorsV2.fib_levels(df_macro, cfg.fib_lookback)

            # 3) Conditions
            macd_cross = TechnicalIndicatorsV2.macd_crossover(macd, lookback=3)
            rsi_cond = TechnicalIndicatorsV2.rsi_condition(rsi)
            rsi_val = float(rsi.dropna().iloc[-1]) if rsi.notna().any() else float("nan")

            latest_doji = bool(doji.iloc[-1])
            latest_hammer = bool(candles["hammer"].iloc[-1])
            latest_bull_eng = bool(candles["bullish_engulfing"].iloc[-1])
            latest_bear_eng = bool(candles["bearish_engulfing"].iloc[-1])

            recent_bull_fr = bool(fr["bullish"].iloc[-5:-1].any())
            recent_bear_fr = bool(fr["bearish"].iloc[-5:-1].any())

            recent_bull_fvg = bool(fvgs["bullish_fvg"].iloc[-4:-1].any())
            recent_bear_fvg = bool(fvgs["bearish_fvg"].iloc[-4:-1].any())

            recent_bull_sweep = bool(sweeps["bullish_sweep"].iloc[-4:-1].any())
            recent_bear_sweep = bool(sweeps["bearish_sweep"].iloc[-4:-1].any())

            # Order Flow components
            of_impulse_up = of_signals["delta_impulse_up"]
            of_impulse_dn = of_signals["delta_impulse_dn"]
            cvd_up = of_signals["cvd_up"]
            cvd_dn = of_signals["cvd_down"]
            
            last_delta = float(df_micro_of["delta"].iloc[-1]) if "delta" in df_micro_of.columns else 0.0

            liq = TechnicalIndicatorsV2.liquidity_score(df_micro, 20)

            # 4) TRAP MODEL: Sweep + Delta Exhaustion + Reversal
            reasons: list[str] = []
            score = 0
            signal: SignalType = None

            # Delta exhaustion detection
            delta_series = df_micro_of["delta"]
            delta_avg = delta_series.abs().rolling(20, min_periods=10).mean()
            delta_curr = float(delta_series.iloc[-1]) if len(delta_series) > 0 else 0.0
            delta_prev = float(delta_series.iloc[-2]) if len(delta_series) > 1 else 0.0
            delta_avg_prev = float(delta_avg.iloc[-2]) if len(delta_avg) > 1 else float("nan")

            # Previous bar sweep detection
            bull_sweep_prev = bool(sweeps["bullish_sweep"].iloc[-2]) if len(sweeps["bullish_sweep"]) > 1 else False
            bear_sweep_prev = bool(sweeps["bearish_sweep"].iloc[-2]) if len(sweeps["bearish_sweep"]) > 1 else False

            if not np.isnan(delta_avg_prev) and delta_avg_prev > 0:
                # LONG TRAP: bull sweep + strong selling exhaustion + buy reversal
                is_sell_exhaustion = (delta_prev < 0) and (abs(delta_prev) > 1.8 * delta_avg_prev)
                is_buy_reversal = (delta_curr > 0)

                if bull_sweep_prev and is_sell_exhaustion and is_buy_reversal:
                    signal = "LONG"
                    score = 100
                    reasons.append("🪤 Liquidity Trap LONG: Sweep + Sell Exhaustion + Buy Reversal")

                # SHORT TRAP: bear sweep + strong buying exhaustion + sell reversal
                is_buy_exhaustion = (delta_prev > 0) and (abs(delta_prev) > 1.8 * delta_avg_prev)
                is_sell_reversal = (delta_curr < 0)

                if bear_sweep_prev and is_buy_exhaustion and is_sell_reversal:
                    signal = "SHORT"
                    score = 100
                    reasons.append("🪤 Liquidity Trap SHORT: Sweep + Buy Exhaustion + Sell Reversal")

            strength = float(100 if signal else 0)

            # 5) Risk Engine (ATR-based)
            entry = float(df_micro["close"].iloc[-1])
            atr_v = float(atr.dropna().iloc[-1]) if atr.notna().any() else 0.0

            stop_loss = None
            tps = None

            if signal and atr_v > 0:
                sl_mult = risk_cfg.base_sl_atr_mult

                if signal == "LONG":
                    # SL below the sweep low
                    sweep_low = float(df_micro["low"].iloc[-2])
                    stop_loss = min(entry - atr_v * sl_mult, sweep_low - atr_v * 0.2)
                else:
                    # SL above the sweep high
                    sweep_high = float(df_micro["high"].iloc[-2])
                    stop_loss = max(entry + atr_v * sl_mult, sweep_high + atr_v * 0.2)

                tps = SignalEngineV2.take_profit_targets(
                    entry_price=entry,
                    stop_loss=float(stop_loss),
                    signal_type=signal,
                    min_rrr=risk_cfg.min_rrr,
                    tp2_mult=risk_cfg.tp2_mult,
                    tp3_mult=risk_cfg.tp3_mult,
                )

            return {
                "signal": signal,
                "score": int(score),
                "strength": strength,
                "macro_trend": macro_trend,
                "timeframes": {"macro": macro_timeframe, "micro": micro_timeframe},
                "entry_price": entry,
                "atr": atr_v,
                "stop_loss": float(stop_loss) if stop_loss is not None else None,
                "take_profits": tps,
                "snapshots": {
                    "macd_cross": macd_cross,
                    "rsi_condition": rsi_cond,
                    "rsi_value": rsi_val,
                    "doji": latest_doji,
                    "bullish_engulfing": latest_bull_eng,
                    "bearish_engulfing": latest_bear_eng,
                    "hammer": latest_hammer,
                    "bull_fractal": recent_bull_fr,
                    "bear_fractal": recent_bear_fr,
                    "bull_fvg": recent_bull_fvg,
                    "bear_fvg": recent_bear_fvg,
                    "bull_sweep": recent_bull_sweep,
                    "bear_sweep": recent_bear_sweep,
                    "of_impulse_up": of_impulse_up,
                    "of_impulse_dn": of_impulse_dn,
                    "cvd_up": cvd_up,
                    "cvd_dn": cvd_dn,
                    "last_delta": last_delta,
                    "liquidity_score": liq,
                    "fib_0_618": float(fib.get("0.618", 0.0)),
                },
                "reasons": reasons,
                "timestamp": _last_timestamp(df_micro),
            }

        except Exception as e:
            logger.exception("SignalEngineV2 error")
            return {"signal": None, "score": 0, "strength": 0, "error": str(e)}

    @staticmethod
    def take_profit_targets(
        entry_price: float,
        stop_loss: float,
        signal_type: Literal["LONG", "SHORT"],
        min_rrr: float = 2.0,
        tp2_mult: float = 1.5,
        tp3_mult: float = 2.0,
    ) -> Dict[str, float]:
        risk = abs(entry_price - stop_loss)
        if risk <= 0:
            return {"tp1": entry_price, "tp2": entry_price, "tp3": entry_price, "risk": 0.0, "rrr": min_rrr}

        if signal_type == "LONG":
            tp1 = entry_price + risk * min_rrr
            tp2 = entry_price + risk * (min_rrr * tp2_mult)
            tp3 = entry_price + risk * (min_rrr * tp3_mult)
        else:
            tp1 = entry_price - risk * min_rrr
            tp2 = entry_price - risk * (min_rrr * tp2_mult)
            tp3 = entry_price - risk * (min_rrr * tp3_mult)

        return {"tp1": tp1, "tp2": tp2, "tp3": tp3, "risk": risk, "rrr": min_rrr}


class SignalEngineV3_LiquidityTrap:
    @staticmethod
    def generate_entry_signal(
        df_macro: pd.DataFrame,
        df_micro: pd.DataFrame,
        cfg: IndicatorConfig = IndicatorConfig(),
        w: ScoreWeights = ScoreWeights(),
        risk_cfg: RiskConfig = RiskConfig(),
    ) -> Dict[str, Any]:
        _require_cols(df_micro, ("open", "high", "low", "close", "volume", "taker_buy_base"), "df_micro")
        
        signal = "NEUTRAL"
        reasons = []
        
        if len(df_micro) < 25:
            return {"signal": "NEUTRAL", "reasons": ["Not enough data"]}
            
        # Macro trend
        macro_trend = TechnicalIndicatorsV2.trend_direction(df_macro, sma_period=50, ema_period=20)
        
        # Order Flow
        of = TechnicalIndicatorsV2.real_delta(df_micro)
        delta = of["delta"]
        cvd = of["cvd"]
        delta_avg = delta.abs().rolling(20, min_periods=10).mean()
        
        # Sweeps
        sweeps = TechnicalIndicatorsV2.liquidity_sweeps(df_micro, window=cfg.sweep_window)
        
        delta_curr = delta.iloc[-1]
        delta_prev = delta.iloc[-2]
        delta_avg_prev = delta_avg.iloc[-2] if len(delta_avg) > 1 else np.nan
        
        bullish_sweep_prev = sweeps["bullish_sweep"].iloc[-2]
        bearish_sweep_prev = sweeps["bearish_sweep"].iloc[-2]
        
        if not np.isnan(delta_avg_prev):
            # FIX BUG 4: Remove macro_trend filter to match vectorized logic
            # Vectorized has NO macro filter and generates 248 signals
            # With macro filter, we only get 125 signals (50% rejected!)

            # LONG SETUP
            is_strong_sell_prev = (delta_prev < 0) and (abs(delta_prev) > 1.8 * delta_avg_prev)
            is_reversal_buy_curr = (delta_curr > 0)

            if bullish_sweep_prev and is_strong_sell_prev and is_reversal_buy_curr:
                signal = "LONG"
                reasons.append("Bullish Sweep + Sell Exhaustion + Buy Reversal (Trap)")

            # SHORT SETUP
            is_strong_buy_prev = (delta_prev > 0) and (abs(delta_prev) > 1.8 * delta_avg_prev)
            is_reversal_sell_curr = (delta_curr < 0)

            if bearish_sweep_prev and is_strong_buy_prev and is_reversal_sell_curr:
                signal = "SHORT"
                reasons.append("Bearish Sweep + Buy Exhaustion + Sell Reversal (Trap)")
                
        # Risk Engine
        entry = float(df_micro["close"].iloc[-1])
        atr = TechnicalIndicatorsV2.atr(df_micro, cfg.atr_period)
        atr_v = float(atr.dropna().iloc[-1]) if atr.notna().any() else 0.0
        
        stop_loss = None
        tps = None
        
        if signal in ("LONG", "SHORT") and atr_v > 0:
            sl_mult = risk_cfg.base_sl_atr_mult

            if signal == "LONG":
                # FIX BUG 3: Use ATR-based SL only (no sweep-based tight SL)
                # Sweep-based logic was causing 65.6% of losers to have SL < 0.25%
                # Standard ATR-based SL provides better breathing room
                stop_loss = entry - atr_v * sl_mult

            else:
                # FIX BUG 3: Use ATR-based SL only (no sweep-based tight SL)
                # For SHORT: SL should be ABOVE entry
                stop_loss = entry + atr_v * sl_mult
                
            tps = SignalEngineV2.take_profit_targets(
                entry_price=entry,
                stop_loss=float(stop_loss),
                signal_type=signal,
                min_rrr=risk_cfg.min_rrr,
                tp2_mult=risk_cfg.tp2_mult,
                tp3_mult=risk_cfg.tp3_mult,
            )
            
        return {
            "signal": signal,
            "score": 100 if signal != "NEUTRAL" else 0, # Trap model has absolute confidence
            "strength": 100 if signal != "NEUTRAL" else 0,
            "macro_trend": macro_trend,
            "entry_price": entry,
            "atr": atr_v,
            "stop_loss": float(stop_loss) if stop_loss is not None else None,
            "take_profits": tps,
            "reasons": reasons,
            "snapshots": {}
        }
