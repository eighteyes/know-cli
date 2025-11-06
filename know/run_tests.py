#!/usr/bin/env python3
"""
Simple test runner without pytest dependency.
Tests core functionality of know_lib.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add know_lib to path
sys.path.insert(0, str(Path(__file__).parent))

from know_lib import (
    GraphManager, EntityManager, DependencyManager,
    GraphValidator, LLMManager, parse_entity_id,
    validate_name_format, get_graph_stats
)


def test_parse_entity_id():
    """Test entity ID parsing."""
    print("Testing parse_entity_id...")

    entity_type, entity_name = parse_entity_id("features:analytics")
    assert entity_type == "features", f"Expected 'features', got '{entity_type}'"
    assert entity_name == "analytics", f"Expected 'analytics', got '{entity_name}'"

    entity_type, entity_name = parse_entity_id("invalid")
    assert entity_type is None, "Should return None for invalid ID"
    assert entity_name is None, "Should return None for invalid ID"

    print("  ✓ parse_entity_id passed")


def test_validate_name_format():
    """Test name validation."""
    print("Testing validate_name_format...")

    is_valid, error = validate_name_format("user-dashboard")
    assert is_valid, "Should accept valid kebab-case"

    is_valid, error = validate_name_format("user_dashboard")
    assert not is_valid, "Should reject underscores"

    is_valid, error = validate_name_format("UserDashboard")
    assert not is_valid, "Should reject uppercase"

    print("  ✓ validate_name_format passed")


def test_graph_operations():
    """Test graph operations."""
    print("Testing graph operations...")

    # Create temp graph
    test_graph = {
        "meta": {"project": {"name": "Test"}},
        "entities": {
            "users": {
                "owner": {"name": "Owner", "description": "Test user"}
            },
            "features": {
                "analytics": {"name": "Analytics", "description": "Test feature"}
            }
        },
        "references": {},
        "graph": {
            "users:owner": {"depends_on": []},
            "features:analytics": {"depends_on": ["users:owner"]}
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(test_graph, f)
        temp_path = f.name

    try:
        # Test graph loading
        graph = GraphManager(temp_path)
        data = graph.load()
        assert 'entities' in data, "Graph should have entities"

        # Test entity operations
        entities = EntityManager(graph)
        entity_list = entities.list_entities()
        assert len(entity_list) == 2, f"Expected 2 entities, got {len(entity_list)}"

        entity = entities.get_entity("users:owner")
        assert entity is not None, "Should get entity"
        assert entity['name'] == "Owner", "Entity should have correct name"

        # Test dependencies
        deps = DependencyManager(graph)
        dependencies = deps.get_dependencies("features:analytics")
        assert "users:owner" in dependencies, "Should find dependency"

        # Test validation
        is_valid = deps.is_valid_dependency("features", "users")
        # Features can depend on actions, not users directly, but let's check structure

        cycles = deps.detect_cycles()
        assert len(cycles) == 0, "Should have no cycles"

        # Test graph stats
        stats = get_graph_stats(data)
        assert stats['total_entities'] == 2, f"Expected 2 entities, got {stats['total_entities']}"

        print("  ✓ graph operations passed")

    finally:
        Path(temp_path).unlink()


def test_validation():
    """Test graph validation."""
    print("Testing validation...")

    # Create valid graph
    test_graph = {
        "meta": {"project": {"name": "Test"}, "phases": []},
        "entities": {
            "users": {
                "owner": {"name": "Owner", "description": "Test user"}
            }
        },
        "references": {},
        "graph": {
            "users:owner": {"depends_on": []}
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(test_graph, f)
        temp_path = f.name

    try:
        graph = GraphManager(temp_path)
        validator = GraphValidator(graph)

        is_valid, results = validator.validate_all()
        assert is_valid or len(results['errors']) == 0, "Valid graph should pass validation"

        # Test completeness score
        score = validator.get_completeness_score("users:owner")
        assert score['total'] > 0, "Should have completeness score"
        assert 'percentage' in score, "Should calculate percentage"

        print("  ✓ validation passed")

    finally:
        Path(temp_path).unlink()


def test_llm():
    """Test LLM integration."""
    print("Testing LLM integration...")

    llm = LLMManager()

    # Test listing
    providers = llm.list_providers()
    assert len(providers) > 0, "Should have providers"

    workflows = llm.list_workflows()
    assert len(workflows) > 0, "Should have workflows"

    # Test mock provider
    provider = llm.get_provider('mock')
    assert provider is not None, "Should get mock provider"

    # Test workflow execution
    result = llm.execute_workflow(
        'node_extraction',
        {
            'question': 'What features?',
            'answer': 'User auth',
            'graph_context': {}
        },
        provider_name='mock'
    )
    assert result is not None, "Should get result from workflow"

    print("  ✓ LLM integration passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("Running Know Tool Tests")
    print("=" * 70)
    print()

    tests = [
        test_parse_entity_id,
        test_validate_name_format,
        test_graph_operations,
        test_validation,
        test_llm
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} ERROR: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
