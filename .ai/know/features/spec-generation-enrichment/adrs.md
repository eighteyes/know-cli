# Architecture Decision Records: Spec Generation Enrichment

**Feature**: spec-generation-enrichment
**Date**: 2025-12-22

---

## ADR-001: Pragmatic Balance Architecture

**Date**: 2025-12-22
**Status**: Accepted

### Context

We need to enhance the spec generation system to support:
- 4 new reference types (api-schema, signature, test-spec, security-spec)
- Rich feature specs using meta.feature_specs
- TypeScript rendering for data models
- Function signature formatting
- Component → operation → signature linking

Three architectural approaches were evaluated:
1. **Minimal Changes** - 43 LOC, 45 min, surgical edits only
2. **Clean Architecture** - 2,700 LOC, 5.5 weeks, full rewrite with patterns
3. **Pragmatic Balance** - 126 LOC, 5.3 hours, focused helpers + inline enhancement

### Decision

**Chose Option 3: Pragmatic Balance**

Implement 5 focused helper methods and enhance `generate_feature_spec()` inline while maintaining existing code patterns.

### Rationale

**Why Pragmatic Balance over Minimal Changes:**
- Minimal changes don't fully leverage meta.feature_specs structure
- Limited extensibility for future enhancements
- Doesn't deliver all success criteria (rich spec generation)
- Helpers would be needed eventually anyway

**Why Pragmatic Balance over Clean Architecture:**
- 5.5 weeks timeline is excessive for current needs
- 2,700 LOC introduces significant complexity
- Over-engineered for single-developer project
- Existing patterns (helper methods, inline rendering) work well
- Can refactor to cleaner architecture later if needed

**Why Pragmatic Balance is optimal:**
- ✅ Delivers all success criteria in 5.3 hours
- ✅ Follows established codebase patterns (`_get_reference_data()` style)
- ✅ Helper methods provide clear extension points
- ✅ Reusable across other generators (component_spec, interface_spec)
- ✅ Non-breaking, backward compatible
- ✅ Easy to test incrementally
- ✅ Code remains maintainable and readable

### Implementation Strategy

#### 1. Configuration Updates (15 min)
- Add 4 reference types to `dependency-rules.json`
- Document meta.feature_specs schema
- Non-breaking additions only

#### 2. Core Helpers (90 min)
Add 5 instance methods to `SpecGenerator` class:

```python
def _get_feature_spec_meta(self, feature_name: str) -> dict:
    """Query meta.feature_specs for a feature."""
    # Returns empty dict if missing (graceful degradation)

def _render_data_model_typescript(self, model_data: dict, model_name: str) -> str:
    """Convert data-model reference to TypeScript interface."""
    # Handles language field, schema object
    # Supports primitives, arrays, unions, optionals

def _render_signature(self, sig_data: dict) -> str:
    """Convert signature reference to readable function signature."""
    # Format: functionName(param1: Type1, param2: Type2): ReturnType
    # Handles missing params/returns gracefully

def _get_component_operations(self, component_id: str) -> list[str]:
    """Query graph for operation entities linked to component."""
    # Returns list of operation IDs: ["operation:x", "operation:y"]

def _get_component_file(self, component_id: str) -> str:
    """Query source-file reference for component."""
    # Returns file path or empty string
```

#### 3. Enhanced generate_feature_spec() (90 min)
Rewrite existing 75-line method to include 11 sections:
1. Header + Description (existing)
2. **Status/Phase/Priority** from meta.feature_specs (NEW)
3. Dependencies (existing, enhanced)
4. **Components with file paths and operations** (ENHANCED)
5. **Interfaces with api-schema rendering** (NEW)
6. **Data Models as TypeScript** (NEW)
7. **Business Logic** (existing, enhanced)
8. **Use Cases** from meta.feature_specs (NEW)
9. **Testing Requirements** from meta.feature_specs (NEW)
10. **Security & Privacy** from meta.feature_specs (NEW)
11. **Monitoring & Observability** from meta.feature_specs (NEW)

### Consequences

**Positive:**
- ✅ Meets all success criteria
- ✅ Delivers in single work session
- ✅ Maintainable by single developer
- ✅ Helper methods reusable
- ✅ Graceful degradation for missing data
- ✅ No breaking changes
- ✅ Can iterate/improve later

**Negative:**
- ⚠️ Some inline rendering logic (not fully abstracted)
- ⚠️ Less extensible than clean architecture
- ⚠️ May need refactoring if requirements expand significantly

**Mitigations:**
- Helper methods provide clear extraction points if refactoring needed
- Inline code follows established, readable patterns
- Can introduce Strategy pattern later if reference types proliferate
- Test coverage ensures safe refactoring in future

### Alternatives Considered

**Alternative 1: Minimal Changes**
- Rejected: Doesn't deliver full feature enrichment
- Rejected: Would need more helpers eventually anyway

**Alternative 2: Clean Architecture**
- Rejected: Timeline too long (5.5 weeks)
- Rejected: Over-engineered for current scope
- Future option: Can migrate to this if extensibility needs grow

**Alternative 3: Hybrid (helpers + strategy pattern)**
- Considered: Add StrategyFactory for reference rendering
- Rejected: Adds complexity without clear benefit for 4 reference types
- Future option: Introduce if reference types exceed ~10

### Success Metrics

**Definition of Done:**
- [ ] 4 new reference types added to dependency-rules.json
- [ ] meta.feature_specs schema fully documented
- [ ] 5 helper methods implemented and tested
- [ ] generate_feature_spec() produces rich output
- [ ] graph-embeddings enhanced with full metadata as example
- [ ] Backward compatible (existing features work unchanged)
- [ ] Soft validation warnings guide users

**Quality Gates:**
- All existing tests pass
- Manual test with graph-embeddings shows rich output
- Validation runs cleanly (no errors, only warnings)
- Code review passes (follows existing patterns)

### Timeline

- **Phase 1: Config** - 15 min
- **Phase 2: Helpers** - 90 min
- **Phase 3: Enhanced Generator** - 90 min
- **Phase 4: Testing** - 60 min
- **Phase 5: Documentation** - 30 min
- **Total**: ~5.3 hours

### Files Modified

1. `/workspace/know-cli/know/config/dependency-rules.json` (+8 LOC)
   - Add reference types array entries
   - Add reference descriptions
   - Document meta.feature_specs schema

2. `/workspace/know-cli/know/src/generators.py` (+118 LOC)
   - Add 5 helper methods (80 lines)
   - Rewrite generate_feature_spec() (38 lines added to existing 75)

**Total Impact**: ~126 LOC added, 0 LOC deleted, 0 refactoring

### Trade-Offs Accepted

| Trade-Off | Decision | Justification |
|-----------|----------|---------------|
| Helper methods vs full abstraction | Helpers | Proven pattern in codebase; sufficient for needs |
| Inline sections vs extracted | Inline | Readable; follows existing generator pattern |
| TypeScript-only vs multi-language | TypeScript + fallback | Covers 90% use case; extensible later |
| Soft vs hard validation | Soft warnings | Supports incremental adoption |
| Manual vs auto-population | Manual | Auto-gen is future enhancement |

### References

- **Existing Patterns**: `_get_reference_data()` at generators.py:369
- **Similar Features**: beads-integration (reference-based storage)
- **Schema Definition**: dependency-rules.json lines 15-202
- **Validation**: validation.py (soft validation precedent)

---

## ADR-002: Use meta.feature_specs for Feature-Level Prose

**Date**: 2025-12-22
**Status**: Accepted

### Context

Feature-specific content like use cases, testing requirements, security needs, and monitoring specs could be stored in:
1. Entity fields (add to feature entity)
2. References (create use-case, test-spec references)
3. Meta section (meta.feature_specs)

### Decision

**Store in meta.feature_specs**

### Rationale

**Why not entity fields:**
- Entities should be lightweight (name + description only)
- Violates separation of concerns (entities = concepts, not details)
- Would require schema changes to entity validation
- Not cross-referenceable

**Why not references:**
- Use cases aren't reusable across features
- Would create reference sprawl (one per use case)
- References are for cross-referenceable content
- Harder to query all metadata for a feature

**Why meta.feature_specs:**
- ✅ Already defined in schema (underutilized, not new)
- ✅ Feature-scoped (all metadata in one place)
- ✅ Flexible schema (can add fields without validation changes)
- ✅ Unvalidated section (soft enforcement matches project philosophy)
- ✅ Easy to query: `meta.feature_specs[feature_name]`
- ✅ Doesn't pollute graph section

### Consequences

**Positive:**
- Clean separation: entities (concepts) vs references (reusable) vs meta (feature prose)
- Easy to access all feature metadata in one query
- Can add new metadata fields without schema changes
- Supports partial metadata (graceful degradation)

**Negative:**
- Meta section is unvalidated (could have typos/inconsistencies)
- Not cross-referenceable (can't link to specific use case)

**Mitigations:**
- Document schema clearly in dependency-rules.json
- Add soft validation hints
- Generators validate structure during rendering

---

## ADR-003: TypeScript-Only for Data Model Rendering (Initial)

**Date**: 2025-12-22
**Status**: Accepted

### Context

Data models could support multiple output languages:
- TypeScript (interfaces)
- Python (dataclasses, Pydantic)
- JSON Schema
- GraphQL
- Go (structs)

### Decision

**Support TypeScript with generic fallback**

Rendering logic:
```python
if model_data.get('language') == 'typescript':
    return _render_data_model_typescript(model_data)
else:
    return str(model_data)  # Generic fallback
```

### Rationale

**Why TypeScript:**
- ✅ Most common in web/API documentation
- ✅ Clear, readable syntax
- ✅ Supports complex types (unions, arrays, optionals)
- ✅ Existing examples in plan.md use TypeScript

**Why not multi-language initially:**
- Each language requires separate rendering logic
- Maintenance burden (keep 5+ renderers in sync)
- Current project is Python/TypeScript focused
- 90% of use cases covered by TypeScript

**Why generic fallback:**
- ✅ Handles unknown languages gracefully
- ✅ Shows raw schema structure (better than nothing)
- ✅ Doesn't block users from adding other languages

### Consequences

**Positive:**
- Simpler implementation (one renderer)
- Clear, consistent output format
- Easy to extend later (add Python renderer when needed)

**Negative:**
- Limited to TypeScript initially
- Generic fallback less readable than native rendering

**Future Extensions:**
- Add `_render_data_model_python()` when Python models needed
- Add `_render_data_model_json_schema()` for API specs
- Strategy pattern if language count exceeds 3

---

## ADR-004: Soft Validation for New Reference Types

**Date**: 2025-12-22
**Status**: Accepted

### Context

We could enforce new reference types with:
1. **Hard validation** - Fail if missing required references
2. **Soft validation** - Warn but allow proceeding
3. **No validation** - Only validate at generation time

### Decision

**Soft validation with actionable warnings**

### Rationale

**Why not hard validation:**
- Breaks existing graphs immediately
- Blocks incremental adoption
- Too strict for optional enrichment

**Why not no validation:**
- Users won't know about new features
- Missed opportunities for rich specs
- No guidance on best practices

**Why soft validation:**
- ✅ Supports incremental adoption
- ✅ Guides users without blocking
- ✅ Provides actionable fix commands
- ✅ Matches project philosophy (warnings over errors)
- ✅ AI-friendly (structured warning messages)

### Warning Examples

```
⚠ Component 'component:X' lacks source-file reference

Suggested fix:
  know -g .ai/spec-graph.json add-ref source-file X '{"path":"src/X.py"}'
  know -g .ai/spec-graph.json link component:X source-file:X
```

### Consequences

**Positive:**
- Non-breaking adoption path
- Users learn about features organically
- Clear guidance on how to improve specs
- AI can parse and apply fixes automatically

**Negative:**
- Optional features might be underutilized
- Some specs remain minimal

**Mitigations:**
- Clear documentation in SKILL.md
- Example specs show full enrichment
- Validation messages educate users

---

## Future ADRs (Placeholders)

### ADR-005: [Future] Add Python Data Model Rendering
**Status**: Deferred
- When: If Python models become common (>10 instances)
- Approach: Add `_render_data_model_python()` helper

### ADR-006: [Future] Extract Reference Rendering to Strategy Pattern
**Status**: Deferred
- When: If reference types exceed 10 or rendering becomes complex
- Approach: Create `BaseReferenceStrategy` with concrete implementations

### ADR-007: [Future] Add Auto-Population from Code Analysis
**Status**: Deferred
- When: If manual metadata becomes bottleneck
- Approach: AST parsing to extract signatures, types

---

## ADR Summary Table

| ID | Title | Status | Impact |
|----|-------|--------|--------|
| ADR-001 | Pragmatic Balance Architecture | Accepted | Core implementation approach |
| ADR-002 | Use meta.feature_specs | Accepted | Data modeling decision |
| ADR-003 | TypeScript-Only Initially | Accepted | Rendering scope |
| ADR-004 | Soft Validation | Accepted | User experience |
| ADR-005 | Python Rendering | Deferred | Future enhancement |
| ADR-006 | Strategy Pattern | Deferred | Future refactoring |
| ADR-007 | Auto-Population | Deferred | Future enhancement |
