"""
Dependency management for the specification graph.
Handles dependency validation, resolution, and cycle detection.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque


class DependencyManager:
    """Manages dependencies between entities in the graph."""

    def __init__(self, graph_manager, rules_path: Optional[str] = None):
        """
        Initialize dependency manager.

        Args:
            graph_manager: GraphManager instance
            rules_path: Path to dependency-rules.json
        """
        self.graph = graph_manager

        # Load dependency rules
        if rules_path is None:
            rules_path = Path(__file__).parent.parent / "config" / "dependency-rules.json"

        with open(rules_path, 'r') as f:
            self.rules = json.load(f)

        self.allowed_deps = self.rules.get('allowed_dependencies', {})
        self.entity_description = self.rules.get('entity_description', {})
        self.reference_description = self.rules.get('reference_description', {})

    def is_valid_dependency(self, from_type: str, to_type: str) -> bool:
        """
        Check if a dependency from one type to another is allowed.

        Args:
            from_type: Source entity type
            to_type: Target entity type

        Returns:
            True if dependency is allowed
        """
        # Rules use singular forms - use types as-is
        allowed = self.allowed_deps.get(from_type, [])
        return to_type in allowed

    def get_allowed_targets(self, entity_type: str) -> List[str]:
        """
        Get list of entity types that can be dependencies of the given type.

        Args:
            entity_type: The source entity type

        Returns:
            List of allowed target entity types
        """
        # Rules use singular forms - use type as-is
        return self.allowed_deps.get(entity_type, [])

    def get_dependencies(self, entity_id: str) -> List[str]:
        """
        Get all direct dependencies for an entity.

        Args:
            entity_id: Entity identifier (e.g., "feature:analytics")

        Returns:
            List of dependency entity IDs
        """
        data = self.graph.get_graph()
        graph = data.get('graph', {})

        entity_node = graph.get(entity_id, {})
        return entity_node.get('depends_on', [])

    def get_dependents(self, entity_id: str) -> List[str]:
        """
        Get all entities that depend on this entity.

        Args:
            entity_id: Entity identifier

        Returns:
            List of entity IDs that depend on this entity
        """
        data = self.graph.get_graph()
        graph = data.get('graph', {})

        dependents = []
        for node_id, node_data in graph.items():
            if entity_id in node_data.get('depends_on', []):
                dependents.append(node_id)

        return dependents

    def resolve_chain(self, entity_id: str, visited: Optional[Set[str]] = None) -> List[str]:
        """
        Resolve the full dependency chain for an entity.

        Args:
            entity_id: Entity identifier
            visited: Set of already visited entities (for cycle detection)

        Returns:
            List of entity IDs in dependency order
        """
        if visited is None:
            visited = set()

        if entity_id in visited:
            return []

        visited.add(entity_id)
        chain = [entity_id]

        for dep in self.get_dependencies(entity_id):
            chain.extend(self.resolve_chain(dep, visited))

        return chain

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.

        Returns:
            List of cycles, where each cycle is a list of entity IDs
        """
        data = self.graph.get_graph()
        graph = data.get('graph', {})

        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for dep in graph.get(node, {}).get('depends_on', []):
                if dep not in visited:
                    dfs(dep, path[:])
                elif dep in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep)
                    cycles.append(path[cycle_start:] + [dep])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def validate_graph(self) -> Tuple[bool, List[str]]:
        """
        Validate all dependencies in the graph against rules.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        data = self.graph.get_graph()
        graph = data.get('graph', {})
        errors = []

        # Check for cycles
        cycles = self.detect_cycles()
        if cycles:
            for cycle in cycles:
                errors.append(f"Circular dependency: {' → '.join(cycle)}")

        # Validate each dependency
        for entity_id, node_data in graph.items():
            entity_type = entity_id.split(':')[0] if ':' in entity_id else entity_id

            # Validate unordered depends_on
            for dep_id in node_data.get('depends_on', []):
                dep_type = dep_id.split(':')[0] if ':' in dep_id else dep_id

                # Skip reference dependencies (they're always valid)
                if dep_type in self.reference_description:
                    continue

                if not self.is_valid_dependency(entity_type, dep_type):
                    allowed = self.get_allowed_targets(entity_type)
                    errors.append(
                        f"Invalid dependency: {entity_id} → {dep_id}. "
                        f"{entity_type} can only depend on: {', '.join(allowed)}\n"
                        f"    Fix: know unlink {entity_id} {dep_id}"
                    )

            # Validate ordered depends_on_ordered
            if "depends_on_ordered" in node_data:
                # Only workflows should have ordered dependencies
                if entity_type != "workflow":
                    errors.append(
                        f"{entity_id} cannot have depends_on_ordered (only workflow entities). "
                        f"Fix: Remove depends_on_ordered or convert to workflow entity"
                    )

                # Validate ordered dependency targets
                for dep_id in node_data.get('depends_on_ordered', []):
                    dep_type = dep_id.split(':')[0] if ':' in dep_id else dep_id

                    # Skip reference dependencies
                    if dep_type in self.reference_description:
                        continue

                    if not self.is_valid_dependency(entity_type, dep_type):
                        allowed = self.get_allowed_targets(entity_type)
                        errors.append(
                            f"Invalid ordered dependency: {entity_id} → {dep_id}. "
                            f"{entity_type} can only depend on: {', '.join(allowed)}"
                        )

        return len(errors) == 0, errors

    def suggest_connections(self, entity_id: str, max_suggestions: int = 5) -> Dict[str, List[str]]:
        """
        Suggest valid connections for an entity based on existing entities.

        Args:
            entity_id: Entity identifier
            max_suggestions: Maximum number of suggestions per type

        Returns:
            Dictionary mapping entity types to lists of suggested entity IDs
        """
        entity_type = entity_id.split(':')[0] if ':' in entity_id else entity_id
        allowed_types = self.get_allowed_targets(entity_type)

        data = self.graph.get_graph()
        entities = data.get('entities', {})

        suggestions = {}
        for allowed_type in allowed_types:
            # Get entities of this type
            type_entities = entities.get(allowed_type, {})
            entity_ids = [f"{allowed_type}:{name}" for name in type_entities.keys()]

            # Limit suggestions
            suggestions[allowed_type] = entity_ids[:max_suggestions]

        return suggestions

    def get_dependency_tree(self, entity_id: str, max_depth: int = 10) -> Dict:
        """
        Get the dependency tree for an entity.

        Args:
            entity_id: Entity identifier
            max_depth: Maximum depth to traverse

        Returns:
            Nested dictionary representing the dependency tree
        """
        if max_depth <= 0:
            return {'id': entity_id, 'dependencies': []}

        deps = self.get_dependencies(entity_id)

        return {
            'id': entity_id,
            'dependencies': [
                self.get_dependency_tree(dep, max_depth - 1)
                for dep in deps
            ]
        }

    def get_reverse_tree(self, entity_id: str, max_depth: int = 10) -> Dict:
        """
        Get the reverse dependency tree (what depends on this entity).

        Args:
            entity_id: Entity identifier
            max_depth: Maximum depth to traverse

        Returns:
            Nested dictionary representing entities that depend on this one
        """
        if max_depth <= 0:
            return {'id': entity_id, 'dependents': []}

        dependents = self.get_dependents(entity_id)

        return {
            'id': entity_id,
            'dependents': [
                self.get_reverse_tree(dep, max_depth - 1)
                for dep in dependents
            ]
        }

    def topological_sort(self) -> List[str]:
        """
        Get a topological ordering of all entities in the graph.

        Returns:
            List of entity IDs in dependency order (dependencies before dependents),
            or empty list if graph has cycles
        """
        data = self.graph.get_graph()
        graph = data.get('graph', {})

        # Build in-degree map
        in_degree = defaultdict(int)
        for node in graph:
            in_degree[node] = 0

        for node, node_data in graph.items():
            for dep in node_data.get('depends_on', []):
                in_degree[node] += 1

        # Queue nodes with no dependencies
        queue = deque([node for node in graph if in_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Reduce in-degree for dependents
            for dependent in self.get_dependents(node):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If we didn't process all nodes, there are cycles
        if len(result) != len(graph):
            return []

        return result

    def add_dependency(self, from_id: str, to_id: str, validate: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Add a dependency between two entities.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID
            validate: Whether to validate the dependency

        Returns:
            Tuple of (success, error_message)
        """
        # Validate if requested
        if validate:
            from_type = from_id.split(':')[0] if ':' in from_id else from_id
            to_type = to_id.split(':')[0] if ':' in to_id else to_id

            # Allow references always
            if to_type not in self.reference_description:
                if not self.is_valid_dependency(from_type, to_type):
                    allowed = self.get_allowed_targets(from_type)
                    return False, f"{from_type} can only depend on: {', '.join(allowed)}"

        # Get current graph
        data = self.graph.get_graph()
        graph = data.get('graph', {})

        # Initialize node if it doesn't exist
        if from_id not in graph:
            graph[from_id] = {'depends_on': []}

        # Add dependency if not already present
        if to_id not in graph[from_id]['depends_on']:
            graph[from_id]['depends_on'].append(to_id)

        # Update graph
        data['graph'] = graph
        self.graph.save(data)

        return True, None

    def remove_dependency(self, from_id: str, to_id: str) -> bool:
        """
        Remove a dependency between two entities.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID

        Returns:
            True if dependency was removed
        """
        data = self.graph.get_graph()
        graph = data.get('graph', {})

        if from_id in graph and to_id in graph[from_id].get('depends_on', []):
            graph[from_id]['depends_on'].remove(to_id)
            data['graph'] = graph
            self.graph.save(data)
            return True

        return False
