# 🧠 Noogh Unified System - System Status & Guide

## 📊 Current System State (March 8, 2026, 8:46 PM)

### ✅ **Active Components**

| Component | PID | Status | Function |
|-----------|-----|--------|----------|
| **autonomous_learner** | 1198527 | ✅ Running | GitHub + HN + Reddit learning |
| **continuous_training** | 1380724 | ✅ Running | Performance analysis + optimization |
| **neuron_integration** | 1629318 | ✅ Running | Connect neurons to trading |
| **integrated_learning** | 2032669 | ✅ Running | Overall coordination |

### 💾 **Data Stats**

- **Total Beliefs**: 14,005
- **Total Neurons**: 9,942
- **Active Neurons** (>0.5 energy): 9,939 (99.97%)
- **Last Learning Cycle**: 20:44 (24 items in 16.2s)

---

## 🚀 Quick Commands

### **Monitor System**

```bash
cd /home/noogh/projects/noogh_unified_system/src

# New: Advanced Brain Monitor
python3 agents/advanced_brain.py --status   # System overview
python3 agents/advanced_brain.py --analyze  # Performance analysis
python3 agents/advanced_brain.py --health   # Health check

# Or all at once (default)
python3 agents/advanced_brain.py
```

### **Monitor Individual Agents**

```bash
# Autonomous Learner (GitHub, HN, Reddit)
tail -f logs/autonomous_learner.log

# Continuous Training
tail -f logs/continuous_training.log

# Neuron Integration
tail -f logs/neuron_integration.log

# Orchestrator
tail -f logs/orchestrator.log
```

### **Check Processes**

```bash
# List all agents
ps aux | grep -E "autonomous_learner|continuous_training|neuron_integration|integrated_learning" | grep -v grep

# Stop an agent gracefully
kill -SIGINT <PID>

# Force stop
kill -9 <PID>
```

---

## 📊 System Architecture

```
🧠 Noogh Unified System
    ├─ 💾 Shared Memory (shared_memory.sqlite)
    │   ├─ Beliefs: 14,005
    │   ├─ Neurons: ~9,000
    │   ├─ Trades: data
    │   └─ Research: results
    │
    ├─ 🧠 Neuron Fabric
    │   ├─ Total: 9,942 neurons
    │   └─ Active: 9,939 (99.97%)
    │
    ├─ 🤖 Autonomous Learner Agent
    │   ├─ GitHub repos scanner
    │   ├─ HackerNews top stories
    │   ├─ Reddit threads
    │   └─ arXiv papers
    │
    ├─ 🔄 Continuous Training Loop
    │   ├─ Performance analysis
    │   ├─ Strategy optimization
    │   └─ Neuron refinement
    │
    ├─ 🔗 Neuron Integration Engine
    │   ├─ Connects neurons to trading
    │   ├─ Top-N selection
    │   └─ Real-time deployment
    │
    └─ 🎯 Integrated Learning System
        ├─ Coordinates all agents
        ├─ Brain orchestration
        └─ Feedback loops
```

---

## 🛠️ Configuration

### **Autonomous Learner**

Interval: 1800s (30 min)  
Sources: GitHub, HackerNews, Reddit, arXiv  
Last run: 20:44 - 24 items learned  

### **Continuous Training**

Interval: 1800s (30 min)  
Mode: Continuous  
Status: Running since 19:26  

### **Neuron Integration**

Mode: Continuous  
Top-N: 10 neurons  
Status: Running since 19:45  

### **Integrated Learning**

Interval: 1800s (30 min)  
Brain Cycle: Every 3 iterations  
Status: Running since 20:14  

---

## 🐛 Troubleshooting

### **Problem: Agent Not Running**

```bash
# Check logs for errors
tail -50 logs/<agent_name>.log

# Restart agent
cd /home/noogh/projects/noogh_unified_system/src
python3 agents/<agent_name>.py --continuous --interval 1800 &
```

### **Problem: Database Locked**

```bash
# Find process using database
fuser src/data/shared_memory.sqlite

# Kill if needed
kill <PID>
```

### **Problem: Low Memory**

```bash
# Check memory usage
free -h

# Check agent memory
ps aux --sort=-%mem | head -10

# Restart heavy agents if needed
```

### **Problem: Slow Performance**

```bash
# Check CPU
top

# Reduce interval if needed (edit agent startup)
--interval 3600  # Change from 1800 to 3600 (1 hour)
```

---

## 📊 Database Queries

```bash
sqlite3 /home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite
```

### **Useful Queries**

```sql
-- Total beliefs
SELECT COUNT(*) FROM beliefs;

-- Neurons
SELECT COUNT(*) FROM beliefs WHERE key LIKE 'neuron:%';

-- Top utility beliefs
SELECT key, utility_score 
FROM beliefs 
WHERE utility_score > 0 
ORDER BY utility_score DESC 
LIMIT 10;

-- Recent research
SELECT key, updated_at 
FROM beliefs 
WHERE key LIKE 'research:%' 
ORDER BY updated_at DESC 
LIMIT 5;

-- Trades data
SELECT key, json_extract(value, '$.pnl') as pnl
FROM beliefs 
WHERE key LIKE 'trade:%'
ORDER BY updated_at DESC 
LIMIT 10;
```

---

## 🚀 Deployment Guide

### **Fresh Start (All Agents)**

```bash
cd /home/noogh/projects/noogh_unified_system/src

# 1. Start Autonomous Learner
nohup python3 agents/autonomous_learner_agent.py --interval 1800 > logs/autonomous_learner.log 2>&1 &
echo $! > /home/noogh/.noogh/autonomous_learner.pid

# 2. Start Continuous Training
nohup python3 agents/continuous_training_loop_v2.py --continuous --interval 1800 > logs/continuous_training.log 2>&1 &
echo $! > /home/noogh/.noogh/continuous_training.pid

# 3. Start Neuron Integration
nohup python3 agents/neuron_integration_engine.py --continuous --top-n 10 > logs/neuron_integration.log 2>&1 &
echo $! > /home/noogh/.noogh/neuron_integration.pid

# 4. Start Integrated Learning
nohup python3 agents/integrated_learning_system.py --interval 1800 --brain-every 3 > logs/integrated_learning.log 2>&1 &
echo $! > /home/noogh/.noogh/integrated_learning.pid

echo "✅ All agents started!"
```

### **Stop All Agents**

```bash
# Graceful stop
for pid_file in /home/noogh/.noogh/*.pid; do
    [ -f "$pid_file" ] && kill -SIGINT $(cat "$pid_file")
done

# Or force stop
pkill -f "autonomous_learner\|continuous_training\|neuron_integration\|integrated_learning"
```

---

## 📊 Performance Metrics

### **Current Performance (March 8, 2026)**

- **Learning Rate**: 24 items / 16.2s = 1.48 items/sec
- **Neuron Activation**: 99.97% active
- **System Uptime**: Multiple hours
- **Memory Usage**: Normal

### **Benchmarks**

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Beliefs | >10,000 | 14,005 | ✅ |
| Active Neurons | >80% | 99.97% | ✅ |
| Learning Cycle | <30s | 16.2s | ✅ |
| Agents Running | 4 | 4 | ✅ |

---

## 🔐 Security

### **Current Security Measures**

✅ **TaskBudget** - Resource limits enforced  
✅ **Output Sanitization** - Dangerous patterns blocked  
✅ **SafeMath** - AST-based evaluation  
✅ **Restricted Builtins** - No eval/exec/open  
✅ **Rate Limiting** - Redis-based (20 calls/min)  

### **File Permissions**

```bash
# Check critical files
ls -la src/data/shared_memory.sqlite
ls -la src/agents/*.py

# Should be owned by noogh:noogh with 644/755
```

---

## 📚 Next Steps

### **Phase 1: Monitoring (Current)**
- ✅ All agents running
- ✅ Data collection active
- 🔄 Monitor with `advanced_brain.py`

### **Phase 2: Optimization (Next Week)**
- 🔄 Analyze performance patterns
- 🔄 Tune learning intervals
- 🔄 Optimize neuron selection

### **Phase 3: Integration (Next Month)**
- 🔄 Connect to trading strategy
- 🔄 Goal-driven learning
- 🔄 Causal reasoning

---

## 📦 Useful Scripts

### **Monitor Script**

```bash
#!/bin/bash
# monitor.sh - Quick system overview

echo "=== Agent Status ==="
ps aux | grep -E "autonomous_learner|continuous_training|neuron_integration|integrated_learning" | grep -v grep

echo -e "\n=== Database Stats ==="
sqlite3 src/data/shared_memory.sqlite "SELECT COUNT(*) as beliefs FROM beliefs; SELECT COUNT(*) as neurons FROM beliefs WHERE key LIKE 'neuron:%';"

echo -e "\n=== Recent Logs ==="
tail -5 logs/autonomous_learner.log
```

### **Health Check Script**

```bash
#!/bin/bash
# health.sh - System health check

cd /home/noogh/projects/noogh_unified_system/src
python3 agents/advanced_brain.py --health
```

---

## ✨ Summary

✅ **System is HEALTHY and OPERATIONAL**  
✅ **4 agents running continuously**  
✅ **14,005 beliefs accumulated**  
✅ **9,942 neurons active (99.97%)**  
✅ **Learning cycle: 16.2s per 24 items**  

🎉 **Everything is working perfectly!**

---

**Last Updated**: March 8, 2026, 8:46 PM +03  
**System Version**: Unified v2.2  
**Status**: 🟢 Operational
