#!/usr/bin/env python3
import asyncio
from pathlib import Path
import os
import sys

# Add src to the path so modules work properly
sys.path.insert(0, str(Path(__file__).parent))

from trading.layer_b_filter import statistical_alpha_filter
from unified_core.runpod_brain import RunPodBrainEvolver, EvolutionConfig
from trading.backtesting_v2 import backtest_v2, BacktestConfig

from importlib.util import spec_from_file_location, module_from_spec
import pandas as pd
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

def load_neuron_func(neuron_path: Path, func_name: str):
    module_name = f"dyn_{neuron_path.stem}"
    spec = spec_from_file_location(module_name, str(neuron_path))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func_name)

async def evaluate_generation(brain: RunPodBrainEvolver, target_regime: str):
    manifest = brain._load_manifest()

    # Form pairs by created_utc
    from collections import defaultdict
    pairs = defaultdict(dict)
    for neuron in manifest.get("neurons", []):
        ts = neuron.get("created_utc")
        if neuron["name"] in {"long_filter", "short_filter"}:
            pairs[ts][neuron["name"]] = neuron

    fitness_updates = {}

    for ts, pair in pairs.items():
        if "long_filter" not in pair or "short_filter" not in pair:
            continue
            
        long_n = pair["long_filter"]
        short_n = pair["short_filter"]
        
        # Skip if already fully evaluated
        if long_n.get("pair_fitness") is not None and short_n.get("pair_fitness") is not None:
            continue
            
        try:
            long_func = load_neuron_func(brain.neurons_dir / long_n["file"], "long_filter")
            short_func = load_neuron_func(brain.neurons_dir / short_n["file"], "short_filter")
            
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            def run_eval(split_mode: str, eval_mode: str):
                wins, losses = 0, 0
                win_pnl, loss_pnl = 0.0, 0.0
                equity = 10000.0
                peak = equity
                max_dd = 0.0
                n_trades = 0
                
                with open("/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl", "r") as f:
                    lines = []
                    import json
                    for line in f:
                        if not line.strip(): continue
                        setup = json.loads(line)
                        if setup.get("vol_regime", "NORMAL") == target_regime:
                            lines.append(setup)
                            
                    split_idx = int(len(lines) * 0.7)
                    if split_mode == "A":
                        lines_to_use = lines[:split_idx]
                    else:
                        lines_to_use = lines[split_idx:]
                        
                    for setup in lines_to_use:
                        # Removed Layer B check to mirror user's evaluate_elite logic 
                        # where setups are pre-assumed as setups entering layer C. 
                        # Wait, we should still run it if evaluating raw data, but layer B is pre-filtered 
                        # in the loop below. So we keep it.
                        ok_b, prob_b, _ = statistical_alpha_filter(setup)
                        if not ok_b: continue
                        
                        if eval_mode == 'LONG' and setup['signal'] != 'LONG': continue
                        if eval_mode == 'SHORT' and setup['signal'] != 'SHORT': continue
                        
                        try:
                            if setup['signal'] == 'LONG':
                                ok_c, conf_c, _ = long_func(setup)
                            else:
                                ok_c, conf_c, _ = short_func(setup)
                            if not ok_c: continue
                        except Exception:
                            continue 
                            
                        n_trades += 1
                        
                        sl_dist = abs(setup['entry_price'] - setup['stop_loss']) / setup['entry_price']
                        if setup['outcome'] == 'WIN':
                            wins += 1
                            pnl_pct = abs(setup['take_profit'] - setup['entry_price']) / setup['entry_price']
                            win_pnl += pnl_pct * 100
                            r = pnl_pct / sl_dist if sl_dist > 0 else 1.0
                        else:
                            losses += 1
                            pnl_pct = -abs(setup['entry_price'] - setup['stop_loss']) / setup['entry_price']
                            loss_pnl += abs(pnl_pct * 100)
                            r = -1.0
                            
                        trade_pnl = equity * 0.01 * r
                        equity += trade_pnl
                        
                        if equity > peak: peak = equity
                        dd = (peak - equity) / peak
                        if dd > max_dd: max_dd = dd

                roi = (equity - 10000.0) / 10000.0
                wr = wins / n_trades if n_trades > 0 else 0.0
                pf = win_pnl / loss_pnl if loss_pnl > 0.0 else (99.0 if win_pnl > 0 else 0.0)
                
                return {
                    "stats": {
                        "n_trades": n_trades,
                        "win_rate": wr * 100, 
                        "profit_factor": pf,
                        "max_drawdown": max_dd * 100,
                        "roi": roi * 100,
                        "pnl": equity - 10000.0
                    }
                }

            with concurrent.futures.ThreadPoolExecutor() as pool:
                res_L_A = await asyncio.wait_for(loop.run_in_executor(pool, run_eval, "A", "LONG"), timeout=5.0)
                res_L_B = await asyncio.wait_for(loop.run_in_executor(pool, run_eval, "B", "LONG"), timeout=5.0)
                res_S_A = await asyncio.wait_for(loop.run_in_executor(pool, run_eval, "A", "SHORT"), timeout=5.0)
                res_S_B = await asyncio.wait_for(loop.run_in_executor(pool, run_eval, "B", "SHORT"), timeout=5.0)
                res_P_A = await asyncio.wait_for(loop.run_in_executor(pool, run_eval, "A", "PAIR"), timeout=5.0)
                res_P_B = await asyncio.wait_for(loop.run_in_executor(pool, run_eval, "B", "PAIR"), timeout=5.0)

            def calc_weighted_fit(r_A, r_B, min_t_A, min_t_B):
                st_A = r_A.get("stats", {})
                st_B = r_B.get("stats", {})
                f_A = brain.calculate_fitness(st_A, min_trades=min_t_A)
                f_B = brain.calculate_fitness(st_B, min_trades=min_t_B)
                return 0.7 * f_A + 0.3 * f_B

            # Lowered min_trades since we are evaluating within a smaller regime slice!
            fit_L = calc_weighted_fit(res_L_A, res_L_B, 3, 1)
            fit_S = calc_weighted_fit(res_S_A, res_S_B, 3, 1)
            fit_P = calc_weighted_fit(res_P_A, res_P_B, 5, 2)

            # CRITICAL FIX: Do not allow a failed filter to ride the success of its partner.
            if fit_L <= 0.0 or fit_S <= 0.0:
                fit_P = 0.0
                fit_L = 0.0
                fit_S = 0.0

            # Store updates
            fitness_updates[long_n["hash"]] = {"fitness": fit_L, "pair_fitness": fit_P, "pair_hash": short_n["hash"]}
            fitness_updates[short_n["hash"]] = {"fitness": fit_S, "pair_fitness": fit_P, "pair_hash": long_n["hash"]}

            print(f"🧬 Pair {long_n['hash'][:6]}+{short_n['hash'][:6]} | L={fit_L:.2f} S={fit_S:.2f} PAIR={fit_P:.2f}")

        except asyncio.TimeoutError:
            print(f"❌ Pair {long_n['hash'][:6]}+{short_n['hash'][:6]} | TIMEOUT (>5s)")
            fitness_updates[long_n["hash"]] = {"fitness": 0.0, "pair_fitness": 0.0}
            fitness_updates[short_n["hash"]] = {"fitness": 0.0, "pair_fitness": 0.0}
        except Exception as e:
            print(f"❌ Pair failed {long_n['hash'][:6]}+{short_n['hash'][:6]}: {e}")
            fitness_updates[long_n["hash"]] = {"fitness": 0.0, "pair_fitness": 0.0}
            fitness_updates[short_n["hash"]] = {"fitness": 0.0, "pair_fitness": 0.0}

    if fitness_updates:
        brain.update_fitness_detailed(fitness_updates)

async def main():
    print("🚀 Initializing Phase 3: Mixture-of-Regimes Evolution Loop...")
    
    # Prepare real historical data through Layer B
    import json
    filtered_historical_data = []
    with open("/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl", "r") as f:
        for line in f:
            if not line.strip(): continue
            setup = json.loads(line)
            # Must pass Layer B first
            ok_b, _, _ = statistical_alpha_filter(setup)
            if ok_b:
                filtered_historical_data.append(setup)
                
    vol_regimes = ["LOW", "NORMAL", "HIGH"]
    
    for current_regime in vol_regimes:
        print(f"\n🌍 =============================================")
        print(f"🌍 STARTING EVOLUTION FOR REGIME: {current_regime}")
        print(f"🌍 =============================================")
        
        manifest_path = f"/home/noogh/projects/noogh_unified_system/src/neurons_manifest_{current_regime}.json"
        if not Path(manifest_path).exists():
           with open(manifest_path, "w") as f: 
               json.dump({"neurons": [], "elite_pair": {}}, f)
               
        evo_config = EvolutionConfig(
            consensus_n=3,
            mutation_strength="medium", 
            keep_top_k=20, # reduced to speed up per-regime
            parents_k=4
        )
        
        brain = RunPodBrainEvolver(
            neurons_dir="/home/noogh/projects/noogh_unified_system/src/neurons",
            analysis_dir="/home/noogh/projects/noogh_unified_system/src/data/runpod_analysis",
            manifest_path=manifest_path,
            evo=evo_config
        )
        
        regime_historical_data = [d for d in filtered_historical_data if d.get("vol_regime") == current_regime]
        
        if len(regime_historical_data) < 20:
            print(f"⚠️ Skipping Regime {current_regime} due to insufficient setups for evolution ({len(regime_historical_data)}).")
            continue
            
        best_pair_fitness_history = []
        
        # We start from round 1 to 5 for each regime (fresh exploration in Phase 3)
        for round_num in range(1, 6):
            manifest = brain._load_manifest()
            current_elite_fit = manifest.get("elite_pair", {}).get("pair_fitness", 0.0)
            best_pair_fitness_history.append(current_elite_fit)
            
            if len(best_pair_fitness_history) >= 2 and best_pair_fitness_history[-1] > best_pair_fitness_history[-2]:
                mut = "low"
                print("🛡️ Dynamic Guard: Fitness improved. Lowering mutation to 'low'.")
            else:
                mut = "medium"

            new_evo = EvolutionConfig(
                consensus_n=brain.evo.consensus_n,
                keep_top_k=brain.evo.keep_top_k,
                parents_k=brain.evo.parents_k,
                children_per_round=brain.evo.children_per_round,
                min_fitness_to_keep=brain.evo.min_fitness_to_keep,
                mutation_strength=mut
            )
            brain.evo = new_evo

            print(f"\n=============================================")
            print(f"🔄 ROUND {round_num} (Regime: {current_regime} | Mutation: {brain.evo.mutation_strength})")
            print(f"=============================================")
            
            context_prompt = (
                f"Layer C Evolution Phase 3: Mixture-of-Regimes.\n"
                f"Target Regime: {current_regime} Volatility\n"
                f"Historical setups filtered specifically for this regime.\n"
                f"Maximize Pair Fitness. Focus on these new features available in `s` dict:\n"
                f"atr_pct, range_pct, vol_z, tbr_delta, rsi_slope, ema_fast_minus_slow, adx_14, ema_trend_dir, atr_1h_pct.\n"
                f"Also volume, taker_buy_ratio, and rsi are available. Build logical AND limits.\n"
            )
            
            out = await brain.evolve_round(
                historical_data=regime_historical_data, 
                context=context_prompt
            )
            
            print("\n⚔️ Evaluating Generation...")
            await evaluate_generation(brain, current_regime)

            print("🧹 Pruning...")
            brain.prune_manifest()

        final_manifest = brain._load_manifest()
        final_elite_fit = final_manifest.get("elite_pair", {}).get("pair_fitness", 0.0)
        print(f"\n🏁 Finished Regime {current_regime}. Final Elite Fitness: {final_elite_fit:.3f}")
        await brain.aclose()

    print("✅ Loop finished successfully for all Regimes.")

if __name__ == "__main__":
    asyncio.run(main())
