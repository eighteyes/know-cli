"""Hypothesis strategies for generating spec and code graphs.

This module provides composable strategies for building valid and invalid graphs
based on the dependency rules defined in know/config/*.json.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy
from datetime import datetime

# Load dependency rules
PROJECT_ROOT = Path(__file__).parent.parent.parent
SPEC_RULES_PATH = PROJECT_ROOT / "know" / "config" / "dependency-rules.json"
CODE_RULES_PATH = PROJECT_ROOT / "know" / "config" / "code-dependency-rules.json"

with open(SPEC_RULES_PATH) as f:
    SPEC_RULES = json.load(f)

with open(CODE_RULES_PATH) as f:
    CODE_RULES = json.load(f)


# ============================================================================
# PRIMITIVES
# ============================================================================

@st.composite
def entity_name(draw: Any) -> str:
    """Generate a valid entity name like 'developer' or 'auth-module'."""
    # Simple alphanumeric names with hyphens
    name_parts = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=10
        ),
        min_size=1,
        max_size=3
    ))
    name = "-".join(name_parts)
    return name


@st.composite
def entity_value(draw: Any) -> Dict[str, str]:
    """Generate entity value with name and description."""
    return {
        "name": draw(st.text(min_size=5, max_size=50)),
        "description": draw(st.text(min_size=10, max_size=200))
    }


@st.composite
def reference_key(draw: Any, ref_type: str) -> str:
    """Generate a reference key like 'data-model:user-schema'."""
    name_parts = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=10
        ),
        min_size=1,
        max_size=3
    ))
    name = "-".join(name_parts)
    return f"{ref_type}:{name}"


# ============================================================================
# SPEC GRAPH STRATEGIES
# ============================================================================

@st.composite
def spec_entity_dict(draw: Any, entity_type: str, count: int = 3) -> Dict[str, Dict[str, str]]:
    """Generate a dictionary of entities of a specific type.

    Note: Keys are just the entity name (e.g., 'developer'), not prefixed (e.g., 'user:developer').
    The prefix is added when referencing in the graph section.
    """
    entities = {}
    for _ in range(count):
        name = draw(entity_name())
        entities[name] = draw(entity_value())
    return entities


@st.composite
def spec_graph_dependencies(
    draw: Any,
    entities: Dict[str, Dict[str, Dict[str, str]]],
    allow_invalid: bool = False
) -> Dict[str, List[str]]:
    """Generate graph dependencies following (or violating) spec rules.

    Args:
        entities: All entities in the graph by type (keys are unprefixed names)
        allow_invalid: If True, may generate rule-violating dependencies

    Returns:
        Graph dict where keys are prefixed (e.g., 'user:developer') and values
        are dependency lists with prefixed keys.
    """
    graph = {}

    # Generate dependencies
    for entity_type, entity_dict in entities.items():
        allowed_deps = SPEC_RULES["allowed_dependencies"].get(entity_type, [])

        for entity_name in entity_dict.keys():
            entity_full_key = f"{entity_type}:{entity_name}"

            if draw(st.booleans()):  # Not all entities need dependencies
                if allow_invalid and draw(st.booleans()):
                    # Generate invalid dependencies (any type)
                    all_targets = []
                    for etype, edict in entities.items():
                        all_targets.extend([f"{etype}:{name}" for name in edict.keys()])

                    if all_targets:
                        deps = draw(st.lists(
                            st.sampled_from(all_targets),
                            min_size=1,
                            max_size=3,
                            unique=True
                        ))
                    else:
                        deps = []
                else:
                    # Generate valid dependencies
                    valid_targets = []
                    for dep_type in allowed_deps:
                        if dep_type in entities:
                            valid_targets.extend([
                                f"{dep_type}:{name}"
                                for name in entities[dep_type].keys()
                            ])

                    if valid_targets:
                        deps = draw(st.lists(
                            st.sampled_from(valid_targets),
                            min_size=1,
                            max_size=min(3, len(valid_targets)),
                            unique=True
                        ))
                    else:
                        deps = []

                if deps:
                    graph[entity_full_key] = {"depends_on": deps}

    return graph


@st.composite
def minimal_spec_graph(draw: Any) -> Dict[str, Any]:
    """Generate a minimal valid spec graph with the Golden Thread.

    The Golden Thread: user → objective → action → component
    This is the minimum viable chain from user intent to implementation.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Create ONE complete chain
    # Entity keys are unprefixed
    user_name = "test-user"
    objective_name = "test-objective"
    action_name = "test-action"
    component_name = "test-component"

    # But graph keys are prefixed
    user_key = f"user:{user_name}"
    objective_key = f"objective:{objective_name}"
    action_key = f"action:{action_name}"
    component_key = f"component:{component_name}"

    entities = {
        "user": {
            user_name: {
                "name": "Test User",
                "description": "A test user for property testing"
            }
        },
        "objective": {
            objective_name: {
                "name": "Test Objective",
                "description": "A test objective for property testing"
            }
        },
        "action": {
            action_name: {
                "name": "Test Action",
                "description": "A test action for property testing"
            }
        },
        "component": {
            component_name: {
                "name": "Test Component",
                "description": "A test component for property testing"
            }
        }
    }

    graph = {
        user_key: {"depends_on": [objective_key]},
        objective_key: {"depends_on": [action_key]},
        action_key: {"depends_on": [component_key]}
    }

    return {
        "meta": {
            "version": "1.0.0",
            "format": "json-graph",
            "description": "Property-generated spec graph",
            "generated_at": timestamp,
            "project": {
                "name": "Test Project",
                "horizons": []
            }
        },
        "entities": entities,
        "graph": graph,
        "references": {}
    }


@st.composite
def valid_spec_graph(draw: Any, min_entities: int = 5, max_entities: int = 15) -> Dict[str, Any]:
    """Generate a valid spec graph with at least one Golden Thread.

    Guarantees:
    - Has user → objective → action → component chain
    - All dependencies follow spec rules
    - Properly structured with meta, entities, graph, references
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Start with minimal graph (has Golden Thread)
    base = draw(minimal_spec_graph())

    # Track entities that are part of the Golden Thread (don't modify these!)
    golden_thread_entities = {
        "user:test-user",
        "objective:test-objective",
        "action:test-action",
        "component:test-component"
    }

    # Add more entities
    entity_types = list(SPEC_RULES["allowed_dependencies"].keys())
    total_to_add = draw(st.integers(min_value=min_entities, max_value=max_entities))

    new_entities_by_type = {}

    for _ in range(total_to_add):
        etype = draw(st.sampled_from(entity_types))
        name = draw(entity_name())
        value = draw(entity_value())

        if etype not in base["entities"]:
            base["entities"][etype] = {}
        base["entities"][etype][name] = value

        # Track new entities for dependency generation
        if etype not in new_entities_by_type:
            new_entities_by_type[etype] = {}
        new_entities_by_type[etype][name] = value

    # Generate valid dependencies ONLY for new entities (preserve Golden Thread)
    if new_entities_by_type:
        new_graph = draw(spec_graph_dependencies(new_entities_by_type, allow_invalid=False))

        # Only add dependencies that don't overwrite the Golden Thread
        for entity_key, deps in new_graph.items():
            if entity_key not in golden_thread_entities:
                base["graph"][entity_key] = deps

    return base


@st.composite
def broken_golden_thread_graph(draw: Any) -> Dict[str, Any]:
    """Generate a spec graph with BROKEN Golden Thread.

    Mutations:
    - User with no objective
    - Objective with no action
    - Action with no component
    - Component exists but not reachable from user
    """
    base = draw(valid_spec_graph())

    mutation = draw(st.sampled_from([
        "orphan_user",
        "orphan_objective",
        "orphan_action",
        "orphan_component",
        "missing_link"
    ]))

    if mutation == "orphan_user":
        # Add user with no objective dependency
        orphan_name = draw(entity_name())
        base["entities"]["user"][orphan_name] = draw(entity_value())
        # Intentionally don't add to graph

    elif mutation == "orphan_objective":
        # Add objective that no user points to
        orphan_name = draw(entity_name())
        if "objective" not in base["entities"]:
            base["entities"]["objective"] = {}
        base["entities"]["objective"][orphan_name] = draw(entity_value())

    elif mutation == "orphan_action":
        # Add action that no objective points to
        orphan_name = draw(entity_name())
        if "action" not in base["entities"]:
            base["entities"]["action"] = {}
        base["entities"]["action"][orphan_name] = draw(entity_value())

    elif mutation == "orphan_component":
        # Add component that no action points to
        orphan_name = draw(entity_name())
        if "component" not in base["entities"]:
            base["entities"]["component"] = {}
        base["entities"]["component"][orphan_name] = draw(entity_value())

    elif mutation == "missing_link":
        # Break an existing chain
        if base["graph"]:
            link_to_break = draw(st.sampled_from(list(base["graph"].keys())))
            del base["graph"][link_to_break]

    return base


# ============================================================================
# CODE GRAPH STRATEGIES
# ============================================================================

@st.composite
def code_entity_dict(draw: Any, entity_type: str, count: int = 3) -> Dict[str, Dict[str, str]]:
    """Generate a dictionary of code entities of a specific type.

    Note: Keys are just the entity name (e.g., 'test-module'), not prefixed.
    The prefix is added when referencing in the graph section.
    """
    entities = {}
    for _ in range(count):
        name = draw(entity_name())
        value = draw(entity_value())

        # Add optional metadata for modules/packages
        if entity_type == "module":
            value["path"] = f"src/{draw(st.text(min_size=5, max_size=20))}.py"
        elif entity_type == "package":
            value["layer"] = draw(st.sampled_from(["domain", "application", "infrastructure"]))

        entities[name] = value
    return entities


@st.composite
def minimal_code_graph(draw: Any) -> Dict[str, Any]:
    """Generate minimal valid code graph with one module."""
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Entity keys are unprefixed
    module_name = "test-module"
    # Graph keys are prefixed
    module_key = f"module:{module_name}"

    return {
        "meta": {
            "version": "1.0.0",
            "format": "json-graph",
            "description": "Property-generated code graph",
            "generated_at": timestamp,
            "project": {
                "name": "Test Code Project",
                "language": "python"
            }
        },
        "entities": {
            "module": {
                module_name: {
                    "name": "Test Module",
                    "description": "A test module",
                    "path": "src/test_module.py"
                }
            }
        },
        "graph": {},
        "references": {}
    }


@st.composite
def valid_code_graph(draw: Any, min_entities: int = 3, max_entities: int = 10) -> Dict[str, Any]:
    """Generate a valid code graph following code dependency rules."""
    timestamp = datetime.utcnow().isoformat() + "Z"

    base = draw(minimal_code_graph())

    # Add more modules, packages, etc
    entity_types = list(CODE_RULES["allowed_dependencies"].keys())
    total_to_add = draw(st.integers(min_value=min_entities, max_value=max_entities))

    for _ in range(total_to_add):
        etype = draw(st.sampled_from(entity_types))
        new_entity_name = draw(entity_name())
        value = draw(entity_value())

        if etype == "module":
            value["path"] = f"src/{draw(st.text(min_size=5, max_size=20))}.py"
        elif etype == "package":
            value["layer"] = draw(st.sampled_from(["domain", "application", "infrastructure"]))

        if etype not in base["entities"]:
            base["entities"][etype] = {}
        base["entities"][etype][new_entity_name] = value

    # Generate valid dependencies - build as a DAG by only allowing deps on entities seen so far
    graph = {}
    processed_entities = set()  # Track which entities we've already processed

    # Iterate over entity types and their entities in a stable order to prevent cycles
    for entity_type in sorted(base["entities"].keys()):
        entity_dict = base["entities"][entity_type]
        allowed_deps = CODE_RULES["allowed_dependencies"].get(entity_type, [])

        for entity_dict_name in sorted(entity_dict.keys()):
            # Create full prefixed key for graph section
            entity_full_key = f"{entity_type}:{entity_dict_name}"

            if draw(st.booleans()):
                valid_targets = []
                # Only allow deps on entities we've already processed (no forward refs)
                for dep_type in allowed_deps:
                    if dep_type in base["entities"]:
                        # Create prefixed keys for dependencies to previously seen entities
                        valid_targets.extend([
                            f"{dep_type}:{name}"
                            for name in base["entities"][dep_type].keys()
                            if f"{dep_type}:{name}" in processed_entities
                        ])

                if valid_targets:
                    deps = draw(st.lists(
                        st.sampled_from(valid_targets),
                        min_size=1,
                        max_size=min(3, len(valid_targets)),
                        unique=True
                    ))
                    if deps:
                        graph[entity_full_key] = {"depends_on": deps}

            processed_entities.add(entity_full_key)

    base["graph"] = graph
    return base


# ============================================================================
# CROSS-GRAPH STRATEGIES (The Golden Thread Test)
# ============================================================================

@st.composite
def linked_graphs(draw: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Generate spec and code graphs that are LINKED via product-component.

    Returns: (spec_graph, code_graph) where at least one module in code_graph
             references a component in spec_graph.

    IMPORTANT: Links to 'test-component' (part of the Golden Thread) to ensure
    a valid thread exists.
    """
    spec = draw(valid_spec_graph())
    code = draw(valid_code_graph())

    # Link to the Golden Thread component specifically
    if "component" in spec["entities"] and "test-component" in spec["entities"]["component"]:
        component_name = "test-component"
        component_key = f"component:{component_name}"

        # Get a module from code graph (prefer test-module if it exists)
        if "module" in code["entities"] and code["entities"]["module"]:
            if "test-module" in code["entities"]["module"]:
                module_name = "test-module"
            else:
                module_name = draw(st.sampled_from(list(code["entities"]["module"].keys())))

            # Create product-component reference
            # Reference key is the module name (unprefixed)
            if "product-component" not in code["references"]:
                code["references"]["product-component"] = {}

            code["references"]["product-component"][module_name] = {
                "component": component_key,
                "graph_path": "spec-graph.json"
            }

    return (spec, code)


@st.composite
def unlinked_graphs(draw: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Generate spec and code graphs with NO connection between them.

    This violates the Golden Thread requirement.
    """
    spec = draw(valid_spec_graph())
    code = draw(valid_code_graph())

    # Ensure NO product-component references
    if "product-component" in code.get("references", {}):
        del code["references"]["product-component"]

    return (spec, code)


@st.composite
def broken_link_graphs(draw: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Generate graphs where product-component refs point to non-existent components."""
    spec = draw(valid_spec_graph())
    code = draw(valid_code_graph())

    # Add product-component ref to NON-EXISTENT component
    if "module" in code["entities"] and code["entities"]["module"]:
        module_name = draw(st.sampled_from(list(code["entities"]["module"].keys())))

        fake_component = "component:non-existent-component"

        if "product-component" not in code["references"]:
            code["references"]["product-component"] = {}

        # Reference key is unprefixed module name
        code["references"]["product-component"][module_name] = {
            "component": fake_component,
            "graph_path": "spec-graph.json"
        }

    return (spec, code)
