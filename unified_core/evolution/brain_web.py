"""
NOOGH Brain Web Research Integration (with Circuit Breaker)
=============================================================
Connects the Brain (Teacher LLM) with live internet search.

Circuit Breaker pattern:
- If 3 consecutive failures → open circuit for 5 minutes
- Prevents slow/blocked network from stalling the pipeline
- Results are cached for 10 minutes to avoid redundant searches

Zero external dependencies.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("unified_core.evolution.brain_web")


# ============================================================
# Circuit Breaker
# ============================================================

class _CircuitBreaker:
    """Simple circuit breaker for web requests."""
    
    def __init__(self, failure_threshold: int = 3, recovery_time: float = 300.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.last_failure = 0.0
        self.state = "CLOSED"  # CLOSED = normal, OPEN = blocking
    
    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure > self.recovery_time:
                self.state = "HALF_OPEN"
                return False
            return True
        return False
    
    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"🔴 Circuit breaker OPEN — {self.failures} failures, "
                f"recovery in {self.recovery_time}s"
            )


_breaker = _CircuitBreaker(failure_threshold=3, recovery_time=300.0)

# Simple cache: query → (result, timestamp)
_search_cache: Dict[str, tuple] = {}
_CACHE_TTL = 600  # 10 minutes


# ============================================================
# Core Functions
# ============================================================

def _search_sync(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Synchronous web search with circuit breaker + caching.
    """
    # Check cache
    cached = _search_cache.get(query)
    if cached and time.time() - cached[1] < _CACHE_TTL:
        return cached[0]
    
    # Check circuit breaker
    if _breaker.is_open():
        logger.debug("Circuit breaker open — skipping web search")
        return []
    
    try:
        from agents.web_researcher_agent import _search_duckduckgo
        results = _search_duckduckgo(query, max_results=max_results)
        _breaker.record_success()
        # Cache results
        _search_cache[query] = (results, time.time())
        return results
    except Exception as e:
        _breaker.record_failure()
        logger.debug(f"Web search failed: {e}")
        return []


def _fetch_sync(url: str, max_chars: int = 3000) -> str:
    """
    Synchronous page fetch with circuit breaker.
    """
    if _breaker.is_open():
        return ""
    
    try:
        from agents.web_researcher_agent import _fetch_url, html_to_text
        result = _fetch_url(url, timeout=8)
        if result["success"]:
            _breaker.record_success()
            text = html_to_text(result["content"])
            return text[:max_chars]
        _breaker.record_failure()
        return ""
    except Exception as e:
        _breaker.record_failure()
        logger.debug(f"Page fetch failed: {e}")
        return ""


async def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Async web search with circuit breaker."""
    if _breaker.is_open():
        return []
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, lambda: _search_sync(query, max_results)),
            timeout=12.0  # Hard timeout
        )
    except asyncio.TimeoutError:
        _breaker.record_failure()
        logger.warning("🔴 Web search timed out (12s)")
        return []


async def fetch_page(url: str, max_chars: int = 3000) -> str:
    """Async page fetch with circuit breaker."""
    if _breaker.is_open():
        return ""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, lambda: _fetch_sync(url, max_chars)),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        _breaker.record_failure()
        return ""


async def research_topic(topic: str, depth: int = 1) -> Dict[str, Any]:
    """
    Research a topic with circuit breaker protection.
    Searches + fetches top `depth` results.
    """
    depth = min(depth, 3)
    start = time.time()
    
    results = await search_web(topic, max_results=depth + 2)
    
    # Fetch top pages
    page_contents = {}
    for r in results[:depth]:
        url = r.get("url", "")
        if url:
            text = await fetch_page(url, max_chars=2000)
            if text and len(text) > 100:
                page_contents[url] = text
    
    context_parts = []
    for r in results:
        context_parts.append(f"• {r.get('title', '')} — {r.get('snippet', '')}")
    for url, text in page_contents.items():
        context_parts.append(f"\n[From {url[:60]}]\n{text[:1000]}")
    
    context = "\n".join(context_parts)
    elapsed = round(time.time() - start, 1)
    
    if results:
        logger.info(f"🌐 Research: '{topic}' → {len(results)} results ({elapsed}s)")
    
    return {
        "query": topic,
        "results": results,
        "pages_fetched": len(page_contents),
        "content": page_contents,
        "summary_context": context[:4000],
        "elapsed": elapsed,
    }


def build_research_prompt_section(research: Dict[str, Any]) -> str:
    """Format research results into a prompt section for the Brain."""
    if not research or not research.get("results"):
        return ""
    
    lines = [
        "\n<web_research>",
        f"Query: {research['query']}",
        f"Results found: {len(research['results'])}",
        "",
    ]
    
    for r in research["results"][:5]:
        lines.append(f"• [{r.get('title', '')}]({r.get('url', '')})")
        if r.get("snippet"):
            lines.append(f"  {r['snippet'][:150]}")
        lines.append("")
    
    for url, text in list(research.get("content", {}).items())[:2]:
        lines.append(f"--- Content from {url[:50]} ---")
        lines.append(text[:800])
        lines.append("")
    
    lines.append("</web_research>")
    return "\n".join(lines)


def get_circuit_status() -> Dict[str, Any]:
    """Get circuit breaker status for monitoring."""
    return {
        "state": _breaker.state,
        "failures": _breaker.failures,
        "cache_size": len(_search_cache),
        "last_failure_ago": round(time.time() - _breaker.last_failure, 1) if _breaker.last_failure else None,
    }
