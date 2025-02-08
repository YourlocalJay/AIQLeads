"""
Performance monitoring system for AIQLeads
Implements real-time metric collection and analysis
"""

import time
import psutil
from datetime import datetime
from typing import Dict, List, Any
from collections import deque

class PerformanceMonitor:
    def __init__(self, history_size: int = 1000):
        self.metrics = {}
        self.history = deque(maxlen=history_size)
        self.start_time = datetime.now()
        
    def start_measurement(self, operation: str) -> None:
        """Start measuring a specific operation"""
        self.metrics[operation] = {
            "start_time": time.time(),
            "start_cpu": psutil.cpu_percent(),
            "start_memory": psutil.Process().memory_info().rss,
            "start_io": psutil.disk_io_counters(),
            "start_network": psutil.net_io_counters()
        }
        
    def end_measurement(self, operation: str) -> Dict[str, Any]:
        """End measurement and return metrics"""
        if operation not in self.metrics:
            raise ValueError(f"No started measurement for {operation}")
            
        end_time = time.time()
        start_data = self.metrics[operation]
        
        # Calculate metrics
        duration = end_time - start_data["start_time"]
        cpu_usage = psutil.cpu_percent() - start_data["start_cpu"]
        memory_delta = psutil.Process().memory_info().rss - start_data["start_memory"]
        
        # Calculate I/O deltas
        end_io = psutil.disk_io_counters()
        io_read_delta = end_io.read_bytes - start_data["start_io"].read_bytes
        io_write_delta = end_io.write_bytes - start_data["start_io"].write_bytes
        
        # Calculate network deltas
        end_network = psutil.net_io_counters()
        net_sent_delta = end_network.bytes_sent - start_data["start_network"].bytes_sent
        net_recv_delta = end_network.bytes_recv - start_data["start_network"].bytes_recv
        
        metrics = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "cpu_percent": cpu_usage,
            "memory_delta_bytes": memory_delta,
            "io_read_bytes": io_read_delta,
            "io_write_bytes": io_write_delta,
            "network_sent_bytes": net_sent_delta,
            "network_recv_bytes": net_recv_delta,
            "timestamp": datetime.now()
        }
        
        # Store in history
        self.history.append(metrics)
        
        # Cleanup
        del self.metrics[operation]
        
        return metrics
        
    def get_history(self) -> List[Dict[str, Any]]:
        """Return all historical metrics"""
        return list(self.history)
        
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from historical data"""
        if not self.history:
            return {}
            
        operations = set(m["operation"] for m in self.history)
        stats = {}
        
        for op in operations:
            op_metrics = [m for m in self.history if m["operation"] == op]
            durations = [m["duration_ms"] for m in op_metrics]
            cpu_usage = [m["cpu_percent"] for m in op_metrics]
            memory_deltas = [m["memory_delta_bytes"] for m in op_metrics]
            
            stats[op] = {
                "count": len(op_metrics),
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "avg_cpu_percent": sum(cpu_usage) / len(cpu_usage),
                "avg_memory_delta_bytes": sum(memory_deltas) / len(memory_deltas)
            }
            
        return stats
        
    def check_thresholds(self, thresholds: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Check metrics against defined thresholds"""
        violations = []
        
        for metric in self.history:
            op = metric["operation"]
            if op in thresholds:
                for key, threshold in thresholds[op].items():
                    if key in metric and metric[key] > threshold:
                        violations.append({
                            "operation": op,
                            "metric": key,
                            "value": metric[key],
                            "threshold": threshold,
                            "timestamp": metric["timestamp"]
                        })
                        
        return violations
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            "start_time": self.start_time,
            "end_time": datetime.now(),
            "total_operations": len(self.history),
            "statistics": self.get_statistics(),
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_usage": psutil.disk_usage('/').percent,
                "load_avg": psutil.getloadavg()
            }
        }