"""
Database connection pooling and query optimization for HealthSync agents.
Provides efficient database connections and query caching.
"""

import asyncio
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
import hashlib
from contextlib import asynccontextmanager
import sqlite3
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class ConnectionConfig:
    """Database connection configuration."""
    database_path: str
    max_connections: int = 10
    connection_timeout: int = 30
    query_timeout: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0

@dataclass
class CacheEntry:
    """Cache entry with expiration and metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = None

class ConnectionPool:
    """
    Thread-safe database connection pool with automatic connection management.
    """
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connections: List[sqlite3.Connection] = []
        self._available_connections: asyncio.Queue = asyncio.Queue(maxsize=config.max_connections)
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=config.max_connections)
        self._initialized = False
        
    async def initialize(self):
        """Initialize the connection pool."""
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            # Create initial connections
            for _ in range(self.config.max_connections):
                conn = self._create_connection()
                self._connections.append(conn)
                await self._available_connections.put(conn)
                
            self._initialized = True
            logger.info(f"Connection pool initialized with {self.config.max_connections} connections")
            
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(
            self.config.database_path,
            timeout=self.config.connection_timeout,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        return conn
        
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self._initialized:
            await self.initialize()
            
        # Get connection with timeout
        try:
            conn = await asyncio.wait_for(
                self._available_connections.get(),
                timeout=self.config.connection_timeout
            )
        except asyncio.TimeoutError:
            raise Exception("Connection pool timeout - no available connections")
            
        try:
            # Verify connection is still valid
            conn.execute("SELECT 1")
            yield conn
        except sqlite3.Error as e:
            logger.warning(f"Connection error, creating new connection: {e}")
            # Create new connection if current one is broken
            conn.close()
            conn = self._create_connection()
            yield conn
        finally:
            # Return connection to pool
            await self._available_connections.put(conn)
            
    async def execute_query(self, query: str, params: Optional[tuple] = None, fetch_one: bool = False) -> Any:
        """Execute a query with connection pooling and error handling."""
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.get_connection() as conn:
                    # Execute query in thread pool to avoid blocking
                    result = await asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        self._execute_query_sync,
                        conn, query, params, fetch_one
                    )
                    return result
                    
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    logger.error(f"Query failed after {self.config.retry_attempts} attempts: {e}")
                    raise
                else:
                    logger.warning(f"Query attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    
    def _execute_query_sync(self, conn: sqlite3.Connection, query: str, params: Optional[tuple], fetch_one: bool) -> Any:
        """Execute query synchronously in thread pool."""
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if query.strip().upper().startswith('SELECT'):
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            else:
                results = cursor.fetchall()
                return [dict(row) for row in results]
        else:
            conn.commit()
            return cursor.rowcount
            
    async def close(self):
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
                    
            self._connections.clear()
            self._executor.shutdown(wait=True)
            logger.info("Connection pool closed")

class QueryCache:
    """
    In-memory cache for database query results with TTL and LRU eviction.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._cleanup_task = None
        self._running = False
        
    def start(self):
        """Start the cache cleanup task."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired())
        logger.info("Query cache started")
        
    async def stop(self):
        """Stop the cache and cleanup task."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Query cache stopped")
        
    def _generate_key(self, query: str, params: Optional[tuple] = None) -> str:
        """Generate cache key from query and parameters."""
        key_data = f"{query}:{params or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
        
    def get(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:
        """Get cached query result."""
        key = self._generate_key(query, params)
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
                
            # Check if expired
            if datetime.now() > entry.expires_at:
                del self._cache[key]
                return None
                
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            return entry.value
            
    def set(self, query: str, params: Optional[tuple], value: Any, ttl: Optional[int] = None) -> None:
        """Cache query result with TTL."""
        key = self._generate_key(query, params)
        ttl = ttl or self.default_ttl
        
        with self._lock:
            # Evict oldest entries if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
                
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl),
                last_accessed=datetime.now()
            )
            
            self._cache[key] = entry
            
    def _evict_lru(self):
        """Evict least recently used entries."""
        if not self._cache:
            return
            
        # Find entries to evict (10% of cache size)
        evict_count = max(1, len(self._cache) // 10)
        
        # Sort by last accessed time
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed or x[1].created_at
        )
        
        for i in range(evict_count):
            key, _ = sorted_entries[i]
            del self._cache[key]
            
    def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern."""
        with self._lock:
            if pattern is None:
                self._cache.clear()
            else:
                keys_to_remove = [
                    key for key in self._cache.keys()
                    if pattern in key
                ]
                for key in keys_to_remove:
                    del self._cache[key]
                    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            
            return {
                'total_entries': total_entries,
                'max_size': self.max_size,
                'cache_usage_percent': (total_entries / self.max_size) * 100,
                'total_accesses': total_accesses,
                'avg_accesses_per_entry': total_accesses / total_entries if total_entries > 0 else 0
            }
            
    async def _cleanup_expired(self):
        """Periodically remove expired cache entries."""
        while self._running:
            try:
                now = datetime.now()
                
                with self._lock:
                    expired_keys = [
                        key for key, entry in self._cache.items()
                        if now > entry.expires_at
                    ]
                    
                    for key in expired_keys:
                        del self._cache[key]
                        
                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                        
                await asyncio.sleep(60)  # Cleanup every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during cache cleanup: {e}")
                await asyncio.sleep(30)

class OptimizedDatabase:
    """
    High-performance database interface with connection pooling and caching.
    """
    
    def __init__(self, database_path: str, pool_size: int = 10, cache_size: int = 1000):
        self.connection_pool = ConnectionPool(ConnectionConfig(
            database_path=database_path,
            max_connections=pool_size
        ))
        self.query_cache = QueryCache(max_size=cache_size)
        
    async def start(self):
        """Start the database system."""
        await self.connection_pool.initialize()
        self.query_cache.start()
        logger.info("Optimized database started")
        
    async def stop(self):
        """Stop the database system."""
        await self.connection_pool.close()
        await self.query_cache.stop()
        logger.info("Optimized database stopped")
        
    async def execute_cached_query(self, query: str, params: Optional[tuple] = None, 
                                 cache_ttl: Optional[int] = None, force_refresh: bool = False) -> Any:
        """Execute query with caching support."""
        # Check cache first (unless force refresh)
        if not force_refresh and query.strip().upper().startswith('SELECT'):
            cached_result = self.query_cache.get(query, params)
            if cached_result is not None:
                return cached_result
                
        # Execute query
        result = await self.connection_pool.execute_query(query, params)
        
        # Cache SELECT results
        if query.strip().upper().startswith('SELECT') and result is not None:
            self.query_cache.set(query, params, result, cache_ttl)
            
        return result
        
    async def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute query without caching."""
        return await self.connection_pool.execute_query(query, params)
        
    def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cached queries."""
        self.query_cache.invalidate(pattern)
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        return {
            'cache_stats': self.query_cache.get_stats(),
            'pool_size': self.connection_pool.config.max_connections,
            'active_connections': len(self.connection_pool._connections)
        }

# Global database instance
_global_db: Optional[OptimizedDatabase] = None

def get_database(database_path: str = "healthsync.db") -> OptimizedDatabase:
    """Get or create global database instance."""
    global _global_db
    if _global_db is None:
        _global_db = OptimizedDatabase(database_path)
    return _global_db