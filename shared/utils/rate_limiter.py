"""
Rate limiting and DDoS protection for HealthSync agents.
Implements token bucket and sliding window algorithms.
"""

import time
import threading
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from collections import defaultdict, deque
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    block_duration_minutes: int = 15
    whitelist_ips: list = None
    
    def __post_init__(self):
        if self.whitelist_ips is None:
            self.whitelist_ips = []

class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        with self.lock:
            now = time.time()
            
            # Refill tokens based on time elapsed
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + (time_passed * self.refill_rate)
            )
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def get_status(self) -> Dict:
        """Get current bucket status"""
        with self.lock:
            return {
                'tokens': self.tokens,
                'capacity': self.capacity,
                'refill_rate': self.refill_rate,
                'last_refill': self.last_refill
            }

class SlidingWindowCounter:
    """Sliding window counter for tracking requests over time"""
    
    def __init__(self, window_size_seconds: int):
        self.window_size = window_size_seconds
        self.requests = deque()
        self.lock = threading.Lock()
    
    def add_request(self, timestamp: Optional[float] = None) -> int:
        """
        Add a request to the window
        
        Args:
            timestamp: Request timestamp (defaults to current time)
            
        Returns:
            Current request count in window
        """
        if timestamp is None:
            timestamp = time.time()
        
        with self.lock:
            # Remove old requests outside the window
            cutoff = timestamp - self.window_size
            while self.requests and self.requests[0] <= cutoff:
                self.requests.popleft()
            
            # Add new request
            self.requests.append(timestamp)
            return len(self.requests)
    
    def get_count(self, timestamp: Optional[float] = None) -> int:
        """Get current request count in window"""
        if timestamp is None:
            timestamp = time.time()
        
        with self.lock:
            # Remove old requests
            cutoff = timestamp - self.window_size
            while self.requests and self.requests[0] <= cutoff:
                self.requests.popleft()
            
            return len(self.requests)

class RateLimiter:
    """Comprehensive rate limiting system"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        
        # Per-IP rate limiting
        self.ip_buckets = defaultdict(lambda: TokenBucket(
            capacity=config.burst_limit,
            refill_rate=config.requests_per_minute / 60.0
        ))
        
        # Per-IP sliding windows
        self.ip_windows_minute = defaultdict(lambda: SlidingWindowCounter(60))
        self.ip_windows_hour = defaultdict(lambda: SlidingWindowCounter(3600))
        
        # Blocked IPs
        self.blocked_ips = {}  # ip -> block_until_timestamp
        
        # Global statistics
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rate_limited_requests': 0,
            'unique_ips': set()
        }
        
        self.lock = threading.Lock()
    
    def is_allowed(self, client_ip: str, user_id: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Check if request is allowed based on rate limits
        
        Args:
            client_ip: Client IP address
            user_id: Optional user identifier
            
        Returns:
            Tuple of (is_allowed, response_info)
        """
        now = time.time()
        
        with self.lock:
            self.stats['total_requests'] += 1
            self.stats['unique_ips'].add(client_ip)
        
        # Check if IP is whitelisted
        if client_ip in self.config.whitelist_ips:
            return True, {'status': 'whitelisted'}
        
        # Check if IP is currently blocked
        if client_ip in self.blocked_ips:
            if now < self.blocked_ips[client_ip]:
                with self.lock:
                    self.stats['blocked_requests'] += 1
                
                remaining_block = self.blocked_ips[client_ip] - now
                return False, {
                    'status': 'blocked',
                    'reason': 'IP temporarily blocked',
                    'retry_after': int(remaining_block),
                    'block_until': datetime.fromtimestamp(self.blocked_ips[client_ip]).isoformat()
                }
            else:
                # Block expired, remove it
                del self.blocked_ips[client_ip]
        
        # Check token bucket (burst protection)
        bucket = self.ip_buckets[client_ip]
        if not bucket.consume():
            self._handle_rate_limit_violation(client_ip, 'burst_limit')
            return False, {
                'status': 'rate_limited',
                'reason': 'Burst limit exceeded',
                'retry_after': 60,
                'limit_type': 'burst'
            }
        
        # Check sliding window limits
        minute_count = self.ip_windows_minute[client_ip].add_request(now)
        if minute_count > self.config.requests_per_minute:
            self._handle_rate_limit_violation(client_ip, 'minute_limit')
            return False, {
                'status': 'rate_limited',
                'reason': 'Per-minute limit exceeded',
                'retry_after': 60,
                'limit_type': 'minute',
                'current_count': minute_count,
                'limit': self.config.requests_per_minute
            }
        
        hour_count = self.ip_windows_hour[client_ip].add_request(now)
        if hour_count > self.config.requests_per_hour:
            self._handle_rate_limit_violation(client_ip, 'hour_limit')
            return False, {
                'status': 'rate_limited',
                'reason': 'Per-hour limit exceeded',
                'retry_after': 3600,
                'limit_type': 'hour',
                'current_count': hour_count,
                'limit': self.config.requests_per_hour
            }
        
        # Request allowed
        return True, {
            'status': 'allowed',
            'remaining_minute': self.config.requests_per_minute - minute_count,
            'remaining_hour': self.config.requests_per_hour - hour_count,
            'bucket_tokens': bucket.get_status()['tokens']
        }
    
    def _handle_rate_limit_violation(self, client_ip: str, violation_type: str):
        """Handle rate limit violations"""
        now = time.time()
        
        with self.lock:
            self.stats['rate_limited_requests'] += 1
        
        # Log the violation
        logger.warning(f"Rate limit violation: {client_ip} - {violation_type}")
        
        # Check if we should block the IP
        if violation_type in ['burst_limit', 'minute_limit']:
            # Count recent violations
            recent_violations = self._count_recent_violations(client_ip)
            
            if recent_violations >= 3:  # Block after 3 violations
                block_until = now + (self.config.block_duration_minutes * 60)
                self.blocked_ips[client_ip] = block_until
                
                logger.warning(f"Blocking IP {client_ip} until {datetime.fromtimestamp(block_until)}")
    
    def _count_recent_violations(self, client_ip: str) -> int:
        """Count recent rate limit violations for an IP"""
        # This is a simplified implementation
        # In production, you'd want to track violations in a persistent store
        return 1
    
    def add_to_whitelist(self, ip: str):
        """Add IP to whitelist"""
        if ip not in self.config.whitelist_ips:
            self.config.whitelist_ips.append(ip)
            logger.info(f"Added {ip} to whitelist")
    
    def remove_from_whitelist(self, ip: str):
        """Remove IP from whitelist"""
        if ip in self.config.whitelist_ips:
            self.config.whitelist_ips.remove(ip)
            logger.info(f"Removed {ip} from whitelist")
    
    def unblock_ip(self, ip: str):
        """Manually unblock an IP"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            logger.info(f"Manually unblocked IP {ip}")
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics"""
        with self.lock:
            return {
                'total_requests': self.stats['total_requests'],
                'blocked_requests': self.stats['blocked_requests'],
                'rate_limited_requests': self.stats['rate_limited_requests'],
                'unique_ips_count': len(self.stats['unique_ips']),
                'currently_blocked_ips': len(self.blocked_ips),
                'blocked_ips': list(self.blocked_ips.keys()),
                'whitelist_size': len(self.config.whitelist_ips)
            }
    
    def cleanup_expired_data(self):
        """Clean up expired data structures"""
        now = time.time()
        
        # Remove expired IP blocks
        expired_blocks = [
            ip for ip, block_until in self.blocked_ips.items()
            if now >= block_until
        ]
        
        for ip in expired_blocks:
            del self.blocked_ips[ip]
        
        # Clean up old bucket data (buckets auto-cleanup on access)
        # Clean up old window data (windows auto-cleanup on access)
        
        if expired_blocks:
            logger.info(f"Cleaned up {len(expired_blocks)} expired IP blocks")

class DDoSProtection:
    """Advanced DDoS protection system"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.suspicious_patterns = []
        self.attack_threshold = 100  # requests per minute from single IP
        self.global_threshold = 10000  # total requests per minute
        
        # Pattern detection
        self.request_patterns = defaultdict(list)
        self.user_agent_counts = defaultdict(int)
        self.request_size_stats = []
    
    def analyze_request(self, client_ip: str, user_agent: str, 
                       request_size: int, endpoint: str) -> Dict:
        """
        Analyze request for DDoS patterns
        
        Returns:
            Analysis result with threat level and recommendations
        """
        now = time.time()
        threat_level = "low"
        alerts = []
        
        # Track request patterns
        self.request_patterns[client_ip].append({
            'timestamp': now,
            'endpoint': endpoint,
            'size': request_size,
            'user_agent': user_agent
        })
        
        # Clean old patterns (keep last hour)
        cutoff = now - 3600
        self.request_patterns[client_ip] = [
            req for req in self.request_patterns[client_ip]
            if req['timestamp'] > cutoff
        ]
        
        # Analyze patterns
        ip_requests = len(self.request_patterns[client_ip])
        
        # Check for high-frequency attacks
        if ip_requests > self.attack_threshold:
            threat_level = "high"
            alerts.append(f"High request frequency from {client_ip}: {ip_requests}/hour")
        
        # Check for suspicious user agents
        self.user_agent_counts[user_agent] += 1
        if self.user_agent_counts[user_agent] > 1000:
            threat_level = "medium"
            alerts.append(f"Suspicious user agent pattern: {user_agent}")
        
        # Check for request size anomalies
        self.request_size_stats.append(request_size)
        if len(self.request_size_stats) > 1000:
            self.request_size_stats = self.request_size_stats[-1000:]
        
        if request_size > 1000000:  # 1MB
            threat_level = "medium"
            alerts.append(f"Large request size: {request_size} bytes")
        
        return {
            'threat_level': threat_level,
            'alerts': alerts,
            'ip_request_count': ip_requests,
            'recommendations': self._get_recommendations(threat_level, alerts)
        }
    
    def _get_recommendations(self, threat_level: str, alerts: List[str]) -> List[str]:
        """Get security recommendations based on threat analysis"""
        recommendations = []
        
        if threat_level == "high":
            recommendations.extend([
                "Consider blocking the source IP",
                "Enable additional monitoring",
                "Review firewall rules"
            ])
        elif threat_level == "medium":
            recommendations.extend([
                "Increase monitoring for this source",
                "Consider rate limiting adjustments"
            ])
        
        return recommendations

# Default rate limiting configurations
DEFAULT_RATE_LIMITS = {
    'patient_agent': RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=500,
        burst_limit=5,
        block_duration_minutes=10
    ),
    
    'research_agent': RateLimitConfig(
        requests_per_minute=20,
        requests_per_hour=200,
        burst_limit=3,
        block_duration_minutes=15
    ),
    
    'data_custodian': RateLimitConfig(
        requests_per_minute=50,
        requests_per_hour=1000,
        burst_limit=10,
        block_duration_minutes=5
    ),
    
    'privacy_agent': RateLimitConfig(
        requests_per_minute=40,
        requests_per_hour=800,
        burst_limit=8,
        block_duration_minutes=10
    ),
    
    'metta_agent': RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1200,
        burst_limit=15,
        block_duration_minutes=5
    )
}