// Main Application Class
class KnowledgeGraphApp {
    constructor() {
        this.currentPhase = 'discover';
        this.currentView = 'start'; // Track current view (start or discover)
        this.graph = null;
        this.ws = null;
        this.apiBase = 'http://localhost:8880/api';
        this.phases = {};
        this.minimap = null;
        this.isModified = false;
        this.currentGraphName = null;
        this.init();
    }

    async init() {
        // Handle initial route based on URL hash
        this.handleInitialRoute();

        // Setup history popstate listener
        window.addEventListener('popstate', (e) => {
            this.handleHistoryChange(e);
        });

        await this.loadGraphList();
        await this.populateStartGraphSelector();
        // Don't load graph initially - wait for user selection
        this.setupWebSocket();
        this.bindEvents();
        this.bindStartViewEvents();
        this.loadPhase(this.currentPhase);
        this.initializeMinimap();

        // Debug: Check if entity sidebar exists
        const entitySidebar = document.getElementById('entity-sidebar');
        if (entitySidebar) {
            console.log('Entity sidebar found, checking visibility:', {
                display: window.getComputedStyle(entitySidebar).display,
                visibility: window.getComputedStyle(entitySidebar).visibility,
                width: window.getComputedStyle(entitySidebar).width,
                classes: entitySidebar.className
            });
        } else {
            console.error('Entity sidebar not found in DOM!');
        }
    }

    async loadGraphList() {
        try {
            const response = await fetch(`${this.apiBase}/graphs/list`);
            const data = await response.json();
            const selector = document.getElementById('graph-selector');

            // Clear and populate selector
            selector.innerHTML = '';
            data.graphs.forEach(graph => {
                const option = document.createElement('option');
                option.value = graph.name;
                option.textContent = graph.name;
                selector.appendChild(option);
            });

            return data.graphs; // Return for use in other methods
        } catch (error) {
            console.error('Failed to load graph list:', error);
            return [];
        }
    }

    async populateStartGraphSelector() {
        try {
            const graphs = await this.loadGraphList();
            const startSelector = document.getElementById('start-graph-selector');

            // Clear and populate start page selector with placeholder
            startSelector.innerHTML = '<option value="">Select a graph to load...</option>';
            graphs.forEach(graph => {
                const option = document.createElement('option');
                option.value = graph.name;
                option.textContent = graph.name;
                startSelector.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to populate start graph selector:', error);
        }
    }

    async loadGraph(graphName = null) {
        try {
            // Get current selected graph if no specific name provided
            const selectedGraph = graphName || document.getElementById('graph-selector')?.value || 'spec-graph.json';

            const response = await fetch(`${this.apiBase}/graph?name=${encodeURIComponent(selectedGraph)}`);
            this.graph = await response.json();

            console.log(`Loaded graph: ${this.graph.meta?.loadedFrom || selectedGraph}`);

            // Track current graph and reset modified state
            this.currentGraphName = selectedGraph;
            this.isModified = false;
            this.updateDropdownDisplay();

            // Update project name display if in discover view
            if (this.currentView === 'discover' && this.graph?.meta?.project?.name) {
                const projectNameEl = document.getElementById('project-name');
                if (projectNameEl) {
                    projectNameEl.textContent = `— ${this.graph.meta.project.name}`;
                }
            }

            this.updateEntitySidebar();
            if (this.minimap) {
                this.minimap.updateGraph(this.graph);
            }
        } catch (error) {
            console.error('Failed to load graph:', error);
            this.showError(`Failed to load graph: ${graphName || 'default'}`);
        }
    }

    setupWebSocket() {
        try {
            // Use the same host as the main app but different port
            const wsHost = window.location.hostname || 'localhost';
            const wsUrl = `ws://${wsHost}:8881`;

            console.log('Connecting to WebSocket:', wsUrl);
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.showSuccess('Connected to real-time updates');
            };

            this.ws.onmessage = (event) => {
                try {
                    const { type, data } = JSON.parse(event.data);
                    this.handleRealtimeUpdate(type, data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            this.ws.onerror = (error) => {
                console.warn('WebSocket error (will retry):', error);
                // Don't show error to user on every retry
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected, retrying in 3s...');
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.setupWebSocket(), 3000);
            };
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
            // Retry after 3 seconds
            setTimeout(() => this.setupWebSocket(), 3000);
        }
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
                this.markAsModified();
                this.loadGraph();
                if (this.phases.discover) {
                    this.phases.discover.refresh();
                }
                break;
            default:
                console.log('Unknown update type:', type, data);
        }
    }

    showStartView(skipHistory = false) {
        const startView = document.getElementById('start-view');
        const discoverView = document.getElementById('discover-view');

        // Reset classes for start view
        startView.classList.remove('hidden', 'waking', 'awake');
        discoverView.classList.add('hidden');
        discoverView.classList.remove('visible');
        this.currentView = 'start';

        // Update URL and history
        if (!skipHistory) {
            window.history.pushState({ view: 'start' }, '', '#start');
        }

        // Update phase button states
        document.querySelectorAll('.phase-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.phase === 'start');
        });

        // Focus on input
        setTimeout(() => {
            document.getElementById('start-ai-prompt').focus();
        }, 100);
    }

    async showDiscoverView(skipHistory = false) {
        const startView = document.getElementById('start-view');
        const discoverView = document.getElementById('discover-view');

        // Prepare discover view
        discoverView.classList.remove('hidden');

        // Small delay to ensure discover view is ready
        await new Promise(resolve => setTimeout(resolve, 50));

        // Start the awakening animation
        startView.classList.add('waking');

        // Fade in discover view
        setTimeout(() => {
            discoverView.classList.add('visible');
        }, 200);

        // Display project name if available
        if (this.graph?.meta?.project?.name) {
            const projectNameEl = document.getElementById('project-name');
            if (projectNameEl) {
                projectNameEl.textContent = `— ${this.graph.meta.project.name}`;
            }
        }

        // After slide animation, dock the start view as header
        setTimeout(() => {
            startView.classList.remove('waking');
            startView.classList.add('awake');

            // Show the docked hamburger menu
            const dockedHamburger = document.querySelector('.docked-hamburger');
            if (dockedHamburger) {
                dockedHamburger.style.display = 'flex';
            }

            // Hide original AI prompt bar since start view is now the header
            const originalPromptBar = document.getElementById('ai-prompt-bar');
            if (originalPromptBar) {
                originalPromptBar.style.display = 'none';
            }

            // Animate sidebars in
            const phaseSidebar = document.getElementById('phase-sidebar-inner');
            if (phaseSidebar) {
                phaseSidebar.classList.remove('hidden');
                phaseSidebar.classList.add('slide-in');
            }

            const entitySidebar = document.getElementById('entity-sidebar');
            if (entitySidebar) {
                entitySidebar.classList.add('slide-in');
            }
        }, 800);

        this.currentView = 'discover';

        // Update URL and history
        if (!skipHistory) {
            window.history.pushState({ view: 'discover', phase: this.currentPhase }, '', '#discover');
        }

        // Update phase button states
        document.querySelectorAll('.phase-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.phase === 'discover');
        });
    }

    handleInitialRoute() {
        const hash = window.location.hash.slice(1); // Remove #
        if (hash === 'discover' || hash.startsWith('discover/')) {
            this.showDiscoverView(true); // Skip history since we're loading from URL
        } else {
            // Default to start page
            this.showStartView(true); // Skip history since we're loading from URL
            if (hash !== 'start') {
                // Update URL to reflect start page
                window.history.replaceState({ view: 'start' }, '', '#start');
            }
        }
    }

    handleHistoryChange(event) {
        const state = event.state || {};
        if (state.view === 'discover') {
            this.showDiscoverView(true); // Skip history to prevent infinite loop
        } else if (state.view === 'start') {
            this.showStartView(true); // Skip history to prevent infinite loop
        }
    }

    bindStartViewEvents() {
        const startInput = document.getElementById('start-ai-prompt');
        const startSubmit = document.getElementById('start-submit');
        const startGraphSelector = document.getElementById('start-graph-selector');

        // Submit button click
        startSubmit.addEventListener('click', () => {
            this.handleStartSubmit();
        });

        // Enter key in input
        startInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleStartSubmit();
            }
        });

        // Graph selector change - load and go to discover
        startGraphSelector.addEventListener('change', async (e) => {
            const selectedGraph = e.target.value;
            if (selectedGraph) {
                await this.loadGraph(selectedGraph);
                // Sync with main graph selector
                const mainSelector = document.getElementById('graph-selector');
                if (mainSelector) {
                    mainSelector.value = selectedGraph;
                }
                // Switch to discover view
                this.showDiscoverView();
            }
        });
    }

    async handleStartSubmit() {
        const input = document.getElementById('start-ai-prompt');
        const value = input.value.trim();

        if (value) {
            // Transfer value to main AI prompt
            const mainPrompt = document.getElementById('ai-prompt');
            if (mainPrompt) {
                mainPrompt.value = value;
            }

            // Switch to discover view
            this.showDiscoverView();

            // Trigger discover phase if available
            if (this.phases.discover && this.phases.discover.handleAIPrompt) {
                this.phases.discover.handleAIPrompt(value);
            }
        }
    }

    async handleStartLoadGraph() {
        const graphSelector = document.getElementById('start-graph-selector');
        const selectedGraph = graphSelector.value;

        // Load the selected graph
        if (selectedGraph) {
            await this.loadGraph(selectedGraph);
            // Sync with main graph selector
            const mainSelector = document.getElementById('graph-selector');
            if (mainSelector) {
                mainSelector.value = selectedGraph;
            }
        }

        // Switch to discover view
        this.showDiscoverView();
    }

    bindEvents() {
        // Graph management
        document.getElementById('graph-selector').addEventListener('change', async (e) => {
            await this.switchGraph(e.target.value);
        });

        document.getElementById('graph-new').addEventListener('click', () => {
            this.createNewGraph();
        });

        document.getElementById('graph-save').addEventListener('click', () => {
            this.saveGraph();
        });

        document.getElementById('graph-restore').addEventListener('click', () => {
            this.restoreGraph();
        });

        // Phase navigation
        document.querySelectorAll('.phase-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (!e.target.disabled) {
                    const phase = e.target.dataset.phase;
                    if (phase === 'start') {
                        this.showStartView();
                    } else {
                        this.switchPhase(phase);
                        if (this.currentView !== 'discover') {
                            this.showDiscoverView();
                        }
                    }
                }
            });
        });

        // AI Prompt buttons
        const uploadBtn = document.getElementById('ai-upload');
        const expandBtn = document.getElementById('ai-expand');
        const promptInput = document.getElementById('ai-prompt');
        const promptMultiline = document.getElementById('ai-prompt-multiline');

        // Upload button - show alert for now
        uploadBtn.addEventListener('click', () => {
            alert('Upload functionality coming soon!');
        });

        // Expand/collapse button
        expandBtn.addEventListener('click', () => {
            const isExpanded = !promptMultiline.classList.contains('hidden');
            if (isExpanded) {
                // Collapse to single line
                promptInput.value = promptMultiline.value;
                promptMultiline.classList.add('hidden');
                promptInput.classList.remove('hidden');
                expandBtn.querySelector('.icon-circle').textContent = '⋯';
                expandBtn.setAttribute('title', 'Expand to multiline');
            } else {
                // Expand to multiline
                promptMultiline.value = promptInput.value;
                promptInput.classList.add('hidden');
                promptMultiline.classList.remove('hidden');
                promptMultiline.focus();
                expandBtn.querySelector('.icon-circle').textContent = '−';
                expandBtn.setAttribute('title', 'Collapse to single line');
            }
        });

        // Sync values between single and multiline
        promptInput.addEventListener('input', (e) => {
            promptMultiline.value = e.target.value;
        });

        promptMultiline.addEventListener('input', (e) => {
            promptInput.value = e.target.value.replace(/\n/g, ' ');
        });

        // Hamburger menu toggle (both original and docked)
        const hamburgerBtn = document.getElementById('phase-menu-toggle');
        const dockedHamburgerBtn = document.getElementById('docked-phase-menu-toggle');
        const phaseSidebar = document.getElementById('phase-sidebar-inner');

        if (hamburgerBtn && phaseSidebar) {
            hamburgerBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.togglePhaseSidebar();
            });
        }

        // Add event for docked hamburger
        if (dockedHamburgerBtn && phaseSidebar) {
            dockedHamburgerBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.togglePhaseSidebar();
            });
        }

        // Entity sidebar toggle
        const entitySidebarToggle = document.getElementById('entity-sidebar-toggle');
        if (entitySidebarToggle) {
            entitySidebarToggle.addEventListener('click', () => {
                this.toggleEntitySidebar();
            });
        }

        // AI prompt bar
        const aiSubmit = document.getElementById('ai-submit');
        const aiPrompt = document.getElementById('ai-prompt');

        aiSubmit.addEventListener('click', () => this.handleAIPrompt());
        aiPrompt.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleAIPrompt();
            }
        });

        // Graph refresh (if it exists)
        const graphRefresh = document.getElementById('graph-refresh');
        if (graphRefresh) {
            graphRefresh.addEventListener('click', () => {
                this.loadGraph();
            });
        }
    }

    async createNewGraph() {
        const name = prompt('Enter name for new graph (or leave empty for auto-name):');
        try {
            const response = await fetch(`${this.apiBase}/graphs/new`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const result = await response.json();
            if (result.success) {
                this.showSuccess(`Created new graph (backup: ${result.backup})`);
                // Reload everything - new graph is now active
                await this.loadGraphList();
                await this.loadGraph();
                // Update the dropdown to show we're on the main graph (which is now the new one)
                document.getElementById('graph-selector').value = 'spec-graph.json';
                // Reload the current phase to show the empty graph
                if (this.phases[this.currentPhase]) {
                    await this.phases[this.currentPhase].init();
                }
            }
        } catch (error) {
            this.showError('Failed to create new graph');
        }
    }

    async saveGraph() {
        const name = prompt('Save current graph as:', `graph-${new Date().toISOString().split('T')[0]}.json`);
        if (!name) return;

        try {
            const response = await fetch(`${this.apiBase}/graphs/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const result = await response.json();
            if (result.success) {
                this.showSuccess(`Graph saved as: ${result.savedAs}`);
                this.isModified = false; // Clear modified flag after successful save
                this.updateDropdownDisplay();
                await this.loadGraphList();
            }
        } catch (error) {
            this.showError('Failed to save graph');
        }
    }

    async switchGraph(name) {
        if (!confirm(`Switch to graph: ${name}? Current changes will be auto-backed up.`)) return;

        try {
            const response = await fetch(`${this.apiBase}/graphs/load`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const result = await response.json();
            if (result.success) {
                this.showSuccess(`Loaded: ${result.loaded} (auto-backup: ${result.autoBackup})`);
                await this.loadGraph('spec-graph.json'); // After loading, it becomes the main graph
            }
        } catch (error) {
            this.showError('Failed to load graph');
        }
    }

    async restoreGraph() {
        // Load the list and let user select which one to restore
        const selector = document.getElementById('graph-selector');
        const selected = selector.value;
        if (selected === 'spec-graph.json') {
            this.showInfo('Already using main graph');
            return;
        }
        await this.switchGraph(selected);
    }

    switchPhase(phaseName) {
        // Update nav buttons
        document.querySelectorAll('.phase-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.phase === phaseName);
        });

        this.currentPhase = phaseName;
        this.updateCurrentPhaseIndicator(phaseName);
        this.closePhaseSidebar(); // Close sidebar after selection
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

        // Show empty state if no graph is loaded
        if (!this.graph) {
            accordion.innerHTML = `
                <div style="padding: 30px 20px; text-align: center; color: #666;">
                    <div style="font-size: 2em; opacity: 0.3; margin-bottom: 15px;">⚡</div>
                    <p style="margin-bottom: 10px; font-size: 1.1em;">No graph loaded</p>
                    <p style="font-size: 0.9em; opacity: 0.7;">Select a graph from the start page or create a new one</p>
                </div>`;
            return;
        }

        // Create WHAT section (users, objectives, actions)
        const whatSection = document.createElement('div');
        whatSection.className = 'sidebar-section';
        whatSection.innerHTML = `
            <div class="section-header">
                <h3>— WHAT —</h3>
            </div>
            <div class="section-content" id="what-content"></div>
        `;

        // Create HOW section (requirements, interfaces, components, presentation, behavior)
        const howSection = document.createElement('div');
        howSection.className = 'sidebar-section';
        howSection.innerHTML = `
            <div class="section-header">
                <h3>— HOW —</h3>
            </div>
            <div class="section-content" id="how-content"></div>
        `;

        // Create SPECS section (references)
        const specsSection = document.createElement('div');
        specsSection.className = 'sidebar-section';
        specsSection.innerHTML = `
            <div class="section-header">
                <h3>— SPECS —</h3>
            </div>
            <div class="section-content" id="specs-content"></div>
        `;

        accordion.appendChild(whatSection);
        accordion.appendChild(howSection);
        accordion.appendChild(specsSection);

        // Populate sections
        this.populateWhatSection(document.getElementById('what-content'));
        this.populateHowSection(document.getElementById('how-content'));
        this.populateSpecsSection(document.getElementById('specs-content'));
    }

    populateWhatSection(container) {
        if (!this.graph.entities) return;

        // WHAT entities: users, objectives, actions
        const whatTypes = ['users', 'objectives', 'actions'];
        this.populateEntityTypes(container, whatTypes);
    }

    populateHowSection(container) {
        if (!this.graph.entities) return;

        // HOW entities: requirements, interfaces, components, presentation, behavior
        const howTypes = ['requirements', 'interfaces', 'components', 'presentation', 'behavior'];
        this.populateEntityTypes(container, howTypes);
    }

    populateEntityTypes(container, typesList) {
        if (!this.graph.entities) return;

        // Filter entities to only include specified types
        for (const type of typesList) {
            if (!this.graph.entities[type]) continue;

            const entities = this.graph.entities[type];
            const count = Object.keys(entities).length;
            if (count === 0) continue;

            const group = document.createElement('div');
            group.className = 'entity-group';

            const brailleCount = this.getCountDisplay(count);

            const header = document.createElement('div');
            header.className = 'entity-group-header';
            header.innerHTML = `
                <span class="entity-type-label">
                    ${this.formatTypeName(type)}
                </span>
                <div class="header-controls">
                    ${brailleCount}
                    <span class="expand-arrow">▶</span>
                </div>
            `;

            // Expand/collapse on clicking the type label or arrow
            const toggleExpand = () => {
                group.classList.toggle('expanded');
                header.querySelector('.expand-arrow').textContent =
                    group.classList.contains('expanded') ? '▼' : '▶';
            };

            header.querySelector('.entity-type-label').addEventListener('click', toggleExpand);
            header.querySelector('.expand-arrow').addEventListener('click', toggleExpand);

            // Add container for add button/input at the end
            const addContainer = document.createElement('div');
            addContainer.className = 'entity-add-container';
            addContainer.innerHTML = `
                <button class="add-entity-btn" data-type="${type}">+ Add ${type.slice(0, -1)}</button>
                <div class="entity-inline-input hidden">
                    <input type="text" class="entity-input" placeholder="Enter ${type.slice(0, -1)} name..." />
                    <div class="input-controls">
                        <button class="entity-save-btn" data-type="${type}">✓</button>
                        <button class="entity-cancel-btn">✕</button>
                    </div>
                </div>
            `;

            // Handle add button click
            addContainer.querySelector('.add-entity-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.showAddInput(addContainer, type);
            });


            const content = document.createElement('div');
            content.className = 'entity-group-content';

            // Add description at the top of the content
            const descriptions = this.getEntityDescriptions();
            const description = descriptions[type] || '';
            if (description) {
                const descriptionDiv = document.createElement('div');
                descriptionDiv.className = 'entity-description-content';
                descriptionDiv.textContent = description;
                content.appendChild(descriptionDiv);
            }

            // Add individual entities
            for (const [id, entity] of Object.entries(entities)) {
                const item = document.createElement('div');
                item.className = 'entity-item';
                item.innerHTML = `
                    <span class="entity-name">${entity.name || id}</span>
                    <span class="entity-edit-icon" title="Edit">✏️</span>
                `;
                item.dataset.entityRef = `${type.slice(0, -1)}:${id}`;
                item.dataset.entityId = id;
                item.dataset.entityType = type;

                // Handle entity name click
                item.querySelector('.entity-name').addEventListener('click', () => this.selectEntity(item.dataset.entityRef));

                // Handle edit icon click
                item.querySelector('.entity-edit-icon').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.editEntity(item);
                });

                content.appendChild(item);
            }

            // Add the add container at the end of the entity list
            content.appendChild(addContainer);

            // Handle input controls in add container
            const saveBtn = addContainer.querySelector('.entity-save-btn');
            const cancelBtn = addContainer.querySelector('.entity-cancel-btn');
            const input = addContainer.querySelector('.entity-input');

            saveBtn.addEventListener('click', async () => {
                const entityName = input.value.trim();
                if (entityName) {
                    const success = await this.addNewEntity(type, entityName);
                    if (success) {
                        input.value = '';
                        // Keep input open for adding more entities
                        input.focus();
                    }
                }
            });

            cancelBtn.addEventListener('click', () => {
                this.hideAddInput(addContainer);
            });

            input.addEventListener('keypress', async (e) => {
                if (e.key === 'Enter') {
                    const entityName = e.target.value.trim();
                    if (entityName) {
                        const success = await this.addNewEntity(type, entityName);
                        if (success) {
                            e.target.value = '';
                            // Keep input open for adding more entities
                            e.target.focus();
                        }
                    }
                }
            });

            group.appendChild(header);
            group.appendChild(content);
            container.appendChild(group);
        }
    }

    populateSpecsSection(container) {
        if (!this.graph.references) {
            container.innerHTML = '<div class="empty-section">No references defined</div>';
            return;
        }

        // Each reference gets its own accordion
        for (const [key, reference] of Object.entries(this.graph.references)) {
            const group = document.createElement('div');
            group.className = 'entity-group';

            // Count the number of items in this reference
            const referenceCount = Object.keys(reference || {}).length;
            const countDisplay = this.getCountDisplay(referenceCount);

            const header = document.createElement('div');
            header.className = 'entity-group-header';
            header.innerHTML = `
                <span class="entity-type-label">
                    ${this.formatReferenceKey(key)}
                </span>
                <div class="header-controls">
                    ${countDisplay}
                    <span class="expand-arrow">▶</span>
                </div>
            `;

            // Expand/collapse functionality
            const toggleExpand = () => {
                group.classList.toggle('expanded');
                header.querySelector('.expand-arrow').textContent =
                    group.classList.contains('expanded') ? '▼' : '▶';
            };

            header.querySelector('.entity-type-label').addEventListener('click', toggleExpand);
            header.querySelector('.expand-arrow').addEventListener('click', toggleExpand);

            const content = document.createElement('div');
            content.className = 'entity-group-content';

            // Create sub-accordions for top-level keys
            const subAccordions = this.createSubAccordions(key, reference);
            subAccordions.forEach(subAccordion => content.appendChild(subAccordion));

            group.appendChild(header);
            group.appendChild(content);
            container.appendChild(group);
        }
    }

    createSubAccordions(parentKey, reference) {
        const subAccordions = [];

        if (typeof reference === 'object' && reference !== null && !Array.isArray(reference)) {
            // For objects, create a sub-accordion for each top-level key
            for (const [subKey, subValue] of Object.entries(reference)) {
                const subAccordion = this.createSubAccordion(subKey, subValue);
                subAccordions.push(subAccordion);
            }
        } else if (typeof reference === 'string' && this.isJsonString(reference)) {
            // For JSON strings, parse and create sub-accordions
            try {
                const parsed = JSON.parse(reference);
                if (typeof parsed === 'object' && parsed !== null) {
                    for (const [subKey, subValue] of Object.entries(parsed)) {
                        const subAccordion = this.createSubAccordion(subKey, subValue);
                        subAccordions.push(subAccordion);
                    }
                } else {
                    // Single value JSON, create one sub-accordion
                    const subAccordion = this.createSubAccordion('content', parsed);
                    subAccordions.push(subAccordion);
                }
            } catch (e) {
                // Not valid JSON, create single content sub-accordion
                const subAccordion = this.createSubAccordion('content', reference);
                subAccordions.push(subAccordion);
            }
        } else {
            // For other types, create a single content sub-accordion
            const subAccordion = this.createSubAccordion('content', reference);
            subAccordions.push(subAccordion);
        }

        return subAccordions;
    }

    createSubAccordion(key, value) {
        const subGroup = document.createElement('div');
        subGroup.className = 'sub-accordion-group';

        const subHeader = document.createElement('div');
        subHeader.className = 'sub-accordion-header';
        subHeader.innerHTML = `
            <span class="sub-accordion-label">${this.formatReferenceKey(key)}</span>
            <span class="sub-expand-arrow">▶</span>
        `;

        const subContent = document.createElement('div');
        subContent.className = 'sub-accordion-content';

        // Check if this is a leaf level (simple key-value pairs)
        const isLeafLevel = typeof value === 'object' && value !== null && this.isSimpleKeyValueObject(value);
        subContent.innerHTML = this.formatReferenceContent(value, isLeafLevel);

        // Sub-accordion toggle functionality
        const toggleSubExpand = () => {
            subGroup.classList.toggle('expanded');
            subHeader.querySelector('.sub-expand-arrow').textContent =
                subGroup.classList.contains('expanded') ? '▼' : '▶';
        };

        subHeader.addEventListener('click', toggleSubExpand);

        subGroup.appendChild(subHeader);
        subGroup.appendChild(subContent);

        return subGroup;
    }

    formatReferenceKey(key) {
        // Convert snake_case and kebab-case to Title Case
        let formatted = key
            .replace(/[_-]/g, ' ')  // Replace underscores and hyphens with spaces
            .replace(/\b\w/g, l => l.toUpperCase());  // Capitalize first letter of each word

        // Special case: ensure "UI" is always capitalized
        formatted = formatted.replace(/\bUi\b/g, 'UI');

        return formatted;
    }

    // Get count display - empty span that only shows number on hover
    getCountDisplay(count) {
        if (count === 0) return '';
        return `<span class="entity-count" data-count="${count}"></span>`;
    }

    formatReferenceContent(reference, isLeafLevel = false) {
        if (typeof reference === 'object' && reference !== null && !Array.isArray(reference)) {
            // If this is a leaf level (final key:value pairs), render as plain text
            if (isLeafLevel || this.isSimpleKeyValueObject(reference)) {
                return this.formatKeyValuePairs(reference);
            }
            return `<pre class="reference-json">${JSON.stringify(reference, null, 2)}</pre>`;
        } else if (typeof reference === 'string') {
            // Check if it looks like structured data
            if (this.isJsonString(reference)) {
                try {
                    const parsed = JSON.parse(reference);
                    if (typeof parsed === 'object' && this.isSimpleKeyValueObject(parsed)) {
                        return this.formatKeyValuePairs(parsed);
                    }
                    return `<pre class="reference-json">${JSON.stringify(parsed, null, 2)}</pre>`;
                } catch (e) {
                    // Fall through to regular text formatting
                }
            }

            // Format multiline text with proper line breaks
            const formattedText = this.formatTextContent(reference);
            return `<div class="reference-text">${formattedText}</div>`;
        } else if (Array.isArray(reference)) {
            return `<div class="reference-list">${this.formatArrayContent(reference)}</div>`;
        }
        return `<span class="reference-value">${reference}</span>`;
    }

    isSimpleKeyValueObject(obj) {
        // Check if object contains only simple values (strings, numbers, booleans)
        return Object.values(obj).every(value =>
            typeof value === 'string' ||
            typeof value === 'number' ||
            typeof value === 'boolean' ||
            value === null
        );
    }

    formatKeyValuePairs(obj) {
        return Object.entries(obj)
            .map(([key, value]) =>
                `<div class="key-value-pair">
                    <span class="formatted-key">${this.formatReferenceKey(key)}:</span>
                    <span class="formatted-value">${value}</span>
                </div>`
            )
            .join('');
    }

    isJsonString(str) {
        return str.trim().startsWith('{') || str.trim().startsWith('[');
    }

    formatTextContent(text) {
        return text
            .split('\n')
            .map(line => {
                line = line.trim();
                if (!line) return '<br>';

                // Format bullet points
                if (line.startsWith('- ') || line.startsWith('* ')) {
                    return `<div class="bullet-item">• ${line.substring(2)}</div>`;
                }

                // Format numbered lists
                if (/^\d+\.\s/.test(line)) {
                    return `<div class="numbered-item">${line}</div>`;
                }

                // Format headers (lines ending with :)
                if (line.endsWith(':') && line.length < 50) {
                    return `<div class="content-header">${line}</div>`;
                }

                return `<div class="content-line">${line}</div>`;
            })
            .join('');
    }

    formatArrayContent(array) {
        return array
            .map(item => `<div class="array-item">• ${typeof item === 'object' ? JSON.stringify(item, null, 2) : item}</div>`)
            .join('');
    }

    populateReferencesSection(container) {
        if (!this.graph.references) {
            container.innerHTML = '<div class="empty-section">No references defined</div>';
            return;
        }

        // Group references by categories (detect common prefixes or treat each as its own category)
        const groupedRefs = this.groupReferences(this.graph.references);

        for (const [category, refs] of Object.entries(groupedRefs)) {
            const count = Object.keys(refs).length;
            if (count === 0) continue;

            const group = document.createElement('div');
            group.className = 'entity-group'; // Reuse entity group styling

            const header = document.createElement('div');
            header.className = 'entity-group-header';
            header.innerHTML = `
                <span class="entity-type-label">${this.formatTypeName(category)} (${count})</span>
                <div class="header-controls">
                    <span class="expand-arrow">▶</span>
                </div>
            `;

            // Expand/collapse functionality
            const toggleExpand = () => {
                group.classList.toggle('expanded');
                header.querySelector('.expand-arrow').textContent =
                    group.classList.contains('expanded') ? '▼' : '▶';
            };

            header.querySelector('.entity-type-label').addEventListener('click', toggleExpand);
            header.querySelector('.expand-arrow').addEventListener('click', toggleExpand);

            const content = document.createElement('div');
            content.className = 'entity-group-content';

            // Add individual references
            for (const [key, reference] of Object.entries(refs)) {
                const item = document.createElement('div');
                item.className = 'entity-item';
                item.innerHTML = `
                    <div class="reference-display">
                        <div class="reference-key">• ${key}</div>
                        <div class="reference-value">${this.formatReferenceValue(reference)}</div>
                    </div>
                `;
                item.addEventListener('click', () => this.selectReference(key));
                content.appendChild(item);
            }

            group.appendChild(header);
            group.appendChild(content);
            container.appendChild(group);
        }
    }

    groupReferences(references) {
        // Simple grouping - you could make this more sophisticated
        // For now, group by common prefixes or put all in "references" category
        const grouped = { references: {} };

        for (const [key, value] of Object.entries(references)) {
            // Check for common prefixes like "ui-", "api-", "style-" etc.
            const prefix = key.split('-')[0];
            if (prefix && prefix.length > 2 && key.includes('-')) {
                if (!grouped[prefix]) grouped[prefix] = {};
                grouped[prefix][key] = value;
            } else {
                grouped.references[key] = value;
            }
        }

        // Remove empty categories
        Object.keys(grouped).forEach(category => {
            if (Object.keys(grouped[category]).length === 0) {
                delete grouped[category];
            }
        });

        return grouped;
    }

    formatReferenceValue(reference) {
        if (typeof reference === 'string') {
            return reference.length > 50 ? reference.substring(0, 50) + '...' : reference;
        }
        return JSON.stringify(reference).substring(0, 50) + '...';
    }

    selectReference(refKey) {
        console.log('Selected reference:', refKey);
        // Could show reference details, etc.
    }

    getEntityDescriptions() {
        return {
            "project": "Top-level container representing the entire software project or system",
            "requirements": "Functional or non-functional specifications that the system must satisfy",
            "interfaces": "User interface screens and pages in the application",
            "features": "Distinct functionality or capability provided to users",
            "actions": "Specific user interactions or system operations",
            "components": "Reusable building blocks of the system architecture",
            "presentation": "Visual and layout aspects of user interface components",
            "behavior": "Logic and state management for component interactions",
            "data_models": "Structure and schema definitions for data entities",
            "users": "Actors or roles that interact with the system",
            "objectives": "High-level goals or outcomes that users want to achieve"
        };
    }


    showAddInput(addContainer, type) {
        // Close any other active inputs first
        this.closeAllActiveInputs();

        const button = addContainer.querySelector('.add-entity-btn');
        const inputDiv = addContainer.querySelector('.entity-inline-input');
        const input = inputDiv.querySelector('.entity-input');

        button.classList.add('hidden');
        inputDiv.classList.remove('hidden');
        input.focus();

        // Mark this input as active
        addContainer.classList.add('active-input');
    }

    hideAddInput(addContainer) {
        const button = addContainer.querySelector('.add-entity-btn');
        const inputDiv = addContainer.querySelector('.entity-inline-input');
        const input = inputDiv.querySelector('.entity-input');

        button.classList.remove('hidden');
        inputDiv.classList.add('hidden');
        input.value = '';

        // Remove active state
        addContainer.classList.remove('active-input');
    }

    editEntity(entityItem) {
        // Close any other active inputs first
        this.closeAllActiveInputs();

        const entityName = entityItem.querySelector('.entity-name');
        const editIcon = entityItem.querySelector('.entity-edit-icon');
        const currentName = entityName.textContent;

        // Create inline input
        const inputDiv = document.createElement('div');
        inputDiv.className = 'entity-inline-input';
        inputDiv.innerHTML = `
            <input type="text" class="entity-input" value="${currentName}" />
            <div class="input-controls">
                <button class="entity-save-btn">✓</button>
                <button class="entity-cancel-btn">✕</button>
            </div>
        `;

        // Replace the entity content
        entityItem.innerHTML = '';
        entityItem.appendChild(inputDiv);
        entityItem.classList.add('active-input');

        const input = inputDiv.querySelector('.entity-input');
        const saveBtn = inputDiv.querySelector('.entity-save-btn');
        const cancelBtn = inputDiv.querySelector('.entity-cancel-btn');

        input.focus();
        input.select();

        // Handle save
        const handleSave = async () => {
            const newName = input.value.trim();
            if (newName && newName !== currentName) {
                // TODO: Implement entity update API call
                console.log('Update entity:', entityItem.dataset.entityRef, 'to:', newName);
                this.showSuccess(`Updated ${newName}`);
            }
            this.restoreEntityItem(entityItem, newName || currentName);
        };

        // Handle cancel
        const handleCancel = () => {
            this.restoreEntityItem(entityItem, currentName);
        };

        saveBtn.addEventListener('click', handleSave);
        cancelBtn.addEventListener('click', handleCancel);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSave();
            } else if (e.key === 'Escape') {
                handleCancel();
            }
        });
    }

    restoreEntityItem(entityItem, name) {
        entityItem.innerHTML = `
            <span class="entity-name">${name}</span>
            <span class="entity-edit-icon" title="Edit">✏️</span>
        `;
        entityItem.classList.remove('active-input');

        // Re-bind events
        entityItem.querySelector('.entity-name').addEventListener('click', () => this.selectEntity(entityItem.dataset.entityRef));
        entityItem.querySelector('.entity-edit-icon').addEventListener('click', (e) => {
            e.stopPropagation();
            this.editEntity(entityItem);
        });
    }

    closeAllActiveInputs() {
        // Close any active add inputs
        document.querySelectorAll('.entity-add-container.active-input').forEach(container => {
            this.hideAddInput(container);
        });

        // Close any active edit inputs
        document.querySelectorAll('.entity-item.active-input').forEach(item => {
            const nameSpan = item.querySelector('.entity-name');
            if (nameSpan) {
                const currentName = nameSpan.textContent;
                this.restoreEntityItem(item, currentName);
            }
        });
    }

    formatTypeName(type) {
        return type.charAt(0).toUpperCase() + type.slice(1);
    }

    selectEntity(entityRef) {
        console.log('Selected entity:', entityRef);
        // Could highlight in graph, show details, etc.
    }

    initializeMinimap() {
        const canvas = document.getElementById('graph-minimap');
        if (!canvas) return;

        // Destroy old minimap if it exists
        if (this.minimap) {
            this.minimap.destroy();
        }

        // Create new enhanced minimap
        this.minimap = new GraphMinimap(canvas, this);

        // Update with current graph data
        if (this.graph) {
            this.minimap.updateGraph(this.graph);
        }
    }

    onEntityAdded(data) {
        this.showSuccess(`Added entity: ${data.name}`);
        this.markAsModified();
        this.updateEntitySidebar();
        if (this.minimap) {
            this.minimap.updateGraph(this.graph);
        }
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

    // Mark graph as modified and update display
    markAsModified() {
        if (!this.isModified) {
            this.isModified = true;
            this.updateDropdownDisplay();
        }
    }

    // Update dropdown display to show asterisk when modified
    updateDropdownDisplay() {
        const selector = document.getElementById('graph-selector');
        if (!selector || !this.currentGraphName) return;

        const option = Array.from(selector.options).find(opt => opt.value === this.currentGraphName);
        if (option) {
            const baseName = this.currentGraphName;
            option.textContent = this.isModified ? `${baseName} *` : baseName;
        }
    }

    // Add new entity through API
    async addNewEntity(type, name) {
        try {
            // Generate a key from the name (lowercase, replace spaces with hyphens)
            const key = name.toLowerCase().replace(/\s+/g, '-');
            const singularType = type.slice(0, -1); // Remove 's' from plural

            console.log(`Adding entity: ${singularType}:${key} (${name})`);

            const response = await fetch(`${this.apiBase}/entities/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: singularType,
                    key,
                    name
                })
            });

            const result = await response.json();
            console.log('Add entity response:', result);

            if (result.success) {
                this.showSuccess(`Added ${singularType}: ${name}`);
                this.markAsModified(); // Mark as modified before reloading
                await this.loadGraph(); // Reload the graph to show the new entity
                return true;
            } else {
                this.showError(result.error || 'Failed to add entity');
                console.error('Entity add failed:', result);
                return false;
            }
        } catch (error) {
            console.error('Failed to add entity:', error);
            this.showError(`Failed to add entity: ${error.message}`);
            return false;
        }
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

    // Sidebar methods
    togglePhaseSidebar() {
        const hamburgerBtn = document.getElementById('phase-menu-toggle');
        const phaseSidebar = document.getElementById('phase-sidebar-inner');

        if (hamburgerBtn && phaseSidebar) {
            const isOpen = phaseSidebar.classList.contains('visible');

            if (isOpen) {
                this.closePhaseSidebar();
            } else {
                this.openPhaseSidebar();
            }
        }
    }

    openPhaseSidebar() {
        const hamburgerBtn = document.getElementById('phase-menu-toggle');
        const phaseSidebar = document.getElementById('phase-sidebar-inner');

        if (hamburgerBtn && phaseSidebar) {
            hamburgerBtn.classList.add('open');
            phaseSidebar.classList.remove('hidden');
            phaseSidebar.classList.add('visible');
        }
    }

    closePhaseSidebar() {
        const hamburgerBtn = document.getElementById('phase-menu-toggle');
        const phaseSidebar = document.getElementById('phase-sidebar-inner');

        if (hamburgerBtn && phaseSidebar) {
            hamburgerBtn.classList.remove('open');
            phaseSidebar.classList.remove('visible');
            phaseSidebar.classList.add('hidden');
        }
    }

    // Entity sidebar collapse/expand
    toggleEntitySidebar() {
        const entitySidebar = document.getElementById('entity-sidebar');
        const toggleIcon = document.querySelector('.sidebar-toggle .toggle-icon');
        if (entitySidebar) {
            entitySidebar.classList.toggle('collapsed');
            // Update arrow direction
            if (toggleIcon) {
                toggleIcon.textContent = entitySidebar.classList.contains('collapsed') ? '▶' : '◀';
            }
        }
    }

    updateCurrentPhaseIndicator(phaseName) {
        const indicator = document.getElementById('current-phase-indicator');
        if (indicator) {
            // Capitalize first letter and format nicely
            const formattedPhase = phaseName.charAt(0).toUpperCase() + phaseName.slice(1);
            indicator.textContent = formattedPhase;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new KnowledgeGraphApp();
});