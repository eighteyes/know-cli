# Codebase Exploration: workflow-branch-entity

## Architecture Overview

The know CLI uses a modular architecture with clear separation of concerns:

```
know.py (CLI entry point, 6100+ lines)
  ↓
├─ entities.py (EntityManager - CRUD operations, 263 lines)
├─ graph.py (GraphManager - NetworkX ops, cross-graph, 475 lines)
├─ validation.py (GraphValidator - multi-layer validation, 921 lines)
├─ dependencies.py (DependencyManager - rule enforcement, 376 lines)
└─ cache.py (GraphCache - atomic read/write, 183 lines)
```

## Key Findings

### 1. Entity Type Definition (NOT Hardcoded!)

**CRITICAL:** Entity types are loaded from `dependency-rules.json`, NOT hardcoded in Python.

**File:** `know/src/entities.py` line 25
```python
self.VALID_ENTITY_TYPES = set(self.rules.get('entity_description', {}).keys())
```

**Implication:** Adding "workflow" to `dependency-rules.json` automatically makes it valid everywhere.

**Current entity types (spec-graph):**
- project, user, objective, feature, action, component, operation

**Current "workflow" status:**
- Exists in `meta_description` as workflow metadata
- NOT in `entity_description` as a first-class entity type
- NOT in `allowed_dependencies`

### 2. Dependency Rules Structure

**File:** `know/config/dependency-rules.json` (292 lines)

**Sections:**
- `allowed_dependencies`: Chain rules (feature→action, action→component, etc.)
- `entity_description`: Entity type definitions
- `reference_description`: 40+ reference types (terminal nodes)
- `reference_dependency_rule`: References can depend on ANY entity
- `meta_description`: Meta section types
- `meta_schema`: Detailed schemas for meta sections

**Rule enforcement:** `know/src/dependencies.py` lines 160-196
```python
def validate_graph():
    for entity_id, node_data in graph.items():
        for dep_id in node_data.get('depends_on', []):
            # Skip references (always valid)
            if dep_type in reference_description:
                continue
            # Check entity→entity rules
            if not is_valid_dependency(entity_type, dep_type):
                errors.append(...)
```

### 3. Graph JSON Structure

**Current structure:**
```json
{
  "entities": {
    "feature": {
      "auth": {"name": "...", "description": "..."}
    }
  },
  "graph": {
    "feature:auth": {
      "depends_on": ["action:login", "action:logout"]
    }
  }
}
```

**`depends_on` parsing:** `know/src/graph.py` lines 178-183
- Reads array, builds NetworkX DiGraph
- Array order is preserved by JSON (Python 3.7+)
- But order is NOT semantically meaningful (treated as set)

### 4. Adding `depends_on_ordered` Support

**Implementation points:**

| File | Function | Lines | Change |
|------|----------|-------|--------|
| `config/dependency-rules.json` | N/A | - | Add workflow to `allowed_dependencies` and `entity_description` |
| `src/entities.py` | `add_dependency()` | 200-222 | Add position parameter for ordered insertion |
| `src/graph.py` | `_diff_graphs()` | 85-111 | Detect reordering for ordered deps (currently uses sets) |
| `src/graph.py` | `build_nx_graph()` | 178-183 | Preserve order metadata in NetworkX edges |
| `src/validation.py` | Various | 438, 648, 675 | Validate `depends_on_ordered` field exists and is valid |
| `know.py` | `link()` | 1397-1414 | Add `--position` flag for ordered linking |
| `src/visualizers/base.py` | Rendering | 93 | Add visual indicators (numbers) for ordered deps |

**JSON serialization status:**
- ✅ Array order already preserved by `json.load()` and `json.dump()`
- ✅ In-memory list operations preserve order
- ❌ Diff detection uses sets (loses order) - line 110-111 in graph.py
- ❌ System doesn't recognize order as semantically meaningful

### 5. Validation Architecture

**Multi-layer validation:** `know/src/validation.py`

| Method | Speed | Checks |
|--------|-------|--------|
| `validate_syntax()` | ~ms | Structure, format, key format |
| `validate_structure()` | ~50ms | Schema, relationships, orphans |
| `validate_semantics()` | ~200ms | Dependencies, cycles, conventions |
| `validate_full()` | Combined | All layers |

**Validation points:**
- Line 86-118: `validate_all()` - entry point
- Line 160-196: `validate_graph()` - dependency rules
- Line 222-229: `detect_cycles()` - circular dependencies
- Line 460-502: `_validate_orphaned_nodes()` - orphan detection

### 6. Entity Operations in CLI

**File:** `know/know.py`

**Commands:**
- `add` (155-234): Auto-detects entity vs reference
- `link` (1393-1414): Calls `entities.add_dependency()`
- `unlink` (1417-1445): Calls `entities.remove_dependency()`
- `get` (394-438): Retrieves entity or reference
- `list` (444-...): Lists all or filtered entities
- `graph` group (1385-...): Subcommands for traversal and validation

**Auto-detection logic (lines 206-231):**
```python
if category == 'entity':
    entities.add_entity(type_name, key, item_data)
else:  # reference
    graph_data['references'][type_name][key] = item_data
```

### 7. Critical Constraints

**Entities-only fields:** `know/src/validation.py` lines 395-414
- Entities restricted to: `name`, `description`, `allowed_metadata` fields
- Relationships MUST be in graph section's `depends_on`
- NEVER add relationship fields to entity data

**Graph mutation safety:**
- All writes via `cache.write()` with atomic rename
- Diff appended to `.ai/know/diff-graph.jsonl`
- NetworkX graph invalidated on each save

### 8. Reference Bypass Rule

**ANY entity can depend on ANY reference type**

References in `reference_description` skip dependency validation:
```python
# Line 185-186 in dependencies.py
if dep_type in self.reference_description:
    continue  # Skip validation
```

This means:
- `feature:auth → business_logic:login-rules` (valid)
- `action:export → data-model:user-schema` (valid)
- No need to add workflow→reference rules

### 9. Existing Workflow in Meta

**Current state:** `dependency-rules.json` lines 234-242

```json
"meta_description": {
  "workflow": "Collections of operations that form complete processes"
},
"meta_schema": {
  "workflow": {
    "type": "array",
    "description": "Workflow definitions",
    "items": {...}
  }
}
```

**This is meta-level workflow (project metadata), NOT entity-level.**

### 10. Implementation Strategy

**Phase 1: Update Rules**
1. Add workflow to `entity_description`
2. Add workflow to `allowed_dependencies`:
   - `feature → workflow`
   - `workflow → action`

**Phase 2: Add `depends_on_ordered` Field**
1. Update graph structure to support `depends_on_ordered: string[]`
2. Validation for `depends_on_ordered` field
3. EntityManager: position-aware insertion

**Phase 3: CLI Commands**
1. `know add workflow <key>` - auto-works (entity type detection)
2. `know link workflow:X action:a action:b` - add position support
3. `know graph down workflow:X` - show ordered list

**Phase 4: Diff & Visualization**
1. Detect reordering as change (not just set diff)
2. Visual indicators for ordered dependencies

## Files Requiring Changes

| Priority | File | Changes |
|----------|------|---------|
| P0 | `config/dependency-rules.json` | Add workflow entity type and allowed deps |
| P0 | `src/validation.py` | Validate `depends_on_ordered` field |
| P1 | `src/entities.py` | Position-aware `add_dependency()` |
| P1 | `src/graph.py` | Order-aware diff detection |
| P2 | `know.py` | Add `--position` flag to link command |
| P2 | `src/visualizers/base.py` | Visual indicators for ordered deps |
| P3 | `CLAUDE.md` | Document workflow hierarchy |

## Open Questions

1. **Diff detection:** Should reordering `[a,b,c]` → `[b,a,c]` create a diff entry?
2. **NetworkX metadata:** Store order as edge attributes or rely on iteration order?
3. **CLI UX:** Is `--position N` better than `--after action:X`?
4. **Validation:** Should empty `depends_on_ordered: []` be valid?
5. **Mixed mode:** Can same entity have both `depends_on` and `depends_on_ordered`?
