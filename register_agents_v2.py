import os
import json
import re
from pathlib import Path

agents_dir = Path("/home/noogh/projects/noogh_unified_system/src/agents")
registry_path = agents_dir / "agent_registry.json"

if registry_path.exists():
    with open(registry_path, "r") as f:
        registry = json.load(f)
else:
    registry = []

registered_files = {str(Path(entry["file"]).resolve()) for entry in registry if "file" in entry}
new_entries = []

agent_class_regex = re.compile(r"^class\s+([A-Za-z0-9_]+Agent[A-Za-z0-9_]*)\s*[:\(]")

for file_name in os.listdir(agents_dir):
    if not file_name.endswith(".py") or file_name == "__init__.py":
        continue
    
    file_path = agents_dir / file_name
    abs_path = str(file_path.resolve())
    
    if abs_path in registered_files:
        continue

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Find class name via regex (fast)
        match = agent_class_regex.search(content)
        if not match:
            # Try a looser match if first fails
            match = re.search(r"class\s+([A-Za-z0-9_]+)\s*\(.*Agent.*\)\s*:", content)
            
        if match:
            class_name = match.group(1)
            role = file_path.stem
            
            entry = {
                "name": class_name,
                "role": role,
                "file": abs_path,
                "capabilities": ["AUTO_DISCOVERED"],
                "reason": "Faster discovery via register_agents_v2.py",
                "created_at": os.path.getctime(file_path),
                "validation": {"valid": True, "violations": []}
            }
            new_entries.append(entry)
            print(f"Discovered: {class_name} in {file_name}")
    except Exception as e:
        print(f"Failed to scan {file_name}: {e}")

if new_entries:
    registry.extend(new_entries)
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=4)
    print(f"SUCCESS: Added {len(new_entries)} new agents to the registry. Total agents: {len(registry)}")
else:
    print("No new agents found.")
