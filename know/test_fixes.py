#!/usr/bin/env python3
"""
Test script to verify bug fixes
"""

import json
from pathlib import Path
from know_lib import GraphManager, EntityManager, DependencyManager, GraphValidator

def test_bug_fixes():
    """Test all bug fixes"""
    print("Testing Bug Fixes\n" + "="*50 + "\n")

    # Use test-graph.json
    graph_path = Path(__file__).parent / "test-graph.json"

    # Initialize managers
    graph = GraphManager(str(graph_path))
    entities = EntityManager(graph)
    deps = DependencyManager(graph)
    validator = GraphValidator(graph)

    # Bug #1: Test that 'operation' is now a valid entity type
    print("Bug #1: Testing 'operation' entity type")
    print(f"Valid entity types: {sorted(entities.VALID_ENTITY_TYPES)}")

    if 'operation' in entities.VALID_ENTITY_TYPES:
        print("✓ 'operation' is recognized as valid entity type\n")
    else:
        print("✗ FAILED: 'operation' still not recognized\n")

    # Bug #2: Test topological sort with no cycles
    print("Bug #2: Testing build-order cycle detection")
    cycles = deps.detect_cycles()
    build_order = deps.topological_sort()

    print(f"Cycles detected: {len(cycles)}")
    print(f"Build order result: {'Valid' if build_order else 'Invalid (returned empty)'}")

    if not cycles and build_order:
        print("✓ Build order works correctly when no cycles exist\n")
    elif cycles and not build_order:
        print("✓ Build order correctly returns empty for cyclic graph\n")
    else:
        print("✗ FAILED: Build order logic inconsistent\n")

    # Bug #4: Test allowed metadata fields
    print("Bug #4: Testing allowed metadata fields")
    print(f"Allowed metadata: {sorted(validator.allowed_metadata)}")

    if 'path' in validator.allowed_metadata:
        print("✓ Custom metadata fields (like 'path') are now allowed\n")
    else:
        print("✗ FAILED: Metadata fields not loaded from rules\n")

    print("\n" + "="*50)
    print("Summary:")
    print(f"  Entity types loaded from rules: {len(entities.VALID_ENTITY_TYPES)}")
    print(f"  Allowed metadata fields: {len(validator.allowed_metadata)}")
    print(f"  Graph has cycles: {bool(cycles)}")
    print(f"  Build order available: {bool(build_order)}")

if __name__ == '__main__':
    test_bug_fixes()
