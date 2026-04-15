#!/usr/bin/env python3
"""
Fuzzing harness generator for the know CLI tool.
Generates malformed, edge-case, and rule-violating graphs to stress-test validation.
"""

import json
import random
import string
from typing import Dict, List, Any, Optional
from pathlib import Path
import datetime


class SpecGraphFuzzer:
    """Generates malformed and rule-violating spec graphs."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize fuzzer with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
        self.seed = seed

    # =========== STRUCTURAL MUTATIONS ===========

    def generate_empty_graph(self) -> Dict[str, Any]:
        """Generate completely empty graph."""
        return {}

    def generate_missing_meta(self) -> Dict[str, Any]:
        """Generate graph missing the 'meta' section."""
        return {
            "entities": {"users": {"owner": {"name": "Owner", "description": "Test"}}},
            "references": {},
            "graph": {"users:owner": {"depends_on": []}}
        }

    def generate_missing_entities(self) -> Dict[str, Any]:
        """Generate graph missing the 'entities' section."""
        return {
            "meta": {"project": {"name": "Test"}},
            "references": {},
            "graph": {"users:owner": {"depends_on": []}}
        }

    def generate_missing_references(self) -> Dict[str, Any]:
        """Generate graph missing the 'references' section."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {"users": {"owner": {"name": "Owner", "description": "Test"}}},
            "graph": {"users:owner": {"depends_on": []}}
        }

    def generate_missing_graph(self) -> Dict[str, Any]:
        """Generate graph missing the 'graph' section."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {"users": {"owner": {"name": "Owner", "description": "Test"}}},
            "references": {}
        }

    def generate_invalid_json_simulation(self) -> Dict[str, Any]:
        """Generate structure that will cause JSON issues when serialized."""
        # Instead of returning invalid JSON string, return a structure with issues
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {"users": {"owner": {"name": "Owner", "description": "Test"}}},
            "references": {},
            "graph": {"users:owner": {"depends_on": []}}
        }

    def generate_non_dict_entities(self) -> Dict[str, Any]:
        """Generate graph where entities is not a dict."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": ["users", "objectives"],  # Should be dict
            "references": {},
            "graph": {}
        }

    def generate_non_dict_references(self) -> Dict[str, Any]:
        """Generate graph where references is not a dict."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {"users": {"owner": {"name": "Owner", "description": "Test"}}},
            "references": ["ref1", "ref2"],  # Should be dict
            "graph": {"users:owner": {"depends_on": []}}
        }

    def generate_non_dict_graph(self) -> Dict[str, Any]:
        """Generate graph where graph section is not a dict."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {"users": {"owner": {"name": "Owner", "description": "Test"}}},
            "references": {},
            "graph": ["users:owner", "features:tracking"]  # Should be dict
        }

    def generate_massive_graph(self, entity_count: int = 100) -> Dict[str, Any]:
        """Generate massive graph with 100+ entities (reduced to avoid recursion)."""
        entities = {}
        graph = {}

        for i in range(entity_count):
            entity_id = f"test_entity_{i}"
            entities[entity_id] = {
                "name": f"Entity {i}",
                "description": f"Auto-generated test entity {i}"
            }
            graph[f"users:{entity_id}"] = {"depends_on": []}

        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {"users": entities},
            "references": {},
            "graph": graph
        }

    def generate_unicode_emoji_names(self) -> Dict[str, Any]:
        """Generate entities with Unicode and emoji in names."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "users": {
                    "owner_🚀_test": {"name": "🚀 Owner", "description": "Unicode test"},
                    "admin_你好": {"name": "Admin 你好", "description": "Chinese characters"},
                    "user_ñ": {"name": "User ñ", "description": "Accented characters"}
                }
            },
            "references": {},
            "graph": {
                "users:owner_🚀_test": {"depends_on": []},
                "users:admin_你好": {"depends_on": []},
                "users:user_ñ": {"depends_on": []}
            }
        }

    def generate_special_characters_names(self) -> Dict[str, Any]:
        """Generate entities with dangerous special characters."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "users": {
                    'user_with_quotes': {"name": 'User with "quotes"', "description": "Test"},
                    'user_with_newline': {"name": 'User with newline', "description": "Test"},
                    'user_with_tab': {"name": 'User with tab', "description": "Test"},
                    'user_with_backslash': {"name": 'User with backslash', "description": "Test"}
                }
            },
            "references": {},
            "graph": {
                'users:user_with_quotes': {"depends_on": []},
                'users:user_with_newline': {"depends_on": []},
                'users:user_with_tab': {"depends_on": []},
                'users:user_with_backslash': {"depends_on": []}
            }
        }

    # =========== RULE VIOLATIONS - SPEC GRAPH ===========

    def generate_invalid_dependency_direction(self) -> Dict[str, Any]:
        """Generate invalid dependency: component→user instead of user→objective."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "System owner"}},
                "components": {"auth": {"name": "Auth", "description": "Authentication"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": []},
                "components:auth": {"depends_on": ["users:owner"]}  # Invalid: component→user
            }
        }

    def generate_circular_dependencies(self) -> Dict[str, Any]:
        """Generate graph with circular dependencies."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "features": {
                    "feature_a": {"name": "Feature A", "description": "Test"},
                    "feature_b": {"name": "Feature B", "description": "Test"},
                    "feature_c": {"name": "Feature C", "description": "Test"}
                }
            },
            "references": {},
            "graph": {
                "features:feature_a": {"depends_on": ["features:feature_b"]},
                "features:feature_b": {"depends_on": ["features:feature_c"]},
                "features:feature_c": {"depends_on": ["features:feature_a"]}  # Circular!
            }
        }

    def generate_self_referencing(self) -> Dict[str, Any]:
        """Generate entity that depends on itself."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "features": {
                    "recursive": {"name": "Recursive", "description": "Self-referencing"}
                }
            },
            "references": {},
            "graph": {
                "features:recursive": {"depends_on": ["features:recursive"]}
            }
        }

    def generate_orphaned_entities(self) -> Dict[str, Any]:
        """Generate entities with no graph entries."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "owner": {"name": "Owner", "description": "In graph"},
                    "admin": {"name": "Admin", "description": "Not in graph"}
                }
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": []}
                # users:admin is missing from graph
            }
        }

    def generate_reference_to_nonexistent_entity(self) -> Dict[str, Any]:
        """Generate dependency pointing to non-existent entity."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": ["objectives:nonexistent"]}  # Doesn't exist
            }
        }

    def generate_wrong_entity_types_in_chain(self) -> Dict[str, Any]:
        """Generate invalid dependency chain like component→action→feature."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "components": {"auth": {"name": "Auth", "description": "Test"}},
                "actions": {"login": {"name": "Login", "description": "Test"}},
                "features": {"security": {"name": "Security", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "components:auth": {"depends_on": ["actions:login"]},  # Invalid direction
                "actions:login": {"depends_on": ["features:security"]}
            }
        }

    # =========== EDGE CASES ===========

    def generate_empty_depends_on_array(self) -> Dict[str, Any]:
        """Generate explicit empty depends_on arrays."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}},
                "objectives": {"goal": {"name": "Goal", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": []},
                "objectives:goal": {"depends_on": []}
            }
        }

    def generate_null_depends_on(self) -> Dict[str, Any]:
        """Generate null depends_on value."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": None}  # Should be array
            }
        }

    def generate_missing_depends_on(self) -> Dict[str, Any]:
        """Generate graph nodes without depends_on field."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {}  # Missing depends_on entirely
            }
        }

    def generate_extremely_long_description(self) -> Dict[str, Any]:
        """Generate entity with 10k+ character description."""
        long_desc = "x" * 10000
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "owner": {"name": "Owner", "description": long_desc}
                }
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": []}
            }
        }

    def generate_duplicate_entity_keys(self) -> Dict[str, Any]:
        """Note: JSON doesn't support duplicate keys, but test malformed structure."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "owner": {"name": "Owner", "description": "First"},
                    "owner": {"name": "Owner", "description": "Second"}  # Duplicate key
                }
            },
            "references": {},
            "graph": {}
        }

    def generate_missing_entity_name(self) -> Dict[str, Any]:
        """Generate entity missing 'name' field."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "owner": {"description": "Missing name"}  # No 'name'
                }
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": []}
            }
        }

    def generate_missing_entity_description(self) -> Dict[str, Any]:
        """Generate entity missing 'description' field."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "owner": {"name": "Owner"}  # No 'description'
                }
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": []}
            }
        }

    def generate_null_values_in_entity(self) -> Dict[str, Any]:
        """Generate entity with null values."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "owner": {"name": None, "description": None}
                }
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": []}
            }
        }

    def generate_invalid_graph_node_id_format(self) -> Dict[str, Any]:
        """Generate graph node IDs without proper type:name format."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "just_owner": {"depends_on": []},  # Missing 'users:' prefix
                "users_owner": {"depends_on": []},  # Wrong separator
                "users:owner": {"depends_on": []}
            }
        }

    # =========== CROSS-GRAPH VALIDATION ===========

    def generate_valid_spec_incomplete_chain(self) -> Dict[str, Any]:
        """Generate spec-graph with chain that doesn't reach component."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}},
                "objectives": {"goal": {"name": "Goal", "description": "Test"}},
                # Missing: features, actions, components
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": ["objectives:goal"]},
                "objectives:goal": {"depends_on": []}
            }
        }

    def generate_missing_component_in_spec(self) -> Dict[str, Any]:
        """Generate spec-graph where user→objective chain has no component."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}},
                "objectives": {"goal": {"name": "Goal", "description": "Test"}},
                "actions": {"perform": {"name": "Perform", "description": "Test"}},
                "features": {"feature_a": {"name": "Feature A", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": ["objectives:goal"]},
                "objectives:goal": {"depends_on": ["actions:perform"]},
                "actions:perform": {"depends_on": ["features:feature_a"]},
                "features:feature_a": {"depends_on": []}  # Stops at feature, no component
            }
        }

    def generate_malformed_meta(self) -> Dict[str, Any]:
        """Generate graph with malformed meta section."""
        return {
            "meta": "not a dict",  # Should be dict
            "entities": {"users": {"owner": {"name": "Owner", "description": "Test"}}},
            "references": {},
            "graph": {"users:owner": {"depends_on": []}}
        }

    def generate_malformed_project_in_meta(self) -> Dict[str, Any]:
        """Generate meta.project that's not a dict."""
        return {
            "meta": {"project": "should be dict", "horizons": []},
            "entities": {"users": {"owner": {"name": "Owner", "description": "Test"}}},
            "references": {},
            "graph": {"users:owner": {"depends_on": []}}
        }

    # =========== NAMING CONVENTION VIOLATIONS ===========

    def generate_underscores_in_names(self) -> Dict[str, Any]:
        """Generate entity names using underscores instead of hyphens."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "test_owner": {"name": "Test Owner", "description": "Uses underscore"},  # Should be test-owner
                    "admin_user": {"name": "Admin User", "description": "Uses underscore"}
                }
            },
            "references": {},
            "graph": {
                "users:test_owner": {"depends_on": []},
                "users:admin_user": {"depends_on": []}
            }
        }

    def generate_camelcase_names(self) -> Dict[str, Any]:
        """Generate entity names using camelCase instead of kebab-case."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "testOwner": {"name": "Test Owner", "description": "Uses camelCase"},
                    "adminUser": {"name": "Admin User", "description": "Uses camelCase"}
                }
            },
            "references": {},
            "graph": {
                "users:testOwner": {"depends_on": []},
                "users:adminUser": {"depends_on": []}
            }
        }

    def generate_uppercase_names(self) -> Dict[str, Any]:
        """Generate entity names with UPPERCASE."""
        return {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {
                    "OWNER": {"name": "Owner", "description": "All uppercase"},
                    "ADMIN": {"name": "Admin", "description": "All uppercase"}
                }
            },
            "references": {},
            "graph": {
                "users:OWNER": {"depends_on": []},
                "users:ADMIN": {"depends_on": []}
            }
        }

    # =========== GENERATION ORCHESTRATION ===========

    def get_all_mutation_types(self) -> List[str]:
        """Return list of all available mutation types (excluding generate_all_mutations)."""
        mutations = []
        for method_name in dir(self):
            if method_name.startswith('generate_') and method_name not in ['generate_all_mutations', 'generate_corpus']:
                mutations.append(method_name)
        return sorted(mutations)

    def generate_all_mutations(self) -> Dict[str, Dict[str, Any]]:
        """Generate all available mutations as a single dict."""
        mutations = {}
        for method_name in self.get_all_mutation_types():
            if method_name == 'generate_all_mutations':
                continue  # Skip self-reference
            try:
                method = getattr(self, method_name)
                mutations[method_name] = method()
            except Exception as e:
                mutations[method_name] = {"error": str(e)}
        return mutations


class CodeGraphFuzzer:
    """Generates malformed and rule-violating code graphs."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize fuzzer with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
        self.seed = seed

    def get_all_mutation_types(self) -> List[str]:
        """Return list of all available mutation types (excluding generate_all_mutations)."""
        mutations = []
        for method_name in dir(self):
            if method_name.startswith('generate_') and method_name != 'generate_all_mutations':
                mutations.append(method_name)
        return sorted(mutations)

    def generate_empty_graph(self) -> Dict[str, Any]:
        """Generate completely empty code graph."""
        return {}

    def generate_missing_sections(self) -> Dict[str, Any]:
        """Generate code graph missing required sections."""
        return {
            "meta": {"project": {"name": "Test"}},
            # Missing: entities, references, graph
        }

    def generate_upward_layer_dependency(self) -> Dict[str, Any]:
        """Generate layer depending on higher layer (violates architecture)."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "layers": {
                    "presentation": {"name": "Presentation", "description": "UI layer"},
                    "business": {"name": "Business", "description": "Business logic"}
                }
            },
            "references": {},
            "graph": {
                "layers:presentation": {"depends_on": ["layers:business"]},
                "layers:business": {"depends_on": ["layers:presentation"]}  # Upward dependency!
            }
        }

    def generate_invalid_layer_cycles(self) -> Dict[str, Any]:
        """Generate circular layer dependencies."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "layers": {
                    "layer_a": {"name": "Layer A", "description": "Test"},
                    "layer_b": {"name": "Layer B", "description": "Test"},
                    "layer_c": {"name": "Layer C", "description": "Test"}
                }
            },
            "references": {},
            "graph": {
                "layers:layer_a": {"depends_on": ["layers:layer_b"]},
                "layers:layer_b": {"depends_on": ["layers:layer_c"]},
                "layers:layer_c": {"depends_on": ["layers:layer_a"]}
            }
        }

    def generate_module_with_invalid_dependency_type(self) -> Dict[str, Any]:
        """Generate module depending on invalid entity type."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "modules": {"auth": {"name": "Auth", "description": "Auth module"}},
                "classes": {"User": {"name": "User", "description": "User class"}},
                "users": {"owner": {"name": "Owner", "description": "Invalid type"}}  # users shouldn't exist in code-graph
            },
            "references": {},
            "graph": {
                "modules:auth": {"depends_on": ["users:owner"]}  # Invalid: module can't depend on users
            }
        }

    def generate_broken_namespace_hierarchy(self) -> Dict[str, Any]:
        """Generate namespace without proper parent structure."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "namespaces": {
                    "deep_child": {"name": "Deep Child", "description": "No parent"}
                }
            },
            "references": {},
            "graph": {
                "namespaces:deep_child": {"depends_on": []}
            }
        }

    def generate_orphaned_product_component_reference(self) -> Dict[str, Any]:
        """Generate product-component reference to non-existent component."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "modules": {"handler": {"name": "Handler", "description": "Test"}}
            },
            "references": {
                "product-component": {
                    "handler": {
                        "component": "component:nonexistent-component",
                        "graph_path": "spec-graph.json"
                    }
                }
            },
            "graph": {
                "modules:handler": {"depends_on": ["product-component:handler"]}
            }
        }

    def generate_product_component_with_wrong_graph_path(self) -> Dict[str, Any]:
        """Generate product-component with invalid graph path."""
        return {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "modules": {"handler": {"name": "Handler", "description": "Test"}}
            },
            "references": {
                "product-component": {
                    "handler": {
                        "component": "component:some-component",
                        "graph_path": "/absolute/path/invalid.json"  # Should be relative
                    }
                }
            },
            "graph": {
                "modules:handler": {"depends_on": ["product-component:handler"]}
            }
        }

    def get_all_mutation_types(self) -> List[str]:
        """Return list of all available mutation types."""
        mutations = []
        for method_name in dir(self):
            if method_name.startswith('generate_'):
                mutations.append(method_name)
        return sorted(mutations)

    def generate_all_mutations(self) -> Dict[str, Dict[str, Any]]:
        """Generate all available mutations."""
        mutations = {}
        for method_name in self.get_all_mutation_types():
            if method_name == 'generate_all_mutations':
                continue  # Skip self-reference
            try:
                method = getattr(self, method_name)
                mutations[method_name] = method()
            except Exception as e:
                mutations[method_name] = {"error": str(e)}
        return mutations


class CrossGraphFuzzer:
    """Generates cross-graph validation issues."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize fuzzer with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
        self.seed = seed

    def generate_spec_without_code(self) -> tuple:
        """Generate valid spec-graph with no corresponding code-graph."""
        spec = {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}},
                "objectives": {"goal": {"name": "Goal", "description": "Test"}},
                "actions": {"perform": {"name": "Perform", "description": "Test"}},
                "components": {"service": {"name": "Service", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": ["objectives:goal"]},
                "objectives:goal": {"depends_on": ["actions:perform"]},
                "actions:perform": {"depends_on": ["components:service"]},
                "components:service": {"depends_on": []}
            }
        }

        code = {}  # Empty code graph

        return spec, code

    def generate_code_without_spec(self) -> tuple:
        """Generate valid code-graph with no corresponding spec-graph."""
        spec = {}  # Empty spec graph

        code = {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "modules": {"auth": {"name": "Auth", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "modules:auth": {"depends_on": []}
            }
        }

        return spec, code

    def generate_broken_golden_thread(self) -> tuple:
        """Generate spec with component but no code-graph connection."""
        spec = {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}},
                "objectives": {"goal": {"name": "Goal", "description": "Test"}},
                "actions": {"perform": {"name": "Perform", "description": "Test"}},
                "components": {"service": {"name": "Service", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": ["objectives:goal"]},
                "objectives:goal": {"depends_on": ["actions:perform"]},
                "actions:perform": {"depends_on": ["components:service"]},
                "components:service": {"depends_on": []}
            }
        }

        code = {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "modules": {"auth": {"name": "Auth", "description": "Implements something"}}
            },
            "references": {
                "product-component": {
                    "auth": {
                        "component": "component:other-service",  # Wrong component
                        "graph_path": "spec-graph.json"
                    }
                }
            },
            "graph": {
                "modules:auth": {"depends_on": ["product-component:auth"]}
            }
        }

        return spec, code

    def generate_missing_product_component_mapping(self) -> tuple:
        """Generate code module implementing spec component but no product-component ref."""
        spec = {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}},
                "objectives": {"goal": {"name": "Goal", "description": "Test"}},
                "actions": {"perform": {"name": "Perform", "description": "Test"}},
                "components": {"auth": {"name": "Auth", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": ["objectives:goal"]},
                "objectives:goal": {"depends_on": ["actions:perform"]},
                "actions:perform": {"depends_on": ["components:auth"]},
                "components:auth": {"depends_on": []}
            }
        }

        code = {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "modules": {"auth": {"name": "Auth", "description": "Implements auth"}}
            },
            "references": {},  # No product-component reference
            "graph": {
                "modules:auth": {"depends_on": []}
            }
        }

        return spec, code

    def generate_orphaned_code_module(self) -> tuple:
        """Generate code module with no connection to spec-graph."""
        spec = {
            "meta": {"project": {"name": "Test"}, "horizons": []},
            "entities": {
                "users": {"owner": {"name": "Owner", "description": "Test"}},
                "objectives": {"goal": {"name": "Goal", "description": "Test"}},
                "actions": {"perform": {"name": "Perform", "description": "Test"}},
                "components": {"service": {"name": "Service", "description": "Test"}}
            },
            "references": {},
            "graph": {
                "users:owner": {"depends_on": ["objectives:goal"]},
                "objectives:goal": {"depends_on": ["actions:perform"]},
                "actions:perform": {"depends_on": ["components:service"]},
                "components:service": {"depends_on": []}
            }
        }

        code = {
            "meta": {"project": {"name": "Test"}},
            "entities": {
                "modules": {
                    "service": {"name": "Service", "description": "Test"},
                    "orphan": {"name": "Orphan", "description": "No purpose"}
                }
            },
            "references": {
                "product-component": {
                    "service": {
                        "component": "component:service",
                        "graph_path": "spec-graph.json"
                    }
                    # orphan has no mapping
                }
            },
            "graph": {
                "modules:service": {"depends_on": ["product-component:service"]},
                "modules:orphan": {"depends_on": []}
            }
        }

        return spec, code

    def get_all_mutation_types(self) -> List[str]:
        """Return list of all available mutation types."""
        mutations = []
        for method_name in dir(self):
            if method_name.startswith('generate_') and method_name != 'generate_all_mutations':
                mutations.append(method_name)
        return sorted(mutations)

    def generate_all_mutations(self) -> Dict[str, tuple]:
        """Generate all available mutations."""
        mutations = {}
        for method_name in self.get_all_mutation_types():
            if method_name == 'generate_all_mutations':
                continue  # Skip self-reference
            try:
                method = getattr(self, method_name)
                mutations[method_name] = method()
            except Exception as e:
                mutations[method_name] = ({"error": str(e)}, {"error": str(e)})
        return mutations


def save_graph(graph: Dict[str, Any], path: Path) -> None:
    """Save graph to JSON file with proper formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(graph, f, indent=2)


def generate_corpus(output_dir: Path, count: int = 100, seed: Optional[int] = None) -> None:
    """
    Generate a corpus of test graphs.

    Args:
        output_dir: Base directory for corpus
        count: Number of test graphs to generate per category
        seed: Random seed for reproducibility
    """
    output_dir = Path(output_dir)

    # Initialize fuzzers
    spec_fuzzer = SpecGraphFuzzer(seed=seed)
    code_fuzzer = CodeGraphFuzzer(seed=seed)
    cross_fuzzer = CrossGraphFuzzer(seed=seed)

    # Generate spec graphs
    spec_corpus = output_dir / "corpus" / "spec"
    spec_mutations = spec_fuzzer.generate_all_mutations()
    for i, (mutation_name, graph) in enumerate(spec_mutations.items()):
        save_graph(graph, spec_corpus / f"{mutation_name}.json")

    # Generate code graphs
    code_corpus = output_dir / "corpus" / "code"
    code_mutations = code_fuzzer.generate_all_mutations()
    for i, (mutation_name, graph) in enumerate(code_mutations.items()):
        save_graph(graph, code_corpus / f"{mutation_name}.json")

    # Generate cross-graph validation issues
    cross_corpus = output_dir / "corpus" / "cross"
    cross_mutations = cross_fuzzer.generate_all_mutations()
    for i, (mutation_name, (spec, code)) in enumerate(cross_mutations.items()):
        save_graph(spec, cross_corpus / f"{mutation_name}_spec.json")
        save_graph(code, cross_corpus / f"{mutation_name}_code.json")

    print(f"Generated {len(spec_mutations)} spec mutations")
    print(f"Generated {len(code_mutations)} code mutations")
    print(f"Generated {len(cross_mutations)} cross-graph mutation pairs")
    print(f"Total: {len(spec_mutations) + len(code_mutations) + len(cross_mutations) * 2} test files")


if __name__ == "__main__":
    import sys

    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/fuzz")
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else None

    generate_corpus(output_dir, seed=seed)
