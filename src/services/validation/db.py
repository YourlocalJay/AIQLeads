from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session


def optimize_validation_query(session: Session, query: str) -> str:
    """Optimize validation queries using execution plan analysis"""
    execution_plan = session.execute(text(f"EXPLAIN ANALYZE {query}")).fetchall()

    # Analyze execution plan and suggest optimizations
    optimized_query = query
    if "Seq Scan" in str(execution_plan):
        # Add appropriate indexes
        optimized_query = f"CREATE INDEX IF NOT EXISTS idx_validation ON validation_results (id, status);\n{query}"

    return optimized_query


def batch_validation_queries(queries: List[str], batch_size: int = 1000) -> List[str]:
    """Batch multiple validation queries for better performance"""
    return [
        ";".join(queries[i : i + batch_size])
        for i in range(0, len(queries), batch_size)
    ]


def cache_validation_results(results: Dict[str, Any], ttl: int = 3600) -> None:
    """Cache validation results with Redis"""
    cache_key = f'validation:{results["id"]}'
    redis_client.setex(cache_key, ttl, json.dumps(results))
