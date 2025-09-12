"""
Monitor de performance y SLA para Comment Analyzer.
Monitorea tiempos de procesamiento y cumplimiento de SLA ≤10s P50.
"""

import time
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import statistics
from functools import wraps
from config import PERFORMANCE_SLA_TARGET_SECONDS, PERFORMANCE_SLA_PERCENTILE

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Métrica individual de performance."""
    operation: str
    duration_seconds: float
    timestamp: float
    batch_size: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class PerformanceStats:
    """Estadísticas agregadas de performance."""
    total_operations: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    p50_duration: float = 0.0
    p95_duration: float = 0.0
    p99_duration: float = 0.0
    success_rate: float = 100.0
    operations_per_second: float = 0.0
    sla_compliance: bool = True
    metrics: List[PerformanceMetric] = field(default_factory=list)

class PerformanceMonitor:
    """Monitor de performance thread-safe para operaciones del sistema."""
    
    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self._active_operations: Dict[str, float] = {}
    
    def start_operation(self, operation_name: str, batch_size: Optional[int] = None) -> str:
        """
        Inicia el monitoreo de una operación.
        
        Args:
            operation_name: Nombre de la operación
            batch_size: Tamaño del batch si aplica
            
        Returns:
            ID único de la operación para usar en end_operation
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"
        self._active_operations[operation_id] = time.time()
        
        logger.debug(f"Started monitoring operation: {operation_name}")
        return operation_id
    
    def end_operation(self, operation_id: str, operation_name: str, 
                     batch_size: Optional[int] = None, success: bool = True, 
                     error_message: Optional[str] = None) -> float:
        """
        Termina el monitoreo de una operación.
        
        Args:
            operation_id: ID de la operación
            operation_name: Nombre de la operación
            batch_size: Tamaño del batch procesado
            success: Si la operación fue exitosa
            error_message: Mensaje de error si falló
            
        Returns:
            Duración en segundos
        """
        if operation_id not in self._active_operations:
            logger.warning(f"Operation ID {operation_id} not found in active operations")
            return 0.0
        
        start_time = self._active_operations.pop(operation_id)
        duration = time.time() - start_time
        
        metric = PerformanceMetric(
            operation=operation_name,
            duration_seconds=duration,
            timestamp=time.time(),
            batch_size=batch_size,
            success=success,
            error_message=error_message
        )
        
        self.metrics[operation_name].append(metric)
        
        # Log de performance
        status = "✅" if success else "❌"
        batch_info = f" (batch: {batch_size})" if batch_size else ""
        logger.info(f"{status} {operation_name}: {duration:.3f}s{batch_info}")
        
        # Verificar SLA
        if operation_name in ['analyze_batch_via_llm', 'full_pipeline']:
            self._check_sla_compliance(operation_name, duration)
        
        return duration
    
    def _check_sla_compliance(self, operation: str, duration: float):
        """Verifica cumplimiento de SLA y log warnings si es necesario."""
        if duration > PERFORMANCE_SLA_TARGET_SECONDS:
            logger.warning(f"🚨 SLA BREACH: {operation} took {duration:.3f}s "
                          f"(target: ≤{PERFORMANCE_SLA_TARGET_SECONDS}s)")
    
    def get_stats(self, operation: str) -> PerformanceStats:
        """
        Obtiene estadísticas para una operación específica.
        
        Args:
            operation: Nombre de la operación
            
        Returns:
            Estadísticas calculadas
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return PerformanceStats()
        
        metrics = self.metrics[operation]
        durations = [m.duration_seconds for m in metrics]
        successful_ops = [m for m in metrics if m.success]
        
        stats = PerformanceStats()
        stats.total_operations = len(metrics)
        stats.total_duration = sum(durations)
        stats.avg_duration = statistics.mean(durations)
        stats.min_duration = min(durations)
        stats.max_duration = max(durations)
        stats.success_rate = (len(successful_ops) / len(metrics)) * 100
        stats.metrics = metrics.copy()
        
        if len(durations) >= 2:
            sorted_durations = sorted(durations)
            stats.p50_duration = statistics.median(sorted_durations)
            stats.p95_duration = sorted_durations[int(len(sorted_durations) * 0.95)]
            stats.p99_duration = sorted_durations[int(len(sorted_durations) * 0.99)]
        else:
            stats.p50_duration = durations[0] if durations else 0.0
            stats.p95_duration = stats.p50_duration
            stats.p99_duration = stats.p50_duration
        
        # Calcular operaciones por segundo
        if stats.total_duration > 0:
            stats.operations_per_second = stats.total_operations / stats.total_duration
        
        # Verificar SLA compliance
        target_percentile = PERFORMANCE_SLA_PERCENTILE / 100.0
        if len(durations) >= 10:  # Solo verificar con suficientes datos
            percentile_duration = sorted(durations)[int(len(durations) * target_percentile)]
            stats.sla_compliance = percentile_duration <= PERFORMANCE_SLA_TARGET_SECONDS
        
        return stats
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """Obtiene estadísticas para todas las operaciones."""
        return {op: self.get_stats(op) for op in self.metrics.keys()}
    
    def reset_stats(self, operation: Optional[str] = None):
        """
        Reinicia estadísticas.
        
        Args:
            operation: Operación específica a reiniciar (None = todas)
        """
        if operation:
            if operation in self.metrics:
                self.metrics[operation].clear()
                logger.info(f"Reset stats for operation: {operation}")
        else:
            self.metrics.clear()
            self._active_operations.clear()
            logger.info("Reset all performance stats")

# Instancia global del monitor
performance_monitor = PerformanceMonitor()

class PerformanceContext:
    """Context manager para monitoreo automático de performance."""
    
    def __init__(self, operation_name: str, batch_size: Optional[int] = None):
        self.operation_name = operation_name
        self.batch_size = batch_size
        self.operation_id = None
        self.success = True
        self.error_message = None
    
    def __enter__(self):
        self.operation_id = performance_monitor.start_operation(
            self.operation_name, self.batch_size
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)
        
        performance_monitor.end_operation(
            self.operation_id, self.operation_name, 
            self.batch_size, self.success, self.error_message
        )

def monitor_performance(operation_name: str, batch_size: Optional[int] = None):
    """
    Decorator para monitoreo automático de performance.
    
    Args:
        operation_name: Nombre de la operación
        batch_size: Tamaño del batch (None para auto-detectar)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Auto-detectar batch_size si es posible
            actual_batch_size = batch_size
            if actual_batch_size is None:
                # Buscar en argumentos comunes
                if 'comments' in kwargs:
                    actual_batch_size = len(kwargs['comments'])
                elif len(args) > 0 and hasattr(args[0], '__len__'):
                    try:
                        actual_batch_size = len(args[0])
                    except:
                        pass
            
            with PerformanceContext(operation_name, actual_batch_size):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def measure_time(timings: dict, key: str):
    """
    Decorator legacy para compatibilidad (deprecated - usar monitor_performance).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            out = func(*args, **kwargs)
            timings[key] = round((time.perf_counter() - t0)*1000, 1)  # ms
            return out
        return wrapper
    return decorator

def generate_performance_report() -> Dict[str, Any]:
    """
    Genera reporte completo de performance.
    
    Returns:
        Diccionario con reporte detallado
    """
    all_stats = performance_monitor.get_all_stats()
    
    if not all_stats:
        return {
            "status": "NO_DATA",
            "message": "No hay datos de performance disponibles",
            "sla_compliance": True
        }
    
    # Calcular compliance general de SLA
    sla_compliant_ops = [stats for stats in all_stats.values() if stats.sla_compliance]
    overall_sla_compliance = len(sla_compliant_ops) == len(all_stats) if all_stats else True
    
    # Encontrar operaciones problemáticas
    slow_operations = []
    for op_name, stats in all_stats.items():
        if stats.p50_duration > PERFORMANCE_SLA_TARGET_SECONDS:
            slow_operations.append({
                "operation": op_name,
                "p50_duration": stats.p50_duration,
                "sla_target": PERFORMANCE_SLA_TARGET_SECONDS
            })
    
    return {
        "status": "SLA_COMPLIANT" if overall_sla_compliance else "SLA_BREACH",
        "overall_sla_compliance": overall_sla_compliance,
        "sla_target": f"≤{PERFORMANCE_SLA_TARGET_SECONDS}s P{PERFORMANCE_SLA_PERCENTILE}",
        "summary": {
            "total_operations_monitored": len(all_stats),
            "total_executions": sum(stats.total_operations for stats in all_stats.values()),
            "avg_success_rate": statistics.mean([stats.success_rate for stats in all_stats.values()]) if all_stats else 100.0
        },
        "by_operation": {
            op_name: {
                "total_executions": stats.total_operations,
                "avg_duration": round(stats.avg_duration, 3),
                "p50_duration": round(stats.p50_duration, 3),
                "p95_duration": round(stats.p95_duration, 3),
                "success_rate": round(stats.success_rate, 2),
                "sla_compliant": stats.sla_compliance,
                "ops_per_second": round(stats.operations_per_second, 2)
            }
            for op_name, stats in all_stats.items()
        },
        "slow_operations": slow_operations,
        "recommendations": _generate_performance_recommendations(all_stats, slow_operations)
    }

def _generate_performance_recommendations(all_stats: Dict[str, PerformanceStats], 
                                        slow_operations: List[Dict]) -> List[str]:
    """Genera recomendaciones basadas en métricas de performance."""
    recommendations = []
    
    if not all_stats:
        return ["Ejecutar operaciones para obtener métricas de performance"]
    
    if slow_operations:
        recommendations.append(f"⚠️ {len(slow_operations)} operaciones exceden el SLA - optimizar performance")
    
    # Verificar success rate
    low_success_ops = [op for op, stats in all_stats.items() if stats.success_rate < 95]
    if low_success_ops:
        recommendations.append(f"🔧 Mejorar reliability de: {', '.join(low_success_ops)}")
    
    # Verificar throughput
    low_throughput_ops = [op for op, stats in all_stats.items() if stats.operations_per_second < 0.1]
    if low_throughput_ops:
        recommendations.append("🚀 Considerar paralelización para mejorar throughput")
    
    if len(recommendations) == 0:
        recommendations.append("✅ Performance cumple con SLAs establecidos")
    
    return recommendations
