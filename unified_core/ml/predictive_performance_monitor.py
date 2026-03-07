"""
Predictive Performance Monitor - Proactive Resource Management
Version: 1.0.0

Uses time series prediction to forecast resource issues before they happen.
Integrates with PerformanceTrigger for proactive interventions.
"""

import logging
import time
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

logger = logging.getLogger("unified_core.ml.predictive_monitor")


@dataclass
class PredictiveAlert:
    """Alert for predicted resource issue."""
    alert_type: str  # cpu_spike, memory_spike, gpu_spike
    severity: str  # low, medium, high, critical
    predicted_time: float  # when the issue will occur (timestamp)
    predicted_value: float  # predicted metric value
    threshold: float  # threshold that will be exceeded
    confidence: float  # prediction confidence (0-1)
    time_to_issue: float  # seconds until issue
    recommendations: List[str]


class PredictivePerformanceMonitor:
    """
    Monitors system metrics and predicts future resource issues.

    Integrates with:
    - MetricsCollector: Gets historical data
    - TimeSeriesPredictor: Makes predictions
    - PerformanceTrigger: Triggers proactive actions
    """

    # Thresholds for alerts
    THRESHOLDS = {
        'cpu_percent': {'high': 85, 'critical': 95},
        'memory_percent': {'high': 85, 'critical': 95},
        'disk_percent': {'high': 90, 'critical': 95},
        'gpu_percent': {'high': 90, 'critical': 95},
        'gpu_temp': {'high': 80, 'critical': 90}
    }

    def __init__(self):
        self._predictor = None
        self._collector = None
        self._last_prediction_time = 0
        self._prediction_interval = 300  # Predict every 5 minutes
        self._alerts: List[PredictiveAlert] = []

        logger.info("PredictivePerformanceMonitor initialized")

    def _load_components(self):
        """Lazy load components."""
        if self._predictor is None:
            try:
                from .time_series_predictor import get_time_series_predictor
                self._predictor = get_time_series_predictor()

                # Try to load existing model
                try:
                    self._predictor.load_model("final_model.pt")
                    logger.info("✅ Loaded trained prediction model")
                except FileNotFoundError:
                    logger.warning("⚠️  No trained model found - predictions disabled")
                    logger.warning("   Run: python scripts/train_time_series_predictor.py")
                    self._predictor = None
            except Exception as e:
                logger.error(f"Failed to load predictor: {e}")
                self._predictor = None

        if self._collector is None:
            try:
                from .metrics_collector import get_metrics_collector
                self._collector = get_metrics_collector()
            except Exception as e:
                logger.error(f"Failed to load collector: {e}")

    def predict_future_metrics(self) -> Optional[Dict[str, List[float]]]:
        """
        Predict future metrics using trained model.

        Returns:
            Dictionary of predictions or None if prediction fails
        """
        self._load_components()

        if self._predictor is None or self._collector is None:
            return None

        try:
            # Get recent metrics
            from .time_series_predictor import MetricsData
            system_metrics = self._collector.get_recent_metrics(hours=1, limit=60)

            if len(system_metrics) < 60:
                logger.debug("Not enough recent data for prediction")
                return None

            # Convert to MetricsData
            metrics_data = [
                MetricsData(
                    timestamp=m.timestamp,
                    cpu_percent=m.cpu_percent,
                    memory_percent=m.memory_percent,
                    disk_percent=m.disk_percent,
                    gpu_percent=m.gpu_percent,
                    gpu_temp=m.gpu_temp
                )
                for m in system_metrics
            ]

            # Predict
            predictions = self._predictor.predict(metrics_data)
            logger.debug("Successfully predicted future metrics")

            return predictions

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None

    def analyze_predictions(self, predictions: Dict[str, List[float]]) -> List[PredictiveAlert]:
        """
        Analyze predictions and generate alerts.

        Args:
            predictions: Predicted metrics

        Returns:
            List of alerts
        """
        alerts = []
        current_time = time.time()

        for feature, values in predictions.items():
            if feature not in self.THRESHOLDS:
                continue

            thresholds = self.THRESHOLDS[feature]

            # Check each predicted time step
            for step_idx, predicted_value in enumerate(values):
                # Time until this prediction (assuming 10s intervals)
                time_to_issue = (step_idx + 1) * 10

                # Check against thresholds
                severity = None
                threshold = None

                if predicted_value >= thresholds['critical']:
                    severity = 'critical'
                    threshold = thresholds['critical']
                elif predicted_value >= thresholds['high']:
                    severity = 'high'
                    threshold = thresholds['high']

                if severity:
                    # Determine alert type
                    alert_type = feature.replace('_percent', '_spike')

                    # Generate recommendations
                    recommendations = self._generate_recommendations(
                        feature, predicted_value, severity
                    )

                    alert = PredictiveAlert(
                        alert_type=alert_type,
                        severity=severity,
                        predicted_time=current_time + time_to_issue,
                        predicted_value=predicted_value,
                        threshold=threshold,
                        confidence=0.85,  # TODO: Calculate from model uncertainty
                        time_to_issue=time_to_issue,
                        recommendations=recommendations
                    )

                    alerts.append(alert)
                    logger.warning(
                        f"🔮 Predicted {alert_type} in {time_to_issue}s: "
                        f"{predicted_value:.1f}% (threshold: {threshold}%)"
                    )

                    # Only report first occurrence per metric
                    break

        return alerts

    def _generate_recommendations(self, feature: str, value: float, severity: str) -> List[str]:
        """Generate recommendations based on predicted issue."""
        recommendations = []

        if feature == 'cpu_percent':
            recommendations = [
                "Consider reducing background processes",
                "Check for CPU-intensive operations",
                "Scale resources if running in cloud"
            ]
        elif feature == 'memory_percent':
            recommendations = [
                "Clear memory caches",
                "Restart memory-intensive services",
                "Check for memory leaks"
            ]
        elif feature == 'gpu_percent':
            recommendations = [
                "Reduce GPU workload",
                "Check for stuck GPU processes",
                "Consider deferring non-critical GPU tasks"
            ]
        elif feature == 'gpu_temp':
            recommendations = [
                "Improve cooling/ventilation",
                "Reduce GPU workload immediately",
                "Check for dust buildup"
            ]

        if severity == 'critical':
            recommendations.insert(0, "⚠️  IMMEDIATE ACTION REQUIRED")

        return recommendations

    def check_and_alert(self) -> List[PredictiveAlert]:
        """
        Main check function - called periodically by agent_daemon.

        Returns:
            List of alerts (empty if no issues predicted)
        """
        # Rate limit predictions
        if time.time() - self._last_prediction_time < self._prediction_interval:
            return []

        self._last_prediction_time = time.time()

        # Predict
        predictions = self.predict_future_metrics()
        if predictions is None:
            return []

        # Analyze
        alerts = self.analyze_predictions(predictions)
        self._alerts = alerts

        if alerts:
            logger.warning(f"🔮 {len(alerts)} predictive alerts generated")

        return alerts

    def get_recent_alerts(self) -> List[PredictiveAlert]:
        """Get recent alerts."""
        return self._alerts

    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        return {
            "predictor_available": self._predictor is not None,
            "collector_available": self._collector is not None,
            "recent_alerts": len(self._alerts),
            "last_prediction_time": self._last_prediction_time,
            "prediction_interval": self._prediction_interval
        }


# Singleton instance
_monitor_instance: Optional[PredictivePerformanceMonitor] = None

def get_predictive_monitor() -> PredictivePerformanceMonitor:
    """Get singleton PredictivePerformanceMonitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PredictivePerformanceMonitor()
    return _monitor_instance
