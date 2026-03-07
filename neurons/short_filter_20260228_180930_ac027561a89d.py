"""
{
  "name": "short_filter",
  "hash": "ac027561a89d",
  "created_utc": "2026-02-28T15:09:30Z",
  "created_local": "20260228_180930",
  "model": "noogh-teacher",
  "prompt_hash": "8ab01a65719e",
  "market": {
    "dominant_side": "SHORT",
    "volatility_regime": "LOW"
  },
  "stats": {
    "counts": {
      "total": 80,
      "long_total": 0,
      "short_total": 80
    },
    "long": {
      "wins": 0,
      "losses": 0,
      "wr": 0.0,
      "avg_tbr": 0.0,
      "avg_atr": 0.0
    },
    "short": {
      "wins": 49,
      "losses": 28,
      "wr": 63.63636363636363,
      "avg_vol": 1564739.190375,
      "avg_atr": 5.8461668928571395
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
    vol_z = s.get('vol_z', 0)
    atr_1h_pct = s.get('atr_1h_pct', 0)
    if vol_z < 1 or atr_1h_pct < 0.005:
        return False, 0.0, 'Low Volume or ATR'
    return True, min(1.0, vol_z * atr_1h_pct), 'Good Volume and ATR'
