# Context: Spec Generation Enrichment

## Key Files

| File | Purpose |
|------|---------|
| `know/config/dependency-rules.json` | Schema definitions, reference types, meta schemas |
| `know/src/generators.py` | Spec generation logic |
| `know/know.py` | CLI commands including `spec` and `feature-spec` |
| `.ai/spec-graph.json` | Example graph to test against |

## Design Decisions

### 1. Three-Tier Data Model

| Tier | Contents | Cross-Ref? |
|------|----------|------------|
| **Entities** | name, description only | Yes (via graph) |
| **References** | Reusable schemas, signatures, data-models | Yes |
| **Meta.feature_specs** | Feature-specific prose (use_cases, testing, etc.) | No |

**Rationale**: Entities and references can be reused across features. Feature-specific prose like "use cases for ensemble-meshes" has no reuse value, so it lives in meta.

### 2. Graph Carries Relationships

All connections via `depends_on`:
- `component:x → source-file:y` (file location)
- `component:x → operation:y` (what it does)
- `operation:x → signature:y` (function signature)
- `operation:x → data-model:y` (input/output types)

**Rationale**: Generator traverses graph to assemble spec. No need to duplicate info in entity attributes.

### 3. New Reference Types

| Type | Purpose | Example |
|------|---------|---------|
| `api-schema` | Public API definitions | Methods, endpoints |
| `signature` | Function signatures | params[], returns |
| `test-spec` | Reusable test specs | May apply to multiple components |
| `security-spec` | Reusable security reqs | May apply to multiple components |

### 4. Meta.feature_specs Structure

```json
"meta": {
  "feature_specs": {
    "<feature-name>": {
      "status": "planned|in-progress|review-ready|complete",
      "phase": "Phase N (Name)",
      "priority": "P0|P1|P2|P3",
      "use_cases": [...],
      "testing": {...},
      "security": [...],
      "monitoring": [...],
      "performance": {...}
    }
  }
}
```

## Target Output

`know spec feature:ensemble-meshes` should produce markdown matching the example spec provided, including:
- Header with status/phase/priority
- Dependencies on other features
- Components with file paths and operations
- Interfaces with TypeScript schemas
- Data Models as TypeScript interfaces
- Business Logic narrative
- Use Cases table
- Testing Requirements (unit/integration/performance)
- Security & Privacy
- Monitoring & Observability
