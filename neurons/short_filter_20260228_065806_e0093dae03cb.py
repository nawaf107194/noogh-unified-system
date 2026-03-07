"""
{
  "name": "short_filter",
  "hash": "e0093dae03cb",
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

def short_filter(s):
    volume = s.get('volume', 0)
    rsi = s.get('rsi', 0)
    if volume < 2000000 or rsi > 50:
        return False, 0.0, 'Volume too low or RSI above neutral'
    return True, min(1.0, volume / 5000000), 'Short conditions met'
