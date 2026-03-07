#!/usr/bin/env python3
"""
مراقبة حية لـ Autonomous Trading Agent
يعرض الحالة real-time
"""
import time
import os
import sys
from datetime import datetime

LOG_FILE = "/home/noogh/projects/noogh_unified_system/src/logs/autonomous_trading_agent.log"


def clear_screen():
    """مسح الشاشة"""
    os.system('clear' if os.name == 'posix' else 'cls')


def parse_log():
    """استخراج آخر نشاط من الـ log"""
    if not os.path.exists(LOG_FILE):
        return None

    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()

        # آخر 200 سطر
        recent_lines = lines[-200:] if len(lines) > 200 else lines

        # استخراج البيانات
        data = {
            'last_cycle': None,
            'mode': None,
            'balance': None,
            'signals': [],
            'trades': [],
            'positions': 0,
            'last_update': None
        }

        for line in recent_lines:
            # Cycle
            if 'Trading Cycle' in line:
                try:
                    data['last_cycle'] = int(line.split('Cycle')[1].split('===')[0].strip())
                except:
                    pass

            # Mode
            if 'AutonomousTradingAgent initialized | Mode:' in line:
                try:
                    data['mode'] = line.split('Mode:')[1].strip()
                except:
                    pass

            # Balance
            if 'Futures Balance:' in line:
                try:
                    data['balance'] = line.split('$')[1].split()[0]
                except:
                    pass

            # Signals
            if '[Trap Signal]' in line:
                try:
                    parts = line.split('[Trap Signal]')[1].strip()
                    symbol = parts.split(':')[0].strip()
                    signal_type = parts.split(':')[1].split('@')[0].strip()
                    data['signals'].append(f"{symbol} {signal_type}")
                except:
                    pass

            # Brain decisions
            if '[Brain Decision]' in line:
                try:
                    parts = line.split('[Brain Decision]')[1].strip()
                    symbol = parts.split(':')[0].strip()
                    decision = parts.split(':')[1].split('|')[0].strip()
                    confidence = parts.split('Confidence:')[1].strip().replace('%', '')
                    data['signals'].append(f"  → Brain: {decision} ({confidence}%)")
                except:
                    pass

            # Paper trades
            if 'Paper Position Opened:' in line:
                try:
                    parts = line.split('Opened:')[1].strip()
                    data['trades'].append(parts)
                    data['positions'] += 1
                except:
                    pass

            # Last update
            if line.strip():
                try:
                    timestamp = line.split('|')[0].strip()
                    data['last_update'] = timestamp
                except:
                    pass

        return data

    except Exception as e:
        return {'error': str(e)}


def display_status():
    """عرض الحالة"""
    clear_screen()

    print("═" * 80)
    print("📊 AUTONOMOUS TRADING AGENT - LIVE MONITOR")
    print("═" * 80)

    data = parse_log()

    if not data:
        print("\n❌ No log data found")
        print(f"\nLog file: {LOG_FILE}")
        return

    if 'error' in data:
        print(f"\n❌ Error: {data['error']}")
        return

    # Status
    print(f"\n🟢 Status: {'RUNNING' if data['last_cycle'] else 'STOPPED'}")
    print(f"⏰ Last Update: {data['last_update'] or 'N/A'}")
    print(f"🔄 Cycle: #{data['last_cycle'] or 'N/A'}")
    print(f"📊 Mode: {data['mode'] or 'N/A'}")
    print(f"💰 Balance: ${data['balance'] or 'N/A'}")
    print(f"📈 Open Positions: {data['positions']}")

    # Recent signals
    if data['signals']:
        print(f"\n🎯 Recent Signals (last {min(5, len(data['signals']))}):")
        print("─" * 80)
        for signal in data['signals'][-5:]:
            print(f"   {signal}")
    else:
        print("\n🎯 No signals detected yet")

    # Recent trades
    if data['trades']:
        print(f"\n💼 Recent Trades:")
        print("─" * 80)
        for trade in data['trades'][-3:]:
            print(f"   {trade}")

    print("\n" + "═" * 80)
    print("Press Ctrl+C to exit")
    print("═" * 80)


def main():
    """Main loop"""
    try:
        while True:
            display_status()
            time.sleep(5)  # تحديث كل 5 ثواني

    except KeyboardInterrupt:
        clear_screen()
        print("\n✅ Monitor stopped\n")


if __name__ == "__main__":
    main()
