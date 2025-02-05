from prometheus_client import Counter, Gauge, Histogram

# Performance metrics
LEADS_PROCESSED = Counter(
    "aggregator_leads_processed_total",
    "Total number of leads processed",
    ["source", "status"],
)

PROCESSING_TIME = Histogram(
    "aggregator_processing_seconds",
    "Time spent processing leads",
    ["operation"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
)

MEMORY_USAGE = Gauge(
    "aggregator_memory_bytes", "Memory usage by component", ["component"]
)

ACTIVE_WORKERS = Gauge(
    "aggregator_active_workers", "Number of active worker threads", ["type"]
)

ERROR_COUNTER = Counter(
    "aggregator_errors_total", "Total number of errors", ["source", "type"]
)


def record_processing_time(operation: str, duration: float) -> None:
    """Record the time taken for a processing operation"""
    PROCESSING_TIME.labels(operation=operation).observe(duration)


def increment_leads_processed(source: str, status: str = "success") -> None:
    """Increment the leads processed counter"""
    LEADS_PROCESSED.labels(source=source, status=status).inc()


def update_memory_usage(component: str, bytes_used: int) -> None:
    """Update memory usage gauge"""
    MEMORY_USAGE.labels(component=component).set(bytes_used)


def set_active_workers(worker_type: str, count: int) -> None:
    """Set the number of active workers"""
    ACTIVE_WORKERS.labels(type=worker_type).set(count)


def record_error(source: str, error_type: str) -> None:
    """Record an error occurrence"""
    ERROR_COUNTER.labels(source=source, type=error_type).inc()
