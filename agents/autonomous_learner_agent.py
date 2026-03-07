#!/home/noogh/projects/noogh_unified_system/src/.venv/bin/python3
"""
NOOGH Autonomous Learning Agent — نظام التعلم الذاتي الكامل

يعمل بشكل دوري:
  1. SEARCH   → يبحث عن محتوى تقني في YouTube
  2. WATCH    → يستخرج الترجمات (أفضل من OCR)
  3. LEARN    → يحلل ويلخص المعرفة
  4. INJECT   → يحقن في ذاكرة NOOGH (beliefs + observations)
  5. EVOLVE   → يقترح ابتكاراً جديداً بناءً على ما تعلمه

يعمل كل 30 دقيقة في الخلفية.
"""

import sys
import os
import json
import time
import re
import subprocess
import sqlite3
import shutil
import hashlib
import glob
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# إضافة مسار المشروع
sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
sys.path.append(str(Path(__file__).parent.parent))

from unified_core.evolution.innovation_storage import InnovationStorage
from proto_generated.evolution import learning_pb2

# إعداد المسارات
HOME = str(Path.home())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | autonomous_learner | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/noogh/projects/noogh_unified_system/src/logs/autonomous_learner.log"),
    ]
)
logger = logging.getLogger("autonomous_learner")

# ─── الإعدادات ───────────────────────────────────────────────
YT_DLP = (shutil.which("yt-dlp")
          or "/home/noogh/projects/noogh_unified_system/src/.venv/bin/yt-dlp")

DB_PATH = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
SEEN_FILE = "/home/noogh/.noogh/autonomous_learner_seen.json"
INTERVAL_SECONDS = 1800  # كل 30 دقيقة

# مواضيع احتياطية (تم توسيعها لتشمل مسارات: التداول، البرمجة، البروتوكولات، الخوارزميات، الذكاء الاصطناعي، وطبقات النظام، وأعمق من ذلك)
FALLBACK_TOPICS = [
    # 📉 مسار التداول المالي الكمي والبنية الدقيقة (Advanced Quant)
    "high frequency trading market microstructure order book imbalance",
    "advanced options pricing quantitative models stochastics",
    
    # 💻 مسار حوسبة الأداء العالي (HPC & GPU)
    "gpu cuda parallel computing optimization hardware architecture",
    "lock-free data structures multi-threading c++ python bindings",
    
    # 🌐 مسار الأنظمة الموزعة والتوافق (Distributed Systems)
    "distributed systems consensus algorithms raft paxos deep dive",
    "network protocols tcp ip udp kernel bypass direct memory access",
    
    # 📐 مسار التشفير والمعرفة الصفرية (Cryptography & ZK)
    "advanced cryptography elliptic curves zero knowledge proofs zk-snarks",
    
    # 🧠 مسار الذكاء الاصطناعي (AI & LLM Training)
    "deep learning backpropagation neural network architecture optimization",
    "reinforcement learning proximal policy optimization for trading algorithms",
    
    # 🏴‍☠️ مسار الهندسة العكسية والأمان (Reverse Engineering & Binary Security)
    "reverse engineering software binary exploitation memory corruption",
    "operating system kernel internals rootkits low level security",

    # ⚛️ مسار الحوسبة الكمية (Quantum Computing)
    "quantum computing algorithms shor grover qiskit quantum cryptography",

    # ⛓️ مسار القيمة المستخرجة من المعدنين والمراجحة على البلوكشين (MEV & On-chain)
    "miner extractable value mev arbitrage smart contract exploitation defi",

    # ⚡ مسار تصميم شرائح الدوائر (Hardware FPGA) وتسريع النواة
    "fpga programming verilog vhdl ultra low latency trading hardware",
    "linux kernel ebpf xdp high performance networking packet processing",

    # 🧮 مسار التحقق الرسمي والمنطق المعقد (Formal Verification)
    "formal verification tla+ system design correctness proofs",
    "stochastic calculus ito lemma black scholes mathematical finance",
]

# قنوات YouTube المتخصصة (تعلم موجّه - الأكاديمية والمتقدمة)
YOUTUBE_CHANNELS = [
    ("@3blue1brown",          "3Blue1Brown",             "رياضيات الذكاء الاصطناعي"),
    ("@TwoMinutePapers",      "Two Minute Papers",       "أبحاث الذكاء الاصطناعي وعلوم الحاسوب"),
    ("@lexfridman",           "Lex Fridman",             "مقابلات خبراء AI والأنظمة المعقدة"),
    ("@ByteByteGo",           "ByteByteGo",              "System Design & Architecture"),
    ("@mitocw",               "MIT OpenCourseWare",      "أعرق علوم الحاسب والرياضيات"),
    ("@stanfordonline",       "Stanford Online",         "أبحاث ستانفورد والذكاء الاصطناعي"),
    ("@YCombinator",          "Y Combinator",            "مسرعة الأعمال وتطوير الشركات التقنية"),
    ("@CppCon",               "CppCon",                  "أعمق تفاصيل C++ والأداء العالي"),
    ("@DEFCONConference",     "DEFCONConference",        "مؤتمرات الأمن السيبراني والهندسة العكسية"),
    ("@freecodecamp",         "freeCodeCamp.org",        "برمجة متكاملة وتطوير النظام"),
    ("@HFTGuy",               "The HFT Guy / Quant",     "High Frequency Trading & Quant"),
    ("@ArxivInsights",        "Arxiv Insights",          "تبسيط أوراق بحثية متقدمة في الذكاء الاصطناعي"),
    ("@geohot",               "George Hotz Archive",     "شروحات هندسة عكسية وبرمجة النظام"),
]


class NooghAutonomousLearner:
    """NOOGH يبحث ويتعلم بنفسه"""

    def __init__(self):
        self._seen: set = self._load_seen()
        self._fallback_idx = int(time.time()) % len(FALLBACK_TOPICS)
        logger.info(f"🤖 Autonomous Learner initialized | {len(self._seen)} videos seen")

    # ── اختيار الموضوع ذاتياً ────────────────────────
    def _choose_topic_autonomously(self) -> str:
        """NOOGH يقرر بنفسه ماذا يحتاج أن يتعلم"""
        candidates = []  # (score, query, reason)

        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            # ① فجوات المعرفة: مفاهيم بـ utility منخفض
            cur.execute("""
                SELECT key, utility_score FROM beliefs
                WHERE key LIKE 'learned_concept:%'
                AND utility_score < 0.70
                ORDER BY utility_score ASC LIMIT 5
            """)
            for row in cur.fetchall():
                concept = row[0].replace('learned_concept:', '').strip()
                score = 1.0 - float(row[1] or 0.5)  # ضعيف = أولوية عالية
                query = f"{concept} tutorial deep dive"
                candidates.append((score + 0.3, query, f"weak belief: {concept}"))

            # ② أهداف النظام الحالية (من الذاكرة)
            cur.execute("""
                SELECT key, value FROM beliefs
                WHERE key LIKE 'goal:%' OR key LIKE 'objective:%'
                ORDER BY updated_at DESC LIMIT 3
            """)
            for row in cur.fetchall():
                try:
                    val = json.loads(row[1])
                    goal_text = str(val.get('description', val.get('text', str(val))))[:60]
                    if goal_text and len(goal_text) > 10:
                        candidates.append((0.8, f"{goal_text} tutorial",
                                           f"active goal: {goal_text[:40]}"))
                except Exception:
                    pass

            # ③ مجالات لم يتعلم منها كثيراً بعد
            cur.execute("""
                SELECT key FROM beliefs WHERE key LIKE 'learned_concept:%'
            """)
            learned_tags = {r[0].replace('learned_concept:', '') for r in cur.fetchall()}
            all_tags = {
                "🔒 Security", "🦀 Rust", "🌐 JavaScript", "📐 Algorithms",
                "📊 Complexity", "📨 Messaging", "⚡ Cache/Redis", "🧩 Microservices"
            }
            unknown_tags = all_tags - learned_tags
            tag_to_query = {
                "🔒 Security": "cybersecurity software engineering",
                "🦀 Rust": "rust programming systems",
                "🌐 JavaScript": "javascript event loop async",
                "📐 Algorithms": "algorithms data structures coding",
                "📊 Complexity": "big O notation complexity analysis",
                "📨 Messaging": "kafka message queue architecture",
                "⚡ Cache/Redis": "redis caching strategies",
                "🧩 Microservices": "microservices patterns design",
            }
            for tag in list(unknown_tags)[:2]:
                if tag in tag_to_query:
                    candidates.append((0.6, tag_to_query[tag], f"unknown tag: {tag}"))

            conn.close()
        except Exception as e:
            logger.debug(f"  DB read for topic selection: {e}")

        # ④ فحص أحدث أخطاء النظام من السجلات
        try:
            log_path = "/home/noogh/projects/noogh_unified_system/src/logs/agent_daemon_live.log"
            errors = []
            with open(log_path) as f:
                for line in f.readlines()[-200:]:
                    if 'ERROR' in line or 'FAILED' in line:
                        errors.append(line)

            error_keywords = {
                'timeout': 'async timeout handling python',
                'memory': 'memory management python optimization',
                'import': 'python module dependency management',
                'connection': 'network connection retry patterns',
                'permission': 'linux file permissions security',
                'cuda': 'GPU CUDA optimization deep learning',
                'json': 'json parsing error handling python',
            }
            error_text = ' '.join(errors[-10:]).lower()
            for kw, query in error_keywords.items():
                if kw in error_text:
                    candidates.append((0.9, query, f"system error: {kw}"))
                    break  # واحد يكفي
        except Exception:
            pass

        # استشارة العقل المدبر لاختيار أفضل موضوع بدلاً من الاعتماد على قواعد ثابتة
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            context_lines = [f"- {c[2]} (Priority: {c[0]:.2f})" for c in candidates[:6]]
            context_str = "\n".join(context_lines)
            
            try:
                import asyncio
                from unified_core.neural_bridge import NeuralEngineClient
                
                prompt = f"""You are the Cognitive Brain of NOOGH. The Autonomous Learner is deciding what to learn next.
Based on the current system context (errors, weak beliefs, active goals), generate the absolute BEST technical search query.
The query MUST be a highly specialized, concise technical search term (max 2-5 words) that addresses these issues.
It MUST be in English. Return ONLY the exact search query string without any other text, reasoning, or quotes.

Current System Context:
{context_str}
"""
                logger.info("🧠 Asking Neural Brain for autonomous topic selection...")
                
                async def ask_brain():
                    import os
                    # Force client to use the local qwen2.5 model
                    os.environ["VLLM_MODEL_NAME"] = "qwen2.5:7b"
                    # We use vllm mode which is OpenAI compatible locally
                    async with NeuralEngineClient(base_url="http://localhost:11434", mode="vllm") as bridge:
                        resp = await bridge.think(prompt, depth="fast")
                        return resp.get("content", "")
                
                # Run the async bridge call within our sync method
                llm_response = asyncio.run(ask_brain())
                
                # Cleanup potential quotation marks or newlines
                clean_llm_query = re.sub(r'[\"\']', '', llm_response.split('\n')[0]).strip()
                
                if 2 < len(clean_llm_query) < 80:
                    logger.info(f"  🎯 Brain autonomously decided to learn: '{clean_llm_query}'")
                    return clean_llm_query
                else:
                    logger.warning(f"  ⚠️ Brain returned invalid query length: {clean_llm_query}")
            except Exception as e:
                logger.warning(f"  ⚠️ Brain consultation failed: {e}. Falling back to heuristics.")
            
            # fallback to heuristic if LLM fails
            score, query, reason = candidates[0]
            logger.info(f"  🎯 Topic chosen by heuristic: '{query}'")
            logger.info(f"     Reason: {reason} (score={score:.2f})")
            return query

        # fallback
        topic = FALLBACK_TOPICS[self._fallback_idx % len(FALLBACK_TOPICS)]
        self._fallback_idx += 1
        logger.info(f"  📋 Fallback topic: '{topic}'")
        return topic

    # ── السجل المرئي ─────────────────────────────────
    def _load_seen(self) -> set:
        Path(SEEN_FILE).parent.mkdir(parents=True, exist_ok=True)
        try:
            return set(json.load(open(SEEN_FILE)))
        except Exception:
            return set()

    def _save_seen(self):
        with open(SEEN_FILE, "w") as f:
            json.dump(list(self._seen), f)

    # ── 1. SEARCH ────────────────────────────────────
    def search_youtube(self, query: str, max_results: int = 5) -> List[Dict]:
        """البحث في YouTube عن محتوى تقني"""
        logger.info(f"🔍 Searching: '{query}'")
        search_url = f"ytsearch{max_results}:{query}"
        cmd = [
            YT_DLP,
            "--flat-playlist",
            "--print", "%(id)s|||%(title)s|||%(duration)s|||%(channel)s",
            "--no-warnings", "--quiet",
            search_url
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            results = []
            for line in r.stdout.strip().split("\n"):
                if "|||" not in line:
                    continue
                parts = line.split("|||")
                if len(parts) < 3:
                    continue
                vid_id = parts[0].strip()
                if vid_id in self._seen:
                    continue
                results.append({
                    "id": vid_id,
                    "title": parts[1].strip(),
                    "duration": parts[2].strip(),
                    "channel": parts[3].strip() if len(parts) > 3 else "?",
                    "url": f"https://youtu.be/{vid_id}"
                })
            logger.info(f"  Found {len(results)} new videos")
            return results
        except Exception as e:
            logger.warning(f"  Search failed: {e}")
            return []

    # ── GitHub: بحث عن مستوديات ────────────────────
    def search_github(self, query: str, max_repos: int = 3) -> List[Dict]:
        """GitHub API — يبحث عن مستوديات ذات صلة"""
        logger.info(f"🐙 GitHub search: '{query}'")
        # تبسيط الاستعلام (GitHub public API — لا يحتاج token)
        clean_q = re.sub(r'[^\w\s]', '', query)[:60].strip().replace(' ', '+')
        url = (f"https://api.github.com/search/repositories"
               f"?q={clean_q}&sort=stars&order=desc&per_page={max_repos}")
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'NOOGH-AutonomousLearner/1.0',
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            repos = []
            for item in data.get('items', [])[:max_repos]:
                repo_id = f"gh_{item['id']}"
                if repo_id in self._seen:
                    continue
                repos.append({
                    "id": repo_id,
                    "name": item['full_name'],
                    "description": item.get('description', '') or '',
                    "stars": item.get('stargazers_count', 0),
                    "language": item.get('language', '?'),
                    "topics": item.get('topics', []),
                    "url": item['html_url'],
                    "readme_url": f"https://raw.githubusercontent.com/{item['full_name']}/HEAD/README.md",
                    "default_branch": item.get('default_branch', 'main'),
                })
            logger.info(f"  Found {len(repos)} new repos")
            return repos
        except Exception as e:
            logger.warning(f"  GitHub search failed: {e}")
            return []

    def read_github_repo(self, repo: Dict) -> str:
        """يقرأ README + أبرز ملف Python من المستودى"""
        content_parts = []
        content_parts.append(f"Repo: {repo['name']}")
        content_parts.append(f"Stars: {repo['stars']} | Lang: {repo['language']}")
        content_parts.append(f"Topics: {', '.join(repo['topics'][:5])}")
        if repo['description']:
            content_parts.append(f"Description: {repo['description']}")

        # README
        try:
            req = urllib.request.Request(
                repo['readme_url'],
                headers={'User-Agent': 'NOOGH-AutonomousLearner/1.0'}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                readme = r.read().decode('utf-8', errors='ignore')
            # تنظيف Markdown
            readme = re.sub(r'```[\s\S]*?```', '[code block]', readme)
            readme = re.sub(r'!\[.*?\]\(.*?\)', '', readme)
            readme = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', readme)
            readme = re.sub(r'#{1,6}\s', '', readme)
            readme_clean = ' '.join(readme.split())[:1200]
            content_parts.append(f"\nREADME: {readme_clean}")
            logger.info(f"  📚 README: {len(readme_clean)} chars")
        except Exception as e:
            logger.debug(f"  README fetch failed: {e}")

        full_content = '\n'.join(content_parts)
        return full_content[:2000]

    def inject_github_to_noogh(self, repo: Dict, content: str, tags: List[str]) -> bool:
        """حقن معرفة GitHub في ذاكرة NOOGH"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cur = conn.cursor()

            obs_key = f"gh_{repo['id']}_{int(time.time())}"
            obs_val = json.dumps({
                "source": "github_autonomous_learner",
                "type": "repository_readme",
                "repo": repo['name'],
                "stars": repo['stars'],
                "language": repo['language'],
                "topics": repo['topics'],
                "content_preview": content[:500],
                "url": repo['url'],
                "tags": tags,
                "topic": self._current_topic,
            }, ensure_ascii=False)

            cur.execute(
                "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
                (obs_key, obs_val, time.time())
            )

            # تقوية المعتقدات ذات الصلة (مصدر code = utility أعلى)
            for tag in tags[:3]:
                belief_key = f"learned_concept:{tag}"
                cur.execute("SELECT value, utility_score FROM beliefs WHERE key=?", (belief_key,))
                row = cur.fetchone()
                if row:
                    try:
                        old_val = json.loads(row[0])
                    except Exception:
                        old_val = {}
                    old_val['github_repos'] = old_val.get('github_repos', 0) + 1
                    old_val['last_github'] = repo['name']
                    # GitHub code يعطي utility bonus أعلى (0.07 بدل 0.05)
                    new_utility = min(0.95, float(row[1] or 0.5) + 0.07)
                    cur.execute(
                        "UPDATE beliefs SET value=?, utility_score=?, updated_at=? WHERE key=?",
                        (json.dumps(old_val), new_utility, time.time(), belief_key)
                    )
                    logger.info(f"  📈 GitHub reinforced: {tag} (utility={new_utility:.2f})")
                else:
                    belief_val = json.dumps({
                        "concept": tag, "source": "github",
                        "repo": repo['name'], "stars": repo['stars'],
                        "count": 1, "first_seen": datetime.now().isoformat(),
                    })
                    cur.execute(
                        "INSERT INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
                        (belief_key, belief_val, 0.70, time.time())  # ابداً 0.70 للكود
                    )
                    logger.info(f"  🔗 New GitHub belief: {tag} (0.70)")

            conn.commit()
            conn.close()
            logger.info(f"  ✅ GitHub injected: {obs_key}")
            return True
        except Exception as e:
            logger.error(f"  ❌ GitHub injection failed: {e}")
            return False


    def is_video_relevant(self, video: Dict) -> bool:
        """فحص العنوان والوصف قبل تحميل Transcript — توفير موارد"""
        title_lower = video.get("title", "").lower()

        # ① رفض الموضوعات غير التقنية فوراً
        blacklist_keywords = [
            "music", "guitar", "song", "interview", "podcast",
            "comedy", "gaming", "vlog", "reaction", "review",
            "unboxing", "trailer", "news", "politics"
        ]
        if any(word in title_lower for word in blacklist_keywords):
            logger.info(f"  ⏭️ Skipped (blacklist): {video['title'][:50]}")
            return False

        # ② قبول المحتوى التقني والتداول
        whitelist_keywords = [
            # برمجة عامة وبنية تحتية وتشفير وقرصنة وكمية وهاردوير
            "algorithm", "code", "programming", "python", "rust", "c++", "gpu", "cuda",
            "database", "api", "system", "architecture", "performance", "consensus", "paxos", "raft",
            "machine learning", "neural", "data structure", "optimization", "distributed",
            "security", "linux", "docker", "kubernetes", "kernel", "cryptography", "zero knowledge", 
            "reverse engineering", "binary", "hardware", "memory", "bypass", "dma",
            "quantum", "qiskit", "mev", "arbitrage", "defi", "smart contract", "fpga", "verilog", "vhdl",
            "ebpf", "xdp", "packet", "formal verification", "tla+", "stochastic", "calculus",
            # تداول ومال
            "trading", "algorithmic trading", "quantitative", "finance", "stochastics",
            "market", "order flow", "technical indicator", "backtest", "microstructure", "imbalance",
            "portfolio", "risk management", "quant", "strategy", "hft",
            "binance", "crypto", "futures", "options"
        ]
        if any(word in title_lower for word in whitelist_keywords):
            return True

        # ③ رفض إذا لم يطابق أي معيار
        logger.info(f"  ⏭️ Skipped (no match): {video['title'][:50]}")
        return False

    def extract_transcript(self, video: Dict) -> str:
        """استخراج الترجمة التلقائية"""
        vid_id = video["id"]
        out_prefix = f"/tmp/noogh_learn_{vid_id}"

        cmd = [
            YT_DLP,
            "--write-auto-sub", "--skip-download",
            "--sub-lang", "en",
            "--sub-format", "vtt",
            "-o", out_prefix,
            "--no-warnings", "--quiet",
            video["url"]
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=25)
        except Exception:
            pass

        # قراءة ملف الترجمة
        vtt_files = glob.glob(f"{out_prefix}*.vtt")
        if not vtt_files:
            logger.debug(f"  No subtitles for {vid_id}")
            return f"[عنوان]: {video['title']}"

        try:
            with open(vtt_files[0]) as f:
                raw = f.read()
            os.remove(vtt_files[0])

            # تنظيف VTT
            lines = raw.split("\n")
            clean = []
            seen_lines = set()
            for l in lines:
                l = re.sub(r"<[^>]+>", "", l).strip()
                if (l and l not in seen_lines
                        and "-->" not in l
                        and not l.startswith("WEBVTT")
                        and not l.startswith("Kind")
                        and not l.startswith("Language")
                        and not l.startswith("NOTE")
                        and not l.isdigit()):
                    seen_lines.add(l)
                    clean.append(l)

            transcript = " ".join(clean)
            logger.info(f"  📝 Transcript: {len(transcript)} chars")
            return transcript[:1500]
        except Exception as e:
            logger.warning(f"  Transcript parse error: {e}")
            return f"[عنوان]: {video['title']}"

    # ── 3. LEARN (Summarize) ──────────────────────────
    def extract_concepts(self, video: Dict, transcript: str) -> Dict:
        """استخراج المفاهيم الrئيسية من المحتوى"""
        title = video["title"].lower()
        text = (title + " " + transcript).lower()

        tags = []
        concept_map = {
            # برمجة وتقنية
            "linux":          "🐧 Linux/OS",
            "docker":         "🐳 Containers",
            "kubernetes":     "⚓ Kubernetes",
            "api":            "🔌 API Design",
            "database":       "🗄️ Database",
            "redis":          "⚡ Cache/Redis",
            "kafka":          "📨 Messaging",
            "microservice":   "🧩 Microservices",
            "machine learn":  "🤖 ML",
            "neural":         "🧠 Neural Networks",
            "async":          "⚙️ Async/Concurrency",
            "algorithm":      "📐 Algorithms",
            "big o":          "📊 Complexity",
            "python":         "🐍 Python",
            "javascript":     "🌐 JavaScript",
            "rust":           "🦀 Rust",
            "security":       "🔒 Security",
            "system design":  "🏗️ System Design",
            "architecture":   "🏛️ Architecture",
            "performance":    "🚀 Performance",
            # تداول ومال
            "trading":        "📈 Trading",
            "algorithmic trading": "🤖 Algo Trading",
            "quantitative":   "📊 Quant Finance",
            "technical indicator": "📉 Technical Analysis",
            "backtest":       "🔬 Backtesting",
            "order flow":     "📊 Order Flow",
            "market making":  "💱 Market Making",
            "risk management": "⚖️ Risk Mgmt",
            "portfolio":      "💼 Portfolio",
            "binance":        "🟡 Binance",
            "futures":        "📜 Futures",
            "options":        "📋 Options",
            "crypto":         "₿ Crypto",
        }
        for keyword, tag in concept_map.items():
            if keyword in text:
                tags.append(tag)

        # قياس جودة المحتوى
        quality = "HIGH" if len(transcript) > 300 else "MEDIUM" if len(transcript) > 100 else "LOW"

        return {
            "video_id": video["id"],
            "title": video["title"],
            "channel": video["channel"],
            "duration": video["duration"],
            "url": video["url"],
            "transcript_preview": transcript[:400],
            "tags": tags,
            "quality": quality,
            "learned_at": datetime.now().isoformat(),
            "topic_query": self._current_topic,
        }

    # ── 4. INJECT (into NOOGH Memory) ─────────────────
    def inject_to_noogh(self, knowledge: Dict) -> bool:
        """حقن المعرفة في ذاكرة NOOGH الحقيقية"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cur = conn.cursor()

            # ① تسجيل كـ Observation
            obs_key = f"yt_{knowledge['video_id']}_{int(time.time())}"
            obs_val = json.dumps({
                "source": "youtube_autonomous_learner",
                "type": "video_transcript",
                "title": knowledge["title"],
                "channel": knowledge["channel"],
                "tags": knowledge["tags"],
                "transcript": knowledge["transcript_preview"],
                "url": knowledge["url"],
                "quality": knowledge["quality"],
                "topic": self._current_topic,
            }, ensure_ascii=False)
            cur.execute(
                "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?, ?, ?)",
                (obs_key, obs_val, time.time())
            )

            # ② تحديث/إضافة Belief لكل tag مكتشف
            for tag in knowledge["tags"][:3]:
                belief_key = f"learned_concept:{tag}"
                cur.execute(
                    "SELECT value, utility_score FROM beliefs WHERE key=?",
                    (belief_key,)
                )
                row = cur.fetchone()
                if row:
                    try:
                        old_val = json.loads(row[0])
                    except Exception:
                        old_val = {}
                    new_count = old_val.get("count", 1) + 1
                    new_val = {**old_val, "count": new_count,
                               "last_seen": knowledge["learned_at"]}
                    new_utility = min(0.95, float(row[1] or 0.5) + 0.05)
                    cur.execute(
                        "UPDATE beliefs SET value=?, utility_score=?, updated_at=? WHERE key=?",
                        (json.dumps(new_val), new_utility, time.time(), belief_key)
                    )
                    logger.info(f"  📈 Belief reinforced: {tag} (utility={new_utility:.2f})")
                else:
                    belief_val = json.dumps({
                        "concept": tag,
                        "source": "youtube",
                        "video": knowledge["title"],
                        "count": 1,
                        "first_seen": knowledge["learned_at"],
                    })
                    cur.execute(
                        "INSERT INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
                        (belief_key, belief_val, 0.65, time.time())
                    )
                    logger.info(f"  🆕 New belief: {tag}")

            conn.commit()
            conn.close()
            logger.info(f"  ✅ Injected: {obs_key}")
            return True

        except sqlite3.OperationalError as e:
            logger.warning(f"  ⚠️ DB issue: {e}")
            return False
        except Exception as e:
            logger.error(f"  ❌ Injection failed: {e}")
            return False


    # ── 5. EVOLVE (Suggest Innovation) ────────────────
    def suggest_innovation(self, knowledge: Dict):
        """اقتراح ابتكار جديد بناءً على المعرفة"""
        tags = knowledge.get("tags", [])
        title = knowledge.get("title", "")

        # خريطة المعرفة → الابتكار المقترح
        innovations = {
            "🗄️ Database":      ("optimize_memory_queries",
                                 "استخدام EXPLAIN QUERY PLAN وتحسين الفهارس في MemoryStore"),
            "🚀 Performance":   ("async_parallel_scan",
                                 "تحسين المعالجة المتوازية في parallel_processor"),
            "🔒 Security":      ("security_audit_enhance",
                                 "تعزيز security_hardening بفحص معمق"),
            "🏗️ System Design": ("architecture_review",
                                 "مراجعة بنية agent_daemon والتبسيط"),
            "🤖 ML":            ("model_fine_tune_trigger",
                                 "تشغيل دورة fine-tuning على البيانات الجديدة"),
            "⚙️ Async/Concurrency": ("event_loop_optimize",
                                     "تحسين دورة الأحداث في neural_bridge"),
        }

        for tag in tags:
            if tag in innovations:
                inno_type, rationale = innovations[tag]
                storage = InnovationStorage()
                pb_inno = learning_pb2.Innovation()
                pb_inno.id = f"{inno_type}_{int(time.time())}"
                pb_inno.status = learning_pb2.INNOVATION_STATUS_SUGGESTED
                pb_inno.title = f"Dynamic Innovation: {inno_type}"
                pb_inno.reasoning = rationale
                pb_inno.description = rationale
                pb_inno.trigger_event = f"YouTube: {title[:60]}"
                if tags:
                    pb_inno.context['tags'] = ",".join(tags)
                pb_inno.context['original_type'] = inno_type
                pb_inno.suggested_at.seconds = int(time.time())
                
                # Enum map
                str_type = inno_type.lower()
                if 'security' in str_type:
                    pb_inno.innovation_type = learning_pb2.INNOVATION_TYPE_FEATURE
                elif 'optimize' in str_type or 'parallel' in str_type or 'async' in str_type:
                    pb_inno.innovation_type = learning_pb2.INNOVATION_TYPE_PERFORMANCE
                elif 'refactor' in str_type or 'architecture' in str_type:
                    pb_inno.innovation_type = learning_pb2.INNOVATION_TYPE_REFACTOR
                else:
                    pb_inno.innovation_type = learning_pb2.INNOVATION_TYPE_UNSPECIFIED
                
                storage.append(pb_inno)
                
                logger.info(f"  💡 Innovation suggested (PB): {inno_type}")
                logger.info(f"     Rationale: {rationale}")
                break

    # ── arXiv: أبحاث علمية ──────────────────────────
    def search_arxiv(self, query: str, max_results: int = 3) -> List[Dict]:
        """يبحث في arXiv عن أحدث الأبحاث"""
        logger.info(f"📚 arXiv search: '{query[:40]}'")
        clean_q = re.sub(r'[^\w\s]', '', query)[:60].strip().replace(' ', '+')
        url = (f"http://export.arxiv.org/api/query"
               f"?search_query=all:{clean_q}&start=0&max_results={max_results}"
               f"&sortBy=submittedDate&sortOrder=descending")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'NOOGH/1.0'})
            with urllib.request.urlopen(req, timeout=12) as r:
                xml = r.read().decode('utf-8')

            # parsing XML manually (avoid dependencies)
            papers = []
            entries = xml.split('<entry>')
            for entry in entries[1:max_results+1]:
                def _tag(t):
                    m = re.search(f'<{t}[^>]*>([\\s\\S]*?)</{t}>', entry)
                    return m.group(1).strip() if m else ''

                paper_id = re.search(r'<id>(.*?)</id>', entry)
                pid = paper_id.group(1).split('/')[-1] if paper_id else ''
                arxiv_key = f"arxiv_{pid}"
                if arxiv_key in self._seen:
                    continue

                title   = re.sub(r'\s+', ' ', _tag('title'))
                summary = re.sub(r'\s+', ' ', _tag('summary'))[:600]
                # authors
                authors = re.findall(r'<name>(.*?)</name>', entry)
                author_str = ', '.join(authors[:3])

                papers.append({
                    "id": arxiv_key,
                    "title": title,
                    "summary": summary,
                    "authors": author_str,
                    "url": f"https://arxiv.org/abs/{pid}",
                    "source": "arxiv",
                })
            logger.info(f"  Found {len(papers)} new papers")
            return papers
        except Exception as e:
            logger.warning(f"  arXiv failed: {e}")
            return []

    def inject_arxiv_to_noogh(self, paper: Dict, tags: List[str]) -> bool:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cur = conn.cursor()
            obs_key = f"{paper['id']}_{int(time.time())}"
            obs_val = json.dumps({
                "source": "arxiv",
                "type": "research_paper",
                "title": paper['title'],
                "authors": paper['authors'],
                "summary": paper['summary'],
                "url": paper['url'],
                "tags": tags,
                "topic": self._current_topic,
            }, ensure_ascii=False)
            cur.execute(
                "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
                (obs_key, obs_val, time.time())
            )
            # أبحاث = utility bonus 0.08 (الأعلى)
            for tag in tags[:2]:
                belief_key = f"learned_concept:{tag}"
                cur.execute("SELECT value, utility_score FROM beliefs WHERE key=?", (belief_key,))
                row = cur.fetchone()
                if row:
                    new_u = min(0.95, float(row[1] or 0.5) + 0.08)
                    cur.execute("UPDATE beliefs SET utility_score=?, updated_at=? WHERE key=?",
                                (new_u, time.time(), belief_key))
                    logger.info(f"  📚 arXiv reinforced: {tag} ({new_u:.2f})")
                else:
                    cur.execute(
                        "INSERT INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
                        (belief_key,
                         json.dumps({"concept": tag, "source": "arxiv", "paper": paper['title'], "count": 1}),
                         0.75, time.time())  # ابحاث = 0.75 مبدئياً
                    )
                    logger.info(f"  📜 New arXiv belief: {tag} (0.75)")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"  ❌ arXiv injection: {e}")
            return False

    # ── Stack Overflow: حلول الأخطاء ───────────────────
    def search_stackoverflow(self, query: str, max_results: int = 3) -> List[Dict]:
        """يبحث عن أجوبة Stack Overflow للمشكلات التقنية"""
        logger.info(f"🟧 Stack Overflow: '{query[:40]}'")
        q = urllib.parse.quote(query[:80])
        url = (f"https://api.stackexchange.com/2.3/search/advanced"
               f"?order=desc&sort=votes&q={q}&site=stackoverflow"
               f"&filter=withbody&pagesize={max_results}")
        try:
            req = urllib.request.Request(url, headers={'Accept-Encoding': 'gzip', 'User-Agent': 'NOOGH/1.0'})
            import gzip
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read()
                try:
                    data = json.loads(gzip.decompress(raw).decode())
                except Exception:
                    data = json.loads(raw.decode())

            questions = []
            for item in data.get('items', [])[:max_results]:
                qid = f"so_{item['question_id']}"
                if qid in self._seen:
                    continue
                body = re.sub(r'<[^>]+>', ' ', item.get('body', ''))[:500]
                questions.append({
                    "id": qid,
                    "title": item.get('title', ''),
                    "body": body,
                    "score": item.get('score', 0),
                    "answers": item.get('answer_count', 0),
                    "tags": item.get('tags', []),
                    "url": item.get('link', ''),
                    "source": "stackoverflow",
                })
            logger.info(f"  Found {len(questions)} questions")
            return questions
        except Exception as e:
            logger.warning(f"  Stack Overflow failed: {e}")
            return []

    def inject_stackoverflow_to_noogh(self, q: Dict, tags: List[str]) -> bool:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cur = conn.cursor()
            obs_key = f"{q['id']}_{int(time.time())}"
            obs_val = json.dumps({
                "source": "stackoverflow",
                "type": "qa_solution",
                "title": q['title'],
                "body": q['body'],
                "score": q['score'],
                "so_tags": q['tags'],
                "url": q['url'],
                "tags": tags,
                "topic": self._current_topic,
            }, ensure_ascii=False)
            cur.execute(
                "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
                (obs_key, obs_val, time.time())
            )
            # حلول عملية = utility +0.06
            for tag in tags[:2]:
                belief_key = f"learned_concept:{tag}"
                cur.execute("SELECT utility_score FROM beliefs WHERE key=?", (belief_key,))
                row = cur.fetchone()
                if row:
                    new_u = min(0.95, float(row[0] or 0.5) + 0.06)
                    cur.execute("UPDATE beliefs SET utility_score=?, updated_at=? WHERE key=?",
                                (new_u, time.time(), belief_key))
                    logger.info(f"  🟧 SO reinforced: {tag} ({new_u:.2f})")
                else:
                    cur.execute(
                        "INSERT INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
                        (belief_key,
                         json.dumps({"concept": tag, "source": "stackoverflow", "count": 1}),
                         0.68, time.time())
                    )
                    logger.info(f"  🟧 New SO belief: {tag}")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"  ❌ SO injection: {e}")
            return False

    # ── قنوات YouTube المتخصصة ────────────────────────
    def fetch_from_curated_channel(self) -> List[Dict]:
        """يختار قناة من القائمة المنسقة ويجلب أحدث فيديو لم يُرَ"""
        import random
        channels = [c for c in YOUTUBE_CHANNELS]
        random.shuffle(channels)
        for handle, name, desc in channels:
            url = f"https://www.youtube.com/{handle}/videos"
            cmd = [
                YT_DLP, "--flat-playlist", "--playlist-end", "3",
                "--print", "%(id)s|||%(title)s|||%(duration)s",
                "--no-warnings", "--quiet", url
            ]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                for line in r.stdout.strip().split("\n"):
                    if "|||" not in line:
                        continue
                    parts = line.split("|||")
                    vid_id = parts[0].strip()
                    if vid_id in self._seen:
                        continue
                    logger.info(f"  📡 Channel [{name}]: {parts[1][:50]}")
                    return [{
                        "id": vid_id,
                        "title": parts[1].strip(),
                        "duration": parts[2].strip() if len(parts) > 2 else "?",
                        "channel": name,
                        "url": f"https://youtu.be/{vid_id}",
                        "channel_desc": desc,
                    }]
            except Exception:
                continue
        return []

    def run_once(self):
        """دورة تعلم ذاتية — NOOGH يختار الموضوع بنفسه"""
        # ← هنا يقرر NOOGH ماذا يحتاج
        self._current_topic = self._choose_topic_autonomously()

        logger.info("═" * 55)
        logger.info(f"🧠 LEARNING CYCLE | {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"📌 Topic: {self._current_topic}")
        logger.info("═" * 55)

        # تنظيف الموضوع من الـ emojis قبل استخدامه في البحث
        clean_topic = re.sub(r'[^\x00-\x7F]+', '', self._current_topic).strip()
        clean_topic = re.sub(r'\s+', ' ', clean_topic).strip()
        if not clean_topic or len(clean_topic) < 5:
            clean_topic = FALLBACK_TOPICS[self._fallback_idx % len(FALLBACK_TOPICS)]
        
        # استخراج أول كلمتين/ثلاث كلمات لاستخدامها في بحث APIs (لتجنب 0 نتائج بسبب طول النصوص)
        short_query = " ".join(clean_topic.split()[:3])
        if len(short_query) < 5:
            short_query = clean_topic[:30]

        logger.info(f"   🔤 Full Topic: '{clean_topic[:60]}...'")
        logger.info(f"   🔤 Short API query: '{short_query}'")

        total_learned = 0

        # ══ A. YouTube (بحث) ════════════════════════
        logger.info("\n🎬 [YouTube Search] ...")
        videos = self.search_youtube(clean_topic, max_results=4)
        learned_yt = 0
        for video in videos[:2]:
            logger.info(f"\n🎬 {video['title'][:60]}")

            # ← فحص مبكر قبل تحميل Transcript (توفير موارد)
            if not self.is_video_relevant(video):
                self._seen.add(video['id'])
                continue

            transcript = self.extract_transcript(video)
            knowledge = self.extract_concepts(video, transcript)
            logger.info(f"   Tags: {', '.join(knowledge['tags'][:5]) or 'none'}")
            if knowledge['tags']:
                ok = self.inject_to_noogh(knowledge)
                if ok:
                    self.suggest_innovation(knowledge)
                    learned_yt += 1
            self._seen.add(video['id'])
        logger.info(f"  ✓ YouTube: {learned_yt}")
        total_learned += learned_yt

        # ══ B. قنوات منتقاة (3Blue1Brown, Sentdex, ...) ════
        logger.info("\n📡 [Curated Channels] ...")
        ch_videos = self.fetch_from_curated_channel()
        learned_ch = 0
        for video in ch_videos[:1]:
            logger.info(f"\n📡 {video['channel']}: {video['title'][:55]}")

            # ← فحص مبكر (حتى للقنوات الموثوقة — Lex Fridman يخلط محتوى)
            if not self.is_video_relevant(video):
                self._seen.add(video['id'])
                continue

            transcript = self.extract_transcript(video)
            knowledge = self.extract_concepts(video, transcript)
            logger.info(f"   Tags: {', '.join(knowledge['tags'][:5]) or 'none'}")
            if knowledge['tags']:
                ok = self.inject_to_noogh(knowledge)
                if ok:
                    self.suggest_innovation(knowledge)
                    learned_ch += 1
            self._seen.add(video['id'])
        logger.info(f"  ✓ Channels: {learned_ch}")
        total_learned += learned_ch

        # ══ C. GitHub ════════════════════════════════
        logger.info("\n🐙 [GitHub] ...")
        github_query = re.sub(r'[^\w\s]', '', short_query)[:50]
        repos = self.search_github(github_query, max_repos=3)
        learned_gh = 0
        for repo in repos[:2]:
            logger.info(f"\n🐙 {repo['name']} ★{repo['stars']:,}")
            content = self.read_github_repo(repo)
            knowledge_gh = self.extract_concepts(
                {"id": repo['id'], "title": repo['name'],
                 "channel": "GitHub", "duration": "N/A", "url": repo['url']}, content)
            for t in repo['topics'][:3]:
                if t:
                    knowledge_gh['tags'].append(f"🏷️ {t}")
            logger.info(f"   Tags: {', '.join(knowledge_gh['tags'][:5]) or 'none'}")
            if knowledge_gh['tags']:
                ok = self.inject_github_to_noogh(repo, content, knowledge_gh['tags'])
                if ok:
                    self.suggest_innovation(knowledge_gh)
                    learned_gh += 1
            self._seen.add(repo['id'])
        logger.info(f"  ✓ GitHub: {learned_gh}")
        total_learned += learned_gh

        # ══ D. arXiv ═════════════════════════════════
        logger.info("\n📚 [arXiv] ...")
        papers = self.search_arxiv(short_query, max_results=3)
        learned_ax = 0
        for paper in papers[:2]:
            logger.info(f"\n📜 {paper['title'][:60]}")
            logger.info(f"   👤 {paper['authors'][:50]}")
            ax_knowledge = self.extract_concepts(
                {"id": paper['id'], "title": paper['title'],
                 "channel": "arXiv", "duration": "N/A", "url": paper['url']},
                paper['summary']
            )
            logger.info(f"   Tags: {', '.join(ax_knowledge['tags'][:5]) or 'none'}")
            if ax_knowledge['tags']:
                ok = self.inject_arxiv_to_noogh(paper, ax_knowledge['tags'])
                if ok:
                    self.suggest_innovation(ax_knowledge)
                    learned_ax += 1
            self._seen.add(paper['id'])
        logger.info(f"  ✓ arXiv: {learned_ax}")
        total_learned += learned_ax

        # ══ E. Stack Overflow ══════════════════════════
        logger.info("\n🟧 [Stack Overflow] ...")
        questions = self.search_stackoverflow(short_query, max_results=3)
        learned_so = 0
        for q in questions[:2]:
            logger.info(f"\n🟧 {q['title'][:60]} [+{q['score']}]")
            so_knowledge = self.extract_concepts(
                {"id": q['id'], "title": q['title'],
                 "channel": "StackOverflow", "duration": "N/A", "url": q['url']},
                q['body'] + " " + " ".join(q['tags'])
            )
            if so_knowledge['tags']:
                ok = self.inject_stackoverflow_to_noogh(q, so_knowledge['tags'])
                if ok:
                    learned_so += 1
            self._seen.add(q['id'])
        logger.info(f"  ✓ StackOverflow: {learned_so}")
        total_learned += learned_so

        self._save_seen()
        logger.info(
            f"\n✅ Cycle complete | "
            f"YT={learned_yt} + CH={learned_ch} + GH={learned_gh} "
            f"+ arXiv={learned_ax} + SO={learned_so} = {total_learned} units"
        )
        logger.info(f"   Total seen: {len(self._seen)} items")
        return total_learned

    # ── حلقة لا نهائية ────────────────────────────────
    def run_forever(self, interval: int = INTERVAL_SECONDS):
        """يعمل إلى الأبد — يتعلم كل {interval} ثانية"""
        logger.info(f"🚀 Starting autonomous learning loop (every {interval//60} min)")
        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                logger.info("⛔ Stopped by user")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}", exc_info=True)

            logger.info(f"💤 Sleeping {interval//60} minutes...")
            time.sleep(interval)


# ─── Main ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NOOGH Autonomous Learner")
    parser.add_argument("--once", action="store_true", help="run one cycle and exit")
    parser.add_argument("--interval", type=int, default=INTERVAL_SECONDS,
                        help="loop interval in seconds")
    args = parser.parse_args()

    learner = NooghAutonomousLearner()

    if args.once:
        learner.run_once()
    else:
        learner.run_forever(args.interval)
