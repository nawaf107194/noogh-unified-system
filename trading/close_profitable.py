#!/usr/bin/env python3
"""Close only profitable positions on Binance Futures"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from trading.binance_futures import BinanceFuturesManager

fm = BinanceFuturesManager(testnet=False, read_only=False)

print("Fetching positions...")
risks = fm.client.futures_position_information()
open_pos = [r for r in risks if float(r.get('positionAmt', 0)) != 0]

print(f"\n{'='*60}")
print(f"  {len(open_pos)} OPEN POSITIONS")
print(f"{'='*60}")

profitable = []
losing = []

for p in open_pos:
    amt = float(p['positionAmt'])
    side = 'LONG' if amt > 0 else 'SHORT'
    entry = float(p['entryPrice'])
    upnl = float(p['unRealizedProfit'])
    mark = float(p.get('markPrice', 0))
    lev = p.get('leverage', '?')
    
    if upnl > 0:
        profitable.append(p)
        emoji = '🟢'
    else:
        losing.append(p)
        emoji = '🔴'
    
    print(f"  {emoji} {p['symbol']:15s} {side:5s} | Lev: {lev}x | Entry: ${entry:.6f} | uPNL: ${upnl:+.4f}")

print(f"\n{'='*60}")
print(f"  🟢 Profitable: {len(profitable)} | 🔴 Losing: {len(losing)}")
print(f"{'='*60}")

if profitable:
    print(f"\n🚀 Closing {len(profitable)} profitable position(s)...")
    for p in profitable:
        symbol = p['symbol']
        amt = float(p['positionAmt'])
        upnl = float(p['unRealizedProfit'])
        side = 'SELL' if amt > 0 else 'BUY'
        qty = abs(amt)
        try:
            order = fm.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=qty,
                reduceOnly=True
            )
            print(f"  ✅ {symbol} closed | Profit: ${upnl:+.4f} | OrderID: {order['orderId']}")
        except Exception as e:
            print(f"  ❌ {symbol}: {e}")
    print("\nDone! ✅")
else:
    print("\n⚠️ No profitable positions to close.")

# Show remaining
print(f"\n🔴 {len(losing)} losing position(s) still open:")
for p in losing:
    print(f"  {p['symbol']}: uPNL ${float(p['unRealizedProfit']):+.4f}")
