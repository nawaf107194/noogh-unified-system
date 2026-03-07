
import asyncio
from gateway.app.ml.intelligent_training import get_training_engine, TrainingConfig

async def verify():
    print("🛡️  ARCHITECTURAL SECURITY VERIFICATION")
    print("---------------------------------------")
    
    engine = get_training_engine()
    
    # Test Case: Try to load 'memories' (Simulating leakage/attack)
    config = TrainingConfig(
        model_name="distilgpt2",
        dataset_name="memories", # ❌ FORBIDDEN SOURCE
        output_dir="./tmp_model",
        use_gpu=False,
        auto_optimize=False
    )
    
    print(f"🧪 Attempting to load forbidden dataset: '{config.dataset_name}'")
    
    try:
        await engine._load_data_parallel(config)
        print("\n\n❌ SECURITY FAILURE: The engine accepted 'memories'! Isolation is broken.")
        exit(1)
    except ValueError as e:
        print(f"\n✅ SECURITY PASS: Engine rejected 'memories' with error:")
        print(f"   \"{str(e)}\"")
        exit(0)
    except Exception as e:
        print(f"\nExample failed with unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
