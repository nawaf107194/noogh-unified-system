"""
Self-Awareness Tracker - Track energy levels and optimize productivity.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class EnergyLevel:
    """Energy level at a specific time"""

    def __init__(self, hour: int, level: int, notes: str = ""):
        self.hour = hour
        self.level = level  # 1-10
        self.notes = notes
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"EnergyLevel(hour={self.hour}, level={self.level})"


class SelfAwarenessTracker:
    """
    Track energy levels and productivity patterns.
    Provides insights for optimal scheduling.
    """

    def __init__(self):
        self.energy_logs: List[EnergyLevel] = []
        self.daily_patterns: Dict[int, List[int]] = defaultdict(list)
        logger.info("SelfAwarenessTracker initialized")

    def log_energy(self, hour: int, level: int, notes: str = ""):
        """
        Log energy level for a specific hour.

        Args:
            hour: Hour of day (0-23)
            level: Energy level (1-10)
            notes: Optional notes
        """
        if not (0 <= hour <= 23):
            raise ValueError("Hour must be between 0 and 23")
        if not (1 <= level <= 10):
            raise ValueError("Energy level must be between 1 and 10")

        entry = EnergyLevel(hour, level, notes)
        self.energy_logs.append(entry)
        self.daily_patterns[hour].append(level)

        logger.info(f"Logged energy: hour={hour}, level={level}")

    def get_peak_hours(self, top_n: int = 3) -> List[Tuple[int, float]]:
        """
        Get peak energy hours.

        Returns:
            List of (hour, avg_energy) tuples
        """
        if not self.daily_patterns:
            return []

        # Calculate average energy for each hour
        avg_energy = {hour: sum(levels) / len(levels) for hour, levels in self.daily_patterns.items()}

        # Sort by energy level
        sorted_hours = sorted(avg_energy.items(), key=lambda x: x[1], reverse=True)

        return sorted_hours[:top_n]

    def get_low_hours(self, bottom_n: int = 3) -> List[Tuple[int, float]]:
        """
        Get low energy hours.

        Returns:
            List of (hour, avg_energy) tuples
        """
        if not self.daily_patterns:
            return []

        # Calculate average energy for each hour
        avg_energy = {hour: sum(levels) / len(levels) for hour, levels in self.daily_patterns.items()}

        # Sort by energy level (ascending)
        sorted_hours = sorted(avg_energy.items(), key=lambda x: x[1])

        return sorted_hours[:bottom_n]

    def suggest_schedule(self) -> Dict[str, List[str]]:
        """
        Suggest optimal schedule based on energy patterns.

        Returns:
            Schedule with activities for different times
        """
        peak_hours = self.get_peak_hours(3)
        low_hours = self.get_low_hours(3)

        schedule = {"peak_hours": [], "low_hours": [], "recommendations": []}

        # Format peak hours
        for hour, energy in peak_hours:
            time_str = f"{hour:02d}:00"
            schedule["peak_hours"].append(f"{time_str} (energy: {energy:.1f}/10)")

        # Format low hours
        for hour, energy in low_hours:
            time_str = f"{hour:02d}:00"
            schedule["low_hours"].append(f"{time_str} (energy: {energy:.1f}/10)")

        # Generate recommendations
        if peak_hours:
            peak_time = f"{peak_hours[0][0]:02d}:00"
            schedule["recommendations"].append(f"Schedule important work around {peak_time}")

        if low_hours:
            low_time = f"{low_hours[0][0]:02d}:00"
            schedule["recommendations"].append(f"Avoid demanding tasks around {low_time}")
            schedule["recommendations"].append("Consider breaks or routine tasks during low energy periods")

        return schedule

    def get_energy_curve(self) -> Dict[int, float]:
        """
        Get average energy curve throughout the day.

        Returns:
            Dict mapping hour to average energy
        """
        return {hour: sum(levels) / len(levels) for hour, levels in self.daily_patterns.items()}

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze energy patterns and provide insights.

        Returns:
            Analysis with insights
        """
        if not self.energy_logs:
            return {"status": "insufficient_data", "message": "Need more energy logs for analysis"}

        peak_hours = self.get_peak_hours(3)
        low_hours = self.get_low_hours(3)
        energy_curve = self.get_energy_curve()

        # Calculate overall stats
        all_levels = [log.level for log in self.energy_logs]
        avg_energy = sum(all_levels) / len(all_levels)

        # Identify patterns
        patterns = []

        # Morning person vs night owl
        morning_avg = (
            sum(energy_curve.get(h, 0) for h in range(6, 12)) / 6 if any(h in energy_curve for h in range(6, 12)) else 0
        )

        evening_avg = (
            sum(energy_curve.get(h, 0) for h in range(18, 24)) / 6
            if any(h in energy_curve for h in range(18, 24))
            else 0
        )

        if morning_avg > evening_avg + 1:
            patterns.append("Morning person - highest energy in AM")
        elif evening_avg > morning_avg + 1:
            patterns.append("Night owl - highest energy in PM")

        # Energy consistency
        if all_levels:
            variance = sum((x - avg_energy) ** 2 for x in all_levels) / len(all_levels)
            if variance < 2:
                patterns.append("Consistent energy throughout day")
            else:
                patterns.append("Variable energy - plan around peaks")

        return {
            "status": "analyzed",
            "total_logs": len(self.energy_logs),
            "avg_energy": f"{avg_energy:.1f}/10",
            "peak_hours": [f"{h:02d}:00" for h, _ in peak_hours],
            "low_hours": [f"{h:02d}:00" for h, _ in low_hours],
            "patterns": patterns,
            "energy_curve": energy_curve,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return {
            "total_logs": len(self.energy_logs),
            "hours_tracked": len(self.daily_patterns),
            "avg_logs_per_hour": (len(self.energy_logs) / len(self.daily_patterns) if self.daily_patterns else 0),
        }


# Global instance
self_awareness_tracker = SelfAwarenessTracker()
