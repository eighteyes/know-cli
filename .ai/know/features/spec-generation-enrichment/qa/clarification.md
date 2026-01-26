# Clarification Q&A: Spec Generation Enrichment

**Date**: 2025-12-22
**Phase**: 2 - Clarify

---

## Example Feature Selection

**Q: Which existing feature should we enhance with the full metadata structure as our working example?**

**A: graph-embeddings (Recommended)**

**Rationale:**
- Already has partial `meta.feature_specs` entry in spec-graph.json
- Well-defined feature (semantic search layer)
- Good mix of components, operations, and data models
- Demonstrates real-world usage
- Can show before/after comparison

**Implementation Plan:**
1. Review current graph-embeddings spec-graph entry
2. Identify components and operations
3. Add source-file references for components
4. Add signature references for key operations
5. Create data-model references for embeddings structures
6. Populate full meta.feature_specs with:
   - Use cases (semantic search, suggestions, etc.)
   - Testing requirements (unit/integration/performance)
   - Security considerations
   - Monitoring metrics
   - Performance characteristics

---

## TypeScript Rendering Format

**Q: For TypeScript rendering of data-models, should we support inline definitions or reference external files?**

**A: Inline only (Recommended)**

**Decision:**
- Schema defined directly in data-model reference as JSON
- No file references or external dependencies
- Generator renders JSON schema as TypeScript interface

**Format:**
```json
{
  "references": {
    "data-model": {
      "embedding-vector": {
        "name": "EmbeddingVector",
        "language": "typescript",
        "schema": {
          "entityId": "string",
          "vector": "number[]",
          "model": "string",
          "hash": "string",
          "createdAt": "string"
        }
      }
    }
  }
}
```

**Rendered as:**
```typescript
interface EmbeddingVector {
  entityId: string;
  vector: number[];
  model: string;
  hash: string;
  createdAt: string;
}
```

**Advantages:**
- Self-contained (no external file dependencies)
- Easy to version and track in graph JSON
- Simple to render
- No file path resolution needed
- Works with any graph location

**Type Syntax Support:**
- Primitives: `string`, `number`, `boolean`
- Arrays: `type[]`
- Union types: `'value1' | 'value2'`
- Optional: `type | undefined`
- Objects: Nested JSON for complex types

---

## Validation Hints Strategy

**Q: Should validation provide helpful hints for using the new reference types?**

**A: Yes, comprehensive hints with actionable guidance**

**Context**: "AI will be using this, give it information to fix the issue"

### Hint 1: Components → source-file

**When to trigger:**
- Component entity exists
- No source-file reference in dependencies

**Message format:**
```
⚠ Component 'component:X' lacks source-file reference

Suggested fix:
  1. Add source-file reference:
     know -g .ai/spec-graph.json add-ref source-file X '{"path":"src/path/to/file.ts","module":"modulename"}'
  2. Link component to file:
     know -g .ai/spec-graph.json link component:X source-file:X
```

**AI-friendly format** (machine-parseable):
```json
{
  "type": "missing_reference",
  "severity": "warning",
  "entity": "component:X",
  "missing": "source-file",
  "suggested_commands": [
    "know -g .ai/spec-graph.json add-ref source-file X '{...}'",
    "know -g .ai/spec-graph.json link component:X source-file:X"
  ]
}
```

### Hint 2: Operations → signature

**When to trigger:**
- Operation entity exists
- No signature reference in dependencies

**Message format:**
```
⚠ Operation 'operation:generate_embedding' lacks signature reference

Suggested fix:
  1. Add signature reference:
     know -g .ai/spec-graph.json add-ref signature generate_embedding '{"name":"generateEmbedding","params":[{"name":"text","type":"string"}],"returns":"Promise<number[]>"}'
  2. Link operation to signature:
     know -g .ai/spec-graph.json link operation:generate_embedding signature:generate_embedding
```

### Hint 3: Features → meta.feature_specs

**When to trigger:**
- Feature entity exists
- Has components/operations (not trivial)
- No entry in meta.feature_specs

**Message format:**
```
⚠ Feature 'feature:graph-embeddings' lacks metadata in meta.feature_specs

This feature has 3 components and 7 operations - consider adding rich metadata.

Suggested addition to spec-graph.json meta section:
{
  "feature_specs": {
    "graph-embeddings": {
      "status": "planned",
      "phase": "Phase 3",
      "priority": "P1",
      "use_cases": [
        {"name": "...", "description": "...", "config": {...}}
      ],
      "testing": {
        "unit": ["..."],
        "integration": ["..."],
        "performance": ["..."]
      },
      "security": ["..."],
      "monitoring": ["..."],
      "performance": {
        "latency": "...",
        "cost": "...",
        "quality": "..."
      }
    }
  }
}
```

### Hint Format Principles

1. **Actionable** - Provide exact commands to fix
2. **Contextual** - Explain why the hint matters
3. **Machine-parseable** - Include structured JSON for AI consumption
4. **Progressive** - Show only relevant hints (don't overwhelm)
5. **Educational** - Teach the pattern for future use

---

## Remaining Technical Decisions

### Data Model Schema Details

**Complex type support:**
```json
{
  "data-model": {
    "fork-config": {
      "name": "ForkConfig",
      "language": "typescript",
      "schema": {
        "enabled": "boolean",
        "forkCount": "number",
        "strategy": "'vote' | 'synthesize' | 'best_of'",
        "models": "('sonnet' | 'opus' | 'haiku')[] | undefined",
        "timeout": "number | undefined"
      }
    }
  }
}
```

**Rendered as:**
```typescript
interface ForkConfig {
  enabled: boolean;
  forkCount: number;
  strategy: 'vote' | 'synthesize' | 'best_of';
  models: ('sonnet' | 'opus' | 'haiku')[] | undefined;
  timeout: number | undefined;
}
```

### Signature Schema Details

**Basic signature:**
```json
{
  "signature": {
    "generate_embedding": {
      "name": "generateEmbedding",
      "params": [
        {"name": "text", "type": "string"},
        {"name": "model", "type": "string", "optional": true}
      ],
      "returns": "Promise<number[]>"
    }
  }
}
```

**Rendered as:**
```typescript
function generateEmbedding(
  text: string,
  model?: string
): Promise<number[]>
```

### API Schema Details

**API Schema structure:**
```json
{
  "api-schema": {
    "embeddings-api": {
      "name": "Embeddings API",
      "description": "Public API for semantic search",
      "methods": [
        {
          "name": "embed",
          "signature": "signature:generate_embedding",
          "description": "Generate embedding for text"
        },
        {
          "name": "find",
          "signature": "signature:find_similar",
          "description": "Find similar entities"
        }
      ]
    }
  }
}
```

**Rendered as:**
```markdown
## Embeddings API

Public API for semantic search

### Methods

**embed** - Generate embedding for text
- Signature: `generateEmbedding(text: string, model?: string): Promise<number[]>`

**find** - Find similar entities
- Signature: `findSimilar(query: string, limit?: number): Promise<Entity[]>`
```

### meta.feature_specs Schema

**Full structure:**
```json
{
  "meta": {
    "feature_specs": {
      "feature-name": {
        "status": "planned" | "in-progress" | "review-ready" | "complete",
        "phase": "Phase N (Name)",
        "priority": "P0" | "P1" | "P2" | "P3",
        "use_cases": [
          {
            "name": "Use Case Name",
            "description": "What this accomplishes",
            "config": {"key": "value"}
          }
        ],
        "testing": {
          "unit": ["Test requirement 1", "Test requirement 2"],
          "integration": ["Integration test 1"],
          "performance": ["Performance benchmark 1"]
        },
        "security": [
          "Security requirement 1",
          "Security consideration 2"
        ],
        "monitoring": [
          "Metric to track 1",
          "Alert condition 2"
        ],
        "performance": {
          "latency": "Expected latency characteristics",
          "cost": "Cost implications",
          "quality": "Quality trade-offs"
        }
      }
    }
  }
}
```

---

## Edge Cases Resolved

### 1. Missing Metadata Sections

**Scenario**: Feature has meta.feature_specs but missing some sections

**Solution**: Graceful degradation
- Render only present sections
- No "Not specified" messages for optional sections
- Empty arrays/objects treated as "not present"

### 2. Invalid TypeScript Syntax

**Scenario**: data-model schema contains invalid TypeScript types

**Solution**: Validate during reference addition
- Basic syntax check (primitives, arrays, unions)
- Warn on unknown types but allow
- Render as-is (let TypeScript compiler catch errors)

### 3. Broken Reference Links

**Scenario**: signature reference ID doesn't exist

**Solution**: Soft validation warning
- Show "⚠ Referenced signature not found: signature:xyz"
- Include fix command
- Continue rendering (show ID as-is)

### 4. Circular Dependencies

**Scenario**: operation:A → signature:A → data-model:B → operation:A

**Solution**: Not applicable (references are terminal)
- References cannot have outgoing dependencies
- Circular deps only possible in entity graph
- Existing cycle detection handles this

---

## Implementation Priorities

### Must-Have (MVP)
1. ✅ 4 new reference types in dependency-rules.json
2. ✅ meta.feature_specs schema documented
3. ✅ Enhanced generate_feature_spec() with new sections
4. ✅ TypeScript rendering for data-models
5. ✅ Signature rendering
6. ✅ graph-embeddings fully enriched as example
7. ✅ 3 validation hints implemented

### Should-Have (Post-MVP)
- API schema rendering
- Business logic narrative extraction
- Test-spec and security-spec reference types
- Multiple example features
- Migration guide for existing features

### Nice-to-Have (Future)
- Auto-generation of signatures from code
- IDE integration for schema editing
- Validation in CI/CD pipeline
- Interactive metadata editor

---

## Next Phase: Architect

With all technical decisions made, we can now design the implementation approach:

1. **Minimal changes approach** - Extend existing generator minimally
2. **Comprehensive approach** - Full rewrite with all features
3. **Pragmatic balance** - Core enhancements with future extensibility

We'll evaluate trade-offs and create an ADR for the chosen architecture.
