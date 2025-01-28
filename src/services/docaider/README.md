# Docaider: Advanced Documentation Management Service

## Overview

Docaider is a comprehensive documentation management service designed for the AIQLeads platform. It provides intelligent documentation generation, metadata tracking, and advanced search capabilities.

## Key Features

- **Automatic Documentation Generation**
  - Extracts docstrings, type hints, and signatures
  - Generates markdown documentation
  - Supports semantic versioning

- **Metadata Management**
  - Pydantic-based metadata model
  - Redis caching for quick retrieval
  - Visibility control (public, internal, private)

- **Advanced Search**
  - Full-text search across documentation
  - Filtering by tags and visibility

- **Versioning System**
  - Automatic version incrementation
  - Comprehensive metadata tracking

## Usage Example

```python
from app.services.docaider import Docaider, DocaiderMetadata

async def document_module():
    docaider = Docaider()
    metadata = await docaider.generate_docs(
        module=YourModule,
        metadata=DocaiderMetadata(
            title="Lead Processing Module",
            description="Advanced lead processing capabilities",
            tags=["leads", "processing", "ml"]
        )
    )
```

## Integration Guidelines

1. Ensure Redis is configured in your application
2. Set documentation root path in configuration
3. Use Docaider service for automatic documentation generation

## Configuration

```python
# In app/core/config.py
class Settings:
    DOCS_ROOT: str = "/app/docs"
    DOCS_CACHE_TTL: int = 86400  # 24 hours
    SYSTEM_AUTHOR: str = "AIQLeads Documentation Team"
```

## Performance Considerations

- Caches documentation metadata in Redis
- Generates markdown files for persistent storage
- Supports efficient full-text search

## Future Roadmap

- ML-powered documentation complexity analysis
- Enhanced dependency tracking
- Advanced search indexing
