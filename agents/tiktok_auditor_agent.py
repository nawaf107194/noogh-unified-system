#!/usr/bin/env python3
"""
NOOGH TikTok Auditor Agent — FIXED VERSION
استبدال yt-dlp/pytesseract بـ RSS/JSON fetcher بدون dependencies خارجية
يعمل عبر TikTok RSS والبحث في مصادر عامة
"""
import asyncio
import logging
import json
import time
import sqlite3
import urllib.request
import urllib.parse
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("agents.tiktok_auditor")

DB_PATH = Path.home() / "projects/noogh_unified_system/src/data/tiktok_audit.sqlite"


class TikTokAuditorAgent:
    """
    TikTok account monitor and intelligence extractor.
    FIXED: Uses RSS/JSON fetching instead of yt-dlp/pytesseract.
    Capabilities:
    - MONITOR_TIKTOK_ACCOUNT: Get recent content info from a specific @username
    - ANALYZE_VIDEO: Get details about TikTok content via public feeds
    """

    def __init__(self):
        self.handlers = {
            "MONITOR_TIKTOK_ACCOUNT": self._monitor_account,
            "ANALYZE_VIDEO": self._analyze_video,
        }
        self._running = False
        self._last_checked: Dict[str, float] = {}
        self._init_db()
        logger.info("\u2705 TikTokAuditorAgent initialized (RSS/JSON mode)")

    def _init_db(self):
        """Initialize SQLite audit DB."""
        try:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(DB_PATH), timeout=10)
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS tiktok_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    video_id TEXT UNIQUE,
                    title TEXT,
                    url TEXT,
                    published TEXT,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    fetched_at REAL
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"DB init warning: {e}")

    def _fetch(self, url: str, timeout: int = 12) -> Optional[str]:
        """HTTP fetch with error handling."""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; NOOGH/1.0)",
                    "Accept": "application/json, text/html, */*"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Fetch failed {url}: {e}")
            return None

    def _fetch_via_nitter_rss(self, username: str) -> List[Dict]:
        """
        Tries fetching TikTok-like content via public RSS alternatives.
        Falls back to a structured metadata response.
        """
        items = []
        # Try fetching from public RSS aggregators that index TikTok
        rss_sources = [
            f"https://www.tiktok.com/@{username}/rss",
        ]
        for rss_url in rss_sources:
            content = self._fetch(rss_url)
            if content and "<item>" in content:
                titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", content)
                links = re.findall(r"<link>(https://www\.tiktok\.com.*?)</link>", content)
                pubdates = re.findall(r"<pubDate>(.*?)</pubDate>", content)

                for i, (title, link) in enumerate(zip(titles[:10], links[:10])):
                    item = {
                        "username": username,
                        "title": title,
                        "url": link,
                        "video_id": re.search(r"video/(\d+)", link).group(1) if re.search(r"video/(\d+)", link) else f"unknown_{i}",
                        "published": pubdates[i] if i < len(pubdates) else "",
                        "source": "rss"
                    }
                    items.append(item)
                if items:
                    break

        return items

    def _search_tiktok_public(self, username: str) -> List[Dict]:
        """
        Uses DuckDuckGo to find recent TikTok posts for @username.
        """
        items = []
        try:
            query = f"site:tiktok.com @{username}"
            params = urllib.parse.urlencode({
                "q": query,
                "format": "json",
                "no_html": "1"
            })
            url = f"https://api.duckduckgo.com/?{params}"
            content = self._fetch(url)
            if content:
                data = json.loads(content)
                for topic in data.get("RelatedTopics", [])[:10]:
                    if isinstance(topic, dict) and topic.get("FirstURL", "").startswith("https://www.tiktok.com"):
                        items.append({
                            "username": username,
                            "title": topic.get("Text", "")[:120],
                            "url": topic["FirstURL"],
                            "video_id": re.search(r"video/(\d+)", topic["FirstURL"]).group(1)
                            if re.search(r"video/(\d+)", topic["FirstURL"]) else f"ddg_{len(items)}",
                            "published": "",
                            "source": "ddg"
                        })
        except Exception as e:
            logger.warning(f"DDG TikTok search failed: {e}")
        return items

    def _save_videos(self, items: List[Dict]):
        """Saves video metadata to SQLite."""
        if not items:
            return
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=10)
            cur = conn.cursor()
            for item in items:
                cur.execute(
                    "INSERT OR IGNORE INTO tiktok_videos "
                    "(username, video_id, title, url, published, fetched_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        item.get("username", ""),
                        item.get("video_id", ""),
                        item.get("title", "")[:300],
                        item.get("url", ""),
                        item.get("published", ""),
                        time.time()
                    )
                )
            conn.commit()
            conn.close()
            logger.info(f"\u2705 Saved {len(items)} TikTok items to DB")
        except Exception as e:
            logger.warning(f"DB save warning: {e}")

    # ------------------------------------------------------------------ #
    #  Task handlers
    # ------------------------------------------------------------------ #

    async def _monitor_account(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor a TikTok account for new videos.
        Args:
            username (str): TikTok @username (without @)
        """
        username = task.get("username", task.get("input", "")).lstrip("@")
        if not username:
            return {"success": False, "error": "No username provided"}

        logger.info(f"\U0001f3a5 Monitoring TikTok account: @{username}")

        # Rate limiting
        last = self._last_checked.get(username, 0)
        if time.time() - last < 300:  # 5 min cooldown
            return {
                "success": True,
                "username": username,
                "message": "Rate limited — checked recently",
                "next_check_in": int(300 - (time.time() - last))
            }

        # Fetch via RSS
        items = await asyncio.get_event_loop().run_in_executor(
            None, self._fetch_via_nitter_rss, username
        )

        # Fallback to DDG search
        if not items:
            items = await asyncio.get_event_loop().run_in_executor(
                None, self._search_tiktok_public, username
            )

        self._last_checked[username] = time.time()
        self._save_videos(items)

        logger.info(f"\u2705 @{username}: found {len(items)} items")
        return {
            "success": True,
            "username": username,
            "videos_found": len(items),
            "videos": items[:10],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    async def _analyze_video(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a TikTok video by URL.
        Args:
            url (str): TikTok video URL
        """
        url = task.get("url", task.get("input", ""))
        if not url:
            return {"success": False, "error": "No URL provided"}

        logger.info(f"\U0001f50d Analyzing TikTok video: {url}")

        # Extract video ID
        video_id_match = re.search(r"video/(\d+)", url)
        video_id = video_id_match.group(1) if video_id_match else "unknown"

        # Extract username from URL
        username_match = re.search(r"@([\w.]+)/video", url)
        username = username_match.group(1) if username_match else "unknown"

        # Try to fetch page metadata
        content = await asyncio.get_event_loop().run_in_executor(
            None, self._fetch, url
        )

        metadata = {
            "video_id": video_id,
            "username": username,
            "url": url,
            "title": "",
            "description": "",
        }

        if content:
            # Extract OG tags
            title_match = re.search(r'<meta property="og:title" content="(.*?)"', content)
            desc_match = re.search(r'<meta property="og:description" content="(.*?)"', content)
            if title_match:
                metadata["title"] = title_match.group(1)
            if desc_match:
                metadata["description"] = desc_match.group(1)

        logger.info(f"\u2705 Video analysis complete: {video_id}")
        return {
            "success": True,
            "metadata": metadata,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Unified task entry point."""
        action = task.get("action", task.get("type", "")).upper()
        handler = self.handlers.get(action)
        if handler:
            return await handler(task)
        return await self._monitor_account(task)

    def start(self):
        self._running = True
        logger.info("\U0001f7e2 TikTokAuditorAgent started")

    def stop(self):
        self._running = False
        logger.info("\U0001f534 TikTokAuditorAgent stopped")


if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.INFO)
        agent = TikTokAuditorAgent()
        agent.start()
        result = await agent.handle_task({
            "action": "MONITOR_TIKTOK_ACCOUNT",
            "username": "tiktok"
        })
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(main())
