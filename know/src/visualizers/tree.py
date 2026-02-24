"""Rich Tree visualizer for terminal output."""

from rich.tree import Tree
from rich.text import Text
from .base import BaseVisualizer, VisualizationData
from .theme import get_color


class RichTreeVisualizer(BaseVisualizer):
    """Render graph as a rich.Tree printed to the terminal."""

    def render(self, data: VisualizationData) -> Tree:
        """Build and return a rich.Tree object."""
        title = data.graph_name or "Graph"
        root = Tree(f"[bold]{title}[/bold]")

        if not data.nodes:
            root.add("[dim]No nodes to display[/dim]")
            return root

        # Build adjacency: from → [to] (dependencies)
        fwd = {}
        rev = {}
        for f, t in data.edges:
            fwd.setdefault(f, []).append(t)
            rev.setdefault(t, []).append(f)

        # Find root nodes (no incoming edges within the data set)
        roots = [nid for nid in data.nodes if nid not in rev]
        if not roots:
            # All nodes have incoming edges — pick all as roots (cycle)
            roots = sorted(data.nodes.keys())

        # Sort roots by type then name
        roots.sort(key=lambda x: (data.nodes[x]["type"], x))

        visited = set()

        def add_subtree(parent_tree, node_id, depth=0):
            if node_id in visited:
                parent_tree.add(f"[dim]{node_id} (↻)[/dim]")
                return
            visited.add(node_id)

            ninfo = data.nodes.get(node_id, {})
            ntype = ninfo.get("type", "?")
            nname = ninfo.get("name", node_id)
            style = get_color(ntype)["rich_style"]
            is_ref = ninfo.get("is_ref", False)

            phase = ninfo.get("phase", "")
            status = ninfo.get("status", "")

            label = Text()
            if status == "delivered":
                label.append("✓ ", style="green bold")
            label.append(f"[{ntype}] ", style="dim")
            label.append(nname, style=style if not is_ref else "dim italic")
            if node_id != f"{ntype}:{nname}":
                label.append(f"  ({node_id})", style="dim")
            if phase:
                label.append(f"  phase:{phase}", style="dim cyan")
                if status and status != "delivered":
                    label.append(f" ({status})", style="dim yellow")

            branch = parent_tree.add(label)

            # Add children (dependencies of this node)
            children = sorted(fwd.get(node_id, []))
            for child in children:
                if child in data.nodes:
                    add_subtree(branch, child, depth + 1)

        # Group by entity type
        type_order = sorted(data.clusters.keys())
        if self.entity_focus:
            # Focused view: just render from the focus entity
            focus_info = data.nodes.get(self.entity_focus, {})
            ftype = focus_info.get("type", "?")
            fname = focus_info.get("name", self.entity_focus)
            style = get_color(ftype)["rich_style"]
            fphase = focus_info.get("phase", "")
            fstatus = focus_info.get("status", "")
            check = "[green bold]✓[/green bold] " if fstatus == "delivered" else ""
            phase_tag = f"  [dim cyan]phase:{fphase}[/dim cyan]" if fphase else ""
            status_tag = f" [dim yellow]({fstatus})[/dim yellow]" if fstatus and fstatus != "delivered" else ""
            root = Tree(f"{check}[{style}]{self.entity_focus}[/{style}] — {fname}{phase_tag}{status_tag}")

            # Show dependents (who depends on me)
            dependents = sorted(rev.get(self.entity_focus, []))
            if dependents:
                dep_branch = root.add("[bold]Used by[/bold]")
                for d in dependents:
                    if d in data.nodes:
                        di = data.nodes[d]
                        ds = get_color(di["type"])["rich_style"]
                        dep_branch.add(f"[{ds}]{d}[/{ds}]")

            # Show dependencies (what I depend on)
            deps = sorted(fwd.get(self.entity_focus, []))
            if deps:
                uses_branch = root.add("[bold]Depends on[/bold]")
                for d in deps:
                    if d in data.nodes:
                        visited.clear()
                        visited.add(self.entity_focus)
                        add_subtree(uses_branch, d)
        else:
            # Full tree grouped by type
            for etype in type_order:
                type_nodes = sorted(data.clusters[etype])
                # Only show root nodes in the type group
                type_roots = [n for n in type_nodes if n in roots]
                if not type_roots:
                    continue
                style = get_color(etype)["rich_style"]
                type_branch = root.add(f"[{style}]{etype}[/{style}] ({len(type_nodes)})")
                for nid in type_roots:
                    add_subtree(type_branch, nid)

        return root
