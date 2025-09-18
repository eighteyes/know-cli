// Mini Progress Vessel - Graph Completion Tracker
class MiniVessel {
    constructor() {
        this.canvas = document.getElementById('mini-vessel-canvas');
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.time = 0;
        this.animationId = null;

        // Fixed settings for mini vessel
        this.settings = {
            baseWidth: 30,  // Minimum width
            maxWidth: 100,  // Maximum width
            height: 40,
            waveSpeed: 0.02,
            waveHeight: 2,
            fillLevel: 0,
            totalNodes: 0,
            completedNodes: 0
        };

        // Single calm wave
        this.wave = {
            amplitude: 2,
            frequency: 0.04,
            phase: 0,
            speed: 0.02,
            opacity: 0.9
        };

        this.init();
    }

    init() {
        // Start animation
        this.animate();

        // Listen for graph updates
        this.setupGraphListener();
    }

    setupGraphListener() {
        // Check for graph updates periodically
        setInterval(() => {
            this.updateFromGraph();
        }, 1000);

        // Initial update
        this.updateFromGraph();
    }

    updateFromGraph() {
        // Get graph data from app if available
        if (window.app && window.app.graph) {
            const graph = window.app.graph;

            // Count total nodes
            let totalNodes = 0;
            let completedNodes = 0;

            if (graph.entities) {
                Object.entries(graph.entities).forEach(([type, entities]) => {
                    Object.entries(entities).forEach(([id, entity]) => {
                        totalNodes++;
                        // Consider a node complete if it has a name and at least one property
                        if (entity.name && Object.keys(entity).length > 1) {
                            completedNodes++;
                        }
                    });
                });
            }

            // Add references to count
            if (graph.references) {
                const refCount = Object.keys(graph.references).length;
                totalNodes += refCount;
                completedNodes += refCount; // References are always considered complete
            }

            this.settings.totalNodes = totalNodes;
            this.settings.completedNodes = completedNodes;

            // Calculate fill level (0-100%)
            if (totalNodes > 0) {
                this.settings.fillLevel = (completedNodes / totalNodes) * 100;
            } else {
                this.settings.fillLevel = 0;
            }

            // Calculate vessel width based on total nodes
            // Map node count to width (30-100px)
            // Use logarithmic scale for better visualization
            const nodeScale = Math.min(100, Math.max(1, totalNodes));
            const widthPercent = Math.log(nodeScale + 1) / Math.log(101); // Log scale 0-1
            const newWidth = this.settings.baseWidth + (this.settings.maxWidth - this.settings.baseWidth) * widthPercent;

            // Smoothly transition width
            if (this.canvas.width !== Math.round(newWidth)) {
                this.canvas.width = Math.round(newWidth);
            }
        }
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Update time
        this.time += this.settings.waveSpeed;

        // Draw water
        this.drawWater();

        // Draw vessel border
        this.drawBorder();

        // Draw subtle info
        this.drawInfo();
    }

    drawWater() {
        const fillHeight = this.canvas.height * (1 - this.settings.fillLevel / 100);

        // Create gradient
        const gradient = this.ctx.createLinearGradient(0, fillHeight, 0, this.canvas.height);
        gradient.addColorStop(0, 'rgba(51, 226, 255, 0.2)');
        gradient.addColorStop(0.5, 'rgba(0, 150, 255, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 118, 254, 0.4)');

        // Draw wave
        this.ctx.beginPath();

        for (let x = 0; x <= this.canvas.width; x++) {
            const waveY = fillHeight +
                Math.sin(x * this.wave.frequency + this.time * this.wave.speed) *
                this.wave.amplitude;

            if (x === 0) {
                this.ctx.moveTo(x, waveY);
            } else {
                this.ctx.lineTo(x, waveY);
            }
        }

        // Complete shape
        this.ctx.lineTo(this.canvas.width, this.canvas.height);
        this.ctx.lineTo(0, this.canvas.height);
        this.ctx.closePath();

        // Fill
        this.ctx.fillStyle = gradient;
        this.ctx.fill();
    }

    drawBorder() {
        this.ctx.strokeStyle = 'rgba(51, 226, 255, 0.5)';
        this.ctx.lineWidth = 1;

        // Draw vessel shape (no top)
        this.ctx.beginPath();
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(0, this.canvas.height - 3);
        this.ctx.quadraticCurveTo(0, this.canvas.height, 3, this.canvas.height);
        this.ctx.lineTo(this.canvas.width - 3, this.canvas.height);
        this.ctx.quadraticCurveTo(this.canvas.width, this.canvas.height, this.canvas.width, this.canvas.height - 3);
        this.ctx.lineTo(this.canvas.width, 0);
        this.ctx.stroke();
    }

    drawInfo() {
        // Draw tiny node count at top
        if (this.settings.totalNodes > 0) {
            this.ctx.fillStyle = 'rgba(51, 226, 255, 0.6)';
            this.ctx.font = '9px Roboto Mono';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(
                `${this.settings.completedNodes}/${this.settings.totalNodes}`,
                this.canvas.width / 2,
                10
            );
        }
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('mini-vessel-canvas')) {
        window.miniVessel = new MiniVessel();
    }
});