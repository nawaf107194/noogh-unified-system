"""
{
  "name": "long_filter",
  "hash": "eed9f838df0d",
  "created_utc": "2026-02-28T12:05:22Z",
  "created_local": "20260228_150522",
  "model": "noogh-teacher",
  "prompt_hash": "1f5be598f438",
  "market": {
    "dominant_side": "SHORT",
    "volatility_regime": "LOW"
  },
  "stats": {
    "counts": {
      "total": 263,
      "long_total": 0,
      "short_total": 263
    },
    "long": {
      "wins": 0,
      "losses": 0,
      "wr": 0.0,
      "avg_tbr": 0.0,
      "avg_atr": 0.0
    },
    "short": {
      "wins": 151,
      "losses": 102,
      "wr": 59.683794466403164,
      "avg_vol": 3521630.7490760456,
      "avg_atr": 9.81473199891363
    },
    "market": {
      "dominant_side": "SHORT",
      "volatility_regime": "LOW"
    }
  }
}
"""

from typing import Tuple

def long_filter(s):
    atr = s.get('atr', 0)
    rsi = s.get('rsi', 50)
    if atr < 6 or rsi > 68: return False, 0.0, 'ATR too low or RSI too high'
    return True, min(1.0, atr / 100), 'ATR and RSI within range'
