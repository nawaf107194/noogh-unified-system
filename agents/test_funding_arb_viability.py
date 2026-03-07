#!/usr/bin/env python3
"""
Funding Arbitrage Viability Test
=================================
Test if delta-neutral funding arbitrage is profitable

Strategy:
- When funding rate > threshold (e.g., 0.01%)
  → Long Spot + Short Perp = Earn funding every 8h
- When funding rate < -threshold
  → Short Spot + Long Perp = Earn funding every 8h

This is TRUE ARBITRAGE (not prediction):
- Delta-neutral (price movement doesn't matter)
- Earn funding payments (guaranteed every 8h)
- Risk: Basis risk, fees, liquidation
"""

import pandas as pd
import numpy as np
from pathlib import Path


def calculate_funding_arb_returns(
    funding_rate: float,
    position_size: float = 1.0,
    spot_fee: float = 0.001,  # 0.1% spot trade fee
    perp_fee: float = 0.0005,  # 0.05% perp trade fee (maker)
    hold_periods: int = 1  # How many 8h periods to hold
) -> dict:
    """
    Calculate returns from funding arbitrage position

    Args:
        funding_rate: Current funding rate (e.g., 0.0001 = 0.01%)
        position_size: Position size in USDT
        spot_fee: Spot trading fee (one-way)
        perp_fee: Perpetual contract fee (one-way)
        hold_periods: Number of 8h funding periods to hold

    Returns:
        dict with gross_return, fees, net_return, roi_per_period
    """
    # Entry costs (open both positions)
    entry_fee = (spot_fee + perp_fee) * position_size

    # Exit costs (close both positions)
    exit_fee = (spot_fee + perp_fee) * position_size

    total_fees = entry_fee + exit_fee

    # Funding earned (absolute value since we're on the right side)
    funding_earned = abs(funding_rate) * position_size * hold_periods

    # Net return
    net_return = funding_earned - total_fees

    # ROI per funding period (8h)
    roi_per_period = (net_return / position_size) / hold_periods if hold_periods > 0 else 0

    return {
        'gross_funding': funding_earned,
        'total_fees': total_fees,
        'net_return': net_return,
        'roi_per_period': roi_per_period,
        'profitable': net_return > 0
    }


def find_arb_opportunities(
    df: pd.DataFrame,
    min_funding_rate: float = 0.005,  # 0.5% = high enough to be profitable
    min_hold_periods: int = 1  # Minimum hold (1 period = 8h)
) -> list:
    """
    Find funding arbitrage opportunities in historical data

    Returns list of opportunities with entry/exit timestamps and returns
    """
    opportunities = []

    # Funding happens every 8 hours (3 times per day)
    # We'll sample at 8h intervals
    funding_times = df.index[::8]  # Every 8 hours

    i = 0
    while i < len(funding_times) - 1:
        ts = funding_times[i]

        if ts not in df.index:
            i += 1
            continue

        funding_rate = df.loc[ts, 'funding_rate']

        # Check if funding rate is extreme enough
        if abs(funding_rate) < min_funding_rate:
            i += 1
            continue

        # Found opportunity - determine hold period
        # Hold until funding normalizes or max 7 days (21 periods)
        hold_periods = 0
        exit_idx = i

        for j in range(i + 1, min(i + 22, len(funding_times))):  # Max 21 periods ahead
            future_ts = funding_times[j]

            if future_ts not in df.index:
                break

            future_funding = df.loc[future_ts, 'funding_rate']
            hold_periods += 1

            # Exit when funding normalizes (crosses zero or drops below threshold)
            if abs(future_funding) < abs(funding_rate) * 0.5:  # 50% reduction
                exit_idx = j
                break

        if hold_periods == 0:
            hold_periods = 1  # Minimum 1 period
            exit_idx = i + 1

        # Calculate returns for this opportunity
        returns = calculate_funding_arb_returns(
            funding_rate=funding_rate,
            position_size=1000,  # Example: $1000 position
            hold_periods=hold_periods
        )

        if returns['profitable']:
            opportunities.append({
                'entry_time': ts,
                'exit_time': funding_times[min(exit_idx, len(funding_times)-1)],
                'funding_rate': funding_rate,
                'hold_periods': hold_periods,
                'hold_hours': hold_periods * 8,
                'gross_funding': returns['gross_funding'],
                'fees': returns['total_fees'],
                'net_return': returns['net_return'],
                'roi_per_period': returns['roi_per_period'],
                'annualized_roi': returns['roi_per_period'] * 365 * 3  # 3 periods per day
            })

        # Jump to exit point
        i = exit_idx + 1

    return opportunities


def main():
    print("="*70)
    print("💰 FUNDING ARBITRAGE VIABILITY TEST")
    print("="*70)

    # Load funding data
    data_file = Path(__file__).parent.parent / 'data' / 'BTCUSDT_1h_with_funding_12M.parquet'

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return

    df = pd.read_parquet(data_file)
    print(f"\n✅ Loaded {len(df):,} 1h bars with funding rates")
    print(f"   Date range: {df.index[0]} → {df.index[-1]}")

    # Quick funding stats
    print(f"\n📊 Funding Rate Distribution:")
    print(f"   Mean:   {df['funding_rate'].mean()*100:.4f}%")
    print(f"   Median: {df['funding_rate'].median()*100:.4f}%")
    print(f"   Std:    {df['funding_rate'].std()*100:.4f}%")
    print(f"   Min:    {df['funding_rate'].min()*100:.4f}%")
    print(f"   Max:    {df['funding_rate'].max()*100:.4f}%")
    print(f"   P90:    {df['funding_rate'].quantile(0.90)*100:.4f}%")
    print(f"   P95:    {df['funding_rate'].quantile(0.95)*100:.4f}%")

    # Test different thresholds
    thresholds = [0.003, 0.005, 0.008, 0.010]  # 0.3%, 0.5%, 0.8%, 1.0%

    print(f"\n{'='*70}")
    print(f"🔍 TESTING DIFFERENT ENTRY THRESHOLDS")
    print(f"{'='*70}")

    best_threshold = None
    best_roi = 0

    for threshold in thresholds:
        print(f"\n📌 THRESHOLD: {threshold*100:.2f}% (funding rate)")
        print(f"-"*70)

        # Find opportunities
        opps = find_arb_opportunities(
            df,
            min_funding_rate=threshold,
            min_hold_periods=1
        )

        if len(opps) == 0:
            print(f"   ❌ No opportunities found")
            continue

        # Calculate stats
        total_return = sum(opp['net_return'] for opp in opps)
        avg_return = total_return / len(opps)
        avg_hold = sum(opp['hold_hours'] for opp in opps) / len(opps)
        avg_roi_period = sum(opp['roi_per_period'] for opp in opps) / len(opps)

        # Annualized ROI (assuming 3 funding periods per day)
        periods_per_year = 365 * 3
        annualized_roi = avg_roi_period * periods_per_year

        # How many opportunities per month
        days_covered = (df.index[-1] - df.index[0]).days
        opps_per_month = len(opps) / (days_covered / 30)

        print(f"   Opportunities: {len(opps)} ({opps_per_month:.1f}/month)")
        print(f"   Avg Hold: {avg_hold:.1f} hours ({avg_hold/24:.1f} days)")
        print(f"   Avg ROI per period (8h): {avg_roi_period*100:.3f}%")
        print(f"   Annualized ROI: {annualized_roi*100:.1f}%")
        print(f"   Total Return ($1000 position): ${total_return:.2f}")

        if annualized_roi > best_roi:
            best_roi = annualized_roi
            best_threshold = threshold

        # Show top 5 opportunities
        if len(opps) >= 5:
            print(f"\n   Top 5 Opportunities:")
            sorted_opps = sorted(opps, key=lambda x: x['net_return'], reverse=True)
            for opp in sorted_opps[:5]:
                print(f"   • {opp['entry_time']} | Funding: {opp['funding_rate']*100:.3f}% | Hold: {opp['hold_hours']}h | Return: ${opp['net_return']:.2f}")

    print(f"\n{'='*70}")
    print(f"🎯 VIABILITY ASSESSMENT")
    print(f"{'='*70}")

    if best_threshold is None:
        print(f"\n❌ FUNDING ARBITRAGE NOT VIABLE")
        print(f"   • No profitable opportunities found at any threshold")
        print(f"   • Fees exceed funding payments")
        print(f"   • Recommendation: NOT WORTH PURSUING")

    else:
        print(f"\n✅ BEST CONFIGURATION:")
        print(f"   Entry Threshold: {best_threshold*100:.2f}%")
        print(f"   Expected Annualized ROI: {best_roi*100:.1f}%")

        # Re-run with best threshold for detailed stats
        best_opps = find_arb_opportunities(df, min_funding_rate=best_threshold)
        days_covered = (df.index[-1] - df.index[0]).days
        opps_per_month = len(best_opps) / (days_covered / 30)

        print(f"\n📊 EXPECTED PERFORMANCE:")
        print(f"   Opportunities per month: {opps_per_month:.1f}")

        if best_roi >= 0.20:  # 20% annualized
            print(f"\n✅ VIABLE - Worth pursuing")
            print(f"   • Expected monthly return: ~{best_roi*100/12:.1f}% on capital")
            print(f"   • Low risk (delta-neutral)")
            print(f"   • Automatable")
        elif best_roi >= 0.10:  # 10% annualized
            print(f"\n⚠️  MARGINAL - Low returns but safe")
            print(f"   • Expected monthly return: ~{best_roi*100/12:.1f}%")
            print(f"   • Better than staking but not exciting")
        else:
            print(f"\n❌ NOT VIABLE - Returns too low")
            print(f"   • Expected monthly return: ~{best_roi*100/12:.1f}%")
            print(f"   • Not worth the complexity")

    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()
