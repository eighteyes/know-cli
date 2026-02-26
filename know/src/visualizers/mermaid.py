"""Mermaid flowchart visualizer."""

from .base import BaseVisualizer, VisualizationData
from .theme import get_color


def _clean_id(entity_id):
    """Convert entity ID to a valid Mermaid node identifier."""
    return entity_id.replace(":", "_").replace("-", "_").replace(".", "_")


def _escape_label(text):
    """Escape text for use in Mermaid labels."""
    text = text.replace('"', "'")
    if len(text) > 40:
        text = text[:37] + "..."
    return text


class MermaidVisualizer(BaseVisualizer):
    """Generate Mermaid flowchart syntax."""

    def render(self, data: VisualizationData) -> str:
        """Return a Mermaid flowchart string."""
        lines = ["flowchart TD"]

        if not data.nodes:
            lines.append("    empty[No nodes to display]")
            return "\n".join(lines)

        # Group nodes into subgraphs by type
        for etype, node_ids in sorted(data.clusters.items()):
            color = get_color(etype)
            lines.append(f"    subgraph {etype}")
            for nid in sorted(node_ids):
                ninfo = data.nodes[nid]
                clean = _clean_id(nid)
                label = _escape_label(ninfo["name"])
                if ninfo.get("is_ref"):
                    lines.append(f'        {clean}[/"{label}"/]')
                else:
                    lines.append(f'        {clean}["{label}"]')
                lines.append(f"        class {clean} {etype}Class")
            lines.append("    end")

        # Edges
        lines.append("")
        for from_id, to_id in sorted(data.edges):
            lines.append(f"    {_clean_id(from_id)} --> {_clean_id(to_id)}")

        # Class definitions for styling
        lines.append("")
        lines.append("    %% Styling")
        seen_types = set()
        for nid, ninfo in data.nodes.items():
            seen_types.add(ninfo["type"])
        for etype in sorted(seen_types):
            c = get_color(etype)
            lines.append(
                f"    classDef {etype}Class "
                f"fill:{c['fill']},stroke:{c['stroke']},"
                f"stroke-width:2px,color:{c['text_color']}"
            )

        return "\n".join(lines)


# Backward-compat alias for existing __init__.py import
MermaidGenerator = MermaidVisualizer
