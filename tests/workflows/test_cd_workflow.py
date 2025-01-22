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

def test_cd_workflow_structure():
    """Test CD workflow has required jobs and steps"""
    workflow = load_workflow('cd')
    
    assert 'deploy' in workflow['jobs']
    deploy_job = workflow['jobs']['deploy']
    
    # Get all step names
    steps = [
        step.get('name', '') if isinstance(step, dict) else ''
        for step in deploy_job['steps']
    ]
    
    # Verify required steps exist
    required_steps = [
        'Set up QEMU',
        'Set up Docker Buildx',
        'Cache Docker layers',
        'Login to DockerHub',
        'Build and push Docker images',
        'Move cache',
        'Deploy to production'
    ]
    
    for required in required_steps:
        assert any(required in step for step in steps), f"Missing step: {required}"

def test_cd_workflow_triggers():
    """Test CD workflow triggers are correctly configured"""
    workflow = load_workflow('cd')
    
    assert 'push' in workflow['on']
    assert 'branches' in workflow['on']['push']
    assert 'tags' in workflow['on']['push']
    assert workflow['on']['push']['tags'] == ['v*']