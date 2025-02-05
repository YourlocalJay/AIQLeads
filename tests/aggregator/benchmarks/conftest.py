import pytest
import psutil
import gc
from typing import Dict, Any


def pytest_benchmark_update_machine_info(
    config: Any, machine_info: Dict[str, Any]
) -> None:
    """Update machine info with additional system metrics"""
    cpu_info = psutil.cpu_freq()
    memory = psutil.virtual_memory()

    machine_info.update(
        {
            "cpu": {
                "frequency": {
                    "current": cpu_info.current if cpu_info else None,
                    "min": cpu_info.min if cpu_info else None,
                    "max": cpu_info.max if cpu_info else None,
                },
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent_used": memory.percent,
            },
        }
    )


@pytest.fixture(autouse=True)
def clear_memory():
    """Fixture to clear memory before each benchmark test"""
    gc.collect()
    yield
    gc.collect()


@pytest.fixture
def benchmark_thresholds():
    """Define performance thresholds for benchmarks"""
    return {
        "parser": {
            "min_throughput": 100,  # leads/second
            "max_latency": 0.01,  # seconds per lead
        },
        "scraper": {
            "min_throughput": 50,  # requests/second
            "max_latency": 0.1,  # seconds per request
        },
        "pipeline": {
            "min_throughput": 30,  # leads/second
            "max_duration": 30,  # seconds for complete pipeline
        },
    }


@pytest.fixture
def benchmark_metrics():
    """Fixture for collecting detailed performance metrics"""
    return {
        "memory_samples": [],
        "cpu_samples": [],
        "latency_samples": [],
        "throughput_samples": [],
        "error_samples": [],
    }


def pytest_benchmark_group_stats(
    config: Any, benchmarks: list, group_by: str
) -> Dict[str, Any]:
    """Calculate additional statistics for benchmark groups"""
    stats = {}
    for benchmark in benchmarks:
        group = benchmark[group_by]
        if group not in stats:
            stats[group] = {
                "min_throughput": float("inf"),
                "max_throughput": 0,
                "total_errors": 0,
                "samples": [],
            }

        # Update statistics
        throughput = 1 / benchmark["stats"]["mean"]
        stats[group]["min_throughput"] = min(stats[group]["min_throughput"], throughput)
        stats[group]["max_throughput"] = max(stats[group]["max_throughput"], throughput)
        stats[group]["samples"].append(benchmark["stats"])

    return stats
