from proto_generated.common import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Side(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SIDE_UNSPECIFIED: _ClassVar[Side]
    SIDE_BUY: _ClassVar[Side]
    SIDE_SELL: _ClassVar[Side]

class SignalType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SIGNAL_TYPE_UNSPECIFIED: _ClassVar[SignalType]
    SIGNAL_TYPE_ENTRY_LONG: _ClassVar[SignalType]
    SIGNAL_TYPE_ENTRY_SHORT: _ClassVar[SignalType]
    SIGNAL_TYPE_EXIT: _ClassVar[SignalType]
    SIGNAL_TYPE_TAKE_PROFIT: _ClassVar[SignalType]
    SIGNAL_TYPE_STOP_LOSS: _ClassVar[SignalType]

class SignalStrength(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SIGNAL_STRENGTH_UNSPECIFIED: _ClassVar[SignalStrength]
    SIGNAL_STRENGTH_WEAK: _ClassVar[SignalStrength]
    SIGNAL_STRENGTH_MODERATE: _ClassVar[SignalStrength]
    SIGNAL_STRENGTH_STRONG: _ClassVar[SignalStrength]
    SIGNAL_STRENGTH_VERY_STRONG: _ClassVar[SignalStrength]

class OrderType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ORDER_TYPE_UNSPECIFIED: _ClassVar[OrderType]
    ORDER_TYPE_MARKET: _ClassVar[OrderType]
    ORDER_TYPE_LIMIT: _ClassVar[OrderType]
    ORDER_TYPE_STOP_MARKET: _ClassVar[OrderType]
    ORDER_TYPE_STOP_LIMIT: _ClassVar[OrderType]

class OrderStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ORDER_STATUS_UNSPECIFIED: _ClassVar[OrderStatus]
    ORDER_STATUS_PENDING: _ClassVar[OrderStatus]
    ORDER_STATUS_OPEN: _ClassVar[OrderStatus]
    ORDER_STATUS_PARTIALLY_FILLED: _ClassVar[OrderStatus]
    ORDER_STATUS_FILLED: _ClassVar[OrderStatus]
    ORDER_STATUS_CANCELLED: _ClassVar[OrderStatus]
    ORDER_STATUS_REJECTED: _ClassVar[OrderStatus]
    ORDER_STATUS_EXPIRED: _ClassVar[OrderStatus]
SIDE_UNSPECIFIED: Side
SIDE_BUY: Side
SIDE_SELL: Side
SIGNAL_TYPE_UNSPECIFIED: SignalType
SIGNAL_TYPE_ENTRY_LONG: SignalType
SIGNAL_TYPE_ENTRY_SHORT: SignalType
SIGNAL_TYPE_EXIT: SignalType
SIGNAL_TYPE_TAKE_PROFIT: SignalType
SIGNAL_TYPE_STOP_LOSS: SignalType
SIGNAL_STRENGTH_UNSPECIFIED: SignalStrength
SIGNAL_STRENGTH_WEAK: SignalStrength
SIGNAL_STRENGTH_MODERATE: SignalStrength
SIGNAL_STRENGTH_STRONG: SignalStrength
SIGNAL_STRENGTH_VERY_STRONG: SignalStrength
ORDER_TYPE_UNSPECIFIED: OrderType
ORDER_TYPE_MARKET: OrderType
ORDER_TYPE_LIMIT: OrderType
ORDER_TYPE_STOP_MARKET: OrderType
ORDER_TYPE_STOP_LIMIT: OrderType
ORDER_STATUS_UNSPECIFIED: OrderStatus
ORDER_STATUS_PENDING: OrderStatus
ORDER_STATUS_OPEN: OrderStatus
ORDER_STATUS_PARTIALLY_FILLED: OrderStatus
ORDER_STATUS_FILLED: OrderStatus
ORDER_STATUS_CANCELLED: OrderStatus
ORDER_STATUS_REJECTED: OrderStatus
ORDER_STATUS_EXPIRED: OrderStatus

class OHLCV(_message.Message):
    __slots__ = ("timestamp", "open", "high", "low", "close", "volume", "symbol", "timeframe")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    OPEN_FIELD_NUMBER: _ClassVar[int]
    HIGH_FIELD_NUMBER: _ClassVar[int]
    LOW_FIELD_NUMBER: _ClassVar[int]
    CLOSE_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    TIMEFRAME_FIELD_NUMBER: _ClassVar[int]
    timestamp: _types_pb2.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str
    def __init__(self, timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., open: _Optional[float] = ..., high: _Optional[float] = ..., low: _Optional[float] = ..., close: _Optional[float] = ..., volume: _Optional[float] = ..., symbol: _Optional[str] = ..., timeframe: _Optional[str] = ...) -> None: ...

class Orderbook(_message.Message):
    __slots__ = ("symbol", "bids", "asks", "timestamp", "sequence")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    BIDS_FIELD_NUMBER: _ClassVar[int]
    ASKS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    bids: _containers.RepeatedCompositeFieldContainer[OrderbookLevel]
    asks: _containers.RepeatedCompositeFieldContainer[OrderbookLevel]
    timestamp: _types_pb2.Timestamp
    sequence: int
    def __init__(self, symbol: _Optional[str] = ..., bids: _Optional[_Iterable[_Union[OrderbookLevel, _Mapping]]] = ..., asks: _Optional[_Iterable[_Union[OrderbookLevel, _Mapping]]] = ..., timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., sequence: _Optional[int] = ...) -> None: ...

class OrderbookLevel(_message.Message):
    __slots__ = ("price", "quantity", "order_count")
    PRICE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    ORDER_COUNT_FIELD_NUMBER: _ClassVar[int]
    price: float
    quantity: float
    order_count: int
    def __init__(self, price: _Optional[float] = ..., quantity: _Optional[float] = ..., order_count: _Optional[int] = ...) -> None: ...

class Trade(_message.Message):
    __slots__ = ("id", "symbol", "price", "quantity", "timestamp", "side", "is_buyer_maker")
    ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    IS_BUYER_MAKER_FIELD_NUMBER: _ClassVar[int]
    id: str
    symbol: str
    price: float
    quantity: float
    timestamp: _types_pb2.Timestamp
    side: Side
    is_buyer_maker: bool
    def __init__(self, id: _Optional[str] = ..., symbol: _Optional[str] = ..., price: _Optional[float] = ..., quantity: _Optional[float] = ..., timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., side: _Optional[_Union[Side, str]] = ..., is_buyer_maker: bool = ...) -> None: ...

class MarketSnapshot(_message.Message):
    __slots__ = ("symbol", "last_price", "bid", "ask", "bid_size", "ask_size", "volume_24h", "change_24h_percent", "timestamp")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    LAST_PRICE_FIELD_NUMBER: _ClassVar[int]
    BID_FIELD_NUMBER: _ClassVar[int]
    ASK_FIELD_NUMBER: _ClassVar[int]
    BID_SIZE_FIELD_NUMBER: _ClassVar[int]
    ASK_SIZE_FIELD_NUMBER: _ClassVar[int]
    VOLUME_24H_FIELD_NUMBER: _ClassVar[int]
    CHANGE_24H_PERCENT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    last_price: float
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    volume_24h: float
    change_24h_percent: float
    timestamp: _types_pb2.Timestamp
    def __init__(self, symbol: _Optional[str] = ..., last_price: _Optional[float] = ..., bid: _Optional[float] = ..., ask: _Optional[float] = ..., bid_size: _Optional[float] = ..., ask_size: _Optional[float] = ..., volume_24h: _Optional[float] = ..., change_24h_percent: _Optional[float] = ..., timestamp: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class TradingSignal(_message.Message):
    __slots__ = ("id", "symbol", "signal_type", "strength", "entry_price", "target_price", "stop_loss", "confidence", "indicators", "patterns", "regime", "strategy_name", "strategy_version", "generated_at", "expires_at", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    ENTRY_PRICE_FIELD_NUMBER: _ClassVar[int]
    TARGET_PRICE_FIELD_NUMBER: _ClassVar[int]
    STOP_LOSS_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    INDICATORS_FIELD_NUMBER: _ClassVar[int]
    PATTERNS_FIELD_NUMBER: _ClassVar[int]
    REGIME_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_NAME_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_VERSION_FIELD_NUMBER: _ClassVar[int]
    GENERATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    id: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    entry_price: float
    target_price: float
    stop_loss: float
    confidence: float
    indicators: _containers.RepeatedCompositeFieldContainer[Indicator]
    patterns: _containers.RepeatedCompositeFieldContainer[Pattern]
    regime: MarketRegime
    strategy_name: str
    strategy_version: str
    generated_at: _types_pb2.Timestamp
    expires_at: _types_pb2.Timestamp
    parameters: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., symbol: _Optional[str] = ..., signal_type: _Optional[_Union[SignalType, str]] = ..., strength: _Optional[_Union[SignalStrength, str]] = ..., entry_price: _Optional[float] = ..., target_price: _Optional[float] = ..., stop_loss: _Optional[float] = ..., confidence: _Optional[float] = ..., indicators: _Optional[_Iterable[_Union[Indicator, _Mapping]]] = ..., patterns: _Optional[_Iterable[_Union[Pattern, _Mapping]]] = ..., regime: _Optional[_Union[MarketRegime, _Mapping]] = ..., strategy_name: _Optional[str] = ..., strategy_version: _Optional[str] = ..., generated_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., expires_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., parameters: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Indicator(_message.Message):
    __slots__ = ("name", "value", "signal", "weight", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    name: str
    value: float
    signal: str
    weight: float
    parameters: _containers.ScalarMap[str, float]
    def __init__(self, name: _Optional[str] = ..., value: _Optional[float] = ..., signal: _Optional[str] = ..., weight: _Optional[float] = ..., parameters: _Optional[_Mapping[str, float]] = ...) -> None: ...

class Pattern(_message.Message):
    __slots__ = ("name", "confidence", "description", "key_levels")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    KEY_LEVELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    confidence: float
    description: str
    key_levels: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, name: _Optional[str] = ..., confidence: _Optional[float] = ..., description: _Optional[str] = ..., key_levels: _Optional[_Iterable[float]] = ...) -> None: ...

class MarketRegime(_message.Message):
    __slots__ = ("regime_type", "volatility", "trend_strength", "description")
    class RegimeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        REGIME_TYPE_UNSPECIFIED: _ClassVar[MarketRegime.RegimeType]
        REGIME_TYPE_TRENDING_UP: _ClassVar[MarketRegime.RegimeType]
        REGIME_TYPE_TRENDING_DOWN: _ClassVar[MarketRegime.RegimeType]
        REGIME_TYPE_RANGING: _ClassVar[MarketRegime.RegimeType]
        REGIME_TYPE_VOLATILE: _ClassVar[MarketRegime.RegimeType]
        REGIME_TYPE_QUIET: _ClassVar[MarketRegime.RegimeType]
    REGIME_TYPE_UNSPECIFIED: MarketRegime.RegimeType
    REGIME_TYPE_TRENDING_UP: MarketRegime.RegimeType
    REGIME_TYPE_TRENDING_DOWN: MarketRegime.RegimeType
    REGIME_TYPE_RANGING: MarketRegime.RegimeType
    REGIME_TYPE_VOLATILE: MarketRegime.RegimeType
    REGIME_TYPE_QUIET: MarketRegime.RegimeType
    REGIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    VOLATILITY_FIELD_NUMBER: _ClassVar[int]
    TREND_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    regime_type: MarketRegime.RegimeType
    volatility: float
    trend_strength: float
    description: str
    def __init__(self, regime_type: _Optional[_Union[MarketRegime.RegimeType, str]] = ..., volatility: _Optional[float] = ..., trend_strength: _Optional[float] = ..., description: _Optional[str] = ...) -> None: ...

class Order(_message.Message):
    __slots__ = ("id", "client_order_id", "symbol", "side", "order_type", "status", "quantity", "filled_quantity", "price", "stop_price", "average_fill_price", "created_at", "updated_at", "filled_at", "signal_id", "position_id", "fee", "fee_currency")
    ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    ORDER_TYPE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    FILLED_QUANTITY_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    STOP_PRICE_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_FILL_PRICE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    FILLED_AT_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_ID_FIELD_NUMBER: _ClassVar[int]
    POSITION_ID_FIELD_NUMBER: _ClassVar[int]
    FEE_FIELD_NUMBER: _ClassVar[int]
    FEE_CURRENCY_FIELD_NUMBER: _ClassVar[int]
    id: str
    client_order_id: str
    symbol: str
    side: Side
    order_type: OrderType
    status: OrderStatus
    quantity: float
    filled_quantity: float
    price: float
    stop_price: float
    average_fill_price: float
    created_at: _types_pb2.Timestamp
    updated_at: _types_pb2.Timestamp
    filled_at: _types_pb2.Timestamp
    signal_id: str
    position_id: str
    fee: float
    fee_currency: str
    def __init__(self, id: _Optional[str] = ..., client_order_id: _Optional[str] = ..., symbol: _Optional[str] = ..., side: _Optional[_Union[Side, str]] = ..., order_type: _Optional[_Union[OrderType, str]] = ..., status: _Optional[_Union[OrderStatus, str]] = ..., quantity: _Optional[float] = ..., filled_quantity: _Optional[float] = ..., price: _Optional[float] = ..., stop_price: _Optional[float] = ..., average_fill_price: _Optional[float] = ..., created_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., filled_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., signal_id: _Optional[str] = ..., position_id: _Optional[str] = ..., fee: _Optional[float] = ..., fee_currency: _Optional[str] = ...) -> None: ...

class Position(_message.Message):
    __slots__ = ("id", "symbol", "side", "quantity", "entry_price", "current_price", "unrealized_pnl", "realized_pnl", "margin_used", "liquidation_price", "opened_at", "updated_at", "closed_at", "order_ids")
    ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    ENTRY_PRICE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PRICE_FIELD_NUMBER: _ClassVar[int]
    UNREALIZED_PNL_FIELD_NUMBER: _ClassVar[int]
    REALIZED_PNL_FIELD_NUMBER: _ClassVar[int]
    MARGIN_USED_FIELD_NUMBER: _ClassVar[int]
    LIQUIDATION_PRICE_FIELD_NUMBER: _ClassVar[int]
    OPENED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    CLOSED_AT_FIELD_NUMBER: _ClassVar[int]
    ORDER_IDS_FIELD_NUMBER: _ClassVar[int]
    id: str
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin_used: float
    liquidation_price: float
    opened_at: _types_pb2.Timestamp
    updated_at: _types_pb2.Timestamp
    closed_at: _types_pb2.Timestamp
    order_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., symbol: _Optional[str] = ..., side: _Optional[_Union[Side, str]] = ..., quantity: _Optional[float] = ..., entry_price: _Optional[float] = ..., current_price: _Optional[float] = ..., unrealized_pnl: _Optional[float] = ..., realized_pnl: _Optional[float] = ..., margin_used: _Optional[float] = ..., liquidation_price: _Optional[float] = ..., opened_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., closed_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., order_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class PerformanceMetrics(_message.Message):
    __slots__ = ("total_trades", "winning_trades", "losing_trades", "win_rate", "total_pnl", "total_pnl_percent", "average_win", "average_loss", "profit_factor", "max_drawdown", "max_drawdown_percent", "sharpe_ratio", "sortino_ratio", "period_start", "period_end", "by_symbol")
    class BySymbolEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: SymbolMetrics
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[SymbolMetrics, _Mapping]] = ...) -> None: ...
    TOTAL_TRADES_FIELD_NUMBER: _ClassVar[int]
    WINNING_TRADES_FIELD_NUMBER: _ClassVar[int]
    LOSING_TRADES_FIELD_NUMBER: _ClassVar[int]
    WIN_RATE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PNL_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PNL_PERCENT_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_WIN_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_LOSS_FIELD_NUMBER: _ClassVar[int]
    PROFIT_FACTOR_FIELD_NUMBER: _ClassVar[int]
    MAX_DRAWDOWN_FIELD_NUMBER: _ClassVar[int]
    MAX_DRAWDOWN_PERCENT_FIELD_NUMBER: _ClassVar[int]
    SHARPE_RATIO_FIELD_NUMBER: _ClassVar[int]
    SORTINO_RATIO_FIELD_NUMBER: _ClassVar[int]
    PERIOD_START_FIELD_NUMBER: _ClassVar[int]
    PERIOD_END_FIELD_NUMBER: _ClassVar[int]
    BY_SYMBOL_FIELD_NUMBER: _ClassVar[int]
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_percent: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    sortino_ratio: float
    period_start: _types_pb2.Timestamp
    period_end: _types_pb2.Timestamp
    by_symbol: _containers.MessageMap[str, SymbolMetrics]
    def __init__(self, total_trades: _Optional[int] = ..., winning_trades: _Optional[int] = ..., losing_trades: _Optional[int] = ..., win_rate: _Optional[float] = ..., total_pnl: _Optional[float] = ..., total_pnl_percent: _Optional[float] = ..., average_win: _Optional[float] = ..., average_loss: _Optional[float] = ..., profit_factor: _Optional[float] = ..., max_drawdown: _Optional[float] = ..., max_drawdown_percent: _Optional[float] = ..., sharpe_ratio: _Optional[float] = ..., sortino_ratio: _Optional[float] = ..., period_start: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., period_end: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., by_symbol: _Optional[_Mapping[str, SymbolMetrics]] = ...) -> None: ...

class SymbolMetrics(_message.Message):
    __slots__ = ("symbol", "trades", "win_rate", "total_pnl", "profit_factor")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    TRADES_FIELD_NUMBER: _ClassVar[int]
    WIN_RATE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PNL_FIELD_NUMBER: _ClassVar[int]
    PROFIT_FACTOR_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    trades: int
    win_rate: float
    total_pnl: float
    profit_factor: float
    def __init__(self, symbol: _Optional[str] = ..., trades: _Optional[int] = ..., win_rate: _Optional[float] = ..., total_pnl: _Optional[float] = ..., profit_factor: _Optional[float] = ...) -> None: ...

class RiskParameters(_message.Message):
    __slots__ = ("max_position_size", "max_drawdown_threshold", "max_leverage", "max_daily_loss", "max_open_positions", "max_per_symbol")
    class MaxPerSymbolEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    MAX_POSITION_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_DRAWDOWN_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    MAX_LEVERAGE_FIELD_NUMBER: _ClassVar[int]
    MAX_DAILY_LOSS_FIELD_NUMBER: _ClassVar[int]
    MAX_OPEN_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    MAX_PER_SYMBOL_FIELD_NUMBER: _ClassVar[int]
    max_position_size: float
    max_drawdown_threshold: float
    max_leverage: float
    max_daily_loss: float
    max_open_positions: float
    max_per_symbol: _containers.ScalarMap[str, float]
    def __init__(self, max_position_size: _Optional[float] = ..., max_drawdown_threshold: _Optional[float] = ..., max_leverage: _Optional[float] = ..., max_daily_loss: _Optional[float] = ..., max_open_positions: _Optional[float] = ..., max_per_symbol: _Optional[_Mapping[str, float]] = ...) -> None: ...

class RiskAssessment(_message.Message):
    __slots__ = ("can_trade", "warnings", "violations", "current_drawdown", "daily_loss", "open_positions", "margin_utilization", "assessed_at")
    CAN_TRADE_FIELD_NUMBER: _ClassVar[int]
    WARNINGS_FIELD_NUMBER: _ClassVar[int]
    VIOLATIONS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_DRAWDOWN_FIELD_NUMBER: _ClassVar[int]
    DAILY_LOSS_FIELD_NUMBER: _ClassVar[int]
    OPEN_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    MARGIN_UTILIZATION_FIELD_NUMBER: _ClassVar[int]
    ASSESSED_AT_FIELD_NUMBER: _ClassVar[int]
    can_trade: bool
    warnings: _containers.RepeatedScalarFieldContainer[str]
    violations: _containers.RepeatedScalarFieldContainer[str]
    current_drawdown: float
    daily_loss: float
    open_positions: int
    margin_utilization: float
    assessed_at: _types_pb2.Timestamp
    def __init__(self, can_trade: bool = ..., warnings: _Optional[_Iterable[str]] = ..., violations: _Optional[_Iterable[str]] = ..., current_drawdown: _Optional[float] = ..., daily_loss: _Optional[float] = ..., open_positions: _Optional[int] = ..., margin_utilization: _Optional[float] = ..., assessed_at: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetMarketDataRequest(_message.Message):
    __slots__ = ("symbol", "timeframe", "start_time", "end_time", "limit")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    TIMEFRAME_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    timeframe: str
    start_time: _types_pb2.Timestamp
    end_time: _types_pb2.Timestamp
    limit: int
    def __init__(self, symbol: _Optional[str] = ..., timeframe: _Optional[str] = ..., start_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., limit: _Optional[int] = ...) -> None: ...

class GetMarketDataResponse(_message.Message):
    __slots__ = ("candles", "error")
    CANDLES_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    candles: _containers.RepeatedCompositeFieldContainer[OHLCV]
    error: _types_pb2.Error
    def __init__(self, candles: _Optional[_Iterable[_Union[OHLCV, _Mapping]]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class SubmitOrderRequest(_message.Message):
    __slots__ = ("symbol", "side", "order_type", "quantity", "price", "stop_price", "signal_id", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    ORDER_TYPE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    STOP_PRICE_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    side: Side
    order_type: OrderType
    quantity: float
    price: float
    stop_price: float
    signal_id: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, symbol: _Optional[str] = ..., side: _Optional[_Union[Side, str]] = ..., order_type: _Optional[_Union[OrderType, str]] = ..., quantity: _Optional[float] = ..., price: _Optional[float] = ..., stop_price: _Optional[float] = ..., signal_id: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class SubmitOrderResponse(_message.Message):
    __slots__ = ("order", "error")
    ORDER_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    order: Order
    error: _types_pb2.Error
    def __init__(self, order: _Optional[_Union[Order, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...

class GetPerformanceRequest(_message.Message):
    __slots__ = ("start_time", "end_time", "strategy_name", "symbol")
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_NAME_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    start_time: _types_pb2.Timestamp
    end_time: _types_pb2.Timestamp
    strategy_name: str
    symbol: str
    def __init__(self, start_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_types_pb2.Timestamp, _Mapping]] = ..., strategy_name: _Optional[str] = ..., symbol: _Optional[str] = ...) -> None: ...

class GetPerformanceResponse(_message.Message):
    __slots__ = ("metrics", "error")
    METRICS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    metrics: PerformanceMetrics
    error: _types_pb2.Error
    def __init__(self, metrics: _Optional[_Union[PerformanceMetrics, _Mapping]] = ..., error: _Optional[_Union[_types_pb2.Error, _Mapping]] = ...) -> None: ...
