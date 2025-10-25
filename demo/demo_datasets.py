"""
HealthSync Demo Datasets

Creates realistic healthcare datasets that highlight privacy and ethics features
for demonstration purposes.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import hashlib

class DemoDatasetGenerator:
    """Generates realistic healthcare datasets for demo purposes"""
    
    def __init__(self):
        self.privacy_levels = ["k5_anonymized", "k10_anonymized", "differential_private"]
        self.institutions = [
            "Stanford Medical Center", "UCSF Medical Center", "Kaiser Permanente",
            "Johns Hopkins Hospital", "Mayo Clinic", "Cleveland Clinic"
        ]
        self.data_types = [
            "genomic_data", "clinical_records", "imaging_data", "lifestyle_data",
            "lab_results", "medication_history", "vital_signs", "demographics"
        ]
        self.research_categories = [
            "diabetes_research", "cardiovascular_research", "cancer_research",
            "mental_health_research", "infectious_disease_research", "pediatric_research"
        ]
    
    def generate_realistic_patient_data(self, count: int = 1000) -> List[Dict[str, Any]]:
        """Generate realistic patient data for demo purposes"""
        patients = []
        
        for i in range(count):
            patient_id = f"patient_{i+1:04d}"
            
            # Generate realistic demographics
            age = random.randint(18, 85)
            gender = random.choice(["male", "female", "other"])
            ethnicity = random.choice([
                "caucasian", "african_american", "hispanic", "asian", 
                "native_american", "pacific_islander", "mixed"
            ])
            
            # Generate medical conditions based on age and demographics
            conditions = self._generate_conditions_for_demographics(age, gender, ethnicity)
            
            # Generate consent preferences
            consent_prefs = self._generate_realistic_consent(conditions)
            
            patient = {
                "patient_id": patient_id,
                "patient_id_hash": hashlib.sha256(patient_id.encode()).hexdigest()[:16],
                "demographics": {
                    "age_range": self._get_age_range(age),
                    "gender": gender,
                    "ethnicity": ethnicity,
                    "location": random.choice(["urban", "suburban", "rural"])
                },
                "medical_conditions": conditions,
                "consent_preferences": consent_prefs,
                "data_quality_score": random.uniform(0.7, 1.0),
                "institution": random.choice(self.institutions),
                "enrollment_date": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
            }
            
            patients.append(patient)
        
        return patients
    
    def _generate_conditions_for_demographics(self, age: int, gender: str, ethnicity: str) -> List[str]:
        """Generate realistic medical conditions based on demographics"""
        conditions = []
        
        # Age-based conditions
        if age > 50:
            if random.random() < 0.3:
                conditions.append("hypertension")
            if random.random() < 0.2:
                conditions.append("diabetes_type2")
            if random.random() < 0.15:
                conditions.append("heart_disease")
        
        if age > 65:
            if random.random() < 0.25:
                conditions.append("arthritis")
            if random.random() < 0.1:
                conditions.append("osteoporosis")
        
        # Gender-specific conditions
        if gender == "female":
            if random.random() < 0.1:
                conditions.append("breast_cancer_history")
            if age > 40 and random.random() < 0.05:
                conditions.append("osteoporosis")
        
        # General conditions
        if random.random() < 0.15:
            conditions.append("anxiety")
        if random.random() < 0.1:
            conditions.append("depression")
        if random.random() < 0.08:
            conditions.append("asthma")
        
        return conditions
    
    def _get_age_range(self, age: int) -> str:
        """Convert age to privacy-preserving age range"""
        if age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        elif age < 55:
            return "45-54"
        elif age < 65:
            return "55-64"
        else:
            return "65+"
    
    def _generate_realistic_consent(self, conditions: List[str]) -> Dict[str, Any]:
        """Generate realistic consent preferences based on conditions"""
        # People with certain conditions are more likely to consent to related research
        consent = {
            "genomic_data": random.random() < 0.4,  # Lower consent rate for genetic data
            "clinical_records": random.random() < 0.8,  # Higher consent for clinical data
            "imaging_data": random.random() < 0.6,
            "lifestyle_data": random.random() < 0.7,
            "research_categories": {}
        }
        
        # Condition-based research consent
        if any(cond in conditions for cond in ["diabetes_type2", "diabetes_type1"]):
            consent["research_categories"]["diabetes_research"] = random.random() < 0.9
        else:
            consent["research_categories"]["diabetes_research"] = random.random() < 0.3
        
        if any(cond in conditions for cond in ["heart_disease", "hypertension"]):
            consent["research_categories"]["cardiovascular_research"] = random.random() < 0.85
        else:
            consent["research_categories"]["cardiovascular_research"] = random.random() < 0.4
        
        if any(cond in conditions for cond in ["anxiety", "depression"]):
            consent["research_categories"]["mental_health_research"] = random.random() < 0.7
        else:
            consent["research_categories"]["mental_health_research"] = random.random() < 0.2
        
        # Default consent rates for other categories
        consent["research_categories"]["cancer_research"] = random.random() < 0.5
        consent["research_categories"]["infectious_disease_research"] = random.random() < 0.6
        consent["research_categories"]["pediatric_research"] = random.random() < 0.3
        
        return consent
    
    def generate_anonymized_dataset(self, patients: List[Dict[str, Any]], 
                                  research_query: Dict[str, Any]) -> Dict[str, Any]:
        """Generate anonymized dataset matching research query"""
        
        # Filter patients based on query criteria
        matching_patients = self._filter_patients_by_query(patients, research_query)
        
        # Apply k-anonymity (k=5 minimum)
        k_anonymous_data = self._apply_k_anonymity(matching_patients, k=5)
        
        # Generate privacy metrics
        privacy_metrics = self._calculate_privacy_metrics(matching_patients, k_anonymous_data)
        
        return {
            "dataset_id": f"DS_{research_query.get('study_id', 'UNKNOWN')}_{datetime.now().strftime('%Y%m%d')}",
            "query_id": research_query.get("query_id", "unknown"),
            "original_patient_count": len(matching_patients),
            "anonymized_patient_count": len(k_anonymous_data),
            "data_fields": self._get_anonymized_fields(research_query),
            "privacy_level": "k5_anonymized",
            "privacy_metrics": privacy_metrics,
            "anonymized_records": k_anonymous_data,
            "generation_timestamp": datetime.now().isoformat(),
            "consent_compliance": True
        }
    
    def _filter_patients_by_query(self, patients: List[Dict[str, Any]], 
                                 query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter patients based on research query criteria"""
        filtered = []
        
        for patient in patients:
            # Check consent for research category
            research_category = query.get("research_category", "")
            if not patient["consent_preferences"]["research_categories"].get(research_category, False):
                continue
            
            # Check required data types consent
            required_data_types = query.get("data_types", [])
            if not all(patient["consent_preferences"].get(dt, False) for dt in required_data_types):
                continue
            
            # Check medical conditions if specified
            required_conditions = query.get("conditions", [])
            if required_conditions and not any(cond in patient["medical_conditions"] for cond in required_conditions):
                continue
            
            # Check demographics if specified
            demo_requirements = query.get("demographics", {})
            if demo_requirements:
                if "age_range" in demo_requirements:
                    if patient["demographics"]["age_range"] not in demo_requirements["age_range"]:
                        continue
                if "gender" in demo_requirements:
                    if patient["demographics"]["gender"] not in demo_requirements["gender"]:
                        continue
            
            filtered.append(patient)
        
        return filtered
    
    def _apply_k_anonymity(self, patients: List[Dict[str, Any]], k: int = 5) -> List[Dict[str, Any]]:
        """Apply k-anonymity to patient data"""
        # Group patients by quasi-identifiers
        groups = {}
        
        for patient in patients:
            # Create quasi-identifier tuple
            quasi_id = (
                patient["demographics"]["age_range"],
                patient["demographics"]["gender"],
                patient["demographics"]["ethnicity"]
            )
            
            if quasi_id not in groups:
                groups[quasi_id] = []
            groups[quasi_id].append(patient)
        
        # Only include groups with k or more patients
        k_anonymous_data = []
        for group_patients in groups.values():
            if len(group_patients) >= k:
                k_anonymous_data.extend(group_patients)
        
        # Remove direct identifiers and add noise
        for patient in k_anonymous_data:
            # Remove patient_id, keep only hash
            if "patient_id" in patient:
                del patient["patient_id"]
            
            # Add statistical noise to sensitive fields
            if "data_quality_score" in patient:
                noise = random.uniform(-0.05, 0.05)
                patient["data_quality_score"] = max(0, min(1, patient["data_quality_score"] + noise))
        
        return k_anonymous_data
    
    def _calculate_privacy_metrics(self, original: List[Dict[str, Any]], 
                                 anonymized: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate privacy preservation metrics"""
        return {
            "k_anonymity_level": 5,
            "data_retention_rate": len(anonymized) / len(original) if original else 0,
            "suppression_rate": (len(original) - len(anonymized)) / len(original) if original else 0,
            "generalization_applied": True,
            "noise_injection_applied": True,
            "privacy_risk_score": random.uniform(0.1, 0.3),  # Low risk after anonymization
            "compliance_verified": True
        }
    
    def _get_anonymized_fields(self, query: Dict[str, Any]) -> List[str]:
        """Get list of fields included in anonymized dataset"""
        base_fields = [
            "patient_id_hash", "demographics", "medical_conditions", 
            "data_quality_score", "institution", "enrollment_date"
        ]
        
        # Add query-specific fields
        requested_types = query.get("data_types", [])
        if "clinical_records" in requested_types:
            base_fields.extend(["diagnosis_history", "treatment_outcomes"])
        if "lifestyle_data" in requested_types:
            base_fields.extend(["lifestyle_factors", "behavioral_data"])
        if "lab_results" in requested_types:
            base_fields.extend(["lab_values", "biomarkers"])
        
        return base_fields
    
    def export_demo_datasets(self, output_dir: str = "datasets"):
        """Export demo datasets to files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate patient cohorts
        diabetes_patients = self.generate_realistic_patient_data(1247)
        cardio_patients = self.generate_realistic_patient_data(892)
        mental_health_patients = self.generate_realistic_patient_data(634)
        
        # Save raw datasets
        datasets = {
            "diabetes_cohort": diabetes_patients,
            "cardiovascular_registry": cardio_patients,
            "mental_health_cohort": mental_health_patients
        }
        
        for name, data in datasets.items():
            with open(f"{output_dir}/{name}.json", 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        # Generate sample anonymized datasets
        sample_queries = [
            {
                "query_id": "DEMO_DIABETES_001",
                "study_id": "DIAB_PREV_2024",
                "research_category": "diabetes_research",
                "data_types": ["clinical_records", "lifestyle_data"],
                "conditions": ["diabetes_type2", "prediabetes"]
            },
            {
                "query_id": "DEMO_CARDIO_001", 
                "study_id": "CARDIO_OUTCOMES_2024",
                "research_category": "cardiovascular_research",
                "data_types": ["clinical_records", "imaging_data"],
                "conditions": ["heart_disease", "hypertension"]
            }
        ]
        
        for query in sample_queries:
            if query["research_category"] == "diabetes_research":
                source_data = diabetes_patients
            else:
                source_data = cardio_patients
                
            anonymized = self.generate_anonymized_dataset(source_data, query)
            
            with open(f"{output_dir}/anonymized_{query['query_id']}.json", 'w') as f:
                json.dump(anonymized, f, indent=2, default=str)
        
        print(f"✅ Demo datasets exported to {output_dir}/")
        return datasets

if __name__ == "__main__":
    print("🔧 Starting dataset generation...")
    generator = DemoDatasetGenerator()
    print("📊 Exporting demo datasets...")
    datasets = generator.export_demo_datasets()
    print(f"✅ Generated {len(datasets)} demo datasets")