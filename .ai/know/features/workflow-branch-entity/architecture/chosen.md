# Chosen Architecture: Pragmatic Balanced Approach

**Selected:** Pragmatic Balanced
**Effort:** 8 hours
**Risk:** Low
**Grade:** B+

## Architecture Overview

```
know.py (CLI)
  ↓ delegates to
workflow.py (NEW - workflow operations)
  ↓ uses
entities.py (reuse - CRUD)
graph.py (extend - edge attributes + diff)
validation.py (extend - ordered deps validation)
dependencies.py (extend - workflow→action rule)
```

## Key Design Decisions

### 1. New `workflow.py` Module

**Single-purpose module** for workflow operations:
- `WorkflowManager` class
- `add_workflow()`, `link_actions()`, `unlink_actions()`, `delete_workflow()`
- Position-based insertion (`--position`, `--after`)
- Auto-create missing actions (opt-in)

**Rationale:** Clean separation without over-abstraction.

### 2. NetworkX Edge Attributes

**Store order as edge data:**
```python
graph.add_edge(
    "workflow:onboarding",
    "action:signup",
    order=0
)
```

**Rationale:** NetworkX native support, no new data structures.

### 3. Extend Existing Validators

**Add to existing validation.py:**
- Check `depends_on_ordered` format (must be array)
- Enforce workflow-only ordering

**Rationale:** Reuse infrastructure, minimal LOC.

### 4. CLI Pattern Reuse

**Add flags to existing commands:**
- `know link workflow:X action:a action:b --position N`
- `know link workflow:X action:y --after action:z`
- `know delete workflow:X -y`

**Rationale:** Consistent UX, no new verb learning.

### 5. Mixed Mode Allowed

**Both fields on same node:**
```json
"graph": {
  "workflow:onboarding": {
    "depends_on": ["component:logger"],  // unordered
    "depends_on_ordered": ["action:a", "action:b"]  // ordered
  }
}
```

**Rationale:** Flexibility for complex workflows (ordered actions + utility components).

## File Changes

| Priority | File | Changes | Lines |
|----------|------|---------|-------|
| P0 | `config/dependency-rules.json` | Add workflow entity type | +2 |
| P0 | `src/workflow.py` | NEW - WorkflowManager class | +150 |
| P1 | `src/graph.py` | Edge attributes, diff tracking | +30 |
| P1 | `src/entities.py` | Batch add with auto-create | +40 |
| P2 | `src/validation.py` | Ordered deps validation | +20 |
| P2 | `src/dependencies.py` | Workflow-only ordering rule | +10 |
| P2 | `know.py` | CLI commands and flags | +50 |

**Total:** ~300 LOC

## Implementation Checklist

### Phase 1: Config (0.5h)
- [ ] Edit `know/config/dependency-rules.json`
  - Add `"workflow": ["action"]` to `allowed_dependencies`
  - Add workflow to `entity_description`
  - Add `execution_order` to allowed metadata

### Phase 2: Core (3h)
- [ ] Modify `know/src/graph.py`
  - Update `build_nx_graph()` to store edge order attributes (lines 178-183)
  - Update `extract_links()` for ordered diff tracking (lines 85-91)
  - Test: NetworkX graph has `order` attribute on workflow edges
- [ ] Modify `know/src/entities.py`
  - Add `add_entities_batch()` method with auto-create flag
  - Test: Batch add 3 entities in one save operation

### Phase 3: New Module (2h)
- [ ] Create `know/src/workflow.py`
  - Implement `WorkflowManager` class
  - Methods: add_workflow, link_actions, unlink_actions, delete_workflow
  - Test: Link 3 actions in order, verify depends_on_ordered

### Phase 4: Validation (1h)
- [ ] Extend `know/src/validation.py`
  - Validate `depends_on_ordered` is array type
  - Add check after line 568
- [ ] Extend `know/src/dependencies.py`
  - Validate only workflows have ordered deps
  - Add check in validate_graph (~line 160)

### Phase 5: CLI (1.5h)
- [ ] Add commands to `know/know.py`
  - `know add workflow <key>` command
  - Add `--position N` flag to link
  - Add `--after ACTION` flag to link
  - Add `--auto-create` flag to link
  - Add `-y` flag to delete (workflow-specific)
- [ ] Update help text and examples

## Validation Rules

### Workflow Entity Rules
1. Workflow can only depend on actions (enforced in dependency-rules.json)
2. Workflows must use `depends_on_ordered` (not required, but recommended)
3. Only workflow entities can have `depends_on_ordered` field

### Ordered Dependency Rules
1. `depends_on_ordered` must be an array
2. All referenced actions must exist (or auto-created if flag set)
3. Duplicate actions allowed (same action can appear multiple times)
4. Empty array allowed (workflow with zero actions is valid)
5. Position must be >= 0 and <= current length

## Error Messages

**Circular dependency:**
```
✗ Circular dependency detected:
  workflow:onboarding → action:setup → workflow:onboarding

  Fix: Remove one of these links to break the cycle
```

**Invalid dependency type:**
```
✗ Invalid dependency: workflow:onboarding → component:form
  workflow can only depend on: action

  Fix: know unlink workflow:onboarding component:form
```

**Malformed field:**
```
✗ Node workflow:onboarding has invalid depends_on_ordered type (expected list)
  Found: "action:login" (string)

  Fix: Use array format: ["action:login"]
```

**Non-workflow ordered deps:**
```
✗ feature:auth cannot have depends_on_ordered (only workflow entities)

  Fix: Remove depends_on_ordered or convert to workflow entity
```

## Testing Strategy

**Manual tests saved to `.ai/know/features/workflow-branch-entity/HUMAN_REVIEW.md`:**
- Basic creation (add workflow entity)
- Link actions (append, position, after)
- Auto-create missing actions
- Unlink actions
- Delete workflow (-y flag)
- Validation (only workflows have ordered deps)
- Diff tracking (reordering generates diffs)

**Integration points:**
- [ ] `know graph down workflow:X` shows ordered actions
- [ ] `know graph up action:Y` includes workflows
- [ ] `know validate` checks workflow rules
- [ ] `know list --type workflow` lists all workflows
- [ ] `know get workflow:X` retrieves workflow entity

## Migration Path

**Backward compatibility:** 100%
- Existing graphs work unchanged
- `depends_on` still works for all entities
- `depends_on_ordered` is additive
- No migration script needed

**Future workflows:**
- Gradual adoption (features can keep using direct action deps)
- No forced migration
- Mixed mode allows incremental conversion

## Extension Points

**Future enhancements can add:**
1. Workflow templates (reusable sequences)
2. Conditional branching (if/else in workflows)
3. Parallel execution (fork/join)
4. Workflow execution tracking (state machine)
5. Workflow versioning (v1, v2, etc.)

**Clean extension path:**
- Add new entity types (workflow-template)
- Add new dependency types (conditional-dep)
- Add new metadata fields (execution-state)
- No refactoring of core workflow logic

## Trade-offs Accepted

| Trade-off | Mitigation |
|-----------|------------|
| Mixed mode might confuse users | Validation warns when both fields present |
| Auto-create could create noise | Opt-in flag (default off) |
| Position diffs can be noisy | Acceptable for audit trail completeness |
| No workflow-specific viz | Use existing visualizers, future enhancement |

## Approval Needed

**Ready to implement?** This architecture:
- ✅ 8 hours implementation time
- ✅ ~300 LOC (reasonable scope)
- ✅ Reuses existing patterns
- ✅ Zero breaking changes
- ✅ Testable in isolation
- ✅ Extensible for future features

**Next:** Phase 5 (Implementation) upon approval.
