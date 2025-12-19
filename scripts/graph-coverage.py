#!/usr/bin/env python3
"""
Graph Coverage Analyzer
Measures what % of entities are connected to root users via dependency chains.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict, deque


def load_graph(graph_path):
    """Load graph JSON file"""
    with open(graph_path) as f:
        return json.load(f)


def build_reverse_graph(graph_data):
    """Build reverse dependency graph (who uses this entity)"""
    reverse = defaultdict(list)
    graph = graph_data.get('graph', {})

    for entity_id, data in graph.items():
        for dep in data.get('depends_on', []):
            reverse[dep].append(entity_id)

    return reverse


def find_roots(graph_data):
    """Find root entities (users, or entities not depended on by anything)"""
    entities = graph_data.get('entities', {})
    graph = graph_data.get('graph', {})
    reverse = build_reverse_graph(graph_data)

    # Get all user entities as roots
    roots = []
    for entity_type, entities_of_type in entities.items():
        if entity_type == 'user':
            for entity_id in entities_of_type:
                roots.append(f"user:{entity_id}")

    # If no users, find entities that nothing depends on
    if not roots:
        all_entities = set()
        for entity_type, entities_of_type in entities.items():
            for entity_id in entities_of_type:
                all_entities.add(f"{entity_type}:{entity_id}")

        depended_on = set()
        for entity_id, data in graph.items():
            for dep in data.get('depends_on', []):
                depended_on.add(dep)

        roots = list(all_entities - depended_on)

    return roots


def find_reachable_from_roots(graph_data, roots):
    """BFS to find all entities reachable from roots via depends_on"""
    graph = graph_data.get('graph', {})
    reachable = set()
    queue = deque(roots)

    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)

        # Add all dependencies to queue
        if current in graph:
            for dep in graph[current].get('depends_on', []):
                if dep not in reachable:
                    queue.append(dep)

    return reachable


def get_all_entity_ids(graph_data):
    """Get all entity IDs in the graph"""
    entities = graph_data.get('entities', {})
    all_ids = []

    for entity_type, entities_of_type in entities.items():
        for entity_id in entities_of_type:
            all_ids.append(f"{entity_type}:{entity_id}")

    return all_ids


def get_entities_in_graph(graph_data):
    """Get entity IDs that have dependencies defined"""
    return set(graph_data.get('graph', {}).keys())


def analyze_coverage(graph_path, verbose=False):
    """Analyze graph coverage and return metrics"""
    graph_data = load_graph(graph_path)

    # Find roots (users)
    roots = find_roots(graph_data)

    # Find all entities reachable from roots
    reachable = find_reachable_from_roots(graph_data, roots)

    # Get all entities
    all_entities = set(get_all_entity_ids(graph_data))
    entities_in_graph = get_entities_in_graph(graph_data)

    # Calculate metrics
    total_entities = len(all_entities)
    connected_entities = len(reachable)
    entities_with_deps = len(entities_in_graph)
    floating_entities = all_entities - entities_in_graph
    disconnected_chains = entities_in_graph - reachable

    coverage_pct = (connected_entities / total_entities * 100) if total_entities > 0 else 0

    results = {
        'total_entities': total_entities,
        'connected_to_roots': connected_entities,
        'coverage_percentage': round(coverage_pct, 1),
        'entities_with_dependencies': entities_with_deps,
        'floating_entities': sorted(list(floating_entities)),
        'disconnected_chains': sorted(list(disconnected_chains)),
        'roots': sorted(roots)
    }

    if verbose:
        print(f"\n{'='*60}")
        print(f"Graph Coverage Report: {graph_path}")
        print(f"{'='*60}")
        print(f"\nRoots (users): {len(roots)}")
        for root in sorted(roots):
            print(f"  • {root}")

        print(f"\nOverall Metrics:")
        print(f"  Total entities:           {total_entities}")
        print(f"  Connected to roots:       {connected_entities}")
        print(f"  Coverage percentage:      {coverage_pct:.1f}%")

        print(f"\nDisconnected Analysis:")
        print(f"  Entities with no deps:    {len(floating_entities)}")
        print(f"  Disconnected chains:      {len(disconnected_chains)}")

        if floating_entities:
            print(f"\n  Floating entities (no dependencies defined):")
            for entity in sorted(floating_entities):
                print(f"    • {entity}")

        if disconnected_chains:
            print(f"\n  Disconnected chains (have deps but not reachable from roots):")
            for entity in sorted(disconnected_chains):
                print(f"    • {entity}")

        print(f"\n{'='*60}\n")

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: graph-coverage.py <path-to-graph.json> [--verbose]")
        sys.exit(1)

    graph_path = sys.argv[1]
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    if not Path(graph_path).exists():
        print(f"Error: Graph file not found: {graph_path}")
        sys.exit(1)

    results = analyze_coverage(graph_path, verbose=verbose)

    if not verbose:
        print(json.dumps(results, indent=2))
