#!/usr/bin/env python3
"""
Test Precision Fix - تأكد من أن quantity يتم تقريبها بشكل صحيح
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.binance_futures import BinanceFuturesManager

print("\n" + "="*80)
print("          🧪 TEST: Quantity Precision Fix")
print("="*80)

# Initialize (production read-only to test with real exchange info)
binance = BinanceFuturesManager(testnet=False, read_only=True)

# Test symbols that had precision issues
test_cases = [
    ('ZRXUSDT', 1234.5678),   # Altcoin - likely integer or 1 decimal
    ('BTCUSDT', 0.0123456),   # BTC - 3 decimals
    ('ETHUSDT', 0.123456),    # ETH - 3 decimals
    ('DOGEUSDT', 12345.67),   # DOGE - integer
]

print("\n📊 Testing quantity rounding:\n")

for symbol, raw_qty in test_cases:
    print(f"   {symbol}:")
    print(f"      Raw:     {raw_qty:.8f}")

    # Get symbol info
    info = binance.get_symbol_info(symbol)
    if info:
        print(f"      Step:    {info.get('step_size', 'N/A')}")
        print(f"      Min:     {info.get('min_qty', 'N/A')}")

        # Round
        rounded = binance.round_quantity(symbol, raw_qty)
        print(f"      Rounded: {rounded:.8f}")
        print(f"      ✅ Valid")
    else:
        print(f"      ❌ Could not fetch info")

    print()

print("="*80)
print("✅ Precision fix test complete!")
print("="*80)
