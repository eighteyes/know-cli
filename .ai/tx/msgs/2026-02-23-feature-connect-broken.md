# Bug: `feature connect` can't find features that exist

**From:** lucid-command
**Priority:** medium

## Issue

`know feature connect <feature-name> module:<code-module>` fails with `Feature not found in spec-graph` for features that demonstrably exist in the graph.

## Reproduction

```bash
# Feature exists:
know get feature:job-notes
# Returns: feature:job-notes { name: 'Job Notes', ... }

# Feature is in graph:
know graph uses feature:job-notes --direct
# Returns: action:add-job-note, data-model:job, sequence:job-notes-flow

# But feature connect can't find it:
know feature connect job-notes module:controllers.jobs.controller.ts
# ✗ Feature not found in spec-graph: feature:job-notes

# Same for features with existing code-links:
know feature connect authentication module:controllers.users.controller.ts
# ✗ Feature not found in spec-graph: feature:authentication
```

Tested with both `job-notes` and `authentication` (which already has code-links). Neither found.

## Impact

Had to manually create 56 code-link references and link them one by one instead of using `feature connect` for bidirectional linkage. The code→spec direction (code-graph side) is still unlinked because `feature connect` is the only command that creates bidirectional links.

## Workaround

Manual pattern:
```bash
know add code-link feature-{name}-code '{"modules": ["module:x"], "status": "verified"}'
know link feature:{name} code-link:feature-{name}-code
```

This only creates the spec→code direction. Code→spec remains unlinked.
