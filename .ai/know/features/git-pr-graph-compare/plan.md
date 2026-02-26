# Implementation Plan: git-pr-graph-compare

## Status
✓ **IMPLEMENTED** — Feature is complete and functional.

## Implementation Summary
Modified `know/know.py` to add git-awareness to the existing `graph diff` command.

### Changes Made
1. **Imports** (lines 12-17)
   - Added `subprocess`, `tempfile` for git operations

2. **Command Signature** (lines 1563-1573)
   - Made `graph1` and `graph2` optional arguments
   - Added `--base/-b <ref>` option
   - Added `@click.pass_context` decorator for access to graph path

3. **Git Mode Logic** (lines 1576-1643)
   - Extract graph path from `ctx.obj['graph'].cache.graph_path`
   - Compute git-root-relative path via `git rev-parse --show-toplevel`
   - Extract base version via `git show <ref>:<path>` into tempfile
   - Set up diff: base (old) vs current (new)

4. **Output Header** (lines 1655-1660)
   - Show `<ref> → current` instead of tempfile name when using `--base`

5. **Cleanup** (lines 1787-1789)
   - Added `finally` block to remove tempfile

### Files Modified
- `know/know.py`: Added git-aware diff functionality
- `know/templates/hooks/SessionStart.sh`: Created (separate feature)

### Dependencies
- Existing `GraphDiff` class in `know/src/diff.py` (no changes needed)
- Git must be installed and repo must be initialized
- Graph file must exist at same path in base ref

## Architecture Notes
- **Separation of concerns**: Git handles version retrieval, GraphDiff handles semantic comparison
- **Backward compatible**: Two-file mode still works (`know graph diff file1 file2`)
- **Consistent with existing patterns**: Uses `-g` flag from parent group like all graph commands

## Next Steps (if expanding)
1. Add `--all-graphs` to compare both spec + code graphs simultaneously
2. Implement entity rename detection via content fingerprinting
3. Create GitHub Actions example workflow
4. Add caching for repeated comparisons
