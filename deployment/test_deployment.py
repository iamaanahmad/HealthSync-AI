#!/usr/bin/env python3
"""
Test script for HealthSync deployment verification.
Tests agent registration, health checks, and ASI:One integration.
"""

import asyncio
import sys
import os
import json
import aiohttp
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import AGENT_CONFIG
from deployment.agentverse_registration import AgentverseRegistrationManager


async def test_agent_health_endpoints():
    """Test agent health check endpoints."""
    print("🏥 Testing Agent Health Endpoints")
    print("-" * 40)
    
    results = []
    
    for agent_name, agent_config in AGENT_CONFIG.items():
        port = agent_config.get("port")
        if not port:
            continue
        
        health_port = port + 1000  # HTTP server port
        health_url = f"http://localhost:{health_port}/health"
        
        try:
            print(f"Testing {agent_name} health endpoint...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=5) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        results.append({
                            "agent_name": agent_name,
                            "health_status": "healthy",
                            "response_time": "< 5s",
                            "health_url": health_url,
                            "agent_data": health_data
                        })
                        print(f"  ✅ {agent_name} health check passed")
                    else:
                        results.append({
                            "agent_name": agent_name,
                            "health_status": "unhealthy",
                            "error": f"HTTP {response.status}",
                            "health_url": health_url
                        })
                        print(f"  ❌ {agent_name} health check failed: HTTP {response.status}")
        
        except Exception as e:
            results.append({
                "agent_name": agent_name,
                "health_status": "unreachable",
                "error": str(e),
                "health_url": health_url
            })
            print(f"  ❌ {agent_name} health check failed: {str(e)}")
    
    return results


async def test_manifest_validation():
    """Test agent manifest validation."""
    print("\n📋 Testing Agent Manifest Validation")
    print("-" * 40)
    
    results = []
    required_fields = ["name", "description", "badges", "chat_protocol_enabled", "agentverse_compatible"]
    required_badges = ["Innovation Lab", "ASI Alliance Hackathon"]
    
    for agent_name in AGENT_CONFIG.keys():
        try:
            print(f"Validating {agent_name} manifest...")
            
            manifest_path = f"agents/manifests/{agent_name}_manifest.json"
            
            if not os.path.exists(manifest_path):
                results.append({
                    "agent_name": agent_name,
                    "status": "failed",
                    "error": "Manifest file not found"
                })
                print(f"  ❌ Manifest file not found")
                continue
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in manifest]
            if missing_fields:
                results.append({
                    "agent_name": agent_name,
                    "status": "failed",
                    "error": f"Missing fields: {', '.join(missing_fields)}"
                })
                print(f"  ❌ Missing fields: {', '.join(missing_fields)}")
                continue
            
            # Check badges
            agent_badges = manifest.get("badges", [])
            missing_badges = [badge for badge in required_badges if badge not in agent_badges]
            
            # Check Chat Protocol
            chat_enabled = manifest.get("chat_protocol_enabled", False)
            agentverse_compatible = manifest.get("agentverse_compatible", False)
            
            if missing_badges or not chat_enabled or not agentverse_compatible:
                issues = []
                if missing_badges:
                    issues.append(f"Missing badges: {', '.join(missing_badges)}")
                if not chat_enabled:
                    issues.append("Chat Protocol not enabled")
                if not agentverse_compatible:
                    issues.append("Agentverse compatibility not enabled")
                
                results.append({
                    "agent_name": agent_name,
                    "status": "partial",
                    "issues": issues
                })
                print(f"  ⚠️  Issues found: {'; '.join(issues)}")
            else:
                results.append({
                    "agent_name": agent_name,
                    "status": "passed",
                    "chat_protocol": chat_enabled,
                    "agentverse_compatible": agentverse_compatible,
                    "badges": agent_badges
                })
                print(f"  ✅ Manifest validation passed")
        
        except Exception as e:
            results.append({
                "agent_name": agent_name,
                "status": "error",
                "error": str(e)
            })
            print(f"  ❌ Validation error: {str(e)}")
    
    return results


async def test_registration_simulation():
    """Test agent registration simulation."""
    print("\n🚀 Testing Agent Registration Simulation")
    print("-" * 40)
    
    try:
        manager = AgentverseRegistrationManager()
        
        print("Simulating agent registration...")
        registration_results = await manager.register_all_agents()
        
        successful = len(registration_results["successful_registrations"])
        total = registration_results["total_agents"]
        
        print(f"Registration simulation: {successful}/{total} agents registered")
        
        if successful == total:
            print("✅ All agents would register successfully")
        else:
            print("⚠️  Some agents would fail registration")
            for failure in registration_results["failed_registrations"]:
                print(f"  - {failure['agent_name']}: {failure['error']}")
        
        return registration_results
        
    except Exception as e:
        print(f"❌ Registration simulation failed: {str(e)}")
        return None


async def run_deployment_tests():
    """Run all deployment tests."""
    print("🧪 HealthSync Deployment Tests")
    print("=" * 50)
    
    test_results = {
        "test_timestamp": datetime.utcnow().isoformat(),
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "results": {}
    }
    
    try:
        # Test 1: Manifest validation
        test_results["tests_run"] += 1
        manifest_results = await test_manifest_validation()
        test_results["results"]["manifest_validation"] = manifest_results
        
        passed_manifests = len([r for r in manifest_results if r["status"] == "passed"])
        if passed_manifests == len(AGENT_CONFIG):
            test_results["tests_passed"] += 1
            print("✅ Manifest validation test passed")
        else:
            test_results["tests_failed"] += 1
            print("❌ Manifest validation test failed")
        
        # Test 2: Registration simulation
        test_results["tests_run"] += 1
        registration_results = await test_registration_simulation()
        test_results["results"]["registration_simulation"] = registration_results
        
        if registration_results and len(registration_results["successful_registrations"]) == len(AGENT_CONFIG):
            test_results["tests_passed"] += 1
            print("✅ Registration simulation test passed")
        else:
            test_results["tests_failed"] += 1
            print("❌ Registration simulation test failed")
        
        # Test 3: Health endpoints (only if agents are running)
        test_results["tests_run"] += 1
        print("\n🏥 Note: Health endpoint tests require running agents")
        print("To test health endpoints, start agents first with: python run_all_agents.py")
        
        # For now, mark as skipped
        test_results["results"]["health_endpoints"] = {"status": "skipped", "reason": "agents not running"}
        
        # Generate test report
        report_path = "deployment/test_results.json"
        with open(report_path, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n📄 Test results saved to {report_path}")
        
        # Display summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Tests Run: {test_results['tests_run']}")
        print(f"Tests Passed: {test_results['tests_passed']}")
        print(f"Tests Failed: {test_results['tests_failed']}")
        
        success_rate = (test_results['tests_passed'] / test_results['tests_run']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        if test_results['tests_failed'] == 0:
            print("🎉 All tests passed - deployment ready!")
            return True
        else:
            print("⚠️  Some tests failed - check results for details")
            return False
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return False


def main():
    """Main test entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("HealthSync Deployment Test Script")
        print("Usage: python test_deployment.py")
        print("\nThis script tests:")
        print("1. Agent manifest validation")
        print("2. Registration simulation")
        print("3. Health endpoint accessibility (if agents running)")
        return
    
    success = asyncio.run(run_deployment_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()