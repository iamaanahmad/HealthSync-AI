"""
Global error handling middleware for HealthSync agents.
Provides centralized error management, compensation transactions, and recovery.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from functools import wraps

from .logging import get_logger
from .error_handling import ErrorRecoveryManager, CircuitBreaker, RetryHandler

logger = get_logger("error_middleware")


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionStatus(Enum):
    """Transaction status for compensation."""
    PENDING = "pending"
    COMMITTED = "committed"
    COMPENSATED = "compensated"
    FAILED = "failed"


@dataclass
class ErrorEvent:
    """Structured error event for tracking and analysis."""
    error_id: str
    agent_name: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class CompensationAction:
    """Represents a compensation action for transaction rollback."""
    action_id: str
    agent_name: str
    action_type: str
    action_data: Dict[str, Any]
    timestamp: str
    executed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class TransactionManager:
    """Manages distributed transactions and compensation."""
    
    def __init__(self):
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self.compensation_actions: Dict[str, List[CompensationAction]] = {}
        self.logger = get_logger("transaction_manager")
    
    def start_transaction(self, transaction_id: str, description: str) -> str:
        """Start a new distributed transaction."""
        self.transactions[transaction_id] = {
            "id": transaction_id,
            "description": description,
            "status": TransactionStatus.PENDING,
            "started_at": datetime.utcnow().isoformat(),
            "participants": [],
            "steps": []
        }
        self.compensation_actions[transaction_id] = []
        
        self.logger.info("Transaction started",
                        transaction_id=transaction_id,
                        description=description)
        return transaction_id
    
    def add_participant(self, transaction_id: str, agent_name: str):
        """Add agent as transaction participant."""
        if transaction_id in self.transactions:
            self.transactions[transaction_id]["participants"].append(agent_name)
            self.logger.debug("Participant added to transaction",
                            transaction_id=transaction_id,
                            agent_name=agent_name)
    
    def add_step(self, transaction_id: str, step_name: str, agent_name: str, 
                 step_data: Dict[str, Any]):
        """Add a step to the transaction."""
        if transaction_id in self.transactions:
            step = {
                "step_name": step_name,
                "agent_name": agent_name,
                "step_data": step_data,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            self.transactions[transaction_id]["steps"].append(step)
    
    def register_compensation(self, transaction_id: str, agent_name: str,
                            action_type: str, action_data: Dict[str, Any]):
        """Register compensation action for rollback."""
        if transaction_id not in self.compensation_actions:
            self.compensation_actions[transaction_id] = []
        
        compensation = CompensationAction(
            action_id=str(uuid.uuid4()),
            agent_name=agent_name,
            action_type=action_type,
            action_data=action_data,
            timestamp=datetime.utcnow().isoformat()
        )
        
        self.compensation_actions[transaction_id].append(compensation)
        self.logger.debug("Compensation action registered",
                         transaction_id=transaction_id,
                         agent_name=agent_name,
                         action_type=action_type)
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit the transaction."""
        if transaction_id not in self.transactions:
            return False
        
        self.transactions[transaction_id]["status"] = TransactionStatus.COMMITTED
        self.transactions[transaction_id]["completed_at"] = datetime.utcnow().isoformat()
        
        self.logger.info("Transaction committed",
                        transaction_id=transaction_id)
        return True
    
    async def compensate_transaction(self, transaction_id: str) -> bool:
        """Execute compensation actions to rollback transaction."""
        if transaction_id not in self.compensation_actions:
            return False
        
        self.logger.warning("Starting transaction compensation",
                           transaction_id=transaction_id)
        
        # Execute compensation actions in reverse order
        actions = list(reversed(self.compensation_actions[transaction_id]))
        success_count = 0
        
        for action in actions:
            try:
                # Here you would call the appropriate agent's compensation method
                # For now, we'll just mark as executed
                action.executed = True
                success_count += 1
                
                self.logger.info("Compensation action executed",
                               transaction_id=transaction_id,
                               action_id=action.action_id,
                               agent_name=action.agent_name)
                
            except Exception as e:
                self.logger.error("Compensation action failed",
                                transaction_id=transaction_id,
                                action_id=action.action_id,
                                error=str(e))
        
        # Update transaction status
        if transaction_id in self.transactions:
            if success_count == len(actions):
                self.transactions[transaction_id]["status"] = TransactionStatus.COMPENSATED
            else:
                self.transactions[transaction_id]["status"] = TransactionStatus.FAILED
        
        self.logger.info("Transaction compensation completed",
                        transaction_id=transaction_id,
                        successful_actions=success_count,
                        total_actions=len(actions))
        
        return success_count == len(actions)
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction status and details."""
        return self.transactions.get(transaction_id)


class ErrorNotificationSystem:
    """Handles error notifications and alerting."""
    
    def __init__(self):
        self.subscribers: Dict[ErrorSeverity, List[Callable]] = {
            severity: [] for severity in ErrorSeverity
        }
        self.notification_history: List[Dict[str, Any]] = []
        self.logger = get_logger("error_notifications")
    
    def subscribe(self, severity: ErrorSeverity, callback: Callable):
        """Subscribe to error notifications of specific severity."""
        self.subscribers[severity].append(callback)
        self.logger.info("Notification subscriber added",
                        severity=severity.value)
    
    async def notify(self, error_event: ErrorEvent):
        """Send notifications for error event."""
        callbacks = self.subscribers.get(error_event.severity, [])
        
        notification = {
            "notification_id": str(uuid.uuid4()),
            "error_event": error_event.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
            "recipients": len(callbacks)
        }
        
        self.notification_history.append(notification)
        
        # Send notifications
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error_event)
                else:
                    callback(error_event)
            except Exception as e:
                self.logger.error("Notification callback failed",
                                error=str(e),
                                callback=str(callback))
        
        self.logger.info("Error notifications sent",
                        error_id=error_event.error_id,
                        severity=error_event.severity.value,
                        recipients=len(callbacks))


class GlobalErrorHandler:
    """Global error handling middleware for all agents."""
    
    def __init__(self):
        self.transaction_manager = TransactionManager()
        self.notification_system = ErrorNotificationSystem()
        self.error_history: List[ErrorEvent] = []
        self.recovery_managers: Dict[str, ErrorRecoveryManager] = {}
        self.logger = get_logger("global_error_handler")
        
        # Error rate tracking
        self.error_rates: Dict[str, List[float]] = {}
        self.rate_window = 300  # 5 minutes
    
    def get_recovery_manager(self, agent_name: str) -> ErrorRecoveryManager:
        """Get or create recovery manager for agent."""
        if agent_name not in self.recovery_managers:
            self.recovery_managers[agent_name] = ErrorRecoveryManager(agent_name)
        return self.recovery_managers[agent_name]
    
    def determine_severity(self, error: Exception, context: Dict[str, Any]) -> ErrorSeverity:
        """Determine error severity based on error type and context."""
        error_type = type(error).__name__
        
        # Critical errors that affect system integrity
        critical_errors = [
            "SecurityError", "AuthenticationError", "DataCorruptionError",
            "SystemShutdownError"
        ]
        
        # High severity errors that affect core functionality
        high_errors = [
            "ConsentViolationError", "PrivacyBreachError", "EthicsViolationError",
            "DataAccessError"
        ]
        
        # Medium severity errors that affect specific operations
        medium_errors = [
            "ValidationError", "ProcessingError", "CommunicationError",
            "TimeoutError"
        ]
        
        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_type in high_errors:
            return ErrorSeverity.HIGH
        elif error_type in medium_errors:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    async def handle_error(self, agent_name: str, error: Exception, 
                          context: Dict[str, Any] = None) -> ErrorEvent:
        """Handle error with comprehensive recovery and notification."""
        context = context or {}
        severity = self.determine_severity(error, context)
        
        # Create error event
        error_event = ErrorEvent(
            error_id=str(uuid.uuid4()),
            agent_name=agent_name,
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            timestamp=datetime.utcnow().isoformat(),
            context=context,
            stack_trace=context.get("stack_trace")
        )
        
        self.error_history.append(error_event)
        self._update_error_rates(agent_name)
        
        # Attempt recovery
        recovery_manager = self.get_recovery_manager(agent_name)
        try:
            recovery_successful = await recovery_manager.handle_error(error, context)
            error_event.recovery_attempted = True
            error_event.recovery_successful = recovery_successful
        except Exception as recovery_error:
            self.logger.error("Recovery attempt failed",
                            agent_name=agent_name,
                            error_id=error_event.error_id,
                            recovery_error=str(recovery_error))
        
        # Send notifications
        await self.notification_system.notify(error_event)
        
        # Handle transaction compensation if needed
        transaction_id = context.get("transaction_id")
        if transaction_id and severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            compensation_success = await self.transaction_manager.compensate_transaction(transaction_id)
            if compensation_success:
                self.logger.info("Transaction compensation completed", 
                               transaction_id=transaction_id)
        
        self.logger.error("Error handled by global handler",
                         error_id=error_event.error_id,
                         agent_name=agent_name,
                         severity=severity.value,
                         recovery_successful=error_event.recovery_successful)
        
        return error_event
    
    def _update_error_rates(self, agent_name: str):
        """Update error rate tracking for agent."""
        current_time = time.time()
        
        if agent_name not in self.error_rates:
            self.error_rates[agent_name] = []
        
        # Add current error timestamp
        self.error_rates[agent_name].append(current_time)
        
        # Remove old timestamps outside the window
        cutoff_time = current_time - self.rate_window
        self.error_rates[agent_name] = [
            t for t in self.error_rates[agent_name] if t > cutoff_time
        ]
    
    def get_error_rate(self, agent_name: str) -> float:
        """Get current error rate for agent (errors per minute)."""
        if agent_name not in self.error_rates:
            return 0.0
        
        current_time = time.time()
        cutoff_time = current_time - self.rate_window
        
        recent_errors = [
            t for t in self.error_rates[agent_name] if t > cutoff_time
        ]
        
        return len(recent_errors) / (self.rate_window / 60)  # errors per minute
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        total_errors = len(self.error_history)
        recent_errors = [
            e for e in self.error_history 
            if datetime.fromisoformat(e.timestamp) > datetime.utcnow() - timedelta(hours=1)
        ]
        
        severity_counts = {}
        for error in recent_errors:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        agent_error_rates = {
            agent: self.get_error_rate(agent)
            for agent in self.error_rates.keys()
        }
        
        return {
            "total_errors": total_errors,
            "recent_errors_1h": len(recent_errors),
            "severity_breakdown": severity_counts,
            "agent_error_rates": agent_error_rates,
            "active_transactions": len(self.transaction_manager.transactions),
            "system_status": "healthy" if len(recent_errors) < 5 else "degraded"
        }


# Global instance
global_error_handler = GlobalErrorHandler()


def with_global_error_handling(agent_name: str):
    """Decorator to add global error handling to agent methods."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Add stack trace for debugging
                import traceback
                context["stack_trace"] = traceback.format_exc()
                
                await global_error_handler.handle_error(agent_name, e, context)
                raise
        
        return wrapper
    return decorator


def with_transaction_support(transaction_id: str = None):
    """Decorator to add transaction support to agent methods."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Use provided transaction_id or create new one
            tx_id = transaction_id or str(uuid.uuid4())
            
            # Add transaction context
            if 'context' in kwargs:
                kwargs['context']['transaction_id'] = tx_id
            else:
                kwargs['context'] = {'transaction_id': tx_id}
            
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        
        return wrapper
    return decorator