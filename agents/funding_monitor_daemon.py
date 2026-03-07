#!/usr/bin/env python3
"""
Funding Rate Monitoring Daemon
================================
Runs every 8 hours (at funding times: 00:00, 08:00, 16:00 UTC)
Scans for regime changes and sends alerts

Alert Triggers:
- ✅ Symbol enters HOT regime (>0.10% daily for 3 days)
- ⚠️  Symbol enters WARM regime (>0.04% daily)
- 🔄 Regime shift detected (NEUTRAL → HOT)
- 💰 New opportunity detected (first time above threshold)

Alerts sent via:
- Console output
- JSON log file
- (Optional) Telegram/Discord webhook
"""

import os
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from funding_regime_detector import FundingRegimeDetector


class FundingMonitor:
    """Continuous funding rate monitor"""

    def __init__(self, alert_threshold_hot: float = 0.0010, alert_threshold_warm: float = 0.0004):
        self.detector = FundingRegimeDetector()
        self.alert_threshold_hot = alert_threshold_hot
        self.alert_threshold_warm = alert_threshold_warm

        # State tracking
        self.last_scan = None
        self.previous_regimes = {}
        self.alerts_file = Path(__file__).parent.parent / 'data' / 'funding_alerts.jsonl'

    def scan_and_alert(self):
        """Scan market and generate alerts"""
        print(f"\n{'='*70}")
        print(f"⏰ FUNDING MONITOR SCAN")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*70}\n")

        # Scan current regimes
        df = self.detector.scan_all_regimes()

        if df.empty:
            print("⚠️  No data retrieved")
            return

        # Generate alerts
        alerts = []

        for _, row in df.iterrows():
            symbol = row['symbol']
            regime = row['regime']
            funding = row['avg_3d_daily']

            # Get previous regime
            prev_regime = self.previous_regimes.get(symbol, 'NEUTRAL')

            # Alert conditions
            if regime == 'HOT' and prev_regime != 'HOT':
                alerts.append({
                    'type': 'NEW_HOT',
                    'symbol': symbol,
                    'funding_daily': funding,
                    'apr_estimate': row['apr_estimate'],
                    'message': f"🔥 NEW HOT: {symbol} entered HOT regime ({funding*100:.4f}% daily = {row['apr_estimate']} APR)",
                    'action': 'DEPLOY CAPITAL NOW',
                    'timestamp': datetime.now().isoformat()
                })

            elif regime == 'WARM' and prev_regime == 'NEUTRAL':
                alerts.append({
                    'type': 'NEW_WARM',
                    'symbol': symbol,
                    'funding_daily': funding,
                    'apr_estimate': row['apr_estimate'],
                    'message': f"⚠️  NEW WARM: {symbol} entered WARM regime ({funding*100:.4f}% daily)",
                    'action': 'Consider deployment',
                    'timestamp': datetime.now().isoformat()
                })

            elif regime == 'INVERSE_HOT' and prev_regime != 'INVERSE_HOT':
                alerts.append({
                    'type': 'INVERSE_HOT',
                    'symbol': symbol,
                    'funding_daily': funding,
                    'apr_estimate': row['apr_estimate'],
                    'message': f"❄️🔥 INVERSE HOT: {symbol} ({funding*100:.4f}% daily = {row['apr_estimate']} APR)",
                    'action': 'SHORT SPOT + LONG PERP (advanced)',
                    'timestamp': datetime.now().isoformat()
                })

            # Update previous regime
            self.previous_regimes[symbol] = regime

        # Print alerts
        if alerts:
            print(f"\n🚨 {len(alerts)} ALERTS TRIGGERED:")
            print(f"{'='*70}")

            for alert in alerts:
                print(f"\n{alert['message']}")
                print(f"   Action: {alert['action']}")

            # Save alerts to log
            self.save_alerts(alerts)

        else:
            print("✅ No new alerts - market unchanged")

        # Print summary
        self.detector.print_regime_report(df)

        self.last_scan = datetime.now()

    def save_alerts(self, alerts: list):
        """Save alerts to JSONL file"""
        with open(self.alerts_file, 'a') as f:
            for alert in alerts:
                f.write(json.dumps(alert) + '\n')

        print(f"\n💾 {len(alerts)} alerts saved to: {self.alerts_file.name}")

    def run_continuous(self, interval_hours: int = 8):
        """Run monitor continuously"""
        print(f"\n🤖 FUNDING MONITOR DAEMON STARTED")
        print(f"   Scan interval: Every {interval_hours} hours (at funding times)")
        print(f"   Alerts: {self.alerts_file}")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                self.scan_and_alert()

                # Wait for next funding time (8 hours)
                print(f"\n⏳ Next scan in {interval_hours} hours...")
                time.sleep(interval_hours * 3600)

        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitor stopped by user")


def run_single_scan():
    """Run a single scan (for testing)"""
    monitor = FundingMonitor()
    monitor.scan_and_alert()


def run_daemon():
    """Run continuous monitoring"""
    monitor = FundingMonitor()
    monitor.run_continuous(interval_hours=8)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        run_daemon()
    else:
        # Single scan by default
        run_single_scan()
