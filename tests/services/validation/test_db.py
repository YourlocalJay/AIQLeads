import pytest
from src.services.validation.db import optimize_validation_query, batch_validation_queries

def test_query_optimization(db_session):
    query = 'SELECT * FROM validation_results WHERE status = "pending"'
    optimized = optimize_validation_query(db_session, query)
    assert 'CREATE INDEX' in optimized

def test_batch_queries():
    queries = ['SELECT 1', 'SELECT 2', 'SELECT 3']
    batched = batch_validation_queries(queries, batch_size=2)
    assert len(batched) == 2
    assert batched[0] == 'SELECT 1;SELECT 2'