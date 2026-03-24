"""Base visualizer with shared extraction logic."""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class VisualizationData:
    """Extracted graph data ready for rendering."""
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # nodes: {entity_id: {type, name, description, is_ref, ...}}
    edges: List[Tuple[str, str]] = field(default_factory=list)
    # edges: [(from_id, to_id), ...]
    graph_name: str = ""
    clusters: Dict[str, List[str]] = field(default_factory=dict)
    # clusters: {entity_type: [entity_id, ...]}


class BaseVisualizer(ABC):
    """Base class for all graph visualizers.

    Reads a GraphManager, filters by type/focus/depth, and delegates
    rendering to subclasses.
    """

    def __init__(self, graph_manager, entity_types=None, entity_focus=None,
                 depth=None, include_refs=False):
        self.gm = graph_manager
        self.entity_types = set(entity_types) if entity_types else None
        self.entity_focus = entity_focus
        self.depth = depth
        self.include_refs = include_refs

    @classmethod
    def check_available(cls) -> Tuple[bool, str]:
        """Check whether optional dependencies are available.

        Returns (True, '') if usable, or (False, install_message).
        """
        return True, ""

    def extract(self) -> VisualizationData:
        """Read the graph and return filtered VisualizationData."""
        graph_data = self.gm.get_graph()
        entities_section = graph_data.get("entities", {})
        refs_section = graph_data.get("references", {})
        graph_section = graph_data.get("graph", {})
        meta = graph_data.get("meta", {})

        graph_name = meta.get("project", {}).get("name", "") if isinstance(meta.get("project"), dict) else ""

        # Build entity→horizon lookup from meta.horizons
        phase_lookup: Dict[str, Dict[str, str]] = {}
        for horizon_name, phase_entities in meta.get("horizons", {}).items():
            if isinstance(phase_entities, dict):
                for eid, pdata in phase_entities.items():
                    status = pdata.get("status", "") if isinstance(pdata, dict) else ""
                    phase_lookup[eid] = {"phase": horizon_name, "status": status}

        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Tuple[str, str]] = []

        # Collect entity nodes
        for etype, elist in entities_section.items():
            if self.entity_types and etype not in self.entity_types:
                continue
            if isinstance(elist, dict):
                for ename, edata in elist.items():
                    eid = f"{etype}:{ename}"
                    phase_info = phase_lookup.get(eid, {})
                    nodes[eid] = {
                        "type": etype,
                        "name": edata.get("name", ename),
                        "description": edata.get("description", ""),
                        "is_ref": False,
                        "phase": phase_info.get("phase", ""),
                        "status": phase_info.get("status", ""),
                    }

        # Collect reference nodes
        if self.include_refs:
            for rtype, rlist in refs_section.items():
                if self.entity_types and rtype not in self.entity_types:
                    continue
                if isinstance(rlist, dict):
                    for rname, rdata in rlist.items():
                        rid = f"{rtype}:{rname}"
                        label = rdata.get("name", rname) if isinstance(rdata, dict) else rname
                        nodes[rid] = {
                            "type": rtype,
                            "name": label,
                            "description": "",
                            "is_ref": True,
                        }

        # Collect edges (only between included nodes)
        all_node_ids = set(nodes.keys())
        for from_id, node_deps in graph_section.items():
            if from_id not in all_node_ids:
                continue
            if isinstance(node_deps, dict):
                for to_id in node_deps.get("depends_on", []):
                    if to_id in all_node_ids:
                        edges.append((from_id, to_id))

        data = VisualizationData(
            nodes=nodes,
            edges=edges,
            graph_name=graph_name,
        )

        # Focus on a specific entity neighborhood
        if self.entity_focus:
            data = self._focus_subgraph(data)

        # Build clusters (group node IDs by type)
        for nid, ninfo in data.nodes.items():
            ntype = ninfo["type"]
            data.clusters.setdefault(ntype, []).append(nid)

        return data

    def _focus_subgraph(self, data: VisualizationData) -> VisualizationData:
        """BFS in both directions from focus entity to self.depth."""
        focus = self.entity_focus
        if focus not in data.nodes:
            return data

        max_depth = self.depth if self.depth is not None else 999

        # Build adjacency lists
        fwd: Dict[str, List[str]] = {}  # from → [to]
        rev: Dict[str, List[str]] = {}  # to → [from]
        for f, t in data.edges:
            fwd.setdefault(f, []).append(t)
            rev.setdefault(t, []).append(f)

        # BFS both directions
        visited: Set[str] = {focus}
        queue: deque = deque([(focus, 0)])
        while queue:
            node, d = queue.popleft()
            if d >= max_depth:
                continue
            for neighbor in fwd.get(node, []) + rev.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, d + 1))

        # Filter
        new_nodes = {k: v for k, v in data.nodes.items() if k in visited}
        new_edges = [(f, t) for f, t in data.edges if f in visited and t in visited]
        return VisualizationData(
            nodes=new_nodes,
            edges=new_edges,
            graph_name=data.graph_name,
        )

    @abstractmethod
    def render(self, data: VisualizationData) -> Any:
        """Render the visualization data. Return type varies by subclass."""

    def run(self) -> Any:
        """Extract + render in one call."""
        data = self.extract()
        return self.render(data)
