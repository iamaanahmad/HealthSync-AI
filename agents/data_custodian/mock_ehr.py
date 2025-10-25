"""
Mock EHR (Electronic Health Record) system for HealthSync.
Simulates healthcare datasets with realistic medical data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import random
import hashlib


class MockPatientRecord:
    """Represents a mock patient medical record."""
    
    def __init__(self, patient_id: str, demographics: Dict[str, Any], 
                 medical_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        self.record_id = self._generate_record_id(patient_id)
        self.patient_id = patient_id
        self.demographics = demographics
        self.medical_data = medical_data
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.data_quality_score = self._calculate_quality_score()
    
    def _generate_record_id(self, patient_id: str) -> str:
        """Generate unique record ID."""
        unique_str = f"{patient_id}:{datetime.utcnow().isoformat()}"
        return f"REC-{hashlib.md5(unique_str.encode()).hexdigest()[:12].upper()}"
    
    def _calculate_quality_score(self) -> float:
        """Calculate data quality score based on completeness."""
        total_fields = 0
        complete_fields = 0
        
        for value in self.demographics.values():
            total_fields += 1
            if value is not None and value != "":
                complete_fields += 1
        
        for value in self.medical_data.values():
            total_fields += 1
            if value is not None and value != "":
                complete_fields += 1
        
        return complete_fields / total_fields if total_fields > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "record_id": self.record_id,
            "patient_id": self.patient_id,
            "demographics": self.demographics,
            "medical_data": self.medical_data,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "data_quality_score": self.data_quality_score
        }


class MockEHRSystem:
    """Mock EHR system that simulates healthcare data storage and retrieval."""
    
    # Data type definitions
    DATA_TYPES = [
        "demographics",
        "diagnoses",
        "medications",
        "lab_results",
        "vital_signs",
        "procedures",
        "allergies",
        "immunizations"
    ]
    
    # Research category definitions
    RESEARCH_CATEGORIES = [
        "cardiovascular_research",
        "diabetes_research",
        "cancer_research",
        "infectious_disease_research",
        "mental_health_research",
        "general_medical_research"
    ]
    
    def __init__(self, institution_id: str = "MOCK_HOSPITAL_001"):
        self.institution_id = institution_id
        self.records: Dict[str, MockPatientRecord] = {}
        self.datasets: Dict[str, Dict[str, Any]] = {}
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock patient records with realistic data."""
        # Generate 50 mock patient records
        for i in range(50):
            patient_id = f"PAT-{str(i+1).zfill(6)}"
            record = self._generate_mock_patient_record(patient_id)
            self.records[patient_id] = record
        
        # Create categorized datasets
        self._create_datasets()
    
    def _generate_mock_patient_record(self, patient_id: str) -> MockPatientRecord:
        """Generate a realistic mock patient record."""
        age = random.randint(18, 85)
        gender = random.choice(["Male", "Female", "Other"])
        
        demographics = {
            "age": age,
            "gender": gender,
            "ethnicity": random.choice(["Caucasian", "African American", "Hispanic", "Asian", "Other"]),
            "zip_code": f"{random.randint(10000, 99999)}",
            "insurance_type": random.choice(["Private", "Medicare", "Medicaid", "Uninsured"])
        }
        
        # Generate medical data based on age and random conditions
        medical_data = {
            "diagnoses": self._generate_diagnoses(age),
            "medications": self._generate_medications(age),
            "lab_results": self._generate_lab_results(),
            "vital_signs": self._generate_vital_signs(age),
            "procedures": self._generate_procedures(),
            "allergies": self._generate_allergies(),
            "immunizations": self._generate_immunizations(age)
        }
        
        metadata = {
            "institution_id": self.institution_id,
            "record_status": "active",
            "last_visit": (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat()
        }
        
        return MockPatientRecord(patient_id, demographics, medical_data, metadata)
    
    def _generate_diagnoses(self, age: int) -> List[Dict[str, Any]]:
        """Generate realistic diagnoses based on age."""
        diagnoses = []
        
        # Age-related conditions
        if age > 50:
            if random.random() < 0.3:
                diagnoses.append({
                    "icd10_code": "I10",
                    "description": "Essential (primary) hypertension",
                    "diagnosed_date": (datetime.utcnow() - timedelta(days=random.randint(365, 3650))).isoformat(),
                    "severity": random.choice(["mild", "moderate", "severe"])
                })
            if random.random() < 0.2:
                diagnoses.append({
                    "icd10_code": "E11",
                    "description": "Type 2 diabetes mellitus",
                    "diagnosed_date": (datetime.utcnow() - timedelta(days=random.randint(365, 3650))).isoformat(),
                    "severity": random.choice(["controlled", "uncontrolled"])
                })
        
        if age > 60:
            if random.random() < 0.15:
                diagnoses.append({
                    "icd10_code": "I25.10",
                    "description": "Atherosclerotic heart disease",
                    "diagnosed_date": (datetime.utcnow() - timedelta(days=random.randint(365, 3650))).isoformat(),
                    "severity": random.choice(["mild", "moderate", "severe"])
                })
        
        # Common conditions
        if random.random() < 0.1:
            diagnoses.append({
                "icd10_code": "J45",
                "description": "Asthma",
                "diagnosed_date": (datetime.utcnow() - timedelta(days=random.randint(365, 7300))).isoformat(),
                "severity": random.choice(["mild", "moderate", "severe"])
            })
        
        return diagnoses
    
    def _generate_medications(self, age: int) -> List[Dict[str, Any]]:
        """Generate realistic medications."""
        medications = []
        
        if age > 50 and random.random() < 0.3:
            medications.append({
                "name": "Lisinopril",
                "dosage": "10mg",
                "frequency": "once daily",
                "start_date": (datetime.utcnow() - timedelta(days=random.randint(30, 1095))).isoformat(),
                "indication": "Hypertension"
            })
        
        if age > 50 and random.random() < 0.2:
            medications.append({
                "name": "Metformin",
                "dosage": "500mg",
                "frequency": "twice daily",
                "start_date": (datetime.utcnow() - timedelta(days=random.randint(30, 1095))).isoformat(),
                "indication": "Type 2 Diabetes"
            })
        
        if random.random() < 0.15:
            medications.append({
                "name": "Atorvastatin",
                "dosage": "20mg",
                "frequency": "once daily",
                "start_date": (datetime.utcnow() - timedelta(days=random.randint(30, 1095))).isoformat(),
                "indication": "High cholesterol"
            })
        
        return medications
    
    def _generate_lab_results(self) -> List[Dict[str, Any]]:
        """Generate realistic lab results."""
        return [
            {
                "test_name": "Hemoglobin A1C",
                "value": round(random.uniform(4.5, 8.5), 1),
                "unit": "%",
                "reference_range": "4.0-5.6",
                "test_date": (datetime.utcnow() - timedelta(days=random.randint(1, 180))).isoformat()
            },
            {
                "test_name": "Total Cholesterol",
                "value": random.randint(150, 280),
                "unit": "mg/dL",
                "reference_range": "<200",
                "test_date": (datetime.utcnow() - timedelta(days=random.randint(1, 180))).isoformat()
            },
            {
                "test_name": "Blood Glucose",
                "value": random.randint(70, 180),
                "unit": "mg/dL",
                "reference_range": "70-100",
                "test_date": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat()
            }
        ]
    
    def _generate_vital_signs(self, age: int) -> Dict[str, Any]:
        """Generate realistic vital signs."""
        base_bp = 120 + (age - 40) * 0.5 if age > 40 else 120
        
        return {
            "blood_pressure": {
                "systolic": int(base_bp + random.randint(-10, 20)),
                "diastolic": int(80 + random.randint(-10, 15)),
                "unit": "mmHg"
            },
            "heart_rate": random.randint(60, 100),
            "temperature": round(random.uniform(97.0, 99.5), 1),
            "respiratory_rate": random.randint(12, 20),
            "oxygen_saturation": random.randint(95, 100),
            "recorded_date": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
        }
    
    def _generate_procedures(self) -> List[Dict[str, Any]]:
        """Generate realistic procedures."""
        procedures = []
        
        if random.random() < 0.2:
            procedures.append({
                "cpt_code": "99213",
                "description": "Office visit, established patient",
                "procedure_date": (datetime.utcnow() - timedelta(days=random.randint(1, 180))).isoformat(),
                "provider": f"Dr. {random.choice(['Smith', 'Johnson', 'Williams', 'Brown'])}"
            })
        
        return procedures
    
    def _generate_allergies(self) -> List[Dict[str, Any]]:
        """Generate realistic allergies."""
        allergies = []
        
        if random.random() < 0.15:
            allergies.append({
                "allergen": random.choice(["Penicillin", "Sulfa drugs", "Aspirin", "Latex"]),
                "reaction": random.choice(["Rash", "Hives", "Anaphylaxis", "Swelling"]),
                "severity": random.choice(["mild", "moderate", "severe"]),
                "documented_date": (datetime.utcnow() - timedelta(days=random.randint(365, 7300))).isoformat()
            })
        
        return allergies
    
    def _generate_immunizations(self, age: int) -> List[Dict[str, Any]]:
        """Generate realistic immunizations."""
        immunizations = []
        
        if age > 50:
            immunizations.append({
                "vaccine": "Influenza",
                "date_administered": (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
                "lot_number": f"LOT-{random.randint(10000, 99999)}"
            })
        
        if age > 65:
            immunizations.append({
                "vaccine": "Pneumococcal",
                "date_administered": (datetime.utcnow() - timedelta(days=random.randint(1, 1825))).isoformat(),
                "lot_number": f"LOT-{random.randint(10000, 99999)}"
            })
        
        return immunizations
    
    def _create_datasets(self):
        """Create categorized datasets for research."""
        # Cardiovascular dataset
        self.datasets["cardiovascular"] = {
            "dataset_id": "DS-CARDIO-001",
            "name": "Cardiovascular Disease Dataset",
            "description": "Patient records with cardiovascular conditions",
            "research_category": "cardiovascular_research",
            "data_types": ["demographics", "diagnoses", "medications", "lab_results", "vital_signs"],
            "patient_count": 0,
            "records": []
        }
        
        # Diabetes dataset
        self.datasets["diabetes"] = {
            "dataset_id": "DS-DIABETES-001",
            "name": "Diabetes Management Dataset",
            "description": "Patient records with diabetes diagnoses",
            "research_category": "diabetes_research",
            "data_types": ["demographics", "diagnoses", "medications", "lab_results"],
            "patient_count": 0,
            "records": []
        }
        
        # General medical dataset
        self.datasets["general"] = {
            "dataset_id": "DS-GENERAL-001",
            "name": "General Medical Records Dataset",
            "description": "Comprehensive patient medical records",
            "research_category": "general_medical_research",
            "data_types": self.DATA_TYPES,
            "patient_count": 0,
            "records": []
        }
        
        # Categorize records into datasets
        for patient_id, record in self.records.items():
            # Check for cardiovascular conditions
            has_cardio = any(
                d.get("icd10_code", "").startswith("I") 
                for d in record.medical_data.get("diagnoses", [])
            )
            if has_cardio:
                self.datasets["cardiovascular"]["records"].append(patient_id)
                self.datasets["cardiovascular"]["patient_count"] += 1
            
            # Check for diabetes
            has_diabetes = any(
                d.get("icd10_code", "").startswith("E11") 
                for d in record.medical_data.get("diagnoses", [])
            )
            if has_diabetes:
                self.datasets["diabetes"]["records"].append(patient_id)
                self.datasets["diabetes"]["patient_count"] += 1
            
            # All records go to general dataset
            self.datasets["general"]["records"].append(patient_id)
            self.datasets["general"]["patient_count"] += 1
    
    def get_record(self, patient_id: str) -> Optional[MockPatientRecord]:
        """Retrieve a patient record by ID."""
        return self.records.get(patient_id)
    
    def search_records(self, criteria: Dict[str, Any]) -> List[MockPatientRecord]:
        """Search records based on criteria."""
        matching_records = []
        
        for record in self.records.values():
            if self._matches_criteria(record, criteria):
                matching_records.append(record)
        
        return matching_records
    
    def _matches_criteria(self, record: MockPatientRecord, criteria: Dict[str, Any]) -> bool:
        """Check if record matches search criteria."""
        # Age range
        if "age_min" in criteria:
            if record.demographics.get("age", 0) < criteria["age_min"]:
                return False
        
        if "age_max" in criteria:
            if record.demographics.get("age", 999) > criteria["age_max"]:
                return False
        
        # Gender
        if "gender" in criteria:
            if record.demographics.get("gender") != criteria["gender"]:
                return False
        
        # Diagnosis codes
        if "diagnosis_codes" in criteria:
            record_codes = [d.get("icd10_code") for d in record.medical_data.get("diagnoses", [])]
            if not any(code in record_codes for code in criteria["diagnosis_codes"]):
                return False
        
        # Research category
        if "research_category" in criteria:
            category = criteria["research_category"]
            if category == "cardiovascular_research":
                if not any(d.get("icd10_code", "").startswith("I") for d in record.medical_data.get("diagnoses", [])):
                    return False
            elif category == "diabetes_research":
                if not any(d.get("icd10_code", "").startswith("E11") for d in record.medical_data.get("diagnoses", [])):
                    return False
        
        return True
    
    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve dataset by ID."""
        for dataset in self.datasets.values():
            if dataset["dataset_id"] == dataset_id:
                return dataset
        return None
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets."""
        return [
            {
                "dataset_id": ds["dataset_id"],
                "name": ds["name"],
                "description": ds["description"],
                "research_category": ds["research_category"],
                "patient_count": ds["patient_count"],
                "data_types": ds["data_types"]
            }
            for ds in self.datasets.values()
        ]
    
    def get_dataset_records(self, dataset_id: str, data_types: List[str]) -> List[Dict[str, Any]]:
        """Get records from a dataset with specified data types."""
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
        
        records = []
        for patient_id in dataset["records"]:
            record = self.get_record(patient_id)
            if record:
                # Filter to requested data types
                filtered_data = {
                    "patient_id": patient_id,
                    "record_id": record.record_id
                }
                
                for data_type in data_types:
                    if data_type == "demographics":
                        filtered_data["demographics"] = record.demographics
                    elif data_type in record.medical_data:
                        filtered_data[data_type] = record.medical_data[data_type]
                
                filtered_data["data_quality_score"] = record.data_quality_score
                records.append(filtered_data)
        
        return records
    
    def validate_data_quality(self, patient_id: str) -> Dict[str, Any]:
        """Validate data quality for a patient record."""
        record = self.get_record(patient_id)
        if not record:
            return {
                "valid": False,
                "error": "Record not found"
            }
        
        issues = []
        
        # Check completeness
        if record.data_quality_score < 0.7:
            issues.append(f"Low data completeness: {record.data_quality_score:.2%}")
        
        # Check for required fields
        if not record.demographics.get("age"):
            issues.append("Missing age in demographics")
        
        if not record.demographics.get("gender"):
            issues.append("Missing gender in demographics")
        
        # Check data freshness
        if record.metadata.get("last_visit"):
            last_visit = datetime.fromisoformat(record.metadata["last_visit"])
            days_since_visit = (datetime.utcnow() - last_visit).days
            if days_since_visit > 730:  # 2 years
                issues.append(f"Data may be stale (last visit: {days_since_visit} days ago)")
        
        return {
            "valid": len(issues) == 0,
            "quality_score": record.data_quality_score,
            "issues": issues,
            "record_id": record.record_id
        }
    
    def get_metadata(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a patient record."""
        record = self.get_record(patient_id)
        if not record:
            return None
        
        return {
            "record_id": record.record_id,
            "patient_id": patient_id,
            "created_at": record.created_at.isoformat(),
            "last_updated": record.last_updated.isoformat(),
            "data_quality_score": record.data_quality_score,
            "institution_id": self.institution_id,
            "available_data_types": list(record.medical_data.keys()) + ["demographics"]
        }
