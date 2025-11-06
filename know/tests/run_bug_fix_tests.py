#!/usr/bin/env python3
"""
Simple test runner for bug fixes (no pytest required)
"""

import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import GraphManager, EntityManager, DependencyManager, GraphValidator


def run_test(test_name, test_func):
    """Run a single test and print result"""
    try:
        test_func()
        print(f"✓ {test_name}")
        return True
    except AssertionError as e:
        print(f"✗ {test_name}")
        print(f"  Error: {e}")
        return False
    except Exception as e:
        print(f"✗ {test_name} (unexpected error)")
        print(f"  Error: {e}")
        return False


def test_operation_recognized():
    """Bug #1: 'operation' should be recognized"""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_file = Path(tmpdir) / "test.json"
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {},
            "references": {},
            "graph": {}
        }
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        entities = EntityManager(graph)

        assert 'operation' in entities.VALID_ENTITY_TYPES, \
            "'operation' should be in VALID_ENTITY_TYPES"


def test_all_types_from_rules():
    """Entity types should match dependency-rules.json"""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_file = Path(tmpdir) / "test.json"
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {},
            "references": {},
            "graph": {}
        }
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        entities = EntityManager(graph)

        # Load rules to compare
        rules_path = Path(__file__).parent.parent / "config" / "dependency-rules.json"
        with open(rules_path) as f:
            rules = json.load(f)

        expected = set(rules['entity_description'].keys())
        actual = entities.VALID_ENTITY_TYPES

        assert actual == expected, \
            f"Entity types mismatch. Expected: {expected}, Got: {actual}"


def test_build_order_no_cycles():
    """Bug #2: Build order should work without cycles"""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_file = Path(tmpdir) / "test.json"
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "feature": {"f1": {"name": "F1", "description": "Feature 1"}},
                "action": {"a1": {"name": "A1", "description": "Action 1"}},
                "component": {"c1": {"name": "C1", "description": "Component 1"}}
            },
            "references": {},
            "graph": {
                "feature:f1": {"depends_on": ["action:a1"]},
                "action:a1": {"depends_on": ["component:c1"]},
                "component:c1": {"depends_on": []}
            }
        }
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        deps = DependencyManager(graph)

        cycles = deps.detect_cycles()
        build_order = deps.topological_sort()

        assert len(cycles) == 0, "Should have no cycles"
        assert len(build_order) > 0, "Build order should return results"
        assert len(build_order) == 3, f"Should have 3 entities, got {len(build_order)}"


def test_build_order_with_cycles():
    """Bug #2: Build order should return empty with cycles"""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_file = Path(tmpdir) / "test.json"
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "action": {
                    "a1": {"name": "A1", "description": "Action 1"},
                    "a2": {"name": "A2", "description": "Action 2"}
                }
            },
            "references": {},
            "graph": {
                "action:a1": {"depends_on": ["action:a2"]},
                "action:a2": {"depends_on": ["action:a1"]}  # Cycle!
            }
        }
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        deps = DependencyManager(graph)

        cycles = deps.detect_cycles()
        build_order = deps.topological_sort()

        assert len(cycles) > 0, "Should detect cycles"
        assert len(build_order) == 0, \
            f"Build order should be empty with cycles, got {len(build_order)}"


def test_metadata_loaded_from_rules():
    """Bug #4: Metadata fields should be loaded from rules"""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_file = Path(tmpdir) / "test.json"
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {},
            "references": {},
            "graph": {}
        }
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        validator = GraphValidator(graph)

        assert hasattr(validator, 'allowed_metadata'), \
            "Validator should have allowed_metadata"

        expected = {'path', 'status', 'tags', 'id', 'type', 'metadata', 'notes'}
        assert expected.issubset(validator.allowed_metadata), \
            f"Expected {expected} in allowed_metadata"


def test_path_metadata_no_warning():
    """Bug #4: 'path' metadata should not trigger warnings"""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_file = Path(tmpdir) / "test.json"
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "component": {
                    "card": {
                        "name": "Card",
                        "description": "Card component",
                        "path": "lib/Card.jsx"
                    }
                }
            },
            "references": {},
            "graph": {
                "component:card": {"depends_on": []}
            }
        }
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        validator = GraphValidator(graph)

        is_valid, results = validator.validate_all()

        path_warnings = [w for w in results['warnings']
                        if 'card' in w and 'path' in w]

        assert len(path_warnings) == 0, \
            f"'path' should not trigger warning, but got: {path_warnings}"


def test_disconnected_subgraphs():
    """Bug #3: Disconnected subgraphs should not fail validation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_file = Path(tmpdir) / "test.json"
        graph_data = {
            "meta": {"version": "1.0.0", "format": "json-graph"},
            "entities": {
                "feature": {
                    "f1": {"name": "F1", "description": "Feature 1"},
                    "f2": {"name": "F2", "description": "Feature 2"},
                    "f3": {"name": "F3", "description": "Feature 3"}
                }
            },
            "references": {},
            "graph": {
                "feature:f1": {"depends_on": []},
                "feature:f2": {"depends_on": []},
                "feature:f3": {"depends_on": []}
            }
        }
        graph_file.write_text(json.dumps(graph_data, indent=2))

        graph = GraphManager(str(graph_file))
        validator = GraphValidator(graph)
        deps = DependencyManager(graph)

        is_valid, results = validator.validate_all()
        cycles = deps.detect_cycles()
        disconnected = validator.find_disconnected_subgraphs()

        assert len(disconnected) > 0, "Should detect disconnected subgraphs"
        assert len(cycles) == 0, "Should have no cycles"
        # Disconnected subgraphs alone should not fail validation
        assert is_valid or len(results['errors']) == 0, \
            "Disconnected subgraphs should not cause validation errors"


def main():
    """Run all tests"""
    print("Running Bug Fix Tests\n" + "="*60 + "\n")

    tests = [
        ("Bug #1: 'operation' entity type recognized", test_operation_recognized),
        ("Bug #1: All entity types loaded from rules", test_all_types_from_rules),
        ("Bug #2: Build order works without cycles", test_build_order_no_cycles),
        ("Bug #2: Build order returns empty with cycles", test_build_order_with_cycles),
        ("Bug #4: Metadata fields loaded from rules", test_metadata_loaded_from_rules),
        ("Bug #4: 'path' metadata doesn't trigger warning", test_path_metadata_no_warning),
        ("Bug #3: Disconnected subgraphs are informational", test_disconnected_subgraphs),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        if run_test(name, test_func):
            passed += 1
        else:
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")


if __name__ == '__main__':
    main()
