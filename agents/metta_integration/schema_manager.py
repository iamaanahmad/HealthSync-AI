"""
MeTTa Schema Manager for HealthSync
Handles loading, validation, and management of MeTTa knowledge graph schemas
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MeTTaSchemaManager:
    """Manages MeTTa schema definitions and provides validation utilities"""
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the schema manager
        
        Args:
            schema_path: Path to the MeTTa schema file
        """
        if schema_path is None:
            schema_path = os.path.join(
                os.path.dirname(__file__), 
                'schema.metta'
            )
        
        self.schema_path = schema_path
        self.schema_content = None
        self.entity_types = []
        self.relationship_types = []
        self.rules = []
        
    def load_schema(self) -> bool:
        """
        Load the MeTTa schema from file
        
        Returns:
            bool: True if schema loaded successfully
        """
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self.schema_content = f.read()
            
            logger.info(f"Loaded MeTTa schema from {self.schema_path}")
            self._parse_schema()
            return True
            
        except FileNotFoundError:
            logger.error(f"Schema file not found: {self.schema_path}")
            return False
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            return False
    
    def _parse_schema(self):
        """Parse schema content to extract entity types, relationships, and rules"""
        if not self.schema_content:
            return
        
        lines = self.schema_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith(';'):
                continue
            
            # Extract entity type definitions
            if line.startswith('(: ') and ' Type)' in line:
                entity_name = line.split()[1]
                self.entity_types.append(entity_name)
            
            # Extract relationship definitions
            elif line.startswith('(: ') and '->' in line and 'Bool)' in line:
                rel_name = line.split()[1]
                if not any(rel_name.startswith(prefix) for prefix in ['patient-', 'consent-', 'type-', 'category-']):
                    self.relationship_types.append(rel_name)
            
            # Extract rule definitions
            elif line.startswith('(= ('):
                rule_name = line.split('(')[2].split()[0]
                self.rules.append(rule_name)
        
        logger.info(f"Parsed schema: {len(self.entity_types)} entities, "
                   f"{len(self.relationship_types)} relationships, "
                   f"{len(self.rules)} rules")
    
    def get_entity_types(self) -> List[str]:
        """Get list of defined entity types"""
        return self.entity_types.copy()
    
    def get_relationship_types(self) -> List[str]:
        """Get list of defined relationship types"""
        return self.relationship_types.copy()
    
    def get_rules(self) -> List[str]:
        """Get list of defined rules"""
        return self.rules.copy()
    
    def validate_entity(self, entity_type: str, entity_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate entity data against schema
        
        Args:
            entity_type: Type of entity (e.g., 'Patient', 'ConsentRecord')
            entity_data: Dictionary containing entity data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if entity_type not in self.entity_types:
            errors.append(f"Unknown entity type: {entity_type}")
            return False, errors
        
        # Validate based on entity type
        if entity_type == 'Patient':
            required_fields = ['patient_id', 'demographic_hash', 'created_at', 'active_status']
        elif entity_type == 'ConsentRecord':
            required_fields = ['consent_id', 'patient_ref', 'data_type_ref', 
                             'research_category_ref', 'consent_granted', 
                             'expiry_date', 'last_updated']
        elif entity_type == 'DataType':
            required_fields = ['type_id', 'type_name', 'sensitivity_level', 'required_permissions']
        elif entity_type == 'ResearchCategory':
            required_fields = ['category_id', 'category_name', 'ethics_requirements', 'allowed_data_types']
        elif entity_type == 'PrivacyRule':
            required_fields = ['rule_id', 'rule_name', 'applies_to_data_type', 
                             'anonymization_method', 'k_anonymity_threshold']
        elif entity_type == 'AnonymizationMethod':
            required_fields = ['method_id', 'method_name', 'technique', 'privacy_level']
        else:
            required_fields = []
        
        # Check required fields
        for field in required_fields:
            if field not in entity_data:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors
    
    def create_patient_entity(self, patient_id: str, demographic_hash: str) -> Dict[str, Any]:
        """Create a patient entity with proper structure"""
        return {
            'entity_type': 'Patient',
            'patient_id': patient_id,
            'demographic_hash': demographic_hash,
            'created_at': datetime.now().isoformat(),
            'active_status': True
        }
    
    def create_consent_record(self, consent_id: str, patient_id: str, 
                            data_type_id: str, research_category_id: str,
                            consent_granted: bool, expiry_date: str) -> Dict[str, Any]:
        """Create a consent record entity"""
        return {
            'entity_type': 'ConsentRecord',
            'consent_id': consent_id,
            'patient_ref': patient_id,
            'data_type_ref': data_type_id,
            'research_category_ref': research_category_id,
            'consent_granted': consent_granted,
            'expiry_date': expiry_date,
            'last_updated': datetime.now().isoformat()
        }
    
    def create_data_type(self, type_id: str, type_name: str, 
                        sensitivity_level: str, required_permissions: List[str]) -> Dict[str, Any]:
        """Create a data type entity"""
        return {
            'entity_type': 'DataType',
            'type_id': type_id,
            'type_name': type_name,
            'sensitivity_level': sensitivity_level,
            'required_permissions': required_permissions
        }
    
    def create_research_category(self, category_id: str, category_name: str,
                                ethics_requirements: str, 
                                allowed_data_types: List[str]) -> Dict[str, Any]:
        """Create a research category entity"""
        return {
            'entity_type': 'ResearchCategory',
            'category_id': category_id,
            'category_name': category_name,
            'ethics_requirements': ethics_requirements,
            'allowed_data_types': allowed_data_types
        }
    
    def create_privacy_rule(self, rule_id: str, rule_name: str,
                          data_type_id: str, anonymization_method_id: str,
                          k_anonymity_threshold: int = 5) -> Dict[str, Any]:
        """Create a privacy rule entity"""
        return {
            'entity_type': 'PrivacyRule',
            'rule_id': rule_id,
            'rule_name': rule_name,
            'applies_to_data_type': data_type_id,
            'anonymization_method': anonymization_method_id,
            'k_anonymity_threshold': k_anonymity_threshold
        }
    
    def create_anonymization_method(self, method_id: str, method_name: str,
                                   technique: str, privacy_level: str) -> Dict[str, Any]:
        """Create an anonymization method entity"""
        return {
            'entity_type': 'AnonymizationMethod',
            'method_id': method_id,
            'method_name': method_name,
            'technique': technique,
            'privacy_level': privacy_level
        }
    
    def get_schema_content(self) -> str:
        """Get the raw schema content"""
        return self.schema_content or ""
    
    def get_schema_stats(self) -> Dict[str, int]:
        """Get statistics about the schema"""
        return {
            'entity_types': len(self.entity_types),
            'relationship_types': len(self.relationship_types),
            'rules': len(self.rules)
        }
