import os
import json
import importlib.util
from pathlib import Path

agents_dir = Path("/home/noogh/projects/noogh_unified_system/src/agents")
registry_path = agents_dir / "agent_registry.json"

if registry_path.exists():
    with open(registry_path, "r") as f:
        registry = json.load(f)
else:
    registry = []

registered_files = {Path(entry["file"]).resolve() for entry in registry if "file" in entry}
new_entries = []

for file_name in os.listdir(agents_dir):
    if not file_name.endswith(".py") or file_name == "__init__.py":
        continue
    
    file_path = agents_dir / file_name
    if file_path.resolve() in registered_files:
        continue

    try:
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        agent_class = None
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if isinstance(obj, type) and attr_name.endswith("Agent") and attr_name != "AgentWorker":
                agent_class = obj
                break

        if agent_class:
            role = getattr(agent_class, "role", module_name)
            # Default capabilities if not specified
            capabilities = ["UNKNOWN_CAPABILITY"]
            
            entry = {
                "name": agent_class.__name__,
                "role": role,
                "file": str(file_path.resolve()),
                "capabilities": capabilities,
                "reason": "Auto-discovered by register_agents.py",
                "created_at": os.path.getctime(file_path),
                "validation": {"valid": True, "violations": []}
            }
            new_entries.append(entry)
            print(f"Discovered: {agent_class.__name__}")
    except Exception as e:
        print(f"Failed to load {file_name}: {e}")

if new_entries:
    registry.extend(new_entries)
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=4)
    print(f"Added {len(new_entries)} new agents to the registry.")
else:
    print("No new agents found.")
