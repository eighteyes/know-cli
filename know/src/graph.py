"""
Core graph operations and management
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
import networkx as nx
from .cache import GraphCache


class GraphManager:
    """Manages graph operations with efficient caching and algorithms"""

    def __init__(self, graph_path: str = ".ai/know/spec-graph.json"):
        self.cache = GraphCache(graph_path)
        self._nx_graph: Optional[nx.DiGraph] = None
        self._counterpart_graph: Optional['GraphManager'] = None

    def get_graph(self) -> Dict[str, Any]:
        """Get the complete graph"""
        return self.cache.get()

    def load(self) -> Dict[str, Any]:
        """Alias for get_graph() for backward compatibility"""
        return self.get_graph()

    def save_graph(self, data: Dict[str, Any]) -> bool:
        """Save the complete graph"""
        self._nx_graph = None  # Invalidate NetworkX cache
        return self.cache.write(data)

    def get_meta(self) -> Dict[str, Any]:
        """Get meta information"""
        return self.get_graph().get("meta", {})

    def set_meta(self, meta: Dict[str, Any]):
        """Update meta information"""
        graph = self.get_graph()
        graph["meta"] = meta
        self.save_graph(graph)

    def get_entities(self) -> Dict[str, Any]:
        """Get all entities"""
        return self.get_graph().get("entities", {})

    def get_references(self) -> Dict[str, Any]:
        """Get all references"""
        return self.get_graph().get("references", {})

    def get_dependencies(self) -> Dict[str, Any]:
        """Get dependency graph"""
        return self.get_graph().get("graph", {})

    def build_nx_graph(self) -> nx.DiGraph:
        """Build NetworkX directed graph from dependencies"""
        if self._nx_graph is not None:
            return self._nx_graph

        self._nx_graph = nx.DiGraph()
        deps = self.get_dependencies()

        for node, node_deps in deps.items():
            if not self._nx_graph.has_node(node):
                self._nx_graph.add_node(node)

            if isinstance(node_deps, dict) and "depends_on" in node_deps:
                dependencies = node_deps["depends_on"]
                if isinstance(dependencies, list):
                    for dep in dependencies:
                        self._nx_graph.add_edge(node, dep)

        return self._nx_graph

    def find_dependencies(self, entity: str, recursive: bool = True) -> List[str]:
        """Find all dependencies for an entity"""
        graph = self.build_nx_graph()

        if entity not in graph:
            return []

        if recursive:
            # Get all ancestors (dependencies)
            try:
                ancestors = nx.ancestors(graph, entity)
                return list(ancestors)
            except:
                return []
        else:
            # Get direct dependencies only
            return list(graph.successors(entity))

    def find_dependents(self, entity: str, recursive: bool = True) -> List[str]:
        """Find all entities that depend on this one"""
        graph = self.build_nx_graph()

        if entity not in graph:
            return []

        if recursive:
            # Get all descendants (dependents)
            try:
                descendants = nx.descendants(graph, entity)
                return list(descendants)
            except:
                return []
        else:
            # Get direct dependents only
            return list(graph.predecessors(entity))

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies"""
        graph = self.build_nx_graph()
        try:
            cycles = list(nx.simple_cycles(graph))
            return cycles
        except:
            return []

    def validate_dependencies(self) -> Dict[str, List[str]]:
        """Validate all dependencies exist"""
        issues = {}
        deps = self.get_dependencies()
        entities = self.get_entities()
        refs = self.get_references()

        all_nodes = set()
        all_nodes.update(entities.keys())
        all_nodes.update(refs.keys())

        for node, node_deps in deps.items():
            if node not in all_nodes:
                if "orphaned" not in issues:
                    issues["orphaned"] = []
                issues["orphaned"].append(node)

            if isinstance(node_deps, dict) and "depends_on" in node_deps:
                dependencies = node_deps["depends_on"]
                if isinstance(dependencies, list):
                    for dep in dependencies:
                        if dep not in all_nodes:
                            if "missing_dependency" not in issues:
                                issues["missing_dependency"] = []
                            issues["missing_dependency"].append(f"{node} -> {dep}")

        # Check for cycles
        cycles = self.detect_cycles()
        if cycles:
            issues["circular_dependencies"] = [" -> ".join(cycle + [cycle[0]]) for cycle in cycles]

        return issues

    def topological_sort(self) -> List[str]:
        """Get topological ordering of graph (build order)"""
        graph = self.build_nx_graph()
        try:
            return list(nx.topological_sort(graph))
        except nx.NetworkXError:
            # Graph has cycles
            return []

    def find_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find path between two nodes"""
        graph = self.build_nx_graph()
        try:
            return nx.shortest_path(graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    # Cross-graph traversal methods
    def get_counterpart_graph_path(self) -> Optional[str]:
        """Get path to counterpart graph from meta.

        Returns:
            Path to code graph if this is spec graph, or path to spec graph if this is code graph.
            None if meta field is not set.
        """
        meta = self.get_meta()

        # Check if this is a spec graph looking for code graph
        if 'code_graph_path' in meta:
            return meta['code_graph_path']

        # Check if this is a code graph looking for spec graph
        if 'spec_graph_path' in meta:
            return meta['spec_graph_path']

        return None

    def load_counterpart_graph(self) -> Optional['GraphManager']:
        """Load the counterpart graph (code ↔ spec).

        Uses meta.code_graph_path or meta.spec_graph_path to load the counterpart.
        Caches the loaded graph for subsequent calls.

        Returns:
            GraphManager instance for the counterpart graph, or None if not configured.
        """
        if self._counterpart_graph is not None:
            return self._counterpart_graph

        counterpart_path = self.get_counterpart_graph_path()
        if not counterpart_path:
            return None

        # Resolve relative path from current graph's directory
        current_graph_path = Path(self.cache.path)
        if not Path(counterpart_path).is_absolute():
            counterpart_path = (current_graph_path.parent / counterpart_path).resolve()

        if not Path(counterpart_path).exists():
            return None

        self._counterpart_graph = GraphManager(str(counterpart_path))
        return self._counterpart_graph

    def resolve_graph_link(self, graph_link_id: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Resolve a graph-link reference to entities in counterpart graph.

        Args:
            graph_link_id: Key from graph-link reference (e.g., "auth-module")

        Returns:
            Tuple of (entity_id, entity_data) from counterpart graph, or None if not found.
            If multiple entities are linked, returns the first one found.
        """
        refs = self.get_references()
        graph_links = refs.get('graph-link', {})

        if graph_link_id not in graph_links:
            return None

        link_data = graph_links[graph_link_id]
        counterpart = self.load_counterpart_graph()

        if not counterpart:
            return None

        # Graph-link can reference component, feature, module, etc.
        # Try to find the first valid entity reference
        counterpart_entities = counterpart.get_entities()

        for key, value in link_data.items():
            if isinstance(value, str) and value in counterpart_entities:
                return (value, counterpart_entities[value])

        return None

    def resolve_implementation(self, impl_ref_id: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Resolve an implementation reference to code entities.

        Args:
            impl_ref_id: Key from implementation reference (e.g., "auth-impl")

        Returns:
            List of (entity_id, entity_data) tuples from code graph.
        """
        refs = self.get_references()
        implementations = refs.get('implementation', {})

        if impl_ref_id not in implementations:
            return []

        impl_refs = implementations[impl_ref_id]
        if not isinstance(impl_refs, list):
            impl_refs = [impl_refs]

        counterpart = self.load_counterpart_graph()
        if not counterpart:
            return []

        results = []
        for ref in impl_refs:
            # Implementation refs point to graph-link IDs in code graph
            if ref.startswith('graph-link:'):
                graph_link_id = ref.replace('graph-link:', '')
                resolved = counterpart.resolve_graph_link(graph_link_id)
                if resolved:
                    results.append(resolved)

        return results

    def get_feature_implementations(self, feature_id: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all code entities that implement a feature.

        Args:
            feature_id: Feature entity ID (e.g., "feature:auth")

        Returns:
            List of (entity_id, entity_data) tuples from code graph.
        """
        graph = self.get_dependencies()
        if feature_id not in graph:
            return []

        dependencies = graph[feature_id].get('depends_on', [])
        results = []

        for dep in dependencies:
            if dep.startswith('implementation:'):
                impl_id = dep.replace('implementation:', '')
                results.extend(self.resolve_implementation(impl_id))

        return results

    def get_code_feature_mapping(self, code_entity_id: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Get the spec feature that a code entity implements.

        Args:
            code_entity_id: Code entity ID (e.g., "module:auth")

        Returns:
            Tuple of (feature_id, feature_data) from spec graph, or None if not mapped.
        """
        # First find which graph-link references this entity
        refs = self.get_references()
        graph_links = refs.get('graph-link', {})

        link_id = None
        for glink_id, glink_data in graph_links.items():
            # Check if this graph-link references our code entity
            for value in glink_data.values():
                if value == code_entity_id:
                    link_id = glink_id
                    break
            if link_id:
                break

        if not link_id:
            return None

        # Now find which feature uses this graph-link via implementation reference
        counterpart = self.load_counterpart_graph()
        if not counterpart:
            return None

        # Look for implementation references that use this graph-link
        counterpart_refs = counterpart.get_references()
        implementations = counterpart_refs.get('implementation', {})

        impl_ref_id = None
        for impl_id, impl_refs in implementations.items():
            if not isinstance(impl_refs, list):
                impl_refs = [impl_refs]

            target = f'graph-link:{link_id}'
            if target in impl_refs:
                impl_ref_id = impl_id
                break

        if not impl_ref_id:
            return None

        # Find which feature depends on this implementation
        counterpart_graph = counterpart.get_dependencies()
        counterpart_entities = counterpart.get_entities()

        for entity_id, entity_deps in counterpart_graph.items():
            if entity_id.startswith('feature:'):
                deps = entity_deps.get('depends_on', [])
                if f'implementation:{impl_ref_id}' in deps:
                    return (entity_id, counterpart_entities.get(entity_id, {}))

        return None