#!/usr/bin/env python3
"""
NOOGH Research Specialist Agent — FIXED VERSION
استبدال PerplexityAdapter بـ DuckDuckGo + urllib (بدون dependencies خارجية)
"""
import logging
import asyncio
import time
import json
import urllib.request
import urllib.parse
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agents.research_specialist")


class ResearchSpecialistAgent:
    """
    Agent for deep research and synthesis.
    Uses DuckDuckGo Instant Answer API + urllib (no external dependencies).
    """

    def __init__(self):
        self.handlers = {
            "THINK_DEEP": self._think_deep,
            "SYNTHESIZE_RESEARCH": self._synthesize_research,
        }
        self._running = False
        logger.info("\u2705 ResearchSpecialistAgent initialized (DuckDuckGo mode)")

    # ------------------------------------------------------------------ #
    #  Search helpers
    # ------------------------------------------------------------------ #

    def _ddg_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """DuckDuckGo Instant Answer API — لا يحتاج API key."""
        results = []
        try:
            params = urllib.parse.urlencode({
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            })
            url = f"https://api.duckduckgo.com/?{params}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "NOOGH-Research/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Abstract (الإجابة المباشرة)
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "content": data["AbstractText"],
                    "url": data.get("AbstractURL", ""),
                    "source": "ddg_abstract"
                })

            # Related Topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:80],
                        "content": topic["Text"],
                        "url": topic.get("FirstURL", ""),
                        "source": "ddg_related"
                    })

        except Exception as e:
            logger.warning(f"DDG search failed for '{query}': {e}")

        # fallback: Wikipedia summary
        if not results:
            results = self._wikipedia_search(query)

        return results[:max_results]

    def _wikipedia_search(self, query: str) -> List[Dict]:
        """Wikipedia REST API كـ fallback."""
        results = []
        try:
            encoded = urllib.parse.quote(query.replace(" ", "_"))
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "NOOGH-Research/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("extract"):
                results.append({
                    "title": data.get("title", query),
                    "content": data["extract"],
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "source": "wikipedia"
                })
        except Exception as e:
            logger.warning(f"Wikipedia fallback failed: {e}")
        return results

    # ------------------------------------------------------------------ #
    #  Task handlers
    # ------------------------------------------------------------------ #

    async def _think_deep(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs in-depth research on a topic.
        Args:
            query (str): The research query.
        """
        query = task.get("query", task.get("input", ""))
        if not query:
            return {"success": False, "error": "No query provided"}

        logger.info(f"\U0001f9e0 Deep Thinking requested: {query}")

        results = await asyncio.get_event_loop().run_in_executor(
            None, self._ddg_search, query, 8
        )

        if results:
            logger.info(f"\u2705 Deep research completed: {len(results)} results for '{query}'")
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            logger.warning(f"\u26a0\ufe0f No results found for: {query}")
            return {
                "success": False,
                "error": f"No results found for: {query}"
            }

    async def _synthesize_research(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combines multiple research points into a technical report.
        """
        findings = task.get("findings", [])
        topic = task.get("topic", "General Discovery")

        if not findings:
            return {"success": False, "error": "No findings to synthesize"}

        report = f"# Research Synthesis: {topic}\n\n"
        report += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for i, item in enumerate(findings):
            report += f"## Analysis Point {i+1}\n"
            if isinstance(item, dict):
                content = item.get("content", str(item))
                citations = item.get("citations", [])
                url = item.get("url", "")
                report += f"{content}\n\n"
                if url:
                    report += f"**Source:** {url}\n"
                if citations:
                    report += "**Citations:**\n"
                    for c in citations:
                        report += f"- {c}\n"
            else:
                report += f"{item}\n"
            report += "\n---\n\n"

        logger.info(f"\u2705 Research synthesis completed: {len(findings)} findings on '{topic}'")
        return {"success": True, "report": report, "topic": topic}

    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """نقطة الدخول الموحدة للمهام."""
        action = task.get("action", task.get("type", "")).upper()
        handler = self.handlers.get(action)
        if handler:
            return await handler(task)
        # default: run search
        return await self._think_deep(task)

    def start(self):
        self._running = True
        logger.info("\U0001f7e2 ResearchSpecialistAgent started")

    def stop(self):
        self._running = False
        logger.info("\U0001f534 ResearchSpecialistAgent stopped")


if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.INFO)
        agent = ResearchSpecialistAgent()
        agent.start()
        # test
        result = await agent.handle_task({
            "action": "THINK_DEEP",
            "query": "artificial intelligence agents 2025"
        })
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(main())
