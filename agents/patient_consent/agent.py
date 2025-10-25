"""
Patient Consent Agent for HealthSync system.
Manages patient data sharing permissions with granular control.
"""

from uagents import Context
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import sys
import os
import uuid
import hashlib

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.base_agent import HealthSyncBaseAgent
from shared.protocols.agent_messages import (
    MessageTypes, ConsentMessage, ConsentQuery, 
    AgentMessage, ErrorCodes, ErrorResponse
)
from shared.protocols.chat_protocol import ChatMessage, ChatResponse, ChatSession
from shared.utils.error_handling import with_error_handling


class ConsentRecord:
    """Represents a patient consent record with validation and expiration."""
    
    def __init__(self, patient_id: str, data_types: List[str], 
                 research_categories: List[str], consent_status: bool,
                 expiry_date: datetime, metadata: Optional[Dict[str, Any]] = None):
        self.consent_id = self._generate_consent_id(patient_id)
        self.patient_id = patient_id
        self.data_types = data_types
        self.research_categories = research_categories
        self.consent_status = consent_status
        self.expiry_date = expiry_date
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.metadata = metadata or {}
        self.version = 1
        self.audit_trail: List[Dict[str, Any]] = []
        
        # Add creation to audit trail
        self._add_audit_entry("created", {"initial_status": consent_status})
    
    def _generate_consent_id(self, patient_id: str) -> str:
        """Generate unique consent ID."""
        unique_str = f"{patient_id}:{datetime.utcnow().isoformat()}:{uuid.uuid4()}"
        return f"CNS-{hashlib.md5(unique_str.encode()).hexdigest()[:12].upper()}"
    
    def _add_audit_entry(self, action: str, details: Dict[str, Any]):
        """Add entry to audit trail."""
        self.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "version": self.version
        })
    
    def is_expired(self) -> bool:
        """Check if consent has expired."""
        return datetime.utcnow() > self.expiry_date
    
    def is_valid(self) -> bool:
        """Check if consent is valid (granted and not expired)."""
        return self.consent_status and not self.is_expired()
    
    def update_consent(self, consent_status: bool, data_types: Optional[List[str]] = None,
                      research_categories: Optional[List[str]] = None,
                      expiry_date: Optional[datetime] = None) -> bool:
        """Update consent record with validation."""
        changes = {}
        
        if consent_status != self.consent_status:
            changes["consent_status"] = {"old": self.consent_status, "new": consent_status}
            self.consent_status = consent_status
        
        if data_types is not None and data_types != self.data_types:
            changes["data_types"] = {"old": self.data_types, "new": data_types}
            self.data_types = data_types
        
        if research_categories is not None and research_categories != self.research_categories:
            changes["research_categories"] = {"old": self.research_categories, "new": research_categories}
            self.research_categories = research_categories
        
        if expiry_date is not None and expiry_date != self.expiry_date:
            changes["expiry_date"] = {"old": self.expiry_date.isoformat(), "new": expiry_date.isoformat()}
            self.expiry_date = expiry_date
        
        if changes:
            self.last_updated = datetime.utcnow()
            self.version += 1
            self._add_audit_entry("updated", changes)
            return True
        
        return False
    
    def renew_consent(self, duration_days: int = 365) -> datetime:
        """Renew consent for specified duration."""
        new_expiry = datetime.utcnow() + timedelta(days=duration_days)
        self.expiry_date = new_expiry
        self.last_updated = datetime.utcnow()
        self.version += 1
        self._add_audit_entry("renewed", {
            "new_expiry_date": new_expiry.isoformat(),
            "duration_days": duration_days
        })
        return new_expiry
    
    def revoke_consent(self):
        """Revoke consent immediately."""
        self.consent_status = False
        self.last_updated = datetime.utcnow()
        self.version += 1
        self._add_audit_entry("revoked", {"revoked_at": datetime.utcnow().isoformat()})
    
    def check_permission(self, data_type: str, research_category: str) -> Tuple[bool, str]:
        """Check if consent allows specific data type and research category."""
        if not self.is_valid():
            if self.is_expired():
                return False, ErrorCodes.CONSENT_EXPIRED
            elif not self.consent_status:
                return False, ErrorCodes.CONSENT_REVOKED
            else:
                return False, ErrorCodes.CONSENT_NOT_FOUND
        
        if data_type not in self.data_types:
            return False, "DATA_TYPE_NOT_CONSENTED"
        
        if research_category not in self.research_categories:
            return False, "RESEARCH_CATEGORY_NOT_CONSENTED"
        
        return True, "CONSENT_VALID"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert consent record to dictionary."""
        return {
            "consent_id": self.consent_id,
            "patient_id": self.patient_id,
            "data_types": self.data_types,
            "research_categories": self.research_categories,
            "consent_status": self.consent_status,
            "expiry_date": self.expiry_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
            "is_valid": self.is_valid(),
            "is_expired": self.is_expired()
        }
    
    def to_metta_entity(self) -> Dict[str, Any]:
        """Convert to MeTTa entity format for storage."""
        return {
            "entity_type": "ConsentRecord",
            "consent_id": self.consent_id,
            "patient_ref": self.patient_id,
            "data_type_ref": self.data_types[0] if self.data_types else None,
            "research_category_ref": self.research_categories[0] if self.research_categories else None,
            "consent_granted": self.consent_status,
            "expiry_date": self.expiry_date.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "version": self.version
        }


class PatientConsentAgent(HealthSyncBaseAgent):
    """Agent responsible for managing patient consent preferences."""
    
    def __init__(self, port: int = 8002, metta_agent_address: Optional[str] = None):
        super().__init__(
            name="Patient Consent Agent",
            port=port,
            endpoint=f"http://localhost:{port}/submit"
        )
        
        # Consent storage (local cache + MeTTa Knowledge Graph)
        self.consent_records: Dict[str, ConsentRecord] = {}
        
        # MeTTa Integration Agent address for storage
        self.metta_agent_address = metta_agent_address
        
        # Consent statistics
        self.stats = {
            "total_consents": 0,
            "active_consents": 0,
            "expired_consents": 0,
            "revoked_consents": 0,
            "consent_queries": 0,
            "consent_updates": 0
        }
        
        # Register message handlers
        self._register_handlers()
        
        self.logger.info("Patient Consent Agent initialized")
    
    def _register_handlers(self):
        """Register message handlers for consent operations."""
        
        self.register_message_handler(
            MessageTypes.CONSENT_UPDATE,
            self._handle_consent_update
        )
        
        self.register_message_handler(
            MessageTypes.CONSENT_QUERY,
            self._handle_consent_query
        )
        
        self.register_message_handler(
            MessageTypes.HEALTH_CHECK,
            self._handle_health_check
        )
        
        # Additional handlers for consent management
        self.register_message_handler(
            "consent_renew",
            self._handle_consent_renewal
        )
        
        self.register_message_handler(
            "consent_revoke",
            self._handle_consent_revocation
        )
        
        self.register_message_handler(
            "consent_history",
            self._handle_consent_history
        )
    
    @with_error_handling("patient_consent_agent")
    async def _handle_consent_update(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle patient consent update requests with validation and MeTTa storage."""
        try:
            # Validate message payload
            consent_data = ConsentMessage(**msg.payload)
            
            # Validate data types and research categories
            validation_result = self._validate_consent_data(
                consent_data.data_types,
                consent_data.research_categories
            )
            
            if not validation_result["valid"]:
                self.logger.warning("Consent validation failed",
                                  patient_id=consent_data.patient_id,
                                  errors=validation_result["errors"])
                return {
                    "status": "error",
                    "message": "Consent validation failed",
                    "errors": validation_result["errors"]
                }
            
            # Check if consent record exists for update or create new
            if consent_data.patient_id in self.consent_records:
                # Update existing consent
                consent_record = self.consent_records[consent_data.patient_id]
                updated = consent_record.update_consent(
                    consent_status=consent_data.consent_status,
                    data_types=consent_data.data_types,
                    research_categories=consent_data.research_categories,
                    expiry_date=consent_data.expiry_date
                )
                
                action = "updated" if updated else "no_change"
            else:
                # Create new consent record
                consent_record = ConsentRecord(
                    patient_id=consent_data.patient_id,
                    data_types=consent_data.data_types,
                    research_categories=consent_data.research_categories,
                    consent_status=consent_data.consent_status,
                    expiry_date=consent_data.expiry_date,
                    metadata=consent_data.metadata
                )
                self.consent_records[consent_data.patient_id] = consent_record
                action = "created"
                self.stats["total_consents"] += 1
            
            # Update statistics
            self._update_consent_statistics()
            self.stats["consent_updates"] += 1
            
            # Store in MeTTa Knowledge Graph
            if self.metta_agent_address:
                await self._store_consent_in_metta(ctx, consent_record)
            
            # Log audit trail
            self.logger.audit(
                event_type=f"consent_{action}",
                details={
                    "consent_id": consent_record.consent_id,
                    "patient_id": consent_data.patient_id,
                    "data_types": consent_data.data_types,
                    "research_categories": consent_data.research_categories,
                    "consent_status": consent_data.consent_status,
                    "expiry_date": consent_data.expiry_date.isoformat(),
                    "version": consent_record.version
                }
            )
            
            return {
                "status": "success",
                "action": action,
                "consent_id": consent_record.consent_id,
                "patient_id": consent_data.patient_id,
                "version": consent_record.version,
                "is_valid": consent_record.is_valid()
            }
            
        except Exception as e:
            self.logger.error("Failed to update consent",
                            error=str(e),
                            patient_id=msg.payload.get("patient_id"))
            return {
                "status": "error",
                "message": f"Failed to update consent: {str(e)}"
            }
    
    @with_error_handling("patient_consent_agent")
    async def _handle_consent_query(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle consent verification queries with detailed validation."""
        try:
            query_data = ConsentQuery(**msg.payload)
            
            self.stats["consent_queries"] += 1
            
            # Check if patient has consent record
            if query_data.patient_id not in self.consent_records:
                self.logger.audit(
                    event_type="consent_query_not_found",
                    details={
                        "patient_id": query_data.patient_id,
                        "data_type": query_data.data_type,
                        "research_category": query_data.research_category,
                        "requester_id": query_data.requester_id
                    }
                )
                
                return {
                    "status": "not_found",
                    "consent_granted": False,
                    "error_code": ErrorCodes.CONSENT_NOT_FOUND,
                    "message": "No consent record found for patient"
                }
            
            consent_record = self.consent_records[query_data.patient_id]
            
            # Check permission with detailed validation
            permission_granted, status_code = consent_record.check_permission(
                query_data.data_type,
                query_data.research_category
            )
            
            # Prepare response based on validation result
            response = {
                "status": "success",
                "consent_granted": permission_granted,
                "patient_id": query_data.patient_id,
                "consent_id": consent_record.consent_id,
                "status_code": status_code,
                "expiry_date": consent_record.expiry_date.isoformat(),
                "is_expired": consent_record.is_expired(),
                "version": consent_record.version
            }
            
            # Add error details if consent not granted
            if not permission_granted:
                if status_code == ErrorCodes.CONSENT_EXPIRED:
                    response["message"] = "Consent has expired"
                    response["expired_at"] = consent_record.expiry_date.isoformat()
                elif status_code == ErrorCodes.CONSENT_REVOKED:
                    response["message"] = "Consent has been revoked"
                elif status_code == "DATA_TYPE_NOT_CONSENTED":
                    response["message"] = f"Data type '{query_data.data_type}' not included in consent"
                    response["allowed_data_types"] = consent_record.data_types
                elif status_code == "RESEARCH_CATEGORY_NOT_CONSENTED":
                    response["message"] = f"Research category '{query_data.research_category}' not included in consent"
                    response["allowed_categories"] = consent_record.research_categories
            
            # Log audit trail
            self.logger.audit(
                event_type="consent_queried",
                details={
                    "consent_id": consent_record.consent_id,
                    "patient_id": query_data.patient_id,
                    "data_type": query_data.data_type,
                    "research_category": query_data.research_category,
                    "requester_id": query_data.requester_id,
                    "consent_granted": permission_granted,
                    "status_code": status_code
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to query consent",
                            error=str(e),
                            patient_id=msg.payload.get("patient_id"))
            return {
                "status": "error",
                "consent_granted": False,
                "message": f"Failed to query consent: {str(e)}"
            }
    
    async def _handle_consent_renewal(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle consent renewal requests."""
        try:
            patient_id = msg.payload.get("patient_id")
            duration_days = msg.payload.get("duration_days", 365)
            
            if patient_id not in self.consent_records:
                return {
                    "status": "error",
                    "error_code": ErrorCodes.CONSENT_NOT_FOUND,
                    "message": "No consent record found for patient"
                }
            
            consent_record = self.consent_records[patient_id]
            new_expiry = consent_record.renew_consent(duration_days)
            
            # Update in MeTTa
            if self.metta_agent_address:
                await self._store_consent_in_metta(ctx, consent_record)
            
            self.logger.audit(
                event_type="consent_renewed",
                details={
                    "consent_id": consent_record.consent_id,
                    "patient_id": patient_id,
                    "new_expiry_date": new_expiry.isoformat(),
                    "duration_days": duration_days,
                    "version": consent_record.version
                }
            )
            
            return {
                "status": "success",
                "consent_id": consent_record.consent_id,
                "patient_id": patient_id,
                "new_expiry_date": new_expiry.isoformat(),
                "version": consent_record.version
            }
            
        except Exception as e:
            self.logger.error("Failed to renew consent", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to renew consent: {str(e)}"
            }
    
    async def _handle_consent_revocation(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle consent revocation requests."""
        try:
            patient_id = msg.payload.get("patient_id")
            
            if patient_id not in self.consent_records:
                return {
                    "status": "error",
                    "error_code": ErrorCodes.CONSENT_NOT_FOUND,
                    "message": "No consent record found for patient"
                }
            
            consent_record = self.consent_records[patient_id]
            consent_record.revoke_consent()
            
            # Update statistics
            self._update_consent_statistics()
            
            # Update in MeTTa
            if self.metta_agent_address:
                await self._store_consent_in_metta(ctx, consent_record)
            
            self.logger.audit(
                event_type="consent_revoked",
                details={
                    "consent_id": consent_record.consent_id,
                    "patient_id": patient_id,
                    "revoked_at": datetime.utcnow().isoformat(),
                    "version": consent_record.version
                }
            )
            
            return {
                "status": "success",
                "consent_id": consent_record.consent_id,
                "patient_id": patient_id,
                "revoked_at": datetime.utcnow().isoformat(),
                "version": consent_record.version
            }
            
        except Exception as e:
            self.logger.error("Failed to revoke consent", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to revoke consent: {str(e)}"
            }
    
    async def _handle_consent_history(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle consent history requests."""
        try:
            patient_id = msg.payload.get("patient_id")
            
            if patient_id not in self.consent_records:
                return {
                    "status": "error",
                    "error_code": ErrorCodes.CONSENT_NOT_FOUND,
                    "message": "No consent record found for patient"
                }
            
            consent_record = self.consent_records[patient_id]
            
            return {
                "status": "success",
                "consent_id": consent_record.consent_id,
                "patient_id": patient_id,
                "current_version": consent_record.version,
                "audit_trail": consent_record.audit_trail,
                "consent_details": consent_record.to_dict()
            }
            
        except Exception as e:
            self.logger.error("Failed to retrieve consent history", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to retrieve consent history: {str(e)}"
            }
    
    async def _handle_health_check(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle health check requests."""
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "consent_records_count": len(self.consent_records),
            "statistics": self.stats,
            "last_heartbeat": self.last_heartbeat.isoformat()
        }
    
    async def _handle_chat_message(self, ctx: Context, sender: str, msg: ChatMessage) -> ChatResponse:
        """Handle Chat Protocol messages for natural language consent management."""
        try:
            self.logger.info("Processing chat message",
                           session_id=msg.session_id,
                           user_id=msg.user_id,
                           content_type=msg.content_type)
            
            # Validate or create session
            if msg.session_id not in self.chat_handler.active_sessions:
                session = self.chat_handler.create_session(
                    user_id=msg.user_id,
                    session_type="patient_consent"
                )
                self.logger.info("Created new chat session",
                               session_id=session.session_id,
                               user_id=msg.user_id)
            
            # Process message based on content type
            if msg.content_type == "text":
                return await self._handle_text_message(msg)
            elif msg.content_type == "structured_data":
                return await self._handle_structured_consent_data(msg)
            elif msg.content_type == "command":
                return await self._handle_consent_command(msg)
            else:
                return ChatResponse(
                    original_message_id=msg.message_id,
                    agent_id=self.agent_id,
                    response_type="error",
                    response_data=f"Unsupported content type: {msg.content_type}"
                )
                
        except Exception as e:
            self.logger.error("Error processing chat message",
                            message_id=msg.message_id,
                            error=str(e))
            return ChatResponse(
                original_message_id=msg.message_id,
                agent_id=self.agent_id,
                response_type="error",
                response_data=f"Error processing your request: {str(e)}"
            )
    
    async def _handle_text_message(self, message: ChatMessage) -> ChatResponse:
        """Handle natural language consent updates via Chat Protocol."""
        try:
            content = message.content_data.lower() if isinstance(message.content_data, str) else ""
            session = self.chat_handler.active_sessions.get(message.session_id)
            
            # Parse natural language intent
            intent = self._parse_consent_intent(content)
            
            if intent == "grant_consent":
                # Extract data types and research categories from natural language
                parsed_data = self._extract_consent_preferences(content)
                
                if not parsed_data.get("patient_id"):
                    # Store context and ask for patient ID
                    session.context["pending_action"] = "grant_consent"
                    session.context["parsed_data"] = parsed_data
                    
                    return ChatResponse(
                        original_message_id=message.message_id,
                        agent_id=self.agent_id,
                        response_type="question",
                        response_data="I understand you want to grant consent. Could you please provide your patient ID?",
                        requires_followup=True
                    )
                
                # Create consent with parsed data
                response_data = await self._create_consent_from_chat(parsed_data)
                
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="data",
                    response_data=response_data
                )
            
            elif intent == "revoke_consent":
                patient_id = self._extract_patient_id(content, session)
                
                if not patient_id:
                    session.context["pending_action"] = "revoke_consent"
                    return ChatResponse(
                        original_message_id=message.message_id,
                        agent_id=self.agent_id,
                        response_type="question",
                        response_data="I understand you want to revoke consent. Could you please provide your patient ID?",
                        requires_followup=True
                    )
                
                # Revoke consent
                if patient_id in self.consent_records:
                    self.consent_records[patient_id].revoke_consent()
                    response_data = f"Your consent has been revoked successfully. All future data sharing has been blocked."
                else:
                    response_data = f"No consent record found for patient ID: {patient_id}"
                
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="data",
                    response_data=response_data
                )
            
            elif intent == "check_status":
                patient_id = self._extract_patient_id(content, session)
                
                if not patient_id:
                    session.context["pending_action"] = "check_status"
                    return ChatResponse(
                        original_message_id=message.message_id,
                        agent_id=self.agent_id,
                        response_type="question",
                        response_data="I can help you check your consent status. Could you please provide your patient ID?",
                        requires_followup=True
                    )
                
                # Get consent status
                if patient_id in self.consent_records:
                    record = self.consent_records[patient_id]
                    status_info = {
                        "patient_id": patient_id,
                        "consent_status": "Active" if record.is_valid() else "Inactive",
                        "data_types": record.data_types,
                        "research_categories": record.research_categories,
                        "expiry_date": record.expiry_date.strftime("%Y-%m-%d"),
                        "is_expired": record.is_expired()
                    }
                    response_data = f"Your consent status:\n- Status: {status_info['consent_status']}\n- Data types: {', '.join(status_info['data_types'])}\n- Research categories: {', '.join(status_info['research_categories'])}\n- Expires: {status_info['expiry_date']}"
                else:
                    response_data = f"No consent record found for patient ID: {patient_id}"
                
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="data",
                    response_data=response_data
                )
            
            elif intent == "renew_consent":
                patient_id = self._extract_patient_id(content, session)
                
                if not patient_id:
                    session.context["pending_action"] = "renew_consent"
                    return ChatResponse(
                        original_message_id=message.message_id,
                        agent_id=self.agent_id,
                        response_type="question",
                        response_data="I can help you renew your consent. Could you please provide your patient ID?",
                        requires_followup=True
                    )
                
                # Renew consent
                if patient_id in self.consent_records:
                    new_expiry = self.consent_records[patient_id].renew_consent()
                    response_data = f"Your consent has been renewed successfully. New expiry date: {new_expiry.strftime('%Y-%m-%d')}"
                else:
                    response_data = f"No consent record found for patient ID: {patient_id}"
                
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="data",
                    response_data=response_data
                )
            
            elif intent == "provide_patient_id":
                # Handle follow-up patient ID provision
                patient_id = self._extract_patient_id(content, session)
                pending_action = session.context.get("pending_action")
                
                if patient_id and pending_action:
                    session.context["patient_id"] = patient_id
                    
                    if pending_action == "grant_consent":
                        return ChatResponse(
                            original_message_id=message.message_id,
                            agent_id=self.agent_id,
                            response_type="question",
                            response_data="Great! Now, which data types would you like to share? (e.g., medical records, lab results, prescriptions)",
                            requires_followup=True
                        )
                    elif pending_action == "check_status":
                        # Recursively call with updated context
                        message.content_data = f"check status for {patient_id}"
                        return await self._handle_text_message(message)
                    elif pending_action == "revoke_consent":
                        message.content_data = f"revoke consent for {patient_id}"
                        return await self._handle_text_message(message)
                    elif pending_action == "renew_consent":
                        message.content_data = f"renew consent for {patient_id}"
                        return await self._handle_text_message(message)
            
            else:
                # Default help message
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="data",
                    response_data="I can help you manage your healthcare data consent. You can:\n- Grant consent for data sharing\n- Revoke existing consent\n- Check your current consent status\n- Renew expiring consent\n\nWhat would you like to do?"
                )
                
        except Exception as e:
            self.logger.error("Error handling text message",
                            message_id=message.message_id,
                            error=str(e))
            return ChatResponse(
                original_message_id=message.message_id,
                agent_id=self.agent_id,
                response_type="error",
                response_data=f"Error processing your request: {str(e)}"
            )
    
    async def _handle_structured_consent_data(self, message: ChatMessage) -> ChatResponse:
        """Handle structured consent data from Chat Protocol."""
        try:
            data = message.content_data if isinstance(message.content_data, dict) else {}
            
            # Validate required fields
            required_fields = ["patient_id", "data_types", "research_categories", "consent_status"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="error",
                    response_data=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Create or update consent
            expiry_date = datetime.fromisoformat(data.get("expiry_date")) if data.get("expiry_date") else datetime.utcnow() + timedelta(days=365)
            
            consent_msg = ConsentMessage(
                patient_id=data["patient_id"],
                data_types=data["data_types"],
                research_categories=data["research_categories"],
                consent_status=data["consent_status"],
                expiry_date=expiry_date,
                metadata=data.get("metadata", {})
            )
            
            # Create mock context and message for internal processing
            mock_msg = AgentMessage(
                sender_agent=message.user_id,
                recipient_agent=self.agent_id,
                message_type=MessageTypes.CONSENT_UPDATE,
                payload=consent_msg.dict(),
                timestamp=datetime.utcnow()
            )
            
            result = await self._handle_consent_update(None, message.user_id, mock_msg)
            
            return ChatResponse(
                original_message_id=message.message_id,
                agent_id=self.agent_id,
                response_type="data",
                response_data=result
            )
            
        except Exception as e:
            self.logger.error("Error handling structured consent data",
                            message_id=message.message_id,
                            error=str(e))
            return ChatResponse(
                original_message_id=message.message_id,
                agent_id=self.agent_id,
                response_type="error",
                response_data=f"Error processing structured data: {str(e)}"
            )
    
    async def _handle_consent_command(self, message: ChatMessage) -> ChatResponse:
        """Handle consent commands from Chat Protocol."""
        try:
            command = message.content_data if isinstance(message.content_data, str) else message.content_data.get("command", "")
            params = message.content_data.get("params", {}) if isinstance(message.content_data, dict) else {}
            
            if command == "get_consent":
                patient_id = params.get("patient_id")
                if patient_id and patient_id in self.consent_records:
                    record = self.consent_records[patient_id]
                    return ChatResponse(
                        original_message_id=message.message_id,
                        agent_id=self.agent_id,
                        response_type="data",
                        response_data=record.to_dict()
                    )
                else:
                    return ChatResponse(
                        original_message_id=message.message_id,
                        agent_id=self.agent_id,
                        response_type="error",
                        response_data="Consent record not found"
                    )
            
            elif command == "list_consents":
                consents = [record.to_dict() for record in self.consent_records.values()]
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="data",
                    response_data={"consents": consents, "total": len(consents)}
                )
            
            elif command == "get_statistics":
                stats = self.get_consent_statistics()
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="data",
                    response_data=stats
                )
            
            else:
                return ChatResponse(
                    original_message_id=message.message_id,
                    agent_id=self.agent_id,
                    response_type="error",
                    response_data=f"Unknown command: {command}"
                )
                
        except Exception as e:
            self.logger.error("Error handling consent command",
                            message_id=message.message_id,
                            error=str(e))
            return ChatResponse(
                original_message_id=message.message_id,
                agent_id=self.agent_id,
                response_type="error",
                response_data=f"Error processing command: {str(e)}"
            )
    
    def _parse_consent_intent(self, text: str) -> str:
        """Parse natural language to determine consent intent."""
        text = text.lower()
        
        # Check for patient ID patterns
        if any(pattern in text for pattern in ["p001", "p002", "p003", "patient", "id"]):
            if "grant" not in text and "revoke" not in text and "check" not in text and "renew" not in text:
                return "provide_patient_id"
        
        if any(word in text for word in ["grant", "allow", "permit", "enable", "share"]):
            return "grant_consent"
        elif any(word in text for word in ["revoke", "remove", "deny", "disable", "stop"]):
            return "revoke_consent"
        elif any(word in text for word in ["status", "check", "view", "show", "current"]):
            return "check_status"
        elif any(word in text for word in ["renew", "extend", "update expiry"]):
            return "renew_consent"
        else:
            return "unknown"
    
    def _extract_patient_id(self, text: str, session: Optional[ChatSession] = None) -> Optional[str]:
        """Extract patient ID from natural language or session context."""
        # Check session context first
        if session and "patient_id" in session.context:
            return session.context["patient_id"]
        
        # Look for patient ID patterns in text
        import re
        patterns = [
            r'\b(P\d{3,})\b',  # Pattern like P001, P002 (most specific, check first)
            r'patient[_\s]?id[:\s]+([A-Z0-9]+)',
            r'(?:^|[^a-z])id[:\s]+([A-Z0-9]+)',  # ID: followed by alphanumeric, not preceded by letter
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_id = match.group(1).upper()
                # Validate it looks like a patient ID (starts with P and has digits)
                if patient_id.startswith('P') and any(c.isdigit() for c in patient_id):
                    return patient_id
        
        return None
    
    def _extract_consent_preferences(self, text: str) -> Dict[str, Any]:
        """Extract consent preferences from natural language."""
        preferences = {
            "data_types": [],
            "research_categories": [],
            "patient_id": None
        }
        
        # Extract patient ID
        preferences["patient_id"] = self._extract_patient_id(text)
        
        # Extract data types
        data_type_keywords = {
            "medical records": "medical_records",
            "lab results": "lab_results",
            "prescriptions": "prescriptions",
            "demographics": "demographics"
        }
        
        for keyword, data_type in data_type_keywords.items():
            if keyword in text.lower():
                preferences["data_types"].append(data_type)
        
        # Extract research categories
        research_keywords = {
            "cancer": "cancer_research",
            "diabetes": "diabetes_research",
            "cardiovascular": "cardiovascular_research",
            "heart": "cardiovascular_research"
        }
        
        for keyword, category in research_keywords.items():
            if keyword in text.lower():
                if category not in preferences["research_categories"]:
                    preferences["research_categories"].append(category)
        
        return preferences
    
    async def _create_consent_from_chat(self, parsed_data: Dict[str, Any]) -> str:
        """Create consent record from parsed chat data."""
        try:
            if not parsed_data.get("patient_id"):
                return "Error: Patient ID is required"
            
            if not parsed_data.get("data_types"):
                return "Error: At least one data type must be specified"
            
            if not parsed_data.get("research_categories"):
                return "Error: At least one research category must be specified"
            
            # Create consent record
            consent_record = ConsentRecord(
                patient_id=parsed_data["patient_id"],
                data_types=parsed_data["data_types"],
                research_categories=parsed_data["research_categories"],
                consent_status=True,
                expiry_date=datetime.utcnow() + timedelta(days=365)
            )
            
            self.consent_records[parsed_data["patient_id"]] = consent_record
            self.stats["total_consents"] += 1
            self._update_consent_statistics()
            
            return f"Consent granted successfully!\n- Patient ID: {consent_record.patient_id}\n- Data types: {', '.join(consent_record.data_types)}\n- Research categories: {', '.join(consent_record.research_categories)}\n- Expires: {consent_record.expiry_date.strftime('%Y-%m-%d')}"
            
        except Exception as e:
            return f"Error creating consent: {str(e)}"
    
    def _validate_consent_data(self, data_types: List[str], 
                              research_categories: List[str]) -> Dict[str, Any]:
        """Validate consent data types and research categories."""
        errors = []
        
        # Validate data types are not empty
        if not data_types:
            errors.append("At least one data type must be specified")
        
        # Validate research categories are not empty
        if not research_categories:
            errors.append("At least one research category must be specified")
        
        # Validate data type format (should be alphanumeric with underscores)
        for dt in data_types:
            if not dt or not isinstance(dt, str):
                errors.append(f"Invalid data type format: {dt}")
        
        # Validate research category format
        for rc in research_categories:
            if not rc or not isinstance(rc, str):
                errors.append(f"Invalid research category format: {rc}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _store_consent_in_metta(self, ctx: Context, consent_record: ConsentRecord):
        """Store consent record in MeTTa Knowledge Graph."""
        try:
            # Convert consent to MeTTa entity format
            metta_entity = consent_record.to_metta_entity()
            
            # Send storage request to MeTTa Integration Agent
            await self.send_message(
                ctx,
                self.metta_agent_address,
                MessageTypes.METTA_STORE,
                {
                    "entity_type": "ConsentRecord",
                    "entity_data": metta_entity,
                    "relationships": []
                },
                requires_ack=True
            )
            
            self.logger.info("Consent stored in MeTTa",
                           consent_id=consent_record.consent_id,
                           patient_id=consent_record.patient_id)
            
        except Exception as e:
            self.logger.error("Failed to store consent in MeTTa",
                            consent_id=consent_record.consent_id,
                            error=str(e))
    
    def _update_consent_statistics(self):
        """Update consent statistics based on current records."""
        active = 0
        expired = 0
        revoked = 0
        
        for consent_record in self.consent_records.values():
            if consent_record.is_valid():
                active += 1
            elif consent_record.is_expired():
                expired += 1
            elif not consent_record.consent_status:
                revoked += 1
        
        self.stats["active_consents"] = active
        self.stats["expired_consents"] = expired
        self.stats["revoked_consents"] = revoked
    
    async def check_and_notify_expiring_consents(self, ctx: Context, days_threshold: int = 30):
        """Check for consents expiring soon and notify patients."""
        expiring_soon = []
        threshold_date = datetime.utcnow() + timedelta(days=days_threshold)
        
        for patient_id, consent_record in self.consent_records.items():
            if (consent_record.is_valid() and 
                consent_record.expiry_date <= threshold_date):
                expiring_soon.append({
                    "patient_id": patient_id,
                    "consent_id": consent_record.consent_id,
                    "expiry_date": consent_record.expiry_date,
                    "days_remaining": (consent_record.expiry_date - datetime.utcnow()).days
                })
        
        if expiring_soon:
            self.logger.info("Consents expiring soon",
                           count=len(expiring_soon),
                           threshold_days=days_threshold)
        
        return expiring_soon
    
    def get_consent_statistics(self) -> Dict[str, Any]:
        """Get comprehensive consent statistics."""
        self._update_consent_statistics()
        return {
            **self.stats,
            "total_patients": len(self.consent_records),
            "consent_coverage": {
                "active_percentage": (self.stats["active_consents"] / max(1, self.stats["total_consents"])) * 100,
                "expired_percentage": (self.stats["expired_consents"] / max(1, self.stats["total_consents"])) * 100,
                "revoked_percentage": (self.stats["revoked_consents"] / max(1, self.stats["total_consents"])) * 100
            }
        }
    
    async def _process_chat_message_override(self, ctx: Context, sender: str, msg: ChatMessage):
        """Override base agent's chat message processing."""
        response = await self._handle_chat_message(ctx, sender, msg)
        await ctx.send(sender, response)
    
    async def on_startup(self, ctx: Context):
        """Custom startup logic for Patient Consent Agent."""
        self.logger.info("Patient Consent Agent starting up",
                        address=ctx.address)
        
        # Initialize MeTTa connection if address provided
        if self.metta_agent_address:
            self.logger.info("MeTTa Integration Agent configured",
                           metta_address=self.metta_agent_address)
        else:
            self.logger.warning("No MeTTa Integration Agent address configured, using local storage only")
        
        # Register Chat Protocol handler override
        self.agent.on_message(model=ChatMessage)(self._process_chat_message_override)
        
    async def on_health_check(self, ctx: Context):
        """Custom health check for Patient Consent Agent."""
        # Check for expiring consents
        expiring = await self.check_and_notify_expiring_consents(ctx, days_threshold=30)
        
        if expiring:
            self.logger.info("Health check: consents expiring soon",
                           count=len(expiring))
        
        # Update statistics
        self._update_consent_statistics()


def main():
    """Main function to run the Patient Consent Agent."""
    agent = PatientConsentAgent()
    agent.run()


if __name__ == "__main__":
    main()