import asyncio
from pathlib import Path
import json

from run_evolution_loop import load_neuron_func
from trading.layer_b_filter import statistical_alpha_filter

async def evaluate_elite():
    brain_dir = Path("/home/noogh/projects/noogh_unified_system/src/neurons")
    
    long_func = load_neuron_func(brain_dir / "long_filter_20260228_150320_6710c82420e1.py", "long_filter")
    short_func = load_neuron_func(brain_dir / "short_filter_20260228_150320_966f5acb6b4e.py", "short_filter")
    
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
            lines = [line for line in f if line.strip()]
            
            # 70/30 split for A and B
            split_idx_1 = int(len(lines) * 0.7)
            # 30/30/40 split for A, B and C (to simulate C) if requested, but let's just do A, B and ALL 
            # and another file for C if it exists. For now, we will just use A and B from the current setups
            # and ALL.
            
            if split_mode == "A":
                lines_to_use = lines[:split_idx_1]
            elif split_mode == "B":
                lines_to_use = lines[split_idx_1:]
            elif split_mode == "ALL":
                lines_to_use = lines
                
            for line in lines_to_use:
                setup = json.loads(line)
                
                # ok_b, prob_b, _ = statistical_alpha_filter(setup)
                # if not ok_b: continue
                
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
            "window": split_mode,
            "mode": eval_mode,
            "n_trades": n_trades,
            "win_rate": wr * 100, 
            "profit_factor": pf,
            "max_drawdown": max_dd * 100,
            "pnl": equity - 10000.0
        }

    with concurrent.futures.ThreadPoolExecutor() as pool:
        res_P_A = await loop.run_in_executor(pool, run_eval, "A", "PAIR")
        res_P_B = await loop.run_in_executor(pool, run_eval, "B", "PAIR")
        res_P_ALL = await loop.run_in_executor(pool, run_eval, "ALL", "PAIR")
        
    print(f"Window A:")
    print(json.dumps(res_P_A, indent=2))
    print(f"\nWindow B:")
    print(json.dumps(res_P_B, indent=2))
    print(f"\nWindow ALL:")
    print(json.dumps(res_P_ALL, indent=2))

if __name__ == "__main__":
    asyncio.run(evaluate_elite())
