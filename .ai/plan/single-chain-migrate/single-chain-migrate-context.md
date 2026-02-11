# Context: Single-Chain Migration

## Key Files
- `know/config/dependency-rules.json` — spec graph rules (primary target)
- `know/src/migration.py` — new file for RulesDiffAnalyzer
- `know/src/__init__.py` — module exports
- `know/know.py` — CLI commands (graph group at line 920, graph_diff at line 1067)
- `know/src/diff.py` — GraphDiff class (pattern reference)
- `know/src/utils.py` — parse_entity_id helper
- `CLAUDE.md` — dual graph documentation

## Decisions
- `requirement` and `interface` demoted to reference types, not deleted
- `graph migrate` is analysis-only, generates commands but doesn't execute
- Command inherits `-g` and `-r` from parent CLI group
- Loads rules JSON directly, does NOT use DependencyManager or GraphValidator
- Output follows `graph diff` pattern (Rich console or JSON)
