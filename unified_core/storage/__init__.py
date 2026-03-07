"""
High-performance storage layer for NOOGH
Uses Protocol Buffers for 6x faster, 3x smaller storage
"""

from .protobuf_storage import (
    ProtobufInnovationStorage,
    get_innovation_storage
)

__all__ = [
    'ProtobufInnovationStorage',
    'get_innovation_storage'
]
