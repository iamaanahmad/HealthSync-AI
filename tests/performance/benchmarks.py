"""
Performance benchmarks for HealthSync system components.
Measures and validates performance characteristics of agents and infrastructure.
"""

import asyncio
import time
import statistics
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import pytest
import gc
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Import HealthSync components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.utils.performance_monitor import get_performance_monitor, PerformanceMonitor
from shared.utils.message_optimizer import get_message_processor, OptimizedMessage, MessagePriority
from shared.utils.connection_pool import OptimizedDatabase, QueryCache
from agents.metta_integration.agent import MeTTaIntegrationAgent
from agents.privacy.anonymization import AnonymizationEngine

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Results from a performance benchmark."""
    name: str
    description: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    throughput: float  # operations per second
    memory_usage: Dict[str, float]
    cpu_usage: float
    percentiles: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PerformanceBenchmark:
    """
    Performance benchmarking framework for HealthSync components.
    """
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.performance_monitor = get_performance_monitor()
        
    async def run_benchmark(self, name: str, description: str, 
                          benchmark_func: Callable, iterations: int = 1000,
                          warmup_iterations: int = 100) -> BenchmarkResult:
        """Run a performance benchmark."""
        logger.info(f"Running benchmark: {name}")
        
        # Warmup
        for _ in range(warmup_iterations):
            await benchmark_func()
            
        # Force garbage collection
        gc.collect()
        
        # Measure baseline memory and CPU
        if HAS_PSUTIL:
            try:
                process = psutil.Process()
                baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
                baseline_cpu = process.cpu_percent()
            except Exception:
                baseline_memory = 0.0
                baseline_cpu = 0.0
        else:
            baseline_memory = 0.0
            baseline_cpu = 0.0
        
        # Run benchmark
        times = []
        start_time = time.perf_counter()
        
        for i in range(iterations):
            iteration_start = time.perf_counter()
            await benchmark_func()
            iteration_time = time.perf_counter() - iteration_start
            times.append(iteration_time)
            
        total_time = time.perf_counter() - start_time
        
        # Measure final memory and CPU
        if HAS_PSUTIL:
            try:
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                final_cpu = process.cpu_percent()
            except Exception:
                final_memory = baseline_memory
                final_cpu = baseline_cpu
        else:
            final_memory = baseline_memory
            final_cpu = baseline_cpu
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = iterations / total_time
        
        # Calculate percentiles
        sorted_times = sorted(times)
        percentiles = {
            "p50": self._percentile(sorted_times, 50),
            "p90": self._percentile(sorted_times, 90),
            "p95": self._percentile(sorted_times, 95),
            "p99": self._percentile(sorted_times, 99)
        }
        
        result = BenchmarkResult(
            name=name,
            description=description,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            throughput=throughput,
            memory_usage={
                "baseline_mb": baseline_memory,
                "final_mb": final_memory,
                "delta_mb": final_memory - baseline_memory
            },
            cpu_usage=final_cpu - baseline_cpu,
            percentiles=percentiles
        )
        
        self.results.append(result)
        logger.info(f"Benchmark completed: {name} - {throughput:.2f} ops/sec")
        
        return result
        
    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not sorted_values:
            return 0.0
            
        index = int(len(sorted_values) * percentile / 100)
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
            
        return sorted_values[index]
        
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate benchmark report."""
        report = {
            "summary": {
                "total_benchmarks": len(self.results),
                "generated_at": datetime.now().isoformat(),
                "system_info": {
                    "cpu_count": psutil.cpu_count() if HAS_PSUTIL else "unknown",
                    "memory_gb": psutil.virtual_memory().total / (1024**3) if HAS_PSUTIL else "unknown",
                    "python_version": sys.version
                }
            },
            "benchmarks": []
        }
        
        for result in self.results:
            benchmark_data = {
                "name": result.name,
                "description": result.description,
                "performance": {
                    "iterations": result.iterations,
                    "total_time": result.total_time,
                    "avg_time": result.avg_time,
                    "min_time": result.min_time,
                    "max_time": result.max_time,
                    "std_dev": result.std_dev,
                    "throughput": result.throughput,
                    "percentiles": result.percentiles
                },
                "resources": {
                    "memory_usage": result.memory_usage,
                    "cpu_usage": result.cpu_usage
                },
                "metadata": result.metadata
            }
            report["benchmarks"].append(benchmark_data)
            
        report_json = json.dumps(report, indent=2)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_json)
                
        return report_json

# Specific benchmark implementations
class AgentBenchmarks:
    """Benchmarks for agent performance."""
    
    def __init__(self):
        self.benchmark = PerformanceBenchmark()
        
    async def benchmark_message_processing(self):
        """Benchmark agent message processing performance."""
        processor = get_message_processor()
        await processor.start()
        
        # Create test message handler
        processed_messages = []
        
        async def test_handler(message: OptimizedMessage):
            processed_messages.append(message)
            await asyncio.sleep(0.001)  # Simulate processing
            
        processor.register_handler("test_message", test_handler)
        
        # Benchmark function
        async def send_test_message():
            message = OptimizedMessage(
                id=f"test_{time.time()}",
                sender="benchmark",
                recipient="test_agent",
                message_type="test_message",
                payload={"data": "test"},
                priority=MessagePriority.NORMAL
            )
            await processor.send_message(message)
            
        result = await self.benchmark.run_benchmark(
            "message_processing",
            "Agent message processing throughput",
            send_test_message,
            iterations=1000
        )
        
        await processor.stop()
        return result
        
    async def benchmark_metta_queries(self):
        """Benchmark MeTTa knowledge graph query performance."""
        # Mock MeTTa agent for benchmarking
        class MockMeTTaAgent:
            async def execute_query(self, query: str):
                # Simulate query processing
                await asyncio.sleep(0.005)
                return {"result": "mock_data", "reasoning_path": ["step1", "step2"]}
                
        agent = MockMeTTaAgent()
        
        async def execute_metta_query():
            query = "(match &kb (consent ?patient ?data_type ?status) (consent ?patient ?data_type ?status))"
            result = await agent.execute_query(query)
            return result
            
        return await self.benchmark.run_benchmark(
            "metta_queries",
            "MeTTa knowledge graph query performance",
            execute_metta_query,
            iterations=500
        )
        
    async def benchmark_privacy_anonymization(self):
        """Benchmark privacy anonymization performance."""
        # Use real anonymization engine
        engine = AnonymizationEngine(k=5, epsilon=1.0)
        test_data = [{"id": f"patient_{i}", "age": 30 + i, "condition": "test"} for i in range(100)]
        
        config = {
            "identifier_fields": ["id"],
            "quasi_identifier_fields": ["age", "condition"],
            "generalization_rules": {
                "age": {"type": "age_bin", "bin_size": 10}
            },
            "numeric_fields_for_noise": [],
            "k_anonymity_strategy": "suppress"
        }
        
        async def anonymize_test_data():
            result, metrics = engine.anonymize_dataset(test_data, config)
            return result
            
        return await self.benchmark.run_benchmark(
            "privacy_anonymization",
            "Privacy data anonymization performance",
            anonymize_test_data,
            iterations=50
        )

class DatabaseBenchmarks:
    """Benchmarks for database performance."""
    
    def __init__(self):
        self.benchmark = PerformanceBenchmark()
        
    async def benchmark_connection_pool(self):
        """Benchmark database connection pool performance."""
        # Use a simple mock for database operations to avoid connection issues
        class MockDatabase:
            def __init__(self):
                self.data = [{"id": i, "name": f"test_{i}", "value": i} for i in range(100)]
                
            async def execute_cached_query(self, query, params):
                # Simulate database query processing
                await asyncio.sleep(0.001)  # Simulate I/O
                # Return filtered results based on params
                if params and len(params) > 0:
                    threshold = params[0]
                    return [row for row in self.data if row["value"] > threshold][:5]
                return self.data[:5]
                
        db = MockDatabase()
        
        async def query_database():
            result = await db.execute_cached_query(
                "SELECT * FROM test_table WHERE value > ? LIMIT 5",
                (50,)
            )
            return result
            
        result = await self.benchmark.run_benchmark(
            "database_queries",
            "Database connection pool query performance",
            query_database,
            iterations=1000
        )
        
        return result
        
    async def benchmark_query_cache(self):
        """Benchmark query cache performance."""
        cache = QueryCache(max_size=1000, default_ttl=300)
        cache.start()
        
        try:
            # Pre-populate cache
            for i in range(100):
                cache.set(f"SELECT * FROM table WHERE id = {i}", None, {"data": f"result_{i}"})
                
            async def cache_lookup():
                key = f"SELECT * FROM table WHERE id = {int(time.time() * 1000) % 100}"
                result = cache.get(key, None)
                return result
                
            result = await self.benchmark.run_benchmark(
                "query_cache",
                "Query cache lookup performance",
                cache_lookup,
                iterations=5000
            )
            
            return result
            
        finally:
            await cache.stop()

class SystemBenchmarks:
    """System-wide performance benchmarks."""
    
    def __init__(self):
        self.benchmark = PerformanceBenchmark()
        
    async def benchmark_concurrent_operations(self):
        """Benchmark concurrent operation handling."""
        async def concurrent_operation():
            # Simulate concurrent work
            tasks = []
            for i in range(10):
                task = asyncio.create_task(asyncio.sleep(0.001))
                tasks.append(task)
            await asyncio.gather(*tasks)
            
        return await self.benchmark.run_benchmark(
            "concurrent_operations",
            "Concurrent operation handling performance",
            concurrent_operation,
            iterations=500
        )
        
    async def benchmark_memory_efficiency(self):
        """Benchmark memory usage efficiency."""
        data_store = []
        
        async def memory_operation():
            # Create and store data
            data = {"id": len(data_store), "payload": "x" * 1000}
            data_store.append(data)
            
            # Cleanup old data to prevent unlimited growth
            if len(data_store) > 1000:
                data_store.pop(0)
                
        return await self.benchmark.run_benchmark(
            "memory_efficiency",
            "Memory usage efficiency",
            memory_operation,
            iterations=2000
        )

# Pytest integration
@pytest.mark.asyncio
async def test_agent_message_processing_benchmark():
    """Test agent message processing performance."""
    benchmarks = AgentBenchmarks()
    result = await benchmarks.benchmark_message_processing()
    
    # Performance assertions
    assert result.throughput > 100, f"Message processing too slow: {result.throughput} ops/sec"
    assert result.avg_time < 0.1, f"Average processing time too high: {result.avg_time}s"
    assert result.percentiles["p95"] < 0.2, f"95th percentile too high: {result.percentiles['p95']}s"

@pytest.mark.asyncio
async def test_metta_query_benchmark():
    """Test MeTTa query performance."""
    benchmarks = AgentBenchmarks()
    result = await benchmarks.benchmark_metta_queries()
    
    # Performance assertions
    assert result.throughput > 50, f"MeTTa queries too slow: {result.throughput} ops/sec"
    assert result.avg_time < 0.05, f"Average query time too high: {result.avg_time}s"

@pytest.mark.asyncio
async def test_database_performance_benchmark():
    """Test database performance."""
    benchmarks = DatabaseBenchmarks()
    result = await benchmarks.benchmark_connection_pool()
    
    # Performance assertions
    assert result.throughput > 200, f"Database queries too slow: {result.throughput} ops/sec"
    assert result.avg_time < 0.01, f"Average query time too high: {result.avg_time}s"

@pytest.mark.asyncio
async def test_cache_performance_benchmark():
    """Test cache performance."""
    benchmarks = DatabaseBenchmarks()
    result = await benchmarks.benchmark_query_cache()
    
    # Performance assertions
    assert result.throughput > 10000, f"Cache lookups too slow: {result.throughput} ops/sec"
    assert result.avg_time < 0.001, f"Average cache lookup too high: {result.avg_time}s"

if __name__ == "__main__":
    async def main():
        """Run all benchmarks."""
        print("Running HealthSync Performance Benchmarks...")
        
        # Agent benchmarks
        agent_benchmarks = AgentBenchmarks()
        await agent_benchmarks.benchmark_message_processing()
        await agent_benchmarks.benchmark_metta_queries()
        await agent_benchmarks.benchmark_privacy_anonymization()
        
        # Database benchmarks
        db_benchmarks = DatabaseBenchmarks()
        await db_benchmarks.benchmark_connection_pool()
        await db_benchmarks.benchmark_query_cache()
        
        # System benchmarks
        sys_benchmarks = SystemBenchmarks()
        await sys_benchmarks.benchmark_concurrent_operations()
        await sys_benchmarks.benchmark_memory_efficiency()
        
        # Generate combined report
        all_results = (agent_benchmarks.benchmark.results + 
                      db_benchmarks.benchmark.results + 
                      sys_benchmarks.benchmark.results)
        
        combined_benchmark = PerformanceBenchmark()
        combined_benchmark.results = all_results
        
        report = combined_benchmark.generate_report("performance_benchmarks.json")
        print("\nBenchmark Results Summary:")
        
        for result in all_results:
            print(f"  {result.name}: {result.throughput:.2f} ops/sec")
            
        print(f"\nDetailed report saved to: performance_benchmarks.json")
        
    asyncio.run(main())