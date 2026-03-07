"""
WebSearcher - Searches the web for information
Enhanced with multiple knowledge sources
"""

import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


class WebSearcher:
    """Searches the web for learning resources from multiple sources"""

    def __init__(self):
        """Initialize WebSearcher"""
        self.search_history = []

        # Trusted knowledge sources (non-Wikipedia)
        self.knowledge_sources = {
            "academic": ["arxiv.org", "scholar.google.com", "researchgate.net", "semanticscholar.org"],
            "documentation": [
                "docs.python.org",
                "pytorch.org/docs",
                "tensorflow.org/api_docs",
                "huggingface.co/docs",
                "fastapi.tiangolo.com",
            ],
            "tutorials": ["realpython.com", "freecodecamp.org", "medium.com", "dev.to", "towardsdatascience.com"],
            "technical": ["stackoverflow.com", "github.com", "hackernoon.com", "dzone.com"],
            "news": ["techcrunch.com", "wired.com", "arstechnica.com", "theverge.com"],
        }

        logger.info("WebSearcher initialized with multiple knowledge sources")

    def search(self, query: str, num_results: int = 5, source_type: str = None) -> List[Dict[str, Any]]:
        """
        Search the web for a query using multiple sources

        Args:
            query: Search query
            num_results: Number of results to return
            source_type: Type of source (academic, documentation, tutorials, etc.)

        Returns:
            List of search results from diverse sources
        """
        logger.info(f"Searching for: {query} (source_type: {source_type})")

        # Record search
        self.search_history.append({"query": query, "num_results": num_results, "source_type": source_type})

        results = []

        # Try multiple search methods
        try:
            # Method 1: DuckDuckGo (general search)
            ddg_results = self._duckduckgo_search(query, num_results)
            results.extend(ddg_results)

            # Method 2: Add curated sources based on query
            curated_results = self._get_curated_sources(query, source_type)
            results.extend(curated_results)

            # Method 3: Add academic sources if technical query
            if self._is_technical_query(query):
                academic_results = self._get_academic_sources(query)
                results.extend(academic_results)

            # Remove duplicates and limit results
            results = self._deduplicate_results(results)[:num_results]

            logger.info(f"Found {len(results)} results from diverse sources")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self._fallback_results(query, num_results)

    def _duckduckgo_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo API"""
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []

            # Get abstract
            if data.get("Abstract"):
                results.append(
                    {
                        "title": data.get("Heading", query),
                        "snippet": data.get("Abstract"),
                        "url": data.get("AbstractURL"),
                        "source": "DuckDuckGo",
                        "type": "general",
                    }
                )

            # Get related topics
            for topic in data.get("RelatedTopics", [])[: num_results - 1]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append(
                        {
                            "title": topic.get("Text", "")[:100],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL"),
                            "source": "DuckDuckGo",
                            "type": "general",
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    def _get_curated_sources(self, query: str, source_type: str = None) -> List[Dict[str, Any]]:
        """Get curated sources based on query"""
        results = []
        query_lower = query.lower()

        # Determine best source type if not specified
        if not source_type:
            if any(word in query_lower for word in ["python", "code", "programming", "api"]):
                source_type = "documentation"
            elif any(word in query_lower for word in ["learn", "tutorial", "how to", "تعلم", "اشرح"]):
                source_type = "tutorials"
            elif any(word in query_lower for word in ["research", "paper", "study"]):
                source_type = "academic"
            else:
                source_type = "technical"

        # Get relevant sources
        sources = self.knowledge_sources.get(source_type, [])

        for source in sources[:2]:  # Top 2 sources
            results.append(
                {
                    "title": f"{query} - {source}",
                    "snippet": f"High-quality information about {query} from {source}",
                    "url": f"https://{source}/search?q={query.replace(' ', '+')}",
                    "source": source,
                    "type": source_type,
                }
            )

        return results

    def _get_academic_sources(self, query: str) -> List[Dict[str, Any]]:
        """Get academic/research sources"""
        results = []

        # arXiv
        results.append(
            {
                "title": f"{query} - arXiv Research Papers",
                "snippet": f"Latest research papers about {query} from arXiv.org",
                "url": f"https://arxiv.org/search/?query={query.replace(' ', '+')}&searchtype=all",
                "source": "arXiv.org",
                "type": "academic",
            }
        )

        return results

    def _is_technical_query(self, query: str) -> bool:
        """Check if query is technical/academic"""
        technical_keywords = [
            "algorithm",
            "neural",
            "machine learning",
            "deep learning",
            "ai",
            "artificial intelligence",
            "model",
            "training",
            "optimization",
            "architecture",
            "framework",
            "library",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in technical_keywords)

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results"""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results

    def _fallback_results(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Enhanced fallback results with diverse sources"""
        return [
            {
                "title": f"{query} - Python Documentation",
                "snippet": f"Official Python documentation about {query}",
                "url": f"https://docs.python.org/3/search.html?q={query.replace(' ', '+')}",
                "source": "Python Docs",
                "type": "documentation",
            },
            {
                "title": f"{query} - Real Python Tutorial",
                "snippet": f"Learn about {query} with practical examples",
                "url": f"https://realpython.com/search?q={query.replace(' ', '+')}",
                "source": "Real Python",
                "type": "tutorial",
            },
            {
                "title": f"{query} - Stack Overflow",
                "snippet": f"Community Q&A about {query}",
                "url": f"https://stackoverflow.com/search?q={query.replace(' ', '+')}",
                "source": "Stack Overflow",
                "type": "technical",
            },
            {
                "title": f"{query} - GitHub",
                "snippet": f"Code examples and projects about {query}",
                "url": f"https://github.com/search?q={query.replace(' ', '+')}",
                "source": "GitHub",
                "type": "code",
            },
            {
                "title": f"{query} - arXiv Papers",
                "snippet": f"Research papers about {query}",
                "url": f"https://arxiv.org/search/?query={query.replace(' ', '+')}&searchtype=all",
                "source": "arXiv",
                "type": "academic",
            },
        ][:num_results]

    def get_source_stats(self) -> Dict[str, int]:
        """Get statistics about sources used"""
        stats = {}
        for search in self.search_history:
            source_type = search.get("source_type", "general")
            stats[source_type] = stats.get(source_type, 0) + 1
        return stats


class ContentFetcher:
    """Fetches content from URLs"""

    def __init__(self):
        logger.info("ContentFetcher initialized")

    def fetch(self, url: str) -> Dict[str, Any]:
        """
        Fetch content from URL

        Args:
            url: URL to fetch

        Returns:
            Content dictionary
        """
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Noug-Neural-OS/1.0 (Learning Bot)"})
            response.raise_for_status()

            return {"url": url, "content": response.text[:5000], "status": "success"}  # First 5000 chars
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return {"url": url, "content": "", "status": "failed", "error": str(e)}


class KnowledgeExtractor:
    """Extracts knowledge from web content"""

    def __init__(self):
        logger.info("KnowledgeExtractor initialized")

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract knowledge from content

        Args:
            content: Content to extract from

        Returns:
            Extracted knowledge
        """
        # Simple extraction: key sentences
        sentences = content.split(".")[:10]  # First 10 sentences

        return {
            "key_points": [s.strip() for s in sentences if len(s.strip()) > 20],
            "length": len(content),
            "extracted_at": "now",
        }


class LearningIntegrator:
    """Integrates learned knowledge into system"""

    def __init__(self):
        self.learned_topics = {}
        logger.info("LearningIntegrator initialized")

    def integrate(self, topic: str, knowledge: Dict[str, Any]):
        """
        Integrate learned knowledge

        Args:
            topic: Topic learned
            knowledge: Knowledge to integrate
        """
        self.learned_topics[topic] = knowledge
        logger.info(f"Integrated knowledge about: {topic}")

    def get_knowledge(self, topic: str) -> Dict[str, Any]:
        """Get knowledge about a topic"""
        return self.learned_topics.get(topic, {})


if __name__ == "__main__":
    # Test web research
    searcher = WebSearcher()

    # Search for Python programming
    results = searcher.search("Python programming", num_results=3)

    print(f"Search results: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', 'No title')}")
        print(f"   {result.get('snippet', 'No snippet')[:100]}...")
        print(f"   URL: {result.get('url', 'No URL')}")
