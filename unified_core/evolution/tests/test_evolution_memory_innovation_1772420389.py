import os
from typing import List, Dict, Any

class EvolutionMemory:
    def __init__(self):
        self._outcomes = [
            {"target_area": "dir1/file.py", "success": True},
            {"target_area": "dir2/file.py", "success": False},
            {"target_area": "dir1/other_file.py", "success": True},
            {"target_area": "dir3/file.py", "success": True}
        ]

    def suggest_similar_targets(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Suggest files similar to those with successful improvements.
        
        v5.0: Finds directories/modules where improvements have worked before
        and suggests other files in the same areas that haven't been touched.
        
        Returns:
            List of dicts with {"directory", "successful_count", "untouched_files"}
        """
        # Find directories with successful outcomes
        successful_dirs: Dict[str, int] = {}
        touched_files: set = set()
        
        for o in self._outcomes:
            if o.success and o.target_area:
                touched_files.add(o.target_area)
                dir_path = os.path.dirname(o.target_area)
                if dir_path:
                    successful_dirs[dir_path] = successful_dirs.get(dir_path, 0) + 1
        
        if not successful_dirs:
            return []
        
        # For top successful directories, find untouched .py files
        suggestions = []
        for dir_path, count in sorted(successful_dirs.items(), key=lambda x: x[1], reverse=True):
            if not os.path.isdir(dir_path):
                continue
            
            try:
                untouched = []
                for f in os.listdir(dir_path):
                    if f.endswith('.py') and not f.startswith('_'):
                        fpath = os.path.join(dir_path, f)
                        if fpath not in touched_files:
                            untouched.append(f)
                
                if untouched:
                    suggestions.append({
                        "directory": dir_path,
                        "successful_count": count,
                        "untouched_files": untouched[:5]  # Cap per directory
                    })
            except OSError:
                continue
        
        return suggestions[:limit]

def test_suggest_similar_targets_happy_path():
    memory = EvolutionMemory()
    result = memory.suggest_similar_targets(limit=3)
    assert len(result) == 2
    assert result[0] == {
        "directory": "dir1",
        "successful_count": 2,
        "untouched_files": ["other_file.py"]
    }
    assert result[1] == {
        "directory": "dir3",
        "successful_count": 1,
        "untouched_files": []
    }

def test_suggest_similar_targets_empty_outcomes():
    memory = EvolutionMemory()
    memory._outcomes = []
    result = memory.suggest_similar_targets(limit=3)
    assert result == []

def test_suggest_similar_targets_limit_zero():
    memory = EvolutionMemory()
    result = memory.suggest_similar_targets(limit=0)
    assert result == []

def test_suggest_similar_targets_directory_not_found():
    memory = EvolutionMemory()
    memory._outcomes = [{"target_area": "nonexistent_dir/file.py", "success": True}]
    result = memory.suggest_similar_targets(limit=3)
    assert result == []