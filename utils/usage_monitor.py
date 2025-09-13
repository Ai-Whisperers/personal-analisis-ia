# -*- coding: utf-8 -*-
"""
Usage Monitor - Track and log API usage metrics
Provides detailed monitoring and alerting for rate limits
"""
import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@dataclass
class UsageMetric:
    """Single usage metric record"""
    timestamp: float
    requests_made: int
    tokens_used: int
    batch_size: int
    processing_time: float
    error_count: int = 0
    rate_limited: bool = False

class UsageMonitor:
    """Monitor and log API usage patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_history: List[UsageMetric] = []
        self.session_start = time.time()
        
        # Thresholds for alerts
        self.warning_threshold_requests = 0.75  # 75% of limit
        self.warning_threshold_tokens = 0.75    # 75% of limit
        self.critical_threshold_requests = 0.90  # 90% of limit
        self.critical_threshold_tokens = 0.90    # 90% of limit
        
        # Limits from config
        self.requests_per_minute = config.get('requests_per_minute', 450)
        self.tokens_per_minute = config.get('tokens_per_minute', 200000)
        
        logger.info(f"Usage monitor initialized - RPM: {self.requests_per_minute}, TPM: {self.tokens_per_minute}")
    
    def log_batch_usage(self, 
                       batch_size: int, 
                       processing_time: float,
                       tokens_used: int = None,
                       requests_made: int = 1,
                       error_count: int = 0,
                       rate_limited: bool = False) -> None:
        """Log usage for a batch processing operation"""
        
        metric = UsageMetric(
            timestamp=time.time(),
            requests_made=requests_made,
            tokens_used=tokens_used or (batch_size * self.config.get('avg_tokens_per_comment', 150)),
            batch_size=batch_size,
            processing_time=processing_time,
            error_count=error_count,
            rate_limited=rate_limited
        )
        
        self.metrics_history.append(metric)
        
        # Keep only last hour of metrics
        cutoff_time = time.time() - 3600  # 1 hour
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        # Log the metric
        logger.info(f"Batch processed: {batch_size} comments, {tokens_used} tokens, {processing_time:.2f}s, errors: {error_count}")
        
        # Check for usage alerts
        self._check_usage_alerts()
    
    def get_current_minute_usage(self) -> Dict[str, int]:
        """Get usage for the current minute window"""
        current_time = time.time()
        minute_start = current_time - 60  # Last 60 seconds
        
        recent_metrics = [m for m in self.metrics_history if m.timestamp > minute_start]
        
        total_requests = sum(m.requests_made for m in recent_metrics)
        total_tokens = sum(m.tokens_used for m in recent_metrics)
        
        return {
            'requests': total_requests,
            'tokens': total_tokens,
            'batch_count': len(recent_metrics)
        }
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the entire session"""
        if not self.metrics_history:
            return {
                'session_duration': time.time() - self.session_start,
                'total_requests': 0,
                'total_tokens': 0,
                'total_batches': 0,
                'average_batch_size': 0,
                'total_errors': 0,
                'rate_limit_incidents': 0
            }
        
        total_requests = sum(m.requests_made for m in self.metrics_history)
        total_tokens = sum(m.tokens_used for m in self.metrics_history)
        total_errors = sum(m.error_count for m in self.metrics_history)
        rate_limit_incidents = sum(1 for m in self.metrics_history if m.rate_limited)
        
        return {
            'session_duration': time.time() - self.session_start,
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_batches': len(self.metrics_history),
            'average_batch_size': sum(m.batch_size for m in self.metrics_history) / len(self.metrics_history),
            'total_errors': total_errors,
            'rate_limit_incidents': rate_limit_incidents,
            'average_processing_time': sum(m.processing_time for m in self.metrics_history) / len(self.metrics_history)
        }
    
    def get_hourly_trends(self) -> Dict[str, List[float]]:
        """Get hourly usage trends for the last hour"""
        current_time = time.time()
        hour_start = current_time - 3600  # Last hour
        
        # Create 12 buckets of 5 minutes each
        bucket_size = 300  # 5 minutes
        buckets = {
            'timestamps': [],
            'requests_per_bucket': [],
            'tokens_per_bucket': [],
            'avg_processing_time': []
        }
        
        for i in range(12):
            bucket_start = hour_start + (i * bucket_size)
            bucket_end = bucket_start + bucket_size
            
            bucket_metrics = [m for m in self.metrics_history 
                            if bucket_start <= m.timestamp < bucket_end]
            
            requests = sum(m.requests_made for m in bucket_metrics)
            tokens = sum(m.tokens_used for m in bucket_metrics)
            avg_time = (sum(m.processing_time for m in bucket_metrics) / len(bucket_metrics)) if bucket_metrics else 0
            
            buckets['timestamps'].append(datetime.fromtimestamp(bucket_start).strftime('%H:%M'))
            buckets['requests_per_bucket'].append(requests)
            buckets['tokens_per_bucket'].append(tokens)
            buckets['avg_processing_time'].append(avg_time)
        
        return buckets
    
    def _check_usage_alerts(self) -> None:
        """Check current usage against thresholds and log alerts"""
        current_usage = self.get_current_minute_usage()
        
        requests_percentage = (current_usage['requests'] / self.requests_per_minute) * 100
        tokens_percentage = (current_usage['tokens'] / self.tokens_per_minute) * 100
        
        # Check for critical alerts (90%+)
        if requests_percentage >= self.critical_threshold_requests * 100:
            logger.critical(f"🚨 CRITICAL: Request usage at {requests_percentage:.1f}% ({current_usage['requests']}/{self.requests_per_minute})")
        elif requests_percentage >= self.warning_threshold_requests * 100:
            logger.warning(f"⚠️  WARNING: Request usage at {requests_percentage:.1f}% ({current_usage['requests']}/{self.requests_per_minute})")
        
        if tokens_percentage >= self.critical_threshold_tokens * 100:
            logger.critical(f"🚨 CRITICAL: Token usage at {tokens_percentage:.1f}% ({current_usage['tokens']:,}/{self.tokens_per_minute:,})")
        elif tokens_percentage >= self.warning_threshold_tokens * 100:
            logger.warning(f"⚠️  WARNING: Token usage at {tokens_percentage:.1f}% ({current_usage['tokens']:,}/{self.tokens_per_minute:,})")
    
    def export_metrics(self, filepath: str) -> None:
        """Export metrics to JSON file"""
        try:
            export_data = {
                'session_summary': self.get_session_summary(),
                'hourly_trends': self.get_hourly_trends(),
                'current_usage': self.get_current_minute_usage(),
                'config': {
                    'requests_per_minute': self.requests_per_minute,
                    'tokens_per_minute': self.tokens_per_minute
                },
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Usage metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on usage patterns"""
        recommendations = []
        
        if not self.metrics_history:
            return ["No usage data available for recommendations"]
        
        current_usage = self.get_current_minute_usage()
        session_summary = self.get_session_summary()
        
        # High usage recommendations
        requests_percentage = (current_usage['requests'] / self.requests_per_minute) * 100
        tokens_percentage = (current_usage['tokens'] / self.tokens_per_minute) * 100
        
        if requests_percentage > 80:
            recommendations.append("Consider reducing concurrent batch processing to avoid rate limits")
        
        if tokens_percentage > 80:
            recommendations.append("Consider reducing batch size or comment length to manage token usage")
        
        # Performance recommendations
        avg_processing_time = session_summary['average_processing_time']
        if avg_processing_time > 30:  # 30 seconds
            recommendations.append("Processing time is high - consider optimizing prompts or reducing batch size")
        
        # Error rate recommendations
        if session_summary['rate_limit_incidents'] > 0:
            recommendations.append("Rate limiting detected - consider upgrading API tier or reducing request rate")
        
        if session_summary['total_errors'] > session_summary['total_batches'] * 0.1:  # >10% error rate
            recommendations.append("High error rate detected - check API configuration and network connectivity")
        
        # Efficiency recommendations
        if session_summary['average_batch_size'] < 20:
            recommendations.append("Small batch sizes detected - consider increasing batch size for better efficiency")
        
        if not recommendations:
            recommendations.append("Usage patterns look healthy - no specific recommendations")
        
        return recommendations