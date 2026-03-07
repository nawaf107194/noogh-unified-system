#!/usr/bin/env python3
"""
Emergency Script: Unblock Evolution Pipeline
Resets stuck innovations and patches trigger threshold.

Usage: python scripts/emergency_unblock_evolution.py
"""

import sys
import time
from pathlib import Path
from collections import Counter

sys.path.append(str(Path(__file__).parent.parent))

from unified_core.evolution.innovation_storage import InnovationStorage
from proto_generated.evolution import learning_pb2

def reset_stuck_innovations():
    """Reset queued/processing innovations back to suggested."""

    storage = InnovationStorage()
    if not Path(storage.pb_file).exists():
        print(f"❌ File not found: {storage.pb_file}")
        return False

    # Read all innovations
    innovations = storage.get_all()

    # Count by status
    status_before = Counter(learning_pb2.InnovationStatus.Name(i.status) for i in innovations)

    # Reset stuck innovations
    reset_count = 0
    for inn in innovations:
        if inn.status in (learning_pb2.INNOVATION_STATUS_QUEUED_FOR_EVOLUTION, learning_pb2.INNOVATION_STATUS_PROCESSING_BY_EVOLUTION):
            inn.status = learning_pb2.INNOVATION_STATUS_SUGGESTED
            inn.context['reset_by'] = 'emergency_unblock'
            inn.context['reset_reason'] = 'evolution_pipeline_stalled'
            reset_count += 1

    # Write back
    storage.save_all(innovations)

    # Count after
    status_after = Counter(learning_pb2.InnovationStatus.Name(i.status) for i in innovations)

    print("=" * 70)
    print("🔧 EMERGENCY: Reset Stuck Innovations")
    print("=" * 70)
    print()
    print("📊 Before:")
    for status, count in status_before.most_common():
        print(f"   {status:30s}: {count:3d}")
    print()
    print("📊 After:")
    for status, count in status_after.most_common():
        print(f"   {status:30s}: {count:3d}")
    print()
    print(f"✅ Reset {reset_count} innovations to 'suggested'")
    print()

    return True


def show_trigger_status():
    """Show if LearningInnovationTrigger can now fire."""

    storage = InnovationStorage()
    innovations = storage.get_all()

    suggested = [i for i in innovations if i.status == learning_pb2.INNOVATION_STATUS_SUGGESTED]

    if not suggested:
        print("⚠️  No suggested innovations found!")
        return

    type_counts = Counter(s.context.get('original_type', str(s.innovation_type)) for s in suggested)
    most_common = type_counts.most_common(1)[0] if type_counts else (None, 0)

    print("=" * 70)
    print("🎯 LearningInnovationTrigger Status")
    print("=" * 70)
    print()
    print(f"📊 Total Suggested: {len(suggested)}")
    print()
    print("   By Type:")
    for itype, count in type_counts.most_common(5):
        print(f"      {itype:30s}: {count}")
    print()

    # Check if trigger will fire
    print("🔍 Trigger Conditions:")
    print(f"   Min suggestions (≥3): {'✅' if len(suggested) >= 3 else '❌'} ({len(suggested)})")
    print(f"   Same type (≥3):       {'✅' if most_common[1] >= 3 else '❌'} ({most_common[1]} of {most_common[0]})")
    print()

    if most_common[1] >= 3:
        print("✅ Trigger WILL FIRE on next check!")
    elif most_common[1] >= 2:
        print("⚠️  Trigger MIGHT fire if threshold lowered to 2")
    else:
        print("❌ Trigger WON'T fire - need more of same type")
    print()


def show_next_steps():
    """Show what to do next."""

    print("=" * 70)
    print("📋 Next Steps")
    print("=" * 70)
    print()
    print("1. Wait for Evolution Controller to process (auto-trigger)")
    print("   - Checked every 10 cycles (~20 seconds)")
    print("   - Will fire if conditions met")
    print()
    print("2. OR manually trigger evolution:")
    print("   .venv/bin/python scripts/apply_learning_innovations.py --max-count 5")
    print()
    print("3. Monitor progress:")
    print("   .venv/bin/python scripts/health_check.py")
    print()
    print("4. Check logs:")
    print("   tail -f logs/agent_daemon_*.log | grep evolution")
    print()


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🚨 EMERGENCY: Unblock NOOGH Evolution Pipeline             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Step 1: Reset stuck innovations
    success = reset_stuck_innovations()

    if not success:
        print("❌ Failed to reset innovations")
        return 1

    # Step 2: Show trigger status
    show_trigger_status()

    # Step 3: Show next steps
    show_next_steps()

    print("=" * 70)
    print("✅ Pipeline Unblocked - Ready for Evolution")
    print("=" * 70)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
