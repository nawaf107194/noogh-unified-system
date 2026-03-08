#!/usr/bin/env python3
"""
Brain Chat - محادثة مع العقل
يطرح 1000 سؤال على نظام NOOGH العصبي ويسجل الإجابات
"""

import asyncio
import json
import logging
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Colors
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("brain_chat")


class BrainInterface:
    """واجهة التحدث مع عقل NOOGH"""

    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'data' / 'shared_memory.sqlite'
        self.conversation_log = []

        # Try to load WorldModel and NeuronFabric
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from unified_core.core.world_model import WorldModel
            from unified_core.core.neuron_fabric import get_neuron_fabric
            from unified_core.core.gravity import DecisionScorer, DecisionContext

            self.world_model = WorldModel()
            self.neuron_fabric = get_neuron_fabric()
            self.decision_scorer = DecisionScorer()
            self.has_core = True

            logger.info("✅ Connected to NOOGH Core (WorldModel + NeuronFabric + DecisionScorer)")
        except Exception as e:
            logger.warning(f"⚠️ Could not load NOOGH Core: {e}")
            self.world_model = None
            self.neuron_fabric = None
            self.decision_scorer = None
            self.has_core = False

    def connect_to_database(self) -> Optional[sqlite3.Connection]:
        """الاتصال بقاعدة البيانات مباشرة"""
        if not self.db_path.exists():
            logger.error(f"❌ Database not found: {self.db_path}")
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return None

    def ask_about_beliefs(self, question: str) -> Dict[str, Any]:
        """سؤال عن المعتقدات"""
        conn = self.connect_to_database()
        if not conn:
            return {"error": "No database connection"}

        try:
            # Extract keywords from question
            keywords = self._extract_keywords(question)

            # Search beliefs matching keywords
            cursor = conn.cursor()
            matching_beliefs = []

            for keyword in keywords:
                cursor.execute("""
                    SELECT key, value, utility_score, updated_at, use_count
                    FROM beliefs
                    WHERE value LIKE ? OR key LIKE ?
                    ORDER BY utility_score DESC
                    LIMIT 10
                """, (f"%{keyword}%", f"%{keyword}%"))

                matching_beliefs.extend([dict(row) for row in cursor.fetchall()])

            # Remove duplicates
            seen = set()
            unique_beliefs = []
            for b in matching_beliefs:
                if b['key'] not in seen:
                    seen.add(b['key'])
                    unique_beliefs.append(b)

            conn.close()

            return {
                "question": question,
                "keywords": keywords,
                "matched_beliefs": unique_beliefs[:5],  # Top 5
                "total_matches": len(unique_beliefs)
            }

        except Exception as e:
            conn.close()
            return {"error": str(e)}

    def ask_about_neurons(self, question: str) -> Dict[str, Any]:
        """سؤال عن العصبونات - using NeuronFabric if available"""

        # Use NeuronFabric if available
        if self.has_core and self.neuron_fabric:
            try:
                total = len(self.neuron_fabric.neurons)
                active = sum(1 for n in self.neuron_fabric.neurons.values() if n.energy > 0.5)
                avg_energy = sum(n.energy for n in self.neuron_fabric.neurons.values()) / total if total > 0 else 0

                # Get top neurons by energy
                top_neurons = sorted(
                    self.neuron_fabric.neurons.values(),
                    key=lambda n: n.energy,
                    reverse=True
                )[:5]

                return {
                    "question": question,
                    "total_neurons": total,
                    "active_neurons": active,
                    "avg_energy": round(avg_energy, 3),
                    "top_neurons": [
                        {
                            "neuron_id": n.neuron_id,
                            "proposition": n.proposition[:60],
                            "energy": round(n.energy, 3),
                            "neuron_type": n.neuron_type.value
                        }
                        for n in top_neurons
                    ]
                }
            except Exception as e:
                return {"error": f"NeuronFabric error: {str(e)}"}

        return {"error": "NeuronFabric not available"}

    def ask_about_decisions(self, question: str) -> Dict[str, Any]:
        """سؤال عن القرارات - using decisions table"""
        conn = self.connect_to_database()
        if not conn:
            return {"error": "No database connection"}

        try:
            cursor = conn.cursor()

            # Get decision statistics
            cursor.execute("SELECT COUNT(*) as total FROM decisions")
            total = cursor.fetchone()['total']

            # Get recent decisions
            cursor.execute("""
                SELECT decision_id, decision_type, query, action_type, cost_paid
                FROM decisions
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            recent_decisions = [dict(row) for row in cursor.fetchall()]

            # Get average cost
            cursor.execute("SELECT AVG(cost_paid) as avg_cost FROM decisions")
            avg_cost = cursor.fetchone()['avg_cost'] or 0

            conn.close()

            return {
                "question": question,
                "total_decisions": total,
                "recent_decisions": recent_decisions,
                "avg_cost": round(avg_cost, 2)
            }

        except Exception as e:
            conn.close()
            return {"error": str(e)}

    def ask_about_system(self, question: str) -> Dict[str, Any]:
        """سؤال عن النظام بشكل عام"""
        conn = self.connect_to_database()
        if not conn:
            return {"error": "No database connection"}

        try:
            cursor = conn.cursor()

            stats = {}

            # Get all table counts
            for table in ['beliefs', 'neurons', 'decisions', 'observations', 'predictions']:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()['count']
                except:
                    stats[f"{table}_count"] = 0

            # Get system uptime (from oldest belief)
            try:
                cursor.execute("SELECT MIN(created_at) as oldest FROM beliefs")
                oldest = cursor.fetchone()['oldest']
                if oldest:
                    uptime_seconds = time.time() - oldest
                    uptime_days = uptime_seconds / 86400
                    stats['system_age_days'] = round(uptime_days, 2)
            except:
                stats['system_age_days'] = 0

            conn.close()

            return {
                "question": question,
                "system_stats": stats
            }

        except Exception as e:
            conn.close()
            return {"error": str(e)}

    def ask_about_trading(self, question: str) -> Dict[str, Any]:
        """سؤال عن التداول"""
        trade_file = Path(__file__).parent.parent / 'data' / 'trading' / 'trade_history.json'

        if not trade_file.exists():
            return {"error": "No trading history found"}

        try:
            with open(trade_file, 'r') as f:
                trade_data = json.load(f)

            stats = trade_data.get('stats', {})
            history = trade_data.get('history', [])

            # Recent trades
            recent = history[:5]

            # Best trade
            best = max(history, key=lambda t: t.get('pnl_percent', 0)) if history else None

            # Worst trade
            worst = min(history, key=lambda t: t.get('pnl_percent', 0)) if history else None

            return {
                "question": question,
                "total_trades": stats.get('total', 0),
                "win_rate": stats.get('win_rate', 0),
                "total_pnl": stats.get('total_pnl', 0),
                "recent_trades": recent,
                "best_trade": best,
                "worst_trade": worst
            }

        except Exception as e:
            return {"error": str(e)}

    def _extract_keywords(self, question: str) -> List[str]:
        """استخراج الكلمات المفتاحية من السؤال"""
        # Remove common words
        stop_words = {'what', 'how', 'why', 'when', 'where', 'is', 'are', 'the', 'a', 'an',
                      'ما', 'كيف', 'لماذا', 'متى', 'أين', 'هل', 'في', 'من', 'إلى'}

        words = question.lower().split()
        keywords = [w.strip('?.,!') for w in words if w.strip('?.,!') not in stop_words]

        return keywords[:5]  # Max 5 keywords

    def route_question(self, question: str) -> Dict[str, Any]:
        """توجيه السؤال للمكان المناسب"""
        q_lower = question.lower()

        # Determine question type
        if any(word in q_lower for word in ['belief', 'معتقد', 'proposition', 'knowledge', 'معرفة']):
            return self.ask_about_beliefs(question)

        elif any(word in q_lower for word in ['neuron', 'عصبون', 'fabric', 'شبكة', 'energy', 'طاقة']):
            return self.ask_about_neurons(question)

        elif any(word in q_lower for word in ['decision', 'قرار', 'choose', 'اختيار', 'action', 'فعل']):
            return self.ask_about_decisions(question)

        elif any(word in q_lower for word in ['trade', 'تداول', 'trading', 'binance', 'crypto', 'عملة']):
            return self.ask_about_trading(question)

        else:
            # General system question
            return self.ask_about_system(question)


class QuestionGenerator:
    """مُولّد الأسئلة الذكي"""

    def __init__(self):
        self.question_templates = self._build_question_bank()

    def _build_question_bank(self) -> List[str]:
        """بناء بنك الأسئلة"""
        questions = []

        # System Questions (100)
        questions.extend([
            "What is the total number of beliefs in the system?",
            "How many neurons are currently active?",
            "What is the average energy level of neurons?",
            "How old is the system (in days)?",
            "How many decisions have been made so far?",
            "What is the most confident belief?",
            "What is the weakest neuron?",
            "How many observations have been recorded?",
            "What is the system's current state?",
            "Are there any falsified beliefs?",
        ] * 10)  # Repeat 10 times with variations

        # Belief Questions (200)
        topics = ['security', 'trading', 'system', 'learning', 'goals', 'risks',
                  'performance', 'strategies', 'optimization', 'decisions']

        for topic in topics * 20:
            questions.append(f"What beliefs exist about {topic}?")
            questions.append(f"Show me high-confidence beliefs related to {topic}")

        # Neuron Questions (200)
        neuron_types = ['sensory', 'cognitive', 'motor', 'emotional', 'meta', 'strategic']

        for ntype in neuron_types * 33:
            questions.append(f"How many {ntype} neurons are active?")
            questions.append(f"What is the strongest {ntype} neuron?")

        # Decision Questions (200)
        for i in range(200):
            questions.append(f"What was decision {i} about?")
            questions.append(f"Show me recent decisions related to trading")

        # Trading Questions (200)
        trading_topics = ['win rate', 'best symbol', 'worst trade', 'total PnL',
                          'recent signals', 'strategy', 'risk', 'performance']

        for topic in trading_topics * 25:
            questions.append(f"What is the {topic}?")
            questions.append(f"Tell me about {topic}")

        # Meta Questions (100)
        meta_questions = [
            "How many synapses connect neurons?",
            "What is the most active cluster?",
            "Which neurons have the highest activation count?",
            "What are the system's current goals?",
            "What predictions have been made?",
            "How accurate are the predictions?",
            "What are the system's weaknesses?",
            "What are the system's strengths?",
            "What lessons have been learned?",
            "What is being monitored right now?",
        ] * 10

        questions.extend(meta_questions)

        return questions[:1000]  # Exactly 1000 questions

    def get_all_questions(self) -> List[str]:
        """الحصول على جميع الأسئلة"""
        return self.question_templates


def print_header(title: str):
    """طباعة رأسية"""
    print(f"\n{CYAN}{BOLD}{'='*70}{RESET}")
    print(f"{CYAN}{BOLD}{title:^70}{RESET}")
    print(f"{CYAN}{BOLD}{'='*70}{RESET}\n")


def print_qa(question_num: int, question: str, answer: Dict[str, Any]):
    """طباعة سؤال وجواب"""
    print(f"\n{YELLOW}{BOLD}Q{question_num}:{RESET} {question}")

    # Format answer based on type
    if 'error' in answer:
        print(f"  {RED}❌ Error: {answer['error']}{RESET}")

    elif 'matched_beliefs' in answer:
        beliefs = answer['matched_beliefs']
        print(f"  {GREEN}✓ Found {answer['total_matches']} beliefs{RESET}")
        for b in beliefs[:3]:
            value_str = b.get('value', '')[:60] if isinstance(b.get('value'), str) else str(b.get('value', ''))[:60]
            utility = b.get('utility_score', 0)
            print(f"    • {value_str}... (utility: {utility:.2f})")

    elif 'total_neurons' in answer:
        print(f"  {GREEN}✓ Total Neurons: {answer['total_neurons']:,}{RESET}")
        print(f"  {GREEN}✓ Active: {answer['active_neurons']:,}{RESET}")
        print(f"  {GREEN}✓ Avg Energy: {answer['avg_energy']:.3f}{RESET}")

    elif 'total_decisions' in answer:
        print(f"  {GREEN}✓ Total Decisions: {answer['total_decisions']:,}{RESET}")
        recent = answer.get('recent_decisions', [])
        print(f"  {GREEN}✓ Recent: {len(recent)} shown{RESET}")
        if 'avg_cost' in answer:
            print(f"  {GREEN}✓ Avg Cost: {answer['avg_cost']:.2f}{RESET}")

    elif 'system_stats' in answer:
        stats = answer['system_stats']
        print(f"  {GREEN}✓ System Stats:{RESET}")
        for key, value in stats.items():
            print(f"    • {key}: {value:,}" if isinstance(value, int) else f"    • {key}: {value}")

    elif 'total_trades' in answer:
        print(f"  {GREEN}✓ Total Trades: {answer['total_trades']:,}{RESET}")
        print(f"  {GREEN}✓ Win Rate: {answer['win_rate']:.1f}%{RESET}")
        print(f"  {GREEN}✓ Total PnL: ${answer['total_pnl']:,.2f}{RESET}")

    else:
        print(f"  {YELLOW}Response: {json.dumps(answer, indent=2)}{RESET}")


async def main():
    """البرنامج الرئيسي"""

    print(f"{CYAN}{BOLD}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║              🧠 BRAIN CHAT - محادثة مع العقل 🧠                 ║")
    print("║                                                                   ║")
    print("║                    1000 Questions Session                         ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(RESET)

    # Initialize
    brain = BrainInterface()
    generator = QuestionGenerator()
    questions = generator.get_all_questions()

    print(f"\n{GREEN}✓ Brain Interface: {'Connected' if brain.has_core else 'Database-only mode'}{RESET}")
    print(f"{GREEN}✓ Questions prepared: {len(questions):,}{RESET}")
    print(f"{YELLOW}Starting Q&A session...{RESET}\n")

    # Log file
    log_file = Path(__file__).parent.parent / 'logs' / 'brain_chat_session.json'
    log_file.parent.mkdir(exist_ok=True)

    session = {
        'started_at': datetime.now().isoformat(),
        'total_questions': len(questions),
        'qa_pairs': []
    }

    # Ask questions in batches
    batch_size = 50
    total_batches = (len(questions) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(questions))
        batch = questions[start_idx:end_idx]

        print_header(f"BATCH {batch_num + 1}/{total_batches} (Questions {start_idx + 1}-{end_idx})")

        for i, question in enumerate(batch):
            question_num = start_idx + i + 1

            # Ask question
            answer = brain.route_question(question)

            # Print (show every 10th question to avoid spam)
            if question_num % 10 == 0 or question_num <= 20:
                print_qa(question_num, question, answer)

            # Log
            session['qa_pairs'].append({
                'question_num': question_num,
                'question': question,
                'answer': answer,
                'timestamp': time.time()
            })

            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.01)

        # Save batch progress
        with open(log_file, 'w') as f:
            json.dump(session, f, indent=2)

        print(f"\n{GREEN}✓ Batch {batch_num + 1} complete ({end_idx}/{len(questions)}){RESET}")
        print(f"{YELLOW}Progress: {end_idx/len(questions)*100:.1f}%{RESET}")

        # Pause between batches
        if batch_num < total_batches - 1:
            await asyncio.sleep(0.5)

    # Session complete
    session['completed_at'] = datetime.now().isoformat()
    session['duration_seconds'] = time.time() - time.mktime(
        datetime.fromisoformat(session['started_at']).timetuple()
    )

    with open(log_file, 'w') as f:
        json.dump(session, f, indent=2)

    # Summary
    print_header("SESSION SUMMARY")

    print(f"{GREEN}✓ Total Questions Asked: {len(session['qa_pairs']):,}{RESET}")
    print(f"{GREEN}✓ Duration: {session['duration_seconds']:.1f} seconds{RESET}")
    print(f"{GREEN}✓ Questions per second: {len(session['qa_pairs'])/session['duration_seconds']:.1f}{RESET}")

    # Error count
    errors = sum(1 for qa in session['qa_pairs'] if 'error' in qa['answer'])
    print(f"{RED if errors > 0 else GREEN}✓ Errors: {errors}{RESET}")

    print(f"\n{CYAN}Session log saved to:{RESET}")
    print(f"  {log_file}")

    print(f"\n{CYAN}{BOLD}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║         🧠 Brain Chat Session Complete - 1000 Q&A Done! 🧠       ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(RESET)


if __name__ == "__main__":
    asyncio.run(main())
