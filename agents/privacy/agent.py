"""
Privacy Agent for HealthSync system.
Performs data anonymization and ensures privacy compliance.
"""

from uagents import Context
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os
import hashlib
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.base_agent import HealthSyncBaseAgent
from shared.protocols.agent_messages import (
    MessageTypes, AgentMessage, ErrorCodes, ErrorResponse
)
from shared.utils.error_handling import with_error_handling

from .anonymization import AnonymizationEngine
from .privacy_compliance import PrivacyComplianceManager, PrivacyAuditLogger


class PrivacyAgent(HealthSyncBaseAgent):
    """Agent responsible for data anonymization and privacy compliance."""
    
    def __init__(self, port: int = 8004,
                 metta_agent_address: Optional[str] = None,
                 k_anonymity: int = 5,
                 epsilon: float = 1.0):
        super().__init__(
            name="Privacy Agent",
            port=port,
            endpoint=f"http://localhost:{port}/submit"
        )
        
        # Initialize anonymization engine
        self.anonymization_engine = AnonymizationEngine(
            k=k_anonymity,
            epsilon=epsilon
        )
        
        # Initialize privacy compliance manager
        self.compliance_manager = PrivacyComplianceManager(
            metta_agent_address=metta_agent_address
        )
        
        # Initialize audit logger
        self.audit_logger = PrivacyAuditLogger()
        
        # MeTTa Integration Agent address
        self.metta_agent_address = metta_agent_address
        
        # Statistics
        self.stats = {
            "total_anonymization_requests": 0,
            "successful_anonymizations": 0,
            "failed_anonymizations": 0,
            "total_records_anonymized": 0,
            "privacy_violations_detected": 0,
            "compliance_checks": 0
        }
        
        # Register message handlers
        self._register_handlers()
        
        self.logger.info("Privacy Agent initialized",
                        k_anonymity=k_anonymity,
                        epsilon=epsilon)
    
    def _register_handlers(self):
        """Register message handlers for privacy operations."""
        
        self.register_message_handler(
            MessageTypes.ANONYMIZATION_REQUEST,
            self._handle_anonymization_request
        )
        
        self.register_message_handler(
            MessageTypes.HEALTH_CHECK,
            self._handle_health_check
        )
        
        # Additional handlers
        self.register_message_handler(
            "privacy_compliance_check",
            self._handle_privacy_compliance_check
        )
        
        self.register_message_handler(
            "privacy_metrics",
            self._handle_privacy_metrics
        )
        
        self.register_message_handler(
            "audit_logs",
            self._handle_audit_logs
        )
        
        self.register_message_handler(
            "privacy_rules_update",
            self._handle_privacy_rules_update
        )
    
    @with_error_handling("privacy_agent")
    async def _handle_anonymization_request(self, ctx: Context, sender: str, 
                                           msg: AgentMessage) -> Dict[str, Any]:
        """Handle data anonymization requests."""
        try:
            self.stats["total_anonymization_requests"] += 1
            
            # Extract request data
            request_id = msg.payload.get("request_id")
            dataset_id = msg.payload.get("dataset_id")
            records = msg.payload.get("records", [])
            anonymization_config = msg.payload.get("anonymization_config", {})
            requester_id = msg.payload.get("requester_id")
            
            self.logger.info("Processing anonymization request",
                           request_id=request_id,
                           dataset_id=dataset_id,
                           record_count=len(records),
                           requester_id=requester_id)
            
            if not records:
                self.stats["failed_anonymizations"] += 1
                return {
                    "status": "error",
                    "request_id": request_id,
                    "message": "No records provided for anonymization"
                }
            
            # Check privacy compliance before anonymization
            compliance_check = await self._check_privacy_compliance(
                ctx=ctx,
                records=records,
                config=anonymization_config
            )
            
            if not compliance_check["compliant"]:
                self.stats["privacy_violations_detected"] += 1
                self.logger.warning("Privacy compliance check failed",
                                  request_id=request_id,
                                  violations=compliance_check.get("violations"))
                
                return {
                    "status": "compliance_failed",
                    "request_id": request_id,
                    "message": "Privacy compliance check failed",
                    "violations": compliance_check.get("violations", [])
                }
            
            # Perform anonymization
            anonymized_records, metrics = self.anonymization_engine.anonymize_dataset(
                records=records,
                config=anonymization_config
            )
            
            # Log anonymization for audit
            audit_entry = self.audit_logger.log_anonymization(
                request_id=request_id,
                dataset_id=dataset_id,
                requester_id=requester_id,
                original_record_count=len(records),
                anonymized_record_count=len(anonymized_records),
                techniques_applied=metrics.get("techniques_applied", []),
                privacy_metrics=metrics
            )
            
            self.stats["successful_anonymizations"] += 1
            self.stats["total_records_anonymized"] += len(anonymized_records)
            
            self.logger.audit(
                event_type="data_anonymized",
                details={
                    "request_id": request_id,
                    "dataset_id": dataset_id,
                    "requester_id": requester_id,
                    "original_count": len(records),
                    "anonymized_count": len(anonymized_records),
                    "retention_rate": metrics.get("data_retention_rate", 0),
                    "audit_id": audit_entry["audit_id"]
                }
            )
            
            return {
                "status": "success",
                "request_id": request_id,
                "dataset_id": dataset_id,
                "anonymized_records": anonymized_records,
                "metrics": metrics,
                "audit_id": audit_entry["audit_id"],
                "compliance_verified": True
            }
            
        except Exception as e:
            self.stats["failed_anonymizations"] += 1
            self.logger.error("Failed to anonymize data",
                            request_id=msg.payload.get("request_id"),
                            error=str(e))
            
            return {
                "status": "error",
                "request_id": msg.payload.get("request_id"),
                "message": f"Anonymization failed: {str(e)}"
            }
    
    async def _check_privacy_compliance(self, ctx: Context, records: List[Dict[str, Any]],
                                       config: Dict[str, Any]) -> Dict[str, Any]:
        """Check privacy compliance before anonymization."""
        self.stats["compliance_checks"] += 1
        
        # Evaluate privacy rules
        if self.metta_agent_address:
            # Query MeTTa for privacy rules
            compliance_result = await self.compliance_manager.evaluate_privacy_rules(
                ctx=ctx,
                records=records,
                config=config,
                metta_address=self.metta_agent_address
            )
        else:
            # Use local compliance rules
            compliance_result = self.compliance_manager.evaluate_local_rules(
                records=records,
                config=config
            )
        
        return compliance_result
    
    async def _handle_privacy_compliance_check(self, ctx: Context, sender: str,
                                               msg: AgentMessage) -> Dict[str, Any]:
        """Handle privacy compliance check requests."""
        try:
            records = msg.payload.get("records", [])
            config = msg.payload.get("config", {})
            
            compliance_result = await self._check_privacy_compliance(ctx, records, config)
            
            return {
                "status": "success",
                "compliance_result": compliance_result
            }
            
        except Exception as e:
            self.logger.error("Failed to check privacy compliance", error=str(e))
            return {
                "status": "error",
                "message": f"Compliance check failed: {str(e)}"
            }
    
    async def _handle_privacy_metrics(self, ctx: Context, sender: str,
                                     msg: AgentMessage) -> Dict[str, Any]:
        """Handle privacy metrics calculation requests."""
        try:
            original_records = msg.payload.get("original_records", [])
            anonymized_records = msg.payload.get("anonymized_records", [])
            quasi_identifier_fields = msg.payload.get("quasi_identifier_fields", [])
            
            metrics = self.anonymization_engine.calculate_privacy_metrics(
                original_records=original_records,
                anonymized_records=anonymized_records,
                quasi_identifier_fields=quasi_identifier_fields
            )
            
            return {
                "status": "success",
                "privacy_metrics": metrics
            }
            
        except Exception as e:
            self.logger.error("Failed to calculate privacy metrics", error=str(e))
            return {
                "status": "error",
                "message": f"Metrics calculation failed: {str(e)}"
            }
    
    async def _handle_audit_logs(self, ctx: Context, sender: str,
                                msg: AgentMessage) -> Dict[str, Any]:
        """Handle audit log retrieval requests."""
        try:
            request_id = msg.payload.get("request_id")
            dataset_id = msg.payload.get("dataset_id")
            start_date = msg.payload.get("start_date")
            end_date = msg.payload.get("end_date")
            
            logs = self.audit_logger.get_audit_logs(
                request_id=request_id,
                dataset_id=dataset_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "status": "success",
                "audit_logs": logs,
                "total_logs": len(logs)
            }
            
        except Exception as e:
            self.logger.error("Failed to retrieve audit logs", error=str(e))
            return {
                "status": "error",
                "message": f"Audit log retrieval failed: {str(e)}"
            }
    
    async def _handle_privacy_rules_update(self, ctx: Context, sender: str,
                                          msg: AgentMessage) -> Dict[str, Any]:
        """Handle privacy rules update requests."""
        try:
            new_rules = msg.payload.get("rules", {})
            rule_version = msg.payload.get("version")
            
            # Update privacy rules
            update_result = self.compliance_manager.update_privacy_rules(
                new_rules=new_rules,
                version=rule_version
            )
            
            # Store updated rules in MeTTa if available
            if self.metta_agent_address:
                await self.compliance_manager.store_rules_in_metta(
                    ctx=ctx,
                    rules=new_rules,
                    version=rule_version,
                    metta_address=self.metta_agent_address
                )
            
            self.logger.audit(
                event_type="privacy_rules_updated",
                details={
                    "version": rule_version,
                    "rule_count": len(new_rules),
                    "updated_by": sender
                }
            )
            
            return {
                "status": "success",
                "message": "Privacy rules updated successfully",
                "version": update_result["version"],
                "rule_count": update_result["rule_count"]
            }
            
        except Exception as e:
            self.logger.error("Failed to update privacy rules", error=str(e))
            return {
                "status": "error",
                "message": f"Privacy rules update failed: {str(e)}"
            }
    
    async def _handle_health_check(self, ctx: Context, sender: str,
                                   msg: AgentMessage) -> Dict[str, Any]:
        """Handle health check requests."""
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "k_anonymity": self.anonymization_engine.k,
            "epsilon": self.anonymization_engine.epsilon,
            "statistics": self.stats,
            "privacy_rules_version": self.compliance_manager.get_current_version(),
            "last_heartbeat": self.last_heartbeat.isoformat()
        }
    
    async def on_startup(self, ctx: Context):
        """Custom startup logic."""
        self.logger.info("Privacy Agent starting up",
                        k_anonymity=self.anonymization_engine.k,
                        epsilon=self.anonymization_engine.epsilon)


# Main entry point for running the agent
if __name__ == "__main__":
    # Configuration
    PORT = int(os.getenv("PRIVACY_AGENT_PORT", "8004"))
    METTA_AGENT_ADDRESS = os.getenv("METTA_AGENT_ADDRESS")
    K_ANONYMITY = int(os.getenv("K_ANONYMITY", "5"))
    EPSILON = float(os.getenv("EPSILON", "1.0"))
    
    # Create and run agent
    agent = PrivacyAgent(
        port=PORT,
        metta_agent_address=METTA_AGENT_ADDRESS,
        k_anonymity=K_ANONYMITY,
        epsilon=EPSILON
    )
    
    agent.run()
