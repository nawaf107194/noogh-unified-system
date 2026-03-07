"""
Safe Execution Engine - محرك تنفيذ آمن للأوامر
==============================================

يحمي من:
- فشل API
- Timeouts
- Partial Fills
- Order Rejection

يتعامل مع:
- Automatic Retry مع Exponential Backoff
- Error Handling الشامل
- State Tracking الدقيق

Institution-Grade Order Execution
"""

from dataclasses import dataclass
from typing import Optional, Protocol
import time
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════

class ExchangeError(Exception):
    """خطأ عام من البورصة"""
    pass


class OrderRejected(ExchangeError):
    """الأمر مرفوض من البورصة"""
    pass


class OrderTimeout(ExchangeError):
    """انتهت مهلة الأمر"""
    pass


# ═══════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════

@dataclass
class OrderRequest:
    """طلب أمر جديد"""
    symbol: str
    side: str           # "BUY" | "SELL"
    order_type: str     # "MARKET" | "LIMIT"
    qty: float
    price: Optional[float] = None
    leverage: int = 10
    reduce_only: bool = False


@dataclass
class OrderResult:
    """نتيجة تنفيذ الأمر"""
    status: str         # "FILLED" | "PARTIAL" | "REJECTED" | "FAILED"
    order_id: Optional[str] = None
    filled_qty: float = 0.0
    avg_price: Optional[float] = None
    reason: Optional[str] = None
    commission: float = 0.0


# ═══════════════════════════════════════════════════════
# Exchange Protocol
# ═══════════════════════════════════════════════════════

class ExchangeClient(Protocol):
    """واجهة البورصة (Protocol)"""

    def create_order(self, req: OrderRequest) -> OrderResult:
        """إنشاء أمر جديد"""
        ...

    def fetch_order(self, symbol: str, order_id: str) -> OrderResult:
        """جلب حالة أمر موجود"""
        ...


# ═══════════════════════════════════════════════════════
# Safe Execution Engine
# ═══════════════════════════════════════════════════════

class SafeExecutionEngine:
    """
    محرك تنفيذ آمن مع Retry و Error Handling

    يضمن:
    1. Retry تلقائي مع Exponential Backoff
    2. معالجة جميع أنواع الأخطاء
    3. تسجيل دقيق للحالة
    4. عدم إضافة صفقات وهمية للنظام

    Examples:
        >>> from safe_execution_engine import SafeExecutionEngine, OrderRequest
        >>> engine = SafeExecutionEngine(exchange_client, max_retries=3)
        >>> req = OrderRequest(symbol="BTCUSDT", side="BUY",
        ...                    order_type="MARKET", qty=1.0)
        >>> result = engine.execute(req)
        >>> if result.status == "FILLED":
        ...     print(f"Order filled: {result.filled_qty} @ {result.avg_price}")
        >>> elif result.status == "PARTIAL":
        ...     print(f"Partial fill: {result.filled_qty} of {req.qty}")
    """

    def __init__(
        self,
        exchange: ExchangeClient,
        max_retries: int = 3,
        base_backoff_sec: float = 0.5,
    ):
        """
        Args:
            exchange: واجهة البورصة (ExchangeClient)
            max_retries: عدد المحاولات القصوى (default: 3)
            base_backoff_sec: وقت الانتظار الأساسي بين المحاولات (default: 0.5s)
        """
        self.exchange = exchange
        self.max_retries = max_retries
        self.base_backoff_sec = base_backoff_sec

        logger.info(
            f"🔒 Safe Execution Engine initialized: "
            f"max_retries={max_retries}, "
            f"backoff={base_backoff_sec}s"
        )

    def execute(self, req: OrderRequest) -> OrderResult:
        """
        تنفيذ أمر مع Retry تلقائي

        Args:
            req: طلب الأمر

        Returns:
            OrderResult: نتيجة التنفيذ (FILLED, PARTIAL, REJECTED, FAILED)
        """
        last_error = None
        attempt = 0

        logger.info(
            f"📤 Executing order: {req.side} {req.qty} {req.symbol} "
            f"@ {req.order_type}"
        )

        for attempt in range(self.max_retries):
            try:
                # محاولة إنشاء الأمر
                result = self.exchange.create_order(req)

                # ✅ تنفيذ كامل
                if result.status == "FILLED":
                    logger.info(
                        f"✅ Order FILLED: {result.filled_qty} {req.symbol} "
                        f"@ ${result.avg_price:,.2f} (id: {result.order_id})"
                    )
                    return result

                # ⚠️ تنفيذ جزئي
                if result.status == "PARTIAL":
                    fill_pct = (result.filled_qty / req.qty) * 100 if req.qty > 0 else 0
                    logger.warning(
                        f"⚠️ Order PARTIAL: {result.filled_qty}/{req.qty} "
                        f"({fill_pct:.1f}%) {req.symbol} "
                        f"@ ${result.avg_price:,.2f} (id: {result.order_id})"
                    )
                    # نقبل Partial Fill ونترك Position Manager يتعامل معه
                    return result

                # ❌ مرفوض
                if result.status == "REJECTED":
                    logger.error(
                        f"❌ Order REJECTED: {req.symbol} - {result.reason}"
                    )
                    # لا retry للأوامر المرفوضة (غالباً مشكلة في الطلب نفسه)
                    return result

                # Unknown status
                last_error = result.reason or "Unknown status"
                logger.warning(f"⚠️ Unknown order status: {result.status}")

            except OrderTimeout as e:
                last_error = f"Timeout: {str(e)}"
                logger.warning(
                    f"⏱️ Order timeout (attempt {attempt + 1}/{self.max_retries}): {last_error}"
                )

            except OrderRejected as e:
                last_error = f"Rejected: {str(e)}"
                logger.error(f"❌ Order rejected: {last_error}")
                # لا retry للرفض
                return OrderResult(
                    status="REJECTED",
                    reason=last_error
                )

            except ExchangeError as e:
                last_error = f"Exchange error: {str(e)}"
                logger.warning(
                    f"⚠️ Exchange error (attempt {attempt + 1}/{self.max_retries}): {last_error}"
                )

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(
                    f"💥 Unexpected error (attempt {attempt + 1}/{self.max_retries}): {last_error}"
                )

            # Exponential backoff قبل المحاولة التالية
            if attempt < self.max_retries - 1:
                backoff = self.base_backoff_sec * (2 ** attempt)
                logger.debug(f"⏳ Backing off for {backoff:.2f}s...")
                time.sleep(backoff)

        # فشلت جميع المحاولات
        logger.error(
            f"💀 Order FAILED after {self.max_retries} attempts: "
            f"{req.symbol} - {last_error}"
        )
        return OrderResult(
            status="FAILED",
            reason=f"Retries exhausted ({self.max_retries}): {last_error}"
        )

    def execute_with_verification(
        self,
        req: OrderRequest,
        verify_after_sec: float = 2.0
    ) -> OrderResult:
        """
        تنفيذ أمر مع تحقق إضافي من الحالة

        مفيد للأوامر المهمة حيث نريد التأكد من الحالة النهائية

        Args:
            req: طلب الأمر
            verify_after_sec: وقت الانتظار قبل التحقق (default: 2.0s)

        Returns:
            OrderResult: النتيجة المحققة
        """
        result = self.execute(req)

        # إذا كان الأمر معلقاً أو غير واضح، نتحقق مرة أخرى
        if result.status not in ("FILLED", "PARTIAL", "REJECTED", "FAILED"):
            if result.order_id:
                logger.info(f"🔍 Verifying order status after {verify_after_sec}s...")
                time.sleep(verify_after_sec)

                try:
                    verified = self.exchange.fetch_order(req.symbol, result.order_id)
                    logger.info(f"✅ Verified status: {verified.status}")
                    return verified
                except Exception as e:
                    logger.error(f"❌ Verification failed: {e}")

        return result
