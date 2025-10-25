"""
Integration tests for Patient Consent Agent Chat Protocol integration.
Tests natural language processing, session management, and ASI:One compatibility.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.patient_consent.agent import PatientConsentAgent, ConsentRecord
from shared.protocols.chat_protocol import ChatMessage, ChatSession, ChatResponse


class TestChatProtocolIntegration:
    """Test Chat Protocol integration for Patient Consent Agent."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return PatientConsentAgent(port=8888, metta_agent_address="metta_test_agent")
    
    @pytest.fixture
    def chat_session(self, agent):
        """Create a test chat session."""
        return agent.chat_handler.create_session(
            user_id="test_user_001",
            session_type="patient_consent"
        )
    
    @pytest.mark.asyncio
    async def test_create_chat_session(self, agent):
        """Test creating a new chat session."""
        session = agent.chat_handler.create_session(
            user_id="test_user_001",
            session_type="patient_consent"
        )
        
        assert session.user_id == "test_user_001"
        assert session.session_type == "patient_consent"
        assert session.active is True
        assert session.session_id in agent.chat_handler.active_sessions
    
    @pytest.mark.asyncio
    async def test_close_chat_session(self, agent, chat_session):
        """Test closing a chat session."""
        session_id = chat_session.session_id
        
        result = agent.chat_handler.close_session(session_id)
        
        assert result is True
        assert session_id not in agent.chat_handler.active_sessions
    
    @pytest.mark.asyncio
    async def test_handle_text_message_help(self, agent, chat_session):
        """Test handling help request via text message."""
        ctx = Mock()
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="help"
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert "grant consent" in response.response_data.lower()
        assert "revoke" in response.response_data.lower()
        assert "check" in response.response_data.lower()
    
    @pytest.mark.asyncio
    async def test_handle_text_message_grant_consent_no_patient_id(self, agent, chat_session):
        """Test handling grant consent request without patient ID."""
        ctx = Mock()
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="I want to grant consent for medical records"
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "question"
        assert "patient id" in response.response_data.lower()
        assert response.requires_followup is True
    
    @pytest.mark.asyncio
    async def test_handle_text_message_grant_consent_with_patient_id(self, agent, chat_session):
        """Test handling grant consent request with patient ID."""
        ctx = Mock()
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="I want to grant consent for medical records and lab results for cancer research. My patient ID is P001"
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert "consent granted successfully" in response.response_data.lower()
        assert "P001" in agent.consent_records
    
    @pytest.mark.asyncio
    async def test_handle_text_message_check_status(self, agent, chat_session):
        """Test handling check status request."""
        ctx = Mock()
        
        # Create a consent record first
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="Check my consent status for patient ID P001"
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert "consent status" in response.response_data.lower()
        assert "active" in response.response_data.lower()
    
    @pytest.mark.asyncio
    async def test_handle_text_message_revoke_consent(self, agent, chat_session):
        """Test handling revoke consent request."""
        ctx = Mock()
        
        # Create a consent record first
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="Revoke my consent for patient ID P001"
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert "revoked successfully" in response.response_data.lower()
        assert agent.consent_records["P001"].consent_status is False
    
    @pytest.mark.asyncio
    async def test_handle_text_message_renew_consent(self, agent, chat_session):
        """Test handling renew consent request."""
        ctx = Mock()
        
        # Create a consent record first
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=30)
        )
        
        old_expiry = agent.consent_records["P001"].expiry_date
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="Renew my consent for patient ID P001"
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert "renewed successfully" in response.response_data.lower()
        assert agent.consent_records["P001"].expiry_date > old_expiry
    
    @pytest.mark.asyncio
    async def test_handle_structured_consent_data(self, agent, chat_session):
        """Test handling structured consent data."""
        ctx = Mock()
        
        structured_data = {
            "patient_id": "P002",
            "data_types": ["medical_records", "lab_results"],
            "research_categories": ["cancer_research", "diabetes_research"],
            "consent_status": True,
            "expiry_date": (datetime.utcnow() + timedelta(days=365)).isoformat()
        }
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="structured_data",
            content_data=structured_data
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert response.response_data["status"] == "success"
        assert "P002" in agent.consent_records
    
    @pytest.mark.asyncio
    async def test_handle_structured_data_missing_fields(self, agent, chat_session):
        """Test handling structured data with missing required fields."""
        ctx = Mock()
        
        incomplete_data = {
            "patient_id": "P003",
            "data_types": ["medical_records"]
            # Missing research_categories and consent_status
        }
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="structured_data",
            content_data=incomplete_data
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "error"
        assert "missing required fields" in response.response_data.lower()
    
    @pytest.mark.asyncio
    async def test_handle_command_get_consent(self, agent, chat_session):
        """Test handling get_consent command."""
        ctx = Mock()
        
        # Create a consent record first
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        command_data = {
            "command": "get_consent",
            "params": {"patient_id": "P001"}
        }
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="command",
            content_data=command_data
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert response.response_data["patient_id"] == "P001"
        assert "consent_id" in response.response_data
    
    @pytest.mark.asyncio
    async def test_handle_command_list_consents(self, agent, chat_session):
        """Test handling list_consents command."""
        ctx = Mock()
        
        # Create multiple consent records
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        agent.consent_records["P002"] = ConsentRecord(
            patient_id="P002",
            data_types=["lab_results"],
            research_categories=["diabetes_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        command_data = {
            "command": "list_consents",
            "params": {}
        }
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="command",
            content_data=command_data
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert response.response_data["total"] == 2
        assert len(response.response_data["consents"]) == 2
    
    @pytest.mark.asyncio
    async def test_handle_command_get_statistics(self, agent, chat_session):
        """Test handling get_statistics command."""
        ctx = Mock()
        
        # Create some consent records
        agent.consent_records["P001"] = ConsentRecord(
            patient_id="P001",
            data_types=["medical_records"],
            research_categories=["cancer_research"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        
        agent.stats["total_consents"] = 1
        
        command_data = {
            "command": "get_statistics",
            "params": {}
        }
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="command",
            content_data=command_data
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.response_type == "data"
        assert "total_consents" in response.response_data
        assert "active_consents" in response.response_data
    
    @pytest.mark.asyncio
    async def test_parse_consent_intent(self, agent):
        """Test parsing consent intent from natural language."""
        assert agent._parse_consent_intent("I want to grant consent") == "grant_consent"
        assert agent._parse_consent_intent("Please revoke my consent") == "revoke_consent"
        assert agent._parse_consent_intent("Check my consent status") == "check_status"
        assert agent._parse_consent_intent("Renew my consent") == "renew_consent"
        assert agent._parse_consent_intent("My patient ID is P001") == "provide_patient_id"
    
    @pytest.mark.asyncio
    async def test_extract_patient_id(self, agent):
        """Test extracting patient ID from text."""
        assert agent._extract_patient_id("My patient ID is P001") == "P001"
        assert agent._extract_patient_id("ID: P002") == "P002"
        assert agent._extract_patient_id("patient_id P003") == "P003"
        assert agent._extract_patient_id("no id here") is None
    
    @pytest.mark.asyncio
    async def test_extract_consent_preferences(self, agent):
        """Test extracting consent preferences from natural language."""
        text = "I want to share my medical records and lab results for cancer research"
        prefs = agent._extract_consent_preferences(text)
        
        assert "medical_records" in prefs["data_types"]
        assert "lab_results" in prefs["data_types"]
        assert "cancer_research" in prefs["research_categories"]
    
    @pytest.mark.asyncio
    async def test_session_context_persistence(self, agent, chat_session):
        """Test that session context persists across messages."""
        ctx = Mock()
        
        # First message - ask to grant consent without patient ID
        message1 = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="I want to grant consent"
        )
        
        response1 = await agent._handle_chat_message(ctx, "test_sender", message1)
        
        assert response1.requires_followup is True
        assert "pending_action" in chat_session.context
        assert chat_session.context["pending_action"] == "grant_consent"
        
        # Second message - provide patient ID
        message2 = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="My patient ID is P001"
        )
        
        response2 = await agent._handle_chat_message(ctx, "test_sender", message2)
        
        assert "patient_id" in chat_session.context
        assert chat_session.context["patient_id"] == "P001"
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_session(self, agent):
        """Test error handling for invalid session."""
        ctx = Mock()
        
        message = ChatMessage(
            session_id="invalid_session_id",
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="test message"
        )
        
        # Should create new session automatically
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        # The agent should create a new session
        assert "invalid_session_id" in agent.chat_handler.active_sessions or response.response_type in ["data", "question"]
    
    @pytest.mark.asyncio
    async def test_acknowledgment_protocol(self, agent, chat_session):
        """Test that responses include proper acknowledgment."""
        ctx = Mock()
        
        message = ChatMessage(
            session_id=chat_session.session_id,
            user_id="test_user_001",
            agent_id=agent.agent_id,
            content_type="text",
            content_data="help"
        )
        
        response = await agent._handle_chat_message(ctx, "test_sender", message)
        
        assert response.original_message_id == message.message_id
        assert response.agent_id == agent.agent_id
        assert hasattr(response, 'response_id')
        assert hasattr(response, 'timestamp')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
