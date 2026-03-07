import json
import sqlite3
import time
import os
from pathlib import Path

start_time = time.time() - (15 * 3600)
print(f"--- Summary for the last 15 hours (since timestamp {start_time}) ---")

base_dir = Path('/home/noogh/projects/noogh_unified_system/src/data')

# 1. Evolution Memory & Ledger
try:
    with sqlite3.connect(base_dir / "evolution" / "evolution_ledger.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, count(*) FROM proposals WHERE created_at > ? GROUP BY status", (start_time,))
        proposals = cursor.fetchall()
        print(f"\n[🧬 Evolution Proposals]: {proposals}")
except:
    print("[🧬 Evolution]: No evolution_ledger.db or error accessing it.")

# 2. Neuron Fabric
try:
    with open(base_dir / "neuron_fabric.json", "r") as f:
        data = json.load(f)
        neurons = data.get("neurons", {})
        synapses = data.get("synapses", [])
        recent = [n for n in neurons.values() if n.get("created_at", 0) > start_time]
        print(f"\n[🧠 Neuron Fabric]: Total Neurons: {len(neurons)}, Synapses: {len(synapses)}. New in last 15h: {len(recent)}")
except Exception as e:
    print(f"\n[🧠 Neuron Fabric]: Error - {e}")

# 3. Time Series Metrics
try:
    with sqlite3.connect(base_dir / "metrics" / "system_metrics.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*), avg(cpu_percent), avg(memory_percent) FROM metrics WHERE timestamp > ?", (start_time,))
        metrics = cursor.fetchone()
        print(f"\n[📊 System Metrics]: Rows collected: {metrics[0]}, Avg CPU: {metrics[1]:.1f}%, Avg Mem: {metrics[2]:.1f}%")
except Exception as e:
    print(f"\n[📊 System Metrics]: Error - {e}")

# 4. Learning Innovations
try:
    with open(base_dir / "innovations.jsonl", "r") as f:
        lines = f.readlines()
        recent = 0
        applied = 0
        for line in lines:
            try:
                data = json.load(line)
                if data.get("timestamp", 0) > start_time:
                    recent += 1
                    if data.get("status") in ("applied", "queued_for_evolution", "processing_by_evolution"):
                        applied += 1
            except: pass
        print(f"\n[💡 Innovations]: {recent} new, {applied} applied/queued.")
except Exception as e:
    print(f"\n[💡 Innovations]: Error - {e}")

# 5. Distillation
try:
    with open(base_dir / "distillation" / "teacher_trajectories.jsonl") as f:
        lines = len(f.readlines())
        print(f"\n[📚 Distillation]: Total teacher trajectories: {lines}")
except: pass

