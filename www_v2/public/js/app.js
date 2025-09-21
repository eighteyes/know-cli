// State Management
const state = {
    currentPage: 'start',
    activeGraph: null,
    originalGraph: null,  // Store original graph for reverting
    hasUnsavedChanges: false,
    currentFilename: null,
    forceMockMode: false,  // Track if mock mode is enabled via URL
    qaSession: {
        currentQuestion: null,
        questionQueue: [],
        answeredQuestions: [],
        skippedQuestions: [],
        answeredSinceRework: 0,
        reworkThreshold: 3
    },
    pendingModifications: {
        entities: [],
        references: [],
        connections: []
    }
};

// Check for mock mode in URL parameters
function checkMockMode() {
    const urlParams = new URLSearchParams(window.location.search);
    state.forceMockMode = urlParams.get('mock') === 'true';
    if (state.forceMockMode) {
        console.log('Mock mode enabled via URL parameter');
        console.log('Use ?mock=true to test with mock data including connections');
    }
}

// Get last selected graph from localStorage
function getLastSelectedGraph() {
    return localStorage.getItem('lastSelectedGraph');
}

// Save last selected graph to localStorage
function saveLastSelectedGraph(filename) {
    if (filename) {
        localStorage.setItem('lastSelectedGraph', filename);
        console.log('Saved last selected graph:', filename);
    }
}

// Load a specific graph file
async function loadSpecificGraph(filename) {
    if (!filename) return;

    try {
        const response = await fetch(`/api/graphs/${filename}`);
        const graphData = await response.json();
        state.activeGraph = graphData;
        state.originalGraph = JSON.parse(JSON.stringify(graphData));
        state.currentFilename = filename;
        state.hasUnsavedChanges = false;

        // Save this as the last selected graph
        saveLastSelectedGraph(filename);

        // Update UI with loaded graph
        updateEntitiesReferences();

        // Restore qaSession from graph if it exists
        if (graphData.qaSession) {
            state.qaSession = { ...graphData.qaSession };
        } else {
            // Reset qaSession for new graph
            state.qaSession = {
                currentQuestion: null,
                questionQueue: [],
                answeredQuestions: [],
                skippedQuestions: [],
                answeredSinceRework: 0,
                reworkThreshold: 3
            };
        }

        // Load saved Q&A sessions
        loadSavedQASessions();

        // Show sidebar toggle when graph is loaded
        if (state.currentPage !== 'start') {
            document.getElementById('sidebar-toggle').classList.remove('hidden');
        }

        // Refresh current page UI to show working interface elements
        navigateToPage(state.currentPage);

        // Auto-show sidebar when graph loads
        showSidebar();

        // Navigate to appropriate page
        if (state.currentPage === 'start') {
            navigateToPage('discover');
        } else if (state.currentPage === 'discover') {
            // Initialize discover page if we're already on it
            initializeDiscoverPage();
        }

        // Update the dropdown to show selected file
        const selectors = [
            document.getElementById('graph-file-selector'),
            document.getElementById('start-graph-selector')
        ];
        selectors.forEach(selector => {
            if (selector) selector.value = filename;
        });

        // Clear unsaved changes indicator since we just loaded
        clearUnsavedChanges();

        console.log('Graph loaded:', filename);
    } catch (error) {
        console.error('Error loading graph:', error);
        alert('Failed to load graph file');
    }
}

// Mock API responses
function getMockResponse(endpoint, body) {
    switch(endpoint) {
        case '/api/ai/generate-questions':
            return {
                questions: [
                    { text: "What are the primary user roles in the system?", source: 'mock' },
                    { text: "How should data be synchronized between components?", source: 'mock' },
                    { text: "What are the performance requirements?", source: 'mock' }
                ]
            };

        case '/api/ai/generate-prioritized-questions':
            return {
                questions: [
                    { text: "Which components have the most dependencies?", priority: 1, source: 'mock' },
                    { text: "What are the critical user journeys?", priority: 2, source: 'mock' },
                    { text: "How will the system handle failures?", priority: 3, source: 'mock' }
                ]
            };

        case '/api/ai/extract-entities':
            return {
                entities: [
                    { type: 'users', name: 'administrator', description: 'System admin user', reasoning: 'Administrative role detected from user management context' },
                    { type: 'features', name: 'user-management', description: 'User management feature', reasoning: 'Core feature identified from system requirements' },
                    { type: 'interfaces', name: 'admin-dashboard', description: 'Administrative interface', reasoning: 'Interface needed for admin operations' }
                ],
                references: [
                    { key: 'api_endpoint', value: '/api/v1/users', reasoning: 'API pattern detected for user operations' },
                    { key: 'admin_role', value: 'ADMIN', reasoning: 'Role constant for administrative access' }
                ],
                connections: [
                    { from: 'users:administrator', to: 'features:user-management', reasoning: 'Admin user needs access to user management feature' },
                    { from: 'features:user-management', to: 'interfaces:admin-dashboard', reasoning: 'User management feature is accessed through admin dashboard' },
                    { from: 'interfaces:admin-dashboard', to: 'users:administrator', reasoning: 'Admin dashboard is designed for administrator users' }
                ]
            };

        case '/api/ai/expand-question':
            return {
                multipleChoice: ['Option A: Cloud-based', 'Option B: On-premises', 'Option C: Hybrid', 'Option D: Edge computing'],
                recommendation: 'Consider Option A for scalability and reduced maintenance overhead',
                tradeoffs: 'Cloud offers scalability but may have latency concerns',
                alternatives: 'Hybrid approach could balance control and flexibility',
                challenges: 'Data sovereignty and compliance requirements need consideration'
            };

        default:
            return { status: 'mock', message: 'Mock response for ' + endpoint };
    }
}

// API Helper Function
async function apiCall(endpoint, body) {
    if (state.forceMockMode) {
        return getMockResponse(endpoint, body);
    }

    const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    return response.json();
}

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
    // Check for mock mode
    checkMockMode();

    // Auto-load last selected graph if we're starting on discover page
    const hash = window.location.hash.slice(1) || 'start';
    if (hash === 'discover') {
        const lastGraph = getLastSelectedGraph();
        if (lastGraph) {
            console.log('Auto-loading last graph on page load:', lastGraph);
            await loadSpecificGraph(lastGraph);
        }
    }

    initializeEventListeners();
    loadGraphFiles();

    // Handle initial route
    handleRoute();

    // Listen for hash changes
    window.addEventListener('hashchange', handleRoute);

    // Add event listeners for save/revert buttons
    document.getElementById('save-graph-btn').addEventListener('click', saveGraphChanges);
    document.getElementById('revert-graph-btn').addEventListener('click', revertGraphChanges);
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
    document.getElementById('skip-question').addEventListener('click', async () => {
        await skipCurrentQuestion();
        loadNextQuestion();
    });
    document.getElementById('expand-toggle').addEventListener('click', toggleExpandOptions);
    document.getElementById('next-question').addEventListener('click', loadNextQuestion);
    document.getElementById('toggle-question-list').addEventListener('click', toggleQuestionList);
    document.getElementById('show-multiple-choices').addEventListener('change', toggleMultipleChoiceView);
    document.getElementById('answers-input').addEventListener('input', handleAnswersInput);
    document.getElementById('answers-submit').addEventListener('click', handleAnswersSubmit);
    document.getElementById('commit-changes').addEventListener('click', commitPendingChanges);
    document.getElementById('discard-changes').addEventListener('click', discardPendingChanges);

    // Multiple choice will be handled dynamically when options are created

    // AI Bar
    document.getElementById('ai-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAICommand(e.target.value);
    });
    document.getElementById('ai-submit').addEventListener('click', () => {
        const input = document.getElementById('ai-input');
        handleAICommand(input.value);
    });
}

// Navigation
function navigateToPage(pageName) {
    // Re-check mock mode on navigation to ensure it's current
    checkMockMode();

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
        // Only show working interface elements if graph is loaded
        if (state.activeGraph) {
            aiBar.classList.remove('hidden');
            sidebar.classList.remove('hidden');
            sidebarToggle.classList.remove('hidden');

            // Show working interface elements
            const qaSection = document.querySelector('.qa-section');
            if (qaSection) qaSection.classList.remove('hidden');
        } else {
            aiBar.classList.add('hidden');
            sidebar.classList.add('hidden');
            sidebarToggle.classList.add('hidden');

            // Hide working interface elements when no graph is loaded
            const qaSection = document.querySelector('.qa-section');
            if (qaSection) qaSection.classList.add('hidden');
        }
    }

    // Page-specific initialization
    if (pageName === 'discover') {
        // Auto-load last selected graph if no graph is currently loaded
        if (!state.activeGraph) {
            const lastGraph = getLastSelectedGraph();
            if (lastGraph) {
                console.log('Auto-loading last selected graph for discover page:', lastGraph);
                loadSpecificGraph(lastGraph).then(() => {
                    initializeDiscoverPage();
                });
                return; // Don't call initializeDiscoverPage() synchronously
            }
        }
        initializeDiscoverPage();
    }
}

// Start Page Functions
async function handleVisionSubmit() {
    const visionInput = document.getElementById('vision-input');
    const vision = visionInput.value.trim();

    if (!vision) return;

    // Check if there's an existing graph with unsaved changes or active session
    if (state.activeGraph && (state.hasUnsavedChanges || state.qaSession.answeredQuestions.length > 0)) {
        const continueAnyway = confirm(
            'Starting a new vision will clear your current work and saved graph selection.\n\n' +
            'Continue anyway?'
        );
        if (!continueAnyway) {
            return;
        }
    }

    // Clear localStorage when starting a new project
    localStorage.removeItem('lastSelectedGraph');

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

    // Show sidebar and navigate to Discover page
    showSidebar();
    navigateToPage('discover');
}

async function handleGraphLoad(e) {
    const filename = e.target.value;
    await loadSpecificGraph(filename);
}

// Discover Page Functions
function initializeDiscoverPage() {
    // Load saved Q&A sessions first
    loadSavedQASessions();

    // If no current question but there are questions in queue, load the first one
    if (!state.qaSession.currentQuestion && state.qaSession.questionQueue.length > 0) {
        loadNextQuestion();
    } else if (state.qaSession.currentQuestion) {
        // Just display the current question
        displayCurrentQuestion();
    } else if (state.activeGraph && state.activeGraph.meta.vision_statement) {
        // Generate new questions if none exist
        generateQuestions(state.activeGraph.meta.vision_statement);
    }
}

async function generateQuestions(context) {
    try {
        // Use the new API helper function
        const data = await apiCall('/api/ai/generate-questions', {
            context,
            existingQA: state.qaSession.answeredQuestions
        });
        state.qaSession.questionQueue = data.questions;

        if (state.qaSession.questionQueue.length > 0) {
            loadNextQuestion();
        }
    } catch (error) {
        console.error('Error generating questions:', error);
    }
}

// Update batch progress indicator bullets
function updateBatchProgress() {
    const bullets = document.querySelectorAll('.batch-bullet');
    const currentPosition = state.qaSession.answeredSinceRework + 1; // 1, 2, or 3

    bullets.forEach((bullet, index) => {
        const position = index + 1;

        // Clear all classes first
        bullet.classList.remove('filled', 'current');

        if (position < currentPosition) {
            // Previously answered questions - filled
            bullet.classList.add('filled');
        } else if (position === currentPosition) {
            // Current question - pulsing
            bullet.classList.add('current');
        }
        // Future questions stay empty (default state)
    });
}

function displayCurrentQuestion() {
    const question = state.qaSession.currentQuestion;
    if (!question) return;

    // Calculate rework status
    const remainingForRework = state.qaSession.reworkThreshold - state.qaSession.answeredSinceRework;
    const questionNumber = (state.activeGraph?.meta?.qa_sessions || []).filter(s => s.answered).length + 1;

    // Update batch progress indicator
    updateBatchProgress();

    // Add rework indicator
    let displayText = question.text;
    let reworkStatus = '';

    if (remainingForRework === 1) {
        displayText += ' 🔄';
        reworkStatus = ' <span style="color: var(--accent-color)">(Last in batch - Modifications next)</span>';
    }

    // Update question text
    const questionTextElement = document.getElementById('question-text');
    if (questionTextElement) {
        questionTextElement.textContent = displayText;
    }

    // Display upcoming questions with indicators
    if (state.qaSession.questionQueue.length > 0) {
        const nextQ = state.qaSession.questionQueue[0];
        let nextText = nextQ.text;
        if (nextQ.source === 'ai-reworked') nextText = `🔄 ${nextText}`;
        if (nextQ === state.qaSession.currentQuestion) nextText = `⤵️ ${nextText} (skipped to end)`;
        document.getElementById('next-question-preview').textContent = nextText;
    } else {
        document.getElementById('next-question-preview').textContent = 'Queue will be reworked...';
    }

    if (state.qaSession.questionQueue.length > 1) {
        const nextNextQ = state.qaSession.questionQueue[1];
        let nextNextText = nextNextQ.text;
        if (nextNextQ.source === 'ai-reworked') nextNextText = `🔄 ${nextNextText}`;
        if (nextNextQ === state.qaSession.currentQuestion) nextNextText = `⤵️ ${nextNextText} (skipped to end)`;
        document.getElementById('next-next-question-preview').textContent = nextNextText;
    } else {
        document.getElementById('next-next-question-preview').textContent = '';
    }
}

function loadNextQuestion() {
    console.log('loadNextQuestion called, queue length:', state.qaSession.questionQueue.length);

    // Simply advance to the next question in the queue
    if (state.qaSession.questionQueue.length === 0) {
        console.log('Queue empty, generating questions...');
        generateQuestions(state.activeGraph.meta.vision_statement);
        return;
    }

    state.qaSession.currentQuestion = state.qaSession.questionQueue.shift();
    console.log('New current question:', state.qaSession.currentQuestion?.text);
    displayCurrentQuestion();

    // Clear previous answer
    document.getElementById('answer-input').value = '';
    document.getElementById('extraction-choices').classList.add('hidden');
    // Show QA controls back when hiding modifications
    document.querySelector('.qa-input').style.display = '';
    document.querySelector('.qa-controls').style.display = '';
    document.getElementById('expand-options').classList.add('hidden');
}

async function skipCurrentQuestion() {
    if (!state.qaSession.currentQuestion) return;

    // According to spec: Skip moves first hidden question (position 4) to end of batch
    // This means the current question goes away and question 4 becomes question 3

    // Store the skipped question to potentially use later
    const skippedQuestion = state.qaSession.currentQuestion;

    // Add the skipped question to the end of the entire queue
    state.qaSession.questionQueue.push(skippedQuestion);

    // The next question will naturally become current when loadNextQuestion is called
    // This effectively moves question 4 into the batch (position 3)

    // Hide extraction UI since we're continuing the batch
    document.getElementById('extraction-choices').classList.add('hidden');

    // Note: Don't increment batch counter - skip just rearranges the batch
}

async function handleAnswerSubmit() {
    console.log('handleAnswerSubmit called');
    const answer = document.getElementById('answer-input').value.trim();
    console.log('Answer:', answer);
    if (!answer) {
        console.log('No answer provided, returning early');
        return;
    }

    // Check if there's a current question
    if (!state.qaSession.currentQuestion) {
        console.log('No current question available');
        return;
    }

    // Initialize qa_sessions if it doesn't exist
    if (!state.activeGraph.meta.qa_sessions) {
        state.activeGraph.meta.qa_sessions = [];
    }

    // Get selected multiple choice options if any
    const selectedOptions = Array.from(document.querySelectorAll('.mc-option.selected'))
        .map(opt => opt.textContent.trim());

    // Create session entry
    const sessionEntry = {
        question: state.qaSession.currentQuestion.text,
        answer: answer,
        answered: true,
        skipped: false,
        timestamp: new Date().toISOString(),
        source: state.qaSession.currentQuestion.source || 'user',
        expandedOptions: state.qaSession.currentQuestion.expandedOptions || null
    };

    // Add to graph's qa_sessions
    state.activeGraph.meta.qa_sessions.push(sessionEntry);

    // Store in local session for immediate use
    state.qaSession.answeredQuestions.push({
        question: state.qaSession.currentQuestion.text,
        answer: answer
    });

    // Increment answered count
    state.qaSession.answeredSinceRework++;

    // Mark changes to persist Q&A session
    saveGraph();

    // Check if we've completed a batch (every 3 answers)
    const batchComplete = state.qaSession.answeredSinceRework >= state.qaSession.reworkThreshold;
    console.log('Batch complete?', batchComplete, 'answered:', state.qaSession.answeredSinceRework, 'threshold:', state.qaSession.reworkThreshold);

    if (batchComplete) {
        // Batch is complete - show extraction/modifications for all 3 answers
        await showBatchExtractions();

        // After processing extractions, rework questions
        await reworkQuestionsForClarity();
        state.qaSession.answeredSinceRework = 0;

        // Update batch progress to reset for new batch
        updateBatchProgress();

        // DON'T call loadNextQuestion() - wait for user to commit/discard modifications
        // loadNextQuestion() will be called from commitPendingChanges() or discardPendingChanges()
    } else {
        // Not at batch boundary - hide extraction UI and continue
        document.getElementById('extraction-choices').classList.add('hidden');

        if (state.qaSession.questionQueue.length < 5) {
            // Generate more questions if queue is running low
            generateQuestions(answer);
        }

        // Load next question automatically only when not at batch boundary
        console.log('Loading next question...');
        loadNextQuestion();
    }
}

// Show extractions for the last batch of answers
async function showBatchExtractions() {
    // Get the last 3 answered questions
    const recentAnswers = state.qaSession.answeredQuestions.slice(-3);

    if (recentAnswers.length === 0) return;

    // Combine all recent answers into one context
    const combinedText = recentAnswers.map((qa, index) =>
        `Q${index + 1}: ${qa.question}\nA${index + 1}: ${qa.answer}`
    ).join('\n\n');

    // Extract entities and references from the combined batch
    await extractEntitiesReferences(combinedText, true);
}

async function extractEntitiesReferences(text, isBatchExtraction = false) {
    try {
        let data;
        if (state.forceMockMode) {
            // Use mock response
            data = getMockResponse('/api/ai/extract-entities', { text, graph: state.activeGraph });
            console.log('Using mock response for extract-entities');
        } else {
            const response = await fetch('/api/ai/extract-entities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, graph: state.activeGraph })
            });
            data = await response.json();
        }

        // Display detections with reasoning
        const detectionsList = document.getElementById('detections-list');
        detectionsList.innerHTML = '';

        // Add batch completion header if this is a batch extraction
        if (isBatchExtraction) {
            const batchHeader = document.createElement('div');
            batchHeader.className = 'batch-header';
            batchHeader.innerHTML = '<strong>Batch Complete!</strong> Based on your last 3 answers, we found:';
            batchHeader.style.marginBottom = '15px';
            batchHeader.style.color = 'var(--accent-color)';
            detectionsList.appendChild(batchHeader);
        }

        data.entities.forEach(entity => {
            const li = document.createElement('li');
            li.className = 'detection-item with-reasoning';

            // Escape any quotes in the entity name for onclick
            const escapedName = entity.name.replace(/'/g, "\\'");
            const escapedReason = (entity.reasoning || '').replace(/'/g, "\\'");

            li.innerHTML = `
                <div class="detection-content">
                    <div class="detection-header">
                        <span class="detection-label">${entity.type}: ${entity.name}</span>
                        <button class="add-btn" onclick="addEntity('${entity.type}', '${escapedName}', '${escapedReason}', this)">+</button>
                    </div>
                    ${entity.reasoning ? `<div class="detection-reasoning">${entity.reasoning}</div>` : ''}
                </div>
            `;
            detectionsList.appendChild(li);
        });

        data.references.forEach(ref => {
            const li = document.createElement('li');
            li.className = 'detection-item with-reasoning';

            // Escape any quotes for onclick
            const escapedKey = ref.key.replace(/'/g, "\\'");
            const escapedValue = (ref.value || '').replace(/'/g, "\\'");
            const escapedReason = (ref.reasoning || '').replace(/'/g, "\\'");

            li.innerHTML = `
                <div class="detection-content">
                    <div class="detection-header">
                        <span class="detection-label">Reference: ${ref.key}</span>
                        <button class="add-btn" onclick="addReference('${escapedKey}', '${escapedValue}', this)">+</button>
                    </div>
                    ${ref.reasoning ? `<div class="detection-reasoning">${ref.reasoning}</div>` : ''}
                </div>
            `;
            detectionsList.appendChild(li);
        });

        document.getElementById('extraction-choices').classList.remove('hidden');
        // Hide QA controls when showing modifications
        document.querySelector('.qa-input').style.display = 'none';
        document.querySelector('.qa-controls').style.display = 'none';

        // Always show connections section, but only populate if there are connections
        console.log('Extraction data:', data);
        console.log('Connections found:', data.connections?.length || 0);

        if (data.connections && data.connections.length > 0) {
            displayConnections(data.connections);
        } else {
            // Show empty connections section with a message
            const connectionsList = document.getElementById('connections-list');
            connectionsList.innerHTML = '<li class="no-connections">No connections detected in this batch.</li>';
            document.getElementById('connections').classList.remove('hidden');
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
        li.className = 'connection-item with-reasoning';

        // Escape quotes for onclick
        const escapedFrom = conn.from.replace(/'/g, "\\'");
        const escapedTo = conn.to.replace(/'/g, "\\'");

        li.innerHTML = `
            <div class="detection-content">
                <div class="detection-header">
                    <span class="detection-label">${conn.from} → ${conn.to}</span>
                    <button class="add-btn" onclick="addConnection('${escapedFrom}', '${escapedTo}', this)">+</button>
                </div>
                ${conn.reasoning ? `<div class="detection-reasoning">${conn.reasoning}</div>` : ''}
            </div>
        `;
        connectionsList.appendChild(li);
    });

    document.getElementById('connections').classList.remove('hidden');
}

// Entity/Reference Management - Stage changes before committing
function addEntity(type, name, description = '', button) {
    // Add to pending changes
    const change = { type, name, description };

    // Check if already pending
    const existing = state.pendingModifications.entities.find(e =>
        e.type === type && e.name === name
    );

    if (!existing) {
        state.pendingModifications.entities.push(change);

        // Update button visual state
        if (button) {
            button.classList.add('selected');
            button.textContent = '✓';
        }
    } else {
        // Remove if clicking again (toggle)
        state.pendingModifications.entities = state.pendingModifications.entities.filter(e =>
            !(e.type === type && e.name === name)
        );

        if (button) {
            button.classList.remove('selected');
            button.textContent = '+';
        }
    }

    updatePendingChangesSummary();
}

function addReference(key, value, button) {
    // Add to pending changes
    const change = { key, value };

    // Check if already pending
    const existing = state.pendingModifications.references.find(r => r.key === key);

    if (!existing) {
        state.pendingModifications.references.push(change);

        // Update button visual state
        if (button) {
            button.classList.add('selected');
            button.textContent = '✓';
        }
    } else {
        // Remove if clicking again (toggle)
        state.pendingModifications.references = state.pendingModifications.references.filter(r =>
            r.key !== key
        );

        if (button) {
            button.classList.remove('selected');
            button.textContent = '+';
        }
    }

    updatePendingChangesSummary();
}

function addConnection(from, to, button) {
    // Add to pending changes
    const change = { from, to, type: 'depends_on' };

    // Check if already pending
    const existing = state.pendingModifications.connections.find(c =>
        c.from === from && c.to === to
    );

    if (!existing) {
        state.pendingModifications.connections.push(change);

        // Update button visual state
        if (button) {
            button.classList.add('selected');
            button.textContent = '✓';
        }
    } else {
        // Remove if clicking again (toggle)
        state.pendingModifications.connections = state.pendingModifications.connections.filter(c =>
            !(c.from === from && c.to === to)
        );

        if (button) {
            button.classList.remove('selected');
            button.textContent = '+';
        }
    }

    updatePendingChangesSummary();
}

// Update pending changes summary display
function updatePendingChangesSummary() {
    const summary = document.getElementById('pending-changes-summary');
    const pendingSection = document.getElementById('pending-changes');

    const hasChanges = state.pendingModifications.entities.length > 0 ||
                      state.pendingModifications.references.length > 0 ||
                      state.pendingModifications.connections.length > 0;

    if (hasChanges) {
        let html = '';

        // Show entities
        state.pendingModifications.entities.forEach(e => {
            html += `<div class="change-item entity">+ Entity: ${e.type}:${e.name}</div>`;
        });

        // Show references
        state.pendingModifications.references.forEach(r => {
            html += `<div class="change-item reference">+ Reference: ${r.key} = ${r.value}</div>`;
        });

        // Show connections
        state.pendingModifications.connections.forEach(c => {
            html += `<div class="change-item connection">+ Connection: ${c.from} → ${c.to}</div>`;
        });

        summary.innerHTML = html;
        pendingSection.classList.remove('hidden');
    } else {
        pendingSection.classList.add('hidden');
    }
}

// Commit all pending changes
async function commitPendingChanges() {
    // Apply entities
    state.pendingModifications.entities.forEach(e => {
        if (!state.activeGraph.entities[e.type]) {
            state.activeGraph.entities[e.type] = {};
        }
        state.activeGraph.entities[e.type][e.name] = {
            description: e.description || ''
        };
    });

    // Apply references
    state.pendingModifications.references.forEach(r => {
        state.activeGraph.references[r.key] = r.value;
    });

    // Apply connections
    state.pendingModifications.connections.forEach(c => {
        // Initialize graph entry if it doesn't exist
        if (!state.activeGraph.graph[c.from]) {
            state.activeGraph.graph[c.from] = { depends_on: [] };
        }
        // Add the dependency if it doesn't already exist
        if (!state.activeGraph.graph[c.from].depends_on.includes(c.to)) {
            state.activeGraph.graph[c.from].depends_on.push(c.to);
        }
    });

    // Clear pending
    state.pendingModifications = {
        entities: [],
        references: [],
        connections: []
    };

    // Update UI
    updateEntitiesReferences();
    saveGraph();

    // Hide extraction UI
    document.getElementById('extraction-choices').classList.add('hidden');
    // Show QA controls back when hiding modifications
    document.querySelector('.qa-input').style.display = '';
    document.querySelector('.qa-controls').style.display = '';

    // Generate fresh questions after modifications
    await generateFreshQuestions();

    // Load next question after committing changes
    loadNextQuestion();
}

// Discard all pending changes
function discardPendingChanges() {
    // Clear pending
    state.pendingModifications = {
        entities: [],
        references: [],
        connections: []
    };

    // Reset all buttons
    document.querySelectorAll('.add-btn.selected').forEach(btn => {
        btn.classList.remove('selected');
        btn.textContent = '+';
    });

    // Hide extraction UI
    document.getElementById('extraction-choices').classList.add('hidden');
    // Show QA controls back when hiding modifications
    document.querySelector('.qa-input').style.display = '';
    document.querySelector('.qa-controls').style.display = '';

    // Load next question after discarding changes
    loadNextQuestion();
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

            // Add new entity input with description
            const addContainer = document.createElement('div');
            addContainer.className = 'add-entity-container';
            addContainer.innerHTML = `
                <input type="text" class="add-entity-input add-entity-name" placeholder="+ Add new ${key.slice(0, -1)}..." data-type="${key}">
                <input type="text" class="add-entity-desc" placeholder="Description..." style="display:none;">
                <div class="edit-actions" style="display:none;">
                    <button class="save-btn" title="Save">✓</button>
                    <button class="cancel-btn" title="Cancel">✕</button>
                </div>
            `;

            const nameInput = addContainer.querySelector('.add-entity-name');
            const descInput = addContainer.querySelector('.add-entity-desc');
            const editActions = addContainer.querySelector('.edit-actions');
            const saveBtn = addContainer.querySelector('.save-btn');
            const cancelBtn = addContainer.querySelector('.cancel-btn');

            const resetForm = () => {
                nameInput.value = '';
                descInput.value = '';
                descInput.style.display = 'none';
                editActions.style.display = 'none';
                nameInput.placeholder = `+ Add new ${key.slice(0, -1)}...`;
            };

            const saveNewEntity = () => {
                const newKey = nameInput.value.trim().toLowerCase().replace(/\s+/g, '-');
                const newDesc = descInput.value.trim();
                if (newKey) {
                    addEntity(key, newKey, newDesc);
                    resetForm();
                    updateEntitiesReferences();
                }
            };

            nameInput.addEventListener('focus', () => {
                descInput.style.display = 'block';
                editActions.style.display = 'flex';
                nameInput.placeholder = 'Name...';
            });

            nameInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') saveNewEntity();
                if (e.key === 'Escape') resetForm();
            });

            descInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') saveNewEntity();
                if (e.key === 'Escape') resetForm();
            });

            saveBtn.addEventListener('click', saveNewEntity);
            cancelBtn.addEventListener('click', resetForm);

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
        <div class="edit-actions">
            <button class="save-btn" title="Save">✓</button>
            <button class="cancel-btn" title="Cancel">✕</button>
            <button class="delete-btn" title="Delete">🗑️</button>
        </div>
    `;

    const nameInput = item.querySelector('.entity-name-input');
    const descInput = item.querySelector('.entity-desc-input');
    const saveBtn = item.querySelector('.save-btn');
    const cancelBtn = item.querySelector('.cancel-btn');
    const deleteBtn = item.querySelector('.delete-btn');

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

    const deleteEntity = () => {
        if (confirm(`Are you sure you want to delete "${currentName}"?`)) {
            delete state.activeGraph.entities[entityType][entityKey];
            saveGraph();
            updateEntitiesReferences();
        }
    };

    const exitEditMode = () => {
        updateEntitiesReferences();
    };

    saveBtn.addEventListener('click', saveChanges);
    cancelBtn.addEventListener('click', exitEditMode);
    deleteBtn.addEventListener('click', deleteEntity);

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
        <div class="edit-actions">
            <button class="save-btn" title="Save">✓</button>
            <button class="cancel-btn" title="Cancel">✕</button>
            <button class="delete-btn" title="Delete">🗑️</button>
        </div>
    `;

    const nameInput = item.querySelector('.entity-name-input');
    const valueInput = item.querySelector('.entity-desc-input');
    const saveBtn = item.querySelector('.save-btn');
    const cancelBtn = item.querySelector('.cancel-btn');
    const deleteBtn = item.querySelector('.delete-btn');

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

    const deleteReference = () => {
        if (confirm(`Are you sure you want to delete "${currentName}"?`)) {
            delete state.activeGraph.references[category][itemKey];
            saveGraph();
            updateEntitiesReferences();
        }
    };

    const exitEditMode = () => {
        updateEntitiesReferences();
    };

    saveBtn.addEventListener('click', saveChanges);
    cancelBtn.addEventListener('click', exitEditMode);
    deleteBtn.addEventListener('click', deleteReference);

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

function showSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');
    if (!sidebar.classList.contains('open')) {
        sidebar.classList.add('open');
        toggle.classList.add('open');
        toggle.textContent = '▶';
    }
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
        let data;
        if (state.forceMockMode) {
            // Use mock response
            data = getMockResponse('/api/ai/expand-question', { question: state.qaSession.currentQuestion.text });
            console.log('Using mock response for expand-question');
        } else {
            const response = await fetch('/api/ai/expand-question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: state.qaSession.currentQuestion.text })
            });
            data = await response.json();
        }

        // Save expanded options to current question
        state.qaSession.currentQuestion.expandedOptions = {
            choices: data.choices,
            recommendation: data.recommendation,
            tradeoffs: data.tradeoffs,
            alternatives: data.alternatives,
            challenges: data.challenges
        };

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

    // Also update the answers input to reflect the current selections
    updateAnswersInputFromSelections();
}

// Update answers input field based on current selections
function updateAnswersInputFromSelections() {
    const selectedOptions = document.querySelectorAll('.mc-option.selected');
    const selections = [];

    // Get current question number
    const questionText = document.getElementById('current-question').textContent;
    const questionNumMatch = questionText.match(/Question #(\d+)/);
    const currentQuestionNum = questionNumMatch ? parseInt(questionNumMatch[1]) : 1;

    selectedOptions.forEach(opt => {
        const letter = opt.dataset.choice.toUpperCase();
        selections.push(`${currentQuestionNum}${letter}`);
    });

    // Update the answers input field
    const answersInput = document.getElementById('answers-input');
    if (answersInput && selections.length > 0) {
        // Preserve other question answers and update current question
        const currentValue = answersInput.value;
        const otherAnswers = currentValue.split(/[\s,]+/)
            .filter(a => {
                const match = a.match(/^(\d+)[A-E]/i);
                return match && parseInt(match[1]) !== currentQuestionNum;
            });

        const allAnswers = [...otherAnswers, ...selections].sort((a, b) => {
            const numA = parseInt(a.match(/^(\d+)/)[1]);
            const numB = parseInt(b.match(/^(\d+)/)[1]);
            return numA - numB;
        });

        answersInput.value = allAnswers.join(' ');
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

    // Get recent answered/skipped from qa_sessions (last 3)
    const recentSessions = (state.activeGraph?.meta?.qa_sessions || []).slice(-3);
    recentSessions.forEach(session => {
        const li = document.createElement('li');
        if (session.answered) {
            li.className = 'question-item answered';
            li.textContent = `✓ ${session.question}`;
        } else if (session.skipped) {
            li.className = 'question-item skipped';
            li.textContent = `⊘ ${session.question}`;
        }
        ul.appendChild(li);
    });

    // Show current question with rework indicator
    if (state.qaSession.currentQuestion) {
        const li = document.createElement('li');
        li.className = 'question-item current';
        const remainingForRework = state.qaSession.reworkThreshold - state.qaSession.answeredSinceRework;
        const reworkIndicator = remainingForRework === 1 ? ' 🔄' : '';
        li.textContent = `▶ ${state.qaSession.currentQuestion.text}${reworkIndicator}`;
        if (remainingForRework === 1) {
            li.title = 'Next answer will trigger AI question rework for clarity';
        }
        ul.appendChild(li);
    }

    // Filter queue to only show unanswered/unskipped questions
    const answeredTexts = new Set(state.qaSession.answeredQuestions.map(q => q.question));
    const skippedTexts = new Set(state.qaSession.skippedQuestions.map(q => q.text));
    const availableQuestions = state.qaSession.questionQueue.filter(q =>
        !answeredTexts.has(q.text) && !skippedTexts.has(q.text)
    );

    // Show only top 3 upcoming questions
    availableQuestions.slice(0, 3).forEach((q, index) => {
        const li = document.createElement('li');
        li.className = 'question-item';

        // Check if we should show multiple choices
        const showChoices = document.getElementById('show-multiple-choices')?.checked;

        // Create question text with number
        const questionNumber = index + 1;
        let questionHTML = `<span class="question-number">${questionNumber}.</span> `;

        // Add visual distinction for AI-generated questions
        if (q.source === 'ai-generated') {
            li.className += ' ai-generated';
            questionHTML += `🤖 ${q.text}`;
            if (q.priority) {
                li.title = `Priority: ${q.priority}/10`;
            }
        } else {
            questionHTML += q.text;
        }

        // If checkbox is checked and question has expandedOptions, show multiple choices
        if (showChoices && q.expandedOptions?.choices) {
            questionHTML += '<div class="question-choices">';
            ['A', 'B', 'C', 'D', 'E'].forEach((letter, i) => {
                if (q.expandedOptions.choices[i]) {
                    const selected = q.multipleChoiceAnswer === letter ? ' selected' : '';
                    questionHTML += `<div class="choice-item${selected}">
                        <span class="choice-letter">${letter}.</span> ${q.expandedOptions.choices[i]}
                    </div>`;
                }
            });
            questionHTML += '</div>';
        } else if (showChoices) {
            // Show placeholder if no choices available
            questionHTML += '<div class="no-choices">(No multiple choices available - click "Expand Options" for this question)</div>';
        }

        li.innerHTML = questionHTML;
        li.onclick = () => selectQuestion(q);
        ul.appendChild(li);
    });

    // Add indicator if more questions are available
    if (availableQuestions.length > 3) {
        const li = document.createElement('li');
        li.className = 'question-item more-indicator';
        li.textContent = `... and ${availableQuestions.length - 3} more questions`;
        li.style.fontStyle = 'italic';
        li.style.color = 'var(--text-secondary)';
        ul.appendChild(li);
    }
}

function selectQuestion(question) {
    // Mark current question as skipped if it exists and hasn't been answered
    if (state.qaSession.currentQuestion && !state.qaSession.answeredQuestions.find(q => q.question === state.qaSession.currentQuestion.text)) {
        // Initialize qa_sessions if it doesn't exist
        if (!state.activeGraph.meta.qa_sessions) {
            state.activeGraph.meta.qa_sessions = [];
        }

        // Add skipped entry to graph
        state.activeGraph.meta.qa_sessions.push({
            question: state.qaSession.currentQuestion.text,
            answer: null,
            answered: false,
            skipped: true,
            timestamp: new Date().toISOString(),
            source: state.qaSession.currentQuestion.source || 'user',
            expandedOptions: state.qaSession.currentQuestion.expandedOptions || null
        });

        // Save graph to persist the skip
        saveGraph();

        // Add to skipped questions list
        state.qaSession.skippedQuestions.push(state.qaSession.currentQuestion);
    }

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
    const answersBar = document.querySelector('.answers-bar');

    if (e.target.checked) {
        qaInput.style.display = 'none';
        qaControls.style.display = 'none';
        qaFrontier.style.display = 'none';
        answersBar.style.display = 'block';
    } else {
        qaInput.style.display = 'block';
        qaControls.style.display = 'block';
        qaFrontier.style.display = 'block';
        answersBar.style.display = 'none';
    }
}

// Handle answers input for multiple choice workflow
function handleAnswersInput(e) {
    const input = e.target.value.trim();

    // Parse input format: "1 A 2 B, 3 D" or "1A 2B 3D" etc.
    const answerPattern = /(\d+)\s*([A-E])/gi;
    const matches = [...input.matchAll(answerPattern)];

    // Clear all selections first
    document.querySelectorAll('.mc-option').forEach(opt => {
        opt.classList.remove('selected');
    });

    // Apply selections based on parsed input
    matches.forEach(match => {
        const questionNum = parseInt(match[1]);
        const choiceLetter = match[2].toLowerCase();

        // Find the corresponding multiple choice option
        const option = document.querySelector(`.mc-option[data-choice="${choiceLetter}"]`);
        if (option) {
            option.classList.add('selected');
        }
    });

    // Update the main answer input based on selections
    updateAnswerFromSelections();
}

function handleAnswersSubmit() {
    const input = document.getElementById('answers-input').value.trim();
    if (!input) return;

    // Parse input and apply answers to questions
    const answerPattern = /(\d+)\s*([A-E])/gi;
    const matches = [...input.matchAll(answerPattern)];

    // Apply answers to the questions in the queue
    matches.forEach(match => {
        const questionNum = parseInt(match[1]) - 1; // 0-indexed
        const choiceLetter = match[2].toUpperCase();

        // Store the answer for the question
        if (state.qaSession.questionQueue[questionNum]) {
            if (!state.qaSession.questionQueue[questionNum].multipleChoiceAnswer) {
                state.qaSession.questionQueue[questionNum].multipleChoiceAnswer = choiceLetter;
            }
        }
    });

    // Clear the input
    document.getElementById('answers-input').value = '';

    // Update the question list display to show the answers
    displayQuestionList();
}

// Update answer input based on selected multiple choice options
function updateAnswerFromSelections() {
    const selectedOptions = document.querySelectorAll('.mc-option.selected');
    const selectedTexts = [];

    selectedOptions.forEach(opt => {
        const fullText = opt.textContent.trim();
        // Remove the "A. " prefix (letter + dot + space)
        const answerText = fullText.substring(3);
        selectedTexts.push(answerText);
    });

    // Update the answer input with selected choices
    if (selectedTexts.length > 0) {
        document.getElementById('answer-input').value = selectedTexts.join('; ');
    } else {
        document.getElementById('answer-input').value = '';
    }
}

// Rework questions for clarity after threshold
async function reworkQuestionsForClarity() {
    try {
        console.log('Reworking questions for maximum clarity...');

        let result;
        if (state.forceMockMode) {
            // Use mock response
            result = getMockResponse('/api/ai/generate-prioritized-questions', {
                graph: state.activeGraph,
                existingQA: state.activeGraph.meta.qa_sessions || [],
                context: 'REWORK: Focus on maximizing graph connectivity and clarity'
            });
            console.log('Using mock response for rework questions');
        } else {
            // Call the prioritized question generation endpoint
            const response = await fetch('/api/ai/generate-prioritized-questions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    graph: state.activeGraph,
                    existingQA: state.activeGraph.meta.qa_sessions || [],
                    context: 'REWORK: Focus on maximizing graph connectivity and clarity'
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to generate questions');
            }

            result = await response.json();
        }

        if (result.questions && result.questions.length > 0) {
            // Clear existing queue and replace with reworked questions
            const reworkedQuestions = result.questions.map(q => ({
                ...q,
                source: 'ai-reworked',
                priority: q.priority || 10,
                reworkedAt: new Date().toISOString()
            }));

            // Sort by priority
            reworkedQuestions.sort((a, b) => b.priority - a.priority);

            // Replace queue with reworked questions
            state.qaSession.questionQueue = reworkedQuestions;

            // Save reworked questions to qa_sessions
            saveAPIQuestionsToSessions(reworkedQuestions, 'ai-reworked');

            // Update display
            displayQuestionList();

            // Show notification
            console.log(`🔄 Questions reworked! ${reworkedQuestions.length} new prioritized questions generated.`);

            // Add rework marker to graph
            if (!state.activeGraph.meta.reworks) {
                state.activeGraph.meta.reworks = [];
            }
            state.activeGraph.meta.reworks.push({
                timestamp: new Date().toISOString(),
                questionCount: reworkedQuestions.length,
                afterAnswers: state.qaSession.answeredQuestions.length
            });

            saveGraph();
        }
    } catch (error) {
        console.error('Error reworking questions:', error);
        // Fallback to regular generation
        generateQuestions('Please generate questions that maximize clarity and connectivity');
    }
}

// AI Command Handler
async function handleAICommand(command) {
    const lowerCommand = command.toLowerCase();

    // Check if we should force mock mode (from URL or command)
    const forceMock = state.forceMockMode || lowerCommand.includes('?mock=true');

    // Strip the mock parameter for further processing
    const cleanCommand = command.replace('?mock=true', '').trim();
    const cleanLowerCommand = cleanCommand.toLowerCase();

    // Check if it's a mock/test command (only explicit commands)
    if (cleanLowerCommand === 'mock' || cleanLowerCommand === 'test' || cleanLowerCommand === 'demo') {
        // Generate mock questions immediately
        const mockQuestions = [
            { text: "What are the primary user personas for this application?", source: 'mock' },
            { text: "How should the authentication system handle session management?", source: 'mock' },
            { text: "What data models are needed for the core functionality?", source: 'mock' },
            { text: "Which features should be prioritized in the MVP?", source: 'mock' },
            { text: "How will the system handle real-time updates?", source: 'mock' }
        ];

        // Replace the first three questions in the queue
        const remainingQuestions = state.qaSession.questionQueue.slice(3);
        state.qaSession.questionQueue = [
            ...mockQuestions.slice(0, 3),
            ...remainingQuestions
        ];

        // If no current question, set the first one
        if (!state.qaSession.currentQuestion && mockQuestions.length > 0) {
            state.qaSession.currentQuestion = mockQuestions[0];
            state.qaSession.questionQueue.shift();
            displayCurrentQuestion();
        }

        // Update UI
        displayQuestionList();
        console.log('Mock questions loaded');
        document.getElementById('ai-input').value = '';
        return;
    }

    // Check if it's a "new" command for fresh questions
    if (cleanLowerCommand === 'new' || cleanLowerCommand === 'fresh' || cleanLowerCommand === 'refresh') {
        if (state.forceMockMode) {
            // Generate fresh mock questions (only in URL mock mode)
            const mockQuestions = [
                { text: "What are the key performance indicators for this system?", source: 'mock' },
                { text: "How should error handling be implemented across components?", source: 'mock' },
                { text: "What accessibility standards should the UI follow?", source: 'mock' },
                { text: "Which third-party services will the system integrate with?", source: 'mock' },
                { text: "How will the system scale to handle increased load?", source: 'mock' }
            ];
            state.qaSession.questionQueue = mockQuestions;
            if (!state.qaSession.currentQuestion && mockQuestions.length > 0) {
                state.qaSession.currentQuestion = mockQuestions[0];
                state.qaSession.questionQueue.shift();
                displayCurrentQuestion();
            }
            displayQuestionList();
            console.log('Fresh mock questions loaded');
        } else {
            generateFreshQuestions();
        }
        document.getElementById('ai-input').value = '';
        return;
    }

    // Check if it's an add/modify command (but not "new")
    if ((cleanLowerCommand.startsWith('add ') || cleanLowerCommand.startsWith('create ')) ||
        (cleanLowerCommand.startsWith('new ') && cleanLowerCommand !== 'new')) {
        if (state.forceMockMode) {
            // Show mock modification proposal (only in URL mock mode)
            showMockModificationProposal(cleanCommand);
        } else {
            showModificationProposal(cleanCommand);
        }
        document.getElementById('ai-input').value = '';
        return;
    }

    // Default behavior: generate questions for any non-empty input
    // (unless it's a specific mock command handled above)
    if (cleanCommand.trim()) {
        if (state.forceMockMode) {
            // Generate mock prioritized questions (only in URL mock mode)
            const mockQuestions = [
                { text: `Mock question based on: ${cleanCommand}`, source: 'mock' },
                { text: "What dependencies exist between components?", source: 'mock' },
                { text: "How should the system handle edge cases?", source: 'mock' },
                { text: "What are the security considerations?", source: 'mock' },
                { text: "How will data consistency be maintained?", source: 'mock' }
            ];
            const remainingQuestions = state.qaSession.questionQueue.slice(3);
            state.qaSession.questionQueue = [
                ...mockQuestions.slice(0, 3),
                ...remainingQuestions
            ];
            if (!state.qaSession.currentQuestion && mockQuestions.length > 0) {
                state.qaSession.currentQuestion = mockQuestions[0];
                state.qaSession.questionQueue.shift();
                displayCurrentQuestion();
            }
            displayQuestionList();
            console.log('Mock prioritized questions generated');
            document.getElementById('ai-input').value = '';
            return;
        }

        try {
            let result;
            if (state.forceMockMode) {
                // Use mock response for prioritized questions
                result = getMockResponse('/api/ai/generate-prioritized-questions', {
                    graph: state.activeGraph,
                    existingQA: state.qaSession.answeredQuestions,
                    context: command
                });
                console.log('Using mock response for prioritized questions');
            } else {
                // Generate prioritized questions
                const response = await fetch('/api/ai/generate-prioritized-questions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        graph: state.activeGraph,
                        existingQA: state.qaSession.answeredQuestions,
                        context: command
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.message || 'Failed to generate questions');
                }

                result = await response.json();
            }

            if (result.questions) {
                // Add AI-generated questions to a separate queue with visual distinction
                const aiQuestions = result.questions.map(q => ({
                    ...q,
                    source: 'ai-generated'
                }));

                // Questions are already prioritized by position in array

                // Replace the first three questions in the queue
                const remainingQuestions = state.qaSession.questionQueue.slice(3); // Keep questions after the first 3
                state.qaSession.questionQueue = [
                    ...aiQuestions.slice(0, 3), // Take top 3 AI questions
                    ...remainingQuestions
                ];

                // Save AI-generated questions to qa_sessions
                saveAPIQuestionsToSessions(aiQuestions, 'ai-generated');

                // If no current question, set the first one
                if (!state.qaSession.currentQuestion && aiQuestions.length > 0) {
                    state.qaSession.currentQuestion = aiQuestions[0];
                    state.qaSession.questionQueue.shift();
                    displayCurrentQuestion();
                }

                // Update UI
                displayQuestionList();
                displayCurrentQuestion(); // Ensure current question is updated
                console.log(`AI Generated ${aiQuestions.length} prioritized questions`);

                // Clear the AI input
                document.getElementById('ai-input').value = '';
            }
        } catch (error) {
            console.error('Error generating questions:', error);
        }
    }
}

// Helper function to save API-generated questions to qa_sessions
function saveAPIQuestionsToSessions(questions, source) {
    if (!state.activeGraph || !questions || questions.length === 0) return;

    // Initialize qa_sessions if it doesn't exist
    if (!state.activeGraph.meta.qa_sessions) {
        state.activeGraph.meta.qa_sessions = [];
    }

    // Add questions to qa_sessions as API-generated entries
    questions.forEach(question => {
        const sessionEntry = {
            question: question.text,
            answer: null,
            answered: false,
            skipped: false,
            timestamp: new Date().toISOString(),
            source: source || 'api-generated',
            priority: question.priority || null,
            api_generated: true
        };

        // Check if this question already exists
        const existingQuestion = state.activeGraph.meta.qa_sessions.find(
            s => s.question === question.text && s.api_generated
        );

        if (!existingQuestion) {
            state.activeGraph.meta.qa_sessions.push(sessionEntry);
        }
    });

    // Mark graph as having unsaved changes
    saveGraph();
}

// Generate fresh questions (used by "new" command and after modifications)
async function generateFreshQuestions() {
    try {
        const context = state.activeGraph?.meta?.vision_statement ||
                       'Generate questions to explore the system architecture';

        let result;
        if (state.forceMockMode) {
            // Use mock response
            result = getMockResponse('/api/ai/generate-prioritized-questions', {
                graph: state.activeGraph,
                existingQA: state.qaSession.answeredQuestions,
                context: `Generate fresh questions focusing on unexplored areas. Context: ${context}`
            });
            console.log('Using mock response for fresh questions');
        } else {
            // Call the prioritized question generation endpoint
            const response = await fetch('/api/ai/generate-prioritized-questions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    graph: state.activeGraph,
                    existingQA: state.qaSession.answeredQuestions,
                    context: `Generate fresh questions focusing on unexplored areas. Context: ${context}`
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to generate questions');
            }

            result = await response.json();
        }

        if (result.questions) {
            // Replace entire queue with fresh questions
            const freshQuestions = result.questions.map(q => ({
                ...q,
                source: 'ai-fresh'
            }));

            // Set new queue
            state.qaSession.questionQueue = freshQuestions;

            // Save fresh questions to qa_sessions
            saveAPIQuestionsToSessions(freshQuestions, 'ai-fresh');

            // If no current question, set the first one
            if (!state.qaSession.currentQuestion && freshQuestions.length > 0) {
                state.qaSession.currentQuestion = freshQuestions[0];
                state.qaSession.questionQueue.shift();
                displayCurrentQuestion();
            }

            // Update UI
            displayQuestionList();
            console.log(`Generated ${freshQuestions.length} fresh questions`);
        }
    } catch (error) {
        console.error('Error generating fresh questions:', error);
        // Fallback to regular generation
        generateQuestions('Generate fresh questions about the system');
    }
}

// Show modification proposal using the existing extraction UI
async function showModificationProposal(command) {
    try {
        // Parse the command to extract what's being added
        const match = command.match(/^(add|create|new)\s+(\w+)\s+(.+)$/i);
        if (!match) {
            console.log('Invalid add command format');
            return;
        }

        const entityType = match[2].toLowerCase();
        const entityName = match[3].trim();

        // Check if it's a valid entity type
        const validEntityTypes = ['users', 'user', 'objectives', 'objective', 'actions', 'action',
                                 'requirements', 'requirement', 'features', 'feature',
                                 'interfaces', 'interface', 'components', 'component'];

        if (validEntityTypes.includes(entityType)) {
            // Normalize entity type to plural form
            const normalizedType = entityType.endsWith('s') ? entityType : entityType + 's';

            // Use the existing extraction UI to show the proposal
            const detectionsList = document.getElementById('detections-list');
            detectionsList.innerHTML = '';

            // Create a detection item for the proposed entity
            const li = document.createElement('li');
            li.className = 'detection-item with-reasoning';

            const escapedName = entityName.replace(/'/g, "\\'");
            li.innerHTML = `
                <div class="detection-content">
                    <div class="detection-header">
                        <span class="detection-label">${normalizedType}: ${entityName}</span>
                        <button class="add-btn" onclick="addEntity('${normalizedType}', '${escapedName}')">+</button>
                    </div>
                    <div class="detection-reasoning">Proposed via AI command</div>
                </div>
            `;
            detectionsList.appendChild(li);

            // Show the extraction choices UI
            document.getElementById('extraction-choices').classList.remove('hidden');
            // Hide QA controls when showing modifications
            document.querySelector('.qa-input').style.display = 'none';
            document.querySelector('.qa-controls').style.display = 'none';

            // Hide connections for now since this is just adding a single entity
            document.getElementById('connections').classList.add('hidden');
        } else {
            console.log('Unknown entity type:', entityType);
        }
    } catch (error) {
        console.error('Error showing modification proposal:', error);
    }
}

// Show mock modification proposal using the existing extraction UI
function showMockModificationProposal(command) {
    // Parse the command to extract what's being added
    const match = command.match(/^(add|create|new)\s+(\w+)\s+(.+)$/i);
    if (!match) {
        console.log('Invalid add command format');
        return;
    }

    const entityType = match[2].toLowerCase();
    const entityName = match[3].trim();

    // Use the existing extraction UI to show the mock proposal
    const detectionsList = document.getElementById('detections-list');
    detectionsList.innerHTML = '';

    // Create mock detection items
    const mockDetections = [
        { type: entityType, name: entityName, reasoning: "Primary entity from command (mock)" },
        { type: 'interfaces', name: `${entityName}-interface`, reasoning: "Related interface needed (mock)" },
        { type: 'components', name: `${entityName}-component`, reasoning: "Implementation component (mock)" }
    ];

    mockDetections.forEach(detection => {
        const li = document.createElement('li');
        li.className = 'detection-item with-reasoning';

        const normalizedType = detection.type.endsWith('s') ? detection.type : detection.type + 's';
        const escapedName = detection.name.replace(/'/g, "\\'");

        li.innerHTML = `
            <div class="detection-content">
                <div class="detection-header">
                    <span class="detection-label">${normalizedType}: ${detection.name}</span>
                    <button class="add-btn" onclick="addEntity('${normalizedType}', '${escapedName}')">+</button>
                </div>
                <div class="detection-reasoning">${detection.reasoning}</div>
            </div>
        `;
        detectionsList.appendChild(li);
    });

    // Mock connections
    const connectionsList = document.getElementById('connections-list');
    connectionsList.innerHTML = `
        <li class="connection-item">
            <span>${entityName} → ${entityName}-interface</span>
            <button class="add-btn" onclick="addConnection('${entityName}', '${entityName}-interface')">+</button>
        </li>
        <li class="connection-item">
            <span>${entityName}-interface → ${entityName}-component</span>
            <button class="add-btn" onclick="addConnection('${entityName}-interface', '${entityName}-component')">+</button>
        </li>
    `;

    // Show both detections and connections
    document.getElementById('extraction-choices').classList.remove('hidden');
    document.getElementById('connections').classList.remove('hidden');
    // Hide QA controls when showing modifications
    document.querySelector('.qa-input').style.display = 'none';
    document.querySelector('.qa-controls').style.display = 'none';

    console.log('Mock modification proposal shown');
}

// Load saved Q&A sessions from graph
function loadSavedQASessions() {
    if (!state.activeGraph?.meta?.qa_sessions) {
        return;
    }

    const qaSessions = state.activeGraph.meta.qa_sessions;

    // Reset Q&A session state
    state.qaSession.questionQueue = [];
    state.qaSession.answeredQuestions = [];
    state.qaSession.skippedQuestions = [];
    state.qaSession.currentQuestion = null;
    state.qaSession.answeredSinceRework = 0;

    // Rebuild answered and skipped questions from saved sessions
    qaSessions.forEach(session => {
        if (session.answered) {
            state.qaSession.answeredQuestions.push({
                question: session.question,
                answer: session.answer
            });
            state.qaSession.answeredSinceRework++;
        } else if (session.skipped) {
            state.qaSession.skippedQuestions.push({
                text: session.question,
                source: session.source,
                expandedOptions: session.expandedOptions
            });
        }
    });

    // Reset answeredSinceRework if we've hit the threshold
    if (state.qaSession.answeredSinceRework >= state.qaSession.reworkThreshold) {
        state.qaSession.answeredSinceRework = state.qaSession.answeredSinceRework % state.qaSession.reworkThreshold;
    }

    // Build a queue of unanswered questions from previous sessions
    const unansweredQuestions = qaSessions
        .filter(session => !session.answered && !session.skipped)
        .map(session => ({
            text: session.question,
            source: session.source || 'saved',
            expandedOptions: session.expandedOptions || null
        }));

    // Add unanswered questions to queue
    state.qaSession.questionQueue = unansweredQuestions;

    // Set current question if available
    if (state.qaSession.questionQueue.length > 0) {
        state.qaSession.currentQuestion = state.qaSession.questionQueue.shift();
    }

    // Always update the question display when loading, regardless of current page
    if (state.qaSession.currentQuestion) {
        displayCurrentQuestion();
    }
    displayQuestionList();
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

function saveGraph() {
    if (!state.activeGraph) return;

    // Save qaSession state to activeGraph
    state.activeGraph.qaSession = { ...state.qaSession };

    // Just mark that we have unsaved changes
    // Actual saving happens when user clicks save button
    markUnsavedChanges();
}

function markUnsavedChanges() {
    state.hasUnsavedChanges = true;
    updateFilenameDisplay();
    document.getElementById('save-graph-btn').style.display = 'inline-block';
    document.getElementById('revert-graph-btn').style.display = 'inline-block';
}

function clearUnsavedChanges() {
    state.hasUnsavedChanges = false;
    updateFilenameDisplay();
    document.getElementById('save-graph-btn').style.display = 'none';
    document.getElementById('revert-graph-btn').style.display = 'none';
}

function updateFilenameDisplay() {
    const selector = document.getElementById('graph-file-selector');
    if (state.currentFilename) {
        const option = selector.querySelector(`option[value="${state.currentFilename}"]`);
        if (option) {
            const originalText = state.currentFilename;
            option.textContent = state.hasUnsavedChanges ? `${originalText} *` : originalText;
        }
    }
}

async function saveGraphChanges() {
    if (!state.activeGraph || !state.hasUnsavedChanges) return;

    // Save qaSession state to graph before persisting
    state.activeGraph.qaSession = { ...state.qaSession };

    try {
        const response = await fetch('/api/graphs/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...state.activeGraph,
                filename: state.currentFilename
            })
        });

        if (response.ok) {
            state.originalGraph = JSON.parse(JSON.stringify(state.activeGraph));
            clearUnsavedChanges();
            console.log('Graph saved successfully');
        }
    } catch (error) {
        console.error('Error saving graph:', error);
    }
}

function revertGraphChanges() {
    if (!state.originalGraph || !state.hasUnsavedChanges) return;

    if (confirm('Are you sure you want to revert all unsaved changes?')) {
        state.activeGraph = JSON.parse(JSON.stringify(state.originalGraph));

        // Restore qaSession from original graph if it exists
        if (state.originalGraph.qaSession) {
            state.qaSession = { ...state.originalGraph.qaSession };
        }

        updateEntitiesReferences();
        clearUnsavedChanges();
        console.log('Changes reverted');
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