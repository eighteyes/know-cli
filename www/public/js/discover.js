// Discover Phase Implementation
class DiscoverPhase {
    constructor(app) {
        this.app = app;
        this.currentQuestion = null;
        this.questionHistory = [];
        this.extractedEntities = [];
        this.graphVisualizer = null;
        this.entityReviewer = new EntityReviewer(this);
    }

    async init() {
        this.renderInterface();
        await this.generateNextQuestion();
        this.bindEvents();
    }

    renderInterface() {
        const content = document.getElementById('phase-content');
        content.innerHTML = `
            <div class="discover-container">
                <div class="project-header">
                    <h2 id="project-name">${this.app.graph?.meta?.project?.name || 'New Project'}</h2>
                    <p id="project-tagline">${this.app.graph?.meta?.project?.tagline || 'Define your vision'}</p>
                </div>

                <div class="qa-section">
                    <div class="question-box">
                        <h3>Current Question:</h3>
                        <p id="current-question">Loading...</p>
                    </div>

                    <div class="answer-box">
                        <label>Your Answer:</label>
                        <textarea id="user-answer" rows="4" placeholder="Type your answer here..."></textarea>
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
                text: 'What are the main features your system needs to provide?',
                context: null
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
                text: 'What is the name of your project and what problem does it solve?',
                context: null
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
            'What are the main features your system needs to provide?',
            'Who are the users of your system and what roles do they have?',
            'What technical platforms or infrastructure will you use?',
            'What are the key business objectives this system must achieve?',
            'Are there any specific requirements or constraints?'
        ];

        return {
            type: 'exploration',
            text: explorationQuestions[Math.floor(Math.random() * explorationQuestions.length)],
            context: null
        };
    }

    displayQuestion(question) {
        document.getElementById('current-question').textContent = question.text;
        this.updateProgress();
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

        try {
            // Extract entities from answer
            const response = await fetch(`${this.app.apiBase}/discover/extract`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: this.currentQuestion,
                    answer: answer,
                    context: this.app.graph
                })
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

        } catch (error) {
            console.error('Failed to extract entities:', error);
            this.app.showError('Failed to process answer');
        }
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