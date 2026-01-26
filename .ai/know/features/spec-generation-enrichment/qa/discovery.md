# Discovery Q&A: Spec Generation Enrichment

**Date**: 2025-12-22
**Phase**: 1 - Discover

---

## Success Criteria

**Q: What is the success criteria for this feature? When should we consider it complete?**

A: The feature is complete when ALL of the following are achieved:

1. ✅ **Schema updates complete**
   - New reference types added to dependency-rules.json:
     - `api-schema` - TypeScript interface definitions for public APIs
     - `signature` - Function/method signatures with params and returns
     - `test-spec` - Reusable test specifications
     - `security-spec` - Reusable security requirements

2. ✅ **Meta schema extended**
   - `meta.feature_specs` structure fully documented in dependency-rules.json
   - Schema includes: status, phase, priority, use_cases, testing, security, monitoring, performance

3. ✅ **Generator enhanced**
   - `generate_feature_spec()` produces rich output with all new sections:
     - Status/Phase/Priority from meta.feature_specs
     - Components with file paths (from source-file references)
     - Operations with signatures
     - Data Models as TypeScript interfaces
     - Business Logic narrativeUse Cases table
     - Testing Requirements (unit/integration/performance)
     - Security & Privacy
     - Monitoring & Observability
     - Performance characteristics

4. ✅ **Example working**
   - Can generate full spec for an existing feature using the new structure
   - Example chosen: Enhance existing feature (graph-embeddings) with new metadata

5. ✅ **Works comprehensively for all entities**
   - All entity types can benefit from the new reference types
   - System works with partial data (graceful degradation)

---

## Backward Compatibility

**Q: Should the feature be backward compatible with existing specs that don't have the new metadata?**

A: **Yes, graceful degradation (Recommended)**

- Generator outputs "Not specified" or omits sections when metadata is missing
- Existing graphs continue to work without any changes
- New reference types and meta sections are additive, not required
- This ensures smooth migration path for existing features

---

## Validation Strategy

**Q: What validation level should we enforce for the new reference types?**

A: **Soft warnings (Recommended)**

- Warn if signatures/data-models are expected but missing
- Allow proceeding even with incomplete metadata
- Validation hints should be helpful, not blocking
- Example: "Component 'X' has operations but no source-file reference"

**Implementation approach:**
- Add soft validation rules that suggest improvements
- Do NOT fail validation for missing optional metadata
- Focus on data integrity (required fields) vs completeness (nice-to-have)

---

## Example Strategy

**Q: Should we create an example feature in spec-graph.json to demonstrate the new structure?**

A: **Use existing feature**

- Enhance an existing feature (like `graph-embeddings`) with the new metadata
- This demonstrates real-world usage rather than hypothetical examples
- Keeps spec-graph.json aligned with actual project features
- Can add more comprehensive examples in separate documentation

**Rationale:**
- More valuable to show how existing features benefit from enrichment
- Avoids cluttering spec-graph with demo/example features
- Provides immediate value to current project

---

## Codebase Context

### Current State (from exploration)

**Key Files:**
- `know/src/generators.py` - 7 generator methods, ~474 lines
- `know/config/dependency-rules.json` - 43 reference types, full meta schema
- `know/know.py` - CLI commands at line 486 (feature_spec), 1543 (spec)
- `know/templates/spec.md` - Template for spec output

**Current Reference Types (43):**
- Design: style, color, layout, pattern, spacing, typography, etc.
- Business: business_logic, acceptance_criterion, constraint, terminology
- API: endpoint, api_contract, validation_rule, data-model
- Code: source-file, external-dep, api-surface, product-component
- System: technical_architecture, library, protocol, configuration
- Execution: execution-trace, call-graph, control-flow, error-path

**Current Meta Schema:**
- Phases with status tracking
- Feature specs structure (already exists but underutilized!)
- Workflow, assumptions, qa_session, decision structures

### Similar Features Analyzed

1. **Beads Integration** (✅ Completed)
   - Added `task` and `beads` reference types
   - Pattern: Reference-based key-value storage
   - 1,215 LOC in `know/src/tasks/`

2. **Schema-Agnostic Know** (📋 Pending)
   - Custom schema support for different domains
   - Pattern: Schema loader abstraction

### Data Flow Architecture

```
CLI Input
  ↓
Manager Layer (BeadsBridge, TaskManager, etc.)
  ↓
Data Storage (.jsonl, .json files)
  ↓
GraphManager (entities.py, dependencies.py)
  ↓
Graph Sections (entities, references, graph, meta)
  ↓
Generators (generators.py)
  ↓
Validators (validation.py)
  ↓
Output (markdown/JSON)
```

---

## Constraints & Non-Goals

**Constraints:**
- Must maintain backward compatibility (graceful degradation)
- Must not break existing validation
- Must not require changes to existing features (optional enrichment)
- Soft validation only (warnings, not errors)

**Out of Scope:**
- Auto-population of metadata from code analysis
- Interactive metadata editors
- Versioning/migration tools for meta.feature_specs
- Hard enforcement of new reference types

**Edge Cases to Consider:**
1. Empty/minimal features with no metadata
2. Partial metadata (some sections present, others missing)
3. Legacy features never updated with new structure
4. Mixed usage (some features enriched, others not)

---

## Next Steps

**Phase 2: Clarify** - Resolve remaining ambiguities:
1. Exact schema structure for each new reference type
2. Generator output format for each new section
3. TypeScript rendering conventions
4. Which existing feature to enhance as example
5. Validation warning messages and thresholds

**Phase 3: Architect** - Design approach:
1. Minimal changes vs comprehensive enhancement
2. Trade-offs between complexity and richness
3. Migration path for existing features
4. ADR documenting architectural decisions
