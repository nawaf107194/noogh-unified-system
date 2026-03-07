#!/usr/bin/env python3
"""
NOOGH Student Model Evaluation
=================================
Evaluates the 7B Student model after distillation training.

Tests:
1. Code quality — can it write clean Python?
2. Refactoring — can it fix code issues?
3. Agent design — can it design agents like the Teacher?
4. Reasoning — can it explain its decisions?

Compares scores before/after training to measure improvement.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("eval_student")

DATA_DIR = Path(__file__).parent / "data"
EVAL_DIR = DATA_DIR / "evaluations"


# ============================================================
# Evaluation Benchmarks
# ============================================================

EVAL_PROMPTS = [
    # 1. Code Quality
    {
        "category": "code_quality",
        "prompt": "Write a Python function that validates an email address using regex. Handle edge cases.",
        "criteria": ["has_function_def", "has_regex", "has_docstring", "handles_edge_cases"],
    },
    # 2. Refactoring
    {
        "category": "refactoring",
        "prompt": """Refactor this function to reduce complexity:
def process(data):
    result = []
    for item in data:
        if item is not None:
            if isinstance(item, dict):
                if 'value' in item:
                    if item['value'] > 0:
                        result.append(item['value'])
    return result""",
        "criteria": ["reduced_nesting", "uses_comprehension_or_filter", "preserves_logic"],
    },
    # 3. Agent Design
    {
        "category": "agent_design",
        "prompt": """Design a Python monitoring agent for the NOOGH system.
Agent: DiskMonitorAgent
Role: disk_monitor
Purpose: Monitor disk usage and alert when space is low
Capabilities: CHECK_DISK, PREDICT_FULL

The agent must:
1. Inherit from AgentWorker
2. __init__ must call super().__init__(role, custom_handlers)
3. Each handler is async: async def _handler(self, task: Dict) -> Dict

Output JSON with handlers array.""",
        "criteria": ["valid_json", "has_handlers", "follows_contract"],
    },
    # 4. Bug Detection
    {
        "category": "bug_detection",
        "prompt": """Find the bug in this code:
def get_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)""",
        "criteria": ["identifies_division_by_zero", "suggests_fix"],
    },
    # 5. Architecture
    {
        "category": "architecture",
        "prompt": "Explain the publish-subscribe pattern and when to use it vs direct function calls. Keep it under 100 words.",
        "criteria": ["mentions_decoupling", "mentions_async", "concise"],
    },
]


def _score_response(response: str, criteria: List[str]) -> Dict[str, Any]:
    """Score a response against criteria."""
    scores = {}
    response_lower = response.lower()
    
    # Code quality criteria
    if "has_function_def" in criteria:
        scores["has_function_def"] = "def " in response
    if "has_regex" in criteria:
        scores["has_regex"] = "re." in response or "import re" in response
    if "has_docstring" in criteria:
        scores["has_docstring"] = '"""' in response or "'''" in response
    if "handles_edge_cases" in criteria:
        scores["handles_edge_cases"] = any(w in response_lower for w in ["none", "empty", "invalid", "error", "except"])
    
    # Refactoring criteria
    if "reduced_nesting" in criteria:
        # Count 'if' statements — should be fewer
        scores["reduced_nesting"] = response.count("    if") < 4
    if "uses_comprehension_or_filter" in criteria:
        scores["uses_comprehension_or_filter"] = any(w in response for w in ["for", "filter", "comprehension", "["])
    if "preserves_logic" in criteria:
        scores["preserves_logic"] = "result" in response or "return" in response
    
    # Agent design criteria
    if "valid_json" in criteria:
        try:
            # Try to find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json.loads(response[start:end])
                scores["valid_json"] = True
            else:
                scores["valid_json"] = False
        except (json.JSONDecodeError, ValueError):
            scores["valid_json"] = False
    if "has_handlers" in criteria:
        scores["has_handlers"] = "handler" in response_lower or "_check" in response or "_monitor" in response
    if "follows_contract" in criteria:
        scores["follows_contract"] = "AgentWorker" in response or "super().__init__" in response
    
    # Bug detection criteria
    if "identifies_division_by_zero" in criteria:
        scores["identifies_division_by_zero"] = any(w in response_lower for w in ["division by zero", "empty", "len(numbers) == 0", "zerodivision"])
    if "suggests_fix" in criteria:
        scores["suggests_fix"] = "if " in response or "not numbers" in response or "len(" in response
    
    # Architecture criteria
    if "mentions_decoupling" in criteria:
        scores["mentions_decoupling"] = any(w in response_lower for w in ["decoupl", "loose", "independent", "separate"])
    if "mentions_async" in criteria:
        scores["mentions_async"] = any(w in response_lower for w in ["async", "event", "message", "subscriber", "observer"])
    if "concise" in criteria:
        scores["concise"] = len(response.split()) < 150
    
    # Calculate overall score
    passed = sum(1 for v in scores.values() if v)
    total = len(scores)
    
    return {
        "criteria_scores": scores,
        "passed": passed,
        "total": total,
        "score": round(passed / total, 2) if total > 0 else 0,
    }


def evaluate_model(model_url: str = None, model_mode: str = "local") -> Dict[str, Any]:
    """
    Run evaluation suite against the Student model.
    
    Args:
        model_url: URL of the model API
        model_mode: "local" or "api"
    
    Returns:
        Evaluation results with per-category and overall scores
    """
    import os
    
    if model_url is None:
        model_url = os.getenv("NEURAL_ENGINE_URL", "http://localhost:8080")
    if model_mode is None:
        model_mode = os.getenv("NEURAL_ENGINE_MODE", "local")
    
    # Use the neural client
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from unified_core.neural_bridge import NeuralEngineClient
        client = NeuralEngineClient(base_url=model_url, mode=model_mode)
    except Exception as e:
        logger.error(f"Cannot create client: {e}")
        return {"error": str(e)}
    
    results = {
        "model_url": model_url,
        "model_mode": model_mode,
        "timestamp": time.time(),
        "eval_prompts": len(EVAL_PROMPTS),
        "categories": {},
        "responses": [],
    }
    
    total_score = 0
    
    for ep in EVAL_PROMPTS:
        category = ep["category"]
        prompt = ep["prompt"]
        criteria = ep["criteria"]
        
        logger.info(f"📝 Evaluating: {category}")
        
        messages = [
            {"role": "system", "content": "You are an expert Python engineer. Be concise and precise."},
            {"role": "user", "content": prompt},
        ]
        
        try:
            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                client.complete(messages, max_tokens=1024)
            )
            
            if result.get("success") and result.get("content"):
                response = result["content"]
                score_result = _score_response(response, criteria)
                
                results["categories"][category] = {
                    "score": score_result["score"],
                    "passed": score_result["passed"],
                    "total": score_result["total"],
                    "details": score_result["criteria_scores"],
                }
                results["responses"].append({
                    "category": category,
                    "response_preview": response[:300],
                })
                
                total_score += score_result["score"]
                logger.info(f"  {category}: {score_result['score']:.0%} ({score_result['passed']}/{score_result['total']})")
            else:
                results["categories"][category] = {"score": 0, "error": "No response"}
                logger.warning(f"  {category}: No response from model")
                
        except Exception as e:
            results["categories"][category] = {"score": 0, "error": str(e)}
            logger.error(f"  {category}: Error — {e}")
    
    # Overall score
    n_categories = len(results["categories"])
    results["overall_score"] = round(total_score / n_categories, 2) if n_categories > 0 else 0
    
    # Save results
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    eval_file = EVAL_DIR / f"eval_{int(time.time())}.json"
    with open(eval_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📊 Overall score: {results['overall_score']:.0%}")
    logger.info(f"💾 Results saved: {eval_file}")
    
    return results


def compare_evaluations() -> Dict[str, Any]:
    """
    Compare the two most recent evaluations.
    Shows improvement/regression per category.
    """
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    eval_files = sorted(EVAL_DIR.glob("eval_*.json"))
    
    if len(eval_files) < 2:
        return {"error": f"Need at least 2 evaluations, found {len(eval_files)}"}
    
    with open(eval_files[-2]) as f:
        before = json.load(f)
    with open(eval_files[-1]) as f:
        after = json.load(f)
    
    comparison = {
        "before_timestamp": before.get("timestamp"),
        "after_timestamp": after.get("timestamp"),
        "before_score": before.get("overall_score", 0),
        "after_score": after.get("overall_score", 0),
        "improvement": round(after.get("overall_score", 0) - before.get("overall_score", 0), 2),
        "categories": {},
    }
    
    for cat in set(list(before.get("categories", {})) + list(after.get("categories", {}))):
        b_score = before.get("categories", {}).get(cat, {}).get("score", 0)
        a_score = after.get("categories", {}).get(cat, {}).get("score", 0)
        delta = round(a_score - b_score, 2)
        comparison["categories"][cat] = {
            "before": b_score,
            "after": a_score,
            "delta": delta,
            "status": "📈" if delta > 0 else ("📉" if delta < 0 else "—"),
        }
    
    return comparison


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NOOGH Student Model Evaluation")
    parser.add_argument("--compare", action="store_true", help="Compare last two evaluations")
    parser.add_argument("--url", type=str, default=None, help="Model API URL")
    parser.add_argument("--mode", type=str, default="local", help="Model mode (local/api)")
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.compare:
        result = compare_evaluations()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        result = evaluate_model(model_url=args.url, model_mode=args.mode)
        
        print(f"\n{'='*50}")
        print(f"📊 Student Model Evaluation")
        print(f"{'='*50}")
        for cat, data in result.get("categories", {}).items():
            score = data.get("score", 0)
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            print(f"  {cat:20s} [{bar}] {score:.0%}")
        print(f"{'='*50}")
        print(f"  Overall: {result.get('overall_score', 0):.0%}")
        print(f"{'='*50}")
