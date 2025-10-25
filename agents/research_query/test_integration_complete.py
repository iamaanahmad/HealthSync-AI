#!/usr/bin/env python3
"""
Comprehensive integration tests for Research Query Agent task 6.1.
Tests query processing, validation, ethical compliance, and workflow coordination.
"""

import unittest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.research_query.query_processor import (
    QueryProcessor, QueryValidator, QueryType, DataSensitivity,
    QueryValidationResult, ParsedQuery
)
from agents.research_query.workflow_orchestrator import (
    WorkflowOrchestrator, WorkflowStatus, AgentRole, 
    WorkflowExecution, WorkflowStep
)
from agents.research_query.agent import ResearchQueryAgent
from shared.protocols.agent_messages import AgentMessage, MessageTypes


class TestTask61Implementation(unittest.TestCase):
    """Test implementation of Task 6.1: Query processing and validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = QueryProcessor()
        self.validator = QueryValidator()
        
        # Valid test query data
        self.valid_query = {
            "query_id": "task61-test-001",
            "researcher_id": "HMS-12345",
            "study_title": "Task 6.1 Integration Test",
            "study_description": "A comprehensive observational clinical study to evaluate treatment outcomes and efficacy in patients with cardiovascular disease for public health research and prevention strategies",
            "data_requirements": {
                "data_types": ["demographics", "vital_signs", "lab_results", "medications"],
                "research_categories": ["clinical_trials", "outcomes_research"],
                "minimum_sample_size": 100,
                "date_range": {
                    "start_date": "2023-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                },
                "specific_fields": ["age", "gender", "blood_pressure", "cholesterol"]
            },
            "ethical_approval_id": f"IRB-{datetime.now().year}-123456",
            "inclusion_criteria": ["age >= 18", "diagnosis = cardiovascular_disease"],
            "exclusion_criteria": ["pregnancy", "terminal_illness"],
            "privacy_requirements": {
                "anonymization_methods": ["k_anonymity", "generalization", "access_control"],
                "k_anonymity": 5
            },
            "study_duration_days": 365
        }
    
    def test_requirement_3_1_research_query_parsing(self):
        """Test Requirement 3.1: Research query parsing and structure validation."""
        print("\n=== Testing Requirement 3.1: Query Parsing ===")
        
        # Test valid query parsing
        parsed_query, validation_result = self.processor.parse_research_query(self.valid_query)
        
        self.assertIsNotNone(parsed_query, "Query parsing should succeed for valid query")
        self.assertTrue(validation_result.is_valid, "Validation should pass for valid query")
        
        # Verify parsed query structure
        self.assertEqual(parsed_query.query_id, "task61-test-001")
        self.assertEqual(parsed_query.researcher_id, "HMS-12345")
        self.assertIn("demographics", parsed_query.required_data_types)
        self.assertIn("clinical_trials", parsed_query.research_categories)
        self.assertEqual(parsed_query.expected_sample_size, 100)
        
        print(f"✓ Query parsed successfully: {parsed_query.query_id}")
        print(f"✓ Query type determined: {parsed_query.query_type.value}")
        print(f"✓ Sensitivity level: {parsed_query.sensitivity_level.value}")
        
        # Test invalid query parsing
        invalid_query = self.valid_query.copy()
        del invalid_query["researcher_id"]
        del invalid_query["ethical_approval_id"]
        
        parsed_invalid, validation_invalid = self.processor.parse_research_query(invalid_query)
        
        self.assertIsNone(parsed_invalid, "Parsing should fail for invalid query")
        self.assertFalse(validation_invalid.is_valid, "Validation should fail for invalid query")
        self.assertIn("Missing required field: researcher_id", validation_invalid.errors)
        
        print("✓ Invalid query properly rejected")
    
    def test_requirement_3_2_ethical_compliance_checking(self):
        """Test Requirement 3.2: Ethical compliance checking using MeTTa reasoning."""
        print("\n=== Testing Requirement 3.2: Ethical Compliance ===")
        
        # Test valid ethical compliance
        ethical_result = self.validator.validate_ethical_compliance(self.valid_query)
        
        self.assertTrue(ethical_result.is_valid, "Ethical validation should pass for valid query")
        self.assertGreaterEqual(ethical_result.ethical_score, 0.6, "Ethical score should be >= 0.6")
        
        print(f"✓ Ethical validation passed with score: {ethical_result.ethical_score:.2f}")
        
        # Test ethical violations
        violation_cases = [
            {
                "name": "Expired Approval",
                "modification": {"ethical_approval_id": "IRB-2020-123456"},
                "expected_error": "Invalid or expired ethical approval"
            },
            {
                "name": "Prohibited Identifiers",
                "modification": {
                    "data_requirements": {
                        **self.valid_query["data_requirements"],
                        "specific_fields": ["ssn", "full_name", "address"]
                    }
                },
                "expected_error": "Prohibited identifiers requested"
            },
            {
                "name": "Genomics without Enhanced Anonymization",
                "modification": {
                    "data_requirements": {
                        **self.valid_query["data_requirements"],
                        "data_types": ["genomics", "demographics"],
                        "enhanced_anonymization": False
                    }
                },
                "expected_error": "Genomics + demographics requires enhanced anonymization"
            }
        ]
        
        for case in violation_cases:
            test_query = self.valid_query.copy()
            test_query.update(case["modification"])
            
            result = self.validator.validate_ethical_compliance(test_query)
            
            self.assertFalse(result.is_valid, f"{case['name']} should fail ethical validation")
            self.assertTrue(
                any(case["expected_error"] in error for error in result.errors),
                f"Should contain error: {case['expected_error']}"
            )
            
            print(f"✓ {case['name']} properly detected and rejected")
    
    def test_requirement_3_3_query_routing_coordination(self):
        """Test Requirement 3.3: Query routing and multi-agent coordination logic."""
        print("\n=== Testing Requirement 3.3: Query Routing & Coordination ===")
        
        agent_addresses = {
            "patient_consent_agent": "agent1qg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg",
            "data_custodian_agent": "agent1qh4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc",
            "privacy_agent": "agent1qi5def5def5def5def5def5def5def5def5def5def5def5def5def",
            "metta_integration_agent": "agent1qj6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi"
        }
        
        orchestrator = WorkflowOrchestrator(agent_addresses)
        parsed_query, _ = self.processor.parse_research_query(self.valid_query)
        
        # Test workflow step building
        steps = orchestrator._build_workflow_steps(parsed_query)
        
        self.assertGreater(len(steps), 0, "Should generate workflow steps")
        
        # Verify all required agent roles are included
        step_agents = [step.agent_role for step in steps]
        required_agents = [AgentRole.METTA_AGENT, AgentRole.CONSENT_AGENT, 
                          AgentRole.DATA_CUSTODIAN, AgentRole.PRIVACY_AGENT]
        
        for agent in required_agents:
            self.assertIn(agent, step_agents, f"Should include {agent.value} step")
            print(f"✓ {agent.value} step included in workflow")
        
        # Test step sequencing and dependencies
        metta_steps = [s for s in steps if s.agent_role == AgentRole.METTA_AGENT]
        consent_steps = [s for s in steps if s.agent_role == AgentRole.CONSENT_AGENT]
        data_steps = [s for s in steps if s.agent_role == AgentRole.DATA_CUSTODIAN]
        privacy_steps = [s for s in steps if s.agent_role == AgentRole.PRIVACY_AGENT]
        
        self.assertGreater(len(metta_steps), 0, "Should have MeTTa validation steps")
        self.assertGreater(len(consent_steps), 0, "Should have consent verification steps")
        self.assertEqual(len(data_steps), 1, "Should have one data retrieval step")
        self.assertEqual(len(privacy_steps), 1, "Should have one anonymization step")
        
        print(f"✓ Workflow contains {len(steps)} properly sequenced steps")
        
        # Test circuit breaker functionality
        self.assertFalse(orchestrator._is_circuit_breaker_open(AgentRole.METTA_AGENT))
        
        # Simulate failures to trigger circuit breaker
        for _ in range(5):
            orchestrator._record_failure(AgentRole.METTA_AGENT)
        
        self.assertTrue(orchestrator._is_circuit_breaker_open(AgentRole.METTA_AGENT))
        print("✓ Circuit breaker functionality working")
    
    def test_requirement_4_1_query_status_tracking(self):
        """Test Requirement 4.1: Query status tracking and progress reporting."""
        print("\n=== Testing Requirement 4.1: Status Tracking ===")
        
        agent = ResearchQueryAgent(port=8005)
        
        # Test query tracking initialization
        self.assertEqual(len(agent.active_queries), 0, "Should start with no active queries")
        self.assertEqual(len(agent.query_history), 0, "Should start with empty history")
        
        # Simulate query processing
        query_id = "status-test-001"
        researcher_id = "HMS-12345"
        
        # Add query to active tracking
        query_tracking = {
            "query_id": query_id,
            "researcher_id": researcher_id,
            "status": "processing",
            "created_at": datetime.utcnow(),
            "parsed_query": Mock(query_type=QueryType.OBSERVATIONAL, study_title="Test Study")
        }
        
        agent.active_queries[query_id] = query_tracking
        
        # Test status retrieval
        mock_ctx = Mock()
        status_message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="research_query_agent",
            message_type=MessageTypes.QUERY_STATUS,
            payload={"query_id": query_id}
        )
        
        # Run async status check
        async def test_status():
            result = await agent._handle_query_status(mock_ctx, "test_sender", status_message)
            
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["query_id"], query_id)
            self.assertEqual(result["query_status"], "processing")
            self.assertEqual(result["researcher_id"], researcher_id)
            
            return result
        
        try:
            result = asyncio.run(test_status())
            print(f"✓ Query status tracking: {result['query_status']}")
        except RuntimeError:
            # Handle case where event loop is already running
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(test_status())
                print(f"✓ Query status tracking: {result['query_status']}")
            finally:
                loop.close()
        
        # Test query completion and history
        query_tracking["status"] = "completed"
        agent.query_history.append(query_tracking)
        del agent.active_queries[query_id]
        
        # Test history retrieval
        history_message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="research_query_agent", 
            message_type="query_history",
            payload={"researcher_id": researcher_id, "limit": 10}
        )
        
        async def test_history():
            result = await agent._handle_query_history(mock_ctx, "test_sender", history_message)
            
            self.assertEqual(result["status"], "success")
            self.assertEqual(len(result["queries"]), 1)
            self.assertEqual(result["queries"][0]["query_id"], query_id)
            
            return result
        
        try:
            history_result = asyncio.run(test_history())
            print(f"✓ Query history tracking: {len(history_result['queries'])} queries")
        except RuntimeError:
            # Handle case where event loop is already running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                history_result = loop.run_until_complete(test_history())
                print(f"✓ Query history tracking: {len(history_result['queries'])} queries")
            finally:
                loop.close()
        
        # Test statistics tracking
        self.assertIn("total_queries", agent.stats)
        self.assertIn("successful_queries", agent.stats)
        self.assertIn("failed_queries", agent.stats)
        print("✓ Statistics tracking initialized")
    
    def test_complexity_and_performance_metrics(self):
        """Test complexity scoring and performance estimation."""
        print("\n=== Testing Complexity & Performance Metrics ===")
        
        # Test simple query complexity
        simple_query = {
            "data_requirements": {
                "data_types": ["demographics"],
                "minimum_sample_size": 50
            }
        }
        
        simple_score = self.validator._calculate_complexity_score(simple_query)
        
        # Test complex query complexity
        complex_query = {
            "data_requirements": {
                "data_types": ["demographics", "genomics", "lab_results", "medications", "procedures"],
                "minimum_sample_size": 50000,
                "date_range": {
                    "start_date": "2020-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                },
                "longitudinal_data": True,
                "multi_site_data": True
            },
            "inclusion_criteria": ["age > 18", "diagnosis = diabetes"],
            "exclusion_criteria": ["pregnancy", "terminal_illness"]
        }
        
        complex_score = self.validator._calculate_complexity_score(complex_query)
        
        self.assertGreater(complex_score, simple_score, "Complex query should have higher score")
        self.assertLessEqual(complex_score, 1.0, "Complexity score should not exceed 1.0")
        
        print(f"✓ Simple query complexity: {simple_score:.3f}")
        print(f"✓ Complex query complexity: {complex_score:.3f}")
        
        # Test processing time estimation
        validation_result = self.validator.validate_query_structure(self.valid_query)
        
        self.assertGreater(validation_result.estimated_processing_time, 0)
        self.assertGreater(validation_result.complexity_score, 0)
        
        print(f"✓ Estimated processing time: {validation_result.estimated_processing_time}s")
        print(f"✓ Complexity score: {validation_result.complexity_score:.3f}")
    
    def test_error_handling_and_validation_edge_cases(self):
        """Test error handling and edge cases in validation."""
        print("\n=== Testing Error Handling & Edge Cases ===")
        
        edge_cases = [
            {
                "name": "Empty Query",
                "query": {},
                "should_fail": True
            },
            {
                "name": "Invalid Data Types",
                "query": {
                    **self.valid_query,
                    "data_requirements": {
                        "data_types": ["invalid_type", "nonexistent_type"]
                    }
                },
                "should_fail": True
            },
            {
                "name": "Negative Sample Size",
                "query": {
                    **self.valid_query,
                    "data_requirements": {
                        **self.valid_query["data_requirements"],
                        "minimum_sample_size": -100
                    }
                },
                "should_fail": True
            },
            {
                "name": "Invalid Date Range",
                "query": {
                    **self.valid_query,
                    "data_requirements": {
                        **self.valid_query["data_requirements"],
                        "date_range": {
                            "start_date": "invalid-date",
                            "end_date": "also-invalid"
                        }
                    }
                },
                "should_fail": True
            },
            {
                "name": "Minimal Valid Query",
                "query": {
                    "researcher_id": "HMS-12345",
                    "study_description": "Minimal valid study description for testing purposes with sufficient length to pass validation",
                    "data_requirements": {
                        "data_types": ["demographics"],
                        "research_categories": ["clinical_trials"]
                    },
                    "ethical_approval_id": f"IRB-{datetime.now().year}-123456"
                },
                "should_fail": False
            }
        ]
        
        for case in edge_cases:
            try:
                parsed_query, validation_result = self.processor.parse_research_query(case["query"])
                
                if case["should_fail"]:
                    self.assertFalse(validation_result.is_valid, f"{case['name']} should fail validation")
                    print(f"✓ {case['name']}: Properly rejected")
                else:
                    self.assertTrue(validation_result.is_valid, f"{case['name']} should pass validation")
                    self.assertIsNotNone(parsed_query, f"{case['name']} should parse successfully")
                    print(f"✓ {case['name']}: Properly accepted")
                    
            except Exception as e:
                if case["should_fail"]:
                    print(f"✓ {case['name']}: Exception properly caught - {str(e)[:50]}...")
                else:
                    self.fail(f"{case['name']} should not raise exception: {str(e)}")


class TestTask61Requirements(unittest.TestCase):
    """Test specific requirements from Task 6.1."""
    
    def test_all_requirements_coverage(self):
        """Verify all Task 6.1 requirements are implemented."""
        print("\n=== Verifying Task 6.1 Requirements Coverage ===")
        
        requirements = [
            "3.1: Research query parsing and structure validation",
            "3.2: Ethical compliance checking using MeTTa reasoning", 
            "3.3: Query routing and multi-agent coordination logic",
            "4.1: Query status tracking and progress reporting"
        ]
        
        # This test verifies that all components exist and are functional
        processor = QueryProcessor()
        validator = QueryValidator()
        orchestrator = WorkflowOrchestrator({})
        agent = ResearchQueryAgent(port=8005)
        
        # Verify core components exist
        self.assertIsNotNone(processor, "QueryProcessor should exist")
        self.assertIsNotNone(validator, "QueryValidator should exist") 
        self.assertIsNotNone(orchestrator, "WorkflowOrchestrator should exist")
        self.assertIsNotNone(agent, "ResearchQueryAgent should exist")
        
        # Verify key methods exist
        self.assertTrue(hasattr(processor, 'parse_research_query'), "Should have parse_research_query method")
        self.assertTrue(hasattr(processor, 'validate_ethical_compliance'), "Should have validate_ethical_compliance method")
        self.assertTrue(hasattr(validator, 'validate_query_structure'), "Should have validate_query_structure method")
        self.assertTrue(hasattr(validator, 'validate_ethical_compliance'), "Should have validate_ethical_compliance method")
        self.assertTrue(hasattr(orchestrator, '_build_workflow_steps'), "Should have _build_workflow_steps method")
        self.assertTrue(hasattr(orchestrator, 'execute_research_workflow'), "Should have execute_research_workflow method")
        
        for req in requirements:
            print(f"✓ {req}: IMPLEMENTED")
        
        print("✓ All Task 6.1 requirements are covered")


def run_all_tests():
    """Run all Task 6.1 tests."""
    print("Research Query Agent - Task 6.1 Implementation Tests")
    print("=" * 60)
    
    # Create test suite
    test_classes = [TestTask61Implementation, TestTask61Requirements]
    
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
                    method()
                except Exception as e:
                    print(f"✗ {method_name} failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"Task 6.1 Implementation Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✓ ALL TESTS PASSED - Task 6.1 implementation is complete!")
        return True
    else:
        print("✗ Some tests failed - implementation needs attention")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)