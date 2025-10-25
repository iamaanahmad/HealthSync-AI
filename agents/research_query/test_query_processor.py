"""
Unit tests for Research Query Agent query processing and validation.
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.research_query.query_processor import (
    QueryProcessor, QueryValidator, QueryType, DataSensitivity,
    QueryValidationResult, ParsedQuery
)


class TestQueryValidator(unittest.TestCase):
    """Test cases for QueryValidator class."""
    
    def setUp(self):
        self.validator = QueryValidator()
        self.valid_query_data = {
            "researcher_id": "HMS-12345",
            "study_description": "A comprehensive observational study to evaluate treatment outcomes in patients with cardiovascular disease",
            "data_requirements": {
                "data_types": ["demographics", "vital_signs", "lab_results", "medications"],
                "research_categories": ["clinical_trials", "outcomes_research"],
                "minimum_sample_size": 100,
                "date_range": {
                    "start_date": "2023-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            },
            "ethical_approval_id": "IRB-2024-123456",
            "privacy_requirements": {
                "anonymization_methods": ["anonymization", "access_control", "k_anonymity"]
            }
        }
    
    def test_validate_query_structure_valid(self):
        """Test validation of valid query structure."""
        result = self.validator.validate_query_structure(self.valid_query_data)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(result.complexity_score, 0)
        self.assertGreater(result.estimated_processing_time, 0)
    
    def test_validate_query_structure_missing_required_fields(self):
        """Test validation with missing required fields."""
        invalid_data = self.valid_query_data.copy()
        del invalid_data["researcher_id"]
        del invalid_data["ethical_approval_id"]
        
        result = self.validator.validate_query_structure(invalid_data)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Missing required field: researcher_id", result.errors)
        self.assertIn("Missing required field: ethical_approval_id", result.errors)
    
    def test_validate_query_structure_invalid_researcher_id(self):
        """Test validation with invalid researcher ID format."""
        invalid_data = self.valid_query_data.copy()
        invalid_data["researcher_id"] = "invalid-format"
        
        result = self.validator.validate_query_structure(invalid_data)
        
        self.assertTrue(result.is_valid)  # Should still be valid, just a warning
        self.assertIn("Researcher ID format should be", result.warnings[0])
    
    def test_validate_query_structure_invalid_ethical_approval(self):
        """Test validation with invalid ethical approval format."""
        invalid_data = self.valid_query_data.copy()
        invalid_data["ethical_approval_id"] = "invalid-format"
        
        result = self.validator.validate_query_structure(invalid_data)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid ethical approval ID format", result.errors[0])
    
    def test_validate_data_requirements_invalid_data_types(self):
        """Test validation with invalid data types."""
        invalid_data = self.valid_query_data.copy()
        invalid_data["data_requirements"]["data_types"] = ["invalid_type", "demographics"]
        
        result = self.validator.validate_query_structure(invalid_data)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid data types: ['invalid_type']", result.errors[0])
    
    def test_validate_data_requirements_large_sample_size(self):
        """Test validation with large sample size."""
        large_sample_data = self.valid_query_data.copy()
        large_sample_data["data_requirements"]["minimum_sample_size"] = 150000
        
        result = self.validator.validate_query_structure(large_sample_data)
        
        self.assertTrue(result.is_valid)
        self.assertIn("Large sample size requested", result.warnings[0])
    
    def test_validate_data_requirements_invalid_date_range(self):
        """Test validation with invalid date range."""
        invalid_data = self.valid_query_data.copy()
        invalid_data["data_requirements"]["date_range"] = {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2023-01-01T00:00:00Z"  # End before start
        }
        
        result = self.validator.validate_query_structure(invalid_data)
        
        self.assertFalse(result.is_valid)
        self.assertIn("start_date must be before end_date", result.errors[0])
    
    def test_validate_ethical_compliance_valid(self):
        """Test ethical compliance validation with valid data."""
        result = self.validator.validate_ethical_compliance(self.valid_query_data)
        
        self.assertTrue(result.is_valid)
        self.assertGreaterEqual(result.ethical_score, 0.6)
    
    def test_validate_ethical_compliance_invalid_approval(self):
        """Test ethical compliance with invalid approval."""
        invalid_data = self.valid_query_data.copy()
        invalid_data["ethical_approval_id"] = "IRB-2020-123456"  # Old approval
        
        result = self.validator.validate_ethical_compliance(invalid_data)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid or expired ethical approval", result.errors[0])
    
    def test_validate_ethical_compliance_prohibited_data(self):
        """Test ethical compliance with prohibited data requests."""
        invalid_data = self.valid_query_data.copy()
        invalid_data["data_requirements"]["specific_fields"] = ["ssn", "full_name", "address"]
        
        result = self.validator.validate_ethical_compliance(invalid_data)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Prohibited identifiers requested", result.errors[0])
    
    def test_validate_ethical_compliance_genomics_without_enhanced_anonymization(self):
        """Test genomics + demographics without enhanced anonymization."""
        risky_data = self.valid_query_data.copy()
        risky_data["data_requirements"]["data_types"] = ["genomics", "demographics"]
        risky_data["data_requirements"]["enhanced_anonymization"] = False
        
        result = self.validator.validate_ethical_compliance(risky_data)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Genomics + demographics requires enhanced anonymization", result.errors[0])
    
    def test_validate_study_purpose_insufficient_description(self):
        """Test study purpose validation with insufficient description."""
        short_desc_data = self.valid_query_data.copy()
        short_desc_data["study_description"] = "Short study"
        
        result = self.validator.validate_ethical_compliance(short_desc_data)
        
        # Should have low ethical score due to insufficient description
        self.assertLess(result.ethical_score, 0.6)
    
    def test_validate_study_purpose_concerning_terms(self):
        """Test study purpose validation with concerning commercial terms."""
        commercial_data = self.valid_query_data.copy()
        commercial_data["study_description"] = "A commercial marketing study for profit and advertisement purposes to sell products"
        
        result = self.validator.validate_ethical_compliance(commercial_data)
        
        # Should have reduced ethical score due to commercial terms
        self.assertLess(result.ethical_score, 0.8)
    
    def test_calculate_complexity_score(self):
        """Test complexity score calculation."""
        # Simple query
        simple_data = {
            "data_requirements": {
                "data_types": ["demographics"],
                "minimum_sample_size": 50
            }
        }
        simple_score = self.validator._calculate_complexity_score(simple_data)
        
        # Complex query
        complex_data = {
            "data_requirements": {
                "data_types": ["demographics", "genomics", "lab_results", "medications", "procedures"],
                "minimum_sample_size": 50000,
                "date_range": {
                    "start_date": "2020-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                },
                "longitudinal_data": True,
                "multi_site_data": True
            },
            "inclusion_criteria": ["age > 18", "diagnosis = diabetes"],
            "exclusion_criteria": ["pregnancy", "terminal_illness"]
        }
        complex_score = self.validator._calculate_complexity_score(complex_data)
        
        self.assertGreater(complex_score, simple_score)
        self.assertLessEqual(complex_score, 1.0)


class TestQueryProcessor(unittest.TestCase):
    """Test cases for QueryProcessor class."""
    
    def setUp(self):
        self.processor = QueryProcessor()
        self.valid_query_data = {
            "query_id": "test-query-123",
            "researcher_id": "HMS-12345",
            "study_title": "Cardiovascular Outcomes Study",
            "study_description": "A comprehensive observational clinical study to evaluate treatment outcomes and efficacy in patients with cardiovascular disease for public health research and prevention strategies",
            "data_requirements": {
                "data_types": ["demographics", "vital_signs", "lab_results"],
                "research_categories": ["clinical_trials", "outcomes_research"],
                "minimum_sample_size": 100
            },
            "ethical_approval_id": f"IRB-{datetime.now().year}-123456",
            "inclusion_criteria": ["age >= 18", "diagnosis = cardiovascular_disease"],
            "exclusion_criteria": ["pregnancy", "terminal_illness"],
            "privacy_requirements": {
                "anonymization_methods": ["k_anonymity", "generalization"]
            }
        }
    
    def test_parse_research_query_valid(self):
        """Test parsing of valid research query."""
        parsed_query, validation_result = self.processor.parse_research_query(self.valid_query_data)
        
        self.assertIsNotNone(parsed_query)
        self.assertTrue(validation_result.is_valid)
        self.assertEqual(parsed_query.query_id, "test-query-123")
        self.assertEqual(parsed_query.researcher_id, "HMS-12345")
        self.assertEqual(parsed_query.study_title, "Cardiovascular Outcomes Study")
        self.assertIn("demographics", parsed_query.required_data_types)
        self.assertIn("clinical_trials", parsed_query.research_categories)
    
    def test_parse_research_query_invalid(self):
        """Test parsing of invalid research query."""
        invalid_data = self.valid_query_data.copy()
        del invalid_data["researcher_id"]  # Remove required field
        
        parsed_query, validation_result = self.processor.parse_research_query(invalid_data)
        
        self.assertIsNone(parsed_query)
        self.assertFalse(validation_result.is_valid)
        self.assertIn("Missing required field: researcher_id", validation_result.errors)
    
    def test_determine_query_type_interventional(self):
        """Test query type determination for interventional studies."""
        interventional_data = self.valid_query_data.copy()
        interventional_data["study_description"] = "A clinical trial to test new intervention therapy treatment"
        
        parsed_query, _ = self.processor.parse_research_query(interventional_data)
        
        self.assertEqual(parsed_query.query_type, QueryType.INTERVENTIONAL)
    
    def test_determine_query_type_diagnostic(self):
        """Test query type determination for diagnostic studies."""
        diagnostic_data = self.valid_query_data.copy()
        diagnostic_data["study_description"] = "A study to evaluate diagnostic screening methods for early detection"
        
        parsed_query, _ = self.processor.parse_research_query(diagnostic_data)
        
        self.assertEqual(parsed_query.query_type, QueryType.DIAGNOSTIC)
    
    def test_determine_query_type_genetic(self):
        """Test query type determination for genetic studies."""
        genetic_data = self.valid_query_data.copy()
        genetic_data["study_description"] = "A genomic study to analyze DNA mutations and genetic variations"
        
        parsed_query, _ = self.processor.parse_research_query(genetic_data)
        
        self.assertEqual(parsed_query.query_type, QueryType.GENETIC)
    
    def test_determine_sensitivity_level_restricted(self):
        """Test sensitivity level determination for restricted data."""
        restricted_data = self.valid_query_data.copy()
        restricted_data["data_requirements"]["data_types"] = ["genomics", "behavioral", "clinical_notes"]
        
        parsed_query, _ = self.processor.parse_research_query(restricted_data)
        
        self.assertEqual(parsed_query.sensitivity_level, DataSensitivity.RESTRICTED)
    
    def test_determine_sensitivity_level_confidential(self):
        """Test sensitivity level determination for confidential data."""
        confidential_data = self.valid_query_data.copy()
        confidential_data["data_requirements"]["data_types"] = ["diagnoses", "medications", "procedures"]
        
        parsed_query, _ = self.processor.parse_research_query(confidential_data)
        
        self.assertEqual(parsed_query.sensitivity_level, DataSensitivity.CONFIDENTIAL)
    
    def test_validate_ethical_compliance_parsed_query(self):
        """Test ethical compliance validation for parsed query."""
        parsed_query, _ = self.processor.parse_research_query(self.valid_query_data)
        ethical_result = self.processor.validate_ethical_compliance(parsed_query)
        
        self.assertTrue(ethical_result.is_valid)
        self.assertGreaterEqual(ethical_result.ethical_score, 0.6)
    
    def test_create_query_summary(self):
        """Test query summary creation."""
        parsed_query, _ = self.processor.parse_research_query(self.valid_query_data)
        summary = self.processor.create_query_summary(parsed_query)
        
        self.assertEqual(summary["query_id"], "test-query-123")
        self.assertEqual(summary["researcher_id"], "HMS-12345")
        # Query type is determined by study description content
        self.assertIn(summary["query_type"], [qt.value for qt in QueryType])
        self.assertEqual(summary["study_title"], "Cardiovascular Outcomes Study")
        self.assertEqual(summary["data_types_count"], 3)
        self.assertEqual(summary["research_categories_count"], 2)
        self.assertTrue(summary["has_inclusion_criteria"])
        self.assertTrue(summary["has_exclusion_criteria"])
        self.assertIn("created_at", summary)


if __name__ == "__main__":
    unittest.main()