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

        // Check if API key is configured
        if (!process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_API_KEY === 'your_anthropic_api_key_here' || process.env.ANTHROPIC_API_KEY === 'your_api_key_here') {
            // Enhanced fallback with better pattern matching
            const lowerCommand = command.toLowerCase();
            let graphUpdates = null;
            let message = '';

            // Make a copy of the graph to modify
            const updatedGraph = JSON.parse(JSON.stringify(graph || { entities: {}, references: {}, graph: [] }));

            // Initialize entities if needed
            if (!updatedGraph.entities) updatedGraph.entities = {};
            if (!updatedGraph.references) updatedGraph.references = {};
            if (!updatedGraph.graph) updatedGraph.graph = [];

            // Parse various command patterns
            if (lowerCommand.includes('add') || lowerCommand.includes('create')) {
                // Extract entity type and name
                let entityType = null;
                let entityName = null;
                let description = '';

                // Check for different entity types
                const entityTypes = ['user', 'feature', 'interface', 'component', 'requirement', 'action', 'objective', 'data-model', 'behavior', 'presentation'];
                for (const type of entityTypes) {
                    if (lowerCommand.includes(type)) {
                        entityType = type + 's'; // pluralize
                        if (type === 'interface') entityType = 'interfaces';
                        if (type === 'data-model') entityType = 'data-models';

                        // Try to extract name from command
                        const patterns = [
                            new RegExp(`add (?:a |an )?${type}\\s+(?:called |named |for )?([\\w-]+)`, 'i'),
                            new RegExp(`create (?:a |an )?${type}\\s+(?:called |named |for )?([\\w-]+)`, 'i'),
                            new RegExp(`add ([\\w-]+)\\s+${type}`, 'i'),
                            new RegExp(`create ([\\w-]+)\\s+${type}`, 'i')
                        ];

                        for (const pattern of patterns) {
                            const match = command.match(pattern);
                            if (match) {
                                entityName = match[1].toLowerCase().replace(/[^a-z0-9]+/g, '-');
                                break;
                            }
                        }

                        // Extract description if present
                        const descMatch = command.match(/(?:for|to|that)\s+(.+?)(?:\.|$)/i);
                        if (descMatch) {
                            description = descMatch[1].trim();
                        } else {
                            description = `${type.charAt(0).toUpperCase() + type.slice(1)} added via command`;
                        }

                        break;
                    }
                }

                if (entityType && entityName) {
                    if (!updatedGraph.entities[entityType]) updatedGraph.entities[entityType] = {};
                    updatedGraph.entities[entityType][entityName] = { description };
                    graphUpdates = updatedGraph;
                    message = `Added ${entityType.slice(0, -1)}: ${entityName}`;
                } else if (entityType) {
                    // Default name if couldn't extract
                    entityName = `new-${entityType.slice(0, -1)}-${Date.now() % 1000}`;
                    if (!updatedGraph.entities[entityType]) updatedGraph.entities[entityType] = {};
                    updatedGraph.entities[entityType][entityName] = { description: description || 'Added via command' };
                    graphUpdates = updatedGraph;
                    message = `Added ${entityType.slice(0, -1)}: ${entityName}`;
                }
            } else if (lowerCommand.includes('remove') || lowerCommand.includes('delete')) {
                // Handle removal
                const entityTypes = Object.keys(updatedGraph.entities);
                let removed = false;

                for (const entityType of entityTypes) {
                    const entities = Object.keys(updatedGraph.entities[entityType] || {});
                    for (const entityName of entities) {
                        if (lowerCommand.includes(entityName)) {
                            delete updatedGraph.entities[entityType][entityName];

                            // Remove from graph connections
                            updatedGraph.graph = updatedGraph.graph.filter(
                                conn => conn.from !== `${entityType}:${entityName}` &&
                                       conn.to !== `${entityType}:${entityName}`
                            );

                            graphUpdates = updatedGraph;
                            message = `Removed ${entityType.slice(0, -1)}: ${entityName}`;
                            removed = true;
                            break;
                        }
                    }
                    if (removed) break;
                }

                if (!removed) {
                    message = 'Could not find entity to remove. Please specify an existing entity name.';
                }
            } else if (lowerCommand.includes('connect') || lowerCommand.includes('link')) {
                // Handle connections
                const words = command.toLowerCase().split(/\s+/);
                let fromEntity = null;
                let toEntity = null;

                // Find entities in the command
                for (const entityType of Object.keys(updatedGraph.entities)) {
                    for (const entityName of Object.keys(updatedGraph.entities[entityType])) {
                        if (words.includes(entityName)) {
                            if (!fromEntity) {
                                fromEntity = `${entityType}:${entityName}`;
                            } else if (!toEntity) {
                                toEntity = `${entityType}:${entityName}`;
                            }
                        }
                    }
                }

                if (fromEntity && toEntity) {
                    updatedGraph.graph.push({ from: fromEntity, to: toEntity });
                    graphUpdates = updatedGraph;
                    message = `Connected ${fromEntity} to ${toEntity}`;
                } else {
                    message = 'Could not identify entities to connect. Please specify two existing entities.';
                }
            } else {
                message = 'Command not understood. Try: "add feature user-auth", "remove unused-component", "connect user-dashboard to api-gateway"';
            }

            return res.json({ graphUpdates, message });
        }

        // Build comprehensive prompt for intelligent command parsing
        const prompt = `You are an expert at understanding natural language commands for modifying a software project graph structure.

ENTITY TYPES (use exact type names):
- project: Top-level container
- requirements: Functional/non-functional specifications
- interfaces: UI screens and pages
- features: Distinct functionality
- actions: User interactions or operations
- components: Reusable building blocks
- presentation: Visual UI aspects
- behavior: Logic and state management
- data-models: Data structures and schemas
- users: System actors and roles
- objectives: High-level goals

CURRENT GRAPH STRUCTURE:
${JSON.stringify(graph, null, 2)}

USER COMMAND:
"${command}"

ANALYSIS INSTRUCTIONS:
1. Parse the natural language command to understand the intended operation
2. Identify the operation type: add, remove, modify, connect, disconnect
3. Extract entity types and names (use kebab-case for names)
4. Generate appropriate descriptions for new entities
5. Validate operations against the dependency rules
6. Handle bulk operations if multiple entities are mentioned
7. For connections, ensure both entities exist or create them if needed

DEPENDENCY RULES:
- project → [requirements, users]
- requirements → [interfaces]
- interfaces → [features]
- features → [actions]
- actions → [components]
- components → [presentation, behavior, data-models]
- users → [objectives, requirements]
- objectives → [actions, features]

OPERATIONS TO SUPPORT:
- Add/Create: "add a user authentication feature", "create admin dashboard interface"
- Remove/Delete: "remove unused components", "delete old-api feature"
- Connect/Link: "connect user-dashboard to api-gateway", "link authentication to user-management"
- Modify/Update: "rename user-dashboard to admin-panel", "update description of auth-feature"
- Bulk: "add features: login, logout, and password-reset"

RESPONSE FORMAT:
Return a JSON object with this structure:
{
  "operations": [
    {
      "type": "add|remove|modify|connect",
      "entityType": "entity type name",
      "entityName": "kebab-case-name",
      "description": "entity description (for add)",
      "from": "source entity (for connect)",
      "to": "target entity (for connect)",
      "oldName": "old name (for modify)",
      "newName": "new name (for modify)"
    }
  ],
  "summary": "Clear explanation of what was done"
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
        let commandData;

        try {
            // Try to extract JSON from the response
            const jsonMatch = responseText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                commandData = JSON.parse(jsonMatch[0]);
            } else {
                throw new Error('No JSON found in response');
            }
        } catch (parseError) {
            console.warn('Failed to parse Claude response as JSON, using fallback');
            // Fallback to simple command parsing
            return res.json({
                graphUpdates: null,
                message: 'Could not parse command. Try simpler commands like "add feature user-auth" or "connect user to dashboard".'
            });
        }

        // Apply the operations to the graph
        let updatedGraph = JSON.parse(JSON.stringify(graph || { entities: {}, references: {}, graph: [] }));

        // Initialize structures if needed
        if (!updatedGraph.entities) updatedGraph.entities = {};
        if (!updatedGraph.references) updatedGraph.references = {};
        if (!updatedGraph.graph) updatedGraph.graph = [];

        let operationMessages = [];

        for (const operation of (commandData.operations || [])) {
            switch (operation.type) {
                case 'add':
                case 'create':
                    if (operation.entityType && operation.entityName) {
                        // Ensure entity type exists (pluralize if needed)
                        let entityType = operation.entityType;
                        if (!entityType.endsWith('s')) {
                            if (entityType === 'interface') {
                                entityType = 'interfaces';
                            } else if (entityType === 'data-model') {
                                entityType = 'data-models';
                            } else {
                                entityType += 's';
                            }
                        }

                        if (!updatedGraph.entities[entityType]) {
                            updatedGraph.entities[entityType] = {};
                        }

                        updatedGraph.entities[entityType][operation.entityName] = {
                            description: operation.description || `${operation.entityType} created via command`
                        };

                        operationMessages.push(`Added ${operation.entityType}: ${operation.entityName}`);
                    }
                    break;

                case 'remove':
                case 'delete':
                    if (operation.entityType && operation.entityName) {
                        let entityType = operation.entityType;
                        if (!entityType.endsWith('s')) {
                            if (entityType === 'interface') {
                                entityType = 'interfaces';
                            } else if (entityType === 'data-model') {
                                entityType = 'data-models';
                            } else {
                                entityType += 's';
                            }
                        }

                        if (updatedGraph.entities[entityType] && updatedGraph.entities[entityType][operation.entityName]) {
                            delete updatedGraph.entities[entityType][operation.entityName];

                            // Remove related connections
                            const entityRef = `${entityType}:${operation.entityName}`;
                            updatedGraph.graph = updatedGraph.graph.filter(
                                conn => conn.from !== entityRef && conn.to !== entityRef
                            );

                            operationMessages.push(`Removed ${operation.entityType}: ${operation.entityName}`);
                        }
                    }
                    break;

                case 'connect':
                case 'link':
                    if (operation.from && operation.to) {
                        // Check if connection already exists
                        const exists = updatedGraph.graph.some(
                            conn => conn.from === operation.from && conn.to === operation.to
                        );

                        if (!exists) {
                            updatedGraph.graph.push({
                                from: operation.from,
                                to: operation.to
                            });
                            operationMessages.push(`Connected ${operation.from} to ${operation.to}`);
                        } else {
                            operationMessages.push(`Connection already exists: ${operation.from} to ${operation.to}`);
                        }
                    }
                    break;

                case 'modify':
                case 'update':
                case 'rename':
                    if (operation.entityType && operation.oldName && operation.newName) {
                        let entityType = operation.entityType;
                        if (!entityType.endsWith('s')) {
                            if (entityType === 'interface') {
                                entityType = 'interfaces';
                            } else if (entityType === 'data-model') {
                                entityType = 'data-models';
                            } else {
                                entityType += 's';
                            }
                        }

                        if (updatedGraph.entities[entityType] && updatedGraph.entities[entityType][operation.oldName]) {
                            // Copy the entity with new name
                            updatedGraph.entities[entityType][operation.newName] = updatedGraph.entities[entityType][operation.oldName];

                            // Update description if provided
                            if (operation.description) {
                                updatedGraph.entities[entityType][operation.newName].description = operation.description;
                            }

                            // Delete old entity
                            delete updatedGraph.entities[entityType][operation.oldName];

                            // Update connections
                            const oldRef = `${entityType}:${operation.oldName}`;
                            const newRef = `${entityType}:${operation.newName}`;

                            updatedGraph.graph = updatedGraph.graph.map(conn => {
                                if (conn.from === oldRef) conn.from = newRef;
                                if (conn.to === oldRef) conn.to = newRef;
                                return conn;
                            });

                            operationMessages.push(`Renamed ${operation.oldName} to ${operation.newName}`);
                        }
                    }
                    break;
            }
        }

        // Prepare response
        const finalMessage = commandData.summary || operationMessages.join('. ') || 'Command processed but no changes made.';

        res.json({
            graphUpdates: operationMessages.length > 0 ? updatedGraph : null,
            message: finalMessage
        });

    } catch (error) {
        console.error('Error processing AI command:', error);

        // Final fallback
        res.json({
            graphUpdates: null,
            message: 'Failed to process command. Try simpler commands like "add feature authentication" or "connect user to dashboard".'
        });
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