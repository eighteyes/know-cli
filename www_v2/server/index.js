const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

const app = express();
const PORT = 8880;

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
        const timestamp = Date.now();
        const filename = `graph-${timestamp}.json`;
        const filepath = path.join(GRAPHS_DIR, filename);

        await fs.writeFile(filepath, JSON.stringify(req.body, null, 2));

        // Also update the main spec-graph.json if it exists
        await fs.writeFile(AI_SPEC_GRAPH, JSON.stringify(req.body, null, 2));

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

        // For MVP, return mock questions
        // In production, this would call Anthropic API
        const questions = [
            { number: 1, text: "What is the primary goal of this system?" },
            { number: 2, text: "Who are the main users of this application?" },
            { number: 3, text: "What key features are essential for the MVP?" },
            { number: 4, text: "What are the performance requirements?" },
            { number: 5, text: "How will users interact with the system?" }
        ];

        // If we have context, generate more specific questions
        if (context && context.length > 20) {
            questions.push(
                { number: 6, text: "What data needs to be stored and managed?" },
                { number: 7, text: "What are the security requirements?" },
                { number: 8, text: "How should the system handle errors?" },
                { number: 9, text: "What integrations are required?" },
                { number: 10, text: "What is the expected scale of usage?" }
            );
        }

        res.json({ questions });
    } catch (error) {
        console.error('Error generating questions:', error);
        res.status(500).json({ error: 'Failed to generate questions' });
    }
});

// Expand question with multiple choice and recommendations
app.post('/api/ai/expand-question', async (req, res) => {
    try {
        const { question } = req.body;

        // Mock expanded options for MVP
        const expanded = {
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

        res.json(expanded);
    } catch (error) {
        console.error('Error expanding question:', error);
        res.status(500).json({ error: 'Failed to expand question' });
    }
});

// Extract entities and references from text
app.post('/api/ai/extract-entities', async (req, res) => {
    try {
        const { text, graph } = req.body;

        // Mock entity extraction for MVP
        const extracted = {
            entities: [],
            references: [],
            connections: []
        };

        // Simple keyword detection for demo
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

        // Add some references
        if (keywords.includes('api') || keywords.includes('endpoint')) {
            extracted.references.push({
                key: 'api_base_url',
                value: '/api/v1'
            });
        }

        // Suggest connections
        if (extracted.entities.length > 1) {
            extracted.connections.push({
                from: extracted.entities[0].name,
                to: extracted.entities[1].name
            });
        }

        res.json(extracted);
    } catch (error) {
        console.error('Error extracting entities:', error);
        res.status(500).json({ error: 'Failed to extract entities' });
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