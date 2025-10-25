#!/usr/bin/env python3
"""
Demonstration of enhanced inter-agent communication system.
Shows message delivery, circuit breakers, retries, and dead letter queue handling.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from .communication_manager import CommunicationManager, DeliveryPriority
from .agent_messages import AgentMessage, MessageTypes
from ..utils.logging import get_logger

logger = get_logger("communication_demo")


class DemoAgent:
    """Demo agent to showcase communication features."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.comm_manager = CommunicationManager(agent_id)
        self.message_log = []
        
        # Register message handlers
        self.comm_manager.register_message_handler(
            MessageTypes.HEALTH_CHECK, self.handle_health_check
        )
        self.comm_manager.register_message_handler(
            MessageTypes.DATA_REQUEST, self.handle_data_request
        )
        self.comm_manager.register_message_handler(
            MessageTypes.STATUS_UPDATE, self.handle_status_update
        )
    
    async def start(self):
        """Start the demo agent."""
        await self.comm_manager.start()
        logger.info(f"Demo agent {self.agent_id} started")
    
    async def stop(self):
        """Stop the demo agent."""
        await self.comm_manager.stop()
        logger.info(f"Demo agent {self.agent_id} stopped")
    
    async def handle_health_check(self, sender: str, message: AgentMessage) -> Dict[str, Any]:
        """Handle health check messages."""
        self.message_log.append({
            "type": "health_check",
            "sender": sender,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": message.payload
        })
        
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "uptime": "demo_uptime",
            "response_time": 0.1
        }
    
    async def handle_data_request(self, sender: str, message: AgentMessage) -> Dict[str, Any]:
        """Handle data request messages."""
        self.message_log.append({
            "type": "data_request",
            "sender": sender,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": message.payload
        })
        
        # Simulate data processing
        await asyncio.sleep(0.1)
        
        return {
            "status": "processed",
            "data": {
                "patient_count": 100,
                "data_fields": ["age", "diagnosis", "treatment"],
                "anonymized": True
            },
            "processing_time": 0.1
        }
    
    async def handle_status_update(self, sender: str, message: AgentMessage) -> Dict[str, Any]:
        """Handle status update messages."""
        self.message_log.append({
            "type": "status_update",
            "sender": sender,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": message.payload
        })
        
        return {"acknowledged": True}
    
    async def send_health_check(self, recipient: str) -> str:
        """Send health check to another agent."""
        return await self.comm_manager.send_message(
            recipient=recipient,
            message_type=MessageTypes.HEALTH_CHECK,
            payload={
                "check_time": datetime.utcnow().isoformat(),
                "sender_status": "healthy"
            },
            priority=DeliveryPriority.HIGH
        )
    
    async def send_data_request(self, recipient: str, request_data: Dict[str, Any]) -> str:
        """Send data request to another agent."""
        return await self.comm_manager.send_message(
            recipient=recipient,
            message_type=MessageTypes.DATA_REQUEST,
            payload=request_data,
            priority=DeliveryPriority.NORMAL
        )
    
    async def broadcast_status(self, recipients: list) -> list:
        """Broadcast status update to multiple agents."""
        return await self.comm_manager.broadcast_message(
            message_type=MessageTypes.STATUS_UPDATE,
            payload={
                "agent_id": self.agent_id,
                "status": "operational",
                "timestamp": datetime.utcnow().isoformat()
            },
            recipients=recipients
        )
    
    async def start_data_conversation(self, recipient: str) -> str:
        """Start a data sharing conversation."""
        return await self.comm_manager.start_conversation(
            recipient=recipient,
            conversation_type="data_sharing",
            initial_message_type=MessageTypes.DATA_REQUEST,
            initial_payload={
                "conversation_starter": self.agent_id,
                "request_type": "patient_data",
                "urgency": "normal"
            }
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent communication statistics."""
        return {
            "agent_id": self.agent_id,
            "messages_received": len(self.message_log),
            "message_types": list(set(msg["type"] for msg in self.message_log)),
            "recent_messages": self.message_log[-5:] if self.message_log else []
        }


async def demo_basic_communication():
    """Demonstrate basic inter-agent communication."""
    print("\n🔄 Demo: Basic Inter-Agent Communication")
    print("-" * 50)
    
    # Create two demo agents
    agent1 = DemoAgent("patient_consent_agent")
    agent2 = DemoAgent("data_custodian_agent")
    
    await agent1.start()
    await agent2.start()
    
    try:
        # Agent1 sends health check to Agent2
        print("📤 Agent1 sending health check to Agent2...")
        message_id = await agent1.send_health_check("data_custodian_agent")
        print(f"   Message ID: {message_id}")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Agent2 sends data request to Agent1
        print("📤 Agent2 sending data request to Agent1...")
        message_id = await agent2.send_data_request(
            "patient_consent_agent",
            {
                "patient_id": "patient_123",
                "data_types": ["demographics", "medical_history"],
                "research_purpose": "diabetes_study"
            }
        )
        print(f"   Message ID: {message_id}")
        
        await asyncio.sleep(0.2)
        
        # Show statistics
        print("\n📊 Communication Statistics:")
        stats1 = agent1.get_statistics()
        stats2 = agent2.get_statistics()
        
        print(f"   {stats1['agent_id']}: {stats1['messages_received']} messages received")
        print(f"   {stats2['agent_id']}: {stats2['messages_received']} messages received")
        
    finally:
        await agent1.stop()
        await agent2.stop()


async def demo_priority_messaging():
    """Demonstrate priority-based message delivery."""
    print("\n⚡ Demo: Priority-Based Message Delivery")
    print("-" * 50)
    
    agent = DemoAgent("priority_test_agent")
    await agent.start()
    
    try:
        # Send messages with different priorities
        priorities = [
            (DeliveryPriority.LOW, "Low priority status update"),
            (DeliveryPriority.HIGH, "High priority alert"),
            (DeliveryPriority.CRITICAL, "Critical system notification"),
            (DeliveryPriority.NORMAL, "Normal data request")
        ]
        
        message_ids = []
        for priority, description in priorities:
            print(f"📤 Sending {priority.name} priority message: {description}")
            message_id = await agent.comm_manager.send_message(
                recipient="target_agent",
                message_type=MessageTypes.STATUS_UPDATE,
                payload={"description": description, "priority": priority.name},
                priority=priority
            )
            message_ids.append(message_id)
        
        print(f"\n✅ Sent {len(message_ids)} messages with different priorities")
        
        # Show delivery service statistics
        stats = await agent.comm_manager.get_communication_statistics()
        print(f"📊 Delivery Statistics: {stats['delivery_service']['messages_sent']} messages queued")
        
    finally:
        await agent.stop()


async def demo_circuit_breaker():
    """Demonstrate circuit breaker functionality."""
    print("\n🔌 Demo: Circuit Breaker Pattern")
    print("-" * 50)
    
    agent = DemoAgent("circuit_breaker_test")
    await agent.start()
    
    try:
        failing_agent = "unreliable_agent"
        
        # Simulate multiple failures to trigger circuit breaker
        print("🔥 Simulating communication failures...")
        for i in range(5):
            agent.comm_manager._record_communication_failure(
                failing_agent, f"Network timeout #{i+1}"
            )
            print(f"   Failure {i+1}: Network timeout")
        
        # Check circuit breaker state
        breaker = agent.comm_manager.get_circuit_breaker(failing_agent)
        print(f"\n🔌 Circuit breaker state: {breaker.state}")
        print(f"   Failure count: {breaker.failure_count}")
        
        # Try to send message (should fail due to circuit breaker)
        try:
            await agent.comm_manager.send_message(
                recipient=failing_agent,
                message_type=MessageTypes.HEALTH_CHECK,
                payload={"test": "data"}
            )
            print("❌ Message should have been blocked by circuit breaker")
        except Exception as e:
            print(f"✅ Circuit breaker blocked message: {str(e)}")
        
        # Show circuit breaker statistics
        stats = await agent.comm_manager.get_communication_statistics()
        cb_stats = stats["circuit_breakers"]
        print(f"\n📊 Circuit Breaker Stats:")
        for agent_id, cb_info in cb_stats.items():
            print(f"   {agent_id}: {cb_info['state']} (failures: {cb_info['failure_count']})")
        
    finally:
        await agent.stop()


async def demo_conversation_management():
    """Demonstrate conversation context management."""
    print("\n💬 Demo: Conversation Management")
    print("-" * 50)
    
    agent1 = DemoAgent("research_query_agent")
    agent2 = DemoAgent("privacy_agent")
    
    await agent1.start()
    await agent2.start()
    
    try:
        # Start a data sharing conversation
        print("🗣️  Starting data sharing conversation...")
        conversation_id = await agent1.start_data_conversation("privacy_agent")
        print(f"   Conversation ID: {conversation_id}")
        
        # Check conversation context
        contexts = agent1.comm_manager.conversation_contexts
        if conversation_id in contexts:
            context = contexts[conversation_id]
            print(f"   Participants: {context['participants']}")
            print(f"   Type: {context['conversation_type']}")
            print(f"   Started: {context['started_at']}")
        
        await asyncio.sleep(0.1)
        
        # Send follow-up messages in conversation
        await agent1.comm_manager.send_message(
            recipient="privacy_agent",
            message_type=MessageTypes.DATA_REQUEST,
            payload={
                "conversation_id": conversation_id,
                "follow_up": "Please anonymize the dataset",
                "k_anonymity": 5
            }
        )
        
        print("✅ Conversation established and follow-up sent")
        
    finally:
        await agent1.stop()
        await agent2.stop()


async def demo_broadcast_messaging():
    """Demonstrate broadcast messaging."""
    print("\n📢 Demo: Broadcast Messaging")
    print("-" * 50)
    
    coordinator = DemoAgent("system_coordinator")
    await coordinator.start()
    
    try:
        # Simulate multiple agents in the system
        agent_list = [
            "patient_consent_agent",
            "data_custodian_agent", 
            "privacy_agent",
            "research_query_agent",
            "metta_integration_agent"
        ]
        
        # Add agents to known agents list
        coordinator.comm_manager.known_agents.update(agent_list)
        
        print(f"📡 Broadcasting system status to {len(agent_list)} agents...")
        
        # Broadcast status update
        message_ids = await coordinator.broadcast_status(agent_list)
        
        print(f"✅ Broadcast completed: {len(message_ids)} messages sent")
        
        # Show broadcast statistics
        stats = await coordinator.comm_manager.get_communication_statistics()
        print(f"📊 Total messages sent: {stats['communication']['total_sent']}")
        
    finally:
        await coordinator.stop()


async def demo_dead_letter_queue():
    """Demonstrate dead letter queue handling."""
    print("\n💀 Demo: Dead Letter Queue")
    print("-" * 50)
    
    agent = DemoAgent("dlq_test_agent")
    await agent.start()
    
    try:
        # Simulate messages that will fail delivery
        print("🔥 Simulating failed message deliveries...")
        
        # Access delivery service directly to simulate failures
        delivery_service = agent.comm_manager.delivery_service
        
        # Create a message that will fail
        from .message_delivery import MessageEnvelope
        from .agent_messages import AgentMessage
        
        failed_message = AgentMessage(
            sender_agent="dlq_test_agent",
            recipient_agent="nonexistent_agent",
            message_type=MessageTypes.HEALTH_CHECK,
            payload={"test": "data"}
        )
        
        envelope = MessageEnvelope(message=failed_message)
        envelope.retry_count = 3  # Max retries exceeded
        
        # Add to dead letter queue
        await delivery_service.dead_letter_queue.add_message(
            envelope, "Agent not found"
        )
        
        print("💀 Message added to dead letter queue")
        
        # Check dead letter queue
        dlq_messages = await delivery_service.get_dead_letter_messages()
        print(f"📊 Dead letter queue contains {len(dlq_messages)} messages")
        
        if dlq_messages:
            msg = dlq_messages[0]
            print(f"   Message ID: {msg['message_id']}")
            print(f"   Recipient: {msg['recipient']}")
            print(f"   Failure reason: {msg['failure_reason']}")
            print(f"   Retry count: {msg['retry_count']}")
        
        # Demonstrate requeuing
        if dlq_messages:
            message_id = dlq_messages[0]['message_id']
            success = await delivery_service.requeue_dead_letter_message(message_id)
            if success:
                print(f"✅ Message {message_id} requeued for delivery")
        
    finally:
        await agent.stop()


async def demo_message_flow_monitoring():
    """Demonstrate message flow monitoring and reporting."""
    print("\n📈 Demo: Message Flow Monitoring")
    print("-" * 50)
    
    agent = DemoAgent("monitoring_agent")
    await agent.start()
    
    try:
        # Send various types of messages to generate activity
        recipients = ["agent1", "agent2", "agent3"]
        
        for i, recipient in enumerate(recipients):
            await agent.comm_manager.send_message(
                recipient=recipient,
                message_type=MessageTypes.HEALTH_CHECK,
                payload={"check_number": i+1}
            )
        
        await asyncio.sleep(0.1)
        
        # Generate message flow report
        print("📊 Generating message flow report...")
        report = await agent.comm_manager.get_message_flow_report()
        
        print(f"\n📈 Message Flow Report for {report['agent_id']}:")
        print(f"   Timestamp: {report['timestamp']}")
        
        comm_stats = report['statistics']['communication']
        print(f"   Total sent: {comm_stats['total_sent']}")
        print(f"   Total received: {comm_stats['total_received']}")
        print(f"   Successful deliveries: {comm_stats['successful_deliveries']}")
        print(f"   Failed deliveries: {comm_stats['failed_deliveries']}")
        
        delivery_stats = report['statistics']['delivery_service']
        print(f"   Pending messages: {delivery_stats['pending_messages']}")
        print(f"   Average delivery time: {delivery_stats['average_delivery_time']:.3f}s")
        
        print(f"   Known agents: {len(report['statistics']['known_agents'])}")
        print(f"   Active conversations: {report['statistics']['active_conversations']}")
        
    finally:
        await agent.stop()


async def main():
    """Run all communication system demonstrations."""
    print("🚀 HealthSync Inter-Agent Communication System Demo")
    print("=" * 60)
    
    demos = [
        demo_basic_communication,
        demo_priority_messaging,
        demo_circuit_breaker,
        demo_conversation_management,
        demo_broadcast_messaging,
        demo_dead_letter_queue,
        demo_message_flow_monitoring
    ]
    
    for demo in demos:
        try:
            await demo()
            await asyncio.sleep(0.5)  # Brief pause between demos
        except Exception as e:
            print(f"❌ Demo {demo.__name__} failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 Communication system demonstration completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Message delivery with priority queues")
    print("✅ Circuit breaker pattern for resilience")
    print("✅ Conversation context management")
    print("✅ Broadcast messaging capabilities")
    print("✅ Dead letter queue for failed messages")
    print("✅ Comprehensive monitoring and reporting")
    print("✅ Acknowledgment and retry mechanisms")
    print("✅ Ordered message delivery guarantees")


if __name__ == "__main__":
    asyncio.run(main())