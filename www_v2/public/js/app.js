// State Management
const state = {
    currentPage: 'start',
    activeGraph: null,
    qaSession: {
        currentQuestion: null,
        questionQueue: [],
        answeredQuestions: [],
        skippedQuestions: []
    },
    entities: {},
    references: {},
    graph: {}
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadGraphFiles();

    // Handle initial route
    handleRoute();

    // Listen for hash changes
    window.addEventListener('hashchange', handleRoute);
});

// URL Routing
function handleRoute() {
    const hash = window.location.hash.slice(1) || 'start';
    const validPages = ['start', 'discover', 'arrange', 'validate', 'define', 'build'];

    if (validPages.includes(hash)) {
        navigateToPage(hash);
    } else {
        navigateToPage('start');
    }
}

// Event Listeners
function initializeEventListeners() {
    // Page Navigation
    document.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!e.target.disabled) {
                navigateToPage(e.target.dataset.page);
            }
        });
    });

    // Start Page
    document.getElementById('vision-submit').addEventListener('click', handleVisionSubmit);
    document.getElementById('vision-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleVisionSubmit();
    });
    document.getElementById('start-graph-selector').addEventListener('change', handleGraphLoad);

    // Graph File Selector
    document.getElementById('graph-file-selector').addEventListener('change', handleGraphLoad);

    // Sidebar
    document.getElementById('sidebar-toggle').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => toggleAccordion(header.parentElement));
    });

    // Discover Page
    document.getElementById('submit-answer').addEventListener('click', handleAnswerSubmit);
    document.getElementById('expand-toggle').addEventListener('click', toggleExpandOptions);
    document.getElementById('next-question').addEventListener('click', loadNextQuestion);
    document.getElementById('toggle-question-list').addEventListener('click', toggleQuestionList);
    document.getElementById('show-multiple-choices').addEventListener('change', toggleMultipleChoiceView);

    // Multiple choice will be handled dynamically when options are created

    // AI Bar
    document.getElementById('ai-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAICommand(e.target.value);
    });
}

// Navigation
function navigateToPage(pageName) {
    state.currentPage = pageName;
    document.body.dataset.page = pageName;

    // Update URL hash
    if (window.location.hash !== `#${pageName}`) {
        window.location.hash = pageName;
    }

    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // Show current page
    document.getElementById(`${pageName}-page`).classList.add('active');

    // Update page buttons
    document.querySelectorAll('.page-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.page === pageName);
    });

    // Show/hide top bar and sidebar based on page
    const topBar = document.getElementById('top-bar');
    const aiBar = document.getElementById('ai-bar');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');

    if (pageName === 'start') {
        topBar.classList.add('hidden');
        aiBar.classList.add('hidden');
        sidebar.classList.add('hidden');
        sidebarToggle.classList.add('hidden');
    } else {
        topBar.classList.remove('hidden');
        aiBar.classList.remove('hidden');
        sidebar.classList.remove('hidden');
        // Only show sidebar toggle if graph is loaded
        if (state.activeGraph) {
            sidebarToggle.classList.remove('hidden');
        } else {
            sidebarToggle.classList.add('hidden');
        }
    }

    // Page-specific initialization
    if (pageName === 'discover') {
        initializeDiscoverPage();
    }
}

// Start Page Functions
async function handleVisionSubmit() {
    const visionInput = document.getElementById('vision-input');
    const vision = visionInput.value.trim();

    if (!vision) return;

    // Initialize new graph with vision
    state.activeGraph = {
        meta: {
            project_name: 'New Project',
            vision_statement: vision,
            qa_sessions: [],
            phases: []
        },
        entities: {},
        references: {},
        graph: []
    };

    // Generate initial questions
    await generateQuestions(vision);

    // Navigate to Discover page
    navigateToPage('discover');
}

async function handleGraphLoad(e) {
    const filename = e.target.value;
    if (!filename) return;

    try {
        const response = await fetch(`/api/graphs/${filename}`);
        const graphData = await response.json();
        state.activeGraph = graphData;

        // Store entities and references in state
        state.entities = graphData.entities || {};
        state.references = graphData.references || {};
        state.graph = graphData.graph || {};

        // Update UI with loaded graph
        updateEntitiesReferences();

        // Show sidebar toggle when graph is loaded
        if (state.currentPage !== 'start') {
            document.getElementById('sidebar-toggle').classList.remove('hidden');
        }

        // Navigate to appropriate page
        if (state.currentPage === 'start') {
            navigateToPage('discover');
        }

        // Update the dropdown to show selected file
        document.getElementById('graph-file-selector').value = filename;
    } catch (error) {
        console.error('Error loading graph:', error);
        alert('Failed to load graph file');
    }
}

// Discover Page Functions
function initializeDiscoverPage() {
    if (state.qaSession.questionQueue.length > 0) {
        displayCurrentQuestion();
    } else if (state.activeGraph && state.activeGraph.meta.vision_statement) {
        generateQuestions(state.activeGraph.meta.vision_statement);
    }
}

async function generateQuestions(context) {
    try {
        const response = await fetch('/api/ai/generate-questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ context, existingQA: state.qaSession.answeredQuestions })
        });

        const data = await response.json();
        state.qaSession.questionQueue = data.questions;

        if (state.qaSession.questionQueue.length > 0) {
            loadNextQuestion();
        }
    } catch (error) {
        console.error('Error generating questions:', error);
    }
}

function displayCurrentQuestion() {
    const question = state.qaSession.currentQuestion;
    if (!question) return;

    document.getElementById('question-text').textContent = question.text;
    document.getElementById('current-question').innerHTML = `Question #${question.number}: <span>${question.text}</span>`;

    // Display upcoming questions
    if (state.qaSession.questionQueue.length > 0) {
        document.getElementById('next-question-preview').textContent = state.qaSession.questionQueue[0].text;
    }
    if (state.qaSession.questionQueue.length > 1) {
        document.getElementById('next-next-question-preview').textContent = state.qaSession.questionQueue[1].text;
    }
}

function loadNextQuestion() {
    if (state.qaSession.questionQueue.length === 0) {
        generateQuestions(state.activeGraph.meta.vision_statement);
        return;
    }

    state.qaSession.currentQuestion = state.qaSession.questionQueue.shift();
    displayCurrentQuestion();

    // Clear previous answer
    document.getElementById('answer-input').value = '';
    document.getElementById('extraction-choices').classList.add('hidden');
    document.getElementById('expand-options').classList.add('hidden');
}

async function handleAnswerSubmit() {
    const answer = document.getElementById('answer-input').value.trim();
    if (!answer) return;

    // Store answer
    state.qaSession.answeredQuestions.push({
        question: state.qaSession.currentQuestion,
        answer: answer
    });

    // Extract entities and references
    await extractEntitiesReferences(answer);

    // Generate more questions based on answer
    if (state.qaSession.questionQueue.length < 5) {
        generateQuestions(answer);
    }
}

async function extractEntitiesReferences(text) {
    try {
        const response = await fetch('/api/ai/extract-entities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, graph: state.activeGraph })
        });

        const data = await response.json();

        // Display detections
        const detectionsList = document.getElementById('detections-list');
        detectionsList.innerHTML = '';

        data.entities.forEach(entity => {
            const li = document.createElement('li');
            li.className = 'detection-item';
            li.innerHTML = `
                <span>${entity.type}: ${entity.name}</span>
                <button class="add-btn" onclick="addEntity('${entity.type}', '${entity.name}')">+</button>
            `;
            detectionsList.appendChild(li);
        });

        data.references.forEach(ref => {
            const li = document.createElement('li');
            li.className = 'detection-item';
            li.innerHTML = `
                <span>Reference: ${ref.key}</span>
                <button class="add-btn" onclick="addReference('${ref.key}', '${ref.value}')">+</button>
            `;
            detectionsList.appendChild(li);
        });

        document.getElementById('extraction-choices').classList.remove('hidden');

        // Show connections if entities were added
        if (data.connections && data.connections.length > 0) {
            displayConnections(data.connections);
        }
    } catch (error) {
        console.error('Error extracting entities:', error);
    }
}

function displayConnections(connections) {
    const connectionsList = document.getElementById('connections-list');
    connectionsList.innerHTML = '';

    connections.forEach(conn => {
        const li = document.createElement('li');
        li.className = 'connection-item';
        li.innerHTML = `
            <span>${conn.from} → ${conn.to}</span>
            <button class="add-btn" onclick="addConnection('${conn.from}', '${conn.to}')">+</button>
        `;
        connectionsList.appendChild(li);
    });

    document.getElementById('connections').classList.remove('hidden');
}

// Entity/Reference Management
function addEntity(type, name, description = '') {
    if (!state.activeGraph.entities[type]) {
        state.activeGraph.entities[type] = {};
    }
    state.activeGraph.entities[type][name] = {
        description: description
    };
    updateEntitiesReferences();
    saveGraph();
}

function addReference(key, value) {
    state.activeGraph.references[key] = value;
    updateEntitiesReferences();
    saveGraph();
}

function addConnection(from, to) {
    state.activeGraph.graph.push({
        from: from,
        to: to,
        type: 'depends_on'
    });
    saveGraph();
}

function updateEntitiesReferences() {
    if (!state.activeGraph) return;

    // Update sidebar accordions - match the actual entity types in the graph
    const entityTypes = [
        { key: 'users', display: 'users' },
        { key: 'objectives', display: 'objectives' },
        { key: 'actions', display: 'actions' },
        { key: 'requirements', display: 'requirements' },
        { key: 'interfaces', display: 'interfaces' },
        { key: 'components', display: 'components' },
        { key: 'presentations', display: 'presentations' },
        { key: 'data-models', display: 'data-models' },
        { key: 'behaviors', display: 'behaviors' },
        { key: 'features', display: 'features' }  // Add features since it's in the graph
    ];

    entityTypes.forEach(({ key, display }) => {
        const accordion = document.querySelector(`.accordion[data-type="${display}"]`);
        if (!accordion) return;

        const content = accordion.querySelector('.accordion-content');
        const count = accordion.querySelector('.count');

        const entities = state.activeGraph?.entities[key] || {};
        const entityKeys = Object.keys(entities);

        if (entityKeys.length > 0) {
            accordion.style.display = 'block';
            count.textContent = `(${entityKeys.length})`;

            content.innerHTML = '';
            entityKeys.forEach(entityKey => {
                const entity = entities[entityKey];
                const description = entity.description || entity.name || '';
                const item = document.createElement('div');
                item.className = 'entity-item';
                item.dataset.key = entityKey;
                item.dataset.type = key;

                // Convert kebab-case and snake_case to Title Case
                const displayName = entityKey
                    .replace(/[-_]/g, ' ')
                    .replace(/\b\w/g, l => l.toUpperCase());

                // Create display mode HTML
                const displayHTML = `
                    <span class="entity-name">${displayName}</span>
                    <span class="entity-description" title="${description}">${description || 'No description'}</span>
                    <span class="edit-icon">✏️</span>
                `;

                // Create edit mode HTML
                const editHTML = `
                    <input type="text" class="entity-name-input" value="${entityKey}" placeholder="Name">
                    <input type="text" class="entity-desc-input" value="${description}" placeholder="Description">
                    <button class="save-btn">✓</button>
                    <button class="cancel-btn">✕</button>
                `;

                item.innerHTML = displayHTML;

                // Add edit functionality
                const editIcon = item.querySelector('.edit-icon');
                editIcon.addEventListener('click', () => enterEditMode(item, key, entityKey, entity));

                content.appendChild(item);
            });

            // Add new entity input
            const addContainer = document.createElement('div');
            addContainer.className = 'add-entity-container';
            addContainer.innerHTML = `
                <input type="text" class="add-entity-input" placeholder="+ Add new ${key.slice(0, -1)}..." data-type="${key}">
            `;

            const addInput = addContainer.querySelector('.add-entity-input');
            addInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && e.target.value.trim()) {
                    const newKey = e.target.value.trim().toLowerCase().replace(/\s+/g, '-');
                    addEntity(key, newKey, '');
                    e.target.value = '';
                    updateEntitiesReferences();
                }
            });

            content.appendChild(addContainer);
        } else {
            accordion.style.display = 'none';
        }
    });

    // Update references section
    const refsList = document.getElementById('references-list');
    const refs = state.activeGraph?.references || {};

    // Get top-level reference categories (not nested values)
    const refCategories = {};
    Object.keys(refs).forEach(key => {
        if (typeof refs[key] === 'object' && refs[key] !== null) {
            refCategories[key] = refs[key];
        }
    });

    refsList.innerHTML = '';

    Object.keys(refCategories).forEach(category => {
        const categoryData = refCategories[category];
        const itemCount = Object.keys(categoryData).length;

        if (itemCount > 0) {
            const accordion = document.createElement('div');
            accordion.className = 'accordion';
            accordion.dataset.type = `ref-${category}`;

            const header = document.createElement('div');
            header.className = 'accordion-header';
            header.innerHTML = `${category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} <span class="count">(${itemCount})</span>`;
            header.addEventListener('click', () => toggleAccordion(accordion));

            const content = document.createElement('div');
            content.className = 'accordion-content';

            Object.keys(categoryData).forEach(itemKey => {
                const itemValue = categoryData[itemKey];
                const displayValue = typeof itemValue === 'object' ?
                    (itemValue.name || itemValue.id || itemValue.type || JSON.stringify(itemValue).substring(0, 50) + '...') :
                    String(itemValue);

                // Convert kebab-case and snake_case to Title Case
                const displayName = itemKey
                    .replace(/[-_]/g, ' ')
                    .replace(/\b\w/g, l => l.toUpperCase());

                const item = document.createElement('div');
                item.className = 'entity-item';

                const descText = typeof itemValue === 'object' ?
                    (itemValue.description || itemValue.name || itemValue.id || 'Complex object') :
                    String(itemValue);

                item.innerHTML = `
                    <span class="entity-name">${displayName}</span>
                    <span class="entity-description" title="${typeof itemValue === 'object' ? JSON.stringify(itemValue, null, 2) : displayValue}">${descText}</span>
                    <span class="edit-icon">✏️</span>
                `;

                // Add edit functionality for references
                const editIcon = item.querySelector('.edit-icon');
                editIcon.addEventListener('click', () => enterReferenceEditMode(item, category, itemKey, itemValue));

                content.appendChild(item);
            });

            accordion.appendChild(header);
            accordion.appendChild(content);
            refsList.appendChild(accordion);
        }
    });
}

// UI Helper Functions
function enterEditMode(item, entityType, entityKey, entity) {
    const currentName = entityKey;
    const currentDesc = entity.description || entity.name || '';

    // Switch to edit mode
    item.classList.add('edit-mode');
    item.innerHTML = `
        <input type="text" class="entity-name-input" value="${currentName}" placeholder="Name">
        <input type="text" class="entity-desc-input" value="${currentDesc}" placeholder="Description">
        <button class="save-btn" title="Save">✓</button>
        <button class="cancel-btn" title="Cancel">✕</button>
    `;

    const nameInput = item.querySelector('.entity-name-input');
    const descInput = item.querySelector('.entity-desc-input');
    const saveBtn = item.querySelector('.save-btn');
    const cancelBtn = item.querySelector('.cancel-btn');

    nameInput.focus();
    nameInput.select();

    const saveChanges = () => {
        const newName = nameInput.value.trim().toLowerCase().replace(/\s+/g, '-');
        const newDesc = descInput.value.trim();

        if (newName && newName !== currentName) {
            // Rename the entity key
            state.activeGraph.entities[entityType][newName] = {
                ...entity,
                description: newDesc
            };
            delete state.activeGraph.entities[entityType][currentName];
        } else if (newName === currentName) {
            // Just update description
            state.activeGraph.entities[entityType][currentName].description = newDesc;
        }

        saveGraph();
        updateEntitiesReferences();
    };

    const exitEditMode = () => {
        updateEntitiesReferences();
    };

    saveBtn.addEventListener('click', saveChanges);
    cancelBtn.addEventListener('click', exitEditMode);

    nameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveChanges();
        if (e.key === 'Escape') exitEditMode();
    });

    descInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveChanges();
        if (e.key === 'Escape') exitEditMode();
    });
}


function enterReferenceEditMode(item, category, itemKey, itemValue) {
    const currentName = itemKey;
    const currentValue = typeof itemValue === 'object' ?
        (itemValue.description || itemValue.name || JSON.stringify(itemValue)) :
        String(itemValue);

    // Switch to edit mode
    item.classList.add('edit-mode');
    item.innerHTML = `
        <input type="text" class="entity-name-input" value="${currentName}" placeholder="Name" readonly>
        <input type="text" class="entity-desc-input" value="${currentValue}" placeholder="Value">
        <button class="save-btn" title="Save">✓</button>
        <button class="cancel-btn" title="Cancel">✕</button>
    `;

    const nameInput = item.querySelector('.entity-name-input');
    const valueInput = item.querySelector('.entity-desc-input');
    const saveBtn = item.querySelector('.save-btn');
    const cancelBtn = item.querySelector('.cancel-btn');

    valueInput.focus();
    valueInput.select();

    const saveChanges = () => {
        const newValue = valueInput.value.trim();

        // Update the data
        if (typeof itemValue === 'object') {
            // For objects, update the entire object or just description
            if (state.activeGraph.references[category][itemKey]) {
                if (typeof state.activeGraph.references[category][itemKey] === 'object') {
                    state.activeGraph.references[category][itemKey].description = newValue;
                } else {
                    state.activeGraph.references[category][itemKey] = newValue;
                }
            }
        } else {
            // For simple values, replace the entire value
            state.activeGraph.references[category][itemKey] = newValue;
        }

        saveGraph();
        updateEntitiesReferences();
    };

    const exitEditMode = () => {
        updateEntitiesReferences();
    };

    saveBtn.addEventListener('click', saveChanges);
    cancelBtn.addEventListener('click', exitEditMode);

    valueInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveChanges();
        if (e.key === 'Escape') exitEditMode();
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');
    const isOpen = sidebar.classList.toggle('open');
    toggle.classList.toggle('open');

    // Change arrow direction
    toggle.textContent = isOpen ? '▶' : '◀';
}

function toggleAccordion(accordion) {
    const wasOpen = accordion.classList.contains('open');

    // Close all accordions in the same section
    const section = accordion.closest('.sidebar-section');
    section.querySelectorAll('.accordion').forEach(acc => {
        acc.classList.remove('open');
    });

    // Toggle the clicked accordion
    if (!wasOpen) {
        accordion.classList.add('open');
    }
}

function toggleExpandOptions() {
    const options = document.getElementById('expand-options');
    const toggle = document.getElementById('expand-toggle');

    if (options.classList.contains('hidden')) {
        options.classList.remove('hidden');
        toggle.textContent = 'Collapse Options ▲';
        loadExpandedOptions();
    } else {
        options.classList.add('hidden');
        toggle.textContent = 'Expand Options ▼';
    }
}

async function loadExpandedOptions() {
    if (!state.qaSession.currentQuestion) return;

    try {
        const response = await fetch('/api/ai/expand-question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: state.qaSession.currentQuestion.text })
        });

        const data = await response.json();

        // Display multiple choice options
        const mcOptions = document.getElementById('mc-options');
        mcOptions.innerHTML = '';
        ['a', 'b', 'c', 'd', 'e'].forEach((letter, index) => {
            if (data.choices[index]) {
                const div = document.createElement('div');
                div.className = 'mc-option';
                div.dataset.choice = letter;
                div.innerHTML = `<span class="letter">${letter.toUpperCase()}.</span> ${data.choices[index]}`;

                // Make the option clickable
                div.addEventListener('click', () => selectMultipleChoice(div));

                mcOptions.appendChild(div);
            }
        });

        // Display other expanded info
        document.getElementById('recommendation').textContent = data.recommendation || '';
        document.getElementById('tradeoffs').textContent = data.tradeoffs || '';
        document.getElementById('alternatives').textContent = data.alternatives || '';
        document.getElementById('challenges').textContent = data.challenges || '';
    } catch (error) {
        console.error('Error loading expanded options:', error);
    }
}

function selectMultipleChoice(optionElement) {
    // Toggle selected class for multi-select
    optionElement.classList.toggle('selected');

    // Collect all selected choices
    const selectedOptions = document.querySelectorAll('.mc-option.selected');
    const selectedTexts = [];
    const selectedLetters = [];

    selectedOptions.forEach(opt => {
        const letter = opt.dataset.choice.toUpperCase();
        const fullText = opt.textContent.trim();
        // Remove the "A. " prefix (letter + dot + space)
        const answerText = fullText.substring(3);
        selectedTexts.push(answerText);
        selectedLetters.push(letter);
    });

    // Update the answer input with selected choices
    if (selectedTexts.length > 0) {
        document.getElementById('answer-input').value = selectedTexts.join('; ');
    } else {
        document.getElementById('answer-input').value = '';
    }
}

function toggleQuestionList() {
    const list = document.getElementById('question-list');
    const toggle = document.getElementById('toggle-question-list');

    if (list.classList.contains('hidden')) {
        list.classList.remove('hidden');
        toggle.textContent = 'Hide Question List ▲';
        displayQuestionList();
    } else {
        list.classList.add('hidden');
        toggle.textContent = 'Show Question List ▼';
    }
}

function displayQuestionList() {
    const ul = document.getElementById('questions-ul');
    ul.innerHTML = '';

    // Show answered questions
    state.qaSession.answeredQuestions.forEach(qa => {
        const li = document.createElement('li');
        li.className = 'question-item answered';
        li.textContent = `✓ ${qa.question.text}`;
        ul.appendChild(li);
    });

    // Show current question
    if (state.qaSession.currentQuestion) {
        const li = document.createElement('li');
        li.className = 'question-item current';
        li.textContent = `▶ ${state.qaSession.currentQuestion.text}`;
        ul.appendChild(li);
    }

    // Show upcoming questions
    state.qaSession.questionQueue.forEach(q => {
        const li = document.createElement('li');
        li.className = 'question-item';
        li.textContent = q.text;
        li.onclick = () => selectQuestion(q);
        ul.appendChild(li);
    });

    // Show skipped questions
    state.qaSession.skippedQuestions.forEach(q => {
        const li = document.createElement('li');
        li.className = 'question-item skipped';
        li.textContent = `⊘ ${q.text}`;
        li.onclick = () => selectQuestion(q);
        ul.appendChild(li);
    });
}

function selectQuestion(question) {
    // Move question to current
    state.qaSession.currentQuestion = question;

    // Remove from queues
    state.qaSession.questionQueue = state.qaSession.questionQueue.filter(q => q !== question);
    state.qaSession.skippedQuestions = state.qaSession.skippedQuestions.filter(q => q !== question);

    displayCurrentQuestion();
    toggleQuestionList();
}

function toggleMultipleChoiceView(e) {
    const qaInput = document.querySelector('.qa-input');
    const qaControls = document.querySelector('.qa-controls');
    const qaFrontier = document.querySelector('.qa-frontier');

    if (e.target.checked) {
        qaInput.style.display = 'none';
        qaControls.style.display = 'none';
        qaFrontier.style.display = 'none';
    } else {
        qaInput.style.display = 'block';
        qaControls.style.display = 'block';
        qaFrontier.style.display = 'block';
    }
}

// AI Command Handler
async function handleAICommand(command) {
    try {
        const response = await fetch('/api/ai/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command, graph: state.activeGraph })
        });

        const result = await response.json();

        if (result.graphUpdates) {
            state.activeGraph = result.graphUpdates;
            updateEntitiesReferences();
            saveGraph();
        }

        if (result.message) {
            console.log('AI Response:', result.message);
        }
    } catch (error) {
        console.error('Error processing AI command:', error);
    }

    document.getElementById('ai-input').value = '';
}

// Graph Management
async function loadGraphFiles() {
    try {
        const response = await fetch('/api/graphs');
        const files = await response.json();

        // Update both dropdowns
        const selectors = [
            document.getElementById('graph-file-selector'),
            document.getElementById('start-graph-selector')
        ];

        selectors.forEach(selector => {
            selector.innerHTML = '<option value="">Select Graph File...</option>';
            files.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                selector.appendChild(option);
            });
        });
    } catch (error) {
        console.error('Error loading graph files:', error);
    }
}

async function saveGraph() {
    if (!state.activeGraph) return;

    try {
        await fetch('/api/graphs/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.activeGraph)
        });
    } catch (error) {
        console.error('Error saving graph:', error);
    }
}

// Utility Functions

// Global functions for inline onclick handlers
window.addEntity = addEntity;
window.addReference = addReference;
window.addConnection = addConnection;
window.editEntity = (type, key) => console.log('Edit entity:', type, key);
window.editReference = (key) => console.log('Edit reference:', key);
window.promptNewEntity = (type) => {
    const name = prompt(`Enter name for new ${type}:`);
    if (name) addEntity(type, name);
};