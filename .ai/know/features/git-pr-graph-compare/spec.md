# Spec: git-pr-graph-compare

## Command Syntax
```bash
know graph diff --base <ref> [--verbose] [--format terminal|json]
know -g <graph-path> graph diff --base <ref>
```

## Arguments
- `--base <ref>`: Git reference (branch, tag, commit SHA, or symbolic ref like HEAD~1)
  - Mutually exclusive with positional `GRAPH2` argument
  - Triggers git-aware mode
- `--verbose`: Show detailed property diffs for modified entities
- `--format`: Output format (terminal | json)
  - `terminal`: Human-readable colored output (default)
  - `json`: Machine-parseable structured output

## Behavior

### Git Operations
1. Validate git repository: `git rev-parse --show-toplevel`
2. Resolve graph file path relative to git root
3. Extract base version: `git show <ref>:<relative-path>` → tempfile
4. Run GraphDiff comparison
5. Clean up tempfile (even on error)

### Comparison Output
**Summary Section:**
- Entity counts: added, removed, modified
- Dependency counts: added, removed, modified
- Reference counts: added, removed
- Meta changed (boolean)

**Default Mode (--verbose=false):**
- Summary counts
- Lists of added/removed/modified entities (keys only)
- Lists of dependency changes (entity + what changed)
- Lists of reference changes (keys only)

**Verbose Mode (--verbose=true):**
- Everything from default mode
- Before/after property values for modified entities
- Specific added/removed dependencies per entity
- Meta field changes with old → new values

### Exit Codes
- `0`: Successful comparison (may or may not have differences)
- `1`: Error (missing ref, invalid path, malformed JSON, git failure)

## Error Messages
| Error | Message | Cause |
|-------|---------|-------|
| Mutual exclusivity | `✗ --base and GRAPH2 are mutually exclusive` | Both `--base` and positional GRAPH2 provided |
| Missing args | `✗ Provide GRAPH1 and GRAPH2, or use --base <ref>` | Neither mode specified |
| Not a git repo | `✗ Not inside a git repository` | Not in git-initialized directory |
| Outside git root | `✗ Graph file is outside the git root: <path>` | Graph file not in repo |
| Missing at ref | `✗ Could not read <file> at ref '<ref>': <git-error>` | File doesn't exist at that ref |

## Examples
```bash
# Compare current spec-graph against main
know graph diff --base main

# Compare code-graph against origin/main with details
know -g .ai/know/code-graph.json graph diff --base origin/main --verbose

# Compare against 3 commits ago
know graph diff --base HEAD~3

# JSON output for CI/CD
know graph diff --base origin/main --format json > graph-diff.json
```

## Constraints
- Graph file must exist at the same path in both current and base ref
- Base ref must be resolvable by git
- Both graphs must be valid JSON (schema validation optional)
- Graph file must be within git repository

## Implementation References
- Command: `know/know.py:1563-1789`
- Diff engine: `know/src/diff.py:8-226`
- QA doc: `.ai/qa/git-pr-graph-compare-qa.md`
