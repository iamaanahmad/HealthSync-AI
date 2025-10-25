"""
Research Query Agent for HealthSync system.
Processes research queries and orchestrates multi-agent workflows.
"""

from uagents import Context
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os
import uuid

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.base_agent import HealthSyncBaseAgent
from shared.protocols.agent_messages import (
    MessageTypes, ResearchQuery, QueryResult, AgentMessage, 
    ErrorCodes, ErrorResponse
)
from shared.protocols.chat_protocol import ChatMessage, ChatResponse
from shared.utils.error_handling import with_error_handling

from .query_processor import QueryProcessor, QueryValidator, ParsedQuery
from .workflow_orchestrator import WorkflowOrchestrator, WorkflowStatus


class ResearchQueryAgent(HealthSyncBaseAgent):
    """Agent responsible for processing research queries and orchestrating workflows."""
    
    def __init__(self, port: int = 8005, agent_addresses: Optional[Dict[str, str]] = None):
        super().__init__(
            name="Research Query Agent",
            port=port,
            endpoint=f"http://localhost:{port}/submit"
        )
        
        # Initialize query processor and orchestrator
        self.query_processor = QueryProcessor()
        self.workflow_orchestrator = WorkflowOrchestrator(
            agent_addresses or self._get_default_agent_addresses()
        )
        
        # Query tracking
        self.active_queries: Dict[str, Dict[str, Any]] = {}
        self.query_history: List[Dict[str, Any]] = []
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_processing_time": 0.0,
            "queries_by_type": {},
            "queries_by_researcher": {}
        }
        
        # Register message handlers
        self._register_handlers()
        
        self.logger.info("Research Query Agent initialized")
    
    def _get_default_agent_addresses(self) -> Dict[str, str]:
        """Get default agent addresses for workflow orchestration."""
        return {
            "patient_consent_agent": "agent1qg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg",
            "data_custodian_agent": "agent1qh4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc",
            "privacy_agent": "agent1qi5def5def5def5def5def5def5def5def5def5def5def5def5def",
            "metta_integration_agent": "agent1qj6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi"
        }
    
    def _register_handlers(self):
        """Register message handlers for research query operations."""
        
        self.register_message_handler(
            MessageTypes.RESEARCH_QUERY,
            self._handle_research_query
        )
        
        self.register_message_handler(
            MessageTypes.QUERY_STATUS,
            self._handle_query_status
        )
        
        self.register_message_handler(
            MessageTypes.HEALTH_CHECK,
            self._handle_health_check
        )
        
        # Additional handlers
        self.register_message_handler(
            "query_cancel",
            self._handle_query_cancellation
        )
        
        self.register_message_handler(
            "query_history",
            self._handle_query_history
        )
    
    @with_error_handling("research_query_agent")
    async def _handle_research_query(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle incoming research query requests with validation and orchestration."""
        try:
            # Parse and validate query
            query_data = msg.payload
            parsed_query, validation_result = self.query_processor.parse_research_query(query_data)
            
            if not validation_result.is_valid:
                self.logger.warning("Query validation failed",
                                  query_id=query_data.get("query_id"),
                                  errors=validation_result.errors)
                return {
                    "status": "validation_failed",
                    "query_id": query_data.get("query_id"),
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                }
            
            # Validate ethical compliance
            ethical_validation = self.query_processor.validate_ethical_compliance(parsed_query)
            
            if not ethical_validation.is_valid or ethical_validation.ethical_score < 0.6:
                self.logger.warning("Ethical validation failed",
                                  query_id=parsed_query.query_id,
                                  ethical_score=ethical_validation.ethical_score)
                return {
                    "status": "ethical_validation_failed",
                    "query_id": parsed_query.query_id,
                    "ethical_score": ethical_validation.ethical_score,
                    "errors": ethical_validation.errors,
                    "warnings": ethical_validation.warnings
                }
            
            # Update statistics
            self.stats["total_queries"] += 1
            query_type = parsed_query.query_type.value
            self.stats["queries_by_type"][query_type] = self.stats["queries_by_type"].get(query_type, 0) + 1
            researcher_id = parsed_query.researcher_id
            self.stats["queries_by_researcher"][researcher_id] = self.stats["queries_by_researcher"].get(researcher_id, 0) + 1
            
            # Track query
            query_tracking = {
                "query_id": parsed_query.query_id,
                "researcher_id": parsed_query.researcher_id,
                "status": "processing",
                "created_at": datetime.utcnow(),
                "validation_result": validation_result,
                "ethical_validation": ethical_validation,
                "parsed_query": parsed_query
            }
            
            self.active_queries[parsed_query.query_id] = query_tracking
            
            # Log audit trail
            self.logger.audit(
                event_type="research_query_received",
                details={
                    "query_id": parsed_query.query_id,
                    "researcher_id": parsed_query.researcher_id,
                    "query_type": parsed_query.query_type.value,
                    "data_types": parsed_query.required_data_types,
                    "research_categories": parsed_query.research_categories,
                    "ethical_score": ethical_validation.ethical_score,
                    "complexity_score": validation_result.complexity_score
                }
            )
            
            # Execute workflow asynchronously
            workflow_result = await self.workflow_orchestrator.execute_research_workflow(
                ctx, query_data, parsed_query
            )
            
            # Update query tracking
            query_tracking["workflow_id"] = workflow_result.workflow_id
            query_tracking["workflow_result"] = workflow_result
            
            if workflow_result.status == WorkflowStatus.COMPLETED:
                query_tracking["status"] = "completed"
                self.stats["successful_queries"] += 1
                
                # Create query result
                result = QueryResult(
                    query_id=parsed_query.query_id,
                    dataset_summary=workflow_result.results.get("data_summary", {}),
                    anonymized_data=workflow_result.results.get("dataset", {}).get("anonymized_data", []),
                    processing_log=workflow_result.results.get("processing_log", []),
                    privacy_metrics=workflow_result.results.get("dataset", {}).get("privacy_metrics", {}),
                    completion_status="completed"
                )
                
                query_tracking["result"] = result
                
                return {
                    "status": "completed",
                    "query_id": parsed_query.query_id,
                    "workflow_id": workflow_result.workflow_id,
                    "result": result.dict(),
                    "processing_time": workflow_result.total_processing_time
                }
            
            else:
                query_tracking["status"] = "failed"
                self.stats["failed_queries"] += 1
                
                return {
                    "status": "failed",
                    "query_id": parsed_query.query_id,
                    "workflow_id": workflow_result.workflow_id,
                    "error_log": workflow_result.error_log,
                    "processing_time": workflow_result.total_processing_time
                }
            
        except Exception as e:
            self.logger.error("Failed to process research query",
                            error=str(e),
                            query_id=msg.payload.get("query_id"))
            
            self.stats["failed_queries"] += 1
            
            return {
                "status": "error",
                "query_id": msg.payload.get("query_id"),
                "message": f"Failed to process research query: {str(e)}"
            }
        
        finally:
            # Move completed/failed queries to history
            query_id = msg.payload.get("query_id")
            if query_id in self.active_queries:
                query_tracking = self.active_queries[query_id]
                if query_tracking["status"] in ["completed", "failed"]:
                    self.query_history.append(query_tracking)
                    del self.active_queries[query_id]
    
    async def _handle_query_status(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle query status requests."""
        try:
            query_id = msg.payload.get("query_id")
            
            if not query_id:
                return {
                    "status": "error",
                    "message": "query_id is required"
                }
            
            # Check active queries
            if query_id in self.active_queries:
                query_tracking = self.active_queries[query_id]
                
                # Get workflow status if available
                workflow_status = None
                if "workflow_id" in query_tracking:
                    workflow_status = self.workflow_orchestrator.get_workflow_status(
                        query_tracking["workflow_id"]
                    )
                
                return {
                    "status": "success",
                    "query_id": query_id,
                    "query_status": query_tracking["status"],
                    "created_at": query_tracking["created_at"].isoformat(),
                    "researcher_id": query_tracking["researcher_id"],
                    "workflow_status": workflow_status
                }
            
            # Check query history
            historical_query = next(
                (q for q in self.query_history if q["query_id"] == query_id),
                None
            )
            
            if historical_query:
                return {
                    "status": "success",
                    "query_id": query_id,
                    "query_status": historical_query["status"],
                    "created_at": historical_query["created_at"].isoformat(),
                    "researcher_id": historical_query["researcher_id"],
                    "result": historical_query.get("result", {}).dict() if historical_query.get("result") else None
                }
            
            return {
                "status": "not_found",
                "query_id": query_id,
                "message": "Query not found"
            }
            
        except Exception as e:
            self.logger.error("Failed to get query status", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to get query status: {str(e)}"
            }
    
    async def _handle_query_cancellation(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle query cancellation requests."""
        try:
            query_id = msg.payload.get("query_id")
            requester_id = msg.payload.get("requester_id")
            
            if query_id not in self.active_queries:
                return {
                    "status": "not_found",
                    "query_id": query_id,
                    "message": "Query not found or already completed"
                }
            
            query_tracking = self.active_queries[query_id]
            
            # Verify requester authorization
            if query_tracking["researcher_id"] != requester_id:
                return {
                    "status": "unauthorized",
                    "query_id": query_id,
                    "message": "Only the original researcher can cancel this query"
                }
            
            # Cancel the query
            query_tracking["status"] = "cancelled"
            query_tracking["cancelled_at"] = datetime.utcnow()
            
            # Move to history
            self.query_history.append(query_tracking)
            del self.active_queries[query_id]
            
            self.logger.audit(
                event_type="research_query_cancelled",
                details={
                    "query_id": query_id,
                    "researcher_id": requester_id,
                    "cancelled_at": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "status": "success",
                "query_id": query_id,
                "message": "Query cancelled successfully"
            }
            
        except Exception as e:
            self.logger.error("Failed to cancel query", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to cancel query: {str(e)}"
            }
    
    async def _handle_query_history(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle query history requests."""
        try:
            researcher_id = msg.payload.get("researcher_id")
            limit = msg.payload.get("limit", 50)
            
            if researcher_id:
                # Filter by researcher
                queries = [
                    q for q in self.query_history 
                    if q["researcher_id"] == researcher_id
                ]
            else:
                queries = self.query_history
            
            # Sort by creation date (newest first) and limit
            queries = sorted(queries, key=lambda x: x["created_at"], reverse=True)[:limit]
            
            # Format response
            query_summaries = []
            for query in queries:
                summary = {
                    "query_id": query["query_id"],
                    "researcher_id": query["researcher_id"],
                    "status": query["status"],
                    "created_at": query["created_at"].isoformat(),
                    "query_type": query["parsed_query"].query_type.value,
                    "study_title": query["parsed_query"].study_title
                }
                
                if "result" in query and query["result"]:
                    summary["patient_count"] = len(query["result"].anonymized_data)
                    summary["completion_status"] = query["result"].completion_status
                
                query_summaries.append(summary)
            
            return {
                "status": "success",
                "queries": query_summaries,
                "total_count": len(query_summaries)
            }
            
        except Exception as e:
            self.logger.error("Failed to get query history", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to get query history: {str(e)}"
            }
    
    async def _handle_health_check(self, ctx: Context, sender: str, msg: AgentMessage) -> Dict[str, Any]:
        """Handle health check requests."""
        orchestrator_stats = self.workflow_orchestrator.get_orchestrator_stats()
        
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "active_queries": len(self.active_queries),
            "query_statistics": self.stats,
            "orchestrator_statistics": orchestrator_stats,
            "last_heartbeat": self.last_heartbeat.isoformat()
        }


if __name__ == "__main__":
    # Example usage
    agent = ResearchQueryAgent(port=8005)
    agent.run()