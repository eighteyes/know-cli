"""Property-based tests for the Golden Thread across spec and code graphs.

The Golden Thread is the requirement that:
1. Spec graph has at least one complete chain: user → objective → action → component
2. Code graph has at least one module
3. That module references the component via product-component reference
4. The component actually exists in the spec graph

This ensures traceability from user intent to implementation.
"""

import json
import tempfile
from pathlib import Path
from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st

from .strategies import (
    linked_graphs,
    unlinked_graphs,
    broken_link_graphs,
    valid_spec_graph,
    valid_code_graph,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ============================================================================
# GRAPH PAIR ANALYSIS
# ============================================================================

def find_golden_threads(spec_graph: dict, code_graph: dict) -> list:
    """Find all complete Golden Threads connecting user intent to code.

    Returns: List of dicts, each containing:
        - user: user entity key
        - objective: objective entity key
        - action: action entity key
        - component: component entity key
        - module: module entity key (from code graph)
    """
    threads = []

    # Get all users
    if "user" not in spec_graph["entities"]:
        return threads

    for user_name in spec_graph["entities"]["user"].keys():
        # Build prefixed key for graph lookups
        user_key = f"user:{user_name}"

        # Find objectives this user wants
        if user_key not in spec_graph["graph"]:
            continue

        for objective_key in spec_graph["graph"][user_key].get("depends_on", []):
            if not objective_key.startswith("objective:"):
                continue

            # Find actions for this objective
            if objective_key not in spec_graph["graph"]:
                continue

            for action_key in spec_graph["graph"][objective_key].get("depends_on", []):
                if not action_key.startswith("action:"):
                    continue

                # Find components for this action
                if action_key not in spec_graph["graph"]:
                    continue

                for component_key in spec_graph["graph"][action_key].get("depends_on", []):
                    if not component_key.startswith("component:"):
                        continue

                    # Now find modules that implement this component
                    pc_refs = code_graph.get("references", {}).get("product-component", {})

                    for pc_key, pc_data in pc_refs.items():
                        if pc_data.get("component") == component_key:
                            # Found a complete thread!
                            # pc_key is the unprefixed module name
                            module_name = pc_key
                            module_key = f"module:{module_name}"

                            # Verify module exists (entities dict uses unprefixed keys)
                            if "module" in code_graph.get("entities", {}):
                                if module_name in code_graph["entities"]["module"]:
                                    threads.append({
                                        "user": user_key,
                                        "objective": objective_key,
                                        "action": action_key,
                                        "component": component_key,
                                        "module": module_key,
                                    })

    return threads


def has_orphaned_components(spec_graph: dict) -> list:
    """Find components not reachable from any user.

    Returns: List of component keys that are orphaned.
    """
    if "component" not in spec_graph["entities"]:
        return []

    # Find all components reachable from users
    reachable = set()

    if "user" not in spec_graph["entities"]:
        # No users means all components are orphaned (return prefixed keys)
        return [f"component:{name}" for name in spec_graph["entities"]["component"].keys()]

    # Build prefixed user keys for graph lookups
    for user_name in spec_graph["entities"]["user"].keys():
        user_key = f"user:{user_name}"
        if user_key not in spec_graph["graph"]:
            continue

        for objective_key in spec_graph["graph"][user_key].get("depends_on", []):
            if objective_key not in spec_graph["graph"]:
                continue

            for action_key in spec_graph["graph"][objective_key].get("depends_on", []):
                if action_key not in spec_graph["graph"]:
                    continue

                for component_key in spec_graph["graph"][action_key].get("depends_on", []):
                    if component_key.startswith("component:"):
                        reachable.add(component_key)

    # Find orphans (compare prefixed keys)
    all_components = {f"component:{name}" for name in spec_graph["entities"]["component"].keys()}
    orphans = all_components - reachable

    return list(orphans)


def has_orphaned_modules(code_graph: dict) -> list:
    """Find modules not linked to any spec component.

    Returns: List of module keys with no product-component link.
    """
    if "module" not in code_graph["entities"]:
        return []

    pc_refs = code_graph.get("references", {}).get("product-component", {})
    # pc_refs keys are unprefixed module names
    linked_modules = {f"module:{pc_key}" for pc_key in pc_refs.keys()}

    # all_modules should also be prefixed for comparison
    all_modules = {f"module:{name}" for name in code_graph["entities"]["module"].keys()}
    orphans = all_modules - linked_modules

    return list(orphans)


# ============================================================================
# PROPERTY TESTS
# ============================================================================

@given(graphs=linked_graphs())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_linked_graphs_have_at_least_one_golden_thread(graphs):
    """Property: Graphs explicitly linked MUST have at least one Golden Thread."""
    spec_graph, code_graph = graphs

    threads = find_golden_threads(spec_graph, code_graph)

    assert len(threads) >= 1, \
        f"Linked graphs should have at least one Golden Thread, found {len(threads)}"


@given(graphs=unlinked_graphs())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_unlinked_graphs_have_no_golden_threads(graphs):
    """Property: Graphs with no product-component refs MUST have zero Golden Threads."""
    spec_graph, code_graph = graphs

    threads = find_golden_threads(spec_graph, code_graph)

    assert len(threads) == 0, \
        f"Unlinked graphs should have zero Golden Threads, found {len(threads)}"


@given(graphs=broken_link_graphs())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_broken_links_have_no_complete_threads(graphs):
    """Property: Broken product-component refs MUST NOT create valid Golden Threads."""
    spec_graph, code_graph = graphs

    threads = find_golden_threads(spec_graph, code_graph)

    # Broken links point to non-existent components, so should find zero threads
    assert len(threads) == 0, \
        f"Broken links should not create valid threads, found {len(threads)}"


@given(spec_graph=valid_spec_graph())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_valid_spec_graphs_may_have_orphaned_components(spec_graph):
    """Property: Valid spec graphs MAY have components not reachable from users.

    This is ALLOWED but not ideal. A warning-level validation would catch this.
    """
    orphans = has_orphaned_components(spec_graph)

    # This test just documents that orphans CAN exist
    # The validator could optionally warn about them
    # No assertion - this is informational


@given(code_graph=valid_code_graph())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_valid_code_graphs_may_have_orphaned_modules(code_graph):
    """Property: Valid code graphs MAY have modules not linked to components.

    This is ALLOWED (e.g., utility modules, test modules) but notable.
    """
    orphans = has_orphaned_modules(code_graph)

    # This test documents that orphaned modules can exist
    # No assertion - this is informational


@given(graphs=linked_graphs())
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_product_component_refs_point_to_existing_components(graphs):
    """Property: All product-component refs MUST point to components that exist."""
    spec_graph, code_graph = graphs

    pc_refs = code_graph.get("references", {}).get("product-component", {})

    for pc_key, pc_data in pc_refs.items():
        component_key = pc_data.get("component")

        # Extract component type and check it exists
        if component_key and component_key.startswith("component:"):
            component_name = component_key.split(":")[1]

            assert "component" in spec_graph["entities"], \
                "Spec graph missing component entities"

            # Entities dict uses unprefixed keys
            assert component_name in spec_graph["entities"]["component"], \
                f"product-component ref points to non-existent {component_key}"


# ============================================================================
# REACHABILITY TESTS
# ============================================================================

def get_all_reachable_from_users(spec_graph: dict) -> set:
    """Find all entities reachable from any user via depends_on."""
    reachable = set()

    if "user" not in spec_graph["entities"]:
        return reachable

    # BFS from all users (need prefixed keys for graph lookups)
    to_visit = [f"user:{name}" for name in spec_graph["entities"]["user"].keys()]
    visited = set()

    while to_visit:
        current = to_visit.pop(0)

        if current in visited:
            continue

        visited.add(current)
        reachable.add(current)

        # Add dependencies to queue
        if current in spec_graph["graph"]:
            for dep in spec_graph["graph"][current].get("depends_on", []):
                if dep not in visited:
                    to_visit.append(dep)

    return reachable


@given(spec_graph=valid_spec_graph())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_components_in_golden_thread_are_reachable(spec_graph):
    """Property: A valid spec graph MAY have components reachable from users.

    This test is informational - it demonstrates reachability analysis.
    Not all components need to be reachable (some may be planned but not linked yet).
    """
    reachable = get_all_reachable_from_users(spec_graph)

    # Filter for components
    reachable_components = {
        key for key in reachable if key.startswith("component:")
    }

    # Document that we can find reachable components
    # No strict assertion - this is informational


# ============================================================================
# CROSS-GRAPH VALIDATION SCENARIO TESTS
# ============================================================================

@given(
    spec_graph=valid_spec_graph(),
    code_graph=valid_code_graph()
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_independent_valid_graphs_dont_guarantee_golden_thread(spec_graph, code_graph):
    """Property: Two independently valid graphs MAY NOT have Golden Thread.

    This demonstrates why cross-graph validation is needed.
    """
    threads = find_golden_threads(spec_graph, code_graph)

    # Most random pairs won't have Golden Thread
    # This test documents the need for explicit linking
    # No specific assertion - informational


@given(graphs=linked_graphs())
@settings(max_examples=15, suppress_health_check=[HealthCheck.too_slow])
def test_golden_thread_preserves_user_intent_chain(graphs):
    """Property: Golden Thread MUST maintain user→objective→action→component sequence."""
    spec_graph, code_graph = graphs

    threads = find_golden_threads(spec_graph, code_graph)

    for thread in threads:
        # Verify the chain exists in spec graph
        user_key = thread["user"]
        objective_key = thread["objective"]
        action_key = thread["action"]
        component_key = thread["component"]

        # User → Objective
        assert user_key in spec_graph["graph"], f"{user_key} not in graph"
        assert objective_key in spec_graph["graph"][user_key]["depends_on"], \
            f"{user_key} doesn't depend on {objective_key}"

        # Objective → Action
        assert objective_key in spec_graph["graph"], f"{objective_key} not in graph"
        assert action_key in spec_graph["graph"][objective_key]["depends_on"], \
            f"{objective_key} doesn't depend on {action_key}"

        # Action → Component
        assert action_key in spec_graph["graph"], f"{action_key} not in graph"
        assert component_key in spec_graph["graph"][action_key]["depends_on"], \
            f"{action_key} doesn't depend on {component_key}"
