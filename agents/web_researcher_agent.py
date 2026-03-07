"""NOOGH WebResearchAgent — Internet Search & Knowledge Gathering

Purpose: Search the web, extract content, and summarize findings
Capabilities:
- WEB_SEARCH: Search via DuckDuckGo (no API key needed)
- FETCH_PAGE: Fetch and extract text from a URL
- SUMMARIZE_FINDINGS: Structure and summarize collected research

Zero external dependencies — uses only Python stdlib.
"""

import asyncio
import json
import logging
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional

from unified_core.orchestration.agent_worker import AgentWorker
from unified_core.orchestration.messages import AgentRole

logger = logging.getLogger("agents.web_researcher")

# ============================================================
# HTML → Text Extractor (stdlib, no BeautifulSoup needed)
# ============================================================

class _TextExtractor(HTMLParser):
    """Lightweight HTML to text converter."""
    
    SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "meta", "link"}
    
    def __init__(self):
        super().__init__()
        self._text_parts: List[str] = []
        self._skip_depth = 0
        self._current_tag = ""
    
    def handle_starttag(self, tag, attrs):
        self._current_tag = tag.lower()
        if self._current_tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if self._current_tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "li", "tr"):
            self._text_parts.append("\n")
    
    def handle_endtag(self, tag):
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
    
    def handle_data(self, data):
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._text_parts.append(text)
    
    def get_text(self) -> str:
        raw = " ".join(self._text_parts)
        # Clean up whitespace
        raw = re.sub(r'\n\s*\n+', '\n\n', raw)
        raw = re.sub(r'  +', ' ', raw)
        return raw.strip()


def html_to_text(html: str) -> str:
    """Convert HTML string to clean text."""
    parser = _TextExtractor()
    try:
        parser.feed(html)
        return parser.get_text()
    except Exception:
        # Fallback: strip all tags
        return re.sub(r'<[^>]+>', '', html).strip()


def extract_links(html: str, base_url: str = "") -> List[Dict[str, str]]:
    """Extract links from HTML."""
    links = []
    for match in re.finditer(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE):
        href = match.group(1)
        text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if href.startswith("http") and text and len(text) > 3:
            links.append({"url": href, "text": text[:200]})
    return links[:20]


# ============================================================
# HTTP Client (stdlib)
# ============================================================

# Permissive SSL context for sites with cert issues
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

def _fetch_url(url: str, timeout: int = 15, max_size: int = 500_000) -> Dict[str, Any]:
    """
    Fetch a URL and return content.
    
    Returns:
        {"success": bool, "content": str, "url": str, "status": int}
    """
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json,text/plain",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        })
        
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            
            # Read with size limit
            raw = response.read(max_size)
            
            # Decode
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()
            
            try:
                text = raw.decode(charset, errors="replace")
            except (UnicodeDecodeError, LookupError):
                text = raw.decode("utf-8", errors="replace")
            
            return {
                "success": True,
                "content": text,
                "url": url,
                "status": status,
                "content_type": content_type,
                "size": len(raw),
            }
    
    except urllib.error.HTTPError as e:
        return {"success": False, "error": f"HTTP {e.code}: {e.reason}", "url": url, "status": e.code}
    except urllib.error.URLError as e:
        return {"success": False, "error": f"URL Error: {e.reason}", "url": url}
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


# ============================================================
# Search Engine (DuckDuckGo HTML — no API key)
# ============================================================

def _search_duckduckgo(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo and extract results.
    No API key needed — uses the HTML lite version.
    """
    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded}"
    
    result = _fetch_url(search_url, timeout=10)
    if not result["success"]:
        return []
    
    html = result["content"]
    results = []
    
    # Parse DuckDuckGo HTML results
    # Pattern: <a rel="nofollow" class="result__a" href="...">Title</a>
    for match in re.finditer(
        r'class="result__a"\s+href="([^"]*)"[^>]*>(.*?)</a>.*?'
        r'class="result__snippet"[^>]*>(.*?)</(?:td|div|span)',
        html, re.DOTALL | re.IGNORECASE
    ):
        url = match.group(1)
        title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        snippet = re.sub(r'<[^>]+>', '', match.group(3)).strip()
        
        # DuckDuckGo uses redirect URLs — extract actual URL
        if "uddg=" in url:
            actual = urllib.parse.unquote(url.split("uddg=")[-1].split("&")[0])
            url = actual
        
        if title and url.startswith("http"):
            results.append({
                "title": title[:200],
                "url": url,
                "snippet": snippet[:300],
            })
        
        if len(results) >= max_results:
            break
    
    return results


# ============================================================
# WebResearchAgent
# ============================================================

class WebResearchAgent(AgentWorker):
    """
    Internet research agent for NOOGH.
    
    Capabilities:
    - WEB_SEARCH: Search the web via DuckDuckGo
    - FETCH_PAGE: Fetch and extract text from URLs
    - SUMMARIZE_FINDINGS: Aggregate search results into structured knowledge
    
    Zero external deps — uses Python stdlib only.
    """
    
    def __init__(self):
        custom_handlers = {
            "WEB_SEARCH": self._web_search,
            "FETCH_PAGE": self._fetch_page,
            "SUMMARIZE_FINDINGS": self._summarize_findings,
        }
        role = AgentRole("web_researcher")
        super().__init__(role, custom_handlers)
        
        # Research session cache
        self._search_cache: Dict[str, List[Dict]] = {}
        self._page_cache: Dict[str, str] = {}
        self._session_start = time.time()
        
        logger.info("✅ WebResearchAgent initialized")
    
    async def _web_search(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search the web for a query.
        
        Task params:
            query (str): Search query
            max_results (int): Max results (default 8)
        """
        query = task.get("query", task.get("input", ""))
        max_results = task.get("max_results", 8)
        
        if not query:
            return {"success": False, "error": "No search query provided"}
        
        logger.info(f"🔍 Searching: {query}")
        
        try:
            # Run search in thread to avoid blocking event loop
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, lambda: _search_duckduckgo(query, max_results)
            )
            
            if not results:
                # Fallback: try a simpler search
                logger.warning(f"DuckDuckGo returned 0 results for: {query}")
                return {
                    "success": True,
                    "results": [],
                    "count": 0,
                    "query": query,
                    "message": "No results found"
                }
            
            # Cache results
            self._search_cache[query] = results
            
            logger.info(f"🔍 Found {len(results)} results for: {query}")
            
            return {
                "success": True,
                "results": results,
                "count": len(results),
                "query": query,
            }
        
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"success": False, "error": str(e), "query": query}
    
    async def _fetch_page(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch a page and extract its text content.
        
        Task params:
            url (str): URL to fetch
            extract_links (bool): Also extract links (default False)
            max_chars (int): Max characters to return (default 5000)
        """
        url = task.get("url", "")
        do_extract_links = task.get("extract_links", False)
        max_chars = task.get("max_chars", 5000)
        
        if not url:
            return {"success": False, "error": "No URL provided"}
        
        logger.info(f"📄 Fetching: {url}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: _fetch_url(url))
            
            if not result["success"]:
                return result
            
            html_content = result["content"]
            
            # Extract text
            text = html_to_text(html_content)
            
            # Cache
            self._page_cache[url] = text[:max_chars]
            
            response = {
                "success": True,
                "url": url,
                "text": text[:max_chars],
                "text_length": len(text),
                "status": result.get("status"),
            }
            
            if do_extract_links:
                response["links"] = extract_links(html_content, url)
            
            logger.info(f"📄 Fetched {len(text)} chars from {url}")
            
            return response
        
        except Exception as e:
            logger.error(f"Page fetch failed: {e}")
            return {"success": False, "error": str(e), "url": url}
    
    async def _summarize_findings(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize accumulated research findings.
        
        Task params:
            topic (str): Research topic
            include_sources (bool): Include source URLs (default True)
        """
        topic = task.get("topic", task.get("query", ""))
        include_sources = task.get("include_sources", True)
        
        # Gather all cached data
        searches = self._search_cache
        pages = self._page_cache
        
        if not searches and not pages:
            return {
                "success": False,
                "error": "No research data collected. Run WEB_SEARCH or FETCH_PAGE first."
            }
        
        # Build summary
        summary = {
            "topic": topic,
            "searches_performed": len(searches),
            "pages_fetched": len(pages),
            "session_duration_seconds": round(time.time() - self._session_start, 1),
        }
        
        # Aggregate search results
        all_results = []
        for query, results in searches.items():
            for r in results:
                all_results.append({
                    "query": query,
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "url": r.get("url", "") if include_sources else "[redacted]",
                })
        
        summary["results"] = all_results[:30]
        summary["total_results"] = len(all_results)
        
        # Include page excerpts
        if pages:
            summary["page_excerpts"] = {
                url: text[:500] for url, text in list(pages.items())[:5]
            }
        
        return {"success": True, "summary": summary}
    
    def get_stats(self) -> Dict[str, Any]:
        """Extended stats with research metrics."""
        base = super().get_stats()
        base.update({
            "searches_cached": len(self._search_cache),
            "pages_cached": len(self._page_cache),
            "session_uptime": round(time.time() - self._session_start, 1),
        })
        return base


# ============================================================
# Entry Point
# ============================================================

async def main():
    """Start the WebResearchAgent."""
    logger.info("🚀 Starting WebResearchAgent...")
    agent = WebResearchAgent()
    agent.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 WebResearchAgent stopping...")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
