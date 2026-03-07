"""
Instinct System — Continuous Learning from Evolution Decisions
Version: 1.0.0
Inspired by: affaan-m/everything-claude-code continuous-learning-v2

Observes every evolution outcome (promotion/failure/rejection) and extracts
reusable "instincts" — patterns that guide future decisions.

Flow:
1. Observer records every proposal outcome to observations.jsonl
2. Pattern extractor clusters observations by outcome type
3. Instincts accumulate confidence scores over time
4. High-confidence instincts feed back into innovation prompts and policy gate
5. /evolve promotes instincts into formal rules

Architecture:
- InstinctObserver: passive recorder (no extra API calls)
- InstinctExtractor: clusters observations into patterns
- InstinctStore: persistence layer (YAML + JSONL)
- InstinctAdvisor: provides guidance to InnovationEngine based on instincts
"""

import json
import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from collections import Counter, defaultdict

logger = logging.getLogger("unified_core.evolution.instinct")

# Storage paths
_NOOGH_DIR = Path.home() / ".noogh" / "evolution"
OBSERVATIONS_FILE = _NOOGH_DIR / "observations.jsonl"
INSTINCTS_FILE = _NOOGH_DIR / "instincts.json"


# ─────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────

@dataclass
class Observation:
    """A single evolution event observation."""
    timestamp: float
    event_type: str          # promoted | failed | rejected | canary_pass | canary_fail
    proposal_id: str
    innovation_type: str     # feature | bug_fix | test | architecture
    title: str
    target_file: str
    lines_of_code: int
    error: str = ""          # if failed/rejected, why
    duration_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Instinct:
    """A learned pattern extracted from multiple observations."""
    instinct_id: str
    trigger: str             # "when generating feature innovations"
    action: str              # "avoid logging/error_handler concepts"
    confidence: float        # 0.0 – 1.0
    domain: str              # innovation_type or "general"
    observations_count: int  # how many observations support this
    last_updated: float = field(default_factory=time.time)
    examples: List[str] = field(default_factory=list)  # sample titles

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────
# InstinctObserver: passive recorder
# ─────────────────────────────────────────────

class InstinctObserver:
    """Records every evolution outcome to observations.jsonl."""

    def __init__(self):
        _NOOGH_DIR.mkdir(parents=True, exist_ok=True)
        self._obs_file = OBSERVATIONS_FILE

    def record(
        self,
        event_type: str,
        proposal_id: str,
        innovation_type: str,
        title: str,
        target_file: str,
        lines_of_code: int = 0,
        error: str = "",
        duration_sec: float = 0.0,
    ) -> None:
        """Append one observation to the JSONL file."""
        obs = Observation(
            timestamp=time.time(),
            event_type=event_type,
            proposal_id=proposal_id,
            innovation_type=innovation_type,
            title=title,
            target_file=target_file,
            lines_of_code=lines_of_code,
            error=error,
            duration_sec=duration_sec,
        )
        try:
            with open(self._obs_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(obs.to_dict()) + "\n")
            logger.debug(f"👁️ Observation recorded: {event_type} / {title[:40]}")
        except Exception as e:
            logger.warning(f"InstinctObserver.record failed: {e}")

    def load_all(self) -> List[Observation]:
        """Load all observations from disk."""
        observations = []
        if not self._obs_file.exists():
            return observations
        try:
            with open(self._obs_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        observations.append(Observation(**d))
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"InstinctObserver.load_all failed: {e}")
        return observations


# ─────────────────────────────────────────────
# InstinctExtractor: clusters observations into instincts
# ─────────────────────────────────────────────

class InstinctExtractor:
    """Extracts patterns (instincts) from accumulated observations."""

    # Keywords that appear in failed/rejected titles → avoid them
    FAILURE_KEYWORDS = [
        "error_handler", "error handler", "logging", "log", "health_check",
        "health check", "monitor", "retry", "cache", "handler",
    ]

    # Domain-specific keywords — track saturation separately
    DOMAIN_KEYWORDS = [
        "memory", "governance", "security", "routing",
        "resilience", "healing", "supervisor", "orchestrator",
        "multi-agent", "journal", "pattern", "filter",
        "market regime", "trailing stop", "drawdown", "position sizing"
    ]

    # Innovation types and their success patterns
    SUCCESS_PATTERNS: Dict[str, List[str]] = {
        "test": ["test_", "tests for", "unit test"],
        "feature": ["pipeline", "transformer", "scheduler", "validator", "parser",
                    "regime", "trailing", "drawdown", "confluence", "sizing"],
        "architecture": ["factory", "observer", "strategy", "abstract", "interface"],
        "bug_fix": ["race condition", "null check", "resource leak", "edge case"],
    }

    def extract(self, observations: List[Observation]) -> List[Instinct]:
        """Derive instincts from the observation history."""
        instincts: List[Instinct] = []

        if not observations:
            return instincts

        # ── Instinct 1: concept saturation (concepts that keep failing/deduping) ──
        failed_titles = [
            o.title.lower()
            for o in observations
            if o.event_type in ("failed", "rejected", "dedup_rejected")
        ]
        keyword_failures = Counter()
        for title in failed_titles:
            for kw in self.FAILURE_KEYWORDS:
                if kw in title:
                    keyword_failures[kw] += 1

        for kw, count in keyword_failures.items():
            if count >= 2:
                confidence = min(0.95, 0.5 + count * 0.1)
                instincts.append(Instinct(
                    instinct_id=f"avoid_saturated_{kw.replace(' ', '_')}",
                    trigger="when proposing any new innovation",
                    action=f"Avoid '{kw}' concepts — already over-represented ({count} failures)",
                    confidence=confidence,
                    domain="general",
                    observations_count=count,
                    examples=failed_titles[:3],
                ))

        # ── Instinct 2: successful innovation types by file pattern ──
        # v21: Diversity-aware — cap confidence for over-dominant types
        promoted = [o for o in observations if o.event_type == "promoted"]
        type_success = Counter(o.innovation_type for o in promoted)
        total_promoted = max(sum(type_success.values()), 1)

        for itype, count in type_success.items():
            if count >= 3:
                ratio = count / total_promoted
                if ratio > 0.7:
                    # Over-dominant type — suppress to encourage diversity
                    confidence = 0.3
                    action = (
                        f"Consider diversifying away from '{itype}' innovations — "
                        f"{count} promotions ({ratio:.0%} of total). "
                        f"Try feature, architecture, refactor, or bug_fix instead."
                    )
                else:
                    confidence = min(0.9, 0.4 + count * 0.05)
                    action = f"Prefer '{itype}' innovations — {count} successful promotions"
                instincts.append(Instinct(
                    instinct_id=f"prefer_{itype}_type",
                    trigger=f"when choosing innovation type",
                    action=action,
                    confidence=confidence,
                    domain=itype,
                    observations_count=count,
                    examples=[o.title for o in promoted if o.innovation_type == itype][:3],
                ))

        # ── Instinct 3: file size sweet spot ──
        size_data = [(o.lines_of_code, o.event_type) for o in observations if o.lines_of_code > 0]
        if size_data:
            promoted_sizes = [s for s, t in size_data if t == "promoted"]
            failed_sizes = [s for s, t in size_data if t == "failed"]
            if promoted_sizes:
                avg_promoted = sum(promoted_sizes) / len(promoted_sizes)
                instincts.append(Instinct(
                    instinct_id="ideal_code_size",
                    trigger="when generating code for innovation",
                    action=f"Target ~{int(avg_promoted)} lines — average size of promoted innovations",
                    confidence=0.7,
                    domain="general",
                    observations_count=len(promoted_sizes),
                    examples=[f"{s} lines" for s in promoted_sizes[:5]],
                ))

        # ── Instinct 3b: domain features already built (avoid repeating) ──
        domain_promoted = [
            o.title.lower() for o in promoted
            if any(kw in o.title.lower() for kw in self.DOMAIN_KEYWORDS)
        ]
        if domain_promoted:
            instincts.append(Instinct(
                instinct_id="domain_features_built",
                trigger="when proposing new system features",
                action=(
                    f"Already built domain features: {', '.join(domain_promoted[:5])}. "
                    "Focus on NEW architecture improvements not yet implemented."
                ),
                confidence=0.85,
                domain="feature",
                observations_count=len(domain_promoted),
                examples=domain_promoted[:5],
            ))

        # ── Instinct 4: common failure reasons → policy hints ──
        error_counter = Counter()
        for o in observations:
            if o.error and o.event_type in ("failed", "rejected"):
                # Normalize errors
                if "missing original" in o.error.lower():
                    error_counter["missing_original_code"] += 1
                elif "syntax" in o.error.lower():
                    error_counter["syntax_error"] += 1
                elif "policy" in o.error.lower():
                    error_counter["policy_violation"] += 1
                elif "target file not found" in o.error.lower():
                    error_counter["file_not_found"] += 1

        for err_type, count in error_counter.items():
            if count >= 2:
                advice = {
                    "missing_original_code": "Always extract original_code via AST before proposing bug_fix",
                    "syntax_error": "Validate Python syntax before submitting refactored_code",
                    "policy_violation": "Check policy gate patterns before writing code with exec/eval/subprocess",
                    "file_not_found": "Resolve relative paths to absolute using src_root before targeting files",
                }.get(err_type, f"Avoid causing '{err_type}' errors")

                instincts.append(Instinct(
                    instinct_id=f"prevent_{err_type}",
                    trigger="before creating any evolution proposal",
                    action=advice,
                    confidence=min(0.95, 0.6 + count * 0.1),
                    domain="proposal_quality",
                    observations_count=count,
                ))

        return instincts


# ─────────────────────────────────────────────
# InstinctStore: persistence
# ─────────────────────────────────────────────

class InstinctStore:
    """Loads and saves instincts to disk."""

    def __init__(self):
        _NOOGH_DIR.mkdir(parents=True, exist_ok=True)
        self._path = INSTINCTS_FILE

    def save(self, instincts: List[Instinct]) -> None:
        data = {
            "version": "1.0",
            "updated_at": time.time(),
            "count": len(instincts),
            "instincts": [i.to_dict() for i in instincts],
        }
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"🧠 InstinctStore: saved {len(instincts)} instincts")
        except Exception as e:
            logger.warning(f"InstinctStore.save failed: {e}")

    def load(self) -> List[Instinct]:
        if not self._path.exists():
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            instincts = []
            for d in data.get("instincts", []):
                try:
                    instincts.append(Instinct(**d))
                except Exception:
                    pass
            logger.info(f"🧠 InstinctStore: loaded {len(instincts)} instincts")
            return instincts
        except Exception as e:
            logger.warning(f"InstinctStore.load failed: {e}")
            return []


# ─────────────────────────────────────────────
# InstinctAdvisor: provides guidance to InnovationEngine
# ─────────────────────────────────────────────

class InstinctAdvisor:
    """
    Provides actionable guidance based on learned instincts.
    Called by InnovationEngine before generating prompts.
    """

    def __init__(self):
        self._store = InstinctStore()
        self._observer = InstinctObserver()
        self._extractor = InstinctExtractor()
        self._instincts: List[Instinct] = self._store.load()
        self._last_evolved = 0.0
        self._evolve_interval = 300  # Re-extract every 5 min

    @property
    def observer(self) -> InstinctObserver:
        return self._observer

    def evolve(self, force: bool = False) -> int:
        """Re-extract instincts from observations. Returns count."""
        now = time.time()
        if not force and (now - self._last_evolved) < self._evolve_interval:
            return len(self._instincts)

        observations = self._observer.load_all()
        self._instincts = self._extractor.extract(observations)
        self._store.save(self._instincts)
        self._last_evolved = now
        logger.info(f"🧬 Instincts evolved: {len(self._instincts)} patterns from {len(observations)} observations")
        return len(self._instincts)

    def get_guidance(self, domain: str = "general", min_confidence: float = 0.6) -> str:
        """
        Return a formatted string of instinct-based guidance for use in LLM prompts.
        High-confidence instincts become explicit instructions.
        """
        self.evolve()  # Refresh if stale
        relevant = [
            i for i in self._instincts
            if i.confidence >= min_confidence
            and (i.domain == domain or i.domain == "general" or domain == "general")
        ]
        if not relevant:
            return ""

        lines = ["LEARNED INSTINCTS (from past evolution outcomes):"]
        for inst in sorted(relevant, key=lambda x: -x.confidence)[:8]:
            lines.append(f"- [{inst.confidence:.0%} confidence] {inst.action}")

        return "\n".join(lines)

    def get_avoid_keywords(self, min_confidence: float = 0.7) -> List[str]:
        """Return list of keywords to avoid in innovation titles/descriptions."""
        self.evolve()
        keywords = []
        for inst in self._instincts:
            if inst.confidence >= min_confidence and "avoid" in inst.action.lower():
                # Extract keyword from action: "Avoid 'X' concepts..."
                import re
                match = re.search(r"Avoid '([^']+)'", inst.action)
                if match:
                    keywords.append(match.group(1))
        return keywords

    def get_preferred_types(self) -> List[str]:
        """Return innovation types ordered by historical success rate."""
        self.evolve()
        preferred = []
        for inst in self._instincts:
            if "prefer_" in inst.instinct_id and inst.confidence >= 0.6:
                domain = inst.domain
                preferred.append((inst.confidence, domain))
        return [t for _, t in sorted(preferred, reverse=True)]

    def summary(self) -> Dict[str, Any]:
        """Return a human-readable summary of current instincts."""
        self.evolve()
        obs = self._observer.load_all()
        return {
            "total_observations": len(obs),
            "total_instincts": len(self._instincts),
            "promoted": sum(1 for o in obs if o.event_type == "promoted"),
            "failed": sum(1 for o in obs if o.event_type == "failed"),
            "rejected": sum(1 for o in obs if o.event_type in ("rejected", "dedup_rejected")),
            "high_confidence_instincts": [
                {"id": i.instinct_id, "confidence": i.confidence, "action": i.action}
                for i in self._instincts if i.confidence >= 0.8
            ],
        }


# ─────────────────────────────────────────────
# Singleton accessor
# ─────────────────────────────────────────────

_instinct_advisor: Optional[InstinctAdvisor] = None


def get_instinct_advisor() -> InstinctAdvisor:
    global _instinct_advisor
    if _instinct_advisor is None:
        _instinct_advisor = InstinctAdvisor()
    return _instinct_advisor
