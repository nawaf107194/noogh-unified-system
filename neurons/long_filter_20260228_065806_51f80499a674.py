"""
{
  "name": "long_filter",
  "hash": "51f80499a674",
  "created_utc": "2026-02-28T03:58:06Z",
  "created_local": "20260228_065806",
  "model": "noogh-teacher",
  "prompt_hash": "9857a6d5afdd",
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
    tbr = s.get('taker_buy_ratio', 0)
    if atr < 5 or tbr < 0.5:
        return False, 0.0, 'ATR too low or TBR below threshold'
    return True, min(1.0, atr / 100), 'Long conditions met'
