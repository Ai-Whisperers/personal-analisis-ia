# -*- coding: utf-8 -*-
"""
Performance Monitor - Decorator and tools for measuring performance
Ensures SLA compliance (≤10s P50 for 800-1200 rows)
"""
import time
import logging
import functools
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    function_name: str
    duration: float
    timestamp: datetime
    input_size: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class PerformanceMonitor:
    """Thread-safe performance monitoring"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.lock = threading.Lock()
        self.sla_targets = {
            'pipeline_execution': 10.0,  # 10 seconds for full pipeline
            'file_processing': 2.0,      # 2 seconds for file processing
            'llm_batch': 8.0,            # 8 seconds for LLM batch processing
            'data_export': 3.0           # 3 seconds for data export
        }
    
    def measure_time(
        self, 
        function_name: Optional[str] = None,
        sla_category: Optional[str] = None,
        input_size_key: Optional[str] = None
    ):
        """Decorator to measure function execution time"""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                func_name = function_name or f"{func.__module__}.{func.__name__}"
                
                # Extract input size if specified
                input_size = None
                if input_size_key:
                    input_size = self._extract_input_size(args, kwargs, input_size_key)
                
                success = True
                error = None
                result = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                
                except Exception as e:
                    success = False
                    error = str(e)
                    logger.error(f"Error in {func_name}: {error}")
                    raise
                
                finally:
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # Create metric
                    metric = PerformanceMetric(
                        function_name=func_name,
                        duration=duration,
                        timestamp=datetime.now(),
                        input_size=input_size,
                        success=success,
                        error=error,
                        metadata={
                            'sla_category': sla_category,
                            'args_count': len(args),
                            'kwargs_keys': list(kwargs.keys())
                        }
                    )
                    
                    # Store metric thread-safely
                    with self.lock:
                        self.metrics.append(metric)
                    
                    # Log performance
                    self._log_performance(metric, sla_category)
            
            return wrapper
        return decorator
    
    def _extract_input_size(self, args: tuple, kwargs: dict, size_key: str) -> Optional[int]:
        """Extract input size from function arguments"""
        try:
            # Check if it's a DataFrame size
            if size_key == 'dataframe_size':
                for arg in args:
                    if hasattr(arg, '__len__'):
                        return len(arg)
                for value in kwargs.values():
                    if hasattr(value, '__len__'):
                        return len(value)
            
            # Check for specific key in kwargs
            if size_key in kwargs:
                value = kwargs[size_key]
                if hasattr(value, '__len__'):
                    return len(value)
                return int(value)
            
            # Check for list/batch size in args
            if size_key == 'batch_size':
                for arg in args:
                    if isinstance(arg, (list, tuple)):
                        return len(arg)
        
        except Exception:
            pass  # Ignore errors in size extraction
        
        return None
    
    def _log_performance(self, metric: PerformanceMetric, sla_category: Optional[str]):
        """Log performance and check SLA compliance"""
        duration = metric.duration
        
        # Log basic performance
        log_msg = f"Performance: {metric.function_name} took {duration:.3f}s"
        if metric.input_size:
            log_msg += f" (input_size: {metric.input_size})"
        
        if metric.success:
            logger.info(log_msg)
        else:
            logger.error(f"{log_msg} - FAILED: {metric.error}")
        
        # Check SLA compliance
        if sla_category and sla_category in self.sla_targets:
            sla_target = self.sla_targets[sla_category]
            if duration > sla_target:
                logger.warning(
                    f"SLA VIOLATION: {metric.function_name} took {duration:.3f}s "
                    f"(target: {sla_target}s) - {((duration/sla_target - 1) * 100):.1f}% over"
                )
            else:
                logger.debug(f"SLA OK: {metric.function_name} within {sla_target}s target")
    
    def get_metrics(self, function_name: Optional[str] = None) -> List[PerformanceMetric]:
        """Get performance metrics, optionally filtered by function name"""
        with self.lock:
            if function_name:
                return [m for m in self.metrics if m.function_name == function_name]
            return self.metrics.copy()
    
    def get_summary_stats(self, sla_category: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary statistics"""
        with self.lock:
            metrics = self.metrics.copy()
        
        if not metrics:
            return {'no_data': True}
        
        # Filter by SLA category if specified
        if sla_category:
            metrics = [
                m for m in metrics 
                if m.metadata and m.metadata.get('sla_category') == sla_category
            ]
        
        if not metrics:
            return {'no_data_for_category': sla_category}
        
        # Calculate statistics
        durations = [m.duration for m in metrics if m.success]
        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]
        
        if not durations:
            return {'no_successful_executions': True}
        
        # Basic stats
        stats = {
            'total_executions': len(metrics),
            'successful_executions': len(successful_metrics),
            'failed_executions': len(failed_metrics),
            'success_rate': len(successful_metrics) / len(metrics) * 100,
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p50_duration': self._percentile(durations, 50),
            'p95_duration': self._percentile(durations, 95),
            'p99_duration': self._percentile(durations, 99)
        }
        
        # SLA compliance
        if sla_category and sla_category in self.sla_targets:
            sla_target = self.sla_targets[sla_category]
            sla_violations = [d for d in durations if d > sla_target]
            stats.update({
                'sla_target': sla_target,
                'sla_compliance_rate': (1 - len(sla_violations) / len(durations)) * 100,
                'sla_violations': len(sla_violations),
                'avg_violation_severity': sum(sla_violations) / len(sla_violations) if sla_violations else 0
            })
        
        # Input size analysis
        sizes = [m.input_size for m in successful_metrics if m.input_size is not None]
        if sizes:
            stats.update({
                'avg_input_size': sum(sizes) / len(sizes),
                'min_input_size': min(sizes),
                'max_input_size': max(sizes),
                'throughput_per_second': sum(sizes) / sum(durations) if sum(durations) > 0 else 0
            })
        
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        sorted_data = sorted(data)
        n = len(sorted_data)
        if n == 0:
            return 0.0
        
        index = (percentile / 100) * (n - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def check_sla_compliance(self, sla_category: str) -> Dict[str, Any]:
        """Check SLA compliance for a specific category"""
        stats = self.get_summary_stats(sla_category)
        
        if 'sla_target' not in stats:
            return {'error': f'No SLA target defined for category: {sla_category}'}
        
        sla_target = stats['sla_target']
        p50_duration = stats.get('p50_duration', 0)
        compliance_rate = stats.get('sla_compliance_rate', 100)
        
        return {
            'category': sla_category,
            'sla_target': sla_target,
            'p50_duration': p50_duration,
            'compliance_rate': compliance_rate,
            'is_compliant': p50_duration <= sla_target,
            'violation_severity': max(0, p50_duration - sla_target),
            'recommendation': self._get_performance_recommendation(stats)
        }
    
    def _get_performance_recommendation(self, stats: Dict[str, Any]) -> str:
        """Generate performance improvement recommendations"""
        if stats.get('no_data'):
            return "No performance data available"
        
        p50 = stats.get('p50_duration', 0)
        sla_target = stats.get('sla_target', float('inf'))
        success_rate = stats.get('success_rate', 100)
        
        recommendations = []
        
        if success_rate < 95:
            recommendations.append("Investigate and fix error causes to improve reliability")
        
        if p50 > sla_target:
            overage = ((p50 / sla_target - 1) * 100)
            if overage > 50:
                recommendations.append("Critical performance issue - major optimization needed")
            elif overage > 20:
                recommendations.append("Significant performance degradation - optimization recommended")
            else:
                recommendations.append("Minor performance issue - fine-tuning recommended")
        
        if stats.get('avg_input_size', 0) > 1000:
            recommendations.append("Consider batch size optimization for large datasets")
        
        if not recommendations:
            recommendations.append("Performance within acceptable parameters")
        
        return "; ".join(recommendations)
    
    def reset_metrics(self):
        """Clear all performance metrics"""
        with self.lock:
            self.metrics.clear()
        logger.info("Performance metrics reset")
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export metrics for external analysis"""
        with self.lock:
            return {
                'metrics': [
                    {
                        'function_name': m.function_name,
                        'duration': m.duration,
                        'timestamp': m.timestamp.isoformat(),
                        'input_size': m.input_size,
                        'success': m.success,
                        'error': m.error,
                        'metadata': m.metadata
                    }
                    for m in self.metrics
                ],
                'sla_targets': self.sla_targets,
                'export_timestamp': datetime.now().isoformat()
            }

# Global instance
monitor = PerformanceMonitor()

# Convenience decorators
def measure_time(function_name: Optional[str] = None, sla_category: Optional[str] = None):
    """Convenience decorator for performance measurement"""
    return monitor.measure_time(function_name, sla_category, 'dataframe_size')

def measure_pipeline_performance(func: Callable) -> Callable:
    """Decorator specifically for pipeline performance measurement"""
    return monitor.measure_time(
        function_name=f"pipeline.{func.__name__}",
        sla_category='pipeline_execution',
        input_size_key='dataframe_size'
    )(func)

def measure_llm_performance(func: Callable) -> Callable:
    """Decorator specifically for LLM call performance measurement"""
    return monitor.measure_time(
        function_name=f"llm.{func.__name__}",
        sla_category='llm_batch',
        input_size_key='batch_size'
    )(func)

# Convenience functions
def get_performance_summary() -> Dict[str, Any]:
    """Get overall performance summary"""
    return monitor.get_summary_stats()

def check_pipeline_sla() -> Dict[str, Any]:
    """Check pipeline SLA compliance"""
    return monitor.check_sla_compliance('pipeline_execution')

def reset_performance_metrics():
    """Reset all performance metrics"""
    monitor.reset_metrics()