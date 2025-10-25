"""
Unit tests for Mock EHR System.
"""

import unittest
from datetime import datetime, timedelta
from .mock_ehr import MockEHRSystem, MockPatientRecord


class TestMockPatientRecord(unittest.TestCase):
    """Test MockPatientRecord class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.demographics = {
            "age": 45,
            "gender": "Female",
            "ethnicity": "Caucasian",
            "zip_code": "12345"
        }
        
        self.medical_data = {
            "diagnoses": [
                {
                    "icd10_code": "I10",
                    "description": "Hypertension",
                    "diagnosed_date": datetime.utcnow().isoformat()
                }
            ],
            "medications": [
                {
                    "name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "once daily"
                }
            ]
        }
        
        self.record = MockPatientRecord(
            patient_id="PAT-000001",
            demographics=self.demographics,
            medical_data=self.medical_data
        )
    
    def test_record_creation(self):
        """Test patient record creation."""
        self.assertIsNotNone(self.record.record_id)
        self.assertEqual(self.record.patient_id, "PAT-000001")
        self.assertEqual(self.record.demographics["age"], 45)
        self.assertIsInstance(self.record.created_at, datetime)
    
    def test_record_id_generation(self):
        """Test unique record ID generation."""
        record2 = MockPatientRecord(
            patient_id="PAT-000002",
            demographics=self.demographics,
            medical_data=self.medical_data
        )
        
        self.assertNotEqual(self.record.record_id, record2.record_id)
        self.assertTrue(self.record.record_id.startswith("REC-"))
    
    def test_quality_score_calculation(self):
        """Test data quality score calculation."""
        # Record with complete data should have high quality score
        self.assertGreater(self.record.data_quality_score, 0.5)
        
        # Record with incomplete data should have lower score
        incomplete_record = MockPatientRecord(
            patient_id="PAT-000003",
            demographics={"age": None, "gender": None},
            medical_data={}
        )
        
        self.assertLess(incomplete_record.data_quality_score, self.record.data_quality_score)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        record_dict = self.record.to_dict()
        
        self.assertIn("record_id", record_dict)
        self.assertIn("patient_id", record_dict)
        self.assertIn("demographics", record_dict)
        self.assertIn("medical_data", record_dict)
        self.assertIn("data_quality_score", record_dict)
        self.assertEqual(record_dict["patient_id"], "PAT-000001")


class TestMockEHRSystem(unittest.TestCase):
    """Test MockEHRSystem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ehr_system = MockEHRSystem(institution_id="TEST_HOSPITAL")
    
    def test_system_initialization(self):
        """Test EHR system initialization."""
        self.assertEqual(self.ehr_system.institution_id, "TEST_HOSPITAL")
        self.assertGreater(len(self.ehr_system.records), 0)
        self.assertGreater(len(self.ehr_system.datasets), 0)
    
    def test_mock_data_generation(self):
        """Test mock patient data generation."""
        # Should have 50 patient records
        self.assertEqual(len(self.ehr_system.records), 50)
        
        # Check first record structure
        first_patient_id = list(self.ehr_system.records.keys())[0]
        record = self.ehr_system.records[first_patient_id]
        
        self.assertIsInstance(record, MockPatientRecord)
        self.assertIn("age", record.demographics)
        self.assertIn("gender", record.demographics)
        self.assertIn("diagnoses", record.medical_data)
    
    def test_get_record(self):
        """Test retrieving a patient record."""
        patient_id = list(self.ehr_system.records.keys())[0]
        record = self.ehr_system.get_record(patient_id)
        
        self.assertIsNotNone(record)
        self.assertEqual(record.patient_id, patient_id)
        
        # Test non-existent record
        non_existent = self.ehr_system.get_record("PAT-999999")
        self.assertIsNone(non_existent)
    
    def test_search_records_by_age(self):
        """Test searching records by age criteria."""
        criteria = {
            "age_min": 50,
            "age_max": 70
        }
        
        results = self.ehr_system.search_records(criteria)
        
        self.assertIsInstance(results, list)
        
        # Verify all results match criteria
        for record in results:
            age = record.demographics.get("age")
            self.assertGreaterEqual(age, 50)
            self.assertLessEqual(age, 70)
    
    def test_search_records_by_gender(self):
        """Test searching records by gender."""
        criteria = {"gender": "Female"}
        
        results = self.ehr_system.search_records(criteria)
        
        self.assertIsInstance(results, list)
        
        # Verify all results match criteria
        for record in results:
            self.assertEqual(record.demographics.get("gender"), "Female")
    
    def test_search_records_by_research_category(self):
        """Test searching records by research category."""
        criteria = {"research_category": "cardiovascular_research"}
        
        results = self.ehr_system.search_records(criteria)
        
        # Verify results have cardiovascular diagnoses
        for record in results:
            diagnoses = record.medical_data.get("diagnoses", [])
            has_cardio = any(d.get("icd10_code", "").startswith("I") for d in diagnoses)
            self.assertTrue(has_cardio)
    
    def test_dataset_creation(self):
        """Test dataset creation and categorization."""
        self.assertIn("cardiovascular", self.ehr_system.datasets)
        self.assertIn("diabetes", self.ehr_system.datasets)
        self.assertIn("general", self.ehr_system.datasets)
        
        # Check dataset structure
        cardio_dataset = self.ehr_system.datasets["cardiovascular"]
        self.assertIn("dataset_id", cardio_dataset)
        self.assertIn("patient_count", cardio_dataset)
        self.assertIn("records", cardio_dataset)
        self.assertGreater(cardio_dataset["patient_count"], 0)
    
    def test_list_datasets(self):
        """Test listing all datasets."""
        datasets = self.ehr_system.list_datasets()
        
        self.assertIsInstance(datasets, list)
        self.assertGreater(len(datasets), 0)
        
        # Check dataset structure
        for dataset in datasets:
            self.assertIn("dataset_id", dataset)
            self.assertIn("name", dataset)
            self.assertIn("research_category", dataset)
            self.assertIn("patient_count", dataset)
    
    def test_get_dataset(self):
        """Test retrieving a specific dataset."""
        dataset = self.ehr_system.get_dataset("DS-CARDIO-001")
        
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset["dataset_id"], "DS-CARDIO-001")
        self.assertEqual(dataset["research_category"], "cardiovascular_research")
        
        # Test non-existent dataset
        non_existent = self.ehr_system.get_dataset("DS-NONEXISTENT")
        self.assertIsNone(non_existent)
    
    def test_get_dataset_records(self):
        """Test retrieving records from a dataset."""
        data_types = ["demographics", "diagnoses"]
        records = self.ehr_system.get_dataset_records("DS-GENERAL-001", data_types)
        
        self.assertIsInstance(records, list)
        self.assertGreater(len(records), 0)
        
        # Verify records contain requested data types
        for record in records:
            self.assertIn("patient_id", record)
            self.assertIn("demographics", record)
            self.assertIn("diagnoses", record)
            self.assertIn("data_quality_score", record)
    
    def test_validate_data_quality(self):
        """Test data quality validation."""
        patient_id = list(self.ehr_system.records.keys())[0]
        validation = self.ehr_system.validate_data_quality(patient_id)
        
        self.assertIn("valid", validation)
        self.assertIn("quality_score", validation)
        self.assertIn("issues", validation)
        self.assertIsInstance(validation["valid"], bool)
        self.assertIsInstance(validation["quality_score"], float)
        
        # Test non-existent patient
        invalid_validation = self.ehr_system.validate_data_quality("PAT-999999")
        self.assertFalse(invalid_validation["valid"])
        self.assertIn("error", invalid_validation)
    
    def test_get_metadata(self):
        """Test retrieving record metadata."""
        patient_id = list(self.ehr_system.records.keys())[0]
        metadata = self.ehr_system.get_metadata(patient_id)
        
        self.assertIsNotNone(metadata)
        self.assertIn("record_id", metadata)
        self.assertIn("patient_id", metadata)
        self.assertIn("data_quality_score", metadata)
        self.assertIn("institution_id", metadata)
        self.assertIn("available_data_types", metadata)
        self.assertEqual(metadata["institution_id"], "TEST_HOSPITAL")
        
        # Test non-existent patient
        non_existent_metadata = self.ehr_system.get_metadata("PAT-999999")
        self.assertIsNone(non_existent_metadata)
    
    def test_data_types_constant(self):
        """Test DATA_TYPES constant."""
        self.assertIn("demographics", MockEHRSystem.DATA_TYPES)
        self.assertIn("diagnoses", MockEHRSystem.DATA_TYPES)
        self.assertIn("medications", MockEHRSystem.DATA_TYPES)
        self.assertIn("lab_results", MockEHRSystem.DATA_TYPES)
    
    def test_research_categories_constant(self):
        """Test RESEARCH_CATEGORIES constant."""
        self.assertIn("cardiovascular_research", MockEHRSystem.RESEARCH_CATEGORIES)
        self.assertIn("diabetes_research", MockEHRSystem.RESEARCH_CATEGORIES)
        self.assertIn("general_medical_research", MockEHRSystem.RESEARCH_CATEGORIES)


if __name__ == "__main__":
    unittest.main()
