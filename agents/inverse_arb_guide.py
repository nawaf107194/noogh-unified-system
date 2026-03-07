#!/usr/bin/env python3
"""
Inverse Funding Arbitrage Execution Guide
==========================================
Step-by-step guide for executing inverse funding arbitrage

INVERSE ARB = When funding is NEGATIVE (shorts paying longs)
Strategy: SHORT SPOT + LONG PERP → Collect funding from shorts

Current Opportunities (Mar 2026):
- ATOMUSDT: -0.4782% daily = 175% APR
- AXSUSDT: -0.1473% daily = 54% APR
"""

import os
from binance.client import Client
from datetime import datetime, timedelta

API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")


class InverseArbGuide:
    """Generate execution guide for inverse funding arbitrage"""

    def __init__(self, symbol: str, capital_usdt: float = 1000):
        self.client = Client(API_KEY, API_SECRET)
        self.symbol = symbol
        self.capital = capital_usdt

    def get_current_price(self) -> float:
        """Get current mark price"""
        try:
            ticker = self.client.futures_mark_price(symbol=self.symbol)
            return float(ticker['markPrice'])
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None

    def get_funding_info(self) -> dict:
        """Get current funding rate info"""
        try:
            # Get recent funding history
            rates = self.client.futures_funding_rate(
                symbol=self.symbol,
                limit=9  # Last 3 days
            )

            if not rates:
                return None

            recent_rates = [float(r['fundingRate']) for r in rates]
            avg_funding_8h = sum(recent_rates) / len(recent_rates)
            avg_funding_daily = avg_funding_8h * 3

            return {
                'current_rate': float(rates[-1]['fundingRate']),
                'avg_8h': avg_funding_8h,
                'avg_daily': avg_funding_daily,
                'next_funding_time': rates[-1].get('fundingTime', 'Unknown')
            }
        except Exception as e:
            print(f"Error fetching funding: {e}")
            return None

    def calculate_position(self, price: float, funding_daily: float, hold_days: int = 14) -> dict:
        """Calculate position sizes and expected returns"""

        # Position size
        position_size_usdt = self.capital
        position_size_coin = position_size_usdt / price

        # Funding collected
        funding_periods = hold_days * 3  # 3 per day
        total_funding_rate = abs(funding_daily) * hold_days
        funding_collected_usdt = position_size_usdt * total_funding_rate

        # Fees (Bybit spot margin)
        spot_borrow_fee_daily = 0.0003  # ~0.03% daily (approximate)
        spot_borrow_fees = position_size_usdt * spot_borrow_fee_daily * hold_days

        # Trading fees
        spot_short_fee = position_size_usdt * 0.001  # 0.1% to open short
        perp_long_fee = position_size_usdt * 0.0005  # 0.05% to open long
        exit_fees = spot_short_fee + perp_long_fee  # Same to close
        total_trading_fees = (spot_short_fee + perp_long_fee) * 2  # Open + close

        # Net P&L
        total_fees = spot_borrow_fees + total_trading_fees
        net_profit = funding_collected_usdt - total_fees

        # ROI
        roi = (net_profit / position_size_usdt) * 100
        apr = (net_profit / position_size_usdt) * (365 / hold_days) * 100

        return {
            'capital': position_size_usdt,
            'position_coin': position_size_coin,
            'price': price,
            'funding_collected': funding_collected_usdt,
            'borrow_fees': spot_borrow_fees,
            'trading_fees': total_trading_fees,
            'total_fees': total_fees,
            'net_profit': net_profit,
            'roi_percent': roi,
            'apr_percent': apr,
            'hold_days': hold_days
        }

    def print_execution_guide(self):
        """Print complete execution guide"""

        print("="*70)
        print(f"🔧 INVERSE FUNDING ARB EXECUTION GUIDE")
        print(f"   Symbol: {self.symbol}")
        print(f"   Capital: ${self.capital:,.2f} USDT")
        print("="*70)

        # Get current data
        price = self.get_current_price()
        funding_info = self.get_funding_info()

        if not price or not funding_info:
            print("\n❌ Error: Could not fetch market data")
            return

        print(f"\n📊 CURRENT MARKET DATA:")
        print(f"   Price: ${price:.2f}")
        print(f"   Current Funding: {funding_info['current_rate']*100:.4f}% per 8h")
        print(f"   3-Day Avg: {funding_info['avg_daily']*100:.4f}% daily")
        print(f"   APR Estimate: {abs(funding_info['avg_daily'])*365*100:.0f}%")

        # Calculate for 14-day hold
        calc = self.calculate_position(price, funding_info['avg_daily'], hold_days=14)

        print(f"\n💰 POSITION SIZING (14-day hold):")
        print(f"   Short Spot: {calc['position_coin']:.4f} {self.symbol[:-4]}")
        print(f"   Long Perp:  {calc['position_coin']:.4f} {self.symbol[:-4]}")
        print(f"   Notional:   ${calc['capital']:,.2f} USDT")

        print(f"\n📈 EXPECTED RETURNS:")
        print(f"   Funding Collected: ${calc['funding_collected']:.2f}")
        print(f"   Borrow Fees:       -${calc['borrow_fees']:.2f}")
        print(f"   Trading Fees:      -${calc['trading_fees']:.2f}")
        print(f"   ────────────────────────────────")
        print(f"   Net Profit:        ${calc['net_profit']:.2f}")
        print(f"   ROI:               {calc['roi_percent']:.2f}%")
        print(f"   APR:               {calc['apr_percent']:.1f}%")

        print(f"\n🎯 RISK ASSESSMENT:")

        # Liquidation risk
        leverage = 1.0  # Delta-neutral, no leverage
        liquidation_distance = "N/A (delta-neutral)"

        print(f"   Directional Risk:  ZERO (delta-neutral)")
        print(f"   Leverage:          {leverage}x")
        print(f"   Liquidation Risk:  {liquidation_distance}")
        print(f"   Main Risk:         Funding reversal (exit early if needed)")

        print(f"\n{'='*70}")
        print(f"📋 STEP-BY-STEP EXECUTION (Bybit)")
        print(f"{'='*70}")

        steps = [
            ("1. Setup Bybit Account", [
                "• Enable Spot Margin trading",
                "• Transfer ${:,.2f} USDT to Spot account".format(self.capital),
                "• Verify margin borrowing is enabled"
            ]),

            ("2. Open Short Spot Position", [
                f"• Go to Spot → Margin Trading",
                f"• Borrow {calc['position_coin']:.4f} {self.symbol[:-4]}",
                f"• Sell {calc['position_coin']:.4f} {self.symbol[:-4]} at market",
                f"• Receive ~${calc['capital']:,.2f} USDT"
            ]),

            ("3. Open Long Perp Position", [
                f"• Go to Derivatives → {self.symbol} Perp",
                f"• Long {calc['position_coin']:.4f} {self.symbol[:-4]} (1x leverage)",
                f"• Use isolated margin mode",
                f"• Set TP/SL (optional)"
            ]),

            ("4. Monitor Position", [
                f"• Check funding collection every 8h (00:00, 08:00, 16:00 UTC)",
                f"• Expected: ${calc['funding_collected']/42:.2f} per funding period",
                f"• Monitor funding rate - exit if turns positive",
                f"• Check borrow fees daily"
            ]),

            ("5. Exit Strategy (Day 14 or earlier)", [
                f"• Close long perp: Sell {calc['position_coin']:.4f} {self.symbol[:-4]} perp",
                f"• Buy back {calc['position_coin']:.4f} {self.symbol[:-4]} spot",
                f"• Repay borrowed {self.symbol[:-4]}",
                f"• Withdraw profit"
            ])
        ]

        for title, items in steps:
            print(f"\n{title}")
            print("-" * 70)
            for item in items:
                print(f"   {item}")

        print(f"\n{'='*70}")
        print(f"⚠️  IMPORTANT NOTES:")
        print(f"{'='*70}")

        notes = [
            "• This is ADVANCED strategy - requires spot margin",
            "• Test with SMALL capital first ($100-500)",
            "• Monitor funding rate daily - exit if reverses",
            "• Borrow fees vary by exchange - verify current rates",
            "• Keep extra collateral for safety (110% of position)",
            "• Set price alerts at ±5% to monitor liquidation risk"
        ]

        for note in notes:
            print(f"   {note}")

        print(f"\n💡 RECOMMENDATION:")

        if calc['apr_percent'] > 100:
            print(f"   ✅ EXCELLENT opportunity ({calc['apr_percent']:.0f}% APR)")
            print(f"   Suggested allocation: 20-30% of capital")
        elif calc['apr_percent'] > 50:
            print(f"   ⚠️  GOOD opportunity ({calc['apr_percent']:.0f}% APR)")
            print(f"   Suggested allocation: 10-20% of capital")
        else:
            print(f"   ❌ Marginal opportunity ({calc['apr_percent']:.0f}% APR)")
            print(f"   Consider waiting for better rates")

        print(f"\n{'='*70}\n")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 inverse_arb_guide.py <SYMBOL> [CAPITAL_USDT]")
        print("Example: python3 inverse_arb_guide.py ATOMUSDT 1000")
        return

    symbol = sys.argv[1]
    capital = float(sys.argv[2]) if len(sys.argv) > 2 else 1000

    guide = InverseArbGuide(symbol, capital)
    guide.print_execution_guide()


if __name__ == "__main__":
    main()
