# TODO: git-pr-graph-compare

## Implementation
- [x] Add `--base` flag to `know graph diff` command
- [x] Git operations: extract graph from ref via `git show`
- [x] Tempfile handling with cleanup in finally block
- [x] Error handling for missing refs, invalid paths
- [x] Terminal output header showing `<ref> → current`
- [x] Mutual exclusivity check (`--base` XOR `GRAPH2`)

## Documentation
- [ ] Update know-tool skill with `--base` flag usage
- [ ] Add example to README showing PR workflow
- [ ] Document error messages in troubleshooting guide

## Testing
- [ ] Test with non-existent git refs
- [ ] Test with graph file not in git history
- [ ] Test with renamed graph files between branches
- [ ] Test with malformed graphs at different refs
- [ ] Test cleanup of tempfiles on error paths

## Future Enhancements
- [ ] Support `--from <ref> --to <ref>` for symmetric comparisons
- [ ] Add `--format github-comment` for PR comment markdown
- [ ] Entity rename detection via fingerprinting
- [ ] Graph merge conflict detection
