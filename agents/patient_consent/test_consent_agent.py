"""
Unit tests for Patient Consent Agent
Tests core consent management functionality including validation, expiration, and audit trails.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.patient_consent.agent import PatientConsentAgent, ConsentRecord
from shared.protocols.agent_messages import (
    ConsentMessage, ConsentQuery, AgentMessage, MessageTypes, ErrorCodes
)


class TestConsentRecord:
    """Test ConsentRecord class functionality."""
    
    def test_consent_record_creation(self):
        """Test creating a new consent record."""
        patient_id = "P001"
        data_types = ["medical_records", "lab_results"]
        research_categories = ["cancer_research", "diabetes_research"]
        expiry_date = datetime.utcnow() + timedelta(days=365)
        
        record = ConsentRecord(
            patient_id=patient_id,
            data_types=data_types,
            research_categories=research_categories,
            consent_status=True,
            expiry_date=expiry_date
        )
        
        assert record.patient_id == patient_id
        assert record.data_types == data_types
        assert record.research_categories == research_categories
        assert record.consent_status is True
        assert record.version == 1
        assert len(record.audit_trail) == 1
        assert record.audit_trail[0]["action"] == "created"
    
    def test_consent_id_generation(self):
        """Test that consent IDs are unique and properly formatted."""
        record1 = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        record2 = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        assert record1.consent_id != record2.consent_id
        assert record1.consent_id.startswith("CNS-")
        assert len(record1.consent_id) == 16  # CNS- + 12 hex chars
    
    def test_consent_is_valid(self):
        """Test consent validity checking."""
        # Valid consent
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        assert record.is_valid() is True
        
        # Expired consent
        expired_record = ConsentRecord(
            patient_id="P002",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() - timedelta(days=1)
        )
        assert expired_record.is_valid() is False
        assert expired_record.is_expired() is True
        
        # Revoked consent
        revoked_record = ConsentRecord(
            patient_id="P003",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=False,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        assert revoked_record.is_valid() is False
    
    def test_consent_update(self):
        """Test updating consent record."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        initial_version = record.version
        
        # Update consent
        updated = record.update_consent(
            consent_status=True,
            data_types=["medical_records", "lab_results"],
            research_categories=["cancer_research", "diabetes_research"]
        )
        
        assert updated is True
        assert record.version == initial_version + 1
        assert len(record.data_types) == 2
        assert len(record.research_categories) == 2
        assert len(record.audit_trail) == 2
        assert record.audit_trail[1]["action"] == "updated"
    
    def test_consent_renewal(self):
        """Test consent renewal."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=30)
        )
        
        initial_version = record.version
        initial_expiry = record.expiry_date
        
        # Renew consent
        new_expiry = record.renew_consent(duration_days=365)
        
        assert record.version == initial_version + 1
        assert new_expiry > initial_expiry
        assert len(record.audit_trail) == 2
        assert record.audit_trail[1]["action"] == "renewed"
    
    def test_consent_revocation(self):
        """Test consent revocation."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        assert record.is_valid() is True
        
        # Revoke consent
        record.revoke_consent()
        
        assert record.consent_status is False
        assert record.is_valid() is False
        assert len(record.audit_trail) == 2
        assert record.audit_trail[1]["action"] == "revoked"
    
    def test_check_permission_valid(self):
        """Test permission checking with valid consent."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records", "lab_results"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        granted, status = record.check_permission("medical_records", "cancer_research")
        assert granted is True
        assert status == "CONSENT_VALID"
    
    def test_check_permission_expired(self):
        """Test permission checking with expired consent."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() - timedelta(days=1)
        )
        
        granted, status = record.check_permission("medical_records", "cancer_research")
        assert granted is False
        assert status == ErrorCodes.CONSENT_EXPIRED
    
    def test_check_permission_revoked(self):
        """Test permission checking with revoked consent."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=False,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        granted, status = record.check_permission("medical_records", "cancer_research")
        assert granted is False
        assert status == ErrorCodes.CONSENT_REVOKED
    
    def test_check_permission_data_type_not_consented(self):
        """Test permission checking with non-consented data type."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        granted, status = record.check_permission("prescriptions", "cancer_research")
        assert granted is False
        assert status == "DATA_TYPE_NOT_CONSENTED"
    
    def test_check_permission_research_category_not_consented(self):
        """Test permission checking with non-consented research category."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        granted, status = record.check_permission("medical_records", "diabetes_research")
        assert granted is False
        assert status == "RESEARCH_CATEGORY_NOT_CONSENTED"
    
    def test_to_dict(self):
        """Test converting consent record to dictionary."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365),
            metadata={"source": "patient_portal"}
        )
        
        data = record.to_dict()
        
        assert data["patient_id"] == "P001"
        assert data["consent_status"] is True
        assert "consent_id" in data
        assert "version" in data
        assert "is_valid" in data
        assert "is_expired" in data
        assert data["metadata"]["source"] == "patient_portal"
    
    def test_to_metta_entity(self):
        """Test converting consent record to MeTTa entity format."""
        record = ConsentRecord(
            patient_id="P001",
            data_types=["DT001"],
            research_categories=["RC001"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        entity = record.to_metta_entity()
        
        assert entity["entity_type"] == "ConsentRecord"
        assert entity["patient_ref"] == "P001"
        assert entity["data_type_ref"] == "DT001"
        assert entity["research_category_ref"] == "RC001"
        assert entity["consent_granted"] is True


class TestPatientConsentAgent:
    """Test PatientConsentAgent functionality."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return PatientConsentAgent(port=8888, metta_agent_address="metta_test_agent")
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "Patient Consent Agent"
        assert agent.metta_agent_address == "metta_test_agent"
        assert len(agent.consent_records) == 0
        assert agent.stats["total_consents"] == 0
    
    def test_validate_consent_data_valid(self, agent):
        """Test consent data validation with valid data."""
        result = agent._validate_consent_data(
            data_types=["medical_records", "lab_results"],
            research_categories=["cancer_research"]
        )
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_consent_data_empty_data_types(self, agent):
        """Test consent data validation with empty data types."""
        result = agent._validate_consent_data(
            data_types=[],
            research_categories=["cancer_research"]
        )
        
        assert result["valid"] is False
        assert "At least one data type must be specified" in result["errors"]
    
    def test_validate_consent_data_empty_research_categories(self, agent):
        """Test consent data validation with empty research categories."""
        result = agent._validate_consent_data(
            data_types=["medical_records"],
            research_categories=[]
        )
        
        assert result["valid"] is False
        assert "At least one research category must be specified" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_handle_consent_update_create_new(self, agent):
        """Test handling consent update to create new record."""
        ctx = Mock()
        ctx.send = AsyncMock()
        
        consent_msg = ConsentMessage(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        msg = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type=MessageTypes.CONSENT_UPDATE,
            payload=consent_msg.dict(),
            timestamp=datetime.utcnow()
        )
        
        result = await agent._handle_consent_update(ctx, "test_sender", msg)
        
        assert result["status"] == "success"
        assert result["action"] == "created"
        assert result["patient_id"] == "P001"
        assert "consent_id" in result
        assert agent.stats["total_consents"] == 1
        assert "P001" in agent.consent_records
    
    @pytest.mark.asyncio
    async def test_handle_consent_update_modify_existing(self, agent):
        """Test handling consent update to modify existing record."""
        ctx = Mock()
        ctx.send = AsyncMock()
        
        # Create initial consent
        initial_consent = ConsentMessage(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        msg1 = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type=MessageTypes.CONSENT_UPDATE,
            payload=initial_consent.dict(),
            timestamp=datetime.utcnow()
        )
        
        await agent._handle_consent_update(ctx, "test_sender", msg1)
        
        # Update consent
        updated_consent = ConsentMessage(
            patient_id="P001",
            data_types=["medical_records", "lab_results"],
            research_categories=["cancer_research", "diabetes_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        msg2 = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type=MessageTypes.CONSENT_UPDATE,
            payload=updated_consent.dict(),
            timestamp=datetime.utcnow()
        )
        
        result = await agent._handle_consent_update(ctx, "test_sender", msg2)
        
        assert result["status"] == "success"
        assert result["action"] == "updated"
        assert result["version"] == 2
        assert len(agent.consent_records["P001"].data_types) == 2
    
    @pytest.mark.asyncio
    async def test_handle_consent_query_valid(self, agent):
        """Test handling consent query with valid consent."""
        ctx = Mock()
        
        # Create consent record
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        agent.consent_records["P001"] = record
        
        # Query consent
        query = ConsentQuery(
            patient_id="P001",
            data_type="medical_records",
            research_category="cancer_research",
            requester_id="researcher_001"
        )
        
        msg = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type=MessageTypes.CONSENT_QUERY,
            payload=query.dict(),
            timestamp=datetime.utcnow()
        )
        
        result = await agent._handle_consent_query(ctx, "test_sender", msg)
        
        assert result["status"] == "success"
        assert result["consent_granted"] is True
        assert result["status_code"] == "CONSENT_VALID"
    
    @pytest.mark.asyncio
    async def test_handle_consent_query_not_found(self, agent):
        """Test handling consent query with no consent record."""
        ctx = Mock()
        
        query = ConsentQuery(
            patient_id="P999",
            data_type="medical_records",
            research_category="cancer_research",
            requester_id="researcher_001"
        )
        
        msg = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type=MessageTypes.CONSENT_QUERY,
            payload=query.dict(),
            timestamp=datetime.utcnow()
        )
        
        result = await agent._handle_consent_query(ctx, "test_sender", msg)
        
        assert result["status"] == "not_found"
        assert result["consent_granted"] is False
        assert result["error_code"] == ErrorCodes.CONSENT_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_handle_consent_query_expired(self, agent):
        """Test handling consent query with expired consent."""
        ctx = Mock()
        
        # Create expired consent record
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() - timedelta(days=1)
        )
        agent.consent_records["P001"] = record
        
        query = ConsentQuery(
            patient_id="P001",
            data_type="medical_records",
            research_category="cancer_research",
            requester_id="researcher_001"
        )
        
        msg = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type=MessageTypes.CONSENT_QUERY,
            payload=query.dict(),
            timestamp=datetime.utcnow()
        )
        
        result = await agent._handle_consent_query(ctx, "test_sender", msg)
        
        assert result["consent_granted"] is False
        assert result["status_code"] == ErrorCodes.CONSENT_EXPIRED
        assert "expired" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_consent_renewal(self, agent):
        """Test handling consent renewal."""
        ctx = Mock()
        ctx.send = AsyncMock()
        
        # Create consent record
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=30)
        )
        agent.consent_records["P001"] = record
        
        msg = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type="consent_renew",
            payload={"patient_id": "P001", "duration_days": 365},
            timestamp=datetime.utcnow()
        )
        
        result = await agent._handle_consent_renewal(ctx, "test_sender", msg)
        
        assert result["status"] == "success"
        assert result["patient_id"] == "P001"
        assert "new_expiry_date" in result
        assert agent.consent_records["P001"].version == 2
    
    @pytest.mark.asyncio
    async def test_handle_consent_revocation(self, agent):
        """Test handling consent revocation."""
        ctx = Mock()
        ctx.send = AsyncMock()
        
        # Create consent record
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        agent.consent_records["P001"] = record
        
        msg = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type="consent_revoke",
            payload={"patient_id": "P001"},
            timestamp=datetime.utcnow()
        )
        
        result = await agent._handle_consent_revocation(ctx, "test_sender", msg)
        
        assert result["status"] == "success"
        assert result["patient_id"] == "P001"
        assert agent.consent_records["P001"].consent_status is False
        assert agent.consent_records["P001"].is_valid() is False
    
    @pytest.mark.asyncio
    async def test_handle_consent_history(self, agent):
        """Test handling consent history request."""
        ctx = Mock()
        
        # Create and update consent record
        record = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        record.update_consent(
            consent_status=True,
            data_types=["medical_records", "lab_results"]
        )
        agent.consent_records["P001"] = record
        
        msg = AgentMessage(
            sender_agent="test_sender",
            recipient_agent=agent.agent_id,
            message_type="consent_history",
            payload={"patient_id": "P001"},
            timestamp=datetime.utcnow()
        )
        
        result = await agent._handle_consent_history(ctx, "test_sender", msg)
        
        assert result["status"] == "success"
        assert result["patient_id"] == "P001"
        assert result["current_version"] == 2
        assert len(result["audit_trail"]) == 2
        assert "consent_details" in result
    
    def test_update_consent_statistics(self, agent):
        """Test updating consent statistics."""
        # Create various consent records
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        agent.consent_records["P002"] = ConsentRecord(
            patient_id="P002",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() - timedelta(days=1)  # Expired
        )
        
        agent.consent_records["P003"] = ConsentRecord(
            patient_id="P003",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=False,  # Revoked
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        agent._update_consent_statistics()
        
        assert agent.stats["active_consents"] == 1
        assert agent.stats["expired_consents"] == 1
        assert agent.stats["revoked_consents"] == 1
    
    @pytest.mark.asyncio
    async def test_check_expiring_consents(self, agent):
        """Test checking for expiring consents."""
        ctx = Mock()
        
        # Create consent expiring in 20 days
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=20)
        )
        
        # Create consent expiring in 60 days
        agent.consent_records["P002"] = ConsentRecord(
            patient_id="P002",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=60)
        )
        
        expiring = await agent.check_and_notify_expiring_consents(ctx, days_threshold=30)
        
        assert len(expiring) == 1
        assert expiring[0]["patient_id"] == "P001"
        assert expiring[0]["days_remaining"] <= 30
    
    def test_get_consent_statistics(self, agent):
        """Test getting comprehensive consent statistics."""
        # Create actual consent records to test statistics
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        agent.consent_records["P002"] = ConsentRecord(
            patient_id="P002",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        agent.stats["total_consents"] = 2
        
        stats = agent.get_consent_statistics()
        
        assert stats["total_consents"] == 2
        assert stats["active_consents"] == 2
        assert "consent_coverage" in stats
        assert stats["consent_coverage"]["active_percentage"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
