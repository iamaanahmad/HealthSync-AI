#!/usr/bin/env python3
"""
Test runner for Research Query Agent integration tests.
"""

import asyncio
import sys
import os
import unittest
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.research_query.test_workflow_integration import (
    TestWorkflowOrchestrator,
    TestResearchQueryAgentIntegration,
    TestEndToEndWorkflow
)


async def run_async_test_method(test_instance, method_name):
    """Run a single async test method."""
    try:
        method = getattr(test_instance, method_name)
        if asyncio.iscoroutinefunction(method):
            await method()
            print(f"✓ {test_instance.__class__.__name__}.{method_name}")
            return True
        else:
            method()
            print(f"✓ {test_instance.__class__.__name__}.{method_name}")
            return True
    except Exception as e:
        print(f"✗ {test_instance.__class__.__name__}.{method_name}: {str(e)}")
        return False


async def run_test_class(test_class):
    """Run all test methods in a test class."""
    print(f"\nRunning {test_class.__name__}:")
    print("-" * 50)
    
    test_instance = test_class()
    if hasattr(test_instance, 'setUp'):
        test_instance.setUp()
    
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        success = await run_async_test_method(test_instance, method_name)
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return passed, failed


async def main():
    """Run all integration tests."""
    print("Research Query Agent Integration Tests")
    print("=" * 50)
    
    test_classes = [
        TestWorkflowOrchestrator,
        TestResearchQueryAgentIntegration,
        TestEndToEndWorkflow
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_class in test_classes:
        passed, failed = await run_test_class(test_class)
        total_passed += passed
        total_failed += failed
    
    print("\n" + "=" * 50)
    print(f"TOTAL RESULTS: {total_passed} passed, {total_failed} failed")
    
    if total_failed > 0:
        sys.exit(1)
    else:
        print("All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())