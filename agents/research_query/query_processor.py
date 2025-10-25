"""
Query processing and validation for Research Query Agent.
Handles research query parsing, structure validation, and ethical compliance checking.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import re
import uuid
import json
from dataclasses import dataclass
from enum import Enum

from shared.protocols.agent_messages import ResearchQuery, ErrorCodes


class QueryType(Enum):
    """Supported research query types."""
    OBSERVATIONAL = "observational"
    INTERVENTIONAL = "interventional"
    DIAGNOSTIC = "diagnostic"
    EPIDEMIOLOGICAL = "epidemiological"
    GENETIC = "genetic"
    BEHAVIORAL = "behavioral"


class DataSensitivity(Enum):
    """Data sensitivity levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class QueryValidationResult:
    """Result of query validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    ethical_score: float
    complexity_score: float
    estimated_processing_time: int  # seconds


@dataclass
class ParsedQuery:
    """Structured representation of a parsed research query."""
    query_id: str
    researcher_id: str
    query_type: QueryType
    study_title: str
    study_description: str
    data_requirements: Dict[str, Any]
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]
    required_data_types: List[str]
    research_categories: List[str]
    ethical_approval_id: str
    sensitivity_level: DataSensitivity
    expected_sample_size: Optional[int]
    study_duration: Optional[int]  # days
    privacy_requirements: Dict[str, Any]
    metadata: Dict[str, Any]


class QueryValidator:
    """Validates research queries for structure, ethics, and compliance."""
    
    def __init__(self):
        self.required_fields = [
            "researcher_id", "study_description", "data_requirements",
            "ethical_approval_id"
        ]
        
        self.valid_data_types = [
            "demographics", "vital_signs", "lab_results", "medications",
            "diagnoses", "procedures", "imaging", "genomics", "behavioral",
            "social_determinants", "clinical_notes", "device_data"
        ]
        
        self.valid_research_categories = [
            "clinical_trials", "epidemiology", "public_health", "drug_safety",
            "outcomes_research", "health_economics", "quality_improvement",
            "population_health", "precision_medicine", "digital_health"
        ]
        
        self.ethical_requirements = {
            "minimum_approval_level": "institutional",
            "required_privacy_measures": ["anonymization", "access_control"],
            "prohibited_identifiers": ["ssn", "full_name", "address", "phone"],
            "maximum_data_retention": 2555  # 7 years in days
        }
    
    def validate_query_structure(self, query_data: Dict[str, Any]) -> QueryValidationResult:
        """Validate basic query structure and required fields."""
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in query_data or not query_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate researcher ID format
        researcher_id = query_data.get("researcher_id", "")
        if researcher_id and not re.match(r"^[A-Z]{2,4}-\d{4,6}$", researcher_id):
            warnings.append("Researcher ID format should be: PREFIX-NUMBER (e.g., HMS-12345)")
        
        # Validate ethical approval ID
        ethical_approval = query_data.get("ethical_approval_id", "")
        if ethical_approval and not re.match(r"^(IRB|REB|EC)-\d{4}-\d{3,6}$", ethical_approval):
            errors.append("Invalid ethical approval ID format. Expected: IRB-YYYY-NNNNNN")
        
        # Validate data requirements structure
        data_requirements = query_data.get("data_requirements", {})
        if not isinstance(data_requirements, dict):
            errors.append("data_requirements must be a dictionary")
        else:
            self._validate_data_requirements(data_requirements, errors, warnings)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(query_data)
        
        # Estimate processing time based on complexity
        estimated_time = max(30, int(complexity_score * 60))  # 30 seconds minimum
        
        return QueryValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            ethical_score=0.0,  # Will be calculated in ethical validation
            complexity_score=complexity_score,
            estimated_processing_time=estimated_time
        )
    
    def _validate_data_requirements(self, data_requirements: Dict[str, Any], 
                                  errors: List[str], warnings: List[str]):
        """Validate data requirements structure."""
        
        # Check for required data types
        required_types = data_requirements.get("data_types", [])
        if not required_types:
            errors.append("At least one data type must be specified")
        else:
            invalid_types = [dt for dt in required_types if dt not in self.valid_data_types]
            if invalid_types:
                errors.append(f"Invalid data types: {invalid_types}")
        
        # Check research categories
        categories = data_requirements.get("research_categories", [])
        if not categories:
            warnings.append("No research categories specified")
        else:
            invalid_categories = [cat for cat in categories if cat not in self.valid_research_categories]
            if invalid_categories:
                warnings.append(f"Unrecognized research categories: {invalid_categories}")
        
        # Validate sample size requirements
        sample_size = data_requirements.get("minimum_sample_size")
        if sample_size is not None:
            if not isinstance(sample_size, int) or sample_size < 1:
                errors.append("minimum_sample_size must be a positive integer")
            elif sample_size > 100000:
                warnings.append("Large sample size requested - may require special approval")
        
        # Validate date ranges
        date_range = data_requirements.get("date_range", {})
        if date_range:
            start_date = date_range.get("start_date")
            end_date = date_range.get("end_date")
            
            if start_date and end_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    
                    if start >= end:
                        errors.append("start_date must be before end_date")
                    
                    # Check if date range is too broad
                    if (end - start).days > 3650:  # 10 years
                        warnings.append("Date range spans more than 10 years - consider narrowing scope")
                        
                except ValueError:
                    errors.append("Invalid date format in date_range")
    
    def validate_ethical_compliance(self, query_data: Dict[str, Any]) -> QueryValidationResult:
        """Validate ethical compliance and calculate ethical score."""
        errors = []
        warnings = []
        ethical_score = 1.0
        
        # Check ethical approval validity
        ethical_approval = query_data.get("ethical_approval_id", "")
        if not self._validate_ethical_approval(ethical_approval):
            errors.append("Invalid or expired ethical approval")
            ethical_score -= 0.5
        
        # Check for prohibited data requests
        data_requirements = query_data.get("data_requirements", {})
        prohibited_check = self._check_prohibited_data(data_requirements)
        if prohibited_check["violations"]:
            errors.extend(prohibited_check["violations"])
            ethical_score -= 0.3
        
        # Validate privacy requirements
        privacy_requirements = query_data.get("privacy_requirements", {})
        privacy_score = self._validate_privacy_requirements(privacy_requirements)
        ethical_score *= privacy_score
        
        # Check study purpose legitimacy
        study_description = query_data.get("study_description", "")
        purpose_score = self._validate_study_purpose(study_description)
        ethical_score *= purpose_score
        
        if purpose_score < 0.7:
            warnings.append("Study purpose may require additional ethical review")
        
        # Check data retention requirements
        retention_days = data_requirements.get("data_retention_days", 365)
        if retention_days > self.ethical_requirements["maximum_data_retention"]:
            errors.append(f"Data retention period exceeds maximum allowed ({self.ethical_requirements['maximum_data_retention']} days)")
            ethical_score -= 0.2
        
        return QueryValidationResult(
            is_valid=len(errors) == 0 and ethical_score >= 0.6,
            errors=errors,
            warnings=warnings,
            ethical_score=max(0.0, ethical_score),
            complexity_score=0.0,  # Not calculated here
            estimated_processing_time=0  # Not calculated here
        )
    
    def _validate_ethical_approval(self, approval_id: str) -> bool:
        """Validate ethical approval ID format and simulate approval check."""
        if not re.match(r"^(IRB|REB|EC)-\d{4}-\d{3,6}$", approval_id):
            return False
        
        # Extract year from approval ID
        try:
            year = int(approval_id.split('-')[1])
            current_year = datetime.now().year
            
            # Approval should be from current year or previous year
            return current_year - 1 <= year <= current_year
        except (IndexError, ValueError):
            return False
    
    def _check_prohibited_data(self, data_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check for requests of prohibited data types."""
        violations = []
        
        # Check for prohibited identifiers
        requested_fields = data_requirements.get("specific_fields", [])
        prohibited_fields = []
        
        for field in requested_fields:
            field_lower = field.lower()
            for prohibited in self.ethical_requirements["prohibited_identifiers"]:
                if prohibited in field_lower:
                    prohibited_fields.append(field)
        
        if prohibited_fields:
            violations.append(f"Prohibited identifiers requested: {prohibited_fields}")
        
        # Check for high-risk data combinations
        data_types = data_requirements.get("data_types", [])
        if "genomics" in data_types and "demographics" in data_types:
            if not data_requirements.get("enhanced_anonymization", False):
                violations.append("Genomics + demographics requires enhanced anonymization")
        
        return {"violations": violations, "prohibited_fields": prohibited_fields}
    
    def _validate_privacy_requirements(self, privacy_requirements: Dict[str, Any]) -> float:
        """Validate and score privacy requirements."""
        score = 1.0
        
        # Check for required privacy measures
        required_measures = self.ethical_requirements["required_privacy_measures"]
        specified_measures = privacy_requirements.get("anonymization_methods", [])
        
        missing_measures = set(required_measures) - set(specified_measures)
        if missing_measures:
            score -= 0.2 * len(missing_measures)
        
        # Bonus for additional privacy measures
        additional_measures = ["differential_privacy", "k_anonymity", "l_diversity"]
        bonus_measures = set(specified_measures) & set(additional_measures)
        score += 0.1 * len(bonus_measures)
        
        return max(0.0, min(1.0, score))
    
    def _validate_study_purpose(self, study_description: str) -> float:
        """Validate study purpose and calculate legitimacy score."""
        if not study_description or len(study_description) < 50:
            return 0.3  # Very low score for insufficient description
        
        # Check for legitimate research keywords
        legitimate_keywords = [
            "treatment", "diagnosis", "prevention", "outcomes", "efficacy",
            "safety", "epidemiology", "public health", "clinical trial",
            "observational", "cohort", "case-control", "intervention"
        ]
        
        description_lower = study_description.lower()
        keyword_matches = sum(1 for keyword in legitimate_keywords if keyword in description_lower)
        
        # Base score from keyword matches
        score = min(1.0, keyword_matches / 5.0)
        
        # Check for concerning terms
        concerning_terms = ["commercial", "marketing", "profit", "sale", "advertisement"]
        concerning_matches = sum(1 for term in concerning_terms if term in description_lower)
        
        if concerning_matches > 0:
            score -= 0.3 * concerning_matches
        
        return max(0.0, score)
    
    def _calculate_complexity_score(self, query_data: Dict[str, Any]) -> float:
        """Calculate query complexity score (0.0 to 1.0)."""
        complexity = 0.0
        
        data_requirements = query_data.get("data_requirements", {})
        
        # Data types complexity
        data_types = data_requirements.get("data_types", [])
        complexity += min(0.3, len(data_types) * 0.05)
        
        # Sample size complexity
        sample_size = data_requirements.get("minimum_sample_size", 0)
        if sample_size > 10000:
            complexity += 0.2
        elif sample_size > 1000:
            complexity += 0.1
        
        # Date range complexity
        date_range = data_requirements.get("date_range", {})
        if date_range:
            try:
                start = datetime.fromisoformat(date_range.get("start_date", "").replace('Z', '+00:00'))
                end = datetime.fromisoformat(date_range.get("end_date", "").replace('Z', '+00:00'))
                days = (end - start).days
                
                if days > 1825:  # 5 years
                    complexity += 0.2
                elif days > 365:  # 1 year
                    complexity += 0.1
            except (ValueError, TypeError):
                pass
        
        # Inclusion/exclusion criteria complexity
        inclusion_criteria = query_data.get("inclusion_criteria", [])
        exclusion_criteria = query_data.get("exclusion_criteria", [])
        criteria_count = len(inclusion_criteria) + len(exclusion_criteria)
        complexity += min(0.2, criteria_count * 0.02)
        
        # Special requirements complexity
        if data_requirements.get("longitudinal_data", False):
            complexity += 0.1
        
        if data_requirements.get("multi_site_data", False):
            complexity += 0.1
        
        return min(1.0, complexity)


class QueryProcessor:
    """Processes and parses research queries into structured format."""
    
    def __init__(self):
        self.validator = QueryValidator()
    
    def parse_research_query(self, query_data: Dict[str, Any]) -> Tuple[ParsedQuery, QueryValidationResult]:
        """Parse research query into structured format with validation."""
        
        # First validate the query structure
        validation_result = self.validator.validate_query_structure(query_data)
        
        if not validation_result.is_valid:
            # Return empty parsed query if validation fails
            return None, validation_result
        
        # Parse query into structured format
        try:
            parsed_query = ParsedQuery(
                query_id=query_data.get("query_id", str(uuid.uuid4())),
                researcher_id=query_data["researcher_id"],
                query_type=self._determine_query_type(query_data),
                study_title=query_data.get("study_title", "Untitled Study"),
                study_description=query_data["study_description"],
                data_requirements=query_data["data_requirements"],
                inclusion_criteria=query_data.get("inclusion_criteria", []),
                exclusion_criteria=query_data.get("exclusion_criteria", []),
                required_data_types=query_data["data_requirements"].get("data_types", []),
                research_categories=query_data["data_requirements"].get("research_categories", []),
                ethical_approval_id=query_data["ethical_approval_id"],
                sensitivity_level=self._determine_sensitivity_level(query_data),
                expected_sample_size=query_data["data_requirements"].get("minimum_sample_size"),
                study_duration=query_data.get("study_duration_days"),
                privacy_requirements=query_data.get("privacy_requirements", {}),
                metadata=query_data.get("metadata", {})
            )
            
            return parsed_query, validation_result
            
        except Exception as e:
            validation_result.errors.append(f"Failed to parse query: {str(e)}")
            validation_result.is_valid = False
            return None, validation_result
    
    def validate_ethical_compliance(self, parsed_query: ParsedQuery) -> QueryValidationResult:
        """Validate ethical compliance for parsed query."""
        query_data = {
            "researcher_id": parsed_query.researcher_id,
            "study_description": parsed_query.study_description,
            "data_requirements": parsed_query.data_requirements,
            "ethical_approval_id": parsed_query.ethical_approval_id,
            "privacy_requirements": parsed_query.privacy_requirements
        }
        
        return self.validator.validate_ethical_compliance(query_data)
    
    def _determine_query_type(self, query_data: Dict[str, Any]) -> QueryType:
        """Determine query type based on study description and requirements."""
        description = query_data.get("study_description", "").lower()
        
        if any(term in description for term in ["intervention", "treatment", "therapy", "clinical trial"]):
            return QueryType.INTERVENTIONAL
        elif any(term in description for term in ["diagnostic", "diagnosis", "screening"]):
            return QueryType.DIAGNOSTIC
        elif any(term in description for term in ["genetic", "genomic", "dna", "mutation"]):
            return QueryType.GENETIC
        elif any(term in description for term in ["behavior", "psychological", "mental health"]):
            return QueryType.BEHAVIORAL
        elif any(term in description for term in ["epidemiology", "population", "outbreak"]):
            return QueryType.EPIDEMIOLOGICAL
        else:
            return QueryType.OBSERVATIONAL
    
    def _determine_sensitivity_level(self, query_data: Dict[str, Any]) -> DataSensitivity:
        """Determine data sensitivity level based on requirements."""
        data_types = query_data.get("data_requirements", {}).get("data_types", [])
        
        # High sensitivity data types
        if any(dt in data_types for dt in ["genomics", "behavioral", "clinical_notes"]):
            return DataSensitivity.RESTRICTED
        
        # Medium sensitivity data types
        if any(dt in data_types for dt in ["diagnoses", "medications", "procedures"]):
            return DataSensitivity.CONFIDENTIAL
        
        # Low sensitivity data types
        if any(dt in data_types for dt in ["demographics", "vital_signs"]):
            return DataSensitivity.INTERNAL
        
        return DataSensitivity.PUBLIC
    
    def create_query_summary(self, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Create summary of parsed query for logging and tracking."""
        return {
            "query_id": parsed_query.query_id,
            "researcher_id": parsed_query.researcher_id,
            "query_type": parsed_query.query_type.value,
            "study_title": parsed_query.study_title,
            "data_types_count": len(parsed_query.required_data_types),
            "research_categories_count": len(parsed_query.research_categories),
            "sensitivity_level": parsed_query.sensitivity_level.value,
            "expected_sample_size": parsed_query.expected_sample_size,
            "has_inclusion_criteria": len(parsed_query.inclusion_criteria) > 0,
            "has_exclusion_criteria": len(parsed_query.exclusion_criteria) > 0,
            "ethical_approval_id": parsed_query.ethical_approval_id,
            "created_at": datetime.utcnow().isoformat()
        }