"""
Security middleware for HealthSync agents.
Implements security controls for agent endpoints and communications.
"""

import functools
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import hashlib
import hmac

from .security_validator import security_validator, VALIDATION_SCHEMAS
from .rate_limiter import RateLimiter, DEFAULT_RATE_LIMITS
from .security_audit import security_auditor, SecurityEventType, RiskLevel
from .encryption import data_encryption

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for agent endpoints"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.rate_limiter = RateLimiter(DEFAULT_RATE_LIMITS.get(agent_type, DEFAULT_RATE_LIMITS['patient_agent']))
        self.message_signatures = {}  # For message integrity verification
    
    def secure_endpoint(self, validation_schema: Optional[str] = None, 
                       require_auth: bool = True,
                       log_access: bool = True):
        """
        Decorator to secure agent endpoints
        
        Args:
            validation_schema: Schema name for input validation
            require_auth: Whether authentication is required
            log_access: Whether to log access attempts
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request context
                request_context = self._extract_request_context(args, kwargs)
                
                try:
                    # 1. Rate limiting check
                    if not self._check_rate_limit(request_context):
                        return self._create_error_response("Rate limit exceeded", 429)
                    
                    # 2. Authentication check
                    if require_auth and not self._verify_authentication(request_context):
                        return self._create_error_response("Authentication required", 401)
                    
                    # 3. Input validation
                    if validation_schema and not self._validate_input(request_context, validation_schema):
                        return self._create_error_response("Invalid input data", 400)
                    
                    # 4. Message integrity check
                    if not self._verify_message_integrity(request_context):
                        return self._create_error_response("Message integrity verification failed", 400)
                    
                    # 5. Log access attempt
                    if log_access:
                        self._log_access_attempt(request_context, True)
                    
                    # Execute the original function
                    result = await func(*args, **kwargs)
                    
                    # 6. Encrypt sensitive response data
                    if self._contains_sensitive_data(result):
                        result = self._encrypt_response_data(result)
                    
                    return result
                    
                except Exception as e:
                    # Log security event
                    if log_access:
                        self._log_access_attempt(request_context, False, str(e))
                    
                    logger.error(f"Security middleware error: {str(e)}")
                    return self._create_error_response("Internal security error", 500)
            
            return wrapper
        return decorator
    
    def _extract_request_context(self, args, kwargs) -> Dict[str, Any]:
        """Extract request context from function arguments"""
        context = {
            'timestamp': datetime.utcnow(),
            'agent_type': self.agent_type,
            'source_ip': 'unknown',
            'user_id': None,
            'session_id': None,
            'message_data': None
        }
        
        # Try to extract context from different argument patterns
        if args:
            # Check if first argument is a message or request object
            first_arg = args[0]
            if hasattr(first_arg, 'sender'):
                context['user_id'] = first_arg.sender
            if hasattr(first_arg, 'session_id'):
                context['session_id'] = first_arg.session_id
            if hasattr(first_arg, 'content'):
                context['message_data'] = first_arg.content
        
        # Extract from kwargs
        context.update({
            k: v for k, v in kwargs.items() 
            if k in ['source_ip', 'user_id', 'session_id', 'message_data']
        })
        
        return context
    
    def _check_rate_limit(self, context: Dict[str, Any]) -> bool:
        """Check rate limiting for the request"""
        source_ip = context.get('source_ip', 'unknown')
        user_id = context.get('user_id')
        
        allowed, info = self.rate_limiter.is_allowed(source_ip, user_id)
        
        if not allowed:
            # Log rate limit violation
            security_auditor.log_event(
                event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                risk_level=RiskLevel.MEDIUM,
                source_ip=source_ip,
                resource=f"{self.agent_type}_endpoint",
                action="request",
                outcome="blocked",
                user_id=user_id,
                details=info
            )
        
        return allowed
    
    def _verify_authentication(self, context: Dict[str, Any]) -> bool:
        """Verify request authentication"""
        user_id = context.get('user_id')
        session_id = context.get('session_id')
        
        # Basic authentication check
        if not user_id:
            return False
        
        # Validate user ID format
        if not self._is_valid_user_id(user_id):
            return False
        
        # Session validation (simplified)
        if session_id and not self._is_valid_session(session_id, user_id):
            return False
        
        return True
    
    def _validate_input(self, context: Dict[str, Any], schema_name: str) -> bool:
        """Validate input data against schema"""
        message_data = context.get('message_data')
        
        if not message_data:
            return True  # No data to validate
        
        # Get validation schema
        schema = VALIDATION_SCHEMAS.get(schema_name)
        if not schema:
            logger.warning(f"Unknown validation schema: {schema_name}")
            return True
        
        # Validate input
        result = security_validator.validate_input(message_data, schema)
        
        if not result.is_valid:
            # Log validation failure
            security_auditor.log_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                risk_level=RiskLevel.HIGH if result.risk_level == "critical" else RiskLevel.MEDIUM,
                source_ip=context.get('source_ip', 'unknown'),
                resource=f"{self.agent_type}_endpoint",
                action="input_validation",
                outcome="blocked",
                user_id=context.get('user_id'),
                details={
                    'validation_errors': result.errors,
                    'risk_level': result.risk_level,
                    'schema': schema_name
                }
            )
        
        return result.is_valid
    
    def _verify_message_integrity(self, context: Dict[str, Any]) -> bool:
        """Verify message integrity using HMAC"""
        message_data = context.get('message_data')
        
        if not message_data or not isinstance(message_data, dict):
            return True  # No message to verify
        
        # Check for message signature
        signature = message_data.get('_signature')
        if not signature:
            return True  # No signature to verify
        
        # Remove signature from data for verification
        data_to_verify = {k: v for k, v in message_data.items() if k != '_signature'}
        
        # Calculate expected signature
        expected_signature = self._calculate_message_signature(data_to_verify)
        
        # Verify signature
        return hmac.compare_digest(signature, expected_signature)
    
    def _calculate_message_signature(self, data: Dict[str, Any]) -> str:
        """Calculate HMAC signature for message data"""
        # Use a shared secret key (in production, this should be properly managed)
        secret_key = b"healthsync_message_integrity_key"
        
        # Serialize data consistently
        import json
        data_str = json.dumps(data, sort_keys=True)
        
        # Calculate HMAC
        signature = hmac.new(secret_key, data_str.encode(), hashlib.sha256).hexdigest()
        
        return signature
    
    def _log_access_attempt(self, context: Dict[str, Any], success: bool, error: Optional[str] = None):
        """Log access attempt to security audit"""
        security_auditor.log_event(
            event_type=SecurityEventType.DATA_ACCESS if success else SecurityEventType.AUTHORIZATION_FAILURE,
            risk_level=RiskLevel.LOW if success else RiskLevel.MEDIUM,
            source_ip=context.get('source_ip', 'unknown'),
            resource=f"{self.agent_type}_endpoint",
            action="access",
            outcome="success" if success else "failure",
            user_id=context.get('user_id'),
            details={
                'timestamp': context['timestamp'].isoformat(),
                'session_id': context.get('session_id'),
                'error': error
            }
        )
    
    def _contains_sensitive_data(self, response_data: Any) -> bool:
        """Check if response contains sensitive data that should be encrypted"""
        if not isinstance(response_data, dict):
            return False
        
        # Check for sensitive field patterns
        sensitive_patterns = [
            'patient_id', 'ssn', 'medical_record', 'diagnosis',
            'treatment', 'medication', 'lab_result', 'genetic'
        ]
        
        response_str = str(response_data).lower()
        return any(pattern in response_str for pattern in sensitive_patterns)
    
    def _encrypt_response_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive response data"""
        try:
            # Identify sensitive fields
            sensitive_fields = {}
            non_sensitive_fields = {}
            
            for key, value in response_data.items():
                if self._is_sensitive_field(key):
                    sensitive_fields[key] = value
                else:
                    non_sensitive_fields[key] = value
            
            # Encrypt sensitive fields if any
            if sensitive_fields:
                encrypted_package = data_encryption.encrypt_sensitive_data(
                    sensitive_fields, 
                    f"{self.agent_type}_response"
                )
                
                # Combine with non-sensitive fields
                return {
                    **non_sensitive_fields,
                    '_encrypted_data': encrypted_package
                }
            
            return response_data
            
        except Exception as e:
            logger.error(f"Response encryption failed: {str(e)}")
            return response_data
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if field contains sensitive data"""
        sensitive_fields = [
            'patient_id', 'ssn', 'medical_record_number',
            'diagnosis', 'treatment', 'medication', 'lab_result',
            'genetic_data', 'biometric_data', 'personal_info'
        ]
        
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in sensitive_fields)
    
    def _is_valid_user_id(self, user_id: str) -> bool:
        """Validate user ID format"""
        import re
        
        # Check for valid patient or researcher ID format
        patterns = [
            r'^PAT_[A-Za-z0-9_-]{8,32}$',  # Patient ID
            r'^RES_[A-Za-z0-9_-]{8,32}$',  # Researcher ID
            r'^ADM_[A-Za-z0-9_-]{8,32}$'   # Admin ID
        ]
        
        return any(re.match(pattern, user_id) for pattern in patterns)
    
    def _is_valid_session(self, session_id: str, user_id: str) -> bool:
        """Validate session ID (simplified implementation)"""
        # In production, this would check against a session store
        import re
        
        # Basic format validation
        if not re.match(r'^SES_[A-Za-z0-9_-]{16,64}$', session_id):
            return False
        
        # Session should not be expired (simplified check)
        # In production, check against session store with expiration
        return True
    
    def _create_error_response(self, message: str, status_code: int) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'error': True,
            'message': message,
            'status_code': status_code,
            'timestamp': datetime.utcnow().isoformat(),
            'agent_type': self.agent_type
        }

# Security middleware instances for each agent type
security_middlewares = {
    'patient_consent': SecurityMiddleware('patient_consent'),
    'data_custodian': SecurityMiddleware('data_custodian'),
    'privacy_agent': SecurityMiddleware('privacy_agent'),
    'research_query': SecurityMiddleware('research_query'),
    'metta_integration': SecurityMiddleware('metta_integration')
}

def get_security_middleware(agent_type: str) -> SecurityMiddleware:
    """Get security middleware for agent type"""
    return security_middlewares.get(agent_type, SecurityMiddleware(agent_type))

# Convenience decorators for each agent type
def secure_patient_endpoint(**kwargs):
    """Security decorator for patient consent agent endpoints"""
    return security_middlewares['patient_consent'].secure_endpoint(**kwargs)

def secure_custodian_endpoint(**kwargs):
    """Security decorator for data custodian agent endpoints"""
    return security_middlewares['data_custodian'].secure_endpoint(**kwargs)

def secure_privacy_endpoint(**kwargs):
    """Security decorator for privacy agent endpoints"""
    return security_middlewares['privacy_agent'].secure_endpoint(**kwargs)

def secure_research_endpoint(**kwargs):
    """Security decorator for research query agent endpoints"""
    return security_middlewares['research_query'].secure_endpoint(**kwargs)

def secure_metta_endpoint(**kwargs):
    """Security decorator for MeTTa integration agent endpoints"""
    return security_middlewares['metta_integration'].secure_endpoint(**kwargs)