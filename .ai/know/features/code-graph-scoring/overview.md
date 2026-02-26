# code-graph-scoring

Automatic structural health capture for code-graph, recorded by agents at runtime.

## Summary
Agents compute code-graph health metrics (coverage, connectivity, cross-linking, orphan count, etc.) during normal operations and persist them to a sibling file `code-graph-grade.json`. The schema is fixed. History accumulates as an append-only series of snapshots.

## Key Decisions
- **Trigger**: Captured from agent metadata at runtime, not a user-invoked command
- **Dimensions**: Agent determines what to score; schema is fixed
- **Storage**: Time-series history in `code-graph-grade.json`, survives graph rebuilds
- **Grading**: Raw metrics only — no letter grades, no thresholds, no weighting

## Open Questions
- Which agent operations trigger a snapshot (every graph modify? periodic? on `know check`?)
- Exact set of metrics in the fixed schema
- Whether `code-graph-grade.json` lives next to code-graph or in feature dir
