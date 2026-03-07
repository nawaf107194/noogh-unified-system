import os
import torch
import shutil
from gateway.app.ml.model_registry import ModelRegistry
from neural_engine.autonomic_system.hardware_awareness import get_hardware_consciousness

def test_hardware_abstraction():
    print("[TEST] Hardware Abstraction")
    hw = get_hardware_consciousness()
    
    device = hw.get_compute_device()
    print(f"   Compute Device: {device} (Type: {type(device)})")
    assert isinstance(device, torch.device)
    
    bf16 = hw.is_bf16_supported()
    print(f"   BF16 Supported: {bf16}")
    
    # Simple sanity check
    if torch.cuda.is_available():
        assert device.type == "cuda"
    else:
        assert device.type == "cpu"
    print("[PASS] Hardware Abstraction Verified")

def test_model_registry():
    print("\n[TEST] Model Registry")
    
    # Use temporary path
    test_path = "./models_test/registry.json"
    if os.path.exists("./models_test"):
        shutil.rmtree("./models_test")
        
    registry = ModelRegistry(registry_path=test_path)
    
    # 1. Register
    model = registry.register_model(
        model_name="test-model",
        base_model="mistral-7b",
        path="/tmp/model",
        metrics={"accuracy": 0.95},
        tags=["experimental"]
    )
    print(f"   Registered: {model.model_name}:{model.version}")
    assert model.version == "v1"
    
    # 2. Promote
    registry.promote_to_production("test-model", "v1")
    prod = registry.get_production_model("test-model")
    print(f"   Production: {prod.model_name}:{prod.version} tags={prod.tags}")
    assert prod.version == "v1"
    assert "production" in prod.tags
    
    # 3. New version
    v2 = registry.register_model("test-model", "mistral-7b", "/tmp/model/v2", {}, [])
    print(f"   Registered: {v2.model_name}:{v2.version}")
    assert v2.version == "v2"
    
    # 4. Promote v2, check v1 demotion
    registry.promote_to_production("test-model", "v2")
    v1_old = next(m for m in registry.registry if m.version == "v1")
    v2_new = registry.get_production_model("test-model")
    
    print(f"   Old v1 tags: {v1_old.tags}")
    assert "production" not in v1_old.tags
    assert "archived" in v1_old.tags
    assert v2_new.version == "v2"
    
    # Cleanup
    shutil.rmtree("./models_test")
    print("[PASS] Model Registry Verified")

if __name__ == "__main__":
    try:
        test_hardware_abstraction()
        test_model_registry()
        print("\n✅ PHASE 2 VERIFICATION PASSED")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        exit(1)
