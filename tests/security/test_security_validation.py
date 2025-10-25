"""
Security validation tests for HealthSync system.
Tests input validation, sanitization, and security controls.
"""

import pytest
import json
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from shared.utils.security_validator import (
    SecurityValidator, ValidationResult, VALIDATION_SCHEMAS, security_validator
)
from shared.utils.rate_limiter import (
    RateLimiter, RateLimitConfig, TokenBucket, SlidingWindowCounter, 
    DDoSProtection, DEFAULT_RATE_LIMITS
)
from shared.utils.encryption import (
    DataEncryption, KeyManager, EncryptionConfig, AsymmetricEncryption, SecureStorage
)
from shared.utils.security_audit import (
    SecurityAuditor, SecurityEventType, RiskLevel, security_auditor
)
from shared.utils.privacy_compliance import (
    PrivacyComplianceValidator, PrivacyRegulation, ComplianceStatus, privacy_compliance
)

class TestSecurityValidator:
    """Test security input validation and sanitization"""
    
    def setup_method(self):
        self.validator = SecurityValidator()
    
    def test_valid_patient_consent_data(self):
        """Test validation of valid patient consent data"""
        valid_data = {
            'patient_id': 'PAT_12345678',
            'data_types': ['medical_records', 'lab_results'],
            'research_categories': ['epidemiological', 'clinical_trial'],
            'consent_status': True,
            'expiry_date': '2025-12-31T23:59:59'
        }
        
        result = self.validator.validate_input(valid_data, VALIDATION_SCHEMAS['patient_consent'])
        
        assert result.is_valid
        assert result.risk_level == "low"
        assert len(result.errors) == 0
        assert result.sanitized_data is not None
    
    def test_invalid_patient_id_format(self):
        """Test validation with invalid patient ID format"""
        invalid_data = {
            'patient_id': 'invalid<script>alert("xss")</script>',
            'data_types': ['medical_records'],
            'research_categories': ['epidemiological'],
            'consent_status': True
        }
        
        result = self.validator.validate_input(invalid_data, VALIDATION_SCHEMAS['patient_consent'])
        
        assert not result.is_valid
        assert result.risk_level in ["medium", "high", "critical"]
        assert any("Invalid patient ID format" in error for error in result.errors)
    
    def test_xss_injection_detection(self):
        """Test detection of XSS injection attempts"""
        malicious_data = {
            'researcher_id': 'RES_12345678',
            'query_text': '<script>alert("xss")</script>',
            'study_description': 'javascript:void(0)',
            'data_requirements': {'type': 'medical'},
            'ethical_approval_id': 'ETH123'
        }
        
        result = self.validator.validate_input(malicious_data, VALIDATION_SCHEMAS['research_query'])
        
        assert not result.is_valid
        assert result.risk_level == "critical"
        assert any("Dangerous pattern detected" in error for error in result.errors)
    
    def test_sql_injection_detection(self):
        """Test detection of SQL injection attempts"""
        malicious_data = {
            'researcher_id': 'RES_12345678',
            'query_text': "'; DROP TABLE patients; --",
            'study_description': 'UNION SELECT * FROM users',
            'data_requirements': {'type': 'medical'},
            'ethical_approval_id': 'ETH123'
        }
        
        result = self.validator.validate_input(malicious_data, VALIDATION_SCHEMAS['research_query'])
        
        assert not result.is_valid
        assert result.risk_level == "critical"
    
    def test_field_length_limits(self):
        """Test field length validation"""
        oversized_data = {
            'patient_id': 'PAT_' + 'A' * 100,  # Exceeds 64 char limit
            'data_types': ['medical_records'],
            'research_categories': ['epidemiological'],
            'consent_status': True
        }
        
        result = self.validator.validate_input(oversized_data, VALIDATION_SCHEMAS['patient_consent'])
        
        assert not result.is_valid
        assert any("exceeds maximum length" in error for error in result.errors)
    
    def test_data_sanitization(self):
        """Test data sanitization functionality"""
        dirty_data = {
            'session_id': 'SES_123<>&"',
            'user_id': 'PAT_456\x00null',
            'message_content': '  Multiple   spaces   and\nnewlines  ',
            'message_type': 'consent_update'
        }
        
        result = self.validator.validate_input(dirty_data, VALIDATION_SCHEMAS['chat_message'])
        
        if result.is_valid:
            # Check sanitization
            assert '<' not in result.sanitized_data['session_id']
            assert '\x00' not in result.sanitized_data['user_id']
            assert '  ' not in result.sanitized_data['message_content']  # Normalized whitespace

class TestRateLimiter:
    """Test rate limiting and DDoS protection"""
    
    def setup_method(self):
        self.config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_limit=3,
            block_duration_minutes=1
        )
        self.rate_limiter = RateLimiter(self.config)
    
    def test_normal_request_allowed(self):
        """Test that normal requests are allowed"""
        allowed, info = self.rate_limiter.is_allowed("192.168.1.1")
        
        assert allowed
        assert info['status'] == 'allowed'
    
    def test_burst_limit_protection(self):
        """Test burst limit protection"""
        client_ip = "192.168.1.2"
        
        # Make requests up to burst limit
        for i in range(self.config.burst_limit):
            allowed, info = self.rate_limiter.is_allowed(client_ip)
            assert allowed
        
        # Next request should be rate limited
        allowed, info = self.rate_limiter.is_allowed(client_ip)
        assert not allowed
        assert info['status'] == 'rate_limited'
        assert info['limit_type'] == 'burst'
    
    def test_per_minute_limit(self):
        """Test per-minute rate limiting"""
        client_ip = "192.168.1.3"
        
        # Simulate requests over time to avoid burst limit
        for i in range(self.config.requests_per_minute + 1):
            time.sleep(0.1)  # Small delay to avoid burst limit
            allowed, info = self.rate_limiter.is_allowed(client_ip)
            
            if i < self.config.requests_per_minute:
                assert allowed or info.get('limit_type') == 'burst'  # May hit burst first
            else:
                if not allowed:
                    assert info['limit_type'] in ['minute', 'burst']
    
    def test_ip_whitelisting(self):
        """Test IP whitelisting functionality"""
        whitelisted_ip = "192.168.1.100"
        self.rate_limiter.add_to_whitelist(whitelisted_ip)
        
        # Whitelisted IP should always be allowed
        for _ in range(20):  # Exceed normal limits
            allowed, info = self.rate_limiter.is_allowed(whitelisted_ip)
            assert allowed
            assert info['status'] == 'whitelisted'
    
    def test_ddos_protection(self):
        """Test DDoS protection mechanisms"""
        ddos_protection = DDoSProtection(self.rate_limiter)
        
        # Simulate high-frequency requests
        analysis = ddos_protection.analyze_request(
            client_ip="192.168.1.4",
            user_agent="AttackBot/1.0",
            request_size=1000000,  # 1MB request
            endpoint="/api/data"
        )
        
        assert analysis['threat_level'] in ['medium', 'high']
        assert len(analysis['alerts']) > 0

class TestEncryption:
    """Test data encryption and key management"""
    
    def setup_method(self):
        self.config = EncryptionConfig()
        self.key_manager = KeyManager(self.config)
        self.encryption = DataEncryption(self.key_manager)
    
    def test_data_encryption_decryption(self):
        """Test basic data encryption and decryption"""
        test_data = {
            'patient_id': 'PAT_12345678',
            'medical_data': 'sensitive information'
        }
        
        # Encrypt data
        encrypted_package = self.encryption.encrypt_sensitive_data(test_data, "test_data")
        
        assert 'encrypted_data' in encrypted_package
        assert 'key_id' in encrypted_package
        assert encrypted_package['algorithm'] == 'Fernet-AES256'
        
        # Decrypt data
        decrypted_data = self.encryption.decrypt_sensitive_data(encrypted_package)
        
        assert decrypted_data == test_data
    
    def test_patient_data_sanitization(self):
        """Test patient data sanitization before encryption"""
        patient_data = {
            'patient_id': 'PAT_12345678',
            'ssn': '123-45-6789',
            'email': 'patient@example.com',
            'medical_condition': 'diabetes'
        }
        
        encrypted_package = self.encryption.encrypt_patient_data(patient_data)
        decrypted_data = self.encryption.decrypt_sensitive_data(encrypted_package)
        
        # Check that PII was hashed
        assert 'ssn' not in decrypted_data
        assert 'ssn_hash' in decrypted_data
        assert 'email_hash' in decrypted_data
        assert decrypted_data['medical_condition'] == 'diabetes'  # Non-PII preserved
    
    def test_key_rotation(self):
        """Test encryption key rotation"""
        original_key_id = self.key_manager.current_key_id
        
        # Rotate keys
        self.key_manager.rotate_keys()
        
        # Should have new current key
        assert self.key_manager.current_key_id != original_key_id
        
        # Old key should still be available for decryption
        assert self.key_manager.get_key(original_key_id) is not None

class TestSecurityAudit:
    """Test security audit logging and monitoring"""
    
    def setup_method(self):
        self.auditor = SecurityAuditor()
    
    def test_authentication_logging(self):
        """Test authentication event logging"""
        event_id = self.auditor.log_authentication(
            user_id="PAT_12345678",
            source_ip="192.168.1.1",
            success=True,
            details={'method': 'password'}
        )
        
        assert event_id is not None
        assert len(self.auditor.recent_events) > 0
        
        # Check event details
        event = self.auditor.recent_events[-1]
        assert event.event_type == SecurityEventType.AUTHENTICATION_SUCCESS
        assert event.user_id == "PAT_12345678"
        assert event.outcome == "success"
    
    def test_data_access_logging(self):
        """Test data access event logging"""
        event_id = self.auditor.log_data_access(
            user_id="RES_12345678",
            agent_id="data_custodian",
            source_ip="192.168.1.2",
            resource="patient_data",
            data_type="medical_records",
            patient_count=100,
            success=True
        )
        
        assert event_id is not None
        
        event = self.auditor.recent_events[-1]
        assert event.event_type == SecurityEventType.DATA_ACCESS
        assert event.details['patient_count'] == 100
        assert event.details['data_type'] == "medical_records"
    
    def test_security_report_generation(self):
        """Test security report generation"""
        # Generate some test events
        self.auditor.log_authentication("PAT_1", "192.168.1.1", True)
        self.auditor.log_authentication("PAT_2", "192.168.1.2", False)
        
        report = self.auditor.get_security_report(hours=1)
        
        assert 'total_events' in report
        assert 'risk_distribution' in report
        assert 'event_type_distribution' in report
        assert report['total_events'] >= 2

class TestPrivacyCompliance:
    """Test privacy compliance validation"""
    
    def setup_method(self):
        self.validator = PrivacyComplianceValidator()
        
        # Set up test consent record
        self.validator.update_consent_record("PAT_12345678", {
            'explicit_consent': True,
            'consent_date': datetime.utcnow().isoformat(),
            'allowed_purposes': ['epidemiological_research', 'clinical_trials']
        })
    
    def test_gdpr_consent_validation(self):
        """Test GDPR explicit consent validation"""
        data_request = {
            'patient_id': 'PAT_12345678',
            'data_types': ['medical_records'],
            'purpose': 'epidemiological_research'
        }
        
        checks = self.validator.validate_data_processing(data_request)
        
        # Should have compliance checks
        assert len(checks) > 0
        
        # Find GDPR consent check
        gdpr_consent_checks = [
            check for check in checks 
            if check.regulation == PrivacyRegulation.GDPR and 'consent' in check.rule_id
        ]
        
        assert len(gdpr_consent_checks) > 0
        assert gdpr_consent_checks[0].status == ComplianceStatus.COMPLIANT
    
    def test_hipaa_minimum_necessary(self):
        """Test HIPAA minimum necessary validation"""
        data_request = {
            'patient_id': 'PAT_12345678',
            'data_types': ['medical_records'],
            'data_fields': ['age_group', 'diagnosis', 'outcome', 'unnecessary_field'],
            'purpose': 'epidemiological research'
        }
        
        checks = self.validator.validate_data_processing(data_request)
        
        # Find HIPAA minimum necessary check
        hipaa_checks = [
            check for check in checks 
            if check.regulation == PrivacyRegulation.HIPAA and 'minimum' in check.rule_id
        ]
        
        if hipaa_checks:
            # Should flag excessive fields
            assert hipaa_checks[0].status == ComplianceStatus.NON_COMPLIANT
            assert 'unnecessary_field' in hipaa_checks[0].details.get('excessive_fields', [])
    
    def test_compliance_report_generation(self):
        """Test compliance report generation"""
        # Generate test compliance checks
        data_request = {
            'patient_id': 'PAT_12345678',
            'data_types': ['medical_records'],
            'purpose': 'epidemiological_research'
        }
        
        self.validator.validate_data_processing(data_request)
        
        report = self.validator.generate_compliance_report(hours=1)
        
        assert 'total_compliance_checks' in report
        assert 'compliance_rate' in report
        assert 'regulation_statistics' in report

class TestSecurityIntegration:
    """Integration tests for security components"""
    
    def test_end_to_end_security_workflow(self):
        """Test complete security workflow"""
        # 1. Input validation
        validator = SecurityValidator()
        data = {
            'patient_id': 'PAT_12345678',
            'data_types': ['medical_records'],
            'research_categories': ['epidemiological'],
            'consent_status': True
        }
        
        validation_result = validator.validate_input(data, VALIDATION_SCHEMAS['patient_consent'])
        assert validation_result.is_valid
        
        # 2. Rate limiting check
        rate_limiter = RateLimiter(RateLimitConfig())
        allowed, info = rate_limiter.is_allowed("192.168.1.1")
        assert allowed
        
        # 3. Data encryption
        key_manager = KeyManager(EncryptionConfig())
        encryption = DataEncryption(key_manager)
        encrypted_data = encryption.encrypt_sensitive_data(data, "test")
        
        # 4. Security audit logging
        auditor = SecurityAuditor()
        event_id = auditor.log_data_access(
            user_id="PAT_12345678",
            agent_id="test_agent",
            source_ip="192.168.1.1",
            resource="patient_data",
            data_type="medical_records",
            patient_count=1,
            success=True
        )
        
        assert event_id is not None
        
        # 5. Privacy compliance check
        compliance_validator = PrivacyComplianceValidator()
        compliance_checks = compliance_validator.validate_data_processing(data)
        
        assert len(compliance_checks) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])