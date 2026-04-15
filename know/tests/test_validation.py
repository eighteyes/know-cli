"""
Tests for graph validation.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src import GraphManager, GraphValidator


@pytest.fixture
def valid_graph():
    """Create a valid graph for testing."""
    return {
        "meta": {
            "project": {"name": "Test Project"},
            "horizons": []
        },
        "entities": {
            "users": {
                "owner": {
                    "name": "Owner",
                    "description": "System owner"
                }
            },
            "features": {
                "tracking": {
                    "name": "Tracking",
                    "description": "Track items"
                }
            }
        },
        "references": {
            "acceptance_criteria": {
                "accuracy": {
                    "description": "Must be accurate"
                }
            }
        },
        "graph": {
            "users:owner": {"depends_on": []},
            "features:tracking": {"depends_on": []}
        }
    }


@pytest.fixture
def invalid_graph():
    """Create an invalid graph for testing."""
    return {
        "meta": {},
        "entities": {
            "features": {
                "bad_name": {  # underscore instead of dash
                    "name": "Bad Feature"
                    # missing description
                }
            }
        },
        "references": {},
        "graph": {
            "features:bad_name": {"depends_on": []},
            "orphaned:node": {"depends_on": []}  # orphaned node
        }
    }


def test_valid_graph_validation():
    """Test validation of a valid graph."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(valid_graph(), f)
        temp_path = f.name

    try:
        graph = GraphManager(temp_path)
        validator = GraphValidator(graph)

        is_valid, results = validator.validate_all()

        assert is_valid
        assert len(results['errors']) == 0

    finally:
        Path(temp_path).unlink()


def test_invalid_graph_validation():
    """Test validation of an invalid graph."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(invalid_graph(), f)
        temp_path = f.name

    try:
        graph = GraphManager(temp_path)
        validator = GraphValidator(graph)

        is_valid, results = validator.validate_all()

        assert not is_valid
        assert len(results['errors']) > 0 or len(results['warnings']) > 0

    finally:
        Path(temp_path).unlink()


def test_missing_descriptions():
    """Test detection of missing descriptions."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        graph_data = valid_graph()
        del graph_data['entities']['users']['owner']['description']
        json.dump(graph_data, f)
        temp_path = f.name

    try:
        graph = GraphManager(temp_path)
        validator = GraphValidator(graph)

        is_valid, results = validator.validate_all()

        # Should have warnings about missing descriptions
        assert len(results['warnings']) > 0

    finally:
        Path(temp_path).unlink()


def test_naming_conventions():
    """Test naming convention validation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(invalid_graph(), f)
        temp_path = f.name

    try:
        graph = GraphManager(temp_path)
        validator = GraphValidator(graph)

        naming_results = validator.validate_naming_conventions()

        # Should warn about underscore in entity name
        assert len(naming_results['warnings']) > 0

    finally:
        Path(temp_path).unlink()


def test_completeness_score():
    """Test completeness scoring."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(valid_graph(), f)
        temp_path = f.name

    try:
        graph = GraphManager(temp_path)
        validator = GraphValidator(graph)

        score = validator.get_completeness_score("users:owner")

        assert 'total' in score
        assert 'completed' in score
        assert 'percentage' in score
        assert score['percentage'] > 0

    finally:
        Path(temp_path).unlink()


def test_orphaned_nodes():
    """Test detection of orphaned nodes."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(invalid_graph(), f)
        temp_path = f.name

    try:
        graph = GraphManager(temp_path)
        validator = GraphValidator(graph)

        is_valid, results = validator.validate_all()

        # Should detect orphaned:node
        assert any('orphaned' in str(e).lower() for e in results['errors'])

    finally:
        Path(temp_path).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
