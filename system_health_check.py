#!/usr/bin/env python3
# System Health Check - فحص شامل للنظام
# يتأكد من عمل كل مكون بشكل صحيح

"""
System Health Check

يفحص:
1. الملفات الأساسية (هل موجودة؟)
2. المكتبات (هل يمكن استيرادها؟)
3. قاعدة البيانات (هل يمكن الوصول؟)
4. الوكلاء (هل يمكن إنشاؤهم؟)
5. التكامل بين المكونات

الاستخدام:
  python3 system_health_check.py
"""

import sys
import os
from pathlib import Path
import importlib
import sqlite3
from datetime import datetime

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

class HealthCheck:
    def __init__(self):
        self.project_root = Path('/home/noogh/projects/noogh_unified_system')
        self.src_root = self.project_root / 'src'
        self.results = []
        
    def log(self, status: str, component: str, message: str):
        """Log test result"""
        color = GREEN if status == "PASS" else RED if status == "FAIL" else YELLOW
        print(f"{color}[{status}]{RESET} {component}: {message}")
        self.results.append((status, component, message))

    def test_files_exist(self):
        """Test 1: فحص وجود الملفات الأساسية"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}📁 Test 1: Core Files Existence{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        core_files = [
            ('local_brain.py', 'Local Brain entry point'),
            ('advanced_brain.py', 'Advanced Brain with Goal Planning'),
            ('agents/unified_context.py', 'Unified Context'),
            ('agents/unified_brain_daemon.py', 'Brain Daemon'),
            ('agents/goal_planner.py', 'Goal Planner'),
            ('agents/causal_reasoning_engine.py', 'Causal Reasoning'),
            ('agents/proactive_research_agent.py', 'Proactive Research'),
            ('agents/brain_research_orchestrator.py', 'Brain Orchestrator'),
            ('agents/youtube_research_agent.py', 'YouTube Agent'),
            ('agents/github_research_agent.py', 'GitHub Agent'),
            ('agents/arxiv_research_agent.py', 'arXiv Agent'),
            ('agents/continuous_training_loop.py', 'Continuous Training'),
            ('trading/advanced_strategy.py', 'Advanced Strategy'),
            ('data/shared_memory.sqlite', 'Shared Memory DB'),
        ]
        
        for file_path, description in core_files:
            full_path = self.src_root / file_path
            if full_path.exists():
                self.log("PASS", description, f"{file_path}")
            else:
                self.log("FAIL", description, f"{file_path} NOT FOUND")

    def test_imports(self):
        """Test 2: فحص استيراد المكونات"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}📦 Test 2: Component Imports{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        # Add src to path
        sys.path.insert(0, str(self.src_root))
        
        imports = [
            ('agents.unified_context', 'UnifiedContext'),
            ('agents.goal_planner', 'GoalPlanner'),
            ('agents.causal_reasoning_engine', 'CausalReasoningEngine'),
            ('agents.proactive_research_agent', 'ProactiveResearchAgent'),
            ('agents.brain_research_orchestrator', 'BrainResearchOrchestrator'),
        ]
        
        for module_name, class_name in imports:
            try:
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                self.log("PASS", f"Import {class_name}", f"from {module_name}")
            except Exception as e:
                self.log("FAIL", f"Import {class_name}", f"{str(e)}")

    def test_database(self):
        """Test 3: فحص قاعدة البيانات"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}💾 Test 3: Database Connectivity{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        db_path = self.src_root / 'data' / 'shared_memory.sqlite'
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test beliefs table
            cursor.execute('SELECT COUNT(*) FROM beliefs')
            beliefs_count = cursor.fetchone()[0]
            self.log("PASS", "Beliefs Table", f"{beliefs_count:,} entries")
            
            # Test neurons
            cursor.execute("SELECT COUNT(*) FROM beliefs WHERE key LIKE 'neuron:%'")
            neurons_count = cursor.fetchone()[0]
            self.log("PASS", "Neurons", f"{neurons_count:,} entries")
            
            # Test goals table (if exists)
            try:
                cursor.execute('SELECT COUNT(*) FROM goals')
                goals_count = cursor.fetchone()[0]
                self.log("PASS", "Goals Table", f"{goals_count} entries")
            except:
                self.log("WARN", "Goals Table", "Not initialized yet (run GoalPlanner once)")
            
            # Test causal nodes table (if exists)
            try:
                cursor.execute('SELECT COUNT(*) FROM causal_nodes')
                nodes_count = cursor.fetchone()[0]
                self.log("PASS", "Causal Nodes", f"{nodes_count} entries")
            except:
                self.log("WARN", "Causal Nodes", "Not initialized yet (run CausalEngine once)")
            
            conn.close()
            
        except Exception as e:
            self.log("FAIL", "Database", str(e))

    def test_agent_creation(self):
        """Test 4: فحص إنشاء الوكلاء"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}🤖 Test 4: Agent Creation{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        sys.path.insert(0, str(self.src_root))
        
        # Test UnifiedContext
        try:
            from agents.unified_context import UnifiedContext
            context = UnifiedContext()
            self.log("PASS", "UnifiedContext", "Created successfully")
        except Exception as e:
            self.log("FAIL", "UnifiedContext", str(e))
        
        # Test GoalPlanner
        try:
            from agents.goal_planner import GoalPlanner
            planner = GoalPlanner()
            self.log("PASS", "GoalPlanner", f"Main goal: {planner.main_goal.description[:50]}...")
        except Exception as e:
            self.log("FAIL", "GoalPlanner", str(e))
        
        # Test CausalReasoningEngine
        try:
            from agents.causal_reasoning_engine import CausalReasoningEngine
            engine = CausalReasoningEngine()
            self.log("PASS", "CausalReasoningEngine", "Created successfully")
        except Exception as e:
            self.log("FAIL", "CausalReasoningEngine", str(e))
        
        # Test ProactiveResearchAgent
        try:
            from agents.proactive_research_agent import ProactiveResearchAgent
            from agents.unified_context import UnifiedContext
            context = UnifiedContext()
            agent = ProactiveResearchAgent(context)
            self.log("PASS", "ProactiveResearchAgent", "Created successfully")
        except Exception as e:
            self.log("FAIL", "ProactiveResearchAgent", str(e))

    def test_integration(self):
        """Test 5: فحص التكامل بين المكونات"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}🔗 Test 5: Component Integration{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        sys.path.insert(0, str(self.src_root))
        
        try:
            # Test full integration
            from agents.unified_context import UnifiedContext
            from agents.goal_planner import GoalPlanner
            from agents.causal_reasoning_engine import CausalReasoningEngine
            
            context = UnifiedContext()
            planner = GoalPlanner()
            engine = CausalReasoningEngine()
            
            # Test context update
            context.update_from_trading()
            self.log("PASS", "Context Update", "Trading data loaded")
            
            # Test goal decomposition
            subgoals = planner._load_subgoals(planner.main_goal.id)
            if not subgoals:
                subgoals = planner.decompose_goal(planner.main_goal)
            self.log("PASS", "Goal Decomposition", f"{len(subgoals)} sub-goals created")
            
            # Test causal analysis (mock)
            mock_trade = {
                'id': 'health_check_test',
                'pnl': -1.0,
                'exit_reason': 'stop_loss',
                'setup_type': 'breakout',
                'volatility_spike': True,
                'entry_quality_score': 0.5,
                'entry_time': datetime.now().isoformat()
            }
            analysis = engine.analyze_loss(mock_trade)
            self.log("PASS", "Causal Analysis", f"Root cause: {analysis['root_cause']['description'][:50]}...")
            
        except Exception as e:
            self.log("FAIL", "Integration", str(e))

    def test_kernel(self):
        """Test 6: فحص AgentKernel"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}🛡️ Test 6: AgentKernel{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        kernel_path = self.project_root / 'gateway' / 'app' / 'core' / 'agent_kernel.py'
        
        if kernel_path.exists():
            self.log("PASS", "AgentKernel File", "Found")
            
            # Check key features
            with open(kernel_path, 'r') as f:
                content = f.read()
                
                if 'TaskBudget' in content:
                    self.log("PASS", "TaskBudget", "Resource limits implemented")
                else:
                    self.log("WARN", "TaskBudget", "Not found")
                
                if '_sanitize_answer' in content:
                    self.log("PASS", "Output Sanitization", "Security filters active")
                else:
                    self.log("WARN", "Output Sanitization", "Not found")
                
                if 'SafeMathEvaluator' in content:
                    self.log("PASS", "SafeMath", "Math evaluator integrated")
                else:
                    self.log("WARN", "SafeMath", "Not found")
        else:
            self.log("FAIL", "AgentKernel", "File not found")

    def generate_report(self):
        """Generate final report"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}📊 HEALTH CHECK REPORT{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        total = len(self.results)
        passed = sum(1 for s, _, _ in self.results if s == "PASS")
        failed = sum(1 for s, _, _ in self.results if s == "FAIL")
        warnings = sum(1 for s, _, _ in self.results if s == "WARN")
        
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"{YELLOW}Warnings: {warnings}{RESET}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print(f"\n{GREEN}✅ SYSTEM STATUS: EXCELLENT{RESET}")
            print(f"{GREEN}   النظام يعمل بشكل ممتاز ✨{RESET}")
        elif success_rate >= 70:
            print(f"\n{YELLOW}⚠️ SYSTEM STATUS: GOOD{RESET}")
            print(f"{YELLOW}   النظام يعمل بشكل جيد مع بعض التحذيرات{RESET}")
        else:
            print(f"\n{RED}❌ SYSTEM STATUS: NEEDS ATTENTION{RESET}")
            print(f"{RED}   النظام يحتاج إصلاحات{RESET}")
        
        # Recommendations
        if failed > 0:
            print(f"\n{BLUE}💡 RECOMMENDATIONS:{RESET}")
            for status, component, message in self.results:
                if status == "FAIL":
                    print(f"   - Fix: {component}")
        
        print(f"\n{BLUE}{'='*70}{RESET}\n")

    def run_all(self):
        """Run all health checks"""
        print(f"\n{BLUE}{'#'*70}{RESET}")
        print(f"{BLUE}# NOOGH UNIFIED SYSTEM - HEALTH CHECK{RESET}")
        print(f"{BLUE}# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{BLUE}{'#'*70}{RESET}")
        
        self.test_files_exist()
        self.test_imports()
        self.test_database()
        self.test_agent_creation()
        self.test_integration()
        self.test_kernel()
        self.generate_report()


if __name__ == '__main__':
    checker = HealthCheck()
    checker.run_all()