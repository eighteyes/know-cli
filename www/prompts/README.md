# AI Prompts

This directory contains extracted AI prompts used by the discovery application.

## Structure

```
prompts/
├── README.md                  # This file
├── loader.js                 # Prompt loading and formatting utility
├── generate-questions.md     # Progressive question generation
├── expand-question.md        # Question expansion with choices
├── extract-entities.md       # Entity extraction from text
├── parse-command.md         # Natural language command parsing
└── prioritized-questions.md  # Connectivity-focused questions
```

## Usage

The prompts are loaded and formatted using the `PromptLoader` class:

```javascript
const PromptLoader = require('./prompts/loader');
const promptLoader = new PromptLoader();

// Load and format a prompt with variables
const prompt = await promptLoader.formatPrompt('generate-questions', {
    context: 'Project context here',
    existingQA: promptLoader.formatQAHistory(qaArray),
    currentGraph: 'Graph info'
});
```

## Prompt Files

### generate-questions.md
Generates intelligent follow-up questions based on conversation history and project context. Uses progressive phases:
- Initial Discovery (0 Q&As)
- Requirements Gathering (< 5 Q&As)
- Architecture & Design (< 10 Q&As)
- Implementation Details (10+ Q&As)

### expand-question.md
Expands a single question into multiple choice options with:
- Strategic choices
- Expert recommendations
- Tradeoff analysis
- Alternatives
- Implementation challenges

### extract-entities.md
Extracts structured entities and references from user text:
- Entity types (users, features, interfaces, etc.)
- Reference categories (config, metrics, etc.)
- Dependency relationships

### parse-command.md
Parses natural language commands to modify the graph:
- Add/Create entities
- Remove/Delete entities
- Connect/Link entities
- Modify/Update entities
- Bulk operations

### prioritized-questions.md
Generates questions prioritized by connectivity impact:
- Connectivity score (8-10)
- Integration score (6-8)
- Dependency score (5-7)
- Completeness score (4-6)
- Detail score (1-3)

## Helper Functions

The `PromptLoader` class provides utilities:
- `formatQAHistory()` - Format Q&A pairs
- `formatEntities()` - Format entity lists
- `formatConnections()` - Format graph connections
- `countEntities()` - Count total entities

## Variable Substitution

Prompts use `{variable}` syntax for substitution:
```markdown
## Context Variables
- `{context}` - PROJECT CONTEXT
- `{existingQA}` - CONVERSATION HISTORY
```

Variables are replaced when formatting the prompt.

## JSON Schema Validation

All prompts now include structured JSON schemas for validation:

### Schema Files
- `schemas.js` - Contains JSON Schema definitions for all prompt responses
- Each prompt file includes:
  - JSON Schema definition
  - Example responses
  - Field validation rules

### Validation Features
- **Type checking** - Ensures correct data types
- **Pattern validation** - Enforces kebab-case naming conventions
- **Required fields** - Validates all required properties exist
- **Array constraints** - Min/max items, array structure
- **String constraints** - Minimum length, regex patterns
- **Enum validation** - Restricted value sets

### Usage in Server
```javascript
// Structured AI call with automatic validation
const data = await makeStructuredAICall(
    'generate-questions',    // Prompt name
    { context: 'app' },      // Variables
    'generateQuestions',     // Schema name
    1000                     // Max tokens
);
```

### Response Cleaning
The system automatically:
- Converts entity names to kebab-case
- Ensures required arrays exist
- Adds missing sequence numbers
- Validates enum values
- Sanitizes input patterns

## Best Practices

1. Keep prompts focused and structured
2. Use clear section headers
3. Define expected response formats with JSON schemas
4. Include context variables at the top
5. Provide concrete examples with proper formatting
6. Document phases and strategies
7. Test responses against schemas
8. Use validation for type safety