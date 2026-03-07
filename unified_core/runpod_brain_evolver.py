#!/usr/bin/env python3
"""
RunPod Brain - FINAL Self-Evolving Version (vLLM / OpenAI-format)

What you get:
- Ultra-strict AST sandbox gate (no imports, no loops, no try/with, no exec, only s.get + min/max)
- JSON-only with <json> tags
- Consensus generation (N candidates) + best selection
- Neuron manifest registry with fitness tracking
- Evolution loop: select parents -> mutate/crossover -> save -> prune
- Safe dedup by code hash
- Robust retries + backoff + jitter
- No execution of model code (static validation only)

Integration:
- You run your backtest separately and call update_fitness({hash: fitness, ...})
- Then call evolve_round(...) to generate the next generation based on winners
"""

import os
import json
import ast
import asyncio
import aiohttp
import hashlib
import random
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RunPodBrainEvolver")


# ============================================================
# Utils
# ============================================================

def utc_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


# ============================================================
# JSON extraction (prefer <json> tags; fallback brace-balance)
# ============================================================

def extract_json_payload(text: str) -> Optional[str]:
    tag = re.search(r"<json>\s*(\{.*\})\s*</json>", text, re.DOTALL)
    if tag:
        return tag.group(1)

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return None


# ============================================================
# Ultra strict AST security gate
# ============================================================

class NeuronSecurityGate:
    """
    Hard rules:
    - Exactly one def, name must match expected
    - Signature: def name(s):
    - No imports, loops, try/with/raise, lambda/class/async, comprehensions
    - Only attribute access allowed: s.get
    - Only free calls allowed: min, max
    - Every return must be a literal 3-tuple: (bool, float, str)
    """

    FORBIDDEN_NODE_TYPES = (
        ast.Import, ast.ImportFrom,
        ast.For, ast.While, ast.AsyncFor,
        ast.Try, ast.With, ast.AsyncWith,
        ast.Raise, ast.Assert,
        ast.Lambda, ast.ClassDef,
        ast.AsyncFunctionDef,
        ast.Global, ast.Nonlocal,
        ast.Yield, ast.YieldFrom,
        ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
        ast.Await,
    )

    FORBIDDEN_CALL_NAMES = {
        "eval", "exec", "compile", "open", "__import__",
        "globals", "locals", "getattr", "setattr", "vars", "input",
        "dir", "help", "type", "super",
        "memoryview", "bytearray", "bytes",
    }

    ALLOWED_FREE_CALLS = {"min", "max"}

    def __init__(self, max_lines: int = 25):
        self.max_lines = max_lines

    def validate(self, code: str, expected_name: str) -> Tuple[bool, str]:
        code = (code or "").strip()
        if not code:
            return False, "Empty code"

        if len(code.splitlines()) > self.max_lines:
            return False, f"Too many lines (> {self.max_lines})"

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"SyntaxError: {e}"

        # forbid certain nodes
        for node in ast.walk(tree):
            if isinstance(node, self.FORBIDDEN_NODE_TYPES):
                return False, f"Forbidden syntax: {type(node).__name__}"

        # exactly one function
        funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        if len(funcs) != 1:
            return False, "Must define exactly one function"

        fn = funcs[0]
        if fn.name != expected_name:
            return False, f"Function name mismatch (expected {expected_name})"

        if len(fn.args.args) != 1 or fn.args.args[0].arg != "s":
            return False, "Signature must be def name(s)"

        if fn.decorator_list:
            return False, "Decorators not allowed"

        # validate attribute and calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # only allow s.get
                if not (isinstance(node.value, ast.Name) and node.value.id == "s" and node.attr == "get"):
                    return False, "Forbidden attribute access"

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if not (isinstance(node.func.value, ast.Name) and node.func.value.id == "s" and node.func.attr == "get"):
                        return False, "Only s.get(...) attribute calls allowed"
                elif isinstance(node.func, ast.Name):
                    name = node.func.id
                    if name in self.FORBIDDEN_CALL_NAMES:
                        return False, f"Forbidden call: {name}"
                    if name not in self.ALLOWED_FREE_CALLS:
                        return False, f"Only min/max allowed (got {name})"
                else:
                    return False, "Forbidden call type"

            if isinstance(node, ast.Name):
                if node.id in {"__builtins__", "builtins"}:
                    return False, "Forbidden name usage"
                if node.id.startswith("__") and node.id not in {"__name__"}:
                    return False, "Forbidden dunder usage"

        # returns must be 3-tuple literals
        returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
        if not returns:
            return False, "No return found"

        for r in returns:
            if r.value is None:
                return False, "Return must return a value"
            if not isinstance(r.value, ast.Tuple) or len(r.value.elts) != 3:
                return False, "Every return must be a literal 3-tuple (bool,float,str)"

        return True, "Safe"


# ============================================================
# Config
# ============================================================

@dataclass(frozen=True)
class RunPodConfig:
    base_url: str
    api_key: str
    model: str

    temperature: float = 0.2
    top_p: float = 0.9
    presence_penalty: float = 0.05
    frequency_penalty: float = 0.05
    max_tokens: int = 1200

    retries: int = 4
    backoff_base: float = 0.8
    backoff_cap: float = 8.0

    timeout_total: int = 600
    timeout_connect: int = 30
    timeout_read: int = 600


@dataclass(frozen=True)
class EvolutionConfig:
    consensus_n: int = 3            # number of candidates per generation
    keep_top_k: int = 20            # keep best K in manifest (by fitness)
    parents_k: int = 6              # pick top K as parent pool
    children_per_round: int = 2     # expect 2 neurons (long_filter, short_filter) per candidate
    min_fitness_to_keep: float = 0.0
    mutation_strength: str = "medium"  # low/medium/high


# ============================================================
# Main Brain Evolver
# ============================================================

class RunPodBrainEvolver:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "noogh-teacher",
        neurons_dir: str = "./neurons",
        analysis_dir: str = "./analysis",
        manifest_path: str = "./neurons_manifest.json",
        evo: Optional[EvolutionConfig] = None,
    ):
        cfg = RunPodConfig(
            base_url=(base_url or os.getenv("RUNPOD_BASE_URL", "")).rstrip("/"),
            api_key=(api_key or os.getenv("RUNPOD_API_KEY", "EMPTY")),
            model=os.getenv("RUNPOD_MODEL", model),
        )
        self.cfg = cfg
        self.evo = evo or EvolutionConfig()

        self.neurons_dir = Path(neurons_dir)
        self.analysis_dir = Path(analysis_dir)
        self.manifest_path = Path(manifest_path)

        self.neurons_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

        self.gate = NeuronSecurityGate(max_lines=25)

        self._session: Optional[aiohttp.ClientSession] = None

        logger.info("🧠 RunPodBrainEvolver initialized")
        logger.info(f"🔌 Base URL: {self.cfg.base_url}")
        logger.info(f"🤖 Model: {self.cfg.model}")
        logger.info(f"📜 Manifest: {self.manifest_path.resolve()}")

    async def aclose(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        timeout = aiohttp.ClientTimeout(
            total=self.cfg.timeout_total,
            connect=self.cfg.timeout_connect,
            sock_read=self.cfg.timeout_read,
        )
        self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    # ========================================================
    # 1) Fitness update (you call this after backtest)
    # ========================================================

    def update_fitness(self, fitness_by_hash: Dict[str, float]) -> Dict:
        """
        fitness_by_hash: { "abc123def456": 0.73, ... }
        fitness expected in [0..1], but we clamp.
        """
        manifest = self._load_manifest()
        updated = 0
        missing = 0

        index = {n.get("hash"): n for n in manifest.get("neurons", []) if isinstance(n, dict)}
        for h, f in fitness_by_hash.items():
            if h in index:
                index[h]["fitness"] = clamp01(safe_float(f, 0.0))
                index[h]["fitness_updated_utc"] = utc_iso()
                updated += 1
            else:
                missing += 1

        self._save_manifest(manifest)
        logger.info(f"📈 Fitness updated: {updated} | missing: {missing}")
        return {"updated": updated, "missing": missing}

    # ========================================================
    # 2) Evolution round (generate new neurons from best parents)
    # ========================================================

    async def evolve_round(self, historical_data: List[Dict], context: str = "") -> Dict:
        """
        One evolution step:
        - Summarize market
        - Select parents from manifest (top fitness)
        - Generate consensus candidates (N)
        - Validate + save new children
        - Prune manifest
        """
        summary = self._prepare_data_summary(historical_data)
        parents = self._select_parents()

        prompt = self._build_evolution_prompt(summary, context, parents)

        candidates: List[Dict] = []
        raw_responses: List[str] = []

        for i in range(self.evo.consensus_n):
            resp = await self._call_vllm(prompt)
            if not resp:
                continue
            raw_responses.append(resp)
            parsed = self._parse_response(resp)
            if parsed:
                candidates.append(parsed)

        selected = self._select_best_candidate(candidates)
        saved, blocked = self._validate_and_save(selected, summary, raw_prompt=prompt)

        # Save analysis snapshot
        analysis = {
            "ts_utc": utc_iso(),
            "summary": summary,
            "parents_used": [{"name": p["name"], "hash": p["hash"], "fitness": p.get("fitness", 0.0)} for p in parents],
            "candidates": len(candidates),
            "saved": saved,
            "blocked": blocked,
            "raw_samples": raw_responses[:3],  # keep small
        }
        self._save_analysis(analysis)

        # prune
        pruned = self.prune_manifest()

        return {
            "saved": saved,
            "blocked": blocked,
            "candidates": len(candidates),
            "parents": len(parents),
            "pruned": pruned,
            "ts_utc": utc_iso(),
        }

    # ========================================================
    # 3) Manifest prune (keep top K)
    # ========================================================

    def prune_manifest(self) -> Dict:
        manifest = self._load_manifest()
        neurons = manifest.get("neurons", [])
        if not isinstance(neurons, list):
            neurons = []

        # filter min fitness
        neurons = [n for n in neurons if isinstance(n, dict) and safe_float(n.get("fitness", 0.0)) >= self.evo.min_fitness_to_keep]

        # sort by fitness desc, then newer
        def keyfn(n):
            return (
                safe_float(n.get("fitness", 0.0)),
                n.get("created_utc", ""),
            )

        neurons.sort(key=keyfn, reverse=True)

        before = len(neurons)
        neurons = neurons[: self.evo.keep_top_k]
        after = len(neurons)

        manifest["neurons"] = neurons
        manifest["pruned_utc"] = utc_iso()
        self._save_manifest(manifest)

        logger.info(f"🧹 Pruned manifest: {before} -> {after}")
        return {"before": before, "after": after}

    # ========================================================
    # Data summary (same logic as earlier)
    # ========================================================

    def _prepare_data_summary(self, historical_data: List[Dict]) -> Dict:
        long_data = [d for d in historical_data if d.get("signal") == "LONG"]
        short_data = [d for d in historical_data if d.get("signal") == "SHORT"]

        def wins_losses(data):
            w = sum(1 for d in data if d.get("outcome") == "WIN")
            l = sum(1 for d in data if d.get("outcome") == "LOSS")
            return w, l

        lw, ll = wins_losses(long_data)
        sw, sl = wins_losses(short_data)

        def winrate(w, l):
            t = w + l
            return (w / t * 100.0) if t > 0 else 0.0

        long_wr = winrate(lw, ll)
        short_wr = winrate(sw, sl)

        avg_tbr = sum(safe_float(d.get("taker_buy_ratio", 0.5)) for d in long_data) / max(len(long_data), 1)
        long_atr = sum(safe_float(d.get("atr", 0)) for d in long_data) / max(len(long_data), 1)
        short_atr = sum(safe_float(d.get("atr", 0)) for d in short_data) / max(len(short_data), 1)
        avg_vol = sum(safe_float(d.get("volume", 0)) for d in short_data) / max(len(short_data), 1)

        dominant_side = "NEUTRAL"
        if long_wr > short_wr + 1e-9:
            dominant_side = "LONG"
        elif short_wr > long_wr + 1e-9:
            dominant_side = "SHORT"

        if long_atr > 30:
            vol_regime = "HIGH"
        elif long_atr > 20:
            vol_regime = "NORMAL"
        else:
            vol_regime = "LOW"

        return {
            "counts": {"total": len(historical_data), "long_total": len(long_data), "short_total": len(short_data)},
            "long": {"wins": lw, "losses": ll, "wr": long_wr, "avg_tbr": avg_tbr, "avg_atr": long_atr},
            "short": {"wins": sw, "losses": sl, "wr": short_wr, "avg_vol": avg_vol, "avg_atr": short_atr},
            "market": {"dominant_side": dominant_side, "volatility_regime": vol_regime},
        }

    # ========================================================
    # Parents selection
    # ========================================================

    def _select_parents(self) -> List[Dict]:
        manifest = self._load_manifest()
        neurons = manifest.get("neurons", [])
        if not isinstance(neurons, list):
            return []

        # sort by fitness desc
        def keyfn(n):
            return safe_float(n.get("fitness", 0.0))

        ranked = [n for n in neurons if isinstance(n, dict)]
        ranked.sort(key=keyfn, reverse=True)

        # take top parents_k
        parents = ranked[: self.evo.parents_k]
        return parents

    # ========================================================
    # Prompt building (Breeding + Mutation)
    # ========================================================

    def _build_evolution_prompt(self, summary: Dict, context: str, parents: List[Dict]) -> str:
        m = summary["market"]
        L = summary["long"]
        S = summary["short"]

        # Provide parent snippets (small and safe): last known code is not stored in manifest by default.
        # We can load file content from the saved neuron file names.
        parent_snippets = []
        for p in parents[: self.evo.parents_k]:
            f = p.get("file")
            if not f:
                continue
            path = self.neurons_dir / f
            if not path.exists():
                continue
            code = path.read_text(encoding="utf-8", errors="ignore")
            # keep only the function body section; limit length to reduce prompt size
            code_lines = code.splitlines()
            code_trim = "\n".join(code_lines[-40:])  # last 40 lines typically includes function
            parent_snippets.append({
                "name": p.get("name"),
                "hash": p.get("hash"),
                "fitness": p.get("fitness", 0.0),
                "code": code_trim
            })

        parents_json = json.dumps(parent_snippets, ensure_ascii=False)

        # Mutation strength guidance
        mut = self.evo.mutation_strength

        return f"""
You are evolving TWO ultra-safe Python trading filters for a live system.

Market snapshot:
- dominant_side: {m["dominant_side"]}
- volatility_regime: {m["volatility_regime"]}
- LONG_WR: {L["wr"]:.0f}% avg_tbr={L["avg_tbr"]:.2f} avg_atr={L["avg_atr"]:.0f}
- SHORT_WR: {S["wr"]:.0f}% avg_vol={S["avg_vol"]:.0f} avg_atr={S["avg_atr"]:.0f}
- context: {context}

Parents (best performers) as reference (DO NOT copy verbatim; improve them):
{parents_json}

EVOLUTION INSTRUCTIONS:
- Create improved children by mutating thresholds and logic.
- mutation_strength: {mut}
- Prefer simple adaptive thresholds based on volatility_regime and dominant_side.
- Keep max 3 conditions total per filter (rejects + boosters).
- Make reason strings concise and informative.

HARD RULES (must follow):
1) Output MUST be ONLY one JSON object wrapped in <json>...</json>. No other text.
2) Create exactly 2 neurons:
   - name: "long_filter"
   - name: "short_filter"
3) Each neuron "code" MUST:
   - define exactly one function with the same name and signature: def <name>(s):
   - use ONLY: s.get("key", default), numeric ops, comparisons, boolean ops
   - allowed calls: min(...), max(...)
   - NO imports, NO file access, NO attribute access except s.get
   - NO loops, NO try/with/raise/assert, NO lambdas/classes/async, NO comprehensions
   - max 25 lines per function
   - every return must return a literal 3-tuple: (bool, float, str)
   - confidence float MUST be clamped to [0,1] using min/max

Return format:
<json>{{
  "neurons":[
    {{"name":"long_filter","code":"..."}},
    {{"name":"short_filter","code":"..."}}
  ]
}}</json>
""".strip()

    # ========================================================
    # vLLM call with retries/backoff
    # ========================================================

    async def _call_vllm(self, prompt: str) -> Optional[str]:
        if not self.cfg.base_url:
            logger.error("❌ RUNPOD_BASE_URL missing")
            return None

        url = f"{self.cfg.base_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.cfg.api_key}",
        }
        payload = {
            "model": self.cfg.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.cfg.temperature,
            "top_p": self.cfg.top_p,
            "presence_penalty": self.cfg.presence_penalty,
            "frequency_penalty": self.cfg.frequency_penalty,
            "max_tokens": self.cfg.max_tokens,
            "stream": False,
        }

        session = await self._get_session()

        for attempt in range(self.cfg.retries + 1):
            try:
                async with session.post(url, headers=headers, json=payload) as resp:
                    txt = await resp.text()

                    if resp.status == 200:
                        data = json.loads(txt)
                        return data["choices"][0]["message"]["content"]

                    if resp.status in {408, 409, 429, 500, 502, 503, 504}:
                        raise RuntimeError(f"Retryable HTTP {resp.status}: {txt[:200]}")

                    logger.error(f"❌ Non-retryable HTTP {resp.status}: {txt[:500]}")
                    return None

            except (asyncio.TimeoutError, aiohttp.ClientError, RuntimeError) as e:
                if attempt >= self.cfg.retries:
                    logger.error(f"❌ API failed after retries: {type(e).__name__}: {e}")
                    return None
                backoff = min(self.cfg.backoff_cap, self.cfg.backoff_base * (2 ** attempt))
                jitter = random.uniform(0.0, 0.25)
                sleep_s = backoff + jitter
                logger.warning(f"⚠ retry {attempt+1}/{self.cfg.retries} in {sleep_s:.2f}s: {type(e).__name__}: {e}")
                await asyncio.sleep(sleep_s)

        return None

    # ========================================================
    # Parse model response
    # ========================================================

    def _parse_response(self, response_text: str) -> Optional[Dict]:
        raw = extract_json_payload(response_text)
        if not raw:
            return None
        try:
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                return None
            return obj
        except json.JSONDecodeError:
            return None

    # ========================================================
    # Candidate selection (consensus)
    # ========================================================

    def _select_best_candidate(self, candidates: List[Dict]) -> Dict:
        if not candidates:
            return {}

        # Score candidate by:
        # - must contain both neurons
        # - shorter code (less drift) but not too tiny
        # - presence of "min(" or "max(" for clamping
        def score(c: Dict) -> float:
            neurons = c.get("neurons", [])
            if not isinstance(neurons, list):
                return -1.0
            names = {n.get("name") for n in neurons if isinstance(n, dict)}
            if {"long_filter", "short_filter"} != names:
                return -1.0

            total_len = 0
            clamp_hits = 0
            for n in neurons:
                code = (n.get("code") or "")
                total_len += len(code)
                if "min(" in code or "max(" in code:
                    clamp_hits += 1

            # prefer moderate length, penalize huge
            length_score = max(0.0, 1.0 - (max(0, total_len - 900) / 900.0))
            clamp_score = 0.2 * clamp_hits
            return length_score + clamp_score

        ranked = [(score(c), c) for c in candidates]
        ranked.sort(key=lambda x: x[0], reverse=True)
        return ranked[0][1]

    # ========================================================
    # Validate + Save
    # ========================================================

    def _validate_and_save(self, result: Dict, summary: Dict, raw_prompt: str) -> Tuple[int, int]:
        neurons = result.get("neurons", [])
        if not isinstance(neurons, list):
            return 0, 0

        manifest = self._load_manifest()
        saved = 0
        blocked = 0
        ts = stamp()
        prompt_hash = sha12(raw_prompt)

        # Build set of existing hashes
        existing_hashes = {n.get("hash") for n in manifest.get("neurons", []) if isinstance(n, dict)}

        for n in neurons:
            if not isinstance(n, dict):
                blocked += 1
                continue

            name = n.get("name")
            code = (n.get("code") or "").strip()
            if name not in {"long_filter", "short_filter"}:
                blocked += 1
                continue

            ok, reason = self.gate.validate(code, expected_name=name)
            if not ok:
                blocked += 1
                logger.error(f"🚫 Blocked {name}: {reason}")
                continue

            h = sha12(code)
            if h in existing_hashes:
                logger.info(f"♻️ Dedup skip {name}: {h}")
                continue

            file_name = f"{name}_{ts}_{h}.py"
            path = self.neurons_dir / file_name

            header = {
                "name": name,
                "hash": h,
                "created_utc": utc_iso(),
                "created_local": ts,
                "model": self.cfg.model,
                "prompt_hash": prompt_hash,
                "market": summary.get("market", {}),
                "stats": summary,
            }

            # Keep neuron file minimal and safe (no extra code)
            content = (
                '"""\n' + json.dumps(header, ensure_ascii=False, indent=2) + '\n"""\n\n'
                "from typing import Tuple\n\n"
                f"{code}\n"
            )
            path.write_text(content, encoding="utf-8")
            logger.info(f"💾 Saved neuron: {file_name}")

            manifest.setdefault("neurons", []).append({
                "name": name,
                "hash": h,
                "file": file_name,
                "fitness": 0.0,  # will be updated after backtest
                "created_utc": utc_iso(),
                "model": self.cfg.model,
                "prompt_hash": prompt_hash,
                "market": summary.get("market", {}),
            })

            existing_hashes.add(h)
            saved += 1

        self._save_manifest(manifest)
        return saved, blocked

    # ========================================================
    # Manifest IO
    # ========================================================

    def _load_manifest(self) -> Dict:
        if not self.manifest_path.exists():
            return {"version": 1, "neurons": [], "created_utc": utc_iso()}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return {"version": 1, "neurons": [], "created_utc": utc_iso()}

    def _save_manifest(self, manifest: Dict) -> None:
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # ========================================================
    # Analysis snapshots
    # ========================================================

    def _save_analysis(self, data: Dict) -> None:
        p = self.analysis_dir / f"evo_{stamp()}.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"🧾 Analysis saved: {p.name}")
