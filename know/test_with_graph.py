#!/usr/bin/env python3
"""
Test know commands with minimal test graph.
"""

import sys
import json
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Import minimal version that doesn't require networkx
try:
    from know_minimal import GraphManager, EntityManager
    print("Using know_minimal (no networkx)")
except ImportError:
    print("ERROR: Cannot import know_minimal")
    sys.exit(1)


def test_graph_loading():
    """Test loading the graph."""
    print("\n" + "=" * 70)
    print("Test 1: Graph Loading")
    print("=" * 70)

    graph = GraphManager("test-graph.json")
    data = graph.get_graph()

    assert 'entities' in data, "Graph should have entities"
    assert 'graph' in data, "Graph should have graph section"

    print(f"✓ Graph loaded successfully")
    print(f"  - Entity types: {len(data['entities'])}")
    print(f"  - Total graph nodes: {len(data['graph'])}")

    return graph


def test_entity_operations(graph):
    """Test entity operations."""
    print("\n" + "=" * 70)
    print("Test 2: Entity Operations")
    print("=" * 70)

    entities = EntityManager(graph)

    # List all entities
    all_entities = entities.list_entities()
    print(f"✓ Found {len(all_entities)} total entities:")
    for e in all_entities[:5]:
        print(f"    {e}")
    if len(all_entities) > 5:
        print(f"    ... and {len(all_entities) - 5} more")

    # List by type
    users = entities.list_entities('users')
    print(f"\n✓ Found {len(users)} users:")
    for u in users:
        print(f"    {u}")

    # Get specific entity
    admin = entities.get_entity('users:admin')
    assert admin is not None, "Should find admin user"
    print(f"\n✓ Retrieved entity 'users:admin':")
    print(f"    Name: {admin.get('name')}")
    print(f"    Description: {admin.get('description')}")

    return entities


def test_dependencies(graph):
    """Test dependency operations."""
    print("\n" + "=" * 70)
    print("Test 3: Dependencies")
    print("=" * 70)

    data = graph.get_graph()
    graph_data = data.get('graph', {})

    # Get dependencies for a feature
    feature_deps = graph_data.get('features:user-management', {}).get('depends_on', [])
    print(f"✓ Feature 'user-management' depends on:")
    for dep in feature_deps:
        print(f"    {dep}")

    # Find what depends on an action
    dependents = []
    for node_id, node_data in graph_data.items():
        if 'actions:create-user' in node_data.get('depends_on', []):
            dependents.append(node_id)

    print(f"\n✓ Entities that depend on 'actions:create-user':")
    for dep in dependents:
        print(f"    {dep}")

    return len(feature_deps), len(dependents)


def test_graph_traversal(graph):
    """Test graph traversal."""
    print("\n" + "=" * 70)
    print("Test 4: Graph Traversal")
    print("=" * 70)

    data = graph.get_graph()
    graph_data = data.get('graph', {})

    # Trace dependency chain
    def get_deps_recursive(entity_id, visited=None):
        if visited is None:
            visited = set()
        if entity_id in visited:
            return []

        visited.add(entity_id)
        deps = graph_data.get(entity_id, {}).get('depends_on', [])

        result = [entity_id]
        for dep in deps:
            result.extend(get_deps_recursive(dep, visited))

        return result

    chain = get_deps_recursive('users:admin')
    print(f"✓ Full dependency chain for 'users:admin':")
    for i, item in enumerate(chain):
        print(f"    {i+1}. {item}")

    return len(chain)


def test_entity_counts(graph):
    """Test entity counting."""
    print("\n" + "=" * 70)
    print("Test 5: Entity Statistics")
    print("=" * 70)

    data = graph.get_graph()
    entities_data = data.get('entities', {})

    print("✓ Entity counts by type:")
    total = 0
    for entity_type, entities in entities_data.items():
        count = len(entities) if isinstance(entities, dict) else 0
        total += count
        print(f"    {entity_type}: {count}")

    print(f"\n  Total entities: {total}")

    return total


def test_reference_access(graph):
    """Test reference access."""
    print("\n" + "=" * 70)
    print("Test 6: References")
    print("=" * 70)

    data = graph.get_graph()
    references = data.get('references', {})

    print("✓ Reference types:")
    for ref_type, refs in references.items():
        count = len(refs) if isinstance(refs, dict) else 0
        print(f"    {ref_type}: {count} items")

        # Show first reference
        if isinstance(refs, dict) and refs:
            first_key = list(refs.keys())[0]
            first_ref = refs[first_key]
            print(f"      Example: {first_key}")
            if isinstance(first_ref, dict) and 'description' in first_ref:
                desc = first_ref['description']
                if len(desc) > 50:
                    desc = desc[:50] + "..."
                print(f"        {desc}")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("Know Tool - Minimal Graph Tests")
    print("=" * 70)
    print("\nTest Graph: test-graph.json")

    try:
        # Load graph
        graph = test_graph_loading()

        # Test entity operations
        entities = test_entity_operations(graph)

        # Test dependencies
        dep_count, dependent_count = test_dependencies(graph)

        # Test traversal
        chain_length = test_graph_traversal(graph)

        # Test statistics
        total_entities = test_entity_counts(graph)

        # Test references
        test_reference_access(graph)

        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        print(f"✓ All tests passed")
        print(f"\nGraph Statistics:")
        print(f"  - Total entities: {total_entities}")
        print(f"  - Dependency chain length: {chain_length}")
        print(f"  - Sample dependencies found: {dep_count}")
        print(f"  - Sample dependents found: {dependent_count}")
        print("\n✓ Graph is valid and functional")

        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
