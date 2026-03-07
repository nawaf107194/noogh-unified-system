"""
{
  "name": "short_filter",
  "hash": "fedcc8d0998d",
  "created_utc": "2026-02-28T12:04:21Z",
  "created_local": "20260228_150421",
  "model": "noogh-teacher",
  "prompt_hash": "ba99bfb8a1c8",
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

def short_filter(s):
    volume = s.get('volume', 0)
    taker_buy_ratio = s.get('taker_buy_ratio', 0)
    if volume < 2500000 or taker_buy_ratio > 0.45: return False, 0.0, 'Volume too low or TBR too high'
    return True, min(1.0, volume / 5000000), 'Volume and TBR within range'
