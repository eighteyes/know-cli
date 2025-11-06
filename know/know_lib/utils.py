"""
Utility functions for the know tool.
Common helpers for formatting, parsing, and data manipulation.
"""

import re
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path


def parse_entity_id(entity_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse an entity ID into type and name.

    Args:
        entity_id: Entity ID in format "type:name"

    Returns:
        Tuple of (entity_type, entity_name) or (None, None) if invalid
    """
    if ':' not in entity_id:
        return None, None

    parts = entity_id.split(':', 1)
    if len(parts) != 2:
        return None, None

    return parts[0], parts[1]


def format_entity_id(entity_type: str, entity_name: str) -> str:
    """
    Format an entity type and name into an ID.

    Args:
        entity_type: Entity type
        entity_name: Entity name

    Returns:
        Entity ID in format "type:name"
    """
    return f"{entity_type}:{entity_name}"


def normalize_entity_type(entity_type: str) -> str:
    """
    Normalize entity type to lowercase.

    NOTE: All entity types in the system use singular forms.
    The dependency rules use singular forms like 'feature', 'action', 'component'.

    Args:
        entity_type: Entity type to normalize

    Returns:
        Normalized entity type (lowercase, no plural conversion)
    """
    return entity_type.lower()


def snake_to_kebab(text: str) -> str:
    """
    Convert snake_case to kebab-case.

    Args:
        text: Text in snake_case

    Returns:
        Text in kebab-case
    """
    return text.replace('_', '-')


def kebab_to_snake(text: str) -> str:
    """
    Convert kebab-case to snake_case.

    Args:
        text: Text in kebab-case

    Returns:
        Text in snake_case
    """
    return text.replace('-', '_')


def validate_name_format(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate entity/reference name format.

    Args:
        name: Name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Should use kebab-case (lowercase with dashes)
    if not name:
        return False, "Name cannot be empty"

    # Check for spaces
    if ' ' in name:
        return False, "Name cannot contain spaces (use dashes instead)"

    # Check for uppercase
    if name != name.lower():
        return False, "Name should be lowercase"

    # Check for underscores (should use dashes)
    if '_' in name:
        return False, "Name should use dashes, not underscores"

    # Check for invalid characters
    if not re.match(r'^[a-z0-9-]+$', name):
        return False, "Name can only contain lowercase letters, numbers, and dashes"

    # Check for leading/trailing dashes
    if name.startswith('-') or name.endswith('-'):
        return False, "Name cannot start or end with a dash"

    # Check for consecutive dashes
    if '--' in name:
        return False, "Name cannot contain consecutive dashes"

    return True, None


def truncate_text(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_list(items: List[str], connector: str = "and", oxford_comma: bool = True) -> str:
    """
    Format a list of items into a human-readable string.

    Args:
        items: List of items
        connector: Word to use between last two items
        oxford_comma: Whether to use Oxford comma

    Returns:
        Formatted string
    """
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} {connector} {items[1]}"

    if oxford_comma:
        return ", ".join(items[:-1]) + f", {connector} {items[-1]}"
    else:
        return ", ".join(items[:-1]) + f" {connector} {items[-1]}"


def get_entity_display_name(entity_data: Dict[str, Any], fallback_name: str) -> str:
    """
    Get the display name for an entity.

    Args:
        entity_data: Entity data dictionary
        fallback_name: Name to use if entity has no name field

    Returns:
        Display name
    """
    return entity_data.get('name', fallback_name)


def find_fuzzy_match(query: str, candidates: List[str], threshold: int = 2) -> List[str]:
    """
    Find fuzzy matches for a query string.

    Args:
        query: Query string
        candidates: List of candidate strings
        threshold: Maximum edit distance for a match

    Returns:
        List of matching candidates
    """
    query_lower = query.lower()
    matches = []

    for candidate in candidates:
        candidate_lower = candidate.lower()

        # Exact match
        if query_lower == candidate_lower:
            matches.append(candidate)
            continue

        # Substring match
        if query_lower in candidate_lower:
            matches.append(candidate)
            continue

        # Simple edit distance check (Levenshtein)
        distance = _edit_distance(query_lower, candidate_lower)
        if distance <= threshold:
            matches.append(candidate)

    return matches


def _edit_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein edit distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance
    """
    if len(s1) < len(s2):
        return _edit_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def safe_filename(text: str) -> str:
    """
    Convert text to a safe filename.

    Args:
        text: Text to convert

    Returns:
        Safe filename
    """
    # Replace spaces and special chars with dashes
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'[\s_]+', '-', safe)
    safe = safe.strip('-').lower()
    return safe


def group_by(items: List[Dict], key: str) -> Dict[Any, List[Dict]]:
    """
    Group a list of dictionaries by a key.

    Args:
        items: List of dictionaries
        key: Key to group by

    Returns:
        Dictionary mapping key values to lists of items
    """
    groups = {}
    for item in items:
        group_key = item.get(key)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)

    return groups


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator between keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def resolve_graph_path(path: Optional[str] = None) -> Path:
    """
    Resolve the path to the spec-graph.json file.

    Args:
        path: Optional path override

    Returns:
        Resolved Path object
    """
    if path:
        return Path(path).resolve()

    # Default path
    default_path = Path('.ai/spec-graph.json')

    # Check if we're in a subdirectory
    if not default_path.exists():
        # Try parent directory
        parent_path = Path('../.ai/spec-graph.json')
        if parent_path.exists():
            return parent_path.resolve()

    return default_path.resolve()


def count_entity_types(data: Dict) -> Dict[str, int]:
    """
    Count entities by type.

    Args:
        data: Graph data

    Returns:
        Dictionary mapping entity types to counts
    """
    entities = data.get('entities', {})
    counts = {}

    for entity_type, entity_list in entities.items():
        if isinstance(entity_list, dict):
            counts[entity_type] = len(entity_list)

    return counts


def get_graph_stats(data: Dict) -> Dict[str, Any]:
    """
    Get statistics about the graph.

    Args:
        data: Graph data

    Returns:
        Dictionary of statistics
    """
    stats = {
        'entity_types': len(data.get('entities', {})),
        'reference_types': len(data.get('references', {})),
        'graph_nodes': len(data.get('graph', {})),
        'entities_by_type': count_entity_types(data)
    }

    # Count total entities
    stats['total_entities'] = sum(stats['entities_by_type'].values())

    # Count total references
    references = data.get('references', {})
    ref_counts = {}
    for ref_type, ref_list in references.items():
        if isinstance(ref_list, dict):
            ref_counts[ref_type] = len(ref_list)

    stats['references_by_type'] = ref_counts
    stats['total_references'] = sum(ref_counts.values())

    # Count dependencies
    graph = data.get('graph', {})
    total_deps = 0
    for node_data in graph.values():
        if isinstance(node_data, dict):
            total_deps += len(node_data.get('depends_on', []))

    stats['total_dependencies'] = total_deps

    return stats
