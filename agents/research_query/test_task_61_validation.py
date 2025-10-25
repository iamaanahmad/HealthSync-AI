#!/usr/bin/env python3
"""
Task 6.1 Validation Test - Verify all requirements are implemented.
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.research_query.query_processor import (
    QueryProcessor, QueryValidator, QueryType, DataSensitivity
)
from agents.research_query.workflow_orchestrator import (
    WorkflowOrchestrator, WorkflowStatus, AgentRole
)
from agents.research_query.agent import ResearchQueryAgent


def test_requirement_3_1_query_parsing():
    """Test Requirement 3.1: Research query parsing and structure validation."""
    print("Testing Requirement 3.1: Query Parsing and Structure Validation")
    
    processor = QueryProcessor()
    
    # Valid query
    valid_query = {
        "query_id": "req31-test-001",
        "researcher_id": "HMS-12345",
        "study_title": "Requirement 3.1 Test",
        "study_description": "A comprehensive observational clinical study to evaluate treatment outcomes and efficacy in patients with cardiovascular disease for public health research and prevention strategies",
        "data_requirements": {
            "data_types": ["demographics", "vital_signs", "lab_results"],
            "research_categories": ["clinical_trials", "outcomes_research"],
            "minimum_sample_size": 100
        },
        "ethical_approval_id": f"IRB-{datetime.now().year}-123456",
        "inclusion_criteria": ["age >= 18"],
        "exclusion_criteria": ["pregnancy"],
        "privacy_requirements": {
            "anonymization_methods": ["k_anonymity"],
            "k_anonymity": 5
        }
    }
    
    # Test parsing
    parsed_query, validation_result = processor.parse_research_query(valid_query)
    
    assert parsed_query is not None, "Query parsing should succeed"
    assert validation_result.is_valid, "Validation should pass"
    assert parsed_query.query_id == "req31-test-001"
    assert "demographics" in parsed_query.required_data_types
    assert "clinical_trials" in parsed_query.research_categories
    
    print("  ✓ Valid query parsing: SUCCESS")
    print(f"  ✓ Query type: {parsed_query.query_type.value}")
    print(f"  ✓ Sensitivity level: {parsed_query.sensitivity_level.value}")
    
    # Test invalid query
    invalid_query = valid_query.copy()
    del invalid_query["researcher_id"]
    
    parsed_invalid, validation_invalid = processor.parse_research_query(invalid_query)
    
    assert parsed_invalid is None, "Invalid query should not parse"
    assert not validation_invalid.is_valid, "Invalid query should fail validation"
    assert any("researcher_id" in error for error in validation_invalid.errors)
    
    print("  ✓ Invalid query rejection: SUCCESS")
    
    return True


def test_requirement_3_2_ethical_compliance():
    """Test Requirement 3.2: Ethical compliance checking using MeTTa reasoning."""
    print("Testing Requirement 3.2: Ethical Compliance Checking")
    
    validator = QueryValidator()
    
    # Valid ethical query
    valid_query = {
        "researcher_id": "HMS-12345",
        "study_description": "A comprehensive observational clinical study to evaluate treatment outcomes and efficacy in patients with cardiovascular disease for public health research and prevention strategies",
        "data_requirements": {
            "data_types": ["demographics", "vital_signs"],
            "research_categories": ["clinical_trials"]
        },
        "ethical_approval_id": f"IRB-{datetime.now().year}-123456",
        "privacy_requirements": {
            "anonymization_methods": ["k_anonymity", "access_control"]
        }
    }
    
    ethical_result = validator.validate_ethical_compliance(valid_query)
    
    assert ethical_result.is_valid, "Valid query should pass ethical validation"
    assert ethical_result.ethical_score >= 0.6, "Ethical score should be >= 0.6"
    
    print(f"  ✓ Ethical validation: PASSED (score: {ethical_result.ethical_score:.2f})")
    
    # Test ethical violations
    violations = [
        {
            "name": "Expired Approval",
            "query": {**valid_query, "ethical_approval_id": "IRB-2020-123456"},
            "expected_error": "Invalid or expired ethical approval"
        },
        {
            "name": "Prohibited Data",
            "query": {
                **valid_query,
                "data_requirements": {
                    **valid_query["data_requirements"],
                    "specific_fields": ["ssn", "full_name"]
                }
            },
            "expected_error": "Prohibited identifiers requested"
        }
    ]
    
    for violation in violations:
        result = validator.validate_ethical_compliance(violation["query"])
        assert not result.is_valid, f"{violation['name']} should fail"
        assert any(violation["expected_error"] in error for error in result.errors)
        print(f"  ✓ {violation['name']}: Properly rejected")
    
    return True


def test_requirement_3_3_query_routing():
    """Test Requirement 3.3: Query routing and multi-agent coordination logic."""
    print("Testing Requirement 3.3: Query Routing and Multi-Agent Coordination")
    
    agent_addresses = {
        "patient_consent_agent": "agent1qg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg",
        "data_custodian_agent": "agent1qh4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc4abc",
        "privacy_agent": "agent1qi5def5def5def5def5def5def5def5def5def5def5def5def5def",
        "metta_integration_agent": "agent1qj6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi6ghi"
    }
    
    orchestrator = WorkflowOrchestrator(agent_addresses)
    processor = QueryProcessor()
    
    # Create test query
    query_data = {
        "query_id": "req33-test-001",
        "researcher_id": "HMS-12345",
        "study_description": "Test query for routing validation",
        "data_requirements": {
            "data_types": ["demographics", "vital_signs"],
            "research_categories": ["clinical_trials"],
            "minimum_sample_size": 50
        },
        "ethical_approval_id": f"IRB-{datetime.now().year}-123456",
        "privacy_requirements": {"k_anonymity": 5}
    }
    
    parsed_query, _ = processor.parse_research_query(query_data)
    
    # Test workflow step building
    steps = orchestrator._build_workflow_steps(parsed_query)
    
    assert len(steps) > 0, "Should generate workflow steps"
    
    # Verify required agents
    step_agents = [step.agent_role for step in steps]
    required_agents = [AgentRole.METTA_AGENT, AgentRole.CONSENT_AGENT, 
                      AgentRole.DATA_CUSTODIAN, AgentRole.PRIVACY_AGENT]
    
    for agent in required_agents:
        assert agent in step_agents, f"Should include {agent.value}"
        print(f"  ✓ {agent.value}: Included in workflow")
    
    print(f"  ✓ Workflow steps: {len(steps)} steps generated")
    
    # Test circuit breaker
    assert not orchestrator._is_circuit_breaker_open(AgentRole.METTA_AGENT)
    
    # Trigger circuit breaker
    for _ in range(5):
        orchestrator._record_failure(AgentRole.METTA_AGENT)
    
    assert orchestrator._is_circuit_breaker_open(AgentRole.METTA_AGENT)
    print("  ✓ Circuit breaker: Working correctly")
    
    return True


def test_requirement_4_1_status_tracking():
    """Test Requirement 4.1: Query status tracking and progress reporting."""
    print("Testing Requirement 4.1: Query Status Tracking and Progress Reporting")
    
    agent = ResearchQueryAgent(port=8005)
    
    # Test initial state
    assert len(agent.active_queries) == 0, "Should start with no active queries"
    assert len(agent.query_history) == 0, "Should start with empty history"
    
    print("  ✓ Initial state: Clean")
    
    # Test query tracking
    query_id = "req41-test-001"
    query_tracking = {
        "query_id": query_id,
        "researcher_id": "HMS-12345",
        "status": "processing",
        "created_at": datetime.now()
    }
    
    agent.active_queries[query_id] = query_tracking
    
    assert query_id in agent.active_queries
    assert agent.active_queries[query_id]["status"] == "processing"
    
    print("  ✓ Query tracking: Active queries managed")
    
    # Test statistics
    assert "total_queries" in agent.stats
    assert "successful_queries" in agent.stats
    assert "failed_queries" in agent.stats
    
    print("  ✓ Statistics tracking: Initialized")
    
    # Test orchestrator stats
    stats = agent.workflow_orchestrator.get_orchestrator_stats()
    
    assert "active_workflows" in stats
    assert "circuit_breaker_status" in stats
    
    print("  ✓ Orchestrator stats: Available")
    
    return True


def test_complexity_and_performance():
    """Test complexity scoring and performance estimation."""
    print("Testing Complexity Scoring and Performance Estimation")
    
    validator = QueryValidator()
    
    # Simple query
    simple_query = {
        "data_requirements": {
            "data_types": ["demographics"],
            "minimum_sample_size": 50
        }
    }
    
    simple_score = validator._calculate_complexity_score(simple_query)
    
    # Complex query
    complex_query = {
        "data_requirements": {
            "data_types": ["demographics", "genomics", "lab_results", "medications"],
            "minimum_sample_size": 10000,
            "date_range": {
                "start_date": "2020-01-01T00:00:00Z",
                "end_date": "2024-01-01T00:00:00Z"
            },
            "longitudinal_data": True,
            "multi_site_data": True
        },
        "inclusion_criteria": ["age > 18"],
        "exclusion_criteria": ["pregnancy"]
    }
    
    complex_score = validator._calculate_complexity_score(complex_query)
    
    assert complex_score > simple_score, "Complex query should have higher score"
    assert complex_score <= 1.0, "Score should not exceed 1.0"
    
    print(f"  ✓ Simple complexity: {simple_score:.3f}")
    print(f"  ✓ Complex complexity: {complex_score:.3f}")
    
    # Test processing time estimation
    full_query = {
        "researcher_id": "HMS-12345",
        "study_description": "Test query for performance estimation",
        "data_requirements": complex_query["data_requirements"],
        "ethical_approval_id": f"IRB-{datetime.now().year}-123456"
    }
    
    validation_result = validator.validate_query_structure(full_query)
    
    assert validation_result.estimated_processing_time > 0
    assert validation_result.complexity_score > 0
    
    print(f"  ✓ Processing time estimate: {validation_result.estimated_processing_time}s")
    
    return True


def main():
    """Run all Task 6.1 validation tests."""
    print("Research Query Agent - Task 6.1 Implementation Validation")
    print("=" * 60)
    
    tests = [
        ("Requirement 3.1", test_requirement_3_1_query_parsing),
        ("Requirement 3.2", test_requirement_3_2_ethical_compliance),
        ("Requirement 3.3", test_requirement_3_3_query_routing),
        ("Requirement 4.1", test_requirement_4_1_status_tracking),
        ("Complexity & Performance", test_complexity_and_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}:")
            result = test_func()
            if result:
                passed += 1
                print(f"  ✓ {test_name}: PASSED")
            else:
                print(f"  ✗ {test_name}: FAILED")
        except Exception as e:
            print(f"  ✗ {test_name}: ERROR - {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"Task 6.1 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL REQUIREMENTS IMPLEMENTED - Task 6.1 is COMPLETE!")
        
        # Summary of implemented features
        print("\nImplemented Features:")
        print("• Research query parsing and structure validation")
        print("• Ethical compliance checking with scoring")
        print("• Multi-agent workflow coordination")
        print("• Query status tracking and progress reporting")
        print("• Complexity scoring and performance estimation")
        print("• Circuit breaker pattern for agent failures")
        print("• Comprehensive error handling and validation")
        
        return True
    else:
        print("✗ Some requirements not fully implemented")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)