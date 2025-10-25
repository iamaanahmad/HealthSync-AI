"""
Integration tests for comprehensive error handling and recovery mechanisms.
Tests error scenarios, compensation transactions, and recovery strategies.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import uuid

from .error_middleware import (
    GlobalErrorHandler, TransactionManager, ErrorNotificationSystem,
    ErrorSeverity, TransactionStatus, ErrorEvent, CompensationAction,
    global_error_handler, with_global_error_handling, with_transaction_support
)
from .error_handling import (
    CircuitBreaker, RetryHandler, ErrorRecoveryManager,
    CircuitBreakerError, RetryExhaustedError
)
from .enhanced_logging import (
    EnhancedStructuredLogger, AuditEventType, get_enhanced_logger,
    log_performance
)


class TestCircuitBreakerIntegration:
    """Test circuit breaker functionality in error scenarios."""
    
    @pytest.fixture
    def circuit_breaker(self):
        return CircuitBreaker(failure_threshold=3, recovery_timeout=1)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, circuit_breaker):
        """Test that circuit breaker opens after threshold failures."""
        
        @circuit_breaker
        async def failing_function():
            raise ValueError("Test error")
        
        # First 3 calls should fail normally
        for i in range(3):
            with pytest.raises(ValueError):
                await failing_function()
        
        # 4th call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await failing_function()
        
        assert circuit_breaker.state == "OPEN"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker recovery after timeout."""
        
        call_count = 0
        
        @circuit_breaker
        async def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise ValueError("Test error")
            return "success"
        
        # Trigger circuit breaker opening
        for i in range(3):
            with pytest.raises(ValueError):
                await sometimes_failing_function()
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Should succeed after recovery
        result = await sometimes_failing_function()
        assert result == "success"
        assert circuit_breaker.state == "CLOSED"


class TestRetryHandlerIntegration:
    """Test retry handler functionality."""
    
    @pytest.fixture
    def retry_handler(self):
        return RetryHandler(max_attempts=3, base_delay=0.1)
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self, retry_handler):
        """Test successful retry after initial failures."""
        
        call_count = 0
        
        @retry_handler
        async def eventually_succeeding_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = await eventually_succeeding_function()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, retry_handler):
        """Test retry exhaustion after max attempts."""
        
        @retry_handler
        async def always_failing_function():
            raise ValueError("Persistent error")
        
        with pytest.raises(RetryExhaustedError):
            await always_failing_function()


class TestTransactionManagerIntegration:
    """Test transaction manager and compensation functionality."""
    
    @pytest.fixture
    def transaction_manager(self):
        return TransactionManager()
    
    def test_transaction_lifecycle(self, transaction_manager):
        """Test complete transaction lifecycle."""
        tx_id = str(uuid.uuid4())
        
        # Start transaction
        transaction_manager.start_transaction(tx_id, "Test transaction")
        
        # Add participants and steps
        transaction_manager.add_participant(tx_id, "agent1")
        transaction_manager.add_participant(tx_id, "agent2")
        
        transaction_manager.add_step(tx_id, "step1", "agent1", {"data": "test"})
        transaction_manager.add_step(tx_id, "step2", "agent2", {"data": "test2"})
        
        # Register compensation actions
        transaction_manager.register_compensation(
            tx_id, "agent1", "rollback_step1", {"original_data": "test"}
        )
        transaction_manager.register_compensation(
            tx_id, "agent2", "rollback_step2", {"original_data": "test2"}
        )
        
        # Check transaction status
        status = transaction_manager.get_transaction_status(tx_id)
        assert status["status"] == TransactionStatus.PENDING
        assert len(status["participants"]) == 2
        assert len(status["steps"]) == 2
    
    @pytest.mark.asyncio
    async def test_transaction_compensation(self, transaction_manager):
        """Test transaction compensation execution."""
        tx_id = str(uuid.uuid4())
        
        # Start transaction and register compensation
        transaction_manager.start_transaction(tx_id, "Test compensation")
        transaction_manager.register_compensation(
            tx_id, "agent1", "rollback", {"data": "test"}
        )
        
        # Execute compensation
        success = await transaction_manager.compensate_transaction(tx_id)
        assert success
        
        # Check compensation actions were executed
        actions = transaction_manager.compensation_actions[tx_id]
        assert len(actions) == 1
        assert actions[0].executed


class TestGlobalErrorHandlerIntegration:
    """Test global error handler integration."""
    
    @pytest.fixture
    def error_handler(self):
        return GlobalErrorHandler()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, error_handler):
        """Test complete error handling workflow."""
        
        # Mock recovery manager
        recovery_manager = Mock()
        recovery_manager.handle_error = AsyncMock(return_value=True)
        error_handler.recovery_managers["test_agent"] = recovery_manager
        
        # Handle error
        error = ValueError("Test error")
        context = {"operation": "test_operation", "user_id": "user123"}
        
        error_event = await error_handler.handle_error("test_agent", error, context)
        
        # Verify error event
        assert error_event.agent_name == "test_agent"
        assert error_event.error_type == "ValueError"
        assert error_event.severity == ErrorSeverity.LOW
        assert error_event.recovery_attempted
        assert error_event.recovery_successful
        
        # Verify recovery was called
        recovery_manager.handle_error.assert_called_once_with(error, context)
    
    def test_error_severity_determination(self, error_handler):
        """Test error severity determination logic."""
        
        # Test critical error
        critical_error = Exception("SecurityError")
        critical_error.__class__.__name__ = "SecurityError"
        severity = error_handler.determine_severity(critical_error, {})
        assert severity == ErrorSeverity.CRITICAL
        
        # Test high severity error
        high_error = Exception("ConsentViolationError")
        high_error.__class__.__name__ = "ConsentViolationError"
        severity = error_handler.determine_severity(high_error, {})
        assert severity == ErrorSeverity.HIGH
        
        # Test medium severity error
        medium_error = Exception("ValidationError")
        medium_error.__class__.__name__ = "ValidationError"
        severity = error_handler.determine_severity(medium_error, {})
        assert severity == ErrorSeverity.MEDIUM
        
        # Test low severity error
        low_error = Exception("UnknownError")
        severity = error_handler.determine_severity(low_error, {})
        assert severity == ErrorSeverity.LOW
    
    def test_error_rate_tracking(self, error_handler):
        """Test error rate tracking functionality."""
        agent_name = "test_agent"
        
        # Simulate multiple errors
        for _ in range(5):
            error_handler._update_error_rates(agent_name)
            time.sleep(0.1)
        
        error_rate = error_handler.get_error_rate(agent_name)
        assert error_rate > 0
        
        # Test system health
        health = error_handler.get_system_health()
        assert "agent_error_rates" in health
        assert agent_name in health["agent_error_rates"]


class TestErrorNotificationSystem:
    """Test error notification system."""
    
    @pytest.fixture
    def notification_system(self):
        return ErrorNotificationSystem()
    
    @pytest.mark.asyncio
    async def test_notification_subscription_and_delivery(self, notification_system):
        """Test notification subscription and delivery."""
        
        # Mock callback
        callback = AsyncMock()
        notification_system.subscribe(ErrorSeverity.HIGH, callback)
        
        # Create error event
        error_event = ErrorEvent(
            error_id=str(uuid.uuid4()),
            agent_name="test_agent",
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.utcnow().isoformat(),
            context={"test": "data"}
        )
        
        # Send notification
        await notification_system.notify(error_event)
        
        # Verify callback was called
        callback.assert_called_once_with(error_event)
        
        # Verify notification history
        assert len(notification_system.notification_history) == 1
        notification = notification_system.notification_history[0]
        assert notification["recipients"] == 1


class TestEnhancedLoggingIntegration:
    """Test enhanced logging integration with error handling."""
    
    @pytest.fixture
    def logger(self):
        return get_enhanced_logger("test_logger")
    
    def test_audit_logging(self, logger):
        """Test comprehensive audit logging."""
        
        # Test different types of audit events
        logger.log_data_access("user123", "dataset456", "read", success=True)
        logger.log_consent_change("patient789", "research_data", True)
        logger.log_privacy_operation("anonymize", "dataset456", success=True, duration_ms=150.5)
        logger.log_error_recovery("ValidationError", "retry", success=True, duration_ms=50.2)
        logger.log_transaction("tx123", "commit", success=True)
        logger.log_communication("consent_request", "agent1", "agent2", success=True)
        logger.log_security_event("unauthorized_access", "medium")
        
        # Verify audit events were logged
        audit_trail = logger.get_audit_trail()
        assert len(audit_trail) == 7
        
        # Test filtering
        data_access_events = logger.get_audit_trail(event_type=AuditEventType.DATA_ACCESS)
        assert len(data_access_events) == 1
        assert data_access_events[0].user_id == "user123"
    
    def test_error_analysis(self, logger):
        """Test error analysis functionality."""
        
        # Log some errors
        logger.audit("failed_operation", success=False, error_message="Test error 1")
        logger.audit("another_failure", success=False, error_message="Test error 2")
        logger.audit("successful_operation", success=True)
        
        # Get error analysis
        analysis = logger.get_error_analysis()
        assert analysis["total_errors"] == 2
        assert analysis["error_rate"] == 2/3
        assert "errors_by_action" in analysis
    
    def test_performance_analysis(self, logger):
        """Test performance analysis functionality."""
        
        # Log performance events
        logger.log_performance("operation1", 100.5)
        logger.log_performance("operation2", 200.3)
        logger.log_performance("operation1", 150.7)
        
        # Get performance analysis
        analysis = logger.get_performance_analysis()
        assert analysis["total_performance_events"] == 3
        assert analysis["average_duration_ms"] > 0
        assert "agent_average_performance" in analysis


class TestDecoratorIntegration:
    """Test error handling decorators integration."""
    
    @pytest.mark.asyncio
    async def test_global_error_handling_decorator(self):
        """Test global error handling decorator."""
        
        @with_global_error_handling("test_agent")
        async def test_function():
            raise ValueError("Test error")
        
        # Mock the global error handler
        with patch('shared.utils.error_middleware.global_error_handler') as mock_handler:
            mock_handler.handle_error = AsyncMock()
            
            with pytest.raises(ValueError):
                await test_function()
            
            # Verify error was handled
            mock_handler.handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_support_decorator(self):
        """Test transaction support decorator."""
        
        @with_transaction_support()
        async def test_function(**kwargs):
            return kwargs.get('context', {}).get('transaction_id')
        
        result = await test_function()
        assert result is not None  # Should have transaction_id
    
    @pytest.mark.asyncio
    async def test_performance_logging_decorator(self):
        """Test performance logging decorator."""
        logger = get_enhanced_logger("test_perf_logger")
        
        @log_performance(logger, "test_operation")
        async def test_function():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await test_function()
        assert result == "success"
        
        # Check performance was logged
        analysis = logger.get_performance_analysis()
        assert analysis["total_performance_events"] == 1


class TestEndToEndErrorScenarios:
    """Test end-to-end error scenarios and recovery."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow_failure_and_recovery(self):
        """Test complete multi-agent workflow failure and recovery."""
        
        # Simulate multi-agent workflow with failure
        error_handler = GlobalErrorHandler()
        transaction_manager = error_handler.transaction_manager
        
        # Start transaction
        tx_id = str(uuid.uuid4())
        transaction_manager.start_transaction(tx_id, "Multi-agent workflow")
        
        # Add participants
        agents = ["consent_agent", "data_custodian", "privacy_agent"]
        for agent in agents:
            transaction_manager.add_participant(tx_id, agent)
        
        # Simulate successful steps
        transaction_manager.add_step(tx_id, "validate_consent", "consent_agent", {"result": "approved"})
        transaction_manager.add_step(tx_id, "fetch_data", "data_custodian", {"records": 100})
        
        # Register compensation actions
        transaction_manager.register_compensation(
            tx_id, "consent_agent", "revert_consent", {"consent_id": "123"}
        )
        transaction_manager.register_compensation(
            tx_id, "data_custodian", "release_lock", {"dataset_id": "456"}
        )
        
        # Simulate failure in privacy agent
        error = Exception("Anonymization failed")
        context = {"transaction_id": tx_id, "operation": "anonymize_data"}
        
        error_event = await error_handler.handle_error("privacy_agent", error, context)
        
        # Verify error was handled and compensation was triggered
        assert error_event.agent_name == "privacy_agent"
        
        # Check transaction was compensated
        tx_status = transaction_manager.get_transaction_status(tx_id)
        assert tx_status["status"] == TransactionStatus.COMPENSATED
    
    @pytest.mark.asyncio
    async def test_cascading_failure_scenario(self):
        """Test cascading failure scenario across multiple agents."""
        
        error_handler = GlobalErrorHandler()
        
        # Simulate cascading failures
        agents = ["agent1", "agent2", "agent3"]
        errors = [
            ValueError("Primary failure"),
            ConnectionError("Secondary failure"),
            TimeoutError("Tertiary failure")
        ]
        
        error_events = []
        for agent, error in zip(agents, errors):
            context = {"cascade_level": len(error_events) + 1}
            error_event = await error_handler.handle_error(agent, error, context)
            error_events.append(error_event)
        
        # Verify all errors were handled
        assert len(error_events) == 3
        
        # Check system health degradation
        health = error_handler.get_system_health()
        assert health["system_status"] == "degraded"  # Should be degraded due to multiple recent errors


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])