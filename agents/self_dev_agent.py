"""
Self Development Agent - NOOGH
==============================
يراقب أداء النظام ويقترح تحسينات تلقائية على الكود.
يعمل بشكل دوري ويسجل ملاحظاته في knowledge base.
"""
import os
import ast
import json
import time
import logging
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent

logger = logging.getLogger("SelfDevAgent")

# ─── Config ──────────────────────────────────────────────────────────────────
AGENTS_DIR = Path(__file__).parent
REPORTS_DIR = AGENTS_DIR.parent / "data" / "dev_reports"
KNOWLEDGE_FILE = AGENTS_DIR.parent / "data" / "dev_knowledge.json"
SCAN_INTERVAL = 3600  # كل ساعة


# ─── Code Analyzer ───────────────────────────────────────────────────────────

class CodeAnalyzer:
    """يحلل ملفات Python ويكتشف المشاكل الشائعة."""

    ISSUES = {
        "no_docstring": "⚠️  دالة/كلاس بدون docstring",
        "bare_except": "🔴 except: عارية (تخفي الأخطاء)",
        "long_function": "📏 دالة طويلة جداً (>80 سطر)",
        "duplicate_logic": "🔁 منطق مكرر محتمل",
        "no_type_hints": "📝 دوال بدون type hints",
        "magic_numbers": "🔢 أرقام سحرية غير معرّفة",
    }

    def analyze_file(self, filepath: Path) -> Dict:
        issues = []
        suggestions = []
        score = 100  # نبدأ من 100 وننقص

        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception as e:
            return {"file": str(filepath.name), "error": str(e), "score": 0}

        lines = source.splitlines()

        for node in ast.walk(tree):
            # bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append({"type": "bare_except", "line": node.lineno})
                suggestions.append(f"L{node.lineno}: استبدل `except:` بـ `except Exception as e:`")
                score -= 10

            # functions without docstring
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)):
                    issues.append({"type": "no_docstring", "name": node.name, "line": node.lineno})
                    score -= 2

                # long function
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > 80:
                    issues.append({"type": "long_function", "name": node.name, "lines": func_lines})
                    suggestions.append(f"دالة `{node.name}` ({func_lines} سطر) — فكر في تقسيمها")
                    score -= 5

                # no type hints
                if not node.returns and not any(
                    a.annotation for a in node.args.args
                ):
                    issues.append({"type": "no_type_hints", "name": node.name})
                    score -= 1

        return {
            "file": filepath.name,
            "size_kb": round(filepath.stat().st_size / 1024, 1),
            "lines": len(lines),
            "issues": issues,
            "suggestions": suggestions,
            "score": max(0, score),
            "analyzed_at": datetime.now().isoformat(),
        }


# ─── Duplicate Detector ───────────────────────────────────────────────────────

class DuplicateDetector:
    """يكتشف الملفات المكررة أو الزائدة."""

    def scan(self, directory: Path) -> List[Dict]:
        duplicates = []
        seen: Dict[str, List[str]] = {}

        for f in directory.glob("*.py"):
            # timestamp-suffixed files (e.g. base_agent_1771673767.py)
            name = f.stem
            parts = name.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) >= 9:
                duplicates.append({
                    "file": f.name,
                    "reason": f"ملف مكرر بـ timestamp — يجب دمجه في `{parts[0]}.py`",
                    "action": "merge_or_delete",
                })

            # .backup files
            for bf in directory.glob("*.backup*"):
                duplicates.append({
                    "file": bf.name,
                    "reason": "ملف backup — انقله لمجلد backups/",
                    "action": "move_to_backups",
                })
                break  # avoid duplicating

        return duplicates


# ─── Performance Monitor ──────────────────────────────────────────────────────

class PerformanceMonitor:
    """يقرأ آخر نتائج التداول ويقيّم صحة النظام."""

    def __init__(self):
        self.data_dir = Path("data")

    def read_trading_stats(self) -> Dict:
        stats_file = self.data_dir / "trading_stats.json"
        if stats_file.exists():
            try:
                return json.loads(stats_file.read_text())
            except Exception:
                pass
        return {}

    def evaluate(self) -> Dict:
        stats = self.read_trading_stats()
        recommendations = []

        winrate = stats.get("win_rate", None)
        if winrate is not None:
            if winrate < 0.45:
                recommendations.append("🔴 Win rate منخفض (<45%) — راجع فلاتر الدخول")
            elif winrate < 0.55:
                recommendations.append("🟡 Win rate متوسط — اختبر استراتيجيات إضافية")
            else:
                recommendations.append("🟢 Win rate جيد")

        drawdown = stats.get("max_drawdown", None)
        if drawdown is not None and drawdown > 0.15:
            recommendations.append("🔴 Max Drawdown >15% — فعّل circuit breaker")

        return {
            "stats": stats,
            "recommendations": recommendations,
            "evaluated_at": datetime.now().isoformat(),
        }


# ─── Main Agent ───────────────────────────────────────────────────────────────

class SelfDevAgent(BaseAgent):
    """
    وكيل التطوير الذاتي.
    يعمل بشكل دوري ويُنتج تقارير تطوير تُحفظ في data/dev_reports/
    """

    def __init__(self):
        super().__init__(name="SelfDevAgent")
        self.analyzer = CodeAnalyzer()
        self.duplicate_detector = DuplicateDetector()
        self.perf_monitor = PerformanceMonitor()
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    async def start(self):
        self.logger.info("🔧 SelfDevAgent started")
        asyncio.create_task(self.run(interval=SCAN_INTERVAL))

    async def stop(self):
        self._running = False
        self.logger.info("🔧 SelfDevAgent stopped")

    async def process(self, data: Any):
        """Main scan cycle."""
        self.logger.info("🔍 Starting dev scan...")
        report = await asyncio.get_event_loop().run_in_executor(None, self._full_scan)
        self._save_report(report)
        self._update_knowledge(report)
        self._print_summary(report)

    def _full_scan(self) -> Dict:
        """Run full system scan (sync - runs in executor)."""
        # 1. Code quality
        code_results = []
        priority_files = [
            "noogh_orchestrator.py",
            "autonomous_trading_agent.py",
            "adaptive_strategy_selector.py",
            "symbol_scorer.py",
            "volatility_guard.py",
            "decision_engine.py",
            "goal_planner.py",
            "self_healer.py",
        ]
        for fname in priority_files:
            fpath = AGENTS_DIR / fname
            if fpath.exists():
                code_results.append(self.analyzer.analyze_file(fpath))

        # 2. Duplicates
        duplicates = self.duplicate_detector.scan(AGENTS_DIR)

        # 3. Performance
        perf = self.perf_monitor.evaluate()

        # 4. Overall score
        scores = [r["score"] for r in code_results if "score" in r]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        return {
            "scan_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
            "timestamp": datetime.now().isoformat(),
            "overall_score": avg_score,
            "code_quality": code_results,
            "duplicates": duplicates,
            "performance": perf,
            "top_issues": self._extract_top_issues(code_results),
        }

    def _extract_top_issues(self, results: List[Dict]) -> List[str]:
        all_suggestions = []
        for r in results:
            for s in r.get("suggestions", []):
                all_suggestions.append(f"[{r['file']}] {s}")
        return all_suggestions[:10]  # top 10

    def _save_report(self, report: Dict):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = REPORTS_DIR / f"dev_report_{ts}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        self.logger.info(f"📄 Report saved: {path.name}")

    def _update_knowledge(self, report: Dict):
        """Accumulate knowledge over time."""
        knowledge = {}
        if KNOWLEDGE_FILE.exists():
            try:
                knowledge = json.loads(KNOWLEDGE_FILE.read_text())
            except Exception:
                pass

        history = knowledge.get("score_history", [])
        history.append({
            "ts": report["timestamp"],
            "score": report["overall_score"],
        })
        knowledge["score_history"] = history[-50:]  # keep last 50
        knowledge["last_scan"] = report["timestamp"]
        knowledge["latest_issues"] = report["top_issues"]
        knowledge["duplicates_found"] = len(report["duplicates"])

        KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        KNOWLEDGE_FILE.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2))

    def _print_summary(self, report: Dict):
        score = report["overall_score"]
        emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        print(f"\n{'='*55}")
        print(f"  🔧 NOOGH SelfDevAgent Report [{report['scan_id']}]")
        print(f"  {emoji} Code Quality Score: {score}/100")
        print(f"  🗂️  Files Scanned: {len(report['code_quality'])}")
        print(f"  ⚠️  Duplicates Found: {len(report['duplicates'])}")
        if report["top_issues"]:
            print(f"  📋 Top Issues:")
            for issue in report["top_issues"][:5]:
                print(f"     • {issue}")
        perf_recs = report["performance"].get("recommendations", [])
        if perf_recs:
            print(f"  📈 Performance:")
            for r in perf_recs:
                print(f"     {r}")
        print(f"{'='*55}\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

async def main():
    agent = SelfDevAgent()
    await agent.start()
    # Run one cycle immediately
    await agent.process(None)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(message)s")
    asyncio.run(main())
