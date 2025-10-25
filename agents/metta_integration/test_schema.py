"""
Unit tests for MeTTa schema definitions and validation
"""

import unittest
import os
from datetime import datetime, timedelta
from agents.metta_integration.schema_manager import MeTTaSchemaManager


class TestMeTTaSchema(unittest.TestCase):
    """Test cases for MeTTa schema loading and validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_manager = MeTTaSchemaManager()
        self.assertTrue(self.schema_manager.load_schema(), "Schema should load successfully")
    
    def test_schema_loading(self):
        """Test that schema file loads correctly"""
        self.assertIsNotNone(self.schema_manager.schema_content)
        self.assertGreater(len(self.schema_manager.schema_content), 0)
    
    def test_entity_types_parsed(self):
        """Test that entity types are correctly parsed from schema"""
        entity_types = self.schema_manager.get_entity_types()
        
        expected_entities = [
            'Patient', 'ConsentRecord', 'DataType', 
            'ResearchCategory', 'PrivacyRule', 'AnonymizationMethod'
        ]
        
        for entity in expected_entities:
            self.assertIn(entity, entity_types, 
                         f"Entity type '{entity}' should be in schema")
    
    def test_relationship_types_parsed(self):
        """Test that relationship types are correctly parsed"""
        relationships = self.schema_manager.get_relationship_types()
        
        expected_relationships = [
            'has-consent', 'covers-data-type', 'allows-research-category',
            'privacy-rule-applies', 'requires-data-type'
        ]
        
        for rel in expected_relationships:
            self.assertIn(rel, relationships,
                         f"Relationship '{rel}' should be in schema")
    
    def test_rules_parsed(self):
        """Test that rules are correctly parsed from schema"""
        rules = self.schema_manager.get_rules()
        
        expected_rules = [
            'has-valid-consent', 'is-expired', 'is-active-consent',
            'meets-ethical-requirements', 'get-privacy-rule',
            'requires-high-anonymization', 'meets-k-anonymity'
        ]
        
        for rule in expected_rules:
            self.assertIn(rule, rules,
                         f"Rule '{rule}' should be in schema")
    
    def test_schema_stats(self):
        """Test schema statistics"""
        stats = self.schema_manager.get_schema_stats()
        
        self.assertGreater(stats['entity_types'], 0)
        self.assertGreater(stats['relationship_types'], 0)
        self.assertGreater(stats['rules'], 0)


class TestPatientEntity(unittest.TestCase):
    """Test cases for Patient entity creation and validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_manager = MeTTaSchemaManager()
        self.schema_manager.load_schema()
    
    def test_create_patient_entity(self):
        """Test creating a valid patient entity"""
        patient = self.schema_manager.create_patient_entity(
            patient_id="P001",
            demographic_hash="abc123def456"
        )
        
        self.assertEqual(patient['entity_type'], 'Patient')
        self.assertEqual(patient['patient_id'], 'P001')
        self.assertEqual(patient['demographic_hash'], 'abc123def456')
        self.assertTrue(patient['active_status'])
        self.assertIsNotNone(patient['created_at'])
    
    def test_validate_patient_entity(self):
        """Test validation of patient entity"""
        patient = self.schema_manager.create_patient_entity(
            patient_id="P001",
            demographic_hash="abc123def456"
        )
        
        is_valid, errors = self.schema_manager.validate_entity('Patient', patient)
        self.assertTrue(is_valid, f"Patient should be valid. Errors: {errors}")
        self.assertEqual(len(errors), 0)
    
    def test_validate_invalid_patient(self):
        """Test validation fails for incomplete patient data"""
        invalid_patient = {
            'entity_type': 'Patient',
            'patient_id': 'P001'
            # Missing required fields
        }
        
        is_valid, errors = self.schema_manager.validate_entity('Patient', invalid_patient)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestConsentRecordEntity(unittest.TestCase):
    """Test cases for ConsentRecord entity"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_manager = MeTTaSchemaManager()
        self.schema_manager.load_schema()
    
    def test_create_consent_record(self):
        """Test creating a valid consent record"""
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        
        consent = self.schema_manager.create_consent_record(
            consent_id="C001",
            patient_id="P001",
            data_type_id="DT001",
            research_category_id="RC001",
            consent_granted=True,
            expiry_date=expiry
        )
        
        self.assertEqual(consent['entity_type'], 'ConsentRecord')
        self.assertEqual(consent['consent_id'], 'C001')
        self.assertEqual(consent['patient_ref'], 'P001')
        self.assertTrue(consent['consent_granted'])
    
    def test_validate_consent_record(self):
        """Test validation of consent record"""
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        
        consent = self.schema_manager.create_consent_record(
            consent_id="C001",
            patient_id="P001",
            data_type_id="DT001",
            research_category_id="RC001",
            consent_granted=True,
            expiry_date=expiry
        )
        
        is_valid, errors = self.schema_manager.validate_entity('ConsentRecord', consent)
        self.assertTrue(is_valid, f"Consent record should be valid. Errors: {errors}")


class TestDataTypeEntity(unittest.TestCase):
    """Test cases for DataType entity"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_manager = MeTTaSchemaManager()
        self.schema_manager.load_schema()
    
    def test_create_data_type(self):
        """Test creating a data type entity"""
        data_type = self.schema_manager.create_data_type(
            type_id="DT001",
            type_name="Medical Records",
            sensitivity_level="high",
            required_permissions=["patient_consent", "ethics_approval"]
        )
        
        self.assertEqual(data_type['entity_type'], 'DataType')
        self.assertEqual(data_type['type_id'], 'DT001')
        self.assertEqual(data_type['sensitivity_level'], 'high')
        self.assertIsInstance(data_type['required_permissions'], list)
    
    def test_validate_data_type(self):
        """Test validation of data type entity"""
        data_type = self.schema_manager.create_data_type(
            type_id="DT001",
            type_name="Medical Records",
            sensitivity_level="high",
            required_permissions=["patient_consent"]
        )
        
        is_valid, errors = self.schema_manager.validate_entity('DataType', data_type)
        self.assertTrue(is_valid, f"Data type should be valid. Errors: {errors}")


class TestResearchCategoryEntity(unittest.TestCase):
    """Test cases for ResearchCategory entity"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_manager = MeTTaSchemaManager()
        self.schema_manager.load_schema()
    
    def test_create_research_category(self):
        """Test creating a research category entity"""
        category = self.schema_manager.create_research_category(
            category_id="RC001",
            category_name="Cancer Research",
            ethics_requirements="IRB_APPROVED",
            allowed_data_types=["DT001", "DT002"]
        )
        
        self.assertEqual(category['entity_type'], 'ResearchCategory')
        self.assertEqual(category['category_id'], 'RC001')
        self.assertEqual(category['category_name'], 'Cancer Research')
        self.assertIsInstance(category['allowed_data_types'], list)
    
    def test_validate_research_category(self):
        """Test validation of research category"""
        category = self.schema_manager.create_research_category(
            category_id="RC001",
            category_name="Cancer Research",
            ethics_requirements="IRB_APPROVED",
            allowed_data_types=["DT001"]
        )
        
        is_valid, errors = self.schema_manager.validate_entity('ResearchCategory', category)
        self.assertTrue(is_valid, f"Research category should be valid. Errors: {errors}")


class TestPrivacyRuleEntity(unittest.TestCase):
    """Test cases for PrivacyRule entity"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_manager = MeTTaSchemaManager()
        self.schema_manager.load_schema()
    
    def test_create_privacy_rule(self):
        """Test creating a privacy rule entity"""
        rule = self.schema_manager.create_privacy_rule(
            rule_id="PR001",
            rule_name="High Sensitivity Anonymization",
            data_type_id="DT001",
            anonymization_method_id="AM001",
            k_anonymity_threshold=5
        )
        
        self.assertEqual(rule['entity_type'], 'PrivacyRule')
        self.assertEqual(rule['rule_id'], 'PR001')
        self.assertEqual(rule['k_anonymity_threshold'], 5)
    
    def test_validate_privacy_rule(self):
        """Test validation of privacy rule"""
        rule = self.schema_manager.create_privacy_rule(
            rule_id="PR001",
            rule_name="Standard Anonymization",
            data_type_id="DT001",
            anonymization_method_id="AM001"
        )
        
        is_valid, errors = self.schema_manager.validate_entity('PrivacyRule', rule)
        self.assertTrue(is_valid, f"Privacy rule should be valid. Errors: {errors}")


class TestAnonymizationMethodEntity(unittest.TestCase):
    """Test cases for AnonymizationMethod entity"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_manager = MeTTaSchemaManager()
        self.schema_manager.load_schema()
    
    def test_create_anonymization_method(self):
        """Test creating an anonymization method entity"""
        method = self.schema_manager.create_anonymization_method(
            method_id="AM001",
            method_name="K-Anonymity",
            technique="generalization",
            privacy_level="high"
        )
        
        self.assertEqual(method['entity_type'], 'AnonymizationMethod')
        self.assertEqual(method['method_id'], 'AM001')
        self.assertEqual(method['technique'], 'generalization')
    
    def test_validate_anonymization_method(self):
        """Test validation of anonymization method"""
        method = self.schema_manager.create_anonymization_method(
            method_id="AM001",
            method_name="K-Anonymity",
            technique="generalization",
            privacy_level="high"
        )
        
        is_valid, errors = self.schema_manager.validate_entity('AnonymizationMethod', method)
        self.assertTrue(is_valid, f"Anonymization method should be valid. Errors: {errors}")


class TestSchemaIntegration(unittest.TestCase):
    """Integration tests for complete schema workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_manager = MeTTaSchemaManager()
        self.schema_manager.load_schema()
    
    def test_complete_consent_workflow(self):
        """Test creating a complete consent workflow with all entities"""
        # Create patient
        patient = self.schema_manager.create_patient_entity(
            patient_id="P001",
            demographic_hash="hash123"
        )
        
        # Create data type
        data_type = self.schema_manager.create_data_type(
            type_id="DT001",
            type_name="Medical Records",
            sensitivity_level="high",
            required_permissions=["patient_consent"]
        )
        
        # Create research category
        category = self.schema_manager.create_research_category(
            category_id="RC001",
            category_name="Cancer Research",
            ethics_requirements="IRB_APPROVED",
            allowed_data_types=["DT001"]
        )
        
        # Create consent record
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        consent = self.schema_manager.create_consent_record(
            consent_id="C001",
            patient_id=patient['patient_id'],
            data_type_id=data_type['type_id'],
            research_category_id=category['category_id'],
            consent_granted=True,
            expiry_date=expiry
        )
        
        # Validate all entities
        self.assertTrue(self.schema_manager.validate_entity('Patient', patient)[0])
        self.assertTrue(self.schema_manager.validate_entity('DataType', data_type)[0])
        self.assertTrue(self.schema_manager.validate_entity('ResearchCategory', category)[0])
        self.assertTrue(self.schema_manager.validate_entity('ConsentRecord', consent)[0])
    
    def test_privacy_rule_workflow(self):
        """Test creating privacy rules with anonymization methods"""
        # Create anonymization method
        method = self.schema_manager.create_anonymization_method(
            method_id="AM001",
            method_name="K-Anonymity",
            technique="generalization",
            privacy_level="high"
        )
        
        # Create data type
        data_type = self.schema_manager.create_data_type(
            type_id="DT001",
            type_name="Medical Records",
            sensitivity_level="high",
            required_permissions=["patient_consent"]
        )
        
        # Create privacy rule
        rule = self.schema_manager.create_privacy_rule(
            rule_id="PR001",
            rule_name="High Sensitivity Rule",
            data_type_id=data_type['type_id'],
            anonymization_method_id=method['method_id'],
            k_anonymity_threshold=5
        )
        
        # Validate all entities
        self.assertTrue(self.schema_manager.validate_entity('AnonymizationMethod', method)[0])
        self.assertTrue(self.schema_manager.validate_entity('DataType', data_type)[0])
        self.assertTrue(self.schema_manager.validate_entity('PrivacyRule', rule)[0])


if __name__ == '__main__':
    unittest.main()
