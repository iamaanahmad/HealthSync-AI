"""
Demonstration of comprehensive error handling and recovery system.
Shows how all components work together in realistic scenarios.
"""

import asyncio
import random
from datetime import datetime
from typing import Dict, Any

from .error_middleware import (
    global_error_handler, GlobalErrorHandler, ErrorSeverity, 
    with_global_error_handling, with_transaction_support
)
from .error_handling import with_circuit_breaker, with_retry
from .enhanced_logging import get_enhanced_logger, AuditEventType, log_performance
from .agent_error_recovery import global_recovery_orchestrator, register_agent_recovery_strategies
from .error_monitoring import global_error_monitor, SystemMetrics, AlertType


class MockHealthSyncAgent:
    """Mock HealthSync agent for demonstration."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_enhanced_logger(agent_name)
        self.failure_rate = 0.1  # 10% failure rate
        self.is_healthy = True
    
    @with_global_error_handling("mock_agent")
    @with_transaction_support()
    @with_circuit_breaker(failure_threshold=3, recovery_timeout=5)
    @with_retry(max_attempts=2, base_delay=0.5)
    @log_performance(get_enhanced_logger("mock_agent"), "process_request")
    async def process_request(self, request_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process a request with comprehensive error handling."""
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Simulate random failures
        if random.random() < self.failure_rate:
            error_types = [
                ValueError("Validation failed"),
                ConnectionError("Network timeout"),
                PermissionError("Access denied"),
                RuntimeError("Processing error")
            ]
            raise random.choice(error_types)
        
        # Log successful processing
        self.logger.audit(
            "request_processed",
            event_type=AuditEventType.AGENT_ACTION,
            success=True,
            details=request_data
        )
        
        return {
            "status": "success",
            "agent": self.agent_name,
            "processed_at": datetime.utcnow().isoformat(),
            "data": request_data
        }
    
    async def simulate_data_access(self, user_id: str, resource_id: str) -> Dict[str, Any]:
        """Simulate data access with audit logging."""
        
        # Log data access attempt
        self.logger.log_data_access(
            user_id=user_id,
            resource_id=resource_id,
            action="read_data",
            success=True
        )
        
        return {"data": f"mock_data_for_{resource_id}"}
    
    async def simulate_consent_change(self, patient_id: str, consent_type: str, new_value: bool):
        """Simulate consent change with audit logging."""
        
        self.logger.log_consent_change(
            patient_id=patient_id,
            consent_type=consent_type,
            new_value=new_value
        )
    
    def set_failure_rate(self, rate: float):
        """Set failure rate for testing."""
        self.failure_rate = rate
        self.logger.info("Failure rate updated", new_rate=rate)


class ErrorHandlingDemo:
    """Demonstrates comprehensive error handling system."""
    
    def __init__(self):
        self.logger = get_enhanced_logger("error_demo")
        self.agents = {
            "patient_consent": MockHealthSyncAgent("patient_consent"),
            "data_custodian": MockHealthSyncAgent("data_custodian"),
            "privacy": MockHealthSyncAgent("privacy"),
            "research_query": MockHealthSyncAgent("research_query"),
            "metta_integration": MockHealthSyncAgent("metta_integration")
        }
        
        # Register recovery strategies
        register_agent_recovery_strategies()
    
    async def demonstrate_normal_operation(self):
        """Demonstrate normal system operation."""
        print("🟢 Demonstrating Normal Operation")
        print("=" * 50)
        
        # Process some normal requests
        for i in range(5):
            agent_name = random.choice(list(self.agents.keys()))
            agent = self.agents[agent_name]
            
            try:
                result = await agent.process_request({
                    "request_id": f"req_{i}",
                    "type": "normal_operation",
                    "data": f"test_data_{i}"
                })
                print(f"✅ {agent_name}: {result['status']}")
            except Exception as e:
                print(f"❌ {agent_name}: {type(e).__name__}: {e}")
        
        print()
    
    async def demonstrate_error_scenarios(self):
        """Demonstrate various error scenarios and recovery."""
        print("🔴 Demonstrating Error Scenarios")
        print("=" * 50)
        
        # Increase failure rates to trigger errors
        for agent in self.agents.values():
            agent.set_failure_rate(0.7)  # 70% failure rate
        
        # Process requests that will likely fail
        for i in range(10):
            agent_name = random.choice(list(self.agents.keys()))
            agent = self.agents[agent_name]
            
            try:
                result = await agent.process_request({
                    "request_id": f"error_req_{i}",
                    "type": "error_scenario",
                    "data": f"error_test_data_{i}"
                })
                print(f"✅ {agent_name}: {result['status']}")
            except Exception as e:
                print(f"❌ {agent_name}: {type(e).__name__}: {e}")
        
        # Reset failure rates
        for agent in self.agents.values():
            agent.set_failure_rate(0.1)
        
        print()
    
    async def demonstrate_transaction_compensation(self):
        """Demonstrate transaction compensation."""
        print("🔄 Demonstrating Transaction Compensation")
        print("=" * 50)
        
        transaction_manager = global_error_handler.transaction_manager
        
        # Start a multi-agent transaction
        tx_id = "demo_transaction_001"
        transaction_manager.start_transaction(tx_id, "Multi-agent workflow demo")
        
        # Add participants
        for agent_name in self.agents.keys():
            transaction_manager.add_participant(tx_id, agent_name)
        
        # Simulate workflow steps
        try:
            # Step 1: Consent validation
            transaction_manager.add_step(tx_id, "validate_consent", "patient_consent", {"result": "approved"})
            transaction_manager.register_compensation(tx_id, "patient_consent", "revert_consent", {"consent_id": "123"})
            print("✅ Step 1: Consent validated")
            
            # Step 2: Data retrieval
            transaction_manager.add_step(tx_id, "retrieve_data", "data_custodian", {"records": 100})
            transaction_manager.register_compensation(tx_id, "data_custodian", "release_lock", {"dataset_id": "456"})
            print("✅ Step 2: Data retrieved")
            
            # Step 3: Privacy processing (simulate failure)
            print("❌ Step 3: Privacy processing failed - triggering compensation")
            await transaction_manager.compensate_transaction(tx_id)
            print("🔄 Transaction compensated successfully")
            
        except Exception as e:
            print(f"❌ Transaction failed: {e}")
        
        print()
    
    async def demonstrate_monitoring_and_alerting(self):
        """Demonstrate monitoring and alerting system."""
        print("📊 Demonstrating Monitoring and Alerting")
        print("=" * 50)
        
        # Start monitoring
        await global_error_monitor.start_monitoring(interval_seconds=2)
        
        # Update agent statuses
        for agent_name in self.agents.keys():
            global_error_monitor.update_agent_status(agent_name, "active")
        
        # Record some system metrics
        metrics = SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            total_agents=len(self.agents),
            active_agents=len(self.agents),
            error_rate_per_minute=2.5,
            average_response_time_ms=150.0,
            failed_transactions=2,
            successful_transactions=8,
            memory_usage_mb=512.0,
            cpu_usage_percent=45.0
        )
        global_error_monitor.record_system_metrics(metrics)
        
        # Simulate some errors to trigger alerts
        for i in range(3):
            agent_name = f"agent_{i}"
            error = ValueError(f"Simulated error {i}")
            await global_error_handler.handle_error(agent_name, error, {"demo": True})
        
        # Wait for monitoring cycle
        await asyncio.sleep(3)
        
        # Get monitoring data
        dashboard_data = global_error_monitor.get_monitoring_dashboard_data()
        
        print(f"System Health Score: {dashboard_data['system_health_score']:.1f}/100")
        print(f"Active Alerts: {len(dashboard_data['active_alerts'])}")
        print(f"Alert Statistics: {dashboard_data['alert_statistics']}")
        
        # Stop monitoring
        await global_error_monitor.stop_monitoring()
        
        print()
    
    async def demonstrate_audit_trail(self):
        """Demonstrate comprehensive audit trail."""
        print("📋 Demonstrating Audit Trail")
        print("=" * 50)
        
        # Simulate various auditable events
        agent = self.agents["patient_consent"]
        
        # Data access events
        await agent.simulate_data_access("patient_123", "medical_record_456")
        await agent.simulate_data_access("researcher_789", "dataset_101")
        
        # Consent changes
        await agent.simulate_consent_change("patient_123", "research_data", True)
        await agent.simulate_consent_change("patient_456", "genetic_data", False)
        
        # Get audit trail
        audit_trail = agent.logger.get_audit_trail()
        
        print(f"Total audit events: {len(audit_trail)}")
        
        # Show recent events
        for event in audit_trail[-5:]:
            print(f"  {event.timestamp}: {event.action} ({event.event_type.value})")
        
        # Get audit summary
        summary = agent.logger.get_audit_summary()
        print(f"Audit Summary: {summary}")
        
        print()
    
    async def demonstrate_performance_monitoring(self):
        """Demonstrate performance monitoring."""
        print("⚡ Demonstrating Performance Monitoring")
        print("=" * 50)
        
        # Process requests with performance logging
        for i in range(10):
            agent = random.choice(list(self.agents.values()))
            await agent.process_request({
                "request_id": f"perf_req_{i}",
                "type": "performance_test"
            })
        
        # Get performance analysis
        for agent_name, agent in self.agents.items():
            analysis = agent.logger.get_performance_analysis()
            if analysis["total_performance_events"] > 0:
                print(f"{agent_name}:")
                print(f"  Average Duration: {analysis['average_duration_ms']:.1f}ms")
                print(f"  Max Duration: {analysis['max_duration_ms']:.1f}ms")
                print(f"  Total Events: {analysis['total_performance_events']}")
        
        print()
    
    async def run_full_demo(self):
        """Run the complete error handling demonstration."""
        print("🚀 HealthSync Error Handling & Recovery System Demo")
        print("=" * 60)
        print()
        
        try:
            await self.demonstrate_normal_operation()
            await self.demonstrate_error_scenarios()
            await self.demonstrate_transaction_compensation()
            await self.demonstrate_monitoring_and_alerting()
            await self.demonstrate_audit_trail()
            await self.demonstrate_performance_monitoring()
            
            # Final system health report
            health = global_error_handler.get_system_health()
            print("📈 Final System Health Report")
            print("=" * 50)
            print(f"Total Errors: {health['total_errors']}")
            print(f"Recent Errors (1h): {health['recent_errors_1h']}")
            print(f"System Status: {health['system_status']}")
            print(f"Active Transactions: {health['active_transactions']}")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run the error handling demonstration."""
    demo = ErrorHandlingDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())