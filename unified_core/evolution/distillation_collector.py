"""
Auto-Distillation Collector — Passive Knowledge Harvester
Version: 1.0.0
Part of: Self-Directed Layer

Automatically captures every Brain (32B Teacher) response during refactoring
and saves it as high-quality training data for the 7B Student model.

Flow:
1. BrainAssistedRefactoring calls the Teacher (32B) for code improvements
2. This collector intercepts successful (prompt → response) pairs
3. Saves them as JSONL in the distillation dataset
4. Periodically exports high-quality trajectories for fine-tuning

This is PASSIVE — it doesn't make extra API calls, it just records
what the Agent already does during its evolution cycles.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("unified_core.evolution.distillation")

# Default output paths
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "distillation"
TRAJECTORIES_FILE = DATA_DIR / "teacher_trajectories.jsonl"
EXPORT_FILE = DATA_DIR / "training_ready.jsonl"


@dataclass
class TeacherTrajectory:
    """A single Teacher → Student training example."""
    timestamp: float
    category: str  # e.g., "refactoring", "innovation", "architecture"  
    task_description: str  # What was asked
    system_prompt: str  # System message used
    user_prompt: str  # The actual prompt
    teacher_response: str  # Raw response from 32B
    extracted_code: str  # Clean code after extraction
    quality_score: float  # 0.0-1.0 based on outcome
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_training_format(self) -> Dict[str, Any]:
        """Convert to ChatML training format."""
        return {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt},
                {"role": "assistant", "content": self.extracted_code or self.teacher_response}
            ],
            "category": self.category,
            "quality_score": self.quality_score,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "category": self.category,
            "task_description": self.task_description,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "teacher_response": self.teacher_response,
            "extracted_code": self.extracted_code,
            "quality_score": self.quality_score,
            "metadata": self.metadata
        }


class DistillationCollector:
    """
    Passively collects Teacher responses for Student training.
    
    Designed to be called from BrainAssistedRefactoring and InnovationEngine
    after each successful Brain interaction.
    """
    
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._trajectories: List[TeacherTrajectory] = []
        self._total_collected = 0
        self._total_exported = 0
        
        # Load count from existing file
        if TRAJECTORIES_FILE.exists():
            try:
                with open(TRAJECTORIES_FILE, 'r') as f:
                    self._total_collected = sum(1 for _ in f)
            except Exception:
                pass
        
        logger.info(f"📚 DistillationCollector initialized: {self._total_collected} existing trajectories")
    
    def record(self, 
               category: str,
               system_prompt: str,
               user_prompt: str,
               teacher_response: str,
               extracted_code: str = "",
               quality_score: float = 0.5,
               metadata: Dict[str, Any] = None) -> TeacherTrajectory:
        """
        Record a Teacher interaction for distillation.
        
        Called after each successful Brain call.
        """
        trajectory = TeacherTrajectory(
            timestamp=time.time(),
            category=category,
            task_description=metadata.get("description", category) if metadata else category,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            teacher_response=teacher_response,
            extracted_code=extracted_code,
            quality_score=quality_score,
            metadata=metadata or {}
        )
        
        # Append to file immediately (crash-safe)
        try:
            with open(TRAJECTORIES_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trajectory.to_dict(), ensure_ascii=False) + "\n")
            
            self._total_collected += 1
            self._trajectories.append(trajectory)
            
            logger.info(
                f"📚 Trajectory #{self._total_collected} recorded: "
                f"{category} (quality={quality_score:.0%})"
            )
        except Exception as e:
            logger.error(f"Failed to save trajectory: {e}")
        
        return trajectory
    
    def record_refactor_success(self, 
                                 prompt: str,
                                 response: str,
                                 extracted_code: str,
                                 issue_type: str,
                                 function_name: str,
                                 file_path: str,
                                 applied: bool = False):
        """Convenience method for BrainAssistedRefactoring results."""
        quality = 0.9 if applied else 0.7  # Applied = higher quality
        
        return self.record(
            category="refactoring",
            system_prompt=(
                "You are NOOGH, an expert software engineer. "
                "Write clean, production-ready code without unnecessary boilerplate. "
                "Output ONLY the code, no explanations unless asked."
            ),
            user_prompt=prompt,
            teacher_response=response,
            extracted_code=extracted_code,
            quality_score=quality,
            metadata={
                "description": f"Refactor {function_name}: {issue_type}",
                "issue_type": issue_type,
                "function": function_name,
                "file": file_path,
                "applied_to_production": applied
            }
        )
    
    def record_innovation(self,
                          prompt: str,
                          response: str,
                          innovation_type: str,
                          description: str,
                          quality_score: float = 0.6):
        """Convenience method for InnovationEngine results."""
        return self.record(
            category="innovation",
            system_prompt=(
                "You are NOOGH, a creative AI system architect. "
                "Design novel features, patterns, and improvements. "
                "Think beyond simple fixes — innovate."
            ),
            user_prompt=prompt,
            teacher_response=response,
            quality_score=quality_score,
            metadata={
                "description": description,
                "innovation_type": innovation_type
            }
        )
    
    def record_agent_design(self,
                            prompt: str,
                            response: str,
                            agent_name: str,
                            role: str,
                            capabilities: list,
                            deployed: bool = False):
        """Convenience method for Brain-designed agent blueprints."""
        quality = 0.9 if deployed else 0.85
        
        return self.record(
            category="agent_design",
            system_prompt=(
                "You are NOOGH, an expert autonomous systems architect. "
                "Design modular, safe agents that integrate with the AgentWorker framework. "
                "Output agent specifications as JSON with name, role, capabilities, and handlers."
            ),
            user_prompt=prompt,
            teacher_response=response,
            extracted_code="",  # Blueprint is the response itself
            quality_score=quality,
            metadata={
                "description": f"Design agent: {agent_name} ({role})",
                "agent_name": agent_name,
                "role": role,
                "capabilities": capabilities,
                "deployed_to_production": deployed,
            }
        )
    
    def export_training_data(self, min_quality: float = 0.6) -> Dict[str, Any]:
        """
        Export high-quality trajectories as ChatML training data.
        
        Returns stats about the exported data.
        """
        if not TRAJECTORIES_FILE.exists():
            return {"exported": 0, "error": "No trajectories file"}
        
        exported = 0
        categories = {}
        
        try:
            with open(TRAJECTORIES_FILE, 'r') as fin, \
                 open(EXPORT_FILE, 'w', encoding='utf-8') as fout:
                
                for line in fin:
                    try:
                        data = json.loads(line.strip())
                        quality = data.get("quality_score", 0)
                        
                        if quality >= min_quality:
                            # Convert to ChatML format
                            training_item = {
                                "messages": [
                                    {"role": "system", "content": data["system_prompt"]},
                                    {"role": "user", "content": data["user_prompt"]},
                                    {"role": "assistant", "content": data.get("extracted_code") or data["teacher_response"]}
                                ]
                            }
                            fout.write(json.dumps(training_item, ensure_ascii=False) + "\n")
                            exported += 1
                            
                            cat = data.get("category", "unknown")
                            categories[cat] = categories.get(cat, 0) + 1
                    except json.JSONDecodeError:
                        continue
            
            self._total_exported = exported
            
            logger.info(f"📤 Exported {exported} training examples to {EXPORT_FILE}")
            
            return {
                "exported": exported,
                "output_file": str(EXPORT_FILE),
                "categories": categories,
                "min_quality": min_quality
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"exported": 0, "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            "total_collected": self._total_collected,
            "total_exported": self._total_exported,
            "trajectories_file": str(TRAJECTORIES_FILE),
            "file_size_kb": round(TRAJECTORIES_FILE.stat().st_size / 1024, 1) if TRAJECTORIES_FILE.exists() else 0,
            "session_collected": len(self._trajectories)
        }


# Singleton
_collector_instance: Optional[DistillationCollector] = None

def get_distillation_collector() -> DistillationCollector:
    """Get or create global DistillationCollector instance."""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = DistillationCollector()
    return _collector_instance
