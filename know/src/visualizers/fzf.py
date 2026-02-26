"""fzf-based fuzzy picker for graph entities."""

from .base import BaseVisualizer, VisualizationData
from .theme import get_color

try:
    from iterfzf import iterfzf
    HAS_ITERFZF = True
except ImportError:
    HAS_ITERFZF = False


class FzfPicker(BaseVisualizer):
    """Interactive fzf picker that returns a selected entity ID."""

    @classmethod
    def check_available(cls):
        if not HAS_ITERFZF:
            return False, "pip install iterfzf  (also needs fzf binary: apt install fzf)"
        return True, ""

    def render(self, data: VisualizationData) -> str:
        """Launch fzf and return the selected entity ID, or empty string."""
        if not HAS_ITERFZF:
            raise RuntimeError("iterfzf not installed")

        # Build lines: "type:key  — display name  (description)"
        lines = []
        for nid in sorted(data.nodes.keys()):
            ninfo = data.nodes[nid]
            desc = ninfo.get("description", "")
            label = ninfo["name"]
            line = f"{nid}  — {label}"
            if desc:
                short_desc = desc[:60] + "..." if len(desc) > 60 else desc
                line += f"  ({short_desc})"
            lines.append(line)

        if not lines:
            return ""

        selected = iterfzf(lines, prompt="Select entity> ", multi=False)
        if not selected:
            return ""

        # Extract entity ID (everything before first "  —")
        return selected.split("  —")[0].strip()
