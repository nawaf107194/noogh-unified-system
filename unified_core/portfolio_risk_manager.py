"""
Portfolio Risk Manager - إدارة مخاطر المحفظة
============================================

يحمي من:
- التعرض الكلي المفرط (Total Portfolio Exposure)
- التركيز على رمز واحد (Symbol Concentration)
- التعرض للأصول المترابطة (Correlated Assets)
- عدد الصفقات المتزامنة المفرط

المبدأ:
Kelly Criterion يحسب حجم الصفقة الواحدة
Portfolio Risk Manager يضمن أن المحفظة ككل آمنة

Institution-Grade Portfolio Management
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════

@dataclass(frozen=True)
class RiskDecision:
    """قرار المخاطرة - هل يُسمح بفتح الصفقة؟"""
    allowed: bool
    reason: str
    adjusted_size_usdt: Optional[float] = None


@dataclass
class PositionSnapshot:
    """لقطة من صفقة مفتوحة"""
    symbol: str
    notional_usdt: float  # القيمة المطلقة للتعرض
    side: str             # "LONG" | "SHORT"


# ═══════════════════════════════════════════════════════
# Portfolio Risk Manager
# ═══════════════════════════════════════════════════════

class PortfolioRiskManager:
    """
    مدير مخاطر المحفظة - يضمن سلامة المحفظة ككل

    القواعد:
    1. max_total_exposure: الحد الأقصى للتعرض الكلي (مثال: 30% من الرصيد)
    2. max_symbol_exposure: الحد الأقصى لرمز واحد (مثال: 10% من الرصيد)
    3. max_correlated_exposure: الحد الأقصى للأصول المترابطة (مثال: 15%)
    4. max_open_trades: الحد الأقصى لعدد الصفقات المتزامنة (مثال: 5)

    Examples:
        >>> rm = PortfolioRiskManager(max_total_exposure=0.30,
        ...                           max_symbol_exposure=0.10)
        >>> positions = [PositionSnapshot("BTCUSDT", 250.0, "LONG")]
        >>> decision = rm.can_open(equity_usdt=1000.0,
        ...                        positions=positions,
        ...                        new_symbol="ETHUSDT",
        ...                        requested_size_usdt=100.0)
        >>> if decision.allowed:
        ...     print(f"Approved: {decision.adjusted_size_usdt}")
    """

    def __init__(
        self,
        max_total_exposure: float = 0.30,       # 30% من الرصيد
        max_symbol_exposure: float = 0.10,      # 10% لكل رمز
        max_correlated_exposure: float = 0.15,  # 15% للأصول المترابطة
        corr_threshold: float = 0.70,           # حد الارتباط (70%)
        max_open_trades: int = 5,               # 5 صفقات متزامنة كحد أقصى
    ):
        """
        Args:
            max_total_exposure: الحد الأقصى للتعرض الكلي (نسبة من الرصيد)
            max_symbol_exposure: الحد الأقصى لرمز واحد (نسبة من الرصيد)
            max_correlated_exposure: الحد الأقصى للأصول المترابطة
            corr_threshold: حد الارتباط (مثال: 0.70 = 70%)
            max_open_trades: الحد الأقصى لعدد الصفقات المفتوحة
        """
        self.max_total_exposure = max_total_exposure
        self.max_symbol_exposure = max_symbol_exposure
        self.max_correlated_exposure = max_correlated_exposure
        self.corr_threshold = corr_threshold
        self.max_open_trades = max_open_trades

        # مصفوفة الارتباط: corr[symbol_a][symbol_b] = 0..1
        self.corr: Dict[str, Dict[str, float]] = {}

        logger.info(
            f"📊 Portfolio Risk Manager initialized: "
            f"total={max_total_exposure:.0%}, "
            f"symbol={max_symbol_exposure:.0%}, "
            f"corr={max_correlated_exposure:.0%}, "
            f"max_trades={max_open_trades}"
        )

    def set_correlation_matrix(self, corr: Dict[str, Dict[str, float]]) -> None:
        """
        تعيين مصفوفة الارتباط

        Args:
            corr: مصفوفة الارتباط {symbol_a: {symbol_b: correlation}}

        Example:
            >>> corr = {
            ...     "BTCUSDT": {"ETHUSDT": 0.85, "SOLUSDT": 0.75},
            ...     "ETHUSDT": {"BTCUSDT": 0.85, "SOLUSDT": 0.80},
            ... }
            >>> rm.set_correlation_matrix(corr)
        """
        self.corr = corr
        logger.info(f"📈 Correlation matrix updated: {len(corr)} symbols")

    def _get_corr(self, symbol_a: str, symbol_b: str) -> float:
        """الحصول على معامل الارتباط بين رمزين"""
        if symbol_a == symbol_b:
            return 1.0

        # البحث في كلا الاتجاهين
        corr_ab = self.corr.get(symbol_a, {}).get(symbol_b)
        if corr_ab is not None:
            return float(corr_ab)

        corr_ba = self.corr.get(symbol_b, {}).get(symbol_a)
        if corr_ba is not None:
            return float(corr_ba)

        # افتراضي: لا ارتباط
        return 0.0

    def total_exposure_ratio(
        self,
        equity_usdt: float,
        positions: List[PositionSnapshot]
    ) -> float:
        """
        حساب نسبة التعرض الكلي

        Returns:
            نسبة التعرض (0.0 - 1.0+)
        """
        if equity_usdt <= 0:
            return 0.0

        total_notional = sum(abs(p.notional_usdt) for p in positions)
        return total_notional / equity_usdt

    def symbol_exposure_ratio(
        self,
        equity_usdt: float,
        positions: List[PositionSnapshot],
        symbol: str
    ) -> float:
        """
        حساب نسبة التعرض لرمز معين

        Returns:
            نسبة التعرض (0.0 - 1.0+)
        """
        if equity_usdt <= 0:
            return 0.0

        symbol_notional = sum(
            abs(p.notional_usdt)
            for p in positions
            if p.symbol == symbol
        )
        return symbol_notional / equity_usdt

    def correlated_exposure_ratio(
        self,
        equity_usdt: float,
        positions: List[PositionSnapshot],
        new_symbol: str,
    ) -> float:
        """
        حساب التعرض للأصول المترابطة مع الرمز الجديد

        Returns:
            نسبة التعرض المترابط (0.0 - 1.0+)
        """
        if equity_usdt <= 0:
            return 0.0

        correlated_notional = sum(
            abs(p.notional_usdt)
            for p in positions
            if self._get_corr(p.symbol, new_symbol) >= self.corr_threshold
        )

        return correlated_notional / equity_usdt

    def can_open(
        self,
        equity_usdt: float,
        positions: List[PositionSnapshot],
        new_symbol: str,
        requested_size_usdt: float,
    ) -> RiskDecision:
        """
        هل يُسمح بفتح صفقة جديدة؟

        Args:
            equity_usdt: الرصيد الحالي
            positions: الصفقات المفتوحة حالياً
            new_symbol: الرمز الجديد
            requested_size_usdt: الحجم المطلوب بالدولار

        Returns:
            RiskDecision: القرار (allowed + السبب + الحجم المعدل)
        """
        if requested_size_usdt <= 0:
            return RiskDecision(
                False,
                "Requested size <= 0",
                adjusted_size_usdt=0.0
            )

        # 1. فحص عدد الصفقات المفتوحة
        if len(positions) >= self.max_open_trades:
            logger.warning(
                f"🛑 Max open trades reached: "
                f"{len(positions)}/{self.max_open_trades}"
            )
            return RiskDecision(
                False,
                f"Max open trades reached ({self.max_open_trades})"
            )

        # 2. فحص التعرض الكلي
        current_total = sum(abs(p.notional_usdt) for p in positions)
        new_total = current_total + abs(requested_size_usdt)
        total_ratio = new_total / max(equity_usdt, 1e-9)

        if total_ratio > self.max_total_exposure:
            # محاولة تعديل الحجم
            max_allowed = max(
                self.max_total_exposure * equity_usdt - current_total,
                0.0
            )

            if max_allowed <= 0:
                logger.warning(
                    f"🛑 Portfolio exposure limit: "
                    f"{total_ratio:.1%} > {self.max_total_exposure:.1%}"
                )
                return RiskDecision(
                    False,
                    "Portfolio exposure limit",
                    adjusted_size_usdt=0.0
                )

            # تعديل الحجم ليناسب الحد
            logger.info(
                f"📉 Adjusting size for portfolio limit: "
                f"${requested_size_usdt:.2f} → ${max_allowed:.2f}"
            )
            return RiskDecision(
                True,
                "Adjusted to portfolio exposure limit",
                adjusted_size_usdt=max_allowed
            )

        # 3. فحص التعرض للرمز الواحد
        current_symbol = sum(
            abs(p.notional_usdt)
            for p in positions
            if p.symbol == new_symbol
        )
        new_symbol_total = current_symbol + abs(requested_size_usdt)
        symbol_ratio = new_symbol_total / max(equity_usdt, 1e-9)

        if symbol_ratio > self.max_symbol_exposure:
            # محاولة تعديل الحجم
            max_allowed = max(
                self.max_symbol_exposure * equity_usdt - current_symbol,
                0.0
            )

            if max_allowed <= 0:
                logger.warning(
                    f"🛑 Symbol exposure limit for {new_symbol}: "
                    f"{symbol_ratio:.1%} > {self.max_symbol_exposure:.1%}"
                )
                return RiskDecision(
                    False,
                    f"Symbol exposure limit ({new_symbol})",
                    adjusted_size_usdt=0.0
                )

            logger.info(
                f"📉 Adjusting size for {new_symbol} limit: "
                f"${requested_size_usdt:.2f} → ${max_allowed:.2f}"
            )
            return RiskDecision(
                True,
                f"Adjusted to symbol exposure limit ({new_symbol})",
                adjusted_size_usdt=max_allowed
            )

        # 4. فحص الارتباط
        corr_exposure = self.correlated_exposure_ratio(
            equity_usdt, positions, new_symbol
        )
        new_corr_exposure = (corr_exposure * equity_usdt + abs(requested_size_usdt)) / equity_usdt

        if new_corr_exposure > self.max_correlated_exposure:
            logger.warning(
                f"🛑 Correlated exposure too high for {new_symbol}: "
                f"{new_corr_exposure:.1%} > {self.max_correlated_exposure:.1%}"
            )
            return RiskDecision(
                False,
                "Correlated exposure too high"
            )

        # ✅ كل الفحوصات نجحت
        logger.debug(
            f"✅ Risk check passed: {new_symbol} "
            f"(total={total_ratio:.1%}, symbol={symbol_ratio:.1%}, "
            f"corr={new_corr_exposure:.1%})"
        )
        return RiskDecision(
            True,
            "OK",
            adjusted_size_usdt=requested_size_usdt
        )

    def get_status(
        self,
        equity_usdt: float,
        positions: List[PositionSnapshot]
    ) -> str:
        """
        الحصول على حالة المحفظة

        Returns:
            تقرير نصي
        """
        total_ratio = self.total_exposure_ratio(equity_usdt, positions)
        total_notional = sum(abs(p.notional_usdt) for p in positions)

        # حساب التعرض لكل رمز
        symbol_exposures = {}
        for pos in positions:
            symbol_exposures[pos.symbol] = symbol_exposures.get(pos.symbol, 0) + abs(pos.notional_usdt)

        status_lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║         Portfolio Risk Manager Status                   ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║  Equity:           ${equity_usdt:>10,.2f}                      ║",
            f"║  Total Exposure:   ${total_notional:>10,.2f} ({total_ratio:>5.1%})              ║",
            f"║  Max Allowed:      {self.max_total_exposure:>5.0%}                              ║",
            f"║  Open Trades:      {len(positions):>3d} / {self.max_open_trades:<2d}                            ║",
            "╠══════════════════════════════════════════════════════════╣",
        ]

        if symbol_exposures:
            status_lines.append("║  Symbol Exposures:                                       ║")
            for symbol, notional in sorted(symbol_exposures.items(), key=lambda x: x[1], reverse=True):
                ratio = notional / equity_usdt if equity_usdt > 0 else 0
                status_lines.append(f"║    {symbol:<12s} ${notional:>8,.2f} ({ratio:>5.1%})                ║")

        status_lines.append("╚══════════════════════════════════════════════════════════╝")

        return "\n".join(status_lines)
