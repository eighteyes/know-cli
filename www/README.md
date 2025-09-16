# Knowledge Graph Builder Webapp

An interactive web application for building knowledge graphs with AI assistance, based on the `know` CLI tool.

## Features

### Phase 1: Discover (Implemented ✅)
- Interactive Q&A workflow for building knowledge graphs
- AI-powered entity extraction from natural language answers
- Entity review and editing interface before adding to graph
- Gap-driven question generation using `know` CLI analysis
- Real-time graph visualization
- WebSocket updates for live collaboration
- Persistent entity sidebar with minimap

### Upcoming Phases
- **Validation** - Wireframe generation and ML testing
- **Define** - Specification generation from validated designs
- **Deliver** - Package generation for AI handoff
- **Phases** - Work organization and prioritization

## Setup

### Prerequisites
- Node.js 16+
- The `know` CLI tool installed and accessible
- A `spec-graph.json` file in `.ai/` directory

### Installation

1. Install dependencies:
```bash
cd www
npm install
```

2. Configure environment (already done in `.env`):
```
PORT=3001
WS_PORT=8081
KNOWLEDGE_MAP_PATH=../../.ai/spec-graph.json
KNOW_CLI_PATH=../../know/know
```

3. Start the server:
```bash
npm start
```

4. Open your browser to: http://localhost:3001

## Usage

### Discover Phase

1. **Answer Questions**: The system asks targeted questions based on gaps in your knowledge graph
2. **Review Entities**: AI extracts entities from your answers - review and edit before adding
3. **Build Graph**: Entities are added to the graph with proper dependencies
4. **Visualize Progress**: See your graph grow in real-time

### Key Features

- **Gap-Driven Questions**: Uses `know health`, `know gaps`, and `know validate` to generate relevant questions
- **Entity Extraction**: Natural language processing to identify features, components, requirements
- **Duplicate Detection**: Prevents adding similar entities
- **Dependency Management**: Automatically suggests and validates dependencies
- **Real-time Updates**: WebSocket connection for live graph updates

## Architecture

```
webapp/
├── server/
│   └── index.js         # Express server with know CLI proxy
├── public/
│   ├── index.html       # Main layout
│   ├── css/
│   │   └── styles.css   # Dark theme with glassmorphism
│   └── js/
│       ├── app.js       # Core application logic
│       ├── discover.js  # Discover phase implementation
│       └── graph.js     # Graph visualization
└── package.json
```

## API Endpoints

- `GET /api/graph` - Get the complete knowledge graph
- `POST /api/know/command` - Execute any know CLI command
- `POST /api/discover/extract` - Extract entities from text
- `POST /api/discover/analyze-gaps` - Analyze graph gaps
- `GET /api/discover/next-question` - Get next targeted question

## WebSocket Events

- `connected` - Initial connection confirmation
- `entity-added` - New entity added to graph
- `graph-updated` - Graph has been modified

## Development

To run in development mode with auto-reload:
```bash
npm run dev
```

## Troubleshooting

- If ports are in use, modify `.env` and update the ports in `app.js`
- Ensure `know` CLI is accessible from the server directory
- Check that `spec-graph.json` exists and is valid JSON

## Next Steps

1. Implement remaining phases (Validation, Define, Deliver, Phases)
2. Add AI integration for better entity extraction
3. Enhance graph visualization with better layouts
4. Add authentication and multi-user support
5. Implement graph versioning and history