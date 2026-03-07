"""Quick safe mode reset — minimal imports."""
import json, time
from pathlib import Path

ledger_file = Path.home() / ".noogh" / "evolution" / "evolution_ledger.jsonl"

# Write a safe_mode_exit entry
entry = {
    "timestamp": time.time(),
    "event_type": "safe_mode_exit",
    "data": {"reason": "Structural Integrity Gate deployed — indentation auto-fix + AST validation"},
    "prev_hash": "manual_reset",
    "hash": f"reset_{int(time.time())}"
}

with open(ledger_file, 'a') as f:
    f.write(json.dumps(entry) + '\n')

print(f"✅ Safe mode exit entry written to {ledger_file}")
print("⚠️  Daemon must be restarted for changes to take effect")
