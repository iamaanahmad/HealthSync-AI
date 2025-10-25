"""
Integration tests for Privacy Agent.
Tests complete anonymization workflow with privacy compliance.
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.privacy.agent import PrivacyAgent
from agents.privacy.anonymization import AnonymizationEngine
from shared.protocols.agent_messages import AgentMessage, MessageTypes


class MockContext:
    """Mock uAgents Context for testing."""
    
    def __init__(self):
        self.agent = Mock()
        self.logger = Mock()


class TestPrivacyAgentIntegration:
    """Integration tests for Privacy Agent."""
    
    @pytest.fixture
    def privacy_agent(self):
        """Create Privacy Agent for testing."""
        return PrivacyAgent(
            port=8004,
            metta_agent_address="test_metta_address",
            k_anonymity=5,
            epsilon=1.0
        )
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        return MockContext()
    
    @pytest.fixture
    def sample_records(self):
        """Sample healthcare records for testing."""
        return [
            {
                "patient_id": "PATIENT-001",
                "ssn": "123-45-6789",
                "age": 25,
                "zipcode": "12345",
                "weight": 70.5,
                "diagnosis": "hypertension",
                "visit_date": "2024-01-15"
            },
            {
                "patient_id": "PATIENT-002", 
                "ssn": "234-56-7890",
                "age": 28,
                "zipcode": "12345",
                "weight": 68.2,
                "diagnosis": "diabetes",
                "visit_date": "2024-01-16"
            },
            {
                "patient_id": "PATIENT-003",
                "ssn": "345-67-8901", 
                "age": 32,
                "zipcode": "12345",
                "weight": 75.8,
                "diagnosis": "hypertension",
                "visit_date": "2024-01-17"
            },
            {
                "patient_id": "PATIENT-004",
                "ssn": "456-78-9012",
                "age": 29,
                "zipcode": "12345", 
                "weight": 72.1,
                "diagnosis": "diabetes",
                "visit_date": "2024-01-18"
            },
            {
                "patient_id": "PATIENT-005",
                "ssn": "567-89-0123",
                "age": 31,
                "zipcode": "12345",
                "weight": 69.7,
                "diagnosis": "hypertension", 
                "visit_date": "2024-01-19"
            }
        ]
    
    @pytest.fixture
    def anonymization_config(self):
        """Standard anonymization configuration."""
        return {
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
    
    @pytest.mark.asyncio
    async def test_anonymization_request_success(self, privacy_agent, mock_context, 
                                                sample_records, anonymization_config):
        """Test successful anonymization request processing."""
        # Create anonymization request message
        request_msg = AgentMessage(
            message_id="test-001",
            message_type=MessageTypes.ANONYMIZATION_REQUEST,
            sender_id="data_custodian_agent",
            recipient_id="privacy_agent",
            payload={
                "request_id": "REQ-001",
                "dataset_id": "DS-001", 
                "records": sample_records,
                "anonymization_config": anonymization_config,
                "requester_id": "RESEARCHER-001"
            },
            timestamp=datetime.now()
        )
        
        # Process the request
        response = await privacy_agent._handle_anonymization_request(
            mock_context, "data_custodian_agent", request_msg
        )
        
        # Verify response
        assert response["status"] == "success"
        assert response["request_id"] == "REQ-001"
        assert response["dataset_id"] == "DS-001"
        assert "anonymized_records" in response
        assert "metrics" in response
        assert "audit_id" in response
        assert response["compliance_verified"] is True
        
        # Verify anonymized records
        anonymized_records = response["anonymized_records"]
        assert len(anonymized_records) == len(sample_records)  # All records should be kept with k=5
        
        # Verify identifiers are hashed
        for record in anonymized_records:
            assert record["patient_id"] != sample_records[0]["patient_id"]
            assert record["patient_id_hashed"] is True
            assert record["ssn_hashed"] is True
        
        # Verify generalization
        for record in anonymized_records:
            assert record["age"] in ["20-29", "30-39"]
            assert record["zipcode"] == "123**"
        
        # Verify noise addition
        for record in anonymized_records:
            assert record["weight_noised"] is True
        
        # Verify statistics updated
        assert privacy_agent.stats["successful_anonymizations"] == 1
        assert privacy_agent.stats["total_records_anonymized"] == len(anonymized_records)
    
    def test_agent_initialization(self):
        """Test Privacy Agent initialization."""
        agent = PrivacyAgent(
            port=8004,
            metta_agent_address="test_metta",
            k_anonymity=7,
            epsilon=0.5
        )
        
        assert agent.anonymization_engine.k == 7
        assert agent.anonymization_engine.epsilon == 0.5
        assert agent.metta_agent_address == "test_metta"
        assert agent.stats["total_anonymization_requests"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])