import pytest
import os
from datetime import datetime
from typing import Any

from app.services.docaider import Docaider, DocaiderMetadata
from app.services.cache.redis_service import AIQRedisCache

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

    # Validate markdown content
    with open(metadata.path, 'r') as f:
        content = f.read()
        assert "Test Module Documentation" in content
        assert "sample_function" in content
        assert "SampleClass" in content

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
            "tags": ["updated", "test"]
        }
    )

    # Validate versioning
    assert updated_metadata.version == "1.0.1"
    assert updated_metadata.description == "Updated module description"
    assert updated_metadata.tags == ["updated", "test"]
    assert updated_metadata.updated_at > initial_metadata.updated_at

@pytest.mark.asyncio
async def test_docaider_search():
    """Test documentation search functionality"""
    docaider = Docaider()
    
    # Generate multiple test documents
    doc1 = await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Search Test Module 1",
            description="Module about lead processing",
            tags=["leads", "processing"]
        )
    )
    
    doc2 = await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Search Test Module 2",
            description="Module about market analysis",
            tags=["market", "analysis"]
        )
    )

    # Search by query
    lead_results = await docaider.search_docs(query="lead processing")
    assert len(lead_results) > 0
    assert any(doc.title == "Search Test Module 1" for doc in lead_results)

    # Search by tags
    market_results = await docaider.search_docs(tags=["market"])
    assert len(market_results) > 0
    assert any(doc.title == "Search Test Module 2" for doc in market_results)

@pytest.mark.asyncio
async def test_docaider_caching():
    """Test documentation metadata caching"""
    cache = AIQRedisCache()
    docaider = Docaider(cache=cache)

    # Generate documentation
    metadata = await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Cached Module",
            description="Module for caching test"
        )
    )

    # Retrieve from cache
    cached_metadata = await cache.get(f"docaider:metadata:{metadata.id}")
    
    assert cached_metadata is not None
    assert cached_metadata['title'] == "Cached Module"
    assert cached_metadata['version'] == "1.0.0"

@pytest.mark.asyncio
async def test_docaider_error_handling():
    """Test error handling in documentation service"""
    docaider = Docaider()

    # Test version docs with non-existent ID
    with pytest.raises(ValueError, match="Documentation with ID .* not found"):
        await docaider.version_docs(
            doc_id="non_existent_id",
            changes={"description": "This should fail"}
        )

def test_version_increment():
    """Test semantic version incrementing"""
    docaider = Docaider()

    # Test standard increment
    assert docaider._increment_version("1.0.0") == "1.0.1"
    
    # Test minor version rollover
    assert docaider._increment_version("1.0.99") == "1.1.0"
    
    # Test major version rollover
    assert docaider._increment_version("1.99.99") == "2.0.0"

@pytest.mark.asyncio
async def test_docaider_visibility():
    """Test documentation visibility filtering"""
    docaider = Docaider()

    # Generate documents with different visibility
    public_doc = await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Public Document",
            description="Publicly visible document",
            visibility="public"
        )
    )

    internal_doc = await docaider.generate_docs(
        module=TestModule,
        metadata=DocaiderMetadata(
            title="Internal Document",
            description="Internally visible document",
            visibility="internal"
        )
    )

    # Search with visibility filter
    public_results = await docaider.search_docs(
        query="document", 
        visibility="public"
    )
    internal_results = await docaider.search_docs(
        query="document", 
        visibility="internal"
    )

    assert any(doc.title == "Public Document" for doc in public_results)
    assert any(doc.title == "Internal Document" for doc in internal_results)
    assert not any(doc.visibility != "public" for doc in public_results)
    assert not any(doc.visibility != "internal" for doc in internal_results)
