"""
Enhanced communication manager for reliable inter-agent messaging.
Integrates message delivery, circuit breakers, and monitoring.
"""

import asyncio
from typing import Dict, Any, Optional, Callable, List, Set
from datetime import datetime, timedelta
from uagents import Context

from .agent_messages import (
    AgentMessage, AgentAcknowledgment, MessageTypes, ErrorResponse, ErrorCodes
)
from .message_delivery import (
    MessageDeliveryService, DeliveryPriority, MessageStatus
)
from ..utils.error_handling import CircuitBreaker, RetryHandler
from ..utils.logging import get_logger


class CommunicationManager:
    """Enhanced communication manager with reliability features."""
    
    def __init__(self, agent_id: str, context: Optional[Context] = None):
        self.agent_id = agent_id
        self.context = context
        self.logger = get_logger(f"{agent_id}_comm")
        
        # Core services
        self.delivery_service = MessageDeliveryService(agent_id)
        
        # Circuit breakers for each recipient agent
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Message routing and handlers
        self.message_handlers: Dict[str, Callable] = {}
        self.middleware_stack: List[Callable] = []
        
        # Agent discovery and health tracking
        self.known_agents: Set[str] = set()
        self.agent_health: Dict[str, Dict[str, Any]] = {}
        self.last_health_check: Dict[str, datetime] = {}
        
        # Communication patterns
        self.conversation_contexts: Dict[str, Dict[str, Any]] = {}
        self.message_correlations: Dict[str, str] = {}
        
        # Monitoring
        self.communication_stats = {
            "total_sent": 0,
            "total_received": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "circuit_breaker_trips": 0
        }
    
    async def start(self) -> None:
        """Start the communication manager."""
        await self.delivery_service.start()
        self.logger.info("Communication manager started")
    
    async def stop(self) -> None:
        """Stop the communication manager."""
        await self.delivery_service.stop()
        self.logger.info("Communication manager stopped")
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register handler for specific message type."""
        self.message_handlers[message_type] = handler
        self.logger.info("Message handler registered", message_type=message_type)
    
    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to message processing pipeline."""
        self.middleware_stack.append(middleware)
        self.logger.info("Middleware added to communication stack")
    
    async def send_message(self, 
                          recipient: str,
                          message_type: str,
                          payload: Dict[str, Any],
                          priority: DeliveryPriority = DeliveryPriority.NORMAL,
                          requires_ack: bool = True,
                          ordered_group: Optional[str] = None,
                          correlation_id: Optional[str] = None,
                          timeout: float = 30.0) -> str:
        """Send message with enhanced reliability features."""
        
        # Check circuit breaker for recipient
        if recipient in self.circuit_breakers:
            breaker = self.circuit_breakers[recipient]
            if breaker.state == "OPEN":
                self.logger.warning("Circuit breaker open for recipient",
                                  recipient=recipient)
                raise Exception(f"Circuit breaker open for {recipient}")
        
        # Create message
        message = AgentMessage(
            sender_agent=self.agent_id,
            recipient_agent=recipient,
            message_type=message_type,
            payload=payload,
            requires_acknowledgment=requires_ack,
            correlation_id=correlation_id
        )
        
        # Apply middleware
        for middleware in self.middleware_stack:
            try:
                message = await middleware(message) if asyncio.iscoroutinefunction(middleware) else middleware(message)
            except Exception as e:
                self.logger.error("Middleware failed", error=str(e))
                raise
        
        # Track correlation if provided
        if correlation_id:
            self.message_correlations[message.message_id] = correlation_id
        
        # Send through delivery service
        try:
            message_id = await self.delivery_service.send_message(
                message=message,
                priority=priority,
                ordered_group=ordered_group,
                delivery_callback=self._on_delivery_complete
            )
            
            self.communication_stats["total_sent"] += 1
            self.known_agents.add(recipient)
            
            self.logger.info("Message sent",
                           message_id=message_id,
                           recipient=recipient,
                           message_type=message_type,
                           priority=priority.name)
            
            return message_id
        
        except Exception as e:
            self._record_communication_failure(recipient, str(e))
            raise
    
    async def send_request_response(self,
                                  recipient: str,
                                  message_type: str,
                                  payload: Dict[str, Any],
                                  timeout: float = 30.0) -> Dict[str, Any]:
        """Send message and wait for response."""
        correlation_id = f"req_{datetime.utcnow().timestamp()}"
        
        # Set up response waiter
        response_future = asyncio.Future()
        
        def response_handler(ack: AgentAcknowledgment):
            if not response_future.done():
                response_future.set_result(ack.response_data or {})
        
        # Send message
        message_id = await self.send_message(
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id,
            requires_ack=True
        )
        
        # Register temporary callback
        self.delivery_service.delivery_callbacks[message_id] = response_handler
        
        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            self.logger.error("Request-response timeout",
                            message_id=message_id,
                            recipient=recipient)
            raise
        finally:
            # Clean up callback
            if message_id in self.delivery_service.delivery_callbacks:
                del self.delivery_service.delivery_callbacks[message_id]
    
    async def handle_incoming_message(self, sender: str, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming message with middleware and routing."""
        self.communication_stats["total_received"] += 1
        self.known_agents.add(sender)
        
        try:
            # Apply middleware in reverse order
            processed_message = message
            for middleware in reversed(self.middleware_stack):
                try:
                    processed_message = await middleware(processed_message) if asyncio.iscoroutinefunction(middleware) else middleware(processed_message)
                except Exception as e:
                    self.logger.error("Incoming middleware failed", error=str(e))
                    return {"error": f"Middleware processing failed: {str(e)}"}
            
            # Route to appropriate handler
            if message.message_type in self.message_handlers:
                handler = self.message_handlers[message.message_type]
                try:
                    result = await handler(sender, processed_message) if asyncio.iscoroutinefunction(handler) else handler(sender, processed_message)
                    
                    self.logger.info("Message processed successfully",
                                   message_id=message.message_id,
                                   message_type=message.message_type,
                                   sender=sender)
                    
                    return result
                except Exception as e:
                    self.logger.error("Message handler failed",
                                    message_id=message.message_id,
                                    message_type=message.message_type,
                                    error=str(e))
                    return {"error": f"Handler failed: {str(e)}"}
            else:
                self.logger.warning("No handler for message type",
                                  message_type=message.message_type)
                return {"error": f"No handler for message type: {message.message_type}"}
        
        except Exception as e:
            self.logger.error("Error processing incoming message",
                            message_id=message.message_id,
                            error=str(e))
            return {"error": f"Processing failed: {str(e)}"}
    
    async def handle_acknowledgment(self, ack: AgentAcknowledgment) -> None:
        """Handle acknowledgment from delivery service."""
        await self.delivery_service.handle_acknowledgment(ack)
        
        # Update circuit breaker on successful delivery
        sender = ack.sender_agent
        if sender in self.circuit_breakers:
            # Record success to help circuit breaker recovery
            pass
    
    async def broadcast_message(self,
                              message_type: str,
                              payload: Dict[str, Any],
                              recipients: Optional[List[str]] = None,
                              priority: DeliveryPriority = DeliveryPriority.NORMAL) -> List[str]:
        """Broadcast message to multiple recipients."""
        if recipients is None:
            recipients = list(self.known_agents)
        
        message_ids = []
        for recipient in recipients:
            try:
                message_id = await self.send_message(
                    recipient=recipient,
                    message_type=message_type,
                    payload=payload,
                    priority=priority,
                    requires_ack=False  # Broadcasts typically don't require acks
                )
                message_ids.append(message_id)
            except Exception as e:
                self.logger.error("Broadcast failed for recipient",
                                recipient=recipient,
                                error=str(e))
        
        self.logger.info("Broadcast completed",
                        message_type=message_type,
                        recipients_count=len(recipients),
                        successful_sends=len(message_ids))
        
        return message_ids
    
    async def start_conversation(self, 
                               recipient: str,
                               conversation_type: str,
                               initial_message_type: str,
                               initial_payload: Dict[str, Any]) -> str:
        """Start a conversation context with another agent."""
        conversation_id = f"conv_{self.agent_id}_{recipient}_{datetime.utcnow().timestamp()}"
        
        self.conversation_contexts[conversation_id] = {
            "participants": [self.agent_id, recipient],
            "conversation_type": conversation_type,
            "started_at": datetime.utcnow(),
            "message_count": 0,
            "last_activity": datetime.utcnow()
        }
        
        # Send initial message with conversation context
        await self.send_message(
            recipient=recipient,
            message_type=initial_message_type,
            payload={
                **initial_payload,
                "conversation_id": conversation_id,
                "conversation_type": conversation_type
            },
            correlation_id=conversation_id
        )
        
        self.logger.info("Conversation started",
                        conversation_id=conversation_id,
                        recipient=recipient,
                        conversation_type=conversation_type)
        
        return conversation_id
    
    def get_circuit_breaker(self, recipient: str) -> CircuitBreaker:
        """Get or create circuit breaker for recipient."""
        if recipient not in self.circuit_breakers:
            self.circuit_breakers[recipient] = CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=60,
                expected_exception=Exception
            )
        return self.circuit_breakers[recipient]
    
    def _record_communication_failure(self, recipient: str, error: str) -> None:
        """Record communication failure for circuit breaker."""
        breaker = self.get_circuit_breaker(recipient)
        breaker._on_failure()
        
        if breaker.state == "OPEN":
            self.communication_stats["circuit_breaker_trips"] += 1
            self.logger.warning("Circuit breaker opened for recipient",
                              recipient=recipient,
                              error=error)
    
    async def _on_delivery_complete(self, ack: AgentAcknowledgment) -> None:
        """Callback for successful message delivery."""
        if ack.status == "processed":
            self.communication_stats["successful_deliveries"] += 1
        else:
            self.communication_stats["failed_deliveries"] += 1
        
        # Update agent health based on response
        sender = ack.sender_agent
        self.agent_health[sender] = {
            "last_response": datetime.utcnow(),
            "status": ack.status,
            "response_time": ack.processing_time
        }
    
    async def health_check_agents(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on known agents."""
        health_results = {}
        
        for agent_id in self.known_agents:
            try:
                # Send health check message
                response = await self.send_request_response(
                    recipient=agent_id,
                    message_type=MessageTypes.HEALTH_CHECK,
                    payload={"timestamp": datetime.utcnow().isoformat()},
                    timeout=10.0
                )
                
                health_results[agent_id] = {
                    "status": "healthy",
                    "response_time": response.get("response_time", 0),
                    "last_check": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                health_results[agent_id] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
        
        self.last_health_check = {agent: datetime.utcnow() for agent in self.known_agents}
        return health_results
    
    async def get_communication_statistics(self) -> Dict[str, Any]:
        """Get comprehensive communication statistics."""
        delivery_stats = await self.delivery_service.get_statistics()
        
        circuit_breaker_stats = {}
        for agent_id, breaker in self.circuit_breakers.items():
            circuit_breaker_stats[agent_id] = {
                "state": breaker.state,
                "failure_count": breaker.failure_count,
                "last_failure": breaker.last_failure_time
            }
        
        return {
            "communication": self.communication_stats,
            "delivery_service": delivery_stats,
            "circuit_breakers": circuit_breaker_stats,
            "known_agents": list(self.known_agents),
            "active_conversations": len(self.conversation_contexts),
            "agent_health": self.agent_health
        }
    
    async def get_message_flow_report(self) -> Dict[str, Any]:
        """Generate message flow report for monitoring."""
        return {
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": await self.get_communication_statistics(),
            "dead_letter_messages": await self.delivery_service.get_dead_letter_messages(50),
            "recent_conversations": [
                {
                    "conversation_id": conv_id,
                    "participants": context["participants"],
                    "type": context["conversation_type"],
                    "message_count": context["message_count"],
                    "duration": (datetime.utcnow() - context["started_at"]).total_seconds()
                }
                for conv_id, context in list(self.conversation_contexts.items())[-10:]
            ]
        }


# Middleware functions
async def logging_middleware(message: AgentMessage) -> AgentMessage:
    """Middleware to log all messages."""
    logger = get_logger("message_middleware")
    logger.info("Message processed by logging middleware",
               message_id=message.message_id,
               message_type=message.message_type,
               sender=message.sender_agent,
               recipient=message.recipient_agent)
    return message


async def validation_middleware(message: AgentMessage) -> AgentMessage:
    """Middleware to validate message format."""
    if not message.sender_agent or not message.recipient_agent:
        raise ValueError("Message must have sender and recipient")
    
    if not message.message_type:
        raise ValueError("Message must have message type")
    
    if not isinstance(message.payload, dict):
        raise ValueError("Message payload must be a dictionary")
    
    return message


async def security_middleware(message: AgentMessage) -> AgentMessage:
    """Middleware to apply security checks."""
    # Add security validation logic here
    # For example: check sender authorization, validate payload content, etc.
    
    # Placeholder security check
    if "malicious" in str(message.payload).lower():
        raise ValueError("Message contains potentially malicious content")
    
    return message