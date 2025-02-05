from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sqlite3
import threading
from dataclasses import dataclass
import json


@dataclass
class MetricPoint:
    timestamp: datetime
    value: float
    context: Dict


class AIResourceMonitor:
    def __init__(self, db_path: str = "ai_metrics.db"):
        self._lock = threading.Lock()
        self._setup_db(db_path)

    def _setup_db(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)

        # Metrics table for raw data
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                timestamp TIMESTAMP,
                metric_name TEXT,
                value REAL,
                context TEXT,
                PRIMARY KEY (timestamp, metric_name)
            )
        """
        )

        # Aggregated metrics for analysis
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_aggregates (
                period_start TIMESTAMP,
                metric_name TEXT,
                avg_value REAL,
                min_value REAL,
                max_value REAL,
                count INTEGER,
                context TEXT,
                PRIMARY KEY (period_start, metric_name)
            )
        """
        )

        # Anomaly detection thresholds
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS anomaly_thresholds (
                metric_name TEXT PRIMARY KEY,
                lower_bound REAL,
                upper_bound REAL,
                last_updated TIMESTAMP
            )
        """
        )

    def record_metric(
        self, metric_name: str, value: float, context: Optional[Dict] = None
    ):
        timestamp = datetime.now()
        context_json = json.dumps(context) if context else "{}"

        with self._lock:
            # Record raw metric
            self._conn.execute(
                "INSERT INTO metrics (timestamp, metric_name, value, context) VALUES (?, ?, ?, ?)",
                (timestamp, metric_name, value, context_json),
            )

            # Update aggregates
            self._update_aggregates(metric_name, value, context_json)

            # Check for anomalies
            self._check_anomaly(metric_name, value)

            self._conn.commit()

    def _update_aggregates(self, metric_name: str, value: float, context_json: str):
        period_start = datetime.now().replace(minute=0, second=0, microsecond=0)

        self._conn.execute(
            """
            INSERT INTO metric_aggregates 
                (period_start, metric_name, avg_value, min_value, max_value, count, context)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT (period_start, metric_name) DO UPDATE
            SET avg_value = ((avg_value * count + ?) / (count + 1)),
                min_value = MIN(min_value, ?),
                max_value = MAX(max_value, ?),
                count = count + 1
        """,
            (
                period_start,
                metric_name,
                value,
                value,
                value,
                context_json,
                value,
                value,
                value,
            ),
        )

    def _check_anomaly(self, metric_name: str, value: float):
        # Get current thresholds
        cursor = self._conn.execute(
            "SELECT lower_bound, upper_bound FROM anomaly_thresholds WHERE metric_name = ?",
            (metric_name,),
        )
        thresholds = cursor.fetchone()

        if not thresholds:
            # Calculate initial thresholds from historical data
            self._update_thresholds(metric_name)
            return

        lower_bound, upper_bound = thresholds
        if value < lower_bound or value > upper_bound:
            self._record_anomaly(metric_name, value, lower_bound, upper_bound)

    def _update_thresholds(self, metric_name: str):
        # Get historical data for the past 24 hours
        day_ago = datetime.now() - timedelta(days=1)
        cursor = self._conn.execute(
            "SELECT value FROM metrics WHERE metric_name = ? AND timestamp > ?",
            (metric_name, day_ago),
        )
        values = [row[0] for row in cursor.fetchall()]

        if not values:
            return

        # Calculate mean and standard deviation
        mean = sum(values) / len(values)
        std_dev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

        # Set thresholds at 3 standard deviations
        lower_bound = mean - 3 * std_dev
        upper_bound = mean + 3 * std_dev

        self._conn.execute(
            """
            INSERT INTO anomaly_thresholds (metric_name, lower_bound, upper_bound, last_updated)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (metric_name) DO UPDATE
            SET lower_bound = ?,
                upper_bound = ?,
                last_updated = ?
        """,
            (
                metric_name,
                lower_bound,
                upper_bound,
                datetime.now(),
                lower_bound,
                upper_bound,
                datetime.now(),
            ),
        )

    def _record_anomaly(
        self, metric_name: str, value: float, lower_bound: float, upper_bound: float
    ):
        # Here you would implement anomaly recording and alerting
        # For now, we'll just print the anomaly
        print(
            f"ANOMALY DETECTED: {metric_name} = {value} (bounds: {lower_bound}, {upper_bound})"
        )

    def get_metrics(
        self, metric_name: str, start_time: datetime, end_time: datetime = None
    ) -> List[MetricPoint]:
        if end_time is None:
            end_time = datetime.now()

        cursor = self._conn.execute(
            "SELECT timestamp, value, context FROM metrics WHERE metric_name = ? AND timestamp BETWEEN ? AND ?",
            (metric_name, start_time, end_time),
        )

        return [
            MetricPoint(
                timestamp=datetime.fromisoformat(row[0]),
                value=row[1],
                context=json.loads(row[2]),
            )
            for row in cursor.fetchall()
        ]

    def get_aggregates(
        self, metric_name: str, start_time: datetime, end_time: datetime = None
    ) -> Dict:
        if end_time is None:
            end_time = datetime.now()

        cursor = self._conn.execute(
            """
            SELECT 
                AVG(avg_value) as total_avg,
                MIN(min_value) as total_min,
                MAX(max_value) as total_max,
                SUM(count) as total_count
            FROM metric_aggregates 
            WHERE metric_name = ? AND period_start BETWEEN ? AND ?
        """,
            (metric_name, start_time, end_time),
        )

        row = cursor.fetchone()
        return {
            "average": row[0],
            "minimum": row[1],
            "maximum": row[2],
            "count": row[3],
        }

    def __del__(self):
        self._conn.close()
