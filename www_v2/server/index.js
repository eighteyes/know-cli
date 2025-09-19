const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');

const app = express();
const PORT = 8880;

// Initialize Anthropic client
const anthropic = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY
});

// Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, '../public')));

// CORS for development
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

// Paths
const GRAPHS_DIR = path.join(__dirname, '../graphs');
const AI_SPEC_GRAPH = path.join(__dirname, '../../../.ai/spec-graph.json');
const KNOW_TOOL = path.join(__dirname, '../../../know/know');

// Ensure graphs directory exists
async function ensureGraphsDir() {
    try {
        await fs.access(GRAPHS_DIR);
    } catch {
        await fs.mkdir(GRAPHS_DIR, { recursive: true });
    }
}

// API Routes

// Get list of graph files
app.get('/api/graphs', async (req, res) => {
    try {
        await ensureGraphsDir();
        const files = await fs.readdir(GRAPHS_DIR);
        const jsonFiles = files.filter(f => f.endsWith('.json'));
        res.json(jsonFiles);
    } catch (error) {
        console.error('Error reading graphs directory:', error);
        res.status(500).json({ error: 'Failed to read graph files' });
    }
});

// Load specific graph file
app.get('/api/graphs/:filename', async (req, res) => {
    try {
        const filepath = path.join(GRAPHS_DIR, req.params.filename);
        const content = await fs.readFile(filepath, 'utf-8');
        res.json(JSON.parse(content));
    } catch (error) {
        // Try loading from .ai directory if not in graphs
        try {
            const content = await fs.readFile(AI_SPEC_GRAPH, 'utf-8');
            res.json(JSON.parse(content));
        } catch {
            console.error('Error loading graph:', error);
            res.status(404).json({ error: 'Graph file not found' });
        }
    }
});

// Save graph
app.post('/api/graphs/save', async (req, res) => {
    try {
        await ensureGraphsDir();

        // Extract filename from request body if provided, otherwise generate new one
        const { filename: providedFilename, ...graphData } = req.body;
        const filename = providedFilename || `graph-${Date.now()}.json`;
        const filepath = path.join(GRAPHS_DIR, filename);

        await fs.writeFile(filepath, JSON.stringify(graphData, null, 2));

        // Also update the main spec-graph.json if it exists
        await fs.writeFile(AI_SPEC_GRAPH, JSON.stringify(graphData, null, 2));

        res.json({ success: true, filename });
    } catch (error) {
        console.error('Error saving graph:', error);
        res.status(500).json({ error: 'Failed to save graph' });
    }
});

// AI Integration Endpoints

// Generate questions
app.post('/api/ai/generate-questions', async (req, res) => {
    try {
        const { context, existingQA } = req.body;

        // Check if API key is configured
        if (!process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_API_KEY === 'your_anthropic_api_key_here' || process.env.ANTHROPIC_API_KEY === 'your_api_key_here') {
            // Return mock questions if API key not configured
            const questions = [
                { number: 1, text: "What is the primary goal of this system?" },
                { number: 2, text: "Who are the main users of this application?" },
                { number: 3, text: "What key features are essential for the MVP?" },
                { number: 4, text: "What are the performance requirements?" },
                { number: 5, text: "How will users interact with the system?" }
            ];
            return res.json({ questions });
        }

        // Build prompt for question generation
        let prompt = `You are helping to generate insightful questions for a software project discovery session.

Context: ${context || 'No specific context provided'}

`;

        if (existingQA && existingQA.length > 0) {
            prompt += `Previous Q&A pairs:\n`;
            existingQA.forEach((qa, index) => {
                prompt += `Q${index + 1}: ${qa.question}\nA${index + 1}: ${qa.answer}\n\n`;
            });
        }

        prompt += `Generate 5-10 strategic questions that will help uncover important requirements, constraints, and decisions for this project. Each question should:
1. Be specific and actionable
2. Build on the context and previous answers
3. Help clarify technical, business, or user experience aspects
4. Avoid questions already answered in the previous Q&A

Return the response as a JSON object with a "questions" array containing objects with "number" and "text" fields.

Example format:
{
  "questions": [
    { "number": 1, "text": "What is the primary goal of this system?" },
    { "number": 2, "text": "Who are the main users of this application?" }
  ]
}`;

        const message = await anthropic.messages.create({
            model: 'claude-3-5-sonnet-20241022',
            max_tokens: 1000,
            messages: [{
                role: 'user',
                content: prompt
            }]
        });

        // Parse the response
        const responseText = message.content[0].text;
        let questionsData;

        try {
            // Try to extract JSON from the response
            const jsonMatch = responseText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                questionsData = JSON.parse(jsonMatch[0]);
            } else {
                throw new Error('No JSON found in response');
            }
        } catch (parseError) {
            console.warn('Failed to parse Claude response as JSON, using fallback');
            // Fallback: extract questions manually
            const lines = responseText.split('\n').filter(line => line.trim());
            const questions = [];
            let questionNumber = 1;

            for (const line of lines) {
                if (line.includes('?') && !line.includes('Example') && !line.includes('format')) {
                    const cleanText = line.replace(/^\d+\.\s*/, '').replace(/^-\s*/, '').trim();
                    if (cleanText.length > 10) {
                        questions.push({ number: questionNumber++, text: cleanText });
                    }
                }
            }

            questionsData = { questions: questions.slice(0, 10) };
        }

        res.json(questionsData);
    } catch (error) {
        console.error('Error generating questions:', error);

        // Fallback to mock questions on error
        const questions = [
            { number: 1, text: "What is the primary goal of this system?" },
            { number: 2, text: "Who are the main users of this application?" },
            { number: 3, text: "What key features are essential for the MVP?" },
            { number: 4, text: "What are the performance requirements?" },
            { number: 5, text: "How will users interact with the system?" }
        ];

        res.json({ questions });
    }
});

// Expand question with multiple choice and recommendations
app.post('/api/ai/expand-question', async (req, res) => {
    try {
        const { question, context, existingQA } = req.body;

        // Check if API key is configured
        if (!process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_API_KEY === 'your_anthropic_api_key_here' || process.env.ANTHROPIC_API_KEY === 'your_api_key_here') {
            // Fallback to contextual mock data based on question content
            const questionLower = question ? question.toLowerCase() : '';
            let expanded;

            if (questionLower.includes('deploy') || questionLower.includes('host') || questionLower.includes('infrastructure')) {
                expanded = {
                    choices: [
                        "Cloud-based solution with auto-scaling",
                        "On-premise deployment for data security",
                        "Hybrid approach with selective cloud services",
                        "Serverless architecture for cost optimization",
                        "Containerized microservices"
                    ],
                    recommendation: "Based on modern practices, a cloud-based solution with auto-scaling would provide the best balance of performance, cost, and maintainability.",
                    tradeoffs: "Cloud solutions offer scalability but may have higher long-term costs. On-premise provides more control but requires more maintenance.",
                    alternatives: "Consider using a Platform-as-a-Service (PaaS) solution to reduce operational overhead while maintaining flexibility.",
                    challenges: "Main challenges include data migration, security compliance, and ensuring minimal downtime during deployment."
                };
            } else if (questionLower.includes('database') || questionLower.includes('data') || questionLower.includes('storage')) {
                expanded = {
                    choices: [
                        "Relational database (PostgreSQL/MySQL)",
                        "NoSQL document store (MongoDB)",
                        "Time-series database (InfluxDB)",
                        "Graph database (Neo4j)",
                        "Multi-model database approach"
                    ],
                    recommendation: "For most applications, a relational database like PostgreSQL provides the best balance of features, performance, and ecosystem support.",
                    tradeoffs: "Relational databases offer ACID compliance but may be less flexible for unstructured data. NoSQL provides flexibility but may lack strong consistency.",
                    alternatives: "Consider starting with a single database and adding specialized stores as specific needs arise.",
                    challenges: "Key challenges include data modeling decisions, migration strategies, and ensuring proper backup and recovery procedures."
                };
            } else if (questionLower.includes('auth') || questionLower.includes('security') || questionLower.includes('login')) {
                expanded = {
                    choices: [
                        "OAuth 2.0 with third-party providers",
                        "JWT-based authentication system",
                        "Session-based authentication",
                        "Multi-factor authentication (MFA)",
                        "Single Sign-On (SSO) integration"
                    ],
                    recommendation: "Implement OAuth 2.0 with reputable providers (Google, GitHub) for user convenience while maintaining JWT tokens for API authentication.",
                    tradeoffs: "OAuth reduces development overhead but creates dependency on third parties. Custom auth provides control but requires security expertise.",
                    alternatives: "Consider passwordless authentication using magic links or WebAuthn for improved user experience.",
                    challenges: "Main challenges include secure token storage, handling token refresh, and implementing proper session management."
                };
            } else {
                // Generic fallback
                expanded = {
                    choices: [
                        "Industry standard approach",
                        "Custom solution tailored to needs",
                        "Open-source framework integration",
                        "Third-party service integration",
                        "Hybrid approach combining multiple options"
                    ],
                    recommendation: "Start with industry standards and well-established patterns, then customize based on specific requirements.",
                    tradeoffs: "Standard approaches offer reliability but may lack specific features. Custom solutions provide flexibility but require more development time.",
                    alternatives: "Evaluate existing solutions thoroughly before building custom implementations.",
                    challenges: "Balance between time-to-market, maintenance overhead, and feature requirements."
                };
            }

            return res.json(expanded);
        }

        // Build comprehensive prompt for intelligent question expansion
        let prompt = `You are an expert software architect and product strategist helping to expand a discovery question with intelligent multiple-choice options and analysis.

QUESTION TO EXPAND:
"${question}"

PROJECT CONTEXT:
${context ? `Project Context: ${context}` : 'No specific project context provided'}

EXISTING Q&A CONTEXT:
${existingQA && existingQA.length > 0
    ? existingQA.map((qa, index) => `Q${index + 1}: ${qa.question}\nA${index + 1}: ${qa.answer}`).join('\n\n')
    : 'No previous Q&A available'
}

YOUR TASK:
Generate 4-6 strategic multiple-choice options that represent different approaches to answering this question. Then provide expert analysis covering:

1. CHOICES: Specific, actionable options that represent different strategic approaches
2. RECOMMENDATION: Your expert recommendation based on modern best practices
3. TRADEOFFS: Honest analysis of the pros and cons of different approaches
4. ALTERNATIVES: Additional approaches or variations to consider
5. CHALLENGES: Potential obstacles, risks, or implementation difficulties

GUIDELINES:
- Make choices specific and actionable, not generic
- Base recommendations on industry best practices and current technology trends
- Include realistic tradeoffs that acknowledge both benefits and drawbacks
- Suggest practical alternatives that might work better in certain contexts
- Identify real challenges teams typically face with each approach
- Consider the existing project context and previous answers
- Focus on strategic decisions rather than implementation details

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{
  "choices": [
    "Specific choice option 1",
    "Specific choice option 2",
    "Specific choice option 3",
    "Specific choice option 4",
    "Specific choice option 5"
  ],
  "recommendation": "Clear recommendation with reasoning based on best practices",
  "tradeoffs": "Honest analysis of key tradeoffs between the main approaches",
  "alternatives": "Additional approaches or variations worth considering",
  "challenges": "Realistic challenges and potential obstacles to implementation"
}`;

        const message = await anthropic.messages.create({
            model: 'claude-3-5-sonnet-20241022',
            max_tokens: 1200,
            messages: [{
                role: 'user',
                content: prompt
            }]
        });

        // Parse the response
        const responseText = message.content[0].text;
        let expandedData;

        try {
            // Try to extract JSON from the response
            const jsonMatch = responseText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                expandedData = JSON.parse(jsonMatch[0]);
            } else {
                throw new Error('No JSON found in response');
            }

            // Validate and ensure required fields exist
            expandedData.choices = expandedData.choices || [];
            expandedData.recommendation = expandedData.recommendation || '';
            expandedData.tradeoffs = expandedData.tradeoffs || '';
            expandedData.alternatives = expandedData.alternatives || '';
            expandedData.challenges = expandedData.challenges || '';

            // Ensure choices is an array and limit to reasonable number
            if (Array.isArray(expandedData.choices)) {
                expandedData.choices = expandedData.choices.slice(0, 8); // Max 8 choices
            } else {
                expandedData.choices = [];
            }

        } catch (parseError) {
            console.warn('Failed to parse Claude response as JSON, using fallback extraction');

            // Fallback: try to extract structured information from the response
            expandedData = {
                choices: [],
                recommendation: '',
                tradeoffs: '',
                alternatives: '',
                challenges: ''
            };

            const lines = responseText.split('\n');
            let currentSection = null;
            let sectionContent = [];

            for (const line of lines) {
                const trimmedLine = line.trim();

                if (trimmedLine.toLowerCase().includes('choices') || trimmedLine.toLowerCase().includes('options')) {
                    if (currentSection && sectionContent.length > 0) {
                        expandedData[currentSection] = sectionContent.join(' ').trim();
                    }
                    currentSection = 'choices';
                    sectionContent = [];
                } else if (trimmedLine.toLowerCase().includes('recommendation')) {
                    if (currentSection && sectionContent.length > 0) {
                        if (currentSection === 'choices') {
                            expandedData.choices = sectionContent.filter(c => c.trim().length > 0);
                        } else {
                            expandedData[currentSection] = sectionContent.join(' ').trim();
                        }
                    }
                    currentSection = 'recommendation';
                    sectionContent = [];
                } else if (trimmedLine.toLowerCase().includes('tradeoffs') || trimmedLine.toLowerCase().includes('trade-offs')) {
                    if (currentSection && sectionContent.length > 0) {
                        if (currentSection === 'choices') {
                            expandedData.choices = sectionContent.filter(c => c.trim().length > 0);
                        } else {
                            expandedData[currentSection] = sectionContent.join(' ').trim();
                        }
                    }
                    currentSection = 'tradeoffs';
                    sectionContent = [];
                } else if (trimmedLine.toLowerCase().includes('alternatives')) {
                    if (currentSection && sectionContent.length > 0) {
                        if (currentSection === 'choices') {
                            expandedData.choices = sectionContent.filter(c => c.trim().length > 0);
                        } else {
                            expandedData[currentSection] = sectionContent.join(' ').trim();
                        }
                    }
                    currentSection = 'alternatives';
                    sectionContent = [];
                } else if (trimmedLine.toLowerCase().includes('challenges')) {
                    if (currentSection && sectionContent.length > 0) {
                        if (currentSection === 'choices') {
                            expandedData.choices = sectionContent.filter(c => c.trim().length > 0);
                        } else {
                            expandedData[currentSection] = sectionContent.join(' ').trim();
                        }
                    }
                    currentSection = 'challenges';
                    sectionContent = [];
                } else if (trimmedLine.length > 0 && currentSection) {
                    // Clean the line and add to current section
                    const cleanLine = trimmedLine.replace(/^\d+\.\s*/, '').replace(/^-\s*/, '').replace(/^\*\s*/, '');
                    if (cleanLine.length > 0) {
                        sectionContent.push(cleanLine);
                    }
                }
            }

            // Handle the last section
            if (currentSection && sectionContent.length > 0) {
                if (currentSection === 'choices') {
                    expandedData.choices = sectionContent.filter(c => c.trim().length > 0);
                } else {
                    expandedData[currentSection] = sectionContent.join(' ').trim();
                }
            }

            // If we still don't have good data, provide a basic fallback
            if (expandedData.choices.length === 0) {
                expandedData.choices = [
                    "Standard industry approach",
                    "Custom solution",
                    "Third-party integration",
                    "Hybrid approach"
                ];
            }
        }

        res.json(expandedData);
    } catch (error) {
        console.error('Error expanding question:', error);

        // Final fallback
        const fallbackExpanded = {
            choices: [
                "Industry standard approach",
                "Custom solution tailored to needs",
                "Third-party service integration",
                "Hybrid approach combining options"
            ],
            recommendation: "Evaluate standard approaches first, then customize based on specific requirements.",
            tradeoffs: "Standard solutions offer reliability but may lack specific features. Custom solutions provide flexibility but require more development time.",
            alternatives: "Consider phased implementation starting with proven solutions.",
            challenges: "Balance between time-to-market, maintenance overhead, and feature requirements."
        };

        res.json(fallbackExpanded);
    }
});

// Extract entities and references from text
app.post('/api/ai/extract-entities', async (req, res) => {
    try {
        const { text, graph } = req.body;

        // Check if API key is configured
        if (!process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_API_KEY === 'your_anthropic_api_key_here' || process.env.ANTHROPIC_API_KEY === 'your_api_key_here') {
            // Fallback to simple keyword detection
            const extracted = { entities: [], references: [], connections: [] };
            const keywords = text.toLowerCase();

            if (keywords.includes('user') || keywords.includes('admin') || keywords.includes('customer')) {
                extracted.entities.push({
                    type: 'users',
                    name: 'primary-user',
                    description: 'Main system user'
                });
            }

            if (keywords.includes('dashboard') || keywords.includes('interface') || keywords.includes('screen')) {
                extracted.entities.push({
                    type: 'interfaces',
                    name: 'main-dashboard',
                    description: 'Primary user interface'
                });
            }

            if (keywords.includes('data') || keywords.includes('database') || keywords.includes('storage')) {
                extracted.entities.push({
                    type: 'data-models',
                    name: 'core-data-model',
                    description: 'Primary data structure'
                });
            }

            if (keywords.includes('api') || keywords.includes('endpoint')) {
                extracted.references.push({
                    key: 'api_base_url',
                    value: '/api/v1'
                });
            }

            if (extracted.entities.length > 1) {
                extracted.connections.push({
                    from: extracted.entities[0].name,
                    to: extracted.entities[1].name
                });
            }

            return res.json(extracted);
        }

        // Build comprehensive prompt for entity extraction
        let prompt = `You are an expert system architect analyzing user responses to extract structured entities and references for a software project graph.

ENTITY TYPES AND DESCRIPTIONS:
- project: Top-level container representing the entire software project
- requirements: Functional or non-functional specifications the system must satisfy
- interfaces: User interface screens and pages in the application
- features: Distinct functionality or capability provided to users
- actions: Specific user interactions or system operations
- components: Reusable building blocks of the system architecture
- presentation: Visual and layout aspects of user interface components
- behavior: Logic and state management for component interactions
- data_models: Structure and schema definitions for data entities
- users: Actors or roles that interact with the system
- objectives: High-level goals or outcomes that users want to achieve

REFERENCE CATEGORIES:
- technical_architecture: Infrastructure components and system architecture
- endpoints: API endpoint definitions
- libraries: Code libraries and frameworks
- protocols: Communication protocols
- platforms: Platform specifications (cloud, mobile, web)
- business_logic: Detailed workflows and rules
- acceptance_criteria: Success criteria for features
- content: User-facing text, branding, taglines
- labels: Specific text labels for UI elements
- styles: CSS styles and visual specifications
- configuration: Feature toggles, environment configs
- metrics: Analytics events and KPIs
- examples: Sample inputs/outputs and test scenarios
- constraints: Business rules and system invariants
- terminology: Domain-specific terms and naming conventions

DEPENDENCY RULES:
- project → [requirements, users]
- requirements → [interfaces]
- interfaces → [features]
- features → [actions]
- actions → [components]
- components → [presentation, behavior, data_models, assets]
- users → [objectives, requirements]
- objectives → [actions, features]

USER RESPONSE TO ANALYZE:
"${text}"

EXISTING GRAPH CONTEXT:
${graph ? JSON.stringify(graph, null, 2) : 'No existing graph provided'}

ANALYSIS INSTRUCTIONS:
1. Extract meaningful entities mentioned or implied in the user response
2. Use kebab-case naming (e.g., "user-dashboard", "api-gateway")
3. Create concise but descriptive entity descriptions
4. Identify key-value references that would be useful for implementation
5. Suggest logical connections between entities based on dependency rules
6. Avoid duplicating entities that already exist in the graph
7. Focus on extracting 2-5 high-quality entities rather than many low-quality ones

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{
  "entities": [
    {
      "type": "entity_type",
      "name": "kebab-case-name",
      "description": "Clear description of what this entity represents"
    }
  ],
  "references": [
    {
      "category": "reference_category",
      "key": "kebab-case-key",
      "value": "actual value or specification"
    }
  ],
  "connections": [
    {
      "from": "source-entity-name",
      "to": "target-entity-name",
      "reason": "Brief explanation of the relationship"
    }
  ]
}`;

        const message = await anthropic.messages.create({
            model: 'claude-3-5-sonnet-20241022',
            max_tokens: 1500,
            messages: [{
                role: 'user',
                content: prompt
            }]
        });

        // Parse the response
        const responseText = message.content[0].text;
        let extractedData;

        try {
            // Try to extract JSON from the response
            const jsonMatch = responseText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                extractedData = JSON.parse(jsonMatch[0]);
            } else {
                throw new Error('No JSON found in response');
            }

            // Validate and clean the response structure
            extractedData.entities = extractedData.entities || [];
            extractedData.references = extractedData.references || [];
            extractedData.connections = extractedData.connections || [];

            // Clean entity names to ensure kebab-case
            extractedData.entities = extractedData.entities.map(entity => ({
                ...entity,
                name: entity.name ? entity.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : 'unnamed-entity'
            }));

            // Clean reference keys to ensure kebab-case
            extractedData.references = extractedData.references.map(ref => ({
                ...ref,
                key: ref.key ? ref.key.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : 'unnamed-key'
            }));

        } catch (parseError) {
            console.warn('Failed to parse Claude response as JSON, using fallback extraction');

            // Fallback: try to extract entities manually from the response
            extractedData = { entities: [], references: [], connections: [] };

            const lines = responseText.split('\n');
            let currentSection = null;

            for (const line of lines) {
                const trimmedLine = line.trim();

                if (trimmedLine.includes('entities') || trimmedLine.includes('ENTITIES')) {
                    currentSection = 'entities';
                } else if (trimmedLine.includes('references') || trimmedLine.includes('REFERENCES')) {
                    currentSection = 'references';
                } else if (trimmedLine.includes('connections') || trimmedLine.includes('CONNECTIONS')) {
                    currentSection = 'connections';
                } else if (currentSection === 'entities' && trimmedLine.includes(':')) {
                    // Try to extract entity information
                    const parts = trimmedLine.split(':');
                    if (parts.length >= 2) {
                        const name = parts[0].replace(/[^a-z0-9]+/gi, '-').toLowerCase().replace(/^-+|-+$/g, '');
                        const description = parts.slice(1).join(':').trim();
                        if (name && description) {
                            extractedData.entities.push({
                                type: 'features', // default type
                                name: name,
                                description: description
                            });
                        }
                    }
                }
            }
        }

        res.json(extractedData);
    } catch (error) {
        console.error('Error extracting entities:', error);

        // Final fallback to simple extraction
        const fallbackExtracted = { entities: [], references: [], connections: [] };
        const keywords = text.toLowerCase();

        if (keywords.includes('user') || keywords.includes('admin') || keywords.includes('customer')) {
            fallbackExtracted.entities.push({
                type: 'users',
                name: 'primary-user',
                description: 'Main system user'
            });
        }

        if (keywords.includes('dashboard') || keywords.includes('interface') || keywords.includes('screen')) {
            fallbackExtracted.entities.push({
                type: 'interfaces',
                name: 'main-dashboard',
                description: 'Primary user interface'
            });
        }

        res.json(fallbackExtracted);
    }
});

// Handle AI commands from the AI bar
app.post('/api/ai/command', async (req, res) => {
    try {
        const { command, graph } = req.body;

        // Parse command for simple operations
        const lowerCommand = command.toLowerCase();

        let graphUpdates = null;
        let message = '';

        // Simple command parsing
        if (lowerCommand.includes('add user')) {
            if (!graph.entities.users) graph.entities.users = {};
            const userName = command.match(/add user (\w+)/i)?.[1] || 'new-user';
            graph.entities.users[userName] = { description: 'Added via AI command' };
            graphUpdates = graph;
            message = `Added user: ${userName}`;
        } else if (lowerCommand.includes('add feature')) {
            if (!graph.entities.features) graph.entities.features = {};
            const featureName = command.match(/add feature (\w+)/i)?.[1] || 'new-feature';
            graph.entities.features[featureName] = { description: 'Added via AI command' };
            graphUpdates = graph;
            message = `Added feature: ${featureName}`;
        } else {
            message = 'Command processed. Use "add user [name]" or "add feature [name]" to modify the graph.';
        }

        res.json({ graphUpdates, message });
    } catch (error) {
        console.error('Error processing AI command:', error);
        res.status(500).json({ error: 'Failed to process command' });
    }
});

// Know tool integration
app.post('/api/know/generate', async (req, res) => {
    try {
        const { type, entity } = req.body;

        // Execute know tool command
        const command = `${KNOW_TOOL} generate ${type} ${entity}`;
        const { stdout, stderr } = await execPromise(command);

        if (stderr) {
            console.error('Know tool error:', stderr);
        }

        res.json({ output: stdout, error: stderr });
    } catch (error) {
        console.error('Error executing know tool:', error);
        res.status(500).json({ error: 'Failed to execute know tool' });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    ensureGraphsDir();
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM signal received: closing HTTP server');
    app.close(() => {
        console.log('HTTP server closed');
    });
});