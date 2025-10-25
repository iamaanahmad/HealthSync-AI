"""
Error handling utilities for HealthSync agents.
Provides circuit breakers, retry mechanisms, and error recovery.
"""

import asyncio
import time
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta
import random

from .logging import get_logger

logger = get_logger("error_handler")


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class RetryExhaustedError(Exception):
    """Exception raised when retry attempts are exhausted."""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation for agent resilience."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker to function."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN", 
                          function=func.__name__)
            else:
                logger.warning("Circuit breaker is OPEN, rejecting call",
                             function=func.__name__)
                raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            logger.error("Circuit breaker recorded failure",
                        function=func.__name__, error=str(e))
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful function execution."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker reset to CLOSED")
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed function execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("Circuit breaker opened due to failures",
                          failure_count=self.failure_count)


class RetryHandler:
    """Retry mechanism with exponential backoff."""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_factor: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply retry logic to function."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.retry(func, *args, **kwargs)
        return wrapper
    
    async def retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                if attempt > 0:
                    logger.info("Function succeeded after retry",
                              function=func.__name__, attempt=attempt + 1)
                return result
            except Exception as e:
                last_exception = e
                logger.warning("Function failed, will retry",
                             function=func.__name__, 
                             attempt=attempt + 1,
                             error=str(e))
                
                if attempt < self.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        logger.error("Function failed after all retry attempts",
                    function=func.__name__, 
                    max_attempts=self.max_attempts)
        raise RetryExhaustedError(f"Failed after {self.max_attempts} attempts") from last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            delay *= (0.5 + random.random() * 0.5)
        
        return delay


class ErrorRecoveryManager:
    """Manages error recovery strategies for agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_logger(f"{agent_name}_recovery")
        self.recovery_strategies: Dict[str, Callable] = {}
        self.error_history: List[Dict[str, Any]] = []
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register recovery strategy for specific error type."""
        self.recovery_strategies[error_type] = strategy
        self.logger.info("Recovery strategy registered",
                        error_type=error_type)
    
    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """Handle error with appropriate recovery strategy."""
        error_type = type(error).__name__
        error_data = {
            "error_type": error_type,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }
        
        self.error_history.append(error_data)
        self.logger.error("Error occurred", **error_data)
        
        # Try to recover using registered strategy
        if error_type in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[error_type]
                success = await strategy(error, context) if asyncio.iscoroutinefunction(strategy) else strategy(error, context)
                
                if success:
                    self.logger.info("Error recovery successful",
                                   error_type=error_type)
                    return True
                else:
                    self.logger.warning("Error recovery failed",
                                      error_type=error_type)
            except Exception as recovery_error:
                self.logger.error("Recovery strategy failed",
                                error_type=error_type,
                                recovery_error=str(recovery_error))
        
        return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        if not self.error_history:
            return {"total_errors": 0}
        
        error_counts = {}
        recent_errors = []
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        for error in self.error_history:
            error_type = error["error_type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            error_time = datetime.fromisoformat(error["timestamp"])
            if error_time > cutoff_time:
                recent_errors.append(error)
        
        return {
            "total_errors": len(self.error_history),
            "error_counts": error_counts,
            "recent_errors_1h": len(recent_errors),
            "most_common_error": max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None
        }


# Utility decorators
def with_circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    """Decorator to add circuit breaker protection."""
    def decorator(func: Callable) -> Callable:
        breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        return breaker(func)
    return decorator


def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """Decorator to add retry logic."""
    def decorator(func: Callable) -> Callable:
        retry_handler = RetryHandler(max_attempts, base_delay)
        return retry_handler(func)
    return decorator


def with_error_handling(agent_name: str):
    """Decorator to add comprehensive error handling."""
    def decorator(func: Callable) -> Callable:
        recovery_manager = ErrorRecoveryManager(agent_name)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:100],  # Truncate for logging
                    "kwargs": str(kwargs)[:100]
                }
                await recovery_manager.handle_error(e, context)
                raise
        
        return wrapper
    return decorator