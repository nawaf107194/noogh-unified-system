"""Emergency: Set SL/TP for all open Binance Futures positions"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from trading.binance_futures import BinanceFuturesManager

fm = BinanceFuturesManager(testnet=False, read_only=False, max_leverage=20)

# Get all open positions
positions = fm.get_positions()
if not positions:
    print("No open positions found")
    sys.exit(0)

for pos in positions:
    symbol = pos['symbol']
    qty = abs(float(pos.get('positionAmt', 0)))
    entry = float(pos.get('entryPrice', 0))
    side = pos.get('positionSide', 'BOTH')
    
    if qty <= 0 or entry <= 0:
        continue
    
    # Determine if LONG or SHORT
    is_long = float(pos.get('positionAmt', 0)) > 0
    
    # Calculate SL/TP based on 0.4% risk, 2:1 R:R
    sl_pct = 0.004  # 0.4%
    tp_pct = 0.008  # 0.8% (2x SL)
    
    if is_long:
        sl_price = entry * (1 - sl_pct)
        tp_price = entry * (1 + tp_pct)
        sl_side = 'SELL'
        tp_side = 'SELL'
    else:  # SHORT
        sl_price = entry * (1 + sl_pct)
        tp_price = entry * (1 - tp_pct)
        sl_side = 'BUY'
        tp_side = 'BUY'
    
    # Round prices
    sl_price = fm.round_price(symbol, sl_price)
    tp_price = fm.round_price(symbol, tp_price)
    rounded_qty = fm.round_quantity(symbol, qty)
    
    print(f"\n{'🟢 LONG' if is_long else '🔴 SHORT'} {symbol}")
    print(f"  Entry: {entry}, Qty: {qty}")
    print(f"  SL: {sl_price}, TP: {tp_price}")
    
    # Cancel existing orders for this symbol first
    try:
        fm.cancel_all_orders(symbol)
        print(f"  ✅ Cancelled existing orders")
    except Exception as e:
        print(f"  ⚠️ Cancel error: {e}")
    
    # Set Stop Loss
    try:
        sl_order = fm.client.futures_create_order(
            symbol=symbol,
            side=sl_side,
            type='STOP_MARKET',
            stopPrice=sl_price,
            quantity=rounded_qty,
            reduceOnly=True
        )
        print(f"  ✅ SL set at {sl_price} (order #{sl_order.get('orderId', '?')})")
    except Exception as e:
        print(f"  ❌ SL error: {e}")
        # Fallback: closePosition
        try:
            sl_order = fm.client.futures_create_order(
                symbol=symbol,
                side=sl_side,
                type='STOP_MARKET',
                stopPrice=sl_price,
                closePosition=True
            )
            print(f"  ✅ SL (closePosition) set at {sl_price}")
        except Exception as e2:
            print(f"  ❌ SL fallback error: {e2}")
    
    # Set Take Profit
    try:
        tp_order = fm.client.futures_create_order(
            symbol=symbol,
            side=tp_side,
            type='TAKE_PROFIT_MARKET',
            stopPrice=tp_price,
            quantity=rounded_qty,
            reduceOnly=True
        )
        print(f"  ✅ TP set at {tp_price} (order #{tp_order.get('orderId', '?')})")
    except Exception as e:
        print(f"  ❌ TP error: {e}")
        # Fallback
        try:
            tp_order = fm.client.futures_create_order(
                symbol=symbol,
                side=tp_side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=tp_price,
                closePosition=True
            )
            print(f"  ✅ TP (closePosition) set at {tp_price}")
        except Exception as e2:
            print(f"  ❌ TP fallback error: {e2}")

print("\n✅ Done setting SL/TP for all positions")
