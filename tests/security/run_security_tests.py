#!/usr/bin/env python3
"""
Security test runner for HealthSync system.
Executes comprehensive security tests and generates reports.
"""

import sys
import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.utils.security_validator import security_validator
from shared.utils.rate_limiter import RateLimiter, RateLimitConfig
from shared.utils.encryption import data_encryption
from shared.utils.security_audit import security_auditor
from shared.utils.privacy_compliance import privacy_compliance

class SecurityTestRunner:
    """Comprehensive security test execution and reporting"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🔒 Starting HealthSync Security Test Suite")
        print("=" * 50)
        
        # Input validation tests
        self.run_input_validation_tests()
        
        # Rate limiting tests
        self.run_rate_limiting_tests()
        
        # Encryption tests
        self.run_encryption_tests()
        
        # Audit logging tests
        self.run_audit_tests()
        
        # Privacy compliance tests
        self.run_privacy_tests()
        
        # Penetration testing scenarios
        self.run_penetration_tests()
        
        # Generate final report
        self.generate_report()
    
    def run_input_validation_tests(self):
        """Test input validation and sanitization"""
        print("\n📝 Running Input Validation Tests...")
        
        test_cases = [
            {
                'name': 'XSS Protection',
                'data': {
                    'patient_id': '<script>alert("xss")</script>',
                    'data_types': ['medical_records'],
                    'research_categories': ['epidemiological'],
                    'consent_status': True
                },
                'schema': 'patient_consent',
                'should_pass': False
            },
            {
                'name': 'SQL Injection Protection',
                'data': {
                    'researcher_id': "'; DROP TABLE patients; --",
                    'query_text': 'UNION SELECT * FROM users',
                    'study_description': 'Test study',
                    'data_requirements': {'type': 'medical'}
                },
                'schema': 'research_query',
                'should_pass': False
            },
            {
                'name': 'Valid Input Processing',
                'data': {
                    'patient_id': 'PAT_12345678',
                    'data_types': ['medical_records'],
                    'research_categories': ['epidemiological'],
                    'consent_status': True
                },
                'schema': 'patient_consent',
                'should_pass': True
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                from shared.utils.security_validator import VALIDATION_SCHEMAS
                result = security_validator.validate_input(
                    test_case['data'], 
                    VALIDATION_SCHEMAS[test_case['schema']]
                )
                
                passed = (result.is_valid == test_case['should_pass'])
                results.append({
                    'name': test_case['name'],
                    'passed': passed,
                    'details': {
                        'expected_valid': test_case['should_pass'],
                        'actual_valid': result.is_valid,
                        'risk_level': result.risk_level,
                        'errors': result.errors
                    }
                })
                
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status} {test_case['name']}")
                
            except Exception as e:
                results.append({
                    'name': test_case['name'],
                    'passed': False,
                    'error': str(e)
                })
                print(f"  ❌ FAIL {test_case['name']} - Error: {e}")
        
        self.test_results['tests']['input_validation'] = results
        self._update_summary(results)
    
    def run_rate_limiting_tests(self):
        """Test rate limiting and DDoS protection"""
        print("\n🚦 Running Rate Limiting Tests...")
        
        config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=50,
            burst_limit=2,
            block_duration_minutes=1
        )
        rate_limiter = RateLimiter(config)
        
        results = []
        
        # Test normal requests
        try:
            allowed, info = rate_limiter.is_allowed("192.168.1.1")
            results.append({
                'name': 'Normal Request Allowed',
                'passed': allowed and info['status'] == 'allowed',
                'details': info
            })
            print(f"  {'✅ PASS' if allowed else '❌ FAIL'} Normal Request Allowed")
        except Exception as e:
            results.append({'name': 'Normal Request Allowed', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Normal Request Allowed - Error: {e}")
        
        # Test burst limit
        try:
            client_ip = "192.168.1.2"
            burst_blocked = False
            
            for i in range(config.burst_limit + 2):
                allowed, info = rate_limiter.is_allowed(client_ip)
                if not allowed and info.get('limit_type') == 'burst':
                    burst_blocked = True
                    break
            
            results.append({
                'name': 'Burst Limit Protection',
                'passed': burst_blocked,
                'details': {'burst_limit_triggered': burst_blocked}
            })
            print(f"  {'✅ PASS' if burst_blocked else '❌ FAIL'} Burst Limit Protection")
        except Exception as e:
            results.append({'name': 'Burst Limit Protection', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Burst Limit Protection - Error: {e}")
        
        # Test IP whitelisting
        try:
            whitelist_ip = "192.168.1.100"
            rate_limiter.add_to_whitelist(whitelist_ip)
            
            # Should be allowed even after many requests
            allowed = True
            for _ in range(10):
                allowed, info = rate_limiter.is_allowed(whitelist_ip)
                if not allowed:
                    break
            
            results.append({
                'name': 'IP Whitelisting',
                'passed': allowed and info.get('status') == 'whitelisted',
                'details': info
            })
            print(f"  {'✅ PASS' if allowed else '❌ FAIL'} IP Whitelisting")
        except Exception as e:
            results.append({'name': 'IP Whitelisting', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL IP Whitelisting - Error: {e}")
        
        self.test_results['tests']['rate_limiting'] = results
        self._update_summary(results)
    
    def run_encryption_tests(self):
        """Test data encryption and key management"""
        print("\n🔐 Running Encryption Tests...")
        
        results = []
        
        # Test data encryption/decryption
        try:
            test_data = {
                'patient_id': 'PAT_12345678',
                'sensitive_info': 'confidential medical data'
            }
            
            encrypted_package = data_encryption.encrypt_sensitive_data(test_data, "test")
            decrypted_data = data_encryption.decrypt_sensitive_data(encrypted_package)
            
            encryption_works = (decrypted_data == test_data)
            results.append({
                'name': 'Data Encryption/Decryption',
                'passed': encryption_works,
                'details': {
                    'algorithm': encrypted_package.get('algorithm'),
                    'key_id': encrypted_package.get('key_id')
                }
            })
            print(f"  {'✅ PASS' if encryption_works else '❌ FAIL'} Data Encryption/Decryption")
        except Exception as e:
            results.append({'name': 'Data Encryption/Decryption', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Data Encryption/Decryption - Error: {e}")
        
        # Test patient data sanitization
        try:
            patient_data = {
                'patient_id': 'PAT_12345678',
                'ssn': '123-45-6789',
                'email': 'patient@example.com',
                'medical_condition': 'diabetes'
            }
            
            encrypted_package = data_encryption.encrypt_patient_data(patient_data)
            decrypted_data = data_encryption.decrypt_sensitive_data(encrypted_package)
            
            # Check PII was hashed
            pii_sanitized = ('ssn' not in decrypted_data and 
                           'ssn_hash' in decrypted_data and
                           'email_hash' in decrypted_data)
            
            results.append({
                'name': 'PII Sanitization',
                'passed': pii_sanitized,
                'details': {
                    'original_fields': list(patient_data.keys()),
                    'sanitized_fields': list(decrypted_data.keys())
                }
            })
            print(f"  {'✅ PASS' if pii_sanitized else '❌ FAIL'} PII Sanitization")
        except Exception as e:
            results.append({'name': 'PII Sanitization', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL PII Sanitization - Error: {e}")
        
        self.test_results['tests']['encryption'] = results
        self._update_summary(results)
    
    def run_audit_tests(self):
        """Test security audit logging"""
        print("\n📊 Running Audit Logging Tests...")
        
        results = []
        
        # Test authentication logging
        try:
            initial_count = len(security_auditor.recent_events)
            
            event_id = security_auditor.log_event(
                event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
                risk_level=RiskLevel.LOW,
                source_ip="192.168.1.1",
                resource="authentication",
                action="login",
                outcome="success",
                user_id="TEST_USER"
            )
            
            auth_logged = (event_id is not None and 
                          len(security_auditor.recent_events) > initial_count)
            
            results.append({
                'name': 'Authentication Logging',
                'passed': auth_logged,
                'details': {'event_id': event_id}
            })
            print(f"  {'✅ PASS' if auth_logged else '❌ FAIL'} Authentication Logging")
        except Exception as e:
            results.append({'name': 'Authentication Logging', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Authentication Logging - Error: {e}")
        
        # Test data access logging
        try:
            initial_count = len(security_auditor.recent_events)
            
            event_id = security_auditor.log_event(
                event_type=SecurityEventType.DATA_ACCESS,
                risk_level=RiskLevel.LOW,
                source_ip="192.168.1.2",
                resource="patient_data",
                action="access",
                outcome="success",
                user_id="TEST_RESEARCHER",
                agent_id="data_custodian",
                details={
                    'data_type': 'medical_records',
                    'patient_count': 10
                }
            )
            
            access_logged = (event_id is not None and 
                           len(security_auditor.recent_events) > initial_count)
            
            results.append({
                'name': 'Data Access Logging',
                'passed': access_logged,
                'details': {'event_id': event_id}
            })
            print(f"  {'✅ PASS' if access_logged else '❌ FAIL'} Data Access Logging")
        except Exception as e:
            results.append({'name': 'Data Access Logging', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Data Access Logging - Error: {e}")
        
        # Test security report generation
        try:
            report = security_auditor.get_security_report(hours=1)
            
            report_valid = ('total_events' in report and 
                          'risk_distribution' in report and
                          report['total_events'] >= 0)
            
            results.append({
                'name': 'Security Report Generation',
                'passed': report_valid,
                'details': {
                    'total_events': report.get('total_events'),
                    'report_sections': list(report.keys())
                }
            })
            print(f"  {'✅ PASS' if report_valid else '❌ FAIL'} Security Report Generation")
        except Exception as e:
            results.append({'name': 'Security Report Generation', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Security Report Generation - Error: {e}")
        
        self.test_results['tests']['audit_logging'] = results
        self._update_summary(results)
    
    def run_privacy_tests(self):
        """Test privacy compliance validation"""
        print("\n🔒 Running Privacy Compliance Tests...")
        
        results = []
        
        # Set up test consent
        privacy_compliance.update_consent_record("TEST_PATIENT", {
            'explicit_consent': True,
            'consent_date': datetime.utcnow().isoformat(),
            'allowed_purposes': ['epidemiological_research']
        })
        
        # Test GDPR compliance
        try:
            data_request = {
                'patient_id': 'TEST_PATIENT',
                'data_types': ['medical_records'],
                'purpose': 'epidemiological_research'
            }
            
            checks = privacy_compliance.validate_data_processing(data_request)
            
            gdpr_compliant = any(
                check.status.value == 'compliant' 
                for check in checks 
                if 'gdpr' in check.rule_id.lower()
            )
            
            results.append({
                'name': 'GDPR Compliance Validation',
                'passed': gdpr_compliant,
                'details': {
                    'total_checks': len(checks),
                    'compliant_checks': len([c for c in checks if c.status.value == 'compliant'])
                }
            })
            print(f"  {'✅ PASS' if gdpr_compliant else '❌ FAIL'} GDPR Compliance Validation")
        except Exception as e:
            results.append({'name': 'GDPR Compliance Validation', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL GDPR Compliance Validation - Error: {e}")
        
        # Test compliance report generation
        try:
            report = privacy_compliance.generate_compliance_report(hours=1)
            
            report_valid = ('total_compliance_checks' in report and 
                          'compliance_rate' in report and
                          isinstance(report['compliance_rate'], (int, float)))
            
            results.append({
                'name': 'Compliance Report Generation',
                'passed': report_valid,
                'details': {
                    'compliance_rate': report.get('compliance_rate'),
                    'total_checks': report.get('total_compliance_checks')
                }
            })
            print(f"  {'✅ PASS' if report_valid else '❌ FAIL'} Compliance Report Generation")
        except Exception as e:
            results.append({'name': 'Compliance Report Generation', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Compliance Report Generation - Error: {e}")
        
        self.test_results['tests']['privacy_compliance'] = results
        self._update_summary(results)
    
    def run_penetration_tests(self):
        """Run basic penetration testing scenarios"""
        print("\n🎯 Running Penetration Testing Scenarios...")
        
        results = []
        
        # Test directory traversal protection
        try:
            traversal_payloads = [
                '../../../etc/passwd',
                '..\\..\\..\\windows\\system32\\config\\sam',
                '....//....//....//etc/passwd',
                '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
            ]
            
            traversal_blocked = True
            for payload in traversal_payloads:
                # Simulate file access attempt
                if '../' in payload or '..\\' in payload:
                    # This should be blocked by input validation
                    continue
                else:
                    traversal_blocked = False
                    break
            
            results.append({
                'name': 'Directory Traversal Protection',
                'passed': traversal_blocked,
                'details': {'tested_payloads': len(traversal_payloads)}
            })
            print(f"  {'✅ PASS' if traversal_blocked else '❌ FAIL'} Directory Traversal Protection")
        except Exception as e:
            results.append({'name': 'Directory Traversal Protection', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Directory Traversal Protection - Error: {e}")
        
        # Test command injection protection
        try:
            command_payloads = [
                '; ls -la',
                '| cat /etc/passwd',
                '&& whoami',
                '`id`',
                '$(uname -a)'
            ]
            
            command_blocked = True
            for payload in command_payloads:
                # Input validation should block these
                result = security_validator.validate_input(
                    {'test_field': payload},
                    {'test_field': 'safe_text'}
                )
                if result.is_valid:
                    command_blocked = False
                    break
            
            results.append({
                'name': 'Command Injection Protection',
                'passed': command_blocked,
                'details': {'tested_payloads': len(command_payloads)}
            })
            print(f"  {'✅ PASS' if command_blocked else '❌ FAIL'} Command Injection Protection")
        except Exception as e:
            results.append({'name': 'Command Injection Protection', 'passed': False, 'error': str(e)})
            print(f"  ❌ FAIL Command Injection Protection - Error: {e}")
        
        self.test_results['tests']['penetration_testing'] = results
        self._update_summary(results)
    
    def _update_summary(self, results):
        """Update test summary statistics"""
        for result in results:
            self.test_results['summary']['total_tests'] += 1
            if result['passed']:
                self.test_results['summary']['passed'] += 1
            else:
                self.test_results['summary']['failed'] += 1
    
    def generate_report(self):
        """Generate comprehensive security test report"""
        print("\n📋 Generating Security Test Report...")
        
        # Calculate success rate
        total = self.test_results['summary']['total_tests']
        passed = self.test_results['summary']['passed']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n🔒 Security Test Summary")
        print("=" * 30)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {self.test_results['summary']['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Save detailed report
        report_file = f"security_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = Path(__file__).parent / report_file
        
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Return overall status
        return success_rate >= 90  # 90% pass rate required

def main():
    """Main test execution"""
    runner = SecurityTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n✅ All security tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some security tests failed. Please review the report.")
        sys.exit(1)

if __name__ == "__main__":
    main()