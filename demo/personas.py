"""
HealthSync Demo Personas and Sample Data

This module contains realistic patient and researcher personas with sample data
for demonstrating the HealthSync system capabilities.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class DemoPersonas:
    """Manages demo personas and their associated data"""
    
    def __init__(self):
        self.patients = self._create_patient_personas()
        self.researchers = self._create_researcher_personas()
        self.demo_datasets = self._create_demo_datasets()
    
    def _create_patient_personas(self) -> List[Dict[str, Any]]:
        """Create realistic patient personas with diverse backgrounds"""
        return [
            {
                "patient_id": "patient_001",
                "name": "Sarah Chen",
                "age": 34,
                "demographics": {
                    "gender": "female",
                    "ethnicity": "asian",
                    "location": "urban",
                    "education": "college"
                },
                "medical_conditions": ["diabetes_type2", "hypertension"],
                "consent_preferences": {
                    "genomic_data": True,
                    "clinical_records": True,
                    "imaging_data": False,
                    "lifestyle_data": True,
                    "research_categories": {
                        "diabetes_research": True,
                        "cardiovascular_research": True,
                        "cancer_research": False,
                        "mental_health_research": False
                    }
                },
                "consent_history": [
                    {
                        "timestamp": datetime.now() - timedelta(days=30),
                        "action": "initial_consent",
                        "changes": "granted_all_diabetes_research"
                    },
                    {
                        "timestamp": datetime.now() - timedelta(days=15),
                        "action": "updated_consent",
                        "changes": "revoked_imaging_data_sharing"
                    }
                ],
                "story": "Tech professional diagnosed with Type 2 diabetes, actively manages health through technology"
            },
            {
                "patient_id": "patient_002", 
                "name": "Marcus Johnson",
                "age": 67,
                "demographics": {
                    "gender": "male",
                    "ethnicity": "african_american",
                    "location": "rural",
                    "education": "high_school"
                },
                "medical_conditions": ["heart_disease", "arthritis", "diabetes_type2"],
                "consent_preferences": {
                    "genomic_data": False,
                    "clinical_records": True,
                    "imaging_data": True,
                    "lifestyle_data": False,
                    "research_categories": {
                        "diabetes_research": True,
                        "cardiovascular_research": True,
                        "cancer_research": False,
                        "mental_health_research": False
                    }
                },
                "consent_history": [
                    {
                        "timestamp": datetime.now() - timedelta(days=45),
                        "action": "initial_consent",
                        "changes": "selective_consent_cardiovascular_only"
                    }
                ],
                "story": "Retired factory worker with multiple chronic conditions, cautious about genetic data sharing"
            },
            {
                "patient_id": "patient_003",
                "name": "Emma Rodriguez",
                "age": 28,
                "demographics": {
                    "gender": "female", 
                    "ethnicity": "hispanic",
                    "location": "suburban",
                    "education": "graduate"
                },
                "medical_conditions": ["anxiety", "migraines"],
                "consent_preferences": {
                    "genomic_data": True,
                    "clinical_records": True,
                    "imaging_data": True,
                    "lifestyle_data": True,
                    "research_categories": {
                        "diabetes_research": False,
                        "cardiovascular_research": False,
                        "cancer_research": True,
                        "mental_health_research": True
                    }
                },
                "consent_history": [
                    {
                        "timestamp": datetime.now() - timedelta(days=10),
                        "action": "initial_consent",
                        "changes": "granted_all_mental_health_research"
                    }
                ],
                "story": "Graduate student in psychology, interested in contributing to mental health research"
            }
        ]
    
    def _create_researcher_personas(self) -> List[Dict[str, Any]]:
        """Create realistic researcher personas with different research focuses"""
        return [
            {
                "researcher_id": "researcher_001",
                "name": "Dr. Jennifer Park",
                "institution": "Stanford Medical Center",
                "department": "Endocrinology",
                "research_focus": "diabetes_prevention",
                "credentials": {
                    "degree": "MD, PhD",
                    "years_experience": 12,
                    "publications": 45,
                    "ethics_certifications": ["IRB_certified", "CITI_trained"]
                },
                "current_studies": [
                    {
                        "study_id": "DIAB_PREV_2024",
                        "title": "AI-Driven Diabetes Prevention in Urban Populations",
                        "ethics_approval": "IRB-2024-001",
                        "data_requirements": {
                            "patient_count_min": 1000,
                            "data_types": ["clinical_records", "lifestyle_data"],
                            "demographics": ["urban", "age_25_65"],
                            "conditions": ["prediabetes", "diabetes_type2"]
                        }
                    }
                ],
                "story": "Leading researcher in diabetes prevention using AI and population health data"
            },
            {
                "researcher_id": "researcher_002",
                "name": "Dr. Michael Thompson",
                "institution": "Johns Hopkins University",
                "department": "Cardiology",
                "research_focus": "cardiovascular_outcomes",
                "credentials": {
                    "degree": "MD",
                    "years_experience": 8,
                    "publications": 23,
                    "ethics_certifications": ["IRB_certified", "GCP_certified"]
                },
                "current_studies": [
                    {
                        "study_id": "CARDIO_OUTCOMES_2024",
                        "title": "Multi-ethnic Cardiovascular Risk Assessment",
                        "ethics_approval": "IRB-2024-002", 
                        "data_requirements": {
                            "patient_count_min": 500,
                            "data_types": ["clinical_records", "imaging_data"],
                            "demographics": ["diverse_ethnicity", "age_40_80"],
                            "conditions": ["heart_disease", "hypertension"]
                        }
                    }
                ],
                "story": "Cardiologist researching health disparities in cardiovascular outcomes"
            }
        ]
    
    def _create_demo_datasets(self) -> Dict[str, Any]:
        """Create sample datasets that highlight privacy and ethics features"""
        return {
            "diabetes_cohort": {
                "dataset_id": "DS_DIABETES_001",
                "description": "Longitudinal diabetes patient data from multiple institutions",
                "patient_count": 1247,
                "data_fields": [
                    "patient_id_hash", "age_range", "gender", "ethnicity_category",
                    "diagnosis_date", "hba1c_levels", "medication_history",
                    "complication_status", "lifestyle_factors"
                ],
                "privacy_level": "k5_anonymized",
                "consent_coverage": 0.78,  # 78% of patients consented
                "institutions": ["Stanford Medical", "UCSF", "Kaiser Permanente"]
            },
            "cardiovascular_registry": {
                "dataset_id": "DS_CARDIO_001", 
                "description": "Multi-ethnic cardiovascular outcomes registry",
                "patient_count": 892,
                "data_fields": [
                    "patient_id_hash", "age_range", "gender", "ethnicity_category",
                    "cardiac_events", "imaging_results", "risk_factors",
                    "treatment_outcomes", "follow_up_duration"
                ],
                "privacy_level": "k5_anonymized",
                "consent_coverage": 0.85,
                "institutions": ["Johns Hopkins", "Mayo Clinic", "Cleveland Clinic"]
            },
            "mental_health_cohort": {
                "dataset_id": "DS_MENTAL_001",
                "description": "Mental health treatment outcomes in young adults",
                "patient_count": 634,
                "data_fields": [
                    "patient_id_hash", "age_range", "gender", "diagnosis_category",
                    "treatment_type", "outcome_measures", "duration_treatment",
                    "comorbidities", "social_factors"
                ],
                "privacy_level": "k5_anonymized", 
                "consent_coverage": 0.92,
                "institutions": ["UCLA Medical", "NYU Langone", "Mass General"]
            }
        }
    
    def get_patient_by_id(self, patient_id: str) -> Dict[str, Any]:
        """Get patient persona by ID"""
        for patient in self.patients:
            if patient["patient_id"] == patient_id:
                return patient
        return None
    
    def get_researcher_by_id(self, researcher_id: str) -> Dict[str, Any]:
        """Get researcher persona by ID"""
        for researcher in self.researchers:
            if researcher["researcher_id"] == researcher_id:
                return researcher
        return None
    
    def get_matching_datasets(self, research_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find datasets matching research requirements"""
        matching = []
        for dataset_id, dataset in self.demo_datasets.items():
            # Simple matching logic for demo purposes
            if dataset["consent_coverage"] > 0.7:  # Sufficient consent coverage
                matching.append(dataset)
        return matching
    
    def export_personas_json(self, filepath: str):
        """Export all personas to JSON file for easy loading"""
        data = {
            "patients": self.patients,
            "researchers": self.researchers,
            "datasets": self.demo_datasets,
            "generated_at": datetime.now().isoformat()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

if __name__ == "__main__":
    # Generate demo personas
    personas = DemoPersonas()
    personas.export_personas_json("demo/personas_data.json")
    print("Demo personas generated successfully!")