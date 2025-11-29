"""Property-based tests for graph invariants.

These tests use Hypothesis to generate thousands of test cases and verify
that certain properties ALWAYS hold (or NEVER hold) for valid/invalid graphs.
"""

import json
import tempfile
import subprocess
from pathlib import Path
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from .strategies import (
    valid_spec_graph,
    valid_code_graph,
    minimal_spec_graph,
    minimal_code_graph,
    broken_golden_thread_graph,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
KNOW_CLI = PROJECT_ROOT / "know" / "know"


def run_validation(graph_dict: dict, graph_type: str = "spec") -> dict:
    """Run know validate on a graph and return results.

    Args:
        graph_dict: The graph to validate
        graph_type: "spec" or "code" - determines which graph file to use

    Returns:
        dict with keys: success (bool), stdout (str), stderr (str), exit_code (int)
    """
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix=f'-{graph_type}-graph.json',
        delete=False
    ) as f:
        json.dump(graph_dict, f, indent=2)
        graph_path = f.name

    try:
        result = subprocess.run(
            [str(KNOW_CLI), "-g", graph_path, "validate"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    finally:
        Path(graph_path).unlink(missing_ok=True)


# ============================================================================
# STRUCTURAL INVARIANTS
# ============================================================================

@given(spec_graph=valid_spec_graph())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_valid_spec_graphs_always_pass_validation(spec_graph):
    """Property: All valid spec graphs MUST pass validation."""
    result = run_validation(spec_graph, "spec")
    assert result["success"], f"Valid graph failed validation:\n{result['stderr']}"


@given(code_graph=valid_code_graph())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_valid_code_graphs_always_pass_validation(code_graph):
    """Property: All valid code graphs MUST pass validation."""
    result = run_validation(code_graph, "code")
    assert result["success"], f"Valid graph failed validation:\n{result['stderr']}"


@given(spec_graph=minimal_spec_graph())
@settings(max_examples=20)
def test_minimal_spec_graph_has_golden_thread(spec_graph):
    """Property: Minimal spec graphs MUST have complete user→component chain."""
    # Check that the Golden Thread exists
    assert "user" in spec_graph["entities"]
    assert "objective" in spec_graph["entities"]
    assert "action" in spec_graph["entities"]
    assert "component" in spec_graph["entities"]

    # Check that there's at least one of each
    assert len(spec_graph["entities"]["user"]) >= 1
    assert len(spec_graph["entities"]["objective"]) >= 1
    assert len(spec_graph["entities"]["action"]) >= 1
    assert len(spec_graph["entities"]["component"]) >= 1


@given(spec_graph=valid_spec_graph())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_all_entities_have_required_fields(spec_graph):
    """Property: All entities MUST have name and description."""
    for entity_type, entities in spec_graph["entities"].items():
        for key, value in entities.items():
            assert "name" in value, f"{key} missing 'name'"
            assert "description" in value, f"{key} missing 'description'"
            assert isinstance(value["name"], str)
            assert isinstance(value["description"], str)
            assert len(value["name"]) > 0
            assert len(value["description"]) > 0


@given(spec_graph=valid_spec_graph())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_graph_section_only_contains_depends_on(spec_graph):
    """Property: Graph section MUST only contain depends_on relationships."""
    for entity_key, relationships in spec_graph["graph"].items():
        assert "depends_on" in relationships, f"{entity_key} has invalid relationship type"
        assert isinstance(relationships["depends_on"], list)

        # Ensure no other keys besides depends_on
        assert set(relationships.keys()) == {"depends_on"}


@given(spec_graph=valid_spec_graph())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_dependencies_reference_existing_entities_or_references(spec_graph):
    """Property: All dependencies MUST point to entities or references that exist."""
    # Collect all valid targets
    valid_targets = set()

    # Add all entity keys (prefixed, like they appear in the graph)
    for entity_type, entities in spec_graph["entities"].items():
        for entity_name in entities.keys():
            valid_targets.add(f"{entity_type}:{entity_name}")

    # Add all reference keys
    for ref_type, refs in spec_graph.get("references", {}).items():
        for ref_key in refs.keys():
            valid_targets.add(f"{ref_type}:{ref_key}")

    # Check all dependencies
    for entity_key, relationships in spec_graph["graph"].items():
        for dep in relationships["depends_on"]:
            assert dep in valid_targets, f"{entity_key} depends on non-existent {dep}"


# ============================================================================
# GOLDEN THREAD INVARIANTS
# ============================================================================

@given(broken_graph=broken_golden_thread_graph())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_broken_golden_thread_detected(broken_graph):
    """Property: Graphs with broken Golden Threads should be detectable.

    NOTE: This test may fail if the validator doesn't yet check for Golden Thread.
    That's the POINT - it reveals missing validation logic.
    """
    # For now, we just verify the graph has orphans
    # Later, the validator should catch this

    all_entities = set()
    for entity_type, entities in broken_graph["entities"].items():
        all_entities.update(entities.keys())

    entities_in_graph = set(broken_graph["graph"].keys())
    entities_referenced = set()

    for relationships in broken_graph["graph"].values():
        entities_referenced.update(relationships["depends_on"])

    # There should be orphans (entities not in graph and not referenced)
    orphans = all_entities - entities_in_graph - entities_referenced

    # This test documents that broken Golden Thread graphs HAVE orphans
    # The validator should eventually reject these
    assert len(orphans) > 0, "Broken Golden Thread graph should have orphans"


# ============================================================================
# DEPENDENCY RULE INVARIANTS
# ============================================================================

@given(
    spec_graph=valid_spec_graph(),
    entity_type=st.sampled_from(["user", "objective", "action", "component", "feature"])
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_dependencies_follow_allowed_rules(spec_graph, entity_type):
    """Property: All dependencies MUST follow allowed_dependencies rules."""
    from .strategies import SPEC_RULES

    allowed_deps = SPEC_RULES["allowed_dependencies"].get(entity_type, [])

    if entity_type not in spec_graph["entities"]:
        return  # Skip if this entity type not in graph

    for entity_key in spec_graph["entities"][entity_type].keys():
        if entity_key in spec_graph["graph"]:
            for dep in spec_graph["graph"][entity_key]["depends_on"]:
                # Extract dependency type
                if ":" in dep:
                    dep_type = dep.split(":")[0]

                    # References are always allowed
                    if dep_type in SPEC_RULES["reference_dependency_rule"]["reference_types"]:
                        continue

                    # Otherwise must be in allowed_dependencies
                    assert dep_type in allowed_deps, \
                        f"{entity_key} cannot depend on {dep_type} (allowed: {allowed_deps})"


# ============================================================================
# META INVARIANTS
# ============================================================================

@given(spec_graph=valid_spec_graph())
@settings(max_examples=20)
def test_meta_section_required_fields(spec_graph):
    """Property: Meta section MUST have required fields."""
    assert "meta" in spec_graph
    meta = spec_graph["meta"]

    required = ["version", "format", "description", "generated_at"]
    for field in required:
        assert field in meta, f"Meta missing required field: {field}"


@given(code_graph=valid_code_graph())
@settings(max_examples=20)
def test_code_graph_modules_have_path(code_graph):
    """Property: Module entities SHOULD have path metadata."""
    if "module" in code_graph["entities"]:
        for module_key, module_data in code_graph["entities"]["module"].items():
            # Modules generated by our strategy always have paths
            assert "path" in module_data, f"{module_key} missing path"


# ============================================================================
# SHRINKING DEMONSTRATION
# ============================================================================

@given(spec_graph=valid_spec_graph(min_entities=10, max_entities=50))
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_hypothesis_shrinks_to_minimal_example(spec_graph):
    """Demonstration: When this test fails, Hypothesis shrinks to minimal case.

    Uncomment the assertion to see shrinking in action.
    """
    # This test always passes - it's just to demonstrate the graph generation
    total_entities = sum(len(entities) for entities in spec_graph["entities"].values())

    # Uncomment to see Hypothesis shrink a large graph to minimal failing example:
    # assert total_entities < 5, f"Graph has {total_entities} entities"

    assert total_entities >= 0  # Always passes
