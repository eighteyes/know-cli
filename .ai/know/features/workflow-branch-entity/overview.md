# Feature Overview: workflow-branch-entity

## Purpose
Add `workflow` entity type to spec-graph model, enabling ordered action sequences that implement features.

## Architecture

### Entity Hierarchy
```
feature → workflow → action (ordered)
feature → action (direct, for simple cases)
```

### Key Design Decisions

**1. Mixed Dependency Model**
- Features can depend on workflows (complex, ordered sequences)
- Features can depend on actions directly (simple, standalone)
- Actions can be reused across multiple workflows with different orderings

**2. Explicit Ordering via `depends_on_ordered`**
- New graph field: `depends_on_ordered: string[]`
- Only workflow entities use this field
- Array order is semantically significant
- No semantic overloading of regular `depends_on`

**3. Validation Rules**
- All actions in `depends_on_ordered` must exist as entities
- No circular dependencies (DAG preservation)
- Transitive dependencies implicit (no redundant edges needed)

## Data Model

**Workflow Entity:**
```json
"entities": {
  "workflow": {
    "login-flow": {
      "name": "Standard Login Flow",
      "description": "User authentication sequence"
    }
  }
}
```

**Graph Dependencies:**
```json
"graph": {
  "feature:login": {
    "depends_on": ["workflow:login-flow", "action:log-attempt"]
  },
  "workflow:login-flow": {
    "depends_on_ordered": ["action:show-form", "action:validate-credentials", "action:create-session"]
  }
}
```

## Benefits
- ✅ Actions reusable across workflows
- ✅ Clear separation: workflows = ordering, actions = behavior
- ✅ Flexible: features can mix workflows + standalone actions
- ✅ Explicit: `depends_on_ordered` clearly signals semantic ordering
- ✅ DAG preserved: no cycles, transitive deps implicit

## Implementation Requirements

### 1. Schema Changes
- Add `workflow` to allowed entity types in `dependency-rules.json`
- Support `depends_on_ordered` field in graph section
- Allow: `feature → workflow`, `workflow → action`

### 2. CLI Commands
- `know add workflow <key>` - create workflow entity
- `know link workflow:<key> action:a action:b action:c` - ordered linking
- `know graph down workflow:<key>` - show ordered actions
- `know check validate` - validate workflow dependencies

### 3. Validation Logic
- Check `depends_on_ordered` targets exist
- Detect circular dependencies
- Preserve array order in JSON serialization
- Ensure DAG invariants maintained

### 4. Documentation
- Update CLAUDE.md with workflow hierarchy
- Document `depends_on_ordered` semantics
- Add workflow examples to docs
