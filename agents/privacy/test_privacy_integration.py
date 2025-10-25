"""
Comprehensive integration tests for Privacy Agent compliance and audit system.
Tests privacy rule evaluation, audit logging, and rule versioning with MeTTa integration.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.privacy.agent import PrivacyAgent
from agents.privacy.privacy_compliance import PrivacyComplianceManager, PrivacyAuditLogger, PrivacyRule
from agents.privacy.anonymization import AnonymizationEngine
from shared.protocols.agent_messages import AgentMessage, MessageTypes


class TestPrivacyComplianceIntegration:
    """Integration tests for privacy compliance and audit system."""
    
    def test_privacy_agent_initialization_with_compliance_system(self):
        """Test that Privacy Agent initializes with all compliance components."""
        agent = PrivacyAgent(
            port=8004,
            metta_agent_address="test_metta_address",
            k_anonymity=5,
            epsilon=1.0
        )
        
        # Verify all components are initialized
        assert agent.anonymization_engine is not None
        assert agent.compliance_manager is not None
        assert agent.audit_logger is not None
        
        # Verify configuration
        assert agent.anonymization_engine.k == 5
        assert agent.anonymization_engine.epsilon == 1.0
        assert agent.metta_agent_address == "test_metta_address"
        
        # Verify default privacy rules are loaded
        assert len(agent.compliance_manager.privacy_rules) > 0
        assert "k_anonymity_minimum" in agent.compliance_manager.privacy_rules
        assert "identifier_hashing_required" in agent.compliance_manager.privacy_rules
    
    def test_privacy_rule_evaluation_with_compliant_data(self):
        """Test privacy rule evaluation with compliant data configuration."""
        manager = PrivacyComplianceManager()
        
        # Create compliant configuration
        records = [{"patient_id": f"P{i:03d}", "age": 25 + i} for i in range(10)]
        config = {
            "k_anonymity": 5,  # Meets minimum requirement
            "identifier_fields": ["patient_id"],  # Has identifiers to hash
            "numeric_fields_for_noise": ["age"],  # Has numeric fields
            "epsilon": 1.0,  # Valid epsilon
            "data_sensitivity": "medium"
        }
        
        result = manager.evaluate_local_rules(records, config)
        
        assert result["compliant"] is True
        assert len(result["violations"]) == 0
        assert result["rules_evaluated"] > 0
        assert "evaluation_timestamp" in result
    
    def test_privacy_rule_evaluation_with_violations(self):
        """Test privacy rule evaluation with multiple violations."""
        manager = PrivacyComplianceManager()
        
        # Create configuration with violations
        records = [{"patient_id": f"P{i:03d}"} for i in range(3)]
        config = {
            "k_anonymity": 3,  # Violates minimum k=5
            "identifier_fields": [],  # No hashing when identifiers exist
            "epsilon": 0,  # Invalid epsilon
            "data_sensitivity": "high"
        }
        
        result = manager.evaluate_local_rules(records, config)
        
        assert result["compliant"] is False
        assert len(result["violations"]) > 0
        
        # Check specific violations
        violation_rules = [v["rule_id"] for v in result["violations"]]
        assert "k_anonymity_minimum" in violation_rules
    
    def test_privacy_rules_versioning_and_updates(self):
        """Test privacy rules versioning and update mechanisms."""
        manager = PrivacyComplianceManager()
        initial_version = manager.get_current_version()
        
        # Add new privacy rules
        new_rules = {
            "genomic_data_protection": {
                "rule_type": "data_protection",
                "conditions": {
                    "data_type": {"operator": "equals", "value": "genomic"}
                },
                "actions": {
                    "require_advanced_anonymization": True,
                    "minimum_k": 10,
                    "message": "Genomic data requires k≥10 and advanced techniques"
                }
            },
            "rare_disease_protection": {
                "rule_type": "anonymization_requirement",
                "conditions": {
                    "diagnosis_category": {"operator": "in", "value": ["rare_disease", "genetic_disorder"]}
                },
                "actions": {
                    "suppress_diagnosis": True,
                    "message": "Rare disease diagnoses must be suppressed"
                }
            }
        }
        
        # Update rules with automatic versioning
        update_result = manager.update_privacy_rules(new_rules)
        
        assert update_result["version"] == initial_version + 1
        assert update_result["rule_count"] > len(new_rules)  # Includes existing rules
        assert manager.get_current_version() == initial_version + 1
        
        # Verify new rules are active
        assert "genomic_data_protection" in manager.privacy_rules
        assert "rare_disease_protection" in manager.privacy_rules
        
        # Update with specific version
        more_rules = {
            "international_transfer": {
                "rule_type": "compliance_requirement",
                "conditions": {
                    "transfer_destination": {"operator": "in", "value": ["EU", "UK", "Canada"]}
                },
                "actions": {
                    "require_gdpr_compliance": True,
                    "message": "International transfers require GDPR compliance"
                }
            }
        }
        
        update_result = manager.update_privacy_rules(more_rules, version=10)
        assert manager.get_current_version() == 10
    
    def test_audit_logging_with_cryptographic_verification(self):
        """Test comprehensive audit logging with cryptographic verification."""
        logger = PrivacyAuditLogger()
        
        # Log multiple anonymization operations
        audit_entries = []
        for i in range(5):
            entry = logger.log_anonymization(
                request_id=f"REQ-{i:03d}",
                dataset_id=f"DS-{i:03d}",
                requester_id=f"RESEARCHER-{i:03d}",
                original_record_count=100 + i * 10,
                anonymized_record_count=90 + i * 8,
                techniques_applied=["k_anonymity", "hashing", "generalization"],
                privacy_metrics={
                    "retention_rate": (90 + i * 8) / (100 + i * 10),
                    "k_value": 5,
                    "epsilon": 1.0
                }
            )
            audit_entries.append(entry)
        
        # Verify all entries are logged
        assert len(logger.audit_logs) == 5
        
        # Verify cryptographic verification for each entry
        for entry in audit_entries:
            verification = logger.verify_audit_entry(entry["audit_id"])
            assert verification["verified"] is True
            assert verification["stored_hash"] == verification["calculated_hash"]
        
        # Test tamper detection
        original_count = logger.audit_logs[0]["original_record_count"]
        logger.audit_logs[0]["original_record_count"] = 999  # Tamper with data
        
        verification = logger.verify_audit_entry(audit_entries[0]["audit_id"])
        assert verification["verified"] is False
        assert verification["stored_hash"] != verification["calculated_hash"]
        
        # Restore original data
        logger.audit_logs[0]["original_record_count"] = original_count
    
    def test_audit_log_filtering_and_retrieval(self):
        """Test audit log filtering and retrieval capabilities."""
        logger = PrivacyAuditLogger()
        
        # Create audit logs with different attributes
        base_time = datetime.now()
        
        # Logs for different requests
        logger.log_anonymization(
            request_id="REQ-ALPHA",
            dataset_id="DS-CARDIOLOGY",
            requester_id="RESEARCHER-001",
            original_record_count=100,
            anonymized_record_count=95,
            techniques_applied=["k_anonymity"],
            privacy_metrics={}
        )
        
        logger.log_anonymization(
            request_id="REQ-BETA",
            dataset_id="DS-CARDIOLOGY",
            requester_id="RESEARCHER-002",
            original_record_count=200,
            anonymized_record_count=180,
            techniques_applied=["k_anonymity", "noise_injection"],
            privacy_metrics={}
        )
        
        logger.log_anonymization(
            request_id="REQ-GAMMA",
            dataset_id="DS-ONCOLOGY",
            requester_id="RESEARCHER-001",
            original_record_count=150,
            anonymized_record_count=140,
            techniques_applied=["k_anonymity", "suppression"],
            privacy_metrics={}
        )
        
        # Test filtering by request ID
        alpha_logs = logger.get_audit_logs(request_id="REQ-ALPHA")
        assert len(alpha_logs) == 1
        assert alpha_logs[0]["request_id"] == "REQ-ALPHA"
        
        # Test filtering by dataset ID
        cardiology_logs = logger.get_audit_logs(dataset_id="DS-CARDIOLOGY")
        assert len(cardiology_logs) == 2
        assert all(log["dataset_id"] == "DS-CARDIOLOGY" for log in cardiology_logs)
        
        # Test filtering by date range
        start_date = (base_time - timedelta(minutes=5)).isoformat()
        end_date = (base_time + timedelta(minutes=5)).isoformat()
        
        recent_logs = logger.get_audit_logs(start_date=start_date, end_date=end_date)
        assert len(recent_logs) == 3  # All logs should be in this range
    
    def test_privacy_metrics_calculation_and_reporting(self):
        """Test privacy metrics calculation and aggregate reporting."""
        logger = PrivacyAuditLogger()
        
        # Create diverse audit logs
        test_data = [
            {
                "request_id": "REQ-001",
                "dataset_id": "DS-001",
                "requester_id": "RESEARCHER-001",
                "original_record_count": 1000,
                "anonymized_record_count": 950,
                "techniques_applied": ["k_anonymity", "hashing", "generalization"],
                "privacy_metrics": {"k_value": 5, "retention_rate": 0.95}
            },
            {
                "request_id": "REQ-002",
                "dataset_id": "DS-002",
                "requester_id": "RESEARCHER-002",
                "original_record_count": 500,
                "anonymized_record_count": 400,
                "techniques_applied": ["k_anonymity", "noise_injection"],
                "privacy_metrics": {"k_value": 7, "retention_rate": 0.80}
            },
            {
                "request_id": "REQ-003",
                "dataset_id": "DS-003",
                "requester_id": "RESEARCHER-001",
                "original_record_count": 2000,
                "anonymized_record_count": 1800,
                "techniques_applied": ["k_anonymity", "hashing", "suppression"],
                "privacy_metrics": {"k_value": 5, "retention_rate": 0.90}
            }
        ]
        
        for data in test_data:
            logger.log_anonymization(**data)
        
        # Calculate aggregate metrics
        report = logger.calculate_privacy_metrics_report()
        
        assert report["total_anonymizations"] == 3
        assert report["total_original_records"] == 3500  # 1000 + 500 + 2000
        assert report["total_anonymized_records"] == 3150  # 950 + 400 + 1800
        assert abs(report["average_retention_rate"] - (3150/3500)) < 0.01
        
        # Check technique usage statistics
        assert report["techniques_usage"]["k_anonymity"] == 3
        assert report["techniques_usage"]["hashing"] == 2
        assert report["techniques_usage"]["generalization"] == 1
        assert report["techniques_usage"]["noise_injection"] == 1
        assert report["techniques_usage"]["suppression"] == 1
    
    def test_end_to_end_privacy_compliance_workflow(self):
        """Test complete end-to-end privacy compliance workflow."""
        # Initialize Privacy Agent
        agent = PrivacyAgent(port=8004, k_anonymity=5, epsilon=1.0)
        
        # Sample healthcare data - designed to satisfy k=5 anonymity
        # Create 10 records with 2 groups of 5 each
        sample_records = []
        
        # Group 1: 5 records with age 30-39, zipcode 12345
        for i in range(5):
            sample_records.append({
                "patient_id": f"PATIENT-{i+1:03d}",
                "ssn": f"123-45-{i+1000:04d}",
                "age": 35,  # Same generalized age group
                "zipcode": "12345",
                "diagnosis": "hypertension",
                "weight": 70.0 + i,
                "visit_date": "2024-01-15"
            })
        
        # Group 2: 5 records with age 30-39, zipcode 54321
        for i in range(5):
            sample_records.append({
                "patient_id": f"PATIENT-{i+6:03d}",
                "ssn": f"234-56-{i+2000:04d}",
                "age": 37,  # Same generalized age group
                "zipcode": "54321",
                "diagnosis": "diabetes",
                "weight": 75.0 + i,
                "visit_date": "2024-01-16"
            })
        
        # Anonymization configuration
        config = {
            "identifier_fields": ["patient_id", "ssn"],
            "quasi_identifier_fields": ["age", "zipcode"],
            "generalization_rules": {
                "age": {"type": "age_bin", "bin_size": 10},
                "zipcode": {"type": "zipcode", "digits": 3},
                "visit_date": {"type": "date_precision", "precision": "month"}
            },
            "numeric_fields_for_noise": ["weight"],
            "k_anonymity_strategy": "suppress",
            "data_sensitivity": "high"
        }
        
        # Step 1: Evaluate privacy compliance
        compliance_result = agent.compliance_manager.evaluate_local_rules(sample_records, config)
        assert compliance_result["compliant"] is True
        
        # Step 2: Perform anonymization
        anonymized_records, metrics = agent.anonymization_engine.anonymize_dataset(
            sample_records, config
        )
        
        # Verify anonymization results
        assert len(anonymized_records) == len(sample_records)  # All records retained with k=5
        assert "cryptographic_hashing" in metrics["techniques_applied"]
        assert "data_generalization" in metrics["techniques_applied"]
        assert "k_anonymity" in metrics["techniques_applied"]
        assert "differential_privacy" in metrics["techniques_applied"]
        
        # Step 3: Log anonymization for audit
        audit_entry = agent.audit_logger.log_anonymization(
            request_id="REQ-E2E-001",
            dataset_id="DS-E2E-001",
            requester_id="RESEARCHER-E2E",
            original_record_count=len(sample_records),
            anonymized_record_count=len(anonymized_records),
            techniques_applied=metrics["techniques_applied"],
            privacy_metrics=metrics
        )
        
        # Step 4: Verify audit integrity
        verification = agent.audit_logger.verify_audit_entry(audit_entry["audit_id"])
        assert verification["verified"] is True
        
        # Step 5: Calculate privacy metrics
        privacy_metrics = agent.anonymization_engine.calculate_privacy_metrics(
            original_records=sample_records,
            anonymized_records=anonymized_records,
            quasi_identifier_fields=config["quasi_identifier_fields"]
        )
        
        assert privacy_metrics["k_anonymity"]["satisfies_k_anonymity"] is True
        assert privacy_metrics["data_utility"]["retention_rate"] == 1.0  # All records retained
        
        # Step 6: Generate compliance report
        compliance_report = agent.audit_logger.calculate_privacy_metrics_report()
        assert compliance_report["total_anonymizations"] >= 1
        assert compliance_report["total_original_records"] >= len(sample_records)
        
        print("End-to-end privacy compliance workflow completed successfully!")
        print(f"Anonymized {len(anonymized_records)} records with {len(metrics['techniques_applied'])} techniques")
        print(f"Audit entry: {audit_entry['audit_id']}")
        print(f"Privacy compliance verified: {verification['verified']}")
    
    def test_metta_integration_placeholder(self):
        """Test MeTTa integration placeholder for future implementation."""
        # This test verifies the integration points for MeTTa
        # In production, this would test actual MeTTa queries
        
        manager = PrivacyComplianceManager(metta_agent_address="test_metta_address")
        
        # Verify MeTTa address is stored
        assert manager.metta_agent_address == "test_metta_address"
        
        # Test local rule evaluation (fallback when MeTTa unavailable)
        records = [{"patient_id": "P001", "diagnosis": "rare_condition"}]
        config = {"k_anonymity": 5, "data_sensitivity": "critical"}
        
        result = manager.evaluate_local_rules(records, config)
        assert "compliant" in result
        assert "evaluation_timestamp" in result
        
        print("MeTTa integration points verified (using local fallback)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])