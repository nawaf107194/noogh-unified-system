"""
Safety Components Unit Tests - اختبارات مكونات الأمان
======================================================

اختبارات شاملة لـ:
1. CircuitBreaker
2. PortfolioRiskManager
3. StateReconciler

Unit Tests for Institution-Grade Safety Components
"""

import pytest
from circuit_breaker import CircuitBreaker, TradingStats, BreakerState
from portfolio_risk_manager import PortfolioRiskManager, PositionSnapshot, RiskDecision
from state_reconciliation import StateReconciler, ExchangePosition, LocalTrade, ReconcileReport


# ═══════════════════════════════════════════════════════
# Circuit Breaker Tests
# ═══════════════════════════════════════════════════════

class TestCircuitBreaker:
    """اختبارات Circuit Breaker"""

    def test_daily_loss_limit_triggers_halt(self):
        """اختبار: الخسارة اليومية تُوقف التداول"""
        cb = CircuitBreaker(daily_loss_limit=-0.10)  # -10%

        stats = TradingStats(
            equity_peak=1000,
            equity_now=950,
            daily_pnl_ratio=-0.12,  # -12% (أكثر من الحد)
            consecutive_losses=0,
            trades_last_hour=0
        )

        result = cb.check(stats)

        assert result.halted is True
        assert "Daily loss" in result.reason

    def test_no_halt_when_within_limits(self):
        """اختبار: لا إيقاف عندما كل شيء طبيعي"""
        cb = CircuitBreaker(
            daily_loss_limit=-0.10,
            max_drawdown_limit=-0.20,
            max_consecutive_losses=5
        )

        stats = TradingStats(
            equity_peak=1000,
            equity_now=980,        # -2% من القمة
            daily_pnl_ratio=-0.05, # -5% اليوم
            consecutive_losses=2,
            trades_last_hour=3
        )

        result = cb.check(stats)

        assert result.halted is False
        assert result.reason is None

    def test_max_drawdown_triggers_halt(self):
        """اختبار: التراجع الكبير يُوقف التداول"""
        cb = CircuitBreaker(max_drawdown_limit=-0.20)  # -20%

        stats = TradingStats(
            equity_peak=1000,
            equity_now=750,        # -25% من القمة
            daily_pnl_ratio=0.0,
            consecutive_losses=0,
            trades_last_hour=0
        )

        result = cb.check(stats)

        assert result.halted is True
        assert "drawdown" in result.reason.lower()

    def test_consecutive_losses_trigger_halt(self):
        """اختبار: الخسائر المتتالية تُوقف التداول"""
        cb = CircuitBreaker(max_consecutive_losses=5)

        stats = TradingStats(
            equity_peak=1000,
            equity_now=950,
            daily_pnl_ratio=-0.05,
            consecutive_losses=5,  # بالضبط الحد
            trades_last_hour=0
        )

        result = cb.check(stats)

        assert result.halted is True
        assert "consecutive" in result.reason.lower()

    def test_trade_rate_limit_triggers_halt(self):
        """اختبار: معدل التداول المرتفع يُوقف التداول"""
        cb = CircuitBreaker(max_trades_per_hour=20)

        stats = TradingStats(
            equity_peak=1000,
            equity_now=1000,
            daily_pnl_ratio=0.0,
            consecutive_losses=0,
            trades_last_hour=20  # بالضبط الحد
        )

        result = cb.check(stats)

        assert result.halted is True
        assert "rate" in result.reason.lower()


# ═══════════════════════════════════════════════════════
# Portfolio Risk Manager Tests
# ═══════════════════════════════════════════════════════

class TestPortfolioRiskManager:
    """اختبارات Portfolio Risk Manager"""

    def test_total_exposure_adjustment(self):
        """اختبار: تعديل الحجم عند تجاوز التعرض الكلي"""
        rm = PortfolioRiskManager(max_total_exposure=0.30)  # 30%

        equity = 1000.0
        positions = [
            PositionSnapshot("BTCUSDT", 250.0, "LONG")  # 25% تعرض حالي
        ]

        # طلب 200$ إضافية → يصبح 45% (فوق الحد 30%)
        decision = rm.can_open(
            equity_usdt=equity,
            positions=positions,
            new_symbol="ETHUSDT",
            requested_size_usdt=200.0
        )

        assert decision.allowed is True
        # يجب تعديل الحجم: 30% * 1000 - 250 = 50
        assert decision.adjusted_size_usdt == pytest.approx(50.0, abs=0.1)
        assert "portfolio" in decision.reason.lower()

    def test_symbol_exposure_limit(self):
        """اختبار: منع التركيز على رمز واحد"""
        rm = PortfolioRiskManager(max_symbol_exposure=0.10)  # 10% لكل رمز

        equity = 1000.0
        positions = [
            PositionSnapshot("BTCUSDT", 80.0, "LONG")  # 8% BTC حالياً
        ]

        # طلب 50$ إضافية لـ BTC → يصبح 13% (فوق الحد 10%)
        decision = rm.can_open(
            equity_usdt=equity,
            positions=positions,
            new_symbol="BTCUSDT",
            requested_size_usdt=50.0
        )

        assert decision.allowed is True
        # يجب تعديل: 10% * 1000 - 80 = 20
        assert decision.adjusted_size_usdt == pytest.approx(20.0, abs=0.1)

    def test_max_open_trades_limit(self):
        """اختبار: الحد الأقصى للصفقات المفتوحة"""
        rm = PortfolioRiskManager(max_open_trades=3)

        equity = 1000.0
        positions = [
            PositionSnapshot("BTCUSDT", 50.0, "LONG"),
            PositionSnapshot("ETHUSDT", 50.0, "LONG"),
            PositionSnapshot("SOLUSDT", 50.0, "LONG"),  # 3 صفقات
        ]

        # محاولة فتح الرابعة
        decision = rm.can_open(
            equity_usdt=equity,
            positions=positions,
            new_symbol="BNBUSDT",
            requested_size_usdt=50.0
        )

        assert decision.allowed is False
        assert "max" in decision.reason.lower()

    def test_correlation_risk_rejection(self):
        """اختبار: منع التعرض للأصول المترابطة"""
        rm = PortfolioRiskManager(
            max_correlated_exposure=0.15,  # 15%
            corr_threshold=0.70
        )

        # تعيين correlation matrix
        rm.set_correlation_matrix({
            "BTCUSDT": {"ETHUSDT": 0.85, "SOLUSDT": 0.75},
            "ETHUSDT": {"BTCUSDT": 0.85, "SOLUSDT": 0.80},
            "SOLUSDT": {"BTCUSDT": 0.75, "ETHUSDT": 0.80},
        })

        equity = 1000.0
        positions = [
            PositionSnapshot("BTCUSDT", 100.0, "LONG"),  # 10%
            PositionSnapshot("ETHUSDT", 50.0, "LONG"),   # 5%
            # Total correlated with SOL: 15%
        ]

        # محاولة فتح SOL (مترابط مع BTC و ETH)
        # 15% موجود + 5% جديد = 20% > 15% limit
        decision = rm.can_open(
            equity_usdt=equity,
            positions=positions,
            new_symbol="SOLUSDT",
            requested_size_usdt=50.0
        )

        assert decision.allowed is False
        assert "correlated" in decision.reason.lower()

    def test_allows_uncorrelated_asset(self):
        """اختبار: السماح بأصل غير مترابط"""
        rm = PortfolioRiskManager(max_correlated_exposure=0.15)

        rm.set_correlation_matrix({
            "BTCUSDT": {"GOLD": 0.1},  # ارتباط منخفض
        })

        equity = 1000.0
        positions = [
            PositionSnapshot("BTCUSDT", 100.0, "LONG")
        ]

        decision = rm.can_open(
            equity_usdt=equity,
            positions=positions,
            new_symbol="GOLD",  # غير مترابط
            requested_size_usdt=50.0
        )

        assert decision.allowed is True

    def test_zero_size_rejected(self):
        """اختبار: رفض حجم صفر أو سالب"""
        rm = PortfolioRiskManager()

        decision = rm.can_open(
            equity_usdt=1000.0,
            positions=[],
            new_symbol="BTCUSDT",
            requested_size_usdt=0.0
        )

        assert decision.allowed is False


# ═══════════════════════════════════════════════════════
# State Reconciliation Tests
# ═══════════════════════════════════════════════════════

class DummyExchangeSource:
    """محاكي بورصة للاختبار"""

    def __init__(self, positions: list[ExchangePosition]):
        self.positions = positions

    def fetch_positions(self) -> list[ExchangePosition]:
        return self.positions


class TestStateReconciliation:
    """اختبارات State Reconciliation"""

    def test_detects_ghost_positions(self):
        """اختبار: اكتشاف صفقات على البورصة فقط"""
        # البورصة لديها صفقة BTCUSDT
        source = DummyExchangeSource([
            ExchangePosition("BTCUSDT", "LONG", 1.0, 50000.0)
        ])

        reconciler = StateReconciler(source)

        # المحلي فارغ
        local_trades = []

        report = reconciler.reconcile(local_trades)

        assert report.has_issues is True
        assert len(report.ghosts_on_exchange) == 1
        assert report.ghosts_on_exchange[0].symbol == "BTCUSDT"
        assert len(report.missing_on_exchange) == 0

    def test_detects_missing_positions(self):
        """اختبار: اكتشاف صفقات محلية فقط"""
        # البورصة فارغة
        source = DummyExchangeSource([])

        reconciler = StateReconciler(source)

        # المحلي لديه صفقة
        local_trades = [
            LocalTrade("ETHUSDT", "LONG", 1.0, 3000.0, "order_123")
        ]

        report = reconciler.reconcile(local_trades)

        assert report.has_issues is True
        assert len(report.ghosts_on_exchange) == 0
        assert len(report.missing_on_exchange) == 1
        assert report.missing_on_exchange[0].symbol == "ETHUSDT"

    def test_detects_quantity_mismatch(self):
        """اختبار: اكتشاف عدم تطابق الكميات"""
        source = DummyExchangeSource([
            ExchangePosition("BTCUSDT", "LONG", 1.5, 50000.0)  # البورصة: 1.5
        ])

        reconciler = StateReconciler(source, qty_tolerance=0.01)  # 1% tolerance

        local_trades = [
            LocalTrade("BTCUSDT", "LONG", 1.0, 50000.0)  # المحلي: 1.0
        ]

        report = reconciler.reconcile(local_trades)

        assert report.has_issues is True
        assert len(report.mismatched_qty) == 1
        local, exchange = report.mismatched_qty[0]
        assert local.qty == 1.0
        assert exchange.qty == 1.5

    def test_no_issues_when_synced(self):
        """اختبار: لا مشاكل عندما كل شيء متطابق"""
        source = DummyExchangeSource([
            ExchangePosition("BTCUSDT", "LONG", 1.0, 50000.0),
            ExchangePosition("ETHUSDT", "SHORT", 2.0, 3000.0),
        ])

        reconciler = StateReconciler(source)

        local_trades = [
            LocalTrade("BTCUSDT", "LONG", 1.0, 50000.0),
            LocalTrade("ETHUSDT", "SHORT", 2.0, 3000.0),
        ]

        report = reconciler.reconcile(local_trades)

        assert report.has_issues is False
        assert len(report.ghosts_on_exchange) == 0
        assert len(report.missing_on_exchange) == 0
        assert len(report.mismatched_qty) == 0

    def test_auto_fix_adds_ghost_positions(self):
        """اختبار: الإصلاح التلقائي يضيف ghost positions"""
        source = DummyExchangeSource([
            ExchangePosition("BTCUSDT", "LONG", 1.0, 50000.0)
        ])

        reconciler = StateReconciler(source)
        local_trades = []

        report = reconciler.reconcile(local_trades)
        assert len(report.ghosts_on_exchange) == 1

        # إصلاح تلقائي
        fixed_trades = reconciler.auto_fix(report, local_trades)

        assert len(fixed_trades) == 1
        assert fixed_trades[0].symbol == "BTCUSDT"
        assert fixed_trades[0].qty == 1.0

    def test_auto_fix_removes_missing_positions(self):
        """اختبار: الإصلاح التلقائي يحذف missing positions"""
        source = DummyExchangeSource([])  # البورصة فارغة

        reconciler = StateReconciler(source)

        local_trades = [
            LocalTrade("ETHUSDT", "LONG", 1.0, 3000.0)
        ]

        report = reconciler.reconcile(local_trades)
        assert len(report.missing_on_exchange) == 1

        # إصلاح تلقائي
        fixed_trades = reconciler.auto_fix(report, local_trades)

        assert len(fixed_trades) == 0  # تم الحذف

    def test_auto_fix_updates_quantity(self):
        """اختبار: الإصلاح التلقائي يعدل الكميات"""
        source = DummyExchangeSource([
            ExchangePosition("BTCUSDT", "LONG", 2.0, 50000.0)
        ])

        reconciler = StateReconciler(source, qty_tolerance=0.01)

        local_trades = [
            LocalTrade("BTCUSDT", "LONG", 1.0, 50000.0)
        ]

        report = reconciler.reconcile(local_trades)
        assert len(report.mismatched_qty) == 1

        # إصلاح تلقائي
        fixed_trades = reconciler.auto_fix(report, local_trades)

        assert len(fixed_trades) == 1
        assert fixed_trades[0].qty == 2.0  # تم التحديث من البورصة


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
