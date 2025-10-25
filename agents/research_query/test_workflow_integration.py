"""
Integration tests for Research Query Agent workflow orchestration.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.research_query.workflow_orchestrator import (
    WorkflowOrchestrator, WorkflowStatus, AgentRole, 
    WorkflowExecution, WorkflowStep
)
from agents.research_query.query_processor import QueryProcessor, QueryType, DataSensitivity
from agents.research_query.agent import ResearchQueryAgent
from shared.protocols.agent_messages import AgentMessage, MessageTypes


class TestWorkflowOrchestrator(unittest.TestCase):
    """Test cases for WorkflowOrchestrator class."""
    
    def setUp(self):
        self.agent_addresses = {
            "patient_consent_agent": "agent1qg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg",
            "data_custodian_agent": "agent1qh4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc",
            "privacy_agent": "agent1qi5def5def5def5def5def5def5def5def5def5def5def5def5def",
            "metta_integration_agent": "agent1qj6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi"
        }
        self.orchestrator = WorkflowOrchestrator(self.agent_addresses)
        
        # Mock query processor and parsed query
        self.query_processor = QueryProcessor()
        self.sample_query_data = {
            "query_id": "test-workflow-123",
            "researcher_id": "HMS-12345",
            "study_title": "Integration Test Study",
            "study_description": "A comprehensive observational study to test workflow integration",
            "data_requirements": {
                "data_types": ["demographics", "vital_signs"],
                "research_categories": ["clinical_trials"],
                "minimum_sample_size": 50
            },
            "ethical_approval_id": "IRB-2024-123456",
            "inclusion_criteria": ["age >= 18"],
            "exclusion_criteria": ["pregnancy"],
            "privacy_requirements": {
                "anonymization_methods": ["k_anonymity"],
                "k_anonymity": 5
            }
        }
        
        self.parsed_query, _ = self.query_processor.parse_research_query(self.sample_query_data)
    
    def test_build_workflow_steps(self):
        """Test workflow step building."""
        steps = self.orchestrator._build_workflow_steps(self.parsed_query)
        
        # Should have steps for ethics validation, consent checks, data retrieval, and anonymization
        self.assertGreater(len(steps), 3)
        
        # Check for required step types
        step_agents = [step.agent_role for step in steps]
        self.assertIn(AgentRole.METTA_AGENT, step_agents)
        self.assertIn(AgentRole.CONSENT_AGENT, step_agents)
        self.assertIn(AgentRole.DATA_CUSTODIAN, step_agents)
        self.assertIn(AgentRole.PRIVACY_AGENT, step_agents)
        
        # Check step structure
        for step in steps:
            self.assertIsNotNone(step.step_id)
            self.assertIsNotNone(step.step_name)
            self.assertEqual(step.status, WorkflowStatus.PENDING)
            self.assertIsInstance(step.input_data, dict)
    
    async def test_execute_research_workflow_success(self):
        """Test successful workflow execution."""
        mock_ctx = Mock()
        
        # Mock successful responses for all agent communications
        with patch.object(self.orchestrator, '_send_and_wait') as mock_send:
            mock_send.return_value = {
                "success": True,
                "results": [{"validation": "passed"}],
                "reasoning_path": ["ethical-approval-valid"],
                "confidence_score": 0.95
            }
            
            workflow = await self.orchestrator.execute_research_workflow(
                mock_ctx, self.sample_query_data, self.parsed_query
            )
            
            self.assertEqual(workflow.status, WorkflowStatus.COMPLETED)
            self.assertIsNotNone(workflow.workflow_id)
            self.assertEqual(workflow.query_id, "test-workflow-123")
            self.assertEqual(workflow.researcher_id, "HMS-12345")
            self.assertIsNotNone(workflow.results)
            self.assertGreater(workflow.total_processing_time, 0)
    
    async def test_execute_research_workflow_failure(self):
        """Test workflow execution with failures."""
        mock_ctx = Mock()
        
        # Mock failed response for MeTTa validation
        with patch.object(self.orchestrator, '_send_and_wait') as mock_send:
            mock_send.side_effect = Exception("MeTTa validation failed")
            
            workflow = await self.orchestrator.execute_research_workflow(
                mock_ctx, self.sample_query_data, self.parsed_query
            )
            
            self.assertEqual(workflow.status, WorkflowStatus.FAILED)
            self.assertGreater(len(workflow.error_log), 0)
    
    async def test_execute_metta_step(self):
        """Test MeTTa validation step execution."""
        step = WorkflowStep(
            step_id="test-metta-step",
            step_name="Test MeTTa Validation",
            agent_role=AgentRole.METTA_AGENT,
            status=WorkflowStatus.PENDING,
            input_data={
                "query_type": "validate",
                "query_expression": "(ethical-compliance-check IRB-2024-123456 observational)"
            }
        )
        
        result = await self.orchestrator._execute_metta_step(
            Mock(), step, self.agent_addresses["metta_integration_agent"]
        )
        
        self.assertIn("validation_result", result)
        self.assertIn("reasoning_path", result)
        self.assertIn("confidence_score", result)
    
    async def test_execute_consent_step(self):
        """Test consent verification step execution."""
        step = WorkflowStep(
            step_id="test-consent-step",
            step_name="Test Consent Check",
            agent_role=AgentRole.CONSENT_AGENT,
            status=WorkflowStatus.PENDING,
            input_data={
                "data_type": "demographics",
                "research_category": "clinical_trials",
                "requester_id": "HMS-12345"
            }
        )
        
        result = await self.orchestrator._execute_consent_step(
            Mock(), step, self.agent_addresses["patient_consent_agent"]
        )
        
        self.assertEqual(result["consent_status"], "granted")
        self.assertEqual(result["data_type"], "demographics")
        self.assertEqual(result["research_category"], "clinical_trials")
    
    async def test_execute_data_step(self):
        """Test data retrieval step execution."""
        # Create mock workflow with successful consent steps
        workflow = WorkflowExecution(
            workflow_id="test-workflow",
            query_id="test-query",
            researcher_id="HMS-12345",
            status=WorkflowStatus.RUNNING
        )
        
        # Add successful consent step
        consent_step = WorkflowStep(
            step_id="consent-step",
            step_name="Consent Check",
            agent_role=AgentRole.CONSENT_AGENT,
            status=WorkflowStatus.COMPLETED,
            input_data={},
            output_data={"consent_status": "granted"}
        )
        workflow.steps.append(consent_step)
        
        data_step = WorkflowStep(
            step_id="test-data-step",
            step_name="Test Data Retrieval",
            agent_role=AgentRole.DATA_CUSTODIAN,
            status=WorkflowStatus.PENDING,
            input_data={
                "requester_id": "HMS-12345",
                "data_criteria": {"data_types": ["demographics"]}
            }
        )
        
        result = await self.orchestrator._execute_data_step(
            Mock(), data_step, self.agent_addresses["data_custodian_agent"], workflow
        )
        
        self.assertIn("dataset_id", result)
        self.assertIn("patient_count", result)
        self.assertIn("raw_data", result)
    
    async def test_execute_privacy_step(self):
        """Test data anonymization step execution."""
        # Create mock workflow with data retrieval results
        workflow = WorkflowExecution(
            workflow_id="test-workflow",
            query_id="test-query",
            researcher_id="HMS-12345",
            status=WorkflowStatus.RUNNING
        )
        
        # Add data retrieval step with results
        data_step = WorkflowStep(
            step_id="data-step",
            step_name="Data Retrieval",
            agent_role=AgentRole.DATA_CUSTODIAN,
            status=WorkflowStatus.COMPLETED,
            input_data={},
            output_data={
                "dataset_id": "DS-TEST123",
                "raw_data": [{"patient_id": "P001", "age": 45, "gender": "M"}]
            }
        )
        workflow.steps.append(data_step)
        
        privacy_step = WorkflowStep(
            step_id="test-privacy-step",
            step_name="Test Anonymization",
            agent_role=AgentRole.PRIVACY_AGENT,
            status=WorkflowStatus.PENDING,
            input_data={
                "privacy_level": "confidential",
                "k_anonymity_threshold": 5
            }
        )
        
        result = await self.orchestrator._execute_privacy_step(
            Mock(), privacy_step, self.agent_addresses["privacy_agent"], workflow
        )
        
        self.assertIn("anonymized_data", result)
        self.assertIn("privacy_metrics", result)
        self.assertIn("anonymization_log", result)
    
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker pattern for agent failures."""
        agent_role = AgentRole.METTA_AGENT
        
        # Initially circuit breaker should be closed
        self.assertFalse(self.orchestrator._is_circuit_breaker_open(agent_role))
        
        # Record multiple failures to trigger circuit breaker
        for _ in range(5):
            self.orchestrator._record_failure(agent_role)
        
        # Circuit breaker should now be open
        self.assertTrue(self.orchestrator._is_circuit_breaker_open(agent_role))
        
        # Reset circuit breaker
        self.orchestrator._reset_circuit_breaker(agent_role)
        self.assertFalse(self.orchestrator._is_circuit_breaker_open(agent_role))
    
    def test_get_workflow_status(self):
        """Test workflow status retrieval."""
        # Create a workflow and add to active workflows
        workflow = WorkflowExecution(
            workflow_id="test-status-workflow",
            query_id="test-query",
            researcher_id="HMS-12345",
            status=WorkflowStatus.RUNNING
        )
        self.orchestrator.active_workflows[workflow.workflow_id] = workflow
        
        status = self.orchestrator.get_workflow_status(workflow.workflow_id)
        
        self.assertIsNotNone(status)
        self.assertEqual(status["workflow_id"], workflow.workflow_id)
        self.assertEqual(status["status"], WorkflowStatus.RUNNING.value)
        self.assertIn("created_at", status)
        self.assertIn("steps", status)
    
    def test_get_orchestrator_stats(self):
        """Test orchestrator statistics retrieval."""
        stats = self.orchestrator.get_orchestrator_stats()
        
        self.assertIn("active_workflows", stats)
        self.assertIn("completed_workflows", stats)
        self.assertIn("failed_workflows", stats)
        self.assertIn("circuit_breaker_status", stats)
        self.assertIn("average_processing_time", stats)
        
        # Check circuit breaker status structure
        for agent_role in AgentRole:
            self.assertIn(agent_role.value, stats["circuit_breaker_status"])
            breaker_status = stats["circuit_breaker_status"][agent_role.value]
            self.assertIn("is_open", breaker_status)
            self.assertIn("failure_count", breaker_status)


class TestResearchQueryAgentIntegration(unittest.TestCase):
    """Integration tests for complete Research Query Agent functionality."""
    
    def setUp(self):
        self.agent = ResearchQueryAgent(port=8005)
        self.sample_message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="research_query_agent",
            message_type=MessageTypes.RESEARCH_QUERY,
            payload={
                "query_id": "integration-test-123",
                "researcher_id": "HMS-12345",
                "study_title": "Integration Test Study",
                "study_description": "A comprehensive observational study to test complete agent integration",
                "data_requirements": {
                    "data_types": ["demographics", "vital_signs", "lab_results"],
                    "research_categories": ["clinical_trials", "outcomes_research"],
                    "minimum_sample_size": 100,
                    "date_range": {
                        "start_date": "2023-01-01T00:00:00Z",
                        "end_date": "2024-01-01T00:00:00Z"
                    }
                },
                "ethical_approval_id": "IRB-2024-123456",
                "inclusion_criteria": ["age >= 18", "diagnosis = cardiovascular_disease"],
                "exclusion_criteria": ["pregnancy", "terminal_illness"],
                "privacy_requirements": {
                    "anonymization_methods": ["k_anonymity", "generalization"],
                    "k_anonymity": 5
                }
            }
        )
    
    async def test_handle_research_query_success(self):
        """Test successful research query handling."""
        mock_ctx = Mock()
        
        # Mock workflow orchestrator to return successful result
        with patch.object(self.agent.workflow_orchestrator, 'execute_research_workflow') as mock_execute:
            mock_workflow_result = Mock()
            mock_workflow_result.workflow_id = "test-workflow-123"
            mock_workflow_result.status = WorkflowStatus.COMPLETED
            mock_workflow_result.total_processing_time = 45.5
            mock_workflow_result.results = {
                "data_summary": {"patient_count": 150, "data_fields": ["age", "gender"]},
                "dataset": {
                    "anonymized_data": [{"patient_id": "ANON_001", "age": 45, "gender": "M"}],
                    "privacy_metrics": {"k_anonymity": 5}
                },
                "processing_log": ["Step 1: Validation completed", "Step 2: Data retrieved"]
            }
            mock_execute.return_value = mock_workflow_result
            
            result = await self.agent._handle_research_query(mock_ctx, "test_sender", self.sample_message)
            
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["query_id"], "integration-test-123")
            self.assertEqual(result["workflow_id"], "test-workflow-123")
            self.assertIn("result", result)
            self.assertIn("processing_time", result)
    
    async def test_handle_research_query_validation_failure(self):
        """Test research query handling with validation failure."""
        mock_ctx = Mock()
        
        # Create invalid query (missing required field)
        invalid_message = self.sample_message
        del invalid_message.payload["researcher_id"]
        
        result = await self.agent._handle_research_query(mock_ctx, "test_sender", invalid_message)
        
        self.assertEqual(result["status"], "validation_failed")
        self.assertIn("errors", result)
        self.assertIn("Missing required field: researcher_id", result["errors"])
    
    async def test_handle_research_query_ethical_failure(self):
        """Test research query handling with ethical validation failure."""
        mock_ctx = Mock()
        
        # Create query with ethical issues (old approval)
        ethical_issue_message = self.sample_message
        ethical_issue_message.payload["ethical_approval_id"] = "IRB-2020-123456"  # Old approval
        
        result = await self.agent._handle_research_query(mock_ctx, "test_sender", ethical_issue_message)
        
        self.assertEqual(result["status"], "ethical_validation_failed")
        self.assertIn("ethical_score", result)
        self.assertLess(result["ethical_score"], 0.6)
    
    async def test_handle_query_status(self):
        """Test query status handling."""
        mock_ctx = Mock()
        
        # Add a query to active queries
        query_id = "status-test-123"
        self.agent.active_queries[query_id] = {
            "query_id": query_id,
            "researcher_id": "HMS-12345",
            "status": "processing",
            "created_at": datetime.utcnow()
        }
        
        status_message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="research_query_agent",
            message_type=MessageTypes.QUERY_STATUS,
            payload={"query_id": query_id}
        )
        
        result = await self.agent._handle_query_status(mock_ctx, "test_sender", status_message)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["query_id"], query_id)
        self.assertEqual(result["query_status"], "processing")
        self.assertEqual(result["researcher_id"], "HMS-12345")
    
    async def test_handle_query_cancellation(self):
        """Test query cancellation handling."""
        mock_ctx = Mock()
        
        # Add a query to active queries
        query_id = "cancel-test-123"
        researcher_id = "HMS-12345"
        self.agent.active_queries[query_id] = {
            "query_id": query_id,
            "researcher_id": researcher_id,
            "status": "processing",
            "created_at": datetime.utcnow()
        }
        
        cancel_message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="research_query_agent",
            message_type="query_cancel",
            payload={
                "query_id": query_id,
                "requester_id": researcher_id
            }
        )
        
        result = await self.agent._handle_query_cancellation(mock_ctx, "test_sender", cancel_message)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["query_id"], query_id)
        self.assertNotIn(query_id, self.agent.active_queries)
        self.assertEqual(len(self.agent.query_history), 1)
        self.assertEqual(self.agent.query_history[0]["status"], "cancelled")
    
    async def test_handle_query_history(self):
        """Test query history handling."""
        mock_ctx = Mock()
        
        # Add queries to history
        researcher_id = "HMS-12345"
        for i in range(3):
            query = {
                "query_id": f"history-test-{i}",
                "researcher_id": researcher_id,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=i),
                "parsed_query": Mock(query_type=QueryType.OBSERVATIONAL, study_title=f"Study {i}")
            }
            self.agent.query_history.append(query)
        
        history_message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="research_query_agent",
            message_type="query_history",
            payload={
                "researcher_id": researcher_id,
                "limit": 10
            }
        )
        
        result = await self.agent._handle_query_history(mock_ctx, "test_sender", history_message)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["queries"]), 3)
        self.assertEqual(result["total_count"], 3)
        
        # Check that queries are sorted by creation date (newest first)
        query_dates = [q["created_at"] for q in result["queries"]]
        self.assertEqual(query_dates, sorted(query_dates, reverse=True))
    
    async def test_handle_health_check(self):
        """Test health check handling."""
        mock_ctx = Mock()
        
        health_message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="research_query_agent",
            message_type=MessageTypes.HEALTH_CHECK,
            payload={}
        )
        
        result = await self.agent._handle_health_check(mock_ctx, "test_sender", health_message)
        
        self.assertEqual(result["status"], "healthy")
        self.assertIn("agent_id", result)
        self.assertIn("active_queries", result)
        self.assertIn("query_statistics", result)
        self.assertIn("orchestrator_statistics", result)
        self.assertIn("last_heartbeat", result)
    
    def test_agent_statistics_tracking(self):
        """Test agent statistics tracking."""
        # Initial stats should be zero
        self.assertEqual(self.agent.stats["total_queries"], 0)
        self.assertEqual(self.agent.stats["successful_queries"], 0)
        self.assertEqual(self.agent.stats["failed_queries"], 0)
        
        # Stats should be updated when processing queries
        # This would be tested in integration with actual query processing


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end workflow tests."""
    
    async def test_complete_research_workflow(self):
        """Test complete research workflow from query to results."""
        # This test would simulate a complete workflow
        # from query submission to anonymized results delivery
        
        # 1. Create research query
        query_data = {
            "query_id": "e2e-test-123",
            "researcher_id": "HMS-12345",
            "study_description": "End-to-end test study for cardiovascular outcomes research",
            "data_requirements": {
                "data_types": ["demographics", "vital_signs", "lab_results"],
                "research_categories": ["outcomes_research"],
                "minimum_sample_size": 50
            },
            "ethical_approval_id": "IRB-2024-123456",
            "privacy_requirements": {
                "anonymization_methods": ["k_anonymity"],
                "k_anonymity": 5
            }
        }
        
        # 2. Process query through agent
        agent = ResearchQueryAgent(port=8005)
        query_processor = QueryProcessor()
        
        # 3. Parse and validate query
        parsed_query, validation_result = query_processor.parse_research_query(query_data)
        
        self.assertIsNotNone(parsed_query)
        self.assertTrue(validation_result.is_valid)
        
        # 4. Validate ethical compliance
        ethical_result = query_processor.validate_ethical_compliance(parsed_query)
        
        self.assertTrue(ethical_result.is_valid)
        self.assertGreaterEqual(ethical_result.ethical_score, 0.6)
        
        # 5. Build workflow steps
        orchestrator = WorkflowOrchestrator(agent._get_default_agent_addresses())
        steps = orchestrator._build_workflow_steps(parsed_query)
        
        self.assertGreater(len(steps), 0)
        
        # 6. Verify workflow structure
        step_types = [step.agent_role for step in steps]
        required_agents = [AgentRole.METTA_AGENT, AgentRole.CONSENT_AGENT, 
                          AgentRole.DATA_CUSTODIAN, AgentRole.PRIVACY_AGENT]
        
        for required_agent in required_agents:
            self.assertIn(required_agent, step_types)
        
        # Note: Full workflow execution would require actual agent communication
        # which is mocked in the individual component tests above


if __name__ == "__main__":
    # Run async tests
    async def run_async_tests():
        # Create test suite for async tests
        async_test_classes = [
            TestWorkflowOrchestrator,
            TestResearchQueryAgentIntegration,
            TestEndToEndWorkflow
        ]
        
        for test_class in async_test_classes:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            for test in suite:
                if asyncio.iscoroutinefunction(getattr(test, test._testMethodName)):
                    await getattr(test, test._testMethodName)()
                else:
                    test.debug()
    
    # Run synchronous tests normally
    unittest.main(verbosity=2, exit=False)
    
    # Run async tests
    asyncio.run(run_async_tests())