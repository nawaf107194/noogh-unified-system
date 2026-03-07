from proto_generated.common import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Question(_message.Message):
    __slots__ = ("level", "question_type", "question_text", "answer", "timestamp", "insights")
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        TYPE_UNSPECIFIED: _ClassVar[Question.Type]
        TYPE_WHY: _ClassVar[Question.Type]
        TYPE_HOW: _ClassVar[Question.Type]
        TYPE_WHAT_IF: _ClassVar[Question.Type]
        TYPE_WHAT_ELSE: _ClassVar[Question.Type]
    TYPE_UNSPECIFIED: Question.Type
    TYPE_WHY: Question.Type
    TYPE_HOW: Question.Type
    TYPE_WHAT_IF: Question.Type
    TYPE_WHAT_ELSE: Question.Type
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    QUESTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    QUESTION_TEXT_FIELD_NUMBER: _ClassVar[int]
    ANSWER_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    INSIGHTS_FIELD_NUMBER: _ClassVar[int]
    level: int
    question_type: Question.Type
    question_text: str
    answer: str
    timestamp: _types_pb2.Timestamp
    insights: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, level: _Optional[int] = ..., question_type: _Optional[_Union[Question.Type, str]] = ..., question_text: _Optional[str] = ..., answer: _Optional[str] = ..., timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., insights: _Optional[_Iterable[str]] = ...) -> None: ...

class QuestionChain(_message.Message):
    __slots__ = ("observation", "questions", "depth_reached", "root_cause", "all_insights", "created_at")
    OBSERVATION_FIELD_NUMBER: _ClassVar[int]
    QUESTIONS_FIELD_NUMBER: _ClassVar[int]
    DEPTH_REACHED_FIELD_NUMBER: _ClassVar[int]
    ROOT_CAUSE_FIELD_NUMBER: _ClassVar[int]
    ALL_INSIGHTS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    observation: str
    questions: _containers.RepeatedCompositeFieldContainer[Question]
    depth_reached: int
    root_cause: str
    all_insights: _containers.RepeatedScalarFieldContainer[str]
    created_at: _types_pb2.Timestamp
    def __init__(self, observation: _Optional[str] = ..., questions: _Optional[_Iterable[_Union[Question, _Mapping]]] = ..., depth_reached: _Optional[int] = ..., root_cause: _Optional[str] = ..., all_insights: _Optional[_Iterable[str]] = ..., created_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class WhyChainRequest(_message.Message):
    __slots__ = ("observation", "max_depth", "context")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    OBSERVATION_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    observation: str
    max_depth: int
    context: _containers.ScalarMap[str, str]
    def __init__(self, observation: _Optional[str] = ..., max_depth: _Optional[int] = ..., context: _Optional[_Mapping[str, str]] = ...) -> None: ...

class HowChainRequest(_message.Message):
    __slots__ = ("goal", "max_depth", "context")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    GOAL_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    goal: str
    max_depth: int
    context: _containers.ScalarMap[str, str]
    def __init__(self, goal: _Optional[str] = ..., max_depth: _Optional[int] = ..., context: _Optional[_Mapping[str, str]] = ...) -> None: ...

class WhatIfRequest(_message.Message):
    __slots__ = ("situation", "scenario_count")
    SITUATION_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_COUNT_FIELD_NUMBER: _ClassVar[int]
    situation: str
    scenario_count: int
    def __init__(self, situation: _Optional[str] = ..., scenario_count: _Optional[int] = ...) -> None: ...

class QuestioningResponse(_message.Message):
    __slots__ = ("chain", "confidence", "error")
    CHAIN_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    chain: QuestionChain
    confidence: _types_pb2.Confidence
    error: _types_pb2.Error
    def __init__(self, chain: _Optional[_Union[QuestionChain, _Mapping]] = ..., confidence: _Optional[_Union[_types_pb2.Confidence, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class Evidence(_message.Message):
    __slots__ = ("content", "source", "timestamp", "strength", "supports_claim")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_CLAIM_FIELD_NUMBER: _ClassVar[int]
    content: str
    source: str
    timestamp: _types_pb2.Timestamp
    strength: float
    supports_claim: bool
    def __init__(self, content: _Optional[str] = ..., source: _Optional[str] = ..., timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., strength: _Optional[float] = ..., supports_claim: bool = ...) -> None: ...

class CognitiveBias(_message.Message):
    __slots__ = ("bias_type", "description", "severity", "recommendation")
    class BiasType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        BIAS_UNSPECIFIED: _ClassVar[CognitiveBias.BiasType]
        BIAS_CONFIRMATION: _ClassVar[CognitiveBias.BiasType]
        BIAS_AVAILABILITY: _ClassVar[CognitiveBias.BiasType]
        BIAS_ANCHORING: _ClassVar[CognitiveBias.BiasType]
        BIAS_CORRELATION_CAUSATION: _ClassVar[CognitiveBias.BiasType]
        BIAS_SURVIVORSHIP: _ClassVar[CognitiveBias.BiasType]
        BIAS_RECENCY: _ClassVar[CognitiveBias.BiasType]
    BIAS_UNSPECIFIED: CognitiveBias.BiasType
    BIAS_CONFIRMATION: CognitiveBias.BiasType
    BIAS_AVAILABILITY: CognitiveBias.BiasType
    BIAS_ANCHORING: CognitiveBias.BiasType
    BIAS_CORRELATION_CAUSATION: CognitiveBias.BiasType
    BIAS_SURVIVORSHIP: CognitiveBias.BiasType
    BIAS_RECENCY: CognitiveBias.BiasType
    BIAS_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    bias_type: CognitiveBias.BiasType
    description: str
    severity: float
    recommendation: str
    def __init__(self, bias_type: _Optional[_Union[CognitiveBias.BiasType, str]] = ..., description: _Optional[str] = ..., severity: _Optional[float] = ..., recommendation: _Optional[str] = ...) -> None: ...

class LogicalFallacy(_message.Message):
    __slots__ = ("fallacy_type", "description", "location")
    class FallacyType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        FALLACY_UNSPECIFIED: _ClassVar[LogicalFallacy.FallacyType]
        FALLACY_HASTY_GENERALIZATION: _ClassVar[LogicalFallacy.FallacyType]
        FALLACY_FALSE_DICHOTOMY: _ClassVar[LogicalFallacy.FallacyType]
        FALLACY_SLIPPERY_SLOPE: _ClassVar[LogicalFallacy.FallacyType]
        FALLACY_CIRCULAR_REASONING: _ClassVar[LogicalFallacy.FallacyType]
        FALLACY_POST_HOC: _ClassVar[LogicalFallacy.FallacyType]
    FALLACY_UNSPECIFIED: LogicalFallacy.FallacyType
    FALLACY_HASTY_GENERALIZATION: LogicalFallacy.FallacyType
    FALLACY_FALSE_DICHOTOMY: LogicalFallacy.FallacyType
    FALLACY_SLIPPERY_SLOPE: LogicalFallacy.FallacyType
    FALLACY_CIRCULAR_REASONING: LogicalFallacy.FallacyType
    FALLACY_POST_HOC: LogicalFallacy.FallacyType
    FALLACY_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    fallacy_type: LogicalFallacy.FallacyType
    description: str
    location: str
    def __init__(self, fallacy_type: _Optional[_Union[LogicalFallacy.FallacyType, str]] = ..., description: _Optional[str] = ..., location: _Optional[str] = ...) -> None: ...

class ReasoningEvaluation(_message.Message):
    __slots__ = ("claim", "evidence", "reasoning", "valid", "issues", "alternatives", "assumptions", "biases", "fallacies", "confidence")
    CLAIM_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    VALID_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    ALTERNATIVES_FIELD_NUMBER: _ClassVar[int]
    ASSUMPTIONS_FIELD_NUMBER: _ClassVar[int]
    BIASES_FIELD_NUMBER: _ClassVar[int]
    FALLACIES_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    claim: str
    evidence: _containers.RepeatedCompositeFieldContainer[Evidence]
    reasoning: str
    valid: bool
    issues: _containers.RepeatedScalarFieldContainer[str]
    alternatives: _containers.RepeatedScalarFieldContainer[str]
    assumptions: _containers.RepeatedScalarFieldContainer[str]
    biases: _containers.RepeatedCompositeFieldContainer[CognitiveBias]
    fallacies: _containers.RepeatedCompositeFieldContainer[LogicalFallacy]
    confidence: _types_pb2.Confidence
    def __init__(self, claim: _Optional[str] = ..., evidence: _Optional[_Iterable[_Union[Evidence, _Mapping]]] = ..., reasoning: _Optional[str] = ..., valid: bool = ..., issues: _Optional[_Iterable[str]] = ..., alternatives: _Optional[_Iterable[str]] = ..., assumptions: _Optional[_Iterable[str]] = ..., biases: _Optional[_Iterable[_Union[CognitiveBias, _Mapping]]] = ..., fallacies: _Optional[_Iterable[_Union[LogicalFallacy, _Mapping]]] = ..., confidence: _Optional[_Union[_types_pb2.Confidence, _Mapping]] = ...) -> None: ...

class EvaluateReasoningRequest(_message.Message):
    __slots__ = ("claim", "evidence", "reasoning")
    CLAIM_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    claim: str
    evidence: _containers.RepeatedCompositeFieldContainer[Evidence]
    reasoning: str
    def __init__(self, claim: _Optional[str] = ..., evidence: _Optional[_Iterable[_Union[Evidence, _Mapping]]] = ..., reasoning: _Optional[str] = ...) -> None: ...

class EvaluateReasoningResponse(_message.Message):
    __slots__ = ("evaluation", "error")
    EVALUATION_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    evaluation: ReasoningEvaluation
    error: _types_pb2.Error
    def __init__(self, evaluation: _Optional[_Union[ReasoningEvaluation, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class Decision(_message.Message):
    __slots__ = ("trigger", "action", "reasoning_steps", "selection_reason", "alternatives", "evidence_quality", "strategy_success_rate", "risk_score", "confidence", "risks", "next_steps")
    TRIGGER_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    REASONING_STEPS_FIELD_NUMBER: _ClassVar[int]
    SELECTION_REASON_FIELD_NUMBER: _ClassVar[int]
    ALTERNATIVES_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_QUALITY_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_SUCCESS_RATE_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    RISKS_FIELD_NUMBER: _ClassVar[int]
    NEXT_STEPS_FIELD_NUMBER: _ClassVar[int]
    trigger: str
    action: str
    reasoning_steps: _containers.RepeatedScalarFieldContainer[str]
    selection_reason: str
    alternatives: _containers.RepeatedCompositeFieldContainer[Alternative]
    evidence_quality: float
    strategy_success_rate: float
    risk_score: int
    confidence: _types_pb2.Confidence
    risks: _containers.RepeatedScalarFieldContainer[str]
    next_steps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, trigger: _Optional[str] = ..., action: _Optional[str] = ..., reasoning_steps: _Optional[_Iterable[str]] = ..., selection_reason: _Optional[str] = ..., alternatives: _Optional[_Iterable[_Union[Alternative, _Mapping]]] = ..., evidence_quality: _Optional[float] = ..., strategy_success_rate: _Optional[float] = ..., risk_score: _Optional[int] = ..., confidence: _Optional[_Union[_types_pb2.Confidence, _Mapping]] = ..., risks: _Optional[_Iterable[str]] = ..., next_steps: _Optional[_Iterable[str]] = ...) -> None: ...

class Alternative(_message.Message):
    __slots__ = ("name", "description", "pros", "cons", "score", "rejection_reason")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PROS_FIELD_NUMBER: _ClassVar[int]
    CONS_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    REJECTION_REASON_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    pros: _containers.RepeatedScalarFieldContainer[str]
    cons: _containers.RepeatedScalarFieldContainer[str]
    score: float
    rejection_reason: str
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., pros: _Optional[_Iterable[str]] = ..., cons: _Optional[_Iterable[str]] = ..., score: _Optional[float] = ..., rejection_reason: _Optional[str] = ...) -> None: ...

class Explanation(_message.Message):
    __slots__ = ("decision", "why_this_decision", "why_not_alternatives", "factor_weights", "summary")
    class FactorWeightsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    DECISION_FIELD_NUMBER: _ClassVar[int]
    WHY_THIS_DECISION_FIELD_NUMBER: _ClassVar[int]
    WHY_NOT_ALTERNATIVES_FIELD_NUMBER: _ClassVar[int]
    FACTOR_WEIGHTS_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    decision: Decision
    why_this_decision: _containers.RepeatedScalarFieldContainer[str]
    why_not_alternatives: _containers.RepeatedScalarFieldContainer[str]
    factor_weights: _containers.ScalarMap[str, float]
    summary: str
    def __init__(self, decision: _Optional[_Union[Decision, _Mapping]] = ..., why_this_decision: _Optional[_Iterable[str]] = ..., why_not_alternatives: _Optional[_Iterable[str]] = ..., factor_weights: _Optional[_Mapping[str, float]] = ..., summary: _Optional[str] = ...) -> None: ...

class ExplainDecisionRequest(_message.Message):
    __slots__ = ("decision", "alternatives")
    DECISION_FIELD_NUMBER: _ClassVar[int]
    ALTERNATIVES_FIELD_NUMBER: _ClassVar[int]
    decision: Decision
    alternatives: _containers.RepeatedCompositeFieldContainer[Alternative]
    def __init__(self, decision: _Optional[_Union[Decision, _Mapping]] = ..., alternatives: _Optional[_Iterable[_Union[Alternative, _Mapping]]] = ...) -> None: ...

class ExplainDecisionResponse(_message.Message):
    __slots__ = ("explanation", "error")
    EXPLANATION_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    explanation: Explanation
    error: _types_pb2.Error
    def __init__(self, explanation: _Optional[_Union[Explanation, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class Situation(_message.Message):
    __slots__ = ("name", "domain", "description", "entities", "relationships", "solution", "outcome", "metadata")
    class RelationshipsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIPS_FIELD_NUMBER: _ClassVar[int]
    SOLUTION_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    name: str
    domain: str
    description: str
    entities: _containers.RepeatedScalarFieldContainer[str]
    relationships: _containers.ScalarMap[str, str]
    solution: str
    outcome: str
    metadata: _types_pb2.Metadata
    def __init__(self, name: _Optional[str] = ..., domain: _Optional[str] = ..., description: _Optional[str] = ..., entities: _Optional[_Iterable[str]] = ..., relationships: _Optional[_Mapping[str, str]] = ..., solution: _Optional[str] = ..., outcome: _Optional[str] = ..., metadata: _Optional[_Union[_types_pb2.Metadata, _Mapping]] = ...) -> None: ...

class AnalogyMatch(_message.Message):
    __slots__ = ("source_situation", "target_situation", "similarity_score", "matching_features", "transferable_insights", "confidence")
    SOURCE_SITUATION_FIELD_NUMBER: _ClassVar[int]
    TARGET_SITUATION_FIELD_NUMBER: _ClassVar[int]
    SIMILARITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    MATCHING_FEATURES_FIELD_NUMBER: _ClassVar[int]
    TRANSFERABLE_INSIGHTS_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    source_situation: Situation
    target_situation: Situation
    similarity_score: float
    matching_features: _containers.RepeatedScalarFieldContainer[str]
    transferable_insights: _containers.RepeatedScalarFieldContainer[str]
    confidence: _types_pb2.Confidence
    def __init__(self, source_situation: _Optional[_Union[Situation, _Mapping]] = ..., target_situation: _Optional[_Union[Situation, _Mapping]] = ..., similarity_score: _Optional[float] = ..., matching_features: _Optional[_Iterable[str]] = ..., transferable_insights: _Optional[_Iterable[str]] = ..., confidence: _Optional[_Union[_types_pb2.Confidence, _Mapping]] = ...) -> None: ...

class FindAnalogyRequest(_message.Message):
    __slots__ = ("current_situation", "past_situations", "max_results", "min_similarity")
    CURRENT_SITUATION_FIELD_NUMBER: _ClassVar[int]
    PAST_SITUATIONS_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    MIN_SIMILARITY_FIELD_NUMBER: _ClassVar[int]
    current_situation: Situation
    past_situations: _containers.RepeatedCompositeFieldContainer[Situation]
    max_results: int
    min_similarity: float
    def __init__(self, current_situation: _Optional[_Union[Situation, _Mapping]] = ..., past_situations: _Optional[_Iterable[_Union[Situation, _Mapping]]] = ..., max_results: _Optional[int] = ..., min_similarity: _Optional[float] = ...) -> None: ...

class FindAnalogyResponse(_message.Message):
    __slots__ = ("matches", "error")
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    matches: _containers.RepeatedCompositeFieldContainer[AnalogyMatch]
    error: _types_pb2.Error
    def __init__(self, matches: _Optional[_Iterable[_Union[AnalogyMatch, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class Hypothesis(_message.Message):
    __slots__ = ("name", "description", "prior_probability", "posterior_probability", "evidence_impact")
    class EvidenceImpactEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PRIOR_PROBABILITY_FIELD_NUMBER: _ClassVar[int]
    POSTERIOR_PROBABILITY_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_IMPACT_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    prior_probability: float
    posterior_probability: float
    evidence_impact: _containers.ScalarMap[str, float]
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., prior_probability: _Optional[float] = ..., posterior_probability: _Optional[float] = ..., evidence_impact: _Optional[_Mapping[str, float]] = ...) -> None: ...

class EvidenceProb(_message.Message):
    __slots__ = ("description", "likelihood_if_true", "strength", "observed_at")
    class LikelihoodIfTrueEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    LIKELIHOOD_IF_TRUE_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    OBSERVED_AT_FIELD_NUMBER: _ClassVar[int]
    description: str
    likelihood_if_true: _containers.ScalarMap[str, float]
    strength: float
    observed_at: _types_pb2.Timestamp
    def __init__(self, description: _Optional[str] = ..., likelihood_if_true: _Optional[_Mapping[str, float]] = ..., strength: _Optional[float] = ..., observed_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ProbabilisticOption(_message.Message):
    __slots__ = ("name", "outcomes", "expected_value")
    NAME_FIELD_NUMBER: _ClassVar[int]
    OUTCOMES_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_VALUE_FIELD_NUMBER: _ClassVar[int]
    name: str
    outcomes: _containers.RepeatedCompositeFieldContainer[Outcome]
    expected_value: float
    def __init__(self, name: _Optional[str] = ..., outcomes: _Optional[_Iterable[_Union[Outcome, _Mapping]]] = ..., expected_value: _Optional[float] = ...) -> None: ...

class Outcome(_message.Message):
    __slots__ = ("description", "probability", "value")
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PROBABILITY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    description: str
    probability: float
    value: float
    def __init__(self, description: _Optional[str] = ..., probability: _Optional[float] = ..., value: _Optional[float] = ...) -> None: ...

class UpdateBeliefsRequest(_message.Message):
    __slots__ = ("hypotheses", "evidence")
    HYPOTHESES_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    hypotheses: _containers.RepeatedCompositeFieldContainer[Hypothesis]
    evidence: _containers.RepeatedCompositeFieldContainer[EvidenceProb]
    def __init__(self, hypotheses: _Optional[_Iterable[_Union[Hypothesis, _Mapping]]] = ..., evidence: _Optional[_Iterable[_Union[EvidenceProb, _Mapping]]] = ...) -> None: ...

class UpdateBeliefsResponse(_message.Message):
    __slots__ = ("posterior_probabilities", "most_likely", "error")
    class PosteriorProbabilitiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    POSTERIOR_PROBABILITIES_FIELD_NUMBER: _ClassVar[int]
    MOST_LIKELY_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    posterior_probabilities: _containers.ScalarMap[str, float]
    most_likely: Hypothesis
    error: _types_pb2.Error
    def __init__(self, posterior_probabilities: _Optional[_Mapping[str, float]] = ..., most_likely: _Optional[_Union[Hypothesis, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class DecideUnderUncertaintyRequest(_message.Message):
    __slots__ = ("options", "risk_tolerance")
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    RISK_TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    options: _containers.RepeatedCompositeFieldContainer[ProbabilisticOption]
    risk_tolerance: float
    def __init__(self, options: _Optional[_Iterable[_Union[ProbabilisticOption, _Mapping]]] = ..., risk_tolerance: _Optional[float] = ...) -> None: ...

class DecideUnderUncertaintyResponse(_message.Message):
    __slots__ = ("best_option", "expected_value", "confidence", "ranked_options", "error")
    BEST_OPTION_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_VALUE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    RANKED_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    best_option: str
    expected_value: float
    confidence: _types_pb2.Confidence
    ranked_options: _containers.RepeatedCompositeFieldContainer[ProbabilisticOption]
    error: _types_pb2.Error
    def __init__(self, best_option: _Optional[str] = ..., expected_value: _Optional[float] = ..., confidence: _Optional[_Union[_types_pb2.Confidence, _Mapping]] = ..., ranked_options: _Optional[_Iterable[_Union[ProbabilisticOption, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class CognitiveState(_message.Message):
    __slots__ = ("timestamp", "context", "decision", "outcome", "state_variables")
    class StateVariablesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    STATE_VARIABLES_FIELD_NUMBER: _ClassVar[int]
    timestamp: _types_pb2.Timestamp
    context: str
    decision: str
    outcome: str
    state_variables: _containers.ScalarMap[str, str]
    def __init__(self, timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., context: _Optional[str] = ..., decision: _Optional[str] = ..., outcome: _Optional[str] = ..., state_variables: _Optional[_Mapping[str, str]] = ...) -> None: ...

class DecisionPoint(_message.Message):
    __slots__ = ("timestamp", "context", "actual_decision", "alternative_decisions")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_DECISION_FIELD_NUMBER: _ClassVar[int]
    ALTERNATIVE_DECISIONS_FIELD_NUMBER: _ClassVar[int]
    timestamp: _types_pb2.Timestamp
    context: str
    actual_decision: str
    alternative_decisions: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., context: _Optional[str] = ..., actual_decision: _Optional[str] = ..., alternative_decisions: _Optional[_Iterable[str]] = ...) -> None: ...

class SimulatedOutcome(_message.Message):
    __slots__ = ("alternative_decision", "simulated_outcome", "outcome_quality", "better_than_actual", "key_differences", "confidence")
    ALTERNATIVE_DECISION_FIELD_NUMBER: _ClassVar[int]
    SIMULATED_OUTCOME_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_QUALITY_FIELD_NUMBER: _ClassVar[int]
    BETTER_THAN_ACTUAL_FIELD_NUMBER: _ClassVar[int]
    KEY_DIFFERENCES_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    alternative_decision: str
    simulated_outcome: str
    outcome_quality: float
    better_than_actual: bool
    key_differences: _containers.RepeatedScalarFieldContainer[str]
    confidence: _types_pb2.Confidence
    def __init__(self, alternative_decision: _Optional[str] = ..., simulated_outcome: _Optional[str] = ..., outcome_quality: _Optional[float] = ..., better_than_actual: bool = ..., key_differences: _Optional[_Iterable[str]] = ..., confidence: _Optional[_Union[_types_pb2.Confidence, _Mapping]] = ...) -> None: ...

class CounterfactualAnalysis(_message.Message):
    __slots__ = ("actual_state", "decision_point", "scenarios", "lessons_learned")
    ACTUAL_STATE_FIELD_NUMBER: _ClassVar[int]
    DECISION_POINT_FIELD_NUMBER: _ClassVar[int]
    SCENARIOS_FIELD_NUMBER: _ClassVar[int]
    LESSONS_LEARNED_FIELD_NUMBER: _ClassVar[int]
    actual_state: CognitiveState
    decision_point: DecisionPoint
    scenarios: _containers.RepeatedCompositeFieldContainer[SimulatedOutcome]
    lessons_learned: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, actual_state: _Optional[_Union[CognitiveState, _Mapping]] = ..., decision_point: _Optional[_Union[DecisionPoint, _Mapping]] = ..., scenarios: _Optional[_Iterable[_Union[SimulatedOutcome, _Mapping]]] = ..., lessons_learned: _Optional[_Iterable[str]] = ...) -> None: ...

class SimulateCounterfactualsRequest(_message.Message):
    __slots__ = ("past_state", "decision_point")
    PAST_STATE_FIELD_NUMBER: _ClassVar[int]
    DECISION_POINT_FIELD_NUMBER: _ClassVar[int]
    past_state: CognitiveState
    decision_point: DecisionPoint
    def __init__(self, past_state: _Optional[_Union[CognitiveState, _Mapping]] = ..., decision_point: _Optional[_Union[DecisionPoint, _Mapping]] = ...) -> None: ...

class SimulateCounterfactualsResponse(_message.Message):
    __slots__ = ("analysis", "error")
    ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    analysis: CounterfactualAnalysis
    error: _types_pb2.Error
    def __init__(self, analysis: _Optional[_Union[CounterfactualAnalysis, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class SystemNode(_message.Message):
    __slots__ = ("name", "node_type", "state", "tags")
    class NodeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NODE_TYPE_UNSPECIFIED: _ClassVar[SystemNode.NodeType]
        NODE_TYPE_EXTERNAL: _ClassVar[SystemNode.NodeType]
        NODE_TYPE_INTERNAL: _ClassVar[SystemNode.NodeType]
        NODE_TYPE_OUTPUT: _ClassVar[SystemNode.NodeType]
    NODE_TYPE_UNSPECIFIED: SystemNode.NodeType
    NODE_TYPE_EXTERNAL: SystemNode.NodeType
    NODE_TYPE_INTERNAL: SystemNode.NodeType
    NODE_TYPE_OUTPUT: SystemNode.NodeType
    class StateEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_TYPE_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    name: str
    node_type: SystemNode.NodeType
    state: _containers.ScalarMap[str, str]
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., node_type: _Optional[_Union[SystemNode.NodeType, str]] = ..., state: _Optional[_Mapping[str, str]] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class CausalLink(_message.Message):
    __slots__ = ("from_node", "to_node", "link_type", "strength", "description", "delay_seconds")
    class LinkType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LINK_TYPE_UNSPECIFIED: _ClassVar[CausalLink.LinkType]
        LINK_TYPE_POSITIVE: _ClassVar[CausalLink.LinkType]
        LINK_TYPE_NEGATIVE: _ClassVar[CausalLink.LinkType]
    LINK_TYPE_UNSPECIFIED: CausalLink.LinkType
    LINK_TYPE_POSITIVE: CausalLink.LinkType
    LINK_TYPE_NEGATIVE: CausalLink.LinkType
    FROM_NODE_FIELD_NUMBER: _ClassVar[int]
    TO_NODE_FIELD_NUMBER: _ClassVar[int]
    LINK_TYPE_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DELAY_SECONDS_FIELD_NUMBER: _ClassVar[int]
    from_node: str
    to_node: str
    link_type: CausalLink.LinkType
    strength: float
    description: str
    delay_seconds: int
    def __init__(self, from_node: _Optional[str] = ..., to_node: _Optional[str] = ..., link_type: _Optional[_Union[CausalLink.LinkType, str]] = ..., strength: _Optional[float] = ..., description: _Optional[str] = ..., delay_seconds: _Optional[int] = ...) -> None: ...

class FeedbackLoop(_message.Message):
    __slots__ = ("nodes", "loop_type", "strength", "impact", "description")
    class LoopType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LOOP_TYPE_UNSPECIFIED: _ClassVar[FeedbackLoop.LoopType]
        LOOP_TYPE_REINFORCING: _ClassVar[FeedbackLoop.LoopType]
        LOOP_TYPE_BALANCING: _ClassVar[FeedbackLoop.LoopType]
    LOOP_TYPE_UNSPECIFIED: FeedbackLoop.LoopType
    LOOP_TYPE_REINFORCING: FeedbackLoop.LoopType
    LOOP_TYPE_BALANCING: FeedbackLoop.LoopType
    NODES_FIELD_NUMBER: _ClassVar[int]
    LOOP_TYPE_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    IMPACT_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedScalarFieldContainer[str]
    loop_type: FeedbackLoop.LoopType
    strength: float
    impact: str
    description: str
    def __init__(self, nodes: _Optional[_Iterable[str]] = ..., loop_type: _Optional[_Union[FeedbackLoop.LoopType, str]] = ..., strength: _Optional[float] = ..., impact: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class SystemAnalysis(_message.Message):
    __slots__ = ("nodes", "links", "feedback_loops", "leverage_points")
    NODES_FIELD_NUMBER: _ClassVar[int]
    LINKS_FIELD_NUMBER: _ClassVar[int]
    FEEDBACK_LOOPS_FIELD_NUMBER: _ClassVar[int]
    LEVERAGE_POINTS_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[SystemNode]
    links: _containers.RepeatedCompositeFieldContainer[CausalLink]
    feedback_loops: _containers.RepeatedCompositeFieldContainer[FeedbackLoop]
    leverage_points: _containers.RepeatedCompositeFieldContainer[LeveragePoint]
    def __init__(self, nodes: _Optional[_Iterable[_Union[SystemNode, _Mapping]]] = ..., links: _Optional[_Iterable[_Union[CausalLink, _Mapping]]] = ..., feedback_loops: _Optional[_Iterable[_Union[FeedbackLoop, _Mapping]]] = ..., leverage_points: _Optional[_Iterable[_Union[LeveragePoint, _Mapping]]] = ...) -> None: ...

class LeveragePoint(_message.Message):
    __slots__ = ("node", "reason", "impact_score", "recommendations")
    NODE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    IMPACT_SCORE_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATIONS_FIELD_NUMBER: _ClassVar[int]
    node: str
    reason: str
    impact_score: float
    recommendations: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, node: _Optional[str] = ..., reason: _Optional[str] = ..., impact_score: _Optional[float] = ..., recommendations: _Optional[_Iterable[str]] = ...) -> None: ...

class AnalyzeSystemRequest(_message.Message):
    __slots__ = ("nodes", "links")
    NODES_FIELD_NUMBER: _ClassVar[int]
    LINKS_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[SystemNode]
    links: _containers.RepeatedCompositeFieldContainer[CausalLink]
    def __init__(self, nodes: _Optional[_Iterable[_Union[SystemNode, _Mapping]]] = ..., links: _Optional[_Iterable[_Union[CausalLink, _Mapping]]] = ...) -> None: ...

class AnalyzeSystemResponse(_message.Message):
    __slots__ = ("analysis", "error")
    ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    analysis: SystemAnalysis
    error: _types_pb2.Error
    def __init__(self, analysis: _Optional[_Union[SystemAnalysis, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class Objective(_message.Message):
    __slots__ = ("name", "minimize", "weight", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    MINIMIZE_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    minimize: bool
    weight: float
    description: str
    def __init__(self, name: _Optional[str] = ..., minimize: bool = ..., weight: _Optional[float] = ..., description: _Optional[str] = ...) -> None: ...

class MultiObjectiveOption(_message.Message):
    __slots__ = ("name", "scores", "description")
    class ScoresEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    SCORES_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    scores: _containers.ScalarMap[str, float]
    description: str
    def __init__(self, name: _Optional[str] = ..., scores: _Optional[_Mapping[str, float]] = ..., description: _Optional[str] = ...) -> None: ...

class OptimizationResult(_message.Message):
    __slots__ = ("ranked_options", "best_option", "pareto_optimal", "dominated")
    RANKED_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    BEST_OPTION_FIELD_NUMBER: _ClassVar[int]
    PARETO_OPTIMAL_FIELD_NUMBER: _ClassVar[int]
    DOMINATED_FIELD_NUMBER: _ClassVar[int]
    ranked_options: _containers.RepeatedCompositeFieldContainer[RankedOption]
    best_option: RankedOption
    pareto_optimal: _containers.RepeatedScalarFieldContainer[str]
    dominated: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ranked_options: _Optional[_Iterable[_Union[RankedOption, _Mapping]]] = ..., best_option: _Optional[_Union[RankedOption, _Mapping]] = ..., pareto_optimal: _Optional[_Iterable[str]] = ..., dominated: _Optional[_Iterable[str]] = ...) -> None: ...

class RankedOption(_message.Message):
    __slots__ = ("name", "rank", "overall_score", "scores", "normalized_scores")
    class ScoresEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    class NormalizedScoresEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    RANK_FIELD_NUMBER: _ClassVar[int]
    OVERALL_SCORE_FIELD_NUMBER: _ClassVar[int]
    SCORES_FIELD_NUMBER: _ClassVar[int]
    NORMALIZED_SCORES_FIELD_NUMBER: _ClassVar[int]
    name: str
    rank: int
    overall_score: float
    scores: _containers.ScalarMap[str, float]
    normalized_scores: _containers.ScalarMap[str, float]
    def __init__(self, name: _Optional[str] = ..., rank: _Optional[int] = ..., overall_score: _Optional[float] = ..., scores: _Optional[_Mapping[str, float]] = ..., normalized_scores: _Optional[_Mapping[str, float]] = ...) -> None: ...

class OptimizeRequest(_message.Message):
    __slots__ = ("objectives", "options")
    OBJECTIVES_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    objectives: _containers.RepeatedCompositeFieldContainer[Objective]
    options: _containers.RepeatedCompositeFieldContainer[MultiObjectiveOption]
    def __init__(self, objectives: _Optional[_Iterable[_Union[Objective, _Mapping]]] = ..., options: _Optional[_Iterable[_Union[MultiObjectiveOption, _Mapping]]] = ...) -> None: ...

class OptimizeResponse(_message.Message):
    __slots__ = ("result", "error")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    result: OptimizationResult
    error: _types_pb2.Error
    def __init__(self, result: _Optional[_Union[OptimizationResult, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class CognitiveRequest(_message.Message):
    __slots__ = ("subject", "problem_description", "context", "use_questioning", "use_critical_thinking", "use_explainer", "use_analogical", "use_probabilistic", "use_counterfactual", "use_systems", "use_multi_objective")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    PROBLEM_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    USE_QUESTIONING_FIELD_NUMBER: _ClassVar[int]
    USE_CRITICAL_THINKING_FIELD_NUMBER: _ClassVar[int]
    USE_EXPLAINER_FIELD_NUMBER: _ClassVar[int]
    USE_ANALOGICAL_FIELD_NUMBER: _ClassVar[int]
    USE_PROBABILISTIC_FIELD_NUMBER: _ClassVar[int]
    USE_COUNTERFACTUAL_FIELD_NUMBER: _ClassVar[int]
    USE_SYSTEMS_FIELD_NUMBER: _ClassVar[int]
    USE_MULTI_OBJECTIVE_FIELD_NUMBER: _ClassVar[int]
    subject: str
    problem_description: str
    context: _containers.ScalarMap[str, str]
    use_questioning: bool
    use_critical_thinking: bool
    use_explainer: bool
    use_analogical: bool
    use_probabilistic: bool
    use_counterfactual: bool
    use_systems: bool
    use_multi_objective: bool
    def __init__(self, subject: _Optional[str] = ..., problem_description: _Optional[str] = ..., context: _Optional[_Mapping[str, str]] = ..., use_questioning: bool = ..., use_critical_thinking: bool = ..., use_explainer: bool = ..., use_analogical: bool = ..., use_probabilistic: bool = ..., use_counterfactual: bool = ..., use_systems: bool = ..., use_multi_objective: bool = ...) -> None: ...

class CognitiveResponse(_message.Message):
    __slots__ = ("questioning", "critical_thinking", "explainer", "analogical", "probabilistic", "counterfactual", "systems", "multi_objective", "unified_insights", "recommended_action", "overall_confidence", "metadata", "error")
    QUESTIONING_FIELD_NUMBER: _ClassVar[int]
    CRITICAL_THINKING_FIELD_NUMBER: _ClassVar[int]
    EXPLAINER_FIELD_NUMBER: _ClassVar[int]
    ANALOGICAL_FIELD_NUMBER: _ClassVar[int]
    PROBABILISTIC_FIELD_NUMBER: _ClassVar[int]
    COUNTERFACTUAL_FIELD_NUMBER: _ClassVar[int]
    SYSTEMS_FIELD_NUMBER: _ClassVar[int]
    MULTI_OBJECTIVE_FIELD_NUMBER: _ClassVar[int]
    UNIFIED_INSIGHTS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_ACTION_FIELD_NUMBER: _ClassVar[int]
    OVERALL_CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    questioning: QuestioningResponse
    critical_thinking: EvaluateReasoningResponse
    explainer: ExplainDecisionResponse
    analogical: FindAnalogyResponse
    probabilistic: UpdateBeliefsResponse
    counterfactual: SimulateCounterfactualsResponse
    systems: AnalyzeSystemResponse
    multi_objective: OptimizeResponse
    unified_insights: _containers.RepeatedScalarFieldContainer[str]
    recommended_action: str
    overall_confidence: _types_pb2.Confidence
    metadata: _types_pb2.Metadata
    error: _types_pb2.Error
    def __init__(self, questioning: _Optional[_Union[QuestioningResponse, _Mapping]] = ..., critical_thinking: _Optional[_Union[EvaluateReasoningResponse, _Mapping]] = ..., explainer: _Optional[_Union[ExplainDecisionResponse, _Mapping]] = ..., analogical: _Optional[_Union[FindAnalogyResponse, _Mapping]] = ..., probabilistic: _Optional[_Union[UpdateBeliefsResponse, _Mapping]] = ..., counterfactual: _Optional[_Union[SimulateCounterfactualsResponse, _Mapping]] = ..., systems: _Optional[_Union[AnalyzeSystemResponse, _Mapping]] = ..., multi_objective: _Optional[_Union[OptimizeResponse, _Mapping]] = ..., unified_insights: _Optional[_Iterable[str]] = ..., recommended_action: _Optional[str] = ..., overall_confidence: _Optional[_Union[_types_pb2.Confidence, _Mapping]] = ..., metadata: _Optional[_Union[_types_pb2.Metadata, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...
