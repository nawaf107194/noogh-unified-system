import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("unified_core.core.spatial_specialist")

class SpatialSpecialist:
    """
    Scans and maps the physical project environment to expand the agent's self-awareness.
    Discovers directory purposes, key files, and structural hierarchies.
    """
    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.spatial_map = {}
        logger.info(f"SpatialSpecialist initialized for root: {self.root_path}")

    async def generate_map(self) -> Dict[str, Any]:
        """
        Recursively scans the project structure and produces a semantic map.
        """
        logger.info("🗺️ Generating Spatial Map...")
        nodes = []
        
        try:
            # We limit depth to avoid excessive scanning
            for entry in os.scandir(self.root_path):
                try:
                    if entry.name.startswith('.'):
                        continue
                    
                    node = {
                        "name": entry.name,
                        "type": "directory" if entry.is_dir() else "file",
                        "path": str(Path(entry.path).relative_to(self.root_path)),
                        "description": await self._infer_purpose(entry)
                    }
                    nodes.append(node)
                except (PermissionError, OSError) as e:
                    logger.warning(f"Skipping inaccessible entry {entry.name}: {e}")
                    continue
                
            self.spatial_map = {
                "root": str(self.root_path),
                "nodes": nodes,
                "discovery_time": os.path.getmtime(self.root_path)
            }
            logger.info(f"Spatial Map generated with {len(nodes)} root-level nodes.")
            return self.spatial_map
            
        except Exception as e:
            logger.error(f"Spatial mapping failed: {e}")
            return {"error": str(e)}

    async def _infer_purpose(self, entry: os.DirEntry) -> str:
        """
        Attempts to infer the purpose of a directory or file.
        """
        if not entry.is_dir():
            if entry.name == "README.md": return "Project documentation"
            if entry.name == "Dockerfile": return "Containerization definition"
            if entry.name == "requirements.txt": return "Python dependencies"
            return "Unknown file"

        # Directory heuristics
        name = entry.name.lower()
        if name == "src": return "Source code root"
        if name == "data": return "Persistent data storage"
        if name == "logs": return "System logs and traces"
        if name == "tests": return "Unit and integration tests"
        if name == "scripts": return "Automation and utility scripts"
        if name == "backups": return "System and data backups"
        if name == "docs": return "Project documentation"
        if "trained_model" in name: return "ML model artifacts"
        
        # Check for README in directory
        readme_path = Path(entry.path) / "README.md"
        if readme_path.exists():
            try:
                content = readme_path.read_text().split('\n')[0].strip('# ')
                return f"Documentation: {content}"
            except:
                pass
                
        return "Unknown directory"

    def get_spatial_belief_propositions(self) -> List[str]:
        """
        Generates logic-ready propositions for the WorldModel.
        """
        if not self.spatial_map:
            return []
            
        propositions = [
            f"My physical root is located at {self.spatial_map['root']}",
            f"I have awareness of {len(self.spatial_map['nodes'])} top-level components"
        ]
        
        for node in self.spatial_map['nodes']:
            propositions.append(f"Directory '{node['name']}' serves as: {node['description']}")
            
        return propositions
