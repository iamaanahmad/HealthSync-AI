"""
Comprehensive error monitoring and alerting system for HealthSync agents.
Provides real-time error tracking, alerting, and system health monitoring.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import statistics

from .enhanced_logging import get_enhanced_logger, AuditEventType
from .error_middleware import ErrorSeverity, ErrorEvent


class AlertType(Enum):
    """Types of alerts."""
    ERROR_RATE_HIGH = "error_rate_high"
    CASCADING_FAILURES = "cascading_failures"
    AGENT_UNRESPONSIVE = "agent_unresponsive"
    SYSTEM_DEGRADED = "system_degraded"
    RECOVERY_FAILED = "recovery_failed"
    SECURITY_BREACH = "security_breach"
    DATA_INTEGRITY = "data_integrity"
    PERFORMANCE_DEGRADED = "performance_degraded"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents a system alert."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: str
    agent_name: Optional[str] = None
    affected_components: List[str] = None
    metrics: Dict[str, Any] = None
    recommended_actions: List[str] = None
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class SystemMetrics:
    """System health and performance metrics."""
    timestamp: str
    total_agents: int
    active_agents: int
    error_rate_per_minute: float
    average_response_time_ms: float
    failed_transactions: int
    successful_transactions: int
    memory_usage_mb: float
    cpu_usage_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class ErrorPatternDetector:
    """Detects error patterns and anomalies."""
    
    def __init__(self):
        self.logger = get_enhanced_logger("error_pattern_detector")
        self.error_history: List[ErrorEvent] = []
        self.pattern_thresholds = {
            "error_rate_threshold": 10,  # errors per minute
            "cascading_failure_window": 300,  # 5 minutes
            "cascading_failure_threshold": 3,  # agents affected
            "recovery_failure_threshold": 3,  # consecutive failures
        }
    
    def add_error_event(self, error_event: ErrorEvent):
        """Add error event for pattern analysis."""
        self.error_history.append(error_event)
        
        # Keep only recent events (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.error_history = [
            e for e in self.error_history
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]
    
    def detect_high_error_rate(self, window_minutes: int = 5) -> Optional[Dict[str, Any]]:
        """Detect if error rate is abnormally high."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_errors = [
            e for e in self.error_history
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]
        
        error_rate = len(recent_errors) / window_minutes
        
        if error_rate > self.pattern_thresholds["error_rate_threshold"]:
            return {
                "pattern_type": "high_error_rate",
                "error_rate": error_rate,
                "threshold": self.pattern_thresholds["error_rate_threshold"],
                "window_minutes": window_minutes,
                "recent_errors": len(recent_errors)
            }
        
        return None
    
    def detect_cascading_failures(self) -> Optional[Dict[str, Any]]:
        """Detect cascading failures across agents."""
        window_seconds = self.pattern_thresholds["cascading_failure_window"]
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        recent_errors = [
            e for e in self.error_history
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]
        
        # Group by agent
        agents_with_errors = set(e.agent_name for e in recent_errors)
        
        if len(agents_with_errors) >= self.pattern_thresholds["cascading_failure_threshold"]:
            # Check if errors occurred in sequence (potential cascade)
            error_timeline = sorted(recent_errors, key=lambda x: x.timestamp)
            
            return {
                "pattern_type": "cascading_failures",
                "affected_agents": list(agents_with_errors),
                "total_errors": len(recent_errors),
                "window_seconds": window_seconds,
                "error_timeline": [
                    {"agent": e.agent_name, "timestamp": e.timestamp, "error_type": e.error_type}
                    for e in error_timeline[-10:]  # Last 10 errors
                ]
            }
        
        return None
    
    def detect_recovery_failures(self) -> Optional[Dict[str, Any]]:
        """Detect repeated recovery failures."""
        recovery_failures = [
            e for e in self.error_history
            if not e.recovery_successful and e.recovery_attempted
        ]
        
        # Group by agent and error type
        failure_patterns = {}
        for error in recovery_failures:
            key = f"{error.agent_name}:{error.error_type}"
            if key not in failure_patterns:
                failure_patterns[key] = []
            failure_patterns[key].append(error)
        
        # Check for consecutive failures
        problematic_patterns = {}
        for pattern_key, failures in failure_patterns.items():
            if len(failures) >= self.pattern_thresholds["recovery_failure_threshold"]:
                # Check if failures are recent and consecutive
                recent_failures = sorted(failures, key=lambda x: x.timestamp)[-3:]
                if len(recent_failures) >= 3:
                    problematic_patterns[pattern_key] = recent_failures
        
        if problematic_patterns:
            return {
                "pattern_type": "recovery_failures",
                "problematic_patterns": {
                    pattern: [{"timestamp": f.timestamp, "error_message": f.error_message} 
                             for f in failures]
                    for pattern, failures in problematic_patterns.items()
                }
            }
        
        return None
    
    def detect_error_anomalies(self) -> List[Dict[str, Any]]:
        """Detect various error anomalies."""
        anomalies = []
        
        # High error rate
        high_error_rate = self.detect_high_error_rate()
        if high_error_rate:
            anomalies.append(high_error_rate)
        
        # Cascading failures
        cascading_failures = self.detect_cascading_failures()
        if cascading_failures:
            anomalies.append(cascading_failures)
        
        # Recovery failures
        recovery_failures = self.detect_recovery_failures()
        if recovery_failures:
            anomalies.append(recovery_failures)
        
        return anomalies


class SystemHealthMonitor:
    """Monitors overall system health and performance."""
    
    def __init__(self):
        self.logger = get_enhanced_logger("system_health_monitor")
        self.metrics_history: List[SystemMetrics] = []
        self.agent_status: Dict[str, Dict[str, Any]] = {}
        self.performance_baselines: Dict[str, float] = {}
    
    def update_agent_status(self, agent_name: str, status: str, 
                           last_seen: datetime = None, metrics: Dict[str, Any] = None):
        """Update agent status information."""
        self.agent_status[agent_name] = {
            "status": status,  # "active", "inactive", "error", "recovering"
            "last_seen": (last_seen or datetime.utcnow()).isoformat(),
            "metrics": metrics or {}
        }
    
    def record_system_metrics(self, metrics: SystemMetrics):
        """Record system metrics for trend analysis."""
        self.metrics_history.append(metrics)
        
        # Keep only recent metrics (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        # Update performance baselines
        self._update_performance_baselines()
    
    def _update_performance_baselines(self):
        """Update performance baselines from historical data."""
        if len(self.metrics_history) < 10:
            return
        
        recent_metrics = self.metrics_history[-100:]  # Last 100 measurements
        
        self.performance_baselines = {
            "avg_response_time": statistics.mean(m.average_response_time_ms for m in recent_metrics),
            "avg_error_rate": statistics.mean(m.error_rate_per_minute for m in recent_metrics),
            "avg_cpu_usage": statistics.mean(m.cpu_usage_percent for m in recent_metrics),
            "avg_memory_usage": statistics.mean(m.memory_usage_mb for m in recent_metrics)
        }
    
    def detect_performance_degradation(self) -> Optional[Dict[str, Any]]:
        """Detect performance degradation compared to baselines."""
        if not self.metrics_history or not self.performance_baselines:
            return None
        
        latest_metrics = self.metrics_history[-1]
        degradation_threshold = 1.5  # 50% worse than baseline
        
        degradations = {}
        
        # Check response time
        if (latest_metrics.average_response_time_ms > 
            self.performance_baselines["avg_response_time"] * degradation_threshold):
            degradations["response_time"] = {
                "current": latest_metrics.average_response_time_ms,
                "baseline": self.performance_baselines["avg_response_time"],
                "degradation_factor": latest_metrics.average_response_time_ms / self.performance_baselines["avg_response_time"]
            }
        
        # Check error rate
        if (latest_metrics.error_rate_per_minute > 
            self.performance_baselines["avg_error_rate"] * degradation_threshold):
            degradations["error_rate"] = {
                "current": latest_metrics.error_rate_per_minute,
                "baseline": self.performance_baselines["avg_error_rate"],
                "degradation_factor": latest_metrics.error_rate_per_minute / self.performance_baselines["avg_error_rate"]
            }
        
        if degradations:
            return {
                "degradation_type": "performance",
                "degradations": degradations,
                "timestamp": latest_metrics.timestamp
            }
        
        return None
    
    def detect_unresponsive_agents(self, timeout_minutes: int = 5) -> List[str]:
        """Detect agents that haven't been seen recently."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        unresponsive_agents = []
        
        for agent_name, status_info in self.agent_status.items():
            last_seen = datetime.fromisoformat(status_info["last_seen"])
            if last_seen < cutoff_time:
                unresponsive_agents.append(agent_name)
        
        return unresponsive_agents
    
    def get_system_health_score(self) -> float:
        """Calculate overall system health score (0-100)."""
        if not self.metrics_history:
            return 50.0  # Neutral score when no data
        
        latest_metrics = self.metrics_history[-1]
        score = 100.0
        
        # Deduct points for high error rate
        if latest_metrics.error_rate_per_minute > 5:
            score -= min(30, latest_metrics.error_rate_per_minute * 2)
        
        # Deduct points for inactive agents
        total_agents = latest_metrics.total_agents
        active_agents = latest_metrics.active_agents
        if total_agents > 0:
            agent_availability = active_agents / total_agents
            score *= agent_availability
        
        # Deduct points for high resource usage
        if latest_metrics.cpu_usage_percent > 80:
            score -= (latest_metrics.cpu_usage_percent - 80) * 0.5
        
        if latest_metrics.memory_usage_mb > 1000:  # Assuming 1GB threshold
            score -= min(20, (latest_metrics.memory_usage_mb - 1000) / 100)
        
        return max(0.0, min(100.0, score))


class AlertManager:
    """Manages system alerts and notifications."""
    
    def __init__(self):
        self.logger = get_enhanced_logger("alert_manager")
        self.alerts: List[Alert] = []
        self.alert_handlers: Dict[AlertType, List[Callable]] = {}
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.cooldown_duration = timedelta(minutes=15)  # Prevent alert spam
    
    def register_alert_handler(self, alert_type: AlertType, handler: Callable):
        """Register handler for specific alert type."""
        if alert_type not in self.alert_handlers:
            self.alert_handlers[alert_type] = []
        self.alert_handlers[alert_type].append(handler)
    
    async def create_alert(self, alert_type: AlertType, severity: AlertSeverity,
                          title: str, description: str, agent_name: str = None,
                          affected_components: List[str] = None,
                          metrics: Dict[str, Any] = None,
                          recommended_actions: List[str] = None) -> Alert:
        """Create and process a new alert."""
        
        # Check cooldown to prevent spam
        cooldown_key = f"{alert_type.value}:{agent_name or 'system'}"
        if cooldown_key in self.alert_cooldowns:
            if datetime.utcnow() < self.alert_cooldowns[cooldown_key]:
                self.logger.debug("Alert suppressed due to cooldown", 
                                alert_type=alert_type.value,
                                agent_name=agent_name)
                return None
        
        # Create alert
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.utcnow().isoformat(),
            agent_name=agent_name,
            affected_components=affected_components or [],
            metrics=metrics or {},
            recommended_actions=recommended_actions or []
        )
        
        self.alerts.append(alert)
        
        # Set cooldown
        self.alert_cooldowns[cooldown_key] = datetime.utcnow() + self.cooldown_duration
        
        # Log alert
        self.logger.audit(
            "alert_created",
            event_type=AuditEventType.SECURITY_EVENT,
            success=True,
            details={
                "alert_id": alert.alert_id,
                "alert_type": alert_type.value,
                "severity": severity.value,
                "title": title,
                "agent_name": agent_name
            }
        )
        
        # Notify handlers
        await self._notify_handlers(alert)
        
        return alert
    
    async def _notify_handlers(self, alert: Alert):
        """Notify registered handlers about the alert."""
        handlers = self.alert_handlers.get(alert.alert_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                self.logger.error("Alert handler failed",
                                alert_id=alert.alert_id,
                                handler=str(handler),
                                error=str(e))
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = None):
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.logger.audit(
                    "alert_acknowledged",
                    event_type=AuditEventType.SECURITY_EVENT,
                    success=True,
                    details={
                        "alert_id": alert_id,
                        "acknowledged_by": acknowledged_by
                    }
                )
                break
    
    def resolve_alert(self, alert_id: str, resolved_by: str = None):
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                self.logger.audit(
                    "alert_resolved",
                    event_type=AuditEventType.SECURITY_EVENT,
                    success=True,
                    details={
                        "alert_id": alert_id,
                        "resolved_by": resolved_by
                    }
                )
                break
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Get active (unresolved) alerts."""
        active_alerts = [a for a in self.alerts if not a.resolved]
        
        if severity:
            active_alerts = [a for a in active_alerts if a.severity == severity]
        
        return active_alerts
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        total_alerts = len(self.alerts)
        
        if total_alerts == 0:
            return {"total_alerts": 0}
        
        # Count by severity
        severity_counts = {}
        for alert in self.alerts:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by type
        type_counts = {}
        for alert in self.alerts:
            alert_type = alert.alert_type.value
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        
        # Resolution statistics
        resolved_count = sum(1 for a in self.alerts if a.resolved)
        acknowledged_count = sum(1 for a in self.alerts if a.acknowledged)
        
        return {
            "total_alerts": total_alerts,
            "resolved_alerts": resolved_count,
            "acknowledged_alerts": acknowledged_count,
            "resolution_rate": resolved_count / total_alerts,
            "acknowledgment_rate": acknowledged_count / total_alerts,
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts
        }


class ComprehensiveErrorMonitor:
    """Main error monitoring system that coordinates all monitoring components."""
    
    def __init__(self):
        self.logger = get_enhanced_logger("comprehensive_error_monitor")
        self.pattern_detector = ErrorPatternDetector()
        self.health_monitor = SystemHealthMonitor()
        self.alert_manager = AlertManager()
        self.monitoring_active = False
        self.monitoring_task = None
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        
        self.logger.info("Error monitoring started", interval_seconds=interval_seconds)
    
    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Error monitoring stopped")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await self._perform_monitoring_cycle()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Monitoring cycle failed", error=str(e))
                await asyncio.sleep(interval_seconds)
    
    async def _perform_monitoring_cycle(self):
        """Perform one monitoring cycle."""
        
        # Detect error patterns
        anomalies = self.pattern_detector.detect_error_anomalies()
        
        for anomaly in anomalies:
            await self._handle_error_anomaly(anomaly)
        
        # Check system health
        performance_degradation = self.health_monitor.detect_performance_degradation()
        if performance_degradation:
            await self._handle_performance_degradation(performance_degradation)
        
        # Check for unresponsive agents
        unresponsive_agents = self.health_monitor.detect_unresponsive_agents()
        if unresponsive_agents:
            await self._handle_unresponsive_agents(unresponsive_agents)
        
        # Calculate and log system health score
        health_score = self.health_monitor.get_system_health_score()
        
        self.logger.audit(
            "monitoring_cycle_completed",
            event_type=AuditEventType.PERFORMANCE,
            success=True,
            details={
                "health_score": health_score,
                "anomalies_detected": len(anomalies),
                "unresponsive_agents": len(unresponsive_agents)
            }
        )
    
    async def _handle_error_anomaly(self, anomaly: Dict[str, Any]):
        """Handle detected error anomaly."""
        pattern_type = anomaly["pattern_type"]
        
        if pattern_type == "high_error_rate":
            await self.alert_manager.create_alert(
                AlertType.ERROR_RATE_HIGH,
                AlertSeverity.WARNING,
                "High Error Rate Detected",
                f"Error rate of {anomaly['error_rate']:.1f} errors/min exceeds threshold of {anomaly['threshold']}",
                metrics=anomaly,
                recommended_actions=[
                    "Check agent logs for recurring errors",
                    "Verify system resources",
                    "Consider scaling up if needed"
                ]
            )
        
        elif pattern_type == "cascading_failures":
            await self.alert_manager.create_alert(
                AlertType.CASCADING_FAILURES,
                AlertSeverity.ERROR,
                "Cascading Failures Detected",
                f"Multiple agents ({len(anomaly['affected_agents'])}) experiencing failures",
                affected_components=anomaly['affected_agents'],
                metrics=anomaly,
                recommended_actions=[
                    "Investigate root cause",
                    "Check inter-agent communication",
                    "Consider system restart if needed"
                ]
            )
        
        elif pattern_type == "recovery_failures":
            await self.alert_manager.create_alert(
                AlertType.RECOVERY_FAILED,
                AlertSeverity.ERROR,
                "Recovery Failures Detected",
                "Multiple recovery attempts have failed",
                metrics=anomaly,
                recommended_actions=[
                    "Review recovery strategies",
                    "Check system dependencies",
                    "Consider manual intervention"
                ]
            )
    
    async def _handle_performance_degradation(self, degradation: Dict[str, Any]):
        """Handle performance degradation."""
        await self.alert_manager.create_alert(
            AlertType.PERFORMANCE_DEGRADED,
            AlertSeverity.WARNING,
            "Performance Degradation Detected",
            "System performance has degraded compared to baseline",
            metrics=degradation,
            recommended_actions=[
                "Check system resources",
                "Review recent changes",
                "Consider performance optimization"
            ]
        )
    
    async def _handle_unresponsive_agents(self, unresponsive_agents: List[str]):
        """Handle unresponsive agents."""
        for agent_name in unresponsive_agents:
            await self.alert_manager.create_alert(
                AlertType.AGENT_UNRESPONSIVE,
                AlertSeverity.ERROR,
                f"Agent Unresponsive: {agent_name}",
                f"Agent {agent_name} has not been seen recently",
                agent_name=agent_name,
                recommended_actions=[
                    f"Check {agent_name} agent status",
                    "Verify agent connectivity",
                    "Restart agent if necessary"
                ]
            )
    
    def add_error_event(self, error_event: ErrorEvent):
        """Add error event for monitoring."""
        self.pattern_detector.add_error_event(error_event)
    
    def update_agent_status(self, agent_name: str, status: str, metrics: Dict[str, Any] = None):
        """Update agent status."""
        self.health_monitor.update_agent_status(agent_name, status, metrics=metrics)
    
    def record_system_metrics(self, metrics: SystemMetrics):
        """Record system metrics."""
        self.health_monitor.record_system_metrics(metrics)
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring data for dashboard."""
        return {
            "system_health_score": self.health_monitor.get_system_health_score(),
            "active_alerts": [a.to_dict() for a in self.alert_manager.get_active_alerts()],
            "alert_statistics": self.alert_manager.get_alert_statistics(),
            "agent_status": self.health_monitor.agent_status,
            "recent_metrics": [m.to_dict() for m in self.health_monitor.metrics_history[-10:]],
            "monitoring_active": self.monitoring_active
        }


# Global error monitor instance
global_error_monitor = ComprehensiveErrorMonitor()


# Default alert handlers
async def console_alert_handler(alert: Alert):
    """Default console alert handler."""
    print(f"🚨 ALERT [{alert.severity.value.upper()}]: {alert.title}")
    print(f"   Description: {alert.description}")
    if alert.agent_name:
        print(f"   Agent: {alert.agent_name}")
    if alert.recommended_actions:
        print(f"   Recommended Actions: {', '.join(alert.recommended_actions)}")
    print()


# Register default handlers
global_error_monitor.alert_manager.register_alert_handler(AlertType.ERROR_RATE_HIGH, console_alert_handler)
global_error_monitor.alert_manager.register_alert_handler(AlertType.CASCADING_FAILURES, console_alert_handler)
global_error_monitor.alert_manager.register_alert_handler(AlertType.AGENT_UNRESPONSIVE, console_alert_handler)
global_error_monitor.alert_manager.register_alert_handler(AlertType.RECOVERY_FAILED, console_alert_handler)