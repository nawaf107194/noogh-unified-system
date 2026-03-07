import ast
from typing import List, Dict, Any

class CodeAnalyzer:
    def extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """
        Extract all imports from AST

        Args:
            tree: AST tree

        Returns:
            List of import info dictionaries
        """
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({"type": "import", "module": alias.name, "alias": alias.asname, "line": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                        }
                    )

        logger.info(f"Extracted {len(imports)} imports")
        return imports

# Import the actual class for testing
from neural_engine.specialized_systems.code_analyzer import CodeAnalyzer

def test_extract_imports_happy_path():
    code = """
import os
from math import sqrt as square_root
"""
    tree = ast.parse(code)
    analyzer = CodeAnalyzer()
    result = analyzer.extract_imports(tree)
    expected = [
        {"type": "import", "module": "os", "alias": None, "line": 2},
        {"type": "from_import", "module": "math", "name": "sqrt", "alias": "square_root", "line": 3}
    ]
    assert result == expected

def test_extract_imports_empty_tree():
    tree = ast.parse("")
    analyzer = CodeAnalyzer()
    result = analyzer.extract_imports(tree)
    assert result == []

def test_extract_imports_none_input():
    with pytest.raises(TypeError):
        analyzer = CodeAnalyzer()
        analyzer.extract_imports(None)

def test_extract_imports_syntax_error():
    code = "import invalid"
    tree = ast.parse(code)  # This should raise a SyntaxError
    analyzer = CodeAnalyzer()
    result = analyzer.extract_imports(tree)
    assert result == []

# To ensure the logger works as expected, we need to capture its output
from unittest.mock import patch
import logging

@pytest.mark.parametrize("code, expected", [
    ("import os\nfrom math import sqrt as square_root", [
        {"type": "import", "module": "os", "alias": None, "line": 2},
        {"type": "from_import", "module": "math", "name": "sqrt", "alias": "square_root", "line": 3}
    ]),
    ("", []),
    (None, []),
])
def test_extract_imports_with_logger(code, expected):
    tree = ast.parse(code) if code else None
    analyzer = CodeAnalyzer()
    with patch.object(logging.Logger, 'info') as mock_info:
        result = analyzer.extract_imports(tree)
        assert result == expected
        mock_info.assert_called_once_with(f"Extracted {len(result)} imports")