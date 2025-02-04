"""
AI-enhanced circuit breaker implementation with dynamic failure detection
and intelligent recovery strategies.
"""
from typing import Optional, Dict, List, Tuple, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
import json
import sqlite3
from enum import Enum
from collections import deque
import threading
import numpy as np
from functools import wraps

logger = logging.getLogger(__name__)

[Previous code remains the same until AICircuitRegistry class...]

class AICircuitRegistry:
    """Registry for managing multiple AI circuit breakers."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AICircuitRegistry, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._circuits: Dict[str, AICircuitBreaker] = {}
            self._lock = threading.Lock()
            self.initialized = True
        
    async def get_circuit(
        self,
        name: str,
        failure_threshold: float = 0.5,
        recovery_timeout: float = 60.0,
        **kwargs
    ) -> AICircuitBreaker:
        """Get or create a circuit breaker."""
        with self._lock:
            if name not in self._circuits:
                self._circuits[name] = AICircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    **kwargs
                )
            return self._circuits[name]
            
    async def reset_all(self):
        """Reset all circuit breakers to closed state."""
        with self._lock:
            for circuit in self._circuits.values():
                circuit._state = CircuitState.CLOSED
                circuit.stats = AICircuitStats()
                circuit._last_failure_time = None
                circuit._half_open_start = None
                circuit._save_state()
                
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all circuits."""
        with self._lock:
            return {
                name: {
                    'state': circuit._state.value,
                    'total_requests': circuit.stats.total_requests,
                    'success_rate': circuit.stats.successful_requests / 
                                  max(circuit.stats.total_requests, 1),
                    'region_stats': circuit.stats.region_stats,
                    'priority_stats': circuit.stats.priority_stats
                }
                for name, circuit in self._circuits.items()
            }
            
    def remove_circuit(self, name: str):
        """Remove a circuit breaker from the registry."""
        with self._lock:
            if name in self._circuits:
                del self._circuits[name]

# Global registry instance
registry = AICircuitRegistry()

def ai_circuit_protected(
    circuit_name: str,
    priority_level: int = 0,
    failure_threshold: float = 0.5,
    recovery_timeout: float = 60.0
):
    """
    Decorator for protecting functions with AI circuit breaker.
    
    Args:
        circuit_name: Name of the circuit breaker
        priority_level: Priority level of the protected operation (0-10)
        failure_threshold: Failure rate threshold for tripping circuit
        recovery_timeout: Base recovery timeout in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            circuit = await registry.get_circuit(
                circuit_name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
            
            if not circuit.allow_request(priority_level):
                raise CircuitBreakerError(
                    f"Circuit {circuit_name} is open"
                )
            
            start_time = datetime.now()
            retry_count = 0
            error = None
            
            try:
                while retry_count < 3:  # Max 3 retries
                    try:
                        result = await func(*args, **kwargs)
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        # Extract region and lead_id from kwargs if available
                        region = kwargs.get('region')
                        lead_id = kwargs.get('lead_id')
                        
                        await circuit.on_success(
                            response_time,
                            region=region,
                            priority=priority_level
                        )
                        return result
                        
                    except Exception as e:
                        error = e
                        retry_count += 1
                        if retry_count < 3:
                            # Exponential backoff with jitter
                            delay = (2 ** retry_count) + random.uniform(0, 1)
                            await asyncio.sleep(delay)
                        
                # If we get here, all retries failed
                response_time = (datetime.now() - start_time).total_seconds()
                await circuit.on_failure(
                    error=error,
                    response_time=response_time,
                    retry_count=retry_count,
                    priority_level=priority_level,
                    region=kwargs.get('region'),
                    lead_id=kwargs.get('lead_id'),
                    model_version=kwargs.get('model_version')
                )
                raise error
                
            except Exception as e:
                response_time = (datetime.now() - start_time).total_seconds()
                await circuit.on_failure(
                    error=e,
                    response_time=response_time,
                    retry_count=retry_count,
                    priority_level=priority_level,
                    region=kwargs.get('region'),
                    lead_id=kwargs.get('lead_id'),
                    model_version=kwargs.get('model_version')
                )
                raise
                
        return wrapper
    return decorator

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker prevents operation."""
    pass
