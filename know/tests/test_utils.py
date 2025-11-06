"""
Tests for utility functions.
"""

import pytest
from src.utils import (
    parse_entity_id,
    format_entity_id,
    normalize_entity_type,
    validate_name_format,
    truncate_text,
    format_list,
    find_fuzzy_match,
    snake_to_kebab,
    kebab_to_snake
)


def test_parse_entity_id_valid():
    """Test parsing valid entity ID."""
    entity_type, entity_name = parse_entity_id("features:analytics")

    assert entity_type == "features"
    assert entity_name == "analytics"


def test_parse_entity_id_invalid():
    """Test parsing invalid entity ID."""
    entity_type, entity_name = parse_entity_id("invalid")

    assert entity_type is None
    assert entity_name is None


def test_format_entity_id():
    """Test formatting entity ID."""
    result = format_entity_id("features", "analytics")

    assert result == "features:analytics"


def test_normalize_entity_type():
    """Test normalizing entity type to lowercase (no pluralization)."""
    assert normalize_entity_type("Feature") == "feature"
    assert normalize_entity_type("COMPONENT") == "component"
    assert normalize_entity_type("action") == "action"


def test_validate_name_format_valid():
    """Test validating valid names."""
    is_valid, error = validate_name_format("user-dashboard")
    assert is_valid
    assert error is None

    is_valid, error = validate_name_format("feature-123")
    assert is_valid


def test_validate_name_format_invalid_spaces():
    """Test detecting spaces in names."""
    is_valid, error = validate_name_format("user dashboard")
    assert not is_valid
    assert "spaces" in error.lower()


def test_validate_name_format_invalid_uppercase():
    """Test detecting uppercase in names."""
    is_valid, error = validate_name_format("UserDashboard")
    assert not is_valid
    assert "lowercase" in error.lower()


def test_validate_name_format_invalid_underscore():
    """Test detecting underscores in names."""
    is_valid, error = validate_name_format("user_dashboard")
    assert not is_valid
    assert "dash" in error.lower()


def test_truncate_text():
    """Test text truncation."""
    text = "This is a very long text that should be truncated"

    result = truncate_text(text, max_length=20)

    assert len(result) <= 20
    assert result.endswith("...")


def test_truncate_text_no_truncation():
    """Test text that doesn't need truncation."""
    text = "Short text"

    result = truncate_text(text, max_length=20)

    assert result == text


def test_format_list_single():
    """Test formatting single item list."""
    result = format_list(["apple"])
    assert result == "apple"


def test_format_list_two():
    """Test formatting two item list."""
    result = format_list(["apple", "banana"])
    assert result == "apple and banana"


def test_format_list_multiple():
    """Test formatting multiple item list."""
    result = format_list(["apple", "banana", "cherry"])
    assert result == "apple, banana, and cherry"


def test_format_list_no_oxford():
    """Test formatting without Oxford comma."""
    result = format_list(["apple", "banana", "cherry"], oxford_comma=False)
    assert result == "apple, banana and cherry"


def test_find_fuzzy_match_exact():
    """Test exact fuzzy match."""
    candidates = ["apple", "banana", "cherry"]

    matches = find_fuzzy_match("apple", candidates)

    assert "apple" in matches


def test_find_fuzzy_match_substring():
    """Test substring fuzzy match."""
    candidates = ["apple-pie", "banana-split", "cherry-tart"]

    matches = find_fuzzy_match("apple", candidates)

    assert "apple-pie" in matches


def test_find_fuzzy_match_no_match():
    """Test fuzzy match with no results."""
    candidates = ["apple", "banana", "cherry"]

    matches = find_fuzzy_match("zzzzz", candidates)

    assert len(matches) == 0


def test_snake_to_kebab():
    """Test converting snake_case to kebab-case."""
    assert snake_to_kebab("user_dashboard") == "user-dashboard"
    assert snake_to_kebab("my_feature_name") == "my-feature-name"


def test_kebab_to_snake():
    """Test converting kebab-case to snake_case."""
    assert kebab_to_snake("user-dashboard") == "user_dashboard"
    assert kebab_to_snake("my-feature-name") == "my_feature_name"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
