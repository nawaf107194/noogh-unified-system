"""
System Introspector - System Self-Understanding
Analyzes component structure, logs, performance, and knowledge map.
"""

import ast
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# import pandas as pd # Removed as unused and missing
import networkx as nx
import yaml

from gateway.app.core.logging import get_logger

logger = get_logger("system_introspector")


@dataclass
class SystemComponent:
    """Analyzed system component"""

    name: str
    type: str  # module, class, function, agent, tool
    file_path: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    usage_count: int = 0
    error_rate: float = 0.0
    last_modified: Optional[str] = None
    docstring: Optional[str] = None
    methods: List[str] = field(default_factory=list)


@dataclass
class KnowledgeMap:
    """Knowledge map extracted from the system"""

    concepts: Dict[str, List[str]]  # concept -> [sources]
    relationships: List[Tuple[str, str, str]]  # (source, relation, target)
    categories: Dict[str, List[str]]  # category -> [concepts]
    confidence: Dict[str, float]  # confidence in each concept


class SystemIntrospector:
    """Internal System Analyst"""

    def __init__(self, system_root: str = "."):
        self.system_root = Path(system_root)
        self.components: Dict[str, SystemComponent] = {}
        self.knowledge_map = KnowledgeMap(concepts={}, relationships=[], categories={}, confidence={})
        self.metrics_history = []
        self.architecture_graph = nx.DiGraph()

    async def run_full_introspection(self) -> Dict[str, Any]:
        """Run comprehensive system analysis"""

        logger.info("🔍 Starting full system introspection...")

        results = {"timestamp": datetime.now().isoformat(), "phases": {}}

        # Phase 1: Code Structure Analysis
        results["phases"]["code_analysis"] = await self.analyze_code_structure()

        # Phase 2: Log Analysis
        results["phases"]["log_analysis"] = await self.analyze_system_logs()

        # Phase 3: Model Performance Analysis
        results["phases"]["model_analysis"] = await self.analyze_model_performance()

        # Phase 4: Tool Usage Analysis
        results["phases"]["tool_analysis"] = await self.analyze_tool_usage()

        # Phase 5: Workflow Analysis
        results["phases"]["workflow_analysis"] = await self.analyze_workflow_patterns()

        # Phase 6: Knowledge Extraction
        results["phases"]["knowledge_extraction"] = await self.extract_knowledge_map()

        # Phase 7: Weakness Identification
        results["phases"]["weakness_analysis"] = self.identify_weaknesses(results)

        # Phase 8: Improvement Plan Generation
        results["improvement_plan"] = self.generate_improvement_plan(results)

        logger.info(
            f"✅ Introspection complete: {len(self.components)} components, {len(self.knowledge_map.concepts)} concepts"
        )

        return results

    async def analyze_code_structure(self) -> Dict[str, Any]:
        """Analyze code structure"""

        logger.info("📁 Analyzing code structure...")

        analysis = {
            "modules_found": 0,
            "classes_found": 0,
            "functions_found": 0,
            "total_lines": 0,
            "complexity_distribution": {},
            "dependency_graph": {},
        }

        # Scan all python files
        python_files = list(self.system_root.rglob("*.py"))

        for py_file in python_files:
            if "test" in str(py_file) or "venv" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")
                    analysis["total_lines"] += len(lines)

                    # AST Analysis
                    tree = ast.parse(content)

                    # Extract modules, classes, functions
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = node.name
                            component = SystemComponent(
                                name=class_name,
                                type="class",
                                file_path=str(py_file.relative_to(self.system_root)),
                                docstring=ast.get_docstring(node),
                                methods=[n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                            )
                            self.components[class_name] = component
                            analysis["classes_found"] += 1

                        elif isinstance(node, ast.FunctionDef):
                            func_name = node.name
                            component = SystemComponent(
                                name=func_name,
                                type="function",
                                file_path=str(py_file.relative_to(self.system_root)),
                                docstring=ast.get_docstring(node),
                            )
                            self.components[func_name] = component
                            analysis["functions_found"] += 1

                analysis["modules_found"] += 1

            except Exception as e:
                logger.warning(f"Failed to analyze file {py_file}: {e}")
                continue

        # Calculate cyclomatic complexity
        analysis["complexity_distribution"] = self._calculate_complexity()

        # Build dependency graph
        analysis["dependency_graph"] = self._build_dependency_graph()

        return analysis

    def _calculate_complexity(self) -> Dict[str, float]:
        """Calculate complexity distribution"""
        complexity_scores = defaultdict(list)

        for component in self.components.values():
            score = self._compute_complexity_score(component)
            component.complexity_score = score
            complexity_scores[component.type].append(score)

        distribution = {}
        for comp_type, scores in complexity_scores.items():
            if scores:
                distribution[comp_type] = {
                    "average": sum(scores) / len(scores),
                    "max": max(scores),
                    "min": min(scores),
                    "count": len(scores),
                }

        return distribution

    def _compute_complexity_score(self, component: SystemComponent) -> float:
        """Compute complexity score for a component"""
        score = 1.0

        # Add points based on number of dependencies
        score += len(component.dependencies) * 0.2

        # Add points based on number of methods (for classes)
        score += len(component.methods) * 0.1

        # Add points based on path depth
        if component.file_path:
            depth = len(component.file_path.split("/"))
            score += depth * 0.05

        return round(score, 2)

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph"""
        graph = defaultdict(list)

        for component in self.components.values():
            if component.dependencies:
                graph[component.name] = component.dependencies

        return dict(graph)

    async def analyze_system_logs(self) -> Dict[str, Any]:
        """Analyze system logs"""

        logger.info("📊 Analyzing system logs...")

        log_analysis = {
            "total_entries": 0,
            "error_distribution": {},
            "warning_distribution": {},
            "error_trends": [],
            "most_common_errors": [],
            "error_sources": {},
        }

        log_files = []
        # Check specific log location first, or root
        if (self.system_root / "gateway.log").exists():
            log_files.append(self.system_root / "gateway.log")

        # Also check logs dir if exists
        log_dir = self.system_root / "logs"
        if log_dir.exists():
            log_files.extend(list(log_dir.rglob("*.log")))

        if not log_files:
            return log_analysis

        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    log_analysis["total_entries"] += len(lines)

                    for line in lines[-1000:]:  # Last 1000 lines for efficiency
                        # Analyze log level
                        if "ERROR" in line:
                            log_analysis["error_distribution"][log_file.name] = (
                                log_analysis["error_distribution"].get(log_file.name, 0) + 1
                            )

                            # Extract error message
                            error_msg = self._extract_error_message(line)
                            if error_msg:
                                log_analysis["most_common_errors"].append(error_msg)

                                # Identify error source
                                source = self._identify_error_source(line)
                                if source:
                                    log_analysis["error_sources"][source] = (
                                        log_analysis["error_sources"].get(source, 0) + 1
                                    )

                        elif "WARNING" in line:
                            log_analysis["warning_distribution"][log_file.name] = (
                                log_analysis["warning_distribution"].get(log_file.name, 0) + 1
                            )

            except Exception as e:
                logger.warning(f"Failed to read log {log_file}: {e}")

        # Feature: Error Trends (Simplified implementation)
        # log_analysis["error_trends"] = self._analyze_error_trends(log_files)

        # Most common errors
        error_counter = Counter(log_analysis["most_common_errors"])
        log_analysis["most_common_errors"] = [
            {"error": error, "count": count} for error, count in error_counter.most_common(10)
        ]

        return log_analysis

    def _extract_error_message(self, log_line: str) -> Optional[str]:
        """Extract error message from log line"""
        try:
            # Simple pattern to extract message
            patterns = [r"ERROR.*?: (.*)", r"Exception: (.*)", r"Traceback.*?\n.*?(\w+Error.*)"]

            for pattern in patterns:
                match = re.search(pattern, log_line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()[:100]  # First 100 chars

            return None
        except Exception:
            return None

    def _identify_error_source(self, log_line: str) -> Optional[str]:
        """Identify error source"""
        components = [
            "AgentKernel",
            "Brain",
            "Memory",
            "Tool",
            "Distillation",
            "DreamWorker",
            "Router",
            "API",
            "Database",
            "interpreter",
        ]

        for component in components:
            if component in log_line:
                return component

        return "Unknown"

    async def analyze_model_performance(self) -> Dict[str, Any]:
        """Analyze model performance"""

        logger.info("🧠 Analyzing model performance...")

        model_analysis = {
            "models_detected": [],
            "performance_metrics": {},
            "resource_usage": {},
            "inference_times": [],
            "accuracy_trends": [],
        }

        # Find model files
        model_extensions = [".pt", ".pth", ".bin", ".safetensors", ".gguf"]
        model_files = []

        for ext in model_extensions:
            # Avoid overly deep search or large dirs if possible
            model_files.extend(self.system_root.rglob(f"*{ext}"))

        for model_file in model_files:
            # Skip hidden or venv
            if ".git" in str(model_file) or "venv" in str(model_file) or ".cache" in str(model_file):
                continue

            try:
                model_info = {
                    "name": model_file.name,
                    "path": str(model_file),
                    "size_mb": model_file.stat().st_size / (1024 * 1024),
                    "last_modified": datetime.fromtimestamp(model_file.stat().st_mtime).isoformat(),
                }
                model_analysis["models_detected"].append(model_info)

            except Exception as e:
                logger.warning(f"Failed to analyze model {model_file}: {e}")

        return model_analysis

    async def analyze_tool_usage(self) -> Dict[str, Any]:
        """Analyze tool usage"""

        logger.info("🛠️ Analyzing tool usage...")

        tool_analysis = {
            "tools_registered": [],
            "usage_frequency": {},
            "success_rates": {},
            "average_execution_time": {},
            "most_used_tools": [],
            "least_used_tools": [],
            "error_prone_tools": [],
        }

        # Simple placeholder implementation as we don't have structured tool logs yet
        # In a real system we would parse tool usage from logs

        return tool_analysis

    async def analyze_workflow_patterns(self) -> Dict[str, Any]:
        """Analyze workflow patterns"""

        logger.info("🔄 Analyzing workflow patterns...")

        workflow_analysis = {
            "common_workflows": [],
            "workflow_complexity": {},
            "average_steps": 0,
            "completion_rates": {},
            "bottlenecks": [],
        }

        return workflow_analysis

    async def extract_knowledge_map(self) -> KnowledgeMap:
        """Extract knowledge map from system"""

        logger.info("🗺️ Extracting knowledge map...")

        # Collect concepts from various sources
        concepts = defaultdict(list)

        # 1. From code (docstrings, names)
        for component in self.components.values():
            if component.docstring:
                self._extract_concepts_from_text(component.docstring, concepts, source=f"docstring:{component.name}")
            if component.name:
                self._extract_concepts_from_text(component.name, concepts, source=f"name:{component.name}")

        # 2. From logs (gateway.log)
        log_file = self.system_root / "gateway.log"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    # Read last 20KB
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 20000))
                    content = f.read()
                    self._extract_concepts_from_text(content, concepts, source=f"log:{log_file.name}")
            except Exception:
                pass

        # 4. Categorize concepts
        categories = self._categorize_concepts(concepts)

        # 5. Discover relationships
        relationships = self._discover_relationships(concepts)

        # 6. Calculate confidence
        confidence = self._calculate_confidence(concepts)

        self.knowledge_map = KnowledgeMap(
            concepts=dict(concepts), relationships=relationships, categories=categories, confidence=confidence
        )

        return self.knowledge_map

    def _extract_concepts_from_text(self, text: str, concepts: dict, source: str):
        """Extract concepts from text"""
        # List of common technical terms
        technical_terms = [
            "neural",
            "network",
            "learning",
            "model",
            "training",
            "inference",
            "memory",
            "agent",
            "tool",
            "api",
            "database",
            "cache",
            "queue",
            "distillation",
            "dream",
            "router",
            "kernel",
            "protocol",
            "auth",
        ]

        for term in technical_terms:
            if term.lower() in text.lower():
                concepts[term].append(source)

        # Extract function and class names as concepts
        pattern = r"\b([A-Z][a-z]+[A-Z][a-z]+|\w+[A-Z][a-z]+)\b"
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) > 3:  # Ignore short words
                concepts[match].append(source)

    def _categorize_concepts(self, concepts: dict) -> Dict[str, List[str]]:
        """Categorize concepts"""
        categories = {
            "ai_ml": ["neural", "network", "learning", "model", "training", "inference", "distillation"],
            "system": ["memory", "agent", "tool", "kernel", "protocol"],
            "infrastructure": ["api", "database", "cache", "queue", "router"],
            "operations": ["auth", "security", "logging", "monitoring"],
            "general": [],  # For unclassified
        }

        categorized = {cat: [] for cat in categories.keys()}

        for concept in concepts.keys():
            categorized_flag = False
            for category, keywords in categories.items():
                if category == "general":
                    continue

                # Check if concept relates to these keywords
                concept_lower = concept.lower()
                if any(keyword in concept_lower for keyword in keywords):
                    categorized[category].append(concept)
                    categorized_flag = True
                    break

            if not categorized_flag:
                categorized["general"].append(concept)

        return categorized

    def _discover_relationships(self, concepts: dict) -> List[Tuple[str, str, str]]:
        """Discover relationships between concepts"""
        relationships = []

        concept_list = list(concepts.keys())

        # Simple co-occurrence relationship
        # Limit complexity for now
        max_checks = 100
        checks = 0

        for i, concept1 in enumerate(concept_list):
            for concept2 in concept_list[i + 1 :]:
                checks += 1
                if checks > max_checks:
                    break

                # If both appear in same source
                common_sources = set(concepts[concept1]) & set(concepts[concept2])
                if common_sources:
                    strength = len(common_sources) / min(len(concepts[concept1]), len(concepts[concept2]))
                    if strength > 0.3:  # Threshold
                        relationships.append((concept1, "related_to", concept2))

        return relationships

    def _calculate_confidence(self, concepts: dict) -> Dict[str, float]:
        """Calculate confidence score for each concept"""
        confidence = {}

        for concept, sources in concepts.items():
            source_count = len(sources)
            source_types = set(s.split(":")[0] for s in sources)

            base_confidence = min(1.0, source_count / 10)

            # Boost confidence for diversity
            type_diversity = len(source_types) / max(1, source_count)
            base_confidence *= 1 + type_diversity * 0.5

            # Boost for important sources
            important_sources = ["docstring", "config"]
            important_count = sum(1 for s in sources if any(i in s for i in important_sources))
            if important_count > 0:
                base_confidence *= 1.2

            confidence[concept] = round(min(1.0, base_confidence), 2)

        return confidence

    def identify_weaknesses(self, analysis_results: Dict) -> Dict[str, Any]:
        """Identify system weaknesses"""

        weaknesses = {
            "high_complexity_components": [],
            "error_prone_modules": [],
            "underutilized_tools": [],
            "performance_bottlenecks": [],
            "knowledge_gaps": [],
            "security_concerns": [],
        }

        # 1. High Complexity
        for comp_name, component in self.components.items():
            if component.complexity_score > 3.0:  # Threshold
                weaknesses["high_complexity_components"].append(
                    {
                        "name": comp_name,
                        "complexity": component.complexity_score,
                        "type": component.type,
                        "file": component.file_path,
                    }
                )

        # 2. Error Prone Modules
        error_sources = analysis_results["phases"]["log_analysis"].get("error_sources", {})
        for source, count in error_sources.items():
            if count > 5:  # Lower threshold for demo
                weaknesses["error_prone_modules"].append({"module": source, "error_count": count})

        # 5. Knowledge Gaps
        for category, concepts in self.knowledge_map.categories.items():
            if category == "general" and len(concepts) > 20:
                weaknesses["knowledge_gaps"].append(
                    {"issue": "Many unclassified concepts", "unclassified_concepts": len(concepts)}
                )

        return weaknesses

    def generate_improvement_plan(self, analysis_results: Dict) -> Dict[str, Any]:
        """Generate improvement plan"""

        plan = {
            "priority_areas": [],
            "specific_actions": [],
            "timeline": {},
            "expected_impact": {},
            "monitoring_metrics": [],
        }

        weaknesses = analysis_results["phases"]["weakness_analysis"]

        # Identify priority areas
        priority_scores = {}

        if weaknesses["high_complexity_components"]:
            priority_scores["reduce_complexity"] = 8

        if weaknesses["error_prone_modules"]:
            priority_scores["fix_errors"] = 9

        if weaknesses["performance_bottlenecks"]:
            priority_scores["optimize_performance"] = 7

        if weaknesses["knowledge_gaps"]:
            priority_scores["fill_knowledge_gaps"] = 6

        sorted_priorities = sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)
        plan["priority_areas"] = [area for area, _ in sorted_priorities[:3]]

        # Generate specific actions
        specific_actions = []

        if "reduce_complexity" in plan["priority_areas"]:
            for comp in weaknesses["high_complexity_components"][:3]:
                specific_actions.append(
                    {
                        "action": f"Refactor {comp['name']}",
                        "reason": f"High Complexity ({comp['complexity']})",
                        "estimated_effort": "medium",
                        "expected_benefit": "Maintainability",
                    }
                )

        if "fix_errors" in plan["priority_areas"]:
            for module in weaknesses["error_prone_modules"][:3]:
                specific_actions.append(
                    {
                        "action": f"Debug {module['module']}",
                        "reason": f"{module['error_count']} errors",
                        "estimated_effort": "high",
                        "expected_benefit": "Reliability",
                    }
                )

        plan["specific_actions"] = specific_actions

        return plan

    def generate_report(self, analysis_results: Dict) -> str:
        """Generate text report"""

        report = [
            "=" * 60,
            "System Introspection Report",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            "",
            "🔍 System Summary:",
            f"   - Components Detected: {len(self.components)}",
            f"   - Knowledge Concepts: {len(self.knowledge_map.concepts)}",
            f"   - Relationships: {len(self.knowledge_map.relationships)}",
            "",
            "📊 System Performance:",
            f"   - Total Log Entries Analyzed: {analysis_results['phases']['log_analysis'].get('total_entries', 0)}",
            f"   - Models Detected: {len(analysis_results['phases']['model_analysis'].get('models_detected', []))}",
            "",
            "⚠️ Weaknesses:",
        ]

        weaknesses = analysis_results["phases"]["weakness_analysis"]

        if weaknesses["high_complexity_components"]:
            report.append(f"   - High Complexity Components: {len(weaknesses['high_complexity_components'])}")
            for c in weaknesses["high_complexity_components"][:3]:
                report.append(f"     * {c['name']} ({c['complexity']})")

        if weaknesses["error_prone_modules"]:
            report.append(f"   - Error Prone Modules: {len(weaknesses['error_prone_modules'])}")
            for m in weaknesses["error_prone_modules"][:3]:
                report.append(f"     * {m['module']} ({m['error_count']} errors)")

        report.extend(
            [
                "",
                "🎯 Improvement Plan:",
                f"   - Priority Areas: {', '.join(analysis_results['improvement_plan']['priority_areas'][:3])}",
                "   - Key Actions:",
            ]
        )

        for action in analysis_results["improvement_plan"]["specific_actions"]:
            report.append(f"     * {action['action']} ({action['reason']})")

        report.extend(["", "=" * 60, "End Report", "=" * 60])

        return "\n".join(report)

    async def export_analysis(self, output_dir: str = "./system_analysis"):
        """Export results to files"""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)  # Ensure parents exist

        # Run if not already run
        if not self.components:
            await self.run_full_introspection()

        # Save Components
        components_file = output_path / "components.json"
        components_data = {
            name: {
                "type": comp.type,
                "file_path": comp.file_path,
                "dependencies": comp.dependencies,
                "complexity_score": comp.complexity_score,
                "usage_count": comp.usage_count,
                "error_rate": comp.error_rate,
                "docstring": comp.docstring[:500] if comp.docstring else None,
                "methods": comp.methods,
            }
            for name, comp in self.components.items()
        }

        with open(components_file, "w", encoding="utf-8") as f:
            json.dump(components_data, f, indent=2, ensure_ascii=False)

        # Save Knowledge Map
        knowledge_file = output_path / "knowledge_map.json"
        knowledge_data = {
            "concepts": self.knowledge_map.concepts,
            "relationships": self.knowledge_map.relationships,
            "categories": self.knowledge_map.categories,
            "confidence": self.knowledge_map.confidence,
        }

        with open(knowledge_file, "w", encoding="utf-8") as f:
            json.dump(knowledge_data, f, indent=2, ensure_ascii=False)

        # Save Text Report
        report_file = output_path / "analysis_report.txt"

        # Re-get full analysis result for report generation (since we run it inside export if needed)
        # Note: self.components is populated, but we need the 'results' dict structure
        # for generate_report. For this simple implementation, we'll re-run or better yet,
        # we should pass results to export_analysis. But to match the User's API style,
        # let's just re-construct the results dict structure from internal state or return it from run().

        # Workaround: run_full_introspection returns results.
        # If we just called it, we have it. If we call export directly...
        # Let's assume user calls run_full_introspection recursively inside export if needed.
        # But wait, run_full_introspection calls export? No, user example calls run then export.

        # Correct path: The user manually calls run, then export produces files.
        # But this method *calls* run if components are empty.
        # If components are empty, we lose the return value of run() here.
        # Let's fix this to ensure we have the results dict.

        full_analysis = await self.run_full_introspection()  # Always run fresh to get proper dict
        report_text = self.generate_report(full_analysis)

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_text)

        # Save Plan
        plan_file = output_path / "improvement_plan.yaml"
        plan_data = full_analysis["improvement_plan"]

        with open(plan_file, "w", encoding="utf-8") as f:
            yaml.dump(plan_data, f, allow_unicode=True)

        logger.info(f"✅ Exported analysis to {output_path}")

        return {
            "components_file": str(components_file),
            "knowledge_file": str(knowledge_file),
            "report_file": str(report_file),
            "plan_file": str(plan_file),
        }
