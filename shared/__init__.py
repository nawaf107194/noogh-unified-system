"""
shared — Curated utility library for the NOOGH Unified System.

Exposes best-of-breed modules from the Innovation Engine for easy import:
    from shared import EventBus, DataSanitizer, PerformanceProfiler
"""

# Core utilities
from shared.event_bus import EventBus
from shared.error_handler import ErrorHandler
from shared.dependency_injection import DependencyInjector

# Data processing
from shared.data_sanitizer import DataSanitizer
from shared.data_validation_framework import DataValidationFramework
from shared.data_normalization import DataNormalizer

# Observability
from shared.performance_profiler import PerformanceProfiler
from shared.metrics_aggregator import MetricsAggregator
from shared.event_logger import EventLogger

# Feature management
from shared.feature_flag_manager import FeatureFlagManager

# Scheduling & caching
from shared.async_task_scheduler import AsyncTaskScheduler
from shared.cache_utility import CacheUtility

__all__ = [
    "EventBus",
    "ErrorHandler",
    "DependencyInjector",
    "DataSanitizer",
    "DataValidationFramework",
    "DataNormalizer",
    "PerformanceProfiler",
    "MetricsAggregator",
    "EventLogger",
    "FeatureFlagManager",
    "AsyncTaskScheduler",
    "CacheUtility",
]
