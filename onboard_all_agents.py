import os
import json
import re
from pathlib import Path

# Paths
root_dir = Path("/home/noogh/projects/noogh_unified_system/src")
agents_dir = root_dir / "agents"
registry_path = agents_dir / "agent_registry.json"

# Load current registry
if registry_path.exists():
    with open(registry_path, "r") as f:
        registry = json.load(f)
else:
    registry = []

# Tracker for uniqueness
registered_files = {str(Path(entry["file"]).resolve()) for entry in registry if "file" in entry}
roles = {entry.get("role") for entry in registry if "role" in entry}

# Agent class regex
agent_class_regex = re.compile(r"class\s+([A-Za-z0-9_]+Agent[A-Za-z0-9_]*)\s*[:\(]")

new_count = 0
# Scan src recursively except venvs and node_modules
exclude_dirs = {".venv", "node_modules", "__pycache__", ".git", "training", ".noogh_venv"}

for root, dirs, files in os.walk(root_dir):
    # Prune exclude dirs
    dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
    
    for file_name in files:
        if not file_name.endswith(".py") or file_name == "__init__.py":
            continue
            
        file_path = Path(root) / file_name
        abs_path = str(file_path.resolve())
        
        if abs_path in registered_files:
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            match = agent_class_regex.search(content)
            if match:
                class_name = match.group(1)
                role = file_path.stem
                
                # Deduplicate role
                base_role = role
                counter = 1
                while role in roles:
                    role = f"{base_role}_{counter}"
                    counter += 1
                
                entry = {
                    "name": class_name,
                    "role": role,
                    "file": abs_path,
                    "capabilities": ["AUTO_DISCOVERED"],
                    "created_at": os.path.getctime(file_path),
                    "validation": {"valid": True, "violations": []}
                }
                registry.append(entry)
                registered_files.add(abs_path)
                roles.add(role)
                new_count += 1
                print(f"Registered: {class_name} in {file_path.relative_to(root_dir)}")
        except Exception as e:
            print(f"Error scanning {file_name}: {e}")

if new_count > 0:
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=4)
    print(f"\nSUCCESS: Added {new_count} new agents. Total agents in registry: {len(registry)}")
else:
    print("\nNo new agents found.")
