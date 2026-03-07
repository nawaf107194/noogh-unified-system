#!/usr/bin/env python3
"""
Inverse Funding Arbitrage Paper Trading Simulator
==================================================
Simulates inverse funding arbitrage positions without real capital

Tracks:
- Entry/exit timestamps
- Funding collected every 8h
- Borrow fees (daily)
- Trading fees
- Real-time P&L
- Performance metrics

Usage:
    python3 paper_trade_inverse_arb.py ATOMUSDT 1000 --days 14
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from binance.client import Client

API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")


class PaperTradeSimulator:
    """Paper trading simulator for inverse funding arbitrage"""

    def __init__(self, symbol: str, capital: float):
        self.client = Client(API_KEY, API_SECRET)
        self.symbol = symbol
        self.capital = capital

        self.positions_file = Path(__file__).parent.parent / 'data' / 'paper_trades.jsonl'

        # Current position
        self.position = None

    def get_current_price(self) -> float:
        """Get current mark price"""
        try:
            ticker = self.client.futures_mark_price(symbol=self.symbol)
            return float(ticker['markPrice'])
        except:
            return None

    def get_funding_rate(self) -> float:
        """Get current funding rate"""
        try:
            rates = self.client.futures_funding_rate(symbol=self.symbol, limit=1)
            if rates:
                return float(rates[0]['fundingRate'])
            return None
        except:
            return None

    def enter_position(self):
        """Enter inverse arb position (SHORT SPOT + LONG PERP)"""

        price = self.get_current_price()
        funding = self.get_funding_rate()

        if not price or not funding:
            print("❌ Error: Could not fetch market data")
            return False

        position_size = self.capital / price

        self.position = {
            'symbol': self.symbol,
            'entry_time': datetime.now().isoformat(),
            'entry_price': price,
            'position_size': position_size,
            'capital': self.capital,
            'entry_funding_rate': funding,
            'type': 'INVERSE_ARB',

            # Tracking
            'funding_collections': [],
            'borrow_fees': 0,
            'entry_fees': self.capital * 0.0015,  # 0.15% entry fees

            # Status
            'status': 'OPEN',
            'exit_time': None,
            'exit_price': None,
            'exit_fees': 0,
            'realized_pnl': 0
        }

        print("="*70)
        print("✅ PAPER TRADE POSITION OPENED")
        print("="*70)
        print(f"Symbol:        {self.symbol}")
        print(f"Type:          INVERSE ARB (Short Spot + Long Perp)")
        print(f"Entry Time:    {self.position['entry_time']}")
        print(f"Entry Price:   ${price:.4f}")
        print(f"Position Size: {position_size:.4f} {self.symbol[:-4]}")
        print(f"Capital:       ${self.capital:,.2f}")
        print(f"Funding Rate:  {funding*100:.4f}% per 8h")
        print(f"Entry Fees:    ${self.position['entry_fees']:.2f}")
        print("="*70)

        # Save to file
        self.save_position()

        return True

    def collect_funding(self):
        """Collect funding payment (called every 8h)"""

        if not self.position or self.position['status'] != 'OPEN':
            print("⚠️  No open position")
            return

        funding_rate = self.get_funding_rate()

        if not funding_rate:
            print("❌ Error: Could not fetch funding rate")
            return

        # Calculate funding collected
        funding_payment = abs(funding_rate) * self.capital

        collection = {
            'time': datetime.now().isoformat(),
            'funding_rate': funding_rate,
            'payment': funding_payment
        }

        self.position['funding_collections'].append(collection)

        total_funding = sum(c['payment'] for c in self.position['funding_collections'])

        print(f"\n💰 Funding Collected:")
        print(f"   Time:          {collection['time']}")
        print(f"   Rate:          {funding_rate*100:.4f}% per 8h")
        print(f"   Payment:       ${funding_payment:.2f}")
        print(f"   Total So Far:  ${total_funding:.2f}")

        self.save_position()

    def apply_borrow_fees(self):
        """Apply daily borrow fees"""

        if not self.position or self.position['status'] != 'OPEN':
            return

        daily_borrow_fee = self.capital * 0.0003  # 0.03% daily

        self.position['borrow_fees'] += daily_borrow_fee

        print(f"\n📉 Borrow Fee Applied:")
        print(f"   Daily Fee:    ${daily_borrow_fee:.2f}")
        print(f"   Total Fees:   ${self.position['borrow_fees']:.2f}")

        self.save_position()

    def exit_position(self):
        """Exit position and calculate final P&L"""

        if not self.position or self.position['status'] != 'OPEN':
            print("⚠️  No open position to close")
            return

        price = self.get_current_price()

        if not price:
            print("❌ Error: Could not fetch price")
            return

        # Calculate P&L
        total_funding = sum(c['payment'] for c in self.position['funding_collections'])
        exit_fees = self.capital * 0.0015  # 0.15% exit fees

        total_fees = self.position['entry_fees'] + self.position['borrow_fees'] + exit_fees
        realized_pnl = total_funding - total_fees

        # Update position
        self.position['exit_time'] = datetime.now().isoformat()
        self.position['exit_price'] = price
        self.position['exit_fees'] = exit_fees
        self.position['realized_pnl'] = realized_pnl
        self.position['status'] = 'CLOSED'

        # Calculate metrics
        entry_time = datetime.fromisoformat(self.position['entry_time'])
        exit_time = datetime.fromisoformat(self.position['exit_time'])
        hold_hours = (exit_time - entry_time).total_seconds() / 3600
        hold_days = hold_hours / 24

        roi = (realized_pnl / self.capital) * 100
        apr = (roi / hold_days) * 365 if hold_days > 0 else 0

        print("\n" + "="*70)
        print("🔒 PAPER TRADE POSITION CLOSED")
        print("="*70)
        print(f"Symbol:           {self.symbol}")
        print(f"Entry Price:      ${self.position['entry_price']:.4f}")
        print(f"Exit Price:       ${price:.4f}")
        print(f"Hold Period:      {hold_days:.2f} days")
        print(f"\n💰 P&L BREAKDOWN:")
        print(f"   Funding Collected:  +${total_funding:.2f}")
        print(f"   Entry Fees:         -${self.position['entry_fees']:.2f}")
        print(f"   Borrow Fees:        -${self.position['borrow_fees']:.2f}")
        print(f"   Exit Fees:          -${exit_fees:.2f}")
        print(f"   ─────────────────────────────")
        print(f"   Realized P&L:       ${realized_pnl:+.2f}")
        print(f"\n📊 PERFORMANCE:")
        print(f"   ROI:                {roi:+.2f}%")
        print(f"   APR:                {apr:.1f}%")
        print(f"   Funding Periods:    {len(self.position['funding_collections'])}")
        print("="*70)

        self.save_position()

        return {
            'realized_pnl': realized_pnl,
            'roi': roi,
            'apr': apr,
            'hold_days': hold_days
        }

    def save_position(self):
        """Save position to JSONL file"""
        with open(self.positions_file, 'a') as f:
            f.write(json.dumps(self.position) + '\n')

    def simulate_full_period(self, days: int = 14):
        """Simulate full trading period with historical funding data"""

        print(f"\n{'='*70}")
        print(f"🔬 SIMULATING {days}-DAY PAPER TRADE")
        print(f"{'='*70}\n")

        # Enter position
        if not self.enter_position():
            return

        # Get historical funding rates
        try:
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            rates = self.client.futures_funding_rate(
                symbol=self.symbol,
                startTime=start_time,
                endTime=end_time,
                limit=1000
            )

            if not rates:
                print("❌ No historical funding data")
                return

            print(f"\n⏳ Simulating {len(rates)} funding periods ({len(rates)/3:.1f} days)...\n")

            # Simulate funding collections
            for i, rate_data in enumerate(rates):
                funding_rate = float(rate_data['fundingRate'])
                funding_payment = abs(funding_rate) * self.capital

                collection = {
                    'time': pd.Timestamp(int(rate_data['fundingTime']), unit='ms').isoformat(),
                    'funding_rate': funding_rate,
                    'payment': funding_payment
                }

                self.position['funding_collections'].append(collection)

                # Apply borrow fees every 3 periods (1 day)
                if (i + 1) % 3 == 0:
                    self.position['borrow_fees'] += self.capital * 0.0003

            # Calculate final stats
            total_funding = sum(c['payment'] for c in self.position['funding_collections'])
            print(f"✅ Simulation Complete:")
            print(f"   Funding Periods:     {len(self.position['funding_collections'])}")
            print(f"   Total Funding:       ${total_funding:.2f}")
            print(f"   Total Borrow Fees:   ${self.position['borrow_fees']:.2f}")

            # Exit position
            print()
            self.exit_position()

        except Exception as e:
            print(f"❌ Simulation error: {e}")


    def simulate_with_current_rates(self, days: int = 14):
        """Simulate using CURRENT funding rate (projected forward)"""

        print(f"\n{'='*70}")
        print(f"🔬 PROJECTING CURRENT RATES FORWARD ({days} days)")
        print(f"{'='*70}\n")

        # Enter position
        if not self.enter_position():
            return

        # Get current 3-day average funding rate
        try:
            rates = self.client.futures_funding_rate(symbol=self.symbol, limit=9)

            if not rates:
                print("❌ No funding data")
                return

            # Calculate 3-day average
            recent_rates = [float(r['fundingRate']) for r in rates]
            avg_funding_8h = sum(recent_rates) / len(recent_rates)

            print(f"📊 CURRENT FUNDING RATE ANALYSIS:")
            print(f"   3-day avg:     {avg_funding_8h*100:.4f}% per 8h")
            print(f"   Daily rate:    {avg_funding_8h*3*100:.4f}%")
            print(f"   Projected APR: {abs(avg_funding_8h*3)*365*100:.0f}%")
            print(f"\n⏳ Projecting this rate forward for {days} days...\n")

            # Simulate funding collections using current rate
            funding_periods = days * 3

            for i in range(funding_periods):
                funding_payment = abs(avg_funding_8h) * self.capital

                collection = {
                    'time': (datetime.now() + timedelta(hours=8*i)).isoformat(),
                    'funding_rate': avg_funding_8h,
                    'payment': funding_payment
                }

                self.position['funding_collections'].append(collection)

                # Apply borrow fees every 3 periods (1 day)
                if (i + 1) % 3 == 0:
                    self.position['borrow_fees'] += self.capital * 0.0003

            # Calculate final stats
            total_funding = sum(c['payment'] for c in self.position['funding_collections'])
            print(f"✅ Projection Complete:")
            print(f"   Funding Periods:     {len(self.position['funding_collections'])}")
            print(f"   Projected Funding:   ${total_funding:.2f}")
            print(f"   Total Borrow Fees:   ${self.position['borrow_fees']:.2f}")

            # Exit position
            print()
            result = self.exit_position()

            if result:
                print(f"\n💡 INTERPRETATION:")
                if result['apr'] > 100:
                    print(f"   ✅ EXCELLENT - If funding stays at current levels:")
                    print(f"      Expected: ${result['realized_pnl']:.2f} profit ({result['roi']:.2f}% ROI)")
                    print(f"      This is {result['apr']:.0f}% annualized")
                elif result['apr'] > 50:
                    print(f"   ✅ GOOD - Solid returns if sustained:")
                    print(f"      Expected: ${result['realized_pnl']:.2f} profit ({result['roi']:.2f}% ROI)")
                else:
                    print(f"   ⚠️  MARGINAL - Returns depend on funding stability")

                print(f"\n⚠️  ASSUMPTIONS:")
                print(f"   • Funding rate remains at {avg_funding_8h*100:.4f}% per 8h")
                print(f"   • No funding reversal occurs")
                print(f"   • Borrow fees stay at 0.03% daily")
                print(f"   • ACTUAL results will vary based on real funding changes")

        except Exception as e:
            print(f"❌ Simulation error: {e}")


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 paper_trade_inverse_arb.py <SYMBOL> <CAPITAL> [OPTIONS]")
        print("\nOptions:")
        print("  --days DAYS      Simulation period (default: 14)")
        print("  --current        Use current funding rate (projected forward)")
        print("  --historical     Use historical funding data (default)")
        print("\nExamples:")
        print("  python3 paper_trade_inverse_arb.py ATOMUSDT 1000 --days 14 --current")
        print("  python3 paper_trade_inverse_arb.py ATOMUSDT 1000 --historical")
        return

    symbol = sys.argv[1]
    capital = float(sys.argv[2])

    days = 14
    if '--days' in sys.argv:
        days_idx = sys.argv.index('--days') + 1
        if days_idx < len(sys.argv):
            days = int(sys.argv[days_idx])

    use_current = '--current' in sys.argv

    simulator = PaperTradeSimulator(symbol, capital)

    if use_current:
        simulator.simulate_with_current_rates(days=days)
    else:
        simulator.simulate_full_period(days=days)


if __name__ == "__main__":
    main()
