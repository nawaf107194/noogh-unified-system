from proto_generated.cognitive import intelligence_pb2 as _intelligence_pb2
from proto_generated.trading import market_pb2 as _market_pb2
from proto_generated.evolution import learning_pb2 as _learning_pb2
from proto_generated.common import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OrderbookRequest(_message.Message):
    __slots__ = ("symbol", "depth")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    depth: int
    def __init__(self, symbol: _Optional[str] = ..., depth: _Optional[int] = ...) -> None: ...

class TradesRequest(_message.Message):
    __slots__ = ("symbol", "start_time")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    start_time: _types_pb2.Timestamp
    def __init__(self, symbol: _Optional[str] = ..., start_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GenerateSignalRequest(_message.Message):
    __slots__ = ("symbol", "strategy_name", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    strategy_name: str
    parameters: _containers.ScalarMap[str, str]
    def __init__(self, symbol: _Optional[str] = ..., strategy_name: _Optional[str] = ..., parameters: _Optional[_Mapping[str, str]] = ...) -> None: ...

class GenerateSignalResponse(_message.Message):
    __slots__ = ("signal", "error")
    SIGNAL_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    signal: _market_pb2.TradingSignal
    error: _types_pb2.Error
    def __init__(self, signal: _Optional[_Union[_market_pb2.TradingSignal, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetSignalsRequest(_message.Message):
    __slots__ = ("symbol", "signal_types", "start_time", "end_time", "limit")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_TYPES_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    signal_types: _containers.RepeatedScalarFieldContainer[_market_pb2.SignalType]
    start_time: _types_pb2.Timestamp
    end_time: _types_pb2.Timestamp
    limit: int
    def __init__(self, symbol: _Optional[str] = ..., signal_types: _Optional[_Iterable[_Union[_market_pb2.SignalType, str]]] = ..., start_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., limit: _Optional[int] = ...) -> None: ...

class GetSignalsResponse(_message.Message):
    __slots__ = ("signals", "error")
    SIGNALS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    signals: _containers.RepeatedCompositeFieldContainer[_market_pb2.TradingSignal]
    error: _types_pb2.Error
    def __init__(self, signals: _Optional[_Iterable[_Union[_market_pb2.TradingSignal, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class StreamSignalsRequest(_message.Message):
    __slots__ = ("symbol", "signal_types")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_TYPES_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    signal_types: _containers.RepeatedScalarFieldContainer[_market_pb2.SignalType]
    def __init__(self, symbol: _Optional[str] = ..., signal_types: _Optional[_Iterable[_Union[_market_pb2.SignalType, str]]] = ...) -> None: ...

class CancelOrderRequest(_message.Message):
    __slots__ = ("order_id", "symbol")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    symbol: str
    def __init__(self, order_id: _Optional[str] = ..., symbol: _Optional[str] = ...) -> None: ...

class CancelOrderResponse(_message.Message):
    __slots__ = ("order", "error")
    ORDER_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    order: _market_pb2.Order
    error: _types_pb2.Error
    def __init__(self, order: _Optional[_Union[_market_pb2.Order, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetOrderRequest(_message.Message):
    __slots__ = ("order_id",)
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    def __init__(self, order_id: _Optional[str] = ...) -> None: ...

class GetOrdersRequest(_message.Message):
    __slots__ = ("symbol", "statuses", "start_time", "end_time", "limit")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    STATUSES_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    statuses: _containers.RepeatedScalarFieldContainer[_market_pb2.OrderStatus]
    start_time: _types_pb2.Timestamp
    end_time: _types_pb2.Timestamp
    limit: int
    def __init__(self, symbol: _Optional[str] = ..., statuses: _Optional[_Iterable[_Union[_market_pb2.OrderStatus, str]]] = ..., start_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., limit: _Optional[int] = ...) -> None: ...

class GetOrdersResponse(_message.Message):
    __slots__ = ("orders", "error")
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    orders: _containers.RepeatedCompositeFieldContainer[_market_pb2.Order]
    error: _types_pb2.Error
    def __init__(self, orders: _Optional[_Iterable[_Union[_market_pb2.Order, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class StreamOrdersRequest(_message.Message):
    __slots__ = ("symbol",)
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    def __init__(self, symbol: _Optional[str] = ...) -> None: ...

class GetPositionRequest(_message.Message):
    __slots__ = ("position_id", "symbol")
    POSITION_ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    position_id: str
    symbol: str
    def __init__(self, position_id: _Optional[str] = ..., symbol: _Optional[str] = ...) -> None: ...

class GetPositionsRequest(_message.Message):
    __slots__ = ("symbol", "open_only")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    OPEN_ONLY_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    open_only: bool
    def __init__(self, symbol: _Optional[str] = ..., open_only: bool = ...) -> None: ...

class GetPositionsResponse(_message.Message):
    __slots__ = ("positions", "error")
    POSITIONS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    positions: _containers.RepeatedCompositeFieldContainer[_market_pb2.Position]
    error: _types_pb2.Error
    def __init__(self, positions: _Optional[_Iterable[_Union[_market_pb2.Position, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class ClosePositionRequest(_message.Message):
    __slots__ = ("position_id", "price")
    POSITION_ID_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    position_id: str
    price: float
    def __init__(self, position_id: _Optional[str] = ..., price: _Optional[float] = ...) -> None: ...

class ClosePositionResponse(_message.Message):
    __slots__ = ("position", "close_order", "error")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    CLOSE_ORDER_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    position: _market_pb2.Position
    close_order: _market_pb2.Order
    error: _types_pb2.Error
    def __init__(self, position: _Optional[_Union[_market_pb2.Position, _Mapping]] = ..., close_order: _Optional[_Union[_market_pb2.Order, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class AssessRiskRequest(_message.Message):
    __slots__ = ("positions", "pending_orders")
    POSITIONS_FIELD_NUMBER: _ClassVar[int]
    PENDING_ORDERS_FIELD_NUMBER: _ClassVar[int]
    positions: _containers.RepeatedCompositeFieldContainer[_market_pb2.Position]
    pending_orders: _containers.RepeatedCompositeFieldContainer[_market_pb2.Order]
    def __init__(self, positions: _Optional[_Iterable[_Union[_market_pb2.Position, _Mapping]]] = ..., pending_orders: _Optional[_Iterable[_Union[_market_pb2.Order, _Mapping]]] = ...) -> None: ...

class UpdateRiskParametersRequest(_message.Message):
    __slots__ = ("parameters",)
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    parameters: _market_pb2.RiskParameters
    def __init__(self, parameters: _Optional[_Union[_market_pb2.RiskParameters, _Mapping]] = ...) -> None: ...

class UpdateRiskParametersResponse(_message.Message):
    __slots__ = ("parameters", "error")
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    parameters: _market_pb2.RiskParameters
    error: _types_pb2.Error
    def __init__(self, parameters: _Optional[_Union[_market_pb2.RiskParameters, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class StreamInnovationsRequest(_message.Message):
    __slots__ = ("statuses",)
    STATUSES_FIELD_NUMBER: _ClassVar[int]
    statuses: _containers.RepeatedScalarFieldContainer[_learning_pb2.InnovationStatus]
    def __init__(self, statuses: _Optional[_Iterable[_Union[_learning_pb2.InnovationStatus, str]]] = ...) -> None: ...

class GetPatternsRequest(_message.Message):
    __slots__ = ("category", "min_confidence", "limit")
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    MIN_CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    category: str
    min_confidence: float
    limit: int
    def __init__(self, category: _Optional[str] = ..., min_confidence: _Optional[float] = ..., limit: _Optional[int] = ...) -> None: ...

class GetPatternsResponse(_message.Message):
    __slots__ = ("patterns", "error")
    PATTERNS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    patterns: _containers.RepeatedCompositeFieldContainer[_learning_pb2.Pattern]
    error: _types_pb2.Error
    def __init__(self, patterns: _Optional[_Iterable[_Union[_learning_pb2.Pattern, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetInsightsRequest(_message.Message):
    __slots__ = ("start_time", "end_time", "min_impact", "limit")
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    MIN_IMPACT_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    start_time: _types_pb2.Timestamp
    end_time: _types_pb2.Timestamp
    min_impact: float
    limit: int
    def __init__(self, start_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., min_impact: _Optional[float] = ..., limit: _Optional[int] = ...) -> None: ...

class GetInsightsResponse(_message.Message):
    __slots__ = ("insights", "error")
    INSIGHTS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    insights: _containers.RepeatedCompositeFieldContainer[_learning_pb2.Insight]
    error: _types_pb2.Error
    def __init__(self, insights: _Optional[_Iterable[_Union[_learning_pb2.Insight, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetNeuralStateRequest(_message.Message):
    __slots__ = ("neuron_ids", "include_synapses")
    NEURON_IDS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_SYNAPSES_FIELD_NUMBER: _ClassVar[int]
    neuron_ids: _containers.RepeatedScalarFieldContainer[str]
    include_synapses: bool
    def __init__(self, neuron_ids: _Optional[_Iterable[str]] = ..., include_synapses: bool = ...) -> None: ...

class ActivateNeuronRequest(_message.Message):
    __slots__ = ("neuron_id", "concept", "activation_level")
    NEURON_ID_FIELD_NUMBER: _ClassVar[int]
    CONCEPT_FIELD_NUMBER: _ClassVar[int]
    ACTIVATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    neuron_id: str
    concept: str
    activation_level: float
    def __init__(self, neuron_id: _Optional[str] = ..., concept: _Optional[str] = ..., activation_level: _Optional[float] = ...) -> None: ...

class ActivateNeuronResponse(_message.Message):
    __slots__ = ("neuron", "coactivated_synapses", "error")
    NEURON_FIELD_NUMBER: _ClassVar[int]
    COACTIVATED_SYNAPSES_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    neuron: _learning_pb2.Neuron
    coactivated_synapses: _containers.RepeatedCompositeFieldContainer[_learning_pb2.Synapse]
    error: _types_pb2.Error
    def __init__(self, neuron: _Optional[_Union[_learning_pb2.Neuron, _Mapping]] = ..., coactivated_synapses: _Optional[_Iterable[_Union[_learning_pb2.Synapse, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class StrengthenSynapseRequest(_message.Message):
    __slots__ = ("from_neuron_id", "to_neuron_id", "strength_delta")
    FROM_NEURON_ID_FIELD_NUMBER: _ClassVar[int]
    TO_NEURON_ID_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_DELTA_FIELD_NUMBER: _ClassVar[int]
    from_neuron_id: str
    to_neuron_id: str
    strength_delta: float
    def __init__(self, from_neuron_id: _Optional[str] = ..., to_neuron_id: _Optional[str] = ..., strength_delta: _Optional[float] = ...) -> None: ...

class StrengthenSynapseResponse(_message.Message):
    __slots__ = ("synapse", "error")
    SYNAPSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    synapse: _learning_pb2.Synapse
    error: _types_pb2.Error
    def __init__(self, synapse: _Optional[_Union[_learning_pb2.Synapse, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetBeliefsRequest(_message.Message):
    __slots__ = ("min_confidence", "limit")
    MIN_CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    min_confidence: float
    limit: int
    def __init__(self, min_confidence: _Optional[float] = ..., limit: _Optional[int] = ...) -> None: ...

class GetBeliefsResponse(_message.Message):
    __slots__ = ("beliefs", "error")
    BELIEFS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    beliefs: _containers.RepeatedCompositeFieldContainer[_learning_pb2.Belief]
    error: _types_pb2.Error
    def __init__(self, beliefs: _Optional[_Iterable[_Union[_learning_pb2.Belief, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class UpdateBeliefRequest(_message.Message):
    __slots__ = ("belief_id", "confidence_delta", "new_evidence", "supports_belief")
    BELIEF_ID_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_DELTA_FIELD_NUMBER: _ClassVar[int]
    NEW_EVIDENCE_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_BELIEF_FIELD_NUMBER: _ClassVar[int]
    belief_id: str
    confidence_delta: float
    new_evidence: str
    supports_belief: bool
    def __init__(self, belief_id: _Optional[str] = ..., confidence_delta: _Optional[float] = ..., new_evidence: _Optional[str] = ..., supports_belief: bool = ...) -> None: ...

class UpdateBeliefResponse(_message.Message):
    __slots__ = ("belief", "error")
    BELIEF_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    belief: _learning_pb2.Belief
    error: _types_pb2.Error
    def __init__(self, belief: _Optional[_Union[_learning_pb2.Belief, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetContradictionsRequest(_message.Message):
    __slots__ = ("resolved_only", "min_severity")
    RESOLVED_ONLY_FIELD_NUMBER: _ClassVar[int]
    MIN_SEVERITY_FIELD_NUMBER: _ClassVar[int]
    resolved_only: bool
    min_severity: float
    def __init__(self, resolved_only: bool = ..., min_severity: _Optional[float] = ...) -> None: ...

class GetContradictionsResponse(_message.Message):
    __slots__ = ("contradictions", "error")
    CONTRADICTIONS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    contradictions: _containers.RepeatedCompositeFieldContainer[_learning_pb2.Contradiction]
    error: _types_pb2.Error
    def __init__(self, contradictions: _Optional[_Iterable[_Union[_learning_pb2.Contradiction, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class RecordFailureRequest(_message.Message):
    __slots__ = ("failure", "create_scar_tissue")
    FAILURE_FIELD_NUMBER: _ClassVar[int]
    CREATE_SCAR_TISSUE_FIELD_NUMBER: _ClassVar[int]
    failure: _learning_pb2.Failure
    create_scar_tissue: bool
    def __init__(self, failure: _Optional[_Union[_learning_pb2.Failure, _Mapping]] = ..., create_scar_tissue: bool = ...) -> None: ...

class RecordFailureResponse(_message.Message):
    __slots__ = ("failure_id", "scar_tissue", "error")
    FAILURE_ID_FIELD_NUMBER: _ClassVar[int]
    SCAR_TISSUE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    failure_id: str
    scar_tissue: _learning_pb2.ScarTissue
    error: _types_pb2.Error
    def __init__(self, failure_id: _Optional[str] = ..., scar_tissue: _Optional[_Union[_learning_pb2.ScarTissue, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetScarTissueRequest(_message.Message):
    __slots__ = ("failure_category", "limit")
    FAILURE_CATEGORY_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    failure_category: str
    limit: int
    def __init__(self, failure_category: _Optional[str] = ..., limit: _Optional[int] = ...) -> None: ...

class GetScarTissueResponse(_message.Message):
    __slots__ = ("scar_tissues", "error")
    SCAR_TISSUES_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    scar_tissues: _containers.RepeatedCompositeFieldContainer[_learning_pb2.ScarTissue]
    error: _types_pb2.Error
    def __init__(self, scar_tissues: _Optional[_Iterable[_Union[_learning_pb2.ScarTissue, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetTriggersRequest(_message.Message):
    __slots__ = ("types", "fired_only")
    TYPES_FIELD_NUMBER: _ClassVar[int]
    FIRED_ONLY_FIELD_NUMBER: _ClassVar[int]
    types: _containers.RepeatedScalarFieldContainer[_learning_pb2.TriggerType]
    fired_only: bool
    def __init__(self, types: _Optional[_Iterable[_Union[_learning_pb2.TriggerType, str]]] = ..., fired_only: bool = ...) -> None: ...

class GetTriggersResponse(_message.Message):
    __slots__ = ("triggers", "error")
    TRIGGERS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    triggers: _containers.RepeatedCompositeFieldContainer[_learning_pb2.EvolutionTrigger]
    error: _types_pb2.Error
    def __init__(self, triggers: _Optional[_Iterable[_Union[_learning_pb2.EvolutionTrigger, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class FireTriggerRequest(_message.Message):
    __slots__ = ("trigger_id", "context")
    class ContextEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TRIGGER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    trigger_id: str
    context: _containers.ScalarMap[str, str]
    def __init__(self, trigger_id: _Optional[str] = ..., context: _Optional[_Mapping[str, str]] = ...) -> None: ...

class FireTriggerResponse(_message.Message):
    __slots__ = ("event", "error")
    EVENT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    event: _learning_pb2.TriggerEvent
    error: _types_pb2.Error
    def __init__(self, event: _Optional[_Union[_learning_pb2.TriggerEvent, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ("component",)
    COMPONENT_FIELD_NUMBER: _ClassVar[int]
    component: str
    def __init__(self, component: _Optional[str] = ...) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _types_pb2.HealthStatus
    def __init__(self, status: _Optional[_Union[_types_pb2.HealthStatus, _Mapping]] = ...) -> None: ...

class StreamHealthRequest(_message.Message):
    __slots__ = ("components", "interval_seconds")
    COMPONENTS_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    components: _containers.RepeatedScalarFieldContainer[str]
    interval_seconds: int
    def __init__(self, components: _Optional[_Iterable[str]] = ..., interval_seconds: _Optional[int] = ...) -> None: ...

class GetMetricsRequest(_message.Message):
    __slots__ = ("metric_names", "start_time", "end_time")
    METRIC_NAMES_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    metric_names: _containers.RepeatedScalarFieldContainer[str]
    start_time: _types_pb2.Timestamp
    end_time: _types_pb2.Timestamp
    def __init__(self, metric_names: _Optional[_Iterable[str]] = ..., start_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetMetricsResponse(_message.Message):
    __slots__ = ("metrics", "error")
    METRICS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    metrics: _containers.RepeatedCompositeFieldContainer[Metric]
    error: _types_pb2.Error
    def __init__(self, metrics: _Optional[_Iterable[_Union[Metric, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class StreamMetricsRequest(_message.Message):
    __slots__ = ("metric_names", "interval_seconds")
    METRIC_NAMES_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    metric_names: _containers.RepeatedScalarFieldContainer[str]
    interval_seconds: int
    def __init__(self, metric_names: _Optional[_Iterable[str]] = ..., interval_seconds: _Optional[int] = ...) -> None: ...

class Metric(_message.Message):
    __slots__ = ("name", "value", "unit", "timestamp", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    value: float
    unit: str
    timestamp: _types_pb2.Timestamp
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., value: _Optional[float] = ..., unit: _Optional[str] = ..., timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class StartRequest(_message.Message):
    __slots__ = ("component", "config")
    class ConfigEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    COMPONENT_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    component: str
    config: _containers.ScalarMap[str, str]
    def __init__(self, component: _Optional[str] = ..., config: _Optional[_Mapping[str, str]] = ...) -> None: ...

class StartResponse(_message.Message):
    __slots__ = ("status", "message", "error")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    status: _types_pb2.Status
    message: str
    error: _types_pb2.Error
    def __init__(self, status: _Optional[_Union[_types_pb2.Status, str]] = ..., message: _Optional[str] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class StopRequest(_message.Message):
    __slots__ = ("component", "graceful", "timeout_seconds")
    COMPONENT_FIELD_NUMBER: _ClassVar[int]
    GRACEFUL_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    component: str
    graceful: bool
    timeout_seconds: int
    def __init__(self, component: _Optional[str] = ..., graceful: bool = ..., timeout_seconds: _Optional[int] = ...) -> None: ...

class StopResponse(_message.Message):
    __slots__ = ("status", "message", "error")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    status: _types_pb2.Status
    message: str
    error: _types_pb2.Error
    def __init__(self, status: _Optional[_Union[_types_pb2.Status, str]] = ..., message: _Optional[str] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class RestartRequest(_message.Message):
    __slots__ = ("component", "graceful", "new_config")
    class NewConfigEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    COMPONENT_FIELD_NUMBER: _ClassVar[int]
    GRACEFUL_FIELD_NUMBER: _ClassVar[int]
    NEW_CONFIG_FIELD_NUMBER: _ClassVar[int]
    component: str
    graceful: bool
    new_config: _containers.ScalarMap[str, str]
    def __init__(self, component: _Optional[str] = ..., graceful: bool = ..., new_config: _Optional[_Mapping[str, str]] = ...) -> None: ...

class RestartResponse(_message.Message):
    __slots__ = ("status", "message", "error")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    status: _types_pb2.Status
    message: str
    error: _types_pb2.Error
    def __init__(self, status: _Optional[_Union[_types_pb2.Status, str]] = ..., message: _Optional[str] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetStatusRequest(_message.Message):
    __slots__ = ("components",)
    COMPONENTS_FIELD_NUMBER: _ClassVar[int]
    components: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, components: _Optional[_Iterable[str]] = ...) -> None: ...

class GetStatusResponse(_message.Message):
    __slots__ = ("statuses", "error")
    class ComponentStatus(_message.Message):
        __slots__ = ("component", "state", "started_at", "uptime_seconds", "info")
        class InfoEntry(_message.Message):
            __slots__ = ("key", "value")
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        COMPONENT_FIELD_NUMBER: _ClassVar[int]
        STATE_FIELD_NUMBER: _ClassVar[int]
        STARTED_AT_FIELD_NUMBER: _ClassVar[int]
        UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
        INFO_FIELD_NUMBER: _ClassVar[int]
        component: str
        state: str
        started_at: _types_pb2.Timestamp
        uptime_seconds: int
        info: _containers.ScalarMap[str, str]
        def __init__(self, component: _Optional[str] = ..., state: _Optional[str] = ..., started_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., uptime_seconds: _Optional[int] = ..., info: _Optional[_Mapping[str, str]] = ...) -> None: ...
    STATUSES_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    statuses: _containers.RepeatedCompositeFieldContainer[GetStatusResponse.ComponentStatus]
    error: _types_pb2.Error
    def __init__(self, statuses: _Optional[_Iterable[_Union[GetStatusResponse.ComponentStatus, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...
