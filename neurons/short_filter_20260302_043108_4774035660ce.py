"""
{
  "name": "short_filter",
  "hash": "4774035660ce",
  "created_utc": "2026-03-02T01:31:08Z",
  "created_local": "20260302_043108",
  "model": "qwen2.5:7b",
  "prompt_hash": "5f1c395fe61f",
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
    tbr_delta = s.get('tbr_delta', 0)
    if tbr_delta > 0.05:
        return False, 0.0, 'Positive TBR Delta'
    atr_1h_pct = s.get('atr_1h_pct', 0)
    if atr_1h_pct > 0.015:
        return False, 0.0, 'High ATR'
    return True, min(1.0, tbr_delta * atr_1h_pct), 'Negative TBR Delta and Low ATR'
