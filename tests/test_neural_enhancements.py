"""
اختبارات شاملة لتحسينات النظام العصبي

يختبر جميع المكونات الجديدة:
1. Parallel Processing
2. Intelligent Caching
3. Hierarchical Reasoning
4. Enhanced Neural Models
5. Neural Integration
"""

import asyncio
import pytest
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# استيراد المكونات للاختبار
from unified_core.parallel_processor import ParallelProcessor, ProcessingResult
from unified_core.intelligent_cache import IntelligentCache, CacheEntry
from unified_core.hierarchical_reasoner import HierarchicalReasoner, ReasoningContext, ReasoningResult, ReasoningLevel
from unified_core.neural_core.enhanced_model import EnhancedNeuralModel, InferenceResult, ModelType
from unified_core.neural_integration import NeuralIntegrationSystem, IntegratedReasoningRequest, IntegratedReasoningResult


class TestParallelProcessor:
    """اختبارات المعالجة المتوازية"""
    
    @pytest.fixture
    def processor(self):
        return ParallelProcessor(max_workers=2)
    
    @pytest.mark.asyncio
    async def test_process_batch_success(self, processor):
        """اختبار معالجة دفعة ناجحة"""
        items = [1, 2, 3, 4, 5]
        
        def square(x):
            return x * x
        
        results = await processor.process_batch(items, square)
        
        assert len(results) == len(items)
        assert all(r.success for r in results)
        assert [r.result for r in results] == [1, 4, 9, 16, 25]
        
        stats = processor.get_stats()
        assert stats["total_tasks"] == len(items)
        assert stats["successful_tasks"] == len(items)
        assert stats["success_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_process_batch_with_errors(self, processor):
        """اختبار معالجة دفعة تحتوي على أخطاء"""
        items = [1, 2, 3]
        
        def sometimes_fail(x):
            if x == 2:
                raise ValueError("Test error")
            return x * x
        
        results = await processor.process_batch(items, sometimes_fail)
        
        assert len(results) == len(items)
        assert results[0].success  # item 1
        assert not results[1].success  # item 2
        assert results[2].success  # item 3
        
        stats = processor.get_stats()
        assert stats["success_rate"] < 1.0
    
    @pytest.mark.asyncio
    async def test_map_reduce(self, processor):
        """اختبار نمط Map-Reduce"""
        items = [1, 2, 3, 4, 5]
        
        def map_func(x):
            return x * 2
        
        def reduce_func(results):
            return sum(results)
        
        result = await processor.map_reduce(items, map_func, reduce_func)
        
        assert result == 30  # (1*2 + 2*2 + 3*2 + 4*2 + 5*2) = 30


class TestIntelligentCache:
    """اختبارات الذاكرة المؤقتة الذكية"""
    
    @pytest.fixture
    def cache(self):
        return IntelligentCache(max_size=10, max_memory_mb=1.0)
    
    @pytest.mark.asyncio
    async def test_basic_operations(self, cache):
        """اختبار العمليات الأساسية"""
        # حفظ
        await cache.set("test_key", "test_value")
        
        # استرجاع
        value = await cache.get("test_key")
        assert value == "test_value"
        
        # استرجاع غير موجود
        missing = await cache.get("missing_key")
        assert missing is None
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
    
    @pytest.mark.asyncio
    async def test_get_or_compute(self, cache):
        """اختبار get_or_compute"""
        compute_count = 0
        
        async def compute_func():
            nonlocal compute_count
            compute_count += 1
            return f"computed_{compute_count}"
        
        # المرة الأولى: compute
        result1 = await cache.get_or_compute("compute_key", compute_func)
        assert result1 == "computed_1"
        assert compute_count == 1
        
        # المرة الثانية: get from cache
        result2 = await cache.get_or_compute("compute_key", compute_func)
        assert result2 == "computed_1"
        assert compute_count == 1  # لم تتغير
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache):
        """اختبار إزالة LRU"""
        # ملء الذاكرة المؤقتة
        for i in range(15):  # أكثر من max_size
            await cache.set(f"key_{i}", f"value_{i}")
        
        stats = cache.get_stats()
        assert stats["size"] <= 10  # يجب أن يكون <= max_size
        assert stats["evictions"] > 0
    
    @pytest.mark.asyncio
    async def test_expiration(self, cache):
        """اختبار انتهاء الصلاحية"""
        await cache.set("temp_key", "temp_value", ttl=0.1)  # 100ms
        
        # الانتظار حتى انتهاء الصلاحية
        await asyncio.sleep(0.2)
        
        value = await cache.get("temp_key")
        assert value is None
        
        stats = cache.get_stats()
        assert stats["expirations"] == 1


class TestHierarchicalReasoner:
    """اختبارات المفكر الهرمي"""
    
    @pytest.fixture
    def reasoner(self):
        return HierarchicalReasoner()
    
    @pytest.fixture
    def basic_context(self):
        return ReasoningContext(
            observation={"status": "normal"},
            current_beliefs={"stable": True},
            goals=["optimize"],
            constraints={},
            available_actions=["wait", "optimize"],
            urgency=5.0,
            importance=5.0,
            complexity=5.0
        )
    
    @pytest.mark.asyncio
    async def test_reasoning_level_selection(self, reasoner, basic_context):
        """اختبار اختيار مستوى التفكير المناسب"""
        # اختبار Urgency العالية → Reactive
        high_urgency_context = basic_context
        high_urgency_context.urgency = 9.0
        result = await reasoner.reason(high_urgency_context)
        assert result.level == ReasoningLevel.REACTIVE
        
        # اختبار التعقيد العالي → Strategic
        high_complexity_context = basic_context
        high_complexity_context.urgency = 1.0  # Reset urgency
        high_complexity_context.complexity = 8.0
        high_complexity_context.importance = 8.0
        result = await reasoner.reason(high_complexity_context)
        assert result.level in [ReasoningLevel.STRATEGIC, ReasoningLevel.METACOGNITIVE]
    
    @pytest.mark.asyncio
    async def test_reasoning_quality(self, reasoner, basic_context):
        """اختبار جودة التفكير"""
        result = await reasoner.reason(basic_context)
        
        assert result.success
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.decision is not None
        assert len(result.reasoning_steps) > 0
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, reasoner, basic_context):
        """اختبار آلية Fallback"""
        # Mock فشل المستوى العالي
        with patch.object(reasoner, '_strategic_reasoning', side_effect=Exception("Test failure")):
            strategic_context = basic_context
            strategic_context.complexity = 8.0
            strategic_context.importance = 8.0
            
            result = await reasoner.reason(strategic_context)
            
            # يجب أن ينتقل إلى مستوى أبسط
            assert result.success
            assert result.level in [ReasoningLevel.ANALYTICAL, ReasoningLevel.REACTIVE]


class TestEnhancedNeuralModel:
    """اختبارات النموذج العصبي المحسن"""
    
    @pytest.fixture
    def neural_model(self):
        model = EnhancedNeuralModel()
        # استخدام mock بدلاً من تحميل نماذج حقيقية
        model.models = {}
        model.tokenizers = {}
        model.pipelines = {}
        return model
    
    @pytest.mark.asyncio
    async def test_model_selection(self, neural_model):
        """اختبار اختيار النموذج"""
        context = {"urgency": 9.0, "complexity": 3.0}
        # مع نماذج mock، سيعود None
        selected = neural_model._select_best_model(context)
        assert selected is None
    
    @pytest.mark.asyncio
    async def test_confidence_estimation(self, neural_model):
        """اختبار تقدير الثقة"""
        text = "This is a comprehensive and well-reasoned response with multiple points."
        context = {"keywords": ["comprehensive", "reasoned", "points"]}
        
        confidence = neural_model._estimate_confidence(text, context)
        
        assert 0.0 <= confidence <= 1.0
        # النص الجيد يجب أن يكون بثقة عالية
        assert confidence > 0.5


class TestNeuralIntegrationSystem:
    """اختبارات نظام التكامل العصبي"""
    
    @pytest.fixture
    def integration_system(self):
        system = NeuralIntegrationSystem()
        
        # Mock المكونات الداخلية باستخدام AsyncMock للوظائف التي يتم انتظارها
        system.processor = Mock()
        system.processor.process_batch = AsyncMock()
        
        system.belief_cache = Mock()
        system.belief_cache.get = AsyncMock()
        system.belief_cache.set = AsyncMock()
        
        system.decision_cache = Mock()
        system.decision_cache.get = AsyncMock()
        system.decision_cache.set = AsyncMock()
        system.decision_cache.get_stats = Mock(return_value={"hits": 0, "misses": 0})
        
        system.observation_cache = Mock()
        system.observation_cache.get = AsyncMock()
        system.observation_cache.set = AsyncMock()
        
        system.reasoner = Mock()
        system.reasoner.reason = AsyncMock()
        system.reasoner.get_stats = Mock(return_value={"successful": 0})
        
        system.neural_model = Mock()
        system.neural_model.generate = AsyncMock()
        system.neural_model.get_stats = Mock(return_value={"inferences": 0})
        
        return system
    
    @pytest.fixture
    def sample_request(self):
        return IntegratedReasoningRequest(
            observation={"test": "data"},
            current_beliefs={"belief": "value"},
            goals=["test_goal"],
            constraints={},
            available_actions=["action1", "action2"],
            urgency=5.0,
            importance=5.0,
            complexity=5.0
        )
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, integration_system, sample_request):
        """اختبار ضرب الذاكرة المؤقتة"""
        integration_system.decision_cache.get.return_value = "cached_decision"
        
        result = await integration_system.integrated_reasoning(sample_request)
        
        assert result.success
        assert result.final_decision == "cached_decision"
        assert "cache" in result.components_used
        integration_system.decision_cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_full_reasoning_flow(self, integration_system, sample_request):
        """اختبار مسار التفكير الكامل"""
        integration_system.decision_cache.get.return_value = None  # cache miss
        
        integration_system.processor.process_batch.return_value = [
            ProcessingResult(success=True, result={"processed": True}, duration_ms=10, worker_id=1)
        ]
        
        reasoning_result = ReasoningResult(
            level=ReasoningLevel.ANALYTICAL,
            decision="test_decision",
            confidence=0.8,
            reasoning_steps=["Step 1", "Step 2"],
            time_taken_ms=50.0
        )
        integration_system.reasoner.reason.return_value = reasoning_result
        
        result = await integration_system.integrated_reasoning(sample_request)
        
        assert result.success
        assert result.final_decision == "test_decision"
        assert result.confidence == 0.8
        assert "hierarchical_reasoning" in result.components_used
        integration_system.decision_cache.set.assert_called_once()


class TestPerformanceBenchmarks:
    """اختبارات أداء"""
    
    @pytest.mark.asyncio
    async def test_parallel_processing_performance(self):
        """اختبار أداء المعالجة المتوازية"""
        processor = ParallelProcessor(max_workers=4)
        
        items = list(range(100))
        
        def process_item(x):
            time.sleep(0.001)  # 1ms محاكاة
            return x * x
        
        start_time = time.time()
        results = await processor.process_batch(items, process_item)
        total_time = (time.time() - start_time) * 1000
        
        assert len(results) == len(items)
        assert all(r.success for r in results)
        
        # يجب أن يكون الوقت أقل من المعالجة التسلسلية
        sequential_time_estimate = len(items) * 1  # 100ms تسلسلي
        assert total_time < sequential_time_estimate * 2  # مع بعض overhead
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """اختبار أداء الذاكرة المؤقتة"""
        cache = IntelligentCache(max_size=1000)
        
        start_time = time.time()
        
        # اختبار سرعة الإدخال
        for i in range(100):
            await cache.set(f"key_{i}", f"value_{i}")
        
        # اختبار سرعة الاسترجاع
        for i in range(100):
            await cache.get(f"key_{i}")
        
        total_time = (time.time() - start_time) * 1000
        
        # يجب أن يكون سريعاً (أقل من 10ms لكل عملية في المتوسط)
        avg_time_per_op = total_time / 200  # 200 عملية
        assert avg_time_per_op < 10.0  # أقل من 10ms لكل عملية


@pytest.mark.integration
class TestIntegrationScenarios:
    """اختبارات سيناريوهات التكامل"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """اختبار سير العمل الكامل"""
        # هذا اختبار تكامل حقيقي قد يتطلب تهيئة
        pytest.skip("Integration test requires proper setup")
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """اختبار استعادة الأخطاء"""
        # اختبار كيفية تعامل النظام مع الأخطاء
        pytest.skip("Error recovery test requires proper setup")


# اختبارات الأداء الشاملة
@pytest.mark.performance
class TestComprehensivePerformance:
    """اختبارات أداء شاملة"""
    
    @pytest.mark.asyncio
    async def test_throughput_benchmark(self):
        """اختبار معدل الإنتاجية"""
        processor = ParallelProcessor(max_workers=8)
        cache = IntelligentCache(max_size=1000)
        
        # اختبار معدل الإنتاجية
        test_items = list(range(500))
        
        start_time = time.time()
        
        # معالجة متوازية
        results = await processor.process_batch(
            test_items,
            lambda x: x * x
        )
        
        # استخدام الذاكرة المؤقتة
        for i in test_items[:100]:
            await cache.set(f"perf_key_{i}", f"perf_value_{i}")
        
        for i in test_items[:100]:
            await cache.get(f"perf_key_{i}")
        
        total_time = (time.time() - start_time) * 1000
        total_operations = len(test_items) + 200  # 500 معالجة + 200 عملية cache
        
        throughput = total_operations / (total_time / 1000)  # عمليات/ثانية
        
        print(f"Throughput: {throughput:.1f} ops/sec")
        print(f"Total time: {total_time:.1f}ms")
        print(f"Total operations: {total_operations}")
        
        assert throughput > 1000  # يجب أن يكون على الأقل 1000 عملية/ثانية


if __name__ == "__main__":
    # تشغيل الاختبارات
    import sys
    import subprocess
    
    print("🚀 Running neural enhancement tests...")
    
    # تشغيل pytest مع output مفصل
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    
    if result.returncode != 0:
        print("❌ Tests failed!")
        print(result.stderr)
        sys.exit(1)
    else:
        print("✅ All tests passed!")
