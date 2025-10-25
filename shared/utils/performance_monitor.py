"""
Performance monitoring and metrics collection for HealthSync agents.
Provides real-time performance tracking, metrics aggregation, and alerting.
"""

import time
import asyncio
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import logging
from contextlib import contextmanager
import statistics
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = "ms"

@dataclass
class AgentPerformanceStats:
    """Aggregated performance statistics for an agent."""
    agent_id: str
    message_count: int = 0
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    error_count: int = 0
    success_rate: float = 100.0
    throughput: float = 0.0  # messages per second
    memory_usage: float = 0.0  # MB
    cpu_usage: float = 0.0  # percentage
    last_updated: datetime = field(default_factory=datetime.now)

class PerformanceMonitor:
    """
    Centralized performance monitoring system for HealthSync agents.
    Collects metrics, calculates statistics, and provides alerting.
    """
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.agent_stats: Dict[str, AgentPerformanceStats] = {}
        self.alert_thresholds = {
            'response_time': 5000,  # 5 seconds
            'error_rate': 5.0,      # 5%
            'memory_usage': 1024,   # 1GB
            'cpu_usage': 80.0       # 80%
        }
        self.alert_callbacks: List[Callable] = []
        self._lock = threading.Lock()
        self._running = False
        self._cleanup_task = None
        
    def start(self):
        """Start the performance monitoring system."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_old_metrics())
        logger.info("Performance monitor started")
        
    async def stop(self):
        """Stop the performance monitoring system."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitor stopped")
        
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: str = "ms"):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            unit=unit
        )
        
        with self._lock:
            self.metrics[name].append(metric)
            
        # Update agent stats if this is an agent-specific metric
        if tags and 'agent_id' in tags:
            self._update_agent_stats(tags['agent_id'], name, value)
            
    def _update_agent_stats(self, agent_id: str, metric_name: str, value: float):
        """Update aggregated statistics for an agent."""
        with self._lock:
            if agent_id not in self.agent_stats:
                self.agent_stats[agent_id] = AgentPerformanceStats(agent_id=agent_id)
                
            stats = self.agent_stats[agent_id]
            
            if metric_name == 'message_response_time':
                stats.message_count += 1
                if stats.min_response_time == float('inf'):
                    stats.min_response_time = value
                else:
                    stats.min_response_time = min(stats.min_response_time, value)
                stats.max_response_time = max(stats.max_response_time, value)
                
                # Calculate rolling average
                if stats.message_count == 1:
                    stats.avg_response_time = value
                else:
                    stats.avg_response_time = (
                        (stats.avg_response_time * (stats.message_count - 1) + value) / 
                        stats.message_count
                    )
                    
            elif metric_name == 'message_error':
                stats.error_count += 1
                stats.success_rate = (
                    (stats.message_count - stats.error_count) / stats.message_count * 100
                    if stats.message_count > 0 else 100.0
                )
                
            elif metric_name == 'memory_usage':
                stats.memory_usage = value
                
            elif metric_name == 'cpu_usage':
                stats.cpu_usage = value
                
            stats.last_updated = datetime.now()
            
            # Calculate throughput (messages per second over last minute)
            one_minute_ago = datetime.now() - timedelta(minutes=1)
            recent_messages = sum(
                1 for metric in self.metrics['message_response_time']
                if (metric.tags.get('agent_id') == agent_id and 
                    metric.timestamp >= one_minute_ago)
            )
            stats.throughput = recent_messages / 60.0
            
            # Check for alerts
            self._check_alerts(agent_id, stats)
            
    def _check_alerts(self, agent_id: str, stats: AgentPerformanceStats):
        """Check if any performance thresholds are exceeded."""
        alerts = []
        
        if stats.avg_response_time > self.alert_thresholds['response_time']:
            alerts.append(f"High response time: {stats.avg_response_time:.2f}ms")
            
        if stats.success_rate < (100 - self.alert_thresholds['error_rate']):
            alerts.append(f"High error rate: {100 - stats.success_rate:.2f}%")
            
        if stats.memory_usage > self.alert_thresholds['memory_usage']:
            alerts.append(f"High memory usage: {stats.memory_usage:.2f}MB")
            
        if stats.cpu_usage > self.alert_thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {stats.cpu_usage:.2f}%")
            
        if alerts:
            alert_data = {
                'agent_id': agent_id,
                'timestamp': datetime.now(),
                'alerts': alerts,
                'stats': stats
            }
            
            for callback in self.alert_callbacks:
                try:
                    callback(alert_data)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
                    
    @contextmanager
    def measure_time(self, metric_name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for measuring execution time."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
            self.record_metric(metric_name, duration, tags)
            
    def get_metrics(self, name: str, since: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get metrics by name, optionally filtered by time."""
        with self._lock:
            metrics = list(self.metrics[name])
            
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
            
        return metrics
        
    def get_agent_stats(self, agent_id: Optional[str] = None) -> Dict[str, AgentPerformanceStats]:
        """Get performance statistics for agents."""
        with self._lock:
            if agent_id:
                return {agent_id: self.agent_stats.get(agent_id)}
            return dict(self.agent_stats)
            
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system-wide performance metrics."""
        if HAS_PSUTIL:
            try:
                process = psutil.Process()
                system_metrics = {
                    'system_cpu_percent': psutil.cpu_percent(),
                    'system_memory_percent': psutil.virtual_memory().percent,
                    'process_cpu_percent': process.cpu_percent(),
                    'process_memory_mb': process.memory_info().rss / 1024 / 1024,
                }
            except Exception:
                system_metrics = {
                    'system_cpu_percent': 0.0,
                    'system_memory_percent': 0.0,
                    'process_cpu_percent': 0.0,
                    'process_memory_mb': 0.0,
                }
        else:
            system_metrics = {
                'system_cpu_percent': 0.0,
                'system_memory_percent': 0.0,
                'process_cpu_percent': 0.0,
                'process_memory_mb': 0.0,
            }
        
        system_metrics.update({
            'active_agents': len(self.agent_stats),
            'total_messages': sum(stats.message_count for stats in self.agent_stats.values()),
            'avg_response_time': statistics.mean([
                stats.avg_response_time for stats in self.agent_stats.values()
                if stats.message_count > 0
            ]) if self.agent_stats else 0.0
        })
        
        return system_metrics
        
    def calculate_percentiles(self, metric_name: str, percentiles: List[float] = [50, 90, 95, 99]) -> Dict[str, float]:
        """Calculate percentiles for a given metric."""
        with self._lock:
            values = [m.value for m in self.metrics[metric_name]]
            
        if not values:
            return {f"p{p}": 0.0 for p in percentiles}
            
        values.sort()
        result = {}
        
        for p in percentiles:
            index = int(len(values) * p / 100)
            if index >= len(values):
                index = len(values) - 1
            result[f"p{p}"] = values[index]
            
        return result
        
    def add_alert_callback(self, callback: Callable):
        """Add a callback function for performance alerts."""
        self.alert_callbacks.append(callback)
        
    def set_alert_threshold(self, metric: str, threshold: float):
        """Set alert threshold for a metric."""
        self.alert_thresholds[metric] = threshold
        
    async def _cleanup_old_metrics(self):
        """Periodically clean up old metrics to prevent memory leaks."""
        while self._running:
            try:
                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
                
                with self._lock:
                    for metric_name, metric_list in self.metrics.items():
                        # Remove old metrics
                        while metric_list and metric_list[0].timestamp < cutoff_time:
                            metric_list.popleft()
                            
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during metrics cleanup: {e}")
                await asyncio.sleep(60)
                
    def export_metrics(self, format: str = 'json') -> str:
        """Export current metrics in specified format."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'agent_stats': {
                agent_id: {
                    'agent_id': stats.agent_id,
                    'message_count': stats.message_count,
                    'avg_response_time': stats.avg_response_time,
                    'max_response_time': stats.max_response_time,
                    'min_response_time': stats.min_response_time if stats.min_response_time != float('inf') else 0,
                    'error_count': stats.error_count,
                    'success_rate': stats.success_rate,
                    'throughput': stats.throughput,
                    'memory_usage': stats.memory_usage,
                    'cpu_usage': stats.cpu_usage,
                    'last_updated': stats.last_updated.isoformat()
                }
                for agent_id, stats in self.agent_stats.items()
            },
            'system_metrics': self.get_system_metrics()
        }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor