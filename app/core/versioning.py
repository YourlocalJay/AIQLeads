"""
Feature versioning system for AIQLeads.
Handles schema validation, version tracking, and compatibility management.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import threading
from enum import Enum

logger = logging.getLogger(__name__)

class VersionStatus(Enum):
    """Feature version status."""
    ALPHA = "alpha"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    RETIRED = "retired"

@dataclass
class VersionInfo:
    """Information about a feature version."""
    major: int
    minor: int
    patch: int
    status: VersionStatus
    created_at: datetime
    schema_hash: str
    description: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)
    breaking_changes: List[str] = field(default_factory=list)
    migrations: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}-{self.status.value}"

class VersionError(Exception):
    """Base class for versioning errors."""
    pass

class SchemaError(VersionError):
    """Raised for schema validation errors."""
    pass

class MigrationError(VersionError):
    """Raised for migration errors."""
    pass

class FeatureVersioning:
    """
    Feature versioning system with schema validation and migration support.
    """
    
    def __init__(self, feature_name: str):
        self.feature_name = feature_name
        self._versions: Dict[str, VersionInfo] = {}
        self._current_version: Optional[str] = None
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_version(
        self,
        major: int,
        minor: int,
        patch: int,
        status: VersionStatus,
        schema: Dict[str, Any],
        description: str = "",
        dependencies: Dict[str, str] = None,
        breaking_changes: List[str] = None,
        migrations: List[str] = None
    ) -> str:
        """Register a new feature version."""
        with self._lock:
            version_str = f"{major}.{minor}.{patch}"
            if version_str in self._versions:
                raise VersionError(f"Version {version_str} already exists")

            # Generate schema hash
            schema_hash = hashlib.sha256(
                json.dumps(schema, sort_keys=True).encode()
            ).hexdigest()

            # Create version info
            version_info = VersionInfo(
                major=major,
                minor=minor,
                patch=patch,
                status=status,
                created_at=datetime.utcnow(),
                schema_hash=schema_hash,
                description=description,
                dependencies=dependencies or {},
                breaking_changes=breaking_changes or [],
                migrations=migrations or []
            )

            self._versions[version_str] = version_info
            self._schemas[version_str] = schema

            # Update current version if this is the first or a newer stable version
            if (not self._current_version or 
                (status == VersionStatus.STABLE and 
                self._is_newer_version(version_str, self._current_version))):
                self._current_version = version_str

            return version_str

    def validate_data(self, data: Dict[str, Any], version: Optional[str] = None) -> bool:
        """Validate data against version schema."""
        version = version or self._current_version
        if not version:
            raise VersionError("No version specified and no current version set")

        if version not in self._schemas:
            raise VersionError(f"Unknown version: {version}")

        try:
            self._validate_against_schema(data, self._schemas[version])
            return True
        except SchemaError as e:
            logger.error(f"Validation error for version {version}: {str(e)}")
            return False

    def _validate_against_schema(self, data: Dict[str, Any], schema: Dict[str, Any], path: str = ""):
        """Recursively validate data against schema."""
        for key, schema_value in schema.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check required fields
            if key not in data:
                if schema_value.get("required", True):
                    raise SchemaError(f"Missing required field: {current_path}")
                continue

            data_value = data[key]
            value_type = schema_value.get("type")

            # Validate type
            if value_type:
                if value_type == "object" and isinstance(data_value, dict):
                    self._validate_against_schema(
                        data_value,
                        schema_value.get("properties", {}),
                        current_path
                    )
                elif value_type == "array" and isinstance(data_value, list):
                    item_schema = schema_value.get("items", {})
                    for i, item in enumerate(data_value):
                        self._validate_against_schema(
                            {"value": item},
                            {"value": item_schema},
                            f"{current_path}[{i}]"
                        )
                elif not self._check_type(data_value, value_type):
                    raise SchemaError(
                        f"Invalid type for {current_path}. "
                        f"Expected {value_type}, got {type(data_value).__name__}"
                    )

            # Validate enum
            if "enum" in schema_value and data_value not in schema_value["enum"]:
                raise SchemaError(
                    f"Invalid value for {current_path}. "
                    f"Must be one of: {schema_value['enum']}"
                )

            # Validate pattern
            if "pattern" in schema_value:
                import re
                if not re.match(schema_value["pattern"], str(data_value)):
                    raise SchemaError(
                        f"Invalid format for {current_path}. "
                        f"Must match pattern: {schema_value['pattern']}"
                    )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        return isinstance(value, type_mapping.get(expected_type, object))

    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare two version strings."""
        v1_parts = list(map(int, version1.split(".")))
        v2_parts = list(map(int, version2.split(".")))
        return v1_parts > v2_parts

    def migrate_data(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Migrate data from one version to another."""
        to_version = to_version or self._current_version
        if not to_version:
            raise VersionError("No target version specified and no current version set")

        if from_version not in self._versions or to_version not in self._versions:
            raise VersionError("Invalid version specified")

        # Check if migration is needed
        if from_version == to_version:
            return data

        # Validate source data
        if not self.validate_data(data, from_version):
            raise MigrationError(f"Source data invalid for version {from_version}")

        # Find migration path
        migration_path = self._find_migration_path(from_version, to_version)
        if not migration_path:
            raise MigrationError(
                f"No migration path found from {from_version} to {to_version}"
            )

        # Apply migrations
        migrated_data = data.copy()
        for i in range(len(migration_path) - 1):
            current = migration_path[i]
            next_version = migration_path[i + 1]
            migrated_data = self._apply_migration(
                migrated_data,
                current,
                next_version
            )

        return migrated_data

    def _find_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """Find path of versions to migrate through."""
        # Simple implementation - could be enhanced with graph-based path finding
        all_versions = sorted(
            self._versions.keys(),
            key=lambda v: list(map(int, v.split(".")))
        )
        try:
            start_idx = all_versions.index(from_version)
            end_idx = all_versions.index(to_version)
            if start_idx <= end_idx:
                return all_versions[start_idx:end_idx + 1]
            return list(reversed(all_versions[end_idx:start_idx + 1]))
        except ValueError:
            return []

    def _apply_migration(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """Apply migration between adjacent versions."""
        version_info = self._versions[to_version]
        migrations = version_info.migrations

        migrated_data = data.copy()
        for migration in migrations:
            # Migration scripts would be implemented as separate functions
            # For now, we'll just pass the data through
            logger.info(f"Applying migration: {migration}")

        return migrated_data

    @property
    def current_version(self) -> Optional[str]:
        """Get current stable version."""
        return self._current_version

    def get_version_info(self, version: Optional[str] = None) -> Optional[VersionInfo]:
        """Get information about a specific version."""
        version = version or self._current_version
        return self._versions.get(version)

    def list_versions(self, status: Optional[VersionStatus] = None) -> List[str]:
        """List all registered versions, optionally filtered by status."""
        if status:
            return [
                v for v, info in self._versions.items()
                if info.status == status
            ]
        return list(self._versions.keys())

# Global registry for feature versions
version_registry: Dict[str, FeatureVersioning] = {}