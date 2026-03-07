"""
Constrained ReAct Loop for NOOGH (HYBRID ANALYTICAL v4.0)
Role: Senior Security Architect

Fixed: Arabic question mark support in SafeMath.
Enhanced: Deep analytical parsing.
"""

import os
import asyncio
import logging
import json
import re
import ast
import operator
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger("react_loop")

@dataclass
class ReActResult:
    answer: str
    confidence: float = 1.0
    iterations: int = 1
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    reasoning_trace: List[str] = field(default_factory=list)
    raw_response: str = ""

class SafeMathEvaluator:
    @classmethod
    def evaluate(cls, expression: str):
        import math as _math
        ops = {
            ast.Add: operator.add, 
            ast.Sub: operator.sub, 
            ast.Mult: operator.mul, 
            ast.Div: operator.truediv,
            ast.Pow: operator.pow
        }
        try:
            # 1. Arabic & Punctuation Cleanup
            expr = expression.replace('؟', '').replace('?', '').replace(',', '')
            expr = expr.replace('×', '*').replace('÷', '/').replace('x', '*')
            
            # 2. Handle sqrt/√ symbols
            expr = re.sub(r'√\s*(\d+\.?\d*)', r'sqrt(\1)', expr)
            
            # 3. Extract only math parts
            expr = re.sub(r'[^0-9\+\-\*\/\^\.\(\)sqrtSQRT]', '', expr)
            
            if not expr.strip():
                return "No mathematical expression found"

            # 4. Replace sqrt() calls with actual math
            expr = re.sub(r'sqrt\((\d+\.?\d*)\)', lambda m: str(_math.sqrt(float(m.group(1)))), expr)

            tree = ast.parse(expr.strip(), mode='eval')
            def _eval(node):
                if isinstance(node, ast.Constant): 
                    return node.value
                elif isinstance(node, ast.BinOp): 
                    return ops[type(node.op)](_eval(node.left), _eval(node.right))
                elif isinstance(node, ast.UnaryOp):
                    return ops[type(node.op)](_eval(node.operand)) if type(node.op) in ops else _eval(node.operand)
                raise ValueError("Operation not allowed")
            return _eval(tree.body)
        except Exception as e:
            logger.error(f"SafeMath Error: {e} | Original: {expression}")
            return f"Error: {e}"

class ReActLoop:
    def __init__(self, reasoning_engine=None):
        self.reasoning_engine = reasoning_engine

    async def run(self, query: str, context: Optional[Dict] = None, pre_fill: str = "") -> ReActResult:
        logger.info(f"🧠 Processing Query: {query[:100]}")
        
        # 1. OPTIMIZED MATH PATH
        # Only use SafeMath for PURE math queries (no Arabic/text mixed in)
        # This prevents hijacking questions like "ما الجذر التربيعي لـ 144 + 25"
        stripped = re.sub(r'[\s؟?,،]', '', query)
        is_pure_math = bool(re.fullmatch(r'[\d\+\-\*\/×÷\^\.\(\)√]+', stripped))
        if not pre_fill and is_pure_math:
            res = SafeMathEvaluator.evaluate(query)
            if not str(res).startswith("Error") and not str(res).startswith("No"):
                return ReActResult(answer=f"النتيجة: {res}", reasoning_trace=["Fast-Path: SafeMathEvaluator"])

        # 2. DEEP REASONING PATH (LLM)
        if self.reasoning_engine:
            try:
                ctx = context or {}
                result = await self.reasoning_engine.reason(context=ctx, query=query, pre_fill=pre_fill)
                
                answer = result.conclusion if hasattr(result, 'conclusion') else str(result)
                tool_calls = getattr(result, 'tool_calls', [])
                
                # 3. PROSE TOOL CALL FALLBACK
                # If the model described a tool call in prose instead of JSON,
                # extract and execute it. This handles the 7B model's tendency
                # to say "سأقوم بتنفيذ الأمر ls..." instead of {"tool":"sys.execute",...}
                if not tool_calls:
                    prose_result = await self._extract_and_run_prose_tool(answer, query, ctx)
                    if prose_result:
                        return prose_result
                
                # Cleanup answer from any potential leak of system instructions
                answer = re.sub(r'<\|im_.*?\|>', '', answer)
                
                return ReActResult(
                    answer=answer,
                    confidence=getattr(result, 'confidence', 1.0),
                    iterations=getattr(result, 'iterations', 1),
                    tool_calls=tool_calls,
                    reasoning_trace=getattr(result, 'reasoning_trace', ["Neural Logic Process"]),
                    raw_response=getattr(result, 'raw_response', "") or ""
                )
            except Exception as e:
                logger.error(f"Reasoning Engine Failure: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return ReActResult(answer=f"عذراً، حدث خطأ أثناء التحليل: {e}", confidence=0.0)

        return ReActResult(answer="أنا NOOGH، مساعدك الذكي. كيف يمكنني خدمتك؟")

    async def _extract_and_run_prose_tool(self, answer: str, query: str, context: dict) -> Optional[ReActResult]:
        """
        Fallback: Extract tool intent from Arabic prose and execute it.
        Catches patterns like:
          - سأقوم بتنفيذ الأمر "ls -la /path"
          - سأنفذ الأمر cat /path  
          - سأقوم بعرض محتويات المجلد
        """
        import subprocess
        
        # Pattern 1: Model mentions a command to execute in quotes or after الأمر
        cmd_match = re.search(
            r'(?:سأقوم\s+بتنفيذ|سأنفذ|تنفيذ)\s+(?:الأمر\s*)?["\']?([a-zA-Z][\w\s\-\./|\'*]+)',
            answer
        )
        
        # Pattern 2: Direct command reference like "cat /path" or "ls -la /path"
        if not cmd_match:
            cmd_match = re.search(
                r'(?:الأمر|command)\s*[:\s"\']*([a-zA-Z][\w\s\-\./|\'*]+)',
                answer
            )
        
        if not cmd_match:
            # Pattern 3: Check if the original query is a directory listing request
            dir_match = re.search(
                r'(?:محتويات|اعرض|عرض)\s+(?:المجلد|المسار|الدليل)\s*[:\s]*(\/[\w\-\.\/]+)',
                query
            )
            if dir_match:
                cmd = f"ls -la {dir_match.group(1)}"
            else:
                return None
        else:
            cmd = cmd_match.group(1).strip().rstrip('"\'')
        
        # Safety: only allow read-only commands
        cmd_base = cmd.split()[0] if cmd.split() else ""
        safe_commands = {"ls", "cat", "head", "tail", "wc", "find", "df", "du", "uname", "hostname", "whoami", "date", "uptime", "free", "pwd", "echo", "file", "stat"}
        if cmd_base not in safe_commands:
            logger.warning(f"⚠️ Prose fallback: Command '{cmd_base}' not in safe list, skipping")
            return None
        
        logger.info(f"🔧 Prose fallback: Executing extracted command: {cmd}")
        
        try:
            import shlex
            # SECURITY FIX (HIGH-05): shell=False prevents command injection
            proc = subprocess.run(
                shlex.split(cmd), shell=False, capture_output=True, text=True, timeout=10,
                cwd="/home/noogh/projects/noogh_unified_system/src"
            )
            output = proc.stdout.strip() or proc.stderr.strip() or "(لا يوجد مخرجات)"
            if len(output) > 2000:
                output = output[:2000] + "\n... [مقتطع]"
            
            return ReActResult(
                answer=output,
                confidence=1.0,
                iterations=1,
                tool_calls=[{"tool": "sys.execute", "args": {"command": cmd}}],
                reasoning_trace=["Prose-Fallback: Extracted command from Arabic prose"]
            )
        except subprocess.TimeoutExpired:
            return ReActResult(answer="⚠️ انتهت مهلة تنفيذ الأمر (10 ثوانٍ)", confidence=0.5)
        except Exception as e:
            logger.error(f"Prose fallback execution error: {e}")
            return None

_instance = None
def get_react_loop(reasoning_engine=None):
    global _instance
    if reasoning_engine: _instance = ReActLoop(reasoning_engine)
    elif _instance is None:
        try:
            from neural_engine.reasoning_engine import ReasoningEngine
            _instance = ReActLoop(ReasoningEngine(backend="auto"))
        except Exception as e:
            logger.error(f"Failed to auto-init ReasoningEngine: {e}")
            _instance = ReActLoop(None)
    return _instance
