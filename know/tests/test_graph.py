"""
Test suite for graph operations
"""

import json
import tempfile
import pytest
from pathlib import Path
from src import GraphManager


@pytest.fixture
def temp_graph_file():
    """Create a temporary graph file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_graph = {
            "meta": {"version": "1.0.0", "horizons": {}},
            "references": {
                "ref1": {"value": "test"}
            },
            "entities": {
                "user": {
                    "owner": {"name": "Owner User"},
                    "admin": {"name": "Admin User"}
                },
                "feature": {
                    "auth": {"description": "Authentication"},
                    "dashboard": {"description": "Dashboard"}
                }
            },
            "graph": {
                "feature:auth": {"depends_on": ["user:owner"]},
                "feature:dashboard": {"depends_on": ["feature:auth", "user:admin"]}
            }
        }
        json.dump(test_graph, f)
        return Path(f.name)


def test_load_graph(temp_graph_file):
    """Test loading graph from file"""
    gm = GraphManager(str(temp_graph_file))
    graph = gm.get_graph()

    assert "meta" in graph
    assert "entities" in graph
    assert "graph" in graph
    assert graph["meta"]["version"] == "1.0.0"


def test_get_entities(temp_graph_file):
    """Test getting entities"""
    gm = GraphManager(str(temp_graph_file))
    entities = gm.get_entities()

    assert "user" in entities
    assert "feature" in entities
    assert "owner" in entities["user"]
    assert "auth" in entities["feature"]


def test_find_dependencies(temp_graph_file):
    """Test finding dependencies"""
    gm = GraphManager(str(temp_graph_file))

    # Direct dependencies
    direct_deps = gm.find_dependencies("feature:dashboard", recursive=False)
    assert set(direct_deps) == {"feature:auth", "user:admin"}

    # All dependencies
    all_deps = gm.find_dependencies("feature:dashboard", recursive=True)
    assert set(all_deps) == {"feature:auth", "user:admin", "user:owner"}


def test_find_dependents(temp_graph_file):
    """Test finding dependents"""
    gm = GraphManager(str(temp_graph_file))

    # Direct dependents of user:owner
    direct_deps = gm.find_dependents("user:owner", recursive=False)
    assert set(direct_deps) == {"feature:auth"}

    # All dependents
    all_deps = gm.find_dependents("user:owner", recursive=True)
    assert set(all_deps) == {"feature:auth", "feature:dashboard"}


def test_validate_dependencies(temp_graph_file):
    """Test dependency validation"""
    gm = GraphManager(str(temp_graph_file))
    issues = gm.validate_dependencies()

    # Should have no issues with valid graph
    assert len(issues) == 0


def test_topological_sort(temp_graph_file):
    """Test topological sorting"""
    gm = GraphManager(str(temp_graph_file))
    order = gm.topological_sort()

    # Check that dependencies come before dependents
    assert order.index("user:owner") < order.index("feature:auth")
    assert order.index("feature:auth") < order.index("feature:dashboard")
    assert order.index("user:admin") < order.index("feature:dashboard")


def test_detect_cycles():
    """Test cycle detection"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        cyclic_graph = {
            "meta": {},
            "entities": {
                "component": {
                    "a": {},
                    "b": {},
                    "c": {}
                }
            },
            "graph": {
                "component:a": {"depends_on": ["component:b"]},
                "component:b": {"depends_on": ["component:c"]},
                "component:c": {"depends_on": ["component:a"]}  # Creates cycle
            },
            "references": {}
        }
        json.dump(cyclic_graph, f)
        temp_file = Path(f.name)

    gm = GraphManager(str(temp_file))
    cycles = gm.detect_cycles()

    assert len(cycles) > 0
    # Should detect the a->b->c->a cycle
    assert any(set(cycle) == {"component:a", "component:b", "component:c"}
               for cycle in cycles)


def test_save_graph(temp_graph_file):
    """Test saving graph"""
    gm = GraphManager(str(temp_graph_file))

    # Modify graph
    graph = gm.get_graph()
    graph["entities"]["user"]["test_user"] = {"name": "Test"}

    # Save
    assert gm.save_graph(graph)

    # Reload and verify
    new_graph = gm.get_graph()
    assert "test_user" in new_graph["entities"]["user"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])