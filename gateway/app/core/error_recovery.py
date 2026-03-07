"""
Error Recovery System for Noogh Agent.
Parses Python execution errors and suggests fixes.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from gateway.app.core.logging import get_logger

logger = get_logger("error_recovery")


@dataclass
class ParsedError:
    """Parsed Python error information"""

    error_type: str
    message: str
    line_number: Optional[int] = None
    context: Optional[str] = None
    original: str = ""


class ErrorParser:
    """
    Parse Python execution errors and suggest fixes.
    """

    # Common error patterns and fixes
    ERROR_PATTERNS = {
        "NameError": {
            "pattern": r"name '(\w+)' is not defined",
            "fixes": [
                "Import the module: import {var}",
                "Define the variable before using it",
                "Check for typos in variable name",
            ],
        },
        "FileNotFoundError": {
            "pattern": r"\[Errno 2\] No such file or directory: '([^']+)'",
            "fixes": [
                "Check if file exists with os.path.exists('{file}')",
                "Use correct file path - check with list_files",
                "Create the file first if needed",
            ],
        },
        "TypeError": {
            "pattern": r"unsupported operand type.*: '(\w+)' and '(\w+)'",
            "fixes": [
                "Convert types before operation",
                "Check types with isinstance()",
                "Filter invalid types from data",
            ],
        },
        "AttributeError": {
            "pattern": r"'(\w+)' object has no attribute '(\w+)'",
            "fixes": [
                "Check object type before accessing attribute",
                "Use hasattr() to verify attribute exists",
                "Inspect object with dir() or type()",
            ],
        },
        "KeyError": {
            "pattern": r"'(\w+)'",
            "fixes": [
                "Use .get() method with default value",
                "Check if key exists with 'key in dict'",
                "Inspect dict.keys() first",
            ],
        },
        "IndexError": {
            "pattern": r"list index out of range",
            "fixes": [
                "Check list length before accessing",
                "Use try/except or if len(list) > index",
                "Iterate with for item in list instead",
            ],
        },
        "ValueError": {
            "pattern": r"invalid literal for (\w+)\(\) with base",
            "fixes": [
                "Validate input before conversion",
                "Use try/except to handle invalid values",
                "Filter non-numeric values first",
            ],
        },
        "ZeroDivisionError": {
            "pattern": r"division by zero",
            "fixes": [
                "Check if denominator is zero before division",
                "Use if divisor != 0 guard",
                "Handle edge case separately",
            ],
        },
    }

    def parse(self, error_output: str) -> ParsedError:
        """
        Parse error output and extract structured information.

        Args:
            error_output: Raw error output from code execution

        Returns:
            ParsedError with extracted information
        """
        # Extract error type (last line usually)
        lines = error_output.strip().split("\n")
        error_line = lines[-1] if lines else error_output

        # Match error type
        error_type_match = re.match(r"(\w+Error|\w+Exception):", error_line)
        error_type = error_type_match.group(1) if error_type_match else "Unknown"

        # Extract message
        message = error_line
        if ":" in error_line:
            message = error_line.split(":", 1)[1].strip()

        # Try to extract line number
        line_number = None
        for line in lines:
            line_match = re.search(r"line (\d+)", line)
            if line_match:
                line_number = int(line_match.group(1))
                break

        # Get context (few lines before error if available)
        context = None
        if len(lines) > 1:
            context = "\n".join(lines[-3:-1])

        return ParsedError(
            error_type=error_type, message=message, line_number=line_number, context=context, original=error_output
        )

    def suggest_fixes(self, parsed_error: ParsedError) -> List[str]:
        """
        Suggest fixes based on error type and pattern.
        """
        error_type = parsed_error.error_type

        # Check for unrecoverable markers
        unrecoverable_markers = ["not authorized", "blocked", "forbidden", "unavailable", "deprecated"]
        if any(marker in parsed_error.message.lower() for marker in unrecoverable_markers):
            return ["This operation is unrecoverable. Use UNSUPPORTED block to report this."]

        # Get pattern-specific fixes
        if error_type in self.ERROR_PATTERNS:
            pattern_info = self.ERROR_PATTERNS[error_type]
            fixes = pattern_info["fixes"].copy()

            # Try to customize fixes with extracted info
            pattern = pattern_info["pattern"]
            match = re.search(pattern, parsed_error.message)

            if match:
                # Substitute placeholders in fixes
                for i, fix in enumerate(fixes):
                    if error_type == "NameError" and "{var}" in fix:
                        fixes[i] = fix.format(var=match.group(1))
                    elif error_type == "FileNotFoundError" and "{file}" in fix:
                        fixes[i] = fix.format(file=match.group(1))

            return fixes

        # Generic fixes for unknown errors
        return [
            "Read error message carefully",
            "Check syntax and indentation",
            "Break problem into smaller steps",
            "Print intermediate values to debug",
        ]

    def generate_fix_code(self, original_code: str, parsed_error: ParsedError) -> Optional[str]:
        """
        Generate fixed code based on error (simple heuristics).

        Args:
            original_code: Original failing code
            parsed_error: Parsed error

        Returns:
            Suggested fixed code or None
        """
        error_type = parsed_error.error_type

        # Simple fix patterns
        if error_type == "NameError":
            # Try to add  common import
            match = re.search(r"name '(\w+)' is not defined", parsed_error.message)
            if match:
                var = match.group(1)
                common_imports = {
                    "os": "import os",
                    "sys": "import sys",
                    "json": "import json",
                    "math": "import math",
                    "re": "import re",
                    "datetime": "from datetime import datetime",
                }
                if var in common_imports:
                    return f"{common_imports[var]}\n{original_code}"

        elif error_type == "FileNotFoundError":
            # Add file existence check
            match = re.search(r"No such file or directory: '([^']+)'", parsed_error.message)
            if match:
                filename = match.group(1)
                return f"""import os
if os.path.exists('{filename}'):
{self._indent_code(original_code)}
else:
    print(f"Error: File '{filename}' not found")
    # List available files:
    print(os.listdir('.'))
"""

        # No automatic fix available
        return None

    def _indent_code(self, code: str, spaces: int = 4) -> str:
        """Add indentation to code"""
        indent = " " * spaces
        return "\n".join(indent + line for line in code.split("\n"))

    def format_error_report(self, parsed_error: ParsedError, fixes: List[str]) -> str:
        """
        Format error report with suggestions.

        Args:
            parsed_error: Parsed error
            fixes: List of suggested fixes

        Returns:
            Formatted report
        """
        report = f"""ERROR ANALYSIS:
Type: {parsed_error.error_type}
Message: {parsed_error.message}
"""

        if parsed_error.line_number:
            report += f"Line: {parsed_error.line_number}\n"

        report += "\nSUGGESTED FIXES:\n"
        for i, fix in enumerate(fixes, 1):
            report += f"{i}. {fix}\n"

        return report


# Global instance
error_parser = ErrorParser()
