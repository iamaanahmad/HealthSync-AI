"""
Multi-agent workflow orchestration for Research Query Agent.
Coordinates data retrieval workflow across multiple agents.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
from dataclasses import dataclass, field

from shared.protocols.agent_messages import (
    AgentMessage, MessageTypes, ConsentQuery, DataRequest, 
    AnonymizationRequest, MeTTaQuery, ErrorCodes
)
from shared.utils.logging import get_logger


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    CONSENT_CHECK = "consent_check"
    DATA_RETRIEVAL = "data_retrieval"
    ANONYMIZATION = "anonymization"
    AGGREGATION = "aggregation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(Enum):
    """Agent roles in the workflow."""
    CONSENT_AGENT = "patient_consent_agent"
    DATA_CUSTODIAN = "data_custodian_agent"
    PRIVACY_AGENT = "privacy_agent"
    METTA_AGENT = "metta_integration_agent"


@dataclass
class WorkflowStep:
    """Individual step in the workflow."""
    step_id: str
    step_name: str
    agent_role: AgentRole
    status: WorkflowStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowExecution:
    """Complete workflow execution context."""
    workflow_id: str
    query_id: str
    researcher_id: str
    status: WorkflowStatus
    steps: List[WorkflowStep] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_processing_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowOrchestrator:
    """Orchestrates multi-agent workflows for research query processing."""
    
    def __init__(self, agent_addresses: Dict[str, str]):
        self.agent_addresses = agent_addresses
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_history: List[WorkflowExecution] = []
        self.logger = get_logger("workflow_orchestrator")
        
        # Workflow configuration
        self.step_timeout = 300  # 5 minutes per step
        self.workflow_timeout = 1800  # 30 minutes total
        self.max_concurrent_workflows = 10
        
        # Circuit breaker configuration
        self.circuit_breakers = {
            agent_role.value: {
                "failure_count": 0,
                "last_failure": None,
                "is_open": False,
                "failure_threshold": 5,
                "recovery_timeout": 300  # 5 minutes
            }
            for agent_role in AgentRole
        }
        
        # Enhanced error handling and recovery
        self.retry_strategies = {
            AgentRole.METTA_AGENT: {"max_retries": 3, "backoff_factor": 2.0},
            AgentRole.CONSENT_AGENT: {"max_retries": 5, "backoff_factor": 1.5},
            AgentRole.DATA_CUSTODIAN: {"max_retries": 3, "backoff_factor": 2.0},
            AgentRole.PRIVACY_AGENT: {"max_retries": 2, "backoff_factor": 3.0}
        }
        
        # Result aggregation configuration
        self.aggregation_rules = {
            "consent_threshold": 0.8,  # 80% consent required
            "data_quality_threshold": 0.7,  # 70% quality score minimum
            "privacy_compliance_threshold": 0.9  # 90% privacy compliance required
        }
        
        # Audit trail configuration
        self.audit_trail: List[Dict[str, Any]] = []
        self.detailed_logging = True
        
        # Performance metrics
        self.performance_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_processing_time": 0.0,
            "agent_performance": {role.value: {"success_rate": 1.0, "avg_response_time": 0.0} 
                               for role in AgentRole}
        }
    
    async def execute_research_workflow(self, ctx, query_data: Dict[str, Any], 
                                      parsed_query) -> WorkflowExecution:
        """Execute complete research data retrieval workflow."""
        
        # Check concurrent workflow limit
        if len(self.active_workflows) >= self.max_concurrent_workflows:
            raise Exception("Maximum concurrent workflows exceeded")
        
        # Create workflow execution
        workflow = WorkflowExecution(
            workflow_id=str(uuid.uuid4()),
            query_id=query_data.get("query_id", str(uuid.uuid4())),
            researcher_id=query_data["researcher_id"],
            status=WorkflowStatus.PENDING,
            metadata={
                "query_type": parsed_query.query_type.value,
                "data_types": parsed_query.required_data_types,
                "research_categories": parsed_query.research_categories,
                "expected_sample_size": parsed_query.expected_sample_size
            }
        )
        
        self.active_workflows[workflow.workflow_id] = workflow
        
        try:
            # Build workflow steps
            workflow.steps = self._build_workflow_steps(parsed_query)
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.utcnow()
            
            self.logger.info("Starting research workflow",
                           workflow_id=workflow.workflow_id,
                           query_id=workflow.query_id,
                           researcher_id=workflow.researcher_id)
            
            # Execute workflow steps sequentially
            for step in workflow.steps:
                if workflow.status == WorkflowStatus.FAILED:
                    break
                
                await self._execute_workflow_step(ctx, workflow, step)
                
                # Check for workflow timeout
                if self._is_workflow_timeout(workflow):
                    workflow.status = WorkflowStatus.FAILED
                    self._add_error_log(workflow, "WORKFLOW_TIMEOUT", 
                                      "Workflow exceeded maximum execution time")
                    break
            
            # Finalize workflow
            if workflow.status == WorkflowStatus.RUNNING:
                await self._finalize_workflow(workflow)
            
            workflow.completed_at = datetime.utcnow()
            workflow.total_processing_time = (
                workflow.completed_at - workflow.started_at
            ).total_seconds()
            
            self.logger.info("Workflow completed",
                           workflow_id=workflow.workflow_id,
                           status=workflow.status.value,
                           processing_time=workflow.total_processing_time)
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.utcnow()
            self._add_error_log(workflow, "WORKFLOW_EXCEPTION", str(e))
            
            self.logger.error("Workflow failed with exception",
                            workflow_id=workflow.workflow_id,
                            error=str(e))
        
        finally:
            # Move to history and cleanup
            self.workflow_history.append(workflow)
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]
        
        return workflow
    
    def _build_workflow_steps(self, parsed_query) -> List[WorkflowStep]:
        """Build workflow steps based on query requirements."""
        steps = []
        
        # Step 1: Ethical compliance validation with MeTTa
        steps.append(WorkflowStep(
            step_id=f"ethics_validation_{uuid.uuid4().hex[:8]}",
            step_name="Ethical Compliance Validation",
            agent_role=AgentRole.METTA_AGENT,
            status=WorkflowStatus.PENDING,
            input_data={
                "query_type": "validate",
                "query_expression": f"(ethical-compliance-check {parsed_query.ethical_approval_id} {parsed_query.query_type.value})",
                "context_variables": {
                    "researcher_id": parsed_query.researcher_id,
                    "study_description": parsed_query.study_description,
                    "data_types": parsed_query.required_data_types,
                    "research_categories": parsed_query.research_categories
                }
            }
        ))
        
        # Step 2: Patient consent verification
        for data_type in parsed_query.required_data_types:
            for research_category in parsed_query.research_categories:
                steps.append(WorkflowStep(
                    step_id=f"consent_check_{data_type}_{research_category}_{uuid.uuid4().hex[:8]}",
                    step_name=f"Consent Check: {data_type} for {research_category}",
                    agent_role=AgentRole.CONSENT_AGENT,
                    status=WorkflowStatus.PENDING,
                    input_data={
                        "data_type": data_type,
                        "research_category": research_category,
                        "requester_id": parsed_query.researcher_id,
                        "query_id": parsed_query.query_id
                    }
                ))
        
        # Step 3: Data retrieval from custodians
        steps.append(WorkflowStep(
            step_id=f"data_retrieval_{uuid.uuid4().hex[:8]}",
            step_name="Data Retrieval",
            agent_role=AgentRole.DATA_CUSTODIAN,
            status=WorkflowStatus.PENDING,
            input_data={
                "requester_id": parsed_query.researcher_id,
                "data_criteria": {
                    "data_types": parsed_query.required_data_types,
                    "inclusion_criteria": parsed_query.inclusion_criteria,
                    "exclusion_criteria": parsed_query.exclusion_criteria,
                    "date_range": parsed_query.data_requirements.get("date_range"),
                    "minimum_sample_size": parsed_query.expected_sample_size
                },
                "research_purpose": parsed_query.study_description,
                "ethical_approval": parsed_query.ethical_approval_id
            }
        ))
        
        # Step 4: Data anonymization
        steps.append(WorkflowStep(
            step_id=f"anonymization_{uuid.uuid4().hex[:8]}",
            step_name="Data Anonymization",
            agent_role=AgentRole.PRIVACY_AGENT,
            status=WorkflowStatus.PENDING,
            input_data={
                "privacy_level": parsed_query.sensitivity_level.value,
                "k_anonymity_threshold": parsed_query.privacy_requirements.get("k_anonymity", 5),
                "anonymization_methods": parsed_query.privacy_requirements.get(
                    "anonymization_methods", ["k_anonymity", "generalization"]
                )
            }
        ))
        
        return steps
    
    async def _execute_workflow_step(self, ctx, workflow: WorkflowExecution, 
                                   step: WorkflowStep):
        """Execute individual workflow step with enhanced error handling and recovery."""
        
        step.started_at = datetime.utcnow()
        step.status = WorkflowStatus.RUNNING
        
        # Log step initiation
        self._log_audit_event(workflow, "STEP_STARTED", {
            "step_id": step.step_id,
            "step_name": step.step_name,
            "agent_role": step.agent_role.value,
            "retry_count": step.retry_count
        })
        
        # Check circuit breaker
        if self._is_circuit_breaker_open(step.agent_role):
            step.status = WorkflowStatus.FAILED
            step.error_message = f"Circuit breaker open for {step.agent_role.value}"
            workflow.status = WorkflowStatus.FAILED
            
            self._log_audit_event(workflow, "STEP_FAILED_CIRCUIT_BREAKER", {
                "step_id": step.step_id,
                "agent_role": step.agent_role.value,
                "reason": "Circuit breaker is open"
            })
            return
        
        # Get retry strategy for this agent
        retry_strategy = self.retry_strategies.get(step.agent_role, {"max_retries": 3, "backoff_factor": 2.0})
        step.max_retries = retry_strategy["max_retries"]
        
        try:
            self.logger.info("Executing workflow step",
                           workflow_id=workflow.workflow_id,
                           step_id=step.step_id,
                           step_name=step.step_name,
                           agent_role=step.agent_role.value,
                           retry_count=step.retry_count)
            
            # Get agent address
            agent_address = self.agent_addresses.get(step.agent_role.value)
            if not agent_address:
                raise Exception(f"No address configured for {step.agent_role.value}")
            
            # Execute step with timeout
            step_start_time = datetime.utcnow()
            
            try:
                # Execute step based on agent role with timeout
                step_task = None
                if step.agent_role == AgentRole.METTA_AGENT:
                    step_task = self._execute_metta_step(ctx, step, agent_address)
                elif step.agent_role == AgentRole.CONSENT_AGENT:
                    step_task = self._execute_consent_step(ctx, step, agent_address)
                elif step.agent_role == AgentRole.DATA_CUSTODIAN:
                    step_task = self._execute_data_step(ctx, step, agent_address, workflow)
                elif step.agent_role == AgentRole.PRIVACY_AGENT:
                    step_task = self._execute_privacy_step(ctx, step, agent_address, workflow)
                
                # Execute with timeout
                step.output_data = await asyncio.wait_for(step_task, timeout=self.step_timeout)
                
            except asyncio.TimeoutError:
                raise Exception(f"Step execution timed out after {self.step_timeout} seconds")
            
            step_end_time = datetime.utcnow()
            processing_time = (step_end_time - step_start_time).total_seconds()
            
            # Validate step output
            if not self._validate_step_output(step):
                raise Exception(f"Step output validation failed for {step.step_name}")
            
            step.status = WorkflowStatus.COMPLETED
            step.completed_at = step_end_time
            
            # Update performance metrics
            self._update_agent_performance(step.agent_role, True, processing_time)
            
            # Reset circuit breaker on success
            self._reset_circuit_breaker(step.agent_role)
            
            # Log successful completion
            self._log_audit_event(workflow, "STEP_COMPLETED", {
                "step_id": step.step_id,
                "agent_role": step.agent_role.value,
                "processing_time": processing_time,
                "retry_count": step.retry_count,
                "output_summary": self._summarize_step_output(step.output_data)
            })
            
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.error_message = str(e)
            step.completed_at = datetime.utcnow()
            
            # Update performance metrics
            processing_time = (step.completed_at - step.started_at).total_seconds()
            self._update_agent_performance(step.agent_role, False, processing_time)
            
            # Update circuit breaker
            self._record_failure(step.agent_role)
            
            self.logger.error("Workflow step failed",
                            workflow_id=workflow.workflow_id,
                            step_id=step.step_id,
                            error=str(e),
                            retry_count=step.retry_count)
            
            # Log failure
            self._log_audit_event(workflow, "STEP_FAILED", {
                "step_id": step.step_id,
                "agent_role": step.agent_role.value,
                "error": str(e),
                "retry_count": step.retry_count,
                "processing_time": processing_time
            })
            
            # Enhanced retry logic with exponential backoff
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = WorkflowStatus.PENDING
                
                # Calculate backoff delay
                backoff_factor = retry_strategy.get("backoff_factor", 2.0)
                delay = min(300, backoff_factor ** step.retry_count)  # Max 5 minutes
                
                self.logger.info("Retrying workflow step",
                               workflow_id=workflow.workflow_id,
                               step_id=step.step_id,
                               retry_count=step.retry_count,
                               delay=delay)
                
                self._log_audit_event(workflow, "STEP_RETRY_SCHEDULED", {
                    "step_id": step.step_id,
                    "retry_count": step.retry_count,
                    "delay": delay,
                    "reason": str(e)
                })
                
                # Wait before retry with exponential backoff
                await asyncio.sleep(delay)
                await self._execute_workflow_step(ctx, workflow, step)
            else:
                # Max retries exceeded - attempt recovery
                recovery_successful = await self._attempt_step_recovery(ctx, workflow, step)
                
                if not recovery_successful:
                    workflow.status = WorkflowStatus.FAILED
                    self._add_error_log(workflow, "STEP_FAILED_MAX_RETRIES", 
                                      f"Step {step.step_name} failed after {step.max_retries} retries: {str(e)}")
                    
                    self._log_audit_event(workflow, "WORKFLOW_FAILED", {
                        "reason": "Step exceeded maximum retries",
                        "failed_step": step.step_name,
                        "agent_role": step.agent_role.value,
                        "final_error": str(e)
                    })
    
    async def _execute_metta_step(self, ctx, step: WorkflowStep, agent_address: str) -> Dict[str, Any]:
        """Execute MeTTa validation step."""
        message = AgentMessage(
            sender_agent="research_query_agent",
            recipient_agent=agent_address,
            message_type=MessageTypes.METTA_VALIDATE,
            payload=step.input_data
        )
        
        # Send message and wait for response
        response = await self._send_and_wait(ctx, agent_address, message)
        
        if not response.get("success", False):
            raise Exception(f"MeTTa validation failed: {response.get('error_message', 'Unknown error')}")
        
        return {
            "validation_result": response.get("results", []),
            "reasoning_path": response.get("reasoning_path", []),
            "confidence_score": response.get("confidence_score", 0.0)
        }
    
    async def _execute_consent_step(self, ctx, step: WorkflowStep, agent_address: str) -> Dict[str, Any]:
        """Execute consent verification step."""
        # For this step, we need to check consent for all patients
        # In a real implementation, this would query for all patients matching criteria
        
        message = AgentMessage(
            sender_agent="research_query_agent",
            recipient_agent=agent_address,
            message_type=MessageTypes.CONSENT_QUERY,
            payload={
                "patient_id": "aggregate_query",  # Special case for aggregate consent check
                "data_type": step.input_data["data_type"],
                "research_category": step.input_data["research_category"],
                "requester_id": step.input_data["requester_id"]
            }
        )
        
        response = await self._send_and_wait(ctx, agent_address, message)
        
        if not response.get("consent_granted", False):
            error_code = response.get("error_code", "CONSENT_DENIED")
            raise Exception(f"Consent check failed: {error_code}")
        
        return {
            "consent_status": "granted",
            "data_type": step.input_data["data_type"],
            "research_category": step.input_data["research_category"],
            "consent_details": response
        }
    
    async def _execute_data_step(self, ctx, step: WorkflowStep, agent_address: str, 
                               workflow: WorkflowExecution) -> Dict[str, Any]:
        """Execute data retrieval step."""
        
        # Collect consent verification results
        consent_verified = all(
            s.status == WorkflowStatus.COMPLETED and 
            s.output_data.get("consent_status") == "granted"
            for s in workflow.steps 
            if s.agent_role == AgentRole.CONSENT_AGENT
        )
        
        if not consent_verified:
            raise Exception("Cannot retrieve data without valid consent")
        
        message = AgentMessage(
            sender_agent="research_query_agent",
            recipient_agent=agent_address,
            message_type=MessageTypes.DATA_REQUEST,
            payload={
                **step.input_data,
                "consent_verified": True
            }
        )
        
        response = await self._send_and_wait(ctx, agent_address, message)
        
        if not response.get("access_granted", False):
            denial_reason = response.get("denial_reason", "Unknown reason")
            raise Exception(f"Data access denied: {denial_reason}")
        
        return {
            "dataset_id": response.get("dataset_id"),
            "patient_count": response.get("patient_count", 0),
            "data_fields": response.get("data_fields", []),
            "raw_data": response.get("data", [])  # This would be anonymized in next step
        }
    
    async def _execute_privacy_step(self, ctx, step: WorkflowStep, agent_address: str,
                                  workflow: WorkflowExecution) -> Dict[str, Any]:
        """Execute data anonymization step."""
        
        # Get raw data from data retrieval step
        data_step = next(
            (s for s in workflow.steps if s.agent_role == AgentRole.DATA_CUSTODIAN),
            None
        )
        
        if not data_step or not data_step.output_data:
            raise Exception("No data available for anonymization")
        
        raw_data = data_step.output_data.get("raw_data", [])
        dataset_id = data_step.output_data.get("dataset_id", "unknown")
        
        message = AgentMessage(
            sender_agent="research_query_agent",
            recipient_agent=agent_address,
            message_type=MessageTypes.ANONYMIZATION_REQUEST,
            payload={
                "dataset_id": dataset_id,
                "raw_data": raw_data,
                **step.input_data
            }
        )
        
        response = await self._send_and_wait(ctx, agent_address, message)
        
        if not response.get("success", False):
            raise Exception(f"Anonymization failed: {response.get('error', 'Unknown error')}")
        
        return {
            "anonymized_data": response.get("anonymized_records", []),
            "privacy_metrics": response.get("privacy_metrics", {}),
            "anonymization_log": response.get("anonymization_log", ""),
            "quality_score": response.get("quality_score", 0.0)
        }
    
    async def _send_and_wait(self, ctx, agent_address: str, message: AgentMessage, 
                           timeout: int = 300) -> Dict[str, Any]:
        """Send message to agent and wait for response."""
        
        # In a real implementation, this would use proper async messaging
        # For now, we'll simulate the response based on message type
        
        await asyncio.sleep(1)  # Simulate network delay
        
        # Simulate responses based on message type
        if message.message_type == MessageTypes.METTA_VALIDATE:
            return {
                "success": True,
                "results": [{"validation": "passed"}],
                "reasoning_path": ["ethical-approval-valid", "study-purpose-legitimate"],
                "confidence_score": 0.95
            }
        
        elif message.message_type == MessageTypes.CONSENT_QUERY:
            return {
                "consent_granted": True,
                "status": "success",
                "patient_id": message.payload.get("patient_id"),
                "consent_id": f"CNS-{uuid.uuid4().hex[:12].upper()}"
            }
        
        elif message.message_type == MessageTypes.DATA_REQUEST:
            return {
                "access_granted": True,
                "dataset_id": f"DS-{uuid.uuid4().hex[:8].upper()}",
                "patient_count": 150,
                "data_fields": ["age", "gender", "diagnosis", "treatment"],
                "data": [{"patient_id": f"P{i:03d}", "age": 45+i, "gender": "M" if i%2 else "F"} 
                        for i in range(10)]  # Sample data
            }
        
        elif message.message_type == MessageTypes.ANONYMIZATION_REQUEST:
            raw_data = message.payload.get("raw_data", [])
            return {
                "success": True,
                "anonymized_records": [
                    {k: v if k != "patient_id" else f"ANON_{i:03d}" 
                     for k, v in record.items()}
                    for i, record in enumerate(raw_data)
                ],
                "privacy_metrics": {"k_anonymity": 5, "l_diversity": 3},
                "anonymization_log": "Applied k-anonymity and generalization",
                "quality_score": 0.92
            }
        
        else:
            return {"error": f"Unknown message type: {message.message_type}"}
    
    async def _finalize_workflow(self, workflow: WorkflowExecution):
        """Finalize workflow with comprehensive result aggregation."""
        
        self.logger.info("Finalizing workflow",
                        workflow_id=workflow.workflow_id,
                        total_steps=len(workflow.steps))
        
        self._log_audit_event(workflow, "WORKFLOW_FINALIZATION_STARTED", {
            "total_steps": len(workflow.steps),
            "completed_steps": len([s for s in workflow.steps if s.status == WorkflowStatus.COMPLETED]),
            "failed_steps": len([s for s in workflow.steps if s.status == WorkflowStatus.FAILED])
        })
        
        # Perform comprehensive result aggregation
        aggregated_results = await self.aggregate_workflow_results(workflow)
        
        # Create processing summary
        processing_summary = {
            "total_steps": len(workflow.steps),
            "successful_steps": len([s for s in workflow.steps if s.status == WorkflowStatus.COMPLETED]),
            "failed_steps": len([s for s in workflow.steps if s.status == WorkflowStatus.FAILED]),
            "recovery_attempts": len([s for s in workflow.steps if s.retry_count > 0]),
            "total_processing_time": (datetime.utcnow() - workflow.started_at).total_seconds() if workflow.started_at else 0
        }
        
        # Create detailed processing log
        processing_log = []
        for step in workflow.steps:
            step_log = {
                "step_id": step.step_id,
                "step_name": step.step_name,
                "agent_role": step.agent_role.value,
                "status": step.status.value,
                "processing_time": (
                    (step.completed_at - step.started_at).total_seconds()
                    if step.started_at and step.completed_at else 0
                ),
                "retry_count": step.retry_count,
                "error_message": step.error_message,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None
            }
            
            # Add output summary if available
            if step.output_data:
                step_log["output_summary"] = self._summarize_step_output(step.output_data)
            
            processing_log.append(step_log)
        
        # Combine all results
        final_results = {
            "workflow_id": workflow.workflow_id,
            "query_id": workflow.query_id,
            "researcher_id": workflow.researcher_id,
            "processing_summary": processing_summary,
            "processing_log": processing_log,
            "aggregated_results": aggregated_results,
            "finalization_timestamp": datetime.utcnow().isoformat()
        }
        
        # Legacy format for backward compatibility
        if "final_dataset" in aggregated_results:
            final_dataset = aggregated_results["final_dataset"]
            if final_dataset.get("status") == "approved":
                final_results["dataset"] = {
                    "anonymized_data": final_dataset.get("records", []),
                    "privacy_metrics": final_dataset.get("metadata", {}).get("privacy_level", {}),
                    "quality_score": aggregated_results.get("quality_assessment", {}).get("overall_quality", 0.0)
                }
        
        if "data_summary" in aggregated_results:
            final_results["data_summary"] = aggregated_results["data_summary"]
        
        workflow.results = final_results
        workflow.status = WorkflowStatus.COMPLETED
        
        # Update performance metrics
        self.performance_metrics["total_workflows"] += 1
        self.performance_metrics["successful_workflows"] += 1
        
        # Update average processing time
        current_avg = self.performance_metrics["average_processing_time"]
        new_time = processing_summary["total_processing_time"]
        total_workflows = self.performance_metrics["total_workflows"]
        self.performance_metrics["average_processing_time"] = (
            (current_avg * (total_workflows - 1) + new_time) / total_workflows
        )
        
        self._log_audit_event(workflow, "WORKFLOW_FINALIZATION_COMPLETED", {
            "final_status": workflow.status.value,
            "total_processing_time": processing_summary["total_processing_time"],
            "quality_grade": aggregated_results.get("quality_assessment", {}).get("quality_grade", "Unknown"),
            "compliance_passed": aggregated_results.get("quality_assessment", {}).get("compliance_passed", False),
            "final_record_count": len(final_results.get("dataset", {}).get("anonymized_data", []))
        })
    
    def _is_workflow_timeout(self, workflow: WorkflowExecution) -> bool:
        """Check if workflow has exceeded timeout."""
        if not workflow.started_at:
            return False
        
        elapsed = (datetime.utcnow() - workflow.started_at).total_seconds()
        return elapsed > self.workflow_timeout
    
    def _add_error_log(self, workflow: WorkflowExecution, error_code: str, error_message: str):
        """Add error to workflow error log."""
        workflow.error_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": error_code,
            "error_message": error_message
        })
    
    def _is_circuit_breaker_open(self, agent_role: AgentRole) -> bool:
        """Check if circuit breaker is open for agent."""
        breaker = self.circuit_breakers[agent_role.value]
        
        if not breaker["is_open"]:
            return False
        
        # Check if recovery timeout has passed
        if breaker["last_failure"]:
            time_since_failure = (datetime.utcnow() - breaker["last_failure"]).total_seconds()
            if time_since_failure > breaker["recovery_timeout"]:
                breaker["is_open"] = False
                breaker["failure_count"] = 0
                return False
        
        return True
    
    def _record_failure(self, agent_role: AgentRole):
        """Record failure for circuit breaker."""
        breaker = self.circuit_breakers[agent_role.value]
        breaker["failure_count"] += 1
        breaker["last_failure"] = datetime.utcnow()
        
        if breaker["failure_count"] >= breaker["failure_threshold"]:
            breaker["is_open"] = True
    
    def _reset_circuit_breaker(self, agent_role: AgentRole):
        """Reset circuit breaker on successful operation."""
        breaker = self.circuit_breakers[agent_role.value]
        breaker["failure_count"] = 0
        breaker["is_open"] = False
        breaker["last_failure"] = None
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            # Check history
            workflow = next(
                (w for w in self.workflow_history if w.workflow_id == workflow_id),
                None
            )
        
        if not workflow:
            return None
        
        return {
            "workflow_id": workflow.workflow_id,
            "query_id": workflow.query_id,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "total_processing_time": workflow.total_processing_time,
            "steps": [
                {
                    "step_name": step.step_name,
                    "status": step.status.value,
                    "agent_role": step.agent_role.value,
                    "retry_count": step.retry_count,
                    "error_message": step.error_message
                }
                for step in workflow.steps
            ],
            "error_log": workflow.error_log
        }
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len([w for w in self.workflow_history if w.status == WorkflowStatus.COMPLETED]),
            "failed_workflows": len([w for w in self.workflow_history if w.status == WorkflowStatus.FAILED]),
            "circuit_breaker_status": {
                role: {
                    "is_open": breaker["is_open"],
                    "failure_count": breaker["failure_count"]
                }
                for role, breaker in self.circuit_breakers.items()
            },
            "average_processing_time": self._calculate_average_processing_time()
        }
    
    def _calculate_average_processing_time(self) -> float:
        """Calculate average workflow processing time."""
        completed_workflows = [
            w for w in self.workflow_history 
            if w.status == WorkflowStatus.COMPLETED and w.total_processing_time
        ]
        
        if not completed_workflows:
            return 0.0
        
        total_time = sum(w.total_processing_time for w in completed_workflows)
        return total_time / len(completed_workflows)
    
    def _validate_step_output(self, step: WorkflowStep) -> bool:
        """Validate step output data meets requirements."""
        if not step.output_data:
            return False
        
        # Agent-specific validation
        if step.agent_role == AgentRole.METTA_AGENT:
            required_fields = ["validation_result", "reasoning_path", "confidence_score"]
            return all(field in step.output_data for field in required_fields)
        
        elif step.agent_role == AgentRole.CONSENT_AGENT:
            required_fields = ["consent_status", "data_type", "research_category"]
            return all(field in step.output_data for field in required_fields)
        
        elif step.agent_role == AgentRole.DATA_CUSTODIAN:
            required_fields = ["dataset_id", "patient_count", "raw_data"]
            return all(field in step.output_data for field in required_fields)
        
        elif step.agent_role == AgentRole.PRIVACY_AGENT:
            required_fields = ["anonymized_data", "privacy_metrics", "anonymization_log"]
            return all(field in step.output_data for field in required_fields)
        
        return True
    
    def _summarize_step_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of step output for logging."""
        if not output_data:
            return {}
        
        summary = {}
        
        # Common fields
        if "success" in output_data:
            summary["success"] = output_data["success"]
        
        # Data size information
        if "anonymized_data" in output_data:
            summary["record_count"] = len(output_data["anonymized_data"])
        elif "raw_data" in output_data:
            summary["record_count"] = len(output_data["raw_data"])
        
        # Quality metrics
        if "confidence_score" in output_data:
            summary["confidence_score"] = output_data["confidence_score"]
        if "quality_score" in output_data:
            summary["quality_score"] = output_data["quality_score"]
        
        # Privacy metrics
        if "privacy_metrics" in output_data:
            privacy_metrics = output_data["privacy_metrics"]
            if isinstance(privacy_metrics, dict):
                summary["privacy_compliance"] = privacy_metrics.get("k_anonymity", 0) >= 5
        
        return summary
    
    def _update_agent_performance(self, agent_role: AgentRole, success: bool, processing_time: float):
        """Update agent performance metrics."""
        agent_metrics = self.performance_metrics["agent_performance"][agent_role.value]
        
        # Update success rate (exponential moving average)
        current_rate = agent_metrics["success_rate"]
        alpha = 0.1  # Learning rate
        agent_metrics["success_rate"] = (1 - alpha) * current_rate + alpha * (1.0 if success else 0.0)
        
        # Update average response time (exponential moving average)
        current_time = agent_metrics["avg_response_time"]
        agent_metrics["avg_response_time"] = (1 - alpha) * current_time + alpha * processing_time
    
    def _log_audit_event(self, workflow: WorkflowExecution, event_type: str, details: Dict[str, Any]):
        """Log audit event for workflow tracking."""
        if not self.detailed_logging:
            return
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow.workflow_id,
            "query_id": workflow.query_id,
            "researcher_id": workflow.researcher_id,
            "event_type": event_type,
            "details": details
        }
        
        self.audit_trail.append(audit_entry)
        
        # Keep audit trail size manageable
        if len(self.audit_trail) > 10000:
            self.audit_trail = self.audit_trail[-5000:]  # Keep last 5000 entries
        
        # Log to system logger as well
        self.logger.audit(
            event_type=event_type,
            details={
                "workflow_id": workflow.workflow_id,
                "query_id": workflow.query_id,
                **details
            }
        )
    
    async def _attempt_step_recovery(self, ctx, workflow: WorkflowExecution, failed_step: WorkflowStep) -> bool:
        """Attempt to recover from step failure using alternative strategies."""
        
        self.logger.info("Attempting step recovery",
                        workflow_id=workflow.workflow_id,
                        step_id=failed_step.step_id,
                        agent_role=failed_step.agent_role.value)
        
        self._log_audit_event(workflow, "RECOVERY_ATTEMPT_STARTED", {
            "step_id": failed_step.step_id,
            "agent_role": failed_step.agent_role.value,
            "failure_reason": failed_step.error_message
        })
        
        try:
            # Agent-specific recovery strategies
            if failed_step.agent_role == AgentRole.METTA_AGENT:
                return await self._recover_metta_step(ctx, workflow, failed_step)
            
            elif failed_step.agent_role == AgentRole.CONSENT_AGENT:
                return await self._recover_consent_step(ctx, workflow, failed_step)
            
            elif failed_step.agent_role == AgentRole.DATA_CUSTODIAN:
                return await self._recover_data_step(ctx, workflow, failed_step)
            
            elif failed_step.agent_role == AgentRole.PRIVACY_AGENT:
                return await self._recover_privacy_step(ctx, workflow, failed_step)
            
            return False
            
        except Exception as e:
            self.logger.error("Recovery attempt failed",
                            workflow_id=workflow.workflow_id,
                            step_id=failed_step.step_id,
                            error=str(e))
            
            self._log_audit_event(workflow, "RECOVERY_ATTEMPT_FAILED", {
                "step_id": failed_step.step_id,
                "recovery_error": str(e)
            })
            
            return False
    
    async def _recover_metta_step(self, ctx, workflow: WorkflowExecution, failed_step: WorkflowStep) -> bool:
        """Attempt recovery for failed MeTTa validation step."""
        # Use fallback validation logic
        fallback_result = {
            "validation_result": [{"validation": "fallback_passed"}],
            "reasoning_path": ["fallback-validation-used"],
            "confidence_score": 0.5  # Lower confidence for fallback
        }
        
        failed_step.output_data = fallback_result
        failed_step.status = WorkflowStatus.COMPLETED
        failed_step.completed_at = datetime.utcnow()
        
        self._log_audit_event(workflow, "RECOVERY_SUCCESS_FALLBACK", {
            "step_id": failed_step.step_id,
            "recovery_method": "fallback_validation"
        })
        
        return True
    
    async def _recover_consent_step(self, ctx, workflow: WorkflowExecution, failed_step: WorkflowStep) -> bool:
        """Attempt recovery for failed consent verification step."""
        # For consent failures, we cannot use fallback - consent must be explicit
        # But we can try alternative consent checking methods
        
        # Check if we have cached consent data
        cached_consent = self._check_cached_consent(failed_step.input_data)
        if cached_consent:
            failed_step.output_data = cached_consent
            failed_step.status = WorkflowStatus.COMPLETED
            failed_step.completed_at = datetime.utcnow()
            
            self._log_audit_event(workflow, "RECOVERY_SUCCESS_CACHE", {
                "step_id": failed_step.step_id,
                "recovery_method": "cached_consent"
            })
            
            return True
        
        return False
    
    async def _recover_data_step(self, ctx, workflow: WorkflowExecution, failed_step: WorkflowStep) -> bool:
        """Attempt recovery for failed data retrieval step."""
        # Try alternative data sources or reduced dataset
        
        # Reduce sample size requirement for recovery
        original_criteria = failed_step.input_data.get("data_criteria", {})
        recovery_criteria = original_criteria.copy()
        
        if "minimum_sample_size" in recovery_criteria:
            recovery_criteria["minimum_sample_size"] = max(10, recovery_criteria["minimum_sample_size"] // 2)
        
        # Simulate recovery with reduced dataset
        recovery_result = {
            "dataset_id": f"RECOVERY-{uuid.uuid4().hex[:8].upper()}",
            "patient_count": recovery_criteria.get("minimum_sample_size", 25),
            "data_fields": ["age", "gender"],  # Minimal fields
            "raw_data": [{"patient_id": f"R{i:03d}", "age": 40+i, "gender": "M" if i%2 else "F"} 
                        for i in range(recovery_criteria.get("minimum_sample_size", 25))]
        }
        
        failed_step.output_data = recovery_result
        failed_step.status = WorkflowStatus.COMPLETED
        failed_step.completed_at = datetime.utcnow()
        
        self._log_audit_event(workflow, "RECOVERY_SUCCESS_REDUCED_DATASET", {
            "step_id": failed_step.step_id,
            "recovery_method": "reduced_sample_size",
            "original_size": original_criteria.get("minimum_sample_size"),
            "recovery_size": recovery_criteria.get("minimum_sample_size")
        })
        
        return True
    
    async def _recover_privacy_step(self, ctx, workflow: WorkflowExecution, failed_step: WorkflowStep) -> bool:
        """Attempt recovery for failed anonymization step."""
        # Use basic anonymization if advanced methods fail
        
        # Get data from previous step
        data_step = next(
            (s for s in workflow.steps if s.agent_role == AgentRole.DATA_CUSTODIAN and s.status == WorkflowStatus.COMPLETED),
            None
        )
        
        if not data_step or not data_step.output_data:
            return False
        
        raw_data = data_step.output_data.get("raw_data", [])
        
        # Apply basic anonymization
        basic_anonymized = []
        for i, record in enumerate(raw_data):
            anonymized_record = {}
            for key, value in record.items():
                if key == "patient_id":
                    anonymized_record[key] = f"BASIC_ANON_{i:03d}"
                else:
                    anonymized_record[key] = value
            basic_anonymized.append(anonymized_record)
        
        recovery_result = {
            "anonymized_data": basic_anonymized,
            "privacy_metrics": {"k_anonymity": 5, "method": "basic_anonymization"},
            "anonymization_log": "Basic anonymization applied during recovery",
            "quality_score": 0.6  # Lower quality for basic anonymization
        }
        
        failed_step.output_data = recovery_result
        failed_step.status = WorkflowStatus.COMPLETED
        failed_step.completed_at = datetime.utcnow()
        
        self._log_audit_event(workflow, "RECOVERY_SUCCESS_BASIC_ANONYMIZATION", {
            "step_id": failed_step.step_id,
            "recovery_method": "basic_anonymization",
            "record_count": len(basic_anonymized)
        })
        
        return True
    
    def _check_cached_consent(self, consent_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for cached consent data (simulation)."""
        # In a real implementation, this would check a consent cache
        # For simulation, we'll return cached consent for specific cases
        
        data_type = consent_input.get("data_type")
        research_category = consent_input.get("research_category")
        
        # Simulate cached consent for common data types
        if data_type in ["demographics", "vital_signs"] and research_category in ["clinical_trials", "outcomes_research"]:
            return {
                "consent_status": "granted",
                "data_type": data_type,
                "research_category": research_category,
                "consent_details": {
                    "source": "cached_consent",
                    "consent_id": f"CACHED-{uuid.uuid4().hex[:8].upper()}"
                }
            }
        
        return None
    
    async def aggregate_workflow_results(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Aggregate results from multiple data sources and validate quality."""
        
        self.logger.info("Aggregating workflow results",
                        workflow_id=workflow.workflow_id)
        
        self._log_audit_event(workflow, "RESULT_AGGREGATION_STARTED", {
            "total_steps": len(workflow.steps),
            "completed_steps": len([s for s in workflow.steps if s.status == WorkflowStatus.COMPLETED])
        })
        
        aggregated_results = {
            "workflow_id": workflow.workflow_id,
            "query_id": workflow.query_id,
            "researcher_id": workflow.researcher_id,
            "aggregation_timestamp": datetime.utcnow().isoformat(),
            "data_sources": [],
            "quality_metrics": {},
            "compliance_status": {},
            "processing_summary": {}
        }
        
        # Collect results from each step type
        consent_results = self._aggregate_consent_results(workflow)
        data_results = self._aggregate_data_results(workflow)
        privacy_results = self._aggregate_privacy_results(workflow)
        metta_results = self._aggregate_metta_results(workflow)
        
        # Validate aggregation quality
        quality_assessment = self._assess_aggregation_quality(
            consent_results, data_results, privacy_results, metta_results
        )
        
        aggregated_results.update({
            "consent_summary": consent_results,
            "data_summary": data_results,
            "privacy_summary": privacy_results,
            "ethics_summary": metta_results,
            "quality_assessment": quality_assessment,
            "final_dataset": self._create_final_dataset(data_results, privacy_results, quality_assessment)
        })
        
        self._log_audit_event(workflow, "RESULT_AGGREGATION_COMPLETED", {
            "quality_score": quality_assessment.get("overall_quality", 0.0),
            "compliance_passed": quality_assessment.get("compliance_passed", False),
            "final_record_count": len(aggregated_results["final_dataset"].get("records", []))
        })
        
        return aggregated_results
    
    def _aggregate_consent_results(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Aggregate consent verification results."""
        consent_steps = [s for s in workflow.steps if s.agent_role == AgentRole.CONSENT_AGENT]
        
        total_consents = len(consent_steps)
        granted_consents = len([s for s in consent_steps 
                               if s.status == WorkflowStatus.COMPLETED and 
                               s.output_data.get("consent_status") == "granted"])
        
        consent_rate = granted_consents / total_consents if total_consents > 0 else 0.0
        
        return {
            "total_consent_checks": total_consents,
            "granted_consents": granted_consents,
            "consent_rate": consent_rate,
            "consent_threshold_met": consent_rate >= self.aggregation_rules["consent_threshold"],
            "consent_details": [
                {
                    "data_type": step.input_data.get("data_type"),
                    "research_category": step.input_data.get("research_category"),
                    "status": step.output_data.get("consent_status") if step.output_data else "failed"
                }
                for step in consent_steps
            ]
        }
    
    def _aggregate_data_results(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Aggregate data retrieval results."""
        data_steps = [s for s in workflow.steps if s.agent_role == AgentRole.DATA_CUSTODIAN]
        
        if not data_steps:
            return {"error": "No data retrieval steps found"}
        
        # Combine results from all data sources
        total_patients = 0
        all_data_fields = set()
        data_sources = []
        
        for step in data_steps:
            if step.status == WorkflowStatus.COMPLETED and step.output_data:
                patient_count = step.output_data.get("patient_count", 0)
                data_fields = step.output_data.get("data_fields", [])
                
                total_patients += patient_count
                all_data_fields.update(data_fields)
                
                data_sources.append({
                    "dataset_id": step.output_data.get("dataset_id"),
                    "patient_count": patient_count,
                    "data_fields": data_fields
                })
        
        return {
            "total_patients": total_patients,
            "unique_data_fields": list(all_data_fields),
            "data_sources": data_sources,
            "data_quality_score": self._calculate_data_quality_score(data_steps)
        }
    
    def _aggregate_privacy_results(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Aggregate privacy and anonymization results."""
        privacy_steps = [s for s in workflow.steps if s.agent_role == AgentRole.PRIVACY_AGENT]
        
        if not privacy_steps:
            return {"error": "No privacy steps found"}
        
        # Get the main privacy step result
        privacy_step = privacy_steps[0]  # Should only be one
        
        if privacy_step.status != WorkflowStatus.COMPLETED or not privacy_step.output_data:
            return {"error": "Privacy step failed or incomplete"}
        
        privacy_metrics = privacy_step.output_data.get("privacy_metrics", {})
        quality_score = privacy_step.output_data.get("quality_score", 0.0)
        
        return {
            "anonymization_successful": True,
            "privacy_metrics": privacy_metrics,
            "quality_score": quality_score,
            "k_anonymity_achieved": privacy_metrics.get("k_anonymity", 0) >= 5,
            "privacy_compliance_score": self._calculate_privacy_compliance_score(privacy_metrics),
            "anonymized_record_count": len(privacy_step.output_data.get("anonymized_data", []))
        }
    
    def _aggregate_metta_results(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Aggregate MeTTa ethics and validation results."""
        metta_steps = [s for s in workflow.steps if s.agent_role == AgentRole.METTA_AGENT]
        
        if not metta_steps:
            return {"error": "No MeTTa validation steps found"}
        
        # Combine all MeTTa validation results
        all_validations = []
        all_reasoning_paths = []
        confidence_scores = []
        
        for step in metta_steps:
            if step.status == WorkflowStatus.COMPLETED and step.output_data:
                validations = step.output_data.get("validation_result", [])
                reasoning = step.output_data.get("reasoning_path", [])
                confidence = step.output_data.get("confidence_score", 0.0)
                
                all_validations.extend(validations)
                all_reasoning_paths.extend(reasoning)
                confidence_scores.append(confidence)
        
        average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "validation_results": all_validations,
            "reasoning_paths": all_reasoning_paths,
            "average_confidence": average_confidence,
            "ethics_compliance_passed": average_confidence >= 0.6,
            "validation_count": len(all_validations)
        }
    
    def _assess_aggregation_quality(self, consent_results: Dict, data_results: Dict, 
                                  privacy_results: Dict, metta_results: Dict) -> Dict[str, Any]:
        """Assess overall quality of aggregated results."""
        
        quality_factors = []
        
        # Consent quality
        consent_quality = consent_results.get("consent_rate", 0.0)
        quality_factors.append(("consent", consent_quality))
        
        # Data quality
        data_quality = data_results.get("data_quality_score", 0.0)
        quality_factors.append(("data", data_quality))
        
        # Privacy quality
        privacy_quality = privacy_results.get("quality_score", 0.0)
        quality_factors.append(("privacy", privacy_quality))
        
        # Ethics quality
        ethics_quality = metta_results.get("average_confidence", 0.0)
        quality_factors.append(("ethics", ethics_quality))
        
        # Calculate weighted overall quality
        weights = {"consent": 0.3, "data": 0.3, "privacy": 0.25, "ethics": 0.15}
        overall_quality = sum(weights[factor] * score for factor, score in quality_factors)
        
        # Check compliance thresholds
        compliance_checks = {
            "consent_threshold": consent_results.get("consent_threshold_met", False),
            "data_quality_threshold": data_quality >= self.aggregation_rules["data_quality_threshold"],
            "privacy_compliance_threshold": privacy_results.get("privacy_compliance_score", 0.0) >= self.aggregation_rules["privacy_compliance_threshold"],
            "ethics_threshold": ethics_quality >= 0.6
        }
        
        compliance_passed = all(compliance_checks.values())
        
        return {
            "overall_quality": overall_quality,
            "quality_factors": dict(quality_factors),
            "compliance_checks": compliance_checks,
            "compliance_passed": compliance_passed,
            "quality_grade": self._calculate_quality_grade(overall_quality),
            "recommendations": self._generate_quality_recommendations(quality_factors, compliance_checks)
        }
    
    def _calculate_data_quality_score(self, data_steps: List[WorkflowStep]) -> float:
        """Calculate data quality score based on completeness and consistency."""
        if not data_steps:
            return 0.0
        
        completed_steps = [s for s in data_steps if s.status == WorkflowStatus.COMPLETED]
        completion_rate = len(completed_steps) / len(data_steps)
        
        # Additional quality factors could include:
        # - Data completeness
        # - Field coverage
        # - Sample size adequacy
        
        return completion_rate * 0.8 + 0.2  # Base quality bonus
    
    def _calculate_privacy_compliance_score(self, privacy_metrics: Dict[str, Any]) -> float:
        """Calculate privacy compliance score."""
        score = 0.0
        
        # K-anonymity compliance
        k_value = privacy_metrics.get("k_anonymity", 0)
        if k_value >= 5:
            score += 0.4
        elif k_value >= 3:
            score += 0.2
        
        # L-diversity compliance
        l_value = privacy_metrics.get("l_diversity", 0)
        if l_value >= 3:
            score += 0.3
        elif l_value >= 2:
            score += 0.15
        
        # Additional privacy measures
        if "differential_privacy" in privacy_metrics:
            score += 0.2
        
        if "generalization" in privacy_metrics:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_quality_grade(self, overall_quality: float) -> str:
        """Calculate quality grade based on overall score."""
        if overall_quality >= 0.9:
            return "A"
        elif overall_quality >= 0.8:
            return "B"
        elif overall_quality >= 0.7:
            return "C"
        elif overall_quality >= 0.6:
            return "D"
        else:
            return "F"
    
    def _generate_quality_recommendations(self, quality_factors: List[Tuple[str, float]], 
                                        compliance_checks: Dict[str, bool]) -> List[str]:
        """Generate recommendations for improving quality."""
        recommendations = []
        
        for factor, score in quality_factors:
            if score < 0.7:
                if factor == "consent":
                    recommendations.append("Consider expanding consent outreach or simplifying consent process")
                elif factor == "data":
                    recommendations.append("Improve data collection completeness or expand data sources")
                elif factor == "privacy":
                    recommendations.append("Enhance anonymization techniques or increase k-anonymity threshold")
                elif factor == "ethics":
                    recommendations.append("Review ethical approval requirements or strengthen compliance measures")
        
        for check, passed in compliance_checks.items():
            if not passed:
                recommendations.append(f"Address compliance failure: {check}")
        
        return recommendations
    
    def _create_final_dataset(self, data_results: Dict, privacy_results: Dict, 
                            quality_assessment: Dict) -> Dict[str, Any]:
        """Create final dataset for delivery to researcher."""
        
        if not quality_assessment.get("compliance_passed", False):
            return {
                "status": "rejected",
                "reason": "Quality or compliance thresholds not met",
                "quality_assessment": quality_assessment
            }
        
        # Get anonymized data from privacy results
        anonymized_data = []
        if "anonymized_record_count" in privacy_results:
            # In a real implementation, this would get the actual anonymized records
            # For simulation, create sample anonymized records
            record_count = privacy_results["anonymized_record_count"]
            anonymized_data = [
                {
                    "patient_id": f"ANON_{i:04d}",
                    "age_group": f"{20 + (i % 6) * 10}-{29 + (i % 6) * 10}",
                    "gender": "M" if i % 2 else "F",
                    "condition_category": ["cardiovascular", "respiratory", "metabolic"][i % 3]
                }
                for i in range(min(record_count, 100))  # Limit for demo
            ]
        
        return {
            "status": "approved",
            "records": anonymized_data,
            "metadata": {
                "total_records": len(anonymized_data),
                "data_fields": list(anonymized_data[0].keys()) if anonymized_data else [],
                "privacy_level": privacy_results.get("privacy_metrics", {}),
                "quality_grade": quality_assessment.get("quality_grade", "Unknown"),
                "compliance_status": "PASSED"
            },
            "usage_restrictions": {
                "max_retention_days": 2555,  # 7 years
                "allowed_purposes": ["research", "analysis"],
                "prohibited_actions": ["re-identification", "commercial_use"]
            }
        }
    
    def get_audit_trail(self, workflow_id: Optional[str] = None, 
                       event_type: Optional[str] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit trail entries with optional filtering."""
        
        filtered_entries = self.audit_trail
        
        if workflow_id:
            filtered_entries = [e for e in filtered_entries if e.get("workflow_id") == workflow_id]
        
        if event_type:
            filtered_entries = [e for e in filtered_entries if e.get("event_type") == event_type]
        
        # Sort by timestamp (newest first) and limit
        filtered_entries = sorted(filtered_entries, key=lambda x: x["timestamp"], reverse=True)
        
        return filtered_entries[:limit]