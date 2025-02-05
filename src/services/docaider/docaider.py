import os
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.cache.redis_service import AIQRedisCache


class DocaiderMetadata(BaseModel):
    """Comprehensive documentation metadata model"""

    id: str = Field(
        default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()
    )
    title: str
    description: str
    version: str = "1.0.0"
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    author: str = settings.SYSTEM_AUTHOR
    path: Optional[str] = None
    visibility: str = "internal"  # public, internal, private
    dependencies: List[str] = []


class Docaider:
    """Advanced documentation management service for AIQLeads"""

    def __init__(
        self,
        cache: Optional[AIQRedisCache] = None,
        db_session: Optional[AsyncSession] = None,
    ):
        self.cache = cache or AIQRedisCache()
        self.db_session = db_session
        self.docs_root = Path(settings.DOCS_ROOT)
        self.docs_root.mkdir(parents=True, exist_ok=True)

    async def generate_docs(
        self, module: Any, metadata: Optional[DocaiderMetadata] = None
    ) -> DocaiderMetadata:
        """Generate documentation for a given module"""
        if not metadata:
            metadata = DocaiderMetadata(
                title=module.__name__,
                description=module.__doc__ or "Undocumented module",
            )

        # Extract docstrings and type hints
        doc_content = self._extract_module_docs(module)

        # Generate markdown documentation
        markdown_path = self._write_markdown(metadata, doc_content)

        # Update metadata
        metadata.path = str(markdown_path)
        metadata.updated_at = datetime.now()

        # Cache documentation metadata
        await self._cache_doc_metadata(metadata)

        return metadata

    def _extract_module_docs(self, module: Any) -> Dict[str, Any]:
        """Extract comprehensive module documentation"""
        import inspect
        import typing

        doc_content = {"description": module.__doc__, "functions": {}, "classes": {}}

        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) or inspect.isclass(obj):
                doc_entry = {
                    "docstring": obj.__doc__,
                    "signature": str(inspect.signature(obj)),
                    "annotations": {
                        k: str(v) for k, v in typing.get_type_hints(obj).items()
                    },
                }

                if inspect.isfunction(obj):
                    doc_content["functions"][name] = doc_entry
                else:
                    doc_content["classes"][name] = doc_entry

        return doc_content

    def _write_markdown(
        self, metadata: DocaiderMetadata, doc_content: Dict[str, Any]
    ) -> Path:
        """Convert documentation to markdown"""
        markdown = f"""# {metadata.title}

**Version:** {metadata.version}
**Author:** {metadata.author}
**Created:** {metadata.created_at}

{doc_content.get('description', 'No description available')}

## Functions

"""
        for func_name, func_data in doc_content.get("functions", {}).items():
            markdown += f"### {func_name}\n\n"
            markdown += f"**Signature:** `{func_data['signature']}`\n\n"
            markdown += f"**Docstring:** {func_data['docstring'] or 'No docstring'}\n\n"
            markdown += "**Parameters:**\n"
            for param, annotation in func_data["annotations"].items():
                markdown += f"- `{param}`: {annotation}\n"
            markdown += "\n"

        markdown += "## Classes\n\n"
        for class_name, class_data in doc_content.get("classes", {}).items():
            markdown += f"### {class_name}\n\n"
            markdown += (
                f"**Docstring:** {class_data['docstring'] or 'No docstring'}\n\n"
            )

        # Write markdown file
        file_name = f"{metadata.id}_{metadata.title.lower().replace(' ', '_')}.md"
        file_path = self.docs_root / file_name

        with open(file_path, "w") as f:
            f.write(markdown)

        return file_path

    async def _cache_doc_metadata(self, metadata: DocaiderMetadata):
        """Cache documentation metadata"""
        cache_key = f"docaider:metadata:{metadata.id}"
        await self.cache.set(
            cache_key, metadata.model_dump(), ttl=settings.DOCS_CACHE_TTL
        )

    async def search_docs(
        self, query: str, tags: List[str] = [], visibility: str = "internal"
    ) -> List[DocaiderMetadata]:
        """Advanced documentation search"""
        # In a real implementation, this would use a more sophisticated search index
        results = []
        for doc_file in self.docs_root.glob("*.md"):
            with open(doc_file, "r") as f:
                content = f.read().lower()
                if query.lower() in content:
                    # Retrieve metadata from cache or regenerate
                    metadata_id = doc_file.stem.split("_")[0]
                    metadata = await self.cache.get(f"docaider:metadata:{metadata_id}")
                    if metadata:
                        metadata = DocaiderMetadata(**metadata)
                        if (
                            not tags or any(tag in metadata.tags for tag in tags)
                        ) and metadata.visibility == visibility:
                            results.append(metadata)
        return results

    async def version_docs(
        self, doc_id: str, changes: Dict[str, Any]
    ) -> DocaiderMetadata:
        """Version and update documentation"""
        # Retrieve existing metadata
        current_metadata = await self.cache.get(f"docaider:metadata:{doc_id}")

        if not current_metadata:
            raise ValueError(f"Documentation with ID {doc_id} not found")

        current_metadata = DocaiderMetadata(**current_metadata)

        # Update version and metadata
        current_metadata.version = self._increment_version(current_metadata.version)
        current_metadata.updated_at = datetime.now()

        for key, value in changes.items():
            if hasattr(current_metadata, key):
                setattr(current_metadata, key, value)

        # Re-generate documentation with updated metadata
        module_path = current_metadata.path
        if module_path and os.path.exists(module_path):
            # You would need to implement module loading based on path
            # This is a placeholder
            module = self._load_module_from_path(module_path)
            await self.generate_docs(module, current_metadata)

        return current_metadata

    def _increment_version(self, current_version: str) -> str:
        """Semantic versioning incrementer"""
        major, minor, patch = map(int, current_version.split("."))
        patch += 1
        if patch > 99:
            patch = 0
            minor += 1
        if minor > 99:
            minor = 0
            major += 1
        return f"{major}.{minor}.{patch}"

    def _load_module_from_path(self, path: str) -> Any:
        """Dynamically load module - placeholder implementation"""
        # In a real implementation, you'd use importlib or custom module loader
        raise NotImplementedError("Dynamic module loading not implemented")
