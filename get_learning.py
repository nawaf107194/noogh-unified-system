import sqlite3
import json

conn = sqlite3.connect("/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite")
cur = conn.cursor()

print("=== BELIEFS (Orchestrator Synthesis & Agent Rerports) ===")
# Get the most recent keys related to orchestrator or agents
cur.execute("SELECT key, value, updated_at FROM beliefs WHERE key LIKE 'orchestrator%' OR key LIKE 'agent_run%' ORDER BY updated_at DESC LIMIT 10")
for r in cur.fetchall():
    print(f"Key: {r[0]}")
    try:
        data = json.loads(r[1])
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(r[1])
    print("-" * 50)

print("\n=== OBSERVATIONS (LocalHarvester & Others) ===")
# Get recent observations
try:
    cur.execute("SELECT source, content, timestamp FROM observations ORDER BY timestamp DESC LIMIT 5")
    for r in cur.fetchall():
        print(f"[{r[0]}] {r[1][:500]}...")
except sqlite3.OperationalError:
    print("No observations table or error querying it.")
