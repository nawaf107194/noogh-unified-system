#!/usr/bin/env python3
"""
Autonomous Brain - الدماغ الذاتي الكامل
=====================================

Extends SystemManager with:
- File reading and analysis
- Code understanding
- Autonomous learning decisions
- Trading strategy decisions
- Self-healing and code modification

This is the "thinking" part of the autonomous system.
"""

import ast
import logging
import json
import gc
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Iterator
from dataclasses import dataclass
import time

logger = logging.getLogger("autonomous_brain")


@dataclass
class FileAnalysis:
    """Analysis of a file"""
    path: str
    file_type: str  # 'python', 'json', 'log', 'config'
    size_bytes: int
    last_modified: float
    content_summary: str
    issues: List[str]
    insights: List[str]
    syntax_errors: List[str]


@dataclass
class LearningOpportunity:
    """An opportunity to learn something"""
    source: str  # 'github', 'arxiv', 'web', 'code', 'logs'
    topic: str
    reasoning: str
    priority: int
    estimated_duration_minutes: int


class FileReader:
    """Autonomous file reading and analysis"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        # Cache: {file_path: (mtime, FileAnalysis)}
        self.file_cache: Dict[str, Tuple[float, FileAnalysis]] = {}

    def read_and_analyze(self, file_path: Path) -> Optional[FileAnalysis]:
        """Read and analyze a file (with caching)"""
        try:
            if not file_path.exists():
                return None

            # Get file info
            stat = file_path.stat()
            file_path_str = str(file_path)

            # Check cache - if file hasn't changed, return cached analysis
            if file_path_str in self.file_cache:
                cached_mtime, cached_analysis = self.file_cache[file_path_str]
                if cached_mtime == stat.st_mtime:
                    return cached_analysis

            file_type = self._detect_file_type(file_path)

            # Read content
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
                return None

            # Analyze based on type
            issues = []
            insights = []
            syntax_errors = []

            if file_type == 'python':
                syntax_errors = self._check_python_syntax(content, file_path)
                issues, insights = self._analyze_python_code(content)
            elif file_type == 'json':
                issues = self._check_json_syntax(content)
            elif file_type == 'log':
                issues, insights = self._analyze_logs(content)

            # Create summary
            lines = content.split('\n')
            summary = f"{len(lines)} lines, {len(content)} bytes"

            analysis = FileAnalysis(
                path=str(file_path),
                file_type=file_type,
                size_bytes=stat.st_size,
                last_modified=stat.st_mtime,
                content_summary=summary,
                issues=issues,
                insights=insights,
                syntax_errors=syntax_errors
            )

            # Cache the analysis
            self.file_cache[file_path_str] = (stat.st_mtime, analysis)

            return analysis

        except Exception as e:
            logger.error(f"File analysis failed for {file_path}: {e}")
            return None

    def _detect_file_type(self, path: Path) -> str:
        """Detect file type"""
        suffix = path.suffix.lower()
        if suffix == '.py':
            return 'python'
        elif suffix == '.json':
            return 'json'
        elif suffix == '.log':
            return 'log'
        elif suffix in ['.yaml', '.yml', '.toml', '.ini']:
            return 'config'
        else:
            return 'text'

    def _check_python_syntax(self, content: str, path: Path) -> List[str]:
        """Check Python syntax"""
        errors = []
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append(f"Line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Parse error: {e}")
        return errors

    def _analyze_python_code(self, content: str) -> Tuple[List[str], List[str]]:
        """Analyze Python code for issues and insights"""
        issues = []
        insights = []

        lines = content.split('\n')

        # Check for common issues
        if 'TODO' in content:
            todo_count = content.count('TODO')
            issues.append(f"{todo_count} TODO items found")

        if 'FIXME' in content:
            issues.append("FIXME comments found")

        # Check for good practices
        if 'logging' in content:
            insights.append("Uses logging")

        if 'async def' in content:
            insights.append("Uses async/await")

        if 'class ' in content:
            class_count = content.count('class ')
            insights.append(f"{class_count} classes defined")

        return issues, insights

    def _check_json_syntax(self, content: str) -> List[str]:
        """Check JSON syntax"""
        errors = []
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"JSON error at line {e.lineno}: {e.msg}")
        return errors

    def _analyze_logs(self, content: str) -> Tuple[List[str], List[str]]:
        """Analyze log files"""
        issues = []
        insights = []

        lines = content.split('\n')

        error_count = sum(1 for line in lines if 'ERROR' in line or 'CRITICAL' in line)
        warning_count = sum(1 for line in lines if 'WARNING' in line)

        if error_count > 0:
            issues.append(f"{error_count} errors in logs")

        if warning_count > 10:
            issues.append(f"{warning_count} warnings in logs")

        insights.append(f"Total log entries: {len(lines)}")

        return issues, insights

    def scan_directory(self, directory: Path, patterns: List[str] = None, max_files: int = 200) -> Iterator[FileAnalysis]:
        """Scan directory and analyze files (yields results to save memory)"""
        if patterns is None:
            patterns = ['*.py', '*.json', '*.log']

        file_count = 0
        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                # Skip venv, node_modules, git, and other noisy directories
                if any(skip in str(file_path) for skip in [
                    '.venv', 'node_modules', '__pycache__', '.git', 
                    '.pytest_cache', '.noogh_venv', '.proposal_memory',
                    '.noogh_audit', '.claude'
                ]):
                    continue

                if file_count >= max_files:
                    logger.info(f"   Reached max files limit ({max_files}) for {directory}")
                    return

                analysis = self.read_and_analyze(file_path)
                if analysis:
                    yield analysis
                    file_count += 1


class AutonomousBrain:
    """
    The autonomous thinking system.
    Reads, understands, decides, acts.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.file_reader = FileReader(base_dir)
        self.knowledge_base = {}
        self.insights_log = []

    def think_about_system(self) -> Dict[str, Any]:
        """
        Think about the current state of the system.
        Read files, analyze, and generate insights.
        Memory-optimized: processes files in batches, doesn't keep all in memory.
        """
        logger.info("🧠 Autonomous Brain is thinking...")

        thoughts = {
            'timestamp': time.time(),
            'file_analyses': [],
            'syntax_errors_found': [],
            'learning_opportunities': [],
            'trading_insights': [],
            'system_improvements': []
        }

        # 1. Scan critical directories (streaming, not loading all into memory)
        logger.info("   📂 Scanning codebase (memory-optimized)...")

        critical_dirs = [
            self.base_dir / 'agents',
            self.base_dir / 'trading',
            self.base_dir / 'unified_core',
        ]

        # Process files in batches to save memory
        total_files = 0
        has_ml_code = False
        has_trading = False
        error_files_count = 0
        test_files_count = 0
        code_files_count = 0

        for directory in critical_dirs:
            if not directory.exists():
                continue

            batch = []
            for analysis in self.file_reader.scan_directory(directory, max_files=1000):
                batch.append(analysis)
                total_files += 1

                # Track key metrics without keeping all analyses
                if 'ml' in analysis.path.lower() or 'model' in analysis.path.lower():
                    has_ml_code = True
                if 'trading' in analysis.path.lower():
                    has_trading = True
                if analysis.syntax_errors:
                    thoughts['syntax_errors_found'].append({
                        'file': analysis.path,
                        'errors': analysis.syntax_errors
                    })
                    error_files_count += 1
                if 'test_' in analysis.path:
                    test_files_count += 1
                if analysis.file_type == 'python' and 'test_' not in analysis.path:
                    code_files_count += 1

                # Keep only first 10 samples for file_analyses
                if len(thoughts['file_analyses']) < 10:
                    thoughts['file_analyses'].append(analysis)

                # Process in batches of 50
                if len(batch) >= 50:
                    # Clear batch and collect garbage
                    batch.clear()
                    gc.collect()

            # Clear final batch
            batch.clear()
            gc.collect()

        if thoughts['syntax_errors_found']:
            logger.warning(f"   ⚠️  Found {len(thoughts['syntax_errors_found'])} files with syntax errors")

        # 3. Identify learning opportunities (based on tracked flags, not all_analyses)
        logger.info("   💡 Identifying learning opportunities...")
        learning_opps = self._identify_learning_opportunities_light(has_ml_code, has_trading)
        thoughts['learning_opportunities'] = learning_opps

        # 4. Trading insights
        logger.info("   💰 Analyzing trading opportunities...")
        trading_insights = self._analyze_trading_opportunities()
        thoughts['trading_insights'] = trading_insights

        # 5. System improvements (based on metrics, not all_analyses)
        logger.info("   🔧 Thinking about system improvements...")
        improvements = self._think_about_improvements_light(
            error_files_count,
            test_files_count,
            code_files_count
        )
        thoughts['system_improvements'] = improvements

        # Store insights (but limit log size)
        self.insights_log.append(thoughts)
        if len(self.insights_log) > 10:
            self.insights_log = self.insights_log[-10:]  # Keep only last 10

        logger.info(f"   ✅ Thinking complete:")
        logger.info(f"      • Files analyzed: {total_files}")
        logger.info(f"      • Syntax errors: {len(thoughts['syntax_errors_found'])}")
        logger.info(f"      • Learning opportunities: {len(learning_opps)}")
        logger.info(f"      • Trading insights: {len(trading_insights)}")

        # Final garbage collection
        gc.collect()

        return thoughts

    def _identify_learning_opportunities(self, analyses: List[FileAnalysis]) -> List[Dict]:
        """Identify what the system should learn (legacy method)"""
        # Extract flags
        has_ml_code = any('ml' in a.path.lower() or 'model' in a.path.lower() for a in analyses)
        has_trading = any('trading' in a.path.lower() for a in analyses)
        return self._identify_learning_opportunities_light(has_ml_code, has_trading)

    def _identify_learning_opportunities_light(self, has_ml_code: bool, has_trading: bool) -> List[Dict]:
        """Identify what the system should learn (memory-optimized)"""
        opportunities = []

        if has_ml_code:
            opportunities.append({
                'source': 'arxiv',
                'topic': 'latest ML techniques',
                'reasoning': 'System has ML code, should stay updated',
                'priority': 2
            })

        if has_trading:
            opportunities.append({
                'source': 'github',
                'topic': 'trading strategies',
                'reasoning': 'Improve trading algorithms',
                'priority': 2
            })

        # Always learn about AI agents
        opportunities.append({
            'source': 'github',
            'topic': 'autonomous AI agents',
            'reasoning': 'Continuous improvement of agent capabilities',
            'priority': 3
        })

        return opportunities

    def _analyze_trading_opportunities(self) -> List[Dict]:
        """Think about trading opportunities"""
        insights = []

        # Check if funding monitor should run
        current_hour = time.localtime().tm_hour
        if current_hour in [0, 8, 16]:  # Funding times
            insights.append({
                'type': 'funding_arbitrage',
                'reasoning': 'Funding rate check time',
                'action': 'spawn_funding_monitor'
            })

        # Check market volatility (placeholder)
        insights.append({
            'type': 'market_analysis',
            'reasoning': 'Continuous market monitoring needed',
            'action': 'ensure_trading_agent_running'
        })

        return insights

    def _think_about_improvements(self, analyses: List[FileAnalysis]) -> List[str]:
        """Think about how to improve the system (legacy method)"""
        error_files_count = sum(1 for a in analyses if a.syntax_errors)
        test_files_count = sum(1 for a in analyses if 'test_' in a.path)
        code_files_count = sum(1 for a in analyses if a.file_type == 'python' and 'test_' not in a.path)
        return self._think_about_improvements_light(error_files_count, test_files_count, code_files_count)

    def _think_about_improvements_light(self, error_files_count: int, test_files_count: int, code_files_count: int) -> List[str]:
        """Think about how to improve the system (memory-optimized)"""
        improvements = []

        if error_files_count > 0:
            improvements.append(f"Fix {error_files_count} files with syntax errors")

        if code_files_count > 0:
            improvements.append("Consider adding more documentation")

        if code_files_count > 0 and test_files_count < code_files_count * 0.3:
            improvements.append("Low test coverage - consider adding more tests")

        return improvements

    def decide_next_action(self, thoughts: Dict[str, Any]) -> Optional[Dict]:
        """
        Based on thoughts, decide what to do next.
        Returns an action to take.
        """
        # Priority 1: Fix syntax errors
        if thoughts['syntax_errors_found']:
            return {
                'action': 'fix_syntax_errors',
                'target': thoughts['syntax_errors_found'][0],
                'reasoning': 'Syntax errors block system functionality'
            }

        # Priority 2: Critical learning
        critical_learning = [l for l in thoughts['learning_opportunities']
                            if l.get('priority', 999) <= 2]
        if critical_learning:
            return {
                'action': 'learn',
                'target': critical_learning[0],
                'reasoning': 'High-priority learning opportunity'
            }

        # Priority 3: Trading
        if thoughts['trading_insights']:
            return {
                'action': 'trading',
                'target': thoughts['trading_insights'][0],
                'reasoning': 'Trading opportunity identified'
            }

        return None


def get_autonomous_brain(base_dir: Path = None) -> AutonomousBrain:
    """Get autonomous brain instance"""
    if base_dir is None:
        base_dir = Path(__file__).parent.parent

    return AutonomousBrain(base_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    brain = get_autonomous_brain()
    thoughts = brain.think_about_system()

    print("\n" + "="*70)
    print("🧠 AUTONOMOUS BRAIN THOUGHTS")
    print("="*70)
    print(json.dumps(thoughts, indent=2, default=str))

    action = brain.decide_next_action(thoughts)
    if action:
        print("\n" + "="*70)
        print("🎯 RECOMMENDED ACTION")
        print("="*70)
        print(json.dumps(action, indent=2))
