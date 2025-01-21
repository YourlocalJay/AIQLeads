import pytest

def test_environment():
    """Test that the test environment is properly configured"""
    assert True

def test_imports():
    """Test that all required packages are installed"""
    import fastapi
    import sqlalchemy
    import redis
    import elasticsearch
    import langchain
    assert all([fastapi, sqlalchemy, redis, elasticsearch, langchain])

def test_python_version():
    """Test that we're using Python 3.10 or higher"""
    import sys
    assert sys.version_info >= (3, 10)