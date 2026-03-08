# GitHub Research Agent for Noogh
# البحث في GitHub عن repos/topics يحددها الدماغ

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class GitHubResearchAgent:
    """
    وكيل GitHub للبحث المتقدم:
    - البحث في repos حسب topic
    - قراءة README و code
    - استخراج insights تقنية
    - تتبع trending repos
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.headers = {}
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
            self.headers['Accept'] = 'application/vnd.github.v3+json'
            logger.info("🐙 GitHub Research Agent initialized")
        else:
            logger.warning("⚠️ GitHub token not available (limited API)")

    def search_repositories(self, query: str, language: Optional[str] = None, 
                           sort: str = 'updated', max_results: int = 10) -> List[Dict]:
        """
        بحث repos في GitHub.
        
        Args:
            query: موضوع البحث (من الدماغ)
            language: لغة البرمجة (python, rust, etc.)
            sort: sorting method (stars, updated, forks)
            max_results: عدد النتائج
            
        Returns:
            List of repository data
        """
        results = []
        
        try:
            # بناء query
            q = query
            if language:
                q += f' language:{language}'
            
            # إضافة فلتر الزمن (آخر 6 أشهر)
            date_limit = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            q += f' created:>{date_limit}'
            
            url = 'https://api.github.com/search/repositories'
            params = {
                'q': q,
                'sort': sort,
                'order': 'desc',
                'per_page': max_results
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            repos = data.get('items', [])
            
            logger.info(f"🐙 Found {len(repos)} repos for: '{query}'")
            
            for repo in repos:
                repo_data = self._extract_repo_data(repo)
                
                # جلب README content
                readme = self._get_readme(repo['full_name'])
                repo_data['readme_summary'] = self._summarize_readme(readme)
                
                # استخراج insights
                repo_data['technical_insights'] = self._extract_technical_insights(
                    readme, repo['description'] or '', repo.get('topics', [])
                )
                
                # حساب quality score
                repo_data['quality_score'] = self._calculate_quality(repo_data)
                
                results.append(repo_data)

        except Exception as e:
            logger.error(f"❌ GitHub search error: {e}")
        
        return results

    def _extract_repo_data(self, repo: Dict) -> Dict:
        """استخراج البيانات المهمة من repo"""
        return {
            'id': repo['id'],
            'name': repo['name'],
            'full_name': repo['full_name'],
            'description': repo['description'] or '',
            'url': repo['html_url'],
            'stars': repo['stargazers_count'],
            'forks': repo['forks_count'],
            'language': repo['language'],
            'topics': repo.get('topics', []),
            'created_at': repo['created_at'],
            'updated_at': repo['updated_at'],
            'open_issues': repo['open_issues_count'],
            'license': repo.get('license', {}).get('name') if repo.get('license') else None,
            'source': 'github',
            'searched_at': datetime.now().isoformat()
        }

    def _get_readme(self, full_name: str) -> str:
        """جلب README content من repo"""
        try:
            url = f'https://api.github.com/repos/{full_name}/readme'
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                import base64
                content = base64.b64decode(data['content']).decode('utf-8')
                return content[:10000]  # أول 10,000 حرف
                
        except Exception as e:
            logger.warning(f"Could not fetch README for {full_name}: {e}")
        
        return ""

    def _summarize_readme(self, readme: str) -> str:
        """تلخيص README"""
        if not readme:
            return "No README available"
        
        # استخراج أول فقرة مفيدة
        lines = readme.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 50:
                return line[:300] + "..."
        
        return readme[:200] + "..."

    def _extract_technical_insights(self, readme: str, description: str, topics: List[str]) -> List[str]:
        """استخراج insights تقنية"""
        insights = []
        text = (readme + ' ' + description).lower()
        
        # كلمات مفتاحية تقنية
        tech_keywords = {
            'architecture': ['transformer', 'cnn', 'rnn', 'lstm', 'gru', 'attention', 'mlp'],
            'training': ['fine-tuning', 'pre-training', 'distillation', 'quantization', 'pruning'],
            'performance': ['sota', 'state-of-the-art', 'benchmark', 'accuracy', 'efficiency'],
            'technique': ['rlhf', 'rag', 'chain-of-thought', 'few-shot', 'zero-shot'],
            'application': ['nlp', 'cv', 'multimodal', 'agent', 'autonomous']
        }
        
        for category, keywords in tech_keywords.items():
            for keyword in keywords:
                if keyword in text or keyword in [t.lower() for t in topics]:
                    insights.append(f"{category}: {keyword}")
        
        return list(set(insights))[:10]

    def _calculate_quality(self, repo_data: Dict) -> float:
        """حساب quality score (0-1)"""
        score = 0.0
        
        # Stars (40%)
        stars = repo_data.get('stars', 0)
        score += min(stars / 1000, 0.4)
        
        # Recent update (30%)
        updated = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
        days_since_update = (datetime.now() - updated.replace(tzinfo=None)).days
        if days_since_update < 30:
            score += 0.3
        elif days_since_update < 90:
            score += 0.15
        
        # Has README insights (20%)
        if repo_data.get('technical_insights'):
            score += 0.2
        
        # Has topics (10%)
        if repo_data.get('topics'):
            score += 0.1
        
        return min(score, 1.0)

    def get_trending_repos(self, language: str = 'python', since: str = 'daily') -> List[Dict]:
        """جلب trending repos (GitHub trending)"""
        # Note: GitHub API doesn't have direct trending endpoint
        # Use search with recent pushes
        query = f'language:{language} pushed:>{(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")}'
        return self.search_repositories(query, language=language, sort='stars', max_results=10)

    def store_in_memory(self, results: List[Dict]) -> int:
        """تخزين النتائج في shared_memory"""
        import sqlite3
        
        if not results:
            return 0
        
        stored = 0
        
        try:
            db_path = Path('/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # إنشاء table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS github_research (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            for item in results:
                key = f"github:{item['full_name']}"
                value = json.dumps(item)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO github_research (id, key, value)
                    VALUES (?, ?, ?)
                ''', (item['id'], key, value))
                
                # أيضاً في beliefs
                cursor.execute('''
                    INSERT OR REPLACE INTO beliefs (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (f"learned:github:{item['full_name']}", value, datetime.now().isoformat()))
                
                stored += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Stored {stored} GitHub repos in shared_memory")
            
        except Exception as e:
            logger.error(f"❌ Error storing in memory: {e}")
        
        return stored

    def research_topic(self, topic: str, language: Optional[str] = 'python') -> Dict:
        """
        البحث الكامل (الواجهة الرئيسية).
        
        Args:
            topic: الموضوع من RunPod Brain
            language: لغة البرمجة المستهدفة
        """
        logger.info(f"🔍 Researching GitHub topic: '{topic}' (lang: {language})")
        
        results = self.search_repositories(topic, language=language, max_results=8)
        stored = self.store_in_memory(results)
        
        # تلخيص top insights
        all_insights = []
        for repo in results:
            all_insights.extend(repo.get('technical_insights', []))
        
        top_insights = list(set(all_insights))[:5]
        
        return {
            'topic': topic,
            'language': language,
            'repos_found': len(results),
            'repos_stored': stored,
            'top_repo': results[0]['full_name'] if results else None,
            'top_stars': results[0]['stars'] if results else 0,
            'technical_trends': top_insights,
            'avg_quality': sum(r['quality_score'] for r in results) / len(results) if results else 0,
            'timestamp': datetime.now().isoformat()
        }


# Integration with RunPod Brain
def research_from_brain(topic: str, token: Optional[str] = None) -> Dict:
    """
    واجهة للدماغ (RunPod).
    
    Usage:
        result = research_from_brain("transformer quantization")
    """
    agent = GitHubResearchAgent(token=token)
    return agent.research_topic(topic)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        topic = ' '.join(sys.argv[1:])
    else:
        topic = "LLM efficiency optimization"
    
    print(f"🔍 Testing GitHub Agent with: '{topic}'")
    
    agent = GitHubResearchAgent()
    result = agent.research_topic(topic)
    
    print(f"\n📊 Results:")
    print(json.dumps(result, indent=2, ensure_ascii=False))