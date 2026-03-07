
import pytest
from unittest.mock import MagicMock, patch
from gateway.app.core.agent_kernel import AgentKernel, AgentResult
from gateway.app.ml.intelligent_training import IntelligentTrainingEngine, TrainingConfig

# ----------------------------------------------------------------------
# 1. MEMORY ADMISSION INVARIANT (The Great Wall)
# ----------------------------------------------------------------------

@pytest.fixture
def kernel_gate():
    """Mock kernel with just enough to test the gate."""
    kernel = AgentKernel(enable_persistence=False, enable_learning=False, enable_dream_mode=False)
    return kernel

def test_memory_gate_rejects_failures(kernel_gate):
    """Invariant: Failed tasks MUST NOT enter memory."""
    bad_result = AgentResult(success=False, answer="I failed", steps=1, error="SomeError")
    assert kernel_gate._should_persist(bad_result) is False

def test_memory_gate_rejects_operational_noise(kernel_gate):
    """Invariant: Operational messages (Gemini Unavailable etc) MUST NOT enter memory."""
    # List of forbidden phrases as defined in architecture
    noise_phrases = [
        "Gemini Unavailable",
        "Local Brain is Hibernated",
        "Fallback mode",
        "Error: Something went wrong",
        "NoneType"
    ]
    for phrase in noise_phrases:
        bad_result = AgentResult(success=True, answer=f"Response with {phrase} inside", steps=1)
        assert kernel_gate._should_persist(bad_result) is False, f"Gate failed to reject: {phrase}"

def test_memory_gate_rejects_internal_tags(kernel_gate):
    """Invariant: Internal Monologue tags (THINK/ACT) MUST NOT enter memory."""
    leak_tags = ["THINK: I am thinking", "ACT: run_tool", "Observation: output"]
    for tag in leak_tags:
        bad_result = AgentResult(success=True, answer=f"Here is the answer. {tag}", steps=1)
        assert kernel_gate._should_persist(bad_result) is False, f"Gate failed to reject tag: {tag}"

def test_memory_gate_rejects_low_confidence(kernel_gate):
    """Invariant: Low confidence (< 0.7) MUST NOT enter memory."""
    uncertain_result = AgentResult(
        success=True, 
        answer="Maybe this is right", 
        steps=1, 
        confidence={"score": 0.5}
    )
    assert kernel_gate._should_persist(uncertain_result) is False

def test_memory_gate_accepts_clean_results(kernel_gate):
    """Invariant: Clean, high-confidence results SHOULD enter memory."""
    good_result = AgentResult(
        success=True, 
        answer="The capital of France is Paris.", 
        steps=1, 
        confidence={"score": 0.9}
    )
    assert kernel_gate._should_persist(good_result) is True


# ----------------------------------------------------------------------
# 2. TRAINING ISOLATION INVARIANT (The Iron Curtain)
# ----------------------------------------------------------------------

def test_training_engine_rejects_polluted_sources():
    """Invariant: Training MUST reject 'memories' or unknown datasets."""
    import asyncio
    
    async def run_async_test():
        engine = IntelligentTrainingEngine()
        
        # 1. Test: Prohibited Source 'memories'
        config_memories = TrainingConfig(
            model_name="gpt2",
            dataset_name="memories", # ❌ Forbidden
            output_dir=".",
            use_gpu=False
        )
        
        with pytest.raises(ValueError) as excinfo:
            await engine._load_data_parallel(config_memories)
        
        assert "Strict Architecture" in str(excinfo.value) or "STRICT ARCHITECTURE" in str(excinfo.value)
        assert "Clean Source" in str(excinfo.value)

        # 2. Test: Unknown Source 'random_thing'
        config_unknown = TrainingConfig(
            model_name="gpt2",
            dataset_name="random_garbage_dataset", # ❌ Unknown
            output_dir=".",
            use_gpu=False
        )
        
        with pytest.raises(ValueError):
            await engine._load_data_parallel(config_unknown)
            
    asyncio.run(run_async_test())

