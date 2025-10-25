#!/usr/bin/env python3
"""
Test script to verify HealthSync setup and basic functionality.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from shared.protocols.chat_protocol import ChatMessage, ChatSession, ChatProtocolHandler
from shared.protocols.agent_messages import (
    AgentMessage, ConsentMessage, ConsentQuery, MessageTypes
)
from shared.utils.logging import get_logger
from shared.base_agent import HealthSyncBaseAgent
from config import get_all_config

logger = get_logger("setup_test")


def test_imports():
    """Test that all required modules can be imported."""
    try:
        logger.info("Testing imports...")
        
        # Test uAgents import
        from uagents import Agent, Context
        logger.info("✓ uAgents imported successfully")
        
        # Test shared modules
        from shared.protocols.chat_protocol import ChatProtocolHandler
        from shared.protocols.agent_messages import AgentMessage
        from shared.utils.logging import HealthSyncLogger
        from shared.utils.error_handling import CircuitBreaker
        logger.info("✓ Shared modules imported successfully")
        
        # Test agent modules
        from agents.patient_consent.agent import PatientConsentAgent
        logger.info("✓ Agent modules imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during import test: {str(e)}")
        return False


def test_configuration():
    """Test configuration loading."""
    try:
        logger.info("Testing configuration...")
        
        config = get_all_config()
        
        # Check required config sections
        required_sections = ["agents", "logging", "metta", "chat", "privacy"]
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing config section: {section}")
                return False
        
        logger.info("✓ Configuration loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Configuration test failed: {str(e)}")
        return False


def test_message_protocols():
    """Test message protocol creation and validation."""
    try:
        logger.info("Testing message protocols...")
        
        # Test AgentMessage
        msg = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="test_recipient",
            message_type=MessageTypes.CONSENT_UPDATE,
            payload={"test": "data"}
        )
        assert msg.message_id is not None
        assert msg.timestamp is not None
        logger.info("✓ AgentMessage creation successful")
        
        # Test ConsentMessage
        consent = ConsentMessage(
            patient_id="patient_123",
            data_types=["medical_records", "lab_results"],
            research_categories=["cancer_research", "drug_trials"],
            consent_status=True,
            expiry_date=datetime.utcnow() + timedelta(days=365)
        )
        logger.info("✓ ConsentMessage creation successful")
        
        # Test ChatMessage
        chat_msg = ChatMessage(
            session_id="session_123",
            user_id="user_123",
            agent_id="agent_123",
            content_type="text",
            content_data="Hello, I want to update my consent preferences"
        )
        assert chat_msg.message_id is not None
        logger.info("✓ ChatMessage creation successful")
        
        return True
        
    except Exception as e:
        logger.error(f"Message protocol test failed: {str(e)}")
        return False


def test_chat_protocol_handler():
    """Test Chat Protocol handler functionality."""
    try:
        logger.info("Testing Chat Protocol handler...")
        
        handler = ChatProtocolHandler("test_agent")
        
        # Create a session
        session = handler.create_session("user_123", "patient_consent")
        assert session.session_id is not None
        assert session.user_id == "user_123"
        logger.info("✓ Chat session creation successful")
        
        # Test message handling (basic)
        chat_msg = ChatMessage(
            session_id=session.session_id,
            user_id="user_123",
            agent_id="test_agent",
            content_type="text",
            content_data="Test message"
        )
        
        # Note: We can't easily test async methods without running event loop
        logger.info("✓ Chat Protocol handler initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Chat Protocol handler test failed: {str(e)}")
        return False


def test_logging():
    """Test logging functionality."""
    try:
        logger.info("Testing logging functionality...")
        
        test_logger = get_logger("test_agent")
        
        # Test different log levels
        test_logger.info("Test info message")
        test_logger.warning("Test warning message")
        test_logger.debug("Test debug message")
        
        # Test audit logging
        test_logger.audit(
            event_type="test_event",
            details={"test_key": "test_value"}
        )
        
        # Test message logging
        test_logger.message_log(
            direction="sent",
            message_type="test_message",
            message_id="msg_123",
            sender="sender_agent",
            recipient="recipient_agent"
        )
        
        logger.info("✓ Logging functionality working")
        return True
        
    except Exception as e:
        logger.error(f"Logging test failed: {str(e)}")
        return False


def test_directory_structure():
    """Test that required directories exist."""
    try:
        logger.info("Testing directory structure...")
        
        required_dirs = [
            "agents",
            "agents/patient_consent",
            "agents/data_custodian", 
            "agents/research_query",
            "agents/privacy",
            "agents/metta_integration",
            "shared",
            "shared/protocols",
            "shared/utils"
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                logger.error(f"Missing directory: {dir_path}")
                return False
        
        logger.info("✓ Directory structure is correct")
        return True
        
    except Exception as e:
        logger.error(f"Directory structure test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all setup tests."""
    logger.info("Starting HealthSync setup verification...")
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Message Protocols", test_message_protocols),
        ("Chat Protocol Handler", test_chat_protocol_handler),
        ("Logging", test_logging)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if test_func():
                logger.info(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} test FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} test FAILED with exception: {str(e)}")
            failed += 1
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed! HealthSync setup is ready.")
        return True
    else:
        logger.error(f"⚠️  {failed} test(s) failed. Please check the setup.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)