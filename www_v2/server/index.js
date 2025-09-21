const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const logger = require('./logger');
const PromptLoader = require('../prompts/loader');

const app = express();
const PORT = 8880;

// Initialize Anthropic client
const anthropic = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY
});

// Initialize prompt loader
const promptLoader = new PromptLoader(path.join(__dirname, '../prompts'));

// Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, '../public')));

// Request logging middleware
app.use((req, res, next) => {
    const start = Date.now();

    // Log request
    logger.log(`${req.method} ${req.path}`);

    // Log response when finished
    res.on('finish', () => {
        const duration = Date.now() - start;
        logger.log(`${req.method} ${req.path} - ${res.statusCode} (${duration}ms)`);
    });

    next();
});

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

// Structured AI call with validation
async function makeStructuredAICall(promptName, variables, schemaName, maxTokens = 1000) {
    try {
        // Format the prompt with variables
        const prompt = await promptLoader.formatPrompt(promptName, variables);

        // Call Claude
        const message = await anthropic.messages.create({
            model: 'claude-3-5-sonnet-20241022',
            max_tokens: maxTokens,
            messages: [{
                role: 'user',
                content: prompt
            }]
        });

        // Parse the response
        const responseText = message.content[0].text;
        let responseData;

        try {
            // Try to extract JSON from the response
            const jsonMatch = responseText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                responseData = JSON.parse(jsonMatch[0]);
            } else {
                throw new Error('No JSON found in response');
            }
        } catch (parseError) {
            logger.warn(`Failed to parse AI response for ${promptName}:`, parseError.message);
            throw new Error('Invalid JSON response from AI');
        }

        // Validate and clean the response
        const validation = promptLoader.validateAndClean(schemaName, responseData);

        if (!validation.isValid) {
            logger.warn(`Schema validation failed for ${promptName}:`, validation.errors);
            // For now, we'll log but continue with cleaned data
            // In production, you might want to retry or use fallbacks
        }

        return validation.data;

    } catch (error) {
        logger.error(`Error in structured AI call for ${promptName}:`, error);
        throw error;
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
        logger.error('Error reading graphs directory:', error);
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
            logger.error('Error loading graph:', error);
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
        logger.error('Error saving graph:', error);
        res.status(500).json({ error: 'Failed to save graph' });
    }
});

// AI Integration Endpoints

// Generate questions
app.post('/api/ai/generate-questions', async (req, res) => {
    try {
        const { context, existingQA, currentGraph } = req.body;

        // Check if API key is configured
        if (!process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_API_KEY === 'your_anthropic_api_key_here' || process.env.ANTHROPIC_API_KEY === 'your_api_key_here') {
            // Enhanced context-aware fallback questions
            const qaCount = existingQA ? existingQA.length : 0;
            let questions = [];

            if (qaCount === 0) {
                // Initial discovery questions
                questions = [
                    { number: 1, text: "What is the primary goal of this system?" },
                    { number: 2, text: "Who are the main users of this application?" },
                    { number: 3, text: "What problem does this system solve?" },
                    { number: 4, text: "What are the key success metrics?" },
                    { number: 5, text: "What is the expected timeline for the MVP?" }
                ];
            } else if (qaCount < 5) {
                // Early exploration questions
                questions = [
                    { number: 1, text: "What key features are essential for the MVP?" },
                    { number: 2, text: "What are the main technical constraints?" },
                    { number: 3, text: "How will users interact with the system?" },
                    { number: 4, text: "What data needs to be captured and stored?" },
                    { number: 5, text: "What are the performance requirements?" }
                ];
            } else if (qaCount < 10) {
                // Mid-stage refinement questions
                questions = [
                    { number: 1, text: "What security requirements must be met?" },
                    { number: 2, text: "How should the system handle errors and edge cases?" },
                    { number: 3, text: "What third-party integrations are required?" },
                    { number: 4, text: "What are the scalability expectations?" },
                    { number: 5, text: "How will the system be deployed and maintained?" }
                ];
            } else {
                // Deep-dive specific questions
                questions = [
                    { number: 1, text: "What are the specific acceptance criteria for the core features?" },
                    { number: 2, text: "How should the system handle concurrent users?" },
                    { number: 3, text: "What monitoring and analytics are needed?" },
                    { number: 4, text: "What are the disaster recovery requirements?" },
                    { number: 5, text: "What compliance or regulatory requirements apply?" }
                ];
            }

            return res.json({ questions });
        }

        // Use structured AI call with validation
        const questionsData = await makeStructuredAICall(
            'generate-questions',
            {
                context: context || 'No initial context provided',
                existingQA: promptLoader.formatQAHistory(existingQA),
                currentGraph: currentGraph ? `Entities discovered: ${Object.keys(currentGraph.entities || {}).join(', ') || 'None yet'}` : 'No graph structure yet'
            },
            'generateQuestions',
            1000
        );

        // Log rationale for debugging but don't send to client
        if (questionsData.rationale) {
            logger.debug('Question generation rationale:', questionsData.rationale);
        }

        // Return only questions to maintain API compatibility
        res.json({ questions: questionsData.questions });
    } catch (error) {
        logger.error('Error generating questions:', error);

        // Context-aware fallback on error
        const qaCount = existingQA ? existingQA.length : 0;
        let questions = [];

        if (qaCount === 0) {
            // Initial discovery questions
            questions = [
                { number: 1, text: "What is the primary goal of this system?" },
                { number: 2, text: "Who are the main users of this application?" },
                { number: 3, text: "What problem does this system solve?" },
                { number: 4, text: "What are the key success metrics?" },
                { number: 5, text: "What is the expected timeline?" }
            ];
        } else if (qaCount < 5) {
            // Early exploration questions
            questions = [
                { number: 1, text: "What key features are essential for the MVP?" },
                { number: 2, text: "What are the technical constraints?" },
                { number: 3, text: "How will users interact with the system?" },
                { number: 4, text: "What data needs to be stored?" },
                { number: 5, text: "What are the performance requirements?" }
            ];
        } else {
            // Deeper exploration questions
            questions = [
                { number: 1, text: "What security requirements must be met?" },
                { number: 2, text: "How should the system handle errors?" },
                { number: 3, text: "What integrations are required?" },
                { number: 4, text: "What are the scalability expectations?" },
                { number: 5, text: "How will the system be deployed?" }
            ];
        }

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

        // Use structured AI call with validation
        const expandedData = await makeStructuredAICall(
            'expand-question',
            {
                question: question,
                context: context ? `Project Context: ${context}` : 'No specific project context provided',
                existingQA: promptLoader.formatQAHistory(existingQA)
            },
            'expandQuestion',
            1200
        );

        res.json(expandedData);
    } catch (error) {
        logger.error('Error expanding question:', error);

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
                    description: 'Main system user',
                    reasoning: 'User entity detected based on mention of user roles. This will serve as the primary actor in the system, essential for defining permissions and access patterns.'
                });
            }

            if (keywords.includes('dashboard') || keywords.includes('interface') || keywords.includes('screen')) {
                extracted.entities.push({
                    type: 'interfaces',
                    name: 'main-dashboard',
                    description: 'Primary user interface',
                    reasoning: 'Interface component identified from UI terminology. Dashboards typically serve as central navigation hubs and should connect to multiple features and data sources.'
                });
            }

            if (keywords.includes('data') || keywords.includes('database') || keywords.includes('storage')) {
                extracted.entities.push({
                    type: 'data-models',
                    name: 'core-data-model',
                    description: 'Primary data structure',
                    reasoning: 'Data model detected from storage-related keywords. Establishing data models early helps define the information architecture and API contracts.'
                });
            }

            if (keywords.includes('api') || keywords.includes('endpoint')) {
                extracted.references.push({
                    key: 'api_base_url',
                    value: '/api/v1',
                    reasoning: 'API endpoint pattern detected. Standardizing API base URLs early ensures consistent routing and versioning across the application.'
                });
            }

            if (extracted.entities.length > 1) {
                extracted.connections.push({
                    from: extracted.entities[0].name,
                    to: extracted.entities[1].name,
                    reasoning: `Connecting ${extracted.entities[0].name} to ${extracted.entities[1].name} establishes the primary interaction flow. This relationship is fundamental for understanding system architecture.`
                });
            }

            return res.json(extracted);
        }

        // Build comprehensive prompt for entity extraction
        const prompt = await promptLoader.formatPrompt('extract-entities', {
            text: text,
            graph: graph ? JSON.stringify(graph, null, 2) : 'No existing graph provided'
        });

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
            logger.warn('Failed to parse Claude response as JSON, using fallback extraction');

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
        logger.error('Error extracting entities:', error);

        // Final fallback to simple extraction
        const fallbackExtracted = { entities: [], references: [], connections: [] };
        const keywords = text.toLowerCase();

        if (keywords.includes('user') || keywords.includes('admin') || keywords.includes('customer')) {
            fallbackExtracted.entities.push({
                type: 'users',
                name: 'primary-user',
                description: 'Main system user',
                reasoning: 'User entity detected based on role keywords. Users are fundamental entities that drive system requirements and access patterns.'
            });
        }

        if (keywords.includes('dashboard') || keywords.includes('interface') || keywords.includes('screen')) {
            fallbackExtracted.entities.push({
                type: 'interfaces',
                name: 'main-dashboard',
                description: 'Primary user interface',
                reasoning: 'Interface identified from UI terms. This will serve as a key interaction point and should be connected to relevant features and data models.'
            });
        }

        // Add connection if multiple entities found
        if (fallbackExtracted.entities.length > 1) {
            fallbackExtracted.connections.push({
                from: fallbackExtracted.entities[0].name,
                to: fallbackExtracted.entities[1].name,
                reasoning: 'Primary relationship between core entities establishes the fundamental system interaction pattern.'
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
        const prompt = await promptLoader.formatPrompt('parse-command', {
            graph: JSON.stringify(graph, null, 2),
            command: command
        });

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
            logger.warn('Failed to parse Claude response as JSON, using fallback');
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
        logger.error('Error processing AI command:', error);

        // Final fallback
        res.json({
            graphUpdates: null,
            message: 'Failed to process command. Try simpler commands like "add feature authentication" or "connect user to dashboard".'
        });
    }
});

// Prioritized question generation based on graph connectivity
app.post('/api/ai/generate-prioritized-questions', async (req, res) => {
    try {
        const { graph, existingQA, context } = req.body;

        // Check if API key is configured
        if (!process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_API_KEY === 'your_anthropic_api_key_here') {
            // Fallback: Generate questions that focus on connectivity
            const entities = graph?.entities || {};
            const connections = graph?.graph || [];
            const entityCount = Object.values(entities).reduce((sum, type) => sum + Object.keys(type).length, 0);

            let prioritizedQuestions = [];

            if (entityCount < 5) {
                // Focus on discovery
                prioritizedQuestions = [
                    { number: 1, text: "What are the core components that need to work together?", priority: 10 },
                    { number: 2, text: "How do users interact with these components?", priority: 9 },
                    { number: 3, text: "What data flows between components?", priority: 8 },
                    { number: 4, text: "Which components are most critical?", priority: 7 },
                    { number: 5, text: "What are the main dependencies?", priority: 6 }
                ];
            } else {
                // Focus on connectivity and relationships
                prioritizedQuestions = [
                    { number: 1, text: "How does the authentication system connect to user management?", priority: 10 },
                    { number: 2, text: "What interfaces do the main features share?", priority: 9 },
                    { number: 3, text: "Which components need to communicate in real-time?", priority: 8 },
                    { number: 4, text: "What are the data dependencies between features?", priority: 7 },
                    { number: 5, text: "How do the UI components map to backend services?", priority: 6 }
                ];
            }

            return res.json({ questions: prioritizedQuestions, source: 'ai-generated' });
        }

        // Build intelligent prompt for connectivity-focused questions
        const entityCount = promptLoader.countEntities(graph?.entities);
        const prompt = await promptLoader.formatPrompt('prioritized-questions', {
            entityTypes: JSON.stringify(Object.keys(graph?.entities || {}), null, 2),
            totalNodes: promptLoader.countEntities(graph?.entities),
            connectionCount: (graph?.graph || []).length,
            entitiesByType: promptLoader.formatEntities(graph?.entities),
            currentConnections: promptLoader.formatConnections(graph?.graph),
            recentQA: promptLoader.formatQAHistory(existingQA, 3)
        });

        const message = await anthropic.messages.create({
            model: 'claude-3-5-sonnet-20241022',
            max_tokens: 1200,
            messages: [{
                role: 'user',
                content: prompt
            }]
        });

        // Parse response
        const responseText = message.content[0].text;
        let questionsData;

        try {
            const jsonMatch = responseText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                questionsData = JSON.parse(jsonMatch[0]);
                // Sort by priority
                if (questionsData.questions) {
                    questionsData.questions.sort((a, b) => (b.priority || 0) - (a.priority || 0));
                    questionsData.source = 'ai-generated';
                }
            }
        } catch (e) {
            // Fallback
            questionsData = {
                questions: [
                    { number: 1, text: "How do your main components interact?", priority: 10 },
                    { number: 2, text: "What are the key data relationships?", priority: 8 },
                    { number: 3, text: "Which features share common infrastructure?", priority: 6 }
                ],
                source: 'ai-generated'
            };
        }

        res.json(questionsData);

    } catch (error) {
        logger.error('Error generating prioritized questions:', error.message || error);
        logger.error('Error stack:', error.stack);
        logger.error('Error details:', JSON.stringify(error, null, 2));

        res.status(500).json({
            error: 'Failed to generate questions',
            message: error.message || 'Unknown error occurred'
        });
    }
});

// Get recent logs endpoint
app.get('/api/logs', async (req, res) => {
    try {
        const lines = parseInt(req.query.lines) || 100;
        const logs = await logger.getRecentLogs(lines);
        res.json({ logs });
    } catch (error) {
        logger.error('Error fetching logs:', error);
        res.status(500).json({ error: 'Failed to fetch logs' });
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
            logger.error('Know tool error:', stderr);
        }

        res.json({ output: stdout, error: stderr });
    } catch (error) {
        logger.error('Error executing know tool:', error);
        res.status(500).json({ error: 'Failed to execute know tool' });
    }
});

// Start server
const server = app.listen(PORT, () => {
    logger.log(`Server running on http://localhost:${PORT}`);
    ensureGraphsDir();
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    logger.log('SIGTERM signal received: closing HTTP server');
    server.close(async () => {
        logger.log('HTTP server closed');
        await logger.archiveLogs();
        process.exit(0);
    });
});

process.on('SIGINT', async () => {
    logger.log('SIGINT signal received: closing HTTP server');
    server.close(async () => {
        logger.log('HTTP server closed');
        await logger.archiveLogs();
        process.exit(0);
    });
});