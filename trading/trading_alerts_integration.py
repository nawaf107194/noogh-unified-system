"""
Trading Alerts Integration - دمج التنبيهات في التداول
=======================================================

Example integration of FailureAlertSystem with the trading system.
Shows how to alert on various trading failure scenarios.

Usage:
    from trading.trading_alerts_integration import setup_trading_alerts
    setup_trading_alerts(trap_trader_instance)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Optional
from unified_core.observability.failure_alert_system import (
    get_failure_alert_system,
    FailureSeverity,
    FailureCategory
)

logger = logging.getLogger(__name__)


def setup_trading_alerts(trader: Optional[object] = None):
    """
    إعداد تنبيهات التداول
    Setup trading-specific failure alerts

    Args:
        trader: TrapLiveTrader instance (optional)
    """
    alert_system = get_failure_alert_system()

    logger.info("Setting up trading alert integrations...")

    # Example alert scenarios for trading
    examples = {
        "large_loss": {
            "severity": FailureSeverity.CRITICAL,
            "category": FailureCategory.TRADING,
            "title": "Large Trading Loss Detected",
            "message": "Position closed with significant loss",
            "suggested_action": "Review trading strategy and risk parameters"
        },
        "api_failure": {
            "severity": FailureSeverity.HIGH,
            "category": FailureCategory.NETWORK,
            "title": "Exchange API Failure",
            "message": "Unable to connect to exchange API",
            "suggested_action": "Check API credentials and network connectivity"
        },
        "risk_breach": {
            "severity": FailureSeverity.CRITICAL,
            "category": FailureCategory.TRADING,
            "title": "Risk Limit Breached",
            "message": "Position size exceeds risk limits",
            "suggested_action": "Close positions and reduce exposure"
        },
        "margin_call": {
            "severity": FailureSeverity.CATASTROPHIC,
            "category": FailureCategory.TRADING,
            "title": "Margin Call Risk",
            "message": "Account balance approaching liquidation threshold",
            "suggested_action": "Close positions immediately and add funds"
        }
    }

    logger.info(f"Registered {len(examples)} trading alert scenarios")

    return alert_system, examples


# Alert helper functions for common trading scenarios

def alert_large_loss(symbol: str, pnl: float, pnl_percent: float):
    """Alert on large trading loss."""
    alert_system = get_failure_alert_system()

    # Determine severity based on loss magnitude
    if abs(pnl_percent) > 10:
        severity = FailureSeverity.CATASTROPHIC
    elif abs(pnl_percent) > 7:
        severity = FailureSeverity.CRITICAL
    elif abs(pnl_percent) > 5:
        severity = FailureSeverity.HIGH
    else:
        severity = FailureSeverity.MEDIUM

    alert_system.alert(
        severity=severity,
        category=FailureCategory.TRADING,
        title=f"Large Loss: {symbol}",
        message=f"Position closed with {pnl_percent:.2f}% loss (${abs(pnl):.2f})",
        details={
            "symbol": symbol,
            "pnl_usd": pnl,
            "pnl_percent": pnl_percent
        },
        source="trading_system",
        suggested_action="Review trade entry logic and risk management"
    )


def alert_api_error(exchange: str, error_message: str, operation: str):
    """Alert on exchange API errors."""
    alert_system = get_failure_alert_system()

    alert_system.alert(
        severity=FailureSeverity.HIGH,
        category=FailureCategory.NETWORK,
        title=f"API Error: {exchange}",
        message=f"Failed to {operation}: {error_message}",
        details={
            "exchange": exchange,
            "operation": operation,
            "error": error_message
        },
        source="trading_api",
        suggested_action="Check API status and retry operation"
    )


def alert_risk_breach(symbol: str, position_size: float, max_allowed: float):
    """Alert on risk limit breach."""
    alert_system = get_failure_alert_system()

    alert_system.alert(
        severity=FailureSeverity.CRITICAL,
        category=FailureCategory.TRADING,
        title="Risk Limit Exceeded",
        message=f"{symbol} position ${position_size:.2f} exceeds limit ${max_allowed:.2f}",
        details={
            "symbol": symbol,
            "position_size": position_size,
            "max_allowed": max_allowed,
            "excess": position_size - max_allowed
        },
        source="risk_manager",
        suggested_action="Reduce position size immediately"
    )


def alert_unusual_market_activity(symbol: str, metric: str, value: float, threshold: float):
    """Alert on unusual market conditions."""
    alert_system = get_failure_alert_system()

    alert_system.alert(
        severity=FailureSeverity.MEDIUM,
        category=FailureCategory.TRADING,
        title=f"Unusual Market Activity: {symbol}",
        message=f"{metric} at {value:.2f} (threshold: {threshold:.2f})",
        details={
            "symbol": symbol,
            "metric": metric,
            "value": value,
            "threshold": threshold
        },
        source="market_monitor",
        suggested_action="Monitor closely for potential regime change"
    )


def alert_low_liquidity(symbol: str, volume_24h: float, avg_volume: float):
    """Alert on low liquidity conditions."""
    alert_system = get_failure_alert_system()

    alert_system.alert(
        severity=FailureSeverity.MEDIUM,
        category=FailureCategory.TRADING,
        title=f"Low Liquidity: {symbol}",
        message=f"24h volume ${volume_24h:.2f} is {((avg_volume - volume_24h) / avg_volume * 100):.1f}% below average",
        details={
            "symbol": symbol,
            "volume_24h": volume_24h,
            "avg_volume": avg_volume
        },
        source="liquidity_monitor",
        suggested_action="Avoid large orders or use limit orders only"
    )


def alert_strategy_underperformance(strategy_name: str, win_rate: float, recent_trades: int):
    """Alert on strategy underperformance."""
    alert_system = get_failure_alert_system()

    severity = FailureSeverity.HIGH if win_rate < 0.3 else FailureSeverity.MEDIUM

    alert_system.alert(
        severity=severity,
        category=FailureCategory.TRADING,
        title=f"Strategy Underperformance: {strategy_name}",
        message=f"Win rate {win_rate*100:.1f}% over last {recent_trades} trades",
        details={
            "strategy": strategy_name,
            "win_rate": win_rate,
            "recent_trades": recent_trades
        },
        source="performance_monitor",
        suggested_action="Review strategy parameters or pause trading"
    )


def alert_connection_lost(exchange: str, duration_seconds: float):
    """Alert on prolonged connection loss."""
    alert_system = get_failure_alert_system()

    severity = FailureSeverity.CRITICAL if duration_seconds > 300 else FailureSeverity.HIGH

    alert_system.alert(
        severity=severity,
        category=FailureCategory.NETWORK,
        title=f"Connection Lost: {exchange}",
        message=f"No connection for {duration_seconds:.0f} seconds",
        details={
            "exchange": exchange,
            "duration": duration_seconds
        },
        source="connection_monitor",
        suggested_action="Check network and exchange status, manage open positions manually"
    )


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Trading Alerts Integration - Example Usage")
    print("=" * 60)

    # Setup
    alert_system, scenarios = setup_trading_alerts()

    # Simulate various alert scenarios
    print("\n1. Large Loss Alert...")
    alert_large_loss("BTCUSDT", pnl=-850.50, pnl_percent=-8.5)

    print("\n2. API Error Alert...")
    alert_api_error("Binance", "Rate limit exceeded", "place_order")

    print("\n3. Risk Breach Alert...")
    alert_risk_breach("ETHUSDT", position_size=5500, max_allowed=5000)

    print("\n4. Unusual Market Activity...")
    alert_unusual_market_activity("BTCUSDT", "volatility", 0.15, 0.08)

    print("\n5. Low Liquidity Alert...")
    alert_low_liquidity("ALTCOIN", volume_24h=50000, avg_volume=200000)

    print("\n6. Strategy Underperformance...")
    alert_strategy_underperformance("TrendFollower", win_rate=0.25, recent_trades=20)

    print("\n7. Connection Lost...")
    alert_connection_lost("Binance", duration_seconds=180)

    # Show statistics
    print("\n" + "=" * 60)
    stats = alert_system.get_statistics()
    print(f"Total alerts created: {stats['total_alerts']}")
    print(f"By severity: {stats['by_severity']}")
    print(f"By category: {stats['by_category']}")
    print("=" * 60)
