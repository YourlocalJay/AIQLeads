import pytest
import os
from datetime import datetime
from typing import Any

from app.services.docaider import Docaider, DocaiderMetadata

class TestModule:
    """Sample module for testing documentation generation"""
    def sample_function(self, param1: str, param2: int) -> bool:
        """A sample function for testing documentation

        Args:
            param1: First parameter
            param2: Second parameter

        Returns:
            Always returns True
        """
        return True

    class SampleClass:
        """A sample class for testing documentation"""
        def __init__(self, name: str):
            self.name = name

@pytest.mark.asyncio
async def test_docaider_generation():
    """Test basic documentation generation"""
    docaider = Docaider()
    metadata = await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Test Module Documentation",
            description="Documentation for test module",
            tags=["test", "documentation"]
        )
    )

    # Validate metadata
    assert metadata.title == "Test Module Documentation"
    assert metadata.tags == ["test", "documentation"]
    assert metadata.version == "1.0.0"
    assert metadata.path is not None
    assert os.path.exists(metadata.path)

@pytest.mark.asyncio
async def test_docaider_versioning():
    """Test documentation versioning"""
    docaider = Docaider()
    
    # Initial generation
    initial_metadata = await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Versioned Module",
            description="Module for versioning test"
        )
    )

    # Version the documentation
    updated_metadata = await docaider.version_docs(
        doc_id=initial_metadata.id,
        changes={
            "description": "Updated module description",
            "tags": ["updated", "versioning"]
        }
    )

    # Validate versioning
    assert updated_metadata.version != initial_metadata.version
    assert updated_metadata.description == "Updated module description"
    assert updated_metadata.tags == ["updated", "versioning"]
    assert updated_metadata.version.startswith("1.0.")

@pytest.mark.asyncio
async def test_docaider_search():
    """Test documentation search functionality"""
    docaider = Docaider()
    
    # Generate multiple test docs
    await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Search Test Module 1",
            description="First test module for search",
            tags=["search", "test1"]
        )
    )
    await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Search Test Module 2",
            description="Second test module for search",
            tags=["search", "test2"]
        )
    )

    # Search by query
    query_results = await docaider.search_docs(query="test module")
    assert len(query_results) >= 2

    # Search by tags
    tag_results = await docaider.search_docs(tags=["search"])
    assert len(tag_results) >= 2

    # Search with visibility
    visibility_results = await docaider.search_docs(
        query="test module", 
        visibility="internal"
    )
    assert len(visibility_results) >= 2

def test_version_increment():
    """Test semantic version incrementing"""
    docaider = Docaider()
    
    # Test standard increments
    assert docaider._increment_version("1.0.0") == "1.0.1"
    assert docaider._increment_version("1.0.99") == "1.1.0"
    assert docaider._increment_version("1.99.99") == "2.0.0"

@pytest.mark.asyncio
async def test_markdown_generation():
    """Test markdown documentation generation"""
    docaider = Docaider()
    
    metadata = await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Markdown Test Module",
            description="Module for testing markdown generation"
        )
    )

    # Verify markdown file exists
    assert os.path.exists(metadata.path)
    
    # Read markdown content
    with open(metadata.path, 'r') as f:
        markdown_content = f.read()
    
    # Check for key markdown elements
    assert "# Markdown Test Module" in markdown_content
    assert "## Functions" in markdown_content
    assert "## Classes" in markdown_content
    assert "sample_function" in markdown_content
