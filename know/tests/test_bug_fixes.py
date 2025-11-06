#!/usr/bin/env python3
"""
Test suite for bug fixes reported in bug report 2025-10-30

Tests:
1. Bug #1: Entity type "operation" recognized
2. Bug #2: Build order cycle detection
3. Bug #3: Disconnected subgraphs are informational
4. Bug #4: Custom metadata fields allowed
"""

import pytest
import json
import tempfile
from pathlib import Path
from know_lib import GraphManager, EntityManager, DependencyManager, GraphValidator


class TestEntityTypeLoading:
    """Test that entity types are loaded from dependency-rules.json"""

    def test_operation_entity_type_recognized(self, tmp_path):
        """Bug #1: 'operation' should be recognized as valid entity type"""
        # Create minimal graph
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {},
            "references": {},
            "graph": {}
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        # Initialize EntityManager
        graph = GraphManager(str(graph_file))
        entities = EntityManager(graph)

        # Verify 'operation' is in valid entity types
        assert 'operation' in entities.VALID_ENTITY_TYPES, \
            "'operation' should be recognized from dependency-rules.json"

    def test_all_entity_types_loaded_from_rules(self, tmp_path):
        """Verify all entity types from rules file are loaded"""
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {},
            "references": {},
            "graph": {}
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        entities = EntityManager(graph)

        # Load rules directly to compare
        rules_path = Path(__file__).parent.parent / "config" / "dependency-rules.json"
        with open(rules_path) as f:
            rules = json.load(f)

        expected_types = set(rules['entity_description'].keys())

        assert entities.VALID_ENTITY_TYPES == expected_types, \
            "EntityManager should load all entity types from dependency-rules.json"

    def test_can_add_operation_entity(self, tmp_path):
        """Verify we can actually add an 'operation' entity"""
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {"operation": {}},
            "references": {},
            "graph": {}
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        entities = EntityManager(graph)

        # Try to add an operation entity
        success, error = entities.add_entity(
            'operation',
            'test-op',
            {'name': 'Test Operation', 'description': 'A test operation'}
        )

        assert success, f"Should be able to add operation entity: {error}"
        assert error is None


class TestTopologicalSort:
    """Test topological sort / build order with and without cycles"""

    def test_build_order_with_no_cycles(self, tmp_path):
        """Bug #2: Build order should work when no cycles exist"""
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "feature": {
                    "auth": {"name": "Authentication", "description": "User auth"},
                    "profile": {"name": "Profile", "description": "User profile"}
                },
                "action": {
                    "login": {"name": "Login", "description": "Login action"},
                    "update-profile": {"name": "Update Profile", "description": "Update action"}
                },
                "component": {
                    "auth-form": {"name": "Auth Form", "description": "Login form"},
                    "profile-editor": {"name": "Profile Editor", "description": "Profile editor"}
                }
            },
            "references": {},
            "graph": {
                "feature:auth": {"depends_on": ["action:login"]},
                "feature:profile": {"depends_on": ["action:update-profile"]},
                "action:login": {"depends_on": ["component:auth-form"]},
                "action:update-profile": {"depends_on": ["component:profile-editor"]},
                "component:auth-form": {"depends_on": []},
                "component:profile-editor": {"depends_on": []}
            }
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        deps = DependencyManager(graph)

        # Check no cycles
        cycles = deps.detect_cycles()
        assert len(cycles) == 0, "Graph should have no cycles"

        # Get build order
        build_order = deps.topological_sort()

        assert len(build_order) > 0, \
            "Build order should return results when no cycles exist"
        assert len(build_order) == 6, \
            "Build order should include all 6 entities"

    def test_build_order_with_cycles(self, tmp_path):
        """Bug #2: Build order should return empty list when cycles exist"""
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "feature": {
                    "a": {"name": "Feature A", "description": "Feature A"},
                    "b": {"name": "Feature B", "description": "Feature B"}
                },
                "action": {
                    "x": {"name": "Action X", "description": "Action X"},
                    "y": {"name": "Action Y", "description": "Action Y"}
                }
            },
            "references": {},
            "graph": {
                "feature:a": {"depends_on": ["action:x"]},
                "feature:b": {"depends_on": ["action:y"]},
                "action:x": {"depends_on": ["action:y"]},
                "action:y": {"depends_on": ["action:x"]}  # Creates cycle
            }
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        deps = DependencyManager(graph)

        # Check cycles exist
        cycles = deps.detect_cycles()
        assert len(cycles) > 0, "Graph should have cycles"

        # Get build order
        build_order = deps.topological_sort()

        assert len(build_order) == 0, \
            "Build order should return empty list when cycles exist"

    def test_cycle_detection_consistency(self, tmp_path):
        """Ensure cycle detection and build order are consistent"""
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "feature": {"f1": {"name": "F1", "description": "Feature 1"}},
                "action": {"a1": {"name": "A1", "description": "Action 1"}}
            },
            "references": {},
            "graph": {
                "feature:f1": {"depends_on": ["action:a1"]},
                "action:a1": {"depends_on": []}
            }
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        deps = DependencyManager(graph)

        cycles = deps.detect_cycles()
        build_order = deps.topological_sort()

        # If no cycles, build order should have results
        # If cycles exist, build order should be empty
        if len(cycles) == 0:
            assert len(build_order) > 0, \
                "When no cycles detected, build order should have results"
        else:
            assert len(build_order) == 0, \
                "When cycles detected, build order should be empty"


class TestMetadataValidation:
    """Test that custom metadata fields are allowed"""

    def test_metadata_fields_loaded_from_rules(self, tmp_path):
        """Bug #4: Metadata fields should be loaded from dependency-rules.json"""
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {},
            "references": {},
            "graph": {}
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        validator = GraphValidator(graph)

        # Verify metadata fields are loaded
        assert hasattr(validator, 'allowed_metadata'), \
            "Validator should have allowed_metadata attribute"

        # Common metadata fields should be present
        expected_fields = {'path', 'status', 'tags', 'id', 'type', 'metadata', 'notes'}
        assert expected_fields.issubset(validator.allowed_metadata), \
            f"Expected metadata fields {expected_fields} should be in allowed_metadata"

    def test_path_metadata_does_not_trigger_warning(self, tmp_path):
        """Bug #4: 'path' metadata should not trigger unexpected field warning"""
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "component": {
                    "metric-card": {
                        "name": "Metric Card",
                        "description": "Dashboard metric card",
                        "path": "lib/components/MetricCard.jsx"  # Should NOT warn
                    }
                }
            },
            "references": {},
            "graph": {
                "component:metric-card": {"depends_on": []}
            }
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        validator = GraphValidator(graph)

        is_valid, results = validator.validate_all()

        # Check that 'path' doesn't trigger warning
        path_warnings = [w for w in results['warnings']
                        if 'metric-card' in w and 'path' in w]

        assert len(path_warnings) == 0, \
            "'path' metadata should not trigger unexpected field warning"

    def test_custom_metadata_fields_allowed(self, tmp_path):
        """Verify multiple custom metadata fields work"""
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "feature": {
                    "analytics": {
                        "name": "Analytics",
                        "description": "Analytics feature",
                        "status": "in_development",
                        "tags": ["metrics", "reporting"],
                        "path": "src/features/analytics",
                        "notes": "High priority"
                    }
                }
            },
            "references": {},
            "graph": {
                "feature:analytics": {"depends_on": []}
            }
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        validator = GraphValidator(graph)

        is_valid, results = validator.validate_all()

        # None of the allowed metadata should trigger warnings
        unexpected_warnings = [w for w in results['warnings']
                              if 'analytics' in w and 'unexpected fields' in w]

        assert len(unexpected_warnings) == 0, \
            "Allowed metadata fields should not trigger unexpected field warnings"


class TestDisconnectedSubgraphs:
    """Test that disconnected subgraphs don't cause health check failure"""

    def test_disconnected_subgraphs_are_informational(self, tmp_path):
        """Bug #3: Disconnected subgraphs should be informational, not critical"""
        # Create graph with intentionally disconnected subgraphs
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "feature": {
                    "auth": {"name": "Auth", "description": "Authentication"},
                    "analytics": {"name": "Analytics", "description": "Analytics"},
                    "reporting": {"name": "Reporting", "description": "Reporting"}
                }
            },
            "references": {},
            "graph": {
                "feature:auth": {"depends_on": []},
                "feature:analytics": {"depends_on": []},
                "feature:reporting": {"depends_on": []}
            }
        }

        graph_file = tmp_path / "test-graph.json"
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        validator = GraphValidator(graph)
        deps = DependencyManager(graph)

        # Validate graph
        is_valid, results = validator.validate_all()
        cycles = deps.detect_cycles()
        disconnected = validator.find_disconnected_subgraphs()

        # Even with disconnected subgraphs, validation should pass if no other errors
        assert is_valid or len(results['errors']) == 0, \
            "Disconnected subgraphs alone should not cause validation failure"

        # Should detect disconnected subgraphs
        assert len(disconnected) > 0, \
            "Should detect disconnected subgraphs in this test graph"

        # But should have no cycles
        assert len(cycles) == 0, \
            "Test graph should have no cycles"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
