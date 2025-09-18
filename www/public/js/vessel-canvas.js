// Canvas-based Vessel Renderer with Real Wave Physics
class CanvasVessel {
    constructor() {
        this.container = document.getElementById('vessel-container');
        this.stats = document.getElementById('completion-percent');

        // Create canvas element
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'vessel-canvas';
        this.canvas.width = 280;
        this.canvas.height = 150;
        this.ctx = this.canvas.getContext('2d');

        // Animation properties
        this.time = 0;
        this.animationId = null;

        // Wave properties
        this.waves = [
            { amplitude: 5, frequency: 0.02, phase: 0, speed: 0.03, opacity: 0.9 },
            { amplitude: 3, frequency: 0.03, phase: Math.PI/3, speed: 0.02, opacity: 0.7 },
            { amplitude: 2, frequency: 0.04, phase: Math.PI/2, speed: 0.025, opacity: 0.5 }
        ];

        // Bubbles array
        this.bubbles = [];

        // Particles for effects
        this.particles = [];

        // Settings
        this.settings = {
            mode: 'waves',
            fillLevel: 30,
            width: 200,
            height: 100,
            waveSpeed: 1,
            waveHeight: 5,
            turbulence: 3,
            glowIntensity: 50,
            bubbleCount: 5,
            refraction: 2,
            viscosity: 5,
            surfaceTension: 3,
            colorShift: 0
        };

        this.init();
    }

    init() {
        // Replace vessel div with canvas
        const vessel = document.getElementById('vessel');
        if (vessel) {
            vessel.innerHTML = '';
            vessel.appendChild(this.canvas);
        }

        this.setupSliders();
        this.setupModeSelector();
        this.setupConfigManagement();

        // Apply initial dimensions
        this.updateDimensions();

        // Start animation
        this.animate();

        // Initialize bubbles
        this.initBubbles();
    }

    updateDimensions() {
        // Update canvas size based on settings
        this.canvas.width = this.settings.width;
        this.canvas.height = this.settings.height;

        // Update vessel container if needed
        const vessel = document.getElementById('vessel');
        if (vessel) {
            vessel.style.width = `${this.settings.width}px`;
            vessel.style.height = `${this.settings.height}px`;
        }
    }

    setupModeSelector() {
        const modeButtons = document.querySelectorAll('.vessel-mode');
        modeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                modeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.settings.mode = btn.dataset.mode;
                this.updateConfig();
            });
        });
    }

    setupSliders() {
        const sliderConfigs = [
            { id: 'fill-level', prop: 'fillLevel' },
            { id: 'vessel-width', prop: 'width', handler: () => this.updateDimensions() },
            { id: 'vessel-height', prop: 'height', handler: () => this.updateDimensions() },
            { id: 'wave-speed', prop: 'waveSpeed' },
            { id: 'wave-height', prop: 'waveHeight' },
            { id: 'turbulence', prop: 'turbulence' },
            { id: 'glow-intensity', prop: 'glowIntensity' },
            { id: 'bubble-count', prop: 'bubbleCount', handler: () => this.initBubbles() },
            { id: 'refraction', prop: 'refraction' },
            { id: 'viscosity', prop: 'viscosity' },
            { id: 'surface-tension', prop: 'surfaceTension' },
            { id: 'color-shift', prop: 'colorShift' }
        ];

        sliderConfigs.forEach(config => {
            const slider = document.getElementById(config.id);
            const value = document.getElementById(`${config.id}-value`);

            if (slider) {
                slider.value = this.settings[config.prop];
                slider.addEventListener('input', (e) => {
                    this.settings[config.prop] = parseFloat(e.target.value);
                    if (value) value.textContent = e.target.value;

                    // Call handler if defined
                    if (config.handler) {
                        config.handler();
                    }

                    this.updateConfig();
                });
            }
        });
    }

    initBubbles() {
        this.bubbles = [];
        for (let i = 0; i < this.settings.bubbleCount; i++) {
            this.bubbles.push({
                x: Math.random() * this.settings.width,
                y: this.settings.height + Math.random() * 50,
                radius: 1 + Math.random() * 3,
                speed: 0.5 + Math.random() * 1.5,
                wobble: Math.random() * Math.PI * 2,
                wobbleSpeed: 0.02 + Math.random() * 0.03,
                opacity: 0.3 + Math.random() * 0.4
            });
        }
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Update time
        this.time += this.settings.waveSpeed * 0.01;

        // Draw based on mode
        switch(this.settings.mode) {
            case 'waves':
                this.drawWavesMode();
                break;
            case 'orb':
                this.drawOrbMode();
                break;
            case 'plasma':
                this.drawPlasmaMode();
                break;
        }

        // Draw vessel border
        this.drawVesselBorder();

        // Stats are now hidden - no % display
    }

    drawWavesMode() {
        const fillHeight = this.canvas.height * (1 - this.settings.fillLevel / 100);

        // Apply color shift
        this.ctx.save();
        if (this.settings.colorShift !== 0) {
            this.ctx.filter = `hue-rotate(${this.settings.colorShift}deg)`;
        }

        // Calculate wave dampening as fill level increases (to prevent slanting)
        const fillPercent = this.settings.fillLevel / 100;
        const waveDampening = fillPercent > 0.7 ? 1 - ((fillPercent - 0.7) / 0.3) : 1;

        // Draw multiple wave layers
        this.waves.forEach((wave, index) => {
            this.ctx.globalAlpha = wave.opacity * (this.settings.glowIntensity / 100);

            // Create gradient for this wave
            const gradient = this.ctx.createLinearGradient(0, fillHeight, 0, this.canvas.height);

            if (index === 0) {
                gradient.addColorStop(0, 'rgba(51, 226, 255, 0.3)');
                gradient.addColorStop(0.5, 'rgba(0, 150, 255, 0.6)');
                gradient.addColorStop(1, 'rgba(0, 118, 254, 0.8)');
            } else if (index === 1) {
                gradient.addColorStop(0, 'rgba(0, 180, 255, 0.2)');
                gradient.addColorStop(1, 'rgba(0, 100, 200, 0.5)');
            } else {
                gradient.addColorStop(0, 'rgba(0, 100, 180, 0.1)');
                gradient.addColorStop(1, 'rgba(0, 50, 150, 0.3)');
            }

            // Draw wave
            this.ctx.beginPath();

            // Start from left edge, ensuring we connect properly
            let firstY = fillHeight;
            for (let x = 0; x <= this.canvas.width; x++) {
                const waveY = fillHeight +
                    Math.sin(x * wave.frequency + this.time * wave.speed + wave.phase) *
                    (wave.amplitude * this.settings.waveHeight / 5 * waveDampening) +
                    Math.sin(x * wave.frequency * 2 + this.time * wave.speed * 1.5) *
                    (wave.amplitude * this.settings.turbulence / 10 * waveDampening);

                if (x === 0) {
                    firstY = waveY;
                    this.ctx.moveTo(x, waveY);
                } else {
                    // Add surface tension effect
                    const tension = this.settings.surfaceTension / 10;
                    const prevX = x - 1;
                    const prevY = fillHeight +
                        Math.sin(prevX * wave.frequency + this.time * wave.speed + wave.phase) *
                        (wave.amplitude * this.settings.waveHeight / 5 * waveDampening);

                    const cpx = prevX + 0.5;
                    const cpy = prevY * (1 - tension) + waveY * tension;

                    this.ctx.quadraticCurveTo(cpx, cpy, x, waveY);
                }
            }

            // Complete the shape - ensure no slant by extending properly
            this.ctx.lineTo(this.canvas.width, this.canvas.height + 10); // Extend below bottom
            this.ctx.lineTo(0, this.canvas.height + 10);
            this.ctx.lineTo(0, firstY); // Close back to first point
            this.ctx.closePath();

            // Fill with gradient
            this.ctx.fillStyle = gradient;
            this.ctx.fill();

            // Add refraction effect
            if (this.settings.refraction > 0 && index === 0) {
                this.ctx.save();
                this.ctx.globalCompositeOperation = 'screen';
                this.ctx.globalAlpha = this.settings.refraction / 20;
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
                this.ctx.fill();
                this.ctx.restore();
            }
        });

        // Bubbles disabled per user request
        // this.drawBubbles();

        this.ctx.restore();
    }

    drawBubbles() {
        this.ctx.save();
        this.ctx.globalCompositeOperation = 'screen';

        this.bubbles.forEach(bubble => {
            // Update bubble position
            bubble.y -= bubble.speed * (11 - this.settings.viscosity) / 10;
            bubble.wobble += bubble.wobbleSpeed;
            bubble.x += Math.sin(bubble.wobble) * 0.5;

            // Reset bubble when it reaches top
            if (bubble.y < -bubble.radius) {
                bubble.y = this.canvas.height + bubble.radius;
                bubble.x = Math.random() * this.canvas.width;
            }

            // Only draw if below water line
            const fillHeight = this.canvas.height * (1 - this.settings.fillLevel / 100);
            if (bubble.y > fillHeight) {
                this.ctx.globalAlpha = bubble.opacity;

                // Draw bubble with gradient
                const gradient = this.ctx.createRadialGradient(
                    bubble.x - bubble.radius * 0.3,
                    bubble.y - bubble.radius * 0.3,
                    0,
                    bubble.x,
                    bubble.y,
                    bubble.radius
                );
                gradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
                gradient.addColorStop(0.5, 'rgba(200, 240, 255, 0.3)');
                gradient.addColorStop(1, 'rgba(150, 220, 255, 0.1)');

                this.ctx.beginPath();
                this.ctx.arc(bubble.x, bubble.y, bubble.radius, 0, Math.PI * 2);
                this.ctx.fillStyle = gradient;
                this.ctx.fill();
            }
        });

        this.ctx.restore();
    }

    drawOrbMode() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const radius = Math.min(this.settings.width, this.settings.height) / 2;

        this.ctx.save();

        // Create circular clip
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius - 2, 0, Math.PI * 2);
        this.ctx.clip();

        // Draw liquid fill
        const fillHeight = this.canvas.height * (1 - this.settings.fillLevel / 100);

        // Create swirling gradient
        const gradient = this.ctx.createRadialGradient(
            centerX, centerY + radius, 0,
            centerX, centerY, radius
        );
        gradient.addColorStop(0, 'rgba(51, 226, 255, 0.9)');
        gradient.addColorStop(0.5, 'rgba(0, 150, 255, 0.7)');
        gradient.addColorStop(1, 'rgba(0, 50, 150, 0.3)');

        // Draw swirling liquid
        this.ctx.beginPath();
        for (let x = centerX - radius; x <= centerX + radius; x++) {
            const waveY = fillHeight +
                Math.sin((x - centerX) * 0.02 + this.time * 0.02) *
                this.settings.waveHeight;

            if (x === centerX - radius) {
                this.ctx.moveTo(x, waveY);
            } else {
                this.ctx.lineTo(x, waveY);
            }
        }

        this.ctx.lineTo(centerX + radius, this.canvas.height);
        this.ctx.lineTo(centerX - radius, this.canvas.height);
        this.ctx.closePath();

        this.ctx.fillStyle = gradient;
        this.ctx.fill();

        // Draw core glow
        const coreSize = 20 + this.settings.fillLevel / 2;
        const coreGradient = this.ctx.createRadialGradient(
            centerX, centerY, 0,
            centerX, centerY, coreSize
        );
        coreGradient.addColorStop(0, `rgba(255, 255, 255, ${this.settings.glowIntensity / 100})`);
        coreGradient.addColorStop(0.5, `rgba(51, 226, 255, ${this.settings.glowIntensity / 200})`);
        coreGradient.addColorStop(1, 'transparent');

        this.ctx.globalCompositeOperation = 'screen';
        this.ctx.fillStyle = coreGradient;
        this.ctx.fillRect(centerX - coreSize, centerY - coreSize, coreSize * 2, coreSize * 2);

        this.ctx.restore();
    }

    drawPlasmaMode() {
        const fillHeight = this.canvas.height * (1 - this.settings.fillLevel / 100);

        this.ctx.save();

        // Draw plasma field
        for (let i = 0; i < 3; i++) {
            const gradient = this.ctx.createRadialGradient(
                this.canvas.width / 2 + Math.sin(this.time * 0.02 + i) * 50,
                fillHeight + Math.cos(this.time * 0.03 + i) * 20,
                0,
                this.canvas.width / 2,
                this.canvas.height / 2,
                100
            );

            gradient.addColorStop(0, `rgba(138, 43, 226, ${0.3 + i * 0.1})`);
            gradient.addColorStop(0.5, `rgba(255, 0, 255, ${0.2 + i * 0.05})`);
            gradient.addColorStop(1, 'rgba(0, 255, 255, 0.1)');

            this.ctx.globalCompositeOperation = 'screen';
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, fillHeight, this.canvas.width, this.canvas.height - fillHeight);
        }

        // Draw energy bolts
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        this.ctx.lineWidth = 1;
        this.ctx.shadowBlur = 10;
        this.ctx.shadowColor = 'rgba(138, 43, 226, 0.8)';

        for (let i = 0; i < this.settings.bubbleCount; i++) {
            const x = (this.time * 20 + i * 100) % this.canvas.width;
            const startY = this.canvas.height;
            const endY = fillHeight;

            this.ctx.beginPath();
            this.ctx.moveTo(x, startY);

            // Create lightning-like path
            let currentY = startY;
            while (currentY > endY) {
                currentY -= 5 + Math.random() * 10;
                const offsetX = x + (Math.random() - 0.5) * 20;
                this.ctx.lineTo(offsetX, currentY);
            }

            this.ctx.stroke();
        }

        this.ctx.restore();
    }

    drawVesselBorder() {
        this.ctx.strokeStyle = '#33E2FF';
        this.ctx.lineWidth = 2;
        this.ctx.shadowBlur = 5;
        this.ctx.shadowColor = '#33E2FF';

        // Draw vessel shape (no top border)
        this.ctx.beginPath();
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(0, this.canvas.height - 8);
        this.ctx.quadraticCurveTo(0, this.canvas.height, 8, this.canvas.height);
        this.ctx.lineTo(this.canvas.width - 8, this.canvas.height);
        this.ctx.quadraticCurveTo(this.canvas.width, this.canvas.height, this.canvas.width, this.canvas.height - 8);
        this.ctx.lineTo(this.canvas.width, 0);
        this.ctx.stroke();

        this.ctx.shadowBlur = 0;
    }

    setupConfigManagement() {
        const configOutput = document.getElementById('vessel-config-output');
        const configInput = document.getElementById('vessel-config-input');
        const copyBtn = document.getElementById('copy-vessel-config');
        const loadBtn = document.getElementById('load-vessel-config');

        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                configOutput.select();
                document.execCommand('copy');
                copyBtn.textContent = '✓';
                setTimeout(() => copyBtn.textContent = '📋', 1000);
            });
        }

        if (loadBtn) {
            loadBtn.addEventListener('click', () => {
                const config = configInput.value.trim();
                if (config) {
                    this.loadConfig(config);
                    configInput.value = '';
                }
            });
        }

        this.updateConfig();
    }

    updateConfig() {
        const config = Object.entries(this.settings)
            .map(([k, v]) => `${k.substring(0, 3)}:${v}`)
            .join(',');

        const configOutput = document.getElementById('vessel-config-output');
        if (configOutput) {
            configOutput.value = config;
        }
    }

    loadConfig(configString) {
        const parts = configString.split(',');
        parts.forEach(part => {
            const [key, value] = part.split(':');
            const fullKey = Object.keys(this.settings).find(k => k.substring(0, 3) === key);
            if (fullKey) {
                this.settings[fullKey] = isNaN(value) ? value : parseFloat(value);
            }
        });

        // Update UI
        Object.entries(this.settings).forEach(([key, value]) => {
            const sliderId = key.replace(/([A-Z])/g, '-$1').toLowerCase();
            const slider = document.getElementById(sliderId);
            const valueElem = document.getElementById(`${sliderId}-value`);
            if (slider) slider.value = value;
            if (valueElem) valueElem.textContent = value;
        });

        if (this.settings.bubbleCount !== this.bubbles.length) {
            this.initBubbles();
        }

        this.updateConfig();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('vessel')) {
        // Replace the old vessel controller
        window.vesselController = new CanvasVessel();
    }
});