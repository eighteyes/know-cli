# git-pr-graph-compare

## Purpose
Compare spec-graph.json or code-graph.json between a PR branch and base branch (typically main) to show what changed in the specification or architecture during development.

## Implementation Status
✓ **COMPLETE** — Feature is implemented and functional as of commit a7a6401.

## Core Functionality
- Extends `know graph diff` with `--base <ref>` flag for git-aware comparison
- Extracts base graph from git history via `git show <ref>:<path>`
- Runs semantic diff via GraphDiff class (not just text diff)
- Shows added/removed/modified entities, dependencies, references, meta fields
- Supports both spec-graph and code-graph via `-g` flag

## Key Design Decisions
- **Git-awareness is additive**: Extends existing command rather than creating new one
- **Graph-agnostic**: Works with any graph via `-g` flag
- **Fail-fast**: Clear error messages for missing refs, invalid paths
- **Tempfile cleanup**: Uses finally block to ensure no leaked files
- **Human-readable by default**: Terminal output optimized for PR reviews; `--format json` for CI/CD

## Integration Points
- CLI: `know graph diff --base <ref>` in know/know.py:1563-1789
- Diff Engine: GraphDiff class in know/src/diff.py
- Git Operations: subprocess calls to `git rev-parse`, `git show`

## References
- Configuration: `configuration:git-pr-graph-compare-config`
- Data Model: `data-model:graph-diff-output`
- Business Logic: `business_logic:git-ref-resolution`
- Acceptance Criteria: `acceptance_criterion:git-pr-diff-complete`
- Interface: `interface:cli-graph-diff-base`
- Constraint: `constraint:git-repo-required`
