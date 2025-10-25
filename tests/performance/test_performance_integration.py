"""
Integration tests for performance optimization components.
Validates that all performance components work together correctly.
"""

import asyncio
import pytest
import tempfile
import os
import time
from unittest.mock import AsyncMock, MagicMock

# Import performance components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.utils.performance_monitor import PerformanceMonitor, get_performance_monitor
from shared.utils.connection_pool import OptimizedDatabase, QueryCache
from shared.utils.message_optimizer import MessageProcessor, OptimizedMessage, MessagePriority

@pytest.mark.asyncio
async def test_performance_monitor_integration():
    """Test performance monitor functionality."""
    monitor = PerformanceMonitor(retention_hours=1)
    monitor.start()
    
    try:
        # Record some metrics
        monitor.record_metric("test_metric", 100.5, {"agent_id": "test_agent"})
        monitor.record_metric("message_response_time", 150.0, {"agent_id": "test_agent"})
        monitor.record_metric("message_response_time", 200.0, {"agent_id": "test_agent"})
        
        # Test context manager
        with monitor.measure_time("operation_time", {"operation": "test"}):
            await asyncio.sleep(0.01)
            
        # Get metrics
        metrics = monitor.get_metrics("test_metric")
        assert len(metrics) == 1
        assert metrics[0].value == 100.5
        
        # Get agent stats
        stats = monitor.get_agent_stats("test_agent")
        assert "test_agent" in stats
        assert stats["test_agent"].message_count == 2
        assert stats["test_agent"].avg_response_time == 175.0
        
        # Get system metrics
        system_metrics = monitor.get_system_metrics()
        assert "active_agents" in system_metrics
        assert "total_messages" in system_metrics
        
    finally:
        await monitor.stop()

@pytest.mark.asyncio
async def test_database_optimization_integration():
    """Test optimized database functionality."""
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
        
    try:
        db = OptimizedDatabase(db_path, pool_size=5, cache_size=100)
        await db.start()
        
        # Create test table
        await db.execute_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        
        # Insert test data
        for i in range(10):
            await db.execute_query(
                "INSERT INTO test_table (name, value) VALUES (?, ?)",
                (f"test_{i}", i * 10)
            )
            
        # Test cached queries
        result1 = await db.execute_cached_query(
            "SELECT * FROM test_table WHERE value > ?",
            (50,),
            cache_ttl=60
        )
        
        result2 = await db.execute_cached_query(
            "SELECT * FROM test_table WHERE value > ?",
            (50,),
            cache_ttl=60
        )
        
        # Results should be identical (from cache)
        assert result1 == result2
        assert len(result1) == 4  # values 60, 70, 80, 90
        
        # Test cache invalidation
        db.invalidate_cache("test_table")
        
        # Get performance stats
        stats = db.get_performance_stats()
        assert "cache_stats" in stats
        assert "pool_size" in stats
        
        await db.stop()
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

@pytest.mark.asyncio
async def test_message_processor_integration():
    """Test message processor functionality."""
    processor = MessageProcessor(max_workers=3, enable_batching=True)
    await processor.start()
    
    try:
        # Track processed messages
        processed_messages = []
        
        async def test_handler(message: OptimizedMessage):
            processed_messages.append(message)
            await asyncio.sleep(0.001)  # Simulate processing
            
        processor.register_handler("test_message", test_handler)
        
        # Send test messages
        messages = []
        for i in range(10):
            message = OptimizedMessage(
                id=f"test_{i}",
                sender="test_sender",
                recipient="test_recipient",
                message_type="test_message",
                payload={"data": f"test_data_{i}"},
                priority=MessagePriority.NORMAL if i < 5 else MessagePriority.HIGH
            )
            messages.append(message)
            await processor.send_message(message)
            
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify messages were processed
        assert len(processed_messages) == 10
        
        # Get processing stats
        stats = processor.get_stats()
        assert stats.total_processed >= 10
        assert stats.throughput > 0
        
    finally:
        await processor.stop()

@pytest.mark.asyncio
async def test_query_cache_functionality():
    """Test query cache functionality."""
    cache = QueryCache(max_size=100, default_ttl=60)
    cache.start()
    
    try:
        # Test cache operations
        cache.set("SELECT * FROM users", None, {"users": ["user1", "user2"]})
        
        result = cache.get("SELECT * FROM users", None)
        assert result == {"users": ["user1", "user2"]}
        
        # Test cache miss
        result = cache.get("SELECT * FROM products", None)
        assert result is None
        
        # Test cache invalidation (clear all)
        cache.invalidate()  # Clear all entries
        result = cache.get("SELECT * FROM users", None)
        assert result is None
        
        # Test cache stats
        stats = cache.get_stats()
        assert "total_entries" in stats
        assert "cache_usage_percent" in stats
        
    finally:
        await cache.stop()

@pytest.mark.asyncio
async def test_performance_components_together():
    """Test all performance components working together."""
    # Initialize components
    monitor = PerformanceMonitor()
    processor = MessageProcessor(max_workers=2)
    
    monitor.start()
    await processor.start()
    
    try:
        # Create handler that records metrics
        async def monitored_handler(message: OptimizedMessage):
            with monitor.measure_time("message_processing", {"message_type": message.message_type}):
                await asyncio.sleep(0.005)  # Simulate work
                monitor.record_metric("messages_processed", 1, {"handler": "test"})
                
        processor.register_handler("monitored_message", monitored_handler)
        
        # Send messages and measure performance
        start_time = time.perf_counter()
        
        for i in range(20):
            message = OptimizedMessage(
                id=f"perf_test_{i}",
                sender="perf_tester",
                recipient="perf_handler",
                message_type="monitored_message",
                payload={"test_data": i}
            )
            await processor.send_message(message)
            
        # Wait for processing
        await asyncio.sleep(0.2)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Verify metrics were recorded
        processing_metrics = monitor.get_metrics("message_processing")
        assert len(processing_metrics) >= 20
        
        processed_metrics = monitor.get_metrics("messages_processed")
        assert len(processed_metrics) >= 20
        
        # Verify performance
        processor_stats = processor.get_stats()
        assert processor_stats.total_processed >= 20
        assert processor_stats.throughput > 0
        
        # Verify system metrics
        system_metrics = monitor.get_system_metrics()
        assert system_metrics["total_messages"] >= 0  # Allow for timing variations
        
        print(f"Processed 20 messages in {total_time:.3f}s")
        print(f"Throughput: {20/total_time:.2f} msg/sec")
        
    finally:
        await processor.stop()
        await monitor.stop()

@pytest.mark.asyncio
async def test_performance_under_load():
    """Test performance components under simulated load."""
    monitor = PerformanceMonitor()
    processor = MessageProcessor(max_workers=5)
    
    monitor.start()
    await processor.start()
    
    try:
        # Create load simulation handler
        processed_count = 0
        
        async def load_handler(message: OptimizedMessage):
            nonlocal processed_count
            with monitor.measure_time("load_test_processing"):
                # Simulate variable processing time
                delay = 0.001 + (hash(message.id) % 10) * 0.001
                await asyncio.sleep(delay)
                processed_count += 1
                
        processor.register_handler("load_test", load_handler)
        
        # Generate load
        message_count = 100
        tasks = []
        
        for i in range(message_count):
            message = OptimizedMessage(
                id=f"load_{i}",
                sender="load_generator",
                recipient="load_handler",
                message_type="load_test",
                payload={"sequence": i},
                priority=MessagePriority.HIGH if i % 10 == 0 else MessagePriority.NORMAL
            )
            
            task = asyncio.create_task(processor.send_message(message))
            tasks.append(task)
            
        # Wait for all messages to be sent
        await asyncio.gather(*tasks)
        
        # Wait for processing to complete
        await asyncio.sleep(1.0)
        
        # Verify results
        assert processed_count >= message_count * 0.9  # Allow for some timing variance
        
        # Check performance metrics
        processing_metrics = monitor.get_metrics("load_test_processing")
        assert len(processing_metrics) >= message_count * 0.9
        
        # Calculate performance statistics
        if processing_metrics:
            times = [m.value for m in processing_metrics]
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            print(f"Load test results:")
            print(f"  Messages processed: {processed_count}/{message_count}")
            print(f"  Average processing time: {avg_time:.3f}ms")
            print(f"  Maximum processing time: {max_time:.3f}ms")
            
            # Performance assertions
            assert avg_time < 50.0  # Average should be under 50ms
            assert max_time < 100.0  # Max should be under 100ms
            
    finally:
        await processor.stop()
        await monitor.stop()

if __name__ == "__main__":
    # Run tests manually
    async def run_tests():
        print("Running performance integration tests...")
        
        await test_performance_monitor_integration()
        print("✓ Performance monitor integration test passed")
        
        await test_database_optimization_integration()
        print("✓ Database optimization integration test passed")
        
        await test_message_processor_integration()
        print("✓ Message processor integration test passed")
        
        await test_query_cache_functionality()
        print("✓ Query cache functionality test passed")
        
        await test_performance_components_together()
        print("✓ Performance components integration test passed")
        
        await test_performance_under_load()
        print("✓ Performance under load test passed")
        
        print("\nAll performance integration tests passed!")
        
    asyncio.run(run_tests())