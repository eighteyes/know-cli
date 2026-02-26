"""D3.js collapsible tree visualizer.
Generates a standalone HTML file with a d3.tree() hierarchical layout.
Responsibilities: convert DAG to tree, render as interactive collapsible D3 tree, write to HTML file."""

import json
from .base import BaseVisualizer, VisualizationData
from .theme import ENTITY_COLORS


class D3TreeVisualizer(BaseVisualizer):
    """Generate a standalone HTML file with a D3 collapsible tree."""

    def _dag_to_tree(self, data):
        """Convert graph edges into a single-root tree structure.

        The graph is a DAG (nodes can have multiple parents). Strategy:
        - Build parent→children map from ALL edges (shared children appear
          under every parent with full subtrees).
        - Cycle prevention: only skip nodes already on the current path
          from root (ancestor set), not globally.
        - Nodes appearing under multiple parents get unique tree IDs
          but identical content.
        """
        children_of = {}  # parent_id → [child_id, ...]

        # edges: (from_id, to_id) where from depends_on to
        # from is PARENT, to is CHILD (from needs to, so from is higher)
        for from_id, to_id in data.edges:
            children_of.setdefault(from_id, []).append(to_id)

        # Find which nodes are children of something
        all_children = set()
        for kids in children_of.values():
            all_children.update(kids)

        # Track which nodes have multiple parents (for visual indicator)
        parent_count = {}
        for from_id, to_id in data.edges:
            parent_count[to_id] = parent_count.get(to_id, 0) + 1

        all_ids = set(data.nodes.keys())
        roots = [nid for nid in all_ids if nid not in all_children]

        counter = [0]  # unique tree IDs

        def build(nid, ancestors=frozenset()):
            ninfo = data.nodes.get(nid, {})
            colors = ENTITY_COLORS.get(ninfo.get("type", ""), ENTITY_COLORS["_reference"])
            is_cycle = nid in ancestors
            is_shared = parent_count.get(nid, 0) > 1
            counter[0] += 1
            tree_id = f"{nid}__{counter[0]}" if counter[0] > 1 else nid
            node = {
                "id": tree_id,
                "entityId": nid,
                "name": ninfo.get("name", nid.split(":")[-1]),
                "type": ninfo.get("type", ""),
                "description": ninfo.get("description", ""),
                "is_ref": ninfo.get("is_ref", False),
                "shared": is_shared,
                "fill": colors["fill"],
                "stroke": colors["stroke"],
            }
            if is_cycle:
                return node  # break cycle, no children
            kids = children_of.get(nid, [])
            if kids:
                next_ancestors = ancestors | {nid}
                node["children"] = [build(c, next_ancestors) for c in kids]
            return node

        # Also find orphans (nodes with no edges at all)
        connected = all_children | set(children_of.keys())
        orphans = [nid for nid in all_ids if nid not in connected]

        root_trees = [build(r) for r in sorted(roots)]
        orphan_trees = [build(o) for o in sorted(orphans)]
        all_trees = root_trees + orphan_trees

        if len(all_trees) == 1:
            return all_trees[0]

        # Virtual root
        return {
            "id": "__root__",
            "name": data.graph_name if isinstance(data.graph_name, str) else
                    data.graph_name.get("value", "Graph") if isinstance(data.graph_name, dict) else "Graph",
            "type": "project",
            "description": "",
            "is_ref": False,
            "fill": ENTITY_COLORS["project"]["fill"],
            "stroke": ENTITY_COLORS["project"]["stroke"],
            "children": all_trees,
        }

    def render(self, data):
        """Return standalone HTML string with embedded D3 tree."""
        tree_data = self._dag_to_tree(data)
        raw_title = data.graph_name or "Graph"
        title = raw_title.get("value", str(raw_title)) if isinstance(raw_title, dict) else str(raw_title)

        tree_json = json.dumps(tree_data, indent=2)
        return _HTML_TEMPLATE.replace("__TREE_DATA__", tree_json).replace("__TITLE__", title)

    def render_to_file(self, data, output_path):
        """Write HTML to file. Returns output path."""
        html = self.render(data)
        with open(output_path, "w") as f:
            f.write(html)
        return output_path


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #1a1a2e; color: #eee; overflow: hidden; }
  svg { display: block; width: 100vw; height: 100vh; }
  .link { fill: none; stroke: #444; stroke-width: 1.5px; }
  .node-circle { cursor: pointer; stroke-width: 2px; transition: r 0.2s; }
  .node-circle:hover { filter: brightness(1.3); }
  .node-label { font-size: 12px; fill: #ddd; pointer-events: none; }
  .node-type { font-size: 9px; fill: #888; pointer-events: none; }
  .node--collapsed .node-circle { stroke-dasharray: 3,2; }
  .node--shared .node-circle { stroke-dasharray: 4,3; opacity: 0.6; }
  .node--shared .node-label { opacity: 0.5; font-style: italic; }
  #tooltip { position: absolute; padding: 8px 12px; background: rgba(0,0,0,0.85); border-radius: 6px; font-size: 12px; pointer-events: none; display: none; max-width: 300px; border: 1px solid #444; z-index: 10; }
  #tooltip .tt-id { color: #aaa; font-size: 10px; }
  #tooltip .tt-name { font-weight: 600; margin: 2px 0; }
  #tooltip .tt-desc { color: #ccc; font-size: 11px; }
  #legend { position: absolute; top: 12px; left: 12px; background: rgba(0,0,0,0.7); padding: 10px 14px; border-radius: 8px; font-size: 12px; }
  #legend div { margin: 3px 0; display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 2px 4px; border-radius: 4px; transition: background 0.15s; }
  #legend div:hover { background: rgba(255,255,255,0.1); }
  #legend div.active { background: rgba(255,255,255,0.2); }
  #legend .swatch { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  .node-dimmed .node-circle { opacity: 0.15; }
  .node-dimmed .node-label, .node-dimmed .node-type { opacity: 0.1; }
  .link-dimmed { stroke-opacity: 0.05 !important; }
  #controls { position: absolute; bottom: 12px; left: 12px; background: rgba(0,0,0,0.7); padding: 8px 12px; border-radius: 8px; font-size: 11px; color: #aaa; }
</style>
</head>
<body>
<div id="tooltip"><div class="tt-id"></div><div class="tt-name"></div><div class="tt-desc"></div></div>
<div id="legend"></div>
<div id="controls">Click nodes to expand/collapse · Scroll to zoom · Drag to pan</div>
<svg></svg>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const treeData = __TREE_DATA__;

const svg = d3.select("svg");
const width = window.innerWidth;
const height = window.innerHeight;
svg.attr("viewBox", [0, 0, width, height]);

const g = svg.append("g").attr("transform", `translate(0, 60)`);
svg.call(d3.zoom().scaleExtent([0.1, 8]).on("zoom", (e) => g.attr("transform", e.transform)));

const root = d3.hierarchy(treeData);
root.x0 = width / 2;
root.y0 = 0;

const colWidth = 160;   // horizontal spacing per node in a row
const rowHeight = 90;    // vertical spacing between wrapped rows
const levelGap = 120;    // vertical gap between hierarchy levels
const maxPerRow = 4;     // max siblings before wrapping
const duration = 400;

const tooltip = d3.select("#tooltip");

// Custom layout: top-down, wrapping siblings into rows of maxPerRow
function layoutTree(root) {
  // First pass: compute subtree width (in columns) for each node
  root.eachAfter(d => {
    const kids = d.children || [];
    if (kids.length === 0) {
      d._cols = 1;
    } else {
      // Each child's subtree width, but wrapped into rows of maxPerRow
      d._cols = Math.min(kids.length, maxPerRow);
      // Take the max subtree width across children
      const maxChildCols = d3.max(kids, c => c._cols) || 1;
      d._cols = Math.max(d._cols * maxChildCols, 1);
    }
  });

  // Second pass: assign x,y positions
  function positionNode(node, cx, cy) {
    node.x = cx;
    node.y = cy;

    const kids = node.children || [];
    if (kids.length === 0) return;

    // Split children into rows of maxPerRow
    const rows = [];
    for (let i = 0; i < kids.length; i += maxPerRow) {
      rows.push(kids.slice(i, i + maxPerRow));
    }

    let currentY = cy + levelGap;

    for (const row of rows) {
      const totalWidth = row.length * colWidth;
      const startX = cx - totalWidth / 2 + colWidth / 2;

      row.forEach((child, i) => {
        positionNode(child, startX + i * colWidth, currentY);
      });

      // Find the max depth reached by this row's subtrees to offset next row
      let maxSubtreeDepth = 0;
      row.forEach(child => {
        let deepest = 0;
        child.each(d => { if (d.y - currentY > deepest) deepest = d.y - currentY; });
        if (deepest > maxSubtreeDepth) maxSubtreeDepth = deepest;
      });

      currentY += maxSubtreeDepth + rowHeight;
    }
  }

  positionNode(root, width / 2, 30);
}

function update(source) {
  layoutTree(root);

  const nodes = root.descendants();
  const links = root.links();

  // --- Links (elbow connectors) ---
  const link = g.selectAll("path.link")
    .data(links, d => d.target.data.id);

  const linkEnter = link.enter().insert("path", "g")
    .attr("class", "link")
    .attr("d", () => elbow({ x: source.x0, y: source.y0 }, { x: source.x0, y: source.y0 }));

  const linkUpdate = linkEnter.merge(link);
  linkUpdate.transition().duration(duration)
    .attr("d", d => elbow(d.source, d.target));

  link.exit().transition().duration(duration)
    .attr("d", () => elbow({ x: source.x, y: source.y }, { x: source.x, y: source.y }))
    .remove();

  // --- Nodes ---
  const node = g.selectAll("g.node")
    .data(nodes, d => d.data.id);

  const nodeEnter = node.enter().append("g")
    .attr("class", d => "node" + (d._children ? " node--collapsed" : "") + (d.data.shared ? " node--shared" : ""))
    .attr("transform", () => `translate(${source.x0},${source.y0})`)
    .on("click", (e, d) => {
      if (d._dragged) { d._dragged = false; return; }
      if (d.data.shared) return; // shared nodes have no children to toggle
      toggle(d); update(d);
    })
    .call(d3.drag()
      .on("start", function(e, d) {
        d._dragStartX = e.x;
        d._dragged = false;
        d3.select(this).raise();
      })
      .on("drag", function(e, d) {
        if (Math.abs(e.x - d._dragStartX) > 5) d._dragged = true;
        // Only drag horizontally
        d3.select(this).attr("transform", `translate(${e.x},${d.y})`);
        if (!d.parent || !d.parent.children) return;
        // Find which sibling slot we're closest to
        const siblings = d.parent.children;
        const myIdx = siblings.indexOf(d);
        for (let i = 0; i < siblings.length; i++) {
          if (i === myIdx) continue;
          const sib = siblings[i];
          // Swap if dragged past sibling center
          if ((myIdx < i && e.x > sib.x) || (myIdx > i && e.x < sib.x)) {
            siblings.splice(myIdx, 1);
            const newIdx = siblings.indexOf(sib);
            siblings.splice(myIdx < i ? newIdx + 1 : newIdx, 0, d);
            // Re-layout and update sibling positions (not the dragged node)
            layoutTree(root);
            g.selectAll("g.node").filter(n => n !== d)
              .transition().duration(200)
              .attr("transform", n => `translate(${n.x},${n.y})`);
            g.selectAll("path.link")
              .transition().duration(200)
              .attr("d", l => elbow(l.source, l.target));
            break;
          }
        }
      })
      .on("end", function(e, d) {
        // Snap to computed position
        layoutTree(root);
        d3.select(this).transition().duration(200)
          .attr("transform", `translate(${d.x},${d.y})`);
        g.selectAll("path.link")
          .transition().duration(200)
          .attr("d", l => elbow(l.source, l.target));
      })
    );

  nodeEnter.append("circle")
    .attr("class", "node-circle")
    .attr("r", 1e-6)
    .attr("fill", d => d.data.fill)
    .attr("stroke", d => d.data.stroke);

  nodeEnter.append("text")
    .attr("class", "node-label")
    .attr("dy", -14)
    .attr("x", 0)
    .attr("text-anchor", "middle")
    .text(d => {
      const label = d.data.name;
      return label.length > 24 ? label.slice(0, 22) + "…" : label;
    });

  nodeEnter.append("text")
    .attr("class", "node-type")
    .attr("dy", 24)
    .attr("x", 0)
    .attr("text-anchor", "middle")
    .text(d => d.data.id === "__root__" ? "" : d.data.type);

  // Tooltip
  nodeEnter.on("mouseover", (e, d) => {
    if (d.data.id === "__root__") return;
    tooltip.style("display", "block");
    tooltip.select(".tt-id").text(d.data.entityId || d.data.id);
    tooltip.select(".tt-name").text(d.data.name + (d.data.shared ? " (shared)" : ""));
    tooltip.select(".tt-desc").text(d.data.description || "");
  }).on("mousemove", (e) => {
    tooltip.style("left", (e.pageX + 12) + "px").style("top", (e.pageY - 12) + "px");
  }).on("mouseout", () => tooltip.style("display", "none"));

  const nodeUpdate = nodeEnter.merge(node);

  // Top-down: translate(x, y) where x=horizontal, y=vertical depth
  nodeUpdate.transition().duration(duration)
    .attr("transform", d => `translate(${d.x},${d.y})`)
    .attr("class", d => "node" + (d._children ? " node--collapsed" : "") + (d.data.shared ? " node--shared" : ""));

  nodeUpdate.select("circle.node-circle")
    .attr("r", d => d.data.shared ? 5 : d._children ? 10 : (d.children ? 8 : 6))
    .attr("fill", d => d._children ? d.data.stroke : d.data.fill)
    .attr("stroke", d => d.data.stroke);

  node.exit().transition().duration(duration)
    .attr("transform", () => `translate(${source.x},${source.y})`)
    .remove()
    .select("circle").attr("r", 1e-6);

  // Stash positions for transition
  nodes.forEach(d => { d.x0 = d.x; d.y0 = d.y; });
}

// Elbow connector: straight down from parent, then straight across to child
function elbow(s, d) {
  const mid = (s.y + d.y) / 2;
  return `M ${s.x} ${s.y} V ${mid} H ${d.x} V ${d.y}`;
}

function toggle(d) {
  if (d.children) {
    d._children = d.children;
    d.children = null;
  } else if (d._children) {
    d.children = d._children;
    d._children = null;
  }
}

// Start fully expanded
update(root);

// Legend with hover-to-highlight
const legend = d3.select("#legend");
const seenTypes = new Map();
root.descendants().forEach(d => {
  if (d.data.id !== "__root__" && !seenTypes.has(d.data.type)) {
    seenTypes.set(d.data.type, d.data);
  }
});

let activeType = null;
function highlightType(type) {
  activeType = type;
  if (!type) {
    g.selectAll("g.node").classed("node-dimmed", false);
    g.selectAll("path.link").classed("link-dimmed", false);
    legend.selectAll("div").classed("active", false);
    return;
  }
  g.selectAll("g.node").classed("node-dimmed", d => d.data.type !== type);
  g.selectAll("path.link").classed("link-dimmed", d =>
    d.source.data.type !== type && d.target.data.type !== type
  );
}

seenTypes.forEach((ndata, type) => {
  const row = legend.append("div")
    .on("mouseenter", () => highlightType(type))
    .on("mouseleave", () => { if (activeType === type) highlightType(null); })
    .on("click", () => {
      if (activeType === type) { highlightType(null); }
      else { highlightType(type); legend.selectAll("div").classed("active", false); row.classed("active", true); }
    });
  row.append("span").attr("class", "swatch").style("background", ndata.fill).style("border", `1px solid ${ndata.stroke}`);
  row.append("span").text(type);
});
</script>
</body>
</html>
"""
