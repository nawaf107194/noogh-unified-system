#!/usr/bin/env python3
"""
Validation: اختبار المرشحات المحسّنة على البيانات التاريخية
نتحقق هل المرشحات فعلاً تحسّن معدل النجاح
"""
import json
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))

# Import directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "brain_improved_filters",
    Path(__file__).parent.parent / 'strategies' / 'brain_improved_filters.py'
)
filters_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filters_module)

improved_long_filter = filters_module.improved_long_filter
improved_short_filter = filters_module.improved_short_filter


def validate_filters():
    """التحقق من تحسين المرشحات"""

    print("\n" + "="*70)
    print("🧪 VALIDATING IMPROVED FILTERS ON HISTORICAL DATA")
    print("="*70)

    # تحميل البيانات
    data_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')

    setups = []
    with open(data_file, 'r') as f:
        for line in f:
            setups.append(json.loads(line))

    print(f"\n📥 Loaded {len(setups)} historical setups")

    # ===============================
    # Before filters (baseline)
    # ===============================
    print(f"\n{'='*70}")
    print("📊 BASELINE (No Filters)")
    print("="*70)

    long_setups = [s for s in setups if s['signal'] == 'LONG']
    short_setups = [s for s in setups if s['signal'] == 'SHORT']

    long_wins_before = len([s for s in long_setups if s['outcome'] == 'WIN'])
    long_losses_before = len([s for s in long_setups if s['outcome'] == 'LOSS'])
    long_wr_before = long_wins_before / (long_wins_before + long_losses_before) * 100 if (long_wins_before + long_losses_before) > 0 else 0

    short_wins_before = len([s for s in short_setups if s['outcome'] == 'WIN'])
    short_losses_before = len([s for s in short_setups if s['outcome'] == 'LOSS'])
    short_wr_before = short_wins_before / (short_wins_before + short_losses_before) * 100 if (short_wins_before + short_losses_before) > 0 else 0

    print(f"\nLONG:  {long_wins_before}W / {long_losses_before}L = {long_wr_before:.1f}% WR ({len(long_setups)} total)")
    print(f"SHORT: {short_wins_before}W / {short_losses_before}L = {short_wr_before:.1f}% WR ({len(short_setups)} total)")

    overall_wr_before = (long_wins_before + short_wins_before) / (long_wins_before + long_losses_before + short_wins_before + short_losses_before) * 100
    print(f"\nOVERALL: {long_wins_before + short_wins_before}W / {long_losses_before + short_losses_before}L = {overall_wr_before:.1f}% WR")

    # ===============================
    # After filters
    # ===============================
    print(f"\n{'='*70}")
    print("✅ AFTER IMPROVED FILTERS")
    print("="*70)

    # تطبيق المرشحات
    long_filtered = []
    long_rejected = 0

    for setup in long_setups:
        passed, reason = improved_long_filter(setup)
        if passed:
            long_filtered.append(setup)
        else:
            long_rejected += 1

    short_filtered = []
    short_rejected = 0

    for setup in short_setups:
        passed, reason = improved_short_filter(setup)
        if passed:
            short_filtered.append(setup)
        else:
            short_rejected += 1

    # حساب النتائج بعد الفلترة
    long_wins_after = len([s for s in long_filtered if s['outcome'] == 'WIN'])
    long_losses_after = len([s for s in long_filtered if s['outcome'] == 'LOSS'])
    long_wr_after = long_wins_after / (long_wins_after + long_losses_after) * 100 if (long_wins_after + long_losses_after) > 0 else 0

    short_wins_after = len([s for s in short_filtered if s['outcome'] == 'WIN'])
    short_losses_after = len([s for s in short_filtered if s['outcome'] == 'LOSS'])
    short_wr_after = short_wins_after / (short_wins_after + short_losses_after) * 100 if (short_wins_after + short_losses_after) > 0 else 0

    print(f"\nLONG:  {long_wins_after}W / {long_losses_after}L = {long_wr_after:.1f}% WR ({len(long_filtered)} passed, {long_rejected} rejected)")
    print(f"SHORT: {short_wins_after}W / {short_losses_after}L = {short_wr_after:.1f}% WR ({len(short_filtered)} passed, {short_rejected} rejected)")

    overall_wr_after = (long_wins_after + short_wins_after) / (long_wins_after + long_losses_after + short_wins_after + short_losses_after) * 100
    print(f"\nOVERALL: {long_wins_after + short_wins_after}W / {long_losses_after + short_losses_after}L = {overall_wr_after:.1f}% WR")

    # ===============================
    # Improvement summary
    # ===============================
    print(f"\n{'='*70}")
    print("📈 IMPROVEMENT SUMMARY")
    print("="*70)

    long_improvement = long_wr_after - long_wr_before
    short_improvement = short_wr_after - short_wr_before
    overall_improvement = overall_wr_after - overall_wr_before

    print(f"\nLONG:    {long_wr_before:.1f}% → {long_wr_after:.1f}% ({long_improvement:+.1f}%) {'✅' if long_improvement > 0 else '❌'}")
    print(f"SHORT:   {short_wr_before:.1f}% → {short_wr_after:.1f}% ({short_improvement:+.1f}%) {'✅' if short_improvement > 0 else '❌'}")
    print(f"OVERALL: {overall_wr_before:.1f}% → {overall_wr_after:.1f}% ({overall_improvement:+.1f}%) {'✅' if overall_improvement > 0 else '❌'}")

    # ===============================
    # What got filtered out?
    # ===============================
    print(f"\n{'='*70}")
    print("🗑️  WHAT GOT REJECTED?")
    print("="*70)

    # Analyze rejected LONG setups
    rejected_long = [s for s in long_setups if not improved_long_filter(s)[0]]
    rejected_long_wins = len([s for s in rejected_long if s['outcome'] == 'WIN'])
    rejected_long_losses = len([s for s in rejected_long if s['outcome'] == 'LOSS'])

    print(f"\nRejected LONG ({len(rejected_long)}):")
    print(f"   Wins: {rejected_long_wins}")
    print(f"   Losses: {rejected_long_losses}")
    print(f"   → Good! Filtered out {rejected_long_losses - rejected_long_wins} more losses than wins")

    # Analyze rejected SHORT setups
    rejected_short = [s for s in short_setups if not improved_short_filter(s)[0]]
    rejected_short_wins = len([s for s in rejected_short if s['outcome'] == 'WIN'])
    rejected_short_losses = len([s for s in rejected_short if s['outcome'] == 'LOSS'])

    print(f"\nRejected SHORT ({len(rejected_short)}):")
    print(f"   Wins: {rejected_short_wins}")
    print(f"   Losses: {rejected_short_losses}")
    print(f"   → Good! Filtered out {rejected_short_losses - rejected_short_wins} more losses than wins")

    # ===============================
    # Final verdict
    # ===============================
    print(f"\n{'='*70}")
    print("🎯 FINAL VERDICT")
    print("="*70)

    if overall_improvement > 5:
        print(f"\n✅ EXCELLENT: +{overall_improvement:.1f}% improvement!")
        print("   → Filters are working as expected")
        print("   → Ready to deploy in autonomous agent")
    elif overall_improvement > 2:
        print(f"\n✅ GOOD: +{overall_improvement:.1f}% improvement")
        print("   → Filters provide meaningful benefit")
        print("   → Can be deployed with monitoring")
    elif overall_improvement > 0:
        print(f"\n⚠️ MARGINAL: +{overall_improvement:.1f}% improvement")
        print("   → Filters help but not significantly")
        print("   → Consider additional refinement")
    else:
        print(f"\n❌ NO IMPROVEMENT: {overall_improvement:.1f}%")
        print("   → Filters need revision")
        print("   → Re-analyze patterns")

    print(f"\n{'='*70}\n")

    # حفظ النتائج
    results = {
        'baseline': {
            'long_wr': long_wr_before,
            'short_wr': short_wr_before,
            'overall_wr': overall_wr_before
        },
        'improved': {
            'long_wr': long_wr_after,
            'short_wr': short_wr_after,
            'overall_wr': overall_wr_after
        },
        'improvement': {
            'long': long_improvement,
            'short': short_improvement,
            'overall': overall_improvement
        },
        'rejection_stats': {
            'long_rejected': long_rejected,
            'short_rejected': short_rejected,
            'long_kept': len(long_filtered),
            'short_kept': len(short_filtered)
        }
    }

    output_file = Path('/home/noogh/projects/noogh_unified_system/src/data/filter_validation.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"💾 Validation results saved to: {output_file}\n")

    return results


if __name__ == "__main__":
    validate_filters()
