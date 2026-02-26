# QA: code-graph-scoring
_Each answer maps to a graph entity or reference. See type hints per section._

## Actions & Operations  [→ action:*, operation:*]
1. What triggers a grade run — only explicit `know check grade`, or also during `know check validate` / after graph rebuild?
2. What specific steps does the user take from "I want to grade my graph" to "I have actionable results" — and what does each step trigger internally?
3. When grading detects problems (orphans, missing cross-links), does it just report or also suggest fixes (e.g. "run `know:connect`")?
4. Does the user review grade history / deltas between runs, or just the current snapshot?
5. What failure paths exist — empty graph, missing spec-graph for cross-link check, malformed graph, first run with no history?

## Components & Responsibilities  [→ component:*]
6. What are the distinct grading dimensions and should each be an isolated scorer component (coverage-scorer, connectivity-scorer, cross-link-scorer, layering-scorer, staleness-scorer, granularity-scorer)?
7. Are these six dimensions fixed, or must the design be dimension-agnostic (plugin new scorers without code changes)?
8. Does the grading system read only the code-graph, or also the spec-graph (for cross-linking) and the actual codebase (for staleness)?
9. What component handles persistence — writing `code-graph-grade.json`, preserving history, computing graph hashes?
10. Which components are reusable by other features (e.g. orphan detection is useful for `know check validate` too)?

## Data Models & Interfaces  [→ data-model:*, interface:*, api_contract:*]
11. What is the structure of `code-graph-grade.json` — per-dimension subscores, composite letter grade, or both? What fields does each entry have (grade, counts, ratios, timestamp, graph hash)?
12. What does the CLI output look like — table of dimensions + grades, single overall grade, or verbose breakdown? What flags control verbosity?
13. Does the grade file store historical runs (time-series array) or just the latest snapshot?
14. What constitutes valid cross-linking between graphs — must every code entity map to a spec entity, or only at feature level via `code-link` references?
15. Does the grade report export to other formats (JSON stdout for CI, markdown for docs)?

## Rules, Config & Constraints  [→ business_logic:*, configuration:*, constraint:*, acceptance_criterion:*]
16. How are letter grades computed — absolute thresholds (>90%=A, >80%=B...), relative to history, or user-configurable boundaries?
17. Are all dimensions equally weighted in the composite grade, user-configurable weights, or do critical violations cap the overall grade?
18. What runtime config is needed — file paths, which dimensions to enable/disable, grade thresholds?
19. Hard invariants: grade file must not be clobbered by graph rebuild, grades must be deterministic for same graph state — what else?
20. What does "this feature works correctly" look like — same graph produces same grade, grade improves when gaps are fixed, grade file survives rebuild?

---
_Answers:_

