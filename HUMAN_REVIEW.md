# Human Review Checklist

---

## Layered Validation + Semantic Search
**Date:** 2026-02-16
**Session:** b3e55e00-403f-40ff-bc81-84f453642904
**Base commit:** 0440bdb

### Feature 1: Layered Validation

Verify each check layer runs and exits cleanly:

```bash
know check syntax
```
Expected: passes fast, checks structure + key format only

```bash
know check structure
```
Expected: checks schema, orphans, entity types, reference usage

```bash
know check semantics
```
Expected: checks dependency rules, cycles, naming conventions

```bash
know check full
```
Expected: all layers combined

```bash
know check validate
```
Expected: identical output to `check full` (backward compat alias)

```bash
know check health
```
Expected: summary output, references `know check full` in hint (not `validate`)

Confirm against a real populated graph:

```bash
know -g .ai/know/spec-graph.json check full
```

### Feature 2: Semantic Search

Build index and verify search:

```bash
know -g /tmp/test-semantic.json find "user login"
```
Expected: returns `feature:authentication` as top match

```bash
know -g /tmp/test-semantic.json find "API integration"
```
Expected: returns `feature:api-gateway`

```bash
know -g /tmp/test-semantic.json related feature:authentication
```
Expected: returns other features with similar text

```bash
know -g /tmp/test-semantic.json suggest-links feature:dashboard
```
Expected: prints "(feature coming soon)" message, exits 0

Confirm index file created alongside graph:

```bash
ls /tmp/test-semantic-search-index.json
```

Confirm index is stale-checked (run twice, second should be instant):

```bash
time know -g /tmp/test-semantic.json find "user"
time know -g /tmp/test-semantic.json find "user"
```

### Regression

```bash
know search "auth"
```
Expected: existing regex search still works

```bash
npm run validate-graph
```
Expected: passes

---

## Spec Graph Diff Log (diff-graph.jsonl)
**Date:** 2026-02-17
**Session:** b3e55e00-403f-40ff-bc81-84f453642904
**Base commit:** 0440bdb

Every write to any `spec-graph.json` appends one line to `.ai/know/diff-graph.jsonl`.

### Verify — entity add is logged

```bash
know -g .ai/spec-graph.json add feature review-diff-test '{"name": "Review", "description": "test"}'
tail -1 .ai/know/diff-graph.jsonl | python3 -m json.tool
```
Expected: `entities_added: ["feature:review-diff-test"]`

### Verify — link change is logged

```bash
know -g .ai/spec-graph.json link feature:review-diff-test feature:<any-existing>
tail -1 .ai/know/diff-graph.jsonl | python3 -m json.tool
```
Expected: `links_added` contains the added edge.

### Verify — entity remove is logged

```bash
know -g .ai/spec-graph.json nodes delete feature:review-diff-test --yes
tail -1 .ai/know/diff-graph.jsonl | python3 -m json.tool
```
Expected: `entities_removed: ["feature:review-diff-test"]`

### Verify — code graph writes are NOT logged

```bash
line_count=$(wc -l < .ai/know/diff-graph.jsonl)
know -g .ai/code-graph.json add module test-no-log '{"name": "no log"}' 2>/dev/null || true
[[ $(wc -l < .ai/know/diff-graph.jsonl) -eq $line_count ]] && echo "PASS: code graph write not logged"
```

---
