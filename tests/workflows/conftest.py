import pytest
import os
import yaml


@pytest.fixture
def workflow_dir():
    """Return the path to the workflows directory"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        ".github",
        "workflows",
    )


@pytest.fixture
def load_workflow(workflow_dir):
    """Fixture to load workflow files"""

    def _load(name):
        with open(os.path.join(workflow_dir, f"{name}.yml"), "r") as f:
            return yaml.safe_load(f)

    return _load
