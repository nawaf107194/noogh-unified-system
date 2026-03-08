#!/usr/bin/env python3
"""
NOOGH Sales Automation Agent — FIXED VERSION
استبدال VendorfulAdapter بـ template-based responses بدون dependencies خارجية
"""
import logging
import asyncio
import time
import json
import sqlite3
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("agents.sales_automation")

# مسار قاعدة بيانات المبيعات
DB_PATH = Path.home() / "projects/noogh_unified_system/src/data/sales.sqlite"


class SalesAutomationAgent:
    """
    Agent for automated response management and sales optimization.
    Orchestrates strategic responses for NOOGH ecosystem inquiries.
    Uses template-based system (no VendorfulAdapter / external deps).
    """

    RESPONSE_TEMPLATES = {
        "greeting": (
            "Thank you for reaching out to NOOGH! "
            "I'm here to help you with {topic}. "
            "Could you provide more details about your requirements?"
        ),
        "proposal": (
            "Based on your inquiry about {topic}, here is our proposal:\n\n"
            "- Solution: {solution}\n"
            "- Timeline: {timeline}\n"
            "- Value: {value}\n\n"
            "Let us know if you'd like to discuss further."
        ),
        "follow_up": (
            "Following up on our previous conversation about {topic}. "
            "Have you had a chance to review our proposal? "
            "We're happy to answer any questions."
        ),
        "closing": (
            "We're excited to move forward with {topic}. "
            "The next steps are:\n"
            "1. {step1}\n"
            "2. {step2}\n"
            "3. {step3}\n"
            "Please confirm to proceed."
        ),
        "objection_handling": (
            "I understand your concern about {concern}. "
            "Here's how we address that:\n\n"
            "{response}\n\n"
            "Does this address your concern?"
        ),
        "default": (
            "Thank you for your inquiry about {topic}. "
            "Our team will analyze your request and provide "
            "a comprehensive response within 24 hours."
        ),
    }

    def __init__(self):
        self.handlers = {
            "GENERATE_STRATEGIC_RESPONSE": self._generate_strategic_response,
            "OPTIMIZE_SALES_FUNNEL": self._optimize_sales_funnel,
        }
        self._running = False
        self._init_db()
        logger.info("\u2705 SalesAutomationAgent initialized (template mode)")

    def _init_db(self):
        """Initialize SQLite sales DB."""
        try:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(DB_PATH), timeout=10)
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS sales_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inquiry_hash TEXT UNIQUE,
                    inquiry TEXT,
                    response TEXT,
                    template_used TEXT,
                    success INTEGER DEFAULT 1,
                    created_at REAL
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"DB init warning: {e}")

    def _render_template(self, template_key: str, context: Dict) -> str:
        """Renders a response template with context variables."""
        template = self.RESPONSE_TEMPLATES.get(
            template_key,
            self.RESPONSE_TEMPLATES["default"]
        )
        try:
            return template.format_map(
                {k: v if v else "N/A" for k, v in {**{"topic": "your inquiry", "solution": "Custom NOOGH solution", "timeline": "2-4 weeks", "value": "High ROI", "step1": "Sign agreement", "step2": "Kickoff call", "step3": "Delivery", "concern": "your concern", "response": "We have addressed this successfully for many clients."}, **context}.items()}
            )
        except (KeyError, ValueError):
            return self.RESPONSE_TEMPLATES["default"].format(topic=context.get("topic", "your request"))

    def _detect_template(self, inquiry: str) -> str:
        """Detects the appropriate template based on inquiry keywords."""
        inquiry_lower = inquiry.lower()
        if any(w in inquiry_lower for w in ["hello", "hi", "interested", "tell me"]):
            return "greeting"
        elif any(w in inquiry_lower for w in ["proposal", "quote", "price", "cost", "plan"]):
            return "proposal"
        elif any(w in inquiry_lower for w in ["follow", "status", "update", "check"]):
            return "follow_up"
        elif any(w in inquiry_lower for w in ["agree", "proceed", "close", "accept", "buy"]):
            return "closing"
        elif any(w in inquiry_lower for w in ["concern", "issue", "problem", "worry", "but", "however"]):
            return "objection_handling"
        return "default"

    def _save_interaction(self, inquiry: str, response: str, template: str):
        """Saves interaction to SQLite."""
        try:
            inquiry_hash = hashlib.md5(inquiry.encode()).hexdigest()
            conn = sqlite3.connect(str(DB_PATH), timeout=10)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO sales_interactions "
                "(inquiry_hash, inquiry, response, template_used, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (inquiry_hash, inquiry[:500], response[:2000], template, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Save interaction warning: {e}")

    # ------------------------------------------------------------------ #
    #  Task handlers
    # ------------------------------------------------------------------ #

    async def _generate_strategic_response(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a professional strategic response.
        Args:
            inquiry (str): The inquiry text.
            context (dict): Optional context.
        """
        inquiry = task.get("inquiry", task.get("input", ""))
        context = task.get("context", {})

        if not inquiry:
            return {"success": False, "error": "No inquiry provided"}

        logger.info(f"\U0001f4a1 Generating strategic response for: {inquiry[:60]}")

        # detect template
        template_key = self._detect_template(inquiry)

        # build context
        if not context.get("topic"):
            # extract topic from inquiry
            words = inquiry.split()
            context["topic"] = " ".join(words[:5]) if len(words) >= 5 else inquiry

        response_text = self._render_template(template_key, context)

        # save
        self._save_interaction(inquiry, response_text, template_key)

        logger.info(f"\u2705 Strategic response generated using template: {template_key}")
        return {
            "success": True,
            "response": response_text,
            "template_used": template_key,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    async def _optimize_sales_funnel(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes and optimizes sales funnel based on stored interactions.
        """
        logger.info("\U0001f4ca Optimizing sales funnel...")

        stats = {
            "total_interactions": 0,
            "template_breakdown": {},
            "recommendations": []
        }

        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=10)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM sales_interactions")
            stats["total_interactions"] = cur.fetchone()[0]

            cur.execute(
                "SELECT template_used, COUNT(*) as cnt "
                "FROM sales_interactions GROUP BY template_used"
            )
            for row in cur.fetchall():
                stats["template_breakdown"][row[0]] = row[1]

            conn.close()
        except Exception as e:
            logger.warning(f"Funnel analysis DB error: {e}")

        # recommendations
        breakdown = stats["template_breakdown"]
        if breakdown.get("objection_handling", 0) > breakdown.get("closing", 0):
            stats["recommendations"].append(
                "High objection rate detected — consider proactive FAQ responses."
            )
        if stats["total_interactions"] < 10:
            stats["recommendations"].append(
                "Low interaction count — increase outreach campaigns."
            )
        if not stats["recommendations"]:
            stats["recommendations"].append(
                "Funnel looks healthy. Continue current strategy."
            )

        logger.info(f"\u2705 Funnel optimization complete: {stats['total_interactions']} interactions analyzed")
        return {"success": True, "stats": stats}

    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Unified task entry point."""
        action = task.get("action", task.get("type", "")).upper()
        handler = self.handlers.get(action)
        if handler:
            return await handler(task)
        return await self._generate_strategic_response(task)

    def start(self):
        self._running = True
        logger.info("\U0001f7e2 SalesAutomationAgent started")

    def stop(self):
        self._running = False
        logger.info("\U0001f534 SalesAutomationAgent stopped")


if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.INFO)
        agent = SalesAutomationAgent()
        agent.start()
        result = await agent.handle_task({
            "action": "GENERATE_STRATEGIC_RESPONSE",
            "inquiry": "Hello, I'm interested in your AI solutions. Can you send me a proposal?",
            "context": {"topic": "AI automation solutions"}
        })
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(main())
