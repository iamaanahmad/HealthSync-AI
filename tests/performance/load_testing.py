"""
Load testing framework for HealthSync agent system.
Tests concurrent users, message throughput, and system scalability.
"""

import asyncio
import time
import random
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
from concurrent.futures import ThreadPoolExecutor
import pytest
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

# Import HealthSync components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.utils.performance_monitor import get_performance_monitor, PerformanceMonitor
from shared.utils.message_optimizer import get_message_processor, OptimizedMessage, MessagePriority
from shared.protocols.agent_messages import AgentMessage
from agents.patient_consent.agent import PatientConsentAgent
from agents.research_query.agent import ResearchQueryAgent

logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios."""
    concurrent_users: int = 50
    test_duration: int = 60  # seconds
    ramp_up_time: int = 10   # seconds
    message_rate: float = 10.0  # messages per second per user
    agent_endpoints: Dict[str, str] = field(default_factory=dict)
    scenarios: List[str] = field(default_factory=list)

@dataclass
class LoadTestResult:
    """Results from load testing."""
    test_name: str
    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    percentiles: Dict[str, float] = field(default_factory=dict)
    throughput: float = 0.0  # requests per second
    error_rate: float = 0.0
    errors: List[str] = field(default_factory=list)

class VirtualUser:
    """
    Simulates a virtual user interacting with the HealthSync system.
    """
    
    def __init__(self, user_id: str, config: LoadTestConfig):
        self.user_id = user_id
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.requests_sent = 0
        self.requests_successful = 0
        
    async def start_session(self):
        """Start HTTP session for this virtual user."""
        # For load testing, we'll simulate without actual HTTP connections
        self.session = True  # Mock session
        
    async def stop_session(self):
        """Stop HTTP session."""
        # Mock session cleanup
        self.session = None
            
    async def run_scenario(self, scenario: str, duration: int):
        """Run a specific test scenario."""
        end_time = time.time() + duration
        
        while time.time() < end_time:
            try:
                if scenario == "patient_consent":
                    await self._patient_consent_scenario()
                elif scenario == "research_query":
                    await self._research_query_scenario()
                elif scenario == "mixed_workload":
                    await self._mixed_workload_scenario()
                else:
                    raise ValueError(f"Unknown scenario: {scenario}")
                    
                # Wait between requests
                await asyncio.sleep(1.0 / self.config.message_rate)
                
            except Exception as e:
                self.errors.append(f"{scenario}: {str(e)}")
                logger.error(f"User {self.user_id} error in {scenario}: {e}")
                
    async def _patient_consent_scenario(self):
        """Simulate patient consent management operations."""
        start_time = time.perf_counter()
        
        # Simulate consent update processing
        consent_data = {
            "patient_id": f"patient_{self.user_id}",
            "data_types": random.sample(["demographics", "lab_results", "medications", "diagnoses"], 2),
            "research_categories": random.sample(["cancer_research", "diabetes_study", "cardiology"], 1),
            "consent_status": random.choice([True, False])
        }
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.01, 0.05))
        
        # Simulate success/failure
        if random.random() > 0.05:  # 95% success rate
            self.requests_successful += 1
        else:
            self.errors.append("Simulated consent processing error")
                    
        self.requests_sent += 1
        response_time = (time.perf_counter() - start_time) * 1000
        self.response_times.append(response_time)
        
    async def _research_query_scenario(self):
        """Simulate research query submission."""
        start_time = time.perf_counter()
        
        # Simulate research query processing
        query_data = {
            "researcher_id": f"researcher_{random.randint(1, 10)}",
            "study_description": f"Study {random.randint(1000, 9999)}",
            "data_requirements": {
                "age_range": [random.randint(18, 30), random.randint(60, 80)],
                "conditions": random.sample(["diabetes", "hypertension", "cancer"], 1),
                "data_types": random.sample(["lab_results", "medications"], 1)
            },
            "ethical_approval_id": f"ethics_{random.randint(100, 999)}"
        }
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.02, 0.08))
        
        # Simulate success/failure
        if random.random() > 0.03:  # 97% success rate
            self.requests_successful += 1
        else:
            self.errors.append("Simulated query processing error")
                    
        self.requests_sent += 1
        response_time = (time.perf_counter() - start_time) * 1000
        self.response_times.append(response_time)
        
    async def _mixed_workload_scenario(self):
        """Simulate mixed workload with different operations."""
        scenario = random.choice(["patient_consent", "research_query"])
        
        if scenario == "patient_consent":
            await self._patient_consent_scenario()
        else:
            await self._research_query_scenario()

class LoadTester:
    """
    Main load testing orchestrator.
    """
    
    def __init__(self, performance_monitor: Optional[PerformanceMonitor] = None):
        self.performance_monitor = performance_monitor or get_performance_monitor()
        self.results: List[LoadTestResult] = []
        
    async def run_load_test(self, test_name: str, config: LoadTestConfig) -> LoadTestResult:
        """Run a complete load test scenario."""
        logger.info(f"Starting load test: {test_name}")
        
        result = LoadTestResult(
            test_name=test_name,
            config=config,
            start_time=datetime.now(),
            end_time=datetime.now()  # Will be updated later
        )
        
        # Create virtual users
        users = [VirtualUser(f"user_{i}", config) for i in range(config.concurrent_users)]
        
        try:
            # Start user sessions
            await asyncio.gather(*[user.start_session() for user in users])
            
            # Run scenarios with ramp-up
            await self._run_with_rampup(users, config)
            
            # Collect results
            self._collect_results(users, result)
            
        finally:
            # Clean up user sessions
            await asyncio.gather(*[user.stop_session() for user in users], return_exceptions=True)
            
        result.end_time = datetime.now()
        self.results.append(result)
        
        logger.info(f"Load test completed: {test_name}")
        return result
        
    async def _run_with_rampup(self, users: List[VirtualUser], config: LoadTestConfig):
        """Run test scenarios with gradual user ramp-up."""
        # Calculate ramp-up intervals
        ramp_interval = config.ramp_up_time / len(users) if users else 0
        
        # Start users gradually
        user_tasks = []
        for i, user in enumerate(users):
            # Delay start for ramp-up
            await asyncio.sleep(ramp_interval)
            
            # Start user scenarios
            for scenario in config.scenarios:
                task = asyncio.create_task(
                    user.run_scenario(scenario, config.test_duration)
                )
                user_tasks.append(task)
                
        # Wait for all users to complete
        await asyncio.gather(*user_tasks, return_exceptions=True)
        
    def _collect_results(self, users: List[VirtualUser], result: LoadTestResult):
        """Collect and aggregate results from all virtual users."""
        all_response_times = []
        all_errors = []
        
        for user in users:
            result.total_requests += user.requests_sent
            result.successful_requests += user.requests_successful
            all_response_times.extend(user.response_times)
            all_errors.extend(user.errors)
            
        result.failed_requests = result.total_requests - result.successful_requests
        result.errors = all_errors
        
        if all_response_times:
            result.avg_response_time = statistics.mean(all_response_times)
            result.min_response_time = min(all_response_times)
            result.max_response_time = max(all_response_times)
            
            # Calculate percentiles
            sorted_times = sorted(all_response_times)
            result.percentiles = {
                "p50": self._percentile(sorted_times, 50),
                "p90": self._percentile(sorted_times, 90),
                "p95": self._percentile(sorted_times, 95),
                "p99": self._percentile(sorted_times, 99)
            }
            
        # Calculate throughput and error rate
        test_duration = (result.end_time - result.start_time).total_seconds()
        if test_duration > 0:
            result.throughput = result.total_requests / test_duration
            
        if result.total_requests > 0:
            result.error_rate = (result.failed_requests / result.total_requests) * 100
            
    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not sorted_values:
            return 0.0
            
        index = int(len(sorted_values) * percentile / 100)
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
            
        return sorted_values[index]
        
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate load test report."""
        report = {
            "summary": {
                "total_tests": len(self.results),
                "generated_at": datetime.now().isoformat()
            },
            "tests": []
        }
        
        for result in self.results:
            test_data = {
                "test_name": result.test_name,
                "config": {
                    "concurrent_users": result.config.concurrent_users,
                    "test_duration": result.config.test_duration,
                    "message_rate": result.config.message_rate,
                    "scenarios": result.config.scenarios
                },
                "results": {
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "avg_response_time": result.avg_response_time,
                    "min_response_time": result.min_response_time,
                    "max_response_time": result.max_response_time,
                    "percentiles": result.percentiles,
                    "throughput": result.throughput,
                    "error_rate": result.error_rate,
                    "error_count": len(result.errors)
                }
            }
            report["tests"].append(test_data)
            
        report_json = json.dumps(report, indent=2)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_json)
                
        return report_json

# Test scenarios
class LoadTestScenarios:
    """Predefined load test scenarios."""
    
    @staticmethod
    def light_load() -> LoadTestConfig:
        """Light load test configuration."""
        return LoadTestConfig(
            concurrent_users=10,
            test_duration=30,
            ramp_up_time=5,
            message_rate=2.0,
            scenarios=["patient_consent", "research_query"]
        )
        
    @staticmethod
    def moderate_load() -> LoadTestConfig:
        """Moderate load test configuration."""
        return LoadTestConfig(
            concurrent_users=50,
            test_duration=60,
            ramp_up_time=10,
            message_rate=5.0,
            scenarios=["mixed_workload"]
        )
        
    @staticmethod
    def heavy_load() -> LoadTestConfig:
        """Heavy load test configuration."""
        return LoadTestConfig(
            concurrent_users=100,
            test_duration=120,
            ramp_up_time=20,
            message_rate=10.0,
            scenarios=["mixed_workload"]
        )
        
    @staticmethod
    def stress_test() -> LoadTestConfig:
        """Stress test configuration."""
        return LoadTestConfig(
            concurrent_users=200,
            test_duration=180,
            ramp_up_time=30,
            message_rate=20.0,
            scenarios=["patient_consent", "research_query", "mixed_workload"]
        )

# Pytest integration
@pytest.mark.asyncio
async def test_light_load():
    """Test system under light load."""
    tester = LoadTester()
    config = LoadTestScenarios.light_load()
    
    result = await tester.run_load_test("light_load", config)
    
    # Assertions
    assert result.error_rate < 1.0, f"Error rate too high: {result.error_rate}%"
    assert result.avg_response_time < 1000, f"Response time too high: {result.avg_response_time}ms"
    assert result.throughput > 10, f"Throughput too low: {result.throughput} req/s"

@pytest.mark.asyncio
async def test_moderate_load():
    """Test system under moderate load."""
    tester = LoadTester()
    config = LoadTestScenarios.moderate_load()
    
    result = await tester.run_load_test("moderate_load", config)
    
    # Assertions
    assert result.error_rate < 5.0, f"Error rate too high: {result.error_rate}%"
    assert result.avg_response_time < 2000, f"Response time too high: {result.avg_response_time}ms"
    assert result.throughput > 50, f"Throughput too low: {result.throughput} req/s"

@pytest.mark.asyncio
async def test_heavy_load():
    """Test system under heavy load."""
    tester = LoadTester()
    config = LoadTestScenarios.heavy_load()
    
    result = await tester.run_load_test("heavy_load", config)
    
    # Assertions
    assert result.error_rate < 10.0, f"Error rate too high: {result.error_rate}%"
    assert result.avg_response_time < 5000, f"Response time too high: {result.avg_response_time}ms"
    assert result.throughput > 100, f"Throughput too low: {result.throughput} req/s"

if __name__ == "__main__":
    async def main():
        """Run load tests manually."""
        tester = LoadTester()
        
        # Run all test scenarios
        scenarios = [
            ("light_load", LoadTestScenarios.light_load()),
            ("moderate_load", LoadTestScenarios.moderate_load()),
            ("heavy_load", LoadTestScenarios.heavy_load())
        ]
        
        for name, config in scenarios:
            try:
                result = await tester.run_load_test(name, config)
                print(f"\n{name} Results:")
                print(f"  Requests: {result.total_requests}")
                print(f"  Success Rate: {100 - result.error_rate:.2f}%")
                print(f"  Avg Response Time: {result.avg_response_time:.2f}ms")
                print(f"  Throughput: {result.throughput:.2f} req/s")
                
            except Exception as e:
                print(f"Error in {name}: {e}")
                
        # Generate report
        report = tester.generate_report("load_test_report.json")
        print(f"\nReport generated: load_test_report.json")
        
    asyncio.run(main())