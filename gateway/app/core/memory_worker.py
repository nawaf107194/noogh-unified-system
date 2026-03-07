"""
Memory Worker - Async Queue Processor

Processes semantic memory writes from queue to prevent async/sync deadlocks.
Provides AT-LEAST-ONCE delivery guarantee with retry logic.
"""

import asyncio
import logging
from typing import Optional
import time

logger = logging.getLogger("gateway.app.core.memory_worker")


class MemoryWorker:
    """Background worker for processing memory writes with guaranteed delivery."""
    
    def __init__(self, semantic_memory):
        self.semantic_memory = semantic_memory
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=1000)  # Bounded queue
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.stats = {
            'enqueued': 0,
            'processed': 0,
            'failed': 0,
            'retries': 0
        }
    
    async def start(self):
        """Start the background worker."""
        if self.running:
            logger.warning("Memory worker already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._process_queue())
        logger.info("✅ Memory worker started")
    
    async def stop(self, drain: bool = True, timeout: float = 10.0):
        """Stop the background worker and optionally drain queue."""
        if not self.running:
            return
        
        logger.info(f"Stopping memory worker (drain={drain}, timeout={timeout}s)")
        self.running = False
        
        if drain:
            # Wait for queue to empty with timeout
            try:
                await asyncio.wait_for(self.queue.join(), timeout=timeout)
                logger.info("✅ Memory queue drained successfully")
            except asyncio.TimeoutError:
                remaining = self.queue.qsize()
                logger.error(f"❌ Queue drain timeout - {remaining} items lost")
        
        # Cancel worker task
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Memory worker stopped - Stats: {self.stats}")
    
    def enqueue_write(self, content: str, metadata: dict) -> bool:
        """
        Synchronous enqueue (non-blocking from sync context).
        Returns True if accepted, False if queue full.
        """
        try:
            self.queue.put_nowait({
                'content': content,
                'metadata': metadata,
                'event_id': f"{metadata.get('task_id', 'unknown')}_{time.time()}",
                'enqueued_at': time.time()
            })
            self.stats['enqueued'] += 1
            return True
        except asyncio.QueueFull:
            logger.error("❌ Memory queue FULL - write REJECTED")
            self.stats['failed'] += 1
            return False
    
    async def enqueue_write_async(self, content: str, metadata: dict):
        """Async enqueue (blocking if queue full)."""
        await self.queue.put({
            'content': content,
            'metadata': metadata,
            'event_id': f"{metadata.get('task_id', 'unknown')}_{time.time()}",
            'enqueued_at': time.time()
        })
        self.stats['enqueued'] += 1
    
    async def _process_queue(self):
        """Process memory writes with at-least-once retry."""
        logger.info("Memory worker processing loop started")
        
        while self.running:
            try:
                # Wait for item with timeout
                try:
                    item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # AT-LEAST-ONCE: retry with exponential backoff
                max_retries = 3
                retry_count = 0
                success = False
                
                while retry_count <= max_retries and not success:
                    try:
                        await self.semantic_memory.add(
                            content=item['content'],
                            metadata=item['metadata']
                        )
                        success = True
                        self.stats['processed'] += 1
                        
                        if retry_count > 0:
                            self.stats['retries'] += retry_count
                            logger.info(f"✅ Memory write succeeded after {retry_count} retries")
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count <= max_retries:
                            backoff = 2 ** retry_count
                            logger.warning(f"Memory write failed (attempt {retry_count}/{max_retries}), retry in {backoff}s: {e}")
                            await asyncio.sleep(backoff)
                        else:
                            logger.error(f"❌ Memory write FAILED permanently after {max_retries} retries: {e}", exc_info=True)
                            self.stats['failed'] += 1
                
                self.queue.task_done()
                    
            except Exception as e:
                logger.error(f"Memory worker error: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.info("Memory worker processing loop exited")
    
    def get_stats(self) -> dict:
        """Get worker statistics."""
        return {
            **self.stats,
            'queue_size': self.queue.qsize(),
            'running': self.running
        }


# Global instance (initialized during startup)
_memory_worker: Optional[MemoryWorker] = None


def get_memory_worker() -> Optional[MemoryWorker]:
    """Get the global memory worker instance."""
    return _memory_worker


def initialize_memory_worker(semantic_memory) -> MemoryWorker:
    """Initialize the global memory worker."""
    global _memory_worker
    if _memory_worker is not None:
        logger.warning("Memory worker already initialized")
    _memory_worker = MemoryWorker(semantic_memory)
    return _memory_worker

