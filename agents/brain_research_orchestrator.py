# Brain Research Orchestrator
# الدماغ يرسل مواضيع → الوكلاء يبحثون

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

# استيراد الوكلاء
from agents.youtube_research_agent import YouTubeResearchAgent
from agents.github_research_agent import GitHubResearchAgent
from agents.arxiv_research_agent import ArxivResearchAgent

logger = logging.getLogger(__name__)


@dataclass
class ResearchTask:
    """مهمة بحث من الدماغ"""
    topic: str
    priority: str  # high, medium, low
    sources: List[str]  # youtube, github, arxiv
    context: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BrainResearchOrchestrator:
    """
    الموجه الرئيسي: الدماغ يفكر ← يرسل مهام ← الوكلاء ينفذون
    
    Workflow:
    1. الدماغ المحلي يحدد topic مهم
    2. Orchestrator يوزع على الوكلاء
    3. كل وكيل يبحث في مصدره (YouTube/GitHub/arXiv)
    4. النتائج تُدمج في shared_memory
    5. NeuronFabric يولد neurons جديدة
    """

    def __init__(self):
        self.youtube_agent = YouTubeResearchAgent()
        self.github_agent = GitHubResearchAgent()
        self.arxiv_agent = ArxivResearchAgent()
        
        self.results_cache = {}
        logger.info("🧠 Brain Research Orchestrator initialized (YouTube + GitHub + arXiv)")

    async def dispatch_research(self, task: ResearchTask) -> Dict:
        """
        توزيع مهمة بحث على الوكلاء.
        
        Args:
            task: مهمة من الدماغ
            
        Returns:
            دمج نتائج كل الوكلاء
        """
        logger.info(f"🎯 Dispatching research: '{task.topic}' → {task.sources}")
        
        results = {
            'topic': task.topic,
            'priority': task.priority,
            'dispatched_at': datetime.now().isoformat(),
            'sources': {},
            'summary': {},
            'insights': []
        }
        
        # تشغيل الوكلاء بشكل parallel
        tasks_list = []
        
        if 'youtube' in task.sources and self.youtube_agent.youtube:
            tasks_list.append(self._research_youtube(task))
        
        if 'github' in task.sources:
            tasks_list.append(self._research_github(task))
        
        if 'arxiv' in task.sources:
            tasks_list.append(self._research_arxiv(task))
        
        # تنفيذ الوكلاء
        if tasks_list:
            source_results = await asyncio.gather(*tasks_list, return_exceptions=True)
            
            for result in source_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Agent failed: {result}")
                    continue
                
                source_name = result.get('source')
                results['sources'][source_name] = result
                results['insights'].extend(result.get('insights', []))
        
        # تلخيص النتائج
        results['summary'] = self._summarize_results(results['sources'])
        results['completed_at'] = datetime.now().isoformat()
        
        # تخزين في cache
        self.results_cache[task.topic] = results
        
        logger.info(f"✅ Research complete: '{task.topic}' → {len(results['insights'])} insights")
        
        return results

    async def _research_youtube(self, task: ResearchTask) -> Dict:
        """YouTube agent"""
        logger.info(f"🎬 YouTube researching: '{task.topic}'")
        
        result = self.youtube_agent.research_topic(task.topic)
        
        return {
            'source': 'youtube',
            'videos_found': result.get('videos_found', 0),
            'top_video': result.get('top_video'),
            'insights': [f"[YouTube] {result.get('top_video')}"] if result.get('top_video') else [],
            'data': result
        }

    async def _research_github(self, task: ResearchTask) -> Dict:
        """GitHub agent"""
        logger.info(f"🐙 GitHub researching: '{task.topic}'")
        
        result = self.github_agent.research_topic(task.topic)
        
        return {
            'source': 'github',
            'repos_found': result.get('repos_found', 0),
            'top_repo': result.get('top_repo'),
            'technical_trends': result.get('technical_trends', []),
            'insights': [f"[GitHub] {t}" for t in result.get('technical_trends', [])],
            'data': result
        }

    async def _research_arxiv(self, task: ResearchTask) -> Dict:
        """arXiv agent"""
        logger.info(f"📚 arXiv researching: '{task.topic}'")
        
        result = self.arxiv_agent.research_topic(task.topic)
        
        return {
            'source': 'arxiv',
            'papers_found': result.get('papers_found', 0),
            'top_paper': result.get('top_paper'),
            'techniques': result.get('techniques_found', []),
            'insights': [f"[arXiv] {t}" for t in result.get('techniques_found', [])],
            'data': result
        }

    def _summarize_results(self, sources: Dict) -> Dict:
        """تلخيص نتائج كل المصادر"""
        summary = {
            'total_sources': len(sources),
            'total_insights': 0,
            'key_themes': set(),
            'recommendations': []
        }
        
        for source_name, data in sources.items():
            if source_name == 'youtube':
                summary['total_insights'] += data.get('videos_found', 0)
                if data.get('top_video'):
                    summary['recommendations'].append(f"Watch: {data['top_video']}")
                    
            elif source_name == 'github':
                summary['total_insights'] += data.get('repos_found', 0)
                summary['key_themes'].update(data.get('technical_trends', []))
                if data.get('top_repo'):
                    summary['recommendations'].append(f"Study: {data['top_repo']}")
                    
            elif source_name == 'arxiv':
                summary['total_insights'] += data.get('papers_found', 0)
                summary['key_themes'].update(data.get('techniques', []))
                if data.get('top_paper'):
                    summary['recommendations'].append(f"Read: {data['top_paper']}")
        
        summary['key_themes'] = list(summary['key_themes'])
        
        return summary

    def generate_neurons_from_research(self, research_results: Dict) -> List[Dict]:
        """
        تحويل نتائج البحث إلى neurons.
        
        هذه الوظيفة تربط البحث بالتداول مباشرة.
        """
        neurons = []
        topic = research_results.get('topic', '')
        insights = research_results.get('insights', [])
        
        for insight in insights[:5]:  # أعلى 5 insights
            neuron = {
                'id': f"research_{int(datetime.now().timestamp())}_{hash(insight) % 10000}",
                'type': 'research_based',
                'concept': insight,
                'source_topic': topic,
                'confidence': 0.8,
                'created_from': 'brain_orchestrator',
                'created_at': datetime.now().isoformat()
            }
            neurons.append(neuron)
        
        # تخزين في NeuronFabric
        self._store_neurons(neurons)
        
        logger.info(f"🧠 Generated {len(neurons)} neurons from research")
        
        return neurons

    def _store_neurons(self, neurons: List[Dict]):
        """تخزين neurons في shared_memory"""
        import sqlite3
        
        try:
            db_path = Path('/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for neuron in neurons:
                key = f"neuron:research:{neuron['id']}"
                value = json.dumps(neuron)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO beliefs (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, value, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing neurons: {e}")

    async def research_and_generate(self, topic: str, 
                                     sources: List[str] = None,
                                     priority: str = 'medium') -> Dict:
        """
        البحث + توليد neurons (واجهة رئيسية).
        
        Usage:
            orchestrator = BrainResearchOrchestrator()
            result = await orchestrator.research_and_generate(
                topic="transformer quantization",
                sources=['youtube', 'github', 'arxiv'],
                priority='high'
            )
        """
        if sources is None:
            sources = ['youtube', 'github', 'arxiv']
        
        task = ResearchTask(
            topic=topic,
            priority=priority,
            sources=sources
        )
        
        # 1. بحث
        research_results = await self.dispatch_research(task)
        
        # 2. توليد neurons
        neurons = self.generate_neurons_from_research(research_results)
        
        # 3. تلخيص
        return {
            'topic': topic,
            'research': research_results,
            'neurons_generated': len(neurons),
            'neurons': neurons,
            'status': 'complete',
            'timestamp': datetime.now().isoformat()
        }


# API للدماغ المحلي
async def brain_think_and_research(topic: str, 
                                    sources: List[str] = None,
                                    generate_neurons: bool = True) -> Dict:
    """
    واجهة الدماغ الرئيسية.
    
    الدماغ المحلي يستدعي هذه الدالة عندما يريد البحث عن موضوع.
    
    Args:
        topic: ما يريد الدماغ معرفته
        sources: ['youtube', 'github', 'arxiv']
        generate_neurons: هل نولد neurons من النتائج؟
    
    Returns:
        نتائج البحث + neurons
    
    Example:
        result = await brain_think_and_research(
            topic="efficient transformer architectures",
            sources=['youtube', 'github', 'arxiv'],
            generate_neurons=True
        )
    """
    orchestrator = BrainResearchOrchestrator()
    
    if generate_neurons:
        return await orchestrator.research_and_generate(topic, sources)
    else:
        task = ResearchTask(topic=topic, priority='high', sources=sources or [])
        return await orchestrator.dispatch_research(task)


if __name__ == '__main__':
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            topic = ' '.join(sys.argv[1:])
        else:
            topic = "LLM efficient inference optimization"
        
        print(f"🧠 Brain thinking about: '{topic}'")
        print(f"🎯 Dispatching to research agents...\n")
        
        result = await brain_think_and_research(
            topic=topic,
            sources=['youtube', 'github', 'arxiv'],
            generate_neurons=True
        )
        
        print(f"\n✅ Research Complete!")
        print(f"📊 Summary:")
        print(f"   - Topic: {result['topic']}")
        print(f"   - Neurons generated: {result['neurons_generated']}")
        print(f"   - Status: {result['status']}")
        
        if result['neurons']:
            print(f"\n🧠 Generated Neurons:")
            for neuron in result['neurons'][:3]:
                print(f"   - {neuron['concept'][:60]}...")
        
        print(f"\n💾 Results stored in shared_memory.sqlite")
    
    asyncio.run(main())