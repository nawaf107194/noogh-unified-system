# 🎯 START HERE - Quick Launch Guide

## ⚡ Run Paper Trading (30 Seconds)

### Option 1: Simple Command
```bash
cd /home/noogh/projects/noogh_unified_system
python3 -m src.trading.start_paper_trading
```

Press `Ctrl+C` to stop.

### Option 2: Background (Recommended)
```bash
cd /home/noogh/projects/noogh_unified_system
nohup python3 -m src.trading.start_paper_trading > paper_trading.log 2>&1 &
```

Monitor with:
```bash
tail -f paper_trading.log
```

Stop with:
```bash
pkill -f start_paper_trading
```

---

## 📊 What It Does

The bot will:
1. ✅ Check BTCUSDT every 5 minutes
2. ✅ Detect liquidity trap signals
3. ✅ Execute paper trades (no real money)
4. ✅ Monitor positions (hybrid exits)
5. ✅ Log everything to `paper_trading.log`

**Expected:**
- 2-3 signals per day
- Win rate: 65%
- Profit factor: 1.12

---

## 🎯 Customize Settings

Edit `start_paper_trading.py`:

```python
# Add more symbols
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

# Change risk
trader = TrapLiveTrader(
    risk_per_trade=0.005,  # 0.5% risk
    initial_capital=5_000.0  # $5k capital
)

# Change interval
time.sleep(600)  # 10 minutes
```

---

## 📖 Full Documentation

- **[README_TRAP_STRATEGY.md](README_TRAP_STRATEGY.md)** - Quick start
- **[PRODUCTION_READY.md](PRODUCTION_READY.md)** - Complete guide
- **[test_live_trader.py](test_live_trader.py)** - Run tests

---

## ⚠️ Before Going Live

1. ✅ Paper trade 1-2 weeks
2. ✅ Verify win rate ~65%
3. ✅ Verify profit factor >1.0
4. ✅ Check drawdown <25%
5. ✅ Start live with $1k-$5k
6. ✅ Use 0.5% risk initially

---

## 🆘 Troubleshooting

### No signals?
- Normal! 2-3 per day average
- Check BTC volume >$1B/day
- Wait patiently

### Tests failing?
```bash
python3 -m src.trading.test_live_trader
```

### Need help?
- Check logs: `paper_trading.log`
- Read: [PRODUCTION_READY.md](PRODUCTION_READY.md)
- Review: [BUGS_FOUND.md](BUGS_FOUND.md)

---

## 🎉 You're Ready!

**Next:** Let it run for 1 week and monitor results.

**Expected (1 week):**
- Signals: 14-21
- Win rate: 60-70%
- PNL: +$100-150 (on $10k)

Good luck! 🚀
