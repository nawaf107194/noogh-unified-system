from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATUS_UNSPECIFIED: _ClassVar[Status]
    STATUS_SUCCESS: _ClassVar[Status]
    STATUS_PENDING: _ClassVar[Status]
    STATUS_FAILED: _ClassVar[Status]
    STATUS_CANCELLED: _ClassVar[Status]
STATUS_UNSPECIFIED: Status
STATUS_SUCCESS: Status
STATUS_PENDING: Status
STATUS_FAILED: Status
STATUS_CANCELLED: Status

class Timestamp(_message.Message):
    __slots__ = ("seconds", "nanos")
    SECONDS_FIELD_NUMBER: _ClassVar[int]
    NANOS_FIELD_NUMBER: _ClassVar[int]
    seconds: int
    nanos: int
    def __init__(self, seconds: _Optional[int] = ..., nanos: _Optional[int] = ...) -> None: ...

class Metadata(_message.Message):
    __slots__ = ("id", "created_at", "updated_at", "created_by", "version", "tags")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    created_at: Timestamp
    updated_at: Timestamp
    created_by: str
    version: str
    tags: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., created_at: _Optional[_Union[Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[Timestamp, _Mapping]] = ..., created_by: _Optional[str] = ..., version: _Optional[str] = ..., tags: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Confidence(_message.Message):
    __slots__ = ("value", "reasoning", "factors")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    FACTORS_FIELD_NUMBER: _ClassVar[int]
    value: float
    reasoning: str
    factors: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, value: _Optional[float] = ..., reasoning: _Optional[str] = ..., factors: _Optional[_Iterable[str]] = ...) -> None: ...

class KeyValue(_message.Message):
    __slots__ = ("key", "string_value", "int_value", "double_value", "bool_value", "bytes_value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    BYTES_VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    string_value: str
    int_value: int
    double_value: float
    bool_value: bool
    bytes_value: bytes
    def __init__(self, key: _Optional[str] = ..., string_value: _Optional[str] = ..., int_value: _Optional[int] = ..., double_value: _Optional[float] = ..., bool_value: bool = ..., bytes_value: _Optional[bytes] = ...) -> None: ...

class Error(_message.Message):
    __slots__ = ("code", "message", "details", "stack_trace", "occurred_at")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    STACK_TRACE_FIELD_NUMBER: _ClassVar[int]
    OCCURRED_AT_FIELD_NUMBER: _ClassVar[int]
    code: str
    message: str
    details: str
    stack_trace: _containers.RepeatedScalarFieldContainer[str]
    occurred_at: Timestamp
    def __init__(self, code: _Optional[str] = ..., message: _Optional[str] = ..., details: _Optional[str] = ..., stack_trace: _Optional[_Iterable[str]] = ..., occurred_at: _Optional[_Union[Timestamp, _Mapping]] = ...) -> None: ...

class HealthStatus(_message.Message):
    __slots__ = ("state", "component", "message", "metrics", "checked_at")
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATE_UNKNOWN: _ClassVar[HealthStatus.State]
        STATE_HEALTHY: _ClassVar[HealthStatus.State]
        STATE_DEGRADED: _ClassVar[HealthStatus.State]
        STATE_UNHEALTHY: _ClassVar[HealthStatus.State]
    STATE_UNKNOWN: HealthStatus.State
    STATE_HEALTHY: HealthStatus.State
    STATE_DEGRADED: HealthStatus.State
    STATE_UNHEALTHY: HealthStatus.State
    class MetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    STATE_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    CHECKED_AT_FIELD_NUMBER: _ClassVar[int]
    state: HealthStatus.State
    component: str
    message: str
    metrics: _containers.ScalarMap[str, str]
    checked_at: Timestamp
    def __init__(self, state: _Optional[_Union[HealthStatus.State, str]] = ..., component: _Optional[str] = ..., message: _Optional[str] = ..., metrics: _Optional[_Mapping[str, str]] = ..., checked_at: _Optional[_Union[Timestamp, _Mapping]] = ...) -> None: ...
