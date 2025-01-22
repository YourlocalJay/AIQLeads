import pytest
from unittest.mock import patch, MagicMock
import yaml
import os

def load_workflow(name):
    """Helper to load workflow file"""
    workflow_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        '.github', 'workflows', f'{name}.yml'
    )
    with open(workflow_path, 'r') as f:
        return yaml.safe_load(f)

def test_ci_workflow_structure():
    """Test CI workflow has required jobs and steps"""
    workflow = load_workflow('ci')
    
    assert 'test' in workflow['jobs']
    test_job = workflow['jobs']['test']
    
    # Verify required services
    assert 'postgres' in test_job['services']
    assert 'redis' in test_job['services']
    assert 'elasticsearch' in test_job['services']
    
    # Get all step names
    steps = [
        step.get('name', '') if isinstance(step, dict) else ''
        for step in test_job['steps']
    ]
    
    # Verify required steps exist
    required_steps = [
        'Set up Python 3.10',
        'Cache dependencies',
        'Install dependencies',
        'Check code formatting',
        'Run tests with coverage',
        'Upload coverage to Codecov'
    ]
    
    for required in required_steps:
        assert any(required in step for step in steps), f"Missing step: {required}"

def test_ci_workflow_python_version():
    """Test Python version is correctly specified"""
    workflow = load_workflow('ci')
    python_step = next(
        step for step in workflow['jobs']['test']['steps']
        if step.get('name') == 'Set up Python 3.10'
    )
    assert python_step['with']['python-version'] == '3.10'