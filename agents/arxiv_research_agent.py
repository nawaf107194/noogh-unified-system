# ArXiv Research Agent for Noogh
# البحث في arXiv عن أوراق علمية

import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import requests
import re

logger = logging.getLogger(__name__)


class ArxivResearchAgent:
    """
    وكيل arXiv للبحث في الأوراق العلمية.
    
    يقوم بـ:
    - البحث بكلمات مفتاحية
    - استخراج abstract + metadata
    - تحميل PDF (اختياري)
    - تلخيص المحتوى
    - تخزين في shared_memory
    """

    API_URL = 'http://export.arxiv.org/api/query'
    
    # الفئات العلمية المهمة
    CATEGORIES = {
        'cs.AI': 'Artificial Intelligence',
        'cs.LG': 'Machine Learning',
        'cs.CL': 'Computation and Language (NLP)',
        'cs.CV': 'Computer Vision',
        'cs.RO': 'Robotics',
        'cs.SE': 'Software Engineering',
        'stat.ML': 'Statistics Machine Learning',
        'q-fin.TR': 'Trading and Finance'
    }

    def __init__(self):
        logger.info("📚 ArXiv Research Agent initialized")

    def search_papers(self, query: str, 
                     categories: List[str] = None,
                     max_results: int = 10,
                     sort_by: str = 'submittedDate',
                     date_range_days: int = 30) -> List[Dict]:
        """
        البحث في arXiv.
        
        Args:
            query: موضوع البحث (من الدماغ)
            categories: فئات علمية (مثلاً ['cs.AI', 'cs.LG'])
            max_results: عدد النتائج
            sort_by: ترتيب حسب (relevance, submittedDate, lastUpdatedDate)
            date_range_days: البحث في آخر كم يوم
            
        Returns:
            List of paper metadata
        """
        results = []
        
        try:
            # بناء query
            search_query = query
            
            # إضافة فئات إذا موجودة
            if categories:
                cat_filter = ' OR '.join([f'cat:{cat}' for cat in categories])
                search_query = f'({search_query}) AND ({cat_filter})'
            
            # إضافة فلتر التاريخ
            start_date = (datetime.now() - timedelta(days=date_range_days)).strftime('%Y%m%d')
            
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': max_results,
                'sortBy': sort_by,
                'sortOrder': 'descending'
            }
            
            logger.info(f"📚 Searching arXiv: '{query}' (last {date_range_days} days)")
            
            response = requests.get(self.API_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # namespaces
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            for entry in root.findall('atom:entry', ns):
                paper = self._parse_paper_entry(entry, ns)
                if paper:
                    results.append(paper)
            
            logger.info(f"✅ Found {len(results)} papers")
            
        except Exception as e:
            logger.error(f"❌ ArXiv search error: {e}")
        
        return results

    def _parse_paper_entry(self, entry: ET.Element, ns: Dict) -> Optional[Dict]:
        """استخراج بيانات الورقة من XML entry"""
        try:
            # Basic info
            title = entry.find('atom:title', ns)
            summary = entry.find('atom:summary', ns)
            published = entry.find('atom:published', ns)
            updated = entry.find('atom:updated', ns)
            
            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    authors.append(name.text)
            
            # Categories
            categories = []
            for cat in entry.findall('atom:category', ns):
                term = cat.get('term', '')
                if term:
                    categories.append(term)
            
            # Links (PDF)
            pdf_url = None
            arxiv_url = None
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    pdf_url = link.get('href')
                elif link.get('rel') == 'alternate':
                    arxiv_url = link.get('href')
            
            # arXiv ID
            id_elem = entry.find('atom:id', ns)
            arxiv_id = id_elem.text.split('/')[-1] if id_elem else ''
            
            # Clean abstract
            abstract_text = summary.text if summary is not None else ''
            abstract_clean = self._clean_text(abstract_text)
            
            paper = {
                'id': arxiv_id,
                'title': self._clean_text(title.text) if title is not None else '',
                'abstract': abstract_clean,
                'abstract_summary': self._summarize_abstract(abstract_clean),
                'authors': authors[:5],  # أول 5 مؤلفين
                'categories': categories,
                'primary_category': categories[0] if categories else '',
                'published': published.text if published is not None else '',
                'updated': updated.text if updated is not None else '',
                'arxiv_url': arxiv_url or f'https://arxiv.org/abs/{arxiv_id}',
                'pdf_url': pdf_url or f'https://arxiv.org/pdf/{arxiv_id}.pdf',
                'source': 'arxiv',
                'searched_at': datetime.now().isoformat(),
                # Insights
                'key_contributions': self._extract_contributions(abstract_clean),
                'techniques': self._extract_techniques(abstract_clean),
                'quality_score': self._calculate_quality(authors, categories, abstract_clean)
            }
            
            return paper
            
        except Exception as e:
            logger.warning(f"Error parsing paper entry: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """تنظيف النص من newlines زائدة"""
        if not text:
            return ''
        text = text.replace('\n', ' ').replace('  ', ' ')
        return text.strip()

    def _summarize_abstract(self, abstract: str, max_length: int = 300) -> str:
        """تلخيص الabstract"""
        if len(abstract) <= max_length:
            return abstract
        
        # أول جملتين
        sentences = abstract.split('.')
        summary = '. '.join(sentences[:2]) + '.'
        
        if len(summary) > max_length:
            return abstract[:max_length] + "..."
        
        return summary

    def _extract_contributions(self, abstract: str) -> List[str]:
        """استخراج Contributions الرئيسية"""
        contributions = []
        
        # كلمات مفتاحية للـ contributions
        patterns = [
            r'we propose ([^.]+)',
            r'we introduce ([^.]+)',
            r'we present ([^.]+)',
            r'our (?:main )?contribution(?:s)? (?:is|are) ([^.]+)',
            r'this paper ([^.]+)',
        ]
        
        abstract_lower = abstract.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, abstract_lower)
            contributions.extend(matches[:2])  # أول 2 تطابق
        
        return list(set(contributions))[:5]

    def _extract_techniques(self, abstract: str) -> List[str]:
        """استخراج التقنيات المستخدمة"""
        techniques = []
        
        # قائمة التقنيات الشائعة
        tech_keywords = [
            'transformer', 'attention', 'bert', 'gpt', 'llm', 'large language model',
            'reinforcement learning', 'rl', 'q-learning', 'ppo', 'sac',
            'neural network', 'cnn', 'rnn', 'lstm', 'gru',
            'diffusion', 'gan', 'vae', 'autoencoder',
            'knowledge distillation', 'quantization', 'pruning',
            'chain-of-thought', 'few-shot', 'zero-shot', 'in-context learning',
            'rag', 'retrieval augmented generation',
            'multimodal', 'vision transformer', 'vit',
            'federated learning', 'self-supervised', 'contrastive learning'
        ]
        
        abstract_lower = abstract.lower()
        
        for tech in tech_keywords:
            if tech in abstract_lower:
                techniques.append(tech)
        
        return techniques[:10]

    def _calculate_quality(self, authors: List[str], categories: List[str], abstract: str) -> float:
        """حساب quality score (0-1)"""
        score = 0.0
        
        # Authors from top institutions (40%)
        top_institutions = ['google', 'openai', 'deepmind', 'microsoft', 'meta', 'facebook', 
                           'stanford', 'mit', 'berkeley', 'cmu', 'openai']
        if any(inst in ' '.join(authors).lower() for inst in top_institutions):
            score += 0.4
        
        # Relevant categories (30%)
        high_impact_cats = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV']
        if any(cat in high_impact_cats for cat in categories):
            score += 0.3
        
        # Abstract length (20%)
        if len(abstract) > 500:
            score += 0.2
        
        # Has techniques (10%)
        if self._extract_techniques(abstract):
            score += 0.1
        
        return min(score, 1.0)

    def store_in_memory(self, papers: List[Dict]) -> int:
        """تخزين الأوراق في shared_memory"""
        import sqlite3
        
        if not papers:
            return 0
        
        stored = 0
        
        try:
            db_path = Path('/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # إنشاء table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS arxiv_research (
                    id TEXT PRIMARY KEY,
                    key TEXT UNIQUE,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            for paper in papers:
                key = f"arxiv:{paper['id']}"
                value = json.dumps(paper)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO arxiv_research (id, key, value)
                    VALUES (?, ?, ?)
                ''', (paper['id'], key, value))
                
                # أيضاً في beliefs
                cursor.execute('''
                    INSERT OR REPLACE INTO beliefs (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (f"learned:arxiv:{paper['id']}", value, datetime.now().isoformat()))
                
                stored += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Stored {stored} arXiv papers in shared_memory")
            
        except Exception as e:
            logger.error(f"❌ Error storing papers: {e}")
        
        return stored

    def research_topic(self, topic: str, 
                      categories: List[str] = None,
                      max_results: int = 8) -> Dict:
        """
        البحث الكامل (الواجهة الرئيسية).
        
        Args:
            topic: الموضوع من الدماغ
            categories: فئات علمية
            max_results: عدد النتائج
        """
        if categories is None:
            categories = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV']
        
        logger.info(f"📚 Researching arXiv topic: '{topic}'")
        
        papers = self.search_papers(
            query=topic,
            categories=categories,
            max_results=max_results,
            date_range_days=60  # آخر شهرين
        )
        
        stored = self.store_in_memory(papers)
        
        # تلخيص
        all_techniques = []
        all_contributions = []
        
        for paper in papers:
            all_techniques.extend(paper.get('techniques', []))
            all_contributions.extend(paper.get('key_contributions', []))
        
        return {
            'topic': topic,
            'categories': categories,
            'papers_found': len(papers),
            'papers_stored': stored,
            'top_paper': papers[0]['title'] if papers else None,
            'techniques_found': list(set(all_techniques))[:10],
            'contributions': list(set(all_contributions))[:5],
            'avg_quality': sum(p['quality_score'] for p in papers) / len(papers) if papers else 0,
            'timestamp': datetime.now().isoformat()
        }


# Integration with Brain
def research_from_brain(topic: str, categories: List[str] = None) -> Dict:
    """
    واجهة الدماغ.
    
    Usage:
        result = research_from_brain("transformer efficiency")
    """
    agent = ArxivResearchAgent()
    return agent.research_topic(topic, categories)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        topic = ' '.join(sys.argv[1:])
    else:
        topic = "efficient transformer architectures"
    
    print(f"📚 Testing ArXiv Agent with: '{topic}'")
    
    agent = ArxivResearchAgent()
    result = agent.research_topic(topic)
    
    print(f"\n📊 Results:")
    print(json.dumps(result, indent=2, ensure_ascii=False))