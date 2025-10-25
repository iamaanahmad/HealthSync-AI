"""
Basic tests for error handling functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from .error_middleware import GlobalErrorHandler, ErrorSeverity
from .error_handling import CircuitBreaker, RetryHandler
from .enhanced_logging import get_enhanced_logger


class TestBasicErrorHandling:
    """Test basic error handling functionality."""
    
    @pytest.mark.asyncio
    async def test_global_error_handler_basic(self):
        """Test basic global error handler functionality."""
        error_handler = GlobalErrorHandler()
        
        # Test error handling
        error = ValueError("Test error")
        context = {"operation": "test"}
        
        error_event = await error_handler.handle_error("test_agent", error, context)
        
        assert error_event.agent_name == "test_agent"
        assert error_event.error_type == "ValueError"
        assert error_event.error_message == "Test error"
        assert error_event.severity == ErrorSeverity.LOW
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_basic(self):
        """Test basic circuit breaker functionality."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        @breaker
        def failing_function():
            raise ValueError("Test error")
        
        # First failure
        with pytest.raises(ValueError):
            await failing_function()
        
        # Second failure should open circuit
        with pytest.raises(ValueError):
            await failing_function()
        
        assert breaker.state == "OPEN"
    
    @pytest.mark.asyncio
    async def test_retry_handler_basic(self):
        """Test basic retry handler functionality."""
        retry_handler = RetryHandler(max_attempts=2, base_delay=0.01)
        
        call_count = 0
        
        @retry_handler
        async def eventually_succeeding_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First failure")
            return "success"
        
        result = await eventually_succeeding_function()
        assert result == "success"
        assert call_count == 2
    
    def test_enhanced_logger_basic(self):
        """Test basic enhanced logger functionality."""
        logger = get_enhanced_logger("test_logger")
        
        # Test basic logging
        logger.info("Test message", test_param="value")
        logger.error("Test error", error_code="E001")
        
        # Test audit logging
        logger.audit("test_action", success=True, details={"key": "value"})
        
        # Verify audit trail
        audit_trail = logger.get_audit_trail()
        assert len(audit_trail) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])