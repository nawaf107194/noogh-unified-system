"""NOOGH TikTok Auditor Agent — Follow and analyze TikTok content

Purpose: Monitors a specific TikTok account, fetches new video metadata,
and extracts descriptions/links for the Neural Engine.
Capabilities:
- MONITOR_TIKTOK_ACCOUNT: Get recent uploads from a specific @username
- ANALYZE_VIDEO: Get full details (description, likes, music) of a specific video

Uses yt-dlp (installed via pip) to securely bypass basic protections and fetch metadata.
"""

import asyncio
import logging
import json
import time
import os
import tempfile
import subprocess
import glob
from typing import Dict, Any, List
try:
    from PIL import Image
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from unified_core.orchestration.agent_worker import AgentWorker
from unified_core.orchestration.messages import AgentRole
from unified_core.core.memory_store import UnifiedMemoryStore

logger = logging.getLogger("agents.tiktok_auditor")

class TikTokAuditorAgent(AgentWorker):
    """
    TikTok account monitor and intelligence extractor.
    """
    
    def __init__(self):
        custom_handlers = {
            "MONITOR_TIKTOK_ACCOUNT": self._monitor_account,
            "ANALYZE_VIDEO": self._analyze_video,
        }
        role = AgentRole("web_researcher")
        super().__init__(role, custom_handlers)
        
        self.memory = UnifiedMemoryStore()
        self._last_checked = {}
        
        if yt_dlp is None:
            logger.error("yt-dlp not installed. Agent will fail to fetch TikTok.")
        else:
            logger.info("✅ TikTokAuditorAgent initialized with yt-dlp support.")
            
    def _get_ytdlp_options(self, max_downloads: int = 5):
        """Configurations to extract metadata safely without downloading the massive MP4."""
        return {
            'extract_flat': True,       # Fast extraction, don't follow all links deeply immediately
            'playlistend': max_downloads, # Max number of videos to fetch from the profile
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,       # Skip deleted/private videos
            'skip_download': True,      # Do NOT download the actual video file, we just want metadata
            # Add user agent to prevent blocks
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }
        
    def _extract_frames_and_read(self, video_path: str) -> str:
        if not pytesseract:
            return ""
        frames_dir = tempfile.mkdtemp()
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", "fps=1/4", f"{frames_dir}/frame_%03d.jpg"]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            logger.error(f"FFmpeg failed: {e}")
            return ""
            
        frames = sorted(glob.glob(f"{frames_dir}/*.jpg"))
        extracted_texts = []
        for img_path in frames:
            try:
                img = Image.open(img_path)
                text = pytesseract.image_to_string(img, lang="eng+ara")
                ctext = " ".join(text.split()).strip()
                if len(ctext) > 5:
                    extracted_texts.append(ctext)
            except Exception:
                pass
            os.remove(img_path)
        os.rmdir(frames_dir)
        
        # Deduplicate and return
        return " | ".join(list(dict.fromkeys(extracted_texts)))

    async def _monitor_account(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan a TikTok account for its latest videos.
        Returns a summary of the latest uploads.
        """
        if yt_dlp is None:
            return {"success": False, "error": "yt-dlp module not found."}
            
        username = task.get("username", task.get("account"))
        if not username:
            return {"success": False, "error": "No username provided (e.g. @bytebytego)"}
            
        # Ensure it has @ symbol
        if not username.startswith("@"):
            username = f"@{username}"
            
        max_videos = task.get("max_videos", 5)
        url = f"https://www.tiktok.com/{username}"
        
        logger.info(f"📱 Scanning TikTok account: {url}")
        
        # We run the yt-dlp extractor in a separate thread so it doesn't block asyncio
        loop = asyncio.get_event_loop()
        
        def fetch_meta():
            opts = self._get_ytdlp_options(max_videos)
            opts['extract_flat'] = 'in_playlist' 
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
                
        try:
            info = await loop.run_in_executor(None, fetch_meta)
            
            if not info or 'entries' not in info:
                return {"success": False, "error": "No videos found or account is private/blocked."}
                
            videos = []
            for entry in info['entries']:
                if entry:
                    # TikTok returns id, title (which is usually the description/caption), url, duration
                    videos.append({
                        "id": entry.get("id"),
                        "title": entry.get("title", ""),
                        "url": entry.get("url", ""),
                        "duration": entry.get("duration"),
                        "view_count": entry.get("view_count", 0)
                    })
                    
            # Record observation in NOOGH Brain
            if videos:
                obs = {
                    "observation_id": f"tiktok_{username}_{int(time.time())}",
                    "source": "TikTokAuditorAgent",
                    "account": username,
                    "latest_video_caption": videos[0]["title"],
                    "timestamp": time.time()
                }
                await self.memory.append_observation(obs)
                
            logger.info(f"📱 Extracted {len(videos)} recent videos from {username}")
            
            return {
                "success": True, 
                "account": username, 
                "video_count": len(videos),
                "videos": videos
            }
            
        except Exception as e:
            logger.error(f"TikTok fetch failed limits bypass: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_video(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches deep metadata about a single specific TikTok video URL.
        """
        url = task.get("url")
        if not url:
            return {"success": False, "error": "No URL provided."}
            
        logger.info(f"📱 Deep analyzing TikTok video: {url}")
        
        loop = asyncio.get_event_loop()
        
        def fetch_single():
            opts = self._get_ytdlp_options(1)
            opts['extract_flat'] = False # We want deep extraction here
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
                
        try:
            info = await loop.run_in_executor(None, fetch_single)
            if not info:
                return {"success": False, "error": "Failed to extract video details."}
                
            details = {
                "id": info.get("id"),
                "uploader": info.get("uploader"),
                "description": info.get("description", info.get("title", "")),
                "tags": info.get("tags", []),
                "like_count": info.get("like_count"),
                "repost_count": info.get("repost_count"),
                "comment_count": info.get("comment_count"),
                "duration": info.get("duration"),
                "music": info.get("track", info.get("artist"))
            }

            # Run OCR if requested or globally
            ocr_text = ""
            if task.get("run_ocr", True):
                logger.info(f"👁️ Running Rapid OCR Vision on {url}")
                vid_opts = {
                    'format': 'worstvideo[ext=mp4]+worstaudio/worst', # Fastest download!
                    'outtmpl': '/tmp/tiktok_dl_%(id)s.%(ext)s',
                    'quiet': True,
                    'no_warnings': True
                }
                with yt_dlp.YoutubeDL(vid_opts) as ydl_vid:
                    ydl_vid.download([url])
                
                downloaded_file = glob.glob(f"/tmp/tiktok_dl_{info.get('id', '*')}.mp4")
                if downloaded_file:
                    ocr_text = self._extract_frames_and_read(downloaded_file[0])
                    details["ocr_text"] = ocr_text
                    os.remove(downloaded_file[0])
            
            # Formally inject this to NOOGH brain!
            obs_content = details["description"]
            if ocr_text:
                obs_content += f"\n[VISUAL OCR TEXT]: {ocr_text}"
            obs = {
                "source": "TikTokAuditorAgent",
                "video_url": url,
                "content": obs_content,
                "relevance": 1.0,
                "timestamp": time.time()
            }
            await self.memory.append_observation(obs)
            
            return {"success": True, "details": details}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

async def main():
    agent = TikTokAuditorAgent()
    agent.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 TikTokAuditorAgent stopping...")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main())
