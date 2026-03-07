from gateway.app.core.ast_validator import validate_code

test_cases = [
    ("print('Hello')", True),
    ("x = 1 + 1", True),
    ("import os", False),
    ("import sys", False),
    ("import subprocess", False),
    ("os.system('rm -rf /')", False),
    ("eval('1+1')", False),
    ("exec('print(1)')", False),
    ("open('/etc/passwd')", False),
    ("import requests", False),
    ("def foo():\n  import os\n  os.system('ls')", False)
]

print("Running AST Validator Tests...")
failures = 0
for code, expected in test_cases:
    allowed, msg = validate_code(code)
    if allowed != expected:
        print(f"FAILED: Code: {code[:20]}... Expected: {expected}, Got: {allowed} ({msg})")
        failures += 1
    else:
        print(f"PASSED: Code: {code[:20]}... ({msg})")

if failures == 0:
    print("✅ All AST tests passed.")
else:
    print(f"❌ {failures} tests failed.")
    exit(1)
