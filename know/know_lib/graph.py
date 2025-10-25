"""
Core graph operations and management
"""

from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import networkx as nx
from .cache import GraphCache


class GraphManager:
    """Manages graph operations with efficient caching and algorithms"""

    def __init__(self, graph_path: str = ".ai/spec-graph.json"):
        self.cache = GraphCache(graph_path)
        self._nx_graph: Optional[nx.DiGraph] = None

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