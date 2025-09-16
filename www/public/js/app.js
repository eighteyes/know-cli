// Main Application Class
class KnowledgeGraphApp {
    constructor() {
        this.currentPhase = 'discover';
        this.graph = null;
        this.ws = null;
        this.apiBase = 'http://localhost:8880/api';
        this.phases = {};
        this.init();
    }

    async init() {
        await this.loadGraph();
        this.setupWebSocket();
        this.bindEvents();
        this.loadPhase(this.currentPhase);
        this.renderGraphMinimap();
    }

    async loadGraph() {
        try {
            const response = await fetch(`${this.apiBase}/graph`);
            this.graph = await response.json();
            this.updateEntitySidebar();
            this.renderGraphMinimap();
        } catch (error) {
            console.error('Failed to load graph:', error);
            this.showError('Failed to load knowledge graph');
        }
    }

    setupWebSocket() {
        this.ws = new WebSocket('ws://localhost:8881');

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.showSuccess('Connected to real-time updates');
        };

        this.ws.onmessage = (event) => {
            const { type, data } = JSON.parse(event.data);
            this.handleRealtimeUpdate(type, data);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showError('Real-time connection error');
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.setupWebSocket(), 3000);
        };
    }

    handleRealtimeUpdate(type, data) {
        switch(type) {
            case 'connected':
                console.log('Server confirmed connection');
                break;
            case 'entity-added':
                this.onEntityAdded(data);
                break;
            case 'graph-updated':
                this.loadGraph();
                if (this.phases.discover) {
                    this.phases.discover.refresh();
                }
                break;
            default:
                console.log('Unknown update type:', type, data);
        }
    }

    bindEvents() {
        // Phase navigation
        document.querySelectorAll('.phase-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (!e.target.disabled) {
                    this.switchPhase(e.target.dataset.phase);
                }
            });
        });

        // AI prompt bar
        const aiSubmit = document.getElementById('ai-submit');
        const aiPrompt = document.getElementById('ai-prompt');

        aiSubmit.addEventListener('click', () => this.handleAIPrompt());
        aiPrompt.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleAIPrompt();
            }
        });

        // Graph refresh
        document.getElementById('graph-refresh').addEventListener('click', () => {
            this.loadGraph();
        });
    }

    switchPhase(phaseName) {
        // Update nav buttons
        document.querySelectorAll('.phase-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.phase === phaseName);
        });

        this.currentPhase = phaseName;
        this.loadPhase(phaseName);
    }

    async loadPhase(phaseName) {
        const content = document.getElementById('phase-content');

        switch(phaseName) {
            case 'discover':
                if (!this.phases.discover) {
                    this.phases.discover = new DiscoverPhase(this);
                }
                await this.phases.discover.init();
                break;

            case 'validation':
                content.innerHTML = '<p>Validation phase - Coming soon</p>';
                break;

            case 'define':
                content.innerHTML = '<p>Define phase - Coming soon</p>';
                break;

            case 'deliver':
                content.innerHTML = '<p>Deliver phase - Coming soon</p>';
                break;

            case 'phases':
                content.innerHTML = '<p>Phases management - Coming soon</p>';
                break;

            default:
                content.innerHTML = '<p>Unknown phase</p>';
        }
    }

    updateEntitySidebar() {
        const accordion = document.getElementById('entity-accordion');
        accordion.innerHTML = '';

        if (!this.graph || !this.graph.entities) return;

        // Group entities by type
        for (const [type, entities] of Object.entries(this.graph.entities)) {
            const count = Object.keys(entities).length;
            if (count === 0) continue;

            const group = document.createElement('div');
            group.className = 'entity-group';

            const header = document.createElement('div');
            header.className = 'entity-group-header';
            header.innerHTML = `
                <span>${this.formatTypeName(type)} (${count})</span>
                <span>▶</span>
            `;
            header.addEventListener('click', () => {
                group.classList.toggle('expanded');
                header.querySelector('span:last-child').textContent =
                    group.classList.contains('expanded') ? '▼' : '▶';
            });

            const content = document.createElement('div');
            content.className = 'entity-group-content';

            // Add individual entities
            for (const [id, entity] of Object.entries(entities)) {
                const item = document.createElement('div');
                item.className = 'entity-item';
                item.textContent = `• ${entity.name || id}`;
                item.dataset.entityRef = `${type.slice(0, -1)}:${id}`;
                item.addEventListener('click', () => this.selectEntity(item.dataset.entityRef));
                content.appendChild(item);
            }

            group.appendChild(header);
            group.appendChild(content);
            accordion.appendChild(group);
        }
    }

    formatTypeName(type) {
        return type.charAt(0).toUpperCase() + type.slice(1);
    }

    selectEntity(entityRef) {
        console.log('Selected entity:', entityRef);
        // Could highlight in graph, show details, etc.
    }

    renderGraphMinimap() {
        const canvas = document.getElementById('graph-minimap');
        if (!canvas || !this.graph) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Extract nodes and edges from graph
        const nodes = [];
        const edges = [];

        // Convert entities to nodes
        if (this.graph.entities) {
            let nodeIndex = 0;
            for (const [type, entities] of Object.entries(this.graph.entities)) {
                for (const [id, entity] of Object.entries(entities)) {
                    nodes.push({
                        id: `${type.slice(0, -1)}:${id}`,
                        type: type,
                        name: entity.name || id,
                        x: 50 + (nodeIndex % 5) * 50,
                        y: 50 + Math.floor(nodeIndex / 5) * 40
                    });
                    nodeIndex++;
                }
            }
        }

        // Extract edges from graph dependencies
        if (this.graph.graph) {
            for (const [from, deps] of Object.entries(this.graph.graph)) {
                if (deps.depends_on) {
                    for (const to of deps.depends_on) {
                        edges.push({ from, to });
                    }
                }
            }
        }

        // Draw edges
        ctx.strokeStyle = 'rgba(58, 122, 254, 0.3)';
        ctx.lineWidth = 1;
        edges.forEach(edge => {
            const fromNode = nodes.find(n => n.id === edge.from);
            const toNode = nodes.find(n => n.id === edge.to);
            if (fromNode && toNode) {
                ctx.beginPath();
                ctx.moveTo(fromNode.x, fromNode.y);
                ctx.lineTo(toNode.x, toNode.y);
                ctx.stroke();
            }
        });

        // Draw nodes
        nodes.forEach(node => {
            ctx.fillStyle = this.getNodeColor(node.type);
            ctx.beginPath();
            ctx.arc(node.x, node.y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    getNodeColor(type) {
        const colors = {
            users: '#0076FE',
            features: '#33E2FF',
            components: '#00C896',
            interfaces: '#FF6B6B',
            requirements: '#FFD93D',
            platforms: '#6C5CE7'
        };
        return colors[type] || '#666';
    }

    onEntityAdded(data) {
        this.showSuccess(`Added entity: ${data.name}`);
        this.updateEntitySidebar();
        this.renderGraphMinimap();
    }

    async handleAIPrompt() {
        const prompt = document.getElementById('ai-prompt').value.trim();
        if (!prompt) return;

        // For now, just log it
        console.log('AI Prompt:', prompt);
        this.showInfo('AI processing coming soon...');

        // Clear the prompt
        document.getElementById('ai-prompt').value = '';
    }

    // Utility methods for notifications
    showSuccess(message) {
        console.log('✅', message);
        // Could show a toast notification
    }

    showError(message) {
        console.error('❌', message);
        // Could show a toast notification
    }

    showInfo(message) {
        console.log('ℹ️', message);
        // Could show a toast notification
    }

    // Execute know command through API
    async executeKnowCommand(command, args = []) {
        try {
            const response = await fetch(`${this.apiBase}/know/command`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, args })
            });

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error);
            }

            return result.output;
        } catch (error) {
            console.error('Know command failed:', error);
            throw error;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new KnowledgeGraphApp();
});