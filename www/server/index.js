const express = require('express');
const { exec } = require('child_process');
const WebSocket = require('ws');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');
const fs = require('fs').promises;
const Anthropic = require('@anthropic-ai/sdk');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const WS_PORT = process.env.WS_PORT || 8080;

// Initialize Anthropic client if API key is available
let anthropic = null;
if (process.env.ANTHROPIC_API_KEY && process.env.ANTHROPIC_API_KEY !== '${ANTHROPIC_API_KEY}') {
  anthropic = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });
  console.log('✅ Anthropic API initialized');
} else {
  console.log('⚠️  No Anthropic API key found - using fallback entity extraction');
}

// WebSocket server
const wss = new WebSocket.Server({ port: WS_PORT });

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '../public')));

// Know CLI wrapper function
function executeKnow(command, args = []) {
  return new Promise((resolve, reject) => {
    const knowPath = path.resolve(__dirname, process.env.KNOW_CLI_PATH || '../../know/know');
    const cmd = `${knowPath} ${command} ${args.join(' ')}`;

    exec(cmd, {
      env: {
        ...process.env,
        KNOWLEDGE_MAP: path.resolve(__dirname, process.env.KNOWLEDGE_MAP_PATH || '../../.ai/spec-graph.json')
      },
      maxBuffer: 1024 * 1024 * 10 // 10MB buffer for large outputs
    }, (error, stdout, stderr) => {
      if (error && !stdout) {
        reject({ error: error.message, stderr });
      } else {
        // Some know commands return non-zero exit codes even on success
        resolve({ output: stdout, stderr });
      }
    });
  });
}

// Broadcast updates to all WebSocket clients
function broadcastUpdate(type, data) {
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ type, data, timestamp: new Date().toISOString() }));
    }
  });
}

// WebSocket connection handler
wss.on('connection', (ws) => {
  console.log('New WebSocket client connected');

  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      console.log('Received:', data);
      // Handle client messages if needed
    } catch (err) {
      console.error('Invalid WebSocket message:', err);
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });

  // Send initial connection confirmation
  ws.send(JSON.stringify({ type: 'connected', message: 'WebSocket connected successfully' }));
});

// API Routes

// Get entire graph (dynamic based on query parameter)
app.get('/api/graph', async (req, res) => {
  try {
    const graphName = req.query.name || 'spec-graph.json';

    let graphPath;
    if (graphName === 'spec-graph.json') {
      // Load main graph from .ai directory
      graphPath = path.resolve(__dirname, process.env.KNOWLEDGE_MAP_PATH || '../../.ai/spec-graph.json');
    } else {
      // Load from graphs directory
      graphPath = path.resolve(__dirname, '../graphs', graphName);
    }

    const graphData = await fs.readFile(graphPath, 'utf8');
    const parsedGraph = JSON.parse(graphData);

    // Add dynamic metadata
    const stats = await fs.stat(graphPath);
    parsedGraph.meta = parsedGraph.meta || {};
    parsedGraph.meta.loadedFrom = graphName;
    parsedGraph.meta.lastModified = stats.mtime.toISOString();
    parsedGraph.meta.fileSize = stats.size;

    res.json(parsedGraph);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to load graph',
      details: error.message,
      requestedGraph: req.query.name
    });
  }
});

// List available graphs
app.get('/api/graphs/list', async (req, res) => {
  try {
    const graphsDir = path.resolve(__dirname, '../graphs');

    // Ensure graphs directory exists
    try {
      await fs.mkdir(graphsDir, { recursive: true });
    } catch (e) {
      // Directory might already exist
    }

    const files = await fs.readdir(graphsDir);
    const graphs = files
      .filter(f => f.endsWith('.json'))
      .map(f => ({
        name: f,
        path: path.join(graphsDir, f)
      }));

    // Add the main spec-graph.json
    graphs.unshift({
      name: 'spec-graph.json',
      path: path.resolve(__dirname, '../../.ai/spec-graph.json')
    });

    res.json({ graphs });
  } catch (error) {
    res.status(500).json({ error: 'Failed to list graphs', details: error.message });
  }
});

// Save current graph to backup
app.post('/api/graphs/save', async (req, res) => {
  try {
    const { name } = req.body;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupName = name || `graph-backup-${timestamp}.json`;

    const graphsDir = path.resolve(__dirname, '../graphs');
    await fs.mkdir(graphsDir, { recursive: true });

    const sourcePath = path.resolve(__dirname, '../../.ai/spec-graph.json');
    const targetPath = path.join(graphsDir, backupName);

    const graphData = await fs.readFile(sourcePath, 'utf8');
    await fs.writeFile(targetPath, graphData);

    res.json({ success: true, savedAs: backupName });
  } catch (error) {
    res.status(500).json({ error: 'Failed to save graph', details: error.message });
  }
});

// Load a saved graph
app.post('/api/graphs/load', async (req, res) => {
  try {
    const { name } = req.body;

    let sourcePath;
    if (name === 'spec-graph.json') {
      sourcePath = path.resolve(__dirname, '../../.ai/spec-graph.json');
    } else {
      sourcePath = path.resolve(__dirname, '../graphs', name);
    }

    const targetPath = path.resolve(__dirname, '../../.ai/spec-graph.json');

    // Backup current before loading new
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = path.resolve(__dirname, '../graphs', `auto-backup-${timestamp}.json`);
    const currentData = await fs.readFile(targetPath, 'utf8');
    await fs.writeFile(backupPath, currentData);

    // Load the selected graph
    const graphData = await fs.readFile(sourcePath, 'utf8');
    await fs.writeFile(targetPath, graphData);

    res.json({ success: true, loaded: name, autoBackup: `auto-backup-${timestamp}.json` });
  } catch (error) {
    res.status(500).json({ error: 'Failed to load graph', details: error.message });
  }
});

// Create new empty graph
app.post('/api/graphs/new', async (req, res) => {
  try {
    const { name } = req.body;
    const newGraphName = name || `new-graph-${Date.now()}.json`;

    const emptyGraph = {
      meta: {
        project: {
          name: "New Project",
          tagline: "Define your vision"
        },
        phases: {},
        qa_sessions: []
      },
      references: {},
      entities: {
        users: {},
        objectives: {},
        actions: {},
        features: {},
        components: {},
        interfaces: {},
        requirements: {},
        platforms: {}
      },
      graph: {}
    };

    const targetPath = path.resolve(__dirname, '../../.ai/spec-graph.json');

    // Backup current
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = path.resolve(__dirname, '../graphs', `before-new-${timestamp}.json`);
    const currentData = await fs.readFile(targetPath, 'utf8');
    await fs.writeFile(backupPath, currentData);

    // Write new empty graph
    await fs.writeFile(targetPath, JSON.stringify(emptyGraph, null, 2));

    res.json({ success: true, created: newGraphName, backup: `before-new-${timestamp}.json` });
  } catch (error) {
    res.status(500).json({ error: 'Failed to create new graph', details: error.message });
  }
});

// List entities by type
app.get('/api/entities/:type', async (req, res) => {
  try {
    const graphPath = path.resolve(__dirname, process.env.KNOWLEDGE_MAP_PATH || '../../.ai/spec-graph.json');
    const graphData = JSON.parse(await fs.readFile(graphPath, 'utf8'));
    const entities = graphData.entities[req.params.type] || {};
    res.json(Object.values(entities));
  } catch (error) {
    res.status(500).json({ error: 'Failed to get entities', details: error.message });
  }
});

// Add new entity
app.post('/api/entities/add', async (req, res) => {
  const { type, key, name } = req.body;

  try {
    // Convert to plural for the know command (it expects plural types)
    const pluralType = `${type}s`;

    // Use mod-graph.sh to add the entity
    const result = await executeKnow('mod', ['add', pluralType, key, name]);

    // Reload the graph to get updated data
    const graphPath = path.resolve(__dirname, '../../.ai/spec-graph.json');
    const graph = JSON.parse(await fs.readFile(graphPath, 'utf8'));

    res.json({
      success: true,
      message: `Added ${type}: ${name}`,
      entity: graph.entities[`${type}s`]?.[key]
    });

    // Broadcast the update to all connected clients
    broadcastUpdate('entity-added', {
      type,
      key,
      name
    });
  } catch (error) {
    console.error('Failed to add entity:', error);
    res.status(500).json({
      success: false,
      error: error.error || error.message || 'Failed to add entity',
      details: error.stderr || error.stack
    });
  }
});

// Execute know command
app.post('/api/know/command', async (req, res) => {
  const { command, args = [] } = req.body;

  try {
    const result = await executeKnow(command, args);

    // Try to parse as JSON if possible
    let output = result.output;
    try {
      output = JSON.parse(result.output);
    } catch {
      // Keep as string if not JSON
    }

    res.json({
      success: true,
      output,
      stderr: result.stderr
    });

    // Broadcast graph update if command modifies graph
    if (['mod', 'connect', 'disconnect', 'add', 'remove'].includes(command)) {
      broadcastUpdate('graph-updated', { command, args });
    }
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.error || error.message,
      stderr: error.stderr
    });
  }
});

// Discovery phase endpoints

// Save Q&A session data
app.post('/api/discover/save-qa', async (req, res) => {
  const { question, answer, entities } = req.body;

  try {
    const graphPath = path.resolve(__dirname, '../../.ai/spec-graph.json');
    const graph = JSON.parse(await fs.readFile(graphPath, 'utf8'));

    // Initialize qa_sessions if it doesn't exist
    if (!graph.meta) graph.meta = {};
    if (!graph.meta.qa_sessions) graph.meta.qa_sessions = [];

    // Find or create current session
    let session = graph.meta.qa_sessions.find(s => s.status === 'in_progress');
    if (!session) {
      session = {
        id: `session-${Date.now()}`,
        phase: 'discover',
        status: 'in_progress',
        started_at: new Date().toISOString(),
        last_updated: new Date().toISOString(),
        context: 'Discovery phase - building initial knowledge graph',
        questions: []
      };
      graph.meta.qa_sessions.push(session);
    }

    // Add Q&A to session
    const qaEntry = {
      q_id: `Q${session.questions.length + 1}`,
      category: question.type || 'exploration',
      question: question.text,
      answer: answer,
      status: 'answered',
      timestamp: new Date().toISOString(),
      graph_updates: entities.map(e => `${e.type}:${e.id}`)
    };

    session.questions.push(qaEntry);
    session.last_updated = new Date().toISOString();

    // Save updated graph
    await fs.writeFile(graphPath, JSON.stringify(graph, null, 2));

    res.json({ success: true, session_id: session.id, qa_id: qaEntry.q_id });
  } catch (error) {
    console.error('Failed to save Q&A:', error);
    res.status(500).json({ error: 'Failed to save Q&A session' });
  }
});

// Extract entities from user answer
app.post('/api/discover/extract', async (req, res) => {
  const { question, answer, context } = req.body;

  try {
    let entities = [];
    let suggestions = {};

    if (anthropic) {
      // Use real AI extraction
      console.log('Using AI for entity extraction...');
      entities = await extractEntitiesWithAI(answer, question, context);
      suggestions = await generateAISuggestions(entities, context);
    } else {
      // Fallback to simple extraction
      console.log('Using fallback entity extraction (no API key)');
      entities = extractEntitiesFromText(answer, question.type || 'exploration');
      suggestions = generateSuggestions(entities, context);
    }

    res.json({
      entities,
      suggestions,
      confidence: anthropic ? 0.95 : 0.65,
      validation: {
        hasDuplicates: false,
        duplicates: []
      }
    });
  } catch (error) {
    console.error('Entity extraction error:', error);
    // Fallback to simple extraction on error
    const entities = extractEntitiesFromText(answer, question.type || 'exploration');
    res.json({
      entities,
      suggestions: generateSuggestions(entities, context),
      confidence: 0.5,
      validation: { hasDuplicates: false, duplicates: [] }
    });
  }
});

// Analyze gaps in the graph
app.post('/api/discover/analyze-gaps', async (req, res) => {
  try {
    const healthResult = await executeKnow('health');
    const gaps = parseHealthOutput(healthResult.output);
    res.json(gaps);
  } catch (error) {
    res.status(500).json({ error: 'Failed to analyze gaps', details: error.message });
  }
});

// Get next question based on gaps
app.get('/api/discover/next-question', async (req, res) => {
  try {
    const healthResult = await executeKnow('health');
    const gaps = parseHealthOutput(healthResult.output);
    const question = generateQuestionFromGaps(gaps);
    res.json(question);
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate question', details: error.message });
  }
});

// AI-powered entity extraction
async function extractEntitiesWithAI(answer, question, context) {
  if (!anthropic) {
    return extractEntitiesFromText(answer, question.type);
  }

  const prompt = `You are a knowledge graph expert helping to extract entities from user answers.

Current context:
- Question: ${question.text}
- Question type: ${question.type || 'exploration'}
- Current graph has ${context?.entities ? Object.keys(context.entities).length : 0} entity types

User's answer: "${answer}"

Extract entities from the answer and return them as a JSON array. Each entity should have:
- type: one of (feature, component, interface, requirement, user, objective, action, platform)
- id: a snake_case identifier
- name: human-readable name
- description: brief description of what it does
- dependencies: array of entity references this depends on (format: "type:id")

Focus on concrete entities mentioned in the answer. Don't invent entities not mentioned.

Return ONLY valid JSON array, no explanation:`;

  try {
    const message = await anthropic.messages.create({
      model: process.env.ANTHROPIC_MODEL || 'claude-3-haiku-20240307',
      max_tokens: 1000,
      temperature: 0.3,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const content = message.content[0].text;
    // Extract JSON from the response
    const jsonMatch = content.match(/\[[\s\S]*\]/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return [];
  } catch (error) {
    console.error('AI extraction error:', error);
    return extractEntitiesFromText(answer, question.type);
  }
}

async function generateAISuggestions(entities, context) {
  if (!anthropic || entities.length === 0) {
    return generateSuggestions(entities, context);
  }

  const prompt = `Given these extracted entities:
${JSON.stringify(entities, null, 2)}

And knowing the current graph context has these entity types:
${context?.entities ? Object.keys(context.entities).join(', ') : 'none'}

Suggest likely dependencies for each entity. Return a JSON object where:
- Keys are entity IDs from the list above
- Values are objects with:
  - dependencies: array of suggested dependency refs (format: "type:id")
  - relatedEntities: array of other related entity refs

Focus on common architectural patterns. Return ONLY valid JSON:`;

  try {
    const message = await anthropic.messages.create({
      model: process.env.ANTHROPIC_MODEL || 'claude-3-haiku-20240307',
      max_tokens: 500,
      temperature: 0.3,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const content = message.content[0].text;
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return {};
  } catch (error) {
    console.error('AI suggestions error:', error);
    return generateSuggestions(entities, context);
  }
}

// Helper functions

function extractEntitiesFromText(text, questionType) {
  // Simple entity extraction logic
  const entities = [];

  // Look for common patterns
  const patterns = {
    feature: /(?:feature|capability|functionality):\s*([^,\.]+)/gi,
    component: /(?:component|service|module):\s*([^,\.]+)/gi,
    requirement: /(?:require|need|must have):\s*([^,\.]+)/gi
  };

  // Split by common delimiters
  const items = text.split(/[,;]|\band\b/i).map(s => s.trim()).filter(Boolean);

  items.forEach(item => {
    const id = item.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    if (id) {
      entities.push({
        type: questionType === 'feature' ? 'feature' : 'component',
        id,
        name: item,
        description: '',
        dependencies: []
      });
    }
  });

  return entities;
}

function generateSuggestions(entities, context) {
  const suggestions = {};

  entities.forEach(entity => {
    suggestions[entity.id] = {
      dependencies: [],
      relatedEntities: []
    };

    // Suggest common dependencies based on type
    if (entity.type === 'feature') {
      if (entity.id.includes('telemetry') || entity.id.includes('real-time')) {
        suggestions[entity.id].dependencies.push('component:websocket-manager');
      }
      if (entity.id.includes('map') || entity.id.includes('location')) {
        suggestions[entity.id].dependencies.push('component:geolocation-service');
      }
    }
  });

  return suggestions;
}

function parseHealthOutput(output) {
  // Parse the health command output
  const gaps = {
    missingDependencies: [],
    incompleteEntities: [],
    orphanedEntities: [],
    lowCompleteness: []
  };

  // This would parse the actual know health output
  // For now, return mock data
  return gaps;
}

function generateQuestionFromGaps(gaps) {
  // Generate targeted questions based on gaps
  const questions = [
    {
      type: 'exploration',
      text: 'What are the main features your system needs to provide?',
      context: null
    },
    {
      type: 'dependency',
      text: 'What components or services does your main feature need?',
      context: null
    },
    {
      type: 'completion',
      text: 'Can you describe the user roles in your system?',
      context: null
    }
  ];

  return questions[Math.floor(Math.random() * questions.length)];
}

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
  console.log(`WebSocket server running on ws://0.0.0.0:${WS_PORT}`);
  console.log(`Knowledge map: ${process.env.KNOWLEDGE_MAP_PATH}`);
  console.log(`Access from browser: http://localhost:${PORT} or http://127.0.0.1:${PORT}`);
});