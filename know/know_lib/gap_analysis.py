"""
Gap analysis tools for knowledge graph
Identifies incomplete dependency chains and missing implementations
"""

from typing import Dict, List, Tuple, Set, Optional
from enum import Enum


class ChainStatus(Enum):
    """Status of a dependency chain"""
    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING_DEPS = "missing_deps"
    MISSING_COMPONENT = "missing_component"
    NO_COMPLETE_CHAINS = "no_complete_chains"
    UNKNOWN = "unknown"


class GapAnalyzer:
    """Analyzes gaps in dependency chains"""

    def __init__(self, graph_manager, entity_manager, dependency_manager):
        """
        Initialize gap analyzer.

        Args:
            graph_manager: GraphManager instance
            entity_manager: EntityManager instance
            dependency_manager: DependencyManager instance
        """
        self.graph = graph_manager
        self.entities = entity_manager
        self.deps = dependency_manager

    def is_component_complete(self, component_id: str) -> ChainStatus:
        """
        Check if a component is fully implemented.

        A component is considered complete if it has both behavior and data model dependencies.

        Args:
            component_id: Component entity ID

        Returns:
            ChainStatus indicating level of completion
        """
        dependencies = self.deps.get_dependencies(component_id)

        has_behavior = any(dep.startswith('operation:') for dep in dependencies)
        has_model = any(dep.startswith('data-model:') or dep.startswith('model:') for dep in dependencies)

        if has_behavior and has_model:
            return ChainStatus.COMPLETE
        elif has_behavior or has_model:
            return ChainStatus.PARTIAL
        else:
            return ChainStatus.MISSING_DEPS

    def analyze_chain(self, entity_id: str, max_depth: int = 10,
                     current_depth: int = 0, visited: Optional[Set[str]] = None) -> List[Tuple[str, ChainStatus]]:
        """
        Analyze dependency chain starting from an entity.

        Args:
            entity_id: Starting entity ID
            max_depth: Maximum traversal depth
            current_depth: Current depth (internal)
            visited: Visited entities to prevent cycles

        Returns:
            List of (chain_path, status) tuples
        """
        if visited is None:
            visited = set()

        if current_depth > max_depth:
            return [(entity_id, ChainStatus.UNKNOWN)]

        if entity_id in visited:
            return [(entity_id, ChainStatus.UNKNOWN)]  # Cycle detected

        visited.add(entity_id)
        entity_type = entity_id.split(':')[0] if ':' in entity_id else ''

        dependencies = self.deps.get_dependencies(entity_id)

        # No dependencies - terminal node
        if not dependencies:
            if entity_type == 'component':
                status = self.is_component_complete(entity_id)
                return [(entity_id, status)]
            else:
                return [(entity_id, ChainStatus.MISSING_DEPS)]

        # Traverse dependencies
        results = []
        found_complete = False

        for dep in dependencies:
            # Check if dependency exists
            dep_entity = self.entities.get_entity(dep)

            if not dep_entity:
                # Dependency not found - might be a reference
                dep_type = dep.split(':')[0] if ':' in dep else ''
                if entity_type == 'component':
                    results.append((f"{entity_id} -> {dep}", ChainStatus.MISSING_COMPONENT))
                continue

            # Recursive traversal
            sub_chains = self.analyze_chain(dep, max_depth, current_depth + 1, visited.copy())

            for sub_path, sub_status in sub_chains:
                chain_path = f"{entity_id} -> {sub_path}"
                results.append((chain_path, sub_status))

                if sub_status == ChainStatus.COMPLETE:
                    found_complete = True

        # If no complete chains found at root level
        if not found_complete and current_depth == 0:
            results.append((entity_id, ChainStatus.NO_COMPLETE_CHAINS))

        return results

    def analyze_all_users_and_objectives(self) -> Dict[str, any]:
        """
        Analyze all users and objectives for implementation gaps.

        Returns:
            Dictionary with analysis results and statistics
        """
        data = self.graph.load()
        entities = data.get('entities', {})

        total_entities = 0
        complete_chains = 0
        partial_chains = 0
        incomplete_chains = 0
        all_chains = []

        # Analyze users
        users = entities.get('user', {})
        for user_name in users.keys():
            user_id = f"user:{user_name}"
            chains = self.analyze_chain(user_id)
            all_chains.extend(chains)
            total_entities += 1

            # Categorize
            has_complete = any(status == ChainStatus.COMPLETE for _, status in chains)
            has_partial = any(status == ChainStatus.PARTIAL for _, status in chains)

            if has_complete:
                complete_chains += 1
            elif has_partial:
                partial_chains += 1
            else:
                incomplete_chains += 1

        # Analyze objectives
        objectives = entities.get('objective', {})
        for obj_name in objectives.keys():
            obj_id = f"objective:{obj_name}"
            chains = self.analyze_chain(obj_id)
            all_chains.extend(chains)
            total_entities += 1

            # Categorize
            has_complete = any(status == ChainStatus.COMPLETE for _, status in chains)
            has_partial = any(status == ChainStatus.PARTIAL for _, status in chains)

            if has_complete:
                complete_chains += 1
            elif has_partial:
                partial_chains += 1
            else:
                incomplete_chains += 1

        return {
            'summary': {
                'total': total_entities,
                'complete': complete_chains,
                'partial': partial_chains,
                'incomplete': incomplete_chains
            },
            'chains': all_chains
        }

    def list_missing_connections(self) -> Dict[str, List[str]]:
        """
        List entities missing expected dependency types.

        Returns:
            Dictionary mapping gap types to list of entity IDs
        """
        data = self.graph.load()
        entities = data.get('entities', {})

        missing = {
            'objectives_without_features': [],
            'features_without_actions': [],
            'actions_without_components': [],
            'components_without_implementation': []
        }

        # Check objectives for features
        for obj_name in entities.get('objective', {}).keys():
            obj_id = f"objective:{obj_name}"
            deps = self.deps.get_dependencies(obj_id)
            if not any(d.startswith('feature:') for d in deps):
                missing['objectives_without_features'].append(obj_id)

        # Check features for actions
        for feat_name in entities.get('feature', {}).keys():
            feat_id = f"feature:{feat_name}"
            deps = self.deps.get_dependencies(feat_id)
            if not any(d.startswith('action:') for d in deps):
                missing['features_without_actions'].append(feat_id)

        # Check actions for components
        for action_name in entities.get('action', {}).keys():
            action_id = f"action:{action_name}"
            deps = self.deps.get_dependencies(action_id)
            if not any(d.startswith('component:') for d in deps):
                missing['actions_without_components'].append(action_id)

        # Check components for implementation
        for comp_name in entities.get('component', {}).keys():
            comp_id = f"component:{comp_name}"
            status = self.is_component_complete(comp_id)
            if status != ChainStatus.COMPLETE:
                missing['components_without_implementation'].append(comp_id)

        return missing

    def get_implementation_summary(self) -> Dict[str, any]:
        """
        Get summary of implementation status.

        Returns:
            Dictionary with entity counts and completion rates
        """
        data = self.graph.load()
        entities = data.get('entities', {})
        graph = data.get('graph', {})

        # Count entities
        total_users = len(entities.get('user', {}))
        total_objectives = len(entities.get('objective', {}))
        total_features = len(entities.get('feature', {}))
        total_actions = len(entities.get('action', {}))
        total_components = len(entities.get('component', {}))

        # Count components with dependencies
        components_with_deps = 0
        for comp_name in entities.get('component', {}).keys():
            comp_id = f"component:{comp_name}"
            if comp_id in graph and graph[comp_id].get('depends_on'):
                components_with_deps += 1

        # Calculate completion rate
        completion_rate = 0
        if total_components > 0:
            completion_rate = int((components_with_deps / total_components) * 100)

        return {
            'entities': {
                'users': total_users,
                'objectives': total_objectives,
                'features': total_features,
                'actions': total_actions,
                'components': {
                    'total': total_components,
                    'with_dependencies': components_with_deps
                }
            },
            'completion_rate': completion_rate
        }
