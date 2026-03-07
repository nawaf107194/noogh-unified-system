"""
NOOGH Intelligence Module
Contains cognitive capabilities for reasoning, analysis, and deep thinking.
"""

# Core capability - always available
from .active_questioning import ActiveQuestioner, Question
from .critical_thinking import CriticalThinker, Evidence
from .explainer import Explainer, Decision, Alternative
from .constraints import ConstraintManager, Proposal
from .analogical import AnalogicalReasoner, Situation, AnalogyMatch
from .probabilistic import ProbabilisticReasoner, Hypothesis, EvidenceProb, ProbabilisticOption, Outcome
from .systems_thinking import SystemsThinker, SystemNode, CausalLink, FeedbackLoop
from .multi_objective import MultiObjectiveOptimizer, Objective, MultiObjectiveOption

__all__ = [
    'ActiveQuestioner',
    'Question',
    'CriticalThinker',
    'Evidence',
    'Explainer',
    'Decision',
    'Alternative',
    'ConstraintManager',
    'Proposal',
    'AnalogicalReasoner',
    'Situation',
    'AnalogyMatch',
    'ProbabilisticReasoner',
    'Hypothesis',
    'EvidenceProb',
    'ProbabilisticOption',
    'Outcome',
    'SystemsThinker',
    'SystemNode',
    'CausalLink',
    'FeedbackLoop',
    'MultiObjectiveOptimizer',
    'Objective',
    'MultiObjectiveOption',
]

# Optional capabilities - loaded only if dependencies available
try:
    from .multi_hypothesis_reasoning import MultiHypothesisReasoning
    __all__.append('MultiHypothesisReasoning')
except ImportError:
    pass

try:
    from .bayesian_belief_updater import BayesianBeliefUpdater
    __all__.append('BayesianBeliefUpdater')
except ImportError:
    pass

try:
    from .adversarial_thinking_module import AdversarialThinkingModule
    __all__.append('AdversarialThinkingModule')
except ImportError:
    pass

__version__ = '5.0.0'  # All Phases Completed (Multi-Objective Optimization + 97.5 Milestone)
