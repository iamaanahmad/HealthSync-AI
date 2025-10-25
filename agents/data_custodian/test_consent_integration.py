"""
Integration tests for Data Custodian Agent with consent validation.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from .agent import DataCustodianAgent
from .mock_ehr import MockEHRSystem
from shared.protocols.agent_messages import DataRequest, MessageTypes


class TestConsentIntegration(unittest.TestCase):
    """Test consent validation and data access control."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = DataCustodianAgent(
            port=8003,
            patient_consent_agent_address="test_consent_agent_address",
            institution_id="TEST_HOSPITAL"
        )
        
        # Mock context
        self.mock_ctx = Mock()
        self.mock_ctx.send = AsyncMock()
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        self.assertIsNotNone(self.agent.ehr_system)
        self.assertIsNotNone(self.agent.data_api)
        self.assertEqual(self.agent.ehr_system.institution_id, "TEST_HOSPITAL")
        self.assertGreater(len(self.agent.ehr_system.records), 0)
    
    def test_data_request_validation_success(self):
        """Test successful data request validation."""
        loop = asyncio.get_event_loop()
        
        # Create valid data request
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics", "diagnoses"],
                "research_category": "cardiovascular_research"
            },
            "research_purpose": "Study cardiovascular disease patterns in elderly patients",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_001"
        msg.requires_acknowledgment = True
        
        # Mock consent verification to return all consents valid
        async def mock_verify_consents(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-CARDIO-001")
            patient_ids = dataset["records"][:5]  # Use first 5 patients
            
            return {
                "all_consents_valid": True,
                "consented_patient_ids": patient_ids,
                "consented_count": len(patient_ids),
                "total_count": len(patient_ids),
                "consent_rate": 1.0
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_consents):
            result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        self.assertEqual(result["status"], "approved")
        self.assertTrue(result["access_granted"])
        self.assertIn("records", result)
        self.assertGreater(len(result["records"]), 0)
    
    def test_data_request_validation_failure(self):
        """Test data request validation failure."""
        loop = asyncio.get_event_loop()
        
        # Create invalid data request (missing ethical approval)
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study",
            "ethical_approval": ""
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_002"
        msg.requires_acknowledgment = True
        
        result = loop.run_until_complete(
            self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
        )
        
        self.assertEqual(result["status"], "denied")
        self.assertFalse(result["access_granted"])
        self.assertIn("denial_reason", result)
    
    def test_consent_verification_insufficient_consents(self):
        """Test data request denied due to insufficient consents."""
        loop = asyncio.get_event_loop()
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics", "diagnoses"],
                "research_category": "cardiovascular_research"
            },
            "research_purpose": "Study cardiovascular disease patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_003"
        msg.requires_acknowledgment = True
        
        # Mock consent verification to return insufficient consents
        async def mock_verify_consents(*args, **kwargs):
            return {
                "all_consents_valid": False,
                "consented_patient_ids": [],
                "consented_count": 0,
                "total_count": 10,
                "consent_rate": 0.0
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_consents):
            result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        self.assertEqual(result["status"], "denied")
        self.assertFalse(result["access_granted"])
        self.assertIn("Insufficient patient consents", result["denial_reason"])
        self.assertIn("consent_details", result)
    
    def test_consent_verification_partial_consents(self):
        """Test data request with partial consents (>50% consented)."""
        loop = asyncio.get_event_loop()
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study demographic patterns in healthcare",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_004"
        msg.requires_acknowledgment = True
        
        # Mock consent verification to return partial consents (60%)
        async def mock_verify_consents(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
            all_patient_ids = dataset["records"][:10]
            consented_ids = all_patient_ids[:6]  # 60% consented
            
            return {
                "all_consents_valid": True,  # >50% is considered valid
                "consented_patient_ids": consented_ids,
                "consented_count": len(consented_ids),
                "total_count": len(all_patient_ids),
                "consent_rate": 0.6
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_consents):
            result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        self.assertEqual(result["status"], "approved")
        self.assertTrue(result["access_granted"])
        self.assertEqual(result["patient_count"], 6)  # Only consented patients
    
    def test_no_matching_datasets(self):
        """Test data request with no matching datasets."""
        loop = asyncio.get_event_loop()
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "nonexistent_research"
            },
            "research_purpose": "Study nonexistent patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_005"
        msg.requires_acknowledgment = True
        
        result = loop.run_until_complete(
            self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
        )
        
        self.assertEqual(result["status"], "denied")
        self.assertFalse(result["access_granted"])
        self.assertIn("No datasets match", result["denial_reason"])
    
    def test_dataset_discovery(self):
        """Test dataset discovery functionality."""
        loop = asyncio.get_event_loop()
        
        msg = Mock()
        msg.payload = {"research_category": "cardiovascular_research"}
        msg.message_id = "test_msg_006"
        
        result = loop.run_until_complete(
            self.agent._handle_dataset_discovery(self.mock_ctx, "test_sender", msg)
        )
        
        self.assertEqual(result["status"], "success")
        self.assertIn("datasets", result)
        self.assertGreater(result["total_datasets"], 0)
        
        # Verify all datasets match the category
        for dataset in result["datasets"]:
            self.assertEqual(dataset["research_category"], "cardiovascular_research")
    
    def test_dataset_summary(self):
        """Test dataset summary retrieval."""
        loop = asyncio.get_event_loop()
        
        msg = Mock()
        msg.payload = {"dataset_id": "DS-GENERAL-001"}
        msg.message_id = "test_msg_007"
        
        result = loop.run_until_complete(
            self.agent._handle_dataset_summary(self.mock_ctx, "test_sender", msg)
        )
        
        self.assertEqual(result["status"], "success")
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["dataset_id"], "DS-GENERAL-001")
        self.assertIn("patient_count", result["summary"])
    
    def test_data_provenance_tracking(self):
        """Test data provenance tracking."""
        loop = asyncio.get_event_loop()
        
        # First, create and approve a data request to generate provenance
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study demographic patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_008"
        msg.requires_acknowledgment = True
        
        # Mock consent verification
        async def mock_verify_consents(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
            patient_ids = dataset["records"][:3]
            
            return {
                "all_consents_valid": True,
                "consented_patient_ids": patient_ids,
                "consented_count": len(patient_ids),
                "total_count": len(patient_ids),
                "consent_rate": 1.0
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_consents):
            data_result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        self.assertEqual(data_result["status"], "approved")
        
        # Now check provenance for one of the accessed patients
        patient_id = data_result["records"][0]["patient_id"]
        
        provenance_msg = Mock()
        provenance_msg.payload = {"patient_id": patient_id}
        provenance_msg.message_id = "test_msg_009"
        
        provenance_result = loop.run_until_complete(
            self.agent._handle_data_provenance(self.mock_ctx, "test_sender", provenance_msg)
        )
        
        self.assertEqual(provenance_result["status"], "success")
        self.assertIn("provenance", provenance_result)
        self.assertEqual(provenance_result["provenance"]["patient_id"], patient_id)
        self.assertIn("access_events", provenance_result["provenance"])
    
    def test_access_logs(self):
        """Test access log retrieval."""
        loop = asyncio.get_event_loop()
        
        # First, create a data request to generate logs
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_010"
        msg.requires_acknowledgment = True
        
        # Mock consent verification
        async def mock_verify_consents(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
            patient_ids = dataset["records"][:2]
            
            return {
                "all_consents_valid": True,
                "consented_patient_ids": patient_ids,
                "consented_count": len(patient_ids),
                "total_count": len(patient_ids),
                "consent_rate": 1.0
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_consents):
            loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        # Now get access logs
        logs_msg = Mock()
        logs_msg.payload = {"requester_id": "RESEARCHER-001"}
        logs_msg.message_id = "test_msg_011"
        
        logs_result = loop.run_until_complete(
            self.agent._handle_access_logs(self.mock_ctx, "test_sender", logs_msg)
        )
        
        self.assertEqual(logs_result["status"], "success")
        self.assertIn("logs", logs_result)
        self.assertGreater(logs_result["total_accesses"], 0)
    
    def test_health_check(self):
        """Test health check functionality."""
        loop = asyncio.get_event_loop()
        
        msg = Mock()
        msg.payload = {}
        msg.message_id = "test_msg_012"
        
        result = loop.run_until_complete(
            self.agent._handle_health_check(self.mock_ctx, "test_sender", msg)
        )
        
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["agent_id"], self.agent.agent_id)
        self.assertIn("statistics", result)
        self.assertIn("total_patients", result)
        self.assertGreater(result["total_patients"], 0)
    
    def test_statistics_tracking(self):
        """Test that statistics are properly tracked."""
        loop = asyncio.get_event_loop()
        
        initial_total = self.agent.stats["total_requests"]
        initial_approved = self.agent.stats["approved_requests"]
        
        # Create valid request
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study demographic patterns in healthcare",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_013"
        msg.requires_acknowledgment = True
        
        # Mock consent verification
        async def mock_verify_consents(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
            patient_ids = dataset["records"][:5]
            
            return {
                "all_consents_valid": True,
                "consented_patient_ids": patient_ids,
                "consented_count": len(patient_ids),
                "total_count": len(patient_ids),
                "consent_rate": 1.0
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_consents):
            result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        # Verify statistics were updated
        self.assertEqual(self.agent.stats["total_requests"], initial_total + 1)
        self.assertEqual(self.agent.stats["approved_requests"], initial_approved + 1)
        self.assertGreater(self.agent.stats["total_records_shared"], 0)


    def test_consent_query_error_handling(self):
        """Test error handling when consent query fails."""
        loop = asyncio.get_event_loop()
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study demographic patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_014"
        msg.requires_acknowledgment = True
        
        # Mock consent query to raise an exception
        async def mock_query_consent_error(*args, **kwargs):
            raise Exception("Consent agent unavailable")
        
        with patch.object(self.agent, '_query_consent_agent', side_effect=mock_query_consent_error):
            # Mock verify_patient_consents to call the error-raising query
            async def mock_verify_with_error(*args, **kwargs):
                dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
                patient_ids = dataset["records"][:2]
                
                # Try to query consent and catch error
                try:
                    await self.agent._query_consent_agent(
                        ctx=self.mock_ctx,
                        query_payload={"patient_id": patient_ids[0]}
                    )
                except Exception:
                    pass
                
                return {
                    "all_consents_valid": False,
                    "consented_patient_ids": [],
                    "consented_count": 0,
                    "total_count": len(patient_ids),
                    "consent_rate": 0.0,
                    "consent_failures": [{"patient_id": pid, "reason": "Consent query failed"} for pid in patient_ids]
                }
            
            with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_with_error):
                result = loop.run_until_complete(
                    self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
                )
        
        self.assertEqual(result["status"], "denied")
        self.assertFalse(result["access_granted"])
    
    def test_multi_data_type_consent_validation(self):
        """Test consent validation for multiple data types."""
        loop = asyncio.get_event_loop()
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics", "diagnoses", "medications"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Comprehensive medical research study",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_015"
        msg.requires_acknowledgment = True
        
        # Mock consent verification for multiple data types
        async def mock_verify_multi_types(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
            patient_ids = dataset["records"][:5]
            
            # Simulate that only some patients have consented to all data types
            consented_ids = patient_ids[:3]  # 3 out of 5 consented to all types
            
            return {
                "all_consents_valid": True,  # 60% is above threshold
                "consented_patient_ids": consented_ids,
                "consented_count": len(consented_ids),
                "total_count": len(patient_ids),
                "consent_rate": 0.6,
                "consent_failures": [
                    {"patient_id": patient_ids[3], "data_type": "medications", "reason": "Not consented"},
                    {"patient_id": patient_ids[4], "data_type": "diagnoses", "reason": "Not consented"}
                ]
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_multi_types):
            result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        self.assertEqual(result["status"], "approved")
        self.assertTrue(result["access_granted"])
        self.assertEqual(result["patient_count"], 3)
        self.assertIn("consent_verification", result)
        self.assertEqual(result["consent_verification"]["consent_rate"], 0.6)
    
    def test_consent_verification_audit_logging(self):
        """Test that consent verification is properly logged for audit."""
        loop = asyncio.get_event_loop()
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study demographic patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_016"
        msg.requires_acknowledgment = True
        
        # Mock consent verification
        async def mock_verify_consents(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
            patient_ids = dataset["records"][:3]
            
            return {
                "all_consents_valid": True,
                "consented_patient_ids": patient_ids,
                "consented_count": len(patient_ids),
                "total_count": len(patient_ids),
                "consent_rate": 1.0
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_consents):
            result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        # Verify that the request was approved and logged
        self.assertEqual(result["status"], "approved")
        self.assertTrue(result["access_granted"])
        
        # Verify consent_verified flag is set
        request = self.agent.data_api.active_requests.get(result["request_id"])
        self.assertIsNotNone(request)
        self.assertTrue(request.consent_verified)
    
    def test_data_access_with_consent_expiry_check(self):
        """Test that expired consents are properly handled."""
        loop = asyncio.get_event_loop()
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study demographic patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_017"
        msg.requires_acknowledgment = True
        
        # Mock consent verification with expired consents
        async def mock_verify_expired(*args, **kwargs):
            return {
                "all_consents_valid": False,
                "consented_patient_ids": [],
                "consented_count": 0,
                "total_count": 5,
                "consent_rate": 0.0,
                "consent_failures": [
                    {"patient_id": f"PAT-{i}", "reason": "Consent expired"} for i in range(5)
                ]
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_expired):
            result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        self.assertEqual(result["status"], "denied")
        self.assertFalse(result["access_granted"])
        self.assertIn("Insufficient patient consents", result["denial_reason"])
    
    def test_consent_verification_statistics(self):
        """Test that consent verification updates statistics correctly."""
        loop = asyncio.get_event_loop()
        
        initial_consent_checks = self.agent.stats["consent_checks"]
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study demographic patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_018"
        msg.requires_acknowledgment = True
        
        # Mock consent verification that performs multiple checks
        async def mock_verify_with_checks(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
            patient_ids = dataset["records"][:3]
            
            # Simulate consent checks (one per patient)
            self.agent.stats["consent_checks"] += len(patient_ids)
            
            return {
                "all_consents_valid": True,
                "consented_patient_ids": patient_ids,
                "consented_count": len(patient_ids),
                "total_count": len(patient_ids),
                "consent_rate": 1.0
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_with_checks):
            result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        # Verify statistics were updated
        self.assertEqual(result["status"], "approved")
        self.assertGreater(self.agent.stats["consent_checks"], initial_consent_checks)
    
    def test_provenance_tracking_with_consent_info(self):
        """Test that provenance includes consent verification information."""
        loop = asyncio.get_event_loop()
        
        request_payload = {
            "requester_id": "RESEARCHER-001",
            "data_criteria": {
                "data_types": ["demographics"],
                "research_category": "general_medical_research"
            },
            "research_purpose": "Study demographic patterns",
            "ethical_approval": "IRB-2024-001"
        }
        
        msg = Mock()
        msg.payload = request_payload
        msg.message_id = "test_msg_019"
        msg.requires_acknowledgment = True
        
        # Mock consent verification
        async def mock_verify_consents(*args, **kwargs):
            dataset = self.agent.ehr_system.get_dataset("DS-GENERAL-001")
            patient_ids = dataset["records"][:2]
            
            return {
                "all_consents_valid": True,
                "consented_patient_ids": patient_ids,
                "consented_count": len(patient_ids),
                "total_count": len(patient_ids),
                "consent_rate": 1.0
            }
        
        with patch.object(self.agent, '_verify_patient_consents', side_effect=mock_verify_consents):
            data_result = loop.run_until_complete(
                self.agent._handle_data_request(self.mock_ctx, "test_sender", msg)
            )
        
        self.assertEqual(data_result["status"], "approved")
        
        # Check that access was logged with consent verification
        access_logs = self.agent.data_api.get_access_logs(requester_id="RESEARCHER-001")
        self.assertGreater(len(access_logs), 0)
        
        # Verify the access log contains patient information
        latest_log = access_logs[-1]
        self.assertEqual(latest_log["requester_id"], "RESEARCHER-001")
        self.assertIn("patient_ids", latest_log)
        self.assertGreater(len(latest_log["patient_ids"]), 0)


if __name__ == "__main__":
    unittest.main()
