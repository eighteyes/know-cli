"""Graphviz DOT visualizer."""

from .base import BaseVisualizer, VisualizationData
from .theme import get_color, get_node_shape_dot

try:
    import graphviz as gv
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False


def _clean_id(entity_id):
    return entity_id.replace(":", "_").replace("-", "_").replace(".", "_")


class DotVisualizer(BaseVisualizer):
    """Generate Graphviz DOT source and optionally render to file."""

    @classmethod
    def check_available(cls):
        if not HAS_GRAPHVIZ:
            return False, "pip install graphviz  (also needs system graphviz: apt install graphviz)"
        return True, ""

    def render(self, data: VisualizationData) -> str:
        """Return DOT source string."""
        lines = [
            "digraph G {",
            '    rankdir=TB;',
            f'    label="{data.graph_name or "Graph"}";',
            '    labelloc=t;',
            '    fontsize=16;',
            '    node [fontsize=11, style=filled];',
            '    edge [color="#666666"];',
        ]

        # Cluster nodes by type
        for etype, node_ids in sorted(data.clusters.items()):
            color = get_color(etype)
            shape = get_node_shape_dot(etype)
            lines.append(f"    subgraph cluster_{etype} {{")
            lines.append(f'        label="{etype}";')
            lines.append(f'        style=rounded;')
            lines.append(f'        color="{color["stroke"]}";')
            for nid in sorted(node_ids):
                ninfo = data.nodes[nid]
                clean = _clean_id(nid)
                label = ninfo["name"]
                if len(label) > 30:
                    label = label[:27] + "..."
                lines.append(
                    f'        {clean} [label="{label}", '
                    f'fillcolor="{color["fill"]}", '
                    f'color="{color["stroke"]}", '
                    f'shape={shape}];'
                )
            lines.append("    }")

        # Edges
        for from_id, to_id in sorted(data.edges):
            lines.append(f"    {_clean_id(from_id)} -> {_clean_id(to_id)};")

        lines.append("}")
        return "\n".join(lines)

    def render_to_file(self, data: VisualizationData, output_path: str,
                       fmt: str = "svg") -> str:
        """Render to file using graphviz library. Returns output file path."""
        if not HAS_GRAPHVIZ:
            raise RuntimeError("graphviz not installed")

        dot_source = self.render(data)
        src = gv.Source(dot_source)
        rendered = src.render(filename=output_path, format=fmt, cleanup=True)
        return rendered
