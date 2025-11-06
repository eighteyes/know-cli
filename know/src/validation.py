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
        Run all validation checks on the graph.

        Returns:
            Tuple of (is_valid, dict of validation results by category)
        """
        results = {
            'errors': [],
            'warnings': [],
            'info': []
        }

        # Run all validation checks
        checks = [
            self._validate_structure,
            self._validate_entity_schema,
            self._validate_reference_usage,
            self._validate_orphaned_nodes,
            self._validate_missing_descriptions,
            self._validate_entity_types,
            self._validate_graph_keys
        ]

        for check in checks:
            check_results = check()
            for level, messages in check_results.items():
                results[level].extend(messages)

        is_valid = len(results['errors']) == 0

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
            if 'phases' not in meta:
                results['warnings'].append("Missing 'phases' in meta")

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
                        results['warnings'].append(
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
            for dep in node_data.get('depends_on', []):
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

    def _validate_graph_keys(self) -> Dict[str, List[str]]:
        """Validate that graph node keys match entity/reference keys."""
        results = {'errors': [], 'warnings': [], 'info': []}

        data = self.graph.load()
        graph = data.get('graph', {})

        for node_id in graph.keys():
            # Check for proper format (type:name)
            if ':' not in node_id:
                results['errors'].append(f"Invalid graph node ID format: {node_id} (missing ':')")
                continue

            # Check for snake-case naming
            parts = node_id.split(':')
            if len(parts) != 2:
                results['errors'].append(f"Invalid graph node ID format: {node_id}")
                continue

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
        if entity_id in graph and graph[entity_id].get('depends_on'):
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
        for node, node_data in graph_data.items():
            for dep in node_data.get('depends_on', []):
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
