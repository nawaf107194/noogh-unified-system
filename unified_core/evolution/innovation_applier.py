"""
Innovation Applier - Applies learning innovations from autonomous_learner
Version: 2.0.0
Part of: Cognitive Evolution System

Reads suggested innovations from protobuf (innovations.pb) and applies them
by generating proposals for the Evolution Controller.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import Counter

from unified_core.evolution.innovation_storage import InnovationStorage
from proto_generated.evolution import learning_pb2

logger = logging.getLogger("unified_core.evolution.innovation_applier")

class InnovationApplier:
    """Applies autonomous learning innovations to the system."""

    def __init__(self, pb_file: str = "/home/noogh/.noogh/innovations.pb"):
        self.storage = InnovationStorage(pb_file=pb_file)
        self._applied_innovations: set = set()
        self._load_applied_history()
        logger.info(f"📚 InnovationApplier initialized | {len(self._applied_innovations)} already applied")

    def _load_applied_history(self):
        """Load history of already applied innovations."""
        history_file = "/home/noogh/.noogh/applied_innovations.json"
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self._applied_innovations = set(data.get('applied', []))
        except Exception as e:
            logger.debug(f"Could not load applied history: {e}")

    def _save_applied_history(self):
        """Save history of applied innovations."""
        history_file = "/home/noogh/.noogh/applied_innovations.json"
        try:
            Path(history_file).parent.mkdir(parents=True, exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump({
                    'applied': list(self._applied_innovations),
                    'last_update': time.time()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save applied history: {e}")

    def get_pending_innovations(self) -> List[learning_pb2.Innovation]:
        """Get all suggested innovations that haven't been applied yet."""
        all_inno = self.storage.get_all()
        pending = []
        for inno in all_inno:
            if inno.status == learning_pb2.INNOVATION_STATUS_SUGGESTED:
                if inno.id not in self._applied_innovations:
                    pending.append(inno)
        return pending

    def prioritize_innovations(self, innovations: List[learning_pb2.Innovation]) -> List[learning_pb2.Innovation]:
        """Prioritize innovations by frequency and recency."""
        type_counts = Counter(i.context.get('original_type', str(i.innovation_type)) for i in innovations)

        # Sort: most requested first, then most recent, then by descending priority
        innovations.sort(
            key=lambda x: (
                -type_counts[x.context.get('original_type', str(x.innovation_type))],  # More requests = higher priority
                -x.suggested_at.seconds,  # More recent = higher priority
                x.priority # Lower priority number = more critical
            )
        )

        return innovations

    def generate_evolution_proposal(self, innovation: learning_pb2.Innovation) -> Optional[Dict[str, Any]]:
        """Convert a protobuf innovation into an Evolution Controller proposal dict."""
        # Use the original type mapped in the migration scripts, or the enum name
        innovation_type = innovation.context.get('original_type', learning_pb2.InnovationType.Name(innovation.innovation_type)).lower()
        rationale = innovation.reasoning or innovation.description
        source_tags = list(filter(None, innovation.context.get('tags', '').split(',')))
        triggered_by = innovation.trigger_event

        # Map innovation types to concrete proposals
        proposals = {
            'optimize_memory_queries': {
                'type': 'code',
                'title': 'Optimize Memory Store Queries',
                'description': f'{rationale}\n\nLearned from: {triggered_by}',
                'target_files': [
                    'unified_core/core/memory_store.py',
                    'unified_core/core/beliefs.py'
                ],
                'priority': 'medium',
                'tags': ['performance', 'database', 'memory']
            },
            'async_parallel_scan': {
                'type': 'code',
                'title': 'Improve Parallel Processing',
                'description': f'{rationale}\n\nLearned from: {triggered_by}',
                'target_files': [
                    'unified_core/parallel_processor.py',
                    'unified_core/agent_daemon.py'
                ],
                'priority': 'medium',
                'tags': ['performance', 'async', 'concurrency']
            },
            'architecture_review': {
                'type': 'refactor',
                'title': 'Architecture Simplification Review',
                'description': f'{rationale}\n\nLearned from: {triggered_by}',
                'target_files': [
                    'unified_core/agent_daemon.py',
                    'unified_core/orchestration/'
                ],
                'priority': 'low',
                'tags': ['architecture', 'refactor', 'maintainability']
            },
            'security_audit_enhance': {
                'type': 'code',
                'title': 'Enhanced Security Hardening',
                'description': f'{rationale}\n\nLearned from: {triggered_by}',
                'target_files': [
                    'unified_core/security/hardening.py',
                    'agents/security_audit_agent.py'
                ],
                'priority': 'high',
                'tags': ['security', 'audit', 'hardening']
            },
            'model_fine_tune_trigger': {
                'type': 'agent',
                'title': 'Model Fine-Tuning Agent',
                'description': f'{rationale}\n\nLearned from: {triggered_by}',
                'agent_role': 'model_trainer',
                'capabilities': ['FINE_TUNE_MODEL', 'COLLECT_TRAINING_DATA'],
                'priority': 'low',
                'tags': ['ml', 'training', 'optimization']
            },
            'event_loop_optimize': {
                'type': 'code',
                'title': 'Event Loop Optimization',
                'description': f'{rationale}\n\nLearned from: {triggered_by}',
                'target_files': [
                    'unified_core/neural_bridge.py',
                    'unified_core/orchestration/message_bus.py'
                ],
                'priority': 'medium',
                'tags': ['performance', 'async', 'event-loop']
            },
            'custom_training_strategy': {
                'type': 'code',
                'title': 'Advanced Training Strategy',
                'description': f'{rationale}\n\nLearned from: {triggered_by}',
                'target_files': list(innovation.affected_files) if len(innovation.affected_files) > 0 else [
                    'unified_core/ml/time_series_predictor.py',
                    'scripts/train_time_series_predictor.py'
                ],
                'priority': 'high',
                'tags': ['ml', 'training', 'optimization', 'gpu', 'mlops']
            }
        }

        # fallback structure
        proposal = proposals.get(innovation_type)
        if not proposal:
            logger.warning(f"Unknown innovation type mapping: {innovation_type}, generating dynamic proposal")
            proposal = {
                 'type': 'code',
                 'title': innovation.title if innovation.title else f'Dynamic Innovation: {innovation_type}',
                 'description': f'{rationale}\n\nLearned from: {triggered_by}',
                 'target_files': list(innovation.affected_files),
                 'priority': 'medium',
                 'tags': source_tags
            }

        # Enrich with learning context
        proposal['source'] = 'autonomous_learning'
        proposal['learning_context'] = {
            'innovation_id': innovation.id,
            'triggered_by': triggered_by,
            'source_tags': source_tags,
            'timestamp': innovation.suggested_at.seconds
        }

        return proposal

    def mark_innovation_applied(self, inno_id: str):
        """Mark an innovation as applied."""
        if inno_id:
            self._applied_innovations.add(inno_id)
            self._save_applied_history()
            logger.info(f"✅ Marked innovation as applied: {inno_id}")

    def apply_top_innovations(self, max_count: int = 3) -> List[Dict[str, Any]]:
        """Get top priority innovations ready for Evolution Controller.

        Returns a list of evolution proposals.
        """
        pending = self.get_pending_innovations()

        if not pending:
            logger.info("📭 No pending innovations to apply")
            return []

        logger.info(f"📚 Found {len(pending)} pending innovations")

        # Prioritize
        prioritized = self.prioritize_innovations(pending)

        # Take top N
        top_innovations = prioritized[:max_count]

        proposals = []
        for innovation in top_innovations:
            proposal = self.generate_evolution_proposal(innovation)
            if proposal:
                proposals.append(proposal)
                logger.info(
                    f"💡 Generated proposal: {proposal['title']} "
                    f"(type={innovation.context.get('original_type', 'custom')})"
                )

        return proposals

    def update_innovation_status(self, innovation_id: str, new_status: str):
        """Update the status of an innovation via Protobuf."""
        # Convert string status to enum
        status_map = {
            'suggested': learning_pb2.INNOVATION_STATUS_SUGGESTED,
            'applied': learning_pb2.INNOVATION_STATUS_APPLIED,
            'rejected': learning_pb2.INNOVATION_STATUS_REJECTED,
            'processing': learning_pb2.INNOVATION_STATUS_PROCESSING_BY_EVOLUTION
        }
        
        status_enum = status_map.get(new_status.lower(), learning_pb2.INNOVATION_STATUS_UNSPECIFIED)
        if self.storage.update_status(innovation_id, status_enum):
             logger.info(f"📝 Updated innovation {innovation_id} → {new_status}")
        else:
             logger.error(f"Failed to update innovation status for {innovation_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about innovations."""
        pending = self.get_pending_innovations()
        type_counts = Counter(i.context.get('original_type', str(i.innovation_type)) for i in pending)

        return {
            'total_pending': len(pending),
            'total_applied': len(self._applied_innovations),
            'pending_by_type': dict(type_counts),
            'innovation_file': self.storage.pb_file
        }


# Singleton instance
_applier_instance = None

def get_innovation_applier() -> InnovationApplier:
    """Get singleton InnovationApplier instance."""
    global _applier_instance
    if _applier_instance is None:
        _applier_instance = InnovationApplier()
    return _applier_instance
