"""
Performance management system for AIQLeads
Integrates monitoring and optimization components
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from .monitor import PerformanceMonitor
from .optimizer import PerformanceOptimizer

class PerformanceManager:
    def __init__(self, thresholds: Dict[str, Dict[str, float]], history_size: int = 1000):
        self.monitor = PerformanceMonitor(history_size=history_size)
        self.optimizer = PerformanceOptimizer(thresholds)
        self.active_operations = set()
        self.last_optimization = None
        self.optimization_interval = timedelta(minutes=5)
        
    def start_operation(self, operation: str) -> None:
        """Start monitoring an operation"""
        if operation in self.active_operations:
            raise ValueError(f"Operation {operation} is already being monitored")
            
        self.active_operations.add(operation)
        self.monitor.start_measurement(operation)
        
    def end_operation(self, operation: str) -> Dict[str, Any]:
        """End operation monitoring and apply optimizations if needed"""
        if operation not in self.active_operations:
            raise ValueError(f"Operation {operation} is not being monitored")
            
        # Get metrics
        metrics = self.monitor.end_measurement(operation)
        self.active_operations.remove(operation)
        
        # Check if optimization is needed
        should_optimize = self._should_optimize()
        if should_optimize:
            optimization_result = self.optimizer.optimize_operation(operation, metrics)
            self.last_optimization = datetime.now()
            
            # Update report with optimization data
            metrics["optimization"] = optimization_result
            
        return metrics
        
    def _should_optimize(self) -> bool:
        """Determine if optimization should be performed"""
        if not self.last_optimization:
            return True
            
        time_since_last = datetime.now() - self.last_optimization
        return time_since_last >= self.optimization_interval
        
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        monitor_stats = self.monitor.get_statistics()
        optimization_stats = self.optimizer.get_optimization_stats()
        
        return {
            "timestamp": datetime.now(),
            "active_operations": list(self.active_operations),
            "monitoring": {
                "statistics": monitor_stats,
                "system_info": self.monitor.generate_report()["system_info"]
            },
            "optimization": {
                "statistics": optimization_stats,
                "last_optimization": self.last_optimization,
                "optimization_count": len(self.optimizer.get_optimization_history())
            }
        }
        
    def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """Analyze performance trends over specified period"""
        cutoff = datetime.now() - timedelta(days=days)
        history = self.monitor.get_history()
        recent_history = [m for m in history if m["timestamp"] >= cutoff]
        
        trends = {}
        operations = set(m["operation"] for m in recent_history)
        
        for op in operations:
            op_metrics = [m for m in recent_history if m["operation"] == op]
            daily_metrics = self._group_by_day(op_metrics)
            
            trends[op] = {
                "daily_averages": self._calculate_daily_averages(daily_metrics),
                "improvement": self._calculate_improvement(daily_metrics),
                "optimization_impact": self._analyze_optimization_impact(op, daily_metrics)
            }
            
        return trends
        
    def _group_by_day(self, metrics: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group metrics by day"""
        daily = {}
        for metric in metrics:
            day = metric["timestamp"].date().isoformat()
            if day not in daily:
                daily[day] = []
            daily[day].append(metric)
        return daily
        
    def _calculate_daily_averages(self, daily_metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, float]]:
        """Calculate daily average metrics"""
        averages = {}
        for day, metrics in daily_metrics.items():
            averages[day] = {
                "duration_ms": sum(m["duration_ms"] for m in metrics) / len(metrics),
                "cpu_percent": sum(m["cpu_percent"] for m in metrics) / len(metrics),
                "memory_delta_bytes": sum(m["memory_delta_bytes"] for m in metrics) / len(metrics)
            }
        return averages
        
    def _calculate_improvement(self, daily_metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """Calculate improvement percentages"""
        if len(daily_metrics) < 2:
            return {}
            
        days = sorted(daily_metrics.keys())
        first_day = days[0]
        last_day = days[-1]
        
        first_metrics = daily_metrics[first_day]
        last_metrics = daily_metrics[last_day]
        
        return {
            "duration_ms": self._calculate_improvement_percentage(
                sum(m["duration_ms"] for m in first_metrics) / len(first_metrics),
                sum(m["duration_ms"] for m in last_metrics) / len(last_metrics)
            ),
            "cpu_percent": self._calculate_improvement_percentage(
                sum(m["cpu_percent"] for m in first_metrics) / len(first_metrics),
                sum(m["cpu_percent"] for m in last_metrics) / len(last_metrics)
            ),
            "memory_delta_bytes": self._calculate_improvement_percentage(
                sum(m["memory_delta_bytes"] for m in first_metrics) / len(first_metrics),
                sum(m["memory_delta_bytes"] for m in last_metrics) / len(last_metrics)
            )
        }
        
    def _calculate_improvement_percentage(self, start: float, end: float) -> float:
        """Calculate improvement percentage"""
        if start == 0:
            return 0
        return ((start - end) / start) * 100
        
    def _analyze_optimization_impact(self, operation: str, daily_metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze impact of optimizations"""
        optimizations = self.optimizer.get_optimization_history(operation)
        if not optimizations:
            return {}
            
        impact = {}
        for opt in optimizations:
            opt_time = opt["timestamp"]
            opt_day = opt_time.date().isoformat()
            
            if opt_day in daily_metrics:
                before = [m for m in daily_metrics[opt_day] if m["timestamp"] < opt_time]
                after = [m for m in daily_metrics[opt_day] if m["timestamp"] > opt_time]
                
                if before and after:
                    impact[opt_day] = {
                        "type": opt["optimizations"][0]["type"],
                        "duration_impact": self._calculate_improvement_percentage(
                            sum(m["duration_ms"] for m in before) / len(before),
                            sum(m["duration_ms"] for m in after) / len(after)
                        ),
                        "cpu_impact": self._calculate_improvement_percentage(
                            sum(m["cpu_percent"] for m in before) / len(before),
                            sum(m["cpu_percent"] for m in after) / len(after)
                        ),
                        "memory_impact": self._calculate_improvement_percentage(
                            sum(m["memory_delta_bytes"] for m in before) / len(before),
                            sum(m["memory_delta_bytes"] for m in after) / len(after)
                        )
                    }
                    
        return impact