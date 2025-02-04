"""
Unit tests for feature versioning system.
"""
import pytest
from datetime import datetime
from app.core.versioning import (
    FeatureVersioning,
    VersionStatus,
    VersionError,
    SchemaError,
    MigrationError
)

@pytest.fixture
def versioning():
    """Fixture providing a clean FeatureVersioning instance."""
    return FeatureVersioning("test_feature")

@pytest.fixture
def basic_schema():
    """Fixture providing a basic schema for testing."""
    return {
        "id": {
            "type": "string",
            "required": True,
            "pattern": "^[A-Z][a-z0-9_]+$"
        },
        "count": {
            "type": "integer",
            "required": False
        },
        "metadata": {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        }
    }

class TestFeatureVersioning:
    """Test suite for FeatureVersioning class."""

    def test_version_registration(self, versioning, basic_schema):
        """Test version registration."""
        version = versioning.register_version(
            major=1,
            minor=0,
            patch=0,
            status=VersionStatus.STABLE,
            schema=basic_schema,
            description="Initial version"
        )

        assert version == "1.0.0"
        assert versioning.current_version == "1.0.0"
        
        info = versioning.get_version_info("1.0.0")
        assert info.major == 1
        assert info.status == VersionStatus.STABLE
        assert info.created_at <= datetime.utcnow()

    def test_duplicate_version(self, versioning, basic_schema):
        """Test handling of duplicate version registration."""
        versioning.register_version(1, 0, 0, VersionStatus.STABLE, basic_schema)
        
        with pytest.raises(VersionError):
            versioning.register_version(1, 0, 0, VersionStatus.BETA, basic_schema)

    def test_schema_validation(self, versioning, basic_schema):
        """Test data validation against schema."""
        versioning.register_version(1, 0, 0, VersionStatus.STABLE, basic_schema)

        # Valid data
        valid_data = {
            "id": "Test_123",
            "count": 42,
            "metadata": {
                "tags": ["test", "validation"]
            }
        }
        assert versioning.validate_data(valid_data)

        # Invalid data - wrong ID format
        invalid_data = {
            "id": "invalid_id",
            "count": 42
        }
        assert not versioning.validate_data(invalid_data)

        # Invalid data - wrong type
        invalid_data = {
            "id": "Test_123",
            "count": "42"  # Should be integer
        }
        assert not versioning.validate_data(invalid_data)

    def test_version_comparison(self, versioning, basic_schema):
        """Test version comparison logic."""
        v1 = versioning.register_version(1, 0, 0, VersionStatus.STABLE, basic_schema)
        v2 = versioning.register_version(1, 1, 0, VersionStatus.STABLE, basic_schema)
        v3 = versioning.register_version(2, 0, 0, VersionStatus.BETA, basic_schema)

        assert versioning._is_newer_version(v2, v1)
        assert versioning._is_newer_version(v3, v2)
        assert not versioning._is_newer_version(v1, v2)

    def test_migration_path(self, versioning, basic_schema):
        """Test migration path finding."""
        v1 = versioning.register_version(1, 0, 0, VersionStatus.STABLE, basic_schema)
        v2 = versioning.register_version(1, 1, 0, VersionStatus.STABLE, basic_schema)
        v3 = versioning.register_version(2, 0, 0, VersionStatus.STABLE, basic_schema)

        path = versioning._find_migration_path(v1, v3)
        assert path == ["1.0.0", "1.1.0", "2.0.0"]

        # Test reverse path
        reverse_path = versioning._find_migration_path(v3, v1)
        assert reverse_path == ["2.0.0", "1.1.0", "1.0.0"]

    def test_data_migration(self, versioning, basic_schema):
        """Test data migration between versions."""
        # Register versions with slightly different schemas
        schema_v1 = basic_schema.copy()
        schema_v2 = basic_schema.copy()
        schema_v2["priority"] = {"type": "string", "enum": ["low", "medium", "high"]}

        v1 = versioning.register_version(1, 0, 0, VersionStatus.STABLE, schema_v1)
        v2 = versioning.register_version(2, 0, 0, VersionStatus.STABLE, schema_v2)

        test_data = {
            "id": "Test_123",
            "count": 42,
            "metadata": {"tags": ["test"]}
        }

        # Test migration
        migrated_data = versioning.migrate_data(test_data, v1, v2)
        assert isinstance(migrated_data, dict)
        assert migrated_data["id"] == test_data["id"]

    def test_version_listing(self, versioning, basic_schema):
        """Test version listing functionality."""
        # Register multiple versions with different statuses
        versioning.register_version(1, 0, 0, VersionStatus.STABLE, basic_schema)
        versioning.register_version(1, 1, 0, VersionStatus.BETA, basic_schema)
        versioning.register_version(2, 0, 0, VersionStatus.ALPHA, basic_schema)
        versioning.register_version(0, 9, 0, VersionStatus.DEPRECATED, basic_schema)

        # Test listing all versions
        all_versions = versioning.list_versions()
        assert len(all_versions) == 4

        # Test filtering by status
        stable_versions = versioning.list_versions(VersionStatus.STABLE)
        assert len(stable_versions) == 1
        assert "1.0.0" in stable_versions

        beta_versions = versioning.list_versions(VersionStatus.BETA)
        assert len(beta_versions) == 1
        assert "1.1.0" in beta_versions

    def test_nested_schema_validation(self, versioning):
        """Test validation of nested schema structures."""
        nested_schema = {
            "user": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "required": True
                    },
                    "settings": {
                        "type": "object",
                        "properties": {
                            "theme": {
                                "type": "string",
                                "enum": ["light", "dark"]
                            },
                            "notifications": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "enabled": {"type": "boolean"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        versioning.register_version(1, 0, 0, VersionStatus.STABLE, nested_schema)

        # Test valid nested data
        valid_data = {
            "user": {
                "name": "Test User",
                "settings": {
                    "theme": "dark",
                    "notifications": [
                        {"type": "email", "enabled": True},
                        {"type": "push", "enabled": False}
                    ]
                }
            }
        }
        assert versioning.validate_data(valid_data)

        # Test invalid nested data
        invalid_data = {
            "user": {
                "name": "Test User",
                "settings": {
                    "theme": "invalid",  # Invalid enum value
                    "notifications": [
                        {"type": "email", "enabled": "true"}  # Wrong type for boolean
                    ]
                }
            }
        }
        assert not versioning.validate_data(invalid_data)

    def test_breaking_changes(self, versioning, basic_schema):
        """Test handling of breaking changes between versions."""
        v1 = versioning.register_version(
            1, 0, 0,
            VersionStatus.STABLE,
            basic_schema,
            breaking_changes=[]
        )

        # Add required field in v2
        schema_v2 = basic_schema.copy()
        schema_v2["priority"] = {
            "type": "string",
            "required": True,
            "enum": ["low", "medium", "high"]
        }

        v2 = versioning.register_version(
            2, 0, 0,
            VersionStatus.STABLE,
            schema_v2,
            breaking_changes=["Added required priority field"]
        )

        # Data valid for v1 but invalid for v2
        test_data = {
            "id": "Test_123",
            "count": 42
        }

        assert versioning.validate_data(test_data, v1)  # Valid for v1
        assert not versioning.validate_data(test_data, v2)  # Invalid for v2

    def test_version_dependencies(self, versioning, basic_schema):
        """Test version dependency tracking."""
        # Register base version
        v1 = versioning.register_version(
            1, 0, 0,
            VersionStatus.STABLE,
            basic_schema,
            dependencies={}
        )

        # Register version with dependencies
        v2 = versioning.register_version(
            2, 0, 0,
            VersionStatus.STABLE,
            basic_schema,
            dependencies={"database": ">=5.0.0", "cache": ">=2.0.0"}
        )

        v1_info = versioning.get_version_info(v1)
        v2_info = versioning.get_version_info(v2)

        assert not v1_info.dependencies
        assert v2_info.dependencies == {"database": ">=5.0.0", "cache": ">=2.0.0"}

if __name__ == "__main__":
    pytest.main([__file__])