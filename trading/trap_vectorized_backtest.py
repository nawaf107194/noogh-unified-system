"""
Vectorized Trap Model Backtest — Hybrid Exit Test
Tests: Quick TP at 1R (50%) + ATR Trailing on remainder (50%)
"""
import os
import numpy as np
import pandas as pd
from prettytable import PrettyTable


def compute_signals(df: pd.DataFrame, sweep_window: int = 20, atr_period: int = 14,
                    delta_mult: float = 1.8, delta_avg_window: int = 20) -> pd.DataFrame:
    """Pre-compute ALL indicators once on the entire DataFrame."""
    out = df.copy()

    # ATR
    tr = pd.concat([
        out["high"] - out["low"],
        (out["high"] - out["close"].shift(1)).abs(),
        (out["low"] - out["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    out["atr"] = tr.rolling(atr_period, min_periods=atr_period).mean()

    # Delta & CVD
    buy = out["taker_buy_base"].fillna(0.0)
    sell = (out["volume"].fillna(0.0) - buy).clip(lower=0.0)
    out["delta"] = buy - sell
    out["delta_avg"] = out["delta"].abs().rolling(delta_avg_window, min_periods=10).mean()

    # Sweeps
    prev_lows = out["low"].rolling(window=sweep_window, min_periods=sweep_window).min().shift(1)
    prev_highs = out["high"].rolling(window=sweep_window, min_periods=sweep_window).max().shift(1)
    out["bull_sweep"] = (out["low"] < prev_lows) & (out["close"] > prev_lows)
    out["bear_sweep"] = (out["high"] > prev_highs) & (out["close"] < prev_highs)

    # Shifted values
    out["delta_prev"] = out["delta"].shift(1)
    out["delta_avg_prev"] = out["delta_avg"].shift(1)
    out["bull_sweep_prev"] = out["bull_sweep"].shift(1).fillna(False).astype(bool)
    out["bear_sweep_prev"] = out["bear_sweep"].shift(1).fillna(False).astype(bool)

    # LONG signal
    strong_sell_prev = (out["delta_prev"] < 0) & (out["delta_prev"].abs() > delta_mult * out["delta_avg_prev"])
    buy_reversal = out["delta"] > 0
    out["long_signal"] = out["bull_sweep_prev"] & strong_sell_prev & buy_reversal

    # SHORT signal
    strong_buy_prev = (out["delta_prev"] > 0) & (out["delta_prev"].abs() > delta_mult * out["delta_avg_prev"])
    sell_reversal = out["delta"] < 0
    out["short_signal"] = out["bear_sweep_prev"] & strong_buy_prev & sell_reversal

    return out


def run_hybrid_exit_backtest(df: pd.DataFrame, sl_atr_mult: float = 2.0,
                              quick_tp_rrr: float = 1.0, trailing_atr_mult: float = 1.5,
                              risk_per_trade: float = 0.01, initial_capital: float = 10_000.0,
                              commission_rate: float = 0.0004, slippage_rate: float = 0.0002) -> dict:
    """
    Hybrid exit backtest:
    - 50% of position exits at Quick TP (1R)
    - 50% trails with ATR trailing stop
    """
    equity = initial_capital
    trades = []

    in_trade = False
    entry_price = 0.0
    stop_loss = 0.0
    quick_tp = 0.0
    trailing_stop = 0.0
    side = None
    qty_quick = 0.0   # 50% for quick TP
    qty_trail = 0.0   # 50% for trailing
    quick_tp_hit = False

    for i in range(1, len(df) - 1):
        row = df.iloc[i]
        next_row = df.iloc[i + 1]
        atr_v = row["atr"]

        if np.isnan(atr_v) or atr_v <= 0:
            continue

        h, l, c = row["high"], row["low"], row["close"]

        # --- Manage open position ---
        if in_trade:
            if side == "LONG":
                # Quick TP hit?
                if not quick_tp_hit and h >= quick_tp and qty_quick > 0:
                    pnl = (quick_tp - entry_price) * qty_quick
                    pnl -= abs(pnl) * (commission_rate + slippage_rate)
                    equity += pnl
                    trades.append({"side": side, "pnl": pnl, "reason": "QUICK_TP"})
                    quick_tp_hit = True
                    # Move trailing stop to break-even
                    trailing_stop = entry_price

                # Stop loss hit on trailing portion?
                if l <= (stop_loss if not quick_tp_hit else trailing_stop):
                    exit_price = stop_loss if not quick_tp_hit else trailing_stop
                    if not quick_tp_hit:
                        # Both portions stopped out
                        total_qty = qty_quick + qty_trail
                        pnl = (exit_price - entry_price) * total_qty
                        pnl -= abs(pnl) * (commission_rate + slippage_rate)
                        equity += pnl
                        trades.append({"side": side, "pnl": pnl, "reason": "SL_FULL"})
                    else:
                        # Only trailing portion
                        pnl = (exit_price - entry_price) * qty_trail
                        pnl -= abs(pnl) * (commission_rate + slippage_rate)
                        equity += pnl
                        trades.append({"side": side, "pnl": pnl, "reason": "SL_TRAIL"})
                    in_trade = False
                    continue

                # Update trailing stop (never lower for LONG)
                if quick_tp_hit:
                    new_trail = c - atr_v * trailing_atr_mult
                    trailing_stop = max(trailing_stop, new_trail)

            else:  # SHORT
                # Quick TP hit?
                if not quick_tp_hit and l <= quick_tp and qty_quick > 0:
                    pnl = (entry_price - quick_tp) * qty_quick
                    pnl -= abs(pnl) * (commission_rate + slippage_rate)
                    equity += pnl
                    trades.append({"side": side, "pnl": pnl, "reason": "QUICK_TP"})
                    quick_tp_hit = True
                    trailing_stop = entry_price

                # Stop loss hit?
                if h >= (stop_loss if not quick_tp_hit else trailing_stop):
                    exit_price = stop_loss if not quick_tp_hit else trailing_stop
                    if not quick_tp_hit:
                        total_qty = qty_quick + qty_trail
                        pnl = (entry_price - exit_price) * total_qty
                        pnl -= abs(pnl) * (commission_rate + slippage_rate)
                        equity += pnl
                        trades.append({"side": side, "pnl": pnl, "reason": "SL_FULL"})
                    else:
                        pnl = (entry_price - exit_price) * qty_trail
                        pnl -= abs(pnl) * (commission_rate + slippage_rate)
                        equity += pnl
                        trades.append({"side": side, "pnl": pnl, "reason": "SL_TRAIL"})
                    in_trade = False
                    continue

                if quick_tp_hit:
                    new_trail = c + atr_v * trailing_atr_mult
                    trailing_stop = min(trailing_stop, new_trail)

        # --- New entry ---
        if not in_trade:
            if row["long_signal"]:
                entry_price = next_row["open"]
                sl_dist = atr_v * sl_atr_mult
                stop_loss = entry_price - sl_dist
                quick_tp = entry_price + sl_dist * quick_tp_rrr
                trailing_stop = stop_loss
                risk_amount = equity * risk_per_trade
                total_qty = risk_amount / sl_dist if sl_dist > 0 else 0
                qty_quick = total_qty * 0.5
                qty_trail = total_qty * 0.5
                quick_tp_hit = False
                if total_qty > 0:
                    side = "LONG"
                    in_trade = True

            elif row["short_signal"]:
                entry_price = next_row["open"]
                sl_dist = atr_v * sl_atr_mult
                stop_loss = entry_price + sl_dist
                quick_tp = entry_price - sl_dist * quick_tp_rrr
                trailing_stop = stop_loss
                risk_amount = equity * risk_per_trade
                total_qty = risk_amount / sl_dist if sl_dist > 0 else 0
                qty_quick = total_qty * 0.5
                qty_trail = total_qty * 0.5
                quick_tp_hit = False
                if total_qty > 0:
                    side = "SHORT"
                    in_trade = True

    # Stats
    if not trades:
        return {"n_trades": 0, "win_rate": 0, "pf": 0, "expectancy": 0, "max_dd": 0, "equity": equity}

    pnls = [t["pnl"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    running = initial_capital
    peak = running
    max_dd = 0
    for p in pnls:
        running += p
        peak = max(peak, running)
        dd = (peak - running) / peak
        max_dd = max(max_dd, dd)

    # Count trade setups (not individual exits)
    setup_count = sum(1 for t in trades if t["reason"] in ("SL_FULL", "QUICK_TP"))

    return {
        "n_trades": len(trades),
        "n_setups": setup_count,
        "win_rate": len(wins) / len(trades) if trades else 0,
        "pf": sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else float("inf"),
        "expectancy": sum(pnls) / len(pnls),
        "max_dd": max_dd,
        "equity": equity,
        "total_pnl": sum(pnls),
    }


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    micro_path = os.path.join(data_dir, "BTCUSDT_5m_3M.parquet")

    if not os.path.exists(micro_path):
        print("ERROR: Data not found.")
        return

    print("Loading data...")
    df = pd.read_parquet(micro_path)
    print(f"Loaded {len(df)} bars ({df.index[0]} → {df.index[-1]})")

    print("Pre-computing indicators...")
    df = compute_signals(df)
    signal_count = int(df["long_signal"].sum() + df["short_signal"].sum())
    print(f"Total raw signals: {signal_count}")

    # Test configurations
    configs = {
        "Fixed TP 1.0R": {"quick_tp_rrr": 1.0, "trailing_atr_mult": 999},  # no trail (huge value = never trails)
        "Hybrid 1R+Trail": {"quick_tp_rrr": 1.0, "trailing_atr_mult": 1.5},
        "Hybrid 1R+Tight": {"quick_tp_rrr": 1.0, "trailing_atr_mult": 1.0},
        "Pure Trail 1.5ATR": {"quick_tp_rrr": 999, "trailing_atr_mult": 1.5},  # no quick TP
    }

    t = PrettyTable()
    t.field_names = ["Metric"] + list(configs.keys())
    t.align["Metric"] = "l"

    results = {}
    for name, cfg in configs.items():
        print(f"  Running {name}...")
        results[name] = run_hybrid_exit_backtest(df, **cfg)

    names = list(configs.keys())
    t.add_row(["Win Rate"] + [f"{results[n]['win_rate']*100:.1f}%" for n in names])
    t.add_row(["Profit Factor"] + [f"{results[n]['pf']:.2f}" for n in names])
    t.add_row(["Expectancy"] + [f"${results[n]['expectancy']:.2f}" for n in names])
    t.add_row(["Max Drawdown"] + [f"{results[n]['max_dd']*100:.1f}%" for n in names])
    t.add_row(["Trade Events"] + [results[n]["n_trades"] for n in names])
    t.add_row(["Total PNL"] + [f"${results[n]['total_pnl']:,.2f}" for n in names])
    t.add_row(["Final Equity"] + [f"${results[n]['equity']:,.2f}" for n in names])

    print("\n" + "=" * 90)
    print("     TRAP MODEL: EXIT STRATEGY COMPARISON (3 Months)")
    print("=" * 90)
    print(t)
    print("=" * 90)


if __name__ == "__main__":
    main()
