import time
from collections import defaultdict
from typing import Dict, Any

class MetricsAggregator:
    def __init__(self):
        self.metrics = defaultdict(list)
    
    def record(self, metric_name: str, value: Any) -> None:
        """Record a new metric value."""
        self.metrics[metric_name].append(value)
    
    def get_average(self, metric_name: str) -> float:
        """Get the average value of a metric."""
        values = self.metrics.get(metric_name, [])
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def get_latest(self, metric_name: str) -> Any:
        """Get the latest recorded value of a metric."""
        values = self.metrics.get(metric_name, [])
        if not values:
            return None
        return values[-1]
    
    def clear(self, metric_name: str = None) -> None:
        """Clear all recorded metrics or a specific one."""
        if metric_name:
            del self.metrics[metric_name]
        else:
            self.metrics.clear()
    
    def report(self) -> Dict[str, Any]:
        """Generate a report of all metrics."""
        report = {}
        for metric, values in self.metrics.items():
            report[metric] = {
                'latest': self.get_latest(metric),
                'average': self.get_average(metric),
                'count': len(values)
            }
        return report
    
    def monitor_performance(self, func, *args, **kwargs):
        """Monitor the performance of a function call."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        self.record(f'{func.__name__}_time', end_time - start_time)
        return result

# Example Usage
if __name__ == "__main__":
    aggregator = MetricsAggregator()
    
    def example_function(x):
        time.sleep(0.1)
        return x * x
    
    for i in range(10):
        aggregator.monitor_performance(example_function, i)
    
    print(aggregator.report())