#!/usr/bin/env python3
"""
NOOGH AI Tool Scout Agent - FIXED v2
Scouts for new AI tools via web search and evaluates them.
Uses only stdlib + shared SQLite DB.
"""
import asyncio
import logging
import sqlite3
import json
import time
import re
import urllib.request
import urllib.parse
import sys
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | ai_tool_scout | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/noogh/projects/noogh_unified_system/src/logs/ai_tool_scout.log"),
    ],
)
logger = logging.getLogger("ai_tool_scout_agent")

DB_PATH = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
AI_TOOLS_DB = "/home/noogh/projects/noogh_unified_system/src/data/ai_tools.sqlite"

# Sources to discover AI tools
SOURCES = [
    "https://huggingface.co/papers",
    "https://arxiv.org/search/?searchtype=all&query=AI+agent+tool&start=0",
    "https://news.ycombinator.com/",
    "https://www.reddit.com/r/MachineLearning/.json?limit=25",
]


def _fetch(url: str, timeout: int = 12) -> Optional[str]:
    """Fetch URL content using stdlib only."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "NOOGH-Scout/2.0 (compatible; stdlib)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Fetch failed for {url}: {e}")
        return None


def _ensure_db(db_path: str):
    """Ensure the AI tools database and table exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT DEFAULT 'unknown',
            description TEXT DEFAULT '',
            url TEXT DEFAULT '',
            api_available INTEGER DEFAULT 0,
            relevance_score REAL DEFAULT 0.5,
            status TEXT DEFAULT 'discovered',
            integration_priority TEXT DEFAULT 'low',
            suggested_agent TEXT DEFAULT '',
            discovered_at TEXT,
            evaluated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def _db_inject(db_path: str, tool: Dict[str, Any]):
    """Insert or update a tool in the database."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('''
            INSERT INTO ai_tools (name, category, description, url, api_available,
                                  relevance_score, status, discovered_at)
            VALUES (?, ?, ?, ?, ?, ?, 'discovered', ?)
            ON CONFLICT(name) DO UPDATE SET
                description = excluded.description,
                relevance_score = MAX(relevance_score, excluded.relevance_score)
        ''', (
            tool.get("name", ""),
            tool.get("category", "unknown"),
            tool.get("description", ""),
            tool.get("url", ""),
            1 if tool.get("api_available") else 0,
            tool.get("relevance_score", 0.5),
            datetime.utcnow().isoformat(),
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"DB inject error for {tool.get('name')}: {e}")
    finally:
        conn.close()


def _share_finding(name: str, description: str, priority: str):
    """Write high-priority findings to the shared memory DB for other agents."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT,
                event_type TEXT,
                payload TEXT,
                created_at TEXT
            )
        ''')
        conn.execute(
            "INSERT INTO agent_events (agent, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (
                "ai_tool_scout",
                "new_tool_found",
                json.dumps({"name": name, "description": description, "priority": priority}),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not share finding to shared_memory: {e}")


def _score_tool(name: str, description: str) -> float:
    """Simple relevance scorer based on keywords."""
    keywords = [
        "agent", "llm", "ai", "model", "api", "automation", "tool",
        "integration", "workflow", "inference", "embedding", "vector",
        "rag", "pipeline", "reasoning", "multimodal", "language model",
    ]
    text = (name + " " + description).lower()
    hits = sum(1 for kw in keywords if kw in text)
    return min(1.0, 0.3 + hits * 0.07)


def _discover_from_reddit(content: str) -> List[Dict]:
    """Parse Reddit JSON for AI tool posts."""
    tools = []
    try:
        data = json.loads(content)
        posts = data.get("data", {}).get("children", [])
        for post in posts:
            p = post.get("data", {})
            title = p.get("title", "")
            url = p.get("url", "")
            desc = p.get("selftext", "")[:300]
            score = _score_tool(title, desc)
            if score >= 0.4:
                tools.append({
                    "name": title[:120],
                    "category": "reddit_ml",
                    "description": desc or title,
                    "url": url,
                    "api_available": False,
                    "relevance_score": score,
                })
    except Exception as e:
        logger.warning(f"Reddit parse error: {e}")
    return tools


def _discover_from_html(content: str, source_url: str) -> List[Dict]:
    """Extract potential tool names/links from HTML."""
    tools = []
    # Find <a> tags with text that looks like a tool
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{5,80})</a>', content)
    seen = set()
    for href, text in links:
        text = re.sub(r'\s+', ' ', text).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        score = _score_tool(text, "")
        if score >= 0.45:
            full_url = href if href.startswith("http") else source_url.rstrip("/") + "/" + href.lstrip("/")
            tools.append({
                "name": text[:120],
                "category": "web_discovery",
                "description": f"Discovered from {source_url}",
                "url": full_url[:500],
                "api_available": False,
                "relevance_score": score,
            })
        if len(tools) >= 20:
            break
    return tools


class AIToolScoutAgent:
    """
    NOOGH AI Tool Scout Agent.
    Periodically scans web sources for new AI tools,
    scores them, stores in DB, and notifies the system via shared memory.
    """

    def __init__(self):
        self.db_path = AI_TOOLS_DB
        self._running = False
        self.scan_interval = 3600 * 6  # Every 6 hours
        _ensure_db(self.db_path)
        logger.info("AIToolScoutAgent initialized.")

    def _discover_tools(self) -> List[Dict]:
        """Fetch all sources and return discovered tools."""
        all_tools = []
        for source in SOURCES:
            logger.info(f"Scanning source: {source}")
            content = _fetch(source)
            if not content:
                continue
            if "reddit.com" in source and source.endswith(".json"):
                tools = _discover_from_reddit(content)
            else:
                tools = _discover_from_html(content, source)
            logger.info(f"  Found {len(tools)} candidates from {source}")
            all_tools.extend(tools)
        return all_tools

    def run_scouting_cycle(self) -> Dict:
        """Run a full discovery + store cycle. Returns summary."""
        logger.info("\u2705 Starting AI Tool Scouting Cycle...")
        start = time.time()
        all_tools = self._discover_tools()
        high_relevance = [t for t in all_tools if t["relevance_score"] >= 0.65]

        for tool in all_tools:
            _db_inject(self.db_path, tool)

        # Share high-relevance findings with the rest of NOOGH
        for tool in high_relevance:
            _share_finding(tool["name"], tool["description"], "high")
            logger.info(f"\u2b50 High-relevance tool: {tool['name']} (score={tool['relevance_score']:.2f})")

        elapsed = round(time.time() - start, 1)
        summary = {
            "total": len(all_tools),
            "high_relevance": len(high_relevance),
            "elapsed": elapsed,
        }
        logger.info(f"\u2705 Scout done: {len(all_tools)} tools, {len(high_relevance)} high-relevance in {elapsed}s")
        return summary

    async def start(self):
        self._running = True
        logger.info("AIToolScoutAgent started (async loop).")
        while self._running:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.run_scouting_cycle)
            except Exception as e:
                logger.error(f"Scout cycle error: {e}")
            await asyncio.sleep(self.scan_interval)

    def stop(self):
        self._running = False
        logger.info("AIToolScoutAgent stopped.")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="NOOGH AI Tool Scout")
    p.add_argument("--once", action="store_true", help="Run one cycle and exit")
    p.add_argument("--report", action="store_true", help="Print DB summary")
    args = p.parse_args()

    if args.report:
        _ensure_db(AI_TOOLS_DB)
        conn = sqlite3.connect(AI_TOOLS_DB)
        rows = conn.execute("SELECT name, relevance_score, status FROM ai_tools ORDER BY relevance_score DESC LIMIT 20").fetchall()
        conn.close()
        print("=== Top AI Tools ===")
        for r in rows:
            print(f"  {r[0][:60]:60s} score={r[1]:.2f}  status={r[2]}")
    else:
        agent = AIToolScoutAgent()
        if args.once:
            result = agent.run_scouting_cycle()
            print(json.dumps(result, indent=2))
        else:
            asyncio.run(agent.start())
