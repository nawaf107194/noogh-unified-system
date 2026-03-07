#!/usr/bin/env python3
"""
Apply Learning Innovations - Manual trigger for autonomous learning application
Usage: python apply_learning_innovations.py [--max-count 3] [--dry-run]
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_core.evolution.innovation_applier import get_innovation_applier
from unified_core.evolution.evolution_triggers import LearningInnovationTrigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("apply_learning")


async def check_trigger():
    """Check if LearningInnovationTrigger would fire."""
    trigger = LearningInnovationTrigger()
    event = await trigger.check()

    if event:
        logger.info("🎯 LearningInnovationTrigger WOULD FIRE:")
        logger.info(f"   Severity: {event.severity.value}")
        logger.info(f"   Context: {event.context}")
        return True
    else:
        logger.info("⏸️  LearningInnovationTrigger would NOT fire (not enough suggestions or cooldown)")
        return False


def apply_innovations(max_count: int = 3, dry_run: bool = False):
    """Apply top priority learning innovations."""
    applier = get_innovation_applier()

    # Get stats
    stats = applier.get_stats()
    logger.info("=" * 70)
    logger.info("📊 Innovation Statistics:")
    logger.info(f"   Total pending: {stats['total_pending']}")
    logger.info(f"   Total applied: {stats['total_applied']}")
    logger.info(f"   Pending by type:")
    for typ, count in sorted(stats['pending_by_type'].items(), key=lambda x: -x[1]):
        logger.info(f"      - {typ}: {count}")
    logger.info("=" * 70)

    if stats['total_pending'] == 0:
        logger.info("✅ No pending innovations to apply")
        return

    # Get top proposals
    logger.info(f"\n💡 Generating top {max_count} innovation proposals...")
    proposals = applier.apply_top_innovations(max_count=max_count)

    if not proposals:
        logger.info("❌ No proposals generated")
        return

    logger.info(f"\n✨ Generated {len(proposals)} proposals:\n")
    for i, proposal in enumerate(proposals, 1):
        logger.info(f"   {i}. {proposal['title']}")
        logger.info(f"      Type: {proposal['type']}")
        logger.info(f"      Priority: {proposal['priority']}")
        logger.info(f"      Tags: {', '.join(proposal['tags'])}")
        logger.info(f"      Description: {proposal['description'][:100]}...")

        if 'target_files' in proposal:
            logger.info(f"      Targets: {', '.join(proposal['target_files'][:2])}")

        learning_ctx = proposal.get('learning_context', {})
        logger.info(f"      Learned from: {learning_ctx.get('triggered_by', 'Unknown')[:60]}...")
        logger.info("")

    if dry_run:
        logger.info("🔍 DRY RUN - No changes made")
        logger.info("   To apply these innovations, run without --dry-run")
        return

    # Mark as applied
    logger.info("📝 Marking innovations as applied...")
    pending = applier.get_pending_innovations()
    for innovation in pending[:max_count]:
        applier.mark_innovation_applied(innovation)
        applier.update_innovation_status(
            innovation['_id'],
            'queued_for_evolution'
        )

    logger.info(f"\n✅ {len(proposals)} innovations queued for Evolution Controller")
    logger.info("\n📋 Next steps:")
    logger.info("   1. Evolution Controller will pick up these proposals")
    logger.info("   2. Brain will design implementations")
    logger.info("   3. Code will be generated and tested")
    logger.info("   4. Changes will be deployed automatically")

    # Save proposals to file for Evolution Controller
    import json
    import time
    proposals_file = f"/home/noogh/projects/noogh_unified_system/src/data/evolution/learning_proposals_{int(time.time())}.json"
    os.makedirs(os.path.dirname(proposals_file), exist_ok=True)

    with open(proposals_file, 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'source': 'autonomous_learning',
            'proposals': proposals
        }, f, indent=2)

    logger.info(f"\n💾 Proposals saved to: {proposals_file}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Apply learning innovations")
    parser.add_argument('--max-count', type=int, default=3,
                        help='Maximum innovations to apply (default: 3)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be applied without applying')
    parser.add_argument('--check-trigger', action='store_true',
                        help='Check if LearningInnovationTrigger would fire')
    args = parser.parse_args()

    logger.info("🧠 NOOGH Learning Innovation Applicator")
    logger.info("=" * 70)

    if args.check_trigger:
        await check_trigger()
        print()

    apply_innovations(max_count=args.max_count, dry_run=args.dry_run)

    logger.info("\n" + "=" * 70)
    logger.info("✨ Done!")


if __name__ == "__main__":
    asyncio.run(main())
