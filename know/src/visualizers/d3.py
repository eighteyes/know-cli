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
  #action-bar { position: absolute; top: 12px; right: 12px; display: none; flex-direction: column; gap: 6px; }
  #action-bar button { background: rgba(60,60,120,0.9); color: #eee; border: 1px solid #666; padding: 8px 16px; border-radius: 6px; font-size: 13px; cursor: pointer; font-family: inherit; transition: background 0.15s; text-align: left; }
  #action-bar button:hover { background: rgba(80,80,160,0.95); }
  #release-others-btn { display: none; background: rgba(100,80,40,0.9) !important; }
  #release-others-btn:hover { background: rgba(140,110,50,0.95) !important; }
  #release-btn { display: none; background: rgba(120,40,40,0.9) !important; }
  #release-btn:hover { background: rgba(160,50,50,0.95) !important; }
  .node-selected circle { stroke-width: 4px !important; filter: brightness(1.4); }
  .node-gathered circle { stroke-dasharray: 3,2; }
</style>
</head>
<body>
<div id="tooltip"><div class="tt-id"></div><div class="tt-name"></div><div class="tt-desc"></div></div>
<div id="legend"></div>
<div id="controls">Scroll to zoom · Drag nodes · Click to select · Double-click to pin/unpin</div>
<div id="action-bar">
  <button id="gather-btn">Gather neighbors</button>
  <button id="fan-btn">Fan whole graph</button>
  <button id="release-others-btn">Release others</button>
  <button id="release-btn">Release all</button>
</div>
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

  // Spread siblings perpendicular to the diagonal, scaled to bucket size
  const spread = count > 1 ? (idx / (count - 1) - 0.5) : 0;
  const perpSpread = Math.max(120, count * 25);

  n.x = margin + (1 - t) * usableW + spread * perpSpread;
  n.y = margin + (1 - t) * usableH + spread * perpSpread * 0.5;
});

// Scale forces to graph size
const nodeCount = data.nodes.length;
const chargeStrength = nodeCount > 200 ? -150 : nodeCount > 50 ? -250 : -400;
const linkDist = nodeCount > 200 ? 60 : nodeCount > 50 ? 80 : 100;
const diagStrength = nodeCount > 200 ? 0.08 : 0.15;

// Simulation with diagonal positioning force
const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.links).id(d => d.id).distance(linkDist).strength(0.3))
  .force("charge", d3.forceManyBody().strength(chargeStrength))
  .force("collision", d3.forceCollide().radius(nodeCount > 100 ? 18 : 30))
  .force("diagonal", () => {
    // Gently pull nodes toward their hierarchical position
    const alpha = simulation.alpha();
    const strength = diagStrength;
    data.nodes.forEach(n => {
      const d = depth.get(n.id);
      const bucket = depthBuckets.get(d);
      const idx = bucket.indexOf(n.id);
      const count = bucket.length;
      const t = maxDepth > 0 ? d / maxDepth : 0;
      const spread = count > 1 ? (idx / (count - 1) - 0.5) : 0;
      const perpSpread = Math.max(120, count * 25);
      const tx = margin + (1 - t) * usableW + spread * perpSpread;
      const ty = margin + (1 - t) * usableH + spread * perpSpread * 0.5;
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

const baseR = nodeCount > 200 ? 6 : nodeCount > 50 ? 10 : 14;
const refR = nodeCount > 200 ? 4 : nodeCount > 50 ? 6 : 8;
const labelSize = nodeCount > 200 ? 8 : nodeCount > 50 ? 10 : 11;

node.append("circle")
  .attr("r", d => d.is_ref ? refR : baseR)
  .attr("fill", d => d.fill)
  .attr("stroke", d => d.stroke)
  .attr("stroke-width", nodeCount > 200 ? 1 : 2)
  .style("cursor", "pointer");

node.append("text")
  .attr("class", "node-label")
  .attr("dy", d => (d.is_ref ? refR : baseR) + 12)
  .style("font-size", labelSize + "px")
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

// Build directional adjacency
// source depends_on target → source is parent, target is child
const parents = new Map();   // id → Set of parent ids (who depends on me)
const children = new Map();  // id → Set of child ids (what I depend on)
const neighbors = new Map(); // id → Set of all connected ids
data.nodes.forEach(n => {
  parents.set(n.id, new Set());
  children.set(n.id, new Set());
  neighbors.set(n.id, new Set());
});
data.links.forEach(l => {
  const sid = typeof l.source === "object" ? l.source.id : l.source;
  const tid = typeof l.target === "object" ? l.target.id : l.target;
  // sid depends_on tid → sid is parent of tid
  children.get(sid)?.add(tid);
  parents.get(tid)?.add(sid);
  neighbors.get(sid)?.add(tid);
  neighbors.get(tid)?.add(sid);
});

// Node lookup by id
const nodeById = new Map();
data.nodes.forEach(n => nodeById.set(n.id, n));

// Selection state
let selectedNode = null;
const actionBar = d3.select("#action-bar");
const gatherBtn = d3.select("#gather-btn");
const fanBtn = d3.select("#fan-btn");
const releaseBtn = d3.select("#release-btn");
const releaseOthersBtn = d3.select("#release-others-btn");

function showActions(d) {
  const nbrCount = neighbors.get(d.id)?.size || 0;
  gatherBtn.text(`Gather ${nbrCount} neighbors`);
  actionBar.style("display", "flex");
}

function hideActions() {
  actionBar.style("display", "none");
}

// Click to select, double-click to pin/unpin
node.on("click", (e, d) => {
  e.stopPropagation();
  if (selectedNode === d) {
    selectedNode = null;
    node.classed("node-selected", false);
    hideActions();
  } else {
    selectedNode = d;
    node.classed("node-selected", n => n === d);
    showActions(d);
  }
}).on("dblclick", (e, d) => {
  e.stopPropagation();
  if (d.fx != null) { d.fx = null; d.fy = null; }
  else { d.fx = d.x; d.fy = d.y; }
});

svg.on("click", () => {
  selectedNode = null;
  node.classed("node-selected", false);
  hideActions();
});

// Directional BFS: walk only parent or child edges
function directedBfs(startId, adjMap) {
  const dist = new Map();
  dist.set(startId, 0);
  const queue = [startId];
  let head = 0;
  while (head < queue.length) {
    const cur = queue[head++];
    const d = dist.get(cur);
    for (const nbr of (adjMap.get(cur) || [])) {
      if (!dist.has(nbr)) {
        dist.set(nbr, d + 1);
        queue.push(nbr);
      }
    }
  }
  return dist;
}

// Place a column of nodes, returns actual height used
function placeColumn(ids, x, minGap) {
  const gap = Math.max(minGap, 32);
  const totalH = (ids.length - 1) * gap;
  const startY = height / 2 - totalH / 2;
  ids.forEach((nid, i) => {
    const target = nodeById.get(nid);
    if (target) {
      target.fx = x;
      target.fy = startY + i * gap;
    }
  });
}

// Gather: immediate neighbors in a ring
gatherBtn.on("click", () => {
  if (!selectedNode) return;
  const d = selectedNode;
  d.fx = d.x; d.fy = d.y;

  const nbrs = neighbors.get(d.id);
  if (!nbrs || nbrs.size === 0) return;

  const nbrArray = [...nbrs];
  const radius = Math.max(80, nbrArray.length * 18);

  nbrArray.forEach((nid, i) => {
    const angle = (2 * Math.PI * i) / nbrArray.length - Math.PI / 2;
    const target = nodeById.get(nid);
    if (target) {
      target.fx = d.x + radius * Math.cos(angle);
      target.fy = d.y + radius * Math.sin(angle);
    }
  });

  node.classed("node-gathered", n => nbrs.has(n.id));
  simulation.alpha(0.3).restart();
  releaseBtn.style("display", "block");
  releaseOthersBtn.style("display", "block");
});

// Fan: left = up the chain (parents), right = down the chain (children)
fanBtn.on("click", () => {
  if (!selectedNode) return;
  const d = selectedNode;

  // BFS up (parents) and down (children) separately
  // parents map: id → Set of ids that DEPEND ON this id (higher in hierarchy)
  // children map: id → Set of ids that this id DEPENDS ON (lower in hierarchy)
  const upDist = directedBfs(d.id, parents);    // who depends on me (ancestors)
  const downDist = directedBfs(d.id, children);  // what I depend on (descendants)

  // Remove self from both
  upDist.delete(d.id);
  downDist.delete(d.id);

  // Remove duplicates: if a node is in both, keep the shorter path
  for (const [nid, dd] of downDist) {
    if (upDist.has(nid) && upDist.get(nid) <= dd) {
      downDist.delete(nid);
    } else if (upDist.has(nid)) {
      upDist.delete(nid);
    }
  }

  // Group by distance
  const leftCols = new Map();  // distance → [ids] going left (parents)
  const rightCols = new Map(); // distance → [ids] going right (children)
  upDist.forEach((dd, nid) => {
    if (!leftCols.has(dd)) leftCols.set(dd, []);
    leftCols.get(dd).push(nid);
  });
  downDist.forEach((dd, nid) => {
    if (!rightCols.has(dd)) rightCols.set(dd, []);
    rightCols.get(dd).push(nid);
  });

  const maxLeft = leftCols.size ? Math.max(...leftCols.keys()) : 0;
  const maxRight = rightCols.size ? Math.max(...rightCols.keys()) : 0;
  const colGap = 180;

  // Center column for selected node
  const centerX = width / 2;
  d.fx = centerX;
  d.fy = height / 2;

  // Place parent columns to the LEFT
  leftCols.forEach((ids, dist) => {
    const x = centerX - dist * colGap;
    placeColumn(ids, x, Math.min(36, (height - 60) / ids.length));
  });

  // Place child columns to the RIGHT
  rightCols.forEach((ids, dist) => {
    const x = centerX + dist * colGap;
    placeColumn(ids, x, Math.min(36, (height - 60) / ids.length));
  });

  // Unreachable nodes — far right
  const placed = new Set([d.id, ...upDist.keys(), ...downDist.keys()]);
  const unreachable = data.nodes.filter(n => !placed.has(n.id));
  if (unreachable.length) {
    const x = centerX + (maxRight + 2) * colGap;
    placeColumn(unreachable.map(n => n.id), x, Math.min(20, (height - 60) / unreachable.length));
  }

  node.classed("node-gathered", n => n !== d && placed.has(n.id));
  simulation.alpha(0.3).restart();
  releaseBtn.style("display", "block");
  releaseOthersBtn.style("display", "block");
});

// Release all
releaseBtn.on("click", () => {
  data.nodes.forEach(n => { n.fx = null; n.fy = null; });
  node.classed("node-gathered", false);
  node.classed("node-selected", false);
  selectedNode = null;
  hideActions();
  simulation.alpha(0.5).restart();
});

// Release others (keep selected node pinned)
releaseOthersBtn.on("click", () => {
  data.nodes.forEach(n => {
    if (n !== selectedNode) { n.fx = null; n.fy = null; }
  });
  node.classed("node-gathered", false);
  releaseOthersBtn.style("display", "none");
  simulation.alpha(0.5).restart();
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
