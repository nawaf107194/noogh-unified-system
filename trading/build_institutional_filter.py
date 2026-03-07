#!/usr/bin/env python3
"""
NOOGH Quant Layer B (Institutional Grade)
Chronological Walk-Forward Logistic Regression
"""

import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score


# =====================================================
# Load
# =====================================================

def load_data(file_path):
    rows = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


# =====================================================
# Feature Engineering
# =====================================================

def build_matrix(df):
    df = df.copy()
    df['target'] = (df['outcome'] == 'WIN').astype(int)
    df['is_long'] = (df['signal'] == 'LONG').astype(int)

    # Approximate PnL using TP/SL distances
    def calc_pnl(row):
        if row['outcome'] == 'WIN':
            return abs(row['take_profit'] - row['entry_price']) / row['entry_price'] * 100
        else:
            return -abs(row['entry_price'] - row['stop_loss']) / row['entry_price'] * 100
            
    if 'pnl' not in df.columns:
        df['pnl'] = df.apply(calc_pnl, axis=1)

    features = ['atr', 'volume', 'taker_buy_ratio', 'rsi', 'is_long']

    for f in features:
        df[f] = df[f].fillna(df[f].median())

    return df[features + ['target', 'pnl']]


# =====================================================
# Walk Forward Validation
# =====================================================

def walk_forward_validation(X, y):
    tscv = TimeSeriesSplit(n_splits=5)
    auc_scores = []
    oof_preds = np.zeros(len(y))

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = LogisticRegression(
            C=0.5,
            class_weight='balanced',
            random_state=42,
            max_iter=1000
        )

        model.fit(X_train, y_train)
        preds = model.predict_proba(X_test)[:, 1]
        oof_preds[test_idx] = preds

        auc = roc_auc_score(y_test, preds)
        auc_scores.append(auc)
        print(f"Fold {fold+1} ROC AUC: {auc:.3f}")

    print(f"\nAverage Walk-Forward ROC AUC: {np.mean(auc_scores):.3f}")

    return oof_preds


# =====================================================
# Threshold Calibration (Expectancy Based)
# =====================================================

def threshold_analysis(probas, y, pnl):
    print("\nThreshold | Trades | WinRate | PF Approx | Expectancy")
    print("-" * 65)

    best_threshold = 0.5
    best_expectancy = -999

    for t in np.arange(0.40, 0.85, 0.05):
        mask = probas >= t
        trades = mask.sum()

        if trades < 20:
            continue

        winrate = y[mask].mean()
        
        wins = pnl[(mask) & (y == 1)]
        losses = pnl[(mask) & (y == 0)]
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0

        expectancy = (winrate * avg_win) - ((1 - winrate) * avg_loss)

        pf = (winrate * avg_win) / ((1 - winrate) * avg_loss) if avg_loss > 0 else 1.0

        print(f"{t:.2f}\t  | {trades}\t   | {winrate:.2f}\t   | {pf:.2f}\t     | {expectancy:.4f}")

        if expectancy > best_expectancy:
            best_expectancy = expectancy
            best_threshold = t

    print("-" * 65)
    print(f"🚀 Optimal Threshold (Expectancy-Based): {best_threshold:.2f}")

    return best_threshold


# =====================================================
# Main
# =====================================================

def main():
    path = "/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl"

    df_raw = load_data(path)
    print(f"Total Trades: {len(df_raw)}")

    df = build_matrix(df_raw)

    X = df.drop(columns=['target', 'pnl'])
    y = df['target']
    pnl = df['pnl']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("\n=== WALK FORWARD VALIDATION ===")
    oof_preds = walk_forward_validation(X_scaled, y)

    print("\n=== THRESHOLD ANALYSIS ===")
    
    # We only analyze OOF predictions for the validated parts
    # First fold training logic leaves the very first block without OOF predictions?
    # oof_preds is 0 for the first train block. We'll only analyze trades that have OOF preds
    valid_idx = oof_preds > 0 
    
    best_threshold = threshold_analysis(oof_preds[valid_idx], y[valid_idx], pnl[valid_idx])

    print("\nFeature Coefficients (Odds Ratios) on Full Dataset:")

    final_model = LogisticRegression(
        C=0.5,
        class_weight='balanced',
        random_state=42,
        max_iter=1000
    )

    final_model.fit(X_scaled, y)

    odds = np.exp(final_model.coef_[0])

    # --- FINAL DUMP TO JSON ---
    print("\nSaving Layer B institutional model to layer_b_model.json...")
    import json
    import os
    
    layer_b_data = {
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "coef": final_model.coef_[0].tolist(),
        "intercept": final_model.intercept_[0],
        "threshold": best_threshold,
        "features": list(X.columns)
    }
    
    with open(os.path.join(os.path.dirname(path), "layer_b_model.json"), "w") as f:
        json.dump(layer_b_data, f, indent=4)
        
    print("Model saved successfully. Layer B is ready for production.")

if __name__ == "__main__":
    main()
