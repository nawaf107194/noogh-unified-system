#!/usr/bin/env python3
"""
NOOGH Autonomous Learning Agent — FIXED v2
يتعلم من: GitHub API + arXiv RSS + HackerNews + Reddit
بدون yt-dlp او proto_generated — stdlib فقط
"""
import sys, os, json, time, re, urllib.request, sqlite3, logging, hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Dynamic source path detection
SRC = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, SRC)

LOG_DIR = os.path.join(SRC, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | autonomous_learner | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "autonomous_learner.log")),
    ],
)
logger = logging.getLogger("autonomous_learner")

HOME = str(Path.home())
DB_PATH = os.path.join(SRC, "data/shared_memory.sqlite")


def _fetch(url: str, timeout: int = 12) -> Optional[str]:
    """جلب URL بامان"""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "NOOGH-Learner/2.0 (autonomous AI agent)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"fetch failed {url[:60]}: {e}")
        return None


def _db_inject(key: str, value: dict, utility: float = 0.80):
    """حقن في shared_memory"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=8)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO beliefs (key,value,utility_score,updated_at) VALUES (?,?,?,?)",
            (key, json.dumps(value, ensure_ascii=False), utility, time.time()),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB inject error: {e}")


class AutonomousLearner:
    """وكيل التعلم الذاتي — بدون dependencies خارجية"""

    # ── مصادر التعلم ──────────────────────────────
    SOURCES = {
        "github": "https://api.github.com/search/repositories?q=AI+LLM+agent&sort=stars&per_page=8",
        "arxiv_ai": "http://export.arxiv.org/rss/cs.AI",
        "arxiv_lg": "http://export.arxiv.org/rss/cs.LG",
        "hackernews": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "reddit_ml": "https://www.reddit.com/r/MachineLearning/top.json?limit=8&t=day",
    }

    def learn_github(self) -> List[Dict]:
        content = _fetch(self.SOURCES["github"])
        if not content:
            return []
        items = []
        try:
            data = json.loads(content)
            for repo in data.get("items", []):
                items.append({
                    "source": "github",
                    "title": repo["full_name"],
                    "description": (repo.get("description") or "")[:200],
                    "url": repo["html_url"],
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language", ""),
                })
        except Exception as e:
            logger.warning(f"GitHub parse error: {e}")
        logger.info(f"\U0001f419 GitHub: {len(items)} repos learned")
        return items

    def learn_arxiv(self) -> List[Dict]:
        items = []
        for key in ("arxiv_ai", "arxiv_lg"):
            content = _fetch(self.SOURCES[key])
            if not content:
                continue
            titles = re.findall(r"<title>(.+?)</title>", content)
            links = re.findall(r"<link>(.+?)</link>", content)
            summaries = re.findall(r"<description>(.+?)</description>", content, re.DOTALL)
            for title, link, summary in zip(titles[1:6], links[1:6], summaries[1:6]):
                items.append({
                    "source": "arxiv",
                    "title": re.sub(r"<[^>]+>", "", title).strip(),
                    "url": link.strip(),
                    "summary": re.sub(r"<[^>]+>", "", summary).strip()[:300],
                })
        logger.info(f"\U0001f4dc arXiv: {len(items)} papers learned")
        return items

    def learn_hackernews(self) -> List[Dict]:
        content = _fetch(self.SOURCES["hackernews"])
        if not content:
            return []
        items = []
        try:
            story_ids = json.loads(content)[:12]
            for sid in story_ids:
                story_data = _fetch(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5)
                if not story_data:
                    continue
                s = json.loads(story_data)
                if s.get("type") != "story":
                    continue
                items.append({
                    "source": "hackernews",
                    "title": s.get("title", ""),
                    "url": s.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                    "score": s.get("score", 0),
                })
        except Exception as e:
            logger.warning(f"HN error: {e}")
        logger.info(f"\U0001f7e7 HackerNews: {len(items)} stories learned")
        return items

    def learn_reddit(self) -> List[Dict]:
        content = _fetch(self.SOURCES["reddit_ml"])
        if not content:
            return []
        items = []
        try:
            data = json.loads(content)
            for post in data["data"]["children"]:
                p = post["data"]
                items.append({
                    "source": "reddit",
                    "title": p.get("title", ""),
                    "url": p.get("url", ""),
                    "score": p.get("score", 0),
                    "selftext": (p.get("selftext") or "")[:300],
                })
        except Exception as e:
            logger.warning(f"Reddit error: {e}")
        logger.info(f"\U0001f4e1 Reddit: {len(items)} posts learned")
        return items

    def inject_all(self, items: List[Dict]):
        """حقن كل ما تم تعلمه في shared_memory"""
        injected = 0
        for item in items:
            key_hash = hashlib.md5(item["title"].encode()).hexdigest()[:10]
            key = f"learned:{item['source']}:{key_hash}"
            # تحديد utility بناءً على popularity
            score = item.get("stars", item.get("score", 0))
            utility = min(0.95, 0.75 + score / 50000)
            _db_inject(key, item, utility)
            injected += 1
        logger.info(f"\u2705 Injected {injected} items into shared_memory")

    def run_cycle(self) -> dict:
        """دورة تعلم كاملة"""
        logger.info("\U0001f3ac ═══ LEARNING CYCLE START ═══")
        start = time.time()
        all_items = []
        all_items.extend(self.learn_github())
        all_items.extend(self.learn_arxiv())
        all_items.extend(self.learn_hackernews())
        all_items.extend(self.learn_reddit())

        if all_items:
            self.inject_all(all_items)

        elapsed = round(time.time() - start, 1)
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_learned": len(all_items),
            "sources": {
                "github": sum(1 for i in all_items if i["source"] == "github"),
                "arxiv": sum(1 for i in all_items if i["source"] == "arxiv"),
                "hackernews": sum(1 for i in all_items if i["source"] == "hackernews"),
                "reddit": sum(1 for i in all_items if i["source"] == "reddit"),
            },
            "elapsed_sec": elapsed,
        }
        # حقن الملخص
        _db_inject("orchestrator:learning_cycle", summary, 0.90)
        logger.info(f"\U0001f3ac ═══ DONE: {len(all_items)} items in {elapsed}s ═══\n")
        return summary


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="NOOGH Autonomous Learner")
    p.add_argument("--once", action="store_true", help="دورة واحدة")
    p.add_argument("--interval", type=int, default=1800, help="كل N ثانية")
    args = p.parse_args()

    learner = AutonomousLearner()
    if args.once:
        result = learner.run_cycle()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        while True:
            learner.run_cycle()
            logger.info(f"\U0001f4a4 Sleeping {args.interval}s...")
            time.sleep(args.interval)
