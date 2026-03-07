#!/usr/bin/env python3
"""
NOOGH Market Data Pipeline
=============================
Bloomberg-grade data infrastructure for crypto trading.

Architecture:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Data Sources │───▶│  Ingestion   │───▶│  Storage     │───▶│  Feature     │
│  (Binance WS, │    │  (Clean,     │    │  (SQLite,    │    │  Store       │
│  REST, CG)   │    │  Validate)   │    │  compressed) │    │  (Indicators)│
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
                    ┌──────────────┐    ┌──────────────┐           │
                    │  Scheduler   │───▶│  API Layer   │◀──────────┘
                    │  (Cron-like) │    │  (HTTP/JSON) │
                    └──────────────┘    └──────────────┘

Usage:
    python3 data_pipeline.py init          # Create database
    python3 data_pipeline.py ingest        # Download historical data
    python3 data_pipeline.py features      # Compute feature store
    python3 data_pipeline.py serve         # Start API server
    python3 data_pipeline.py stream        # Start WebSocket feed
    python3 data_pipeline.py status        # Pipeline health check
"""

import os
import sys
import json
import time
import sqlite3
import asyncio
import signal
import hashlib
import threading
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import numpy as np
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

DB_PATH = Path(__file__).parent / 'data' / 'noogh_market.db'
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT']
INTERVALS = ['5m', '1h', '4h', '1d']


# ═══════════════════════════════════════════════════════════════
# Section 1: Database Schema
# ═══════════════════════════════════════════════════════════════

SCHEMA = """
-- ═══ KLINES (OHLCV) ═══
CREATE TABLE IF NOT EXISTS klines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    open_time INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    close_time INTEGER NOT NULL,
    quote_volume REAL,
    trades INTEGER,
    taker_buy_vol REAL,
    taker_buy_quote REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval, open_time)
);
CREATE INDEX IF NOT EXISTS idx_klines_lookup ON klines(symbol, interval, open_time);
CREATE INDEX IF NOT EXISTS idx_klines_time ON klines(open_time);

-- ═══ FEATURE STORE (Pre-computed indicators) ═══
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    open_time INTEGER NOT NULL,
    -- Momentum
    rsi_14 REAL,
    macd_line REAL,
    macd_signal REAL,
    macd_hist REAL,
    -- Trend
    ema_9 REAL,
    ema_21 REAL,
    sma_50 REAL,
    ema_200 REAL,
    -- Volatility
    atr_14 REAL,
    bb_upper REAL,
    bb_mid REAL,
    bb_lower REAL,
    bb_width REAL,
    -- Volume
    obv REAL,
    vwap REAL,
    volume_sma_20 REAL,
    volume_ratio REAL,
    taker_buy_ratio REAL,
    -- Derived
    z_score_20 REAL,
    price_momentum_10 REAL,
    price_momentum_20 REAL,
    -- Composite
    composite_score REAL,
    signal_direction TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval, open_time)
);
CREATE INDEX IF NOT EXISTS idx_features_lookup ON features(symbol, interval, open_time);

-- ═══ DATA QUALITY LOG ═══
CREATE TABLE IF NOT EXISTS data_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_time TEXT DEFAULT CURRENT_TIMESTAMP,
    symbol TEXT,
    interval TEXT,
    check_type TEXT,
    status TEXT,
    details TEXT
);

-- ═══ PIPELINE STATE ═══
CREATE TABLE IF NOT EXISTS pipeline_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ═══ REAL-TIME TICKS ═══
CREATE TABLE IF NOT EXISTS ticks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    quantity REAL,
    timestamp INTEGER NOT NULL,
    is_buyer_maker INTEGER
);
CREATE INDEX IF NOT EXISTS idx_ticks_sym ON ticks(symbol, timestamp);
"""


# ═══════════════════════════════════════════════════════════════
# Section 2: Database Manager
# ═══════════════════════════════════════════════════════════════

class DatabaseManager:
    """Thread-safe SQLite database manager."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._local = threading.local()
    
    @property
    def conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def init_schema(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def insert_klines(self, symbol: str, interval: str, klines: List[Dict]):
        """Bulk insert klines with upsert."""
        self.conn.executemany(
            """INSERT OR REPLACE INTO klines 
               (symbol, interval, open_time, open, high, low, close, volume,
                close_time, quote_volume, trades, taker_buy_vol, taker_buy_quote)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(symbol, interval, k['open_time'], k['open'], k['high'], k['low'],
              k['close'], k['volume'], k['close_time'], k.get('quote_volume', 0),
              k.get('trades', 0), k.get('taker_buy_vol', 0), k.get('taker_buy_quote', 0))
             for k in klines]
        )
        self.conn.commit()
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500,
                    start: int = None, end: int = None) -> List[Dict]:
        """Query klines with optional time range."""
        q = "SELECT * FROM klines WHERE symbol=? AND interval=?"
        params = [symbol, interval]
        if start:
            q += " AND open_time >= ?"
            params.append(start)
        if end:
            q += " AND open_time <= ?"
            params.append(end)
        q += " ORDER BY open_time DESC LIMIT ?"
        params.append(limit)
        
        rows = self.conn.execute(q, params).fetchall()
        return [dict(r) for r in reversed(rows)]
    
    def get_features(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM features WHERE symbol=? AND interval=? ORDER BY open_time DESC LIMIT ?",
            (symbol, interval, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
    
    def insert_features(self, symbol: str, interval: str, features: List[Dict]):
        cols = ['symbol', 'interval', 'open_time', 'rsi_14', 'macd_line', 'macd_signal',
                'macd_hist', 'ema_9', 'ema_21', 'sma_50', 'ema_200', 'atr_14',
                'bb_upper', 'bb_mid', 'bb_lower', 'bb_width', 'obv', 'vwap',
                'volume_sma_20', 'volume_ratio', 'taker_buy_ratio', 'z_score_20',
                'price_momentum_10', 'price_momentum_20', 'composite_score', 'signal_direction']
        
        placeholders = ','.join(['?'] * len(cols))
        col_str = ','.join(cols)
        
        self.conn.executemany(
            f"INSERT OR REPLACE INTO features ({col_str}) VALUES ({placeholders})",
            [tuple(f.get(c) for c in cols) for f in features]
        )
        self.conn.commit()
    
    def log_quality(self, symbol: str, interval: str, check_type: str,
                     status: str, details: str):
        self.conn.execute(
            "INSERT INTO data_quality (symbol, interval, check_type, status, details) VALUES (?,?,?,?,?)",
            (symbol, interval, check_type, status, details)
        )
        self.conn.commit()
    
    def set_state(self, key: str, value: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO pipeline_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat())
        )
        self.conn.commit()
    
    def get_state(self, key: str) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM pipeline_state WHERE key=?", (key,)).fetchone()
        return row['value'] if row else None
    
    def stats(self) -> Dict:
        result = {}
        for table in ['klines', 'features', 'ticks', 'data_quality']:
            row = self.conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
            result[table] = row['cnt']
        
        # Per-symbol kline counts
        rows = self.conn.execute(
            "SELECT symbol, interval, COUNT(*) as cnt, MIN(open_time) as first, MAX(open_time) as last "
            "FROM klines GROUP BY symbol, interval ORDER BY symbol, interval"
        ).fetchall()
        result['breakdowns'] = [dict(r) for r in rows]
        
        return result


# ═══════════════════════════════════════════════════════════════
# Section 3: Data Ingestion (Binance REST)
# ═══════════════════════════════════════════════════════════════

class BinanceIngester:
    """Download historical klines from Binance."""
    
    BASE = "https://api.binance.com/api/v3"
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def ingest(self, symbol: str, interval: str, days: int = 90):
        """Download and store klines."""
        start_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        end_ms = int(datetime.now().timestamp() * 1000)
        
        all_klines = []
        current = start_ms
        
        while current < end_ms:
            try:
                resp = requests.get(f"{self.BASE}/klines", params={
                    'symbol': symbol, 'interval': interval,
                    'startTime': current, 'endTime': end_ms, 'limit': 1000
                }, timeout=10)
                
                if resp.status_code == 429:
                    logger.warning("Rate limited, waiting...")
                    time.sleep(5)
                    continue
                
                if resp.status_code != 200:
                    logger.error(f"API error {resp.status_code}")
                    break
                
                data = resp.json()
                if not data:
                    break
                
                for k in data:
                    all_klines.append({
                        'open_time': k[0],
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5]),
                        'close_time': k[6],
                        'quote_volume': float(k[7]),
                        'trades': int(k[8]),
                        'taker_buy_vol': float(k[9]),
                        'taker_buy_quote': float(k[10]),
                    })
                
                current = data[-1][6] + 1
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching {symbol} {interval}: {e}")
                break
        
        if all_klines:
            # Validate before storing
            cleaned = self._validate_and_clean(all_klines, symbol, interval)
            self.db.insert_klines(symbol, interval, cleaned)
            logger.info(f"  ✅ {symbol}/{interval}: {len(cleaned)} candles stored")
        
        return len(all_klines)
    
    def ingest_all(self, symbols: List[str] = None, intervals: List[str] = None, days: int = 90):
        """Ingest all symbols and intervals."""
        symbols = symbols or SYMBOLS
        intervals = intervals or INTERVALS
        
        total = 0
        for sym in symbols:
            for intv in intervals:
                logger.info(f"📊 Ingesting {sym}/{intv} ({days}d)...")
                count = self.ingest(sym, intv, days)
                total += count
        
        self.db.set_state('last_ingest', datetime.now().isoformat())
        self.db.set_state('total_candles', str(total))
        logger.info(f"✅ Total: {total} candles ingested")
        return total
    
    def _validate_and_clean(self, klines: List[Dict], symbol: str, interval: str) -> List[Dict]:
        """Data quality checks and cleaning."""
        issues = []
        cleaned = []
        
        for i, k in enumerate(klines):
            # Check 1: Valid OHLC relationships
            if k['high'] < k['low']:
                issues.append(f"Bar {i}: high < low")
                k['high'], k['low'] = k['low'], k['high']
            
            if k['close'] > k['high'] or k['close'] < k['low']:
                issues.append(f"Bar {i}: close outside H/L range")
            
            if k['open'] > k['high'] or k['open'] < k['low']:
                issues.append(f"Bar {i}: open outside H/L range")
            
            # Check 2: Zero/negative prices
            if k['close'] <= 0:
                issues.append(f"Bar {i}: zero/negative close")
                continue
            
            # Check 3: Extreme moves (>20% in single bar)
            if i > 0 and klines[i-1]['close'] > 0:
                move = abs(k['close'] - klines[i-1]['close']) / klines[i-1]['close']
                if move > 0.20:
                    issues.append(f"Bar {i}: extreme move {move*100:.1f}%")
                    # Keep it but flag it
            
            # Check 4: Zero volume
            if k['volume'] == 0:
                issues.append(f"Bar {i}: zero volume")
            
            cleaned.append(k)
        
        if issues:
            self.db.log_quality(symbol, interval, 'INGEST',
                               'WARN' if len(issues) < 5 else 'FAIL',
                               f"{len(issues)} issues: {'; '.join(issues[:5])}")
        else:
            self.db.log_quality(symbol, interval, 'INGEST', 'PASS',
                               f"{len(cleaned)} bars, no issues")
        
        return cleaned


# ═══════════════════════════════════════════════════════════════
# Section 4: Feature Store (Pre-computed Indicators)
# ═══════════════════════════════════════════════════════════════

class FeatureComputer:
    """Compute and store pre-calculated technical indicators."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def compute_all(self, symbols: List[str] = None, intervals: List[str] = None):
        symbols = symbols or SYMBOLS
        intervals = intervals or ['1h', '4h']
        
        for sym in symbols:
            for intv in intervals:
                klines = self.db.get_klines(sym, intv, limit=500)
                if len(klines) < 50:
                    logger.warning(f"⚠️ {sym}/{intv}: insufficient data ({len(klines)})")
                    continue
                
                features = self._compute(sym, intv, klines)
                self.db.insert_features(sym, intv, features)
                logger.info(f"  ✅ {sym}/{intv}: {len(features)} features computed")
        
        self.db.set_state('last_features', datetime.now().isoformat())
    
    def _compute(self, symbol: str, interval: str, klines: List[Dict]) -> List[Dict]:
        """Compute all indicators for a symbol/interval."""
        closes = np.array([k['close'] for k in klines])
        highs = np.array([k['high'] for k in klines])
        lows = np.array([k['low'] for k in klines])
        volumes = np.array([k['volume'] for k in klines])
        taker_buy = np.array([k.get('taker_buy_vol', 0) for k in klines])
        
        n = len(closes)
        
        # Pre-compute all indicators
        rsi = self._rsi(closes, 14)
        ema9 = self._ema(closes, 9)
        ema21 = self._ema(closes, 21)
        sma50 = self._sma(closes, 50)
        ema200 = self._ema(closes, 200)
        macd_l, macd_s, macd_h = self._macd(closes)
        atr = self._atr(highs, lows, closes, 14)
        bb_u, bb_m, bb_l = self._bollinger(closes, 20)
        obv = self._obv(closes, volumes)
        vol_sma = self._sma(volumes, 20)
        
        features = []
        for i in range(50, n):  # Skip warmup
            k = klines[i]
            
            # VWAP (20-bar)
            v_sum = np.sum(volumes[max(0,i-19):i+1])
            vwap = np.sum(closes[max(0,i-19):i+1] * volumes[max(0,i-19):i+1]) / v_sum if v_sum > 0 else closes[i]
            
            # Volume ratio
            vol_ratio = volumes[i] / vol_sma[i] if vol_sma[i] and vol_sma[i] > 0 else 1
            
            # Taker buy ratio
            tbr = taker_buy[i] / volumes[i] if volumes[i] > 0 else 0.5
            
            # Z-score
            w = closes[max(0,i-19):i+1]
            m, s = np.mean(w), np.std(w)
            z = (closes[i] - m) / s if s > 0 else 0
            
            # Momentum
            mom10 = (closes[i] / closes[i-10] - 1) * 100 if i >= 10 else 0
            mom20 = (closes[i] / closes[i-20] - 1) * 100 if i >= 20 else 0
            
            # BB width
            bb_width = (bb_u[i] - bb_l[i]) / bb_m[i] * 100 if bb_m[i] and bb_m[i] > 0 else 0
            
            # Composite score (simplified)
            score = self._composite(rsi[i], macd_h[i], atr[i], ema9[i], ema21[i], z)
            direction = 'LONG' if score > 0.2 else 'SHORT' if score < -0.2 else 'NONE'
            
            features.append({
                'symbol': symbol,
                'interval': interval,
                'open_time': k['open_time'],
                'rsi_14': self._safe(rsi[i]),
                'macd_line': self._safe(macd_l[i]),
                'macd_signal': self._safe(macd_s[i]),
                'macd_hist': self._safe(macd_h[i]),
                'ema_9': self._safe(ema9[i]),
                'ema_21': self._safe(ema21[i]),
                'sma_50': self._safe(sma50[i]),
                'ema_200': self._safe(ema200[i]),
                'atr_14': self._safe(atr[i]),
                'bb_upper': self._safe(bb_u[i]),
                'bb_mid': self._safe(bb_m[i]),
                'bb_lower': self._safe(bb_l[i]),
                'bb_width': round(bb_width, 4),
                'obv': self._safe(obv[i]),
                'vwap': round(vwap, 2),
                'volume_sma_20': self._safe(vol_sma[i]),
                'volume_ratio': round(vol_ratio, 3),
                'taker_buy_ratio': round(tbr, 4),
                'z_score_20': round(z, 4),
                'price_momentum_10': round(mom10, 4),
                'price_momentum_20': round(mom20, 4),
                'composite_score': round(score, 4),
                'signal_direction': direction,
            })
        
        return features
    
    def _composite(self, rsi, macd_h, atr, ema9, ema21, z) -> float:
        if rsi is None or np.isnan(rsi): return 0
        rsi_norm = (rsi - 50) / 50
        macd_norm = max(min(macd_h / atr if atr and atr > 0 else 0, 1), -1) if macd_h and not np.isnan(macd_h) else 0
        ema_cross = 1.0 if ema9 and ema21 and ema9 > ema21 else -1.0
        z_norm = -max(min(z / 2, 1), -1)
        return np.clip(0.3 * rsi_norm + 0.3 * macd_norm + 0.2 * ema_cross + 0.2 * z_norm, -1, 1)
    
    def _safe(self, v):
        if v is None: return None
        try:
            if np.isnan(v): return None
        except: pass
        return round(float(v), 6)
    
    # ── Indicator helpers ──
    def _ema(self, data, period):
        r = np.full_like(data, np.nan, dtype='f8')
        if len(data) < period: return r
        r[period-1] = np.mean(data[:period])
        m = 2/(period+1)
        for i in range(period, len(data)):
            r[i] = (data[i]-r[i-1])*m + r[i-1]
        return r
    
    def _sma(self, data, period):
        r = np.full_like(data, np.nan, dtype='f8')
        for i in range(period-1, len(data)):
            r[i] = np.mean(data[i-period+1:i+1])
        return r
    
    def _rsi(self, data, period=14):
        r = np.full_like(data, np.nan, dtype='f8')
        if len(data) < period+1: return r
        d = np.diff(data)
        g = np.where(d>0,d,0)
        l = np.where(d<0,-d,0)
        ag,al = np.mean(g[:period]),np.mean(l[:period])
        for i in range(period,len(d)):
            ag = (ag*(period-1)+g[i])/period
            al = (al*(period-1)+l[i])/period
            r[i+1] = 100-100/(1+ag/al) if al>0 else 100
        return r
    
    def _macd(self, data, fast=12, slow=26, sig=9):
        ef = self._ema(data, fast)
        es = self._ema(data, slow)
        ml = ef - es
        ms = self._ema(ml, sig)
        return ml, ms, ml - ms
    
    def _atr(self, h, l, c, period=14):
        r = np.full_like(c, np.nan, dtype='f8')
        if len(c) < period+1: return r
        tr = np.maximum(h[1:]-l[1:], np.maximum(np.abs(h[1:]-c[:-1]), np.abs(l[1:]-c[:-1])))
        r[period] = np.mean(tr[:period])
        for i in range(period,len(tr)):
            r[i+1] = (r[i]*(period-1)+tr[i])/period
        return r
    
    def _bollinger(self, data, period=20, mult=2):
        u,m,l = [np.full_like(data,np.nan,dtype='f8') for _ in range(3)]
        for i in range(period-1,len(data)):
            w = data[i-period+1:i+1]
            mu,s = np.mean(w),np.std(w)
            m[i],u[i],l[i] = mu, mu+mult*s, mu-mult*s
        return u,m,l
    
    def _obv(self, close, volume):
        obv = np.zeros_like(close)
        for i in range(1,len(close)):
            if close[i]>close[i-1]: obv[i]=obv[i-1]+volume[i]
            elif close[i]<close[i-1]: obv[i]=obv[i-1]-volume[i]
            else: obv[i]=obv[i-1]
        return obv


# ═══════════════════════════════════════════════════════════════
# Section 5: WebSocket Real-Time Feed
# ═══════════════════════════════════════════════════════════════

class BinanceWebSocket:
    """WebSocket stream with auto-reconnection."""
    
    def __init__(self, db: DatabaseManager, symbols: List[str] = None):
        self.db = db
        self.symbols = [s.lower() for s in (symbols or SYMBOLS)]
        self.running = False
    
    async def start(self):
        """Start WebSocket streams."""
        try:
            import websockets
        except ImportError:
            logger.error("pip install websockets first")
            return
        
        streams = '/'.join([f"{s}@trade" for s in self.symbols])
        url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        
        self.running = True
        reconnect_delay = 1
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    logger.info(f"🔌 WebSocket connected ({len(self.symbols)} streams)")
                    reconnect_delay = 1
                    
                    while self.running:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30)
                        data = json.loads(msg)
                        
                        if 'data' in data:
                            trade = data['data']
                            self.db.conn.execute(
                                "INSERT INTO ticks (symbol, price, quantity, timestamp, is_buyer_maker) VALUES (?,?,?,?,?)",
                                (trade['s'], float(trade['p']), float(trade['q']),
                                 trade['T'], 1 if trade['m'] else 0)
                            )
                            # Commit every 100 ticks
                            if trade['T'] % 100 == 0:
                                self.db.conn.commit()
                                
            except Exception as e:
                logger.warning(f"WebSocket error: {e}. Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)
    
    def stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════
# Section 6: API Layer (HTTP Server)
# ═══════════════════════════════════════════════════════════════

class DataAPIHandler(BaseHTTPRequestHandler):
    """HTTP API endpoints for the data pipeline."""
    
    db = None  # Set before starting server
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        routes = {
            '/api/klines': self._klines,
            '/api/features': self._features,
            '/api/latest': self._latest,
            '/api/status': self._status,
            '/api/symbols': self._symbols,
        }
        
        handler = routes.get(path)
        if handler:
            try:
                result = handler(params)
                self._respond(200, result)
            except Exception as e:
                self._respond(500, {'error': str(e)})
        else:
            self._respond(404, {'error': f'Not found: {path}', 'routes': list(routes.keys())})
    
    def _klines(self, params):
        symbol = params.get('symbol', ['BTCUSDT'])[0]
        interval = params.get('interval', ['1h'])[0]
        limit = int(params.get('limit', ['100'])[0])
        return self.db.get_klines(symbol, interval, limit)
    
    def _features(self, params):
        symbol = params.get('symbol', ['BTCUSDT'])[0]
        interval = params.get('interval', ['1h'])[0]
        limit = int(params.get('limit', ['50'])[0])
        return self.db.get_features(symbol, interval, limit)
    
    def _latest(self, params):
        symbol = params.get('symbol', ['BTCUSDT'])[0]
        interval = params.get('interval', ['1h'])[0]
        features = self.db.get_features(symbol, interval, 1)
        klines = self.db.get_klines(symbol, interval, 1)
        return {
            'symbol': symbol,
            'interval': interval,
            'latest_kline': klines[-1] if klines else None,
            'latest_features': features[-1] if features else None,
        }
    
    def _status(self, params):
        stats = self.db.stats()
        return {
            'status': 'OK',
            'database': str(self.db.db_path),
            'stats': stats,
            'last_ingest': self.db.get_state('last_ingest'),
            'last_features': self.db.get_state('last_features'),
        }
    
    def _symbols(self, params):
        return {'symbols': SYMBOLS, 'intervals': INTERVALS}
    
    def _respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress default logging


# ═══════════════════════════════════════════════════════════════
# Section 7: Scheduler
# ═══════════════════════════════════════════════════════════════

class PipelineScheduler:
    """Simple cron-like scheduler."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.ingester = BinanceIngester(db)
        self.features = FeatureComputer(db)
    
    def run_daily(self):
        """Daily pipeline: ingest latest + recompute features."""
        logger.info("🕐 Daily pipeline starting...")
        
        # Ingest last 2 days (overlap for safety)
        self.ingester.ingest_all(days=2)
        
        # Recompute features
        self.features.compute_all()
        
        self.db.set_state('last_daily_run', datetime.now().isoformat())
        logger.info("✅ Daily pipeline complete")
    
    def run_loop(self, interval_minutes: int = 60):
        """Run on a loop."""
        while True:
            try:
                self.run_daily()
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
            time.sleep(interval_minutes * 60)


# ═══════════════════════════════════════════════════════════════
# Section 8: Main CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='NOOGH Data Pipeline')
    parser.add_argument('command', choices=['init', 'ingest', 'features', 'serve', 'stream', 'status', 'daily'],
                        help='Pipeline command')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--symbols', nargs='+', default=SYMBOLS)
    parser.add_argument('--intervals', nargs='+', default=INTERVALS)
    parser.add_argument('--port', type=int, default=8899)
    args = parser.parse_args()
    
    db = DatabaseManager()
    
    if args.command == 'init':
        db.init_schema()
        
    elif args.command == 'ingest':
        db.init_schema()
        ingester = BinanceIngester(db)
        ingester.ingest_all(args.symbols, args.intervals, args.days)
        
    elif args.command == 'features':
        fc = FeatureComputer(db)
        fc.compute_all(args.symbols)
        
    elif args.command == 'serve':
        DataAPIHandler.db = db
        server = HTTPServer(('0.0.0.0', args.port), DataAPIHandler)
        logger.info(f"🌐 API server running on http://localhost:{args.port}")
        logger.info(f"   Endpoints: /api/klines, /api/features, /api/latest, /api/status")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        
    elif args.command == 'stream':
        ws = BinanceWebSocket(db, args.symbols)
        asyncio.run(ws.start())
        
    elif args.command == 'status':
        stats = db.stats()
        print(f"\n{'=' * 60}")
        print(f"  NOOGH DATA PIPELINE STATUS")
        print(f"{'=' * 60}")
        print(f"  Database: {db.db_path}")
        print(f"  Last Ingest: {db.get_state('last_ingest') or 'Never'}")
        print(f"  Last Features: {db.get_state('last_features') or 'Never'}")
        print(f"\n  Table Counts:")
        for table, count in stats.items():
            if table != 'breakdowns':
                print(f"    {table:<20} {count:>10,}")
        
        if stats.get('breakdowns'):
            print(f"\n  Kline Breakdowns:")
            for b in stats['breakdowns']:
                start = datetime.fromtimestamp(b['first']/1000).strftime('%Y-%m-%d') if b['first'] else '?'
                end = datetime.fromtimestamp(b['last']/1000).strftime('%Y-%m-%d') if b['last'] else '?'
                print(f"    {b['symbol']}/{b['interval']}: {b['cnt']:>6} candles ({start} → {end})")
        print(f"{'=' * 60}")
        
    elif args.command == 'daily':
        sched = PipelineScheduler(db)
        sched.run_daily()


if __name__ == '__main__':
    main()
