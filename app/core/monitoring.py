"""
Advanced monitoring module for AIQLeads.
Handles memory tracking, cost optimization, and resource utilization.
"""
import time
import logging
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional
import psutil
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class ResourceMetrics:
    """Container for resource utilization metrics."""
    cpu_percent: float = 0.0
    memory_used: float = 0.0  # MB
    memory_available: float = 0.0  # MB
    disk_usage: float = 0.0  # Percentage
    network_io: Dict[str, float] = None  # Bytes sent/received
    thread_count: int = 0
    handle_count: int = 0
    cost_estimate: float = 0.0

class ResourceMonitor:
    """System resource monitoring with cost estimation."""
    
    def __init__(
        self,
        sampling_interval: float = 1.0,
        cost_per_mb_hour: float = 0.00001,  # $0.01 per GB-hour
        cost_per_cpu_hour: float = 0.0001   # $0.10 per CPU-hour
    ):
        self._metrics = ResourceMetrics()
        self._sampling_interval = sampling_interval
        self._cost_per_mb_hour = cost_per_mb_hour
        self._cost_per_cpu_hour = cost_per_cpu_hour
        self._start_time = time.time()
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._running = False
        self._history: List[ResourceMetrics] = []
        
    async def start_monitoring(self):
        """Start continuous resource monitoring."""
        if self._running:
            return
            
        self._running = True
        self._start_time = time.time()
        
        while self._running:
            await self._collect_metrics()
            await asyncio.sleep(self._sampling_interval)
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self._running = False
    
    async def _collect_metrics(self):
        """Collect current resource metrics."""
        try:
            process = psutil.Process()
            system = psutil.virtual_memory()
            
            with self._lock:
                self._metrics.cpu_percent = process.cpu_percent()
                self._metrics.memory_used = process.memory_info().rss / 1024 / 1024
                self._metrics.memory_available = system.available / 1024 / 1024
                self._metrics.disk_usage = psutil.disk_usage('/').percent
                self._metrics.network_io = dict(psutil.net_io_counters()._asdict())
                self._metrics.thread_count = process.num_threads()
                self._metrics.handle_count = process.num_handles()
                
                # Calculate cost estimate
                runtime_hours = (time.time() - self._start_time) / 3600
                memory_cost = self._metrics.memory_used * self._cost_per_mb_hour * runtime_hours
                cpu_cost = self._metrics.cpu_percent / 100 * self._cost_per_cpu_hour * runtime_hours
                self._metrics.cost_estimate = memory_cost + cpu_cost
                
                # Store historical data
                self._history.append(ResourceMetrics(**self._metrics.__dict__))
                if len(self._history) > 1000:  # Keep last 1000 samples
                    self._history.pop(0)
                    
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        with self._lock:
            return self._metrics
    
    def get_metrics_history(self) -> List[ResourceMetrics]:
        """Get historical metrics data."""
        with self._lock:
            return self._history.copy()
    
    def get_average_metrics(self, window_minutes: float = 5.0) -> Optional[ResourceMetrics]:
        """Calculate average metrics over the specified time window."""
        with self._lock:
            if not self._history:
                return None
                
            window_samples = int(window_minutes * 60 / self._sampling_interval)
            relevant_samples = self._history[-window_samples:] if window_samples < len(self._history) else self._history
            
            if not relevant_samples:
                return None
                
            avg_metrics = ResourceMetrics()
            avg_metrics.cpu_percent = sum(m.cpu_percent for m in relevant_samples) / len(relevant_samples)
            avg_metrics.memory_used = sum(m.memory_used for m in relevant_samples) / len(relevant_samples)
            avg_metrics.memory_available = sum(m.memory_available for m in relevant_samples) / len(relevant_samples)
            avg_metrics.disk_usage = sum(m.disk_usage for m in relevant_samples) / len(relevant_samples)
            avg_metrics.thread_count = int(sum(m.thread_count for m in relevant_samples) / len(relevant_samples))
            avg_metrics.handle_count = int(sum(m.handle_count for m in relevant_samples) / len(relevant_samples))
            avg_metrics.cost_estimate = sum(m.cost_estimate for m in relevant_samples) / len(relevant_samples)
            
            return avg_metrics
    
    def get_resource_warnings(self) -> List[str]:
        """Get list of resource utilization warnings."""
        warnings = []
        metrics = self.get_current_metrics()
        
        if metrics.cpu_percent > 80:
            warnings.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
        if metrics.memory_used / (metrics.memory_used + metrics.memory_available) > 0.85:
            warnings.append(f"High memory usage: {metrics.memory_used:.1f}MB")
            
        if metrics.disk_usage > 90:
            warnings.append(f"High disk usage: {metrics.disk_usage:.1f}%")
            
        if metrics.thread_count > 100:
            warnings.append(f"High thread count: {metrics.thread_count}")
            
        return warnings

    def estimate_monthly_cost(self) -> float:
        """Estimate monthly cost based on current usage patterns."""
        with self._lock:
            if not self._history:
                return 0.0
                
            avg_metrics = self.get_average_metrics(window_minutes=60)  # Use last hour for projection
            if not avg_metrics:
                return 0.0
                
            hours_per_month = 730  # Average hours in a month
            memory_cost = avg_metrics.memory_used * self._cost_per_mb_hour * hours_per_month
            cpu_cost = avg_metrics.cpu_percent / 100 * self._cost_per_cpu_hour * hours_per_month
            
            return memory_cost + cpu_cost

# Global monitor instance
resource_monitor = ResourceMonitor()

async def start_monitoring():
    """Start global resource monitoring."""
    await resource_monitor.start_monitoring()

if __name__ == "__main__":
    async def main():
        await start_monitoring()
        try:
            while True:
                metrics = resource_monitor.get_current_metrics()
                print(f"CPU: {metrics.cpu_percent:.1f}% | Memory: {metrics.memory_used:.1f}MB")
                print(f"Estimated cost: ${metrics.cost_estimate:.4f}")
                warnings = resource_monitor.get_resource_warnings()
                if warnings:
                    print("Warnings:", warnings)
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            await resource_monitor.stop_monitoring()
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())