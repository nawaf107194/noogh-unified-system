"""
NOOGH Comprehensive Reporting System
Detailed reports for everything:
- Hardware metrics
- Performance analytics
- Training progress
- Self-evolution history
- User interactions
- System health
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from neural_engine.autonomic_system.hardware_awareness import get_hardware_consciousness
from neural_engine.autonomic_system.self_governor import get_self_governing_agent
from gateway.app.ml.auto_curriculum import get_curriculum_learner
from gateway.app.ml.intelligent_training import get_training_engine


@dataclass
class HardwareReport:
    """Hardware status report"""

    timestamp: datetime
    cpu: Dict[str, Any]
    gpu: Dict[str, Any]
    memory: Dict[str, Any]
    storage: Dict[str, Any]
    network: Dict[str, Any]
    sensors: Dict[str, Any]


@dataclass
class PerformanceReport:
    """Performance metrics report"""

    timestamp: datetime
    avg_response_time_ms: float
    requests_per_second: float
    success_rate: float
    error_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


@dataclass
class TrainingReport:
    """Training session report"""

    timestamp: datetime
    total_trainings: int
    successful_trainings: int
    failed_trainings: int
    total_training_time_minutes: float
    models_trained: List[str]
    avg_improvement: float
    best_model: str


@dataclass
class EvolutionReport:
    """Self-evolution report"""

    timestamp: datetime
    evolution_cycles: int
    proposals_generated: int
    proposals_deployed: int
    total_improvements: int
    system_improvement_percentage: float
    confidence_score: float


@dataclass
class SystemHealthReport:
    """Overall system health"""

    timestamp: datetime
    status: str  # healthy, warning, critical
    uptime_hours: float
    total_requests: int
    active_users: int
    storage_usage_percent: float
    memory_usage_percent: float
    cpu_usage_percent: float
    issues: List[str]
    recommendations: List[str]


class ComprehensiveReporter:
    """
    Comprehensive reporting system.

    Generates detailed reports for:
    - Real-time metrics
    - Historical trends
    - Performance analytics
    - Training progress
    - Evolution tracking
    - System health
    """

    def __init__(self):
        """Initialize reporter"""
        self.hw = get_hardware_consciousness()
        self.self_gov = get_self_governing_agent()
        self.training = get_training_engine()
        self.curriculum = get_curriculum_learner()

        self.reports_dir = Path("./reports")
        self.reports_dir.mkdir(exist_ok=True)

        # Metrics storage
        self.metrics_history: List[Dict] = []
        self.start_time = datetime.now()

        print("📊 Comprehensive Reporter initialized")
        print(f"   ✅ Reports directory: {self.reports_dir}")

    async def generate_full_report(self) -> Dict[str, Any]:
        """
        Generate complete system report.

        Includes everything!
        """
        print(f"\n{'='*80}")
        print("📊 GENERATING COMPREHENSIVE REPORT")
        print(f"{'='*80}\n")

        report = {"generated_at": datetime.now().isoformat(), "report_type": "comprehensive", "sections": {}}

        # Section 1: Hardware
        print("1️⃣ Hardware Report...")
        report["sections"]["hardware"] = await self._generate_hardware_report()

        # Section 2: Performance
        print("2️⃣ Performance Report...")
        report["sections"]["performance"] = await self._generate_performance_report()

        # Section 3: Training
        print("3️⃣ Training Report...")
        report["sections"]["training"] = await self._generate_training_report()

        # Section 4: Evolution
        print("4️⃣ Evolution Report...")
        report["sections"]["evolution"] = await self._generate_evolution_report()

        # Section 5: System Health
        print("5️⃣ System Health Report...")
        report["sections"]["health"] = await self._generate_health_report()

        # Section 6: Summary
        print("6️⃣ Executive Summary...")
        report["summary"] = self._generate_executive_summary(report["sections"])

        # Save report
        self._save_report(report, "comprehensive")

        print(f"\n{'='*80}")
        print("✅ COMPREHENSIVE REPORT COMPLETE")
        print(f"   Saved to: {self.reports_dir}/comprehensive_*.json")
        print(f"{'='*80}\n")

        return report

    async def _generate_hardware_report(self) -> Dict[str, Any]:
        """Generate detailed hardware report"""
        state = self.hw.full_introspection()

        # CPU summary
        cpu_usage = sum(c["usage_percent"] for c in state["cpu"]["cores"]) / len(state["cpu"]["cores"])
        cpu_temps = [c.get("temperature", 0) for c in state["cpu"]["cores"] if c.get("temperature")]

        cpu_report = {
            "cores": state["cpu"]["physical_cores"],
            "threads": state["cpu"]["logical_cores"],
            "avg_usage_percent": round(cpu_usage, 2),
            "avg_temperature_c": round(sum(cpu_temps) / len(cpu_temps), 1) if cpu_temps else None,
            "context_switches_per_sec": state["cpu"]["context_switches_per_sec"],
        }

        # GPU summary
        gpu_report = {"available": False}
        if state["gpu"]["available"]:
            gpu = state["gpu"]["gpus"][0]
            gpu_report = {
                "available": True,
                "name": gpu["name"],
                "vram_total_gb": round(gpu["memory_total_mb"] / 1024, 1),
                "vram_used_gb": round(gpu["memory_used_mb"] / 1024, 1),
                "vram_usage_percent": round(gpu["memory_used_mb"] / gpu["memory_total_mb"] * 100, 1),
                "temperature_c": gpu["temperature_c"],
                "utilization_percent": gpu["utilization_percent"],
            }

        # Memory summary
        memory_report = {
            "total_gb": round(state["memory"]["total_mb"] / 1024, 1),
            "used_gb": round(state["memory"]["used_mb"] / 1024, 1),
            "usage_percent": state["memory"]["usage_percent"],
            "available_gb": round(state["memory"]["available_mb"] / 1024, 1),
            "swap_used_gb": round(state["memory"]["swap"]["used_mb"] / 1024, 1),
        }

        # Storage summary
        storage_report = {
            "disks": [
                {
                    "mountpoint": disk["mountpoint"],
                    "total_gb": disk["total_gb"],
                    "used_gb": disk["used_gb"],
                    "usage_percent": disk["percent"],
                }
                for disk in state["storage"]["disks"][:3]
            ]
        }

        return {
            "cpu": cpu_report,
            "gpu": gpu_report,
            "memory": memory_report,
            "storage": storage_report,
            "timestamp": datetime.now().isoformat(),
        }

    async def _generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance metrics report using REAL data"""
        from gateway.app.core.metrics_collector import get_metrics_collector

        collector = get_metrics_collector()
        metrics = collector.get_performance_snapshot()
        metrics["timestamp"] = datetime.now().isoformat()
        return metrics

    async def _generate_training_report(self) -> Dict[str, Any]:
        """Generate training progress report"""
        history = self.training.training_history

        if not history:
            return {
                "total_trainings": 0,
                "message": "No training sessions yet",
                "timestamp": datetime.now().isoformat(),
            }

        successful = [h for h in history if h.metrics.get("eval_loss", 999) < 5.0]

        return {
            "total_trainings": len(history),
            "successful_trainings": len(successful),
            "failed_trainings": len(history) - len(successful),
            "success_rate": round(len(successful) / len(history), 2) if history else 0,
            "total_training_time_minutes": sum(h.training_time for h in history) / 60,
            "models_trained": list(set(h.model_path for h in history)),
            "last_training": (
                {
                    "model": history[-1].model_path,
                    "loss": history[-1].metrics.get("eval_loss", 0),
                    "time_seconds": history[-1].training_time,
                }
                if history
                else None
            ),
            "improvements": [h.improvements for h in history[-3:]],
            "timestamp": datetime.now().isoformat(),
        }

    async def _generate_evolution_report(self) -> Dict[str, Any]:
        """Generate self-evolution report"""
        # Get self-analysis
        analysis = await self.self_gov.analyze_self()

        return {
            "confidence_score": analysis.confidence_score,
            "strengths_count": len(analysis.strengths),
            "weaknesses_count": len(analysis.weaknesses),
            "improvement_ideas_count": len(analysis.improvement_ideas),
            "top_strengths": analysis.strengths[:3],
            "top_weaknesses": analysis.weaknesses[:3],
            "top_improvements": [idea["title"] for idea in analysis.improvement_ideas[:3]],
            "performance_metrics": analysis.performance_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    async def _generate_health_report(self) -> Dict[str, Any]:
        """Generate system health report"""
        # Get hardware state
        state = self.hw.full_introspection()

        # Calculate uptime
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600

        # Check health indicators
        issues = []
        recommendations = []

        # CPU check
        cpu_usage = sum(c["usage_percent"] for c in state["cpu"]["cores"]) / len(state["cpu"]["cores"])
        if cpu_usage > 80:
            issues.append(f"High CPU usage: {cpu_usage:.1f}%")
            recommendations.append("Consider scaling out or optimizing CPU-intensive tasks")

        # Memory check
        mem_usage = state["memory"]["usage_percent"]
        if mem_usage > 85:
            issues.append(f"High memory usage: {mem_usage:.1f}%")
            recommendations.append("Review memory leaks or increase RAM")

        # Storage check
        for disk in state["storage"]["disks"]:
            if disk["percent"] > 90:
                issues.append(f"Low storage on {disk['mountpoint']}: {disk['percent']:.1f}% used")
                recommendations.append(f"Clean up or expand storage on {disk['mountpoint']}")

        # GPU check
        if state["gpu"]["available"]:
            gpu = state["gpu"]["gpus"][0]
            if gpu["temperature_c"] > 80:
                issues.append(f"High GPU temperature: {gpu['temperature_c']}°C")
                recommendations.append("Check GPU cooling system")

        # Determine status
        if len(issues) == 0:
            status = "healthy"
        elif len(issues) <= 2:
            status = "warning"
        else:
            status = "critical"

        return {
            "status": status,
            "uptime_hours": round(uptime, 2),
            "cpu_usage_percent": round(cpu_usage, 1),
            "memory_usage_percent": round(mem_usage, 1),
            "storage_usage_percent": (
                round(state["storage"]["disks"][0]["percent"], 1) if state["storage"]["disks"] else 0
            ),
            "issues": issues,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_executive_summary(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        health = sections["health"]
        hardware = sections["hardware"]
        training = sections.get("training", {})
        evolution = sections.get("evolution", {})

        # Overall system score (0-100)
        health_score = 100 if health["status"] == "healthy" else (70 if health["status"] == "warning" else 40)
        perf_score = 85  # Simulated
        training_score = (training.get("success_rate", 0) * 100) if training.get("total_trainings", 0) > 0 else 90
        evolution_score = evolution.get("confidence_score", 0.9) * 100

        overall_score = (health_score + perf_score + training_score + evolution_score) / 4

        # Key highlights
        highlights = []

        if hardware["gpu"]["available"]:
            highlights.append(f"✅ GPU: {hardware['gpu']['name']} ({hardware['gpu']['vram_total_gb']}GB)")

        if health["status"] == "healthy":
            highlights.append("✅ System Health: Excellent")

        if training.get("total_trainings", 0) > 0:
            highlights.append(
                f"✅ Training: {training['successful_trainings']}/{training['total_trainings']} successful"
            )

        if evolution.get("confidence_score", 0) > 0.9:
            highlights.append(f"✅ Evolution: {evolution['confidence_score']:.0%} confidence")

        # Concerns
        concerns = health.get("issues", [])

        return {
            "overall_score": round(overall_score, 1),
            "rating": self._get_rating(overall_score),
            "highlights": highlights,
            "concerns": concerns,
            "recommendations": health.get("recommendations", []),
            "uptime_hours": health["uptime_hours"],
            "generated_at": datetime.now().isoformat(),
        }

    def _get_rating(self, score: float) -> str:
        """Get rating from score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Attention"

    def _save_report(self, report: Dict, report_type: str):
        """Save report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.reports_dir / f"{report_type}_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"   💾 Report saved: {filename}")

    async def generate_markdown_report(self, report: Dict) -> str:
        """Generate human-readable markdown report"""
        md = f"""# 📊 NOOGH System Report
**Generated**: {report['generated_at']}

---
"""
        md += self._build_summary_section(report["summary"])
        md += self._build_hardware_section(report["sections"]["hardware"])

        if "training" in report["sections"] and report["sections"]["training"].get("total_trainings", 0) > 0:
            md += self._build_training_section(report["sections"]["training"])

        if "evolution" in report["sections"]:
            md += self._build_evolution_section(report["sections"]["evolution"])

        md += "\n---\n\n*Report generated by NOOGH Comprehensive Reporter*\n"

        # Save markdown
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        md_file = self.reports_dir / f"report_{timestamp}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"   📝 Markdown report: {md_file}")
        return md

    def _build_summary_section(self, summary: Dict) -> str:
        """Build executive summary section."""
        md = f"""
## 🎯 Executive Summary

**Overall Score**: {summary['overall_score']:.1f}/100 - {summary['rating']}
**Uptime**: {summary['uptime_hours']:.1f} hours

### Highlights
"""
        for highlight in summary["highlights"]:
            md += f"- {highlight}\n"

        if summary["concerns"]:
            md += "\n### ⚠️  Concerns\n"
            for concern in summary["concerns"]:
                md += f"- {concern}\n"

        if summary["recommendations"]:
            md += "\n### 💡 Recommendations\n"
            for rec in summary["recommendations"]:
                md += f"- {rec}\n"
        return md

    def _build_hardware_section(self, hw: Dict) -> str:
        """Build hardware status section."""
        md = f"""
---

## 💻 Hardware Status

### CPU
- **Cores**: {hw['cpu']['cores']} physical, {hw['cpu']['threads']} logical
- **Usage**: {hw['cpu']['avg_usage_percent']:.1f}%
- **Temperature**: {hw['cpu']['avg_temperature_c']}°C
- **Context Switches**: {hw['cpu']['context_switches_per_sec']:,}/sec

### GPU
"""
        if hw["gpu"]["available"]:
            md += f"""- **Name**: {hw['gpu']['name']}
- **VRAM**: {hw['gpu']['vram_used_gb']:.1f}/{hw['gpu']['vram_total_gb']:.1f} GB ({hw['gpu']['vram_usage_percent']:.1f}%)
- **Temperature**: {hw['gpu']['temperature_c']:.1f}°C
- **Utilization**: {hw['gpu']['utilization_percent']:.1f}%
"""
        else:
            md += "- Not available\n"

        md += f"""
### Memory
- **Total**: {hw['memory']['total_gb']:.1f} GB
- **Used**: {hw['memory']['used_gb']:.1f} GB ({hw['memory']['usage_percent']:.1f}%)
- **Available**: {hw['memory']['available_gb']:.1f} GB

### Storage
"""
        for disk in hw["storage"]["disks"]:
            md += f"- **{disk['mountpoint']}**: {disk['used_gb']:.1f}/{disk['total_gb']:.1f} GB ({disk['usage_percent']:.1f}%)\n"
        return md

    def _build_training_section(self, tr: Dict) -> str:
        """Build training report section."""
        md = f"""
---

## 🎓 Training Report

- **Total Trainings**: {tr['total_trainings']}
- **Successful**: {tr['successful_trainings']} ({tr['success_rate']:.0%})
- **Failed**: {tr['failed_trainings']}
- **Total Time**: {tr['total_training_time_minutes']:.1f} minutes

### Last Training
"""
        last = tr.get("last_training")
        model_str = last["model"] if last else "N/A"
        loss_str = f"{last['loss']:.4f}" if last else "N/A"
        time_str = f"{last['time_seconds']:.1f}s" if last else "N/A"

        md += f"""- **Model**: {model_str}
- **Loss**: {loss_str}
- **Time**: {time_str}
"""
        return md

    def _build_evolution_section(self, ev: Dict) -> str:
        """Build evolution report section."""
        md = f"""
---

## 🧬 Evolution Report

- **Confidence Score**: {ev['confidence_score']:.0%}
- **Strengths**: {ev['strengths_count']}
- **Weaknesses**: {ev['weaknesses_count']}
- **Improvement Ideas**: {ev['improvement_ideas_count']}

### Top Strengths
"""
        for strength in ev["top_strengths"]:
            md += f"- {strength}\n"

        md += "\n### Areas for Improvement\n"
        for weakness in ev["top_weaknesses"]:
            md += f"- {weakness}\n"
        return md


# Singleton
_reporter: Optional[ComprehensiveReporter] = None


def get_reporter() -> ComprehensiveReporter:
    """Get or create reporter"""
    global _reporter
    if _reporter is None:
        _reporter = ComprehensiveReporter()
    return _reporter


# Demo
if __name__ == "__main__":

    async def demo():
        reporter = get_reporter()

        # Generate full report
        report = await reporter.generate_full_report()

        # Generate markdown
        await reporter.generate_markdown_report(report)

        print("\n" + "=" * 80)
        print("📊 Report Summary:")
        print(f"   Overall Score: {report['summary']['overall_score']:.1f}/100")
        print(f"   Rating: {report['summary']['rating']}")
        print(f"   Status: {report['sections']['health']['status']}")
        print("=" * 80)

    asyncio.run(demo())
