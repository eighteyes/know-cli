// Discover Phase Implementation
class DiscoverPhase {
    constructor(app) {
        this.app = app;
        this.currentQuestion = null;
        this.questionHistory = [];
        this.extractedEntities = [];
        this.graphVisualizer = null;
        this.entityReviewer = new EntityReviewer(this);
        // Load expand state from localStorage, defaulting to false
        this.isQuestionExpanded = localStorage.getItem('discoverExpandQuestion') === 'true';
    }

    async init() {
        this.renderInterface();
        // Only proceed with questions if graph is loaded
        if (this.app.graph) {
            await this.generateNextQuestion();
            this.bindEvents();
        }
    }

    // Method to refresh the phase (called from app.js)
    async refresh() {
        await this.generateNextQuestion();
    }

    renderInterface() {
        const content = document.getElementById('phase-content');

        // Show empty state if no graph is loaded
        if (!this.app.graph) {
            content.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #666;">
                    <div style="text-align: center;">
                        <div style="font-size: 3em; opacity: 0.2; margin-bottom: 20px;">🌙</div>
                        <h2 style="margin-bottom: 20px; opacity: 0.8;">No Knowledge Graph Loaded</h2>
                        <p style="font-size: 1.2em; margin-bottom: 30px; opacity: 0.7;">Begin your journey by loading or creating a graph</p>
                        <p style="font-size: 0.9em; opacity: 0.5;">Go to the Start tab to select a graph or describe your vision</p>
                    </div>
                </div>`;
            return;
        }

        content.innerHTML = `
            <div class="discover-container">

                <div class="qa-section">
                    <div class="question-box">
                        <div class="question-header">
                            <h3>Current Question:</h3>
                            <button id="expand-question-toggle" class="expand-toggle" title="Show context and guidance">
                                <span class="expand-icon">${this.isQuestionExpanded ? '▼' : '▶'}</span>
                                <span class="expand-text">Expand Question</span>
                            </button>
                        </div>
                        <p id="current-question">Loading...</p>
                        <div id="question-context" class="question-context ${this.isQuestionExpanded ? 'expanded' : 'collapsed'}">
                            <div class="context-content">
                                <div class="guidance">
                                    <h4>💡 Guidance</h4>
                                    <p id="guidance-text">Loading context...</p>
                                </div>
                                <div class="multiple-choice" id="multiple-choice" style="display: none;">
                                    <h4>📝 Suggested Options</h4>
                                    <div id="choice-options"></div>
                                </div>
                                <div class="assumptions" id="assumptions" style="display: none;">
                                    <h4>🤔 Assumptions</h4>
                                    <ul id="assumptions-list"></ul>
                                </div>
                                <div class="examples" id="examples" style="display: none;">
                                    <h4>📋 Examples</h4>
                                    <ul id="examples-list"></ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="answer-box">
                        <label>Your Answer:</label>
                        <textarea id="user-answer" rows="4" placeholder="Type your answer here..."></textarea>
                        <div id="answer-guidance" class="answer-guidance ${this.isQuestionExpanded ? 'expanded' : 'collapsed'}">
                            <div class="guidance-content">
                                <div class="next-questions">
                                    <h4>📋 Coming Up</h4>
                                    <div id="upcoming-questions"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="qa-controls">
                        <button id="prev-question">Previous</button>
                        <button id="skip-question">Skip</button>
                        <button id="submit-answer">Submit Answer</button>
                    </div>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>

                <div class="entity-suggestions hidden" id="entity-suggestions">
                    <h4>AI Suggestions (<span id="suggestion-count">0</span> entities detected):</h4>
                    <div class="suggestion-list" id="suggestion-list"></div>
                    <div class="suggestion-controls">
                        <button id="review-entities">Review & Edit</button>
                        <button id="accept-all">Accept All</button>
                        <button id="reject-all">Reject</button>
                    </div>
                </div>

                <div class="gap-analysis">
                    <h4>Gap Analysis:</h4>
                    <ul class="gap-list" id="gap-list">
                        <li>Analyzing graph for missing information...</li>
                    </ul>
                </div>

                <div class="graph-visualization">
                    <canvas id="graph-canvas"></canvas>
                </div>
            </div>
        `;
    }

    bindEvents() {
        document.getElementById('submit-answer').addEventListener('click', () => this.submitAnswer());
        document.getElementById('skip-question').addEventListener('click', () => this.generateNextQuestion());
        document.getElementById('prev-question').addEventListener('click', () => this.previousQuestion());

        document.getElementById('review-entities')?.addEventListener('click', () => {
            if (this.extractedEntities.length > 0) {
                this.entityReviewer.show(this.extractedEntities);
            }
        });

        document.getElementById('accept-all')?.addEventListener('click', () => this.acceptAllEntities());
        document.getElementById('reject-all')?.addEventListener('click', () => this.rejectEntities());

        // Expand question toggle functionality
        document.getElementById('expand-question-toggle')?.addEventListener('click', () => {
            this.toggleQuestionExpand();
        });

        // Allow Enter key in answer box to submit
        document.getElementById('user-answer').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.submitAnswer();
            }
        });
    }

    async generateNextQuestion() {
        try {
            // Get gaps from the graph
            const gaps = await this.analyzeGaps();

            // Generate targeted question
            const question = this.createQuestionFromGaps(gaps);

            this.currentQuestion = question;
            this.displayQuestion(question);

        } catch (error) {
            console.error('Failed to generate question:', error);
            // Fallback to default question
            this.currentQuestion = {
                type: 'exploration',
                text: 'What are the main features your system needs to provide? (default)',
                context: null,
                isDefault: true
            };
            this.displayQuestion(this.currentQuestion);
        }
    }

    async analyzeGaps() {
        try {
            const response = await fetch(`${this.app.apiBase}/discover/analyze-gaps`, {
                method: 'POST'
            });
            const gaps = await response.json();

            // Update gap display
            this.displayGaps(gaps);

            return gaps;
        } catch (error) {
            console.error('Failed to analyze gaps:', error);
            return {
                missingDependencies: [],
                incompleteEntities: [],
                orphanedEntities: []
            };
        }
    }

    createQuestionFromGaps(gaps) {
        // If we have no entities at all, start with basics
        if (!this.app.graph?.entities || Object.keys(this.app.graph.entities).every(type =>
            Object.keys(this.app.graph.entities[type]).length === 0)) {
            return {
                type: 'initial',
                text: 'What is the name of your project and what problem does it solve? (default)',
                context: null,
                isDefault: true
            };
        }

        // Check for missing dependencies
        if (gaps.missingDependencies && gaps.missingDependencies.length > 0) {
            const entity = gaps.missingDependencies[0];
            return {
                type: 'dependency',
                text: `What components or services does ${entity} need to function?`,
                context: entity
            };
        }

        // Check for incomplete entities
        if (gaps.incompleteEntities && gaps.incompleteEntities.length > 0) {
            const entity = gaps.incompleteEntities[0];
            return {
                type: 'completion',
                text: `Can you describe more about ${entity}? What are its key responsibilities?`,
                context: entity
            };
        }

        // Default exploration questions
        const explorationQuestions = [
            'What are the main features your system needs to provide? (default)',
            'Who are the users of your system and what roles do they have? (default)',
            'What technical platforms or infrastructure will you use? (default)',
            'What are the key business objectives this system must achieve? (default)',
            'Are there any specific requirements or constraints? (default)'
        ];

        return {
            type: 'exploration',
            text: explorationQuestions[Math.floor(Math.random() * explorationQuestions.length)],
            context: null
        };
    }

    displayQuestion(question) {
        document.getElementById('current-question').textContent = question.text;
        this.updateQuestionContext(question);
        this.updateProgress();
    }

    updateQuestionContext(question) {
        // Generate context based on question type and current graph state
        const guidance = this.generateGuidance(question);
        document.getElementById('guidance-text').textContent = guidance.text;

        // Show/hide multiple choice if available
        const multipleChoiceDiv = document.getElementById('multiple-choice');
        const choiceOptions = document.getElementById('choice-options');
        if (guidance.multipleChoice && guidance.multipleChoice.length > 0) {
            multipleChoiceDiv.style.display = 'block';
            choiceOptions.innerHTML = guidance.multipleChoice.map((choice, index) =>
                `<div class="choice-option" data-choice="${choice}">
                    <span class="choice-text">${choice}</span>
                </div>`
            ).join('');

            // Add click handlers to populate answer box
            choiceOptions.querySelectorAll('.choice-option').forEach(option => {
                option.addEventListener('click', () => {
                    const choice = option.dataset.choice;
                    const answerBox = document.getElementById('user-answer');
                    const currentAnswer = answerBox.value.trim();

                    // Toggle selection visual feedback
                    option.classList.add('selected');
                    setTimeout(() => option.classList.remove('selected'), 200);

                    // Append to existing answer if there's content, otherwise replace
                    if (currentAnswer) {
                        answerBox.value = currentAnswer + '\n\n' + choice;
                    } else {
                        answerBox.value = choice;
                    }

                    // Focus the answer box
                    answerBox.focus();
                });
            });
        } else {
            multipleChoiceDiv.style.display = 'none';
        }

        // Show/hide assumptions if available
        const assumptionsDiv = document.getElementById('assumptions');
        const assumptionsList = document.getElementById('assumptions-list');
        if (guidance.assumptions && guidance.assumptions.length > 0) {
            assumptionsDiv.style.display = 'block';
            assumptionsList.innerHTML = guidance.assumptions.map(assumption =>
                `<li>${assumption}</li>`
            ).join('');
        } else {
            assumptionsDiv.style.display = 'none';
        }

        // Show/hide examples if available
        const examplesDiv = document.getElementById('examples');
        const examplesList = document.getElementById('examples-list');
        if (guidance.examples && guidance.examples.length > 0) {
            examplesDiv.style.display = 'block';
            examplesList.innerHTML = guidance.examples.map(example =>
                `<li>${example}</li>`
            ).join('');
        } else {
            examplesDiv.style.display = 'none';
        }

        // Update upcoming questions
        this.updateUpcomingQuestions();
    }

    updateUpcomingQuestions() {
        const upcomingDiv = document.getElementById('upcoming-questions');
        const nextQuestions = this.generateUpcomingQuestions();

        upcomingDiv.innerHTML = nextQuestions.map((q, index) =>
            `<div class="upcoming-question">
                <span class="question-number">${index + 1}.</span>
                <span class="question-preview">${q}</span>
            </div>`
        ).join('');
    }

    generateUpcomingQuestions() {
        // Generate next 2 potential questions based on current graph state
        const questions = [];

        if (!this.app.graph?.entities || Object.keys(this.app.graph.entities).every(type =>
            Object.keys(this.app.graph.entities[type]).length === 0)) {
            questions.push(
                "What are the main user roles in your system? (default)",
                "What are the core features users need? (default)"
            );
        } else {
            questions.push(
                "How do these components connect to each other? (default)",
                "What are the key business requirements? (default)"
            );
        }

        return questions;
    }

    generateGuidance(question) {
        // Generate contextual guidance based on question type and graph state
        let guidance = {
            text: '',
            multipleChoice: [],
            assumptions: [],
            examples: []
        };

        switch (question.type) {
            case 'initial':
                guidance.text = "Establish your project foundation. Focus on the core problem and primary purpose.";
                guidance.examples = [
                    "Fleet Management System - Manages autonomous delivery robots",
                    "Healthcare Portal - Connects patients with healthcare providers",
                    "E-commerce Platform - Online marketplace for artisan goods"
                ];
                guidance.assumptions = [
                    "You understand your target users",
                    "You've identified the main problem to solve"
                ];
                break;

            case 'dependency':
                guidance.text = "Think about technical components, services, or data this entity needs. Consider direct and indirect dependencies.";
                guidance.multipleChoice = [
                    "Database connections",
                    "External APIs",
                    "User authentication",
                    "Real-time communication",
                    "File storage"
                ];
                guidance.assumptions = [
                    "Dependencies should be clearly defined",
                    "Each dependency serves a specific purpose"
                ];
                break;

            case 'completion':
                guidance.text = "Provide detailed information about this entity's purpose, functionality, and system integration.";
                guidance.examples = [
                    "What data does it handle?",
                    "What operations can users perform?",
                    "How does it interact with other components?"
                ];
                guidance.assumptions = [
                    "More detail leads to better system design",
                    "Clear responsibilities prevent overlap"
                ];
                break;

            case 'exploration':
            default:
                guidance.text = "Explore different system aspects. Think broadly about functionality, users, technical requirements, and business goals.";
                guidance.multipleChoice = [
                    "User management and authentication",
                    "Data processing and analytics",
                    "Real-time communication",
                    "External integrations",
                    "Mobile and web interfaces"
                ];
                guidance.assumptions = [
                    "Your system serves multiple user types",
                    "You need data storage and processing capabilities"
                ];
                break;
        }

        return guidance;
    }

    toggleQuestionExpand() {
        this.isQuestionExpanded = !this.isQuestionExpanded;

        // Save state to localStorage for persistence
        localStorage.setItem('discoverExpandQuestion', this.isQuestionExpanded.toString());

        // Update UI
        const contextDiv = document.getElementById('question-context');
        const answerGuidanceDiv = document.getElementById('answer-guidance');
        const expandIcon = document.querySelector('.expand-icon');

        if (this.isQuestionExpanded) {
            contextDiv.classList.remove('collapsed');
            contextDiv.classList.add('expanded');
            answerGuidanceDiv.classList.remove('collapsed');
            answerGuidanceDiv.classList.add('expanded');
            expandIcon.textContent = '▼';
        } else {
            contextDiv.classList.remove('expanded');
            contextDiv.classList.add('collapsed');
            answerGuidanceDiv.classList.remove('expanded');
            answerGuidanceDiv.classList.add('collapsed');
            expandIcon.textContent = '▶';
        }
    }

    displayGaps(gaps) {
        const gapList = document.getElementById('gap-list');
        gapList.innerHTML = '';

        let gapCount = 0;

        if (gaps.missingDependencies?.length > 0) {
            gaps.missingDependencies.forEach(dep => {
                const li = document.createElement('li');
                li.textContent = `Missing dependencies for ${dep}`;
                gapList.appendChild(li);
                gapCount++;
            });
        }

        if (gaps.incompleteEntities?.length > 0) {
            gaps.incompleteEntities.forEach(entity => {
                const li = document.createElement('li');
                li.textContent = `Incomplete information for ${entity}`;
                gapList.appendChild(li);
                gapCount++;
            });
        }

        if (gaps.orphanedEntities?.length > 0) {
            gaps.orphanedEntities.forEach(entity => {
                const li = document.createElement('li');
                li.textContent = `${entity} has no connections`;
                gapList.appendChild(li);
                gapCount++;
            });
        }

        if (gapCount === 0) {
            const li = document.createElement('li');
            li.textContent = 'No critical gaps detected';
            li.style.color = '#00C896';
            gapList.appendChild(li);
        }
    }

    async submitAnswer() {
        const answer = document.getElementById('user-answer').value.trim();
        if (!answer) {
            this.app.showError('Please provide an answer');
            return;
        }

        // Use AI Request Manager for debouncing and indicator
        const aiRequestManager = window.aiRequestManager || this.app.aiRequestManager;
        await aiRequestManager.makeRequest('submit-answer', async (signal) => {
            try {
                // Extract entities from answer
                const response = await fetch(`${this.app.apiBase}/discover/extract`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: this.currentQuestion,
                        answer: answer,
                        context: this.app.graph
                    }),
                    signal // Pass abort signal for cancellation
                });

                const result = await response.json();
                this.extractedEntities = result.entities;

                // Display suggestions
                this.displaySuggestions(result.entities);

                // Save to history
                this.questionHistory.push({
                    question: this.currentQuestion,
                    answer: answer,
                    entities: result.entities
                });

                // Clear answer box
                document.getElementById('user-answer').value = '';

                return result;
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error('Failed to extract entities:', error);
                    this.app.showError('Failed to process answer');
                }
                throw error;
            }
        });
    }

    displaySuggestions(entities) {
        const container = document.getElementById('entity-suggestions');
        const list = document.getElementById('suggestion-list');
        const count = document.getElementById('suggestion-count');

        container.classList.remove('hidden');
        count.textContent = entities.length;

        list.innerHTML = entities.map((entity, index) => `
            <div class="suggestion-item">
                <input type="checkbox" id="entity-${index}" checked>
                <label for="entity-${index}">
                    <strong>${entity.type}:</strong> ${entity.name}
                </label>
            </div>
        `).join('');
    }

    async acceptAllEntities() {
        // Save Q&A session first
        await this.saveQASession();

        for (const entity of this.extractedEntities) {
            await this.addEntityToGraph(entity);
        }

        this.app.showSuccess(`Added ${this.extractedEntities.length} entities`);
        this.extractedEntities = [];

        // Hide suggestions
        document.getElementById('entity-suggestions').classList.add('hidden');

        // Refresh graph
        await this.app.loadGraph();

        // Generate next question
        await this.generateNextQuestion();
    }

    async saveQASession() {
        const answer = document.getElementById('user-answer').value;
        if (!answer || !this.currentQuestion) return;

        try {
            await fetch(`${this.app.apiBase}/discover/save-qa`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: this.currentQuestion,
                    answer: answer,
                    entities: this.extractedEntities
                })
            });
        } catch (error) {
            console.error('Failed to save Q&A session:', error);
        }
    }

    async addEntityToGraph(entity) {
        try {
            // Add entity using know mod command
            await this.app.executeKnowCommand('mod', [
                'add',
                entity.type + 's',  // Convert to plural
                entity.id,
                entity.name
            ]);

            // Add dependencies if any
            if (entity.dependencies && entity.dependencies.length > 0) {
                for (const dep of entity.dependencies) {
                    await this.app.executeKnowCommand('mod', [
                        'connect',
                        `${entity.type}:${entity.id}`,
                        dep
                    ]);
                }
            }
        } catch (error) {
            console.error('Failed to add entity:', error);
            this.app.showError(`Failed to add ${entity.name}`);
        }
    }

    rejectEntities() {
        this.extractedEntities = [];
        document.getElementById('entity-suggestions').classList.add('hidden');
    }

    previousQuestion() {
        if (this.questionHistory.length > 0) {
            const prev = this.questionHistory.pop();
            this.currentQuestion = prev.question;
            this.displayQuestion(prev.question);
            document.getElementById('user-answer').value = prev.answer;
        }
    }

    updateProgress() {
        // Calculate rough progress based on entity count
        const entityCount = this.countEntities();
        const targetEntities = 50; // Target for good coverage
        const progress = Math.min(100, (entityCount / targetEntities) * 100);

        document.getElementById('progress-fill').style.width = `${progress}%`;
    }

    countEntities() {
        if (!this.app.graph?.entities) return 0;

        let count = 0;
        for (const type of Object.values(this.app.graph.entities)) {
            count += Object.keys(type).length;
        }
        return count;
    }

    refresh() {
        // Called when graph is updated externally
        this.updateProgress();
    }
}

// Entity Reviewer for editing extracted entities
class EntityReviewer {
    constructor(discoverPhase) {
        this.discover = discoverPhase;
        this.entities = [];
    }

    show(entities) {
        this.entities = entities;

        const modal = document.getElementById('entity-review-modal');
        const content = document.getElementById('entity-review-content');

        content.innerHTML = this.renderEntityCards();
        modal.classList.remove('hidden');

        this.bindModalEvents();
    }

    renderEntityCards() {
        return `
            <p>AI extracted ${this.entities.length} entities from your answer:</p>
            <div class="entity-list">
                ${this.entities.map((entity, index) => this.renderEntityCard(entity, index)).join('')}
            </div>
        `;
    }

    renderEntityCard(entity, index) {
        return `
            <div class="entity-card" data-index="${index}">
                <div class="entity-header">
                    <input type="checkbox" class="entity-select" data-index="${index}" checked>

                    <select class="entity-type" data-index="${index}">
                        <option value="feature" ${entity.type === 'feature' ? 'selected' : ''}>Feature</option>
                        <option value="component" ${entity.type === 'component' ? 'selected' : ''}>Component</option>
                        <option value="interface" ${entity.type === 'interface' ? 'selected' : ''}>Interface</option>
                        <option value="requirement" ${entity.type === 'requirement' ? 'selected' : ''}>Requirement</option>
                    </select>
                </div>

                <div class="entity-fields">
                    <label>
                        ID:
                        <input type="text" class="entity-id" data-index="${index}" value="${entity.id}">
                    </label>

                    <label>
                        Name:
                        <input type="text" class="entity-name" data-index="${index}" value="${entity.name}">
                    </label>

                    <label>
                        Description:
                        <textarea class="entity-description" data-index="${index}">${entity.description || ''}</textarea>
                    </label>
                </div>

                ${entity.validation?.hasDuplicates ? `
                    <div class="validation-warning">
                        ⚠ Similar entity exists: ${entity.validation.duplicates[0].entity.name}
                        <div class="duplicate-actions">
                            <button onclick="app.phases.discover.entityReviewer.merge(${index})">Merge</button>
                            <button onclick="app.phases.discover.entityReviewer.keepBoth(${index})">Keep Both</button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    bindModalEvents() {
        const modal = document.getElementById('entity-review-modal');

        // Close button
        modal.querySelector('.close-modal').addEventListener('click', () => this.close());

        // Action buttons
        document.getElementById('accept-entities').addEventListener('click', () => this.acceptSelected());
        document.getElementById('cancel-review').addEventListener('click', () => this.close());
        document.getElementById('validate-entities').addEventListener('click', () => this.validateEntities());
    }

    async acceptSelected() {
        const selected = [];
        const checkboxes = document.querySelectorAll('.entity-select:checked');

        for (const checkbox of checkboxes) {
            const index = parseInt(checkbox.dataset.index);
            const entity = this.getEntityFromForm(index);
            selected.push(entity);
        }

        // Add entities to graph
        for (const entity of selected) {
            await this.discover.addEntityToGraph(entity);
        }

        this.close();
        this.discover.app.showSuccess(`Added ${selected.length} entities`);

        // Refresh and continue
        await this.discover.app.loadGraph();
        await this.discover.generateNextQuestion();
    }

    getEntityFromForm(index) {
        const entity = { ...this.entities[index] };

        entity.type = document.querySelector(`.entity-type[data-index="${index}"]`).value;
        entity.id = document.querySelector(`.entity-id[data-index="${index}"]`).value;
        entity.name = document.querySelector(`.entity-name[data-index="${index}"]`).value;
        entity.description = document.querySelector(`.entity-description[data-index="${index}"]`).value;

        return entity;
    }

    async validateEntities() {
        // Run validation on selected entities
        const selected = document.querySelectorAll('.entity-select:checked');

        for (const checkbox of selected) {
            const index = parseInt(checkbox.dataset.index);
            const entity = this.getEntityFromForm(index);

            try {
                const validation = await this.discover.app.executeKnowCommand('validate', [
                    `${entity.type}:${entity.id}`
                ]);
                console.log('Validation result:', validation);
            } catch (error) {
                console.error('Validation failed:', error);
            }
        }
    }

    close() {
        document.getElementById('entity-review-modal').classList.add('hidden');
    }

    merge(index) {
        // Merge with existing entity
        console.log('Merge entity at index:', index);
        // Implementation would merge with the duplicate
    }

    keepBoth(index) {
        // Keep both entities with different IDs
        const entity = this.entities[index];
        entity.id = entity.id + '-2';
        document.querySelector(`.entity-id[data-index="${index}"]`).value = entity.id;
    }
}