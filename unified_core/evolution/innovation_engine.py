"""
Innovation Engine — Creative Feature Generation
Version: 1.0.0
Part of: Self-Directed Layer

Unlike BrainAssistedRefactoring (which improves EXISTING code),
the InnovationEngine CREATES NEW features, patterns, and capabilities.

Modes:
1. Feature Discovery — asks the Brain "what's missing?"
2. Bug Hunting — proactive security/logic analysis
3. Architecture Review — structural improvements
4. API Enhancement — suggest new endpoints
5. Test Generation — create test cases

Flow:
1. Analyze current codebase structure
2. Ask Brain creative questions about improvements
3. Generate proposals for NEW code (not modifications)
4. Each innovation goes through the standard Evolution pipeline
"""

import asyncio
import json
import logging
import os
import random
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .ledger import EvolutionProposal, ProposalType, ProposalStatus, get_evolution_ledger
from .code_analyzer import get_code_analyzer

logger = logging.getLogger("unified_core.evolution.innovation")


@dataclass
class Innovation:
    """A creative innovation proposal from the Brain."""
    innovation_id: str
    title: str
    description: str
    innovation_type: str  # feature, bug_fix, architecture, api, test
    target_file: str  # New or existing file
    generated_code: str
    rationale: str
    confidence: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "innovation_id": self.innovation_id,
            "title": self.title,
            "description": self.description,
            "type": self.innovation_type,
            "target_file": self.target_file,
            "code_length": len(self.generated_code),
            "rationale": self.rationale,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }


# Creative prompts for different innovation types
INNOVATION_PROMPTS = {
    "missing_feature": """You are improving an autonomous Artificial Intelligence system (NOOGH). Suggest ONE new feature to add to the system architecture.
 
 CURRENT SYSTEM CAPABILITIES:
 {capabilities}
 
 RECENT SYSTEM CHANGES:
 {recent_changes}
 
 ALREADY IMPLEMENTED (DO NOT REPEAT):
 {already_implemented}
 
 The system currently has core elements like:
 - Neural Engine: LLM inference (vLLM, RunPod, local Ollama)
 - Evolution Pipeline: Generates, tests, and promotes new code (InnovationEngine)
 - Memory: SQLite-based MemoryStore, JSON-based Instincts, Cognitive Journal
 - Gateway: FastAPI endpoints for interaction
 - Data Routing: Postgres/VectorDB routing
 
 Think about NEXT LEVEL improvements NOT yet implemented:
 - Autonomous System Administrator (self-healing infra, auto-restart)
 - Advanced Memory Summarization (compressing old episodic memories)
 - Resource governor (throttling brain calls when GPU/CPU is saturated)
 - Goal synthesis (agent generating its own long-term objectives based on environment)
 - Security Intrusion Detection (analyzing logs to block suspicious IPs)
 - Multi-agent collaboration (spawning sub-agents for parallel tasks)
 - Code Quality Linter (automatically fixing PEP8 or typing issues)
 - Emotional/State tracking (agent modifying behavior based on recent failure/success streaks)
 
 CRITICAL: Create the new feature as a NEW FILE in: unified_core/intelligence/ (for thought/reasoning features) OR unified_core/system/ (for infra features).
 
 OUTPUT FORMAT:
 ```json
 {{
     "title": "Feature name",
     "description": "What it does and why it improves the system",
     "target_file": "unified_core/intelligence/new_feature.py",
     "rationale": "How this improves autonomy, speed, or intelligence"
 }}
```

Then provide the complete implementation:
```python
# Your code here
```""",

    "bug_hunter": """Review this Python function for potential bugs, edge cases, and security issues.

FILE: {file_path}
FUNCTION: {function_name}

```python
{code}
```

Look for:
1. Unhandled exceptions that could crash the process
2. Race conditions in async code
3. Missing input validation
4. Resource leaks (unclosed files, sessions, connections)
5. Logic errors in edge cases

If you find a real bug, provide:
```json
{{
    "title": "Bug: description",
    "severity": "HIGH/MEDIUM/LOW",
    "description": "Detailed explanation",
    "fix_description": "How to fix it"
}}
```

Then provide the FIXED version of the SAME function. CRITICAL RULES:
- Keep the EXACT same function signature: `def {function_name}(...)`
- Do NOT wrap in a class, do NOT add imports or module-level code
- Only modify the function BODY to fix the bug
- Return ONLY the complete fixed function definition, nothing else

```python
def {function_name}(...):  # Same signature as original
    # Fixed body here
```

If no real bugs found, respond with: NO_BUGS_FOUND""",

    "test_generator": """Generate a comprehensive unit test for this function.

FILE: {file_path}
FUNCTION: {function_name}

```python
{code}
```

Generate tests that cover:
1. Happy path (normal inputs)
2. Edge cases (empty, None, boundaries)
3. Error cases (invalid inputs)
4. Async behavior (if applicable)

Use pytest style. Output ONLY the test code:
```python
import pytest
# Your tests here
```""",

    "architecture_review": """Review this module's architecture and suggest ONE structural improvement.

MODULE: {module_name}
FILES:
{file_list}

CURRENT PATTERNS:
{patterns}

ALREADY IMPLEMENTED (DO NOT REPEAT):
{already_implemented}

Consider:
- Is there duplicated logic that should be extracted?
- Are there circular dependencies?
- Could a design pattern (Factory, Observer, Strategy) simplify the code?
- What abstraction layer is missing?
- AVOID: error handlers, logging wrappers, health checks (already saturated)

OUTPUT:
```json
{{
    "title": "Improvement name",
    "description": "What to change and why",
    "target_file": "which file to modify or create",
    "pattern": "Which design pattern to apply"
}}
```

Then provide the implementation:
```python
# Your code here
```""",

    "reasoning_optimizer": """You are improving the REASONING and DECISION-MAKING layer of an autonomous AI agent.

TARGET FILES (reasoning/thinking layer):
{file_list}

CURRENT CAPABILITIES:
- NeuralBridge: LLM communication and model selection
- WorldModel: Belief tracking and falsification
- Dreamer: Goal discovery and planning
- CognitiveTrace/Journal: Tracking the agent's thought history
- InnovationEngine: Code generation and self-improvement

ALREADY IMPLEMENTED (DO NOT REPEAT):
{already_implemented}

Suggest ONE improvement to the reasoning/thinking pipeline:
- Confidence calibration (reduce overconfident actions)
- Multi-hypothesis reasoning (consider multiple outcomes before deciding)
- Temporal reasoning (how does the system state evolve over time?)
- Causal reasoning (WHY did a task fail, instead of just THAT it failed)
- Meta-cognition (agent evaluates quality of its own reasoning before acting)
- Bayesian belief updates (update conviction with new evidence)
- Adversarial thinking (what could go wrong with this system change?)

CRITICAL: Create the new improvement as a NEW FILE in: unified_core/intelligence/

OUTPUT FORMAT:
```json
{{
    "title": "Reasoning improvement name",
    "description": "What it does and how it improves decision quality",
    "target_file": "unified_core/intelligence/new_reasoning_module.py",
    "rationale": "How this reduces bad decisions or improves thinking"
}}
```

Then provide the complete implementation:
```python
# Your code here
```""",

    "storage_improver": """You are improving the DATA STORAGE and PERSISTENCE layer of an autonomous AI system.

TARGET FILES (database/storage layer):
{file_list}

CURRENT STORAGE CAPABILITIES:
- SQLite via MemoryStore (beliefs, predictions, observations)
- Evolution ledger (JSONL append-only log)
- Instincts (JSON file-based persistence)
- File-based code storage for innovations

ALREADY IMPLEMENTED (DO NOT REPEAT):
{already_implemented}

Suggest ONE improvement to the storage/database layer:
- Query optimizer for MemoryStore (index hot columns)
- Time-series storage for trade history (efficient candle storage)
- Snapshot/checkpoint system (save full system state periodically)
- Data compaction (archive old ledger entries, prune stale beliefs)
- Caching layer (LRU cache for frequent DB reads)
- Migration system (schema versioning for SQLite)
- Backup rotation (automatic daily backups with retention policy)
- Metrics persistence (store CPU/memory/trade stats over time)
- Knowledge graph storage (link innovations, beliefs, and outcomes)

CRITICAL: Create the new improvement as a NEW FILE in: unified_core/db/

OUTPUT FORMAT:
```json
{{
    "title": "Storage improvement name",
    "description": "What it does and why it improves data management",
    "target_file": "unified_core/db/new_storage_module.py",
    "rationale": "How this improves reliability, performance, or data integrity"
}}
```

Then provide the complete implementation:
```python
# Your code here
```""",

    "deep_refactor": """You are an expert software engineer reviewing and improving EXISTING code.

FILE: {file_path}

CURRENT CODE:
```python
{file_content}
```

Your task: IMPROVE this existing file. You must make MEANINGFUL, DEEP changes — not cosmetic.
You should return the ENTIRE file content with your improvements applied.

OUTPUT FORMAT:
```json
{{
    "title": "Improvement: [what you improved]",
    "description": "What changed and WHY it matters",
    "improvement_type": "algorithm|robustness|performance|integration|intelligence"
}}
```

Then provide the COMPLETE improved function with the EXACT SAME signature:
```python
def {function_name}(...):  # Keep exact same signature
    # Your improved implementation
```

CRITICAL: Return ONLY the improved function body. Same signature, better internals."""
}

# ── Self-Evolving Prompt Loader ──
# Loads prompts from external YAML file so the system can evolve them.
# Falls back to hardcoded INNOVATION_PROMPTS if YAML is missing or broken.

_PROMPTS_YAML_PATH = Path(__file__).resolve().parents[2] / "config" / "innovation_prompts.yaml"
_prompts_cache: Dict[str, str] = {}
_prompts_cache_mtime: float = 0.0

def _load_prompts() -> Dict[str, str]:
    """Load prompts from YAML with hot-reload on file change.
    
    Falls back to hardcoded INNOVATION_PROMPTS if YAML fails.
    Reloads automatically when the YAML file is modified.
    """
    global _prompts_cache, _prompts_cache_mtime
    
    try:
        if _PROMPTS_YAML_PATH.exists():
            mtime = _PROMPTS_YAML_PATH.stat().st_mtime
            if mtime != _prompts_cache_mtime or not _prompts_cache:
                with open(_PROMPTS_YAML_PATH, 'r', encoding='utf-8') as f:
                    loaded = yaml.safe_load(f)
                if isinstance(loaded, dict) and len(loaded) >= 3:
                    _prompts_cache = loaded
                    _prompts_cache_mtime = mtime
                    logger.info(f"📝 Loaded {len(loaded)} prompts from YAML (self-evolvable)")
                    return _prompts_cache
    except Exception as e:
        logger.warning(f"Failed to load prompts YAML: {e} — using hardcoded")
    
    if _prompts_cache:
        return _prompts_cache
    return INNOVATION_PROMPTS

def get_prompt(name: str) -> str:
    """Get a prompt by name — loads from YAML if available."""
    prompts = _load_prompts()
    return prompts.get(name, INNOVATION_PROMPTS.get(name, ""))


class InnovationEngine:
    """
    Creative feature generation engine powered by the Brain (32B).
    
    Unlike BrainAssistedRefactoring which fixes existing code,
    this engine invents NEW capabilities.
    """
    
    def __init__(self):
        self.ledger = get_evolution_ledger()
        self.code_analyzer = get_code_analyzer()
        self._innovations: List[Innovation] = []
        self._total_innovations = 0
        self._successful_innovations = 0
        self._cooldown_hours = 2  # Min hours between same innovation type
        self._last_innovation_time: Dict[str, float] = {}

        # Project root
        self._src_root = Path(__file__).parent.parent.parent  # src/

        # v16: Instinct system — continuous learning from outcomes
        try:
            from .instinct_system import get_instinct_advisor
            self._instinct_advisor = get_instinct_advisor()
        except Exception as e:
            logger.warning(f"InstinctAdvisor unavailable: {e}")
            self._instinct_advisor = None

        logger.info("🚀 InnovationEngine initialized")
    
    def _get_project_structure(self) -> str:
        """Get a summary of the project structure."""
        structure_lines = []
        
        for module_dir in sorted(self._src_root.iterdir()):
            if module_dir.is_dir() and not module_dir.name.startswith(('.', '_')):
                py_files = list(module_dir.rglob("*.py"))
                py_files = [f for f in py_files if '__pycache__' not in str(f)]
                if py_files:
                    structure_lines.append(f"\n📁 {module_dir.name}/ ({len(py_files)} files)")
                    for f in sorted(py_files)[:5]:  # Max 5 per module
                        rel = f.relative_to(self._src_root)
                        structure_lines.append(f"  - {rel}")
                    if len(py_files) > 5:
                        structure_lines.append(f"  ... and {len(py_files) - 5} more")
        
        return "\n".join(structure_lines)
    
    def _get_recent_changes(self) -> str:
        """Get recent evolution changes from the ledger (last 10, for context)."""
        recent = []
        for pid, proposal in self.ledger.proposals.items():
            if proposal.status == ProposalStatus.PROMOTED:
                recent.append(f"- {proposal.description}")

        return "\n".join(recent[-10:]) if recent else "No recent changes"

    def _get_promoted_titles(self) -> List[str]:
        """Return all promoted innovation titles for semantic dedup."""
        titles = []
        for pid, proposal in self.ledger.proposals.items():
            if proposal.status == ProposalStatus.PROMOTED:
                # Strip "[INNOVATION] " prefix if present
                desc = proposal.description or ""
                if desc.startswith("[INNOVATION] "):
                    desc = desc[len("[INNOVATION] "):]
                titles.append(desc.lower())
        return titles

    def _get_existing_module_names(self) -> List[str]:
        """v18: Scan filesystem for existing .py module names.

        Survives ledger resets — reads actual files on disk.
        Returns module names as lowercase word-lists for keyword matching.
        """
        names = []
        try:
            for py_file in self._src_root.rglob("*.py"):
                # Skip __pycache__, .venv, tests, __init__
                parts_str = str(py_file)
                if any(skip in parts_str for skip in
                       ('__pycache__', '.venv', 'venv/', 'site-packages',
                        '__init__', '/tests/', '/test_')):
                    continue
                stem = py_file.stem  # e.g. 'config_management_utility'
                names.append(stem.lower())
        except Exception as e:
            logger.warning(f"⚠️ Disk scan failed: {e}")
        return names

    def _is_semantically_duplicate(self, title: str, description: str = "",
                                    cycle_titles: set = None) -> bool:
        """Check if a proposed innovation is semantically duplicate of existing ones.

        v18: Keyword-cluster matching + in-cycle dedup + DISK-BASED dedup.

        Rejects if ANY of these conditions:
        0. Title overlaps with something already generated THIS cycle
        0.5 Title keywords overlap with an existing .py file on disk (v18)
        1. Exact title match (case-insensitive)
        2. >60% keyword overlap with an existing promoted title
        3. Known high-saturation concept (error_handler, logging, health_check)
           already has ≥3 promoted variants
        """
        # Normalize candidate
        candidate = (title + " " + description).lower()
        candidate_words = set(candidate.replace("_", " ").split())
        stop = {"a", "an", "the", "for", "in", "of", "to", "and", "or",
                "is", "be", "with", "by", "from", "that", "this", "as",
                "tests", "test", "utility", "manager", "handler"}

        # v17: In-cycle dedup — check against titles generated in THIS pipeline run
        if cycle_titles:
            for ct in cycle_titles:
                ct_words = set(ct.lower().replace("_", " ").split()) - stop
                overlap = (candidate_words - stop) & ct_words
                if ct_words and overlap and len(overlap) / len(ct_words) > 0.5:
                    logger.info(f"🔁 In-cycle dedup: '{title}' overlaps with cycle title '{ct}'")
                    return True

        # v18: Disk-based dedup — check against existing .py files on filesystem
        # This survives ledger resets after service restarts
        # v21: Relaxed — require ≥3 real keywords and ≥80% overlap (was 60%)
        existing_modules = self._get_existing_module_names()
        # Expanded stop words: generic module terms that don't indicate real duplication
        module_stop = stop | {
            "module", "system", "engine", "service", "client", "server",
            "improved", "advanced", "enhanced", "new", "refactor", "refactored",
            "base", "core", "main", "common", "shared", "general", "simple",
            "create", "build", "make", "get", "set", "update", "delete",
            "data", "file", "config", "configuration", "management",
        }
        candidate_meaningful = candidate_words - module_stop
        for module_name in existing_modules:
            module_words = set(module_name.replace("_", " ").split()) - module_stop
            if not module_words or len(module_words) < 2:
                continue
            overlap = candidate_meaningful & module_words
            # v21: Only reject if ≥3 keywords overlap AND ≥80% of module words match
            if len(overlap) >= 3 and len(overlap) / len(module_words) >= 0.8:
                logger.info(f"🔁 Disk dedup: '{title}' overlaps with existing module '{module_name}' "
                            f"({len(overlap)}/{len(module_words)} keywords)")
                return True

        promoted = self._get_promoted_titles()

        # 1. Exact match
        title_lower = title.lower()
        if title_lower in promoted:
            logger.info(f"🔁 Dedup: exact title match '{title}'")
            return True

        # 2. Keyword overlap (Jaccard-like)
        # v21: Relaxed from 0.65 to 0.75 — allow more unique innovations
        for existing in promoted:
            existing_words = set(existing.replace("_", " ").split())
            if not existing_words:
                continue
            intersection = candidate_words & existing_words
            # Remove stop-words that don't add meaning
            stop = {"a", "an", "the", "for", "in", "of", "to", "and", "or",
                    "is", "be", "with", "by", "from", "that", "this", "as"}
            intersection -= stop
            meaningful_existing = existing_words - stop
            if meaningful_existing and len(intersection) / len(meaningful_existing) > 0.75:
                logger.info(f"🔁 Dedup: keyword overlap {len(intersection)}/{len(meaningful_existing)} "
                            f"with '{existing}' vs new '{title}'")
                return True

        # 3. High-saturation concepts — count how many promoted variants exist
        saturation_keywords = {
            "error_handler": 3,
            "error handler": 3,
            "centralized_logging": 3,
            "centralized logging": 3,
            "logging_util": 3,
            "logging util": 2,
            "health_check": 3,
            "health check": 3,
            "circuit_breaker": 2,
            "circuit breaker": 2,
            "retry": 3,
            "cache": 3,
            "monitor": 3,
        }
        for kw, limit in saturation_keywords.items():
            count = sum(1 for t in promoted if kw in t)
            if kw in candidate and count >= limit:
                logger.info(f"🔁 Dedup: saturation limit reached for '{kw}' ({count}/{limit})")
                return True

        return False
    
    def _get_capabilities(self) -> str:
        """Summary of system capabilities — focused on autonomy and intelligence."""
        # Read system stats
        try:
            total_promoted = sum(1 for p in self.ledger.proposals.values() if p.status == ProposalStatus.PROMOTED)
            system_stats = f"Live stats: {total_promoted} total innovations promoted."
        except Exception:
            system_stats = "System stats unavailable"

        return f"""
SYSTEM CAPABILITIES (NOOGH):
- NeuralBridge: LLM communication and model selection (Local/Remote)
- WorldModel: Belief tracking and falsification in SQLite
- Dreamer: Goal discovery and planning
- InnovationEngine: Code generation and self-improvement
- DataRouter: PostgreSQL/VectorDB multi-routing orchestration
- Gateway: FastAPI external interaction layer
- CyberSecurity/Autonomy: Defensive security tracking and healing
- {system_stats}

CURRENT WEAKNESSES (focus innovation here):
- Resource governing is too primitive for complex logic
- Long-term memory compression/summarization is lacking
- Multi-agent or thread spawning isn't fully robust
- Emotional/state-based context shifting is minimal
- Automated healing of broken packages isn't proactive
"""
    
    def _pick_random_function(self) -> Optional[Dict[str, Any]]:
        """Pick a random function from across the entire system codebase."""
        try:
            py_files = list(self._src_root.rglob("*.py"))
            skip_patterns = {
                '__pycache__', 'test', '.backup', '.venv', 'venv',
                '.noogh_venv', '.gemini', 'mcp_server',
                'site-packages', 'node_modules', 'dist', 'build',
                'egg-info', '.orig', '.rej', 'migrations',
                '.venv-training', 'training/', 'check_files.py', 'review_ai.py'
            }
            py_files = [f for f in py_files
                       if not any(skip in str(f) for skip in skip_patterns)]

            if not py_files:
                return None

            # Try up to 5 random files to find one with functions
            for _ in range(5):
                random_file = random.choice(py_files)
                analysis = self.code_analyzer.analyze_file(str(random_file))
                
                if analysis.functions:
                    func = random.choice(analysis.functions)
                    
                    # Read function code
                    try:
                        with open(random_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        code = ''.join(lines[func.start_line-1:func.end_line])
                    except Exception:
                        continue
                    
                    return {
                        "file_path": str(random_file),
                        "function_name": func.name,
                        "code": code,
                        "start_line": func.start_line,
                        "end_line": func.end_line
                    }
            
            return None
        except Exception as e:
            logger.error(f"Failed to pick random function: {e}")
            return None
    
    def _build_memory_context(self, target_area: str = None) -> str:
        """v21: Build memory context from past evolution outcomes.
        
        Injects into Brain prompt so it learns from:
        - Recent failures for this target area
        - Overall success patterns (what works)
        - Fragile files to avoid
        """
        try:
            from .evolution_memory import get_evolution_memory
            memory = get_evolution_memory()
        except Exception:
            return ""

        sections = []

        # 1. Recent failures for this target
        if target_area:
            failures = memory.get_recent_failures(target_area, limit=3)
            if failures:
                fail_lines = "\n".join(f"  - {f[:120]}" for f in failures)
                sections.append(
                    f"⚠️ PAST FAILURES for '{target_area}':\n{fail_lines}\n"
                    f"DO NOT repeat these patterns."
                )

        # 2. Success patterns
        patterns = memory.get_success_patterns()
        if patterns and patterns.get("top_types"):
            top = patterns["top_types"][:3]
            overall = patterns.get("overall_success_rate", 0)
            lines = [f"  - {t['type']}: {t['rate']:.0%} success ({t['total']} attempts)"
                     for t in top]
            sections.append(
                f"📊 YOUR SUCCESS PATTERNS (overall {overall:.0%}):\n" +
                "\n".join(lines) + "\n"
                f"Prioritize approaches similar to high-success types."
            )

        # 3. Fragile files warning
        if target_area and memory.should_skip_target(target_area):
            sections.append(
                f"🚨 '{target_area}' is marked FRAGILE — "
                f"be extra conservative, minimal changes only."
            )

        if not sections:
            return ""

        return "\n\n[MEMORY — LEARN FROM PAST]\n" + "\n\n".join(sections)

    async def _call_brain(self, prompt: str, system_prompt: str = None,
                          target_area: str = None) -> Optional[str]:
        """Call the Brain (32B) with a creative prompt.
        
        v21: Injects memory context so Brain learns from past outcomes.
        """
        client = None
        try:
            from ..neural_bridge import NeuralEngineClient
            import os
            # v5.1: Use Teacher 32B (same as brain_refactor) — not local 7B
            teacher_url = os.getenv("NOOGH_TEACHER_URL", os.getenv("NEURAL_ENGINE_URL"))
            teacher_mode = os.getenv("NOOGH_TEACHER_MODE", os.getenv("NEURAL_ENGINE_MODE", "local"))
            client = NeuralEngineClient(base_url=teacher_url, mode=teacher_mode)
            
            # v21: Build memory context
            memory_ctx = self._build_memory_context(target_area)
            
            base_system = system_prompt or (
                "You are NOOGH, a creative AI system architect. "
                "You design novel features and find real bugs. "
                "Be specific, practical, and innovative. "
                "Output working Python code when asked."
            )
            
            # Append memory to system prompt
            if memory_ctx:
                base_system += f"\n\n{memory_ctx}"
            
            messages = [
                {"role": "system", "content": base_system},
                {"role": "user", "content": prompt}
            ]
            
            result = await client.complete(messages, max_tokens=1024, timeout=600)
            
            if result.get("success") and result.get("content"):
                return result["content"]
            else:
                logger.warning(f"Brain call failed: {result.get('error', 'Unknown')}")
                return None
                
        except Exception as e:
            logger.error(f"Brain call error: {e}")
            return None
        finally:
            # v11: Close session to prevent leaks
            if client:
                await client.close()
    
    async def discover_missing_feature(self) -> Optional[Innovation]:
        """Ask the Brain what feature is missing from the project."""
        if not self._can_innovate("missing_feature"):
            return None
        
        # v16: Include already-implemented list + instinct guidance
        _already = self._get_promoted_titles()
        _already_str = "\n".join(f"- {t}" for t in _already[-20:]) if _already else "- (none yet)"

        # Append instinct guidance to prompt if available
        _instinct_block = ""
        if self._instinct_advisor:
            _guidance = self._instinct_advisor.get_guidance(domain="feature")
            if _guidance:
                _instinct_block = f"\n\n{_guidance}"

        prompt = get_prompt("missing_feature").format(
            project_structure=self._get_project_structure(),
            capabilities=self._get_capabilities(),
            recent_changes=self._get_recent_changes(),
            already_implemented=_already_str
        ) + _instinct_block

        response = await self._call_brain(prompt, target_area="missing_feature")
        if not response:
            return None

        # v19: Default target is intelligence directory, not shared/
        intel_dir = self._src_root / "unified_core/intelligence"
        intel_dir.mkdir(parents=True, exist_ok=True)
        default_file = str(intel_dir / f"system_feature_{int(time.time())}.py")

        innovation = self._parse_innovation_response(
            response, "feature",
            default_file=default_file
        )
        if innovation:
            self._record_innovation(innovation)
            # Record for distillation
            self._record_distillation(prompt, response, innovation)
            # v16: Record observation for instinct learning
            if self._instinct_advisor:
                self._instinct_advisor.observer.record(
                    event_type="generated",
                    proposal_id=innovation.innovation_id,
                    innovation_type="feature",
                    title=innovation.title,
                    target_file=innovation.target_file or "",
                    lines_of_code=len(innovation.generated_code.splitlines()),
                )
        
        return innovation
    
    async def hunt_bugs(self) -> Optional[Innovation]:
        """Proactively scan a random function for real bugs."""
        if not self._can_innovate("bug_hunter"):
            return None
        
        target = self._pick_random_function()
        if not target:
            logger.info("No suitable function found for bug hunting")
            return None
        
        prompt = get_prompt("bug_hunter").format(
            file_path=target["file_path"],
            function_name=target["function_name"],
            code=target["code"]
        )
        
        response = await self._call_brain(prompt, target_area=target["file_path"])
        if not response:
            return None
        
        # Check if no bugs found
        if "NO_BUGS_FOUND" in response:
            logger.info(f"🐛 No bugs in {target['function_name']} — clean!")
            self._last_innovation_time["bug_hunter"] = time.time()
            return None
        
        innovation = self._parse_innovation_response(
            response, "bug_fix",
            default_file=target["file_path"],
            default_title=f"Bug fix in {target['function_name']}"
        )
        
        if innovation:
            innovation.metadata = {
                "original_function": target["function_name"],
                "original_file": target["file_path"],
                "start_line": target["start_line"],
                "end_line": target["end_line"]
            }
            self._record_innovation(innovation)
            self._record_distillation(prompt, response, innovation)
        
        return innovation
    
    async def generate_tests(self) -> Optional[Innovation]:
        """Generate unit tests for a random function."""
        if not self._can_innovate("test_generator"):
            return None
        
        target = self._pick_random_function()
        if not target:
            return None
        
        prompt = get_prompt("test_generator").format(
            file_path=target["file_path"],
            function_name=target["function_name"],
            code=target["code"]
        )
        
        response = await self._call_brain(prompt, target_area=target["file_path"])
        if not response:
            return None
        
        # Extract code from response
        code = self._extract_code(response)
        if not code or "def test_" not in code:
            logger.info("Test generation didn't produce valid tests")
            return None
        
        # Determine test file path
        # v19: Guard against recursive nesting — never target a file already in tests/
        original_path = Path(target["file_path"])
        if '/tests/' in str(original_path) or original_path.name.startswith('test_'):
            logger.info(f"🚫 Skipping test-of-test: {original_path.name}")
            return None
        test_dir = original_path.parent / "tests"
        test_file = test_dir / f"test_{original_path.stem}.py"
        
        innovation = Innovation(
            innovation_id=f"innovation_test_{int(time.time())}",
            title=f"Tests for {target['function_name']}",
            description=f"Unit tests for {target['function_name']} in {original_path.name}",
            innovation_type="test",
            target_file=str(test_file),
            generated_code=code,
            rationale=f"Automated test generation for {target['function_name']}",
            confidence=0.7
        )
        
        self._record_innovation(innovation)
        self._record_distillation(prompt, response, innovation)
        
        return innovation
    
    async def review_architecture(self, module_name: str = None) -> Optional[Innovation]:
        """Review a module's architecture and suggest improvements."""
        if not self._can_innovate("architecture_review"):
            return None
        
        # Pick a module
        if not module_name:
            modules = [d.name for d in self._src_root.iterdir() 
                      if d.is_dir() and not d.name.startswith(('.', '_', 'data'))]
            if not modules:
                return None
            module_name = random.choice(modules)
        
        module_path = self._src_root / module_name
        py_files = list(module_path.rglob("*.py"))
        py_files = [f for f in py_files if '__pycache__' not in str(f)]
        
        file_list = "\n".join(f"  - {f.relative_to(self._src_root)}" for f in py_files[:15])
        
        # Detect patterns
        patterns = []
        for f in py_files[:10]:
            try:
                content = f.read_text(encoding='utf-8')
                if "class " in content and "def __init__" in content:
                    patterns.append(f"OOP: {f.name}")
                if "async def " in content:
                    patterns.append(f"Async: {f.name}")
                if "@dataclass" in content:
                    patterns.append(f"Dataclass: {f.name}")
                if "Singleton" in content or "_instance" in content:
                    patterns.append(f"Singleton: {f.name}")
            except Exception:
                continue
        
        # v16: Include already-implemented list
        _already = self._get_promoted_titles()
        _already_str = "\n".join(f"- {t}" for t in _already[-20:]) if _already else "- (none yet)"
        prompt = get_prompt("architecture_review").format(
            module_name=module_name,
            file_list=file_list,
            patterns="\n".join(patterns[:10]) or "No special patterns detected",
            already_implemented=_already_str
        )
        
        response = await self._call_brain(prompt, target_area=module_name)
        if not response:
            return None
        
        # v13c: Provide a default file path under the module
        default_file = str(module_path / f"architecture_{int(time.time())}.py")
        
        innovation = self._parse_innovation_response(
            response, "architecture",
            default_file=default_file,
            default_title=f"Architecture improvement for {module_name}"
        )
        
        if innovation:
            self._record_innovation(innovation)
            self._record_distillation(prompt, response, innovation)
        
        return innovation

    async def optimize_reasoning(self) -> Optional[Innovation]:
        """v20: Improve the reasoning/thinking pipeline."""
        if not self._can_innovate("reasoning_optimizer"):
            return None

        reasoning_files = []
        for d in [self._src_root / "unified_core/intelligence",
                  self._src_root / "unified_core/core"]:
            if d.exists():
                reasoning_files += [f for f in d.rglob("*.py")
                                    if '__pycache__' not in str(f)
                                    and '/tests/' not in str(f)]
        for f in [self._src_root / "unified_core/agent_daemon.py",
                  self._src_root / "unified_core/neural_bridge.py",
                  self._src_root / "unified_core/evolution/innovation_engine.py",
                  self._src_root / "unified_core/evolution/instinct_system.py"]:
            if f.exists():
                reasoning_files.append(f)

        file_list = "\n".join(f"  - {f.relative_to(self._src_root)}" for f in reasoning_files[:15])
        _already = self._get_promoted_titles()
        _already_str = "\n".join(f"- {t}" for t in _already[-20:]) if _already else "- (none yet)"

        prompt = get_prompt("reasoning_optimizer").format(
            file_list=file_list, already_implemented=_already_str
        )
        response = await self._call_brain(prompt, target_area="reasoning")
        if not response:
            return None

        default_file = str(self._src_root / f"unified_core/intelligence/reasoning_{int(time.time())}.py")
        innovation = self._parse_innovation_response(
            response, "feature", default_file=default_file,
            default_title="Reasoning optimization"
        )
        if innovation:
            self._record_innovation(innovation)
            self._record_distillation(prompt, response, innovation)
        return innovation

    async def improve_storage(self) -> Optional[Innovation]:
        """v20: Improve the database/storage/persistence layer."""
        if not self._can_innovate("storage_improver"):
            return None

        storage_files = []
        for d in [self._src_root / "unified_core/db",
                  self._src_root / "unified_core/ml"]:
            if d.exists():
                storage_files += [f for f in d.rglob("*.py")
                                  if '__pycache__' not in str(f)
                                  and '/tests/' not in str(f)]
        for f in [self._src_root / "unified_core/state.py",
                  self._src_root / "unified_core/evolution/evolution_memory.py",
                  self._src_root / "unified_core/evolution/ledger.py"]:
            if f.exists():
                storage_files.append(f)

        file_list = "\n".join(f"  - {f.relative_to(self._src_root)}" for f in storage_files[:15])
        _already = self._get_promoted_titles()
        _already_str = "\n".join(f"- {t}" for t in _already[-20:]) if _already else "- (none yet)"

        prompt = get_prompt("storage_improver").format(
            file_list=file_list, already_implemented=_already_str
        )
        response = await self._call_brain(prompt, target_area="storage")
        if not response:
            return None

        default_file = str(self._src_root / f"unified_core/db/storage_{int(time.time())}.py")
        innovation = self._parse_innovation_response(
            response, "feature", default_file=default_file,
            default_title="Storage improvement"
        )
        if innovation:
            self._record_innovation(innovation)
            self._record_distillation(prompt, response, innovation)
        return innovation

    async def deep_refactor(self) -> Optional[Innovation]:
        """Read an existing function and improve it in-place.
        
        Unlike other innovation types that create new files,
        this one MODIFIES existing code — the deepest form of evolution.
        """
        if not self._can_innovate("deep_refactor"):
            return None
        
        target = self._pick_random_function()
        if not target:
            logger.info("No suitable function found for deep refactoring")
            return None
        
        target_name = target.get("function_name", target.get("file_path", "unknown target"))
        
        # Skip very short functions (< 5 lines) — not worth refactoring
        code_lines = target.get("code", "").strip().splitlines()
        if len(code_lines) < 5:
            logger.info(f"⏭️ Skipping {target_name} — too short ({len(code_lines)} lines)")
            return None
        
        # We will refactor the ENTIRE file where this random function resides.
        file_path = Path(target["file_path"])
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                full_file_content = f.read()
        except Exception as e:
            logger.warning(f"Could not read {file_path} for deep refactor: {e}")
            return None
            
        # Already implemented list for dedup
        _already = self._get_promoted_titles()
        _already_str = "\n".join(f"- {t}" for t in _already[-20:]) if _already else "- (none yet)"
        
        prompt = get_prompt("deep_refactor").format(
            file_path=str(file_path),
            file_content=full_file_content
        )
        
        response = await self._call_brain(prompt, target_area=str(file_path))
        if not response:
            return None
        
        # Check if Brain couldn't improve it
        if "NO_IMPROVEMENT" in response or "already optimal" in response.lower():
            logger.info(f"✅ {file_path.name} — already optimal!")
            self._last_innovation_time["deep_refactor"] = time.time()
            return None
        
        innovation = self._parse_innovation_response(
            response, "refactor",
            default_file=str(file_path),
            default_title=f"Refactor: {file_path.name}"
        )
        
        if innovation:
            # Set target_file to existing file (not a new file)
            innovation.target_file = str(file_path)
            # Critical: Set metadata so _create_proposal does in-place replacement
            innovation.metadata = {
                "original_file": str(file_path),
                "original_code": full_file_content
            }
            self._record_innovation(innovation)
            self._record_distillation(prompt, response, innovation)
            
            # Record for instinct learning
            if self._instinct_advisor:
                self._instinct_advisor.observer.record(
                    event_type="generated",
                    proposal_id=innovation.innovation_id,
                    innovation_type="refactor",
                    title=innovation.title,
                    target_file=target["file_path"],
                    lines_of_code=len(innovation.generated_code.splitlines()),
                )
            
            logger.info(
                f"🔧 Deep refactor: {target_name} in "
                f"{Path(target['file_path']).name} → {len(innovation.generated_code.splitlines())} lines"
            )
        
        return innovation

    async def run_innovation_cycle(self, max_innovations: int = 2) -> Dict[str, Any]:
        """
        v16: Orchestrated Innovation Pipeline — inspired by affaan-m/everything-claude-code.

        Instead of random selection, uses instinct-guided ordering:
        1. Preferred type (from past successes) runs first
        2. Each innovation goes through: generate → handoff → record
        3. Observations feed back into InstinctAdvisor for next cycle

        Handoff document is created between generation and proposal recording
        to track context across pipeline stages.
        """
        results = {
            "innovations": [],
            "total_attempted": 0,
            "total_succeeded": 0,
            "handoffs": [],   # v16: track handoff docs
        }

        # v17: Track titles generated within THIS cycle to prevent same-concept duplication
        _cycle_titles: set = set()
        self._active_cycle_titles = _cycle_titles  # expose to _parse_innovation_response

        # v21: Diversity-enforced pipeline — break test-dominated feedback loop
        # 7 pipeline tasks with diversity-weighted rotation
        all_methods = [
            ("deep_refactor",       "refactor",     self.deep_refactor),
            ("missing_feature",     "feature",      self.discover_missing_feature),
            ("bug_hunter",          "bug_fix",       self.hunt_bugs),
            ("test_generator",      "test",          self.generate_tests),
            ("architecture_review", "architecture", self.review_architecture),
            ("reasoning_optimizer", "reasoning",  self.optimize_reasoning),
            ("storage_improver",    "storage",    self.improve_storage),
        ]

        # v21: Diversity enforcement — if one type dominates, suppress it
        _recent_types = self._get_recent_promotion_types(last_n=50)
        _total_recent = max(sum(_recent_types.values()), 1)
        _test_ratio = _recent_types.get("test", 0) / _total_recent

        if _test_ratio > 0.5:
            # Tests over-represented → force diverse types first
            non_test = [m for m in all_methods if m[1] != "test"]
            test_methods = [m for m in all_methods if m[1] == "test"]
            random.shuffle(non_test)
            ordered = non_test + test_methods
            logger.info(
                f"🎯 Diversity mode: tests={_test_ratio:.0%} of recent — "
                f"suppressing tests, ordering: {[m[0] for m in ordered]}"
            )
        else:
            # Balanced — normal rotation with deep_refactor lead
            lead = [m for m in all_methods if m[0] == "deep_refactor"]
            rest = [m for m in all_methods if m[0] != "deep_refactor"]
            random.shuffle(rest)
            ordered = lead + rest
            logger.info(f"🧠 Balanced pipeline: {[m[0] for m in ordered]}")

        for name, _domain, method in ordered:
            if results["total_succeeded"] >= max_innovations:
                break

            results["total_attempted"] += 1
            _start = time.time()

            try:
                logger.info(f"💡 Innovation attempt: {name}")
                innovation = await method()

                if innovation:
                    results["innovations"].append(innovation.to_dict())
                    results["total_succeeded"] += 1

                    # v17: Track this title so next pipeline step won't duplicate it
                    _cycle_titles.add(innovation.title)

                    # ── Handoff Document (inspired by orchestrate command) ──
                    handoff = self._create_handoff(name, innovation, results)
                    results["handoffs"].append(handoff)
                    logger.info(f"📋 Handoff: {handoff['summary']}")

                    # Create evolution proposal
                    proposal = self._create_proposal(innovation)
                    if proposal:
                        success, _ = self.ledger.record_proposal(proposal)
                        if success:
                            logger.info(f"🚀 Innovation proposal created: {innovation.title}")

                    # v16: Record observation (use domain alias so instinct types match)
                    if self._instinct_advisor:
                        self._instinct_advisor.observer.record(
                            event_type="proposed",
                            proposal_id=innovation.innovation_id,
                            innovation_type=_domain,
                            title=innovation.title,
                            target_file=innovation.target_file or "",
                            lines_of_code=len(innovation.generated_code.splitlines()),
                            duration_sec=time.time() - _start,
                        )

            except Exception as e:
                logger.error(f"Innovation {name} failed: {e}")
                if self._instinct_advisor:
                    self._instinct_advisor.observer.record(
                        event_type="failed",
                        proposal_id=f"innovation_{name}_{int(time.time())}",
                        innovation_type=_domain,
                        title=f"Failed: {name}",
                        target_file="",
                        error=str(e),
                        duration_sec=time.time() - _start,
                    )

        logger.info(
            f"💡 Innovation cycle: {results['total_succeeded']}/{results['total_attempted']} succeeded"
        )

        # v17: Clear cycle-scoped dedup set
        self._active_cycle_titles = None

        # v16: Trigger instinct evolution after each cycle
        if self._instinct_advisor:
            count = self._instinct_advisor.evolve(force=True)
            logger.info(f"🧬 Instincts updated: {count} patterns learned")

        return results

    def _create_handoff(
        self,
        stage: str,
        innovation: Innovation,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a structured handoff document between pipeline stages.
        Inspired by affaan-m/everything-claude-code orchestrate command.

        The handoff captures:
        - What this stage produced
        - Key metadata for the next stage
        - Open questions / risks
        """
        succeeded_so_far = context.get("total_succeeded", 0)
        return {
            "from_stage": stage,
            "to_stage": "evolution_controller",
            "timestamp": time.time(),
            "summary": f"{stage} → {innovation.title[:50]} ({len(innovation.generated_code.splitlines())} lines)",
            "context": {
                "innovation_type": innovation.innovation_type,
                "title": innovation.title,
                "target_file": innovation.target_file,
                "confidence": innovation.confidence,
                "rationale": innovation.rationale[:100] if innovation.rationale else "",
            },
            "findings": {
                "code_lines": len(innovation.generated_code.splitlines()),
                "has_target_file": bool(innovation.target_file),
                "target_exists": os.path.exists(innovation.target_file) if innovation.target_file else False,
            },
            "open_questions": [
                "Will canary test pass syntax validation?",
                "Does code avoid policy gate violations?",
            ] if innovation.confidence < 0.8 else [],
            "pipeline_position": f"{succeeded_so_far + 1}/{context.get('total_attempted', 1)}",
        }
    
    def _get_recent_promotion_types(self, last_n: int = 50) -> Dict[str, int]:
        """Count innovation types in the most recent N promoted observations.
        
        v21: Used by run_innovation_cycle to detect over-represented types
        and enforce diversity in the pipeline ordering.
        
        Optimization: reads only the last ~500 lines of observations.jsonl
        instead of loading the entire file (6K+ lines) to avoid blocking.
        """
        type_counts: Dict[str, int] = {}
        try:
            obs_file = Path.home() / ".noogh" / "evolution" / "observations.jsonl"
            if not obs_file.exists():
                return type_counts
            
            # Read only tail of file — efficient for large files
            from collections import deque
            recent_lines = deque(maxlen=500)
            with open(obs_file, 'r', encoding='utf-8') as f:
                for line in f:
                    recent_lines.append(line)
            
            promoted_count = 0
            for line in reversed(recent_lines):
                if promoted_count >= last_n:
                    break
                try:
                    d = json.loads(line.strip())
                    if d.get("event_type") == "promoted":
                        itype = d.get("innovation_type", "unknown")
                        type_counts[itype] = type_counts.get(itype, 0) + 1
                        promoted_count += 1
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"_get_recent_promotion_types failed: {e}")
        return type_counts

    def _can_innovate(self, innovation_type: str) -> bool:
        """Check cooldown for innovation type."""
            
        last = self._last_innovation_time.get(innovation_type, 0)
        elapsed_hours = (time.time() - last) / 3600
        
        if elapsed_hours < self._cooldown_hours:
            logger.debug(
                f"Innovation {innovation_type} on cooldown "
                f"({elapsed_hours:.1f}h < {self._cooldown_hours}h)"
            )
            return False
        
        return True
    
    def _parse_innovation_response(self, response: str, innovation_type: str,
                                    default_file: str = "",
                                    default_title: str = "") -> Optional[Innovation]:
        """Parse Brain response into an Innovation object."""
        try:
            # Try to extract JSON metadata
            title = default_title or f"Innovation: {innovation_type}"
            description = ""
            target_file = default_file
            rationale = ""
            
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                if json_end > json_start:
                    try:
                        meta = json.loads(response[json_start:json_end].strip())
                        title = meta.get("title", title)
                        description = meta.get("description", "")
                        target_file = meta.get("target_file", target_file)
                        rationale = meta.get("rationale", "")
                    except json.JSONDecodeError:
                        pass
            
            # v13c: Resolve relative paths to absolute using src_root
            if target_file and not os.path.isabs(target_file):
                target_file = str(self._src_root / target_file)
                logger.info(f"📁 Resolved relative path → {target_file}")

            # v15: Reject junk targets — __init__.py, .venv, site-packages
            if target_file:
                _base = os.path.basename(target_file)
                _reject_patterns = ('__init__', 'site-packages', '.venv', 'venv/', 'setup.py', 'conftest.py')
                if any(p in target_file for p in _reject_patterns):
                    logger.warning(f"🚫 Rejecting unsuitable target: {_base} — using default path")
                    target_file = default_file or str(self._src_root / f"shared/innovation_{int(time.time())}.py")

            # v14: For feature/architecture types, if target_file already exists
            # and has no known function context, generate a unique sibling path
            # to avoid overwriting (or failing with "Missing original_code").
            if (innovation_type in ("feature", "architecture")
                    and target_file and os.path.exists(target_file)):
                ts = int(time.time())
                base = target_file
                if base.endswith('.py'):
                    target_file = base[:-3] + f'_{ts}.py'
                else:
                    target_file = base + f'_{ts}.py'
                logger.info(f"📁 Target exists → using unique path: {os.path.basename(target_file)}")

            # v16: Semantic deduplication — reject if title/description too similar
            # to already-promoted innovations (prevents LLM from recycling same ideas)
            if self._is_semantically_duplicate(title, description,
                                                 cycle_titles=getattr(self, '_active_cycle_titles', None)):
                logger.info(f"🔁 Skipping duplicate innovation: '{title}'")
                return None

            # Extract code
            code = self._extract_code(response)
            if not code:
                logger.info(f"Innovation response had no code — skipping")
                return None

            innovation = Innovation(
                innovation_id=f"innovation_{innovation_type}_{int(time.time())}",
                title=title,
                description=description,
                innovation_type=innovation_type,
                target_file=target_file,
                generated_code=code,
                rationale=rationale,
                confidence=0.7
            )
            
            self._last_innovation_time[innovation_type] = time.time()
            
            return innovation
            
        except Exception as e:
            logger.error(f"Failed to parse innovation response: {e}")
            return None
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from response."""
        code = ""
        
        if "```python" in response:
            # Find the LAST python block (usually the implementation)
            parts = response.split("```python")
            if len(parts) > 1:
                last_block = parts[-1]
                end = last_block.find("```")
                if end > 0:
                    code = last_block[:end].strip()
        
        if not code and "```" in response:
            start = response.rfind("```") 
            # Look for the second-to-last ```
            prev = response.rfind("```", 0, start)
            if prev >= 0:
                code = response[prev+3:start].strip()
                # Remove language tag
                if code and code.split('\n')[0].strip().isalpha():
                    code = '\n'.join(code.split('\n')[1:])
        
        return code
    
    def _extract_function_source(self, file_path: str, start_line: int, end_line: int) -> str:
        """Extract function source code from file using line numbers.
        
        v13b: Used by _create_proposal to provide original_code
        for existing-file modifications.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return ''.join(lines[start_line - 1 : end_line])
        except Exception as e:
            logger.warning(f"Failed to extract function source: {e}")
            return ""
    
    def _make_innovation_file_path(self, innovation: 'Innovation') -> str:
        """Generate a safe new file path for an innovation that can't modify an existing file.

        Places the new file next to the target file with a timestamped suffix.
        """
        base = innovation.target_file or str(self._src_root / "shared" / "innovation.py")
        ts = int(time.time())
        if base.endswith('.py'):
            return base[:-3] + f'_innovation_{ts}.py'
        return base + f'_innovation_{ts}.py'

    def _extract_function_by_ast(self, file_path: str, function_name: str) -> Optional[str]:
        """Extract function source using AST (by name, fallback to line numbers).

        v14: More robust than line-number extraction — handles reformatted files.
        """
        import ast as _ast
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = _ast.parse(content)
            lines = content.splitlines(keepends=True)
            for node in _ast.walk(tree):
                if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    if node.name == function_name:
                        start = node.lineno - 1
                        end = getattr(node, 'end_lineno', node.lineno)
                        return ''.join(lines[start:end])
            return None
        except Exception as e:
            logger.warning(f"AST function extraction failed for {function_name}: {e}")
            return None

    def _create_proposal(self, innovation: Innovation) -> Optional[EvolutionProposal]:
        """Create an EvolutionProposal from an Innovation.

        v14: Robust handling of existing vs new files.

        For bug_fix targeting an existing function:
          - Extracts original_code via AST (with line-number fallback)
          - Sets refactored_code = generated_code
          - Sets new_file = False

        For feature/architecture/test targeting an existing file but adding new code:
          - Treats the generated code as a NEW file addition (appended to a new
            sibling file) OR falls back to new_file = True if no function context.
          - Avoids setting new_file = False without original_code (which would
            cause _apply_code_change to fail with "Missing original or refactored code").
        """
        try:
            is_new_file = not os.path.exists(innovation.target_file) if innovation.target_file else True

            proposal = EvolutionProposal(
                proposal_id=innovation.innovation_id,
                proposal_type=ProposalType.CODE,
                description=f"[INNOVATION] {innovation.title}",
                scope="code",
                targets=[innovation.target_file] if innovation.target_file else [],
                diff=f"# Innovation: {innovation.title}\n# Type: {innovation.innovation_type}\n\n{innovation.generated_code}",
                risk_score=35,  # Default moderate risk for innovations
                expected_benefit=innovation.rationale,
                rollback_plan="Remove generated code",
                rationale=f"Innovation Engine: {innovation.description}"
            )

            # v14: Start with base metadata
            proposal.metadata = {
                "innovation_type": innovation.innovation_type,
                "generated_code": innovation.generated_code,
                "new_file": is_new_file,
                "target_file": innovation.target_file,
                "function": innovation.title,  # dedup key for promoted_targets
                "confidence": innovation.confidence
            }

            # v14: For existing files with a known function or full-file refactoring
            # Extract original_code so _apply_code_change can do a precise replacement.
            if not is_new_file and hasattr(innovation, 'metadata') and innovation.metadata:
                func_name = innovation.metadata.get("original_function", "")
                file_path = innovation.metadata.get("original_file", innovation.target_file)
                start = innovation.metadata.get("start_line")
                end = innovation.metadata.get("end_line")

                # If the innovation specificly provides the full original_code (e.g. deep_refactor)
                original_code = innovation.metadata.get("original_code")

                if not original_code and func_name:
                    # Primary: AST extraction (robust, doesn't rely on exact line numbers)
                    original_code = self._extract_function_by_ast(file_path, func_name)
                    if original_code:
                        logger.info(
                            f"📝 AST extracted '{func_name}' from {os.path.basename(file_path)}"
                        )
                    elif start and end:
                        # Fallback: line-number extraction
                        original_code = self._extract_function_source(file_path, start, end)
                        if original_code:
                            logger.info(
                                f"📝 Line-extracted '{func_name}' from {os.path.basename(file_path)} "
                                f"(L{start}-{end})"
                            )

                if original_code:
                    proposal.metadata["original_code"] = original_code
                    proposal.metadata["refactored_code"] = innovation.generated_code
                    proposal.metadata["function"] = func_name or "FULL_FILE"  # Handle full file updates
                    # new_file stays False — _apply_code_change will do in-place replacement
                    logger.info(
                        f"📝 Innovation targets existing code: "
                        f"{func_name or 'FULL_FILE'} in {os.path.basename(file_path)}"
                    )
                else:
                    # Could not extract original_code → treat as new file to avoid apply failure
                    if func_name:
                        logger.warning(
                            f"⚠️  Could not extract '{func_name}' from {os.path.basename(file_path)} — "
                            f"falling back to new_file=True"
                        )
                    proposal.metadata["new_file"] = True
                    proposal.targets = [self._make_innovation_file_path(innovation)]

            elif not is_new_file and not (hasattr(innovation, 'metadata') and innovation.metadata):
                # Existing file but no function context (feature/architecture without metadata):
                # Write as new file to avoid apply failure.
                logger.info(
                    f"📝 Innovation has no function context for existing file — treating as new_file"
                )
                proposal.metadata["new_file"] = True
                proposal.targets = [self._make_innovation_file_path(innovation)]

            return proposal

        except Exception as e:
            logger.error(f"Failed to create proposal from innovation: {e}")
            return None
    
    def _record_innovation(self, innovation: Innovation):
        """Record innovation to history."""
        self._innovations.append(innovation)
        self._total_innovations += 1
        self._successful_innovations += 1
        
        # Also save to file
        innovations_file = Path(__file__).parent.parent.parent / "data" / "innovations.jsonl"
        innovations_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(innovations_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(innovation.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to save innovation: {e}")
    
    def _record_distillation(self, prompt: str, response: str, innovation: Innovation):
        """Record to distillation collector for training data."""
        try:
            from .distillation_collector import get_distillation_collector
            collector = get_distillation_collector()
            collector.record_innovation(
                prompt=prompt,
                response=response,
                innovation_type=innovation.innovation_type,
                description=innovation.title,
                quality_score=innovation.confidence
            )
        except Exception as e:
            logger.debug(f"Distillation recording skipped: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_innovations": self._total_innovations,
            "successful": self._successful_innovations,
            "recent": [i.to_dict() for i in self._innovations[-5:]],
            "cooldowns": {
                k: f"{(time.time() - v) / 3600:.1f}h ago" 
                for k, v in self._last_innovation_time.items()
            }
        }


# Singleton
_innovation_instance: Optional[InnovationEngine] = None

def get_innovation_engine() -> InnovationEngine:
    """Get or create global InnovationEngine instance."""
    global _innovation_instance
    if _innovation_instance is None:
        _innovation_instance = InnovationEngine()
    return _innovation_instance
