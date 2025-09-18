// Enhanced Graph Minimap with force-directed layout
class GraphMinimap {
    constructor(canvas, app) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.app = app;
        this.nodes = [];
        this.edges = [];
        this.simulation = null;
        this.hoveredNode = null;
        this.selectedNode = null;
        this.animationFrame = null;
        this.isDragging = false;

        // Visual settings - static fan layout
        this.settings = {
            nodeRadius: 3,      // Smaller nodes
            selectedRadius: 4,
            linkStrength: 0,    // No physics
            repulsion: 0,       // No physics
            centerForce: 0,     // No physics
            damping: 1,         // Full stop
            minNodeDistance: 0,
            maxVelocity: 0,     // No movement
            usePhysics: false,  // Disable physics entirely
            // Fan layout parameters (configurable via sliders)
            startAngle: -15,      // Starting angle in degrees
            spread: 80,        // Total spread in degrees
            layerSpacing: 12,   // Pixels between layers
            originX: 10,        // X position of fan origin
            originY: 20,        // Y position as percentage
            baseRadius: 20,      // Base distance from origin
            verticalJitter: 4,  // Vertical jitter amount
            lineWidth: 0.8,     // Connection line width
            nodeGap: 1,         // Extra gap between nodes
            layerCurve: 0,      // Curve each layer (degrees)
            glowSize: 3,        // Glow effect size
            lineOpacity: 30,    // Line opacity percentage
            spiral: 0,          // Spiral effect amount
            waveAmp: 0,         // Wave amplitude
            waveFreq: 1         // Wave frequency
        };

        this.setupInteraction();
        this.setupSliders();
        this.startSimulation();
    }

    setupSliders() {
        // Start Angle slider
        const startAngleSlider = document.getElementById('start-angle');
        const startAngleValue = document.getElementById('start-angle-value');
        if (startAngleSlider) {
            startAngleSlider.value = this.settings.startAngle;
            startAngleSlider.addEventListener('input', (e) => {
                this.settings.startAngle = parseFloat(e.target.value);
                startAngleValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Spread slider
        const spreadSlider = document.getElementById('spread');
        const spreadValue = document.getElementById('spread-value');
        if (spreadSlider) {
            spreadSlider.value = this.settings.spread;
            spreadSlider.addEventListener('input', (e) => {
                this.settings.spread = parseFloat(e.target.value);
                spreadValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Layer Spacing slider
        const layerSpacingSlider = document.getElementById('layer-spacing');
        const layerSpacingValue = document.getElementById('layer-spacing-value');
        if (layerSpacingSlider) {
            layerSpacingSlider.value = this.settings.layerSpacing;
            layerSpacingSlider.addEventListener('input', (e) => {
                this.settings.layerSpacing = parseFloat(e.target.value);
                layerSpacingValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Origin X slider
        const originXSlider = document.getElementById('origin-x');
        const originXValue = document.getElementById('origin-x-value');
        if (originXSlider) {
            originXSlider.value = this.settings.originX;
            originXSlider.addEventListener('input', (e) => {
                this.settings.originX = parseFloat(e.target.value);
                originXValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Origin Y slider
        const originYSlider = document.getElementById('origin-y');
        const originYValue = document.getElementById('origin-y-value');
        if (originYSlider) {
            originYSlider.value = this.settings.originY;
            originYSlider.addEventListener('input', (e) => {
                this.settings.originY = parseFloat(e.target.value);
                originYValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Base Radius slider
        const baseRadiusSlider = document.getElementById('base-radius');
        const baseRadiusValue = document.getElementById('base-radius-value');
        if (baseRadiusSlider) {
            baseRadiusSlider.value = this.settings.baseRadius;
            baseRadiusSlider.addEventListener('input', (e) => {
                this.settings.baseRadius = parseFloat(e.target.value);
                baseRadiusValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Node Size slider
        const nodeSizeSlider = document.getElementById('node-size');
        const nodeSizeValue = document.getElementById('node-size-value');
        if (nodeSizeSlider) {
            nodeSizeSlider.value = this.settings.nodeRadius;
            nodeSizeSlider.addEventListener('input', (e) => {
                this.settings.nodeRadius = parseFloat(e.target.value);
                this.settings.selectedRadius = this.settings.nodeRadius + 1;
                nodeSizeValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Vertical Jitter slider
        const verticalJitterSlider = document.getElementById('vertical-jitter');
        const verticalJitterValue = document.getElementById('vertical-jitter-value');
        if (verticalJitterSlider) {
            verticalJitterSlider.value = this.settings.verticalJitter;
            verticalJitterSlider.addEventListener('input', (e) => {
                this.settings.verticalJitter = parseFloat(e.target.value);
                verticalJitterValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Line Width slider
        const lineWidthSlider = document.getElementById('line-width');
        const lineWidthValue = document.getElementById('line-width-value');
        if (lineWidthSlider) {
            lineWidthSlider.value = this.settings.lineWidth;
            lineWidthSlider.addEventListener('input', (e) => {
                this.settings.lineWidth = parseFloat(e.target.value);
                lineWidthValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Node Gap slider
        const nodeGapSlider = document.getElementById('node-gap');
        const nodeGapValue = document.getElementById('node-gap-value');
        if (nodeGapSlider) {
            nodeGapSlider.value = this.settings.nodeGap;
            nodeGapSlider.addEventListener('input', (e) => {
                this.settings.nodeGap = parseFloat(e.target.value);
                nodeGapValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Layer Curve slider
        const layerCurveSlider = document.getElementById('layer-curve');
        const layerCurveValue = document.getElementById('layer-curve-value');
        if (layerCurveSlider) {
            layerCurveSlider.value = this.settings.layerCurve;
            layerCurveSlider.addEventListener('input', (e) => {
                this.settings.layerCurve = parseFloat(e.target.value);
                layerCurveValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Glow Size slider
        const glowSizeSlider = document.getElementById('glow-size');
        const glowSizeValue = document.getElementById('glow-size-value');
        if (glowSizeSlider) {
            glowSizeSlider.value = this.settings.glowSize;
            glowSizeSlider.addEventListener('input', (e) => {
                this.settings.glowSize = parseFloat(e.target.value);
                glowSizeValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Line Opacity slider
        const lineOpacitySlider = document.getElementById('line-opacity');
        const lineOpacityValue = document.getElementById('line-opacity-value');
        if (lineOpacitySlider) {
            lineOpacitySlider.value = this.settings.lineOpacity;
            lineOpacitySlider.addEventListener('input', (e) => {
                this.settings.lineOpacity = parseFloat(e.target.value);
                lineOpacityValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Spiral slider
        const spiralSlider = document.getElementById('spiral');
        const spiralValue = document.getElementById('spiral-value');
        if (spiralSlider) {
            spiralSlider.value = this.settings.spiral;
            spiralSlider.addEventListener('input', (e) => {
                this.settings.spiral = parseFloat(e.target.value);
                spiralValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Wave Amplitude slider
        const waveAmpSlider = document.getElementById('wave-amp');
        const waveAmpValue = document.getElementById('wave-amp-value');
        if (waveAmpSlider) {
            waveAmpSlider.value = this.settings.waveAmp;
            waveAmpSlider.addEventListener('input', (e) => {
                this.settings.waveAmp = parseFloat(e.target.value);
                waveAmpValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Wave Frequency slider
        const waveFreqSlider = document.getElementById('wave-freq');
        const waveFreqValue = document.getElementById('wave-freq-value');
        if (waveFreqSlider) {
            waveFreqSlider.value = this.settings.waveFreq;
            waveFreqSlider.addEventListener('input', (e) => {
                this.settings.waveFreq = parseFloat(e.target.value);
                waveFreqValue.textContent = e.target.value;
                this.updateGraph(this.app.graph);
            });
        }

        // Setup config management
        this.setupConfigManagement();
        this.updateConfigOutput();
    }

    setupConfigManagement() {
        const configOutput = document.getElementById('config-output');
        const configInput = document.getElementById('config-input');
        const copyBtn = document.getElementById('copy-config');
        const loadBtn = document.getElementById('load-config');

        // Update config output whenever a slider changes
        const sliders = ['start-angle', 'spread', 'layer-spacing', 'origin-x', 'origin-y', 'base-radius', 'node-size', 'vertical-jitter', 'line-width', 'node-gap', 'layer-curve', 'glow-size', 'line-opacity', 'spiral', 'wave-amp', 'wave-freq'];
        sliders.forEach(id => {
            const slider = document.getElementById(id);
            if (slider) {
                slider.addEventListener('input', () => this.updateConfigOutput());
            }
        });

        // Copy config to clipboard
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                configOutput.select();
                document.execCommand('copy');
                copyBtn.textContent = '✓';
                setTimeout(() => copyBtn.textContent = '📋', 1000);
            });
        }

        // Load config from input
        if (loadBtn) {
            loadBtn.addEventListener('click', () => {
                const config = configInput.value.trim();
                if (config) {
                    this.loadConfig(config);
                    configInput.value = '';
                }
            });
        }
    }

    updateConfigOutput() {
        const config = [
            this.settings.startAngle,
            this.settings.spread,
            this.settings.layerSpacing,
            this.settings.originX,
            this.settings.originY,
            this.settings.baseRadius,
            this.settings.nodeRadius,
            this.settings.verticalJitter,
            this.settings.lineWidth,
            this.settings.nodeGap,
            this.settings.layerCurve,
            this.settings.glowSize,
            this.settings.lineOpacity,
            this.settings.spiral,
            this.settings.waveAmp,
            this.settings.waveFreq
        ].join(',');

        const configOutput = document.getElementById('config-output');
        if (configOutput) {
            configOutput.value = config;
        }
    }

    loadConfig(configString) {
        const values = configString.split(',').map(v => parseFloat(v));
        if (values.length >= 6) {
            // Update settings
            this.settings.startAngle = values[0] || 0;
            this.settings.spread = values[1] || 252;
            this.settings.layerSpacing = values[2] || 30;
            this.settings.originX = values[3] || 25;
            this.settings.originY = values[4] || 50;
            this.settings.baseRadius = values[5] || 40;
            this.settings.nodeRadius = values[6] || 3;
            this.settings.selectedRadius = this.settings.nodeRadius + 1;
            this.settings.verticalJitter = values[7] || 4;
            this.settings.lineWidth = values[8] || 0.8;
            this.settings.nodeGap = values[9] || 1;
            this.settings.layerCurve = values[10] || 0;
            this.settings.glowSize = values[11] || 3;
            this.settings.lineOpacity = values[12] || 30;
            this.settings.spiral = values[13] || 0;
            this.settings.waveAmp = values[14] || 0;
            this.settings.waveFreq = values[15] || 1;

            // Update sliders and values
            const updates = [
                ['start-angle', 'start-angle-value', this.settings.startAngle],
                ['spread', 'spread-value', this.settings.spread],
                ['layer-spacing', 'layer-spacing-value', this.settings.layerSpacing],
                ['origin-x', 'origin-x-value', this.settings.originX],
                ['origin-y', 'origin-y-value', this.settings.originY],
                ['base-radius', 'base-radius-value', this.settings.baseRadius],
                ['node-size', 'node-size-value', this.settings.nodeRadius],
                ['vertical-jitter', 'vertical-jitter-value', this.settings.verticalJitter],
                ['line-width', 'line-width-value', this.settings.lineWidth],
                ['node-gap', 'node-gap-value', this.settings.nodeGap],
                ['layer-curve', 'layer-curve-value', this.settings.layerCurve],
                ['glow-size', 'glow-size-value', this.settings.glowSize],
                ['line-opacity', 'line-opacity-value', this.settings.lineOpacity],
                ['spiral', 'spiral-value', this.settings.spiral],
                ['wave-amp', 'wave-amp-value', this.settings.waveAmp],
                ['wave-freq', 'wave-freq-value', this.settings.waveFreq]
            ];

            updates.forEach(([sliderId, valueId, value]) => {
                const slider = document.getElementById(sliderId);
                const valueElem = document.getElementById(valueId);
                if (slider) slider.value = value;
                if (valueElem) valueElem.textContent = value;
            });

            // Refresh the graph
            this.updateGraph(this.app.graph);
        }
    }

    setupInteraction() {
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mouseup', () => this.handleMouseUp());
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('mouseleave', () => {
            this.hoveredNode = null;
            this.canvas.style.cursor = 'default';
        });
    }

    handleMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Find node under cursor
        this.hoveredNode = this.nodes.find(node => {
            const dx = node.x - x;
            const dy = node.y - y;
            return Math.sqrt(dx * dx + dy * dy) < this.settings.nodeRadius + 3;
        });

        // Update cursor
        this.canvas.style.cursor = this.hoveredNode ? 'pointer' : 'default';

        // Update info panel on hover (unless locked)
        if (!this.lockedNode && this.hoveredNode) {
            this.updateNodeInfo(this.hoveredNode);
        } else if (!this.lockedNode && !this.hoveredNode) {
            this.updateNodeInfo(null);
        }

        // If dragging, update node position
        if (this.isDragging && this.selectedNode) {
            this.selectedNode.x = x;
            this.selectedNode.y = y;
            this.selectedNode.vx = 0;
            this.selectedNode.vy = 0;
        }
    }

    handleMouseDown(event) {
        if (this.hoveredNode) {
            this.isDragging = true;
            event.preventDefault();
        }
    }

    handleMouseUp() {
        this.isDragging = false;
    }

    handleClick(event) {
        if (!this.isDragging) {
            if (this.hoveredNode) {
                // If clicking the same locked node, unlock it
                if (this.lockedNode === this.hoveredNode) {
                    this.lockedNode = null;
                    this.selectedNode = null;
                    // Don't clear info here - let hover take over
                } else {
                    // Lock the new node
                    this.lockedNode = this.hoveredNode;
                    this.selectedNode = this.hoveredNode;
                    this.updateNodeInfo(this.lockedNode);
                }
            } else {
                // Clicking empty space unlocks
                this.lockedNode = null;
                this.selectedNode = null;
                this.updateNodeInfo(null);
            }
        }
    }

    updateNodeInfo(node) {
        const infoPanel = document.getElementById('graph-node-info');
        if (!infoPanel) return;

        if (!node) {
            infoPanel.innerHTML = `
                <div style="text-align: center; padding: 25px 10px;">
                    <div style="color: #33E2FF; font-size: 18px; font-weight: bold; text-transform: uppercase; letter-spacing: 3px; text-shadow: 0 0 10px rgba(51, 226, 255, 0.5);">
                        ${this.nodes.length} NODES
                    </div>
                    <div style="color: #666; font-size: 11px; margin-top: 10px; letter-spacing: 1px;">
                        HOVER TO PREVIEW • CLICK TO LOCK
                    </div>
                </div>
            `;
            return;
        }

        const nodeColor = this.getNodeColor(node.type);

        infoPanel.innerHTML = `
            <div style="text-align: center; padding: 18px 10px;">
                <div style="color: ${nodeColor}; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; opacity: 0.8;">
                    ${node.type}
                </div>
                <div style="color: #fff; font-size: 18px; margin-top: 10px; font-weight: bold; text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);">
                    ${node.name}
                </div>
                <div style="color: #555; font-size: 10px; margin-top: 8px; font-family: monospace; opacity: 0.7;">
                    ${node.id}
                </div>
            </div>
        `;
    }

    getNodeDependencies(node) {
        const incoming = this.edges.filter(e => e.target === node);
        const outgoing = this.edges.filter(e => e.source === node);
        return { in: incoming, out: outgoing };
    }

    updateGraph(graphData) {
        if (!graphData) return;

        // Reset arrays and clear selection
        this.nodes = [];
        this.edges = [];
        this.selectedNode = null;
        const nodeMap = {};

        // Initialize the info panel with placeholder
        this.updateNodeInfo(null);

        // Define left-to-right layers (high level -> low level)
        const layerOrder = {
            'users': 0,           // Leftmost - highest level
            'objectives': 1,      // Business objectives
            'requirements': 2,    // System requirements
            'features': 3,        // Feature layer
            'interfaces': 4,      // UI layer
            'actions': 5,         // User actions
            'components': 6,      // Implementation layer
            'platforms': 7,       // Infrastructure - rightmost
            'behavior': 7,        // Same level as platforms
            'references': 8       // Far right
        };

        // Count nodes per type for vertical distribution
        const typeCounts = {};
        if (graphData.entities) {
            Object.entries(graphData.entities).forEach(([type, entities]) => {
                typeCounts[type] = Object.keys(entities).length;
            });
        }

        // Create nodes with fan layout - spreading from left to right
        if (graphData.entities) {
            const fanOrigin = {
                x: this.settings.originX,
                y: this.canvas.height * (this.settings.originY / 100)
            };
            const fanAngleRange = Math.PI * (this.settings.spread / 180); // Convert degrees to radians
            const fanStartAngle = Math.PI * (this.settings.startAngle / 180); // Convert degrees to radians

            let globalNodeIndex = 0;
            const totalNodes = Object.entries(graphData.entities).reduce((sum, [type, entities]) =>
                sum + Object.keys(entities).length, 0);

            Object.entries(graphData.entities).forEach(([type, entities]) => {
                const layer = layerOrder[type] !== undefined ? layerOrder[type] : 5;
                const layerRadius = this.settings.baseRadius + (layer * this.settings.layerSpacing);

                Object.entries(entities).forEach(([id, entity], entityIndex) => {
                    const nodeId = `${type.slice(0, -1)}:${id}`;

                    // Calculate fan position with node gap spacing
                    const angleStep = (fanAngleRange / Math.max(totalNodes - 1, 1)) * (1 + this.settings.nodeGap * 0.1);
                    const baseAngle = fanStartAngle + (globalNodeIndex * angleStep);

                    // Apply layer curve effect - makes each layer curve progressively
                    const layerCurveRadians = Math.PI * (this.settings.layerCurve / 180);
                    const curvedAngle = baseAngle + (layer * layerCurveRadians * 0.1);

                    // Add spiral effect - increases radius based on position
                    const spiralRadius = layerRadius + (globalNodeIndex * this.settings.spiral * 2);

                    // Add small offset to prevent overlap but maintain calm layout
                    const radiusOffset = (globalNodeIndex % 3) * 2; // Tiny radius variation
                    const adjustedRadius = spiralRadius + radiusOffset;

                    // Apply wave effect - creates undulating pattern
                    const waveOffset = Math.sin(globalNodeIndex * this.settings.waveFreq * 0.3) * this.settings.waveAmp;
                    const verticalJitter = (globalNodeIndex % 4 - 1.5) * this.settings.verticalJitter;

                    const x = fanOrigin.x + Math.cos(curvedAngle) * adjustedRadius;
                    const y = fanOrigin.y + Math.sin(curvedAngle) * adjustedRadius + verticalJitter + waveOffset;

                    const node = {
                        id: nodeId,
                        type: type,
                        name: entity.name || id,
                        entity: entity,
                        layer: layer,
                        x: x,
                        y: y,
                        vx: 0,
                        vy: 0
                    };
                    this.nodes.push(node);
                    nodeMap[nodeId] = node;
                    globalNodeIndex++;
                });
            });
        }

        // Create edges from dependencies
        if (graphData.graph) {
            Object.entries(graphData.graph).forEach(([fromId, deps]) => {
                if (deps.depends_on && Array.isArray(deps.depends_on)) {
                    deps.depends_on.forEach(toId => {
                        if (nodeMap[fromId] && nodeMap[toId]) {
                            this.edges.push({
                                source: nodeMap[fromId],
                                target: nodeMap[toId]
                            });
                        }
                    });
                }
            });
        }

        // Add some references as special nodes
        if (graphData.references && Object.keys(graphData.references).length > 0) {
            const refNode = {
                id: 'refs',
                type: 'references',
                name: `References (${Object.keys(graphData.references).length})`,
                x: this.canvas.width / 2,
                y: 20,
                vx: 0,
                vy: 0,
                isReference: true
            };
            this.nodes.push(refNode);
        }
    }

    startSimulation() {
        const animate = () => {
            this.simulateForces();
            this.render();
            this.animationFrame = requestAnimationFrame(animate);
        };
        animate();
    }

    simulateForces() {
        // Skip physics entirely for static layout
        if (!this.settings.usePhysics) return;
    }

    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Very subtle background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Skip drawing connection lines for cleaner look

        // Draw nodes with futuristic glow effect
        this.nodes.forEach(node => {
            const isHovered = node === this.hoveredNode;
            const isLocked = node === this.lockedNode;
            const radius = (isHovered || isLocked) ? this.settings.selectedRadius : this.settings.nodeRadius;
            const color = this.getNodeColor(node.type);

            // Simple selection ring
            if (isLocked) {
                this.ctx.strokeStyle = color + 'FF';
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                this.ctx.arc(node.x, node.y, radius + 4, 0, Math.PI * 2);
                this.ctx.stroke();
            }

            // Main node circle
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);

            // Simple clean nodes - just outlines
            this.ctx.strokeStyle = isLocked ? color + 'FF' : (isHovered ? color + 'DD' : color + '99');
            this.ctx.lineWidth = isLocked ? 2 : 1;
            this.ctx.stroke();
        });

        // Draw stats
        this.drawStats();
    }

    drawStats() {
        const stats = {
            nodes: this.nodes.length,
            edges: this.edges.length
        };

        // Futuristic stats display
        this.ctx.fillStyle = '#33E2FF';
        this.ctx.font = '8px "Roboto Mono", monospace';
        this.ctx.textAlign = 'left';

        // Add glow effect to text
        this.ctx.shadowColor = '#33E2FF';
        this.ctx.shadowBlur = 4;

        const text = `ENT:${stats.nodes.toString().padStart(3, '0')} | CON:${stats.edges.toString().padStart(3, '0')}`;
        this.ctx.fillText(text, 8, this.canvas.height - 8);

        // Reset shadow
        this.ctx.shadowBlur = 0;

        // Add tactical grid lines in corners
        this.ctx.strokeStyle = 'rgba(51, 226, 255, 0.3)';
        this.ctx.lineWidth = 0.5;

        // Top-left corner
        this.ctx.beginPath();
        this.ctx.moveTo(5, 5);
        this.ctx.lineTo(15, 5);
        this.ctx.moveTo(5, 5);
        this.ctx.lineTo(5, 15);
        this.ctx.stroke();

        // Top-right corner
        this.ctx.beginPath();
        this.ctx.moveTo(this.canvas.width - 15, 5);
        this.ctx.lineTo(this.canvas.width - 5, 5);
        this.ctx.moveTo(this.canvas.width - 5, 5);
        this.ctx.lineTo(this.canvas.width - 5, 15);
        this.ctx.stroke();
    }

    getNodeColor(type) {
        // Futuristic robotic color scheme
        const colors = {
            users: '#33E2FF',           // Neon cyan for users
            objectives: '#0076FE',      // Primary blue for objectives
            actions: '#00C896',         // Success green for actions
            features: '#00ff88',        // Neon green for features
            components: '#8a2be2',      // Electric purple for components
            interfaces: '#00d4ff',      // Neon blue for interfaces
            requirements: '#FFD93D',    // Warning yellow for requirements
            platforms: '#c0c0c0',       // Chrome silver for platforms
            references: '#9d4edd',      // Hologram purple for references
            behavior: '#00ffff'         // Neon cyan for behavior
        };
        return colors[type] || '#33E2FF';
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ?
            `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` :
            '255, 255, 255';
    }

    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }
}

// Export for use
window.GraphMinimap = GraphMinimap;