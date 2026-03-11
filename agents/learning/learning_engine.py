#!/usr/bin/env python3
"""
LearningEngine — محرك التعلم الموحد لـ NOOGH

يوحّد:
  - AutonomousLearner  (مصادر خارجية: GitHub, arXiv, HN, Reddit)
  - ContinuousTrainingLoop (عصبونات + paper trading)
  - AdaptiveCurriculum   (تحديد ما يجب تعلمه بعد)
  - KnowledgeConsolidator (دمج وترتيب المعرفة)
"""
from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("LearningEngine")


# ──────────────────────────────────────────────────────────────────────────────
# Enums & Data classes
# ──────────────────────────────────────────────────────────────────────────────

class LearningDomain(str, Enum):
    TRADING   = "trading"       # استراتيجيات التداول
    AI        = "ai"            # نماذج الذكاء الاصطناعي
    SYSTEMS   = "systems"       # هندسة الأنظمة
    RESEARCH  = "research"      # أوراق بحثية
    HEURISTIC = "heuristic"     # تعلم إرشادي من النتائج


@dataclass
class KnowledgeItem:
    source: str
    domain: LearningDomain
    title: str
    content: str
    url: str = ""
    utility: float = 0.75
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        h = hashlib.md5(self.title.encode()).hexdigest()[:10]
        return f"learned:{self.domain.value}:{self.source}:{h}"


@dataclass
class LearningCycleResult:
    cycle_id: int
    started_at: str
    finished_at: str
    items_collected: int
    items_injected: int
    domains: Dict[str, int]
    elapsed_sec: float
    errors: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Shared Memory Store
# ──────────────────────────────────────────────────────────────────────────────

class SharedMemoryStore:
    """واجهة موحدة لـ shared_memory.sqlite"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self):
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS beliefs (
                    key         TEXT PRIMARY KEY,
                    value       TEXT,
                    utility_score REAL DEFAULT 0.75,
                    domain      TEXT DEFAULT 'general',
                    updated_at  REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_cycles (
                    cycle_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    data        TEXT,
                    created_at  REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON beliefs(domain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_utility ON beliefs(utility_score DESC)")

    def upsert(self, item: KnowledgeItem):
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO beliefs
                    (key, value, utility_score, domain, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item.key,
                    json.dumps({
                        "title": item.title,
                        "content": item.content,
                        "url": item.url,
                        "source": item.source,
                        "metadata": item.metadata,
                    }, ensure_ascii=False),
                    item.utility,
                    item.domain.value,
                    item.timestamp,
                ),
            )

    def get_top(self, domain: Optional[LearningDomain] = None, limit: int = 20) -> List[Dict]:
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            if domain:
                rows = conn.execute(
                    "SELECT key, value, utility_score FROM beliefs WHERE domain=? ORDER BY utility_score DESC LIMIT ?",
                    (domain.value, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT key, value, utility_score FROM beliefs ORDER BY utility_score DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [{"key": r[0], **json.loads(r[1]), "utility": r[2]} for r in rows]

    def log_cycle(self, result: LearningCycleResult):
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute(
                "INSERT INTO learning_cycles (data, created_at) VALUES (?, ?)",
                (json.dumps(result.__dict__), time.time()),
            )

    def decay_old_items(self, days: int = 30, decay_rate: float = 0.05):
        """تخفيض utility للعناصر القديمة تدريجياً"""
        cutoff = time.time() - days * 86400
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute(
                "UPDATE beliefs SET utility_score = MAX(0.1, utility_score - ?) WHERE updated_at < ?",
                (decay_rate, cutoff),
            )


# ──────────────────────────────────────────────────────────────────────────────
# Adaptive Curriculum
# ──────────────────────────────────────────────────────────────────────────────

class AdaptiveCurriculum:
    """
    يقرر ما يجب تعلمه بعد بناءً على:
    - أداء التداول (win rate / drawdown)
    - حجم المعرفة الحالية لكل domain
    - الأخطاء الأخيرة
    """

    DOMAIN_WEIGHTS: Dict[LearningDomain, float] = {
        LearningDomain.TRADING:   0.40,
        LearningDomain.AI:        0.25,
        LearningDomain.SYSTEMS:   0.15,
        LearningDomain.RESEARCH:  0.15,
        LearningDomain.HEURISTIC: 0.05,
    }

    def __init__(self, store: SharedMemoryStore):
        self.store = store
        self._performance_cache: Dict = {}

    def update_performance(self, win_rate: float, drawdown: float):
        self._performance_cache = {"win_rate": win_rate, "drawdown": drawdown}
        # إذا خسارة عالية → زيادة وزن التعلم عن التداول
        if win_rate < 0.50 or drawdown > 0.10:
            self.DOMAIN_WEIGHTS[LearningDomain.TRADING] = min(0.65, self.DOMAIN_WEIGHTS[LearningDomain.TRADING] + 0.05)
            logger.info("📚 Curriculum: رفع وزن TRADING بسبب أداء منخفض")

    def get_priorities(self) -> List[tuple]:
        """ترتيب الـ domains حسب الأولوية الحالية"""
        return sorted(self.DOMAIN_WEIGHTS.items(), key=lambda x: -x[1])

    def should_focus_on(self, domain: LearningDomain) -> bool:
        return self.DOMAIN_WEIGHTS.get(domain, 0) >= 0.15


# ──────────────────────────────────────────────────────────────────────────────
# Knowledge Consolidator
# ──────────────────────────────────────────────────────────────────────────────

class KnowledgeConsolidator:
    """
    يدمج ويرتب المعرفة المكتسبة:
    - يحذف التكرارات (deduplication)
    - يرفع utility للعناصر المؤكدة من مصادر متعددة
    - يُجري decay للعناصر القديمة
    """

    SIMILARITY_THRESHOLD = 0.85

    def __init__(self, store: SharedMemoryStore):
        self.store = store

    def consolidate(self, new_items: List[KnowledgeItem]) -> List[KnowledgeItem]:
        seen_titles: Dict[str, KnowledgeItem] = {}
        consolidated = []

        for item in new_items:
            # normalize title
            norm = item.title.lower().strip()
            if norm in seen_titles:
                # تعزيز الـ utility إذا تأكد من مصدرين
                existing = seen_titles[norm]
                existing.utility = min(0.98, existing.utility + 0.05)
                existing.metadata["confirmed_by"] = existing.metadata.get("confirmed_by", []) + [item.source]
            else:
                seen_titles[norm] = item
                consolidated.append(item)

        logger.info("🔗 Consolidator: %d → %d (بعد dedup)", len(new_items), len(consolidated))
        return consolidated

    def run_decay(self, days: int = 30):
        self.store.decay_old_items(days=days)
        logger.info("⏳ Decay: خُفّضت utility لعناصر +%d يوم", days)


# ──────────────────────────────────────────────────────────────────────────────
# Learning Engine (الواجهة الرئيسية)
# ──────────────────────────────────────────────────────────────────────────────

class LearningEngine:
    """
    المحرك الرئيسي — يُشغَّل من الـ Orchestrator أو مستقلاً.

    الاستخدام:
        engine = LearningEngine()
        await engine.run_cycle()           # دورة واحدة
        await engine.run_continuous(1800)  # كل 30 دقيقة
    """

    VERSION = "3.0.0"

    def __init__(self, db_path: Optional[Path] = None):
        root = Path(__file__).resolve().parent.parent.parent
        self.db_path = db_path or (root / "data" / "shared_memory.sqlite")
        self.store = SharedMemoryStore(self.db_path)
        self.curriculum = AdaptiveCurriculum(self.store)
        self.consolidator = KnowledgeConsolidator(self.store)
        self._cycle_count = 0
        self._running = False
        logger.info("🧠 LearningEngine v%s جاهز — DB: %s", self.VERSION, self.db_path)

    # ------------------------------------------------------------------
    # Data Collectors
    # ------------------------------------------------------------------

    async def _collect_github(self) -> List[KnowledgeItem]:
        import urllib.request
        url = "https://api.github.com/search/repositories?q=AI+trading+agent+quant&sort=stars&per_page=10"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NOOGH-LearningEngine/3.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read().decode())
            items = []
            for repo in data.get("items", []):
                items.append(KnowledgeItem(
                    source="github",
                    domain=LearningDomain.AI if "ai" in (repo.get("description") or "").lower() else LearningDomain.TRADING,
                    title=repo["full_name"],
                    content=(repo.get("description") or "")[:300],
                    url=repo["html_url"],
                    utility=min(0.95, 0.70 + repo.get("stargazers_count", 0) / 50000),
                    metadata={"stars": repo.get("stargazers_count", 0), "language": repo.get("language")},
                ))
            logger.info("🐙 GitHub: %d repos", len(items))
            return items
        except Exception as e:
            logger.warning("GitHub collect error: %s", e)
            return []

    async def _collect_arxiv(self) -> List[KnowledgeItem]:
        import urllib.request, re
        feeds = [
            ("http://export.arxiv.org/rss/cs.AI",  LearningDomain.AI),
            ("http://export.arxiv.org/rss/q-fin.TR", LearningDomain.TRADING),
        ]
        items = []
        for feed_url, domain in feeds:
            try:
                req = urllib.request.Request(feed_url, headers={"User-Agent": "NOOGH/3.0"})
                with urllib.request.urlopen(req, timeout=12) as r:
                    content = r.read().decode("utf-8", errors="ignore")
                titles = re.findall(r"<title>(.+?)</title>", content)
                links = re.findall(r"<link>(.+?)</link>", content)
                descs = re.findall(r"<description>(.+?)</description>", content, re.DOTALL)
                for t, l, d in zip(titles[1:6], links[1:6], descs[1:6]):
                    title = re.sub(r"<[^>]+>", "", t).strip()
                    items.append(KnowledgeItem(
                        source="arxiv",
                        domain=domain,
                        title=title,
                        content=re.sub(r"<[^>]+>", "", d).strip()[:400],
                        url=l.strip(),
                        utility=0.85,
                    ))
            except Exception as e:
                logger.warning("arXiv collect error [%s]: %s", feed_url, e)
        logger.info("📜 arXiv: %d papers", len(items))
        return items

    async def _collect_hackernews(self) -> List[KnowledgeItem]:
        import urllib.request
        try:
            with urllib.request.urlopen("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10) as r:
                ids = json.loads(r.read())[:15]
            items = []
            for sid in ids:
                try:
                    with urllib.request.urlopen(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=6) as r:
                        s = json.loads(r.read())
                    if s.get("type") != "story":
                        continue
                    items.append(KnowledgeItem(
                        source="hackernews",
                        domain=LearningDomain.SYSTEMS,
                        title=s.get("title", ""),
                        content=s.get("title", ""),
                        url=s.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                        utility=min(0.90, 0.70 + s.get("score", 0) / 2000),
                        metadata={"score": s.get("score", 0)},
                    ))
                except Exception:
                    continue
            logger.info("🟠 HackerNews: %d stories", len(items))
            return items
        except Exception as e:
            logger.warning("HN collect error: %s", e)
            return []

    async def _collect_heuristic(self) -> List[KnowledgeItem]:
        """
        تعلم إرشادي: يقرأ نتائج التداول الأخيرة ويستخلص دروساً.
        """
        items = []
        trades_file = self.db_path.parent / "paper_trades_with_neurons.jsonl"
        if not trades_file.exists():
            return []
        try:
            trades = []
            with open(trades_file) as f:
                for line in f:
                    try:
                        trades.append(json.loads(line))
                    except Exception:
                        continue

            wins = [t for t in trades[-100:] if t.get("outcome") == "WIN"]
            losses = [t for t in trades[-100:] if t.get("outcome") == "LOSS"]
            win_rate = len(wins) / max(1, len(wins) + len(losses))

            lesson = f"Win rate = {win_rate:.1%} من آخر {len(trades[-100:])} صفقة"
            items.append(KnowledgeItem(
                source="heuristic",
                domain=LearningDomain.HEURISTIC,
                title=f"Trading Lesson @ {datetime.now().strftime('%Y-%m-%d')}",
                content=lesson,
                utility=0.88,
                metadata={"win_rate": win_rate, "sample_size": len(trades[-100:])},
            ))
            # إخبار الـ curriculum بالأداء
            self.curriculum.update_performance(win_rate, 0.0)
        except Exception as e:
            logger.warning("Heuristic collect error: %s", e)
        return items

    # ------------------------------------------------------------------
    # Core Cycle
    # ------------------------------------------------------------------

    async def run_cycle(self) -> LearningCycleResult:
        self._cycle_count += 1
        cycle_id = self._cycle_count
        started_at = datetime.now().isoformat()
        t0 = time.time()
        errors: List[str] = []

        logger.info("🎬 ═══ Learning Cycle #%d START ═══", cycle_id)

        # جمع المعرفة بشكل متوازٍ
        collectors = [
            self._collect_github(),
            self._collect_arxiv(),
            self._collect_hackernews(),
            self._collect_heuristic(),
        ]
        results = await asyncio.gather(*collectors, return_exceptions=True)

        raw_items: List[KnowledgeItem] = []
        for res in results:
            if isinstance(res, Exception):
                errors.append(str(res))
            else:
                raw_items.extend(res)

        # دمج وتنظيف
        consolidated = self.consolidator.consolidate(raw_items)

        # حقن في الذاكرة
        injected = 0
        for item in consolidated:
            try:
                self.store.upsert(item)
                injected += 1
            except Exception as e:
                errors.append(f"upsert error: {e}")

        # decay دوري (كل 10 دورات)
        if cycle_id % 10 == 0:
            self.consolidator.run_decay()

        elapsed = round(time.time() - t0, 2)
        domain_counts: Dict[str, int] = {}
        for item in consolidated:
            domain_counts[item.domain.value] = domain_counts.get(item.domain.value, 0) + 1

        result = LearningCycleResult(
            cycle_id=cycle_id,
            started_at=started_at,
            finished_at=datetime.now().isoformat(),
            items_collected=len(raw_items),
            items_injected=injected,
            domains=domain_counts,
            elapsed_sec=elapsed,
            errors=errors,
        )
        self.store.log_cycle(result)

        logger.info(
            "🎬 ═══ Cycle #%d DONE | collected=%d injected=%d elapsed=%.1fs ═══",
            cycle_id, len(raw_items), injected, elapsed,
        )
        return result

    # ------------------------------------------------------------------
    # Continuous mode
    # ------------------------------------------------------------------

    async def run_continuous(self, interval_sec: int = 1800):
        """تشغيل مستمر — يوقفه SIGTERM أو asyncio.CancelledError"""
        self._running = True
        logger.info("♾️  LearningEngine: تشغيل مستمر كل %ds", interval_sec)
        try:
            while self._running:
                await self.run_cycle()
                logger.info("💤 نائم %ds ...", interval_sec)
                await asyncio.sleep(interval_sec)
        except asyncio.CancelledError:
            logger.info("🛑 LearningEngine أُوقف بشكل نظيف")
            self._running = False

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_knowledge(self, domain: Optional[LearningDomain] = None, limit: int = 20) -> List[Dict]:
        """أعلى العناصر utility لـ domain معين"""
        return self.store.get_top(domain=domain, limit=limit)

    def curriculum_priorities(self) -> List[tuple]:
        return self.curriculum.get_priorities()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ap = argparse.ArgumentParser(description="NOOGH LearningEngine v3")
    ap.add_argument("--once", action="store_true", help="دورة واحدة فقط")
    ap.add_argument("--interval", type=int, default=1800, help="الفاصل الزمني (ثانية)")
    ap.add_argument("--top", type=int, default=10, help="اعرض أفضل N عناصر بعد التعلم")
    args = ap.parse_args()

    engine = LearningEngine()

    async def _main():
        if args.once:
            result = await engine.run_cycle()
            print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
            print("\n📚 أفضل ما تعلّمناه:")
            for item in engine.get_knowledge(limit=args.top):
                print(f"  [{item.get('utility', 0):.2f}] {item.get('title', '')[:70]}")
        else:
            await engine.run_continuous(args.interval)

    asyncio.run(_main())
