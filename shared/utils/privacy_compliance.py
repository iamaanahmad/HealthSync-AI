"""
Privacy compliance validation and reporting for HealthSync.
Implements GDPR, HIPAA, and other privacy regulation compliance checks.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import re

logger = logging.getLogger(__name__)

class PrivacyRegulation(Enum):
    """Supported privacy regulations"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    CCPA = "ccpa"
    PIPEDA = "pipeda"

class ComplianceStatus(Enum):
    """Compliance check status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    UNKNOWN = "unknown"

class DataCategory(Enum):
    """Categories of personal data"""
    BASIC_PERSONAL = "basic_personal"
    SENSITIVE_PERSONAL = "sensitive_personal"
    HEALTH_DATA = "health_data"
    BIOMETRIC_DATA = "biometric_data"
    GENETIC_DATA = "genetic_data"
    BEHAVIORAL_DATA = "behavioral_data"

@dataclass
class ComplianceRule:
    """Privacy compliance rule definition"""
    rule_id: str
    regulation: PrivacyRegulation
    data_category: DataCategory
    requirement: str
    validation_method: str
    severity: str  # critical, high, medium, low
    description: str

@dataclass
class ComplianceCheck:
    """Result of a compliance check"""
    rule_id: str
    status: ComplianceStatus
    data_subject: str
    data_category: DataCategory
    regulation: PrivacyRegulation
    details: Dict[str, Any]
    checked_at: datetime
    remediation_required: bool = False
    remediation_steps: List[str] = None

    def __post_init__(self):
        if self.remediation_steps is None:
            self.remediation_steps = []

class PrivacyComplianceValidator:
    """Main privacy compliance validation system"""
    
    def __init__(self):
        self.compliance_rules = self._load_compliance_rules()
        self.compliance_history = []
        self.data_inventory = {}
        self.consent_records = {}
        
    def _load_compliance_rules(self) -> Dict[str, ComplianceRule]:
        """Load privacy compliance rules"""
        rules = {}
        
        # GDPR Rules
        rules["gdpr_consent_001"] = ComplianceRule(
            rule_id="gdpr_consent_001",
            regulation=PrivacyRegulation.GDPR,
            data_category=DataCategory.HEALTH_DATA,
            requirement="Explicit consent required for health data processing",
            validation_method="check_explicit_consent",
            severity="critical",
            description="GDPR Article 9 requires explicit consent for health data"
        )
        
        rules["gdpr_purpose_002"] = ComplianceRule(
            rule_id="gdpr_purpose_002",
            regulation=PrivacyRegulation.GDPR,
            data_category=DataCategory.HEALTH_DATA,
            requirement="Data processing must be limited to specified purposes",
            validation_method="check_purpose_limitation",
            severity="high",
            description="GDPR Article 5(1)(b) purpose limitation principle"
        )
        
        rules["gdpr_retention_003"] = ComplianceRule(
            rule_id="gdpr_retention_003",
            regulation=PrivacyRegulation.GDPR,
            data_category=DataCategory.HEALTH_DATA,
            requirement="Data must not be kept longer than necessary",
            validation_method="check_retention_period",
            severity="medium",
            description="GDPR Article 5(1)(e) storage limitation principle"
        )
        
        rules["gdpr_anonymization_004"] = ComplianceRule(
            rule_id="gdpr_anonymization_004",
            regulation=PrivacyRegulation.GDPR,
            data_category=DataCategory.HEALTH_DATA,
            requirement="Anonymized data should not be re-identifiable",
            validation_method="check_anonymization_quality",
            severity="critical",
            description="GDPR Recital 26 on anonymization"
        )
        
        # HIPAA Rules
        rules["hipaa_minimum_001"] = ComplianceRule(
            rule_id="hipaa_minimum_001",
            regulation=PrivacyRegulation.HIPAA,
            data_category=DataCategory.HEALTH_DATA,
            requirement="Minimum necessary standard for PHI disclosure",
            validation_method="check_minimum_necessary",
            severity="critical",
            description="HIPAA Privacy Rule minimum necessary requirement"
        )
        
        rules["hipaa_authorization_002"] = ComplianceRule(
            rule_id="hipaa_authorization_002",
            regulation=PrivacyRegulation.HIPAA,
            data_category=DataCategory.HEALTH_DATA,
            requirement="Valid authorization required for PHI use/disclosure",
            validation_method="check_hipaa_authorization",
            severity="critical",
            description="HIPAA Privacy Rule authorization requirements"
        )
        
        rules["hipaa_deidentification_003"] = ComplianceRule(
            rule_id="hipaa_deidentification_003",
            regulation=PrivacyRegulation.HIPAA,
            data_category=DataCategory.HEALTH_DATA,
            requirement="Proper de-identification of PHI",
            validation_method="check_hipaa_deidentification",
            severity="high",
            description="HIPAA Safe Harbor or Expert Determination methods"
        )
        
        return rules
    
    def validate_data_processing(self, data_request: Dict[str, Any]) -> List[ComplianceCheck]:
        """
        Validate data processing request against privacy regulations
        
        Args:
            data_request: Data processing request details
            
        Returns:
            List of compliance check results
        """
        checks = []
        
        # Extract request details
        data_subject = data_request.get('patient_id', 'unknown')
        data_categories = self._identify_data_categories(data_request)
        processing_purpose = data_request.get('purpose', '')
        
        # Run compliance checks for each applicable regulation
        for regulation in [PrivacyRegulation.GDPR, PrivacyRegulation.HIPAA]:
            for data_category in data_categories:
                regulation_checks = self._run_regulation_checks(
                    regulation, data_category, data_subject, data_request
                )
                checks.extend(regulation_checks)
        
        # Store compliance history
        self.compliance_history.extend(checks)
        
        return checks
    
    def _identify_data_categories(self, data_request: Dict[str, Any]) -> Set[DataCategory]:
        """Identify data categories in the request"""
        categories = set()
        
        data_types = data_request.get('data_types', [])
        
        for data_type in data_types:
            if data_type.lower() in ['medical_records', 'diagnosis', 'treatment', 'lab_results']:
                categories.add(DataCategory.HEALTH_DATA)
            elif data_type.lower() in ['genetic', 'genomic', 'dna']:
                categories.add(DataCategory.GENETIC_DATA)
            elif data_type.lower() in ['biometric', 'fingerprint', 'facial']:
                categories.add(DataCategory.BIOMETRIC_DATA)
            elif data_type.lower() in ['behavior', 'activity', 'lifestyle']:
                categories.add(DataCategory.BEHAVIORAL_DATA)
            else:
                categories.add(DataCategory.SENSITIVE_PERSONAL)
        
        return categories
    
    def _run_regulation_checks(self, regulation: PrivacyRegulation, 
                              data_category: DataCategory, data_subject: str,
                              data_request: Dict[str, Any]) -> List[ComplianceCheck]:
        """Run compliance checks for specific regulation and data category"""
        checks = []
        
        # Find applicable rules
        applicable_rules = [
            rule for rule in self.compliance_rules.values()
            if rule.regulation == regulation and rule.data_category == data_category
        ]
        
        for rule in applicable_rules:
            check_result = self._execute_compliance_check(rule, data_subject, data_request)
            checks.append(check_result)
        
        return checks
    
    def _execute_compliance_check(self, rule: ComplianceRule, 
                                 data_subject: str, data_request: Dict[str, Any]) -> ComplianceCheck:
        """Execute individual compliance check"""
        
        # Route to specific validation method
        validation_methods = {
            'check_explicit_consent': self._check_explicit_consent,
            'check_purpose_limitation': self._check_purpose_limitation,
            'check_retention_period': self._check_retention_period,
            'check_anonymization_quality': self._check_anonymization_quality,
            'check_minimum_necessary': self._check_minimum_necessary,
            'check_hipaa_authorization': self._check_hipaa_authorization,
            'check_hipaa_deidentification': self._check_hipaa_deidentification
        }
        
        validation_func = validation_methods.get(rule.validation_method)
        if not validation_func:
            return ComplianceCheck(
                rule_id=rule.rule_id,
                status=ComplianceStatus.UNKNOWN,
                data_subject=data_subject,
                data_category=rule.data_category,
                regulation=rule.regulation,
                details={'error': f'Unknown validation method: {rule.validation_method}'},
                checked_at=datetime.utcnow()
            )
        
        return validation_func(rule, data_subject, data_request)
    
    def _check_explicit_consent(self, rule: ComplianceRule, data_subject: str, 
                               data_request: Dict[str, Any]) -> ComplianceCheck:
        """Check for explicit consent (GDPR)"""
        consent_data = self.consent_records.get(data_subject, {})
        
        # Check if explicit consent exists
        has_explicit_consent = consent_data.get('explicit_consent', False)
        consent_date = consent_data.get('consent_date')
        
        if has_explicit_consent and consent_date:
            # Check if consent is still valid (not expired)
            consent_dt = datetime.fromisoformat(consent_date)
            if datetime.utcnow() - consent_dt < timedelta(days=365):  # 1 year validity
                status = ComplianceStatus.COMPLIANT
                details = {'consent_valid': True, 'consent_date': consent_date}
                remediation_required = False
            else:
                status = ComplianceStatus.NON_COMPLIANT
                details = {'consent_expired': True, 'consent_date': consent_date}
                remediation_required = True
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = {'explicit_consent_missing': True}
            remediation_required = True
        
        return ComplianceCheck(
            rule_id=rule.rule_id,
            status=status,
            data_subject=data_subject,
            data_category=rule.data_category,
            regulation=rule.regulation,
            details=details,
            checked_at=datetime.utcnow(),
            remediation_required=remediation_required,
            remediation_steps=['Obtain explicit consent from data subject'] if remediation_required else []
        )
    
    def _check_purpose_limitation(self, rule: ComplianceRule, data_subject: str,
                                 data_request: Dict[str, Any]) -> ComplianceCheck:
        """Check purpose limitation compliance"""
        request_purpose = data_request.get('purpose', '')
        consent_data = self.consent_records.get(data_subject, {})
        allowed_purposes = consent_data.get('allowed_purposes', [])
        
        # Check if request purpose matches consented purposes
        purpose_match = any(
            purpose.lower() in request_purpose.lower() 
            for purpose in allowed_purposes
        )
        
        if purpose_match:
            status = ComplianceStatus.COMPLIANT
            details = {'purpose_authorized': True, 'matched_purposes': allowed_purposes}
            remediation_required = False
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = {
                'purpose_not_authorized': True,
                'request_purpose': request_purpose,
                'allowed_purposes': allowed_purposes
            }
            remediation_required = True
        
        return ComplianceCheck(
            rule_id=rule.rule_id,
            status=status,
            data_subject=data_subject,
            data_category=rule.data_category,
            regulation=rule.regulation,
            details=details,
            checked_at=datetime.utcnow(),
            remediation_required=remediation_required,
            remediation_steps=['Update consent to include new purpose'] if remediation_required else []
        )
    
    def _check_retention_period(self, rule: ComplianceRule, data_subject: str,
                               data_request: Dict[str, Any]) -> ComplianceCheck:
        """Check data retention period compliance"""
        # This is a simplified check - in practice, you'd check actual data age
        retention_policy = data_request.get('retention_days', 0)
        max_retention = 2555  # 7 years for health data
        
        if retention_policy <= max_retention:
            status = ComplianceStatus.COMPLIANT
            details = {'retention_compliant': True, 'retention_days': retention_policy}
            remediation_required = False
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = {
                'retention_excessive': True,
                'requested_days': retention_policy,
                'max_allowed_days': max_retention
            }
            remediation_required = True
        
        return ComplianceCheck(
            rule_id=rule.rule_id,
            status=status,
            data_subject=data_subject,
            data_category=rule.data_category,
            regulation=rule.regulation,
            details=details,
            checked_at=datetime.utcnow(),
            remediation_required=remediation_required,
            remediation_steps=['Reduce retention period to comply with policy'] if remediation_required else []
        )
    
    def _check_anonymization_quality(self, rule: ComplianceRule, data_subject: str,
                                    data_request: Dict[str, Any]) -> ComplianceCheck:
        """Check anonymization quality"""
        anonymization_method = data_request.get('anonymization_method', '')
        k_anonymity = data_request.get('k_anonymity', 0)
        
        # Check anonymization parameters
        has_proper_method = anonymization_method in ['k_anonymity', 'differential_privacy', 'generalization']
        has_sufficient_k = k_anonymity >= 5
        
        if has_proper_method and has_sufficient_k:
            status = ComplianceStatus.COMPLIANT
            details = {
                'anonymization_adequate': True,
                'method': anonymization_method,
                'k_anonymity': k_anonymity
            }
            remediation_required = False
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = {
                'anonymization_inadequate': True,
                'method': anonymization_method,
                'k_anonymity': k_anonymity,
                'min_k_required': 5
            }
            remediation_required = True
        
        return ComplianceCheck(
            rule_id=rule.rule_id,
            status=status,
            data_subject=data_subject,
            data_category=rule.data_category,
            regulation=rule.regulation,
            details=details,
            checked_at=datetime.utcnow(),
            remediation_required=remediation_required,
            remediation_steps=['Improve anonymization method', 'Increase k-anonymity value'] if remediation_required else []
        )
    
    def _check_minimum_necessary(self, rule: ComplianceRule, data_subject: str,
                                data_request: Dict[str, Any]) -> ComplianceCheck:
        """Check HIPAA minimum necessary standard"""
        requested_fields = data_request.get('data_fields', [])
        research_purpose = data_request.get('purpose', '')
        
        # Define necessary fields for different research purposes
        necessary_fields_map = {
            'epidemiological': ['age_group', 'diagnosis', 'outcome'],
            'clinical_trial': ['demographics', 'medical_history', 'treatment_response'],
            'quality_improvement': ['procedure_codes', 'outcomes', 'complications']
        }
        
        # Determine necessary fields based on purpose
        necessary_fields = []
        for purpose_type, fields in necessary_fields_map.items():
            if purpose_type in research_purpose.lower():
                necessary_fields.extend(fields)
        
        # Check if request exceeds minimum necessary
        excessive_fields = [
            field for field in requested_fields 
            if field not in necessary_fields and field not in ['patient_id', 'study_id']
        ]
        
        if not excessive_fields:
            status = ComplianceStatus.COMPLIANT
            details = {'minimum_necessary_met': True, 'requested_fields': requested_fields}
            remediation_required = False
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = {
                'excessive_fields_requested': True,
                'excessive_fields': excessive_fields,
                'necessary_fields': necessary_fields
            }
            remediation_required = True
        
        return ComplianceCheck(
            rule_id=rule.rule_id,
            status=status,
            data_subject=data_subject,
            data_category=rule.data_category,
            regulation=rule.regulation,
            details=details,
            checked_at=datetime.utcnow(),
            remediation_required=remediation_required,
            remediation_steps=['Remove unnecessary data fields from request'] if remediation_required else []
        )
    
    def _check_hipaa_authorization(self, rule: ComplianceRule, data_subject: str,
                                  data_request: Dict[str, Any]) -> ComplianceCheck:
        """Check HIPAA authorization requirements"""
        authorization_data = data_request.get('hipaa_authorization', {})
        
        required_elements = [
            'specific_information',
            'persons_authorized',
            'purpose_of_use',
            'expiration_date',
            'signature',
            'date_signed'
        ]
        
        missing_elements = [
            element for element in required_elements
            if element not in authorization_data or not authorization_data[element]
        ]
        
        if not missing_elements:
            # Check if authorization is not expired
            expiration_date = authorization_data.get('expiration_date')
            if expiration_date and datetime.fromisoformat(expiration_date) > datetime.utcnow():
                status = ComplianceStatus.COMPLIANT
                details = {'valid_authorization': True}
                remediation_required = False
            else:
                status = ComplianceStatus.NON_COMPLIANT
                details = {'authorization_expired': True}
                remediation_required = True
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = {'missing_authorization_elements': missing_elements}
            remediation_required = True
        
        return ComplianceCheck(
            rule_id=rule.rule_id,
            status=status,
            data_subject=data_subject,
            data_category=rule.data_category,
            regulation=rule.regulation,
            details=details,
            checked_at=datetime.utcnow(),
            remediation_required=remediation_required,
            remediation_steps=['Obtain complete HIPAA authorization'] if remediation_required else []
        )
    
    def _check_hipaa_deidentification(self, rule: ComplianceRule, data_subject: str,
                                     data_request: Dict[str, Any]) -> ComplianceCheck:
        """Check HIPAA de-identification compliance"""
        deidentification_method = data_request.get('deidentification_method', '')
        
        # HIPAA Safe Harbor identifiers that must be removed
        safe_harbor_identifiers = [
            'names', 'geographic_subdivisions', 'dates', 'telephone_numbers',
            'fax_numbers', 'email_addresses', 'ssn', 'medical_record_numbers',
            'health_plan_numbers', 'account_numbers', 'certificate_numbers',
            'vehicle_identifiers', 'device_identifiers', 'web_urls',
            'ip_addresses', 'biometric_identifiers', 'full_face_photos',
            'other_unique_identifiers'
        ]
        
        removed_identifiers = data_request.get('removed_identifiers', [])
        
        if deidentification_method == 'safe_harbor':
            missing_removals = [
                identifier for identifier in safe_harbor_identifiers
                if identifier not in removed_identifiers
            ]
            
            if not missing_removals:
                status = ComplianceStatus.COMPLIANT
                details = {'safe_harbor_compliant': True}
                remediation_required = False
            else:
                status = ComplianceStatus.NON_COMPLIANT
                details = {'missing_identifier_removals': missing_removals}
                remediation_required = True
        
        elif deidentification_method == 'expert_determination':
            expert_certification = data_request.get('expert_certification', False)
            
            if expert_certification:
                status = ComplianceStatus.COMPLIANT
                details = {'expert_determination_certified': True}
                remediation_required = False
            else:
                status = ComplianceStatus.NON_COMPLIANT
                details = {'expert_certification_missing': True}
                remediation_required = True
        
        else:
            status = ComplianceStatus.NON_COMPLIANT
            details = {'invalid_deidentification_method': deidentification_method}
            remediation_required = True
        
        return ComplianceCheck(
            rule_id=rule.rule_id,
            status=status,
            data_subject=data_subject,
            data_category=rule.data_category,
            regulation=rule.regulation,
            details=details,
            checked_at=datetime.utcnow(),
            remediation_required=remediation_required,
            remediation_steps=['Complete proper de-identification'] if remediation_required else []
        )
    
    def update_consent_record(self, patient_id: str, consent_data: Dict[str, Any]):
        """Update consent record for compliance tracking"""
        self.consent_records[patient_id] = consent_data
        logger.info(f"Updated consent record for patient: {patient_id}")
    
    def generate_compliance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate privacy compliance report"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent_checks = [
            check for check in self.compliance_history
            if check.checked_at >= cutoff
        ]
        
        # Calculate compliance statistics
        total_checks = len(recent_checks)
        compliant_checks = len([c for c in recent_checks if c.status == ComplianceStatus.COMPLIANT])
        non_compliant_checks = len([c for c in recent_checks if c.status == ComplianceStatus.NON_COMPLIANT])
        
        # Group by regulation
        regulation_stats = {}
        for regulation in PrivacyRegulation:
            reg_checks = [c for c in recent_checks if c.regulation == regulation]
            regulation_stats[regulation.value] = {
                'total': len(reg_checks),
                'compliant': len([c for c in reg_checks if c.status == ComplianceStatus.COMPLIANT]),
                'non_compliant': len([c for c in reg_checks if c.status == ComplianceStatus.NON_COMPLIANT])
            }
        
        # Critical violations requiring immediate attention
        critical_violations = [
            check for check in recent_checks
            if check.status == ComplianceStatus.NON_COMPLIANT and check.remediation_required
        ]
        
        return {
            'report_period_hours': hours,
            'total_compliance_checks': total_checks,
            'compliant_checks': compliant_checks,
            'non_compliant_checks': non_compliant_checks,
            'compliance_rate': (compliant_checks / total_checks * 100) if total_checks > 0 else 0,
            'regulation_statistics': regulation_stats,
            'critical_violations': len(critical_violations),
            'critical_violation_details': [asdict(v) for v in critical_violations[:10]],  # Top 10
            'generated_at': datetime.utcnow().isoformat()
        }

# Global privacy compliance validator
privacy_compliance = PrivacyComplianceValidator()