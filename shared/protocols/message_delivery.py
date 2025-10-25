"""
Message delivery system with ordering guarantees and dead letter queue handling.
Provides reliable inter-agent communication for HealthSync system.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from collections import defaultdict, deque

from .agent_messages import AgentMessage, AgentAcknowledgment, ErrorResponse, ErrorCodes
from ..utils.logging import get_logger


class MessageStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class DeliveryPriority(Enum):
    """Message delivery priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class MessageEnvelope:
    """Enhanced message envelope with delivery metadata."""
    message: AgentMessage
    priority: DeliveryPriority = DeliveryPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    status: MessageStatus = MessageStatus.PENDING
    delivery_attempts: List[Dict[str, Any]] = field(default_factory=list)
    sequence_number: Optional[int] = None
    ordered_group: Optional[str] = None


class MessageQueue:
    """Priority queue for message delivery with ordering guarantees."""
    
    def __init__(self):
        self.queues: Dict[DeliveryPriority, deque] = {
            priority: deque() for priority in DeliveryPriority
        }
        self.ordered_sequences: Dict[str, List[MessageEnvelope]] = defaultdict(list)
        self.sequence_counters: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
    
    async def enqueue(self, envelope: MessageEnvelope) -> None:
        """Add message to appropriate queue."""
        async with self._lock:
            if envelope.ordered_group:
                # Handle ordered messages
                envelope.sequence_number = self.sequence_counters[envelope.ordered_group]
                self.sequence_counters[envelope.ordered_group] += 1
                self.ordered_sequences[envelope.ordered_group].append(envelope)
            else:
                # Add to priority queue
                self.queues[envelope.priority].append(envelope)
    
    async def dequeue(self) -> Optional[MessageEnvelope]:
        """Get next message to deliver, respecting priority and ordering."""
        async with self._lock:
            # First, check for ordered messages that can be delivered
            for group_id, messages in self.ordered_sequences.items():
                if messages and messages[0].status == MessageStatus.PENDING:
                    return messages.popleft()
            
            # Then check priority queues from highest to lowest
            for priority in sorted(DeliveryPriority, key=lambda x: x.value, reverse=True):
                queue = self.queues[priority]
                while queue:
                    envelope = queue.popleft()
                    if envelope.status == MessageStatus.PENDING:
                        return envelope
            
            return None
    
    async def mark_delivered(self, message_id: str) -> None:
        """Mark message as successfully delivered."""
        async with self._lock:
            # Update status in ordered sequences
            for messages in self.ordered_sequences.values():
                for envelope in messages:
                    if envelope.message.message_id == message_id:
                        envelope.status = MessageStatus.ACKNOWLEDGED
                        return
    
    async def get_pending_count(self) -> int:
        """Get count of pending messages."""
        async with self._lock:
            count = 0
            for queue in self.queues.values():
                count += len([e for e in queue if e.status == MessageStatus.PENDING])
            
            for messages in self.ordered_sequences.values():
                count += len([e for e in messages if e.status == MessageStatus.PENDING])
            
            return count


class DeadLetterQueue:
    """Dead letter queue for failed messages."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.messages: deque = deque(maxlen=max_size)
        self.failure_reasons: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self.logger = get_logger("dead_letter_queue")
    
    async def add_message(self, envelope: MessageEnvelope, failure_reason: str) -> None:
        """Add failed message to dead letter queue."""
        async with self._lock:
            envelope.status = MessageStatus.DEAD_LETTER
            self.messages.append(envelope)
            self.failure_reasons[envelope.message.message_id] = failure_reason
            
            self.logger.warning("Message added to dead letter queue",
                              message_id=envelope.message.message_id,
                              failure_reason=failure_reason,
                              retry_count=envelope.retry_count)
    
    async def get_messages(self, limit: int = 100) -> List[MessageEnvelope]:
        """Get messages from dead letter queue."""
        async with self._lock:
            return list(self.messages)[-limit:]
    
    async def requeue_message(self, message_id: str) -> Optional[MessageEnvelope]:
        """Remove message from dead letter queue for reprocessing."""
        async with self._lock:
            for i, envelope in enumerate(self.messages):
                if envelope.message.message_id == message_id:
                    envelope.status = MessageStatus.PENDING
                    envelope.retry_count = 0
                    envelope.next_retry = None
                    del self.messages[i]
                    if message_id in self.failure_reasons:
                        del self.failure_reasons[message_id]
                    return envelope
            return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get dead letter queue statistics."""
        async with self._lock:
            failure_counts = defaultdict(int)
            for reason in self.failure_reasons.values():
                failure_counts[reason] += 1
            
            return {
                "total_messages": len(self.messages),
                "failure_reasons": dict(failure_counts),
                "oldest_message": self.messages[0].created_at.isoformat() if self.messages else None,
                "newest_message": self.messages[-1].created_at.isoformat() if self.messages else None
            }


class MessageDeliveryService:
    """Reliable message delivery service with ordering and retry guarantees."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = get_logger(f"{agent_id}_delivery")
        
        # Message management
        self.outbound_queue = MessageQueue()
        self.pending_acks: Dict[str, MessageEnvelope] = {}
        self.dead_letter_queue = DeadLetterQueue()
        
        # Delivery tracking
        self.delivery_callbacks: Dict[str, Callable] = {}
        self.ack_timeout = 30.0  # seconds
        self.max_retry_delay = 300.0  # 5 minutes
        
        # Service state
        self.is_running = False
        self.delivery_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_acknowledged": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "average_delivery_time": 0.0
        }
    
    async def start(self) -> None:
        """Start the message delivery service."""
        if self.is_running:
            return
        
        self.is_running = True
        self.delivery_task = asyncio.create_task(self._delivery_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Message delivery service started")
    
    async def stop(self) -> None:
        """Stop the message delivery service."""
        self.is_running = False
        
        if self.delivery_task:
            self.delivery_task.cancel()
            try:
                await self.delivery_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Message delivery service stopped")
    
    async def send_message(self, message: AgentMessage, 
                          priority: DeliveryPriority = DeliveryPriority.NORMAL,
                          ordered_group: Optional[str] = None,
                          max_retries: int = 3,
                          delivery_callback: Optional[Callable] = None) -> str:
        """Send message with delivery guarantees."""
        envelope = MessageEnvelope(
            message=message,
            priority=priority,
            max_retries=max_retries,
            ordered_group=ordered_group
        )
        
        if delivery_callback:
            self.delivery_callbacks[message.message_id] = delivery_callback
        
        await self.outbound_queue.enqueue(envelope)
        
        self.logger.info("Message queued for delivery",
                        message_id=message.message_id,
                        recipient=message.recipient_agent,
                        priority=priority.name,
                        ordered_group=ordered_group)
        
        return message.message_id
    
    async def handle_acknowledgment(self, ack: AgentAcknowledgment) -> None:
        """Handle acknowledgment from recipient agent."""
        message_id = ack.original_message_id
        
        if message_id in self.pending_acks:
            envelope = self.pending_acks[message_id]
            envelope.status = MessageStatus.ACKNOWLEDGED
            
            # Calculate delivery time
            delivery_time = (datetime.utcnow() - envelope.created_at).total_seconds()
            self._update_delivery_stats(delivery_time, True)
            
            # Mark as delivered in queue
            await self.outbound_queue.mark_delivered(message_id)
            
            # Call delivery callback if registered
            if message_id in self.delivery_callbacks:
                callback = self.delivery_callbacks[message_id]
                try:
                    await callback(ack) if asyncio.iscoroutinefunction(callback) else callback(ack)
                except Exception as e:
                    self.logger.error("Delivery callback failed",
                                    message_id=message_id,
                                    error=str(e))
                finally:
                    del self.delivery_callbacks[message_id]
            
            del self.pending_acks[message_id]
            
            self.logger.info("Message acknowledged",
                           message_id=message_id,
                           delivery_time=delivery_time,
                           status=ack.status)
        else:
            self.logger.warning("Received acknowledgment for unknown message",
                              message_id=message_id)
    
    async def _delivery_loop(self) -> None:
        """Main delivery loop."""
        while self.is_running:
            try:
                envelope = await self.outbound_queue.dequeue()
                if envelope:
                    await self._attempt_delivery(envelope)
                else:
                    # No messages to deliver, wait a bit
                    await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error("Error in delivery loop", error=str(e))
                await asyncio.sleep(1.0)
    
    async def _attempt_delivery(self, envelope: MessageEnvelope) -> None:
        """Attempt to deliver a message."""
        message = envelope.message
        
        try:
            # Record delivery attempt
            attempt_data = {
                "attempt_number": envelope.retry_count + 1,
                "timestamp": datetime.utcnow().isoformat(),
                "recipient": message.recipient_agent
            }
            envelope.delivery_attempts.append(attempt_data)
            envelope.last_attempt = datetime.utcnow()
            envelope.retry_count += 1
            
            # Simulate message sending (in real implementation, this would use uAgents)
            await self._send_to_agent(message)
            
            envelope.status = MessageStatus.SENT
            self.stats["messages_sent"] += 1
            
            # If acknowledgment is required, track it
            if message.requires_acknowledgment:
                self.pending_acks[message.message_id] = envelope
                # Set timeout for acknowledgment
                asyncio.create_task(self._handle_ack_timeout(message.message_id))
            else:
                # No ack required, consider it delivered
                envelope.status = MessageStatus.ACKNOWLEDGED
                self._update_delivery_stats(
                    (datetime.utcnow() - envelope.created_at).total_seconds(), 
                    True
                )
            
            self.logger.info("Message delivery attempted",
                           message_id=message.message_id,
                           attempt=envelope.retry_count,
                           requires_ack=message.requires_acknowledgment)
        
        except Exception as e:
            await self._handle_delivery_failure(envelope, str(e))
    
    async def _send_to_agent(self, message: AgentMessage) -> None:
        """Send message to target agent (placeholder for actual uAgents integration)."""
        # In real implementation, this would use uAgents Context.send()
        # For now, we'll simulate the sending process
        await asyncio.sleep(0.01)  # Simulate network delay
        
        # Simulate occasional failures for testing
        import random
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("Simulated network failure")
    
    async def _handle_delivery_failure(self, envelope: MessageEnvelope, error: str) -> None:
        """Handle failed message delivery."""
        envelope.status = MessageStatus.FAILED
        self.stats["messages_failed"] += 1
        
        if envelope.retry_count < envelope.max_retries:
            # Schedule retry with exponential backoff
            delay = min(2 ** (envelope.retry_count - 1), self.max_retry_delay)
            envelope.next_retry = datetime.utcnow() + timedelta(seconds=delay)
            envelope.status = MessageStatus.PENDING
            
            # Re-queue for retry
            await self.outbound_queue.enqueue(envelope)
            self.stats["messages_retried"] += 1
            
            self.logger.warning("Message delivery failed, will retry",
                              message_id=envelope.message.message_id,
                              error=error,
                              retry_count=envelope.retry_count,
                              next_retry=envelope.next_retry.isoformat())
        else:
            # Max retries exceeded, send to dead letter queue
            await self.dead_letter_queue.add_message(envelope, error)
            
            self.logger.error("Message delivery failed permanently",
                            message_id=envelope.message.message_id,
                            error=error,
                            retry_count=envelope.retry_count)
    
    async def _handle_ack_timeout(self, message_id: str) -> None:
        """Handle acknowledgment timeout."""
        await asyncio.sleep(self.ack_timeout)
        
        if message_id in self.pending_acks:
            envelope = self.pending_acks[message_id]
            await self._handle_delivery_failure(envelope, "Acknowledgment timeout")
            del self.pending_acks[message_id]
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired data."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Clean up old pending acknowledgments
                cutoff_time = datetime.utcnow() - timedelta(minutes=10)
                expired_acks = [
                    msg_id for msg_id, envelope in self.pending_acks.items()
                    if envelope.last_attempt and envelope.last_attempt < cutoff_time
                ]
                
                for msg_id in expired_acks:
                    envelope = self.pending_acks[msg_id]
                    await self._handle_delivery_failure(envelope, "Acknowledgment expired")
                    del self.pending_acks[msg_id]
                
                if expired_acks:
                    self.logger.info("Cleaned up expired acknowledgments",
                                   count=len(expired_acks))
            
            except Exception as e:
                self.logger.error("Error in cleanup loop", error=str(e))
    
    def _update_delivery_stats(self, delivery_time: float, success: bool) -> None:
        """Update delivery statistics."""
        if success:
            self.stats["messages_acknowledged"] += 1
            
            # Update average delivery time
            current_avg = self.stats["average_delivery_time"]
            total_acks = self.stats["messages_acknowledged"]
            self.stats["average_delivery_time"] = (
                (current_avg * (total_acks - 1) + delivery_time) / total_acks
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get delivery service statistics."""
        pending_count = await self.outbound_queue.get_pending_count()
        dlq_stats = await self.dead_letter_queue.get_statistics()
        
        return {
            **self.stats,
            "pending_messages": pending_count,
            "pending_acknowledgments": len(self.pending_acks),
            "dead_letter_queue": dlq_stats,
            "is_running": self.is_running
        }
    
    async def get_dead_letter_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from dead letter queue."""
        messages = await self.dead_letter_queue.get_messages(limit)
        return [
            {
                "message_id": envelope.message.message_id,
                "recipient": envelope.message.recipient_agent,
                "message_type": envelope.message.message_type,
                "created_at": envelope.created_at.isoformat(),
                "retry_count": envelope.retry_count,
                "failure_reason": self.dead_letter_queue.failure_reasons.get(
                    envelope.message.message_id, "Unknown"
                )
            }
            for envelope in messages
        ]
    
    async def requeue_dead_letter_message(self, message_id: str) -> bool:
        """Requeue message from dead letter queue."""
        envelope = await self.dead_letter_queue.requeue_message(message_id)
        if envelope:
            await self.outbound_queue.enqueue(envelope)
            self.logger.info("Message requeued from dead letter queue",
                           message_id=message_id)
            return True
        return False