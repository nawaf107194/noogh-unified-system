import sys
import os

def log(msg, success=None):
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"
    if success is None:
        print(f"[INFO] {msg}")
    elif success:
        print(f"[{GREEN}PASS{RESET}] {msg}")
    else:
        print(f"[{RED}FAIL{RESET}] {msg}")

def test_imports():
    log("Verifying ML Dependencies")
    
    results = {}
    
    # 1. External Libs
    libs = ["torch", "transformers", "datasets", "mlflow", "pandas", "sklearn"]
    for lib in libs:
        try:
            __import__(lib)
            log(f"Import {lib}", True)
            results[lib] = True
        except ImportError as e:
            log(f"Import {lib}: {e}", False)
            results[lib] = False

    # 2. Internal ML Modules
    modules = [
        "noogh.app.ml.hf_data_manager",
        "noogh.app.ml.model_trainer",
        "noogh.app.ml.experiment_manager"
    ]
    
    # Add src to path
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    for mod in modules:
        try:
            __import__(mod, fromlist=[''])
            log(f"Import {mod}", True)
            results[mod] = True
        except ImportError as e:
            log(f"Import {mod}: {e}", False)
            results[mod] = False
            
    if all(results.values()):
        log("All ML Imports PASSED", True)
        sys.exit(0)
    else:
        log("Some ML Imports FAILED", False)
        sys.exit(1)

if __name__ == "__main__":
    test_imports()
