# Codebase Exploration: Spec Generation Implementation

**Date**: 2025-12-22
**Phase**: 1 - Discover

---

## Executive Summary

The spec generation system in know-cli uses a **3-tier architecture**:
1. **Entities** - Lightweight nodes (name + description) representing concepts
2. **References** - Reusable, cross-referenceable content (schemas, rules, configs)
3. **Graph** - Dependencies linking entities and references
4. **Meta** - Project-level metadata (phases, decisions, feature_specs)

The proposed enrichment leverages the existing `meta.feature_specs` structure (already present but underutilized) and adds 4 new reference types to support richer spec generation.

---

## Key Files and Roles

### Core Generation Logic

**`/workspace/know-cli/know/src/generators.py`** (474 lines)
- Main `SpecGenerator` class with 7 generation methods
- `generate_feature_spec()` (lines 89-164) - **Primary target for enhancement**
- `generate_entity_spec()` (lines 26-87) - Generic entity rendering
- Other generators: interface_spec, component_spec, dependency_report, sitemap, user_flow

**`/workspace/know-cli/know/know.py`** (2,000+ lines)
- CLI command `spec` at line 1543
- CLI command `feature-spec` at line 486
- Routes to generators with format/output options

**`/workspace/know-cli/know/templates/spec.md`**
- Template for spec output formatting
- Uses Jinja2-style placeholders

### Configuration & Rules

**`/workspace/know-cli/know/config/dependency-rules.json`**
- **43 reference types** already defined
- Full meta schema including `feature_specs` structure (lines 100-202)
- Entity types: user, objective, feature, component, action, operation, requirement, interface, project
- Reference descriptions and allowed dependencies

**`/workspace/know-cli/know/config/code-dependency-rules.json`**
- Separate schema for code-graph.json
- 17 reference types for code architecture
- Links to product components via `product-component` reference

### Supporting Modules

**`/workspace/know-cli/know/src/entities.py`** (300+ lines)
- `GraphManager` class for entity CRUD operations
- Entity validation and field checking
- Graph manipulation methods

**`/workspace/know-cli/know/src/reference_tools.py`**
- Reference management and usage tracking
- Query references by type
- Find reference usage across graph

**`/workspace/know-cli/know/src/dependencies.py`**
- Dependency graph traversal
- Topological sorting
- Cycle detection
- Used-by queries

**`/workspace/know-cli/know/src/validation.py`**
- Graph structure validation
- Entity field validation
- Reference integrity checks
- Soft vs hard validation modes

---

## Current Reference Types (43 total)

### Design System (10 types)
- `style`, `color`, `layout`, `pattern`, `spacing`, `typography`
- `breakpoint`, `z-index`, `transition`, `asset`

### Business Layer (6 types)
- `business_logic`, `acceptance_criterion`, `state_mutation`
- `event`, `constraint`, `terminology`

### API & Data (7 types)
- `endpoint`, `api_contract`, `validation_rule`, `data-model`
- `error_state`, `performance_spec`, `default`

### Code References (5 types)
- `source-file` - Links to actual source code
- `external-dep` - npm/pip packages
- `api-surface` - Public APIs
- `product-component` - Links code modules to spec components
- `code-module` - Code organization units

### System & Infrastructure (7 types)
- `technical_architecture`, `library`, `protocol`, `platform`
- `configuration`, `metric`, `notification`

### Execution Tracing (6 types)
- `execution-trace`, `call-graph`, `control-flow`
- `data-flow`, `side-effect`, `error-path`

### Other (2 types)
- `content`, `label`

---

## Current Meta Schema

The meta section already supports:

### Phases Tracking
```json
"phases": {
  "pending": {
    "feature:X": { "status": "incomplete" }
  },
  "review-ready": {
    "feature:Y": { "status": "complete" }
  }
}
```

### Feature Specs (EXISTS BUT UNDERUTILIZED!)
```json
"feature_specs": {
  "graph-embeddings": {
    "status": "planned",
    "use_cases": [],
    "testing": {},
    "security": [],
    "monitoring": [],
    "performance": {}
  }
}
```

**Key Insight**: The `feature_specs` structure already exists in the schema and even has an example entry for graph-embeddings! Our task is to:
1. Fully document the schema in dependency-rules.json
2. Enhance the generator to USE this existing structure
3. Add validation for the schema
4. Create comprehensive examples

### Other Meta Types
- `workflow` - Process definitions
- `assumption` - Technical and business assumptions
- `decision` - Architecture decisions with rationale
- `qa_session` - Q&A refinement rounds
- `out_of_scope` - Explicitly excluded features
- `deployment` - Feature deployment status
- `project` - High-level project info

---

## Current Generator Workflow

### `generate_feature_spec()` Current Implementation (lines 89-164)

```python
def generate_feature_spec(self, feature_id: str) -> str:
    """Generate feature specification."""

    # 1. Get feature entity
    feature = self.entities.get(feature_id)

    # 2. Get dependencies and group by type
    deps = self.dependencies.get_dependencies(feature_id)
    actions = [d for d in deps if d.startswith('action:')]
    components = [d for d in deps if d.startswith('component:')]
    references = [d for d in deps if ':' in d and not d.startswith(('action:', 'component:'))]

    # 3. Build spec sections
    output = f"# {feature['name']}\n\n"
    output += feature['description'] + "\n\n"

    # 4. User Actions section
    if actions:
        output += "## User Actions\n"
        for action_id in actions:
            action = self.entities.get(action_id)
            output += f"- {action['name']}: {action['description']}\n"

    # 5. Components section
    if components:
        output += "## Components\n"
        for comp_id in components:
            comp = self.entities.get(comp_id)
            output += f"- {comp['name']}: {comp['description']}\n"

    # 6. References section (generic)
    if references:
        output += "## References\n"
        for ref_id in references:
            # Render each reference type generically
            ...

    return output
```

**Current Limitations:**
- No use of `meta.feature_specs` data
- Generic reference rendering (no type-specific formatting)
- No structured sections for testing, security, monitoring
- No TypeScript rendering for data-models
- No file paths for components

---

## Proposed Enhancements

### New Reference Types to Add (4)

1. **`api-schema`**
   - TypeScript interface definitions for public APIs
   - Structure: `{name, description, methods: [{name, signature, description}]}`
   - Use: Document public API surfaces

2. **`signature`**
   - Function/method signatures with params and returns
   - Structure: `{name, params: [{name, type}], returns}`
   - Use: Link operations to implementation signatures

3. **`test-spec`**
   - Reusable test specifications
   - Structure: `{name, type: unit|integration|e2e, requirements: []}`
   - Use: Cross-reference test requirements across features

4. **`security-spec`**
   - Reusable security requirements
   - Structure: `{name, description, applies_to: []}`
   - Use: Apply same security requirement to multiple components

### Enhanced Generator Logic

**New helper methods needed:**
```python
def _get_feature_spec_meta(self, feature_name: str) -> dict:
    """Get feature-specific meta from meta.feature_specs."""

def _render_data_model_typescript(self, model_data: dict) -> str:
    """Render a data-model reference as TypeScript interface."""

def _render_signature(self, sig_data: dict) -> str:
    """Render a signature reference as function signature."""

def _get_component_file(self, component_id: str) -> str:
    """Get source file path from source-file reference."""

def _get_component_operations(self, component_id: str) -> list:
    """Get operations linked to a component via graph."""
```

**Enhanced `generate_feature_spec()` output:**
1. Header + Description (existing)
2. **Status/Phase/Priority** from meta.feature_specs (NEW)
3. Dependencies on other features (existing)
4. **Components with file paths and operations** (ENHANCED)
5. **Interfaces section with api-schema rendering** (NEW)
6. **Data Models as TypeScript interfaces** (NEW)
7. **Business Logic narrative** (ENHANCED)
8. **Use Cases table** (NEW)
9. **Testing Requirements** (unit/integration/performance) (NEW)
10. **Security & Privacy** (NEW)
11. **Monitoring & Observability** (NEW)
12. **Performance Characteristics** (NEW)

---

## Similar Features Analysis

### 1. Beads Integration (✅ Completed, 2025-12-19)

**Location**: `/workspace/know-cli/know/src/tasks/`
**Size**: 1,215 LOC across 5 modules

**Pattern**: Reference-Based Storage
- Added `task` reference type for native tasks
- Added `beads` reference type for Beads CLI tasks
- Used JSONL for storage (`.ai/tasks/tasks.jsonl`)
- Manager classes handle CRUD operations
- Sync logic updates spec-graph references section

**Key Files**:
- `beads_bridge.py` (270 LOC) - Beads CLI wrapper
- `task_manager.py` (300 LOC) - Native task CRUD
- `task_sync.py` (320 LOC) - Sync to spec-graph
- `interfaces.py` (85 LOC) - Abstract base classes
- CLI commands in `know.py` (lines 2085-2280)

**Lessons**:
- References are terminal nodes (no outgoing dependencies)
- Flat schema works well for simple key-value data
- Manager pattern provides clean abstraction
- Sync operations keep graph and storage aligned

### 2. Schema-Agnostic Know (📋 Pending)

**Pattern**: Schema Loader Abstraction
- Supports custom LLM-generated schemas for different domains
- Loads schema from JSON files referenced in meta.schema_path
- Validates entities against custom schemas
- Falls back to default rules if no custom schema

**Relevance**:
- Shows how to extend meta section with new fields
- Demonstrates schema validation abstraction
- Pattern for handling multiple schema formats

### 3. Existing meta.feature_specs

**Already in spec-graph.json!**
```json
"meta": {
  "feature_specs": {
    "graph-embeddings": {
      "status": "planned",
      "use_cases": [],
      "testing": {},
      "security": [],
      "monitoring": [],
      "performance": {}
    }
  }
}
```

**Key Insight**: The structure exists but:
- Not fully documented in dependency-rules.json
- Not used by generators
- No validation
- Only one example (graph-embeddings)

---

## Data Flow Architecture

### Layer Stack

```
┌─────────────────────────────────────┐
│ 1. CLI Input (know.py)              │
│    - Parse arguments                │
│    - Route to commands               │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│ 2. Manager Layer                    │
│    - EntityManager, DependencyMgr   │
│    - ReferenceTools, TaskManager    │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│ 3. Data Storage                     │
│    - .ai/know/spec-graph.json            │
│    - .ai/know/code-graph.json            │
│    - .ai/tasks/tasks.jsonl          │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│ 4. GraphManager (entities.py)       │
│    - Load/save graph JSON           │
│    - Entity CRUD operations         │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│ 5. Graph Sections                   │
│    - entities: {...}                │
│    - references: {...}              │
│    - graph: {...}                   │
│    - meta: {...}                    │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│ 6. Generators (generators.py)       │
│    - generate_feature_spec()        │
│    - generate_entity_spec()         │
│    - Markdown/JSON output           │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│ 7. Validators (validation.py)       │
│    - Structure validation           │
│    - Reference integrity            │
│    - Entity field checking          │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│ 8. Output                           │
│    - Markdown file                  │
│    - JSON file                      │
│    - Console display                │
└─────────────────────────────────────┘
```

### Query Path Example

**User runs**: `know spec feature:ensemble-meshes`

1. CLI (`know.py:1543`) parses arguments
2. Loads graph via `GraphManager.load()`
3. Calls `SpecGenerator.generate_feature_spec('feature:ensemble-meshes')`
4. Generator:
   - Loads feature entity from `entities.feature.ensemble-meshes`
   - Queries dependencies via `graph['feature:ensemble-meshes'].depends_on`
   - Loads referenced entities (components, actions)
   - Loads referenced references (data-models, signatures)
   - Queries `meta.feature_specs.ensemble-meshes` (NEW)
5. Renders markdown sections
6. Validates output structure
7. Returns formatted markdown

---

## Design Principles (from analysis)

1. **References are Terminal Nodes**
   - References have no outgoing dependencies
   - Any entity can depend on any reference
   - References bypass entity-to-entity rules

2. **Flat Schema for References**
   - Avoid deep nesting in reference schemas
   - Prefer arrays of simple objects over nested hierarchies
   - Makes querying and rendering simpler

3. **Separation of Concerns**
   - **Entities**: Concepts with relationships (validated structure)
   - **References**: Reusable content (flexible schema)
   - **Graph**: Relationships only (validated dependencies)
   - **Meta**: Project metadata (unvalidated, flexible)

4. **Explicit Linking Required**
   - Entity → reference links must be in graph section
   - No implicit references
   - Enables graph queries and validation

5. **Graceful Degradation**
   - Generators handle missing data
   - Validation warns but doesn't fail
   - Legacy features work without updates

---

## Code Conventions

### Naming
- Entities: `kebab-case` (e.g., `feature:schema-agnostic-know`)
- References: `kebab-case` (e.g., `data-model:fork-result`)
- File paths: `snake_case.py` or `kebab-case.md`

### Entity Structure
```json
{
  "name": "Human Readable Name",
  "description": "Detailed description...",
  "status": "optional-status",
  "tags": [],
  "metadata": {},
  "notes": ""
}
```

### Reference Structure (varies by type)
```json
{
  "key-name": {
    "field1": "value",
    "field2": ["list"],
    "field3": {"nested": "object"}
  }
}
```

### Graph Dependencies
```json
{
  "entity-id": {
    "depends_on": [
      "other-entity:id",
      "reference-type:key"
    ]
  }
}
```

---

## Testing Strategy (from beads-integration)

**Manual Testing Focus**:
- End-to-end workflow tests
- Integration with actual tools (bd CLI)
- Runtime behavior validation

**No Unit Tests** (current project convention):
- MVP scope prioritizes functionality over test coverage
- Acceptance testing validates behavior
- Future: Add pytest tests for core functions

---

## Performance Considerations

**Graph Size**: Current spec-graph.json is ~65 entities
- O(n) for most operations (linear scan)
- No performance concerns at current scale
- Could optimize with indexing if graph grows >1000 entities

**Generator Performance**:
- Lazy loading of related entities
- Single graph load at start
- No caching (fresh data each run)
- Fast enough for CLI usage (<100ms)

---

## Next Steps for Implementation

1. **Schema Updates** (Phase 3-4)
   - Add 4 new reference types to dependency-rules.json
   - Document meta.feature_specs schema structure
   - Add reference_description entries

2. **Generator Enhancement** (Phase 4)
   - Add helper methods for metadata extraction
   - Implement TypeScript rendering
   - Add new output sections
   - Implement graceful degradation

3. **Validation Updates** (Phase 4)
   - Add soft warnings for recommended references
   - Validate meta.feature_specs structure
   - Check signature/data-model completeness

4. **Example Creation** (Phase 4-5)
   - Enhance existing feature (graph-embeddings) with full metadata
   - Document the enhancement process
   - Generate rich spec to demonstrate capabilities

5. **Documentation** (Phase 5)
   - Update README with new reference types
   - Document meta.feature_specs usage
   - Provide migration guide for existing features
