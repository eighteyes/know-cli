"""D3.js force-directed graph visualizer.
Generates a standalone HTML file with an embedded D3 force graph.
Responsibilities: render graph data as interactive D3 visualization, write to HTML file."""

import json
from .base import BaseVisualizer, VisualizationData
from .theme import ENTITY_COLORS


class D3Visualizer(BaseVisualizer):
    """Generate a standalone HTML file with a D3 force-directed graph."""

    def render(self, data: VisualizationData) -> str:
        """Return standalone HTML string with embedded D3 visualization."""
        nodes = []
        for nid, ninfo in data.nodes.items():
            colors = ENTITY_COLORS.get(ninfo["type"], ENTITY_COLORS["_reference"])
            nodes.append({
                "id": nid,
                "label": ninfo["name"],
                "type": ninfo["type"],
                "description": ninfo.get("description", ""),
                "is_ref": ninfo.get("is_ref", False),
                "fill": colors["fill"],
                "stroke": colors["stroke"],
            })

        links = [{"source": f, "target": t} for f, t in data.edges]
        raw_title = data.graph_name or "Graph"
        title = raw_title.get("value", str(raw_title)) if isinstance(raw_title, dict) else str(raw_title)

        graph_json = json.dumps({"nodes": nodes, "links": links}, indent=2)

        return _HTML_TEMPLATE.replace("__GRAPH_DATA__", graph_json).replace("__TITLE__", title)

    def render_to_file(self, data: VisualizationData, output_path: str) -> str:
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
  .link { stroke-opacity: 0.4; }
  .link:hover { stroke-opacity: 0.9; }
  .node-label { font-size: 11px; pointer-events: none; fill: #ddd; text-anchor: middle; dominant-baseline: central; }
  #tooltip { position: absolute; padding: 8px 12px; background: rgba(0,0,0,0.85); border-radius: 6px; font-size: 12px; pointer-events: none; display: none; max-width: 300px; border: 1px solid #444; }
  #tooltip .tt-id { color: #aaa; font-size: 10px; }
  #tooltip .tt-name { font-weight: 600; margin: 2px 0; }
  #tooltip .tt-desc { color: #ccc; font-size: 11px; }
  #legend { position: absolute; top: 12px; left: 12px; background: rgba(0,0,0,0.7); padding: 10px 14px; border-radius: 8px; font-size: 12px; }
  #legend div { margin: 3px 0; display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 2px 4px; border-radius: 4px; transition: background 0.15s; }
  #legend div:hover { background: rgba(255,255,255,0.1); }
  #legend div.active { background: rgba(255,255,255,0.2); }
  #legend .swatch { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  .node-dimmed circle { opacity: 0.15; }
  .node-dimmed text { opacity: 0.1; }
  .link-dimmed { stroke-opacity: 0.05 !important; }
  #controls { position: absolute; bottom: 12px; left: 12px; background: rgba(0,0,0,0.7); padding: 8px 12px; border-radius: 8px; font-size: 11px; color: #aaa; }
</style>
</head>
<body>
<div id="tooltip"><div class="tt-id"></div><div class="tt-name"></div><div class="tt-desc"></div></div>
<div id="legend"></div>
<div id="controls">Scroll to zoom · Drag nodes · Click to pin/unpin</div>
<svg></svg>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = __GRAPH_DATA__;

const svg = d3.select("svg");
const width = window.innerWidth;
const height = window.innerHeight;
svg.attr("viewBox", [0, 0, width, height]);

const g = svg.append("g");

// Zoom
svg.call(d3.zoom().scaleExtent([0.1, 8]).on("zoom", (e) => g.attr("transform", e.transform)));

// Compute topological depth (roots = 0, children = parent + 1)
// Edges go source → target (source depends_on target), so roots have no outgoing edges
// and leaves are depended on by everything. Reverse: parents point to children.
const childrenOf = new Map();  // parent → [child]
const parentCount = new Map(); // child → number of parents
data.nodes.forEach(n => { childrenOf.set(n.id, []); parentCount.set(n.id, 0); });
// In the graph, source depends_on target, so target is the parent (higher in hierarchy)
data.links.forEach(l => {
  const src = typeof l.source === "object" ? l.source.id : l.source;
  const tgt = typeof l.target === "object" ? l.target.id : l.target;
  // tgt is parent, src is child
  if (childrenOf.has(tgt)) childrenOf.get(tgt).push(src);
  parentCount.set(src, (parentCount.get(src) || 0) + 1);
});

// BFS from roots (nodes with no parents)
const depth = new Map();
const queue = [];
data.nodes.forEach(n => {
  if ((parentCount.get(n.id) || 0) === 0) { depth.set(n.id, 0); queue.push(n.id); }
});
while (queue.length) {
  const cur = queue.shift();
  const d = depth.get(cur);
  for (const child of (childrenOf.get(cur) || [])) {
    const prev = depth.get(child);
    if (prev === undefined || d + 1 > prev) { depth.set(child, d + 1); }
    // Only enqueue once all parents processed (simple: always push, depth is max)
    queue.push(child);
  }
}
// Fallback for disconnected nodes
data.nodes.forEach(n => { if (!depth.has(n.id)) depth.set(n.id, 0); });

const maxDepth = Math.max(...depth.values(), 1);

// Count siblings at each depth for horizontal spread
const depthBuckets = new Map();
data.nodes.forEach(n => {
  const d = depth.get(n.id);
  if (!depthBuckets.has(d)) depthBuckets.set(d, []);
  depthBuckets.get(d).push(n.id);
});

// Seed initial positions: top-left → bottom-right diagonal
const margin = 80;
const usableW = width - margin * 2;
const usableH = height - margin * 2;

data.nodes.forEach(n => {
  const d = depth.get(n.id);
  const bucket = depthBuckets.get(d);
  const idx = bucket.indexOf(n.id);
  const count = bucket.length;

  // Diagonal progress based on depth
  const t = maxDepth > 0 ? d / maxDepth : 0;

  // Spread siblings perpendicular to the diagonal
  const spread = count > 1 ? (idx / (count - 1) - 0.5) : 0;
  const perpSpread = 120;

  n.x = margin + (1 - t) * usableW + spread * perpSpread;
  n.y = margin + (1 - t) * usableH + spread * perpSpread * 0.3;
});

// Simulation with diagonal positioning force
const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.links).id(d => d.id).distance(100).strength(0.3))
  .force("charge", d3.forceManyBody().strength(-300))
  .force("collision", d3.forceCollide().radius(30))
  .force("diagonal", () => {
    // Gently pull nodes toward their hierarchical position
    const alpha = simulation.alpha();
    const strength = 0.15;
    data.nodes.forEach(n => {
      const d = depth.get(n.id);
      const bucket = depthBuckets.get(d);
      const idx = bucket.indexOf(n.id);
      const count = bucket.length;
      const t = maxDepth > 0 ? d / maxDepth : 0;
      const spread = count > 1 ? (idx / (count - 1) - 0.5) : 0;
      const perpSpread = 120;
      const tx = margin + (1 - t) * usableW + spread * perpSpread;
      const ty = margin + (1 - t) * usableH + spread * perpSpread * 0.3;
      n.vx += (tx - n.x) * strength * alpha;
      n.vy += (ty - n.y) * strength * alpha;
    });
  });

// Arrow markers
const types = [...new Set(data.nodes.map(n => n.type))];
g.append("defs").selectAll("marker")
  .data(types).join("marker")
  .attr("id", d => `arrow-${d}`)
  .attr("viewBox", "0 -5 10 10")
  .attr("refX", 22).attr("refY", 0)
  .attr("markerWidth", 6).attr("markerHeight", 6)
  .attr("orient", "auto")
  .append("path").attr("d", "M0,-5L10,0L0,5")
  .attr("fill", "#666");

// Links
const link = g.append("g").selectAll("line")
  .data(data.links).join("line")
  .attr("class", "link")
  .attr("stroke", "#555")
  .attr("stroke-width", 1.5)
  .attr("marker-end", d => {
    const src = data.nodes.find(n => n.id === (typeof d.source === "object" ? d.source.id : d.source));
    return src ? `url(#arrow-${src.type})` : "";
  });

// Nodes
const node = g.append("g").selectAll("g")
  .data(data.nodes).join("g")
  .call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended));

node.append("circle")
  .attr("r", d => d.is_ref ? 8 : 14)
  .attr("fill", d => d.fill)
  .attr("stroke", d => d.stroke)
  .attr("stroke-width", 2)
  .style("cursor", "pointer");

node.append("text")
  .attr("class", "node-label")
  .attr("dy", d => (d.is_ref ? 8 : 14) + 14)
  .text(d => d.label.length > 20 ? d.label.slice(0, 18) + "…" : d.label);

// Tooltip
const tooltip = d3.select("#tooltip");
node.on("mouseover", (e, d) => {
  tooltip.style("display", "block");
  tooltip.select(".tt-id").text(d.id);
  tooltip.select(".tt-name").text(d.label);
  tooltip.select(".tt-desc").text(d.description || "");
}).on("mousemove", (e) => {
  tooltip.style("left", (e.pageX + 12) + "px").style("top", (e.pageY - 12) + "px");
}).on("mouseout", () => tooltip.style("display", "none"));

// Click to pin/unpin
node.on("click", (e, d) => {
  if (d.fx != null) { d.fx = null; d.fy = null; }
  else { d.fx = d.x; d.fy = d.y; }
});

// Tick
simulation.on("tick", () => {
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${d.x},${d.y})`);
});

// Drag
function dragstarted(e, d) { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
function dragged(e, d) { d.fx = e.x; d.fy = e.y; }
function dragended(e, d) { if (!e.active) simulation.alphaTarget(0); }

// Legend with hover-to-highlight
const legend = d3.select("#legend");
const seen = new Map();
data.nodes.forEach(n => { if (!seen.has(n.type)) seen.set(n.type, n); });
let activeType = null;

function highlightType(type) {
  activeType = type;
  if (!type) {
    node.classed("node-dimmed", false);
    link.classed("link-dimmed", false);
    legend.selectAll("div").classed("active", false);
    return;
  }
  node.classed("node-dimmed", d => d.type !== type);
  link.classed("link-dimmed", d => {
    const s = typeof d.source === "object" ? d.source : data.nodes.find(n => n.id === d.source);
    const t = typeof d.target === "object" ? d.target : data.nodes.find(n => n.id === d.target);
    return (!s || s.type !== type) && (!t || t.type !== type);
  });
}

seen.forEach((n, type) => {
  const row = legend.append("div")
    .on("mouseenter", () => highlightType(type))
    .on("mouseleave", () => { if (activeType === type) highlightType(null); })
    .on("click", () => {
      if (activeType === type) { highlightType(null); }
      else { highlightType(type); legend.selectAll("div").classed("active", false); row.classed("active", true); }
    });
  row.append("span").attr("class", "swatch").style("background", n.fill).style("border", `1px solid ${n.stroke}`);
  row.append("span").text(type);
});
</script>
</body>
</html>
"""
