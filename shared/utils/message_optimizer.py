"""
Message processing optimization for high-throughput agent communication.
Provides batching, prioritization, and async processing capabilities.
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from collections import deque, defaultdict
import heapq
from contextlib import asynccontextmanager

from .performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)

class MessagePriority(Enum):
    """Message priority levels for processing order."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class OptimizedMessage:
    """Enhanced message with optimization metadata."""
    id: str
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0
    batch_key: Optional[str] = None  # For message batching
    
    def __lt__(self, other):
        """Enable priority queue ordering."""
        return self.priority.value < other.priority.value

@dataclass
class ProcessingStats:
    """Statistics for message processing performance."""
    total_processed: int = 0
    total_failed: int = 0
    avg_processing_time: float = 0.0
    max_processing_time: float = 0.0
    throughput: float = 0.0  # messages per second
    queue_size: int = 0
    batch_efficiency: float = 0.0

class MessageBatcher:
    """
    Batches messages for efficient processing.
    """
    
    def __init__(self, batch_size: int = 10, batch_timeout: float = 1.0):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.batches: Dict[str, List[OptimizedMessage]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self.batch_callbacks: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        
    async def add_message(self, message: OptimizedMessage, callback: Callable):
        """Add message to batch for processing."""
        batch_key = message.batch_key or "default"
        
        async with self._lock:
            self.batches[batch_key].append(message)
            self.batch_callbacks[batch_key] = callback
            
            # Start timer for this batch if not already started
            if batch_key not in self.batch_timers:
                self.batch_timers[batch_key] = asyncio.create_task(
                    self._batch_timer(batch_key)
                )
                
            # Process batch if it's full
            if len(self.batches[batch_key]) >= self.batch_size:
                await self._process_batch(batch_key)
                
    async def _batch_timer(self, batch_key: str):
        """Timer to process batch after timeout."""
        try:
            await asyncio.sleep(self.batch_timeout)
            async with self._lock:
                if batch_key in self.batches and self.batches[batch_key]:
                    await self._process_batch(batch_key)
        except asyncio.CancelledError:
            pass
            
    async def _process_batch(self, batch_key: str):
        """Process a complete batch of messages."""
        if batch_key not in self.batches or not self.batches[batch_key]:
            return
            
        messages = self.batches[batch_key]
        callback = self.batch_callbacks[batch_key]
        
        # Clear batch
        self.batches[batch_key] = []
        
        # Cancel timer
        if batch_key in self.batch_timers:
            self.batch_timers[batch_key].cancel()
            del self.batch_timers[batch_key]
            
        # Process batch
        try:
            await callback(messages)
        except Exception as e:
            logger.error(f"Error processing batch {batch_key}: {e}")
            
    async def flush_all(self):
        """Flush all pending batches."""
        async with self._lock:
            for batch_key in list(self.batches.keys()):
                if self.batches[batch_key]:
                    await self._process_batch(batch_key)

class MessageProcessor:
    """
    High-performance message processor with optimization features.
    """
    
    def __init__(self, max_workers: int = 10, enable_batching: bool = True):
        self.max_workers = max_workers
        self.enable_batching = enable_batching
        
        # Processing queues
        self.priority_queue: List[OptimizedMessage] = []
        self.processing_queue = asyncio.Queue()
        self.dead_letter_queue: List[OptimizedMessage] = []
        
        # Workers and state
        self.workers: List[asyncio.Task] = []
        self.message_handlers: Dict[str, Callable] = {}
        self.middleware: List[Callable] = []
        self.running = False
        
        # Optimization components
        self.batcher = MessageBatcher() if enable_batching else None
        self.circuit_breakers: Dict[str, 'CircuitBreaker'] = {}
        
        # Statistics
        self.stats = ProcessingStats()
        self.performance_monitor = get_performance_monitor()
        
        # Locks
        self._queue_lock = asyncio.Lock()
        self._stats_lock = threading.Lock()
        
    async def start(self):
        """Start the message processor."""
        if self.running:
            return
            
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
            
        logger.info(f"Message processor started with {self.max_workers} workers")
        
    async def stop(self):
        """Stop the message processor."""
        if not self.running:
            return
            
        self.running = False
        
        # Flush pending batches
        if self.batcher:
            await self.batcher.flush_all()
            
        # Cancel workers
        for worker in self.workers:
            worker.cancel()
            
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Message processor stopped")
        
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler for a specific message type."""
        self.message_handlers[message_type] = handler
        
    def add_middleware(self, middleware: Callable):
        """Add middleware for message processing."""
        self.middleware.append(middleware)
        
    async def send_message(self, message: OptimizedMessage) -> bool:
        """Send a message for processing."""
        if not self.running:
            raise RuntimeError("Message processor not running")
            
        # Apply middleware
        for middleware in self.middleware:
            try:
                message = await middleware(message)
                if message is None:
                    return False  # Message filtered out
            except Exception as e:
                logger.error(f"Middleware error: {e}")
                return False
                
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers.get(message.recipient)
        if circuit_breaker and circuit_breaker.is_open():
            logger.warning(f"Circuit breaker open for {message.recipient}, dropping message")
            return False
            
        # Add to priority queue
        async with self._queue_lock:
            heapq.heappush(self.priority_queue, message)
            self.stats.queue_size = len(self.priority_queue)
            
        # Notify workers
        await self.processing_queue.put(None)
        
        return True
        
    async def _worker(self, worker_id: str):
        """Worker task for processing messages."""
        while self.running:
            try:
                # Wait for work
                await self.processing_queue.get()
                
                # Get next message from priority queue
                message = None
                async with self._queue_lock:
                    if self.priority_queue:
                        message = heapq.heappop(self.priority_queue)
                        self.stats.queue_size = len(self.priority_queue)
                        
                if message is None:
                    continue
                    
                # Process message
                await self._process_message(message, worker_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
                
    async def _process_message(self, message: OptimizedMessage, worker_id: str):
        """Process a single message."""
        start_time = time.perf_counter()
        
        try:
            # Check if batching is enabled and message supports it
            if self.batcher and message.batch_key:
                handler = self.message_handlers.get(message.message_type)
                if handler:
                    await self.batcher.add_message(message, self._process_batch)
                    return
                    
            # Process individual message
            handler = self.message_handlers.get(message.message_type)
            if not handler:
                raise ValueError(f"No handler for message type: {message.message_type}")
                
            # Execute handler with timeout
            await asyncio.wait_for(handler(message), timeout=message.timeout)
            
            # Update success statistics
            processing_time = (time.perf_counter() - start_time) * 1000
            self._update_stats(processing_time, success=True)
            
            # Record performance metrics
            self.performance_monitor.record_metric(
                "message_response_time",
                processing_time,
                tags={
                    "agent_id": message.recipient,
                    "message_type": message.message_type,
                    "worker_id": worker_id
                }
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"Message processing timeout: {message.id}")
            await self._handle_failed_message(message, "timeout")
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            await self._handle_failed_message(message, str(e))
            
    async def _process_batch(self, messages: List[OptimizedMessage]):
        """Process a batch of messages."""
        if not messages:
            return
            
        start_time = time.perf_counter()
        
        try:
            # Group messages by handler
            handler_groups = defaultdict(list)
            for message in messages:
                handler_groups[message.message_type].append(message)
                
            # Process each group
            for message_type, group_messages in handler_groups.items():
                handler = self.message_handlers.get(message_type)
                if handler:
                    # Check if handler supports batch processing
                    if hasattr(handler, 'process_batch'):
                        await handler.process_batch(group_messages)
                    else:
                        # Process individually
                        for message in group_messages:
                            await handler(message)
                            
            # Update batch statistics
            processing_time = (time.perf_counter() - start_time) * 1000
            batch_efficiency = len(messages) / processing_time if processing_time > 0 else 0
            
            with self._stats_lock:
                self.stats.batch_efficiency = (
                    (self.stats.batch_efficiency + batch_efficiency) / 2
                    if self.stats.batch_efficiency > 0 else batch_efficiency
                )
                
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            # Retry individual messages
            for message in messages:
                await self._handle_failed_message(message, str(e))
                
    async def _handle_failed_message(self, message: OptimizedMessage, error: str):
        """Handle failed message processing."""
        message.retry_count += 1
        
        # Update failure statistics
        self._update_stats(0, success=False)
        
        # Record error metric
        self.performance_monitor.record_metric(
            "message_error",
            1,
            tags={
                "agent_id": message.recipient,
                "message_type": message.message_type,
                "error": error
            }
        )
        
        # Retry or move to dead letter queue
        if message.retry_count <= message.max_retries:
            # Exponential backoff
            delay = min(2 ** message.retry_count, 60)
            await asyncio.sleep(delay)
            
            # Re-queue message
            async with self._queue_lock:
                heapq.heappush(self.priority_queue, message)
                
            await self.processing_queue.put(None)
        else:
            # Move to dead letter queue
            self.dead_letter_queue.append(message)
            logger.error(f"Message moved to dead letter queue: {message.id}")
            
    def _update_stats(self, processing_time: float, success: bool):
        """Update processing statistics."""
        with self._stats_lock:
            if success:
                self.stats.total_processed += 1
                
                # Update average processing time
                if self.stats.total_processed == 1:
                    self.stats.avg_processing_time = processing_time
                else:
                    self.stats.avg_processing_time = (
                        (self.stats.avg_processing_time * (self.stats.total_processed - 1) + processing_time) /
                        self.stats.total_processed
                    )
                    
                self.stats.max_processing_time = max(self.stats.max_processing_time, processing_time)
            else:
                self.stats.total_failed += 1
                
            # Calculate throughput (messages per second over last minute)
            total_messages = self.stats.total_processed + self.stats.total_failed
            if total_messages > 0:
                self.stats.throughput = total_messages / 60.0  # Simplified calculation
                
    def get_stats(self) -> ProcessingStats:
        """Get current processing statistics."""
        with self._stats_lock:
            return ProcessingStats(
                total_processed=self.stats.total_processed,
                total_failed=self.stats.total_failed,
                avg_processing_time=self.stats.avg_processing_time,
                max_processing_time=self.stats.max_processing_time,
                throughput=self.stats.throughput,
                queue_size=self.stats.queue_size,
                batch_efficiency=self.stats.batch_efficiency
            )
            
    def get_dead_letter_messages(self) -> List[OptimizedMessage]:
        """Get messages in dead letter queue."""
        return list(self.dead_letter_queue)
        
    def clear_dead_letter_queue(self):
        """Clear the dead letter queue."""
        self.dead_letter_queue.clear()

class CircuitBreaker:
    """
    Circuit breaker pattern for agent failure protection.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.state = "closed"
        
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.state == "closed":
            return False
            
        if self.state == "open":
            # Check if recovery timeout has passed
            if (self.last_failure_time and 
                time.time() - self.last_failure_time > self.recovery_timeout):
                self.state = "half-open"
                return False
            return True
            
        return False  # half-open state

# Global message processor instance
_global_processor: Optional[MessageProcessor] = None

def get_message_processor(max_workers: int = 10) -> MessageProcessor:
    """Get or create global message processor instance."""
    global _global_processor
    if _global_processor is None:
        _global_processor = MessageProcessor(max_workers=max_workers)
    return _global_processor