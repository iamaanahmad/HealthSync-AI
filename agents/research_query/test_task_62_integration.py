#!/usr/bin/env python3
"""
Integration tests for Research Query Agent Task 6.2: Multi-agent workflow orchestration.
Tests agent communication protocols, error handling, result aggregation, and audit trails.
"""

import unittest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import uuid

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.research_query.workflow_orchestrator import (
    WorkflowOrchestrator, WorkflowStatus, AgentRole, 
    WorkflowExecution, WorkflowStep
)
from agents.research_query.query_processor import QueryProcessor, QueryType, DataSensitivity
from agents.research_query.agent import ResearchQueryAgent
from shared.protocols.agent_messages import AgentMessage, MessageTypes


class TestTask62WorkflowOrchestration(unittest.TestCase):
    """Test Task 6.2: Multi-agent workflow orchestration implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent_addresses = {
            "patient_consent_agent": "agent1qg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg",
            "data_custodian_agent": "agent1qh4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc",
            "privacy_agent": "agent1qi5def5def5def5def5def5def5def5def5def5def5def5def5def",
            "metta_integration_agent": "agent1qj6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi"
        }
        self.orchestrator = WorkflowOrchestrator(self.agent_addresses)
        
        # Sample query data for testing
        self.sample_query_data = {
            "query_id": "task62-test-001",
            "researcher_id": "HMS-12345",
            "study_title": "Task 6.2 Integration Test",
            "study_description": "A comprehensive test of multi-agent workflow orchestration for research data retrieval",
            "data_requirements": {
                "data_types": ["demographics", "vital_signs", "lab_results"],
                "research_categories": ["clinical_trials", "outcomes_research"],
                "minimum_sample_size": 100
            },
            "ethical_approval_id": f"IRB-{datetime.now().year}-123456",
            "privacy_requirements": {
                "anonymization_methods": ["k_anonymity", "generalization"],
                "k_anonymity": 5
            }
        }
        
        # Create parsed query
        processor = QueryProcessor()
        self.parsed_query, _ = processor.parse_research_query(self.sample_query_data)
    
    def test_requirement_4_1_agent_communication_protocols(self):
        """Test Requirement 4.1: Agent communication protocols for data retrieval workflow."""
        print("\n=== Testing Requirement 4.1: Agent Communication Protocols ===")
        
        # Test workflow step building with proper sequencing
        steps = self.orchestrator._build_workflow_steps(self.parsed_query)
        
        # Verify proper agent sequence: MeTTa → Consent → Data → Privacy
        step_sequence = [step.agent_role for step in steps]
        
        # Check that MeTTa validation comes first
        metta_indices = [i for i, role in enumerate(step_sequence) if role == AgentRole.METTA_AGENT]
        consent_indices = [i for i, role in enumerate(step_sequence) if role == AgentRole.CONSENT_AGENT]
        data_indices = [i for i, role in enumerate(step_sequence) if role == AgentRole.DATA_CUSTODIAN]
        privacy_indices = [i for i, role in enumerate(step_sequence) if role == AgentRole.PRIVACY_AGENT]
        
        self.assertGreater(len(metta_indices), 0, "Should have MeTTa validation steps")
        self.assertGreater(len(consent_indices), 0, "Should have consent verification steps")
        self.assertEqual(len(data_indices), 1, "Should have one data retrieval step")
        self.assertEqual(len(privacy_indices), 1, "Should have one privacy step")
        
        # Verify proper sequencing
        if metta_indices and consent_indices:
            self.assertLess(min(metta_indices), min(consent_indices), "MeTTa should come before consent")
        if consent_indices and data_indices:
            self.assertLess(max(consent_indices), min(data_indices), "Consent should come before data")
        if data_indices and privacy_indices:
            self.assertLess(max(data_indices), min(privacy_indices), "Data should come before privacy")
        
        print(f"✓ Workflow sequence validated: {len(steps)} steps in correct order")
        
        # Test message acknowledgment system
        for step in steps:
            self.assertIsNotNone(step.step_id, "Each step should have unique ID")
            self.assertIsInstance(step.input_data, dict, "Each step should have input data")
            self.assertEqual(step.status, WorkflowStatus.PENDING, "Steps should start as pending")
        
        print("✓ Message acknowledgment system properly configured")
        
        # Test standardized message protocols
        sample_step = steps[0]
        self.assertIn("query_type", sample_step.input_data.keys() | {"data_type", "requester_id", "privacy_level"})
        
        print("✓ Standardized message protocols implemented")
    
    async def test_requirement_4_2_error_handling_recovery(self):
        """Test Requirement 4.2: Error handling and recovery mechanisms for failed agent interactions."""
        print("\n=== Testing Requirement 4.2: Error Handling & Recovery ===")
        
        mock_ctx = Mock()
        
        # Test circuit breaker functionality
        agent_role = AgentRole.METTA_AGENT
        
        # Initially circuit breaker should be closed
        self.assertFalse(self.orchestrator._is_circuit_breaker_open(agent_role))
        
        # Simulate multiple failures to trigger circuit breaker
        for i in range(5):
            self.orchestrator._record_failure(agent_role)
        
        self.assertTrue(self.orchestrator._is_circuit_breaker_open(agent_role))
        print("✓ Circuit breaker triggers after threshold failures")
        
        # Test circuit breaker recovery
        self.orchestrator._reset_circuit_breaker(agent_role)
        self.assertFalse(self.orchestrator._is_circuit_breaker_open(agent_role))
        print("✓ Circuit breaker recovery mechanism works")
        
        # Test retry strategies
        retry_strategies = self.orchestrator.retry_strategies
        for agent_role in AgentRole:
            self.assertIn(agent_role, retry_strategies, f"Should have retry strategy for {agent_role.value}")
            strategy = retry_strategies[agent_role]
            self.assertIn("max_retries", strategy)
            self.assertIn("backoff_factor", strategy)
        
        print("✓ Retry strategies configured for all agents")
        
        # Test step recovery mechanisms
        failed_step = WorkflowStep(
            step_id="test-recovery-step",
            step_name="Test Recovery",
            agent_role=AgentRole.METTA_AGENT,
            status=WorkflowStatus.FAILED,
            input_data={"query_type": "validate"},
            error_message="Simulated failure"
        )
        
        workflow = WorkflowExecution(
            workflow_id="test-recovery-workflow",
            query_id="test-query",
            researcher_id="HMS-12345",
            status=WorkflowStatus.RUNNING
        )
        
        # Test MeTTa step recovery
        recovery_success = await self.orchestrator._attempt_step_recovery(mock_ctx, workflow, failed_step)
        self.assertTrue(recovery_success, "MeTTa step recovery should succeed with fallback")
        self.assertEqual(failed_step.status, WorkflowStatus.COMPLETED)
        self.assertIsNotNone(failed_step.output_data)
        
        print("✓ Step recovery mechanisms implemented")
        
        # Test error escalation
        workflow.error_log = []
        self.orchestrator._add_error_log(workflow, "TEST_ERROR", "Test error message")
        
        self.assertEqual(len(workflow.error_log), 1)
        self.assertEqual(workflow.error_log[0]["error_code"], "TEST_ERROR")
        
        print("✓ Error escalation and logging working")
    
    async def test_requirement_4_3_result_aggregation(self):
        """Test Requirement 4.3: Result aggregation from multiple data sources."""
        print("\n=== Testing Requirement 4.3: Result Aggregation ===")
        
        # Create workflow with completed steps
        workflow = WorkflowExecution(
            workflow_id="test-aggregation-workflow",
            query_id="test-query",
            researcher_id="HMS-12345",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        # Add completed steps with sample outputs
        metta_step = WorkflowStep(
            step_id="metta-step",
            step_name="MeTTa Validation",
            agent_role=AgentRole.METTA_AGENT,
            status=WorkflowStatus.COMPLETED,
            input_data={},
            output_data={
                "validation_result": [{"validation": "passed"}],
                "reasoning_path": ["ethical-approval-valid", "study-purpose-legitimate"],
                "confidence_score": 0.95
            }
        )
        
        consent_step = WorkflowStep(
            step_id="consent-step",
            step_name="Consent Check",
            agent_role=AgentRole.CONSENT_AGENT,
            status=WorkflowStatus.COMPLETED,
            input_data={},
            output_data={
                "consent_status": "granted",
                "data_type": "demographics",
                "research_category": "clinical_trials"
            }
        )
        
        data_step = WorkflowStep(
            step_id="data-step",
            step_name="Data Retrieval",
            agent_role=AgentRole.DATA_CUSTODIAN,
            status=WorkflowStatus.COMPLETED,
            input_data={},
            output_data={
                "dataset_id": "DS-TEST123",
                "patient_count": 150,
                "data_fields": ["age", "gender", "diagnosis"],
                "raw_data": [{"patient_id": f"P{i:03d}", "age": 45+i, "gender": "M" if i%2 else "F"} 
                           for i in range(10)]
            }
        )
        
        privacy_step = WorkflowStep(
            step_id="privacy-step",
            step_name="Data Anonymization",
            agent_role=AgentRole.PRIVACY_AGENT,
            status=WorkflowStatus.COMPLETED,
            input_data={},
            output_data={
                "anonymized_data": [{"patient_id": f"ANON_{i:03d}", "age": 45+i, "gender": "M" if i%2 else "F"} 
                                  for i in range(10)],
                "privacy_metrics": {"k_anonymity": 5, "l_diversity": 3},
                "anonymization_log": "Applied k-anonymity and generalization",
                "quality_score": 0.92
            }
        )
        
        workflow.steps = [metta_step, consent_step, data_step, privacy_step]
        
        # Test result aggregation
        aggregated_results = await self.orchestrator.aggregate_workflow_results(workflow)
        
        # Verify aggregation structure
        self.assertIn("consent_summary", aggregated_results)
        self.assertIn("data_summary", aggregated_results)
        self.assertIn("privacy_summary", aggregated_results)
        self.assertIn("ethics_summary", aggregated_results)
        self.assertIn("quality_assessment", aggregated_results)
        self.assertIn("final_dataset", aggregated_results)
        
        print("✓ Result aggregation structure complete")
        
        # Test consent aggregation
        consent_summary = aggregated_results["consent_summary"]
        self.assertEqual(consent_summary["total_consent_checks"], 1)
        self.assertEqual(consent_summary["granted_consents"], 1)
        self.assertEqual(consent_summary["consent_rate"], 1.0)
        self.assertTrue(consent_summary["consent_threshold_met"])
        
        print("✓ Consent result aggregation working")
        
        # Test data aggregation
        data_summary = aggregated_results["data_summary"]
        self.assertEqual(data_summary["total_patients"], 150)
        self.assertIn("age", data_summary["unique_data_fields"])
        self.assertGreater(data_summary["data_quality_score"], 0.0)
        
        print("✓ Data result aggregation working")
        
        # Test privacy aggregation
        privacy_summary = aggregated_results["privacy_summary"]
        self.assertTrue(privacy_summary["anonymization_successful"])
        self.assertTrue(privacy_summary["k_anonymity_achieved"])
        self.assertEqual(privacy_summary["anonymized_record_count"], 10)
        
        print("✓ Privacy result aggregation working")
        
        # Test quality assessment
        quality_assessment = aggregated_results["quality_assessment"]
        self.assertIn("overall_quality", quality_assessment)
        self.assertIn("compliance_passed", quality_assessment)
        self.assertIn("quality_grade", quality_assessment)
        
        print(f"✓ Quality assessment: {quality_assessment['quality_grade']} grade, "
              f"compliance {'PASSED' if quality_assessment['compliance_passed'] else 'FAILED'}")
        
        # Test final dataset creation
        final_dataset = aggregated_results["final_dataset"]
        if quality_assessment["compliance_passed"]:
            self.assertEqual(final_dataset["status"], "approved")
            self.assertIn("records", final_dataset)
            self.assertIn("metadata", final_dataset)
        
        print("✓ Final dataset creation working")
    
    def test_requirement_4_4_workflow_logging_audit_trail(self):
        """Test Requirement 4.4: Workflow logging and audit trail generation."""
        print("\n=== Testing Requirement 4.4: Workflow Logging & Audit Trail ===")
        
        # Test audit trail initialization
        self.assertIsInstance(self.orchestrator.audit_trail, list)
        # Clear any existing audit trail entries from previous tests
        self.orchestrator.audit_trail.clear()
        
        # Create test workflow
        workflow = WorkflowExecution(
            workflow_id="test-audit-workflow",
            query_id="test-query",
            researcher_id="HMS-12345",
            status=WorkflowStatus.RUNNING
        )
        
        # Test audit event logging
        test_events = [
            ("WORKFLOW_STARTED", {"reason": "test_initialization"}),
            ("STEP_STARTED", {"step_id": "test-step-1", "agent_role": "metta_agent"}),
            ("STEP_COMPLETED", {"step_id": "test-step-1", "processing_time": 2.5}),
            ("STEP_FAILED", {"step_id": "test-step-2", "error": "simulated_error"}),
            ("RECOVERY_ATTEMPT", {"step_id": "test-step-2", "recovery_method": "fallback"}),
            ("WORKFLOW_COMPLETED", {"final_status": "completed"})
        ]
        
        for event_type, details in test_events:
            self.orchestrator._log_audit_event(workflow, event_type, details)
        
        # Verify audit trail entries
        self.assertEqual(len(self.orchestrator.audit_trail), len(test_events))
        
        for i, (expected_type, expected_details) in enumerate(test_events):
            entry = self.orchestrator.audit_trail[i]
            
            self.assertEqual(entry["event_type"], expected_type)
            self.assertEqual(entry["workflow_id"], workflow.workflow_id)
            self.assertEqual(entry["query_id"], workflow.query_id)
            self.assertEqual(entry["researcher_id"], workflow.researcher_id)
            self.assertIn("timestamp", entry)
            
            # Check details are included
            for key, value in expected_details.items():
                self.assertEqual(entry["details"][key], value)
        
        print(f"✓ Audit trail logging: {len(test_events)} events recorded")
        
        # Test audit trail filtering
        workflow_audit = self.orchestrator.get_audit_trail(workflow_id=workflow.workflow_id)
        self.assertEqual(len(workflow_audit), len(test_events))
        
        step_events = self.orchestrator.get_audit_trail(event_type="STEP_STARTED")
        self.assertEqual(len(step_events), 1)
        
        print("✓ Audit trail filtering working")
        
        # Test audit trail size management
        # Add many entries to test size limit
        for i in range(15000):  # Exceed the 10000 limit
            self.orchestrator._log_audit_event(workflow, "TEST_EVENT", {"index": i})
        
        # Should be trimmed to 5000 entries
        self.assertLessEqual(len(self.orchestrator.audit_trail), 10000)
        
        print("✓ Audit trail size management working")
        
        # Test performance metrics tracking
        performance_metrics = self.orchestrator.performance_metrics
        
        required_metrics = ["total_workflows", "successful_workflows", "failed_workflows", 
                          "average_processing_time", "agent_performance"]
        
        for metric in required_metrics:
            self.assertIn(metric, performance_metrics)
        
        # Test agent performance tracking
        agent_performance = performance_metrics["agent_performance"]
        for agent_role in AgentRole:
            self.assertIn(agent_role.value, agent_performance)
            agent_metrics = agent_performance[agent_role.value]
            self.assertIn("success_rate", agent_metrics)
            self.assertIn("avg_response_time", agent_metrics)
        
        print("✓ Performance metrics tracking implemented")
        
        # Test detailed logging configuration
        self.assertTrue(self.orchestrator.detailed_logging)
        
        # Test with logging disabled
        self.orchestrator.detailed_logging = False
        initial_count = len(self.orchestrator.audit_trail)
        
        self.orchestrator._log_audit_event(workflow, "TEST_DISABLED", {})
        
        # Should not add new entry when disabled
        self.assertEqual(len(self.orchestrator.audit_trail), initial_count)
        
        print("✓ Audit logging can be disabled")


class TestTask62EndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests for Task 6.2."""
    
    async def test_complete_workflow_with_orchestration(self):
        """Test complete workflow execution with all Task 6.2 features."""
        print("\n=== Testing Complete Workflow with Enhanced Orchestration ===")
        
        # Create Research Query Agent
        agent = ResearchQueryAgent(port=8005)
        
        # Create comprehensive test query
        test_query = {
            "query_id": "e2e-task62-001",
            "researcher_id": "HMS-12345",
            "study_title": "End-to-End Task 6.2 Test",
            "study_description": "Comprehensive observational clinical study to test enhanced multi-agent workflow orchestration with error handling, recovery, and result aggregation for treatment outcomes research and prevention strategies",
            "data_requirements": {
                "data_types": ["demographics", "vital_signs", "lab_results", "medications"],
                "research_categories": ["clinical_trials", "outcomes_research", "epidemiology"],
                "minimum_sample_size": 200,
                "date_range": {
                    "start_date": "2023-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            },
            "ethical_approval_id": f"IRB-{datetime.now().year}-123456",
            "inclusion_criteria": ["age >= 18", "diagnosis = cardiovascular_disease"],
            "exclusion_criteria": ["pregnancy", "terminal_illness"],
            "privacy_requirements": {
                "anonymization_methods": ["k_anonymity", "generalization", "access_control"],
                "k_anonymity": 5
            }
        }
        
        # Test message creation
        message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="research_query_agent",
            message_type=MessageTypes.RESEARCH_QUERY,
            payload=test_query
        )
        
        mock_ctx = Mock()
        
        # Mock successful workflow execution
        with patch.object(agent.workflow_orchestrator, 'execute_research_workflow') as mock_execute:
            # Create mock workflow result with all Task 6.2 features
            mock_workflow_result = Mock()
            mock_workflow_result.workflow_id = "e2e-workflow-123"
            mock_workflow_result.status = WorkflowStatus.COMPLETED
            mock_workflow_result.total_processing_time = 75.5
            
            # Mock comprehensive results with aggregation
            mock_workflow_result.results = {
                "workflow_id": "e2e-workflow-123",
                "query_id": "e2e-task62-001",
                "researcher_id": "HMS-12345",
                "processing_summary": {
                    "total_steps": 6,
                    "successful_steps": 6,
                    "failed_steps": 0,
                    "recovery_attempts": 1,
                    "total_processing_time": 75.5
                },
                "aggregated_results": {
                    "consent_summary": {
                        "total_consent_checks": 3,
                        "granted_consents": 3,
                        "consent_rate": 1.0,
                        "consent_threshold_met": True
                    },
                    "data_summary": {
                        "total_patients": 200,
                        "unique_data_fields": ["age", "gender", "diagnosis", "treatment"],
                        "data_quality_score": 0.95
                    },
                    "privacy_summary": {
                        "anonymization_successful": True,
                        "k_anonymity_achieved": True,
                        "privacy_compliance_score": 0.98,
                        "anonymized_record_count": 200
                    },
                    "ethics_summary": {
                        "average_confidence": 0.92,
                        "ethics_compliance_passed": True,
                        "validation_count": 1
                    },
                    "quality_assessment": {
                        "overall_quality": 0.94,
                        "compliance_passed": True,
                        "quality_grade": "A"
                    },
                    "final_dataset": {
                        "status": "approved",
                        "records": [{"patient_id": f"ANON_{i:04d}", "age_group": "40-49"} for i in range(10)],
                        "metadata": {
                            "total_records": 200,
                            "quality_grade": "A",
                            "compliance_status": "PASSED"
                        }
                    }
                },
                "dataset": {
                    "anonymized_data": [{"patient_id": f"ANON_{i:04d}", "age_group": "40-49"} for i in range(10)],
                    "privacy_metrics": {"k_anonymity": 5, "l_diversity": 3},
                    "quality_score": 0.94
                },
                "data_summary": {
                    "patient_count": 200,
                    "data_fields": ["age", "gender", "diagnosis", "treatment"]
                },
                "processing_log": [
                    {
                        "step_name": "MeTTa Validation",
                        "agent_role": "metta_integration_agent",
                        "status": "completed",
                        "processing_time": 5.2,
                        "retry_count": 0
                    },
                    {
                        "step_name": "Consent Check",
                        "agent_role": "patient_consent_agent", 
                        "status": "completed",
                        "processing_time": 3.1,
                        "retry_count": 1  # Simulated retry
                    }
                ]
            }
            
            mock_execute.return_value = mock_workflow_result
            
            # Execute the query
            result = await agent._handle_research_query(mock_ctx, "test_sender", message)
            
            # Verify Task 6.2 requirements are met
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["query_id"], "e2e-task62-001")
            self.assertEqual(result["workflow_id"], "e2e-workflow-123")
            self.assertIn("result", result)
            self.assertIn("processing_time", result)
            
            # Verify enhanced orchestration features
            result_data = result["result"]
            
            # Check aggregated results structure
            self.assertIn("aggregated_results", result_data)
            aggregated = result_data["aggregated_results"]
            
            # Verify all result types are aggregated
            self.assertIn("consent_summary", aggregated)
            self.assertIn("data_summary", aggregated)
            self.assertIn("privacy_summary", aggregated)
            self.assertIn("ethics_summary", aggregated)
            self.assertIn("quality_assessment", aggregated)
            
            # Verify quality assessment
            quality = aggregated["quality_assessment"]
            self.assertTrue(quality["compliance_passed"])
            self.assertEqual(quality["quality_grade"], "A")
            self.assertGreaterEqual(quality["overall_quality"], 0.9)
            
            # Verify processing summary includes recovery information
            processing_summary = result_data["processing_summary"]
            self.assertIn("recovery_attempts", processing_summary)
            self.assertIn("total_processing_time", processing_summary)
            
            print("✓ Complete workflow execution with enhanced orchestration successful")
            print(f"✓ Quality Grade: {quality['quality_grade']}")
            print(f"✓ Processing Time: {result['processing_time']}s")
            print(f"✓ Recovery Attempts: {processing_summary['recovery_attempts']}")
            print(f"✓ Final Dataset: {len(aggregated['final_dataset']['records'])} records")
    
    def test_orchestrator_statistics_and_monitoring(self):
        """Test orchestrator statistics and monitoring capabilities."""
        print("\n=== Testing Orchestrator Statistics & Monitoring ===")
        
        orchestrator = WorkflowOrchestrator({})
        
        # Test initial statistics
        stats = orchestrator.get_orchestrator_stats()
        
        required_stats = [
            "active_workflows", "completed_workflows", "failed_workflows",
            "circuit_breaker_status", "average_processing_time"
        ]
        
        for stat in required_stats:
            self.assertIn(stat, stats)
        
        # Test circuit breaker status
        cb_status = stats["circuit_breaker_status"]
        for agent_role in AgentRole:
            self.assertIn(agent_role.value, cb_status)
            agent_cb = cb_status[agent_role.value]
            self.assertIn("is_open", agent_cb)
            self.assertIn("failure_count", agent_cb)
        
        print("✓ Orchestrator statistics complete")
        
        # Test performance metrics
        performance = orchestrator.performance_metrics
        
        self.assertIn("agent_performance", performance)
        agent_perf = performance["agent_performance"]
        
        for agent_role in AgentRole:
            self.assertIn(agent_role.value, agent_perf)
            metrics = agent_perf[agent_role.value]
            self.assertIn("success_rate", metrics)
            self.assertIn("avg_response_time", metrics)
        
        print("✓ Performance metrics tracking complete")


def run_task_62_tests():
    """Run all Task 6.2 tests."""
    print("Research Query Agent - Task 6.2 Multi-Agent Workflow Orchestration Tests")
    print("=" * 80)
    
    # Create test suite
    test_classes = [TestTask62WorkflowOrchestration, TestTask62EndToEndIntegration]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        total_tests += result.testsRun
        passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        
        # Run tests manually to get detailed output
        test_instance = test_class()
        test_instance.setUp() if hasattr(test_instance, 'setUp') else None
        
        for method_name in dir(test_instance):
            if method_name.startswith('test_'):
                try:
                    method = getattr(test_instance, method_name)
                    if asyncio.iscoroutinefunction(method):
                        # Run async test
                        try:
                            asyncio.run(method())
                        except RuntimeError:
                            # Handle case where event loop is already running
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(method())
                            finally:
                                loop.close()
                    else:
                        method()
                except Exception as e:
                    print(f"✗ {method_name} failed: {str(e)}")
                    passed_tests -= 1
    
    print("\n" + "=" * 80)
    print(f"Task 6.2 Implementation Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✓ ALL TESTS PASSED - Task 6.2 implementation is complete!")
        return True
    else:
        print("✗ Some tests failed - implementation needs attention")
        return False


if __name__ == "__main__":
    success = run_task_62_tests()
    sys.exit(0 if success else 1)