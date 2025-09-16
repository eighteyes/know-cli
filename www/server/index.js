const express = require('express');
const { exec } = require('child_process');
const WebSocket = require('ws');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');
const fs = require('fs').promises;
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const WS_PORT = process.env.WS_PORT || 8080;

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

// Get entire graph
app.get('/api/graph', async (req, res) => {
  try {
    const graphPath = path.resolve(__dirname, process.env.KNOWLEDGE_MAP_PATH || '../../.ai/spec-graph.json');
    const graphData = await fs.readFile(graphPath, 'utf8');
    res.json(JSON.parse(graphData));
  } catch (error) {
    res.status(500).json({ error: 'Failed to load graph', details: error.message });
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

// Extract entities from user answer
app.post('/api/discover/extract', async (req, res) => {
  const { question, answer, context } = req.body;

  // For now, use simple extraction logic
  // In production, this would call an AI service
  const entities = extractEntitiesFromText(answer, question.type);

  res.json({
    entities,
    confidence: 0.85,
    suggestions: generateSuggestions(entities, context)
  });
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