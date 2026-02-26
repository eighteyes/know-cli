# QA: git-pr-graph-compare
_Each answer maps to a graph entity or reference. See type hints per section._

## Core Clarification [MUST ANSWER FIRST]
0. **What exactly is being compared to what, and what's the output?** — Is this comparing spec-graph changes between PR and main, code-graph changes, or both? What's the elevator pitch?

---

## Actions & Operations  [→ action:*, operation:*]

1. **What are the exact steps a user performs to initiate and complete a graph comparison between two PRs or branches?** (e.g., do they select two targets, run a command with flags, confirm selections, view results inline, export comparison data?)

2. **For each user-facing step you just described, what specific system operations get triggered behind the scenes?** (e.g., when user selects a PR, does the system fetch-graph-from-remote, parse-pr-metadata, resolve-branch-refs, diff-graph-structures?)

3. **What happens when the user tries to compare graphs that don't exist, are malformed, or come from incompatible sources?** (e.g., what actions does the user take when seeing an error, and what operations does the system execute to handle-missing-graph, validate-graph-schema, or fallback-to-default?)

4. **Which user action in this feature has the most internal complexity, and what are all the sub-operations that make it work?** (e.g., if "generate-visual-diff" is the action, what are the operations: extract-entities, compute-graph-delta, apply-diff-styling, render-comparison-view?)

5. **What state transitions occur throughout this feature, and which actions/operations trigger them?** (e.g., does comparing graphs change from idle → loading → comparing → displaying-results → user-filtering-results, and what operations fire at each transition?)

---

## Components & Responsibilities  [→ component:*]

6. **What component handles retrieving the graph data from different sources?** — What's responsible for fetching the spec-graph from the PR branch versus the current branch? Does this component just read files, or does it also handle git operations like checkout/fetch?

7. **What component performs the structural comparison between two graphs?** — What receives two graph objects and produces a diff/delta? Does this component care about graph validation, or does it assume valid input?

8. **What component formats the comparison results for human consumption?** — What takes the raw diff data and produces the final output (text, JSON, visual tree)? Does this handle all output formats, or is there a separate component per format?

9. **What component validates graph structure before comparison?** — Or do we skip validation entirely and let the comparison component deal with malformed graphs? If validation exists, does it enforce dependency rules, or just check JSON schema?

10. **What component orchestrates the workflow from PR detection through output delivery?** — What's the top-level coordinator that wires together fetching → validating → comparing → formatting? Or is this just the CLI entry point with no separate orchestrator?

---

## Data Models & Interfaces  [→ data-model:*, interface:*, api_contract:*]

11. **What is the primary data structure this feature produces and what are its key fields?** — What does the "diff result" object look like? (e.g., added/removed/modified entities, dependency changes, metadata?)

12. **What does the CLI command interface look like?** — What's the command syntax (flags, arguments, options)? What does `--help` show?

13. **What does the terminal output look like when comparing two graphs?** — How are additions/removals/modifications displayed? Colors? Tree structure? Summary counts?

14. **What data must be validated before comparison proceeds?** — Graph schema validity? File existence? Git ref resolution? Branch accessibility?

15. **What data does this feature expose for downstream consumption?** — JSON output for CI/CD? Exit codes? Structured logs? Machine-readable diff format?

---

## Rules, Config & Constraints  [→ business_logic:*, configuration:*, security-spec:*, constraint:*, acceptance_criterion:*]

16. **When comparing graphs between PRs, what happens when the dependency rules themselves have changed between branches?** — Does the comparison use the source branch's rules, the target branch's rules, or flag this as a special case requiring human intervention? And if entities exist in one graph but not the other, should they be treated as additions/deletions, orphans, or validation errors?

17. **Does this feature need to know where to find both PR branches (local clones, remote refs, GitHub API)?** — Should it work with dirty working trees or require clean checkouts? What about when the graph files themselves are at different paths or have been renamed between branches?

18. **Should graph comparison operations be restricted to PR authors, repo collaborators, or anyone who can read the repo?** — And when displaying differences, are there any entity types or reference values (tokens, credentials, internal URLs) that must be redacted or filtered from the comparison output?

19. **What's absolutely forbidden during comparison?** — Can we never mutate either graph during comparison? Must both graphs be valid before comparison (or do we allow comparing broken states)? Are there entity type mismatches that should halt the operation entirely rather than just flagging them?

20. **What does "successfully compared two PR graphs" actually mean?** — Should it show added/removed/modified entities, dependency changes, and rule violations, or just a simple diff? Does success require both graphs to be valid, or should it work even when one or both are broken? What's the expected output format - human readable, machine parseable JSON, or both?

---

_Answers:_

