"""
Circuit Breaker - نظام إيقاف التداول التلقائي
=============================================

يحمي النظام من:
- الخسائر اليومية الكبيرة
- التراجع الكبير (Max Drawdown)
- سلاسل الخسارة المتتالية
- معدل التداول المفرط

Institution-Grade Trading Safety Component
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingStats:
    """إحصائيات التداول الحالية"""
    equity_peak: float
    equity_now: float
    daily_pnl_ratio: float           # e.g. -0.08 means -8% today
    consecutive_losses: int
    trades_last_hour: int


@dataclass(frozen=True)
class BreakerState:
    """حالة Circuit Breaker"""
    halted: bool
    reason: Optional[str] = None


class CircuitBreaker:
    """
    Circuit Breaker - نظام إيقاف التداول التلقائي

    يوقف التداول عند:
    1. خسارة يومية > daily_loss_limit (مثال: -10%)
    2. تراجع من القمة > max_drawdown_limit (مثال: -20%)
    3. خسائر متتالية >= max_consecutive_losses (مثال: 5)
    4. عدد صفقات في الساعة > max_trades_per_hour (مثال: 20)

    Examples:
        >>> cb = CircuitBreaker(daily_loss_limit=-0.10, max_drawdown_limit=-0.20)
        >>> stats = TradingStats(equity_peak=1000, equity_now=850,
        ...                      daily_pnl_ratio=-0.12, consecutive_losses=3,
        ...                      trades_last_hour=5)
        >>> state = cb.check(stats)
        >>> if state.halted:
        ...     print(f"HALT: {state.reason}")
    """

    def __init__(
        self,
        daily_loss_limit: float = -0.10,      # -10% خسارة يومية
        max_drawdown_limit: float = -0.20,    # -20% تراجع من القمة
        max_consecutive_losses: int = 5,      # 5 خسائر متتالية
        max_trades_per_hour: int = 20,        # 20 صفقة/ساعة
    ):
        """
        Args:
            daily_loss_limit: الحد الأقصى للخسارة اليومية (سالب، مثال: -0.10 = -10%)
            max_drawdown_limit: الحد الأقصى للتراجع من القمة (سالب، مثال: -0.20 = -20%)
            max_consecutive_losses: عدد الخسائر المتتالية المسموح بها
            max_trades_per_hour: الحد الأقصى لعدد الصفقات في الساعة
        """
        self.daily_loss_limit = daily_loss_limit
        self.max_drawdown_limit = max_drawdown_limit
        self.max_consecutive_losses = max_consecutive_losses
        self.max_trades_per_hour = max_trades_per_hour

        logger.info(
            f"🚨 Circuit Breaker initialized: "
            f"daily_loss={daily_loss_limit:.0%}, "
            f"max_dd={max_drawdown_limit:.0%}, "
            f"max_losses={max_consecutive_losses}, "
            f"max_trades/h={max_trades_per_hour}"
        )

    def check(self, stats: TradingStats) -> BreakerState:
        """
        فحص ما إذا كان يجب إيقاف التداول

        Args:
            stats: إحصائيات التداول الحالية

        Returns:
            BreakerState: حالة Breaker (halted=True إذا يجب الإيقاف)
        """
        # 1. فحص الخسارة اليومية
        if stats.daily_pnl_ratio <= self.daily_loss_limit:
            reason = f"Daily loss limit hit: {stats.daily_pnl_ratio:.2%} <= {self.daily_loss_limit:.2%}"
            logger.critical(f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}")
            return BreakerState(True, reason)

        # 2. فحص التراجع من القمة (Max Drawdown)
        dd = 0.0
        if stats.equity_peak > 0:
            dd = (stats.equity_now - stats.equity_peak) / stats.equity_peak

        if dd <= self.max_drawdown_limit:
            reason = f"Max drawdown exceeded: {dd:.2%} <= {self.max_drawdown_limit:.2%}"
            logger.critical(f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}")
            return BreakerState(True, reason)

        # 3. فحص الخسائر المتتالية
        if stats.consecutive_losses >= self.max_consecutive_losses:
            reason = f"Too many consecutive losses: {stats.consecutive_losses} >= {self.max_consecutive_losses}"
            logger.critical(f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}")
            return BreakerState(True, reason)

        # 4. فحص معدل التداول
        if stats.trades_last_hour >= self.max_trades_per_hour:
            reason = f"Trade rate limit exceeded: {stats.trades_last_hour} >= {self.max_trades_per_hour}"
            logger.warning(f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}")
            return BreakerState(True, reason)

        # كل شيء طبيعي
        return BreakerState(False, None)

    def get_status(self, stats: TradingStats) -> str:
        """
        الحصول على حالة مفصلة للـ Circuit Breaker

        Returns:
            تقرير نصي عن الحالة الحالية
        """
        dd = 0.0
        if stats.equity_peak > 0:
            dd = (stats.equity_now - stats.equity_peak) / stats.equity_peak

        status = f"""
╔══════════════════════════════════════════════════════════╗
║               Circuit Breaker Status                     ║
╠══════════════════════════════════════════════════════════╣
║  Daily P&L:      {stats.daily_pnl_ratio:>7.2%} / {self.daily_loss_limit:.2%} limit   ║
║  Drawdown:       {dd:>7.2%} / {self.max_drawdown_limit:.2%} limit   ║
║  Consec Losses:  {stats.consecutive_losses:>7d} / {self.max_consecutive_losses:>2d} limit       ║
║  Trades/Hour:    {stats.trades_last_hour:>7d} / {self.max_trades_per_hour:>2d} limit       ║
╚══════════════════════════════════════════════════════════╝
"""
        return status
