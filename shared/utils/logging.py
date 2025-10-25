"""
Logging utilities for HealthSync agents.
Provides structured logging with audit trails and monitoring integration.
"""

import logging
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os


class HealthSyncLogger:
    """Structured logger for HealthSync agents with audit trail support."""
    
    def __init__(self, agent_name: str, log_level: str = "INFO"):
        self.agent_name = agent_name
        self.log_level = log_level.upper()
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Create logger instance
        self.logger = structlog.get_logger(agent_name)
        
        # Set up file handler for audit logs
        self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Set up file logging for audit trails."""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        log_file = os.path.join(log_dir, f"{self.agent_name}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, self.log_level))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.setLevel(getattr(logging, self.log_level))
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, agent=self.agent_name, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, agent=self.agent_name, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(message, agent=self.agent_name, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, agent=self.agent_name, **kwargs)
    
    def audit(self, event_type: str, details: Dict[str, Any], **kwargs):
        """Log audit event with structured data."""
        audit_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent_name,
            "details": details,
            **kwargs
        }
        self.logger.info("AUDIT_EVENT", **audit_data)
    
    def message_log(self, direction: str, message_type: str, message_id: str, 
                   sender: str, recipient: str, **kwargs):
        """Log agent message for communication audit."""
        message_data = {
            "direction": direction,  # "sent" or "received"
            "message_type": message_type,
            "message_id": message_id,
            "sender": sender,
            "recipient": recipient,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info("MESSAGE_LOG", **message_data)
    
    def performance_log(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        perf_data = {
            "operation": operation,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent_name,
            **kwargs
        }
        self.logger.info("PERFORMANCE_LOG", **perf_data)


def get_logger(agent_name: str, log_level: str = "INFO") -> HealthSyncLogger:
    """Factory function to create logger instances."""
    return HealthSyncLogger(agent_name, log_level)


# Global logger instances for shared use
system_logger = get_logger("system")
audit_logger = get_logger("audit")
performance_logger = get_logger("performance")