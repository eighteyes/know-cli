"""PyVis interactive HTML visualizer."""

from .base import BaseVisualizer, VisualizationData
from .theme import get_color

try:
    from pyvis.network import Network
    HAS_PYVIS = True
except ImportError:
    HAS_PYVIS = False


class HtmlVisualizer(BaseVisualizer):
    """Generate an interactive HTML graph using PyVis."""

    @classmethod
    def check_available(cls):
        if not HAS_PYVIS:
            return False, "pip install pyvis"
        return True, ""

    def render(self, data: VisualizationData) -> str:
        """Return HTML string."""
        if not HAS_PYVIS:
            raise RuntimeError("pyvis not installed")

        net = Network(
            height="750px", width="100%", directed=True,
            bgcolor="#ffffff", font_color="#333333",
        )
        net.barnes_hut(gravity=-3000, spring_length=150)

        for nid, ninfo in data.nodes.items():
            color = get_color(ninfo["type"])
            title = f"{nid}\n{ninfo.get('description', '')}"
            net.add_node(
                nid,
                label=ninfo["name"],
                title=title,
                color=color["fill"],
                borderWidth=2,
                borderWidthSelected=3,
                font={"size": 12},
                group=ninfo["type"],
            )

        for from_id, to_id in data.edges:
            net.add_edge(from_id, to_id, color="#999999")

        return net.generate_html()

    def render_to_file(self, data: VisualizationData, output_path: str) -> str:
        """Write HTML to file. Returns output path."""
        html = self.render(data)
        with open(output_path, "w") as f:
            f.write(html)
        return output_path
