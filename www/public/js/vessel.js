// Progress Vessel Widget Controller - 3 Visualization Modes
class VesselController {
    constructor() {
        this.vessel = document.getElementById('vessel');
        this.container = document.getElementById('vessel-container');
        this.stats = document.getElementById('completion-percent');

        this.currentMode = 'waves';

        // Extended settings with all parameters
        this.settings = {
            mode: 'waves',
            fillLevel: 30,
            width: 200,
            height: 100,
            waveSpeed: 6,  // Slower default
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
        this.setupModeSelector();
        this.setupSliders();
        this.setupConfigManagement();
        this.switchMode('waves');
        this.updateConfig();
    }

    setupModeSelector() {
        const modeButtons = document.querySelectorAll('.vessel-mode');
        modeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                modeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.switchMode(btn.dataset.mode);
            });
        });
    }

    switchMode(mode) {
        this.currentMode = mode;
        this.settings.mode = mode;

        // Clear vessel
        this.vessel.innerHTML = '';
        this.vessel.className = '';

        // Build mode-specific structure
        switch(mode) {
            case 'waves':
                this.buildWavesMode();
                break;
            case 'orb':
                this.buildOrbMode();
                break;
            case 'plasma':
                this.buildPlasmaMode();
                break;
        }

        this.updateVessel();
        this.updateConfig();
    }

    buildWavesMode() {
        this.vessel.innerHTML = `
            <div id="water-layer-3" class="water-layer">
                <div class="wave-shape wave-back"></div>
            </div>
            <div id="water-layer-2" class="water-layer">
                <div class="wave-shape wave-middle"></div>
            </div>
            <div id="water-layer-1" class="water-layer">
                <div class="wave-shape wave-front"></div>
            </div>
            <div id="water-bubbles"></div>
            <div id="vessel-glow"></div>
        `;

        this.waterLayers = [
            document.getElementById('water-layer-1'),
            document.getElementById('water-layer-2'),
            document.getElementById('water-layer-3')
        ];
        this.bubbles = document.getElementById('water-bubbles');
        this.glow = document.getElementById('vessel-glow');
    }

    buildOrbMode() {
        this.vessel.classList.add('vessel-orb');
        this.vessel.innerHTML = `
            <div class="orb-core"></div>
            <div class="orb-liquid"></div>
            <div class="orb-ring"></div>
            <div class="orb-ring" style="animation-delay: 0.5s"></div>
            <div class="orb-ring" style="animation-delay: 1s"></div>
        `;

        this.orbCore = this.vessel.querySelector('.orb-core');
        this.orbLiquid = this.vessel.querySelector('.orb-liquid');
    }

    buildPlasmaMode() {
        this.vessel.classList.add('vessel-plasma');
        this.vessel.innerHTML = `
            <div class="plasma-field"></div>
            <div class="plasma-core"></div>
            <div class="plasma-bolts"></div>
        `;

        this.plasmaField = this.vessel.querySelector('.plasma-field');
        this.plasmaCore = this.vessel.querySelector('.plasma-core');
        this.plasmaBolts = this.vessel.querySelector('.plasma-bolts');

        // Create plasma bolts
        this.createPlasmaBolts();
    }

    createPlasmaBolts() {
        if (!this.plasmaBolts) return;

        this.plasmaBolts.innerHTML = '';
        for (let i = 0; i < this.settings.bubbleCount; i++) {
            const bolt = document.createElement('div');
            bolt.className = 'plasma-bolt';
            bolt.style.left = `${10 + Math.random() * 80}%`;
            bolt.style.animationDelay = `${Math.random() * 1.5}s`;
            bolt.style.animationDuration = `${1 + Math.random() * 2}s`;
            this.plasmaBolts.appendChild(bolt);
        }
    }

    setupSliders() {
        const sliderConfigs = [
            { id: 'fill-level', prop: 'fillLevel', handler: () => this.updateFill() },
            { id: 'vessel-width', prop: 'width', handler: () => this.updateDimensions() },
            { id: 'vessel-height', prop: 'height', handler: () => this.updateDimensions() },
            { id: 'wave-speed', prop: 'waveSpeed', handler: () => this.updateAnimation() },
            { id: 'wave-height', prop: 'waveHeight', handler: () => this.updateWaveHeight() },
            { id: 'turbulence', prop: 'turbulence', handler: () => this.updateEffects() },
            { id: 'glow-intensity', prop: 'glowIntensity', handler: () => this.updateEffects() },
            { id: 'bubble-count', prop: 'bubbleCount', handler: () => this.updateParticles() },
            { id: 'refraction', prop: 'refraction', handler: () => this.updateDistortion() },
            { id: 'viscosity', prop: 'viscosity', handler: () => this.updateFluidDynamics() },
            { id: 'surface-tension', prop: 'surfaceTension', handler: () => this.updateFluidDynamics() },
            { id: 'color-shift', prop: 'colorShift', handler: () => this.updateColors() }
        ];

        sliderConfigs.forEach(config => {
            const slider = document.getElementById(config.id);
            const value = document.getElementById(`${config.id}-value`);

            if (slider) {
                slider.addEventListener('input', (e) => {
                    this.settings[config.prop] = parseFloat(e.target.value);
                    if (value) value.textContent = e.target.value;
                    config.handler();
                    this.updateConfig();
                });
            }
        });
    }

    updateFill() {
        const fill = this.settings.fillLevel;
        this.stats.textContent = `${Math.round(fill)}%`;

        switch(this.currentMode) {
            case 'waves':
                if (this.waterLayers) {
                    this.waterLayers.forEach((layer, i) => {
                        const layerHeight = fill - (i * 2);
                        layer.style.height = `${Math.max(0, layerHeight)}%`;
                    });
                }
                break;

            case 'orb':
                if (this.orbLiquid) {
                    this.orbLiquid.style.height = `${fill}%`;
                    this.orbCore.style.transform = `translate(-50%, -50%) scale(${0.5 + fill/200})`;
                }
                break;

            case 'plasma':
                if (this.plasmaCore) {
                    this.plasmaCore.style.height = `${fill}%`;
                    this.plasmaCore.style.opacity = `${0.3 + fill/150}`;
                }
                break;
        }
    }

    updateDimensions() {
        this.vessel.style.width = `${this.settings.width}px`;
        this.vessel.style.height = `${this.settings.height}px`;
    }

    updateAnimation() {
        const speed = this.settings.waveSpeed;

        switch(this.currentMode) {
            case 'waves':
                if (this.waterLayers) {
                    this.waterLayers.forEach((layer, i) => {
                        const shapes = layer.querySelectorAll('.wave-shape');
                        shapes.forEach(shape => {
                            shape.style.animationDuration = `${speed + i * 0.5}s`;
                        });
                    });
                }
                break;

            case 'orb':
                if (this.orbCore) {
                    this.orbCore.style.animationDuration = `${speed}s`;
                    this.orbLiquid.style.animationDuration = `${speed * 1.5}s`;
                }
                break;

            case 'plasma':
                if (this.plasmaField) {
                    this.plasmaField.style.animationDuration = `${speed * 2}s`;
                    this.plasmaCore.style.animationDuration = `${speed}s, ${speed * 0.8}s`;
                }
                break;
        }
    }

    updateWaveHeight() {
        if (this.currentMode !== 'waves') return;

        const waveShapes = document.querySelectorAll('.wave-shape');
        waveShapes.forEach((shape, index) => {
            const baseHeight = 25 - (index * 5);
            const newHeight = baseHeight + this.settings.waveHeight;
            shape.style.height = `${newHeight}px`;
            shape.style.top = `-${newHeight / 2}px`;
        });
    }

    updateEffects() {
        const turb = this.settings.turbulence;
        const glow = this.settings.glowIntensity;

        switch(this.currentMode) {
            case 'waves':
                if (this.waterLayers) {
                    this.waterLayers.forEach(layer => {
                        layer.style.filter = `blur(${turb/10}px) brightness(${1 + glow/200})`;
                    });

                    if (this.glow) {
                        this.glow.style.opacity = glow/100;
                    }
                }
                break;

            case 'orb':
                if (this.orbCore) {
                    this.orbCore.style.filter = `blur(${turb/5}px) brightness(${1 + glow/100})`;
                    this.orbCore.style.boxShadow = `0 0 ${20 + glow/2}px rgba(51, 226, 255, ${glow/100})`;
                }
                break;

            case 'plasma':
                if (this.plasmaField) {
                    this.plasmaField.style.filter = `blur(${turb/3}px) contrast(${1 + glow/100})`;
                    this.vessel.style.boxShadow = `
                        inset 0 0 ${50 + glow}px rgba(138, 43, 226, ${glow/200}),
                        0 0 ${30 + glow/2}px rgba(138, 43, 226, ${glow/300})`;
                }
                break;
        }
    }

    updateParticles() {
        const count = this.settings.bubbleCount;

        switch(this.currentMode) {
            case 'waves':
                if (this.bubbles) {
                    this.bubbles.innerHTML = '';
                    for (let i = 0; i < count; i++) {
                        const bubble = document.createElement('div');
                        bubble.style.cssText = `
                            position: absolute;
                            width: ${2 + Math.random() * 6}px;
                            height: ${2 + Math.random() * 6}px;
                            background: radial-gradient(circle, rgba(255, 255, 255, 0.4) 0%, transparent 70%);
                            border-radius: 50%;
                            left: ${10 + Math.random() * 80}%;
                            animation: bubble ${6 + Math.random() * 6}s infinite;
                            animation-delay: ${Math.random() * 4}s;
                        `;
                        this.bubbles.appendChild(bubble);
                    }
                }
                break;

            case 'plasma':
                this.createPlasmaBolts();
                break;
        }
    }

    updateDistortion() {
        const refract = this.settings.refraction;

        if (this.currentMode === 'waves' && this.waterLayers) {
            this.waterLayers[0].style.transform = `scaleX(${1 + refract * 0.01}) skewX(${refract * 0.5}deg)`;
            this.waterLayers[1].style.transform = `scaleX(${1 + refract * 0.008}) skewX(${-refract * 0.3}deg)`;
        }
    }

    updateFluidDynamics() {
        const visc = this.settings.viscosity;
        const tension = this.settings.surfaceTension;

        // Create dynamic style for fluid behavior
        const style = document.getElementById('fluid-dynamics-style') || document.createElement('style');
        style.id = 'fluid-dynamics-style';

        if (this.currentMode === 'waves') {
            style.textContent = `
                .wave-shape {
                    transition: all ${visc/10}s cubic-bezier(${0.1 + tension/20}, 0.4, ${0.9 - tension/20}, 0.6);
                }
            `;
        } else if (this.currentMode === 'orb') {
            style.textContent = `
                .orb-liquid {
                    transition: all ${visc/10}s ease-out;
                    border-radius: ${50 - tension * 3}% ${50 - tension * 3}% 50% 50% / ${20 + tension * 2}% ${20 + tension * 2}% 50% 50%;
                }
            `;
        }

        if (!document.getElementById('fluid-dynamics-style')) {
            document.head.appendChild(style);
        }
    }

    updateColors() {
        const shift = this.settings.colorShift;

        this.vessel.style.filter = `hue-rotate(${shift}deg)`;

        // Update percentage color too
        if (this.stats) {
            this.stats.style.filter = `hue-rotate(${shift}deg)`;
        }
    }

    updateVessel() {
        this.updateFill();
        this.updateDimensions();
        this.updateAnimation();
        this.updateWaveHeight();
        this.updateEffects();
        this.updateParticles();
        this.updateDistortion();
        this.updateFluidDynamics();
        this.updateColors();
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
    }

    updateConfig() {
        const config = `mode:${this.settings.mode},fill:${this.settings.fillLevel},w:${this.settings.width},h:${this.settings.height},speed:${this.settings.waveSpeed},wave:${this.settings.waveHeight},turb:${this.settings.turbulence},glow:${this.settings.glowIntensity},bub:${this.settings.bubbleCount},refr:${this.settings.refraction},visc:${this.settings.viscosity},tens:${this.settings.surfaceTension},hue:${this.settings.colorShift}`;

        const configOutput = document.getElementById('vessel-config-output');
        if (configOutput) {
            configOutput.value = config;
        }
    }

    loadConfig(configString) {
        const parts = configString.split(',');
        const config = {};

        parts.forEach(part => {
            const [key, value] = part.split(':');
            config[key] = value;
        });

        // Update mode first
        if (config.mode) {
            const modeBtn = document.querySelector(`[data-mode="${config.mode}"]`);
            if (modeBtn) {
                modeBtn.click();
            }
        }

        // Update settings
        const mapping = {
            fill: 'fillLevel',
            w: 'width',
            h: 'height',
            speed: 'waveSpeed',
            wave: 'waveHeight',
            turb: 'turbulence',
            glow: 'glowIntensity',
            bub: 'bubbleCount',
            refr: 'refraction',
            visc: 'viscosity',
            tens: 'surfaceTension',
            hue: 'colorShift'
        };

        Object.entries(mapping).forEach(([key, prop]) => {
            if (config[key] !== undefined) {
                this.settings[prop] = parseFloat(config[key]);
            }
        });

        // Update all sliders
        Object.entries(this.settings).forEach(([prop, value]) => {
            const sliderId = prop.replace(/([A-Z])/g, '-$1').toLowerCase();
            const slider = document.getElementById(sliderId);
            const valueElem = document.getElementById(`${sliderId}-value`);

            if (slider) slider.value = value;
            if (valueElem) valueElem.textContent = value;
        });

        this.updateVessel();
        this.updateConfig();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('vessel')) {
        new VesselController();
    }
});