"""
{
  "name": "long_filter",
  "hash": "05610d470716",
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

def long_filter(s):
    atr = s.get('avg_atr', 0)
    vol_regime = s.get('volatility_regime', 'MEDIUM')
    if vol_regime == 'LOW' and atr < 0.005: return False, 0.0, 'Low ATR in Low Volatility'
    if vol_regime != 'LOW': return False, 0.0, 'Not Low Volatility'
    return True, min(1.0, atr / 0.05), 'ATR within range'
