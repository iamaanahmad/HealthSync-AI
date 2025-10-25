"""
Enhanced logging utilities for HealthSync agents.
Provides comprehensive audit trails, error tracking, and recovery logging.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import uuid
from enum import Enum
from functools import wraps


class AuditEventType(Enum):
    """Types of audit events."""
    AGENT_ACTION = "agent_action"
    DATA_ACCESS = "data_access"
    CONSENT_CHANGE = "consent_change"
    PRIVACY_OPERATION = "privacy_operation"
    ERROR_RECOVERY = "error_recovery"
    TRANSACTION = "transaction"
    SECURITY_EVENT = "security_event"
    COMMUNICATION = "communication"
    PERFORMANCE = "performance"


@dataclass
class AuditEvent:
    """Structured audit event."""
    event_id: str
    event_type: AuditEventType
    agent_name: str
    action: str
    timestamp: str
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        return data


class ComprehensiveAuditManager:
    """Manages comprehensive audit trails with advanced filtering and analysis."""
    
    def __init__(self):
        self.audit_events: List[AuditEvent] = []
        self.audit_file = "logs/comprehensive_audit.log"
        self.error_audit_file = "logs/error_audit.log"
        self.performance_audit_file = "logs/performance_audit.log"
        os.makedirs("logs", exist_ok=True)
    
    def log_event(self, event_type: AuditEventType, agent_name: str, action: str,
                  user_id: str = None, resource_id: str = None, 
                  details: Dict[str, Any] = None, success: bool = True,
                  error_message: str = None, duration_ms: float = None):
        """Log a comprehensive audit event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            agent_name=agent_name,
            action=action,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            resource_id=resource_id,
            details=details or {},
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        self.audit_events.append(event)
        
        # Write to appropriate audit files
        self._write_to_audit_files(event)
    
    def _write_to_audit_files(self, event: AuditEvent):
        """Write event to appropriate audit files."""
        event_data = json.dumps(event.to_dict(), default=str)
        
        # Write to main audit file
        with open(self.audit_file, "a") as f:
            f.write(event_data + "\n")
        
        # Write to specialized files
        if not event.success or event.error_message:
            with open(self.error_audit_file, "a") as f:
                f.write(event_data + "\n")
        
        if event.event_type == AuditEventType.PERFORMANCE or event.duration_ms:
            with open(self.performance_audit_file, "a") as f:
                f.write(event_data + "\n")
    
    def get_audit_trail(self, agent_name: str = None, event_type: AuditEventType = None,
                       start_time: datetime = None, end_time: datetime = None,
                       success_only: bool = None, user_id: str = None) -> List[AuditEvent]:
        """Get filtered audit trail with advanced filtering."""
        filtered_events = self.audit_events
        
        if agent_name:
            filtered_events = [e for e in filtered_events if e.agent_name == agent_name]
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        
        if start_time:
            filtered_events = [
                e for e in filtered_events 
                if datetime.fromisoformat(e.timestamp) >= start_time
            ]
        
        if end_time:
            filtered_events = [
                e for e in filtered_events 
                if datetime.fromisoformat(e.timestamp) <= end_time
            ]
        
        if success_only is not None:
            filtered_events = [e for e in filtered_events if e.success == success_only]
        
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        
        return filtered_events
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """Get comprehensive error analysis."""
        error_events = [e for e in self.audit_events if not e.success or e.error_message]
        
        if not error_events:
            return {"total_errors": 0}
        
        # Analyze error patterns
        error_by_agent = {}
        error_by_type = {}
        error_by_action = {}
        
        for event in error_events:
            # Count by agent
            agent = event.agent_name
            error_by_agent[agent] = error_by_agent.get(agent, 0) + 1
            
            # Count by event type
            event_type = event.event_type.value
            error_by_type[event_type] = error_by_type.get(event_type, 0) + 1
            
            # Count by action
            action = event.action
            error_by_action[action] = error_by_action.get(action, 0) + 1
        
        return {
            "total_errors": len(error_events),
            "error_rate": len(error_events) / len(self.audit_events) if self.audit_events else 0,
            "errors_by_agent": error_by_agent,
            "errors_by_type": error_by_type,
            "errors_by_action": error_by_action,
            "most_error_prone_agent": max(error_by_agent.items(), key=lambda x: x[1])[0] if error_by_agent else None
        }
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Get performance analysis from audit events."""
        perf_events = [e for e in self.audit_events if e.duration_ms is not None]
        
        if not perf_events:
            return {"total_performance_events": 0}
        
        durations = [e.duration_ms for e in perf_events]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        # Performance by agent
        agent_performance = {}
        for event in perf_events:
            agent = event.agent_name
            if agent not in agent_performance:
                agent_performance[agent] = []
            agent_performance[agent].append(event.duration_ms)
        
        # Calculate averages per agent
        agent_avg_performance = {
            agent: sum(durations) / len(durations)
            for agent, durations in agent_performance.items()
        }
        
        return {
            "total_performance_events": len(perf_events),
            "average_duration_ms": avg_duration,
            "max_duration_ms": max_duration,
            "min_duration_ms": min_duration,
            "agent_average_performance": agent_avg_performance,
            "slowest_agent": max(agent_avg_performance.items(), key=lambda x: x[1])[0] if agent_avg_performance else None
        }


class EnhancedStructuredLogger:
    """Enhanced structured logger with comprehensive audit and error tracking."""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.audit_manager = ComprehensiveAuditManager()
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # File handler for structured logs
        file_handler = logging.FileHandler(f"logs/{name}.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def _log_structured(self, level: str, message: str, **kwargs):
        """Log structured message with additional context."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger": self.name,
            "level": level,
            "message": message,
            "context": kwargs
        }
        
        log_message = json.dumps(log_data, default=str)
        getattr(self.logger, level.lower())(log_message)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_structured("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_structured("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_structured("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_structured("DEBUG", message, **kwargs)
    
    def audit(self, action: str, event_type: AuditEventType = AuditEventType.AGENT_ACTION,
              user_id: str = None, resource_id: str = None, 
              details: Dict[str, Any] = None, success: bool = True,
              error_message: str = None, duration_ms: float = None, **kwargs):
        """Log comprehensive audit trail entry."""
        # Log to audit manager
        self.audit_manager.log_event(
            event_type=event_type,
            agent_name=self.name,
            action=action,
            user_id=user_id,
            resource_id=resource_id,
            details=details,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        # Also log as structured message
        audit_context = {
            "event_type": event_type.value,
            "action": action,
            "user_id": user_id,
            "resource_id": resource_id,
            "success": success,
            **kwargs
        }
        
        if error_message:
            audit_context["error_message"] = error_message
        if duration_ms:
            audit_context["duration_ms"] = duration_ms
        
        self._log_structured("INFO", f"AUDIT: {action}", **audit_context)
    
    def log_data_access(self, user_id: str, resource_id: str, action: str,
                       success: bool = True, error_message: str = None, **details):
        """Log data access event."""
        self.audit(
            action=action,
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            resource_id=resource_id,
            success=success,
            error_message=error_message,
            details=details
        )
    
    def log_consent_change(self, patient_id: str, consent_type: str, 
                          new_value: bool, **details):
        """Log consent change event."""
        self.audit(
            action=f"consent_{consent_type}_{'granted' if new_value else 'revoked'}",
            event_type=AuditEventType.CONSENT_CHANGE,
            user_id=patient_id,
            success=True,
            details={"consent_type": consent_type, "new_value": new_value, **details}
        )
    
    def log_privacy_operation(self, operation: str, dataset_id: str, 
                            success: bool = True, duration_ms: float = None, **details):
        """Log privacy operation event."""
        self.audit(
            action=operation,
            event_type=AuditEventType.PRIVACY_OPERATION,
            resource_id=dataset_id,
            success=success,
            duration_ms=duration_ms,
            details=details
        )
    
    def log_error_recovery(self, error_type: str, recovery_action: str,
                          success: bool, duration_ms: float = None, **details):
        """Log error recovery event."""
        self.audit(
            action=f"recover_{error_type}_{recovery_action}",
            event_type=AuditEventType.ERROR_RECOVERY,
            success=success,
            duration_ms=duration_ms,
            details={"error_type": error_type, "recovery_action": recovery_action, **details}
        )
    
    def log_transaction(self, transaction_id: str, action: str, 
                       success: bool = True, duration_ms: float = None, **details):
        """Log transaction event."""
        self.audit(
            action=action,
            event_type=AuditEventType.TRANSACTION,
            resource_id=transaction_id,
            success=success,
            duration_ms=duration_ms,
            details=details
        )
    
    def log_communication(self, message_type: str, sender: str, recipient: str,
                         success: bool = True, duration_ms: float = None, **details):
        """Log inter-agent communication event."""
        self.audit(
            action=f"message_{message_type}",
            event_type=AuditEventType.COMMUNICATION,
            success=success,
            duration_ms=duration_ms,
            details={"message_type": message_type, "sender": sender, "recipient": recipient, **details}
        )
    
    def log_performance(self, operation: str, duration_ms: float, **details):
        """Log performance metrics."""
        self.audit(
            action=operation,
            event_type=AuditEventType.PERFORMANCE,
            success=True,
            duration_ms=duration_ms,
            details=details
        )
    
    def log_security_event(self, event_type: str, severity: str, **details):
        """Log security event."""
        self.audit(
            action=f"security_{event_type}",
            event_type=AuditEventType.SECURITY_EVENT,
            success=severity not in ["high", "critical"],
            details={"severity": severity, "event_type": event_type, **details}
        )
    
    def get_audit_trail(self, **filters) -> List[AuditEvent]:
        """Get audit trail with filters."""
        return self.audit_manager.get_audit_trail(**filters)
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """Get error analysis for this logger."""
        return self.audit_manager.get_error_analysis()
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Get performance analysis for this logger."""
        return self.audit_manager.get_performance_analysis()


# Performance monitoring decorator
def log_performance(logger: EnhancedStructuredLogger, operation_name: str = None):
    """Decorator to automatically log performance metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            operation = operation_name or f"{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.log_performance(operation, duration, success=True)
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.log_performance(operation, duration, success=False, error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            operation = operation_name or f"{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.log_performance(operation, duration, success=True)
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.log_performance(operation, duration, success=False, error=str(e))
                raise
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global enhanced audit manager instance
global_enhanced_audit_manager = ComprehensiveAuditManager()


def get_enhanced_logger(name: str, log_level: str = "INFO") -> EnhancedStructuredLogger:
    """Get or create enhanced structured logger instance."""
    return EnhancedStructuredLogger(name, log_level)


def log_global_enhanced_audit(event_type: AuditEventType, agent_name: str, action: str, **kwargs):
    """Log to global enhanced audit trail."""
    global_enhanced_audit_manager.log_event(event_type, agent_name, action, **kwargs)