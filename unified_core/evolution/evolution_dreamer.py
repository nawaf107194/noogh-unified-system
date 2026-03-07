"""
Evolution Dreamer — Creative Discovery Through Mental Simulation
Version: 3.0.0
Part of: Cognitive Evolution System

Extends the Dreamer concept to evolution: instead of just finding
complex functions, the system "dreams" about strategic improvements
by consulting the Brain with rich context from WorldModel and Journal.

This is NOT bug-fixing — it's creative architectural thinking.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("unified_core.evolution.dreamer")


@dataclass
class EvolutionDream:
    """A dreamed improvement — not yet a proposal, just an idea."""
    dream_id: str
    title: str
    description: str
    rationale: str
    target_area: str           # Where in the codebase
    dream_type: str            # "architecture", "optimization", "capability", "resilience"
    goal_alignment: float      # 0-1: how well this aligns with active goals
    confidence: float          # 0-1: how confident the dreamer is
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dream_id": self.dream_id,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "target_area": self.target_area,
            "dream_type": self.dream_type,
            "goal_alignment": self.goal_alignment,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }


class EvolutionDreamer:
    """Dreams up strategic improvements by consulting the Brain.
    
    Unlike BrainAssistedRefactoring which targets specific functions,
    this dreamer asks creative questions:
    - "What architectural pattern would improve resilience?"
    - "Which module would benefit most from redesign?"
    - "What capability is missing that would help achieve goals?"
    
    Integrates with:
    - CognitiveJournal: for past experience context
    - WorldModel: for current beliefs and goals
    - GravityWell: to check goal alignment
    - Brain (Neural Engine): for creative consultation
    """
    
    def __init__(self):
        self._journal = None
        self._world_model = None
        self._gravity_well = None
        self._brain_url = None
        self._dream_count = 0
        self._dreams: List[EvolutionDream] = []
    
    def set_components(self, journal=None, world_model=None, 
                       gravity_well=None, brain_url: str = None):
        """Wire cognitive components."""
        if journal:
            self._journal = journal
        if world_model:
            self._world_model = world_model
        if gravity_well:
            self._gravity_well = gravity_well
        if brain_url:
            self._brain_url = brain_url
    
    async def dream(self, trigger_context: Dict[str, Any] = None) -> Optional[EvolutionDream]:
        """Run a dream cycle — generate one creative improvement idea.
        
        Args:
            trigger_context: Context from the trigger that initiated this dream
            
        Returns:
            EvolutionDream if a promising idea was generated, None otherwise
        """
        self._dream_count += 1
        
        # Build rich context from all cognitive sources
        context = await self._build_dream_context(trigger_context)
        
        if not context:
            logger.debug("Dream skipped — insufficient context")
            return None
        
        # Generate creative prompt
        prompt = self._build_creative_prompt(context)
        
        # Consult the Brain
        brain_response = await self._consult_brain(prompt)
        
        if not brain_response:
            return None
        
        # Parse Brain's response into a dream
        dream = self._parse_dream(brain_response, context)
        
        if dream and dream.confidence > 0.5:
            self._dreams.append(dream)
            logger.info(
                f"💭 Dream #{self._dream_count}: {dream.title} "
                f"(type={dream.dream_type}, confidence={dream.confidence:.0%})"
            )
            return dream
        
        return None
    
    async def _build_dream_context(self, trigger_context: Dict = None) -> Optional[Dict]:
        """Gather rich context from all cognitive sources."""
        context = {
            "timestamp": time.time(),
            "dream_number": self._dream_count,
            "trigger": trigger_context or {}
        }
        
        # From CognitiveJournal: recent experiences
        if self._journal:
            try:
                evolution_ctx = self._journal.get_evolution_context(max_entries=5)
                context["past_experiences"] = evolution_ctx
                
                # Recent discoveries
                discoveries = self._journal.recall(
                    entry_type="discovery", limit=3, min_confidence=0.6
                )
                context["recent_discoveries"] = [
                    {"content": d.content, "confidence": d.confidence}
                    for d in discoveries
                ]
            except Exception as e:
                logger.debug(f"Journal context unavailable: {e}")
        
        # From WorldModel: current beliefs
        if self._world_model:
            try:
                belief_state = await self._world_model.get_belief_state()
                context["belief_state"] = {
                    "total_beliefs": belief_state.get("total_beliefs", 0),
                    "avg_confidence": belief_state.get("avg_confidence", 0),
                    "weakened_beliefs": belief_state.get("weakened_beliefs", 0),
                }
            except Exception as e:
                logger.debug(f"WorldModel context unavailable: {e}")
        
        # From GravityWell: active goals
        if self._gravity_well:
            try:
                if hasattr(self._gravity_well, 'get_active_goals'):
                    goals_dict = self._gravity_well.get_active_goals()
                    goals = goals_dict.values() if isinstance(goals_dict, dict) else (goals_dict or [])
                    context["active_goals"] = [
                        {"description": g.description, "priority": g.priority}
                        for g in goals
                    ]
            except Exception as e:
                logger.debug(f"GravityWell context unavailable: {e}")
        
        return context
    
    def _build_creative_prompt(self, context: Dict) -> str:
        """Build a creative prompt for the Brain — asks for IDEAS, not fixes."""
        
        goals_text = ""
        if context.get("active_goals"):
            goals_text = "\n".join(
                f"  - {g['description']} (priority={g['priority']:.1f})"
                for g in context["active_goals"]
            )
        
        experiences_text = str(context.get("past_experiences", "No prior experiences"))
        trigger_text = str(context.get("trigger", {}))
        
        return f"""You are a senior software architect thinking about strategic improvements.

SYSTEM STATE:
- Beliefs: {context.get('belief_state', {}).get('total_beliefs', '?')} active beliefs
- Avg Confidence: {context.get('belief_state', {}).get('avg_confidence', '?')}
- Active Goals: 
{goals_text or '  - No specific goals'}

RECENT TRIGGER:
{trigger_text}

PAST EXPERIENCES:
{experiences_text[:500]}

TASK: Propose ONE strategic improvement. Not a bug fix — think architecturally.

Consider:
1. What capability is missing?
2. What pattern could improve resilience?
3. What module is overdue for restructuring?
4. What would make the system more adaptive?

Respond in this exact format:
TITLE: [Short title]
TYPE: [architecture|optimization|capability|resilience]
TARGET: [Which module/area]
DESCRIPTION: [2-3 sentences about what to change]
RATIONALE: [Why this matters]
CONFIDENCE: [0.0-1.0]
"""
    
    async def _consult_brain(self, prompt: str) -> Optional[str]:
        """Send creative prompt to the Brain (Neural Engine). v21: uses requests for HTTPS."""
        import os
        brain_url = self._brain_url or os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")
        model = os.getenv("VLLM_MODEL_NAME", "noogh-teacher")
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        try:
            import requests as _requests
            import asyncio
            
            def _sync_call():
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                # Use OpenAI-compatible endpoint
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "أنت مطور بايثون محترف. حلّل الكود وقدم اقتراحات إبداعية."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.8,
                }
                resp = _requests.post(
                    f"{brain_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                return None
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _sync_call)
        
        except Exception as e:
            logger.warning(f"Dreamer brain call failed: {e}")
            return None
    
    def _parse_dream(self, response: str, context: Dict) -> Optional[EvolutionDream]:
        """Parse Brain's response into an EvolutionDream."""
        try:
            lines = response.strip().split("\n")
            fields = {}
            
            for line in lines:
                line = line.strip()
                for key in ["TITLE:", "TYPE:", "TARGET:", "DESCRIPTION:", "RATIONALE:", "CONFIDENCE:"]:
                    if line.upper().startswith(key):
                        fields[key.rstrip(":")] = line[len(key):].strip()
                        break
            
            if not fields.get("TITLE"):
                return None
            
            # Parse confidence
            try:
                confidence = float(fields.get("CONFIDENCE", "0.5"))
            except ValueError:
                confidence = 0.5
            
            # Check goal alignment
            goal_alignment = self._check_goal_alignment(
                fields.get("DESCRIPTION", ""), 
                context.get("active_goals", [])
            )
            
            dream_type = fields.get("TYPE", "optimization").lower()
            if dream_type not in ("architecture", "optimization", "capability", "resilience"):
                dream_type = "optimization"
            
            return EvolutionDream(
                dream_id=f"dream_{int(time.time())}_{self._dream_count}",
                title=fields.get("TITLE", "Unknown")[:100],
                description=fields.get("DESCRIPTION", "")[:500],
                rationale=fields.get("RATIONALE", "")[:300],
                target_area=fields.get("TARGET", "unknown")[:100],
                dream_type=dream_type,
                goal_alignment=goal_alignment,
                confidence=min(confidence, 0.95)
            )
            
        except Exception as e:
            logger.debug(f"Dream parsing failed: {e}")
            return None
    
    def _check_goal_alignment(self, description: str, goals: List[Dict]) -> float:
        """Estimate how well a dream aligns with active goals."""
        if not goals or not description:
            return 0.5  # Neutral if no goals
        
        desc_words = set(description.lower().split())
        max_overlap = 0
        
        for goal in goals:
            goal_words = set(goal.get("description", "").lower().split())
            overlap = len(desc_words & goal_words)
            max_overlap = max(max_overlap, overlap)
        
        # Normalize: 5+ shared words = high alignment
        return min(max_overlap / 5.0, 1.0)
    
    def get_recent_dreams(self, limit: int = 5) -> List[Dict]:
        """Return recent dreams for inspection."""
        return [d.to_dict() for d in self._dreams[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_dreams": self._dream_count,
            "stored_dreams": len(self._dreams),
            "avg_confidence": (
                sum(d.confidence for d in self._dreams) / len(self._dreams)
                if self._dreams else 0
            ),
            "dream_types": {
                dt: sum(1 for d in self._dreams if d.dream_type == dt)
                for dt in ("architecture", "optimization", "capability", "resilience")
            }
        }


# Singleton
_dreamer_instance: Optional[EvolutionDreamer] = None

def get_evolution_dreamer() -> EvolutionDreamer:
    """Get or create global EvolutionDreamer instance."""
    global _dreamer_instance
    if _dreamer_instance is None:
        _dreamer_instance = EvolutionDreamer()
    return _dreamer_instance
