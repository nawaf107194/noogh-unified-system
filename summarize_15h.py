import sqlite3
import time
from pathlib import Path
import json

start_time = time.time() - (15 * 3600)
base_dir = Path("/home/noogh/projects/noogh_unified_system/src/data")

print("=== NOOGH 15-Hour Activity Summary ===")

# 1. EVOLUTION LEDGER
try:
    with sqlite3.connect(base_dir / "evolution" / "evolution_ledger.sqlite") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, count(*) FROM proposals WHERE created_at > ? GROUP BY status", (start_time,))
        proposals = cursor.fetchall()
        print(f"\n[🧬 Evolution Proposals Processed]: {proposals}")
except Exception as e:
    print(f"\n[🧬 Evolution Proposals]: Database reading error: {e}")

# 2. NEURON FABRIC (Autonomous Growth)
try:
    with open(base_dir / "neuron_fabric.json", "r") as f:
        data = json.load(f)
        neurons = data.get("neurons", {})
        recent_neurons = [n for n in neurons.values() if n.get("created_at", 0) > start_time]
        print(f"\n[🧠 Neuron Fabric]: Expanded by {len(recent_neurons)} new neurons (Total: {len(neurons)})")
except Exception as e:
    print(f"\n[🧠 Neuron Fabric]: Error reading - {e}")

# 3. SYSTEM STABILITY (Metrics)
try:
    with sqlite3.connect(base_dir / "metrics" / "system_metrics.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*), avg(cpu_percent), avg(memory_percent) FROM metrics WHERE timestamp > ?", (start_time,))
        metrics = cursor.fetchone()
        print(f"\n[📊 System Metrics]: Realtime monitoring captured {metrics[0]} data points (Avg CPU: {metrics[1]:.1f}%, Avg Mem: {metrics[2]:.1f}%)")
except Exception as e:
    print(f"\n[📊 System Metrics]: Error reading - {e}")

# 4. DISTILLATION (Self-Training Data)
try:
    with open(base_dir / "distillation" / "teacher_trajectories.jsonl", "r") as f:
        total = sum(1 for line in f)
        print(f"\n[📚 Knowledge Distillation]: Stored total {total} successful execution trajectories from Teacher model")
except Exception as e:
    print(f"\n[📚 Knowledge Distillation]: N/A")

# 5. TRADING HISTORY (Optional Insight)
try:
    with open(base_dir / "trading" / "trade_history.json", "r") as f:
        trades = json.load(f)
        recent_trades = [t for t in trades if t.get("timestamp", 0) > start_time]
        print(f"\n[📈 Sovereign Trading]: {len(recent_trades)} trades executed in the last 15h (Total: {len(trades)})")
except Exception as e:
    print(f"\n[📈 Sovereign Trading]: N/A or No recent trades")
