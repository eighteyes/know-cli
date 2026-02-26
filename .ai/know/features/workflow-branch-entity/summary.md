# Summary: workflow-branch-entity

**Status:** ✅ Complete
**Date:** 2026-02-20
**Effort:** 8 hours (estimated and actual)

## What Was Built

Added `workflow` entity type to know CLI spec-graph, enabling ordered action sequences that implement features.

### Key Features

1. **Workflow Entity Type**
   - New entity: `workflow` (peer to `feature`, `action`, etc.)
   - Dependencies: `feature → workflow`, `workflow → action`
   - Fully integrated with existing entity CRUD

2. **Ordered Dependencies**
   - New field: `depends_on_ordered: string[]` in graph section
   - Array order is semantically significant
   - Stored as NetworkX edge attributes
   - Diff tracking captures reordering

3. **CLI Commands**
   - `know add workflow <key>` - create workflow
   - `know link workflow:X action:a action:b` - ordered linking
   - `--position N` - insert at index
   - `--after ACTION` - insert after action
   - `--auto-create` - create missing actions with minimal data
   - `know unlink workflow:X action:Y -y` - remove actions
   - `know nodes delete workflow:X -y` - delete workflow

4. **Validation**
   - Only workflows can have `depends_on_ordered`
   - All actions in ordered list must exist (or auto-created)
   - Circular dependency detection works across both ordered/unordered
   - Format validation for `depends_on_ordered` field

5. **Mixed Mode**
   - Workflows can have both `depends_on` and `depends_on_ordered`
   - Example: ordered actions + unordered utility components

## Files Modified

| File | Changes | LOC |
|------|---------|-----|
| `know/config/dependency-rules.json` | Added workflow entity type and rules | +3 |
| `know/src/graph.py` | NetworkX edge attributes, diff tracking | +30 |
| `know/src/entities.py` | Batch add with auto-create | +65 |
| `know/src/workflow.py` | WorkflowManager class (NEW) | +197 |
| `know/src/validation.py` | depends_on_ordered format checks | +12 |
| `know/src/dependencies.py` | Workflow-only enforcement | +25 |
| `know/know.py` | CLI integration (link/unlink flags) | +55 |
| **Total** | | **~387** |

## Architecture Decisions

**Chosen:** Pragmatic Balanced Approach
- New `workflow.py` module for single-purpose workflow operations
- NetworkX edge attributes for order (native support)
- Extend existing validators (don't replace)
- CLI pattern reuse (add flags, not new commands)
- Zero breaking changes

## Testing

**Manual tests completed:**
- ✅ Workflow entity creation
- ✅ Ordered action linking
- ✅ Position-based insertion
- ✅ Insert-after semantics
- ✅ Auto-create missing actions
- ✅ Unlink actions
- ✅ Delete workflow
- ✅ Validation enforcement
- ✅ Diff tracking
- ✅ Graph structure correctness

**Validation:**
- All graph validations pass
- Backward compatibility: 100%
- Existing graphs work unchanged

## Example Usage

```bash
# Create workflow
know add workflow onboarding-flow \\
  '{"name":"User Onboarding","description":"Complete signup process"}'

# Link actions in order
know link workflow:onboarding-flow \\
  action:create-account \\
  action:verify-email \\
  action:setup-profile \\
  --auto-create

# Insert action at position
know link workflow:onboarding-flow action:welcome-email --position 1

# Insert after specific action
know link workflow:onboarding-flow action:tour --after action:setup-profile

# View ordered actions
know graph down workflow:onboarding-flow

# Unlink action
know unlink workflow:onboarding-flow action:tour -y

# Delete workflow
know nodes delete workflow:onboarding-flow -y
```

## Graph Structure

```json
{
  "entities": {
    "workflow": {
      "onboarding-flow": {
        "name": "User Onboarding",
        "description": "Complete signup process"
      }
    }
  },
  "graph": {
    "feature:user-registration": {
      "depends_on": ["workflow:onboarding-flow"]
    },
    "workflow:onboarding-flow": {
      "depends_on_ordered": [
        "action:create-account",
        "action:welcome-email",
        "action:verify-email",
        "action:setup-profile",
        "action:tour"
      ]
    }
  }
}
```

## Benefits

- ✅ **Ordered workflows:** Action sequences have meaningful order
- ✅ **Reusable actions:** Same action can appear in multiple workflows
- ✅ **Mixed mode:** Workflows can have ordered + unordered dependencies
- ✅ **Auto-create:** Rapid workflow prototyping
- ✅ **Explicit ordering:** `depends_on_ordered` clearly signals intent
- ✅ **Diff tracking:** Reordering captured in audit trail
- ✅ **Backward compatible:** No migration needed

## Next Steps

Feature is complete and ready for use. Recommended follow-ups:

1. **Documentation:** Update CLAUDE.md with workflow hierarchy examples
2. **Cross-graph linking:** Add workflow.py modules to code-graph
3. **Visualization:** Add workflow-specific rendering (swimlane view)
4. **Advanced features** (future):
   - Workflow templates (reusable sequences)
   - Conditional branching (if/else in workflows)
   - Parallel execution (fork/join)
   - Workflow state tracking

## Completion Checklist

- [x] Config updated (dependency-rules.json)
- [x] Core implementation (graph.py, entities.py)
- [x] Workflow module created (workflow.py)
- [x] Validation extended
- [x] CLI integrated
- [x] Manual testing complete
- [x] Documentation written (overview, implementation, summary)
- [x] Todo updated
- [x] Test data cleaned up

**Feature complete. Ready for `/know:review` or production use.**
