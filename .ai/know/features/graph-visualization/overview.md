# Feature: Graph Visualization

## User Request

Visualize the spec-graph and code-graph with interactive, explorable views. Enable quick understanding of graph structure, dependencies, and relationships through visual representations.

## Context

Currently, know provides text-based output for graph exploration (`know list`, `know uses`, etc.). Visual representation would make it easier to:
- Understand overall graph structure
- Identify dependency chains
- Find gaps and issues
- Present to stakeholders
- Debug complex graphs

## Requirements

### Core Functionality

1. **Multiple Output Formats**
   - Mermaid diagram (markdown-compatible, GitHub/VSCode preview)
   - HTML with interactive graph (vis.js or cytoscape.js)
   - DOT/Graphviz format (PNG/SVG generation)
   - JSON for custom rendering

2. **Filtering & Focus**
   - Show specific entity types only
   - Start from specific node and show N levels deep
   - Filter by phase
   - Hide/show references
   - Highlight specific paths

3. **Layout Options**
   - Hierarchical (top-down, left-right)
   - Force-directed
   - Circular
   - Tree layout

4. **Interactive Features** (HTML output)
   - Click to explore node details
   - Hover for descriptions
   - Zoom/pan
   - Search/filter
   - Collapse/expand sections
   - Highlight dependency paths

5. **Web Server** (Optional)
   - Serve visualization locally (localhost:8080)
   - Auto-refresh on graph changes
   - Multiple graph comparison view
   - Export/screenshot capability

### Command Interface

```bash
# Generate visualizations
know viz                              # Default: HTML output, open in browser
know viz --format mermaid             # Generate Mermaid diagram
know viz --format dot                 # Generate Graphviz DOT file
know viz --format html -o graph.html  # Generate HTML file

# Filtering
know viz --type feature,action        # Only show features and actions
know viz --from feature:auth --depth 3  # Show 3 levels from auth feature
know viz --phase I                    # Only show Phase I entities

# Layout
know viz --layout hierarchical        # Top-down hierarchy
know viz --layout force               # Force-directed layout
know viz --layout circular            # Circular layout

# Web server mode
know viz --serve                      # Start web server at localhost:8080
know viz --serve --port 3000 --watch  # Auto-reload on changes

# Multiple graphs
know viz --compare .ai/spec-graph.json .ai/code-graph.json
```

## Use Cases

### 1. Architecture Review
Stakeholder wants to see system structure:
```bash
know viz --type feature,component --output architecture.html
# Opens interactive diagram showing features and their components
```

### 2. Dependency Analysis
Find what depends on a specific component:
```bash
know viz --from component:auth --highlight-paths
# Shows all paths through auth component
```

### 3. Gap Identification
Visualize incomplete dependencies:
```bash
know viz --show-gaps
# Highlights missing connections in red
```

### 4. Phase Planning
See what's in each phase:
```bash
know viz --group-by phase --layout hierarchical
# Groups entities by phase with clear boundaries
```

### 5. Live Development
Keep visualization open while building:
```bash
know viz --serve --watch
# Browser auto-refreshes when graph changes
```

## Success Criteria

- [ ] Generate Mermaid diagrams viewable in GitHub/VSCode
- [ ] Generate interactive HTML with zoom/pan/search
- [ ] Support filtering by entity type, phase, depth
- [ ] Layout options: hierarchical, force-directed, circular
- [ ] Click nodes to see details (name, description, dependencies)
- [ ] Highlight dependency paths
- [ ] Optional web server with auto-reload
- [ ] Export capability (PNG, SVG, PDF)
- [ ] Documentation with examples
- [ ] Works with both spec-graph and code-graph

## Technical Constraints

- Keep dependencies minimal (prefer stdlib)
- HTML output should work offline (bundled JS/CSS)
- Large graphs (1000+ nodes) should remain performant
- Generated files should be git-friendly (readable diffs)
- Support both Python 3.8+ environments

## Visualization Libraries

### Option 1: Mermaid (Simplest)
**Pros**: Markdown-compatible, no dependencies, GitHub preview
**Cons**: Limited interactivity, layout control
**Implementation**: Pure Python, generate mermaid syntax

### Option 2: vis.js (Recommended for HTML)
**Pros**: Interactive, good performance, mature
**Cons**: Requires bundling JS
**Implementation**: Generate HTML with vis-network CDN

### Option 3: Cytoscape.js
**Pros**: Very powerful, great layouts, biological network focus
**Cons**: Larger bundle, steeper learning curve
**Implementation**: Generate HTML with cytoscape CDN

### Option 4: D3.js
**Pros**: Maximum flexibility, beautiful
**Cons**: More complex implementation, harder to maintain
**Implementation**: Generate HTML with custom D3 code

### Option 5: Graphviz/DOT
**Pros**: Production-quality output, many formats
**Cons**: Requires graphviz installation
**Implementation**: Generate .dot file, shell out to graphviz

**Recommendation**: Implement Mermaid + vis.js
- Mermaid for quick markdown previews
- vis.js for interactive HTML
- DOT as optional (if graphviz detected)

## Out of Scope (Future Enhancements)

- Real-time collaborative viewing
- Graph editing via UI
- Custom themes/styling
- 3D visualization
- Animation of changes over time
- Integration with other viz tools (Neo4j, etc.)
- Cloud hosting of visualizations

## Implementation Phases

### Phase 1: Mermaid Output (2-3 hours)
- Generate mermaid flowchart syntax
- Support entity filtering
- Basic node styling

### Phase 2: HTML Interactive (4-6 hours)
- Generate standalone HTML with vis.js
- Interactive zoom/pan
- Node details on click
- Search/filter UI

### Phase 3: Advanced Features (3-4 hours)
- Layout options
- Path highlighting
- Phase grouping
- Gap visualization

### Phase 4: Web Server (2-3 hours)
- Simple HTTP server
- Auto-reload on file changes
- Multiple graph comparison

**Total Estimate**: 11-16 hours

## Notes

- Start with Mermaid (quick win, useful immediately)
- vis.js for interactive use cases
- Web server for active development workflow
- DOT output for production-quality renders
