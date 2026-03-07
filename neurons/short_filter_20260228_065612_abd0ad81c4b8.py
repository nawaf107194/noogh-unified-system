"""
{
  "name": "short_filter",
  "hash": "abd0ad81c4b8",
  "created_utc": "2026-02-28T03:56:12Z",
  "created_local": "20260228_065612",
  "model": "noogh-teacher",
  "prompt_hash": "0555ca3f059f",
  "market": {
    "dominant_side": "NEUTRAL",
    "volatility_regime": "LOW"
  },
  "stats": {
    "counts": {
      "total": 0,
      "long_total": 0,
      "short_total": 0
    },
    "long": {
      "wins": 0,
      "losses": 0,
      "wr": 0.0,
      "avg_tbr": 0.0,
      "avg_atr": 0.0
    },
    "short": {
      "wins": 0,
      "losses": 0,
      "wr": 0.0,
      "avg_vol": 0.0,
      "avg_atr": 0.0
    },
    "market": {
      "dominant_side": "NEUTRAL",
      "volatility_regime": "LOW"
    }
  }
}
"""

from typing import Tuple

def short_filter(s):
    vol = s.get('avg_vol', 0)
    side = s.get('dominant_side', 'NEUTRAL')
    if side == 'NEUTRAL' and vol < 12000: return False, 0.0, 'Neutral Side with Low Volume'
    if side != 'NEUTRAL': return False, 0.0, 'Not Neutral Side'
    return True, min(1.0, vol / 120000), 'Volume within range'
