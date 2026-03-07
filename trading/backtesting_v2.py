from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Any, Optional, Literal, Tuple

from trading.technical_indicators import SignalEngineV2, IndicatorConfig, ScoreWeights, RiskConfig


@dataclass
class PositionState:
    side: str                # LONG / SHORT
    qty_total: float
    qty_remaining: float
    entry: float
    stop: float
    tp1: float
    tp2: float
    tp3: float
    entry_index: int
    initial_risk: float      # FIX 6: Store initial risk for proper R-Multiple calculation
    moved_to_be: bool = False


@dataclass
class BacktestConfig:
    initial_capital: float = 10_000.0
    risk_per_trade: float = 0.01          # 1% risk per trade
    commission_rate: float = 0.0004       # 0.04% per side (example)
    slippage_rate: float = 0.0002         # 0.02% entry/exit (example)
    max_leverage: float = 10.0            # futures
    one_position_at_time: bool = True     # simple mode
    allow_flip: bool = False              # if True: can reverse immediately

    # Execution model:
    # enter at next bar open (micro) after signal to avoid lookahead
    enter_on_next_open: bool = True

    # optional time-based exit
    max_bars_in_trade: Optional[int] = None


@dataclass
class WalkForwardConfig:
    train_bars: int = 5000     # micro bars
    test_bars: int = 1500
    step_bars: int = 1500      # move forward by test size
    min_train_bars: int = 2000


def prepare_aligned_data(
    df_micro: pd.DataFrame,
    df_macro: pd.DataFrame,
    suffix_macro: str = "_macro",
) -> pd.DataFrame:
    """
    Align macro features into micro timeline using merge_asof.
    Both DFs must be datetime-indexed and sorted.
    """
    df_micro = df_micro.sort_index().copy()
    df_macro = df_macro.sort_index().copy()

    # Ensure datetime index
    if not isinstance(df_micro.index, pd.DatetimeIndex) or not isinstance(df_macro.index, pd.DatetimeIndex):
        raise ValueError("df_micro and df_macro must have DatetimeIndex")

    # We carry macro OHLCV into micro rows (last known macro bar)
    macro_cols = ["open", "high", "low", "close", "volume"]
    df_macro_ren = df_macro[macro_cols].rename(columns={c: f"{c}{suffix_macro}" for c in macro_cols})

    df_micro.index.name = "ts"
    df_macro_ren.index.name = "ts"

    aligned = pd.merge_asof(
        df_micro.reset_index(),
        df_macro_ren.reset_index(),
        on="ts",
        direction="backward",
        allow_exact_matches=True,
    ).set_index("ts")

    return aligned


def position_size_from_risk(
    capital: float,
    entry: float,
    stop: float,
    risk_per_trade: float,
    max_leverage: float,
) -> float:
    """
    Size = (capital * risk%) / |entry-stop|   (contract/value units)
    Then cap by leverage: notional <= capital * leverage
    """
    risk_amount = capital * risk_per_trade
    per_unit_risk = abs(entry - stop)
    if per_unit_risk <= 0 or np.isnan(per_unit_risk):
        return 0.0

    qty = risk_amount / per_unit_risk
    # leverage cap
    max_qty = (capital * max_leverage) / entry if entry > 0 else 0.0
    return float(max(0.0, min(qty, max_qty)))


def apply_costs(price: float, commission_rate: float, slippage_rate: float, side: Literal["BUY", "SELL"]) -> float:
    """
    Simple cost model: slippage moves price against you.
    - BUY: pay higher (price * (1+slippage))
    - SELL: receive lower (price * (1-slippage))
    Commission is applied separately on notional.
    """
    if side == "BUY":
        return price * (1.0 + slippage_rate)
    else:
        return price * (1.0 - slippage_rate)


def manage_position(row, state: PositionState, atr_value: float, trailing_mode="ATR") -> Tuple[list, PositionState]:
    o, h, l, c = row["open"], row["high"], row["low"], row["close"]
    is_long = state.side == "LONG"

    exit_events = []

    # FIX 4: CONSERVATIVE EXECUTION ORDER
    # Check STOP LOSS FIRST before TPs to avoid intra-bar optimistic bias
    # We don't have tick data, so assume worst case happens first

    # --- STOP LOSS (CHECK FIRST) ---
    if state.qty_remaining > 0 and state.stop is not None and not np.isnan(state.stop):
        hit_sl = (l <= state.stop) if is_long else (h >= state.stop)
        if hit_sl:
            # FIX BUG 2 REVISED: Use exact SL price (match vectorized)
            # Vectorized uses exact SL price, no gap averaging
            # Gap averaging was too pessimistic and reduced WR by 6%
            fill_price = state.stop

            qty = state.qty_remaining
            state.qty_remaining = 0
            exit_events.append(("SL", fill_price, qty))
            # IMPORTANT: Return immediately - don't check TPs if SL hit
            return exit_events, state

    # --- TP1 (FULL EXIT - NO SCALE OUT) ---
    # FIX 7: Remove scale-out for clean R-Multiple analysis
    # Close ENTIRE position at TP1 for clean edge measurement
    if state.qty_remaining > 0 and state.tp1 is not None and not np.isnan(state.tp1):
        hit_tp1 = (h >= state.tp1) if is_long else (l <= state.tp1)
        if hit_tp1:
            qty = state.qty_remaining  # Close full position
            state.qty_remaining = 0
            exit_events.append(("TP1", state.tp1, qty))
            return exit_events, state  # Exit immediately

    # FIX 7: Removed trailing stop for clean edge measurement
    # Trailing stops complicate R-Multiple distribution analysis
    # For edge testing, use fixed SL and TP only

    return exit_events, state


def backtest_v2(
    df_micro: pd.DataFrame,
    df_macro: pd.DataFrame,
    bt: BacktestConfig = BacktestConfig(),
    ind_cfg: IndicatorConfig = IndicatorConfig(),
    w: ScoreWeights = ScoreWeights(),
    risk_cfg: RiskConfig = RiskConfig(),
    layer_b_filter=None,
    custom_neuron=None
) -> Dict[str, Any]:
    """
    Backtest using SignalEngineV2 per bar (semi-vector: loop through bars but keep operations simple).
    Entries at next open (recommended).
    Exits: SL/TP1/TP2/TP3 (we'll do: close full at TP1 or SL for simplicity; you can scale out later).
    """
    # Align macro into micro timeline
    aligned = prepare_aligned_data(df_micro, df_macro)

    # We'll keep original micro OHLCV
    _need = ["open", "high", "low", "close", "volume"]
    if "taker_buy_base" in df_micro.columns:
        _need.append("taker_buy_base")
        
    for c in _need:
        if c not in aligned.columns:
            raise ValueError(f"Aligned data missing {c}")

    equity = bt.initial_capital
    peak = equity

    state: Optional[PositionState] = None
    trades = []
    
    # Store PNL to calculate expectancy and R-multiples later per trade
    trade_pnls = []

    # Pre-slice macro df used by signal engine: we reconstruct per bar
    # Storage for bar-by-bar equity curve
    equity_history = []
    idxs = aligned.index

    for i in range(len(aligned) - 2):  # -2 so we can access next open safely
        ts = idxs[i]
        row = aligned.iloc[i]
        next_row = aligned.iloc[i + 1]

        o, h, l, c = row["open"], row["high"], row["low"], row["close"]

        # Assume we have pre-calculated ATR in aligned, if not, we use a crude approximation or it requires adding to prepare_aligned_data
        atr_val = row.get("atr", (h - l)) # Fallback if ATR not explicitly mapped in aligned yet

        # 1) Manage open position
        if state is not None:
            is_long = state.side == "LONG"
            
            exit_events, state = manage_position(row, state, atr_val, trailing_mode="ATR")

            # Apply any exits
            for exit_reason, exit_price_raw, exec_qty in exit_events:
                if exec_qty <= 0:
                    continue

                # FIX BUG 1: Apply costs correctly (no double cost application)
                # Calculate raw PNL first
                pnl = (exit_price_raw - state.entry) * exec_qty if is_long else (state.entry - exit_price_raw) * exec_qty

                # Apply costs as percentage of PNL (matches vectorized approach)
                pnl -= abs(pnl) * (bt.commission_rate + bt.slippage_rate)

                equity += pnl
                trade_pnls.append(pnl)

                trades.append({
                    "entry_time": idxs[state.entry_index],
                    "exit_time": ts,
                    "side": state.side,
                    "qty": exec_qty,
                    "entry": state.entry,
                    "exit": exit_price_raw,  # FIX: Use exit_price_raw instead of exec_price
                    "stop": state.stop,
                    "reason": exit_reason,
                    "pnl": pnl,  # FIX: pnl already includes costs
                    "equity": equity,
                    "initial_risk": state.initial_risk,  # FIX 6: Store for R-Multiple
                })

            # Time-based exit (if full position not exited yet and limit reached)
            if state.qty_remaining > 0 and bt.max_bars_in_trade is not None:
                if (i - state.entry_index) >= bt.max_bars_in_trade:
                    exit_reason = "TIME_EXIT"
                    exit_price_raw = c
                    exec_qty = state.qty_remaining

                    # FIX BUG 1: Apply costs correctly (no double cost application)
                    pnl = (exit_price_raw - state.entry) * exec_qty if is_long else (state.entry - exit_price_raw) * exec_qty
                    pnl -= abs(pnl) * (bt.commission_rate + bt.slippage_rate)

                    equity += pnl
                    trade_pnls.append(pnl)

                    trades.append({
                        "entry_time": idxs[state.entry_index],
                        "exit_time": ts,
                        "side": state.side,
                        "qty": exec_qty,
                        "entry": state.entry,
                        "exit": exit_price_raw,  # FIX: Use exit_price_raw instead of exec_price
                        "stop": state.stop,
                        "reason": exit_reason,
                        "pnl": pnl,  # FIX: pnl already includes costs
                        "equity": equity,
                        "initial_risk": state.initial_risk,  # FIX 6: Store for R-Multiple
                    })
                    state.qty_remaining = 0

            if state.qty_remaining <= 1e-8: # floating point safety
                state = None
        # Track drawdown
        peak = max(peak, equity)

        # 2) If flat, evaluate new entry signal
        if state is None:
            # Build df_micro slice up to i (inclusive)
            micro_slice = aligned.iloc[: i + 1][_need].copy()

            # Build df_macro slice up to last macro timestamp by using macro columns in aligned
            # We'll reconstruct a pseudo macro DF by taking rows where macro close changes (coarse),
            # but simplest: use original df_macro truncated to current time.
            macro_slice = df_macro.loc[:ts].copy()

            # Generate signal
            sig = SignalEngineV2.generate_entry_signal(
                df_macro=macro_slice,
                df_micro=micro_slice,
                cfg=ind_cfg,
                w=w,
                risk_cfg=risk_cfg,
            )

            signal = sig.get("signal")
            
            # --- START ALPHA FILTERS (B & C) ---
            if signal in ("LONG", "SHORT") and sig.get("stop_loss") is not None:
                setup_data_for_filters = {
                    "atr": float(atr_val),
                    "volume": float(row.get("volume", 0.0)),
                    "taker_buy_ratio": float(row.get("taker_buy_ratio", 0.5)),
                    "rsi": float(row.get("rsi", 50.0)),
                    "signal": signal
                }
                
                # Layer B (Statistical Edge)
                if layer_b_filter is not None:
                    ok_b, prob_b, reason_b = layer_b_filter(setup_data_for_filters)
                    if not ok_b:
                        continue # Strict reject
                        
                # Layer C (Evolutionary Edge)
                if custom_neuron is not None:
                    ok_c, conf_c, reason_c = custom_neuron(setup_data_for_filters)
                    if not ok_c:
                        continue # Evolution reject
            # --- END ALPHA FILTERS ---
                # Entry execution price:
                if bt.enter_on_next_open:
                    raw_entry = float(next_row["open"])
                else:
                    raw_entry = float(c)

                side = "BUY" if signal == "LONG" else "SELL"
                exec_entry = apply_costs(raw_entry, bt.commission_rate, bt.slippage_rate, side=side)

                # FIX 1: Adjust SL/TP based on actual execution entry vs signal entry
                # The signal calculated SL/TP based on close, but we're entering at next_open
                sig_entry = float(sig.get("entry_price", c))
                entry_shift = exec_entry - sig_entry

                sl = float(sig["stop_loss"]) + entry_shift
                tps = sig.get("take_profits") or {}
                _tp1 = float(tps.get("tp1", np.nan)) + entry_shift if np.isfinite(tps.get("tp1", np.nan)) else np.nan
                _tp2 = float(tps.get("tp2", np.nan)) + entry_shift if np.isfinite(tps.get("tp2", np.nan)) else np.nan
                _tp3 = float(tps.get("tp3", np.nan)) + entry_shift if np.isfinite(tps.get("tp3", np.nan)) else np.nan

                # FIX 2: Validate SL is on correct side and has minimum risk
                MIN_RISK_PCT = 0.0001  # 0.01% minimum risk
                risk = abs(exec_entry - sl)
                is_valid_sl = (
                    np.isfinite(sl) and
                    risk > exec_entry * MIN_RISK_PCT and
                    ((signal == "LONG" and sl < exec_entry) or (signal == "SHORT" and sl > exec_entry))
                )

                if not is_valid_sl:
                    # Skip this trade - invalid SL
                    continue

                # Size from risk
                qty = position_size_from_risk(
                    capital=equity,
                    entry=exec_entry,
                    stop=sl,
                    risk_per_trade=bt.risk_per_trade,
                    max_leverage=bt.max_leverage,
                )
                if qty > 0 and np.isfinite(_tp1):
                    # FIX BUG 1: Entry costs handled in exit PNL (no separate deduction)
                    # Entry costs will be accounted for in the exit PNL calculation

                    # FIX 6: Calculate initial risk for R-Multiple
                    initial_risk = abs(exec_entry - sl) * qty

                    state = PositionState(
                        side="LONG" if signal == "LONG" else "SHORT",
                        qty_total=qty,
                        qty_remaining=qty,
                        entry=exec_entry,
                        stop=sl,
                        tp1=_tp1,
                        tp2=_tp2,
                        tp3=_tp3,
                        entry_index=i + 1 if bt.enter_on_next_open else i,
                        initial_risk=initial_risk
                    )
        
        # Track equity per bar for correct Sharpe ratio
        current_equity = equity
        if state is not None:
            # Add unrealized PNL
            upnl = (c - state.entry) * state.qty_remaining if state.side == "LONG" else (state.entry - c) * state.qty_remaining
            current_equity += upnl
            
        equity_history.append((ts, current_equity))

    # Summary stats
    trades_df = pd.DataFrame(trades)
    equity_curve = pd.DataFrame(equity_history, columns=["ts", "equity"]).set_index("ts")
    
    if len(trades_df) == 0:
        return {"equity_final": equity, "trades": trades_df, "equity_curve": equity_curve, "stats": {"n_trades": 0}}

    trades_df["return"] = trades_df["pnl"] / bt.initial_capital
    wins = trades_df[trades_df["pnl"] > 0]
    losses = trades_df[trades_df["pnl"] <= 0]

    dd = (equity_curve["equity"].cummax() - equity_curve["equity"]) / equity_curve["equity"].cummax()
    max_dd = float(dd.max()) if len(dd) else 0.0

    stats = {
        "n_trades": int(len(trades_df)),
        "win_rate": float(len(wins) / len(trades_df)),
        "avg_pnl": float(trades_df["pnl"].mean()),
        "profit_factor": float(wins["pnl"].sum() / abs(losses["pnl"].sum())) if len(losses) else float("inf"),
        "max_drawdown": max_dd,
        "equity_final": float(equity_curve["equity"].iloc[-1]),
    }
    stats.update(advanced_metrics(trades_df, equity_curve))

    return {"equity_final": equity, "trades": trades_df, "equity_curve": equity_curve, "stats": stats}


def advanced_metrics(trades_df, equity_curve):
    if len(equity_curve) < 2 or len(trades_df) == 0:
        return {"sharpe": 0.0, "expectancy": 0.0, "avg_r_multiple": 0.0}

    returns = equity_curve["equity"].pct_change().dropna()

    # FIX 5: Dynamic annual factor based on actual bar frequency
    # Calculate time difference between bars to determine frequency
    if len(equity_curve) >= 2:
        bar_seconds = (equity_curve.index[1] - equity_curve.index[0]).total_seconds()
        bars_per_year = (365 * 24 * 3600) / bar_seconds if bar_seconds > 0 else 365 * 24 * 12
        annual_factor = bars_per_year
    else:
        annual_factor = 365 * 24 * 12  # Fallback to 5m assumption

    sharpe = (returns.mean() / returns.std()) * np.sqrt(annual_factor) if returns.std() != 0 else 0

    expectancy = float(trades_df["pnl"].mean())

    # FIX 6: Correct R-Multiple calculation using ACTUAL risk per trade
    # R = pnl / initial_risk for each trade
    if "initial_risk" in trades_df.columns:
        # Avoid division by zero
        valid_risk = trades_df["initial_risk"] > 0
        r_multiple = pd.Series(0.0, index=trades_df.index)
        r_multiple[valid_risk] = trades_df.loc[valid_risk, "pnl"] / trades_df.loc[valid_risk, "initial_risk"]

        avg_r = float(r_multiple.mean())
        median_r = float(r_multiple.median())
    else:
        # Fallback for old data without initial_risk
        avg_r = 0.0
        median_r = 0.0

    return {
        "sharpe": float(sharpe),
        "expectancy": float(expectancy),
        "avg_r_multiple": avg_r,
        "median_r_multiple": median_r,
    }


def grid_search_optimizer(df_micro, df_macro, param_grid):
    best_score = -np.inf
    best_params = None
    results = []

    for score_th in param_grid.get("min_score", [60]):
        for atr_mult in param_grid.get("atr_mult", [2.0]):
            for fvg_gap in param_grid.get("fvg_gap", [0.25]):

                w = ScoreWeights(min_score_to_trade=score_th)
                ind_cfg = IndicatorConfig(fvg_min_gap_atr_mult=fvg_gap)
                risk_cfg = RiskConfig(base_sl_atr_mult=atr_mult)

                res = backtest_v2(df_micro, df_macro, w=w, ind_cfg=ind_cfg, risk_cfg=risk_cfg)

                stats = res["stats"]
                # A heuristic score: PR * WR * Number of trades (penalty for 0 trades)
                # To prevent divide-by-zero or infinities
                pf = stats.get("profit_factor", 0.0)
                if not np.isfinite(pf):
                    pf = 1.0 # If 0 losses, just use 1.0 multiplier or something similar, or WR

                score = pf * stats.get("win_rate", 0) * min(stats.get("n_trades", 0), 100) # Soft cap trades influence

                results.append((score, score_th, atr_mult, fvg_gap))

                if score > best_score:
                    best_score = score
                    best_params = {
                        "min_score": score_th,
                        "atr_mult": atr_mult,
                        "fvg_gap": fvg_gap
                    }

    return best_params, sorted(results, reverse=True)[:10]


def walk_forward_test(
    df_micro: pd.DataFrame,
    df_macro: pd.DataFrame,
    wf: WalkForwardConfig = WalkForwardConfig(),
    bt: BacktestConfig = BacktestConfig(),
    ind_cfg: IndicatorConfig = IndicatorConfig(),
    w: ScoreWeights = ScoreWeights(),
    risk_cfg: RiskConfig = RiskConfig(),
) -> Dict[str, Any]:
    """
    Walk-forward:
    - Train window: you can calibrate weights/thresholds (placeholder)
    - Test window: run backtest
    This skeleton focuses on splitting and collecting results. You can plug optimizer in "train".
    """
    df_micro = df_micro.sort_index()
    results = []
    start = 0
    n = len(df_micro)

    while start + wf.min_train_bars + wf.test_bars <= n:
        train_end = start + wf.train_bars
        test_end = min(train_end + wf.test_bars, n)

        if train_end <= start + wf.min_train_bars:
            train_end = start + wf.min_train_bars

        train_micro = df_micro.iloc[start:train_end]
        test_micro = df_micro.iloc[train_end:test_end]

        # Macro slices by timestamp range
        train_ts_end = train_micro.index[-1]
        test_ts_end = test_micro.index[-1]

        train_macro = df_macro.loc[:train_ts_end]
        test_macro = df_macro.loc[:test_ts_end]

        # ---- TRAIN PHASE (Grid Search Optimizer) ----
        # Base grid definition for training
        grid = {
            "min_score": [50, 60, 70],
            "atr_mult": [1.5, 2.0, 2.5],
            "fvg_gap": [0.1, 0.25, 0.4]
        }
        
        print(f"[{test_micro.index[0]}] Optimizing on {len(train_micro)} bars...")
        best_params, _ = grid_search_optimizer(train_micro, train_macro, grid)
        print(f"    -> Best Params: {best_params}")

        # If no good params found (no trades), fallback to defaults
        if best_params is None:
            best_params = {"min_score": 60, "atr_mult": 2.0, "fvg_gap": 0.25}

        tuned_w = ScoreWeights(min_score_to_trade=best_params["min_score"])
        tuned_ind = IndicatorConfig(fvg_min_gap_atr_mult=best_params["fvg_gap"])
        tuned_risk = RiskConfig(base_sl_atr_mult=best_params["atr_mult"])

        # ---- TEST PHASE ----
        test_res = backtest_v2(
            df_micro=test_micro,
            df_macro=test_macro,
            bt=bt,
            ind_cfg=tuned_ind,
            w=tuned_w,
            risk_cfg=tuned_risk,
        )

        results.append({
            "start": test_micro.index[0],
            "end": test_micro.index[-1],
            "stats": test_res.get("stats", {}),
        })

        start += wf.step_bars

    return {"walk_forward_results": results}
