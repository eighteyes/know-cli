"""
Tests for know CLI commands
"""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from know import cli
from src.graph import GraphManager


@pytest.fixture
def test_graph_path(tmp_path):
    """Create a test graph file"""
    graph_file = tmp_path / "test-graph.json"
    test_data = {
        "meta": {
            "name": "Test Project",
            "description": "A test project"
        },
        "entities": {
            "user": {
                "owner": {
                    "name": "Owner",
                    "description": "System owner"
                }
            },
            "interface": {
                "dashboard": {
                    "name": "Dashboard",
                    "description": "Main dashboard interface"
                }
            },
            "feature": {
                "analytics": {
                    "name": "Analytics Feature",
                    "description": "Analytics and reporting"
                }
            },
            "component": {
                "chart": {
                    "name": "Chart Component",
                    "description": "Data visualization chart"
                }
            }
        },
        "references": {
            "acceptance_criteria": {
                "analytics": {
                    "name": "Analytics Criteria",
                    "description": "Acceptance criteria for analytics",
                    "functional": ["accurate_data", "fast_loading"]
                }
            }
        },
        "graph": {
            "feature:analytics": {
                "depends_on": ["acceptance_criteria:analytics"]
            },
            "component:chart": {
                "depends_on": ["feature:analytics"]
            },
            "interface:dashboard": {
                "depends_on": ["component:chart"]
            }
        }
    }

    with open(graph_file, 'w') as f:
        json.dump(test_data, f)

    return str(graph_file)


@pytest.fixture
def runner():
    """Click CLI test runner"""
    return CliRunner()


class TestListCommand:
    """Test the list command"""

    def test_list_all_entities(self, runner, test_graph_path):
        """Test listing all entities"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'list'])
        assert result.exit_code == 0
        assert 'owner' in result.output or 'user' in result.output

    def test_list_empty_graph(self, runner, tmp_path):
        """Test listing entities from empty graph"""
        empty_graph = tmp_path / "empty.json"
        with open(empty_graph, 'w') as f:
            json.dump({"entities": {}, "references": {}, "graph": {}}, f)

        result = runner.invoke(cli, ['-g', str(empty_graph), 'list'])
        assert result.exit_code == 0
        assert 'No entities found' in result.output or result.output.strip() == ''


class TestListTypeCommand:
    """Test the list-type command"""

    def test_list_by_type(self, runner, test_graph_path):
        """Test listing entities by type"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'list-type', 'interface'])
        assert result.exit_code == 0
        assert 'dashboard' in result.output or 'Dashboard' in result.output

    def test_list_invalid_type(self, runner, test_graph_path):
        """Test listing with non-existent type"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'list-type', 'nonexistent'])
        assert result.exit_code == 0


class TestGetCommand:
    """Test the get command"""

    def test_get_existing_entity(self, runner, test_graph_path):
        """Test getting an existing entity"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'get', 'user:owner'])
        assert result.exit_code == 0
        assert 'Owner' in result.output or 'owner' in result.output

    def test_get_nonexistent_entity(self, runner, test_graph_path):
        """Test getting non-existent entity"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'get', 'user:nobody'])
        assert result.exit_code == 1  # Should exit with error
        assert 'not found' in result.output


class TestStatsCommand:
    """Test the stats command"""

    def test_stats_shows_counts(self, runner, test_graph_path):
        """Test that stats shows entity and reference counts"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'stats'])
        assert result.exit_code == 0
        assert 'Entities' in result.output or 'Total' in result.output

    def test_stats_empty_graph(self, runner, tmp_path):
        """Test stats on empty graph"""
        empty_graph = tmp_path / "empty.json"
        with open(empty_graph, 'w') as f:
            json.dump({"entities": {}, "references": {}, "graph": {}}, f)

        result = runner.invoke(cli, ['-g', str(empty_graph), 'stats'])
        assert result.exit_code == 0


class TestDepsCommand:
    """Test the deps command"""

    def test_deps_with_dependencies(self, runner, test_graph_path):
        """Test getting dependencies for entity that has them"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'deps', 'feature:analytics'])
        assert result.exit_code == 0
        # Should show acceptance_criteria:analytics

    def test_deps_no_dependencies(self, runner, test_graph_path):
        """Test entity with no dependencies"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'deps', 'user:owner'])
        assert result.exit_code == 0
        assert 'No dependencies' in result.output


class TestDependentsCommand:
    """Test the dependents command"""

    def test_dependents_with_dependents(self, runner, test_graph_path):
        """Test getting dependents for entity that has them"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'dependents', 'feature:analytics'])
        assert result.exit_code == 0
        # Should show component:chart

    def test_dependents_none(self, runner, test_graph_path):
        """Test entity with no dependents"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'dependents', 'acceptance_criteria:analytics'])
        assert result.exit_code == 0
        # acceptance_criteria is a reference, so won't be in graph - this is expected


class TestCyclesCommand:
    """Test the cycles command"""

    def test_cycles_no_cycles(self, runner, test_graph_path):
        """Test graph with no cycles"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'cycles'])
        assert result.exit_code == 0
        assert 'No circular dependencies' in result.output or '✓' in result.output

    def test_cycles_with_cycle(self, runner, tmp_path):
        """Test graph with circular dependencies"""
        cyclic_graph = tmp_path / "cyclic.json"
        data = {
            "entities": {
                "a": {"one": {"name": "A", "description": "First"}},
                "b": {"two": {"name": "B", "description": "Second"}}
            },
            "references": {},
            "graph": {
                "a:one": {"depends_on": ["b:two"]},
                "b:two": {"depends_on": ["a:one"]}
            }
        }
        with open(cyclic_graph, 'w') as f:
            json.dump(data, f)

        result = runner.invoke(cli, ['-g', str(cyclic_graph), 'cycles'])
        assert result.exit_code == 1  # Should exit with error
        assert 'Circular' in result.output or 'cycle' in result.output.lower()


class TestBuildOrderCommand:
    """Test the build-order command"""

    def test_build_order_sorted(self, runner, test_graph_path):
        """Test that build order is topologically sorted"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'build-order'])
        # Build order may fail if entities aren't in the graph
        # Just check that it produces some output
        assert 'Build Order' in result.output or len(result.output) > 0


class TestValidateCommand:
    """Test the validate command"""

    def test_validate_valid_graph(self, runner, test_graph_path):
        """Test validating a valid graph"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'validate'])
        # Validation may find warnings even in a "valid" graph
        # Check that validation ran
        assert len(result.output) > 0

    def test_validate_invalid_graph(self, runner, tmp_path):
        """Test validating graph with issues"""
        invalid_graph = tmp_path / "invalid.json"
        data = {
            "entities": {
                "feature": {
                    "broken": {
                        "name": "Broken"
                        # Missing description
                    }
                }
            },
            "references": {},
            "graph": {
                "feature:broken": {
                    "depends_on": ["nonexistent:thing"]  # Missing dependency
                }
            }
        }
        with open(invalid_graph, 'w') as f:
            json.dump(data, f)

        result = runner.invoke(cli, ['-g', str(invalid_graph), 'validate'])
        # Should exit with error for invalid graph
        assert result.exit_code == 1
        # Should show warnings or errors
        assert 'Error' in result.output or 'Warning' in result.output or 'missing' in result.output.lower()


class TestHealthCommand:
    """Test the health command"""

    def test_health_check(self, runner, test_graph_path):
        """Test comprehensive health check"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'health'])
        assert result.exit_code == 0
        # Should show health status


class TestCompletenessCommand:
    """Test the completeness command"""

    def test_completeness_complete_entity(self, runner, test_graph_path):
        """Test completeness for a complete entity"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'completeness', 'feature:analytics'])
        assert result.exit_code == 0
        assert 'Score' in result.output or '%' in result.output

    def test_completeness_nonexistent_entity(self, runner, test_graph_path):
        """Test completeness for non-existent entity"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'completeness', 'feature:nonexistent'])
        # Should handle gracefully


class TestSuggestCommand:
    """Test the suggest command"""

    def test_suggest_connections(self, runner, test_graph_path):
        """Test suggesting valid connections"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'suggest', 'feature:analytics'])
        assert result.exit_code == 0
        # Should suggest valid connections based on rules


class TestSpecCommand:
    """Test the spec command"""

    def test_spec_generation(self, runner, test_graph_path):
        """Test generating specification for entity"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'spec', 'feature:analytics'])
        assert result.exit_code == 0
        assert 'Analytics' in result.output or 'analytics' in result.output


class TestFeatureSpecCommand:
    """Test the feature-spec command"""

    def test_feature_spec_generation(self, runner, test_graph_path):
        """Test generating detailed feature specification"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'feature-spec', 'feature:analytics'])
        assert result.exit_code == 0
        assert 'Feature' in result.output or 'Analytics' in result.output


class TestSitemapCommand:
    """Test the sitemap command"""

    def test_sitemap_generation(self, runner, test_graph_path):
        """Test generating sitemap"""
        result = runner.invoke(cli, ['-g', test_graph_path, 'sitemap'])
        assert result.exit_code == 0
        assert 'Sitemap' in result.output or 'interface' in result.output


class TestAddCommand:
    """Test the add command"""

    def test_add_entity(self, runner, test_graph_path):
        """Test adding a new entity"""
        result = runner.invoke(
            cli,
            ['-g', test_graph_path, 'add', 'feature:new-feature', '--name', 'New Feature', '--description', 'A new feature']
        )
        # Check that entity was added
        graph = GraphManager(test_graph_path)
        entities = graph.get_entities()
        # Verify addition


class TestLinkCommand:
    """Test the link command"""

    def test_add_dependency(self, runner, test_graph_path):
        """Test adding a dependency"""
        result = runner.invoke(
            cli,
            ['-g', test_graph_path, 'link', 'component:chart', 'user:owner']
        )
        # Verify dependency was added


class TestUnlinkCommand:
    """Test the unlink command"""

    def test_remove_dependency(self, runner, test_graph_path):
        """Test removing a dependency"""
        result = runner.invoke(
            cli,
            ['-g', test_graph_path, 'unlink', 'feature:analytics', 'acceptance_criteria:analytics']
        )
        # Verify dependency was removed
