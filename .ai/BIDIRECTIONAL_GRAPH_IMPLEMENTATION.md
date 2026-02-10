# Bidirectional Graph Linking Implementation

## Summary

Implemented graph-based feature completion tracking replacing fragile markdown checklists with structural, bidirectional graph linkage between spec-graph and code-graph.

## Key Changes

### 1. Documentation Updates

**CLAUDE.md** - Added bidirectional graph linking section:
- Meta configuration (code_graph_path, spec_graph_path)
- Spec → Code linkage via `implementation` references
- Code → Spec linkage via `graph-link` references
- Feature-level linking (not component/action granularity)
- Many-to-many relationships supported

**Schema**:
```json
// spec-graph.json
{
  "meta": {"code_graph_path": ".ai/code-graph.json"},
  "references": {
    "implementation": {
      "auth-impl": ["graph-link:auth-module", "graph-link:user-service"]
    }
  },
  "graph": {
    "feature:auth": {"depends_on": ["implementation:auth-impl"]}
  }
}

// code-graph.json
{
  "meta": {"spec_graph_path": ".ai/spec-graph.json"},
  "references": {
    "graph-link": {
      "auth-module": {
        "component": "component:auth-handler",
        "feature": "feature:auth"
      }
    }
  }
}
```

### 2. Command Workflow Updates

**`/know:review`** (Revision 3):
- Now calls `know feature review <feature>`
- Validates graph linkage BEFORE QA testing
- Checks:
  - Feature has implementation references
  - Graph-links exist in code-graph
  - Bidirectional consistency
  - QA_STEPS.md exists
- Still handles interactive QA workflow in the skill

**`/know:done`** (Revision 4):
- Now calls `know feature done <feature>`
- Validates completion first
- Checks for review-results.md
- Archives only if validated
- Legacy todo.md check still present but secondary

### 3. CLI Commands Implemented

**`know feature review <feature>`**:
- Validates bidirectional graph linkage
- Checks QA_STEPS.md exists
- Returns validation results
- Can skip validation with --skip-validation flag

**`know feature done <feature>`** (enhanced):
- Validates graph completion first
- Checks review-results.md exists
- Tags commits with git notes
- Updates spec-graph phase
- Archives to .ai/know/archive/
- Can skip todos/archive with flags

**Helper function** `_validate_feature_completion()`:
- Shared validation logic
- Checks implementation references exist
- Validates graph-links in code-graph
- Verifies bidirectional consistency
- Returns structured result with messages

### 4. Validation Logic

The validation performs these checks:

1. **Has implementation references**: Feature has at least one `implementation:*` dependency
2. **References are arrays**: Implementation values are arrays of graph-link IDs
3. **Graph-links exist**: Each graph-link exists in code-graph
4. **Bidirectional consistency**: Graph-links point back to the feature

**Example validation output**:
```
Graph Completion Validation:
  ✓ Feature has 2 implementation reference(s)
  ✓ graph-link:auth-module → feature:auth
  ✓ graph-link:user-service → feature:auth
```

## Benefits

1. **Structural completion tracking**: No more stale markdown checklists
2. **Queryable**: Can programmatically find incomplete features
3. **Bidirectional traceability**: Spec ↔ Code links enforced
4. **Impact analysis**: Know what code implements what features
5. **Automated validation**: Can't mark done without proper linkage

## Testing

Commands successfully added to CLI:
```bash
./know feature review --help  # ✓ Works
./know feature done --help    # ✓ Works
./know feature --help         # ✓ Shows both commands
```

Syntax validation:
```bash
python3 -m py_compile know/know.py  # ✓ No errors
```

### 5. Connection Command Implemented

**`know feature connect <feature> <code-entities...>`**:

Creates bidirectional linkage between spec-graph feature and code-graph entities.

**Usage**:
```bash
# Link feature to modules/functions
know feature connect auth module:auth-handler function:authenticate

# Link with component mapping
know feature connect checkout module:payment --component component:payment
```

**What it does**:
1. Verifies feature exists in spec-graph
2. Verifies all code entities exist in code-graph
3. Creates `implementation` reference in spec-graph → points to graph-links
4. Creates `graph-link` references in code-graph → point back to feature
5. Adds dependency: `feature → implementation reference`
6. Saves both graphs
7. Validates bidirectional consistency

**Arguments**:
- `feature_name`: Name of feature (without "feature:" prefix)
- `code_entities`: One or more code-graph entity IDs (e.g., `module:auth`, `function:login`)
- `--component`: Optional component mapping

**Example flow**:
```bash
# 1. Create code entities in code-graph
know -g .ai/code-graph.json add entity module auth '{"name":"Auth Module"}'
know -g .ai/code-graph.json add entity function authenticate '{"name":"Authenticate User"}'

# 2. Connect to feature
know feature connect user-auth module:auth function:authenticate

# Output:
# ✓ module:auth
# ✓ function:authenticate
#
# Bidirectional linkage established!
# Spec-graph:
#   feature:user-auth → implementation:user-auth-impl
#   implementation:user-auth-impl → [graph-link:auth, graph-link:authenticate]
# Code-graph:
#   graph-link:auth → {'feature': 'feature:user-auth'}
#   graph-link:authenticate → {'feature': 'feature:user-auth'}
```

## Next Steps

1. Test with actual feature
2. Update `/know:prepare` to generate code-graph first
3. Update `/know:connect` skill to call `know feature connect`
4. Add query commands:
   - `know feature incomplete` - show features without implementation
   - `know check linkage` - validate all graph linkages

## Files Modified

- `CLAUDE.md` - Integration Between Graphs section rewritten
- `.claude/commands/know/review.md` - Simplified to call CLI (Rev 3)
- `.claude/commands/know/done.md` - Simplified to call CLI (Rev 4)
- `know/know.py` - Added:
  - `_validate_feature_completion()` - shared validation logic
  - `feature review` - validates graph linkage + QA readiness
  - `feature connect` - creates bidirectional spec↔code linkage
  - Enhanced `feature done` - validates before archiving
