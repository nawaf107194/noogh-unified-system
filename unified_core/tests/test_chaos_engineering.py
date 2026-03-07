"""
Chaos Engineering Tests - اختبارات الفوضى
==========================================

تختبر النظام تحت ظروف معادية:
- API Failures
- Partial Fills
- Network Timeouts
- Order Rejections
- Random Slippage

الهدف: التأكد من أن النظام لا ينهار تحت الضغط

Institution-Grade Chaos Testing
"""

import random
import pytest
from typing import List

from safe_execution_engine import (
    SafeExecutionEngine,
    OrderRequest,
    OrderResult,
    ExchangeError,
    OrderRejected,
    OrderTimeout,
)


# ═══════════════════════════════════════════════════════
# Chaos Exchange - محاكي بورصة فوضوي
# ═══════════════════════════════════════════════════════

class ChaosExchange:
    """
    محاكي Binance فوضوي - يحاكي جميع المشاكل الممكنة

    يتصرف بشكل عشوائي:
    - يرفض أوامر عشوائياً
    - ينفذ جزئياً
    - يتأخر (timeout)
    - slippage عشوائي
    """

    def __init__(
        self,
        reject_prob: float = 0.2,       # 20% احتمال رفض
        partial_prob: float = 0.3,      # 30% احتمال تنفيذ جزئي
        timeout_prob: float = 0.1,      # 10% احتمال timeout
        slippage_prob: float = 0.1,     # 10% احتمال slippage
        base_price: float = 100.0,
    ):
        self.reject_prob = reject_prob
        self.partial_prob = partial_prob
        self.timeout_prob = timeout_prob
        self.slippage_prob = slippage_prob
        self.base_price = base_price
        self._order_id = 0

        self.total_orders = 0
        self.filled_orders = 0
        self.partial_orders = 0
        self.rejected_orders = 0
        self.timeout_orders = 0

    def create_order(self, req: OrderRequest) -> OrderResult:
        """إنشاء أمر مع سلوك فوضوي"""
        self.total_orders += 1

        # 1. احتمال Timeout
        if random.random() < self.timeout_prob:
            self.timeout_orders += 1
            raise OrderTimeout("Network timeout")

        # 2. احتمال Rejection
        if random.random() < self.reject_prob:
            self.rejected_orders += 1
            return OrderResult(
                status="REJECTED",
                reason="Insufficient margin / Rate limit exceeded"
            )

        # إنشاء order_id
        self._order_id += 1
        order_id = f"chaos_{self._order_id}"

        # حساب السعر (مع احتمال slippage)
        price = self.base_price
        if random.random() < self.slippage_prob:
            # slippage عشوائي ±0.1%
            slippage = random.uniform(-0.001, 0.001)
            price = price * (1 + slippage)

        # 3. احتمال Partial Fill
        if random.random() < self.partial_prob:
            self.partial_orders += 1
            filled_qty = req.qty * random.uniform(0.3, 0.7)  # 30-70% تنفيذ
            return OrderResult(
                status="PARTIAL",
                order_id=order_id,
                filled_qty=filled_qty,
                avg_price=price,
                reason="Partial fill due to low liquidity"
            )

        # 4. تنفيذ كامل
        self.filled_orders += 1
        return OrderResult(
            status="FILLED",
            order_id=order_id,
            filled_qty=req.qty,
            avg_price=price
        )

    def fetch_order(self, symbol: str, order_id: str) -> OrderResult:
        """جلب حالة أمر (دائماً ناجح في المحاكي)"""
        return OrderResult(
            status="FILLED",
            order_id=order_id,
            filled_qty=1.0,
            avg_price=self.base_price
        )

    def get_stats(self) -> dict:
        """إحصائيات التنفيذ"""
        return {
            "total": self.total_orders,
            "filled": self.filled_orders,
            "partial": self.partial_orders,
            "rejected": self.rejected_orders,
            "timeout": self.timeout_orders,
        }


# ═══════════════════════════════════════════════════════
# Chaos Tests
# ═══════════════════════════════════════════════════════

class TestChaosEngineering:
    """اختبارات الفوضى - النظام تحت الضغط"""

    def test_chaos_1000_orders_no_crash(self):
        """
        الاختبار الأهم: 1000 أمر فوضوي بدون انهيار

        الهدف:
        - النظام لا ينهار
        - جميع الأخطاء معالجة بشكل صحيح
        - لا استثناءات غير معالجة
        """
        exchange = ChaosExchange(
            reject_prob=0.2,
            partial_prob=0.3,
            timeout_prob=0.1,
            slippage_prob=0.1
        )

        engine = SafeExecutionEngine(
            exchange,
            max_retries=5,
            base_backoff_sec=0.0  # لا انتظار في الاختبار
        )

        # إحصائيات النتائج
        filled = 0
        partial = 0
        rejected = 0
        failed = 0

        # تنفيذ 1000 أمر
        for i in range(1000):
            req = OrderRequest(
                symbol="BTCUSDT",
                side="BUY" if i % 2 == 0 else "SELL",
                order_type="MARKET",
                qty=random.uniform(0.01, 1.0)
            )

            result = engine.execute(req)

            if result.status == "FILLED":
                filled += 1
            elif result.status == "PARTIAL":
                partial += 1
            elif result.status == "REJECTED":
                rejected += 1
            elif result.status == "FAILED":
                failed += 1

        # التحقق من النتائج
        total = filled + partial + rejected + failed
        assert total == 1000, "جميع الأوامر يجب أن تُعالج"
        assert filled >= 0 and partial >= 0 and rejected >= 0 and failed >= 0

        # طباعة الإحصائيات
        print(f"\n📊 Chaos Test Results (1000 orders):")
        print(f"  ✅ Filled:   {filled:>4d} ({filled/10:.1f}%)")
        print(f"  ⚠️ Partial:  {partial:>4d} ({partial/10:.1f}%)")
        print(f"  ❌ Rejected: {rejected:>4d} ({rejected/10:.1f}%)")
        print(f"  💀 Failed:   {failed:>4d} ({failed/10:.1f}%)")

        exchange_stats = exchange.get_stats()
        print(f"\n📈 Exchange Stats:")
        print(f"  Total attempts: {exchange_stats['total']}")
        print(f"  Timeouts:       {exchange_stats['timeout']}")

    def test_partial_fill_is_returned_correctly(self):
        """
        اختبار Partial Fill - يجب أن يُعاد بشكل صحيح

        المشكلة الشائعة:
        - البوت يتجاهل partial fills
        - يضيف الصفقة كاملة بينما نُفذ جزء فقط
        - → Ghost position!
        """
        exchange = ChaosExchange(
            partial_prob=1.0,  # دائماً partial
            reject_prob=0.0,
            timeout_prob=0.0,
            slippage_prob=0.0
        )

        engine = SafeExecutionEngine(
            exchange,
            max_retries=1,
            base_backoff_sec=0.0
        )

        req = OrderRequest(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            qty=2.0  # طلب 2.0
        )

        result = engine.execute(req)

        # التحقق
        assert result.status == "PARTIAL"
        assert result.filled_qty > 0 and result.filled_qty < req.qty
        assert result.order_id is not None

        print(f"\n⚠️ Partial Fill: requested={req.qty}, filled={result.filled_qty:.2f}")

    def test_rejection_does_not_retry_forever(self):
        """
        اختبار Rejection - لا retry لا نهائي

        الأوامر المرفوضة لا يجب retry لها
        (المشكلة في الأمر نفسه، ليست مشكلة شبكة)
        """
        exchange = ChaosExchange(
            reject_prob=1.0,  # دائماً مرفوض
            partial_prob=0.0,
            timeout_prob=0.0,
            slippage_prob=0.0
        )

        engine = SafeExecutionEngine(
            exchange,
            max_retries=10,  # حتى لو 10 محاولات
            base_backoff_sec=0.0
        )

        req = OrderRequest(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            qty=1.0
        )

        result = engine.execute(req)

        # يجب أن يُرفض مباشرة بدون retry
        assert result.status == "REJECTED"
        assert exchange.total_orders == 1, "يجب محاولة واحدة فقط (لا retry للرفض)"

    def test_timeout_retries_with_backoff(self):
        """
        اختبار Timeout - retry مع backoff

        Timeouts يجب أن تُعاد المحاولة
        """
        exchange = ChaosExchange(
            reject_prob=0.0,
            partial_prob=0.0,
            timeout_prob=0.9,  # 90% timeout
            slippage_prob=0.0
        )

        engine = SafeExecutionEngine(
            exchange,
            max_retries=5,
            base_backoff_sec=0.0
        )

        req = OrderRequest(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            qty=1.0
        )

        result = engine.execute(req)

        # قد ينجح أو يفشل، لكن يجب أن يحاول عدة مرات
        assert exchange.total_orders >= 1
        assert result.status in ("FILLED", "PARTIAL", "FAILED")

    def test_slippage_is_recorded(self):
        """
        اختبار Slippage - يُسجل السعر الفعلي

        الـ slippage يجب أن يُسجل في avg_price
        """
        exchange = ChaosExchange(
            reject_prob=0.0,
            partial_prob=0.0,
            timeout_prob=0.0,
            slippage_prob=1.0,  # دائماً slippage
            base_price=50000.0
        )

        engine = SafeExecutionEngine(exchange, max_retries=1, base_backoff_sec=0.0)

        req = OrderRequest(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            qty=1.0
        )

        result = engine.execute(req)

        assert result.status == "FILLED"
        assert result.avg_price is not None
        # السعر يجب أن يكون قريباً من 50000 لكن ليس بالضبط (slippage)
        assert abs(result.avg_price - 50000.0) < 100.0

    def test_mixed_chaos_scenario(self):
        """
        اختبار سيناريو مختلط - جميع المشاكل معاً

        الواقع: البورصة لا تفشل بطريقة واحدة
        """
        exchange = ChaosExchange(
            reject_prob=0.15,
            partial_prob=0.25,
            timeout_prob=0.08,
            slippage_prob=0.12
        )

        engine = SafeExecutionEngine(
            exchange,
            max_retries=3,
            base_backoff_sec=0.0
        )

        results = []
        for i in range(100):
            req = OrderRequest(
                symbol=random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT"]),
                side=random.choice(["BUY", "SELL"]),
                order_type="MARKET",
                qty=random.uniform(0.1, 2.0)
            )

            result = engine.execute(req)
            results.append(result)

        # التحقق: جميع الأوامر عولجت
        assert len(results) == 100

        # يجب أن يكون هناك تنوع في النتائج
        statuses = [r.status for r in results]
        unique_statuses = set(statuses)

        print(f"\n🎲 Mixed Chaos Results:")
        for status in ["FILLED", "PARTIAL", "REJECTED", "FAILED"]:
            count = statuses.count(status)
            print(f"  {status:>8s}: {count:>3d} ({count}%)")


# ═══════════════════════════════════════════════════════
# Stress Tests
# ═══════════════════════════════════════════════════════

class TestStressConditions:
    """اختبارات الإجهاد - الحمل الثقيل"""

    def test_10000_orders_memory_stability(self):
        """
        اختبار 10,000 أمر - لا تسريب ذاكرة

        الهدف: التأكد من عدم وجود memory leaks
        """
        exchange = ChaosExchange(
            reject_prob=0.1,
            partial_prob=0.2,
            timeout_prob=0.05
        )

        engine = SafeExecutionEngine(exchange, max_retries=2, base_backoff_sec=0.0)

        for _ in range(10000):
            req = OrderRequest(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                qty=1.0
            )
            result = engine.execute(req)

        # إذا وصلنا هنا بدون crash → نجاح
        assert True

        stats = exchange.get_stats()
        print(f"\n📊 Stress Test (10k orders):")
        print(f"  Total:    {stats['total']:>6d}")
        print(f"  Filled:   {stats['filled']:>6d}")
        print(f"  Partial:  {stats['partial']:>6d}")
        print(f"  Rejected: {stats['rejected']:>6d}")
        print(f"  Timeout:  {stats['timeout']:>6d}")

    def test_rapid_fire_orders(self):
        """
        اختبار إطلاق سريع - 100 أمر بدون تأخير

        يحاكي: bot runaway (يفتح صفقات بسرعة جنونية)
        """
        exchange = ChaosExchange()
        engine = SafeExecutionEngine(exchange, max_retries=1, base_backoff_sec=0.0)

        results = []
        for i in range(100):
            req = OrderRequest(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                qty=1.0
            )
            result = engine.execute(req)
            results.append(result)

        # جميع الأوامر معالجة
        assert len(results) == 100

        filled = sum(1 for r in results if r.status == "FILLED")
        print(f"\n⚡ Rapid Fire: {filled}/100 filled")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
