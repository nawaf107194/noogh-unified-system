"""
{
  "name": "short_filter",
  "hash": "8705a906f0df",
  "created_utc": "2026-02-28T03:35:29Z",
  "created_local": "20260228_063529",
  "model": "noogh-teacher",
  "prompt_hash": "85d04318b86f",
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
    if side == 'NEUTRAL' and vol < 10000: return False, 0.0, 'Neutral Side with Low Volume'
    if side != 'NEUTRAL': return False, 0.0, 'Not Neutral Side'
    return True, min(1.0, vol / 100000), 'Volume within range'
