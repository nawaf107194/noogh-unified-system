#!/usr/bin/env python3
"""
Advanced Brain - الدماغ المتقدم
يدمج الوكلاء الموجودين: autonomous_learner, continuous_training, neuron_integration, integrated_learning

الاستخدام:
  python3 agents/advanced_brain.py --status    # عرض حالة النظام
  python3 agents/advanced_brain.py --analyze   # تحليل شامل
  python3 agents/advanced_brain.py --health    # فحص الصحة
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import sqlite3
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from unified_core.core.neuron_fabric import get_neuron_fabric
except ImportError:
    get_neuron_fabric = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

class AdvancedBrain:
    """يدمج ويراقب جميع مكونات النظام"""

    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'data' / 'shared_memory.sqlite'
        self.fabric = get_neuron_fabric() if get_neuron_fabric else None
        
    def get_system_status(self):
        """عرض حالة النظام الكاملة"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}🧠 NOOGH UNIFIED SYSTEM - STATUS{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        # 1. Shared Memory Stats
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM beliefs")
            total_beliefs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beliefs WHERE key LIKE 'neuron:%'")
            neuron_beliefs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beliefs WHERE key LIKE 'trade:%'")
            trade_beliefs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beliefs WHERE key LIKE 'research:%'")
            research_beliefs = cursor.fetchone()[0]
            
            print(f"{GREEN}📊 Shared Memory:{RESET}")
            print(f"   Total Beliefs: {total_beliefs:,}")
            print(f"   Neurons: {neuron_beliefs:,}")
            print(f"   Trades: {trade_beliefs:,}")
            print(f"   Research: {research_beliefs:,}")
            
            conn.close()
        except Exception as e:
            print(f"{RED}❌ Database Error: {e}{RESET}")
        
        # 2. Neuron Fabric Stats
        try:
            total_neurons = len(self.fabric._neurons)
            active_neurons = sum(1 for n in self.fabric._neurons.values() if n.energy > 0.5)
            
            print(f"\n{GREEN}🧠 Neuron Fabric:{RESET}")
            print(f"   Total Neurons: {total_neurons:,}")
            print(f"   Active (>0.5 energy): {active_neurons:,} ({active_neurons/total_neurons*100:.1f}%)")
        except Exception as e:
            print(f"{RED}❌ Fabric Error: {e}{RESET}")
        
        # 3. Active Agents
        import subprocess
        print(f"\n{GREEN}🤖 Active Agents:{RESET}")
        
        agents_to_check = [
            ('autonomous_learner', 'Autonomous Learner'),
            ('continuous_training', 'Continuous Training'),
            ('neuron_integration', 'Neuron Integration'),
            ('integrated_learning', 'Integrated Learning')
        ]
        
        for pattern, name in agents_to_check:
            result = subprocess.run(
                f"ps aux | grep {pattern} | grep -v grep | wc -l",
                shell=True, capture_output=True, text=True
            )
            count = int(result.stdout.strip())
            status = f"{GREEN}✅ Running{RESET}" if count > 0 else f"{RED}❌ Stopped{RESET}"
            print(f"   {name}: {status}")
        
        print(f"\n{BLUE}{'='*70}{RESET}\n")
    
    def analyze_performance(self):
        """تحليل أداء النظام"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}📈 PERFORMANCE ANALYSIS{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Top utility beliefs
            print(f"{GREEN}🏆 Top 10 High-Utility Beliefs:{RESET}")
            cursor.execute("""
                SELECT key, utility_score, updated_at 
                FROM beliefs 
                WHERE utility_score > 0
                ORDER BY utility_score DESC 
                LIMIT 10
            """)
            
            for i, (key, score, updated) in enumerate(cursor.fetchall(), 1):
                key_short = key[:50] + "..." if len(key) > 50 else key
                print(f"   {i}. {key_short}")
                print(f"      Score: {score:.3f} | Updated: {updated}")
            
            # Recent research
            print(f"\n{GREEN}🔍 Recent Research (Last 5):{RESET}")
            cursor.execute("""
                SELECT key, updated_at 
                FROM beliefs 
                WHERE key LIKE 'research:%'
                ORDER BY updated_at DESC 
                LIMIT 5
            """)
            
            for key, updated in cursor.fetchall():
                topic = key.replace('research:', '')[:60]
                print(f"   📚 {topic}")
                print(f"      Time: {updated}")
            
            # Neuron energy distribution
            print(f"\n{GREEN}⚡ Neuron Energy Distribution:{RESET}")
            
            energy_bins = {
                'Very High (>0.9)': 0,
                'High (0.7-0.9)': 0,
                'Medium (0.5-0.7)': 0,
                'Low (<0.5)': 0
            }
            
            for neuron in self.fabric._neurons.values():
                if neuron.energy > 0.9:
                    energy_bins['Very High (>0.9)'] += 1
                elif neuron.energy > 0.7:
                    energy_bins['High (0.7-0.9)'] += 1
                elif neuron.energy > 0.5:
                    energy_bins['Medium (0.5-0.7)'] += 1
                else:
                    energy_bins['Low (<0.5)'] += 1
            
            for bin_name, count in energy_bins.items():
                pct = count / len(self.fabric._neurons) * 100 if self.fabric._neurons else 0
                bar = '█' * int(pct / 2)
                print(f"   {bin_name:20s}: {bar} {count:,} ({pct:.1f}%)")
            
            conn.close()
            
        except Exception as e:
            print(f"{RED}❌ Analysis Error: {e}{RESET}")
        
        print(f"\n{BLUE}{'='*70}{RESET}\n")
    
    def health_check(self):
        """فحص صحة النظام"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}🏥 SYSTEM HEALTH CHECK{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        checks = []
        
        # 1. Database accessible
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            checks.append((True, "Database", "Accessible"))
        except:
            checks.append((False, "Database", "Connection failed"))
        
        # 2. Beliefs count
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM beliefs")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 1000:
                checks.append((True, "Beliefs Count", f"{count:,} entries"))
            else:
                checks.append((False, "Beliefs Count", f"Only {count} entries (low)"))
        except Exception as e:
            checks.append((False, "Beliefs Count", str(e)))
        
        # 3. Neuron Fabric
        try:
            total = len(self.fabric._neurons)
            active = sum(1 for n in self.fabric._neurons.values() if n.energy > 0.5)
            
            if total > 100 and active / total > 0.8:
                checks.append((True, "Neuron Fabric", f"{total:,} neurons, {active/total*100:.1f}% active"))
            else:
                checks.append((False, "Neuron Fabric", f"Low activity: {active}/{total}"))
        except Exception as e:
            checks.append((False, "Neuron Fabric", str(e)))
        
        # 4. Active agents
        import subprocess
        agents = ['autonomous_learner', 'continuous_training', 'neuron_integration']
        
        for agent in agents:
            result = subprocess.run(
                f"ps aux | grep {agent} | grep -v grep | wc -l",
                shell=True, capture_output=True, text=True
            )
            count = int(result.stdout.strip())
            
            if count > 0:
                checks.append((True, f"Agent: {agent}", "Running"))
            else:
                checks.append((False, f"Agent: {agent}", "Not running"))
        
        # Print results
        passed = sum(1 for status, _, _ in checks if status)
        total = len(checks)
        
        for status, component, message in checks:
            color = GREEN if status else RED
            icon = "✅" if status else "❌"
            print(f"{color}{icon} {component:30s}: {message}{RESET}")
        
        print(f"\n{BLUE}Overall Health: {passed}/{total} ({passed/total*100:.1f}%){RESET}")
        
        if passed / total >= 0.9:
            print(f"{GREEN}🎉 System is HEALTHY{RESET}")
        elif passed / total >= 0.7:
            print(f"{YELLOW}⚠️  System is OPERATIONAL with warnings{RESET}")
        else:
            print(f"{RED}🚨 System needs ATTENTION{RESET}")
        
        print(f"\n{BLUE}{'='*70}{RESET}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Brain - System Monitor')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--analyze', action='store_true', help='Analyze performance')
    parser.add_argument('--health', action='store_true', help='Health check')
    
    args = parser.parse_args()
    
    brain = AdvancedBrain()
    
    if args.status:
        brain.get_system_status()
    elif args.analyze:
        brain.analyze_performance()
    elif args.health:
        brain.health_check()
    else:
        # Default: show everything
        brain.get_system_status()
        brain.analyze_performance()
        brain.health_check()


if __name__ == '__main__':
    main()
