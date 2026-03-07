#!/usr/bin/env python3
"""
Phase 4.2: Institutional PSO WITHOUT Layer B
============================================
Goal: Test hypothesis that Layer B is bottleneck.

- Uses raw setups (no Layer B filtering)
- Fixed structure: Gate + Linear Score
- Temporal split: 60/20/20 (Train/Val/OOS)
- Regularization: L2 on weights
- Weight bounds: [-1, 1]
- Reports metrics on Train/Val/OOS
- Optional: permutation test on OOS
"""

import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


FEATURES = [
    "atr_pct",
    "vol_z",
    "taker_buy_ratio",
    "tbr_delta",
    "range_pct",
    "rsi_slope",
    "ema_trend_dir",
]
N_FEATURES = len(FEATURES)

# -----------------------------
# Feature extraction
# -----------------------------
def extract_features(setup: Dict) -> np.ndarray:
    return np.array([
        float(setup.get("atr_pct", 0.0)),
        float(setup.get("vol_z", 0.0)),
        float(setup.get("taker_buy_ratio", 0.5)),
        float(setup.get("tbr_delta", 0.0)),
        float(setup.get("range_pct", 0.0)),
        float(setup.get("rsi_slope", 0.0)),
        float(setup.get("ema_trend_dir", 0.0)),
    ], dtype=np.float32)

# -----------------------------
# Policy (Gate + Linear Score)
# -----------------------------
@dataclass
class Policy:
    weights: np.ndarray      # (7,)
    threshold: float
    gate_atr: float          # reject if atr_pct > gate_atr

    def __call__(self, x: np.ndarray) -> Tuple[bool, float]:
        if x[0] > self.gate_atr:
            return False, 0.0
        score = float(np.dot(self.weights, x))
        return (score > self.threshold), score

    def to_dict(self) -> Dict:
        return {
            "features": FEATURES,
            "weights": self.weights.tolist(),
            "threshold": float(self.threshold),
            "gate_atr": float(self.gate_atr),
        }

# -----------------------------
# Evaluator (NO Layer B)
# -----------------------------
class Evaluator:
    def __init__(self, setups: List[Dict]):
        self.setups = setups

    @staticmethod
    def r_multiple(setup: Dict) -> Optional[float]:
        sig = setup.get("signal")
        out = setup.get("outcome")
        entry = float(setup.get("entry_price", 0) or 0)
        sl = float(setup.get("stop_loss", 0) or 0)
        tp = float(setup.get("take_profit", 0) or 0)
        if not sig or not out or entry <= 0 or sl <= 0 or tp <= 0:
            return None

        if sig == "LONG":
            risk = entry - sl
            pnl = (tp - entry) if out == "WIN" else (sl - entry)  # loss negative
        elif sig == "SHORT":
            risk = sl - entry
            pnl = (entry - tp) if out == "WIN" else (entry - sl)  # loss negative
        else:
            return None

        if risk <= 0:
            return None
        return pnl / risk

    def evaluate(self, policy: Policy, data: List[Dict], name: str) -> Dict:
        trades=wins=losses=0
        win_r=loss_r=total_r=0.0
        equity=100.0; peak=equity; max_dd=0.0

        for s in data:
            x = extract_features(s)
            passed, _ = policy(x)
            if not passed:
                continue
            r = self.r_multiple(s)
            if r is None:
                continue

            trades += 1
            total_r += r
            equity += r
            if equity > peak: peak = equity
            dd = (peak - equity)/peak if peak>0 else 0.0
            if dd > max_dd: max_dd = dd

            if r > 0:
                wins += 1
                win_r += r
            else:
                losses += 1
                loss_r += abs(r)

        pf = (win_r / loss_r) if loss_r > 0 else (0.0 if win_r <= 0 else 99.0)
        wr = (wins / trades * 100.0) if trades else 0.0
        exp = (total_r / trades) if trades else 0.0

        return {
            "window": name,
            "n_trades": trades,
            "wins": wins,
            "losses": losses,
            "winrate": wr,
            "pf": pf,
            "total_r": total_r,
            "expectancy_r": exp,
            "max_dd": max_dd * 100.0,
        }

    def fitness(
        self,
        policy: Policy,
        train: List[Dict],
        val: List[Dict],
        *,
        min_trades_train: int = 30,
        min_trades_val: int = 10,
        pf_cap: float = 3.0,
        dd_kill: float = 30.0,
        l2_lambda: float = 0.05,
    ) -> float:
        a = self.evaluate(policy, train, "TRAIN")
        b = self.evaluate(policy, val, "VAL")

        # Hard kills (both windows matter)
        if a["n_trades"] < min_trades_train:
            return 0.0
        if b["n_trades"] < min_trades_val:
            return 0.0
        if a["pf"] <= 1.0:
            return 0.0
        if a["max_dd"] > dd_kill:
            return 0.0

        def score(res: Dict) -> float:
            pf_norm = min(res["pf"], pf_cap) / pf_cap
            exp_norm = np.tanh(res["expectancy_r"] * 2.0)
            dd_pen = np.exp(-res["max_dd"] / 10.0)
            n_bonus = min(res["n_trades"] / 60.0, 1.0)
            return float(0.45*pf_norm + 0.30*exp_norm + 0.15*dd_pen + 0.10*n_bonus)

        sa = score(a)
        sb = score(b)

        base = 0.7*sa + 0.3*sb
        stability = min(sa, sb) / max(sa, sb, 1e-9)

        # L2 regularization on weights (prevents boundary solutions)
        reg = l2_lambda * float(np.sum(policy.weights**2))

        return max(0.0, base * stability - reg)

# -----------------------------
# PSO
# -----------------------------
class PSO:
    def __init__(self, evaluator: Evaluator, train: List[Dict], val: List[Dict],
                 n_particles=40, max_iter=80, w=0.7, c1=1.5, c2=1.5):
        self.ev = evaluator
        self.train = train
        self.val = val

        self.n_particles = n_particles
        self.max_iter = max_iter
        self.w=w; self.c1=c1; self.c2=c2

        self.dim = N_FEATURES + 2  # weights + threshold + gate_atr
        self.lb = np.array([-1.0]*N_FEATURES + [-5.0, 0.0], dtype=np.float32)
        self.ub = np.array([ 1.0]*N_FEATURES + [ 5.0, 0.02], dtype=np.float32)

        self.pos = np.random.uniform(self.lb, self.ub, (n_particles, self.dim)).astype(np.float32)
        self.vel = np.random.uniform(-1, 1, (n_particles, self.dim)).astype(np.float32) * (self.ub-self.lb)*0.1

        self.pbest_pos = self.pos.copy()
        self.pbest_fit = np.zeros(n_particles, dtype=np.float32)
        self.gbest_pos = None
        self.gbest_fit = 0.0

    def to_policy(self, p: np.ndarray) -> Policy:
        return Policy(weights=p[:N_FEATURES], threshold=float(p[N_FEATURES]), gate_atr=float(p[N_FEATURES+1]))

    def optimize(self) -> Tuple[Policy, float]:
        # init
        for i in range(self.n_particles):
            fit = self.ev.fitness(self.to_policy(self.pos[i]), self.train, self.val)
            self.pbest_fit[i] = fit
            if fit > self.gbest_fit:
                self.gbest_fit = fit
                self.gbest_pos = self.pos[i].copy()

        for it in range(self.max_iter):
            for i in range(self.n_particles):
                r1 = np.random.random(self.dim).astype(np.float32)
                r2 = np.random.random(self.dim).astype(np.float32)
                self.vel[i] = (
                    self.w*self.vel[i]
                    + self.c1*r1*(self.pbest_pos[i]-self.pos[i])
                    + self.c2*r2*(self.gbest_pos-self.pos[i])
                )
                self.pos[i] = np.clip(self.pos[i] + self.vel[i], self.lb, self.ub)

                fit = self.ev.fitness(self.to_policy(self.pos[i]), self.train, self.val)
                if fit > self.pbest_fit[i]:
                    self.pbest_fit[i] = fit
                    self.pbest_pos[i] = self.pos[i].copy()
                if fit > self.gbest_fit:
                    self.gbest_fit = fit
                    self.gbest_pos = self.pos[i].copy()

            if (it+1) % 10 == 0:
                print(f"Iter {it+1:3d}/{self.max_iter} | best={self.gbest_fit:.4f} | avg={float(np.mean(self.pbest_fit)):.4f}")

        return self.to_policy(self.gbest_pos), float(self.gbest_fit)

# -----------------------------
# Permutation test (OOS)
# -----------------------------
def permutation_test_pf(oos_trades_r: List[float], n=500, seed=42) -> float:
    """
    Permute trade outcomes (signs) to estimate how often PF>=observed happens by chance.
    Returns p_value (smaller is better).
    """
    rng = np.random.default_rng(seed)
    arr = np.array(oos_trades_r, dtype=np.float32)
    if len(arr) < 20:
        return 1.0

    def pf_from_r(rvals: np.ndarray) -> float:
        wins = rvals[rvals > 0].sum()
        losses = np.abs(rvals[rvals < 0]).sum()
        return float(wins / losses) if losses > 0 else (99.0 if wins > 0 else 0.0)

    observed = pf_from_r(arr)
    count = 0
    for _ in range(n):
        signs = rng.choice([-1.0, 1.0], size=len(arr))
        perm = np.abs(arr) * signs
        if pf_from_r(perm) >= observed:
            count += 1
    return (count + 1) / (n + 1)

# -----------------------------
# Main
# -----------------------------
def main():
    data_file = Path("/home/noogh/projects/noogh_unified_system/src/data/backtest_setups_12M.jsonl")
    setups = []
    with open(data_file, "r") as f:
        for line in f:
            if line.strip():
                setups.append(json.loads(line))

    # temporal sort
    setups.sort(key=lambda x: x.get("timestamp", ""))

    n = len(setups)
    if n < 200:
        print("Not enough setups for 60/20/20")
        return

    i1 = int(n * 0.60)
    i2 = int(n * 0.80)
    train = setups[:i1]
    val = setups[i1:i2]
    oos = setups[i2:]

    ev = Evaluator(setups)

    print(f"Total={n} | Train={len(train)} | Val={len(val)} | OOS={len(oos)}")

    pso = PSO(ev, train, val, n_particles=40, max_iter=80)
    best_policy, best_fit = pso.optimize()

    print("\nBEST FITNESS:", best_fit)
    print("POLICY:", best_policy.to_dict())

    r_train = ev.evaluate(best_policy, train, "TRAIN")
    r_val   = ev.evaluate(best_policy, val, "VAL")
    r_oos   = ev.evaluate(best_policy, oos, "OOS")

    print("\nRESULTS:")
    for r in (r_train, r_val, r_oos):
        print(r)

    # collect OOS trade R list for permutation
    # quick re-run to collect r values:
    oos_r = []
    for s in oos:
        x = extract_features(s)
        passed,_ = best_policy(x)
        if not passed:
            continue
        r = ev.r_multiple(s)
        if r is None:
            continue
        oos_r.append(float(r))

    p = permutation_test_pf(oos_r, n=500)
    print(f"\nPermutation p-value (OOS PF): {p:.4f}  (want < 0.05)")

    # save
    out = Path("/home/noogh/projects/noogh_unified_system/src/data/params_NO_LAYER_B.json")
    with open(out, "w") as f:
        json.dump(best_policy.to_dict(), f, indent=2)
    print("Saved:", out)

if __name__ == "__main__":
    np.random.seed(42)
    main()
