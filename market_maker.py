#!/usr/bin/env python3
"""
NOOGH Market Making Simulator
================================
Jane Street-style market making engine for crypto futures.

Features:
- Avellaneda-Stoikov spread model with volatility-adjusted quoting
- Inventory management with skew-based quote adjustment
- Adverse selection detection
- PnL decomposition (spread capture vs directional vs hedging)
- Risk limits and automatic shutdown

Usage:
    python3 market_maker.py --symbol BTCUSDT --days 30 --capital 1000
"""

import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import numpy as np
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')


# ═══════════════════════════════════════════════════════════════
# Section 1: Mathematical Models
# ═══════════════════════════════════════════════════════════════

class AvellanedaStoikov:
    """
    Avellaneda-Stoikov optimal market making model.
    
    The reservation price and optimal spread are:
        r(s,q,t) = s - q × γ × σ² × (T-t)
        δ* = γ × σ² × (T-t) + (2/γ) × ln(1 + γ/k)
    
    Where:
        s = mid price
        q = current inventory  
        γ = risk aversion parameter
        σ = volatility
        T-t = time remaining
        k = order arrival intensity
    """
    
    def __init__(self, gamma: float = 0.1, k: float = 1.5, T: float = 1.0):
        self.gamma = gamma  # Risk aversion (higher = wider spreads)
        self.k = k          # Order arrival intensity
        self.T = T          # Trading session length
    
    def reservation_price(self, mid: float, inventory: float,
                           sigma: float, time_remaining: float) -> float:
        """
        Optimal price to quote around, given inventory risk.
        Skews AWAY from inventory:
          - Long inventory → lower reservation → more aggressive sells
          - Short inventory → higher reservation → more aggressive buys
        """
        return mid - inventory * self.gamma * sigma**2 * time_remaining
    
    def optimal_spread(self, sigma: float, time_remaining: float) -> float:
        """Optimal bid-ask spread width."""
        return (self.gamma * sigma**2 * time_remaining + 
                (2 / self.gamma) * np.log(1 + self.gamma / self.k))
    
    def get_quotes(self, mid: float, inventory: float,
                   sigma: float, time_remaining: float) -> Tuple[float, float]:
        """
        Returns (bid_price, ask_price).
        
        The core market making algorithm:
        1. Calculate reservation price (skewed by inventory)
        2. Calculate optimal spread
        3. Center spread around reservation price
        """
        r = self.reservation_price(mid, inventory, sigma, time_remaining)
        delta = self.optimal_spread(sigma, time_remaining)
        
        bid = r - delta / 2
        ask = r + delta / 2
        
        return round(bid, 8), round(ask, 8)


# ═══════════════════════════════════════════════════════════════
# Section 2: Inventory Manager
# ═══════════════════════════════════════════════════════════════

@dataclass
class InventoryState:
    position: float = 0.0          # Current inventory (+ = long, - = short)
    max_position: float = 10.0     # Max allowed inventory
    avg_entry: float = 0.0         # Average entry price
    total_bought: float = 0.0
    total_sold: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    @property
    def utilization(self) -> float:
        """Inventory utilization: 0 = neutral, 1 = max."""
        return abs(self.position) / self.max_position if self.max_position > 0 else 0
    
    def update_buy(self, price: float, qty: float):
        """Record a buy fill."""
        if self.position >= 0:
            # Adding to long or opening long
            total_cost = self.avg_entry * self.position + price * qty
            self.position += qty
            self.avg_entry = total_cost / self.position if self.position > 0 else price
        else:
            # Closing short
            pnl = (self.avg_entry - price) * min(qty, abs(self.position))
            self.realized_pnl += pnl
            self.position += qty
            if self.position > 0:
                self.avg_entry = price
        self.total_bought += qty
    
    def update_sell(self, price: float, qty: float):
        """Record a sell fill."""
        if self.position <= 0:
            # Adding to short or opening short
            total_cost = self.avg_entry * abs(self.position) + price * qty
            self.position -= qty
            self.avg_entry = total_cost / abs(self.position) if self.position < 0 else price
        else:
            # Closing long
            pnl = (price - self.avg_entry) * min(qty, self.position)
            self.realized_pnl += pnl
            self.position -= qty
            if self.position < 0:
                self.avg_entry = price
        self.total_sold += qty
    
    def mark_to_market(self, current_price: float):
        """Calculate unrealized P&L."""
        if self.position > 0:
            self.unrealized_pnl = (current_price - self.avg_entry) * self.position
        elif self.position < 0:
            self.unrealized_pnl = (self.avg_entry - current_price) * abs(self.position)
        else:
            self.unrealized_pnl = 0


# ═══════════════════════════════════════════════════════════════
# Section 3: Adverse Selection Detector
# ═══════════════════════════════════════════════════════════════

class AdverseSelectionDetector:
    """
    Detect when informed traders are picking off quotes.
    Key metric: ratio of fills that immediately move against us.
    """
    
    def __init__(self, window: int = 20, threshold: float = 0.6):
        self.window = window
        self.threshold = threshold
        self.fill_outcomes: List[bool] = []  # True = adverse
    
    def record_fill(self, direction: str, fill_price: float, 
                     price_after_3bars: float):
        """Record whether a fill was adversely selected."""
        if direction == 'BUY':
            adverse = price_after_3bars < fill_price  # Bought, price fell
        else:
            adverse = price_after_3bars > fill_price  # Sold, price rose
        self.fill_outcomes.append(adverse)
    
    @property
    def adverse_ratio(self) -> float:
        """Fraction of recent fills that were adversely selected."""
        recent = self.fill_outcomes[-self.window:]
        return sum(recent) / len(recent) if recent else 0
    
    @property
    def is_toxic(self) -> bool:
        """Should we widen spreads or stop quoting?"""
        return self.adverse_ratio > self.threshold


# ═══════════════════════════════════════════════════════════════
# Section 4: Risk Manager
# ═══════════════════════════════════════════════════════════════

@dataclass  
class RiskLimits:
    max_inventory: float = 10.0       # Max position size
    max_daily_loss: float = -50.0     # USD
    max_drawdown_pct: float = 5.0     # % of capital
    max_spread_multiple: float = 5.0  # Max spread vs normal
    emergency_flatten_pct: float = 3.0  # Flatten if >3% loss
    
class RiskManager:
    """Enforce risk limits and trigger shutdown."""
    
    def __init__(self, limits: RiskLimits, capital: float):
        self.limits = limits
        self.capital = capital
        self.peak_pnl = 0
        self.halted = False
        self.halt_reason = ""
    
    def check(self, inventory: InventoryState) -> bool:
        """Returns True if trading should continue, False to halt."""
        total_pnl = inventory.realized_pnl + inventory.unrealized_pnl
        
        # Update peak for drawdown calc
        self.peak_pnl = max(self.peak_pnl, total_pnl)
        
        # Check daily loss
        if total_pnl < self.limits.max_daily_loss:
            self.halted = True
            self.halt_reason = f"Max daily loss: ${total_pnl:.2f}"
            return False
        
        # Check drawdown
        dd = (self.peak_pnl - total_pnl) / self.capital * 100
        if dd > self.limits.max_drawdown_pct:
            self.halted = True
            self.halt_reason = f"Max drawdown: {dd:.1f}%"
            return False
        
        # Check inventory
        if abs(inventory.position) > self.limits.max_inventory:
            self.halt_reason = f"Inventory breach: {inventory.position}"
            # Don't halt, but signal to flatten
        
        return True


# ═══════════════════════════════════════════════════════════════
# Section 5: PnL Decomposition
# ═══════════════════════════════════════════════════════════════

@dataclass
class PnLDecomposition:
    """Separate profit sources."""
    spread_capture: float = 0.0      # Profit from bid-ask spread
    directional_pnl: float = 0.0     # Profit from inventory position changes
    hedging_cost: float = 0.0        # Cost of hedging/flattening
    commission_cost: float = 0.0     # Trading fees
    
    @property
    def total(self) -> float:
        return self.spread_capture + self.directional_pnl - self.hedging_cost - self.commission_cost
    
    def summary(self) -> str:
        return (f"Spread: ${self.spread_capture:.2f} | Dir: ${self.directional_pnl:.2f} | "
                f"Hedge: -${self.hedging_cost:.2f} | Comm: -${self.commission_cost:.2f} | "
                f"TOTAL: ${self.total:.2f}")


# ═══════════════════════════════════════════════════════════════
# Section 6: Market Making Simulator
# ═══════════════════════════════════════════════════════════════

@dataclass
class MMResult:
    total_pnl: float
    spread_captured: float
    directional_pnl: float
    hedging_cost: float
    commission_cost: float
    total_fills: int
    buy_fills: int
    sell_fills: int
    avg_spread_bps: float
    inventory_utilization: float
    adverse_selection_rate: float
    sharpe: float
    max_drawdown: float
    fill_rate: float
    halted: bool
    halt_reason: str


class MarketMakingSimulator:
    """
    Event-driven market making simulation on historical klines.
    """
    
    def __init__(self, capital: float = 1000, gamma: float = 0.1,
                 trade_size: float = 0.001, commission: float = 0.0004):
        self.capital = capital
        self.model = AvellanedaStoikov(gamma=gamma)
        self.trade_size = trade_size  # Base qty per fill (in BTC etc)
        self.commission = commission  # 0.04% per side
        
    def run(self, klines: List[Dict], symbol: str = "BTCUSDT") -> MMResult:
        """Run market making simulation."""
        
        inventory = InventoryState(max_position=self.trade_size * 20)
        risk_mgr = RiskManager(
            RiskLimits(max_inventory=self.trade_size * 20, max_daily_loss=-self.capital * 0.05),
            self.capital
        )
        adverse = AdverseSelectionDetector()
        pnl_decomp = PnLDecomposition()
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        # Compute rolling volatility (20-period)
        pnl_curve = [0.0]
        total_fills = 0
        buy_fills = 0
        sell_fills = 0
        quotes_placed = 0
        spreads = []
        
        for i in range(20, len(klines)):
            if risk_mgr.halted:
                break
            
            mid = closes[i]
            
            # Rolling volatility (annualized from returns)
            window_closes = closes[max(0, i-20):i+1]
            if len(window_closes) > 1:
                returns = np.diff(window_closes) / window_closes[:-1]
                sigma = np.std(returns) * np.sqrt(365 * 24) if len(returns) > 1 else 0.5
            else:
                sigma = 0.5
            sigma = max(sigma, 0.01)  # Floor
            
            time_remaining = max(0.01, (len(klines) - i) / len(klines))
            
            # Get optimal quotes
            bid, ask = self.model.get_quotes(mid, inventory.position / self.trade_size,
                                              sigma, time_remaining)
            
            # Widen spread if adverse selection detected
            if adverse.is_toxic:
                spread = ask - bid
                bid -= spread * 0.5
                ask += spread * 0.5
            
            spread_bps = (ask - bid) / mid * 10000
            spreads.append(spread_bps)
            quotes_placed += 1
            
            # Simulate fills: check if bar's price range hits our quotes
            bar_low = lows[i]
            bar_high = highs[i]
            
            bid_filled = bar_low <= bid
            ask_filled = bar_high >= ask
            
            # Enforce max inventory
            if inventory.position >= inventory.max_position:
                bid_filled = False  # Don't buy more
            if inventory.position <= -inventory.max_position:
                ask_filled = False  # Don't sell more
            
            if bid_filled:
                inventory.update_buy(bid, self.trade_size)
                pnl_decomp.spread_capture += (mid - bid) * self.trade_size
                pnl_decomp.commission_cost += bid * self.trade_size * self.commission
                buy_fills += 1
                total_fills += 1
                
                # Adverse selection check
                if i + 3 < len(klines):
                    adverse.record_fill('BUY', bid, closes[i + 3])
            
            if ask_filled:
                inventory.update_sell(ask, self.trade_size)
                pnl_decomp.spread_capture += (ask - mid) * self.trade_size
                pnl_decomp.commission_cost += ask * self.trade_size * self.commission
                sell_fills += 1
                total_fills += 1
                
                if i + 3 < len(klines):
                    adverse.record_fill('SELL', ask, closes[i + 3])
            
            # Inventory hedging: if position too large, flatten partially
            if abs(inventory.position) > inventory.max_position * 0.8:
                hedge_qty = abs(inventory.position) * 0.3
                hedge_price = mid  # Market order to flatten
                hedge_cost = hedge_price * hedge_qty * self.commission * 2  # Round trip cost
                
                if inventory.position > 0:
                    inventory.update_sell(hedge_price, hedge_qty)
                    pnl_decomp.hedging_cost += hedge_cost
                else:
                    inventory.update_buy(hedge_price, hedge_qty)
                    pnl_decomp.hedging_cost += hedge_cost
            
            # Mark to market
            inventory.mark_to_market(mid)
            pnl_decomp.directional_pnl = inventory.unrealized_pnl
            
            current_pnl = inventory.realized_pnl + inventory.unrealized_pnl - pnl_decomp.commission_cost
            pnl_curve.append(current_pnl)
            
            # Risk check
            risk_mgr.check(inventory)
        
        # Final flatten
        if inventory.position != 0:
            final_price = closes[-1]
            if inventory.position > 0:
                inventory.update_sell(final_price, abs(inventory.position))
            else:
                inventory.update_buy(final_price, abs(inventory.position))
            pnl_decomp.commission_cost += final_price * abs(inventory.position) * self.commission
        
        # Compute metrics
        pnl_arr = np.array(pnl_curve)
        peak = np.maximum.accumulate(pnl_arr)
        drawdowns = peak - pnl_arr
        max_dd = np.max(drawdowns)
        
        returns = np.diff(pnl_arr)
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(365 * 24) if np.std(returns) > 0 else 0
        
        fill_rate = total_fills / (quotes_placed * 2) * 100 if quotes_placed > 0 else 0
        
        return MMResult(
            total_pnl=round(pnl_decomp.total, 2),
            spread_captured=round(pnl_decomp.spread_capture, 2),
            directional_pnl=round(inventory.realized_pnl, 2),
            hedging_cost=round(pnl_decomp.hedging_cost, 2),
            commission_cost=round(pnl_decomp.commission_cost, 2),
            total_fills=total_fills,
            buy_fills=buy_fills,
            sell_fills=sell_fills,
            avg_spread_bps=round(np.mean(spreads), 1) if spreads else 0,
            inventory_utilization=round(inventory.utilization * 100, 1),
            adverse_selection_rate=round(adverse.adverse_ratio * 100, 1),
            sharpe=round(sharpe, 2),
            max_drawdown=round(max_dd, 2),
            fill_rate=round(fill_rate, 1),
            halted=risk_mgr.halted,
            halt_reason=risk_mgr.halt_reason,
        )


# ═══════════════════════════════════════════════════════════════
# Section 7: Report
# ═══════════════════════════════════════════════════════════════

def generate_report(result: MMResult, symbol: str, days: int, capital: float):
    print("\n" + "=" * 70)
    print(f"  NOOGH MARKET MAKING SIMULATION — {symbol}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | {days} days | Capital: ${capital:,.0f}")
    print("=" * 70)
    
    print(f"\n💰 PnL DECOMPOSITION")
    print(f"  {'Spread Capture:':<25} ${result.spread_captured:>10,.2f}")
    print(f"  {'Directional P&L:':<25} ${result.directional_pnl:>10,.2f}")
    print(f"  {'Hedging Cost:':<25} -${result.hedging_cost:>9,.2f}")
    print(f"  {'Commission Cost:':<25} -${result.commission_cost:>9,.2f}")
    print(f"  {'─'*45}")
    print(f"  {'TOTAL P&L:':<25} ${result.total_pnl:>10,.2f}")
    print(f"  {'ROI:':<25} {result.total_pnl/capital*100:>9.2f}%")
    
    print(f"\n📊 EXECUTION METRICS")
    print(f"  {'Total Fills:':<25} {result.total_fills:>10}")
    print(f"  {'Buy Fills:':<25} {result.buy_fills:>10}")
    print(f"  {'Sell Fills:':<25} {result.sell_fills:>10}")
    print(f"  {'Fill Rate:':<25} {result.fill_rate:>9.1f}%")
    print(f"  {'Avg Spread:':<25} {result.avg_spread_bps:>9.1f} bps")
    
    print(f"\n🛡️ RISK METRICS")
    print(f"  {'Sharpe Ratio:':<25} {result.sharpe:>10.2f}")
    print(f"  {'Max Drawdown:':<25} ${result.max_drawdown:>9,.2f}")
    print(f"  {'Adverse Selection:':<25} {result.adverse_selection_rate:>9.1f}%")
    print(f"  {'Inventory Util:':<25} {result.inventory_utilization:>9.1f}%")
    print(f"  {'Halted:':<25} {'YES: ' + result.halt_reason if result.halted else 'No'}")
    
    # Verdict
    print(f"\n🎯 VERDICT:")
    if result.total_pnl > 0 and result.sharpe > 1:
        print(f"  🟢 PROFITABLE — Spread capture exceeds costs")
    elif result.total_pnl > 0:
        print(f"  🟡 MARGINAL — Profitable but low Sharpe")
    else:
        print(f"  🔴 UNPROFITABLE — Costs exceed spread capture")
    
    if result.adverse_selection_rate > 55:
        print(f"  ⚠️ HIGH ADVERSE SELECTION ({result.adverse_selection_rate:.0f}%) — informed traders dominating")
    
    print("\n" + "=" * 70)


# ═══════════════════════════════════════════════════════════════
# Section 8: Data & Main
# ═══════════════════════════════════════════════════════════════

def fetch_klines(symbol: str, interval: str = '1h', days: int = 30) -> List[Dict]:
    BASE = "https://api.binance.com/api/v3"
    start_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    end_ms = int(datetime.now().timestamp() * 1000)
    all_klines = []
    current = start_ms
    logger.info(f"📊 Downloading {symbol} {interval} ({days} days)...")
    while current < end_ms:
        resp = requests.get(f"{BASE}/klines", params={
            'symbol': symbol, 'interval': interval,
            'startTime': current, 'endTime': end_ms, 'limit': 1000
        }, timeout=10)
        if resp.status_code != 200: break
        data = resp.json()
        if not data: break
        for k in data:
            all_klines.append({
                'timestamp': k[0], 'open': float(k[1]), 'high': float(k[2]),
                'low': float(k[3]), 'close': float(k[4]), 'volume': float(k[5]),
            })
        current = data[-1][6] + 1
        time.sleep(0.1)
    logger.info(f"✅ {len(all_klines)} candles")
    return all_klines


def main():
    parser = argparse.ArgumentParser(description='NOOGH Market Making Simulator')
    parser.add_argument('--symbol', default='BTCUSDT')
    parser.add_argument('--interval', default='5m', help='Use 5m for MM simulation')
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--capital', type=float, default=1000)
    parser.add_argument('--gamma', type=float, default=0.1, help='Risk aversion')
    parser.add_argument('--trade-size', type=float, default=0.001, help='BTC per fill')
    args = parser.parse_args()
    
    klines = fetch_klines(args.symbol, args.interval, args.days)
    if len(klines) < 100:
        logger.error("❌ Insufficient data")
        return
    
    sim = MarketMakingSimulator(
        capital=args.capital, gamma=args.gamma, trade_size=args.trade_size
    )
    result = sim.run(klines, args.symbol)
    generate_report(result, args.symbol, args.days, args.capital)


if __name__ == '__main__':
    main()
