"""
State Reconciliation - مطابقة الحالة مع البورصة
==================================================

يحمي من:
- Ghost Positions (صفقات على البورصة لكن ليست في النظام)
- Missing Positions (صفقات في النظام لكن ليست على البورصة)
- State Desync (عدم تطابق الحالة)

المبدأ الأساسي:
البورصة = Source of Truth
النظام المحلي = Cache قابل للخطأ

Institution-Grade State Management
"""

from dataclasses import dataclass
from typing import List, Protocol, Optional, Dict
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════

@dataclass
class ExchangePosition:
    """صفقة على البورصة (الحقيقة)"""
    symbol: str
    side: str           # "LONG" | "SHORT"
    qty: float
    entry_price: float
    unrealized_pnl: float = 0.0
    leverage: int = 10


@dataclass
class LocalTrade:
    """صفقة محلية (في ذاكرة البوت)"""
    symbol: str
    side: str
    qty: float
    entry_price: float
    exchange_order_id: Optional[str] = None
    opened_at: float = 0.0


@dataclass
class ReconcileReport:
    """تقرير المطابقة"""
    ghosts_on_exchange: List[ExchangePosition]     # على البورصة لكن ليست محلياً
    missing_on_exchange: List[LocalTrade]          # محلياً لكن ليست على البورصة
    mismatched_qty: List[tuple[LocalTrade, ExchangePosition]]  # الكميات مختلفة

    @property
    def has_issues(self) -> bool:
        """هل توجد مشاكل في المطابقة؟"""
        return (
            len(self.ghosts_on_exchange) > 0
            or len(self.missing_on_exchange) > 0
            or len(self.mismatched_qty) > 0
        )

    def __str__(self) -> str:
        """تقرير نصي"""
        if not self.has_issues:
            return "✅ State reconciliation: All positions synced"

        lines = ["⚠️ State Reconciliation Issues:"]

        if self.ghosts_on_exchange:
            lines.append(f"\n🔴 Ghost Positions (on exchange, not local): {len(self.ghosts_on_exchange)}")
            for pos in self.ghosts_on_exchange:
                lines.append(f"  - {pos.symbol} {pos.side} {pos.qty}")

        if self.missing_on_exchange:
            lines.append(f"\n🟡 Missing Positions (local, not on exchange): {len(self.missing_on_exchange)}")
            for trade in self.missing_on_exchange:
                lines.append(f"  - {trade.symbol} {trade.side} {trade.qty}")

        if self.mismatched_qty:
            lines.append(f"\n🟠 Quantity Mismatches: {len(self.mismatched_qty)}")
            for local, exchange in self.mismatched_qty:
                lines.append(f"  - {local.symbol}: local={local.qty} vs exchange={exchange.qty}")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# Position Source Protocol
# ═══════════════════════════════════════════════════════

class PositionSource(Protocol):
    """واجهة مصدر الصفقات (البورصة)"""

    def fetch_positions(self) -> List[ExchangePosition]:
        """جلب جميع الصفقات المفتوحة من البورصة"""
        ...


# ═══════════════════════════════════════════════════════
# State Reconciler
# ═══════════════════════════════════════════════════════

class StateReconciler:
    """
    مطابق الحالة - يطابق بين الحالة المحلية والبورصة

    الاستخدام:
        >>> reconciler = StateReconciler(exchange_client)
        >>> report = reconciler.reconcile(local_trades)
        >>> if report.has_issues:
        ...     print(report)
        ...     reconciler.auto_fix(report, local_trades)

    المبدأ:
        البورصة هي المصدر الموثوق (Source of Truth)
        إذا اختلفت الحالة المحلية، نصحح المحلي ليطابق البورصة
    """

    def __init__(
        self,
        source: PositionSource,
        qty_tolerance: float = 0.001  # تحمل الفرق في الكمية (0.1%)
    ):
        """
        Args:
            source: مصدر الصفقات (البورصة)
            qty_tolerance: نسبة التحمل للفرق في الكمية (default: 0.1%)
        """
        self.source = source
        self.qty_tolerance = qty_tolerance

        logger.info(f"🔍 State Reconciler initialized (tolerance={qty_tolerance:.1%})")

    def reconcile(self, local_trades: List[LocalTrade]) -> ReconcileReport:
        """
        مطابقة الحالة المحلية مع البورصة

        Args:
            local_trades: قائمة الصفقات المحلية

        Returns:
            ReconcileReport: تقرير المطابقة
        """
        logger.debug("🔍 Starting state reconciliation...")

        # جلب الصفقات من البورصة
        try:
            exchange_positions = self.source.fetch_positions()
            logger.debug(f"📥 Fetched {len(exchange_positions)} positions from exchange")
        except Exception as e:
            logger.error(f"❌ Failed to fetch exchange positions: {e}")
            # نعيد تقرير فارغ في حالة فشل الجلب
            return ReconcileReport([], [], [])

        # بناء خرائط للمطابقة السريعة
        exchange_map: Dict[str, ExchangePosition] = {
            pos.symbol: pos
            for pos in exchange_positions
            if abs(pos.qty) > 0  # نتجاهل الصفقات المغلقة
        }

        local_map: Dict[str, LocalTrade] = {
            trade.symbol: trade
            for trade in local_trades
            if abs(trade.qty) > 0
        }

        ghosts = []
        missing = []
        mismatched = []

        # البحث عن Ghost Positions (على البورصة فقط)
        for symbol, ex_pos in exchange_map.items():
            if symbol not in local_map:
                logger.warning(f"👻 Ghost position detected: {symbol} {ex_pos.side} {ex_pos.qty}")
                ghosts.append(ex_pos)
            else:
                # التحقق من تطابق الكمية
                local_trade = local_map[symbol]
                qty_diff = abs(ex_pos.qty - local_trade.qty)
                qty_pct_diff = qty_diff / max(abs(ex_pos.qty), 1e-9)

                if qty_pct_diff > self.qty_tolerance:
                    logger.warning(
                        f"⚠️ Quantity mismatch: {symbol} "
                        f"local={local_trade.qty} vs exchange={ex_pos.qty} "
                        f"(diff={qty_pct_diff:.2%})"
                    )
                    mismatched.append((local_trade, ex_pos))

        # البحث عن Missing Positions (محلياً فقط)
        for symbol, local_trade in local_map.items():
            if symbol not in exchange_map:
                logger.warning(
                    f"🔍 Missing position on exchange: {symbol} {local_trade.side} {local_trade.qty}"
                )
                missing.append(local_trade)

        report = ReconcileReport(
            ghosts_on_exchange=ghosts,
            missing_on_exchange=missing,
            mismatched_qty=mismatched
        )

        if report.has_issues:
            logger.warning(f"\n{report}")
        else:
            logger.debug("✅ State reconciliation: All positions synced")

        return report

    def auto_fix(
        self,
        report: ReconcileReport,
        local_trades: List[LocalTrade]
    ) -> List[LocalTrade]:
        """
        إصلاح تلقائي للمشاكل المكتشفة

        استراتيجية الإصلاح:
        1. Ghost Positions → إنشاء LocalTrade جديد (emergency record)
        2. Missing Positions → إزالة LocalTrade (البورصة أغلقتها)
        3. Mismatched Qty → تحديث الكمية المحلية

        Args:
            report: تقرير المطابقة
            local_trades: القائمة المحلية (سيتم تعديلها)

        Returns:
            List[LocalTrade]: القائمة المعدلة
        """
        if not report.has_issues:
            return local_trades

        logger.warning("🔧 Auto-fixing state issues...")

        # إصلاح Ghost Positions (إضافة للمحلي)
        for ghost in report.ghosts_on_exchange:
            logger.warning(
                f"🆘 Creating emergency local record for ghost: "
                f"{ghost.symbol} {ghost.side} {ghost.qty}"
            )
            emergency_trade = LocalTrade(
                symbol=ghost.symbol,
                side=ghost.side,
                qty=ghost.qty,
                entry_price=ghost.entry_price,
                exchange_order_id=None,  # غير معروف
                opened_at=0.0  # غير معروف
            )
            local_trades.append(emergency_trade)

        # إصلاح Missing Positions (إزالة من المحلي)
        for missing in report.missing_on_exchange:
            logger.warning(
                f"🗑️ Removing missing position from local: "
                f"{missing.symbol} {missing.side} {missing.qty}"
            )
            if missing in local_trades:
                local_trades.remove(missing)

        # إصلاح Quantity Mismatches (تحديث الكمية)
        for local_trade, ex_pos in report.mismatched_qty:
            logger.warning(
                f"🔄 Updating quantity for {local_trade.symbol}: "
                f"{local_trade.qty} → {ex_pos.qty}"
            )
            local_trade.qty = ex_pos.qty

        logger.info(f"✅ Auto-fix completed: {len(local_trades)} local trades")
        return local_trades

    def get_status(self, local_trades: List[LocalTrade]) -> str:
        """
        الحصول على حالة المطابقة

        Returns:
            تقرير نصي
        """
        report = self.reconcile(local_trades)

        status = f"""
╔══════════════════════════════════════════════════════════╗
║            State Reconciliation Status                   ║
╠══════════════════════════════════════════════════════════╣
║  Ghost Positions:    {len(report.ghosts_on_exchange):>3d}                              ║
║  Missing Positions:  {len(report.missing_on_exchange):>3d}                              ║
║  Qty Mismatches:     {len(report.mismatched_qty):>3d}                              ║
║  Status:             {'⚠️ ISSUES' if report.has_issues else '✅ SYNCED':>10s}                     ║
╚══════════════════════════════════════════════════════════╝
"""
        return status
