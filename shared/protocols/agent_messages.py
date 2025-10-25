"""
Inter-agent communication protocols for HealthSync system.
Defines standardized message formats for agent collaboration.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid


class AgentMessage(BaseModel):
    """Base message format for inter-agent communication."""
    message_id: str = None
    sender_agent: str
    recipient_agent: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = None
    requires_acknowledgment: bool = True
    correlation_id: Optional[str] = None  # For tracking related messages
    
    def __init__(self, **data):
        if data.get('message_id') is None:
            data['message_id'] = str(uuid.uuid4())
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class AgentAcknowledgment(BaseModel):
    """Acknowledgment message for received agent messages."""
    ack_id: str = None
    original_message_id: str
    sender_agent: str
    recipient_agent: str
    status: str  # "received", "processed", "error"
    response_data: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0
    timestamp: datetime = None
    
    def __init__(self, **data):
        if data.get('ack_id') is None:
            data['ack_id'] = str(uuid.uuid4())
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


# Consent-related messages
class ConsentMessage(BaseModel):
    """Message format for patient consent operations."""
    patient_id: str
    data_types: List[str]
    research_categories: List[str]
    consent_status: bool
    expiry_date: datetime
    metadata: Dict[str, Any] = {}


class ConsentQuery(BaseModel):
    """Query format for checking patient consent."""
    patient_id: str
    data_type: str
    research_category: str
    requester_id: str


# Data access messages
class DataRequest(BaseModel):
    """Message format for data access requests."""
    request_id: str = None
    requester_id: str
    data_criteria: Dict[str, Any]
    research_purpose: str
    ethical_approval: str
    consent_verified: bool = False
    
    def __init__(self, **data):
        if data.get('request_id') is None:
            data['request_id'] = str(uuid.uuid4())
        super().__init__(**data)


class DataResponse(BaseModel):
    """Response format for data access requests."""
    request_id: str
    dataset_id: str
    patient_count: int
    data_fields: List[str]
    access_granted: bool
    denial_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}


# Research query messages
class ResearchQuery(BaseModel):
    """Message format for research queries."""
    query_id: str = None
    researcher_id: str
    study_description: str
    data_requirements: Dict[str, Any]
    ethical_approval_id: str
    priority: str = "normal"  # "low", "normal", "high"
    
    def __init__(self, **data):
        if data.get('query_id') is None:
            data['query_id'] = str(uuid.uuid4())
        super().__init__(**data)


class QueryResult(BaseModel):
    """Result format for research queries."""
    query_id: str
    dataset_summary: Dict[str, Any]
    anonymized_data: List[Dict[str, Any]]
    processing_log: List[str]
    privacy_metrics: Dict[str, Any] = {}
    completion_status: str = "completed"  # "completed", "partial", "failed"


# Privacy and anonymization messages
class AnonymizationRequest(BaseModel):
    """Request format for data anonymization."""
    request_id: str = None
    dataset_id: str
    raw_data: List[Dict[str, Any]]
    privacy_level: str  # "basic", "enhanced", "maximum"
    k_anonymity_threshold: int = 5
    
    def __init__(self, **data):
        if data.get('request_id') is None:
            data['request_id'] = str(uuid.uuid4())
        super().__init__(**data)


class AnonymizedData(BaseModel):
    """Response format for anonymized data."""
    request_id: str
    dataset_id: str
    anonymized_records: List[Dict[str, Any]]
    privacy_metrics: Dict[str, Any]
    anonymization_log: str
    quality_score: float = 1.0


# MeTTa integration messages
class MeTTaQuery(BaseModel):
    """Query format for MeTTa Knowledge Graph operations."""
    query_id: str = None
    query_type: str  # "store", "retrieve", "reason", "validate"
    query_expression: str
    context_variables: Dict[str, Any] = {}
    
    def __init__(self, **data):
        if data.get('query_id') is None:
            data['query_id'] = str(uuid.uuid4())
        super().__init__(**data)


class MeTTaResponse(BaseModel):
    """Response format for MeTTa operations."""
    query_id: str
    results: List[Dict[str, Any]]
    reasoning_path: List[str]
    confidence_score: float
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


# Error handling messages
class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error_id: str = None
    error_code: str
    error_message: str
    error_context: Dict[str, Any] = {}
    recovery_suggestions: List[str] = []
    retry_after: Optional[int] = None  # seconds
    timestamp: datetime = None
    
    def __init__(self, **data):
        if data.get('error_id') is None:
            data['error_id'] = str(uuid.uuid4())
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


# Message type constants
class MessageTypes:
    """Constants for message types."""
    
    # Consent operations
    CONSENT_UPDATE = "consent_update"
    CONSENT_QUERY = "consent_query"
    CONSENT_RESPONSE = "consent_response"
    
    # Data operations
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    DATA_ACCESS_LOG = "data_access_log"
    
    # Research operations
    RESEARCH_QUERY = "research_query"
    QUERY_RESULT = "query_result"
    QUERY_STATUS = "query_status"
    
    # Privacy operations
    ANONYMIZATION_REQUEST = "anonymization_request"
    ANONYMIZED_DATA = "anonymized_data"
    PRIVACY_AUDIT = "privacy_audit"
    
    # MeTTa operations
    METTA_QUERY = "metta_query"
    METTA_RESPONSE = "metta_response"
    METTA_UPDATE = "metta_update"
    METTA_STORE = "metta_store"
    METTA_VALIDATE = "metta_validate"
    
    # System operations
    HEALTH_CHECK = "health_check"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    
    # Acknowledgments
    ACK_RECEIVED = "ack_received"
    ACK_PROCESSED = "ack_processed"
    ACK_ERROR = "ack_error"


# Error code constants
class ErrorCodes:
    """Constants for error codes."""
    
    # Consent errors
    CONSENT_EXPIRED = "CONSENT_EXPIRED"
    CONSENT_REVOKED = "CONSENT_REVOKED"
    CONSENT_NOT_FOUND = "CONSENT_NOT_FOUND"
    
    # Data errors
    DATA_NOT_AVAILABLE = "DATA_NOT_AVAILABLE"
    DATA_QUALITY_ISSUES = "DATA_QUALITY_ISSUES"
    ANONYMIZATION_FAILED = "ANONYMIZATION_FAILED"
    
    # Ethics errors
    ETHICS_VIOLATION = "ETHICS_VIOLATION"
    INSUFFICIENT_APPROVAL = "INSUFFICIENT_APPROVAL"
    COMPLIANCE_FAILURE = "COMPLIANCE_FAILURE"
    
    # System errors
    AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"
    METTA_QUERY_FAILED = "METTA_QUERY_FAILED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    INVALID_MESSAGE_FORMAT = "INVALID_MESSAGE_FORMAT"