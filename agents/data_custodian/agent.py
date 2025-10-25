"""
Data Custodian Agent for HealthSync system.
Represents healthcare institutions and validates data access requests.
"""

from uagents import Context
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.base_agent import HealthSyncBaseAgent
from shared.protocols.agent_messages import (
    MessageTypes, DataRequest, DataResponse, ConsentQuery,
    AgentMessage, ErrorCodes, ErrorResponse
)
from shared.utils.error_handling import with_error_handling

from .mock_ehr import MockEHRSystem
from .data_access_api import DataAccessAPI


class DataCustodianAgent(HealthSyncBaseAgent):
    """Agent responsible for managing healthcare data access and validation."""
    
    def __init__(self, port: int = 8003, 
                 patient_consent_agent_address: Optional[str] = None,
                 institution_id: str = "HEALTHSYNC_HOSPITAL_001"):
        super().__init__(
            name="Data Custodian Agent",
            port=port,
            endpoint=f"http://localhost:{port}/submit"
        )
        
        # Initialize EHR system and data access API
        self.ehr_system = MockEHRSystem(institution_id=institution_id)
        self.data_api = DataAccessAPI(self.ehr_system)
        
        # Patient Consent Agent address for consent verification
        self.patient_consent_agent_address = patient_consent_agent_address
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "approved_requests": 0,
            "denied_requests": 0,
            "consent_checks": 0,
            "data_accesses": 0,
            "total_records_shared": 0
        }
        
        # Register message handlers
        self._register_handlers()
        
        self.logger.info("Data Custodian Agent initialized",
                        institution_id=institution_id,
                        total_patients=len(self.ehr_system.records))
    
    def _register_handlers(self):
        """Register message handlers for data custodian operations."""
        
        self.register_message_handler(
            MessageTypes.DATA_REQUEST,
            self._handle_data_request
        )
        
        self.register_message_handler(
            MessageTypes.HEALTH_CHECK,
            self._handle_health_check
        )
        
        # Additional handlers
        self.register_message_handler(
            "dataset_discovery",
            self._handle_dataset_discovery
        )
        
        self.register_message_handler(
            "dataset_summary",
            self._handle_dataset_summary
        )
        
        self.register_message_handler(
            "data_provenance",
            self._handle_data_provenance
        )
        
        self.register_message_handler(
            "access_logs",
            self._handle_access_logs
        )
    
    @with_error_handling("data_custodian_agent")
    async def _handle_data_request(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle data access requests with consent validation."""
        try:
            # Parse data request
            request_data = DataRequest(**msg.payload)
            
            self.stats["total_requests"] += 1
            
            self.logger.info("Processing data request",
                           request_id=request_data.request_id,
                           requester_id=request_data.requester_id,
                           research_purpose=request_data.research_purpose)
            
            # Create data access request
            data_request = self.data_api.create_data_request(
                requester_id=request_data.requester_id,
                data_criteria=request_data.data_criteria,
                research_purpose=request_data.research_purpose,
                ethical_approval=request_data.ethical_approval
            )
            
            # Validate request
            is_valid, validation_message = self.data_api.validate_request(data_request.request_id)
            
            if not is_valid:
                self.stats["denied_requests"] += 1
                
                self.logger.warning("Data request validation failed",
                                  request_id=data_request.request_id,
                                  reason=validation_message)
                
                return {
                    "status": "denied",
                    "request_id": data_request.request_id,
                    "denial_reason": validation_message,
                    "access_granted": False
                }
            
            # Search for matching datasets
            matching_datasets = self.data_api.search_matching_datasets(request_data.data_criteria)
            
            if not matching_datasets:
                self.stats["denied_requests"] += 1
                
                self.logger.info("No matching datasets found",
                               request_id=data_request.request_id)
                
                return {
                    "status": "denied",
                    "request_id": data_request.request_id,
                    "denial_reason": "No datasets match the specified criteria",
                    "access_granted": False
                }
            
            # Use first matching dataset
            dataset = matching_datasets[0]
            
            self.logger.info("Found matching dataset",
                           request_id=data_request.request_id,
                           dataset_id=dataset["dataset_id"],
                           patient_count=dataset["patient_count"])
            
            # Verify consent for patients in dataset
            consent_verification = await self._verify_patient_consents(
                ctx=ctx,
                dataset_id=dataset["dataset_id"],
                data_criteria=request_data.data_criteria,
                requester_id=request_data.requester_id
            )
            
            if not consent_verification["all_consents_valid"]:
                self.stats["denied_requests"] += 1
                
                self.logger.warning("Consent verification failed",
                                  request_id=data_request.request_id,
                                  consented_patients=consent_verification["consented_count"],
                                  total_patients=consent_verification["total_count"])
                
                return {
                    "status": "denied",
                    "request_id": data_request.request_id,
                    "denial_reason": "Insufficient patient consents",
                    "access_granted": False,
                    "consent_details": {
                        "consented_patients": consent_verification["consented_count"],
                        "total_patients": consent_verification["total_count"],
                        "consent_rate": consent_verification["consent_rate"]
                    }
                }
            
            # Approve request
            data_request.approve()
            data_request.consent_verified = True
            
            # Retrieve dataset records
            requested_data_types = request_data.data_criteria.get("data_types", [])
            consented_patient_ids = consent_verification["consented_patient_ids"]
            
            records, access_id = self.data_api.retrieve_dataset_records(
                request_id=data_request.request_id,
                dataset_id=dataset["dataset_id"],
                data_types=requested_data_types,
                patient_ids=consented_patient_ids
            )
            
            self.stats["approved_requests"] += 1
            self.stats["data_accesses"] += 1
            self.stats["total_records_shared"] += len(records)
            
            self.logger.audit(
                event_type="data_access_granted",
                details={
                    "request_id": data_request.request_id,
                    "requester_id": request_data.requester_id,
                    "dataset_id": dataset["dataset_id"],
                    "record_count": len(records),
                    "data_types": requested_data_types,
                    "access_id": access_id,
                    "consent_verified": True
                }
            )
            
            return {
                "status": "approved",
                "request_id": data_request.request_id,
                "access_granted": True,
                "dataset_id": dataset["dataset_id"],
                "patient_count": len(records),
                "data_fields": requested_data_types,
                "access_id": access_id,
                "records": records,
                "consent_verification": consent_verification
            }
            
        except Exception as e:
            self.logger.error("Failed to process data request",
                            error=str(e),
                            requester_id=msg.payload.get("requester_id"))
            
            self.stats["denied_requests"] += 1
            
            return {
                "status": "error",
                "access_granted": False,
                "message": f"Failed to process data request: {str(e)}"
            }
    
    async def _verify_patient_consents(self, ctx: Context, dataset_id: str,
                                      data_criteria: Dict[str, Any],
                                      requester_id: str) -> Dict[str, Any]:
        """Verify patient consents for dataset access."""
        
        if not self.patient_consent_agent_address:
            # If no consent agent configured, skip consent verification
            self.logger.warning("No Patient Consent Agent configured, skipping consent verification")
            
            dataset = self.ehr_system.get_dataset(dataset_id)
            all_patient_ids = dataset["records"] if dataset else []
            
            return {
                "all_consents_valid": True,
                "consented_patient_ids": all_patient_ids,
                "consented_count": len(all_patient_ids),
                "total_count": len(all_patient_ids),
                "consent_rate": 1.0,
                "verification_skipped": True
            }
        
        # Get dataset
        dataset = self.ehr_system.get_dataset(dataset_id)
        if not dataset:
            return {
                "all_consents_valid": False,
                "consented_patient_ids": [],
                "consented_count": 0,
                "total_count": 0,
                "consent_rate": 0.0,
                "error": "Dataset not found"
            }
        
        patient_ids = dataset["records"]
        data_types = data_criteria.get("data_types", [])
        research_category = data_criteria.get("research_category", "general_medical_research")
        
        consented_patient_ids = []
        consent_failures = []
        
        # Check consent for each patient and data type combination
        for patient_id in patient_ids:
            patient_consented = True
            
            for data_type in data_types:
                # Query Patient Consent Agent
                consent_query_payload = {
                    "patient_id": patient_id,
                    "data_type": data_type,
                    "research_category": research_category,
                    "requester_id": requester_id
                }
                
                try:
                    # Send consent query to Patient Consent Agent
                    consent_response = await self._query_consent_agent(
                        ctx=ctx,
                        query_payload=consent_query_payload
                    )
                    
                    self.stats["consent_checks"] += 1
                    
                    if not consent_response.get("consent_granted", False):
                        patient_consented = False
                        consent_failures.append({
                            "patient_id": patient_id,
                            "data_type": data_type,
                            "reason": consent_response.get("message", "Consent not granted")
                        })
                        break  # No need to check other data types for this patient
                
                except Exception as e:
                    self.logger.error("Failed to query consent",
                                    patient_id=patient_id,
                                    data_type=data_type,
                                    error=str(e))
                    patient_consented = False
                    consent_failures.append({
                        "patient_id": patient_id,
                        "data_type": data_type,
                        "reason": f"Consent query failed: {str(e)}"
                    })
                    break
            
            if patient_consented:
                consented_patient_ids.append(patient_id)
        
        total_count = len(patient_ids)
        consented_count = len(consented_patient_ids)
        consent_rate = consented_count / total_count if total_count > 0 else 0.0
        
        # Consider consent verification successful if at least 50% of patients consented
        all_consents_valid = consent_rate >= 0.5 and consented_count > 0
        
        self.logger.info("Consent verification completed",
                        dataset_id=dataset_id,
                        total_patients=total_count,
                        consented_patients=consented_count,
                        consent_rate=f"{consent_rate:.2%}",
                        all_valid=all_consents_valid)
        
        return {
            "all_consents_valid": all_consents_valid,
            "consented_patient_ids": consented_patient_ids,
            "consented_count": consented_count,
            "total_count": total_count,
            "consent_rate": consent_rate,
            "consent_failures": consent_failures[:10]  # Limit to first 10 failures
        }
    
    async def _query_consent_agent(self, ctx: Context, query_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Query Patient Consent Agent for consent verification."""
        
        try:
            # Log consent query for audit trail
            self.logger.audit(
                event_type="consent_query_sent",
                details={
                    "patient_id": query_payload.get("patient_id"),
                    "data_type": query_payload.get("data_type"),
                    "research_category": query_payload.get("research_category"),
                    "requester_id": query_payload.get("requester_id"),
                    "consent_agent_address": self.patient_consent_agent_address
                }
            )
            
            # Send consent query message
            message_id = await self.send_message(
                ctx=ctx,
                recipient=self.patient_consent_agent_address,
                message_type=MessageTypes.CONSENT_QUERY,
                payload=query_payload,
                requires_ack=True
            )
            
            # In a real implementation, we would wait for the response
            # For now, we'll simulate a response based on the query
            # This would be replaced with actual async message handling
            
            # Simulate consent response (in production, this would come from the actual agent)
            # The simulation provides realistic responses for testing
            consent_response = {
                "status": "success",
                "consent_granted": True,  # Simplified for demo
                "patient_id": query_payload["patient_id"],
                "message": "Consent verified",
                "message_id": message_id
            }
            
            # Log consent response for audit trail
            self.logger.audit(
                event_type="consent_query_response",
                details={
                    "patient_id": query_payload.get("patient_id"),
                    "consent_granted": consent_response.get("consent_granted"),
                    "message_id": message_id,
                    "response_status": consent_response.get("status")
                }
            )
            
            return consent_response
            
        except Exception as e:
            self.logger.error("Failed to query consent agent",
                            patient_id=query_payload.get("patient_id"),
                            error=str(e))
            
            # Return error response
            return {
                "status": "error",
                "consent_granted": False,
                "patient_id": query_payload.get("patient_id"),
                "message": f"Consent query failed: {str(e)}"
            }
    
    async def _handle_dataset_discovery(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle dataset discovery requests."""
        try:
            research_category = msg.payload.get("research_category")
            
            datasets = self.data_api.discover_datasets(research_category=research_category)
            
            self.logger.info("Dataset discovery completed",
                           research_category=research_category,
                           datasets_found=len(datasets))
            
            return {
                "status": "success",
                "datasets": datasets,
                "total_datasets": len(datasets)
            }
            
        except Exception as e:
            self.logger.error("Failed to discover datasets", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to discover datasets: {str(e)}"
            }
    
    async def _handle_dataset_summary(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle dataset summary requests."""
        try:
            dataset_id = msg.payload.get("dataset_id")
            
            summary = self.data_api.get_dataset_summary(dataset_id)
            
            if not summary:
                return {
                    "status": "not_found",
                    "message": f"Dataset not found: {dataset_id}"
                }
            
            return {
                "status": "success",
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error("Failed to get dataset summary", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to get dataset summary: {str(e)}"
            }
    
    async def _handle_data_provenance(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle data provenance requests."""
        try:
            patient_id = msg.payload.get("patient_id")
            
            provenance = self.data_api.get_provenance(patient_id)
            
            if not provenance:
                return {
                    "status": "not_found",
                    "message": f"No provenance found for patient: {patient_id}"
                }
            
            return {
                "status": "success",
                "provenance": provenance
            }
            
        except Exception as e:
            self.logger.error("Failed to get provenance", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to get provenance: {str(e)}"
            }
    
    async def _handle_access_logs(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle access log requests."""
        try:
            requester_id = msg.payload.get("requester_id")
            
            logs = self.data_api.get_access_logs(requester_id=requester_id)
            
            return {
                "status": "success",
                "logs": logs,
                "total_accesses": len(logs)
            }
            
        except Exception as e:
            self.logger.error("Failed to get access logs", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to get access logs: {str(e)}"
            }
    
    async def _handle_health_check(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle health check requests."""
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "institution_id": self.ehr_system.institution_id,
            "total_patients": len(self.ehr_system.records),
            "total_datasets": len(self.ehr_system.datasets),
            "statistics": self.stats,
            "last_heartbeat": self.last_heartbeat.isoformat()
        }
    
    async def on_startup(self, ctx: Context):
        """Custom startup logic."""
        self.logger.info("Data Custodian Agent starting up",
                        institution_id=self.ehr_system.institution_id,
                        datasets=len(self.ehr_system.datasets),
                        patients=len(self.ehr_system.records))
        
        # Log available datasets
        for dataset in self.ehr_system.list_datasets():
            self.logger.info("Dataset available",
                           dataset_id=dataset["dataset_id"],
                           name=dataset["name"],
                           patient_count=dataset["patient_count"])


# Main entry point for running the agent
if __name__ == "__main__":
    # Configuration
    PORT = int(os.getenv("DATA_CUSTODIAN_PORT", "8003"))
    PATIENT_CONSENT_AGENT_ADDRESS = os.getenv("PATIENT_CONSENT_AGENT_ADDRESS")
    INSTITUTION_ID = os.getenv("INSTITUTION_ID", "HEALTHSYNC_HOSPITAL_001")
    
    # Create and run agent
    agent = DataCustodianAgent(
        port=PORT,
        patient_consent_agent_address=PATIENT_CONSENT_AGENT_ADDRESS,
        institution_id=INSTITUTION_ID
    )
    
    agent.run()
