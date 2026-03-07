"""
CodeIndexer - Indexes all code elements for fast lookup
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CodeIndexer:
    """Indexes code elements for fast search"""

    def __init__(self):
        """Initialize CodeIndexer"""
        self.function_index = {}  # function_name -> [file_paths]
        self.class_index = {}  # class_name -> [file_paths]
        self.module_index = {}  # module_path -> analysis
        logger.info("CodeIndexer initialized")

    def index_file(self, file_path: str, analysis: Dict[str, Any]):
        """
        Index a file's analysis

        Args:
            file_path: Path to file
            analysis: Analysis from CodeAnalyzer
        """
        # Index functions
        for func in analysis.get("functions", []):
            func_name = func["name"]
            if func_name not in self.function_index:
                self.function_index[func_name] = []
            self.function_index[func_name].append({"file": file_path, "line": func["line"], "args": func["args"]})

        # Index classes
        for cls in analysis.get("classes", []):
            cls_name = cls["name"]
            if cls_name not in self.class_index:
                self.class_index[cls_name] = []
            self.class_index[cls_name].append({"file": file_path, "line": cls["line"], "methods": cls["methods"]})

        # Store full analysis
        self.module_index[file_path] = analysis

        logger.info(
            f"Indexed {file_path}: {len(analysis.get('functions', []))} functions, {len(analysis.get('classes', []))} classes"
        )

    def find_function(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Find all occurrences of a function

        Args:
            function_name: Name of function

        Returns:
            List of locations
        """
        return self.function_index.get(function_name, [])

    def find_class(self, class_name: str) -> List[Dict[str, Any]]:
        """
        Find all occurrences of a class

        Args:
            class_name: Name of class

        Returns:
            List of locations
        """
        return self.class_index.get(class_name, [])

    def get_module_analysis(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get full analysis for a module

        Args:
            file_path: Path to file

        Returns:
            Analysis dictionary or None
        """
        return self.module_index.get(file_path)

    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for a query in all indexed elements

        Args:
            query: Search query

        Returns:
            Dictionary with functions and classes matching query
        """
        results = {"functions": [], "classes": []}

        # Search functions
        for func_name, locations in self.function_index.items():
            if query.lower() in func_name.lower():
                results["functions"].extend(locations)

        # Search classes
        for class_name, locations in self.class_index.items():
            if query.lower() in class_name.lower():
                results["classes"].extend(locations)

        logger.info(f"Search '{query}': {len(results['functions'])} functions, {len(results['classes'])} classes")
        return results

    def get_stats(self) -> Dict[str, int]:
        """
        Get indexing statistics

        Returns:
            Dictionary with stats
        """
        return {
            "total_functions": len(self.function_index),
            "total_classes": len(self.class_index),
            "total_modules": len(self.module_index),
        }


if __name__ == "__main__":
    # Test CodeIndexer
    indexer = CodeIndexer()

    # Index a test file
    test_analysis = {
        "functions": [{"name": "test_func", "line": 10, "args": ["x", "y"]}],
        "classes": [{"name": "TestClass", "line": 20, "methods": ["method1"]}],
    }

    indexer.index_file("test.py", test_analysis)

    print(f"Stats: {indexer.get_stats()}")
    print(f"Find test_func: {indexer.find_function('test_func')}")
