#!/usr/bin/env python3
"""
Basic performance tests that don't require external dependencies.
Tests core performance optimization functionality.
"""

import asyncio
import time
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock

# Import HealthSync components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.utils.performance_monitor import PerformanceMonitor, PerformanceMetric
from shared.utils.connection_pool import OptimizedDatabase, QueryCache, ConnectionPool, ConnectionConfig
from shared.utils.message_optimizer import MessageProcessor, OptimizedMessage, MessagePriority, CircuitBreaker

class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    @pytest.mark.asyncio
    async def test_metric_recording(self):
        """Test basic metric recording."""
        monitor = PerformanceMonitor(retention_hours=1)
        await monitor.start()
        
        try:
            # Record metrics
            monitor.record_metric("test_metric", 100.0, {"test": "value"})
            monitor.record_metric("test_metric", 200.0, {"test": "value2"})
            
            # Retrieve metrics
            metrics = monitor.get_metrics("test_metric")
            assert len(metrics) == 2
            assert metrics[0].value == 100.0
            assert metrics[1].value == 200.0
            
        finally:
            await monitor.stop()
            
    @pytest.mark.asyncio
    async def test_time_measurement(self):
        """Test time measurement context manager."""
        monitor = PerformanceMonitor()
        await monitor.start()
        
        try:
            # Measure execution time
            with monitor.measure_time("operation_time"):
                await asyncio.sleep(0.01)
                
            # Check recorded metric
            metrics = monitor.get_metrics("operation_time")
            assert len(metrics) == 1
            assert metrics[0].value >= 10.0  # At least 10ms
            
        finally:
            await monitor.stop()
            
    def test_agent_stats_update(self):
        """Test agent statistics updates."""
        monitor = PerformanceMonitor()
        
        # Record agent metrics
        monitor.record_metric("message_response_time", 150.0, {"agent_id": "test_agent"})
        monitor.record_metric("message_response_time", 250.0, {"agent_id": "test_agent"})
        monitor.record_metric("message_error", 1, {"agent_id": "test_agent"})
        
        # Check agent stats
        stats = monitor.get_agent_stats("test_agent")
        assert "test_agent" in stats
        agent_stats = stats["test_agent"]
        
        assert agent_stats.message_count == 2
        assert agent_stats.avg_response_time == 200.0
        assert agent_stats.error_count == 1
        assert agent_stats.success_rate == 50.0  # 1 success out of 2 messages
        
    def test_percentile_calculation(self):
        """Test percentile calculations."""
        monitor = PerformanceMonitor()
        
        # Record test data
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for value in values:
            monitor.record_metric("test_percentiles", value)
            
        # Calculate percentiles
        percentiles = monitor.calculate_percentiles("test_percentiles", [50, 90, 95])
        
        assert percentiles["p50"] == 50.0
        assert percentiles["p90"] == 90.0
        assert percentiles["p95"] == 95.0

class TestConnectionPool:
    """Test database connection pooling."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_basic(self):
        """Test basic connection pool functionality."""
        config = ConnectionConfig(
            database_path=":memory:",
            max_connections=3
        )
        
        pool = ConnectionPool(config)
        await pool.initialize()
        
        try:
            # Test connection acquisition
            async with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
                
        finally:
            await pool.close()
            
    @pytest.mark.asyncio
    async def test_query_execution(self):
        """Test query execution with connection pool."""
        config = ConnectionConfig(
            database_path=":memory:",
            max_connections=2
        )
        
        pool = ConnectionPool(config)
        await pool.initialize()
        
        try:
            # Create table
            await pool.execute_query("""
                CREATE TABLE test (id INTEGER, name TEXT)
            """)
            
            # Insert data
            result = await pool.execute_query(
                "INSERT INTO test (id, name) VALUES (?, ?)",
                (1, "test")
            )
            assert result == 1  # One row affected
            
            # Query data
            result = await pool.execute_query(
                "SELECT * FROM test WHERE id = ?",
                (1,)
            )
            assert len(result) == 1
            assert result[0]["id"] == 1
            assert result[0]["name"] == "test"
            
        finally:
            await pool.close()

class TestQueryCache:
    """Test query caching functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_operations(self):
        """Test basic cache operations."""
        cache = QueryCache(max_size=10, default_ttl=60)
        cache.start()
        
        try:
            # Test cache set/get
            cache.set("SELECT 1", None, {"result": 1})
            result = cache.get("SELECT 1", None)
            assert result == {"result": 1}
            
            # Test cache miss
            result = cache.get("SELECT 2", None)
            assert result is None
            
        finally:
            await cache.stop()
            
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache TTL expiration."""
        cache = QueryCache(max_size=10, default_ttl=1)  # 1 second TTL
        cache.start()
        
        try:
            # Set cache entry
            cache.set("SELECT 1", None, {"result": 1}, ttl=1)
            
            # Should be available immediately
            result = cache.get("SELECT 1", None)
            assert result == {"result": 1}
            
            # Wait for expiration
            await asyncio.sleep(1.1)
            
            # Should be expired
            result = cache.get("SELECT 1", None)
            assert result is None
            
        finally:
            await cache.stop()
            
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = QueryCache(max_size=10)
        
        # Set multiple entries
        cache.set("SELECT * FROM users", None, {"users": []})
        cache.set("SELECT * FROM products", None, {"products": []})
        
        # Invalidate by pattern
        cache.invalidate("users")
        
        # Users query should be gone
        result = cache.get("SELECT * FROM users", None)
        assert result is None
        
        # Products query should remain
        result = cache.get("SELECT * FROM products", None)
        assert result == {"products": []}

class TestOptimizedDatabase:
    """Test optimized database functionality."""
    
    @pytest.mark.asyncio
    async def test_database_with_cache(self):
        """Test database operations with caching."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
            
        try:
            db = OptimizedDatabase(db_path, pool_size=2, cache_size=10)
            await db.start()
            
            # Create test table
            await db.execute_query("""
                CREATE TABLE test_cache (id INTEGER, value TEXT)
            """)
            
            # Insert test data
            await db.execute_query(
                "INSERT INTO test_cache (id, value) VALUES (?, ?)",
                (1, "cached_value")
            )
            
            # First query (should hit database)
            result1 = await db.execute_cached_query(
                "SELECT * FROM test_cache WHERE id = ?",
                (1,),
                cache_ttl=60
            )
            
            # Second query (should hit cache)
            result2 = await db.execute_cached_query(
                "SELECT * FROM test_cache WHERE id = ?",
                (1,),
                cache_ttl=60
            )
            
            # Results should be identical
            assert result1 == result2
            assert len(result1) == 1
            assert result1[0]["value"] == "cached_value"
            
            # Test cache invalidation
            db.invalidate_cache("test_cache")
            
            await db.stop()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

class TestMessageProcessor:
    """Test message processing optimization."""
    
    @pytest.mark.asyncio
    async def test_message_processing(self):
        """Test basic message processing."""
        processor = MessageProcessor(max_workers=2)
        await processor.start()
        
        try:
            processed_messages = []
            
            async def test_handler(message: OptimizedMessage):
                processed_messages.append(message.id)
                
            processor.register_handler("test", test_handler)
            
            # Send test message
            message = OptimizedMessage(
                id="test_msg_1",
                sender="test_sender",
                recipient="test_recipient",
                message_type="test",
                payload={"data": "test"}
            )
            
            success = await processor.send_message(message)
            assert success
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            assert "test_msg_1" in processed_messages
            
        finally:
            await processor.stop()
            
    @pytest.mark.asyncio
    async def test_message_priority(self):
        """Test message priority handling."""
        processor = MessageProcessor(max_workers=1)  # Single worker for predictable order
        await processor.start()
        
        try:
            processed_order = []
            
            async def priority_handler(message: OptimizedMessage):
                processed_order.append(message.id)
                await asyncio.sleep(0.01)  # Small delay
                
            processor.register_handler("priority_test", priority_handler)
            
            # Send messages in reverse priority order
            messages = [
                OptimizedMessage(
                    id="low_priority",
                    sender="test",
                    recipient="test",
                    message_type="priority_test",
                    payload={},
                    priority=MessagePriority.LOW
                ),
                OptimizedMessage(
                    id="high_priority",
                    sender="test",
                    recipient="test",
                    message_type="priority_test",
                    payload={},
                    priority=MessagePriority.HIGH
                ),
                OptimizedMessage(
                    id="critical_priority",
                    sender="test",
                    recipient="test",
                    message_type="priority_test",
                    payload={},
                    priority=MessagePriority.CRITICAL
                )
            ]
            
            # Send in reverse priority order
            for message in messages:
                await processor.send_message(message)
                
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Critical should be processed first
            assert processed_order[0] == "critical_priority"
            
        finally:
            await processor.stop()

class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_states(self):
        """Test circuit breaker state transitions."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        # Initially closed
        assert not breaker.is_open()
        
        # Record failures
        breaker.record_failure()
        breaker.record_failure()
        assert not breaker.is_open()  # Still closed
        
        breaker.record_failure()
        assert breaker.is_open()  # Now open
        
        # Record success should close it
        breaker.record_success()
        assert not breaker.is_open()
        
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Trigger circuit breaker
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open()
        
        # Should still be open immediately
        assert breaker.is_open()
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Should transition to half-open
        assert not breaker.is_open()

# Performance benchmark tests
class TestPerformanceBenchmarks:
    """Test performance benchmarking functionality."""
    
    @pytest.mark.asyncio
    async def test_message_throughput(self):
        """Test message processing throughput."""
        processor = MessageProcessor(max_workers=4)
        await processor.start()
        
        try:
            processed_count = 0
            
            async def throughput_handler(message: OptimizedMessage):
                nonlocal processed_count
                processed_count += 1
                
            processor.register_handler("throughput_test", throughput_handler)
            
            # Send messages and measure time
            message_count = 100
            start_time = time.perf_counter()
            
            for i in range(message_count):
                message = OptimizedMessage(
                    id=f"throughput_{i}",
                    sender="benchmark",
                    recipient="handler",
                    message_type="throughput_test",
                    payload={"index": i}
                )
                await processor.send_message(message)
                
            # Wait for processing
            await asyncio.sleep(0.5)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            throughput = processed_count / duration
            
            print(f"Message throughput: {throughput:.2f} msg/sec")
            
            # Should process at least 50 messages per second
            assert throughput > 50
            assert processed_count >= message_count * 0.9  # Allow some variance
            
        finally:
            await processor.stop()
            
    @pytest.mark.asyncio
    async def test_database_query_performance(self):
        """Test database query performance."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
            
        try:
            db = OptimizedDatabase(db_path, pool_size=5)
            await db.start()
            
            # Create test table with data
            await db.execute_query("""
                CREATE TABLE perf_test (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value INTEGER
                )
            """)
            
            # Insert test data
            for i in range(1000):
                await db.execute_query(
                    "INSERT INTO perf_test (name, value) VALUES (?, ?)",
                    (f"item_{i}", i)
                )
                
            # Measure query performance
            query_count = 100
            start_time = time.perf_counter()
            
            for i in range(query_count):
                result = await db.execute_cached_query(
                    "SELECT * FROM perf_test WHERE value > ? LIMIT 10",
                    (i * 5,)
                )
                assert len(result) <= 10
                
            end_time = time.perf_counter()
            duration = end_time - start_time
            queries_per_second = query_count / duration
            
            print(f"Database query performance: {queries_per_second:.2f} queries/sec")
            
            # Should handle at least 100 queries per second
            assert queries_per_second > 100
            
            await db.stop()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

if __name__ == "__main__":
    # Run tests manually
    async def run_basic_tests():
        print("Running basic performance tests...")
        
        # Test performance monitor
        monitor_test = TestPerformanceMonitor()
        await monitor_test.test_metric_recording()
        await monitor_test.test_time_measurement()
        monitor_test.test_agent_stats_update()
        monitor_test.test_percentile_calculation()
        print("✓ Performance monitor tests passed")
        
        # Test connection pool
        pool_test = TestConnectionPool()
        await pool_test.test_connection_pool_basic()
        await pool_test.test_query_execution()
        print("✓ Connection pool tests passed")
        
        # Test query cache
        cache_test = TestQueryCache()
        await cache_test.test_cache_operations()
        await cache_test.test_cache_expiration()
        cache_test.test_cache_invalidation()
        print("✓ Query cache tests passed")
        
        # Test optimized database
        db_test = TestOptimizedDatabase()
        await db_test.test_database_with_cache()
        print("✓ Optimized database tests passed")
        
        # Test message processor
        msg_test = TestMessageProcessor()
        await msg_test.test_message_processing()
        await msg_test.test_message_priority()
        print("✓ Message processor tests passed")
        
        # Test circuit breaker
        cb_test = TestCircuitBreaker()
        cb_test.test_circuit_breaker_states()
        cb_test.test_circuit_breaker_recovery()
        print("✓ Circuit breaker tests passed")
        
        # Test performance benchmarks
        perf_test = TestPerformanceBenchmarks()
        await perf_test.test_message_throughput()
        await perf_test.test_database_query_performance()
        print("✓ Performance benchmark tests passed")
        
        print("\nAll basic performance tests passed!")
        
    asyncio.run(run_basic_tests())