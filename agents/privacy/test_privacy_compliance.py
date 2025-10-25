"""
Integration tests for privacy compliance and audit system.
Tests privacy rule evaluation, audit logging, and rule versioning.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .privacy_compliance import (
    PrivacyRule,
    PrivacyComplianceManager,
    PrivacyAuditLogger
)


class TestPrivacyRule:
    """Test privacy rule evaluation."""
    
    def test_rule_creation(self):
        """Test creating a privacy rule."""
        rule = PrivacyRule(
            rule_id="test_rule",
            rule_type="anonymization_requirement",
            conditions={"k_value": {"operator": "greater_than", "value": 4}},
            actions={"enforce": True}
        )
        
        assert rule.rule_id == "test_rule"
        assert rule.rule_type == "anonymization_requirement"
        assert rule.version == 1
    
    def test_rule_evaluation_conditions_met(self):
        """Test rule evaluation when conditions are met."""
        rule = PrivacyRule(
            rule_id="k_anonymity_check",
            rule_type="anonymization_requirement",
            conditions={"k_value": {"operator": "greater_than", "value": 4}},
            actions={"enforce": True, "message": "K-anonymity satisfied"}
        )
        
        context = {"k_value": 5}
        result = rule.evaluate(context)
        
        assert result["conditions_met"] is True
        assert len(result["failed_conditions"]) == 0
        assert result["actions"]["enforce"] is True
    
    def test_rule_evaluation_conditions_not_met(self):
        """Test rule evaluation when conditions are not met."""
        rule = PrivacyRule(
            rule_id="k_anonymity_check",
            rule_type="anonymization_requirement",
            conditions={"k_value": {"operator": "greater_than", "value": 4}},
            actions={"enforce": True}
        )
        
        context = {"k_value": 3}
        result = rule.evaluate(context)
        
        assert result["conditions_met"] is False
        assert "k_value" in result["failed_conditions"]
        assert result["actions"] == {}
    
    def test_rule_evaluation_multiple_conditions(self):
        """Test rule evaluation with multiple conditions."""
        rule = PrivacyRule(
            rule_id="complex_rule",
            rule_type="data_protection",
            conditions={
                "k_value": {"operator": "greater_than", "value": 4},
                "has_identifiers": True,
                "epsilon": {"operator": "greater_than", "value": 0}
            },
            actions={"enforce": True}
        )
        
        # All conditions met
        context = {"k_value": 5, "has_identifiers": True, "epsilon": 1.0}
        result = rule.evaluate(context)
        assert result["conditions_met"] is True
        
        # One condition not met
        context = {"k_value": 3, "has_identifiers": True, "epsilon": 1.0}
        result = rule.evaluate(context)
        assert result["conditions_met"] is False
        assert "k_value" in result["failed_conditions"]
    
    def test_rule_operators(self):
        """Test different rule operators."""
        # Test 'in' operator
        rule = PrivacyRule(
            rule_id="sensitivity_check",
            rule_type="data_protection",
            conditions={"data_sensitivity": {"operator": "in", "value": ["high", "critical"]}},
            actions={"suppress": True}
        )
        
        assert rule.evaluate({"data_sensitivity": "high"})["conditions_met"] is True
        assert rule.evaluate({"data_sensitivity": "low"})["conditions_met"] is False
        
        # Test 'less_than' operator
        rule = PrivacyRule(
            rule_id="epsilon_check",
            rule_type="privacy_budget",
            conditions={"epsilon": {"operator": "less_than", "value": 2.0}},
            actions={"warn": True}
        )
        
        assert rule.evaluate({"epsilon": 1.0})["conditions_met"] is True
        assert rule.evaluate({"epsilon": 3.0})["conditions_met"] is False


class TestPrivacyComplianceManager:
    """Test privacy compliance manager."""
    
    def test_initialization_with_default_rules(self):
        """Test that manager initializes with default rules."""
        manager = PrivacyComplianceManager()
        
        assert len(manager.privacy_rules) > 0
        assert "k_anonymity_minimum" in manager.privacy_rules
        assert "identifier_hashing_required" in manager.privacy_rules
    
    def test_add_custom_rule(self):
        """Test adding a custom privacy rule."""
        manager = PrivacyComplianceManager()
        initial_count = len(manager.privacy_rules)
        
        custom_rule = PrivacyRule(
            rule_id="custom_rule",
            rule_type="custom",
            conditions={"test": True},
            actions={"action": "test"}
        )
        
        manager.add_rule(custom_rule)
        
        assert len(manager.privacy_rules) == initial_count + 1
        assert "custom_rule" in manager.privacy_rules
    
    def test_evaluate_local_rules_compliant(self):
        """Test evaluating rules when data is compliant."""
        manager = PrivacyComplianceManager()
        
        records = [{"id": i} for i in range(10)]
        config = {
            "k_anonymity": 5,
            "identifier_fields": ["id"],
            "numeric_fields_for_noise": ["value"],
            "epsilon": 1.0,
            "data_sensitivity": "medium"
        }
        
        result = manager.evaluate_local_rules(records, config)
        
        assert result["compliant"] is True
        assert len(result["violations"]) == 0
        assert result["rules_evaluated"] > 0
    
    def test_evaluate_local_rules_violations(self):
        """Test evaluating rules when violations exist."""
        manager = PrivacyComplianceManager()
        
        records = [{"id": i} for i in range(10)]
        config = {
            "k_anonymity": 3,  # Violates minimum k=5 rule
            "identifier_fields": [],  # No identifiers when they exist
            "epsilon": 1.0
        }
        
        result = manager.evaluate_local_rules(records, config)
        
        assert result["compliant"] is False
        assert len(result["violations"]) > 0
    
    def test_update_privacy_rules(self):
        """Test updating privacy rules with versioning."""
        manager = PrivacyComplianceManager()
        initial_version = manager.current_version
        
        new_rules = {
            "new_rule_1": {
                "rule_type": "custom",
                "conditions": {"test": True},
                "actions": {"action": "test"}
            }
        }
        
        result = manager.update_privacy_rules(new_rules)
        
        assert result["version"] == initial_version + 1
        assert manager.current_version == initial_version + 1
        assert "new_rule_1" in manager.privacy_rules
    
    def test_update_privacy_rules_with_specific_version(self):
        """Test updating rules with a specific version number."""
        manager = PrivacyComplianceManager()
        
        new_rules = {
            "versioned_rule": {
                "rule_type": "custom",
                "conditions": {},
                "actions": {}
            }
        }
        
        result = manager.update_privacy_rules(new_rules, version=10)
        
        assert result["version"] == 10
        assert manager.current_version == 10
    
    def test_get_current_version(self):
        """Test getting current privacy rules version."""
        manager = PrivacyComplianceManager()
        
        version = manager.get_current_version()
        assert isinstance(version, int)
        assert version >= 1


class TestPrivacyAuditLogger:
    """Test privacy audit logging system."""
    
    def test_log_anonymization(self):
        """Test logging an anonymization operation."""
        logger = PrivacyAuditLogger()
        
        audit_entry = logger.log_anonymization(
            request_id="REQ-001",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity", "hashing", "noise_injection"],
            privacy_metrics={"retention_rate": 0.95}
        )
        
        assert audit_entry["audit_id"].startswith("AUDIT-")
        assert audit_entry["request_id"] == "REQ-001"
        assert audit_entry["dataset_id"] == "DS-001"
        assert audit_entry["original_record_count"] == 100
        assert audit_entry["anonymized_record_count"] == 95
        assert "verification_hash" in audit_entry
        assert audit_entry["verified"] is True
        assert len(logger.audit_logs) == 1
    
    def test_verification_hash_generation(self):
        """Test that verification hash is generated correctly."""
        logger = PrivacyAuditLogger()
        
        audit_entry = logger.log_anonymization(
            request_id="REQ-001",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        # Verification hash should be a 64-character hex string (SHA-256)
        assert len(audit_entry["verification_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in audit_entry["verification_hash"])
    
    def test_verify_audit_entry_valid(self):
        """Test verifying a valid audit entry."""
        logger = PrivacyAuditLogger()
        
        audit_entry = logger.log_anonymization(
            request_id="REQ-001",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        verification = logger.verify_audit_entry(audit_entry["audit_id"])
        
        assert verification["verified"] is True
        assert verification["audit_id"] == audit_entry["audit_id"]
        assert verification["stored_hash"] == verification["calculated_hash"]
    
    def test_verify_audit_entry_not_found(self):
        """Test verifying a non-existent audit entry."""
        logger = PrivacyAuditLogger()
        
        verification = logger.verify_audit_entry("AUDIT-NONEXISTENT")
        
        assert verification["verified"] is False
        assert "not found" in verification["message"]
    
    def test_verify_audit_entry_tampered(self):
        """Test detecting tampered audit entry."""
        logger = PrivacyAuditLogger()
        
        audit_entry = logger.log_anonymization(
            request_id="REQ-001",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        # Tamper with the audit log
        logger.audit_logs[0]["original_record_count"] = 200
        
        verification = logger.verify_audit_entry(audit_entry["audit_id"])
        
        assert verification["verified"] is False
        assert verification["stored_hash"] != verification["calculated_hash"]
    
    def test_get_audit_logs_no_filter(self):
        """Test retrieving all audit logs."""
        logger = PrivacyAuditLogger()
        
        # Create multiple audit entries
        for i in range(5):
            logger.log_anonymization(
                request_id=f"REQ-{i:03d}",
                dataset_id=f"DS-{i:03d}",
                requester_id="RESEARCHER-001",
                original_record_count=100,
                anonymized_record_count=95,
                techniques_applied=["k_anonymity"],
                privacy_metrics={}
            )
        
        logs = logger.get_audit_logs()
        
        assert len(logs) == 5
    
    def test_get_audit_logs_filter_by_request_id(self):
        """Test retrieving audit logs filtered by request ID."""
        logger = PrivacyAuditLogger()
        
        logger.log_anonymization(
            request_id="REQ-001",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        logger.log_anonymization(
            request_id="REQ-002",
            dataset_id="DS-002",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        logs = logger.get_audit_logs(request_id="REQ-001")
        
        assert len(logs) == 1
        assert logs[0]["request_id"] == "REQ-001"
    
    def test_get_audit_logs_filter_by_dataset_id(self):
        """Test retrieving audit logs filtered by dataset ID."""
        logger = PrivacyAuditLogger()
        
        logger.log_anonymization(
            request_id="REQ-001",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        logger.log_anonymization(
            request_id="REQ-002",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        logs = logger.get_audit_logs(dataset_id="DS-001")
        
        assert len(logs) == 2
        assert all(log["dataset_id"] == "DS-001" for log in logs)
    
    def test_get_audit_logs_filter_by_date_range(self):
        """Test retrieving audit logs filtered by date range."""
        logger = PrivacyAuditLogger()
        
        # Create audit entry
        logger.log_anonymization(
            request_id="REQ-001",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        # Filter with date range
        start_date = (datetime.now() - timedelta(hours=1)).isoformat()
        end_date = (datetime.now() + timedelta(hours=1)).isoformat()
        
        logs = logger.get_audit_logs(start_date=start_date, end_date=end_date)
        
        assert len(logs) == 1
    
    def test_calculate_privacy_metrics_report(self):
        """Test calculating aggregate privacy metrics."""
        logger = PrivacyAuditLogger()
        
        # Create multiple audit entries
        logger.log_anonymization(
            request_id="REQ-001",
            dataset_id="DS-001",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity", "hashing"],
            privacy_metrics={}
        )
        
        logger.log_anonymization(
            request_id="REQ-002",
            dataset_id="DS-002",
            requester_id="RESEARCHER-001",
            original_record_count=200,
            anonymized_record_count=180,
            techniques_applied=["k_anonymity", "noise_injection"],
            privacy_metrics={}
        )
        
        report = logger.calculate_privacy_metrics_report()
        
        assert report["total_anonymizations"] == 2
        assert report["total_original_records"] == 300
        assert report["total_anonymized_records"] == 275
        assert abs(report["average_retention_rate"] - (275/300)) < 0.01
        assert report["techniques_usage"]["k_anonymity"] == 2
        assert report["techniques_usage"]["hashing"] == 1
        assert report["techniques_usage"]["noise_injection"] == 1
    
    def test_calculate_privacy_metrics_report_empty(self):
        """Test calculating metrics report with no audit logs."""
        logger = PrivacyAuditLogger()
        
        report = logger.calculate_privacy_metrics_report()
        
        assert report["total_anonymizations"] == 0
        assert report["total_records_processed"] == 0
        assert report["average_retention_rate"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
