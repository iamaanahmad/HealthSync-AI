"""
Data Access API for Data Custodian Agent.
Provides interfaces for querying and accessing healthcare data.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import hashlib

from .mock_ehr import MockEHRSystem, MockPatientRecord


class DataAccessRequest:
    """Represents a data access request with validation and tracking."""
    
    def __init__(self, requester_id: str, data_criteria: Dict[str, Any],
                 research_purpose: str, ethical_approval: str):
        self.request_id = str(uuid.uuid4())
        self.requester_id = requester_id
        self.data_criteria = data_criteria
        self.research_purpose = research_purpose
        self.ethical_approval = ethical_approval
        self.created_at = datetime.utcnow()
        self.status = "pending"  # pending, approved, denied, completed
        self.consent_verified = False
        self.access_log: List[Dict[str, Any]] = []
        
        self._add_log_entry("created", {"requester_id": requester_id})
    
    def _add_log_entry(self, action: str, details: Dict[str, Any]):
        """Add entry to access log."""
        self.access_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details
        })
    
    def approve(self):
        """Approve the data access request."""
        self.status = "approved"
        self._add_log_entry("approved", {"approved_at": datetime.utcnow().isoformat()})
    
    def deny(self, reason: str):
        """Deny the data access request."""
        self.status = "denied"
        self._add_log_entry("denied", {"reason": reason})
    
    def complete(self, record_count: int):
        """Mark request as completed."""
        self.status = "completed"
        self._add_log_entry("completed", {
            "completed_at": datetime.utcnow().isoformat(),
            "record_count": record_count
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        return {
            "request_id": self.request_id,
            "requester_id": self.requester_id,
            "data_criteria": self.data_criteria,
            "research_purpose": self.research_purpose,
            "ethical_approval": self.ethical_approval,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "consent_verified": self.consent_verified,
            "access_log": self.access_log
        }


class DataProvenanceTracker:
    """Tracks data provenance and access history."""
    
    def __init__(self):
        self.access_history: List[Dict[str, Any]] = []
        self.provenance_records: Dict[str, Dict[str, Any]] = {}
    
    def record_access(self, request_id: str, requester_id: str, 
                     patient_ids: List[str], data_types: List[str],
                     purpose: str) -> str:
        """Record a data access event."""
        access_id = str(uuid.uuid4())
        
        access_record = {
            "access_id": access_id,
            "request_id": request_id,
            "requester_id": requester_id,
            "patient_ids": patient_ids,
            "patient_count": len(patient_ids),
            "data_types": data_types,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat(),
            "access_hash": self._generate_access_hash(request_id, patient_ids)
        }
        
        self.access_history.append(access_record)
        
        # Update provenance for each patient
        for patient_id in patient_ids:
            if patient_id not in self.provenance_records:
                self.provenance_records[patient_id] = {
                    "patient_id": patient_id,
                    "access_events": []
                }
            
            self.provenance_records[patient_id]["access_events"].append({
                "access_id": access_id,
                "requester_id": requester_id,
                "data_types": data_types,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return access_id
    
    def _generate_access_hash(self, request_id: str, patient_ids: List[str]) -> str:
        """Generate cryptographic hash for access verification."""
        data_str = f"{request_id}:{'|'.join(sorted(patient_ids))}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def get_patient_provenance(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get provenance record for a patient."""
        return self.provenance_records.get(patient_id)
    
    def get_access_history(self, requester_id: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get access history with optional filters."""
        filtered_history = self.access_history
        
        if requester_id:
            filtered_history = [
                record for record in filtered_history
                if record["requester_id"] == requester_id
            ]
        
        if start_date:
            filtered_history = [
                record for record in filtered_history
                if datetime.fromisoformat(record["timestamp"]) >= start_date
            ]
        
        if end_date:
            filtered_history = [
                record for record in filtered_history
                if datetime.fromisoformat(record["timestamp"]) <= end_date
            ]
        
        return filtered_history


class DataAccessAPI:
    """API for accessing healthcare data with validation and tracking."""
    
    def __init__(self, ehr_system: MockEHRSystem):
        self.ehr_system = ehr_system
        self.provenance_tracker = DataProvenanceTracker()
        self.active_requests: Dict[str, DataAccessRequest] = {}
    
    def create_data_request(self, requester_id: str, data_criteria: Dict[str, Any],
                           research_purpose: str, ethical_approval: str) -> DataAccessRequest:
        """Create a new data access request."""
        request = DataAccessRequest(
            requester_id=requester_id,
            data_criteria=data_criteria,
            research_purpose=research_purpose,
            ethical_approval=ethical_approval
        )
        
        self.active_requests[request.request_id] = request
        return request
    
    def validate_request(self, request_id: str) -> Tuple[bool, str]:
        """Validate a data access request."""
        request = self.active_requests.get(request_id)
        if not request:
            return False, "Request not found"
        
        # Validate ethical approval
        if not request.ethical_approval or request.ethical_approval == "":
            return False, "Missing ethical approval"
        
        # Validate research purpose
        if not request.research_purpose or len(request.research_purpose) < 10:
            return False, "Research purpose must be at least 10 characters"
        
        # Validate data criteria
        if not request.data_criteria:
            return False, "Data criteria cannot be empty"
        
        # Check if requested data types are valid
        requested_types = request.data_criteria.get("data_types", [])
        invalid_types = [
            dt for dt in requested_types
            if dt not in self.ehr_system.DATA_TYPES
        ]
        
        if invalid_types:
            return False, f"Invalid data types: {', '.join(invalid_types)}"
        
        return True, "Request is valid"
    
    def search_matching_datasets(self, data_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for datasets matching the criteria."""
        matching_datasets = []
        
        research_category = data_criteria.get("research_category")
        requested_data_types = data_criteria.get("data_types", [])
        
        for dataset in self.ehr_system.list_datasets():
            # Check if research category matches
            if research_category and dataset["research_category"] != research_category:
                continue
            
            # Check if dataset has required data types
            if requested_data_types:
                if not all(dt in dataset["data_types"] for dt in requested_data_types):
                    continue
            
            matching_datasets.append(dataset)
        
        return matching_datasets
    
    def get_dataset_summary(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a dataset."""
        dataset = self.ehr_system.get_dataset(dataset_id)
        if not dataset:
            return None
        
        return {
            "dataset_id": dataset["dataset_id"],
            "name": dataset["name"],
            "description": dataset["description"],
            "research_category": dataset["research_category"],
            "patient_count": dataset["patient_count"],
            "available_data_types": dataset["data_types"],
            "institution_id": self.ehr_system.institution_id
        }
    
    def retrieve_dataset_records(self, request_id: str, dataset_id: str,
                                data_types: List[str],
                                patient_ids: Optional[List[str]] = None) -> Tuple[List[Dict[str, Any]], str]:
        """Retrieve records from a dataset."""
        request = self.active_requests.get(request_id)
        if not request:
            return [], "Request not found"
        
        if request.status != "approved":
            return [], "Request not approved"
        
        # Get dataset
        dataset = self.ehr_system.get_dataset(dataset_id)
        if not dataset:
            return [], "Dataset not found"
        
        # Get records
        if patient_ids:
            # Retrieve specific patient records
            records = []
            for patient_id in patient_ids:
                if patient_id in dataset["records"]:
                    record = self.ehr_system.get_record(patient_id)
                    if record:
                        filtered_data = self._filter_record_data(record, data_types)
                        records.append(filtered_data)
        else:
            # Retrieve all records from dataset
            records = self.ehr_system.get_dataset_records(dataset_id, data_types)
        
        # Record access in provenance tracker
        accessed_patient_ids = [r["patient_id"] for r in records]
        access_id = self.provenance_tracker.record_access(
            request_id=request_id,
            requester_id=request.requester_id,
            patient_ids=accessed_patient_ids,
            data_types=data_types,
            purpose=request.research_purpose
        )
        
        # Update request
        request.complete(len(records))
        
        return records, access_id
    
    def _filter_record_data(self, record: MockPatientRecord, 
                           data_types: List[str]) -> Dict[str, Any]:
        """Filter record to include only requested data types."""
        filtered_data = {
            "patient_id": record.patient_id,
            "record_id": record.record_id
        }
        
        for data_type in data_types:
            if data_type == "demographics":
                filtered_data["demographics"] = record.demographics
            elif data_type in record.medical_data:
                filtered_data[data_type] = record.medical_data[data_type]
        
        filtered_data["data_quality_score"] = record.data_quality_score
        
        return filtered_data
    
    def validate_data_quality(self, patient_ids: List[str]) -> Dict[str, Any]:
        """Validate data quality for multiple patients."""
        validation_results = {
            "total_records": len(patient_ids),
            "valid_records": 0,
            "invalid_records": 0,
            "average_quality_score": 0.0,
            "issues": []
        }
        
        quality_scores = []
        
        for patient_id in patient_ids:
            result = self.ehr_system.validate_data_quality(patient_id)
            
            if result["valid"]:
                validation_results["valid_records"] += 1
            else:
                validation_results["invalid_records"] += 1
                validation_results["issues"].append({
                    "patient_id": patient_id,
                    "issues": result.get("issues", [])
                })
            
            quality_scores.append(result.get("quality_score", 0.0))
        
        if quality_scores:
            validation_results["average_quality_score"] = sum(quality_scores) / len(quality_scores)
        
        return validation_results
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a data access request."""
        request = self.active_requests.get(request_id)
        if not request:
            return None
        
        return request.to_dict()
    
    def get_provenance(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get data provenance for a patient."""
        return self.provenance_tracker.get_patient_provenance(patient_id)
    
    def get_access_logs(self, requester_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get access logs with optional filtering."""
        return self.provenance_tracker.get_access_history(requester_id=requester_id)
    
    def discover_datasets(self, research_category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover available datasets."""
        datasets = self.ehr_system.list_datasets()
        
        if research_category:
            datasets = [
                ds for ds in datasets
                if ds["research_category"] == research_category
            ]
        
        return datasets
    
    def get_dataset_catalog(self) -> Dict[str, Any]:
        """Get complete dataset catalog with metadata."""
        datasets = self.ehr_system.list_datasets()
        
        return {
            "institution_id": self.ehr_system.institution_id,
            "total_datasets": len(datasets),
            "total_patients": len(self.ehr_system.records),
            "available_data_types": self.ehr_system.DATA_TYPES,
            "research_categories": self.ehr_system.RESEARCH_CATEGORIES,
            "datasets": datasets
        }
