"""
Security audit logging and monitoring system for HealthSync.
Tracks security events, compliance violations, and system access.
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from pathlib import Path

class SecurityEventType(Enum):
    """Types of security events"""
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONSENT_CHANGE = "consent_change"
    PRIVACY_VIOLATION = "privacy_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SYSTEM_ERROR = "system_error"
    COMPLIANCE_VIOLATION = "compliance_violation"
    AGENT_COMMUNICATION = "agent_communication"
    METTA_QUERY = "metta_query"
    ANONYMIZATION_EVENT = "anonymization_event"

class RiskLevel(Enum):
    """Risk levels for security events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    timestamp: datetime
    event_type: SecurityEventType
    risk_level: RiskLevel
    source_ip: str
    user_id: Optional[str]
    agent_id: Optional[str]
    resource: str
    action: str
    outcome: str  # success, failure, blocked
    details: Dict[str, Any]
    data_hash: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['risk_level'] = self.risk_level.value
        return data

class SecurityAuditor:
    """Main security audit logging system"""
    
    def __init__(self, log_file: str = "logs/security_audit.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger("security_audit")
        self.logger.setLevel(logging.INFO)
        
        # File handler for audit logs
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # In-memory event storage for analysis
        self.recent_events = []
        self.event_counts = {}
        self.risk_metrics = {
            'total_events': 0,
            'high_risk_events': 0,
            'critical_events': 0,
            'failed_authentications': 0,
            'privacy_violations': 0
        }
        
        self.lock = threading.Lock()
    
    def log_event(self, event_type: SecurityEventType, risk_level: RiskLevel,
                  source_ip: str, resource: str, action: str, outcome: str,
                  user_id: Optional[str] = None, agent_id: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  session_id: Optional[str] = None) -> str:
        """
        Log a security event
        
        Returns:
            Event ID for tracking
        """
        if details is None:
            details = {}
        
        # Generate event ID
        event_id = self._generate_event_id(event_type, source_ip, resource)
        
        # Create data hash for integrity
        data_hash = self._create_data_hash(details)
        
        # Create event
        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            risk_level=risk_level,
            source_ip=source_ip,
            user_id=user_id,
            agent_id=agent_id,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details,
            data_hash=data_hash,
            session_id=session_id
        )
        
        # Log to file
        self.logger.info(json.dumps(event.to_dict()))
        
        # Store in memory for analysis
        with self.lock:
            self.recent_events.append(event)
            
            # Keep only last 1000 events in memory
            if len(self.recent_events) > 1000:
                self.recent_events = self.recent_events[-1000:]
            
            # Update metrics
            self._update_metrics(event)
        
        # Check for security alerts
        self._check_security_alerts(event)
        
        return event_id
    
    def log_authentication(self, user_id: str, source_ip: str, 
                          success: bool, details: Optional[Dict] = None):
        """Log authentication event"""
        event_type = SecurityEventType.AUTHENTICATION_SUCCESS if success else SecurityEventType.AUTHENTICATION_FAILURE
        risk_level = RiskLevel.LOW if success else RiskLevel.MEDIUM
        outcome = "success" if success else "failure"
        
        self.log_event(
            event_type=event_type,
            risk_level=risk_level,
            source_ip=source_ip,
            resource="authentication",
            action="login",
            outcome=outcome,
            user_id=user_id,
            details=details or {}
        )
    
    def log_data_access(self, user_id: str, agent_id: str, source_ip: str,
                       resource: str, data_type: str, patient_count: int,
                       success: bool, details: Optional[Dict] = None):
        """Log data access event"""
        risk_level = RiskLevel.LOW if success else RiskLevel.HIGH
        outcome = "success" if success else "blocked"
        
        access_details = {
            'data_type': data_type,
            'patient_count': patient_count,
            'access_time': datetime.utcnow().isoformat()
        }
        if details:
            access_details.update(details)
        
        self.log_event(
            event_type=SecurityEventType.DATA_ACCESS,
            risk_level=risk_level,
            source_ip=source_ip,
            resource=resource,
            action="access",
            outcome=outcome,
            user_id=user_id,
            agent_id=agent_id,
            details=access_details
        )
    
    def log_consent_change(self, patient_id: str, source_ip: str,
                          consent_type: str, old_value: bool, new_value: bool,
                          details: Optional[Dict] = None):
        """Log consent change event"""
        consent_details = {
            'consent_type': consent_type,
            'old_value': old_value,
            'new_value': new_value,
            'change_time': datetime.utcnow().isoformat()
        }
        if details:
            consent_details.update(details)
        
        self.log_event(
            event_type=SecurityEventType.CONSENT_CHANGE,
            risk_level=RiskLevel.MEDIUM,
            source_ip=source_ip,
            resource="patient_consent",
            action="modify",
            outcome="success",
            user_id=patient_id,
            details=consent_details
        )
    
    def log_privacy_event(self, agent_id: str, source_ip: str,
                         anonymization_method: str, patient_count: int,
                         k_anonymity: int, success: bool,
                         details: Optional[Dict] = None):
        """Log privacy/anonymization event"""
        privacy_details = {
            'anonymization_method': anonymization_method,
            'patient_count': patient_count,
            'k_anonymity': k_anonymity,
            'processing_time': datetime.utcnow().isoformat()
        }
        if details:
            privacy_details.update(details)
        
        risk_level = RiskLevel.LOW if success and k_anonymity >= 5 else RiskLevel.HIGH
        outcome = "success" if success else "failure"
        
        self.log_event(
            event_type=SecurityEventType.ANONYMIZATION_EVENT,
            risk_level=risk_level,
            source_ip=source_ip,
            resource="privacy_agent",
            action="anonymize",
            outcome=outcome,
            agent_id=agent_id,
            details=privacy_details
        )
    
    def log_agent_communication(self, sender_agent: str, receiver_agent: str,
                               message_type: str, success: bool,
                               details: Optional[Dict] = None):
        """Log inter-agent communication"""
        comm_details = {
            'sender_agent': sender_agent,
            'receiver_agent': receiver_agent,
            'message_type': message_type,
            'communication_time': datetime.utcnow().isoformat()
        }
        if details:
            comm_details.update(details)
        
        risk_level = RiskLevel.LOW if success else RiskLevel.MEDIUM
        outcome = "success" if success else "failure"
        
        self.log_event(
            event_type=SecurityEventType.AGENT_COMMUNICATION,
            risk_level=risk_level,
            source_ip="internal",
            resource="agent_network",
            action="communicate",
            outcome=outcome,
            agent_id=sender_agent,
            details=comm_details
        )
    
    def log_metta_query(self, agent_id: str, query_type: str, 
                       query_complexity: str, success: bool,
                       details: Optional[Dict] = None):
        """Log MeTTa knowledge graph queries"""
        query_details = {
            'query_type': query_type,
            'query_complexity': query_complexity,
            'query_time': datetime.utcnow().isoformat()
        }
        if details:
            query_details.update(details)
        
        risk_level = RiskLevel.LOW if success else RiskLevel.MEDIUM
        outcome = "success" if success else "failure"
        
        self.log_event(
            event_type=SecurityEventType.METTA_QUERY,
            risk_level=risk_level,
            source_ip="internal",
            resource="metta_knowledge_graph",
            action="query",
            outcome=outcome,
            agent_id=agent_id,
            details=query_details
        )
    
    def _generate_event_id(self, event_type: SecurityEventType, 
                          source_ip: str, resource: str) -> str:
        """Generate unique event ID"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{event_type.value}:{source_ip}:{resource}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _create_data_hash(self, details: Dict[str, Any]) -> str:
        """Create hash of event details for integrity"""
        data_str = json.dumps(details, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _update_metrics(self, event: SecurityEvent):
        """Update security metrics"""
        self.risk_metrics['total_events'] += 1
        
        if event.risk_level == RiskLevel.HIGH:
            self.risk_metrics['high_risk_events'] += 1
        elif event.risk_level == RiskLevel.CRITICAL:
            self.risk_metrics['critical_events'] += 1
        
        if event.event_type == SecurityEventType.AUTHENTICATION_FAILURE:
            self.risk_metrics['failed_authentications'] += 1
        elif event.event_type == SecurityEventType.PRIVACY_VIOLATION:
            self.risk_metrics['privacy_violations'] += 1
        
        # Count events by type
        event_type_key = event.event_type.value
        self.event_counts[event_type_key] = self.event_counts.get(event_type_key, 0) + 1
    
    def _check_security_alerts(self, event: SecurityEvent):
        """Check if event triggers security alerts"""
        alerts = []
        
        # Critical events always trigger alerts
        if event.risk_level == RiskLevel.CRITICAL:
            alerts.append(f"CRITICAL security event: {event.event_type.value}")
        
        # Multiple failed authentications
        if event.event_type == SecurityEventType.AUTHENTICATION_FAILURE:
            recent_failures = self._count_recent_events(
                SecurityEventType.AUTHENTICATION_FAILURE,
                source_ip=event.source_ip,
                minutes=15
            )
            if recent_failures >= 5:
                alerts.append(f"Multiple authentication failures from {event.source_ip}")
        
        # Privacy violations
        if event.event_type == SecurityEventType.PRIVACY_VIOLATION:
            alerts.append(f"Privacy violation detected: {event.details}")
        
        # Log alerts
        for alert in alerts:
            self.logger.warning(f"SECURITY ALERT: {alert}")
    
    def _count_recent_events(self, event_type: SecurityEventType,
                           source_ip: Optional[str] = None,
                           user_id: Optional[str] = None,
                           minutes: int = 60) -> int:
        """Count recent events of specific type"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        count = 0
        for event in self.recent_events:
            if (event.timestamp >= cutoff and 
                event.event_type == event_type and
                (source_ip is None or event.source_ip == source_ip) and
                (user_id is None or event.user_id == user_id)):
                count += 1
        
        return count
    
    def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate security report for specified time period"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter recent events
        recent_events = [
            event for event in self.recent_events
            if event.timestamp >= cutoff
        ]
        
        # Calculate statistics
        total_events = len(recent_events)
        risk_distribution = {}
        event_type_distribution = {}
        outcome_distribution = {}
        
        for event in recent_events:
            # Risk level distribution
            risk_key = event.risk_level.value
            risk_distribution[risk_key] = risk_distribution.get(risk_key, 0) + 1
            
            # Event type distribution
            type_key = event.event_type.value
            event_type_distribution[type_key] = event_type_distribution.get(type_key, 0) + 1
            
            # Outcome distribution
            outcome_distribution[event.outcome] = outcome_distribution.get(event.outcome, 0) + 1
        
        # Top source IPs
        ip_counts = {}
        for event in recent_events:
            ip_counts[event.source_ip] = ip_counts.get(event.source_ip, 0) + 1
        
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'report_period_hours': hours,
            'total_events': total_events,
            'risk_distribution': risk_distribution,
            'event_type_distribution': event_type_distribution,
            'outcome_distribution': outcome_distribution,
            'top_source_ips': top_ips,
            'current_metrics': self.risk_metrics.copy(),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def search_events(self, event_type: Optional[SecurityEventType] = None,
                     risk_level: Optional[RiskLevel] = None,
                     source_ip: Optional[str] = None,
                     user_id: Optional[str] = None,
                     hours: int = 24) -> List[SecurityEvent]:
        """Search security events with filters"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_events = []
        for event in self.recent_events:
            if event.timestamp < cutoff:
                continue
            
            if event_type and event.event_type != event_type:
                continue
            
            if risk_level and event.risk_level != risk_level:
                continue
            
            if source_ip and event.source_ip != source_ip:
                continue
            
            if user_id and event.user_id != user_id:
                continue
            
            filtered_events.append(event)
        
        return filtered_events

# Global security auditor instance
security_auditor = SecurityAuditor()