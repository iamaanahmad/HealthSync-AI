"""
Security validation utilities for HealthSync system.
Implements input validation, sanitization, and security checks.
"""

import re
import html
import json
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of security validation"""
    is_valid: bool
    errors: List[str]
    sanitized_data: Optional[Dict[str, Any]] = None
    risk_level: str = "low"  # low, medium, high, critical

class SecurityValidator:
    """Comprehensive security validation and sanitization"""
    
    # Regex patterns for validation
    PATTERNS = {
        'patient_id': re.compile(r'^[A-Za-z0-9_-]{8,64}$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'research_id': re.compile(r'^RES_[A-Za-z0-9_-]{8,32}$'),
        'agent_id': re.compile(r'^[A-Za-z0-9_-]{8,64}$'),
        'query_id': re.compile(r'^QRY_[A-Za-z0-9_-]{8,32}$'),
        'alphanumeric': re.compile(r'^[A-Za-z0-9_\s-]+$'),
        'safe_text': re.compile(r'^[A-Za-z0-9\s.,!?_-]+$')
    }
    
    # Maximum lengths for different field types
    MAX_LENGTHS = {
        'patient_id': 64,
        'email': 254,
        'name': 100,
        'description': 1000,
        'query_text': 5000,
        'message': 2000,
        'consent_type': 50,
        'research_category': 100
    }
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'eval\s*\(', re.IGNORECASE),
        re.compile(r'exec\s*\(', re.IGNORECASE),
        re.compile(r'import\s+', re.IGNORECASE),
        re.compile(r'__.*__', re.IGNORECASE),
        re.compile(r'\.\./', re.IGNORECASE),
        re.compile(r'union\s+select', re.IGNORECASE),
        re.compile(r'drop\s+table', re.IGNORECASE)
    ]
    
    def __init__(self):
        self.validation_cache = {}
        self.security_events = []
    
    def validate_input(self, data: Dict[str, Any], schema: Dict[str, str]) -> ValidationResult:
        """
        Validate input data against schema with security checks
        
        Args:
            data: Input data to validate
            schema: Validation schema with field types
            
        Returns:
            ValidationResult with validation status and sanitized data
        """
        errors = []
        sanitized_data = {}
        risk_level = "low"
        
        try:
            # Check for required fields
            for field, field_type in schema.items():
                if field.endswith('*'):  # Required field
                    field_name = field.rstrip('*')
                    if field_name not in data:
                        errors.append(f"Required field '{field_name}' is missing")
                        continue
                    value = data[field_name]
                else:
                    field_name = field
                    value = data.get(field_name)
                    if value is None:
                        continue
                
                # Validate and sanitize field
                field_result = self._validate_field(field_name, value, field_type)
                if not field_result.is_valid:
                    errors.extend(field_result.errors)
                    if field_result.risk_level in ["high", "critical"]:
                        risk_level = "high"
                else:
                    sanitized_data[field_name] = field_result.sanitized_data
            
            # Check for suspicious patterns
            security_check = self._check_security_patterns(data)
            if not security_check.is_valid:
                errors.extend(security_check.errors)
                risk_level = "critical"
            
            # Log security events
            if errors or risk_level != "low":
                self._log_security_event(data, errors, risk_level)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                sanitized_data=sanitized_data if len(errors) == 0 else None,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation system error: {str(e)}"],
                risk_level="critical"
            )
    
    def _validate_field(self, field_name: str, value: Any, field_type: str) -> ValidationResult:
        """Validate individual field"""
        errors = []
        risk_level = "low"
        
        # Convert to string for validation
        str_value = str(value) if value is not None else ""
        
        # Check length limits
        max_length = self.MAX_LENGTHS.get(field_name, 1000)
        if len(str_value) > max_length:
            errors.append(f"Field '{field_name}' exceeds maximum length of {max_length}")
            risk_level = "medium"
        
        # Type-specific validation
        if field_type == "patient_id":
            if not self.PATTERNS['patient_id'].match(str_value):
                errors.append(f"Invalid patient ID format: {field_name}")
                risk_level = "high"
        
        elif field_type == "email":
            if not self.PATTERNS['email'].match(str_value):
                errors.append(f"Invalid email format: {field_name}")
        
        elif field_type == "research_id":
            if not self.PATTERNS['research_id'].match(str_value):
                errors.append(f"Invalid research ID format: {field_name}")
        
        elif field_type == "safe_text":
            if not self.PATTERNS['safe_text'].match(str_value):
                errors.append(f"Field '{field_name}' contains unsafe characters")
                risk_level = "medium"
        
        elif field_type == "alphanumeric":
            if not self.PATTERNS['alphanumeric'].match(str_value):
                errors.append(f"Field '{field_name}' must be alphanumeric")
        
        # Sanitize the value
        sanitized_value = self._sanitize_value(str_value, field_type)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_data=sanitized_value,
            risk_level=risk_level
        )
    
    def _sanitize_value(self, value: str, field_type: str) -> str:
        """Sanitize input value based on type"""
        if not value:
            return value
        
        # HTML escape for safety
        sanitized = html.escape(value)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        # Type-specific sanitization
        if field_type in ["patient_id", "research_id", "agent_id"]:
            # Keep only allowed characters
            sanitized = re.sub(r'[^A-Za-z0-9_-]', '', sanitized)
        
        elif field_type == "email":
            # Basic email sanitization
            sanitized = sanitized.lower().strip()
        
        return sanitized
    
    def _check_security_patterns(self, data: Dict[str, Any]) -> ValidationResult:
        """Check for dangerous security patterns"""
        errors = []
        
        # Convert all data to string for pattern matching
        data_str = json.dumps(data, default=str).lower()
        
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(data_str):
                errors.append(f"Dangerous pattern detected: {pattern.pattern}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            risk_level="critical" if errors else "low"
        )
    
    def _log_security_event(self, data: Dict[str, Any], errors: List[str], risk_level: str):
        """Log security validation events"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'validation_failure',
            'risk_level': risk_level,
            'errors': errors,
            'data_hash': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
            'source_ip': data.get('source_ip', 'unknown')
        }
        
        self.security_events.append(event)
        logger.warning(f"Security validation event: {event}")
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_sensitive_data(self, data: str, salt: Optional[str] = None) -> str:
        """Hash sensitive data with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{data}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get_security_events(self, since: Optional[datetime] = None) -> List[Dict]:
        """Get security events since specified time"""
        if since is None:
            return self.security_events
        
        since_str = since.isoformat()
        return [
            event for event in self.security_events
            if event['timestamp'] >= since_str
        ]

# Validation schemas for different data types
VALIDATION_SCHEMAS = {
    'patient_consent': {
        'patient_id*': 'patient_id',
        'data_types*': 'list',
        'research_categories*': 'list',
        'consent_status*': 'boolean',
        'expiry_date': 'datetime'
    },
    
    'research_query': {
        'researcher_id*': 'research_id',
        'query_text*': 'safe_text',
        'study_description*': 'safe_text',
        'data_requirements*': 'dict',
        'ethical_approval_id': 'alphanumeric'
    },
    
    'data_request': {
        'requester_id*': 'research_id',
        'patient_id*': 'patient_id',
        'data_type*': 'alphanumeric',
        'research_category*': 'alphanumeric',
        'purpose*': 'safe_text'
    },
    
    'chat_message': {
        'session_id*': 'alphanumeric',
        'user_id*': 'patient_id',
        'message_content*': 'safe_text',
        'message_type': 'alphanumeric'
    }
}

# Global validator instance
security_validator = SecurityValidator()