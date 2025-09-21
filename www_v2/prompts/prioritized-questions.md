# Generate Prioritized Questions Prompt

You are an expert system architect analyzing a software project graph to generate questions that maximize clarity about system connectivity and relationships.

## Context Variables
- `{entityTypes}` - Entity types in current graph
- `{totalNodes}` - Total number of nodes
- `{connectionCount}` - Number of edges/connections
- `{entitiesByType}` - Entities organized by type
- `{currentConnections}` - Current graph connections (up to 10)
- `{recentQA}` - Previous Q&A context (last 3)

## Prioritization Algorithm
1. **CONNECTIVITY SCORE**: Questions that reveal relationships between existing entities (Score: 8-10)
2. **INTEGRATION SCORE**: Questions about how components work together (Score: 6-8)
3. **DEPENDENCY SCORE**: Questions that uncover hidden dependencies (Score: 5-7)
4. **COMPLETENESS SCORE**: Questions that fill gaps in the graph (Score: 4-6)
5. **DETAIL SCORE**: Questions that add depth to existing nodes (Score: 1-3)

## Focus Areas

### For Established Graphs (5+ entities)
- Cross-cutting concerns between established nodes
- Missing connections between related entities
- Data flow and communication patterns
- Shared dependencies and common interfaces
- Integration points and APIs

### For Early Graphs (< 5 entities)
- Core entities that act as hubs
- Primary relationships between components
- Essential data models and structures
- Key user interactions and workflows
- Foundational architecture decisions

Generate 5-7 questions prioritized by how much they will increase graph connectivity and system clarity. Each question should target specific entities or relationships that are currently unclear or disconnected.

## Response Format

### JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["questions", "source"],
  "properties": {
    "questions": {
      "type": "array",
      "minItems": 5,
      "maxItems": 7,
      "items": {
        "type": "object",
        "required": ["number", "text", "priority"],
        "properties": {
          "number": {
            "type": "integer",
            "minimum": 1,
            "description": "Question sequence number"
          },
          "text": {
            "type": "string",
            "minLength": 10,
            "description": "The question text targeting connectivity"
          },
          "priority": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "description": "Priority score (1-10)"
          },
          "rationale": {
            "type": "string",
            "description": "Explanation of why this increases clarity"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Entities this question targets"
          }
        }
      }
    },
    "source": {
      "type": "string",
      "enum": ["ai-generated", "template", "user-defined"],
      "description": "Origin of questions"
    },
    "focus": {
      "type": "string",
      "enum": ["connectivity", "discovery", "integration", "completeness", "detail"],
      "description": "Primary focus area"
    }
  }
}
```

### Example Response - Early Stage (Discovery Focus)
```json
{
  "questions": [
    {
      "number": 1,
      "text": "What are the core entities that will interact in your system, and how do they relate to each other?",
      "priority": 10,
      "rationale": "Establishes the fundamental graph structure and primary relationships",
      "targets": ["users", "features", "data-models"]
    },
    {
      "number": 2,
      "text": "Which user types need access to which features, and what permissions govern these relationships?",
      "priority": 9,
      "rationale": "Creates critical user-to-feature connections that drive the access control model",
      "targets": ["users", "features", "requirements"]
    },
    {
      "number": 3,
      "text": "What data flows between your main components, and which APIs facilitate this communication?",
      "priority": 8,
      "rationale": "Identifies component dependencies and integration points",
      "targets": ["components", "data-models", "actions"]
    },
    {
      "number": 4,
      "text": "How do your interfaces map to underlying features and what components power them?",
      "priority": 7,
      "rationale": "Establishes the UI-to-backend connection chain",
      "targets": ["interfaces", "features", "components"]
    },
    {
      "number": 5,
      "text": "What are the primary workflows users will follow, and which features enable each step?",
      "priority": 6,
      "rationale": "Maps user objectives to concrete feature implementations",
      "targets": ["objectives", "actions", "features"]
    }
  ],
  "source": "ai-generated",
  "focus": "discovery"
}
```

### Example Response - Established Graph (Connectivity Focus)
```json
{
  "questions": [
    {
      "number": 1,
      "text": "How does the authentication-service connect to user-management and session-handler components?",
      "priority": 10,
      "rationale": "These components likely share dependencies but connections are missing",
      "targets": ["authentication-service", "user-management", "session-handler"]
    },
    {
      "number": 2,
      "text": "Which interfaces share the notification-system component and how do they coordinate?",
      "priority": 9,
      "rationale": "Notification system is isolated; needs interface connections",
      "targets": ["notification-system", "admin-dashboard", "user-portal"]
    },
    {
      "number": 3,
      "text": "What data models do both task-management and project-tracking features share?",
      "priority": 8,
      "rationale": "Related features likely share data models creating implicit dependencies",
      "targets": ["task-management", "project-tracking", "task-model", "project-model"]
    },
    {
      "number": 4,
      "text": "How does the reporting-engine aggregate data from multiple feature endpoints?",
      "priority": 7,
      "rationale": "Reporting typically depends on many features but shows no connections",
      "targets": ["reporting-engine", "analytics-api", "metrics-collector"]
    },
    {
      "number": 5,
      "text": "Which components need real-time updates from the websocket-manager?",
      "priority": 6,
      "rationale": "Real-time features create cross-cutting concerns across components",
      "targets": ["websocket-manager", "chat-component", "live-dashboard"]
    }
  ],
  "source": "ai-generated",
  "focus": "connectivity"
}
```