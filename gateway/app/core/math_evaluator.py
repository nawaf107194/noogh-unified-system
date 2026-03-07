"""
Math Evaluator - Deterministic Math Engine for NOOGH

This module handles math calculations DETERMINISTICALLY without LLM.
Prevents LLM from doing arithmetic (which it often gets wrong).
"""

import ast
import operator
import re
from typing import Optional, Tuple, Union

# Safe operators for math evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

# Math patterns to detect
MATH_PATTERNS = [
    # Arabic math keywords
    r'احسب\s+',
    r'كم\s+(ناتج|حاصل|يساوي)',
    r'ما\s+ناتج',
    r'اجمع\s+',
    r'اطرح\s+',
    r'اضرب\s+',
    r'اقسم\s+',
    r'متوسط\s+',
    r'مجموع\s+',
    # Pure arithmetic expression
    r'^[\d\s\+\-\*\/\×\÷\(\)\.\,\^]+$',
]

# Expression with numbers and operators
EXPRESSION_PATTERN = re.compile(r'[\d\.\,]+\s*[\+\-\*\/\×\÷\^]\s*[\d\.\,]+')


def is_math_query(query: str) -> bool:
    """Check if a query is primarily a math calculation."""
    query_clean = query.strip()
    
    # Check for pure arithmetic expression
    if EXPRESSION_PATTERN.search(query_clean):
        return True
    
    # Check for math keywords
    for pattern in MATH_PATTERNS:
        if re.search(pattern, query_clean, re.IGNORECASE | re.UNICODE):
            return True
    
    return False


def extract_math_expression(query: str) -> Optional[str]:
    """
    Extract a mathematical expression from a query.
    
    Examples:
        "احسب 15 × 7 + 23"     -> "15 * 7 + 23"
        "كم ناتج 100 ÷ 4 + 6"  -> "100 / 4 + 6"
        "5 + 3 = ?"            -> "5 + 3"
    """
    if not query.strip():
        return None

    # Normalize Arabic/Unicode operators to standard ones
    expr = query
    expr = expr.replace('×', '*')
    expr = expr.replace('÷', '/')
    expr = expr.replace('−', '-')  # Unicode minus
    expr = expr.replace('،', ',')  # Arabic comma
    expr = expr.replace(',', '')   # Remove commas from numbers
    
    # Remove Arabic words
    expr = re.sub(r'[أ-ي]+', '', expr)
    
    # Remove common question marks and equals
    expr = re.sub(r'[=؟?]', '', expr)
    
    # Keep only numbers, operators, parentheses, spaces
    expr = re.sub(r'[^\d\s\+\-\*\/\^\(\)\.]', '', expr)
    
    # Clean up whitespace
    expr = ' '.join(expr.split())
    
    return expr.strip() if expr.strip() else None


class SafeMathEvaluator(ast.NodeVisitor):
    """
    AST-based safe math evaluator.
    Only evaluates arithmetic expressions, no function calls or variables.
    """
    
    def visit_Constant(self, node: ast.Constant) -> Union[int, float]:
        """Handle numeric constants."""
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value}")
    
    # Python 3.7 compatibility
    def visit_Num(self, node: ast.Num) -> Union[int, float]:
        return node.n
    
    def visit_BinOp(self, node: ast.BinOp) -> Union[int, float]:
        """Handle binary operations (+, -, *, /, etc.)."""
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        
        op = SAFE_OPERATORS[op_type]
        
        # Check for division by zero
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("القسمة على صفر غير ممكنة")
        
        return op(left, right)
    
    def visit_UnaryOp(self, node: ast.UnaryOp) -> Union[int, float]:
        """Handle unary operations (+, -)."""
        operand = self.visit(node.operand)
        
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        
        return SAFE_OPERATORS[op_type](operand)
    
    def visit_Expression(self, node: ast.Expression) -> Union[int, float]:
        """Handle expression wrapper."""
        return self.visit(node.body)
    
    def generic_visit(self, node: ast.AST):
        """Block any other node types (function calls, names, etc.)."""
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def safe_eval_math(expression: str) -> Tuple[bool, Union[float, str]]:
    """
    Safely evaluate a mathematical expression.
    
    Args:
        expression: A math expression string like "15 * 7 + 23"
        
    Returns:
        Tuple of (success: bool, result: float or error_message: str)
    """
    if not expression or not expression.strip():
        return False, "تعبير فارغ"
    
    try:
        # Parse the expression into AST
        tree = ast.parse(expression, mode='eval')
        
        # Evaluate safely
        evaluator = SafeMathEvaluator()
        result = evaluator.visit(tree)
        
        # Format result nicely
        if isinstance(result, float):
            # Check if it's effectively an integer
            if result == int(result):
                result = int(result)
            else:
                # Round to reasonable precision
                result = round(result, 10)
        
        return True, result
        
    except ZeroDivisionError as e:
        return False, str(e)
    except SyntaxError:
        return False, "صيغة رياضية غير صحيحة"
    except ValueError as e:
        return False, f"خطأ في التقييم: {e}"
    except Exception as e:
        return False, f"خطأ غير متوقع: {e}"


def calculate_average(numbers: list) -> Tuple[bool, Union[float, str]]:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return False, "لا توجد أرقام"
    
    try:
        avg = sum(numbers) / len(numbers)
        return True, avg
    except Exception as e:
        return False, str(e)


def process_math_query(query: str) -> Optional[dict]:
    """
    Process a math query and return deterministic result.
    
    Returns None if query is not a math query.
    Returns dict with result if successfully computed.
    """
    if not is_math_query(query):
        return None
    
    # Extract expression
    expr = extract_math_expression(query)
    if not expr:
        return None
    
    # Check for average calculation
    if 'متوسط' in query or 'average' in query.lower():
        # Extract numbers
        numbers = [float(n) for n in re.findall(r'\d+(?:\.\d+)?', query)]
        if numbers:
            success, result = calculate_average(numbers)
            
            # Check for "multiply by" modifier
            multiply_match = re.search(r'(?:اضرب|×|ثم\s*اضرب).*?(\d+)', query)
            if multiply_match and success:
                multiplier = float(multiply_match.group(1))
                result = result * multiplier
            
            if success:
                return {
                    "success": True,
                    "expression": f"متوسط({', '.join(map(str, numbers))})",
                    "result": result,
                    "answer_ar": f"النتيجة هي {result}"
                }
    
    # Evaluate expression
    success, result = safe_eval_math(expr)
    
    if success:
        return {
            "success": True,
            "expression": expr,
            "result": result,
            "answer_ar": f"النتيجة هي {result}"
        }
    else:
        return {
            "success": False,
            "expression": expr,
            "error": result,
            "answer_ar": f"خطأ في الحساب: {result}"
        }


# Test cases
if __name__ == "__main__":
    test_queries = [
        "احسب 15 × 7 + 23",
        "كم ناتج 100 ÷ 4 + 6",
        "5 + 3",
        "متوسط 10، 20، 30، 40",
        "متوسط 10، 20، 30، 40 ثم اضرب في 3",
        "(15 × 7 + 23) ÷ 2",
    ]
    
    for q in test_queries:
        result = process_math_query(q)
        print(f"Query: {q}")
        print(f"Result: {result}")
        print()
