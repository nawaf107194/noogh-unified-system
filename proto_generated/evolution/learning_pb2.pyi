from proto_generated.common import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class InnovationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    INNOVATION_TYPE_UNSPECIFIED: _ClassVar[InnovationType]
    INNOVATION_TYPE_BUG_FIX: _ClassVar[InnovationType]
    INNOVATION_TYPE_PERFORMANCE: _ClassVar[InnovationType]
    INNOVATION_TYPE_FEATURE: _ClassVar[InnovationType]
    INNOVATION_TYPE_REFACTOR: _ClassVar[InnovationType]
    INNOVATION_TYPE_CONFIG: _ClassVar[InnovationType]
    INNOVATION_TYPE_ARCHITECTURE: _ClassVar[InnovationType]

class InnovationStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    INNOVATION_STATUS_UNSPECIFIED: _ClassVar[InnovationStatus]
    INNOVATION_STATUS_SUGGESTED: _ClassVar[InnovationStatus]
    INNOVATION_STATUS_QUEUED_FOR_EVOLUTION: _ClassVar[InnovationStatus]
    INNOVATION_STATUS_PROCESSING_BY_EVOLUTION: _ClassVar[InnovationStatus]
    INNOVATION_STATUS_CANARY_TESTING: _ClassVar[InnovationStatus]
    INNOVATION_STATUS_APPLIED: _ClassVar[InnovationStatus]
    INNOVATION_STATUS_REJECTED: _ClassVar[InnovationStatus]
    INNOVATION_STATUS_FAILED: _ClassVar[InnovationStatus]
    INNOVATION_STATUS_ROLLED_BACK: _ClassVar[InnovationStatus]

class TriggerType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TRIGGER_TYPE_UNSPECIFIED: _ClassVar[TriggerType]
    TRIGGER_TYPE_TIME_BASED: _ClassVar[TriggerType]
    TRIGGER_TYPE_EVENT_BASED: _ClassVar[TriggerType]
    TRIGGER_TYPE_THRESHOLD_BASED: _ClassVar[TriggerType]
    TRIGGER_TYPE_LEARNING_INNOVATION: _ClassVar[TriggerType]
    TRIGGER_TYPE_PERFORMANCE_DEGRADATION: _ClassVar[TriggerType]

class TriggerPriority(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TRIGGER_PRIORITY_UNSPECIFIED: _ClassVar[TriggerPriority]
    TRIGGER_PRIORITY_LOW: _ClassVar[TriggerPriority]
    TRIGGER_PRIORITY_MEDIUM: _ClassVar[TriggerPriority]
    TRIGGER_PRIORITY_HIGH: _ClassVar[TriggerPriority]
    TRIGGER_PRIORITY_CRITICAL: _ClassVar[TriggerPriority]
INNOVATION_TYPE_UNSPECIFIED: InnovationType
INNOVATION_TYPE_BUG_FIX: InnovationType
INNOVATION_TYPE_PERFORMANCE: InnovationType
INNOVATION_TYPE_FEATURE: InnovationType
INNOVATION_TYPE_REFACTOR: InnovationType
INNOVATION_TYPE_CONFIG: InnovationType
INNOVATION_TYPE_ARCHITECTURE: InnovationType
INNOVATION_STATUS_UNSPECIFIED: InnovationStatus
INNOVATION_STATUS_SUGGESTED: InnovationStatus
INNOVATION_STATUS_QUEUED_FOR_EVOLUTION: InnovationStatus
INNOVATION_STATUS_PROCESSING_BY_EVOLUTION: InnovationStatus
INNOVATION_STATUS_CANARY_TESTING: InnovationStatus
INNOVATION_STATUS_APPLIED: InnovationStatus
INNOVATION_STATUS_REJECTED: InnovationStatus
INNOVATION_STATUS_FAILED: InnovationStatus
INNOVATION_STATUS_ROLLED_BACK: InnovationStatus
TRIGGER_TYPE_UNSPECIFIED: TriggerType
TRIGGER_TYPE_TIME_BASED: TriggerType
TRIGGER_TYPE_EVENT_BASED: TriggerType
TRIGGER_TYPE_THRESHOLD_BASED: TriggerType
TRIGGER_TYPE_LEARNING_INNOVATION: TriggerType
TRIGGER_TYPE_PERFORMANCE_DEGRADATION: TriggerType
TRIGGER_PRIORITY_UNSPECIFIED: TriggerPriority
TRIGGER_PRIORITY_LOW: TriggerPriority
TRIGGER_PRIORITY_MEDIUM: TriggerPriority
TRIGGER_PRIORITY_HIGH: TriggerPriority
TRIGGER_PRIORITY_CRITICAL: TriggerPriority

class Innovation(_message.Message):
    __slots__ = ("id", "innovation_type", "status", "title", "description", "reasoning", "benefits", "risks", "source", "trigger_event", "context", "confidence", "impact_score", "priority", "estimated_effort_hours", "code_changes", "affected_files", "dependencies", "canary_test", "test_results", "outcome", "failure_reason", "lessons_learned", "suggested_at", "applied_at", "rolled_back_at", "applied_by")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    INNOVATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    BENEFITS_FIELD_NUMBER: _ClassVar[int]
    RISKS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_EVENT_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    IMPACT_SCORE_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_EFFORT_HOURS_FIELD_NUMBER: _ClassVar[int]
    CODE_CHANGES_FIELD_NUMBER: _ClassVar[int]
    AFFECTED_FILES_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    CANARY_TEST_FIELD_NUMBER: _ClassVar[int]
    TEST_RESULTS_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    FAILURE_REASON_FIELD_NUMBER: _ClassVar[int]
    LESSONS_LEARNED_FIELD_NUMBER: _ClassVar[int]
    SUGGESTED_AT_FIELD_NUMBER: _ClassVar[int]
    APPLIED_AT_FIELD_NUMBER: _ClassVar[int]
    ROLLED_BACK_AT_FIELD_NUMBER: _ClassVar[int]
    APPLIED_BY_FIELD_NUMBER: _ClassVar[int]
    id: str
    innovation_type: InnovationType
    status: InnovationStatus
    title: str
    description: str
    reasoning: str
    benefits: _containers.RepeatedScalarFieldContainer[str]
    risks: _containers.RepeatedScalarFieldContainer[str]
    source: str
    trigger_event: str
    context: _containers.ScalarMap[str, str]
    confidence: float
    impact_score: float
    priority: int
    estimated_effort_hours: float
    code_changes: _containers.RepeatedCompositeFieldContainer[CodeChange]
    affected_files: _containers.RepeatedScalarFieldContainer[str]
    dependencies: _containers.RepeatedScalarFieldContainer[str]
    canary_test: CanaryTest
    test_results: _containers.RepeatedCompositeFieldContainer[TestResult]
    outcome: str
    failure_reason: str
    lessons_learned: _containers.RepeatedScalarFieldContainer[str]
    suggested_at: _types_pb2.Timestamp
    applied_at: _types_pb2.Timestamp
    rolled_back_at: _types_pb2.Timestamp
    applied_by: str
    def __init__(self, id: _Optional[str] = ..., innovation_type: _Optional[_Union[InnovationType, str]] = ..., status: _Optional[_Union[InnovationStatus, str]] = ..., title: _Optional[str] = ..., description: _Optional[str] = ..., reasoning: _Optional[str] = ..., benefits: _Optional[_Iterable[str]] = ..., risks: _Optional[_Iterable[str]] = ..., source: _Optional[str] = ..., trigger_event: _Optional[str] = ..., context: _Optional[_Mapping[str, str]] = ..., confidence: _Optional[float] = ..., impact_score: _Optional[float] = ..., priority: _Optional[int] = ..., estimated_effort_hours: _Optional[float] = ..., code_changes: _Optional[_Iterable[_Union[CodeChange, _Mapping]]] = ..., affected_files: _Optional[_Iterable[str]] = ..., dependencies: _Optional[_Iterable[str]] = ..., canary_test: _Optional[_Union[CanaryTest, _Mapping]] = ..., test_results: _Optional[_Iterable[_Union[TestResult, _Mapping]]] = ..., outcome: _Optional[str] = ..., failure_reason: _Optional[str] = ..., lessons_learned: _Optional[_Iterable[str]] = ..., suggested_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., applied_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., rolled_back_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., applied_by: _Optional[str] = ...) -> None: ...

class CodeChange(_message.Message):
    __slots__ = ("file_path", "change_type", "diff", "lines_added", "lines_removed")
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    CHANGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DIFF_FIELD_NUMBER: _ClassVar[int]
    LINES_ADDED_FIELD_NUMBER: _ClassVar[int]
    LINES_REMOVED_FIELD_NUMBER: _ClassVar[int]
    file_path: str
    change_type: str
    diff: str
    lines_added: int
    lines_removed: int
    def __init__(self, file_path: _Optional[str] = ..., change_type: _Optional[str] = ..., diff: _Optional[str] = ..., lines_added: _Optional[int] = ..., lines_removed: _Optional[int] = ...) -> None: ...

class CanaryTest(_message.Message):
    __slots__ = ("test_type", "traffic_percentage", "duration_seconds", "success_criteria", "baseline_metrics")
    class TestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        TEST_TYPE_UNSPECIFIED: _ClassVar[CanaryTest.TestType]
        TEST_TYPE_UNIT: _ClassVar[CanaryTest.TestType]
        TEST_TYPE_INTEGRATION: _ClassVar[CanaryTest.TestType]
        TEST_TYPE_PERFORMANCE: _ClassVar[CanaryTest.TestType]
        TEST_TYPE_LIVE_TRAFFIC: _ClassVar[CanaryTest.TestType]
    TEST_TYPE_UNSPECIFIED: CanaryTest.TestType
    TEST_TYPE_UNIT: CanaryTest.TestType
    TEST_TYPE_INTEGRATION: CanaryTest.TestType
    TEST_TYPE_PERFORMANCE: CanaryTest.TestType
    TEST_TYPE_LIVE_TRAFFIC: CanaryTest.TestType
    class BaselineMetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    TEST_TYPE_FIELD_NUMBER: _ClassVar[int]
    TRAFFIC_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    DURATION_SECONDS_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_CRITERIA_FIELD_NUMBER: _ClassVar[int]
    BASELINE_METRICS_FIELD_NUMBER: _ClassVar[int]
    test_type: CanaryTest.TestType
    traffic_percentage: float
    duration_seconds: int
    success_criteria: _containers.RepeatedScalarFieldContainer[str]
    baseline_metrics: _containers.ScalarMap[str, float]
    def __init__(self, test_type: _Optional[_Union[CanaryTest.TestType, str]] = ..., traffic_percentage: _Optional[float] = ..., duration_seconds: _Optional[int] = ..., success_criteria: _Optional[_Iterable[str]] = ..., baseline_metrics: _Optional[_Mapping[str, float]] = ...) -> None: ...

class TestResult(_message.Message):
    __slots__ = ("test_name", "passed", "duration_ms", "output", "error", "executed_at")
    TEST_NAME_FIELD_NUMBER: _ClassVar[int]
    PASSED_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    EXECUTED_AT_FIELD_NUMBER: _ClassVar[int]
    test_name: str
    passed: bool
    duration_ms: float
    output: str
    error: _types_pb2.Error
    executed_at: _types_pb2.Timestamp
    def __init__(self, test_name: _Optional[str] = ..., passed: bool = ..., duration_ms: _Optional[float] = ..., output: _Optional[str] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ..., executed_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class EvolutionTrigger(_message.Message):
    __slots__ = ("id", "trigger_type", "priority", "name", "description", "condition", "thresholds", "required_signals", "action", "parameters", "fired", "fire_count", "last_fired_at", "created_at", "updated_at")
    class ThresholdsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_TYPE_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    THRESHOLDS_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_SIGNALS_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    FIRED_FIELD_NUMBER: _ClassVar[int]
    FIRE_COUNT_FIELD_NUMBER: _ClassVar[int]
    LAST_FIRED_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    trigger_type: TriggerType
    priority: TriggerPriority
    name: str
    description: str
    condition: str
    thresholds: _containers.ScalarMap[str, float]
    required_signals: _containers.RepeatedScalarFieldContainer[str]
    action: str
    parameters: _containers.ScalarMap[str, str]
    fired: bool
    fire_count: int
    last_fired_at: _types_pb2.Timestamp
    created_at: _types_pb2.Timestamp
    updated_at: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., trigger_type: _Optional[_Union[TriggerType, str]] = ..., priority: _Optional[_Union[TriggerPriority, str]] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., condition: _Optional[str] = ..., thresholds: _Optional[_Mapping[str, float]] = ..., required_signals: _Optional[_Iterable[str]] = ..., action: _Optional[str] = ..., parameters: _Optional[_Mapping[str, str]] = ..., fired: bool = ..., fire_count: _Optional[int] = ..., last_fired_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., created_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class TriggerEvent(_message.Message):
    __slots__ = ("trigger_id", "trigger_name", "priority", "context", "innovations_triggered", "fired_at")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TRIGGER_ID_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_NAME_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    INNOVATIONS_TRIGGERED_FIELD_NUMBER: _ClassVar[int]
    FIRED_AT_FIELD_NUMBER: _ClassVar[int]
    trigger_id: str
    trigger_name: str
    priority: TriggerPriority
    context: _containers.ScalarMap[str, str]
    innovations_triggered: _containers.RepeatedScalarFieldContainer[str]
    fired_at: _types_pb2.Timestamp
    def __init__(self, trigger_id: _Optional[str] = ..., trigger_name: _Optional[str] = ..., priority: _Optional[_Union[TriggerPriority, str]] = ..., context: _Optional[_Mapping[str, str]] = ..., innovations_triggered: _Optional[_Iterable[str]] = ..., fired_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Observation(_message.Message):
    __slots__ = ("id", "source", "category", "description", "context", "metrics", "significance", "observed_at")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class MetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    SIGNIFICANCE_FIELD_NUMBER: _ClassVar[int]
    OBSERVED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    source: str
    category: str
    description: str
    context: _containers.ScalarMap[str, str]
    metrics: _containers.ScalarMap[str, float]
    significance: float
    observed_at: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., source: _Optional[str] = ..., category: _Optional[str] = ..., description: _Optional[str] = ..., context: _Optional[_Mapping[str, str]] = ..., metrics: _Optional[_Mapping[str, float]] = ..., significance: _Optional[float] = ..., observed_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Pattern(_message.Message):
    __slots__ = ("id", "pattern_type", "description", "supporting_observations", "confidence", "occurrence_count", "first_seen", "last_seen")
    ID_FIELD_NUMBER: _ClassVar[int]
    PATTERN_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SUPPORTING_OBSERVATIONS_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    OCCURRENCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    FIRST_SEEN_FIELD_NUMBER: _ClassVar[int]
    LAST_SEEN_FIELD_NUMBER: _ClassVar[int]
    id: str
    pattern_type: str
    description: str
    supporting_observations: _containers.RepeatedCompositeFieldContainer[Observation]
    confidence: float
    occurrence_count: int
    first_seen: _types_pb2.Timestamp
    last_seen: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., pattern_type: _Optional[str] = ..., description: _Optional[str] = ..., supporting_observations: _Optional[_Iterable[_Union[Observation, _Mapping]]] = ..., confidence: _Optional[float] = ..., occurrence_count: _Optional[int] = ..., first_seen: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., last_seen: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Insight(_message.Message):
    __slots__ = ("id", "title", "description", "patterns", "observations", "recommendations", "confidence", "impact_potential", "generated_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PATTERNS_FIELD_NUMBER: _ClassVar[int]
    OBSERVATIONS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATIONS_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    IMPACT_POTENTIAL_FIELD_NUMBER: _ClassVar[int]
    GENERATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    title: str
    description: str
    patterns: _containers.RepeatedCompositeFieldContainer[Pattern]
    observations: _containers.RepeatedCompositeFieldContainer[Observation]
    recommendations: _containers.RepeatedScalarFieldContainer[str]
    confidence: float
    impact_potential: float
    generated_at: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., title: _Optional[str] = ..., description: _Optional[str] = ..., patterns: _Optional[_Iterable[_Union[Pattern, _Mapping]]] = ..., observations: _Optional[_Iterable[_Union[Observation, _Mapping]]] = ..., recommendations: _Optional[_Iterable[str]] = ..., confidence: _Optional[float] = ..., impact_potential: _Optional[float] = ..., generated_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Neuron(_message.Message):
    __slots__ = ("id", "concept", "activation_level", "fire_count", "last_fired", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONCEPT_FIELD_NUMBER: _ClassVar[int]
    ACTIVATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    FIRE_COUNT_FIELD_NUMBER: _ClassVar[int]
    LAST_FIRED_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    concept: str
    activation_level: float
    fire_count: int
    last_fired: _types_pb2.Timestamp
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., concept: _Optional[str] = ..., activation_level: _Optional[float] = ..., fire_count: _Optional[int] = ..., last_fired: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class Synapse(_message.Message):
    __slots__ = ("id", "from_neuron_id", "to_neuron_id", "strength", "coactivation_count", "created_at", "last_strengthened")
    ID_FIELD_NUMBER: _ClassVar[int]
    FROM_NEURON_ID_FIELD_NUMBER: _ClassVar[int]
    TO_NEURON_ID_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    COACTIVATION_COUNT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_STRENGTHENED_FIELD_NUMBER: _ClassVar[int]
    id: str
    from_neuron_id: str
    to_neuron_id: str
    strength: float
    coactivation_count: int
    created_at: _types_pb2.Timestamp
    last_strengthened: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., from_neuron_id: _Optional[str] = ..., to_neuron_id: _Optional[str] = ..., strength: _Optional[float] = ..., coactivation_count: _Optional[int] = ..., created_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., last_strengthened: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class NeuralState(_message.Message):
    __slots__ = ("neurons", "synapses", "activation_pattern", "snapshot_at")
    class ActivationPatternEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NEURONS_FIELD_NUMBER: _ClassVar[int]
    SYNAPSES_FIELD_NUMBER: _ClassVar[int]
    ACTIVATION_PATTERN_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_AT_FIELD_NUMBER: _ClassVar[int]
    neurons: _containers.RepeatedCompositeFieldContainer[Neuron]
    synapses: _containers.RepeatedCompositeFieldContainer[Synapse]
    activation_pattern: _containers.ScalarMap[str, float]
    snapshot_at: _types_pb2.Timestamp
    def __init__(self, neurons: _Optional[_Iterable[_Union[Neuron, _Mapping]]] = ..., synapses: _Optional[_Iterable[_Union[Synapse, _Mapping]]] = ..., activation_pattern: _Optional[_Mapping[str, float]] = ..., snapshot_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Belief(_message.Message):
    __slots__ = ("id", "statement", "confidence", "supporting_evidence", "contradicting_evidence", "source", "formed_at", "last_updated")
    ID_FIELD_NUMBER: _ClassVar[int]
    STATEMENT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    SUPPORTING_EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    CONTRADICTING_EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    FORMED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATED_FIELD_NUMBER: _ClassVar[int]
    id: str
    statement: str
    confidence: float
    supporting_evidence: _containers.RepeatedScalarFieldContainer[str]
    contradicting_evidence: _containers.RepeatedScalarFieldContainer[str]
    source: str
    formed_at: _types_pb2.Timestamp
    last_updated: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., statement: _Optional[str] = ..., confidence: _Optional[float] = ..., supporting_evidence: _Optional[_Iterable[str]] = ..., contradicting_evidence: _Optional[_Iterable[str]] = ..., source: _Optional[str] = ..., formed_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., last_updated: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Contradiction(_message.Message):
    __slots__ = ("id", "belief_id_1", "belief_id_2", "description", "severity", "resolved", "resolution", "detected_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    BELIEF_ID_1_FIELD_NUMBER: _ClassVar[int]
    BELIEF_ID_2_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    RESOLVED_FIELD_NUMBER: _ClassVar[int]
    RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    DETECTED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    belief_id_1: str
    belief_id_2: str
    description: str
    severity: float
    resolved: bool
    resolution: str
    detected_at: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., belief_id_1: _Optional[str] = ..., belief_id_2: _Optional[str] = ..., description: _Optional[str] = ..., severity: _Optional[float] = ..., resolved: bool = ..., resolution: _Optional[str] = ..., detected_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Failure(_message.Message):
    __slots__ = ("id", "title", "description", "category", "severity", "root_cause", "contributing_factors", "context", "occurred_at")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    ROOT_CAUSE_FIELD_NUMBER: _ClassVar[int]
    CONTRIBUTING_FACTORS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    OCCURRED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    title: str
    description: str
    category: str
    severity: float
    root_cause: str
    contributing_factors: _containers.RepeatedScalarFieldContainer[str]
    context: _containers.ScalarMap[str, str]
    occurred_at: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., title: _Optional[str] = ..., description: _Optional[str] = ..., category: _Optional[str] = ..., severity: _Optional[float] = ..., root_cause: _Optional[str] = ..., contributing_factors: _Optional[_Iterable[str]] = ..., context: _Optional[_Mapping[str, str]] = ..., occurred_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ScarTissue(_message.Message):
    __slots__ = ("id", "failure", "prevention_rules", "detection_patterns", "recovery_procedures", "prevented_recurrence_count", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    FAILURE_FIELD_NUMBER: _ClassVar[int]
    PREVENTION_RULES_FIELD_NUMBER: _ClassVar[int]
    DETECTION_PATTERNS_FIELD_NUMBER: _ClassVar[int]
    RECOVERY_PROCEDURES_FIELD_NUMBER: _ClassVar[int]
    PREVENTED_RECURRENCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    failure: Failure
    prevention_rules: _containers.RepeatedScalarFieldContainer[str]
    detection_patterns: _containers.RepeatedScalarFieldContainer[str]
    recovery_procedures: _containers.RepeatedScalarFieldContainer[str]
    prevented_recurrence_count: int
    created_at: _types_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., failure: _Optional[_Union[Failure, _Mapping]] = ..., prevention_rules: _Optional[_Iterable[str]] = ..., detection_patterns: _Optional[_Iterable[str]] = ..., recovery_procedures: _Optional[_Iterable[str]] = ..., prevented_recurrence_count: _Optional[int] = ..., created_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class SuggestInnovationRequest(_message.Message):
    __slots__ = ("observation", "patterns", "context")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    OBSERVATION_FIELD_NUMBER: _ClassVar[int]
    PATTERNS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    observation: Observation
    patterns: _containers.RepeatedCompositeFieldContainer[Pattern]
    context: _containers.ScalarMap[str, str]
    def __init__(self, observation: _Optional[_Union[Observation, _Mapping]] = ..., patterns: _Optional[_Iterable[_Union[Pattern, _Mapping]]] = ..., context: _Optional[_Mapping[str, str]] = ...) -> None: ...

class SuggestInnovationResponse(_message.Message):
    __slots__ = ("innovation", "confidence", "error")
    INNOVATION_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    innovation: Innovation
    confidence: _types_pb2.Confidence
    error: _types_pb2.Error
    def __init__(self, innovation: _Optional[_Union[Innovation, _Mapping]] = ..., confidence: _Optional[_Union[_types_pb2.Confidence, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class ApplyInnovationRequest(_message.Message):
    __slots__ = ("innovation_id", "run_canary_test", "auto_rollback_on_failure")
    INNOVATION_ID_FIELD_NUMBER: _ClassVar[int]
    RUN_CANARY_TEST_FIELD_NUMBER: _ClassVar[int]
    AUTO_ROLLBACK_ON_FAILURE_FIELD_NUMBER: _ClassVar[int]
    innovation_id: str
    run_canary_test: bool
    auto_rollback_on_failure: bool
    def __init__(self, innovation_id: _Optional[str] = ..., run_canary_test: bool = ..., auto_rollback_on_failure: bool = ...) -> None: ...

class ApplyInnovationResponse(_message.Message):
    __slots__ = ("innovation", "status", "test_results", "error")
    INNOVATION_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TEST_RESULTS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    innovation: Innovation
    status: _types_pb2.Status
    test_results: _containers.RepeatedCompositeFieldContainer[TestResult]
    error: _types_pb2.Error
    def __init__(self, innovation: _Optional[_Union[Innovation, _Mapping]] = ..., status: _Optional[_Union[_types_pb2.Status, str]] = ..., test_results: _Optional[_Iterable[_Union[TestResult, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetInnovationsRequest(_message.Message):
    __slots__ = ("statuses", "types", "start_time", "end_time", "limit")
    STATUSES_FIELD_NUMBER: _ClassVar[int]
    TYPES_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    statuses: _containers.RepeatedScalarFieldContainer[InnovationStatus]
    types: _containers.RepeatedScalarFieldContainer[InnovationType]
    start_time: _types_pb2.Timestamp
    end_time: _types_pb2.Timestamp
    limit: int
    def __init__(self, statuses: _Optional[_Iterable[_Union[InnovationStatus, str]]] = ..., types: _Optional[_Iterable[_Union[InnovationType, str]]] = ..., start_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., limit: _Optional[int] = ...) -> None: ...

class GetInnovationsResponse(_message.Message):
    __slots__ = ("innovations", "total_count", "error")
    INNOVATIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    innovations: _containers.RepeatedCompositeFieldContainer[Innovation]
    total_count: int
    error: _types_pb2.Error
    def __init__(self, innovations: _Optional[_Iterable[_Union[Innovation, _Mapping]]] = ..., total_count: _Optional[int] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class RecordObservationRequest(_message.Message):
    __slots__ = ("observation",)
    OBSERVATION_FIELD_NUMBER: _ClassVar[int]
    observation: Observation
    def __init__(self, observation: _Optional[_Union[Observation, _Mapping]] = ...) -> None: ...

class RecordObservationResponse(_message.Message):
    __slots__ = ("observation_id", "detected_patterns", "generated_insights", "error")
    OBSERVATION_ID_FIELD_NUMBER: _ClassVar[int]
    DETECTED_PATTERNS_FIELD_NUMBER: _ClassVar[int]
    GENERATED_INSIGHTS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    observation_id: str
    detected_patterns: _containers.RepeatedCompositeFieldContainer[Pattern]
    generated_insights: _containers.RepeatedCompositeFieldContainer[Insight]
    error: _types_pb2.Error
    def __init__(self, observation_id: _Optional[str] = ..., detected_patterns: _Optional[_Iterable[_Union[Pattern, _Mapping]]] = ..., generated_insights: _Optional[_Iterable[_Union[Insight, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...
