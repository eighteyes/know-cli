"""
Test suite for entity operations
"""

import json
import tempfile
import pytest
from pathlib import Path
from src import GraphManager, EntityManager


@pytest.fixture
def temp_graph_setup():
    """Create a temporary graph with entities for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_graph = {
            "meta": {"version": "1.0.0"},
            "references": {},
            "entities": {
                "user": {
                    "owner": {"name": "Owner", "role": "admin"},
                    "viewer": {"name": "Viewer", "role": "read-only"}
                },
                "feature": {
                    "auth": {"description": "Authentication system"}
                }
            },
            "graph": {
                "feature:auth": {"depends_on": ["user:owner"]}
            }
        }
        json.dump(test_graph, f)
        temp_file = Path(f.name)

    gm = GraphManager(str(temp_file))
    em = EntityManager(gm)
    return em, temp_file


def test_list_entities(temp_graph_setup):
    """Test listing all entities"""
    em, _ = temp_graph_setup
    entities = em.list_entities()

    assert "user:owner" in entities
    assert "user:viewer" in entities
    assert "feature:auth" in entities
    assert len(entities) == 3


def test_list_entities_by_type(temp_graph_setup):
    """Test listing entities by type"""
    em, _ = temp_graph_setup
    users = em.list_entities("user")

    assert len(users) == 2
    assert "user:owner" in users
    assert "user:viewer" in users

    features = em.list_entities("feature")
    assert len(features) == 1
    assert "feature:auth" in features


def test_get_entity(temp_graph_setup):
    """Test getting a specific entity"""
    em, _ = temp_graph_setup
    entity = em.get_entity("user:owner")

    assert entity is not None
    assert entity["name"] == "Owner"
    assert entity["role"] == "admin"

    # Non-existent entity
    entity = em.get_entity("user:nonexistent")
    assert entity is None


def test_add_entity(temp_graph_setup):
    """Test adding a new entity"""
    em, _ = temp_graph_setup

    # Add new entity
    success = em.add_entity("user", "developer",
                             {"name": "Developer", "role": "dev"})
    assert success

    # Verify it was added
    entity = em.get_entity("user:developer")
    assert entity is not None
    assert entity["name"] == "Developer"

    # Try adding duplicate
    success = em.add_entity("user", "developer", {"name": "Another"})
    assert not success


def test_update_entity(temp_graph_setup):
    """Test updating an entity"""
    em, _ = temp_graph_setup

    # Update existing entity
    success = em.update_entity("user:owner",
                                {"name": "Updated Owner", "role": "superadmin"})
    assert success

    # Verify update
    entity = em.get_entity("user:owner")
    assert entity["name"] == "Updated Owner"
    assert entity["role"] == "superadmin"

    # Try updating non-existent entity
    success = em.update_entity("user:nonexistent", {"name": "Test"})
    assert not success


def test_delete_entity(temp_graph_setup):
    """Test deleting an entity"""
    em, _ = temp_graph_setup

    # Try deleting entity with dependents (should fail)
    success = em.delete_entity("user:owner", force=False)
    assert not success

    # Delete entity without dependents
    success = em.delete_entity("user:viewer", force=False)
    assert success

    # Verify deletion
    entity = em.get_entity("user:viewer")
    assert entity is None

    # Force delete entity with dependents
    success = em.delete_entity("user:owner", force=True)
    assert success


def test_add_dependency(temp_graph_setup):
    """Test adding dependencies"""
    em, _ = temp_graph_setup

    # Add new dependency
    success = em.add_dependency("user:viewer", "user:owner")
    assert success

    # Verify dependency was added
    deps = em.graph.find_dependencies("user:viewer")
    assert "user:owner" in deps

    # Try adding duplicate dependency
    success = em.add_dependency("user:viewer", "user:owner")
    assert not success


def test_remove_dependency(temp_graph_setup):
    """Test removing dependencies"""
    em, _ = temp_graph_setup

    # Remove existing dependency
    success = em.remove_dependency("feature:auth", "user:owner")
    assert success

    # Verify removal
    deps = em.graph.find_dependencies("feature:auth")
    assert "user:owner" not in deps

    # Try removing non-existent dependency
    success = em.remove_dependency("feature:auth", "user:owner")
    assert not success


def test_entity_stats(temp_graph_setup):
    """Test getting entity statistics"""
    em, _ = temp_graph_setup
    stats = em.get_entity_stats()

    assert stats["total"] == 3
    assert stats["by_type"]["user"] == 2
    assert stats["by_type"]["feature"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])