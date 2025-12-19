# Implementation Plan: Graph Visualization

## Quick Prototype Strategy

**Goal**: Get something working quickly to demonstrate value.

**Approach**: Start with Mermaid (simplest), then add HTML interactive viewer.

---

## Phase 1: Mermaid Generator (2-3 hours)

### Create `know/src/visualizers/mermaid.py`

```python
class MermaidGenerator:
    """Generate Mermaid flowchart from graph."""

    def __init__(self, graph_manager):
        self.graph = graph_manager

    def generate(self, entity_types=None, depth=None, from_entity=None):
        """Generate Mermaid diagram."""
        output = ["flowchart TD"]

        # Get entities to include
        entities = self._filter_entities(entity_types, depth, from_entity)

        # Add nodes
        for entity_id in entities:
            output.append(self._generate_node(entity_id))

        # Add edges
        graph_data = self.graph.load()
        for from_id, to_ids in graph_data.get('graph', {}).items():
            if from_id in entities:
                for to_id in to_ids.get('depends_on', []):
                    if to_id in entities:
                        output.append(f"    {self._clean_id(from_id)} --> {self._clean_id(to_id)}")

        return "\n".join(output)

    def _generate_node(self, entity_id):
        """Generate Mermaid node with styling."""
        entity_type, name = entity_id.split(':', 1)
        clean_id = self._clean_id(entity_id)

        # Get entity details
        graph_data = self.graph.load()
        entity_data = graph_data.get('entities', {}).get(entity_type, {}).get(name, {})
        display_name = entity_data.get('name', name)

        # Style based on type
        style = self._get_style(entity_type)

        return f'    {clean_id}["{display_name}"]:::{style}'

    def _get_style(self, entity_type):
        """Get CSS class for entity type."""
        styles = {
            'feature': 'feature',
            'action': 'action',
            'component': 'component',
            'user': 'user',
            'objective': 'objective'
        }
        return styles.get(entity_type, 'default')

    def _clean_id(self, entity_id):
        """Convert entity ID to valid Mermaid identifier."""
        return entity_id.replace(':', '_').replace('-', '_')

    def _filter_entities(self, entity_types, depth, from_entity):
        """Filter entities based on criteria."""
        # Implementation here
        pass
```

### Add Mermaid Styles

```python
def generate_with_styles(self):
    """Generate Mermaid with custom styling."""
    diagram = self.generate()

    styles = """
    classDef feature fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef action fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef component fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef user fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef objective fill:#fff3e0,stroke:#e65100,stroke-width:2px
    """

    return diagram + "\n" + styles
```

### Add CLI Command (`know/know.py`)

```python
@cli.command()
@click.option('--format', '-f', default='mermaid',
              type=click.Choice(['mermaid', 'html', 'dot', 'json']),
              help='Output format')
@click.option('--output', '-o', default=None,
              help='Output file (default: stdout)')
@click.option('--type', 'entity_types', default=None,
              help='Comma-separated entity types to include')
@click.option('--from', 'from_entity', default=None,
              help='Start from specific entity')
@click.option('--depth', default=None, type=int,
              help='Max depth from starting entity')
@click.option('--serve', is_flag=True,
              help='Start web server to view visualization')
@click.option('--port', default=8080, type=int,
              help='Port for web server')
@click.pass_context
def viz(ctx, format, output, entity_types, from_entity, depth, serve, port):
    """Generate graph visualization."""
    from src.visualizers.mermaid import MermaidGenerator
    from src.visualizers.html import HTMLGenerator

    if format == 'mermaid':
        generator = MermaidGenerator(ctx.obj['graph'])
        diagram = generator.generate_with_styles(
            entity_types=entity_types.split(',') if entity_types else None,
            from_entity=from_entity,
            depth=depth
        )

        if output:
            with open(output, 'w') as f:
                f.write(diagram)
            console.print(f"[green]✓[/green] Saved to {output}")
        else:
            console.print(diagram)

    elif format == 'html':
        generator = HTMLGenerator(ctx.obj['graph'])
        html = generator.generate(
            entity_types=entity_types.split(',') if entity_types else None,
            from_entity=from_entity,
            depth=depth
        )

        if serve:
            # Start web server
            _serve_visualization(html, port)
        elif output:
            with open(output, 'w') as f:
                f.write(html)
            console.print(f"[green]✓[/green] Saved to {output}")
        else:
            console.print(html)
```

---

## Phase 2: HTML Interactive Viewer (4-6 hours)

### Create `know/src/visualizers/html.py`

```python
class HTMLGenerator:
    """Generate interactive HTML visualization with vis.js."""

    def __init__(self, graph_manager):
        self.graph = graph_manager

    def generate(self, entity_types=None, depth=None, from_entity=None):
        """Generate standalone HTML file."""
        graph_data = self.graph.load()

        # Convert to vis.js format
        nodes = self._generate_nodes(graph_data, entity_types)
        edges = self._generate_edges(graph_data, entity_types)

        # Load HTML template
        template = self._load_template()

        # Inject data
        html = template.replace('{{NODES_DATA}}', json.dumps(nodes))
        html = html.replace('{{EDGES_DATA}}', json.dumps(edges))

        return html

    def _generate_nodes(self, graph_data, entity_types):
        """Convert entities to vis.js nodes."""
        nodes = []

        for entity_type, entities in graph_data.get('entities', {}).items():
            if entity_types and entity_type not in entity_types:
                continue

            for name, data in entities.items():
                entity_id = f"{entity_type}:{name}"
                nodes.append({
                    'id': entity_id,
                    'label': data.get('name', name),
                    'title': data.get('description', ''),
                    'group': entity_type,
                    'level': self._get_level(entity_type)
                })

        return nodes

    def _generate_edges(self, graph_data, entity_types):
        """Convert dependencies to vis.js edges."""
        edges = []

        for from_id, to_data in graph_data.get('graph', {}).items():
            for to_id in to_data.get('depends_on', []):
                edges.append({
                    'from': from_id,
                    'to': to_id,
                    'arrows': 'to'
                })

        return edges

    def _get_level(self, entity_type):
        """Get hierarchical level for layout."""
        levels = {
            'project': 0,
            'user': 1,
            'objective': 1,
            'requirement': 2,
            'interface': 3,
            'feature': 4,
            'action': 5,
            'component': 6,
            'operation': 7
        }
        return levels.get(entity_type, 5)

    def _load_template(self):
        """Load HTML template."""
        template_path = Path(__file__).parent / 'templates' / 'graph.html'
        with open(template_path, 'r') as f:
            return f.read()
```

### Create HTML Template (`know/src/visualizers/templates/graph.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Know Graph Visualization</title>
    <script src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        #controls { position: absolute; top: 10px; left: 10px; z-index: 1000; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        #network { width: 100vw; height: 100vh; }
        #info { position: absolute; top: 10px; right: 10px; z-index: 1000; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 300px; display: none; }
        button { background: #0288d1; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin: 2px; }
        button:hover { background: #0277bd; }
        input[type="text"] { padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 200px; }
        label { display: block; margin-top: 10px; font-weight: 500; }
    </style>
</head>
<body>
    <div id="controls">
        <h3>Graph Controls</h3>
        <label>Search</label>
        <input type="text" id="search" placeholder="Search nodes...">
        <label>Layout</label>
        <button onclick="setLayout('hierarchical')">Hierarchical</button>
        <button onclick="setLayout('force')">Force</button>
        <label>Zoom</label>
        <button onclick="network.fit()">Fit</button>
        <button onclick="network.moveTo({scale: 1.0})">Reset</button>
    </div>

    <div id="info">
        <h3 id="info-title"></h3>
        <p id="info-description"></p>
        <h4>Dependencies:</h4>
        <ul id="info-deps"></ul>
    </div>

    <div id="network"></div>

    <script>
        // Data injected by Python
        const nodesData = {{NODES_DATA}};
        const edgesData = {{EDGES_DATA}};

        // Create network
        const nodes = new vis.DataSet(nodesData);
        const edges = new vis.DataSet(edgesData);

        const container = document.getElementById('network');
        const data = { nodes, edges };

        const options = {
            layout: {
                hierarchical: {
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 150
                }
            },
            physics: {
                enabled: false
            },
            groups: {
                feature: { color: { background: '#e1f5ff', border: '#0288d1' }, shape: 'box' },
                action: { color: { background: '#fff9c4', border: '#f57f17' }, shape: 'box' },
                component: { color: { background: '#f3e5f5', border: '#7b1fa2' }, shape: 'ellipse' },
                user: { color: { background: '#e8f5e9', border: '#388e3c' }, shape: 'diamond' },
                objective: { color: { background: '#fff3e0', border: '#e65100' }, shape: 'box' }
            },
            interaction: {
                hover: true,
                navigationButtons: true,
                keyboard: true
            },
            edges: {
                smooth: { type: 'cubicBezier' },
                arrows: { to: { enabled: true, scaleFactor: 0.5 } }
            }
        };

        const network = new vis.Network(container, data, options);

        // Node click handler
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);

                document.getElementById('info-title').textContent = node.label;
                document.getElementById('info-description').textContent = node.title || 'No description';

                // Show dependencies
                const connectedEdges = network.getConnectedEdges(nodeId);
                const deps = connectedEdges.map(edgeId => {
                    const edge = edges.get(edgeId);
                    if (edge.from === nodeId) {
                        const toNode = nodes.get(edge.to);
                        return toNode.label;
                    }
                }).filter(Boolean);

                const depsList = document.getElementById('info-deps');
                depsList.innerHTML = deps.map(dep => `<li>${dep}</li>`).join('');

                document.getElementById('info').style.display = 'block';
            } else {
                document.getElementById('info').style.display = 'none';
            }
        });

        // Search functionality
        document.getElementById('search').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            nodes.forEach(node => {
                const matches = node.label.toLowerCase().includes(searchTerm);
                nodes.update({ id: node.id, opacity: matches ? 1 : 0.2 });
            });
        });

        // Layout functions
        function setLayout(type) {
            if (type === 'hierarchical') {
                network.setOptions({
                    layout: { hierarchical: { enabled: true, direction: 'UD' } },
                    physics: { enabled: false }
                });
            } else if (type === 'force') {
                network.setOptions({
                    layout: { hierarchical: { enabled: false } },
                    physics: {
                        enabled: true,
                        barnesHut: { gravitationalConstant: -2000, springLength: 200 }
                    }
                });
            }
        }
    </script>
</body>
</html>
```

---

## Phase 3: Web Server (2-3 hours)

### Add Server Mode

```python
def _serve_visualization(html, port):
    """Start simple HTTP server to serve visualization."""
    import http.server
    import socketserver
    import tempfile
    import webbrowser
    from pathlib import Path

    # Save HTML to temp file
    temp_dir = Path(tempfile.mkdtemp())
    html_file = temp_dir / 'graph.html'
    with open(html_file, 'w') as f:
        f.write(html)

    # Change to temp directory
    os.chdir(temp_dir)

    # Start server
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        console.print(f"[green]✓[/green] Serving visualization at http://localhost:{port}")
        webbrowser.open(f'http://localhost:{port}/graph.html')
        httpd.serve_forever()
```

### Add Watch Mode

```python
def _serve_with_watch(graph_path, port):
    """Serve visualization and auto-reload on graph changes."""
    import watchdog.observers
    import watchdog.events

    class GraphChangeHandler(watchdog.events.FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path == str(graph_path):
                console.print("[yellow]Graph changed, reloading...[/yellow]")
                # Regenerate HTML
                # Send reload signal to browser (via WebSocket)

    # Start file watcher
    observer = watchdog.observers.Observer()
    observer.schedule(GraphChangeHandler(), str(graph_path.parent))
    observer.start()

    # Start server
    _serve_visualization(html, port)
```

---

## Quick Start Implementation

### 1. Create Directory Structure

```bash
mkdir -p know/src/visualizers/templates
touch know/src/visualizers/__init__.py
touch know/src/visualizers/mermaid.py
touch know/src/visualizers/html.py
touch know/src/visualizers/templates/graph.html
```

### 2. Implement Mermaid First (Quickest Win)

Focus on `mermaid.py` - can be done in 1-2 hours and provides immediate value.

### 3. Test

```bash
# Test Mermaid output
know viz --format mermaid

# Save to file
know viz --format mermaid -o graph.mmd

# View in VSCode or paste into Mermaid Live Editor
```

### 4. Then Add HTML

Once Mermaid works, add HTML generator and test:

```bash
# Generate HTML
know viz --format html -o graph.html

# Serve interactively
know viz --serve
```

---

## Testing Strategy

1. **Small graph** - Test with simple 5-node graph
2. **Medium graph** - Current spec-graph (~20 nodes)
3. **Large graph** - Synthetic graph with 500+ nodes
4. **Edge cases** - Empty graph, single node, disconnected components

---

## Documentation

Add to README:

```markdown
## Visualization

Generate interactive visualizations of your graph:

# Mermaid diagram
know viz --format mermaid -o graph.mmd

# Interactive HTML
know viz --format html -o graph.html

# Serve with auto-reload
know viz --serve --watch

# Filter by type
know viz --type feature,action

# Focus on specific entity
know viz --from feature:auth --depth 3
```

---

## Success Metrics

- [ ] Can generate Mermaid diagram
- [ ] Can generate interactive HTML
- [ ] HTML works offline (bundled assets)
- [ ] Search/filter works
- [ ] Layout options work
- [ ] Click to see details works
- [ ] Web server mode works
- [ ] Performance acceptable for 100+ nodes

---

**Total Estimate**: 8-12 hours for full implementation
**Quick Win**: 2-3 hours for Mermaid-only version
