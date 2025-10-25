#!/usr/bin/env python3
"""
Performance test runner for HealthSync system.
Executes comprehensive performance testing including load tests and benchmarks.
"""

import asyncio
import argparse
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from load_testing import LoadTester, LoadTestScenarios, LoadTestConfig
from benchmarks import AgentBenchmarks, DatabaseBenchmarks, SystemBenchmarks
from shared.utils.performance_monitor import get_performance_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """
    Comprehensive performance test suite for HealthSync.
    """
    
    def __init__(self, output_dir: str = "performance_results"):
        self.output_dir = output_dir
        self.results = {}
        self.performance_monitor = get_performance_monitor()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
    async def run_all_tests(self, include_load_tests: bool = True, 
                           include_benchmarks: bool = True,
                           load_test_scenarios: Optional[List[str]] = None) -> Dict:
        """Run all performance tests."""
        logger.info("Starting comprehensive performance test suite")
        
        # Start performance monitoring
        if hasattr(self.performance_monitor, 'start'):
            await self.performance_monitor.start()
        
        try:
            if include_benchmarks:
                await self.run_benchmarks()
                
            if include_load_tests:
                await self.run_load_tests(load_test_scenarios)
                
            # Generate comprehensive report
            report = self.generate_comprehensive_report()
            
            return report
            
        finally:
            if hasattr(self.performance_monitor, 'stop'):
                await self.performance_monitor.stop()
            
    async def run_benchmarks(self):
        """Run all performance benchmarks."""
        logger.info("Running performance benchmarks...")
        
        # Agent benchmarks
        agent_benchmarks = AgentBenchmarks()
        
        logger.info("Running agent message processing benchmark...")
        msg_result = await agent_benchmarks.benchmark_message_processing()
        
        logger.info("Running MeTTa query benchmark...")
        metta_result = await agent_benchmarks.benchmark_metta_queries()
        
        logger.info("Running privacy anonymization benchmark...")
        privacy_result = await agent_benchmarks.benchmark_privacy_anonymization()
        
        # Database benchmarks
        db_benchmarks = DatabaseBenchmarks()
        
        logger.info("Running database connection pool benchmark...")
        db_result = await db_benchmarks.benchmark_connection_pool()
        
        logger.info("Running query cache benchmark...")
        cache_result = await db_benchmarks.benchmark_query_cache()
        
        # System benchmarks
        sys_benchmarks = SystemBenchmarks()
        
        logger.info("Running concurrent operations benchmark...")
        concurrent_result = await sys_benchmarks.benchmark_concurrent_operations()
        
        logger.info("Running memory efficiency benchmark...")
        memory_result = await sys_benchmarks.benchmark_memory_efficiency()
        
        # Collect all benchmark results
        all_benchmark_results = [
            msg_result, metta_result, privacy_result,
            db_result, cache_result, concurrent_result, memory_result
        ]
        
        # Save benchmark results
        benchmark_report = {
            "test_type": "benchmarks",
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "name": result.name,
                    "description": result.description,
                    "throughput": result.throughput,
                    "avg_time": result.avg_time,
                    "percentiles": result.percentiles,
                    "memory_usage": result.memory_usage,
                    "cpu_usage": result.cpu_usage
                }
                for result in all_benchmark_results
            ]
        }
        
        benchmark_file = os.path.join(self.output_dir, "benchmarks.json")
        with open(benchmark_file, 'w') as f:
            json.dump(benchmark_report, f, indent=2)
            
        self.results["benchmarks"] = benchmark_report
        logger.info(f"Benchmark results saved to {benchmark_file}")
        
    async def run_load_tests(self, scenarios: Optional[List[str]] = None):
        """Run load testing scenarios."""
        logger.info("Running load tests...")
        
        tester = LoadTester(self.performance_monitor)
        
        # Define test scenarios
        test_scenarios = {
            "light": LoadTestScenarios.light_load(),
            "moderate": LoadTestScenarios.moderate_load(),
            "heavy": LoadTestScenarios.heavy_load(),
            "stress": LoadTestScenarios.stress_test()
        }
        
        # Filter scenarios if specified
        if scenarios:
            test_scenarios = {k: v for k, v in test_scenarios.items() if k in scenarios}
            
        load_test_results = []
        
        for scenario_name, config in test_scenarios.items():
            logger.info(f"Running {scenario_name} load test...")
            
            try:
                result = await tester.run_load_test(f"{scenario_name}_load", config)
                
                load_test_results.append({
                    "scenario": scenario_name,
                    "config": {
                        "concurrent_users": config.concurrent_users,
                        "test_duration": config.test_duration,
                        "message_rate": config.message_rate,
                        "scenarios": config.scenarios
                    },
                    "results": {
                        "total_requests": result.total_requests,
                        "successful_requests": result.successful_requests,
                        "failed_requests": result.failed_requests,
                        "avg_response_time": result.avg_response_time,
                        "throughput": result.throughput,
                        "error_rate": result.error_rate,
                        "percentiles": result.percentiles
                    }
                })
                
                logger.info(f"{scenario_name} load test completed - "
                           f"Throughput: {result.throughput:.2f} req/s, "
                           f"Error Rate: {result.error_rate:.2f}%")
                
            except Exception as e:
                logger.error(f"Error in {scenario_name} load test: {e}")
                load_test_results.append({
                    "scenario": scenario_name,
                    "error": str(e)
                })
                
        # Save load test results
        load_test_report = {
            "test_type": "load_tests",
            "timestamp": datetime.now().isoformat(),
            "results": load_test_results
        }
        
        load_test_file = os.path.join(self.output_dir, "load_tests.json")
        with open(load_test_file, 'w') as f:
            json.dump(load_test_report, f, indent=2)
            
        self.results["load_tests"] = load_test_report
        logger.info(f"Load test results saved to {load_test_file}")
        
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive performance report."""
        logger.info("Generating comprehensive performance report...")
        
        # Get system metrics
        system_metrics = self.performance_monitor.get_system_metrics()
        agent_stats = self.performance_monitor.get_agent_stats()
        
        report = {
            "test_suite": "HealthSync Performance Tests",
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform
            },
            "system_metrics": system_metrics,
            "agent_statistics": {
                agent_id: {
                    "message_count": stats.message_count,
                    "avg_response_time": stats.avg_response_time,
                    "success_rate": stats.success_rate,
                    "throughput": stats.throughput,
                    "memory_usage": stats.memory_usage,
                    "cpu_usage": stats.cpu_usage
                }
                for agent_id, stats in agent_stats.items()
            },
            "test_results": self.results,
            "performance_summary": self._generate_performance_summary()
        }
        
        # Save comprehensive report
        report_file = os.path.join(self.output_dir, "comprehensive_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Generate human-readable summary
        summary_file = os.path.join(self.output_dir, "performance_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(self._generate_text_summary(report))
            
        logger.info(f"Comprehensive report saved to {report_file}")
        logger.info(f"Performance summary saved to {summary_file}")
        
        return report
        
    def _generate_performance_summary(self) -> Dict:
        """Generate performance summary with pass/fail status."""
        summary = {
            "overall_status": "PASS",
            "benchmark_status": "PASS",
            "load_test_status": "PASS",
            "issues": []
        }
        
        # Check benchmark results
        if "benchmarks" in self.results:
            for result in self.results["benchmarks"]["results"]:
                # Define performance thresholds
                thresholds = {
                    "message_processing": {"min_throughput": 100},
                    "metta_queries": {"min_throughput": 50},
                    "database_queries": {"min_throughput": 200},
                    "query_cache": {"min_throughput": 10000}
                }
                
                if result["name"] in thresholds:
                    threshold = thresholds[result["name"]]
                    if result["throughput"] < threshold["min_throughput"]:
                        summary["benchmark_status"] = "FAIL"
                        summary["issues"].append(
                            f"{result['name']} throughput too low: "
                            f"{result['throughput']:.2f} < {threshold['min_throughput']}"
                        )
                        
        # Check load test results
        if "load_tests" in self.results:
            for result in self.results["load_tests"]["results"]:
                if "error" in result:
                    summary["load_test_status"] = "FAIL"
                    summary["issues"].append(f"Load test {result['scenario']} failed: {result['error']}")
                elif result["results"]["error_rate"] > 10.0:
                    summary["load_test_status"] = "FAIL"
                    summary["issues"].append(
                        f"Load test {result['scenario']} error rate too high: "
                        f"{result['results']['error_rate']:.2f}%"
                    )
                    
        # Set overall status
        if summary["benchmark_status"] == "FAIL" or summary["load_test_status"] == "FAIL":
            summary["overall_status"] = "FAIL"
            
        return summary
        
    def _generate_text_summary(self, report: Dict) -> str:
        """Generate human-readable text summary."""
        lines = []
        lines.append("=" * 60)
        lines.append("HEALTHSYNC PERFORMANCE TEST SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Generated: {report['timestamp']}")
        lines.append(f"Overall Status: {report['performance_summary']['overall_status']}")
        lines.append("")
        
        # System information
        lines.append("SYSTEM INFORMATION")
        lines.append("-" * 30)
        lines.append(f"Python Version: {report['system_info']['python_version']}")
        lines.append(f"Platform: {report['system_info']['platform']}")
        lines.append("")
        
        # System metrics
        if "system_metrics" in report:
            metrics = report["system_metrics"]
            lines.append("SYSTEM METRICS")
            lines.append("-" * 30)
            lines.append(f"Active Agents: {metrics.get('active_agents', 'N/A')}")
            lines.append(f"Total Messages: {metrics.get('total_messages', 'N/A')}")
            lines.append(f"Avg Response Time: {metrics.get('avg_response_time', 'N/A'):.2f}ms")
            lines.append("")
            
        # Benchmark results
        if "benchmarks" in report["test_results"]:
            lines.append("BENCHMARK RESULTS")
            lines.append("-" * 30)
            for result in report["test_results"]["benchmarks"]["results"]:
                lines.append(f"{result['name']}: {result['throughput']:.2f} ops/sec")
            lines.append("")
            
        # Load test results
        if "load_tests" in report["test_results"]:
            lines.append("LOAD TEST RESULTS")
            lines.append("-" * 30)
            for result in report["test_results"]["load_tests"]["results"]:
                if "error" not in result:
                    lines.append(f"{result['scenario']}: "
                               f"{result['results']['throughput']:.2f} req/s, "
                               f"{result['results']['error_rate']:.2f}% errors")
                else:
                    lines.append(f"{result['scenario']}: FAILED - {result['error']}")
            lines.append("")
            
        # Issues
        if report["performance_summary"]["issues"]:
            lines.append("PERFORMANCE ISSUES")
            lines.append("-" * 30)
            for issue in report["performance_summary"]["issues"]:
                lines.append(f"• {issue}")
            lines.append("")
            
        lines.append("=" * 60)
        
        return "\n".join(lines)

async def main():
    """Main entry point for performance testing."""
    parser = argparse.ArgumentParser(description="HealthSync Performance Test Suite")
    parser.add_argument("--benchmarks-only", action="store_true",
                       help="Run only benchmarks, skip load tests")
    parser.add_argument("--load-tests-only", action="store_true",
                       help="Run only load tests, skip benchmarks")
    parser.add_argument("--scenarios", nargs="+", 
                       choices=["light", "moderate", "heavy", "stress"],
                       help="Specific load test scenarios to run")
    parser.add_argument("--output-dir", default="performance_results",
                       help="Output directory for results")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Determine what tests to run
    include_benchmarks = not args.load_tests_only
    include_load_tests = not args.benchmarks_only
    
    # Create test suite
    test_suite = PerformanceTestSuite(args.output_dir)
    
    try:
        # Run tests
        report = await test_suite.run_all_tests(
            include_load_tests=include_load_tests,
            include_benchmarks=include_benchmarks,
            load_test_scenarios=args.scenarios
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {report['performance_summary']['overall_status']}")
        
        if report['performance_summary']['issues']:
            print("\nIssues Found:")
            for issue in report['performance_summary']['issues']:
                print(f"  • {issue}")
        else:
            print("\nAll performance tests passed!")
            
        print(f"\nDetailed results saved to: {args.output_dir}/")
        
        # Exit with appropriate code
        exit_code = 0 if report['performance_summary']['overall_status'] == 'PASS' else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Performance test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())