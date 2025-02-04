from typing import Callable, Optional, Dict, List
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass
import sqlite3
from collections import deque

@dataclass
class FailureEvent:
    timestamp: datetime
    error_type: str
    context: Dict
    severity: float

class AICircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 half_open_timeout: int = 30):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_timeout = half_open_timeout
        self._state = "CLOSED"
        self._last_failure_time = None
        self._failure_count = 0
        self._lock = threading.Lock()
        self._failure_history = deque(maxlen=100)
        self._setup_db()

    def _setup_db(self):
        self._conn = sqlite3.connect('circuit_breaker.db', check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS failure_patterns (
                error_type TEXT,
                context_pattern TEXT,
                severity REAL,
                frequency INTEGER,
                PRIMARY KEY (error_type, context_pattern)
            )
        """)

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with self._lock:
                if not self._can_execute():
                    raise Exception("Circuit breaker is OPEN")
                
                try:
                    result = func(*args, **kwargs)
                    self._handle_success()
                    return result
                except Exception as e:
                    self._handle_failure(e, {"args": args, "kwargs": kwargs})
                    raise
        return wrapper

    def _can_execute(self) -> bool:
        if self._state == "CLOSED":
            return True

        if self._state == "OPEN":
            if (datetime.now() - self._last_failure_time > 
                timedelta(seconds=self._recovery_timeout)):
                self._state = "HALF_OPEN"
                return True
            return False

        # HALF_OPEN state
        if datetime.now() - self._last_failure_time > 
           timedelta(seconds=self._half_open_timeout):
            self._state = "CLOSED"
            return True
        return True

    def _handle_success(self):
        if self._state == "HALF_OPEN":
            self._state = "CLOSED"
        self._failure_count = 0

    def _handle_failure(self, error: Exception, context: Dict):
        self._last_failure_time = datetime.now()
        error_type = type(error).__name__
        
        # Calculate severity based on historical patterns
        severity = self._calculate_severity(error_type, context)
        
        # Record failure event
        event = FailureEvent(
            timestamp=self._last_failure_time,
            error_type=error_type,
            context=context,
            severity=severity
        )
        self._failure_history.append(event)
        
        # Update failure patterns in database
        self._update_failure_patterns(event)
        
        # Adjust failure count based on severity
        self._failure_count += severity
        
        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"

    def _calculate_severity(self, error_type: str, context: Dict) -> float:
        # Query historical patterns
        cursor = self._conn.execute(
            "SELECT severity, frequency FROM failure_patterns WHERE error_type = ?",
            (error_type,)
        )
        patterns = cursor.fetchall()
        
        if not patterns:
            return 1.0
        
        # Calculate weighted severity
        total_freq = sum(freq for _, freq in patterns)
        weighted_severity = sum(sev * freq for sev, freq in patterns) / total_freq
        
        return max(0.1, min(2.0, weighted_severity))

    def _update_failure_patterns(self, event: FailureEvent):
        self._conn.execute("""
            INSERT INTO failure_patterns (error_type, context_pattern, severity, frequency)
            VALUES (?, ?, ?, 1)
            ON CONFLICT (error_type, context_pattern) DO UPDATE
            SET frequency = frequency + 1,
                severity = (severity + ?) / 2
        """, (event.error_type, str(event.context), event.severity, event.severity))
        self._conn.commit()

    def get_state(self) -> str:
        return self._state

    def reset(self):
        with self._lock:
            self._state = "CLOSED"
            self._failure_count = 0
            self._last_failure_time = None
            self._failure_history.clear()

    def __del__(self):
        self._conn.close()