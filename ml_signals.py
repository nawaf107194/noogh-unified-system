#!/usr/bin/env python3
"""
NOOGH ML Trading Signal Pipeline
====================================
Point72/Cubist-style ML pipeline for crypto price prediction.

Features:
- 50+ engineered features from OHLCV data
- Label construction (forward returns, direction)
- Gradient Boosting from scratch (numpy-only)
- Purged K-Fold cross-validation (no lookahead)
- Feature importance analysis
- Model monitoring & degradation detection
- Signal generation

Usage:
    python3 ml_signals.py --symbol BTCUSDT --days 90 --horizon 5
    python3 ml_signals.py --symbol ETHUSDT --days 60 --horizon 3
"""

import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

import numpy as np
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')


# ═══════════════════════════════════════════════════════════════
# Section 1: Data Fetcher
# ═══════════════════════════════════════════════════════════════

def fetch_klines(symbol: str, interval: str = '1h', days: int = 90) -> Dict[str, np.ndarray]:
    BASE = "https://api.binance.com/api/v3"
    start = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    end = int(datetime.now().timestamp() * 1000)
    raw = []
    current = start
    logger.info(f"📊 Downloading {symbol} {interval} ({days}d)...")
    while current < end:
        r = requests.get(f"{BASE}/klines", params={
            'symbol': symbol, 'interval': interval,
            'startTime': current, 'endTime': end, 'limit': 1000
        }, timeout=10)
        if r.status_code != 200: break
        data = r.json()
        if not data: break
        raw.extend(data)
        current = data[-1][6] + 1
        time.sleep(0.1)
    
    logger.info(f"✅ {len(raw)} candles")
    return {
        'open': np.array([float(k[1]) for k in raw]),
        'high': np.array([float(k[2]) for k in raw]),
        'low': np.array([float(k[3]) for k in raw]),
        'close': np.array([float(k[4]) for k in raw]),
        'volume': np.array([float(k[5]) for k in raw]),
        'trades': np.array([int(k[8]) for k in raw]),
        'taker_buy': np.array([float(k[9]) for k in raw]),
        'quote_vol': np.array([float(k[7]) for k in raw]),
    }


# ═══════════════════════════════════════════════════════════════
# Section 2: Feature Engineering (50+ Features)
# ═══════════════════════════════════════════════════════════════

class FeatureEngineer:
    """
    Build 50+ features from OHLCV data.
    
    Categories:
    1. Returns & Momentum (10 features)
    2. Volatility (8 features)
    3. Volume Profile (8 features)
    4. Trend (8 features)
    5. Mean Reversion (6 features)
    6. Microstructure (6 features)
    7. Pattern (6 features)
    """
    
    FEATURE_NAMES = []
    
    @classmethod
    def build(cls, data: Dict[str, np.ndarray]) -> Tuple[np.ndarray, List[str]]:
        """Build feature matrix. Returns (X, feature_names)."""
        c, h, l, o = data['close'], data['high'], data['low'], data['open']
        v, trades = data['volume'], data['trades']
        taker = data['taker_buy']
        n = len(c)
        
        features = {}
        
        # ── 1. Returns & Momentum ──
        features['ret_1'] = cls._pct_change(c, 1)
        features['ret_3'] = cls._pct_change(c, 3)
        features['ret_5'] = cls._pct_change(c, 5)
        features['ret_10'] = cls._pct_change(c, 10)
        features['ret_20'] = cls._pct_change(c, 20)
        features['ret_cumsum_5'] = cls._rolling_sum(features['ret_1'], 5)
        features['ret_cumsum_10'] = cls._rolling_sum(features['ret_1'], 10)
        features['rsi_14'] = cls._rsi(c, 14)
        features['rsi_7'] = cls._rsi(c, 7)
        features['macd_hist'] = cls._macd_hist(c)
        
        # ── 2. Volatility ──
        features['vol_5'] = cls._rolling_std(features['ret_1'], 5)
        features['vol_10'] = cls._rolling_std(features['ret_1'], 10)
        features['vol_20'] = cls._rolling_std(features['ret_1'], 20)
        features['atr_14'] = cls._atr(h, l, c, 14)
        features['atr_ratio'] = features['atr_14'] / np.where(c > 0, c, 1) * 100
        features['hl_range'] = (h - l) / np.where(c > 0, c, 1) * 100
        features['vol_ratio_5_20'] = np.where(features['vol_20'] > 0,
                                               features['vol_5'] / features['vol_20'], 1)
        features['garman_klass'] = cls._garman_klass_vol(o, h, l, c, 20)
        
        # ── 3. Volume Profile ──
        features['vol_change'] = cls._pct_change(v, 1)
        features['vol_sma_ratio_5'] = v / cls._sma(v, 5)
        features['vol_sma_ratio_20'] = v / cls._sma(v, 20)
        features['taker_ratio'] = np.where(v > 0, taker / v, 0.5)
        features['trade_intensity'] = trades / cls._sma(trades, 20)
        features['obv_slope_5'] = cls._obv_slope(c, v, 5)
        features['obv_slope_10'] = cls._obv_slope(c, v, 10)
        features['volume_price_corr'] = cls._rolling_corr(v, c, 20)
        
        # ── 4. Trend ──
        features['ema_9_dist'] = (c - cls._ema(c, 9)) / np.where(c > 0, c, 1) * 100
        features['ema_21_dist'] = (c - cls._ema(c, 21)) / np.where(c > 0, c, 1) * 100
        features['sma_50_dist'] = (c - cls._sma(c, 50)) / np.where(c > 0, c, 1) * 100
        features['ema_cross_9_21'] = np.sign(cls._ema(c, 9) - cls._ema(c, 21))
        features['price_position'] = cls._price_position(c, 20)
        features['adx_14'] = cls._adx(h, l, c, 14)
        features['linear_slope_10'] = cls._linear_slope(c, 10)
        features['linear_slope_20'] = cls._linear_slope(c, 20)
        
        # ── 5. Mean Reversion ──
        features['z_score_10'] = cls._z_score(c, 10)
        features['z_score_20'] = cls._z_score(c, 20)
        features['z_score_50'] = cls._z_score(c, 50)
        features['bb_position'] = cls._bb_position(c, 20)
        features['dist_from_high_20'] = (c - cls._rolling_max(c, 20)) / np.where(c > 0, c, 1) * 100
        features['dist_from_low_20'] = (c - cls._rolling_min(c, 20)) / np.where(c > 0, c, 1) * 100
        
        # ── 6. Microstructure ──
        features['close_position'] = (c - l) / np.where(h - l > 0, h - l, 1)
        features['body_ratio'] = np.abs(c - o) / np.where(h - l > 0, h - l, 1)
        features['upper_shadow'] = (h - np.maximum(c, o)) / np.where(h - l > 0, h - l, 1)
        features['lower_shadow'] = (np.minimum(c, o) - l) / np.where(h - l > 0, h - l, 1)
        features['gap'] = (o[1:] - c[:-1]) / np.where(c[:-1] > 0, c[:-1], 1) * 100
        features['gap'] = np.append([0], features['gap'])
        features['vwap_dist'] = cls._vwap_distance(c, v, 20)
        
        # ── 7. Pattern ──
        features['higher_highs'] = cls._higher_highs(h, 5)
        features['lower_lows'] = cls._lower_lows(l, 5)
        features['inside_bar'] = ((h[1:] < h[:-1]) & (l[1:] > l[:-1])).astype(float)
        features['inside_bar'] = np.append([0], features['inside_bar'])
        features['engulfing'] = cls._engulfing(o, c)
        features['doji'] = (np.abs(c - o) / np.where(h - l > 0, h - l, 1) < 0.1).astype(float)
        features['three_bar_pattern'] = cls._three_bar_pattern(c)
        
        # Stack into matrix
        names = list(features.keys())
        cls.FEATURE_NAMES = names
        X = np.column_stack([features[name] for name in names])
        
        # Replace NaN/Inf
        X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)
        
        return X, names
    
    # ── Helper functions ──
    @staticmethod
    def _pct_change(a, n):
        r = np.zeros_like(a)
        r[n:] = (a[n:] / a[:-n] - 1) * 100
        return r
    
    @staticmethod
    def _rolling_sum(a, w):
        r = np.zeros_like(a)
        for i in range(w, len(a)): r[i] = np.sum(a[i-w:i])
        return r
    
    @staticmethod
    def _rolling_std(a, w):
        r = np.zeros_like(a)
        for i in range(w, len(a)): r[i] = np.std(a[i-w:i])
        return r
    
    @staticmethod
    def _sma(a, w):
        r = np.full_like(a, np.nan, dtype='f8')
        for i in range(w-1, len(a)): r[i] = np.mean(a[i-w+1:i+1])
        r = np.nan_to_num(r, nan=a[0] if len(a) > 0 else 0)
        return r
    
    @staticmethod
    def _ema(a, w):
        r = np.zeros_like(a, dtype='f8')
        r[0] = a[0]
        m = 2 / (w + 1)
        for i in range(1, len(a)): r[i] = (a[i] - r[i-1]) * m + r[i-1]
        return r
    
    @staticmethod
    def _rsi(a, w):
        r = np.full_like(a, 50.0)
        d = np.diff(a)
        g, l = np.where(d > 0, d, 0), np.where(d < 0, -d, 0)
        if len(d) < w: return r
        ag, al = np.mean(g[:w]), np.mean(l[:w])
        for i in range(w, len(d)):
            ag = (ag * (w-1) + g[i]) / w
            al = (al * (w-1) + l[i]) / w
            r[i+1] = 100 - 100 / (1 + ag / al) if al > 0 else 100
        return r
    
    @staticmethod
    def _macd_hist(a, fast=12, slow=26, sig=9):
        ef = FeatureEngineer._ema(a, fast)
        es = FeatureEngineer._ema(a, slow)
        ml = ef - es
        ms = FeatureEngineer._ema(ml, sig)
        return ml - ms
    
    @staticmethod
    def _atr(h, l, c, w):
        r = np.zeros_like(c)
        tr = np.maximum(h[1:]-l[1:], np.maximum(np.abs(h[1:]-c[:-1]), np.abs(l[1:]-c[:-1])))
        if len(tr) < w: return r
        r[w] = np.mean(tr[:w])
        for i in range(w, len(tr)): r[i+1] = (r[i]*(w-1)+tr[i])/w
        return r
    
    @staticmethod
    def _z_score(a, w):
        r = np.zeros_like(a)
        for i in range(w, len(a)):
            win = a[i-w:i]
            m, s = np.mean(win), np.std(win)
            r[i] = (a[i] - m) / s if s > 0 else 0
        return r
    
    @staticmethod
    def _bb_position(a, w):
        r = np.zeros_like(a)
        for i in range(w, len(a)):
            win = a[i-w:i]
            m, s = np.mean(win), np.std(win)
            if s > 0: r[i] = (a[i] - (m - 2*s)) / (4*s)
        return r
    
    @staticmethod
    def _rolling_max(a, w):
        r = np.full_like(a, a[0])
        for i in range(w, len(a)): r[i] = np.max(a[i-w:i])
        return r
    
    @staticmethod
    def _rolling_min(a, w):
        r = np.full_like(a, a[0])
        for i in range(w, len(a)): r[i] = np.min(a[i-w:i])
        return r
    
    @staticmethod
    def _rolling_corr(a, b, w):
        r = np.zeros(len(a))
        for i in range(w, len(a)):
            wa, wb = a[i-w:i], b[i-w:i]
            c = np.corrcoef(wa, wb)[0, 1] if np.std(wa) > 0 and np.std(wb) > 0 else 0
            r[i] = c if not np.isnan(c) else 0
        return r
    
    @staticmethod
    def _garman_klass_vol(o, h, l, c, w):
        r = np.zeros(len(c))
        for i in range(w, len(c)):
            gk = 0.5 * np.log(h[i-w:i]/l[i-w:i])**2 - (2*np.log(2)-1) * np.log(c[i-w:i]/o[i-w:i])**2
            r[i] = np.sqrt(np.mean(gk) * 252) if np.mean(gk) > 0 else 0
        return r
    
    @staticmethod
    def _price_position(a, w):
        r = np.zeros(len(a))
        for i in range(w, len(a)):
            hi, lo = np.max(a[i-w:i]), np.min(a[i-w:i])
            r[i] = (a[i] - lo) / (hi - lo) if hi > lo else 0.5
        return r
    
    @staticmethod
    def _adx(h, l, c, w):
        r = np.zeros(len(c))
        # Simplified ADX
        for i in range(w+1, len(c)):
            up = h[i] - h[i-1]
            down = l[i-1] - l[i]
            tr = max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
            if tr > 0:
                r[i] = abs(up - down) / tr * 100
        return r
    
    @staticmethod
    def _linear_slope(a, w):
        r = np.zeros(len(a))
        x = np.arange(w)
        for i in range(w, len(a)):
            y = a[i-w:i]
            m = np.polyfit(x, y, 1)[0] if np.std(y) > 0 else 0
            r[i] = m / a[i] * 100 if a[i] > 0 else 0
        return r
    
    @staticmethod
    def _obv_slope(c, v, w):
        obv = np.zeros(len(c))
        for i in range(1, len(c)):
            obv[i] = obv[i-1] + v[i] * (1 if c[i] > c[i-1] else -1 if c[i] < c[i-1] else 0)
        r = np.zeros(len(c))
        for i in range(w, len(c)):
            x = np.arange(w)
            r[i] = np.polyfit(x, obv[i-w:i], 1)[0]
        return r
    
    @staticmethod
    def _vwap_distance(c, v, w):
        r = np.zeros(len(c))
        for i in range(w, len(c)):
            vs = np.sum(v[i-w:i])
            vwap = np.sum(c[i-w:i] * v[i-w:i]) / vs if vs > 0 else c[i]
            r[i] = (c[i] - vwap) / c[i] * 100 if c[i] > 0 else 0
        return r
    
    @staticmethod
    def _higher_highs(h, w):
        r = np.zeros(len(h))
        for i in range(w, len(h)):
            r[i] = float(all(h[i-j] >= h[i-j-1] for j in range(w-1)))
        return r
    
    @staticmethod
    def _lower_lows(l, w):
        r = np.zeros(len(l))
        for i in range(w, len(l)):
            r[i] = float(all(l[i-j] <= l[i-j-1] for j in range(w-1)))
        return r
    
    @staticmethod
    def _engulfing(o, c):
        r = np.zeros(len(o))
        for i in range(1, len(o)):
            if c[i] > o[i] and c[i-1] < o[i-1]:  # Bullish engulfing
                if o[i] <= c[i-1] and c[i] >= o[i-1]: r[i] = 1
            elif c[i] < o[i] and c[i-1] > o[i-1]:  # Bearish
                if o[i] >= c[i-1] and c[i] <= o[i-1]: r[i] = -1
        return r
    
    @staticmethod
    def _three_bar_pattern(c):
        r = np.zeros(len(c))
        for i in range(2, len(c)):
            if c[i] > c[i-1] > c[i-2]: r[i] = 1    # 3 up
            elif c[i] < c[i-1] < c[i-2]: r[i] = -1  # 3 down
        return r


# ═══════════════════════════════════════════════════════════════
# Section 3: Label Construction
# ═══════════════════════════════════════════════════════════════

class LabelBuilder:
    """Construct prediction targets."""
    
    @staticmethod
    def forward_return(close: np.ndarray, horizon: int) -> np.ndarray:
        """Forward return over horizon bars."""
        y = np.full(len(close), np.nan)
        y[:-horizon] = (close[horizon:] / close[:-horizon] - 1) * 100
        return y
    
    @staticmethod
    def direction(close: np.ndarray, horizon: int) -> np.ndarray:
        """Binary: 1 = up, 0 = down."""
        ret = LabelBuilder.forward_return(close, horizon)
        return (ret > 0).astype(float)
    
    @staticmethod
    def triple_barrier(close: np.ndarray, horizon: int, 
                       tp_pct: float = 1.0, sl_pct: float = 1.0) -> np.ndarray:
        """
        Triple barrier labeling (Lopez de Prado):
        +1 = hit TP first, -1 = hit SL first, 0 = expired
        """
        y = np.zeros(len(close))
        for i in range(len(close) - horizon):
            entry = close[i]
            tp = entry * (1 + tp_pct / 100)
            sl = entry * (1 - sl_pct / 100)
            
            for j in range(1, horizon + 1):
                if i + j >= len(close): break
                if close[i + j] >= tp:
                    y[i] = 1
                    break
                elif close[i + j] <= sl:
                    y[i] = -1
                    break
            # If neither hit, label by final return
            if y[i] == 0 and i + horizon < len(close):
                y[i] = 1 if close[i + horizon] > entry else -1
        
        y[len(close) - horizon:] = np.nan
        return y


# ═══════════════════════════════════════════════════════════════
# Section 4: Gradient Boosting (Pure NumPy)
# ═══════════════════════════════════════════════════════════════

class DecisionStump:
    """Single-feature split (weak learner)."""
    
    def __init__(self):
        self.feature_idx = 0
        self.threshold = 0
        self.left_val = 0
        self.right_val = 0
    
    def fit(self, X, residuals, sample_weight=None):
        n, p = X.shape
        best_loss = float('inf')
        
        # Sample features (sqrt(p) for randomization)
        feat_subset = np.random.choice(p, min(int(np.sqrt(p)) + 1, p), replace=False)
        
        for f in feat_subset:
            vals = np.unique(X[:, f])
            if len(vals) > 20:
                # Subsample thresholds for speed
                percentiles = np.percentile(vals, np.linspace(10, 90, 10))
                thresholds = percentiles
            else:
                thresholds = vals
            
            for t in thresholds:
                left = X[:, f] <= t
                right = ~left
                if np.sum(left) < 2 or np.sum(right) < 2:
                    continue
                
                l_val = np.mean(residuals[left])
                r_val = np.mean(residuals[right])
                
                pred = np.where(left, l_val, r_val)
                loss = np.mean((residuals - pred) ** 2)
                
                if loss < best_loss:
                    best_loss = loss
                    self.feature_idx = f
                    self.threshold = t
                    self.left_val = l_val
                    self.right_val = r_val
    
    def predict(self, X):
        left = X[:, self.feature_idx] <= self.threshold
        return np.where(left, self.left_val, self.right_val)


class GradientBoosting:
    """
    Gradient Boosting for regression (pure NumPy).
    
    f(x) = f_0 + Σ η × h_t(x)
    
    where h_t fits the negative gradient (residuals).
    """
    
    def __init__(self, n_estimators: int = 100, learning_rate: float = 0.1,
                 max_depth: int = 3, min_samples: int = 5):
        self.n_estimators = n_estimators
        self.lr = learning_rate
        self.max_depth = max_depth
        self.min_samples = min_samples
        self.trees: List[DecisionStump] = []
        self.base_pred = 0
        self.feature_importances_ = None
        self.train_losses = []
    
    def fit(self, X, y, X_val=None, y_val=None, early_stop: int = 10):
        """Fit with optional early stopping."""
        self.base_pred = np.mean(y)
        pred = np.full(len(y), self.base_pred)
        
        n_features = X.shape[1]
        self.feature_importances_ = np.zeros(n_features)
        
        best_val_loss = float('inf')
        rounds_no_improve = 0
        
        for t in range(self.n_estimators):
            residuals = y - pred
            
            tree = DecisionStump()
            tree.fit(X, residuals)
            
            pred += self.lr * tree.predict(X)
            self.trees.append(tree)
            
            # Track feature importance
            self.feature_importances_[tree.feature_idx] += 1
            
            train_loss = np.mean((y - pred) ** 2)
            self.train_losses.append(train_loss)
            
            # Early stopping
            if X_val is not None and y_val is not None:
                val_pred = self.predict(X_val)
                val_loss = np.mean((y_val - val_pred) ** 2)
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    rounds_no_improve = 0
                else:
                    rounds_no_improve += 1
                    if rounds_no_improve >= early_stop:
                        logger.info(f"  Early stop at round {t+1}")
                        break
        
        # Normalize feature importances
        total = np.sum(self.feature_importances_)
        if total > 0:
            self.feature_importances_ /= total
    
    def predict(self, X):
        pred = np.full(X.shape[0], self.base_pred)
        for tree in self.trees:
            pred += self.lr * tree.predict(X)
        return pred


# ═══════════════════════════════════════════════════════════════
# Section 5: Purged K-Fold Cross-Validation
# ═══════════════════════════════════════════════════════════════

class PurgedKFold:
    """
    Time-series cross-validation with purging.
    
    Purge = remove samples near the train/test boundary to prevent
    label leakage (future returns overlap with training data).
    """
    
    def __init__(self, n_splits: int = 5, purge_gap: int = 5):
        self.n_splits = n_splits
        self.purge_gap = purge_gap
    
    def split(self, n: int):
        """Generate train/test indices."""
        fold_size = n // self.n_splits
        
        for i in range(self.n_splits):
            test_start = i * fold_size
            test_end = min((i + 1) * fold_size, n)
            
            # Training: everything before test (with purge gap)
            train_end = max(0, test_start - self.purge_gap)
            
            if train_end < 50:  # Need minimum training data
                continue
            
            train_idx = np.arange(0, train_end)
            test_idx = np.arange(test_start, test_end)
            
            yield train_idx, test_idx


# ═══════════════════════════════════════════════════════════════
# Section 6: Model Pipeline
# ═══════════════════════════════════════════════════════════════

@dataclass
class ModelResult:
    fold: int
    train_size: int
    test_size: int
    train_mse: float
    test_mse: float
    ic: float           # Information Coefficient (Spearman)
    hit_rate: float     # Directional accuracy
    long_avg: float     # Avg return of top quintile
    short_avg: float    # Avg return of bottom quintile
    spread: float       # Long - Short


class MLPipeline:
    """Full ML training and evaluation pipeline."""
    
    def __init__(self, n_estimators: int = 100, lr: float = 0.1,
                 n_folds: int = 5, horizon: int = 5):
        self.n_estimators = n_estimators
        self.lr = lr
        self.n_folds = n_folds
        self.horizon = horizon
        self.model = None
        self.feature_names = []
    
    def run(self, data: Dict[str, np.ndarray]) -> Dict:
        """Full pipeline: features → labels → train → evaluate."""
        
        # 1. Feature Engineering
        logger.info("🔧 Engineering 50+ features...")
        X, names = FeatureEngineer.build(data)
        self.feature_names = names
        logger.info(f"  ✅ {len(names)} features built")
        
        # 2. Labels
        y = LabelBuilder.forward_return(data['close'], self.horizon)
        
        # 3. Remove NaN labels (future bars)
        valid = ~np.isnan(y)
        X_valid = X[valid]
        y_valid = y[valid]
        
        # 4. Warmup: skip first 50 bars
        X_valid = X_valid[50:]
        y_valid = y_valid[50:]
        
        logger.info(f"📊 Dataset: {X_valid.shape[0]} samples × {X_valid.shape[1]} features")
        
        # 5. Purged K-Fold CV
        logger.info(f"🔄 Purged {self.n_folds}-Fold CV (gap={self.horizon})...")
        cv = PurgedKFold(n_splits=self.n_folds, purge_gap=self.horizon)
        
        results = []
        all_preds = np.zeros(len(y_valid))
        all_actuals = np.zeros(len(y_valid))
        pred_mask = np.zeros(len(y_valid), dtype=bool)
        
        for fold, (train_idx, test_idx) in enumerate(cv.split(len(y_valid))):
            X_train, y_train = X_valid[train_idx], y_valid[train_idx]
            X_test, y_test = X_valid[test_idx], y_valid[test_idx]
            
            # Standardize (no leakage — fit on train only)
            means = np.mean(X_train, axis=0)
            stds = np.std(X_train, axis=0)
            stds[stds == 0] = 1
            X_train = (X_train - means) / stds
            X_test = (X_test - means) / stds
            
            # Train
            model = GradientBoosting(n_estimators=self.n_estimators, learning_rate=self.lr)
            model.fit(X_train, y_train, early_stop=15)
            
            # Predict
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            all_preds[test_idx] = test_pred
            all_actuals[test_idx] = y_test
            pred_mask[test_idx] = True
            
            # Evaluate
            train_mse = np.mean((y_train - train_pred) ** 2)
            test_mse = np.mean((y_test - test_pred) ** 2)
            
            # IC (rank correlation)
            from scipy.stats import spearmanr
            ic, _ = spearmanr(test_pred, y_test)
            if np.isnan(ic): ic = 0
            
            # Hit rate
            hr = np.mean((test_pred > 0) == (y_test > 0)) * 100
            
            # Long/Short quintile returns
            sorted_idx = np.argsort(test_pred)
            q = len(sorted_idx) // 5
            if q > 0:
                long_avg = np.mean(y_test[sorted_idx[-q:]])
                short_avg = np.mean(y_test[sorted_idx[:q]])
            else:
                long_avg = short_avg = 0
            
            r = ModelResult(
                fold=fold + 1,
                train_size=len(train_idx),
                test_size=len(test_idx),
                train_mse=round(train_mse, 4),
                test_mse=round(test_mse, 4),
                ic=round(ic, 4),
                hit_rate=round(hr, 1),
                long_avg=round(long_avg, 4),
                short_avg=round(short_avg, 4),
                spread=round(long_avg - short_avg, 4),
            )
            results.append(r)
            logger.info(f"  Fold {fold+1}: IC={ic:+.4f} HR={hr:.1f}% Spread={long_avg-short_avg:.4f}")
        
        # 6. Train final model on all data
        logger.info("🎯 Training final model on all data...")
        means = np.mean(X_valid, axis=0)
        stds = np.std(X_valid, axis=0)
        stds[stds == 0] = 1
        X_norm = (X_valid - means) / stds
        
        self.model = GradientBoosting(n_estimators=self.n_estimators, learning_rate=self.lr)
        self.model.fit(X_norm, y_valid, early_stop=20)
        
        # 7. Feature Importance
        fi = list(zip(names, self.model.feature_importances_))
        fi.sort(key=lambda x: -x[1])
        
        # 8. Latest signal
        latest_X = X_norm[-1:, :]
        latest_pred = self.model.predict(latest_X)[0]
        
        return {
            'cv_results': results,
            'feature_importance': fi[:20],
            'n_features': len(names),
            'n_samples': len(y_valid),
            'horizon': self.horizon,
            'latest_signal': round(latest_pred, 4),
            'latest_direction': 'LONG' if latest_pred > 0 else 'SHORT',
            'avg_ic': round(np.mean([r.ic for r in results]), 4),
            'avg_hr': round(np.mean([r.hit_rate for r in results]), 1),
            'avg_spread': round(np.mean([r.spread for r in results]), 4),
        }


# ═══════════════════════════════════════════════════════════════
# Section 7: Report
# ═══════════════════════════════════════════════════════════════

def generate_report(result: Dict, symbol: str, days: int):
    print("\n" + "=" * 80)
    print(f"  NOOGH ML SIGNAL RESEARCH — {symbol}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | {days}d | {result['n_features']} features | {result['n_samples']} samples")
    print("=" * 80)
    
    print(f"\n📊 PURGED K-FOLD RESULTS (horizon={result['horizon']}h)")
    print(f"  {'Fold':<6} {'Train':<8} {'Test':<8} {'Train MSE':<12} {'Test MSE':<12} {'IC':<10} {'HR%':<8} {'L/S Spread'}")
    print(f"  {'-'*76}")
    
    for r in result['cv_results']:
        print(f"  {r.fold:<6} {r.train_size:<8} {r.test_size:<8} {r.train_mse:<12} {r.test_mse:<12} "
              f"{r.ic:>+8.4f}  {r.hit_rate:>5.1f}  {r.spread:>+8.4f}")
    
    ics = [r.ic for r in result['cv_results']]
    print(f"  {'─'*76}")
    print(f"  {'AVG':<6} {'':16} {'':12} {'':12} {np.mean(ics):>+8.4f}  {result['avg_hr']:>5.1f}  {result['avg_spread']:>+8.4f}")
    
    # Verdict
    avg_ic = result['avg_ic']
    print(f"\n🎯 MODEL VERDICT:")
    if avg_ic > 0.05 and result['avg_hr'] > 52:
        print(f"  🟢 ALPHA DETECTED — IC={avg_ic:+.4f}, HR={result['avg_hr']:.1f}%")
    elif avg_ic > 0.02 or result['avg_hr'] > 51:
        print(f"  🟡 WEAK SIGNAL — IC={avg_ic:+.4f}, HR={result['avg_hr']:.1f}%")
    else:
        print(f"  🔴 NO ALPHA — IC={avg_ic:+.4f}, HR={result['avg_hr']:.1f}%")
    
    # Feature Importance
    print(f"\n📋 TOP 15 FEATURES:")
    print(f"  {'Rank':<6} {'Feature':<25} {'Importance':<12}")
    print(f"  {'-'*43}")
    for i, (name, imp) in enumerate(result['feature_importance'][:15]):
        bar = "█" * int(imp * 100)
        print(f"  {i+1:<6} {name:<25} {imp:>8.4f}  {bar}")
    
    # Latest Signal
    sig = result['latest_signal']
    print(f"\n🔮 LATEST SIGNAL: {result['latest_direction']} (score: {sig:+.4f})")
    print(f"  Confidence: {'HIGH' if abs(sig) > 0.5 else 'MEDIUM' if abs(sig) > 0.2 else 'LOW'}")
    
    print(f"\n" + "=" * 80)


# ═══════════════════════════════════════════════════════════════
# Section 8: Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='NOOGH ML Signal Pipeline')
    parser.add_argument('--symbol', default='BTCUSDT')
    parser.add_argument('--interval', default='1h')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--horizon', type=int, default=5, help='Prediction horizon (bars)')
    parser.add_argument('--trees', type=int, default=100)
    parser.add_argument('--lr', type=float, default=0.1)
    parser.add_argument('--folds', type=int, default=5)
    args = parser.parse_args()
    
    data = fetch_klines(args.symbol, args.interval, args.days)
    if len(data['close']) < 200:
        logger.error("❌ Insufficient data")
        return
    
    pipeline = MLPipeline(
        n_estimators=args.trees,
        lr=args.lr,
        n_folds=args.folds,
        horizon=args.horizon,
    )
    
    result = pipeline.run(data)
    generate_report(result, args.symbol, args.days)


if __name__ == '__main__':
    main()
