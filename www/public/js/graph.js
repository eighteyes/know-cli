// Graph Visualization Component
class GraphVisualizer {
    constructor(canvasId, graph) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas?.getContext('2d');
        this.graph = graph;
        this.nodes = [];
        this.edges = [];
        this.selectedNode = null;
        this.hoveredNode = null;
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };
        this.zoom = 1;
        this.pan = { x: 0, y: 0 };

        if (this.canvas) {
            this.init();
        }
    }

    init() {
        this.setupCanvas();
        this.parseGraph();
        this.setupInteraction();
        this.animate();
    }

    setupCanvas() {
        // Set canvas size
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width - 20;
        this.canvas.height = 400;

        // High DPI support
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width *= dpr;
        this.canvas.height *= dpr;
        this.ctx.scale(dpr, dpr);
        this.canvas.style.width = `${rect.width - 20}px`;
        this.canvas.style.height = '400px';
    }

    parseGraph() {
        this.nodes = [];
        this.edges = [];

        if (!this.graph) return;

        const nodeMap = new Map();
        let nodeIndex = 0;

        // Convert entities to nodes
        if (this.graph.entities) {
            for (const [type, entities] of Object.entries(this.graph.entities)) {
                for (const [id, entity] of Object.entries(entities)) {
                    const nodeId = `${type.slice(0, -1)}:${id}`;
                    const node = {
                        id: nodeId,
                        type: type,
                        name: entity.name || id,
                        x: Math.random() * (this.canvas.width / window.devicePixelRatio - 100) + 50,
                        y: Math.random() * (this.canvas.height / window.devicePixelRatio - 100) + 50,
                        vx: 0,
                        vy: 0,
                        radius: 20,
                        color: this.getNodeColor(type)
                    };
                    this.nodes.push(node);
                    nodeMap.set(nodeId, node);
                    nodeIndex++;
                }
            }
        }

        // Extract edges from dependencies
        if (this.graph.graph) {
            for (const [from, deps] of Object.entries(this.graph.graph)) {
                if (deps.depends_on) {
                    for (const to of deps.depends_on) {
                        const fromNode = nodeMap.get(from);
                        const toNode = nodeMap.get(to);
                        if (fromNode && toNode) {
                            this.edges.push({
                                source: fromNode,
                                target: toNode
                            });
                        }
                    }
                }
            }
        }

        // Apply force layout
        this.applyForceLayout();
    }

    applyForceLayout() {
        const iterations = 100;
        const centerX = this.canvas.width / window.devicePixelRatio / 2;
        const centerY = this.canvas.height / window.devicePixelRatio / 2;

        for (let iter = 0; iter < iterations; iter++) {
            // Apply repulsion between all nodes
            for (let i = 0; i < this.nodes.length; i++) {
                for (let j = i + 1; j < this.nodes.length; j++) {
                    const node1 = this.nodes[i];
                    const node2 = this.nodes[j];

                    const dx = node2.x - node1.x;
                    const dy = node2.y - node1.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;

                    const force = 1000 / (dist * dist);
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;

                    node1.vx -= fx;
                    node1.vy -= fy;
                    node2.vx += fx;
                    node2.vy += fy;
                }
            }

            // Apply attraction along edges
            for (const edge of this.edges) {
                const dx = edge.target.x - edge.source.x;
                const dy = edge.target.y - edge.source.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;

                const force = dist * 0.01;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;

                edge.source.vx += fx;
                edge.source.vy += fy;
                edge.target.vx -= fx;
                edge.target.vy -= fy;
            }

            // Apply centering force
            for (const node of this.nodes) {
                const dx = centerX - node.x;
                const dy = centerY - node.y;
                node.vx += dx * 0.001;
                node.vy += dy * 0.001;
            }

            // Update positions with damping
            for (const node of this.nodes) {
                node.x += node.vx * 0.1;
                node.y += node.vy * 0.1;
                node.vx *= 0.8;
                node.vy *= 0.8;

                // Keep nodes on screen
                node.x = Math.max(node.radius, Math.min(this.canvas.width / window.devicePixelRatio - node.radius, node.x));
                node.y = Math.max(node.radius, Math.min(this.canvas.height / window.devicePixelRatio - node.radius, node.y));
            }
        }
    }

    setupInteraction() {
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));
    }

    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Check if clicking on a node
        const node = this.getNodeAt(x, y);
        if (node) {
            this.selectedNode = node;
            this.isDragging = true;
            this.dragOffset = {
                x: x - node.x,
                y: y - node.y
            };
        }
    }

    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (this.isDragging && this.selectedNode) {
            this.selectedNode.x = x - this.dragOffset.x;
            this.selectedNode.y = y - this.dragOffset.y;
        } else {
            // Check for hover
            const node = this.getNodeAt(x, y);
            if (node !== this.hoveredNode) {
                this.hoveredNode = node;
                this.canvas.style.cursor = node ? 'pointer' : 'default';
            }
        }
    }

    handleMouseUp(e) {
        this.isDragging = false;
    }

    handleWheel(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.zoom *= delta;
        this.zoom = Math.max(0.5, Math.min(2, this.zoom));
    }

    getNodeAt(x, y) {
        for (const node of this.nodes) {
            const dx = x - node.x;
            const dy = y - node.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < node.radius) {
                return node;
            }
        }
        return null;
    }

    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Save context
        this.ctx.save();

        // Apply zoom and pan
        this.ctx.translate(this.pan.x, this.pan.y);
        this.ctx.scale(this.zoom, this.zoom);

        // Draw edges
        this.ctx.strokeStyle = 'rgba(58, 122, 254, 0.3)';
        this.ctx.lineWidth = 2;
        for (const edge of this.edges) {
            this.drawEdge(edge);
        }

        // Draw nodes
        for (const node of this.nodes) {
            this.drawNode(node);
        }

        // Restore context
        this.ctx.restore();
    }

    drawEdge(edge) {
        const dx = edge.target.x - edge.source.x;
        const dy = edge.target.y - edge.source.y;
        const angle = Math.atan2(dy, dx);

        // Start and end points (accounting for node radius)
        const startX = edge.source.x + Math.cos(angle) * edge.source.radius;
        const startY = edge.source.y + Math.sin(angle) * edge.source.radius;
        const endX = edge.target.x - Math.cos(angle) * edge.target.radius;
        const endY = edge.target.y - Math.sin(angle) * edge.target.radius;

        // Draw line
        this.ctx.beginPath();
        this.ctx.moveTo(startX, startY);
        this.ctx.lineTo(endX, endY);
        this.ctx.stroke();

        // Draw arrowhead
        const arrowSize = 10;
        this.ctx.beginPath();
        this.ctx.moveTo(endX, endY);
        this.ctx.lineTo(
            endX - arrowSize * Math.cos(angle - Math.PI / 6),
            endY - arrowSize * Math.sin(angle - Math.PI / 6)
        );
        this.ctx.lineTo(
            endX - arrowSize * Math.cos(angle + Math.PI / 6),
            endY - arrowSize * Math.sin(angle + Math.PI / 6)
        );
        this.ctx.closePath();
        this.ctx.fillStyle = 'rgba(58, 122, 254, 0.5)';
        this.ctx.fill();
    }

    drawNode(node) {
        // Draw shadow if selected
        if (node === this.selectedNode) {
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, node.radius + 5, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(0, 118, 254, 0.3)';
            this.ctx.fill();
        }

        // Draw circle
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = node.color;
        this.ctx.fill();

        // Draw border
        this.ctx.strokeStyle = node === this.hoveredNode ? '#fff' : 'rgba(255, 255, 255, 0.3)';
        this.ctx.lineWidth = node === this.hoveredNode ? 2 : 1;
        this.ctx.stroke();

        // Draw label
        this.ctx.fillStyle = '#fff';
        this.ctx.font = '10px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';

        // Truncate long names
        let label = node.name;
        if (label.length > 10) {
            label = label.substring(0, 8) + '...';
        }
        this.ctx.fillText(label, node.x, node.y);

        // Draw type below
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        this.ctx.font = '8px sans-serif';
        this.ctx.fillText(node.type.slice(0, -1), node.x, node.y + node.radius + 10);
    }

    getNodeColor(type) {
        const colors = {
            users: '#0076FE',
            features: '#33E2FF',
            components: '#00C896',
            interfaces: '#FF6B6B',
            requirements: '#FFD93D',
            platforms: '#6C5CE7',
            objectives: '#FD79A8',
            actions: '#A29BFE'
        };
        return colors[type] || '#666';
    }

    animate() {
        this.render();
        requestAnimationFrame(() => this.animate());
    }

    addNode(entity) {
        const node = {
            id: `${entity.type}:${entity.id}`,
            type: entity.type + 's',
            name: entity.name,
            x: this.canvas.width / window.devicePixelRatio / 2 + (Math.random() - 0.5) * 100,
            y: this.canvas.height / window.devicePixelRatio / 2 + (Math.random() - 0.5) * 100,
            vx: 0,
            vy: 0,
            radius: 20,
            color: this.getNodeColor(entity.type + 's')
        };

        this.nodes.push(node);

        // Animate the appearance
        node.radius = 0;
        const animate = () => {
            if (node.radius < 20) {
                node.radius += 2;
                requestAnimationFrame(animate);
            }
        };
        animate();

        // Re-apply force layout
        this.applyForceLayout();
    }

    refresh(graph) {
        this.graph = graph;
        this.parseGraph();
    }
}

// Auto-initialize graph visualizer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Graph will be initialized by DiscoverPhase when needed
});