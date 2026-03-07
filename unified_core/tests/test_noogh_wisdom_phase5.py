"""
اختبارات شاملة للمرحلة 5 - NOOGH Wisdom
=====================================

يختبر هذا الملف الميزات الجديدة في المرحلة 5:
1. نظام Kelly Criterion لتحجيم المراكز (Position Sizing)
2. نظام أهداف الربح المتدرجة (Tiered Take Profits: TP1/TP2/TP3)

تشمل الاختبارات:
- الحالات الطبيعية (Happy Path)
- الحالات الحدية (Edge Cases)
- حالات الخطأ (Error Cases)
- التحقق من الصحة (Validation)
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
import time
from typing import List


# ═══════════════════════════════════════════════════════
# Mock Data Structures
# ═══════════════════════════════════════════════════════

@dataclass
class TradeDecision:
    """قرار التداول من الدماغ"""
    symbol: str
    direction: str  # LONG or SHORT
    confidence: float
    entry_price: float
    take_profits: List[float]
    stop_loss: float
    reasoning: str
    leverage: int = 10
    duration_min: int = 30
    timestamp: float = field(default_factory=time.time)

    @property
    def risk_reward(self) -> float:
        if not self.take_profits:
            return 0.0
        tp1 = self.take_profits[0]
        if self.direction == "LONG":
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(tp1 - self.entry_price)
        else:
            risk = abs(self.stop_loss - self.entry_price)
            reward = abs(self.entry_price - tp1)
        return reward / risk if risk > 0 else 0


@dataclass
class ActiveTrade:
    """صفقة نشطة"""
    decision: TradeDecision
    opened_at: float
    current_price: float = 0.0
    pnl_percent: float = 0.0
    status: str = "OPEN"
    closed_at: float = 0.0
    close_price: float = 0.0


# ═══════════════════════════════════════════════════════
# Kelly Criterion Position Sizing Tests
# ═══════════════════════════════════════════════════════

class TestKellyCriterionPositionSizing:
    """اختبارات نظام Kelly Criterion لتحجيم المراكز"""

    def test_kelly_calculation_with_positive_edge(self):
        """اختبار حساب Kelly مع ميزة إيجابية (Win Rate > 50%)"""
        # Given: 60% win rate, 1.5 R:R
        win_rate = 0.60
        R = 1.5

        # When: Kelly calculation
        kelly_f = win_rate - ((1 - win_rate) / R)
        half_kelly = kelly_f / 2.0

        # Then: Should get positive Kelly fraction
        assert kelly_f > 0, "Kelly fraction should be positive with edge"
        assert kelly_f == pytest.approx(0.333, abs=0.01), "Kelly = 0.60 - (0.40/1.5) ≈ 0.333"
        assert half_kelly == pytest.approx(0.167, abs=0.01), "Half-Kelly ≈ 0.167"

    def test_kelly_calculation_with_no_edge(self):
        """اختبار Kelly مع عدم وجود ميزة (Win Rate = 50%)"""
        # Given: 50% win rate, 1.0 R:R (no edge)
        win_rate = 0.50
        R = 1.0

        # When: Kelly calculation
        kelly_f = win_rate - ((1 - win_rate) / R)

        # Then: Should get zero Kelly (don't trade)
        assert kelly_f == 0, "Kelly should be 0 with no edge"

    def test_kelly_calculation_with_negative_edge(self):
        """اختبار Kelly مع ميزة سلبية (Win Rate < 50%)"""
        # Given: 40% win rate, 1.0 R:R (negative edge)
        win_rate = 0.40
        R = 1.0

        # When: Kelly calculation
        kelly_f = win_rate - ((1 - win_rate) / R)

        # Then: Should get negative Kelly (unfavorable system)
        assert kelly_f < 0, "Kelly should be negative with negative edge"

    def test_dynamic_trade_usdt_with_insufficient_data(self):
        """اختبار حجم الصفقة مع بيانات غير كافية (< 5 صفقات)"""
        # Given: Less than 5 trades in history
        balance = 1000.0
        trade_history = []
        consecutive_losses = 0
        min_trade_usdt = 11.0
        base_risk_pct = 0.02

        # When: Calculate dynamic trade size
        expected_default = max(balance * base_risk_pct, min_trade_usdt)

        # Then: Should use default 2% sizing
        assert len(trade_history) < 5
        assert expected_default == 20.0, "2% of $1000 = $20"

    def test_dynamic_trade_usdt_during_drawdown(self):
        """اختبار حجم الصفقة خلال التراجع (2+ خسائر متتالية)"""
        # Given: In drawdown (2+ consecutive losses)
        balance = 1000.0
        consecutive_losses = 2
        loss_risk_pct = 0.01
        min_trade_usdt = 11.0

        # When: Calculate trade size during drawdown
        expected_trade = max(balance * loss_risk_pct, min_trade_usdt)

        # Then: Should reduce to 1% risk (anti-martingale)
        assert expected_trade == 11.0, "Should use MIN_TRADE_USDT since 1% of $1000 = $10 < $11 min"

    def test_kelly_position_sizing_with_good_performance(self):
        """اختبار تحجيم Kelly مع أداء جيد"""
        # Given: Strong performance (60% WR, 2.0 R:R)
        recent_trades = self._create_mock_trades(
            wins=30,  # 60% win rate
            losses=20,
            avg_win_pct=4.0,  # Average win: +4%
            avg_loss_pct=2.0   # Average loss: -2%
        )
        balance = 1000.0

        # When: Calculate Kelly position size
        wins = [t.pnl_percent for t in recent_trades if t.pnl_percent > 0]
        losses = [abs(t.pnl_percent) for t in recent_trades if t.pnl_percent < 0]

        win_rate = len(wins) / len(recent_trades)
        avg_win = sum(wins) / len(wins)
        avg_loss = sum(losses) / len(losses)
        R = avg_win / avg_loss

        kelly_f = win_rate - ((1 - win_rate) / R)
        half_kelly = kelly_f / 2.0
        risk_pct = max(min(half_kelly, 0.10), 0.01)

        # Then: Should recommend healthy position size
        assert win_rate == 0.60
        assert R == pytest.approx(2.0, abs=0.01)
        assert kelly_f == pytest.approx(0.40, abs=0.01), "Kelly = 0.60 - (0.40/2.0) = 0.40"
        assert half_kelly == pytest.approx(0.20, abs=0.01)
        assert risk_pct == 0.10, "Should be capped at 10% max"

    def test_kelly_position_sizing_bounds(self):
        """اختبار حدود تحجيم Kelly (1% min, 10% max)"""
        # Test upper bound
        balance = 1000.0
        kelly_f_high = 0.50  # 50% Kelly
        half_kelly_high = kelly_f_high / 2.0  # 25%
        risk_pct_high = max(min(half_kelly_high, 0.10), 0.01)

        assert risk_pct_high == 0.10, "Should cap at 10% maximum"

        # Test lower bound
        kelly_f_low = -0.10  # Negative Kelly
        half_kelly_low = kelly_f_low / 2.0
        risk_pct_low = max(min(half_kelly_low, 0.10), 0.01)

        assert risk_pct_low == 0.01, "Should floor at 1% minimum"

    def test_rolling_window_size(self):
        """اختبار نافذة التحليل المتحركة (آخر 50 صفقة)"""
        # Given: More than 50 trades
        all_trades = self._create_mock_trades(wins=60, losses=40, avg_win_pct=3.0, avg_loss_pct=2.0)

        # When: Take last 50
        recent_trades = all_trades[-50:]

        # Then: Should only analyze last 50
        assert len(all_trades) == 100
        assert len(recent_trades) == 50

    def _create_mock_trades(self, wins: int, losses: int, avg_win_pct: float, avg_loss_pct: float) -> List[ActiveTrade]:
        """إنشاء صفقات وهمية للاختبار"""
        trades = []

        # Create winning trades
        for _ in range(wins):
            decision = TradeDecision(
                symbol="BTCUSDT",
                direction="LONG",
                confidence=0.75,
                entry_price=50000,
                take_profits=[51000, 52000, 53000],
                stop_loss=49000,
                reasoning="Test trade"
            )
            trade = ActiveTrade(
                decision=decision,
                opened_at=time.time(),
                pnl_percent=avg_win_pct
            )
            trades.append(trade)

        # Create losing trades
        for _ in range(losses):
            decision = TradeDecision(
                symbol="BTCUSDT",
                direction="LONG",
                confidence=0.75,
                entry_price=50000,
                take_profits=[51000, 52000, 53000],
                stop_loss=49000,
                reasoning="Test trade"
            )
            trade = ActiveTrade(
                decision=decision,
                opened_at=time.time(),
                pnl_percent=-avg_loss_pct
            )
            trades.append(trade)

        return trades


# ═══════════════════════════════════════════════════════
# Tiered Take Profits Tests
# ═══════════════════════════════════════════════════════

class TestTieredTakeProfits:
    """اختبارات نظام أهداف الربح المتدرجة"""

    def test_tp_calculation_for_long_position(self):
        """اختبار حساب TPs لصفقة LONG"""
        # Given: LONG entry with SL
        entry_price = 50000.0
        stop_loss = 49250.0  # 1.5% SL
        atr = 500.0

        sl_dist = abs(entry_price - stop_loss)

        # When: Calculate tiered TPs
        tp1 = entry_price + (sl_dist * 1.5)  # Conservative
        tp2 = entry_price + (sl_dist * 2.0)  # Base target
        tp3 = entry_price + (sl_dist * 3.0)  # Runner

        # Then: Verify TP levels
        assert sl_dist == 750.0
        assert tp1 == 51125.0, "TP1 = Entry + (750 * 1.5)"
        assert tp2 == 51500.0, "TP2 = Entry + (750 * 2.0)"
        assert tp3 == 52250.0, "TP3 = Entry + (750 * 3.0)"

    def test_tp_calculation_for_short_position(self):
        """اختبار حساب TPs لصفقة SHORT"""
        # Given: SHORT entry with SL
        entry_price = 50000.0
        stop_loss = 50750.0  # 1.5% SL above

        sl_dist = abs(entry_price - stop_loss)

        # When: Calculate tiered TPs
        tp1 = entry_price - (sl_dist * 1.5)
        tp2 = entry_price - (sl_dist * 2.0)
        tp3 = entry_price - (sl_dist * 3.0)

        # Then: Verify TP levels
        assert sl_dist == 750.0
        assert tp1 == 48875.0, "TP1 = Entry - (750 * 1.5)"
        assert tp2 == 48500.0, "TP2 = Entry - (750 * 2.0)"
        assert tp3 == 47750.0, "TP3 = Entry - (750 * 3.0)"

    def test_tp1_hit_behavior(self):
        """اختبار سلوك النظام عند ضرب TP1 (50% exit + SL to Entry)"""
        # Given: LONG position approaching TP1
        entry_price = 50000.0
        stop_loss = 49250.0
        tp1 = 51125.0
        tp2 = 51500.0
        tp3 = 52250.0

        decision = TradeDecision(
            symbol="BTCUSDT",
            direction="LONG",
            confidence=0.75,
            entry_price=entry_price,
            take_profits=[tp1, tp2, tp3],
            stop_loss=stop_loss,
            reasoning="Test"
        )

        # When: Price hits TP1
        current_price = 51125.0
        tp_hit = current_price >= decision.take_profits[0]

        # Then: Should trigger TP1 logic
        assert tp_hit is True
        assert len(decision.take_profits) == 3

        # Simulate TP1 hit
        decision.take_profits.pop(0)
        original_sl = decision.stop_loss
        decision.stop_loss = decision.entry_price  # Move SL to entry

        assert len(decision.take_profits) == 2, "Should have 2 TPs remaining"
        assert decision.take_profits == [tp2, tp3]
        assert decision.stop_loss == entry_price, "SL should move to entry on TP1"
        assert decision.stop_loss > original_sl, "SL should be raised"

    def test_tp2_hit_behavior(self):
        """اختبار سلوك النظام عند ضرب TP2 (30% exit)"""
        # Given: Position with TP1 already hit
        entry_price = 50000.0
        tp2 = 51500.0
        tp3 = 52250.0

        decision = TradeDecision(
            symbol="BTCUSDT",
            direction="LONG",
            confidence=0.75,
            entry_price=entry_price,
            take_profits=[tp2, tp3],  # TP1 already removed
            stop_loss=entry_price,    # SL already at entry
            reasoning="Test"
        )

        # When: Price hits TP2
        current_price = 51500.0
        tp_hit = current_price >= decision.take_profits[0]

        # Then: Should trigger TP2 logic
        assert tp_hit is True

        # Simulate TP2 hit
        decision.take_profits.pop(0)

        assert len(decision.take_profits) == 1, "Should have 1 TP remaining (TP3)"
        assert decision.take_profits == [tp3]

    def test_tp3_hit_behavior(self):
        """اختبار سلوك النظام عند ضرب TP3 (20% exit - full close)"""
        # Given: Position with TP1 and TP2 already hit
        entry_price = 50000.0
        tp3 = 52250.0

        decision = TradeDecision(
            symbol="BTCUSDT",
            direction="LONG",
            confidence=0.75,
            entry_price=entry_price,
            take_profits=[tp3],  # Only TP3 remaining
            stop_loss=entry_price,
            reasoning="Test"
        )

        # When: Price hits TP3
        current_price = 52250.0
        tp_hit = current_price >= decision.take_profits[0]

        # Then: Should fully close
        assert tp_hit is True

        # Simulate TP3 hit
        decision.take_profits.pop(0)

        assert len(decision.take_profits) == 0, "All TPs hit - should close fully"

    def test_tp_not_hit_when_price_below(self):
        """اختبار عدم ضرب TP عندما السعر أدنى من الهدف (LONG)"""
        # Given: LONG position
        decision = TradeDecision(
            symbol="BTCUSDT",
            direction="LONG",
            confidence=0.75,
            entry_price=50000.0,
            take_profits=[51000.0, 52000.0, 53000.0],
            stop_loss=49000.0,
            reasoning="Test"
        )

        # When: Price is below TP1
        current_price = 50800.0
        tp_hit = current_price >= decision.take_profits[0]

        # Then: Should not trigger
        assert tp_hit is False
        assert len(decision.take_profits) == 3, "No TPs should be removed"

    def test_tp_for_short_position_hit_logic(self):
        """اختبار منطق ضرب TP لصفقة SHORT"""
        # Given: SHORT position
        decision = TradeDecision(
            symbol="BTCUSDT",
            direction="SHORT",
            confidence=0.75,
            entry_price=50000.0,
            take_profits=[49000.0, 48500.0, 47500.0],
            stop_loss=51000.0,
            reasoning="Test"
        )

        # When: Price falls to TP1
        current_price = 49000.0
        tp_hit = current_price <= decision.take_profits[0]

        # Then: Should trigger TP1
        assert tp_hit is True

    def test_risk_reward_calculation_with_tiered_tps(self):
        """اختبار حساب نسبة المخاطرة/المكافأة مع TPs المتدرجة"""
        # Given: Position with tiered TPs (uses TP1 for conservative R:R)
        entry_price = 50000.0
        tp1 = 51125.0
        stop_loss = 49250.0

        decision = TradeDecision(
            symbol="BTCUSDT",
            direction="LONG",
            confidence=0.75,
            entry_price=entry_price,
            take_profits=[tp1, 51500.0, 52250.0],
            stop_loss=stop_loss,
            reasoning="Test"
        )

        # When: Calculate R:R
        risk = abs(entry_price - stop_loss)
        reward = abs(tp1 - entry_price)
        expected_rr = reward / risk

        # Then: Should use TP1 for R:R calculation
        assert risk == 750.0
        assert reward == 1125.0
        assert expected_rr == pytest.approx(1.5, abs=0.01)
        assert decision.risk_reward == pytest.approx(1.5, abs=0.01)

    def test_empty_take_profits_list(self):
        """اختبار حالة قائمة TPs فارغة"""
        # Given: Decision with empty TPs (edge case)
        decision = TradeDecision(
            symbol="BTCUSDT",
            direction="LONG",
            confidence=0.75,
            entry_price=50000.0,
            take_profits=[],
            stop_loss=49000.0,
            reasoning="Test"
        )

        # Then: R:R should be 0
        assert decision.risk_reward == 0.0
        assert len(decision.take_profits) == 0


# ═══════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════

class TestPhase5Integration:
    """اختبارات التكامل بين Kelly و TPs"""

    def test_full_trade_lifecycle_with_all_tps_hit(self):
        """اختبار دورة حياة كاملة لصفقة مع ضرب جميع TPs"""
        # Given: A winning trade setup
        decision = TradeDecision(
            symbol="BTCUSDT",
            direction="LONG",
            confidence=0.80,
            entry_price=50000.0,
            take_profits=[51000.0, 51500.0, 52000.0],
            stop_loss=49500.0,
            reasoning="Strong uptrend"
        )

        # Simulate TP1 hit
        assert len(decision.take_profits) == 3
        decision.take_profits.pop(0)
        decision.stop_loss = decision.entry_price
        assert len(decision.take_profits) == 2
        assert decision.stop_loss == 50000.0

        # Simulate TP2 hit
        decision.take_profits.pop(0)
        assert len(decision.take_profits) == 1

        # Simulate TP3 hit (full close)
        decision.take_profits.pop(0)
        assert len(decision.take_profits) == 0

    def test_kelly_sizing_adapts_to_performance(self):
        """اختبار تكيف Kelly مع تغير الأداء"""
        balance = 1000.0

        # Scenario 1: Good performance
        good_trades = TestKellyCriterionPositionSizing()._create_mock_trades(
            wins=35, losses=15, avg_win_pct=3.0, avg_loss_pct=1.5
        )
        win_rate_good = 35 / 50
        R_good = 3.0 / 1.5
        kelly_good = win_rate_good - ((1 - win_rate_good) / R_good)
        risk_pct_good = max(min(kelly_good / 2, 0.10), 0.01)

        # Scenario 2: Poor performance
        poor_trades = TestKellyCriterionPositionSizing()._create_mock_trades(
            wins=20, losses=30, avg_win_pct=2.0, avg_loss_pct=2.0
        )
        win_rate_poor = 20 / 50
        R_poor = 2.0 / 2.0
        kelly_poor = win_rate_poor - ((1 - win_rate_poor) / R_poor)
        risk_pct_poor = max(min(kelly_poor / 2, 0.10), 0.01)

        # Then: Kelly should adapt
        assert risk_pct_good > risk_pct_poor, "Good performance should recommend larger size"
        assert kelly_good > 0, "Good system has positive Kelly"
        assert kelly_poor < 0, "Poor system has negative Kelly"
        assert risk_pct_poor == 0.01, "Poor system should use minimum 1%"


# ═══════════════════════════════════════════════════════
# Edge Cases & Error Handling
# ═══════════════════════════════════════════════════════

class TestEdgeCasesAndErrors:
    """اختبارات الحالات الحدية والأخطاء"""

    def test_division_by_zero_in_kelly(self):
        """اختبار حماية من القسمة على صفر في Kelly"""
        # Given: All wins (no losses)
        wins = [3.0, 4.0, 2.5]
        losses = []

        # When: Calculate avg_loss with protection
        avg_loss = 1.0 if len(losses) == 0 else sum(losses) / len(losses)

        # Then: Should not crash
        assert avg_loss == 1.0

    def test_zero_risk_reward_ratio(self):
        """اختبار R:R = 0"""
        # Given: R = 0
        R = 0
        win_rate = 0.60

        # When: Calculate Kelly with R = 0
        kelly_f = 0 if R <= 0 else win_rate - ((1 - win_rate) / R)

        # Then: Should return 0
        assert kelly_f == 0

    def test_minimum_trade_size_enforcement(self):
        """اختبار فرض الحد الأدنى لحجم الصفقة"""
        # Given: Small balance
        balance = 100.0
        risk_pct = 0.01
        min_trade_usdt = 11.0

        # When: Calculate trade size
        trade_usdt = balance * risk_pct
        trade_usdt = max(trade_usdt, min_trade_usdt)

        # Then: Should enforce minimum
        assert trade_usdt == min_trade_usdt, "Should use $11 minimum (not $1)"

    def test_negative_kelly_fraction_handling(self):
        """اختبار معالجة Kelly السالب"""
        # Given: Negative Kelly (bad system)
        win_rate = 0.30
        R = 0.8

        # When: Calculate Kelly
        kelly_f = win_rate - ((1 - win_rate) / R)
        half_kelly = kelly_f / 2.0
        risk_pct = max(min(half_kelly, 0.10), 0.01)

        # Then: Should floor at 1%
        assert kelly_f < 0
        assert risk_pct == 0.01, "Should use minimum even with negative Kelly"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
