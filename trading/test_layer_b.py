import json
from layer_b_filter import statistical_alpha_filter

def test_on_setups():
    filepath = "/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl"
    
    total_trades = 0
    passed_trades = 0
    
    wins = 0
    losses = 0
    
    win_pnl = 0.0
    loss_pnl = 0.0
    
    with open(filepath, "r") as f:
        for line in f:
            if not line.strip(): continue
            setup = json.loads(line)
            total_trades += 1
            
            # Apply Layer B
            is_valid, prob, reason = statistical_alpha_filter(setup)
            if not is_valid:
                continue
                
            passed_trades += 1
            
            # Reconstruct exact PnL used in testing
            if setup['outcome'] == 'WIN':
                wins += 1
                pnl = abs(setup['take_profit'] - setup['entry_price']) / setup['entry_price'] * 100
                win_pnl += pnl
            else:
                losses += 1
                pnl = abs(setup['entry_price'] - setup['stop_loss']) / setup['entry_price'] * 100
                loss_pnl += pnl
                
    wr = (wins / passed_trades * 100) if passed_trades > 0 else 0
    pf = (win_pnl / loss_pnl) if loss_pnl > 0 else 0
    
    print(f"Total Base Setups: {total_trades}")
    print(f"Passed Layer B:    {passed_trades} ({(passed_trades/total_trades*100):.1f}%)")
    print(f"Win Rate:          {wr:.1f}%")
    print(f"Profit Factor:     {pf:.2f}")

if __name__ == "__main__":
    test_on_setups()
