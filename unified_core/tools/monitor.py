#!/usr/bin/env python3
"""
NOOGH System Monitor — Safe monitoring tool that runs without GPU.
Usage: CUDA_VISIBLE_DEVICES="" python3 -m unified_core.tools.monitor
   or: nmon  (bash alias)
"""
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Ensure no CUDA interference
os.environ["CUDA_VISIBLE_DEVICES"] = ""

EVOLUTION_DIR = Path.home() / ".noogh" / "evolution"
JOURNAL_DIR = Path.home() / "projects" / "noogh_unified_system" / "data" / "cognitive_journal"
LEDGER = EVOLUTION_DIR / "evolution_ledger.jsonl"
OBSERVATIONS = EVOLUTION_DIR / "observations.jsonl"


def print_header(text):
    print(f"\n{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}")


def evolution_stats():
    """Show evolution ledger statistics."""
    print_header("🧬 إحصائيات التطور")
    
    if not LEDGER.exists():
        print("  ❌ سجل التطور غير موجود")
        return
    
    total = 0
    proposals = {"pending": 0, "promoted": 0, "failed": 0, "rejected": 0}
    events = {"generated": 0, "proposed": 0, "promoted": 0, "failed": 0}
    
    with open(LEDGER) as f:
        for line in f:
            total += 1
            try:
                d = json.loads(line.strip())
                if d.get("type") == "proposal":
                    status = d.get("proposal", {}).get("status", "unknown")
                    proposals[status] = proposals.get(status, 0) + 1
                elif d.get("type") == "event":
                    etype = d.get("event_type", "unknown")
                    events[etype] = events.get(etype, 0) + 1
            except:
                pass
    
    size_mb = LEDGER.stat().st_size / 1024 / 1024
    mod_time = datetime.fromtimestamp(LEDGER.stat().st_mtime).strftime("%H:%M:%S")
    
    print(f"  📊 الإجمالي: {total} مُدخل ({size_mb:.1f} MB)")
    print(f"  🕒 آخر تحديث: {mod_time}")
    print(f"\n  المقترحات:")
    for k, v in proposals.items():
        emoji = {"promoted": "✅", "failed": "❌", "pending": "⏳", "rejected": "🚫"}.get(k, "📝")
        print(f"    {emoji} {k}: {v}")
    print(f"\n  الأحداث:")
    for k, v in events.items():
        print(f"    📌 {k}: {v}")


def latest_observations(n=5):
    """Show latest evolution observations."""
    print_header(f"🔭 آخر {n} ملاحظات تطورية")
    
    if not OBSERVATIONS.exists():
        print("  ❌ ملف الملاحظات غير موجود")
        return
    
    lines = []
    with open(OBSERVATIONS) as f:
        for line in f:
            lines.append(line)
    
    for line in lines[-n:]:
        try:
            d = json.loads(line.strip())
            ts = datetime.fromtimestamp(d.get("timestamp", 0)).strftime("%H:%M:%S")
            etype = d.get("event_type", "?")
            title = d.get("title", "?")[:60]
            target = d.get("target_file", "")
            if target:
                target = os.path.basename(target)
            status_emoji = {"generated": "🔧", "proposed": "📝", "promoted": "✅", "failed": "❌"}.get(etype, "📌")
            print(f"  {status_emoji} [{ts}] {etype: <10} | {title}")
            if target:
                print(f"      📁 {target}")
        except:
            pass


def latest_journal(n=5):
    """Show latest cognitive journal entries."""
    print_header(f"📓 آخر {n} يوميات معرفية")
    
    today = datetime.now().strftime("%Y-%m-%d")
    journal_file = JOURNAL_DIR / f"journal_{today}.jsonl"
    
    if not journal_file.exists():
        print(f"  ❌ يوميات اليوم غير موجودة ({journal_file.name})")
        return
    
    size_kb = journal_file.stat().st_size / 1024
    print(f"  📊 حجم يوميات اليوم: {size_kb:.0f} KB")
    
    lines = []
    with open(journal_file) as f:
        for line in f:
            lines.append(line)
    
    for line in lines[-n:]:
        try:
            d = json.loads(line.strip())
            ts = datetime.fromtimestamp(d.get("timestamp", 0)).strftime("%H:%M:%S")
            entry_type = d.get("entry_type", "?")
            content = d.get("content", "?")[:70]
            cycle = d.get("cycle", "?")
            emoji = {"success": "✅", "observation": "👁️", "error": "❌", "decision": "🧠"}.get(entry_type, "📝")
            print(f"  {emoji} [{ts}] C{cycle} | {entry_type: <12} | {content}")
        except:
            pass


def system_processes():
    """Show NOOGH processes status."""
    print_header("🖥️ عمليات النظام")
    
    import subprocess
    result = subprocess.run(
        ["ps", "aux"], capture_output=True, text=True
    )
    
    services = {
        "agent_daemon": "🧠 Agent Daemon",
        "ollama serve": "🤖 Ollama Server",
        "ollama runner": "🔮 Ollama Runner",
        "gateway.app": "🌐 Gateway API",
        "neural_engine/api": "⚡ Neural Engine",
        "task_worker": "⚙️ Task Worker",
        "dashboard.app": "📊 Dashboard",
        "vite": "💻 Console",
    }
    
    for key, name in services.items():
        found = False
        for line in result.stdout.split("\n"):
            if key in line and "grep" not in line:
                parts = line.split()
                pid, cpu, mem = parts[1], parts[2], parts[3]
                print(f"  {name: <25} PID: {pid: <8} CPU: {cpu}%  MEM: {mem}%")
                found = True
                break
        if not found:
            print(f"  {name: <25} ❌ غير شغال")


def main():
    print("\n" + "🔬 NOOGH System Monitor".center(50))
    print(f"  🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    system_processes()
    evolution_stats()
    latest_observations(5)
    latest_journal(5)
    
    promoted = EVOLUTION_DIR / "promoted_targets.json"
    if promoted.exists():
        size_kb = promoted.stat().st_size / 1024
        print(f"\n  📋 أهداف مُرقّاة: {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
