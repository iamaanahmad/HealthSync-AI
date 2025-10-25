#!/usr/bin/env python3
"""
Simple test to validate performance components are working.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from benchmarks import AgentBenchmarks, DatabaseBenchmarks, SystemBenchmarks

async def main():
    print("Testing performance components...")
    
    try:
        # Test agent benchmarks
        print("1. Testing agent benchmarks...")
        agent_benchmarks = AgentBenchmarks()
        
        result = await agent_benchmarks.benchmark_message_processing()
        print(f"   Message processing: {result.throughput:.2f} ops/sec")
        
        result = await agent_benchmarks.benchmark_metta_queries()
        print(f"   MeTTa queries: {result.throughput:.2f} ops/sec")
        
        result = await agent_benchmarks.benchmark_privacy_anonymization()
        print(f"   Privacy anonymization: {result.throughput:.2f} ops/sec")
        
        # Test database benchmarks
        print("2. Testing database benchmarks...")
        db_benchmarks = DatabaseBenchmarks()
        
        result = await db_benchmarks.benchmark_connection_pool()
        print(f"   Database queries: {result.throughput:.2f} ops/sec")
        
        result = await db_benchmarks.benchmark_query_cache()
        print(f"   Query cache: {result.throughput:.2f} ops/sec")
        
        # Test system benchmarks
        print("3. Testing system benchmarks...")
        sys_benchmarks = SystemBenchmarks()
        
        result = await sys_benchmarks.benchmark_concurrent_operations()
        print(f"   Concurrent operations: {result.throughput:.2f} ops/sec")
        
        result = await sys_benchmarks.benchmark_memory_efficiency()
        print(f"   Memory efficiency: {result.throughput:.2f} ops/sec")
        
        print("\nAll performance tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())