"""
Performance optimization system for AIQLeads
Implements adaptive optimization based on performance metrics
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

class PerformanceOptimizer:
    def __init__(self, thresholds: Dict[str, Dict[str, float]]):
        self.thresholds = thresholds
        self.optimizations = defaultdict(list)
        self.optimization_history = []
        
    def analyze_metrics(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze metrics and suggest optimizations"""
        suggestions = []
        
        # Check duration thresholds
        if metrics["duration_ms"] > self.thresholds.get("duration_ms", float('inf')):
            suggestions.append({
                "type": "duration",
                "severity": "high" if metrics["duration_ms"] > self.thresholds["duration_ms"] * 2 else "medium",
                "suggestion": "Consider implementing caching or reducing operation complexity",
                "current": metrics["duration_ms"],
                "threshold": self.thresholds["duration_ms"]
            })
            
        # Check CPU usage
        if metrics["cpu_percent"] > self.thresholds.get("cpu_percent", float('inf')):
            suggestions.append({
                "type": "cpu",
                "severity": "high" if metrics["cpu_percent"] > self.thresholds["cpu_percent"] * 1.5 else "medium",
                "suggestion": "Optimize CPU-intensive operations or implement parallel processing",
                "current": metrics["cpu_percent"],
                "threshold": self.thresholds["cpu_percent"]
            })
            
        # Check memory usage
        if metrics["memory_delta_bytes"] > self.thresholds.get("memory_bytes", float('inf')):
            suggestions.append({
                "type": "memory",
                "severity": "high" if metrics["memory_delta_bytes"] > self.thresholds["memory_bytes"] * 2 else "medium",
                "suggestion": "Implement memory cleanup or reduce object allocation",
                "current": metrics["memory_delta_bytes"],
                "threshold": self.thresholds["memory_bytes"]
            })
            
        return suggestions
        
    def optimize_operation(self, operation: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optimizations based on metrics"""
        suggestions = self.analyze_metrics(metrics)
        optimizations = []
        
        for suggestion in suggestions:
            if suggestion["severity"] == "high":
                # Apply immediate optimizations
                optimization = self._apply_optimization(operation, suggestion)
                if optimization:
                    optimizations.append(optimization)
                    
        if optimizations:
            self.optimizations[operation].extend(optimizations)
            self.optimization_history.append({
                "operation": operation,
                "timestamp": datetime.now(),
                "optimizations": optimizations,
                "metrics_before": metrics
            })
            
        return {
            "operation": operation,
            "suggestions": suggestions,
            "applied_optimizations": optimizations
        }
        
    def _apply_optimization(self, operation: str, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """Apply specific optimization strategy"""
        optimization = {
            "type": suggestion["type"],
            "timestamp": datetime.now(),
            "strategy": None
        }
        
        if suggestion["type"] == "duration":
            optimization["strategy"] = "caching"
            # Implement caching logic here
            
        elif suggestion["type"] == "cpu":
            optimization["strategy"] = "parallel_processing"
            # Implement parallel processing logic here
            
        elif suggestion["type"] == "memory":
            optimization["strategy"] = "memory_cleanup"
            # Implement memory cleanup logic here
            
        return optimization
        
    def get_optimization_history(self, operation: str = None) -> List[Dict[str, Any]]:
        """Get optimization history for specific or all operations"""
        if operation:
            return [h for h in self.optimization_history if h["operation"] == operation]
        return self.optimization_history
        
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        stats = defaultdict(lambda: defaultdict(int))
        
        for history in self.optimization_history:
            operation = history["operation"]
            for opt in history["optimizations"]:
                stats[operation][opt["type"]] += 1
                
        return dict(stats)
        
    def adjust_thresholds(self, metrics_history: List[Dict[str, Any]]) -> None:
        """Adaptively adjust thresholds based on metrics history"""
        if not metrics_history:
            return
            
        # Calculate average metrics
        avg_metrics = defaultdict(float)
        for metric in metrics_history:
            for key, value in metric.items():
                if isinstance(value, (int, float)):
                    avg_metrics[key] += value
                    
        for key in avg_metrics:
            avg_metrics[key] /= len(metrics_history)
            
        # Adjust thresholds based on averages
        for key, value in avg_metrics.items():
            if key in self.thresholds:
                # Adjust threshold if consistently below current threshold
                if value * 1.5 < self.thresholds[key]:
                    self.thresholds[key] = max(value * 1.2, self.thresholds[key] * 0.9)
                    logging.info(f"Adjusted threshold for {key}: {self.thresholds[key]}")
                    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        return {
            "total_optimizations": len(self.optimization_history),
            "optimization_stats": self.get_optimization_stats(),
            "current_thresholds": self.thresholds,
            "last_updated": datetime.now(),
            "optimization_types": {
                opt_type: len([h for h in self.optimization_history 
                             for o in h["optimizations"] 
                             if o["type"] == opt_type])
                for opt_type in ["duration", "cpu", "memory"]
            }
        }