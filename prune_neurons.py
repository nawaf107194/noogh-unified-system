#!/usr/bin/env python3
"""
NOOGH NeuronFabric Pruner — Clean up stale neurons and weak synapses
=====================================================================
Removes:
1. Dead neurons (energy < 0.08, activations < 3)
2. Stale neurons (not activated in 7+ days, low energy)
3. Weak synapses (weight < 0.02, rarely fired)
4. Orphaned synapses (source/target neuron missing)
5. Duplicate monitoring neurons

Can be run manually or via evolution pipeline.
"""

import json
import time
import logging
import shutil
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger("neuron_pruner")

FABRIC_PATH = Path(__file__).parent / "data/neuron_fabric.json"
BACKUP_DIR = Path(__file__).parent / "data/backups"


def load_fabric():
    """Load raw neuron fabric JSON."""
    with open(FABRIC_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_fabric(data, backup=True):
    """Save fabric with optional backup."""
    if backup:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / f"neuron_fabric_{int(time.time())}.json"
        shutil.copy2(FABRIC_PATH, backup_path)
        logger.info(f"📦 Backup saved: {backup_path.name}")
    
    with open(FABRIC_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=None)
    
    size_kb = FABRIC_PATH.stat().st_size / 1024
    logger.info(f"💾 Fabric saved: {size_kb:.0f} KB")


def prune(
    max_age_days: float = 7.0,
    min_energy: float = 0.1,
    min_synapse_weight: float = 0.03,
    min_activations: int = 2,
    dry_run: bool = False,
) -> dict:
    """
    Deep prune the NeuronFabric.
    
    Args:
        max_age_days: Remove neurons not activated in this many days
        min_energy: Minimum energy to keep a neuron
        min_synapse_weight: Minimum synapse weight to keep
        min_activations: Minimum activation count to keep a neuron
        dry_run: If True, only report what would be pruned
    
    Returns:
        Pruning statistics dict
    """
    data = load_fabric()
    neurons = data.get("neurons", {})
    synapses = data.get("synapses", {})
    
    now = time.time()
    cutoff = now - (max_age_days * 86400)
    
    stats = {
        "neurons_before": len(neurons),
        "synapses_before": len(synapses),
        "pruned_dead": 0,
        "pruned_stale": 0,
        "pruned_weak_synapses": 0,
        "pruned_orphan_synapses": 0,
        "pruned_duplicate": 0,
    }
    
    # ── Phase 1: Identify dead neurons ──
    dead_ids = set()
    for nid, n in neurons.items():
        energy = n.get("energy", 0)
        act_count = n.get("activation_count", 0)
        
        if energy < 0.08 and act_count < min_activations:
            dead_ids.add(nid)
            stats["pruned_dead"] += 1
    
    # ── Phase 2: Identify stale neurons ──
    stale_ids = set()
    for nid, n in neurons.items():
        if nid in dead_ids:
            continue
        
        last_activated = n.get("last_activated", 0)
        energy = n.get("energy", 0)
        act_count = n.get("activation_count", 0)
        
        if last_activated < cutoff and energy < min_energy and act_count < 5:
            stale_ids.add(nid)
            stats["pruned_stale"] += 1
    
    # ── Phase 3: Identify duplicate monitoring neurons ──
    # Group by proposition prefix (first 50 chars)
    prop_groups = defaultdict(list)
    for nid, n in neurons.items():
        if nid in dead_ids or nid in stale_ids:
            continue
        prop = n.get("proposition", "")[:50]
        prop_groups[prop].append((nid, n))
    
    dup_ids = set()
    for prop, group in prop_groups.items():
        if len(group) <= 1:
            continue
        # Keep the strongest, prune others
        group.sort(key=lambda x: (
            x[1].get("energy", 0) * x[1].get("activation_count", 0)
        ), reverse=True)
        for nid, n in group[1:]:  # Skip the strongest
            dup_ids.add(nid)
            stats["pruned_duplicate"] += 1
    
    remove_neuron_ids = dead_ids | stale_ids | dup_ids
    
    # ── Phase 4: Identify weak synapses ──
    weak_syn_ids = set()
    for sid, s in synapses.items():
        weight = abs(s.get("weight", 0))
        fire_count = s.get("fire_count", 0)
        
        if weight < min_synapse_weight and fire_count < 2:
            weak_syn_ids.add(sid)
            stats["pruned_weak_synapses"] += 1
    
    # ── Phase 5: Identify orphaned synapses ──
    remaining_neurons = set(neurons.keys()) - remove_neuron_ids
    orphan_syn_ids = set()
    for sid, s in synapses.items():
        if sid in weak_syn_ids:
            continue
        src = s.get("source_id", "")
        tgt = s.get("target_id", "")
        if src not in remaining_neurons or tgt not in remaining_neurons:
            orphan_syn_ids.add(sid)
            stats["pruned_orphan_synapses"] += 1
    
    remove_syn_ids = weak_syn_ids | orphan_syn_ids
    
    # ── Report ──
    total_pruned = len(remove_neuron_ids) + len(remove_syn_ids)
    stats["neurons_after"] = len(neurons) - len(remove_neuron_ids)
    stats["synapses_after"] = len(synapses) - len(remove_syn_ids)
    stats["total_pruned"] = total_pruned
    
    print(f"\n{'='*50}")
    print(f"🧹 NeuronFabric Pruning {'(DRY RUN)' if dry_run else ''}")
    print(f"{'='*50}")
    print(f"  Neurons: {stats['neurons_before']} → {stats['neurons_after']}")
    print(f"  Synapses: {stats['synapses_before']} → {stats['synapses_after']}")
    print(f"  Dead: {stats['pruned_dead']}")
    print(f"  Stale (>{max_age_days}d): {stats['pruned_stale']}")
    print(f"  Duplicate: {stats['pruned_duplicate']}")
    print(f"  Weak synapses: {stats['pruned_weak_synapses']}")
    print(f"  Orphaned synapses: {stats['pruned_orphan_synapses']}")
    print(f"  Total pruned: {total_pruned}")
    print(f"{'='*50}\n")
    
    if dry_run:
        return stats
    
    # ── Apply ──
    for nid in remove_neuron_ids:
        del neurons[nid]
    for sid in remove_syn_ids:
        del synapses[sid]
    
    data["neurons"] = neurons
    data["synapses"] = synapses
    
    save_fabric(data, backup=True)
    
    logger.info(f"🧹 Pruned {total_pruned} items ({len(remove_neuron_ids)} neurons, {len(remove_syn_ids)} synapses)")
    
    return stats


def auto_prune_if_needed(max_neurons: int = 3000, max_synapses: int = 20000) -> dict:
    """
    Auto-prune if fabric is too large.
    Called by evolution pipeline.
    """
    try:
        data = load_fabric()
        n_neurons = len(data.get("neurons", {}))
        n_synapses = len(data.get("synapses", {}))
        
        if n_neurons < max_neurons and n_synapses < max_synapses:
            return {"skipped": True, "neurons": n_neurons, "synapses": n_synapses}
        
        logger.info(
            f"🧹 Auto-pruning: {n_neurons} neurons, {n_synapses} synapses "
            f"(limits: {max_neurons}/{max_synapses})"
        )
        return prune(max_age_days=5.0, min_energy=0.15, dry_run=False)
        
    except Exception as e:
        logger.warning(f"Auto-prune failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NOOGH NeuronFabric Pruner")
    parser.add_argument("--dry-run", action="store_true", help="Only report, don't prune")
    parser.add_argument("--max-age", type=float, default=7.0, help="Max days since last activation")
    parser.add_argument("--min-energy", type=float, default=0.1, help="Min energy to keep")
    parser.add_argument("--aggressive", action="store_true", help="Aggressive pruning (3 days, 0.15 energy)")
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.aggressive:
        result = prune(max_age_days=3.0, min_energy=0.15, dry_run=args.dry_run)
    else:
        result = prune(max_age_days=args.max_age, min_energy=args.min_energy, dry_run=args.dry_run)
