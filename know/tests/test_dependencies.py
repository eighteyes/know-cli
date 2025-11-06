"""
Tests for dependency management.
"""

import pytest
import json
import tempfile
from pathlib import Path

from know_lib import GraphManager, DependencyManager


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    return {
        "meta": {
            "project": {"name": "Test Project"}
        },
        "entities": {
            "users": {
                "owner": {"name": "Owner", "description": "System owner"}
            },
            "objectives": {
                "manage-fleet": {"name": "Manage Fleet", "description": "Manage vehicle fleet"}
            },
            "features": {
                "vehicle-tracking": {"name": "Vehicle Tracking", "description": "Track vehicles"}
            },
            "components": {
                "map-view": {"name": "Map View", "description": "Map display"}
            }
        },
        "references": {
            "acceptance_criteria": {
                "track-accuracy": {"description": "Location accuracy within 10m"}
            }
        },
        "graph": {
            "users:owner": {
                "depends_on": ["objectives:manage-fleet"]
            },
            "objectives:manage-fleet": {
                "depends_on": ["features:vehicle-tracking"]
            },
            "features:vehicle-tracking": {
                "depends_on": ["components:map-view", "acceptance_criteria:track-accuracy"]
            },
            "components:map-view": {
                "depends_on": []
            }
        }
    }


@pytest.fixture
def temp_graph_file(sample_graph):
    """Create a temporary graph file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(sample_graph, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


def test_get_dependencies(temp_graph_file):
    """Test getting direct dependencies."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    # Test direct dependencies
    result = deps.get_dependencies("features:vehicle-tracking")
    assert "components:map-view" in result
    assert "acceptance_criteria:track-accuracy" in result
    assert len(result) == 2


def test_get_dependents(temp_graph_file):
    """Test getting dependents."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    # Test what depends on a feature
    result = deps.get_dependents("features:vehicle-tracking")
    assert "objectives:manage-fleet" in result


def test_dependency_validation(temp_graph_file):
    """Test dependency validation."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    # Valid dependency
    assert deps.is_valid_dependency("features", "components")
    assert deps.is_valid_dependency("features", "actions")

    # Invalid dependency
    assert not deps.is_valid_dependency("components", "features")
    assert not deps.is_valid_dependency("users", "components")


def test_cycle_detection(temp_graph_file):
    """Test cycle detection."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    # No cycles initially
    cycles = deps.detect_cycles()
    assert len(cycles) == 0

    # Add a cycle
    data = graph.load()
    data['graph']['components:map-view']['depends_on'] = ['features:vehicle-tracking']
    graph.save(data)

    # Should detect cycle
    cycles = deps.detect_cycles()
    assert len(cycles) > 0


def test_topological_sort(temp_graph_file):
    """Test topological sorting."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    order = deps.topological_sort()

    # Map view should come before vehicle tracking
    map_idx = order.index('components:map-view')
    tracking_idx = order.index('features:vehicle-tracking')
    assert map_idx < tracking_idx

    # Vehicle tracking should come before manage fleet
    fleet_idx = order.index('objectives:manage-fleet')
    assert tracking_idx < fleet_idx


def test_add_dependency(temp_graph_file):
    """Test adding dependencies."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    # Add valid dependency
    success, error = deps.add_dependency(
        "features:vehicle-tracking",
        "components:map-view",
        validate=True
    )
    assert success
    assert error is None

    # Try invalid dependency
    success, error = deps.add_dependency(
        "components:map-view",
        "features:vehicle-tracking",
        validate=True
    )
    assert not success
    assert error is not None


def test_remove_dependency(temp_graph_file):
    """Test removing dependencies."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    # Remove existing dependency
    result = deps.remove_dependency(
        "features:vehicle-tracking",
        "components:map-view"
    )
    assert result

    # Verify it's gone
    dependencies = deps.get_dependencies("features:vehicle-tracking")
    assert "components:map-view" not in dependencies


def test_suggest_connections(temp_graph_file):
    """Test connection suggestions."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    # Get suggestions for a feature
    suggestions = deps.suggest_connections("features:vehicle-tracking")

    # Should suggest valid dependency types
    assert isinstance(suggestions, dict)
    # Features can depend on actions and components
    assert "actions" in suggestions or "components" in suggestions


def test_allowed_targets(temp_graph_file):
    """Test getting allowed targets."""
    graph = GraphManager(temp_graph_file)
    deps = DependencyManager(graph)

    # Features can depend on actions
    allowed = deps.get_allowed_targets("features")
    assert "actions" in allowed

    # Users can depend on objectives
    allowed = deps.get_allowed_targets("users")
    assert "objectives" in allowed or "requirements" in allowed


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
