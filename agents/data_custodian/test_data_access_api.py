"""
Unit tests for Data Access API.
"""

import unittest
from datetime import datetime
from .mock_ehr import MockEHRSystem
from .data_access_api import DataAccessAPI, DataAccessRequest, DataProvenanceTracker


class TestDataAccessRequest(unittest.TestCase):
    """Test DataAccessRequest class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.request = DataAccessRequest(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics", "diagnoses"]},
            research_purpose="Study cardiovascular disease patterns",
            ethical_approval="IRB-2024-001"
        )
    
    def test_request_creation(self):
        """Test data access request creation."""
        self.assertIsNotNone(self.request.request_id)
        self.assertEqual(self.request.requester_id, "RESEARCHER-001")
        self.assertEqual(self.request.status, "pending")
        self.assertFalse(self.request.consent_verified)
        self.assertIsInstance(self.request.created_at, datetime)
    
    def test_approve_request(self):
        """Test approving a request."""
        self.request.approve()
        
        self.assertEqual(self.request.status, "approved")
        self.assertGreater(len(self.request.access_log), 1)
    
    def test_deny_request(self):
        """Test denying a request."""
        self.request.deny("Insufficient ethical approval")
        
        self.assertEqual(self.request.status, "denied")
        
        # Check log entry
        last_log = self.request.access_log[-1]
        self.assertEqual(last_log["action"], "denied")
        self.assertIn("reason", last_log["details"])
    
    def test_complete_request(self):
        """Test completing a request."""
        self.request.complete(record_count=25)
        
        self.assertEqual(self.request.status, "completed")
        
        # Check log entry
        last_log = self.request.access_log[-1]
        self.assertEqual(last_log["action"], "completed")
        self.assertEqual(last_log["details"]["record_count"], 25)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        request_dict = self.request.to_dict()
        
        self.assertIn("request_id", request_dict)
        self.assertIn("requester_id", request_dict)
        self.assertIn("status", request_dict)
        self.assertIn("access_log", request_dict)
        self.assertEqual(request_dict["requester_id"], "RESEARCHER-001")


class TestDataProvenanceTracker(unittest.TestCase):
    """Test DataProvenanceTracker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = DataProvenanceTracker()
    
    def test_record_access(self):
        """Test recording data access."""
        access_id = self.tracker.record_access(
            request_id="REQ-001",
            requester_id="RESEARCHER-001",
            patient_ids=["PAT-000001", "PAT-000002"],
            data_types=["demographics", "diagnoses"],
            purpose="Cardiovascular research"
        )
        
        self.assertIsNotNone(access_id)
        self.assertEqual(len(self.tracker.access_history), 1)
        
        # Check access record
        access_record = self.tracker.access_history[0]
        self.assertEqual(access_record["requester_id"], "RESEARCHER-001")
        self.assertEqual(access_record["patient_count"], 2)
        self.assertIn("access_hash", access_record)
    
    def test_patient_provenance(self):
        """Test patient provenance tracking."""
        self.tracker.record_access(
            request_id="REQ-001",
            requester_id="RESEARCHER-001",
            patient_ids=["PAT-000001"],
            data_types=["demographics"],
            purpose="Research"
        )
        
        provenance = self.tracker.get_patient_provenance("PAT-000001")
        
        self.assertIsNotNone(provenance)
        self.assertEqual(provenance["patient_id"], "PAT-000001")
        self.assertIn("access_events", provenance)
        self.assertEqual(len(provenance["access_events"]), 1)
    
    def test_get_access_history(self):
        """Test retrieving access history."""
        # Record multiple accesses
        self.tracker.record_access(
            request_id="REQ-001",
            requester_id="RESEARCHER-001",
            patient_ids=["PAT-000001"],
            data_types=["demographics"],
            purpose="Research 1"
        )
        
        self.tracker.record_access(
            request_id="REQ-002",
            requester_id="RESEARCHER-002",
            patient_ids=["PAT-000002"],
            data_types=["diagnoses"],
            purpose="Research 2"
        )
        
        # Get all history
        all_history = self.tracker.get_access_history()
        self.assertEqual(len(all_history), 2)
        
        # Filter by requester
        researcher1_history = self.tracker.get_access_history(requester_id="RESEARCHER-001")
        self.assertEqual(len(researcher1_history), 1)
        self.assertEqual(researcher1_history[0]["requester_id"], "RESEARCHER-001")


class TestDataAccessAPI(unittest.TestCase):
    """Test DataAccessAPI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ehr_system = MockEHRSystem(institution_id="TEST_HOSPITAL")
        self.api = DataAccessAPI(self.ehr_system)
    
    def test_api_initialization(self):
        """Test API initialization."""
        self.assertIsNotNone(self.api.ehr_system)
        self.assertIsNotNone(self.api.provenance_tracker)
        self.assertEqual(len(self.api.active_requests), 0)
    
    def test_create_data_request(self):
        """Test creating a data access request."""
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics", "diagnoses"]},
            research_purpose="Study cardiovascular disease patterns",
            ethical_approval="IRB-2024-001"
        )
        
        self.assertIsNotNone(request)
        self.assertIn(request.request_id, self.api.active_requests)
        self.assertEqual(request.requester_id, "RESEARCHER-001")
    
    def test_validate_request_success(self):
        """Test validating a valid request."""
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics", "diagnoses"]},
            research_purpose="Study cardiovascular disease patterns in elderly patients",
            ethical_approval="IRB-2024-001"
        )
        
        is_valid, message = self.api.validate_request(request.request_id)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Request is valid")
    
    def test_validate_request_missing_approval(self):
        """Test validating request with missing ethical approval."""
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics"]},
            research_purpose="Study patterns",
            ethical_approval=""
        )
        
        is_valid, message = self.api.validate_request(request.request_id)
        
        self.assertFalse(is_valid)
        self.assertIn("ethical approval", message.lower())
    
    def test_validate_request_short_purpose(self):
        """Test validating request with short research purpose."""
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics"]},
            research_purpose="Study",
            ethical_approval="IRB-2024-001"
        )
        
        is_valid, message = self.api.validate_request(request.request_id)
        
        self.assertFalse(is_valid)
        self.assertIn("purpose", message.lower())
    
    def test_validate_request_invalid_data_types(self):
        """Test validating request with invalid data types."""
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics", "invalid_type"]},
            research_purpose="Study cardiovascular disease patterns",
            ethical_approval="IRB-2024-001"
        )
        
        is_valid, message = self.api.validate_request(request.request_id)
        
        self.assertFalse(is_valid)
        self.assertIn("invalid", message.lower())
    
    def test_search_matching_datasets(self):
        """Test searching for matching datasets."""
        criteria = {
            "research_category": "cardiovascular_research",
            "data_types": ["demographics", "diagnoses"]
        }
        
        datasets = self.api.search_matching_datasets(criteria)
        
        self.assertIsInstance(datasets, list)
        self.assertGreater(len(datasets), 0)
        
        # Verify datasets match criteria
        for dataset in datasets:
            self.assertEqual(dataset["research_category"], "cardiovascular_research")
    
    def test_get_dataset_summary(self):
        """Test getting dataset summary."""
        summary = self.api.get_dataset_summary("DS-GENERAL-001")
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary["dataset_id"], "DS-GENERAL-001")
        self.assertIn("patient_count", summary)
        self.assertIn("available_data_types", summary)
        self.assertEqual(summary["institution_id"], "TEST_HOSPITAL")
        
        # Test non-existent dataset
        non_existent = self.api.get_dataset_summary("DS-NONEXISTENT")
        self.assertIsNone(non_existent)
    
    def test_retrieve_dataset_records(self):
        """Test retrieving dataset records."""
        # Create and approve request
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics", "diagnoses"]},
            research_purpose="Study cardiovascular disease patterns",
            ethical_approval="IRB-2024-001"
        )
        request.approve()
        
        # Retrieve records
        records, access_id = self.api.retrieve_dataset_records(
            request_id=request.request_id,
            dataset_id="DS-GENERAL-001",
            data_types=["demographics", "diagnoses"]
        )
        
        self.assertIsInstance(records, list)
        self.assertGreater(len(records), 0)
        self.assertIsNotNone(access_id)
        
        # Verify record structure
        for record in records:
            self.assertIn("patient_id", record)
            self.assertIn("demographics", record)
            self.assertIn("diagnoses", record)
    
    def test_retrieve_records_unapproved_request(self):
        """Test retrieving records with unapproved request."""
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics"]},
            research_purpose="Study patterns",
            ethical_approval="IRB-2024-001"
        )
        
        records, message = self.api.retrieve_dataset_records(
            request_id=request.request_id,
            dataset_id="DS-GENERAL-001",
            data_types=["demographics"]
        )
        
        self.assertEqual(len(records), 0)
        self.assertIn("not approved", message.lower())
    
    def test_validate_data_quality(self):
        """Test validating data quality for multiple patients."""
        patient_ids = list(self.ehr_system.records.keys())[:5]
        
        validation = self.api.validate_data_quality(patient_ids)
        
        self.assertIn("total_records", validation)
        self.assertIn("valid_records", validation)
        self.assertIn("average_quality_score", validation)
        self.assertEqual(validation["total_records"], 5)
        self.assertGreater(validation["average_quality_score"], 0)
    
    def test_get_request_status(self):
        """Test getting request status."""
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics"]},
            research_purpose="Study patterns",
            ethical_approval="IRB-2024-001"
        )
        
        status = self.api.get_request_status(request.request_id)
        
        self.assertIsNotNone(status)
        self.assertEqual(status["request_id"], request.request_id)
        self.assertEqual(status["status"], "pending")
        
        # Test non-existent request
        non_existent = self.api.get_request_status("REQ-NONEXISTENT")
        self.assertIsNone(non_existent)
    
    def test_get_provenance(self):
        """Test getting data provenance."""
        # Create and approve request
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics"]},
            research_purpose="Study patterns",
            ethical_approval="IRB-2024-001"
        )
        request.approve()
        
        # Retrieve records to create provenance
        patient_ids = list(self.ehr_system.records.keys())[:2]
        self.api.retrieve_dataset_records(
            request_id=request.request_id,
            dataset_id="DS-GENERAL-001",
            data_types=["demographics"],
            patient_ids=patient_ids
        )
        
        # Get provenance
        provenance = self.api.get_provenance(patient_ids[0])
        
        self.assertIsNotNone(provenance)
        self.assertEqual(provenance["patient_id"], patient_ids[0])
        self.assertIn("access_events", provenance)
    
    def test_get_access_logs(self):
        """Test getting access logs."""
        # Create and approve request
        request = self.api.create_data_request(
            requester_id="RESEARCHER-001",
            data_criteria={"data_types": ["demographics"]},
            research_purpose="Study patterns",
            ethical_approval="IRB-2024-001"
        )
        request.approve()
        
        # Retrieve records
        self.api.retrieve_dataset_records(
            request_id=request.request_id,
            dataset_id="DS-GENERAL-001",
            data_types=["demographics"]
        )
        
        # Get logs
        logs = self.api.get_access_logs()
        
        self.assertIsInstance(logs, list)
        self.assertGreater(len(logs), 0)
        
        # Filter by requester
        researcher_logs = self.api.get_access_logs(requester_id="RESEARCHER-001")
        self.assertEqual(len(researcher_logs), 1)
    
    def test_discover_datasets(self):
        """Test dataset discovery."""
        # Discover all datasets
        all_datasets = self.api.discover_datasets()
        
        self.assertIsInstance(all_datasets, list)
        self.assertGreater(len(all_datasets), 0)
        
        # Discover by research category
        cardio_datasets = self.api.discover_datasets(research_category="cardiovascular_research")
        
        for dataset in cardio_datasets:
            self.assertEqual(dataset["research_category"], "cardiovascular_research")
    
    def test_get_dataset_catalog(self):
        """Test getting complete dataset catalog."""
        catalog = self.api.get_dataset_catalog()
        
        self.assertIn("institution_id", catalog)
        self.assertIn("total_datasets", catalog)
        self.assertIn("total_patients", catalog)
        self.assertIn("available_data_types", catalog)
        self.assertIn("research_categories", catalog)
        self.assertIn("datasets", catalog)
        
        self.assertEqual(catalog["institution_id"], "TEST_HOSPITAL")
        self.assertGreater(catalog["total_patients"], 0)
        self.assertGreater(catalog["total_datasets"], 0)


if __name__ == "__main__":
    unittest.main()
