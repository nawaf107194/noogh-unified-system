# YouTube Research Agent for Noogh
# البحث في YouTube عن topics يحددها الدماغ

import os
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

try:
    from googleapiclient.discovery import build
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logging.warning("YouTube APIs not installed. Run: pip install google-api-python-client youtube-transcript-api")

logger = logging.getLogger(__name__)


class YouTubeResearchAgent:
    """
    وكيل YouTube للبحث:
    - البحث بكلمات مفتاحية
    - استخراج transcripts
    - تلخيص المحتوى
    - تخزين في shared_memory
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        self.youtube = None
        
        if self.api_key and YOUTUBE_AVAILABLE:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("🎬 YouTube Research Agent initialized")
        else:
            logger.warning("⚠️ YouTube API not available")

    def search_and_extract(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        بحث YouTube + استخراج محتوى.
        
        Args:
            query: موضوع البحث (من الدماغ)
            max_results: عدد الفيديوهات
            
        Returns:
            List of video data with transcripts
        """
        if not self.youtube:
            logger.error("❌ YouTube API not initialized")
            return []

        results = []
        
        try:
            # 1. البحث
            search_response = self.youtube.search().list(
                q=query,
                part='snippet',
                maxResults=max_results,
                type='video',
                order='relevance',
                publishedAfter=(datetime.now() - timedelta(days=30)).isoformat() + 'Z'
            ).execute()

            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                channel = item['snippet']['channelTitle']
                published = item['snippet']['publishedAt']
                
                logger.info(f"🎥 Found: {title[:60]}...")

                # 2. استخراج التفاصيل
                video_details = self._get_video_details(video_id)
                
                # 3. استخراج transcript
                transcript = self._get_transcript(video_id)
                
                # 4. تلخيص المحتوى
                summary = self._summarize_content(title, transcript)

                video_data = {
                    'id': video_id,
                    'title': title,
                    'channel': channel,
                    'published': published,
                    'views': video_details.get('viewCount', 0),
                    'likes': video_details.get('likeCount', 0),
                    'duration': video_details.get('duration', ''),  # PT15M30S
                    'transcript': transcript[:5000] if transcript else '',  # أول 5000 حرف
                    'summary': summary,
                    'key_insights': self._extract_insights(transcript, title),
                    'relevance_score': self._calculate_relevance(query, title, transcript),
                    'url': f"https://youtube.com/watch?v={video_id}",
                    'source': 'youtube',
                    'searched_at': datetime.now().isoformat(),
                    'query': query
                }
                
                results.append(video_data)

            logger.info(f"✅ Extracted {len(results)} videos for query: '{query}'")
            
        except Exception as e:
            logger.error(f"❌ YouTube search error: {e}")

        return results

    def _get_video_details(self, video_id: str) -> Dict:
        """جلب تفاصيل الفيديو (views, likes, duration)"""
        try:
            response = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=video_id
            ).execute()
            
            if response['items']:
                stats = response['items'][0]['statistics']
                details = response['items'][0]['contentDetails']
                return {
                    'viewCount': int(stats.get('viewCount', 0)),
                    'likeCount': int(stats.get('likeCount', 0)),
                    'duration': details.get('duration', '')
                }
        except Exception as e:
            logger.warning(f"Could not get details for {video_id}: {e}")
        
        return {'viewCount': 0, 'likeCount': 0, 'duration': ''}

    def _get_transcript(self, video_id: str) -> str:
        """استخراج transcript من الفيديو"""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = ' '.join([item['text'] for item in transcript_list])
            return transcript
        except Exception as e:
            logger.warning(f"No transcript for {video_id}: {e}")
            return ""

    def _summarize_content(self, title: str, transcript: str) -> str:
        """تلخيص المحتوى (مبسط)"""
        if not transcript:
            return title
        
        # أول 500 حرف كـ summary مبدئي
        # في الإنتاج: استخدم LLM للتلخيص
        sentences = transcript.split('.')
        summary = '. '.join(sentences[:3])[:300]
        return summary + "..."

    def _extract_insights(self, transcript: str, title: str) -> List[str]:
        """استخراج insights رئيسية"""
        insights = []
        
        # كلمات مفتاحية مهمة
        keywords = [
            'breakthrough', 'novel', 'state-of-the-art', 'SOTA',
            'new method', 'architecture', 'outperforms', ' achieves',
            'accuracy', 'efficiency', 'training', 'inference'
        ]
        
        text = (title + ' ' + transcript).lower()
        
        for keyword in keywords:
            if keyword in text:
                # استخراج الجملة المحيطة
                pattern = f"[^.]*{keyword}[^.]*\."
                matches = re.findall(pattern, text, re.IGNORECASE)
                insights.extend(matches[:2])  # أول 2 تطابق
        
        return list(set(insights))[:5]  # 5 insights فريدة

    def _calculate_relevance(self, query: str, title: str, transcript: str) -> float:
        """حساب مدى relevance للموضوع (0-1)"""
        query_words = set(query.lower().split())
        text = (title + ' ' + transcript[:1000]).lower()
        text_words = set(text.split())
        
        if not query_words:
            return 0.5
        
        intersection = query_words & text_words
        return len(intersection) / len(query_words)

    def store_in_memory(self, results: List[Dict]) -> int:
        """تخزين النتائج في shared_memory.sqlite"""
        import sqlite3
        
        if not results:
            return 0
        
        stored = 0
        
        try:
            # استخدم نفس قاعدة بيانات autonomous_learner
            db_path = Path('/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # إنشاء table إذا مو موجود
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS youtube_research (
                    id TEXT PRIMARY KEY,
                    key TEXT UNIQUE,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            for item in results:
                key = f"youtube:{item['id']}"
                value = json.dumps(item)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO youtube_research (id, key, value, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (item['id'], key, value, datetime.now().isoformat()))
                
                # أيضاً في beliefs للتوافق مع autonomous_learner
                cursor.execute('''
                    INSERT OR REPLACE INTO beliefs (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (f"learned:youtube:{item['id']}", value, datetime.now().isoformat()))
                
                stored += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Stored {stored} YouTube items in shared_memory")
            
        except Exception as e:
            logger.error(f"❌ Error storing in memory: {e}")
        
        return stored

    def research_topic(self, topic: str) -> Dict:
        """
        البحث الكامل عن موضوع (الواجهة الرئيسية).
        
        Args:
            topic: الموضوع من RunPod Brain
            
        Returns:
            Summary of research results
        """
        logger.info(f"🔍 Researching topic: '{topic}'")
        
        results = self.search_and_extract(topic, max_results=5)
        stored = self.store_in_memory(results)
        
        return {
            'topic': topic,
            'videos_found': len(results),
            'videos_stored': stored,
            'top_video': results[0]['title'] if results else None,
            'insights_extracted': sum(len(v['key_insights']) for v in results),
            'timestamp': datetime.now().isoformat()
        }


# Integration with RunPod Brain
def research_from_brain(topic: str, api_key: Optional[str] = None) -> Dict:
    """
    واجهة للدماغ (RunPod) لاستدعاء وكيل YouTube.
    
    Usage from RunPod:
        result = research_from_brain("transformer architecture improvements")
    """
    agent = YouTubeResearchAgent(api_key=api_key)
    return agent.research_topic(topic)


if __name__ == '__main__':
    # Test
    import sys
    
    if len(sys.argv) > 1:
        topic = ' '.join(sys.argv[1:])
    else:
        topic = "transformer architecture improvements 2025"
    
    print(f"🔍 Testing YouTube Agent with: '{topic}'")
    
    agent = YouTubeResearchAgent()
    result = agent.research_topic(topic)
    
    print(f"\n📊 Results:")
    print(json.dumps(result, indent=2, ensure_ascii=False))