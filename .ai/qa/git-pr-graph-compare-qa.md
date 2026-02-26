# QA: git-pr-graph-compare

## Q1: What is the core purpose of this feature?
Choices:
    A) Compare spec-graph.json between PR branch and base branch (e.g., main)
    B) Compare code-graph.json between PR branch and base branch
    C) Support comparing EITHER spec-graph.json OR code-graph.json via the `-g` flag
    D) Compare both graphs simultaneously and show cross-graph impacts

Recommendations:
**C** — The implementation uses the existing `-g` flag from the parent `graph` group, so it works with whichever graph file the user specifies. This is the most flexible and follows existing CLI patterns.

Tradeoffs:
- Option C requires users to run the command twice if they want to compare both graphs
- Option D would be more powerful but adds significant complexity (which graph's rules to use? how to visualize cross-graph diffs?)
- Options A/B are too restrictive and would require a separate command for each graph type

Alternatives:
- Could add `--all-graphs` flag that compares both and shows side-by-side results
- Could add graph type auto-detection from git history

Challenges:
- What if the graph file path changed between branches?
- What if dependency rules themselves changed between branches?
- Should the comparison validate graphs before diffing, or diff broken graphs?

A1: C — Support comparing EITHER spec-graph.json OR code-graph.json via the `-g` flag. Most flexible, follows existing CLI patterns.

---

## Q2: What's the user command syntax?
Choices:
    A) `know graph diff --base <ref>` (uses current graph file from `-g` flag)
    B) `know graph pr-diff <ref>` (new top-level command)
    C) `know graph diff <ref>` (ref as positional arg, auto-detect git mode)
    D) `know diff --pr <ref>` (dedicated diff command group)

Recommendations:
**A** — Already implemented. Extends existing `know graph diff` command with optional `--base` flag, making git-awareness additive rather than creating a new command. Follows the principle of least surprise.

Tradeoffs:
- Option A makes the command signature more complex (3 modes: two files, --base, or error)
- Option B would be more discoverable but adds command sprawl
- Option C is ambiguous (is "main" a file path or a git ref?)
- Option D breaks the command hierarchy (diff is naturally under graph)

Alternatives:
- `know graph diff --from <ref> --to <ref>` for symmetric git-aware diffing
- `know graph git-diff <ref>` as a subcommand

Challenges:
- How do users discover the `--base` flag exists?
- Should `--base` be the default mode if no file args provided?

A2: A — `know graph diff --base <ref>` extends existing command with optional `--base` flag for git-awareness.

---

## Q3: What git operations are required?
Choices:
    A) `git show <ref>:<path>` only (extract file at ref)
    B) `git diff <ref> HEAD -- <path>` (use git's native diff)
    C) `git show` + GraphDiff class (current implementation)
    D) GitHub API calls (for remote PRs without local checkout)

Recommendations:
**C** — Current implementation. Uses `git show <ref>:<path>` to extract the base version into a tempfile, then runs the existing GraphDiff logic. Clean separation: git handles version retrieval, GraphDiff handles semantic comparison.

Tradeoffs:
- Option C requires a local git repo with the ref available
- Option B gives file-level diffs, not semantic entity/dependency diffs
- Option D would enable remote-only comparisons but adds API auth complexity
- Tempfile approach in C has cleanup edge cases (handled via finally block)

Alternatives:
- Could use `git worktree` to avoid tempfiles
- Could cache extracted graphs to speed up repeated comparisons

Challenges:
- What if the user is in a detached HEAD state?
- What if the ref is a remote branch not yet fetched?
- Should we auto-fetch if ref is missing?

A3: C — `git show <ref>:<path>` to extract base version into tempfile, then GraphDiff handles semantic comparison. Clean separation of concerns.

---

## Q4: What does the output show?
Choices:
    A) Summary counts only (X entities added, Y removed, Z modified)
    B) Summary + entity lists (show which entities changed)
    C) Summary + entity lists + property diffs (current --verbose mode)
    D) Interactive TUI for exploring the diff

Recommendations:
**B by default, C with --verbose** — Current implementation. Default mode shows summary counts + lists of added/removed/modified entities. Verbose mode adds before/after property diffs. Strikes a balance between signal and noise.

Tradeoffs:
- Option A is too sparse for PR reviews (need to know *what* changed)
- Option C by default is overwhelming for large changes
- Option D would be powerful but adds significant implementation cost

Alternatives:
- `--format json` for machine-readable output (already implemented)
- `--filter <entity-type>` to focus on specific types
- Color-coded diff with +/- prefixes (partially implemented)

Challenges:
- How to visualize dependency graph changes? (A depends on B → A depends on C)
- Should removed entities show their full spec, or just the key?
- What if the diff is too large to fit in a terminal?

A4: B by default, C with --verbose — Summary counts + entity lists by default. Property diffs with --verbose. Balances signal/noise.

---

## Q5: How are graph file paths resolved?
Choices:
    A) Hardcoded to `.ai/know/spec-graph.json`
    B) Use `-g` flag value (current implementation)
    C) Auto-detect from git history
    D) Support path mapping (base uses old path, current uses new path)

Recommendations:
**B** — Uses the `-g` flag from the parent graph group. This means `know -g .ai/know/code-graph.json graph diff --base main` works correctly. Consistent with all other graph commands.

Tradeoffs:
- Option B requires the graph file to exist at the same path in both refs
- Option D would handle renames but adds complexity (how to specify the mapping?)
- Option C could be fragile (what if multiple graphs exist?)

Alternatives:
- Add `--base-path` flag for asymmetric path resolution
- Use git's rename detection to track file moves

Challenges:
- What if the graph file was renamed between base and current?
- What if the file exists in base but not in current (feature deleted)?
- Should we error or treat missing file as "empty graph"?

A5: B — Uses `-g` flag value from parent graph group. Consistent with all other graph commands.

---

## Q6: What are the failure modes and error messages?
Choices:
    A) Fail fast on any error (current implementation)
    B) Best-effort comparison (compare what's valid, skip broken parts)
    C) Collect all errors and report at the end
    D) Interactive recovery (prompt user when errors occur)

Recommendations:
**A** — Current implementation fails fast with clear error messages:
- "Not inside a git repository"
- "Graph file is outside the git root"
- "Could not read <file> at ref '<ref>'" (shows git error)
- "GRAPH2 and --base are mutually exclusive"

Tradeoffs:
- Option A prevents partial/misleading results but requires users to fix issues before seeing any output
- Option B is more resilient but can hide problems
- Option C gives better diagnostics but delays feedback

Alternatives:
- `--strict` / `--lenient` flags to toggle failure behavior
- Warnings for non-fatal issues, errors for fatal ones

Challenges:
- What if one graph is valid but the other is malformed?
- Should we compare "as much as possible" or require both to be valid?
- What constitutes a "valid" graph (schema only, or also dependency rules)?

A6: A — Fail fast with clear error messages. Prevents partial/misleading results.

---

## Q7: What are the acceptance criteria for "feature works correctly"?
Choices:
    A) Successfully shows added/removed entities between two refs
    B) Detects all semantic changes (entities, dependencies, references, meta)
    C) Produces accurate diffs even with renamed/moved entities
    D) Handles all edge cases (empty graphs, invalid graphs, missing refs)

Recommendations:
**B** — Current implementation detects:
- Added/removed/modified entities
- Added/removed/modified dependencies
- Added/removed references
- Changed meta fields
Exit code 0 if successful, 1 on error.

Tradeoffs:
- Option C would require entity fingerprinting to track renames (not implemented)
- Option D would require extensive error handling that may not be worth the complexity
- Current implementation assumes entity keys are stable identifiers

Alternatives:
- Add `--exit-code` flag like git diff (exit 1 if differences found)
- Add `--ignore-meta` / `--ignore-refs` filters

Challenges:
- How to distinguish "entity renamed" from "entity deleted + different entity added"?
- Should meta changes (like project name) cause a non-zero exit code?
- What if dependency rules changed and old graph is now invalid under new rules?

A7: B — Detects all semantic changes: entities, dependencies, references, meta. Exit 0 on success, 1 on error.

---

## Q8: How does this integrate with PR workflows?
Choices:
    A) Manual invocation only (current implementation)
    B) GitHub Actions integration (auto-comment on PRs)
    C) Git hooks (block commits if graph broken)
    D) IDE integration (show diff in editor)

Recommendations:
**A for now** — Current implementation is a CLI tool. Users run it manually during PR review or locally before pushing.

Tradeoffs:
- Option B would automate PR reviews but requires CI/CD setup
- Option C would prevent bad commits but might be too aggressive
- Manual invocation gives flexibility but relies on user discipline

Alternatives:
- Provide example GitHub Actions workflow in docs
- Add `--format github-comment` for markdown output optimized for PR comments
- Generate diff summary for commit messages

Challenges:
- Should this block PRs if graph coverage decreases?
- How to make diffs actionable (link to entities in codebase)?
- What's the right signal-to-noise ratio for automated PR comments?

A8: A for now — Manual CLI invocation. Users run during PR review or before pushing. Future: GitHub Actions integration possible.

---

## Q9: What configuration/environment does this feature need?
Choices:
    A) None (works in any git repo)
    B) Requires know-cli installed globally
    C) Requires graph file at standard path
    D) Requires specific git version

Recommendations:
**A + B** — Works in any git repo where know-cli is installed. No special config needed. Graph path is determined by `-g` flag.

Tradeoffs:
- Requiring global install (B) means users can't vendor the tool
- No config is simple but inflexible (can't set default base branch)

Alternatives:
- Support `.knowrc` config file for defaults (base branch, output format, etc.)
- Support `KNOW_GRAPH_DIFF_BASE` env var

Challenges:
- Should users be able to compare graphs from different repos?
- What if know-cli version differs between base and current commits?

A9: A + B — Works in any git repo where know-cli is installed. No special config needed.

---

## Q10: What's out of scope for this feature?
Not Included:
- Cross-repo comparisons
- Entity rename detection
- Visual/interactive diff viewer
- Automatic conflict resolution
- Graph merge operations
- Dependency rule migration
- Performance metrics (time to build, graph size)

Should any of these be included?

A10: Out of scope — Cross-repo comparisons, entity rename detection, visual diff viewer, graph merge operations. These may be added in future iterations if needed.

---

**Status:** Answer A1-A10 above. Use "A#: [your answer]" format. Once complete, I'll convert this to clean Q&A format and proceed with feature registration.
