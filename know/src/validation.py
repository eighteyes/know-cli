"""
Graph validation for the specification graph.
Validates structure, schema, references, and completeness.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


class GraphValidator:
    """Validates the structure and content of the specification graph."""

    def __init__(self, graph_manager, rules_path: Optional[str] = None):
        """
        Initialize graph validator.

        Args:
            graph_manager: GraphManager instance
            rules_path: Path to dependency-rules.json (overrides all auto-detection)
        """
        self.graph = graph_manager

        # Load dependency rules with fallback logic
        if rules_path is None:
            rules_path = self._resolve_dependency_rules()

        with open(rules_path, 'r') as f:
            self.rules = json.load(f)

        self.entity_description = self.rules.get('entity_description', {})
        self.reference_description = self.rules.get('reference_description', {})

        # Extract allowed metadata from entity_note
        entity_note = self.rules.get('entity_note', {})
        self.allowed_metadata = set(entity_note.get('allowed_metadata', []))

    def _resolve_dependency_rules(self) -> Path:
        """
        Resolve which dependency rules file to use.

        Priority:
        1. Explicit meta.dependency_rules.file in graph
        2. Format-based default from known formats
        3. Ultimate fallback to dependency-rules.json

        Returns:
            Path to dependency rules file
        """
        data = self.graph.load()
        meta = data.get('meta', {})

        # Check for explicit reference in meta.dependency_rules
        dep_rules_config = meta.get('dependency_rules', {})
        if isinstance(dep_rules_config, dict):
            explicit_file = dep_rules_config.get('file')
            if explicit_file:
                # Resolve relative to graph file location
                graph_path = Path(self.graph.graph_path)
                rules_path = graph_path.parent / explicit_file

                if rules_path.exists():
                    return rules_path
                else:
                    # Warn but continue to fallback
                    print(f"Warning: Specified rules file not found: {rules_path}")

        # Fall back to format-based defaults
        graph_format = meta.get('format', '')

        format_to_rules = {
            'json-graph': 'dependency-rules.json',
            'code-dependency-graph': 'code-dependency-rules.json',
        }

        rules_file = format_to_rules.get(graph_format, 'dependency-rules.json')
        default_path = Path(__file__).parent.parent / "config" / rules_file

        if default_path.exists():
            return default_path

        # Ultimate fallback
        return Path(__file__).parent.parent / "config" / "dependency-rules.json"

    def validate_all(self) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Run all validation checks on the graph (syntax + structure layers only).
        For backward compatibility, this matches original behavior.

        Returns:
            Tuple of (is_valid, dict of validation results by category)
        """
        results = {
            'errors': [],
            'warnings': [],
            'info': []
        }

        # Run all validation checks (syntax + structure layers)
        checks = [
            self._validate_structure,
            self._validate_meta_schema,
            self._validate_graph_key_format,
            self._validate_entity_schema,
            self._validate_reference_usage,
            self._validate_orphaned_nodes,
            self._validate_entity_types,
        ]

        for check in checks:
            check_results = check()
            for level, messages in check_results.items():
                results[level].extend(messages)

        is_valid = len(results['errors']) == 0

        return is_valid, results

    def _merge_results(self, *result_sets) -> Dict[str, List[str]]:
        """
        Merge multiple result dictionaries.

        Args:
            *result_sets: Variable number of result dicts with 'errors', 'warnings', 'info' keys

        Returns:
            Merged result dictionary
        """
        merged = {'errors': [], 'warnings': [], 'info': []}

        for results in result_sets:
            for level in ['errors', 'warnings', 'info']:
                merged[level].extend(results.get(level, []))

        return merged

    def validate_syntax(self) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Run syntax-level validation (fast, ~ms).
        Checks basic structure and format correctness.

        Returns:
            Tuple of (is_valid, dict of validation results by category)
        """
        checks = [
            self._validate_structure,
            self._validate_meta_schema,
            self._validate_graph_key_format,
        ]

        results = self._merge_results(*[check() for check in checks])
        is_valid = len(results['errors']) == 0

        return is_valid, results

    def validate_structure(self) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Run structure-level validation (~50ms).
        Checks schema compliance and node relationships.

        Returns:
            Tuple of (is_valid, dict of validation results by category)
        """
        checks = [
            self._validate_entity_schema,
            self._validate_orphaned_nodes,
            self._validate_entity_types,
            self._validate_reference_usage,
        ]

        results = self._merge_results(*[check() for check in checks])
        is_valid = len(results['errors']) == 0

        return is_valid, results

    def validate_semantics(self, deps_manager) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Run semantic-level validation (~200ms).
        Checks dependency rules, cycles, and naming conventions.

        Args:
            deps_manager: DependencyManager instance for graph validation

        Returns:
            Tuple of (is_valid, dict of validation results by category)
        """
        results = {'errors': [], 'warnings': [], 'info': []}

        # Dependency validation
        dep_valid, dep_errors = deps_manager.validate_graph()
        if not dep_valid:
            results['errors'].extend(dep_errors)

        # Cycle detection
        cycles = deps_manager.detect_cycles()
        if cycles:
            results['errors'].append(f"Found {len(cycles)} circular dependencies")
            for cycle in cycles[:5]:  # Show first 5
                cycle_str = " -> ".join(cycle)
                results['errors'].append(f"  Cycle: {cycle_str}")

        # Naming conventions
        naming_results = self._validate_graph_key_naming()
        for level, messages in naming_results.items():
            results[level].extend(messages)

        # Missing descriptions
        desc_results = self._validate_missing_descriptions()
        for level, messages in desc_results.items():
            results[level].extend(messages)

        is_valid = len(results['errors']) == 0

        return is_valid, results

    def validate_full(self, deps_manager) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Run full validation (all layers combined).

        Args:
            deps_manager: DependencyManager instance for graph validation

        Returns:
            Tuple of (is_valid, dict of validation results by category)
        """
        # Run all layers
        syntax_valid, syntax_results = self.validate_syntax()
        structure_valid, structure_results = self.validate_structure()
        semantics_valid, semantics_results = self.validate_semantics(deps_manager)

        # Merge all results
        results = self._merge_results(syntax_results, structure_results, semantics_results)
        is_valid = syntax_valid and structure_valid and semantics_valid

        return is_valid, results

    def _validate_structure(self) -> Dict[str, List[str]]:
        """Validate top-level graph structure."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()

        # Check for required top-level keys
        required_keys = ['meta', 'entities', 'references', 'graph']
        for key in required_keys:
            if key not in data:
                results['errors'].append(f"Missing required top-level key: {key}")

        # Check meta structure
        if 'meta' in data:
            meta = data['meta']
            if 'project' not in meta:
                results['warnings'].append("Missing 'project' in meta")
            if 'horizons' not in meta:
                results['warnings'].append("Missing 'horizons' in meta")

            # Validate horizons structure
            if 'horizons' in meta:
                horizons = meta['horizons']
                if isinstance(horizons, list):
                    results['errors'].append(
                        "meta.horizons must be a dict, not a list. "
                        "Expected format: {\"pending\": {\"feature:x\": {\"status\": \"incomplete\"}}}"
                    )
                elif not isinstance(horizons, dict):
                    results['errors'].append("meta.horizons must be a dict")
                else:
                    for phase_id, entries in horizons.items():
                        if not isinstance(entries, dict):
                            continue
                        for entity_id, entry in entries.items():
                            if not isinstance(entry, dict):
                                continue
                            if entry.get('status') == 'complete' and not entry.get('version'):
                                results['warnings'].append(
                                    f"{entity_id} is complete in horizon '{phase_id}' but has no version set"
                                )

            # Validate horizons_metadata structure if present
            if 'horizons_metadata' in meta:
                horizons_meta = meta['horizons_metadata']
                if not isinstance(horizons_meta, dict):
                    results['errors'].append("meta.horizons_metadata must be a dict")

        # Check entities structure
        if 'entities' in data:
            if not isinstance(data['entities'], dict):
                results['errors'].append("'entities' must be a dictionary")
            else:
                results['info'].append(f"Found {len(data['entities'])} entity types")

        # Check references structure
        if 'references' in data:
            if not isinstance(data['references'], dict):
                results['errors'].append("'references' must be a dictionary")
            else:
                results['info'].append(f"Found {len(data['references'])} reference types")

        # Check graph structure
        if 'graph' in data:
            if not isinstance(data['graph'], dict):
                results['errors'].append("'graph' must be a dictionary")
            else:
                results['info'].append(f"Found {len(data['graph'])} graph nodes")

                # Validate depends_on_ordered fields
                for node_id, node_data in data['graph'].items():
                    if isinstance(node_data, dict) and "depends_on_ordered" in node_data:
                        ordered_deps = node_data["depends_on_ordered"]
                        if not isinstance(ordered_deps, list):
                            results['errors'].append(
                                f"Node {node_id} has invalid depends_on_ordered type "
                                f"(expected list, got {type(ordered_deps).__name__})"
                            )

        return results

    def _validate_meta_schema(self) -> Dict[str, List[str]]:
        """Validate meta section keys against schema defined in rules."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        meta = data.get('meta', {})
        if not isinstance(meta, dict):
            return results  # Structure check already catches this

        # Build allowed meta keys from rules
        meta_schema = self.rules.get('meta_schema', {})
        meta_description = self.rules.get('meta_description', {})

        # Keys from meta_schema.top_level (string-typed top-level fields)
        top_level_keys = set()
        if 'top_level' in meta_schema:
            top_level_keys = set(meta_schema['top_level'].keys())

        # Keys from meta_schema sub-objects (everything except top_level)
        sub_object_keys = set(meta_schema.keys()) - {'top_level'}

        # Keys from meta_description (fallback when meta_schema is absent)
        description_keys = set(meta_description.keys())

        # Operational keys always allowed (used by the system)
        operational_keys = {
            'horizons', 'horizons_metadata', 'code_graph_path',
            'spec_graph_path', 'dependency_rules', 'feature_specs'
        }

        # Standard envelope keys present on all graphs
        envelope_keys = {
            'version', 'format', 'description',
            'generated_at', 'project_root', 'source'
        }

        allowed_keys = top_level_keys | sub_object_keys | description_keys | operational_keys | envelope_keys

        # Error on unknown meta keys
        for key in meta.keys():
            if key not in allowed_keys:
                results['errors'].append(
                    f"meta has unknown key '{key}' — allowed: {', '.join(sorted(allowed_keys))}"
                )

        # Type checks — errors for critical structure
        if 'project' in meta and not isinstance(meta['project'], dict):
            results['errors'].append(
                "meta.project must be a dict"
            )

        # meta.horizons dict check already in _validate_structure, skip here

        # Type checks — warnings for softer constraints
        if 'out_of_scope' in meta and not isinstance(meta['out_of_scope'], list):
            results['warnings'].append(
                "meta.out_of_scope should be an array"
            )

        # Warn if string-typed top-level keys are not strings
        for key in top_level_keys:
            if key in meta and not isinstance(meta[key], str):
                results['warnings'].append(
                    f"meta.{key} should be a string"
                )

        return results

    def _validate_entity_schema(self) -> Dict[str, List[str]]:
        """Validate entity schema compliance."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        entities = data.get('entities', {})

        # Check each entity type
        for entity_type, entity_list in entities.items():
            if not isinstance(entity_list, dict):
                results['errors'].append(f"Entity type '{entity_type}' must be a dictionary")
                continue

            # Check each entity
            for entity_name, entity_data in entity_list.items():
                entity_id = f"{entity_type}:{entity_name}"

                # Validate required fields
                if not isinstance(entity_data, dict):
                    results['errors'].append(f"Entity {entity_id} must be a dictionary")
                    continue

                # Check for required fields: name and description
                if 'name' not in entity_data:
                    results['warnings'].append(f"Entity {entity_id} missing 'name' field")

                if 'description' not in entity_data:
                    results['warnings'].append(f"Entity {entity_id} missing 'description' field")

                # Warn about unexpected fields (entities should only have name & description)
                # But allow metadata fields defined in dependency-rules.json
                expected_fields = {'name', 'description'}
                actual_fields = set(entity_data.keys())
                unexpected = actual_fields - expected_fields - self.allowed_metadata

                if unexpected:
                    # Check if these are actually relationships that should be in graph
                    relationship_keywords = {'refs', 'screen', 'parent', 'uses', 'depends_on', 'references'}
                    problematic = unexpected & relationship_keywords

                    if problematic:
                        results['errors'].append(
                            f"Entity {entity_id} has relationship fields that should be in graph: "
                            f"{', '.join(problematic)}"
                        )
                    else:
                        results['errors'].append(
                            f"Entity {entity_id} has unexpected fields: {', '.join(unexpected)}"
                        )

        return results

    def _validate_reference_usage(self) -> Dict[str, List[str]]:
        """Validate that references are used correctly."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        references = data.get('references', {})
        graph = data.get('graph', {})

        # Track which references are actually used
        used_references = set()

        for node_id, node_data in graph.items():
            # Defensive check: ensure node_data is a dictionary
            if not isinstance(node_data, dict):
                results['errors'].append(
                    f"Graph node {node_id} has invalid data type: {type(node_data).__name__} "
                    f"(expected dict)"
                )
                continue

            from .utils import get_all_deps
            for dep in get_all_deps(node_data):
                if ':' in dep:
                    ref_type = dep.split(':')[0]
                    if ref_type in references:
                        used_references.add(dep)

        # Find unused references
        all_references = set()
        for ref_type, ref_list in references.items():
            if isinstance(ref_list, dict):
                for ref_name in ref_list.keys():
                    all_references.add(f"{ref_type}:{ref_name}")

        unused = all_references - used_references
        if unused:
            results['warnings'].append(f"Found {len(unused)} unused references")
            # Only list first 10 to avoid clutter
            for ref in list(unused)[:10]:
                results['info'].append(f"  Unused reference: {ref}")

        return results

    def _validate_orphaned_nodes(self) -> Dict[str, List[str]]:
        """Find orphaned nodes (nodes not in entities/references but in graph)."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        entities = data.get('entities', {})
        references = data.get('references', {})
        graph = data.get('graph', {})

        # Build set of valid entity IDs
        valid_ids = set()
        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, dict):
                for entity_name in entity_list.keys():
                    valid_ids.add(f"{entity_type}:{entity_name}")

        # Add valid reference IDs
        for ref_type, ref_list in references.items():
            if isinstance(ref_list, dict):
                for ref_name in ref_list.keys():
                    valid_ids.add(f"{ref_type}:{ref_name}")

        # Check for orphaned graph nodes
        orphaned = []
        for node_id in graph.keys():
            if node_id not in valid_ids:
                orphaned.append(node_id)

        if orphaned:
            results['errors'].append(f"Found {len(orphaned)} orphaned graph nodes")
            for node in orphaned[:10]:
                results['errors'].append(f"  Orphaned node: {node}")

        # Check for missing graph nodes (entities/references without graph entries)
        entities_in_graph = set(graph.keys())
        missing_from_graph = valid_ids - entities_in_graph

        if missing_from_graph:
            results['warnings'].append(f"Found {len(missing_from_graph)} entities/references not in graph")
            for node in list(missing_from_graph)[:10]:
                results['info'].append(f"  Not in graph: {node}")

        return results

    def _validate_missing_descriptions(self) -> Dict[str, List[str]]:
        """Check for entities missing descriptions."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        entities = data.get('entities', {})

        missing_count = 0
        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, dict):
                for entity_name, entity_data in entity_list.items():
                    if isinstance(entity_data, dict):
                        if not entity_data.get('description'):
                            missing_count += 1
                            if missing_count <= 10:  # Only show first 10
                                results['warnings'].append(
                                    f"Entity {entity_type}:{entity_name} missing description"
                                )

        if missing_count > 10:
            results['warnings'].append(f"...and {missing_count - 10} more missing descriptions")

        return results

    def _validate_entity_types(self) -> Dict[str, List[str]]:
        """Validate entity types against dependency rules."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        entities = data.get('entities', {})

        # Check if all entity types are documented in rules
        for entity_type in entities.keys():
            if entity_type not in self.entity_description:
                results['warnings'].append(
                    f"Entity type '{entity_type}' not documented in dependency-rules.json"
                )

        # Check if there are documented entity types not used
        for entity_type in self.entity_description.keys():
            if entity_type not in entities:
                results['info'].append(
                    f"Documented entity type '{entity_type}' not used in graph"
                )

        return results

    def _validate_graph_key_format(self) -> Dict[str, List[str]]:
        """Validate graph node key format (syntax check)."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        graph = data.get('graph', {})

        for node_id in graph.keys():
            # Check for proper format (type:name)
            if ':' not in node_id:
                results['errors'].append(f"Invalid graph node ID format: {node_id} (missing ':')")
                continue

            # Check for correct number of parts
            parts = node_id.split(':')
            if len(parts) != 2:
                results['errors'].append(f"Invalid graph node ID format: {node_id}")
                continue

        return results

    def _validate_graph_key_naming(self) -> Dict[str, List[str]]:
        """Validate graph node naming conventions (semantic check)."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        graph = data.get('graph', {})

        for node_id in graph.keys():
            if ':' not in node_id:
                continue  # Format errors caught in syntax layer

            parts = node_id.split(':')
            if len(parts) != 2:
                continue  # Format errors caught in syntax layer

            node_type, node_name = parts

            # Check naming conventions
            if '_' in node_name:
                results['warnings'].append(
                    f"Node name uses underscore instead of dash: {node_id}"
                )

            # Check for reusing parent names (anti-pattern)
            if node_type in node_name:
                results['warnings'].append(
                    f"Node name reuses parent type: {node_id}"
                )

        return results

    def get_completeness_score(self, entity_id: str) -> Dict:
        """
        Calculate completeness score for an entity.

        Args:
            entity_id: Entity identifier

        Returns:
            Dictionary with score and details
        """
        data = self.graph.load()
        entity_type, entity_name = entity_id.split(':')

        score = {
            'total': 0,
            'completed': 0,
            'percentage': 0,
            'checks': {}
        }

        # Check if entity exists
        entity_data = data.get('entities', {}).get(entity_type, {}).get(entity_name)
        if not entity_data:
            return score

        score['total'] += 1
        score['checks']['exists'] = True
        score['completed'] += 1

        # Check for name
        score['total'] += 1
        if entity_data.get('name'):
            score['checks']['has_name'] = True
            score['completed'] += 1

        # Check for description
        score['total'] += 1
        if entity_data.get('description'):
            score['checks']['has_description'] = True
            score['completed'] += 1

        # Check for dependencies
        score['total'] += 1
        graph = data.get('graph', {})
        from .utils import get_all_deps
        graph_node = graph.get(entity_id, {})
        if isinstance(graph_node, dict) and get_all_deps(graph_node):
            score['checks']['has_dependencies'] = True
            score['completed'] += 1

        # Calculate percentage
        if score['total'] > 0:
            score['percentage'] = round((score['completed'] / score['total']) * 100, 1)

        return score

    def find_disconnected_subgraphs(self) -> List[Set[str]]:
        """
        Find disconnected subgraphs in the dependency graph.

        Returns:
            List of sets, where each set contains node IDs in a disconnected subgraph
        """
        data = self.graph.load()
        graph_data = data.get('graph', {})

        # Build adjacency list (undirected for connectivity)
        adjacency = defaultdict(set)
        from .utils import get_all_deps
        for node, node_data in graph_data.items():
            # Defensive check: ensure node_data is a dictionary
            if not isinstance(node_data, dict):
                continue

            for dep in get_all_deps(node_data):
                adjacency[node].add(dep)
                adjacency[dep].add(node)

        # Find connected components using DFS
        visited = set()
        components = []

        def dfs(node: str, component: Set[str]):
            visited.add(node)
            component.add(node)
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, component)

        for node in graph_data.keys():
            if node not in visited:
                component = set()
                dfs(node, component)
                components.append(component)

        # Return only if there are multiple components
        return components if len(components) > 1 else []

    def validate_naming_conventions(self) -> Dict[str, List[str]]:
        """Validate naming conventions for entities and references."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()

        # Check entities
        entities = data.get('entities', {})
        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, dict):
                for entity_name in entity_list.keys():
                    # Should use dashes, not underscores
                    if '_' in entity_name:
                        results['warnings'].append(
                            f"Entity name uses underscore: {entity_type}:{entity_name}"
                        )

        # Check references
        references = data.get('references', {})
        for ref_type, ref_list in references.items():
            if isinstance(ref_list, dict):
                for ref_name in ref_list.keys():
                    # References can use any naming for final nodes
                    # But check for key_object_notation style issues
                    if ref_name.replace('-', '').replace('_', '').isalpha():
                        if '_' in ref_name and '-' in ref_name:
                            results['info'].append(
                                f"Reference mixes dashes and underscores: {ref_type}:{ref_name}"
                            )

        return results


class ContractValidator:
    """
    Validates feature contracts for declared vs observed consistency.

    Provides severity-based validation with high, medium, and info levels.
    """

    SEVERITY_HIGH = 'high'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_INFO = 'info'

    def __init__(self, features_dir: str = ".ai/know/features"):
        """
        Initialize ContractValidator.

        Args:
            features_dir: Path to features directory
        """
        from .contract_manager import ContractManager
        self.features_dir = Path(features_dir)
        self.contract_manager = ContractManager(features_dir=features_dir)

    def validate_declared_vs_observed(self, feature_name: str) -> Dict[str, List]:
        """
        Compare declared intent vs observed reality.

        Args:
            feature_name: Feature name

        Returns:
            Dict with 'high', 'medium', 'info' severity lists
        """
        results = {
            'high': [],
            'medium': [],
            'info': []
        }

        contract = self.contract_manager.load_contract(feature_name)
        if not contract:
            results['high'].append({
                'type': 'contract_missing',
                'message': f"No contract found for feature: {feature_name}"
            })
            return results

        declared = contract.get('declared', {})
        observed = contract.get('observed', {})

        # Validate files
        self._validate_files(declared, observed, results)

        # Validate entities
        self._validate_entities(declared, observed, results)

        # Validate actions
        self._validate_actions(declared, results)

        return results

    def _validate_files(
        self,
        declared: Dict,
        observed: Dict,
        results: Dict[str, List]
    ) -> None:
        """Validate declared files vs observed files."""
        declared_creates = declared.get('files', {}).get('creates', [])
        declared_modifies = declared.get('files', {}).get('modifies', [])
        observed_created = observed.get('files', {}).get('created', [])
        observed_modified = observed.get('files', {}).get('modified', [])

        # Check declared creates were actually created
        for pattern in declared_creates:
            matched = any(self._matches_pattern(f, pattern) for f in observed_created)
            if not matched:
                results['high'].append({
                    'type': 'file_not_created',
                    'pattern': pattern,
                    'message': f"Declared file pattern '{pattern}' was not created"
                })

        # Check declared modifies were actually modified
        for pattern in declared_modifies:
            matched = any(self._matches_pattern(f, pattern) for f in observed_modified)
            if not matched:
                results['medium'].append({
                    'type': 'file_not_modified',
                    'pattern': pattern,
                    'message': f"Declared file pattern '{pattern}' was not modified"
                })

        # Check for unexpected created files
        all_patterns = declared_creates + declared_modifies
        for created_file in observed_created:
            matched = any(self._matches_pattern(created_file, p) for p in all_patterns)
            if not matched:
                results['medium'].append({
                    'type': 'file_unexpected',
                    'file': created_file,
                    'message': f"Created file '{created_file}' was not declared"
                })

    def _validate_entities(
        self,
        declared: Dict,
        observed: Dict,
        results: Dict[str, List]
    ) -> None:
        """Validate declared entities vs observed entities."""
        declared_creates = declared.get('entities', {}).get('creates', [])
        observed_created = observed.get('entities', {}).get('created', [])

        # Check declared creates were actually created
        for entity_id in declared_creates:
            if entity_id not in observed_created:
                results['high'].append({
                    'type': 'entity_not_created',
                    'entity': entity_id,
                    'message': f"Declared entity '{entity_id}' was not created"
                })

        # Check for unexpected entities
        for entity_id in observed_created:
            if entity_id not in declared_creates:
                results['info'].append({
                    'type': 'entity_unexpected',
                    'entity': entity_id,
                    'message': f"Created entity '{entity_id}' was not declared"
                })

    def _validate_actions(
        self,
        declared: Dict,
        results: Dict[str, List]
    ) -> None:
        """Validate action verification status."""
        actions = declared.get('actions', [])

        for action in actions:
            if not action.get('verified', False):
                results['medium'].append({
                    'type': 'action_unverified',
                    'action': action.get('entity'),
                    'description': action.get('description', ''),
                    'message': f"Action '{action.get('entity')}' has not been verified"
                })

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a glob pattern."""
        from fnmatch import fnmatch

        if '**' in pattern:
            return fnmatch(path, pattern) or fnmatch(path, pattern.replace('**/', '*/'))
        return fnmatch(path, pattern)

    def get_validation_summary(self, feature_name: str) -> Dict:
        """
        Get validation summary with counts and overall status.

        Args:
            feature_name: Feature name

        Returns:
            Dict with counts and status
        """
        results = self.validate_declared_vs_observed(feature_name)

        high_count = len(results['high'])
        medium_count = len(results['medium'])
        info_count = len(results['info'])

        if high_count > 0:
            status = 'drifted'
        elif medium_count > 0:
            status = 'pending'
        else:
            status = 'verified'

        return {
            'feature': feature_name,
            'status': status,
            'counts': {
                'high': high_count,
                'medium': medium_count,
                'info': info_count
            },
            'issues': results
        }
