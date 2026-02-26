# Human Review Checklist

---

## Reference Parity Patches
**Date:** 2026-02-24
**Session:** 6859a7d6-9281-4216-91f1-e67cf2441067

### A5: get_all_deps sweep — depends_on_ordered included everywhere

```bash
know -g .ai/know/spec-graph.json graph check validate
```
Expected: passes, no new errors from ordered dep handling

### A1: nodes rename works on references

```bash
know -g .ai/know/spec-graph.json nodes rename code-link:workflow-branch-entity-code test-rename -y
know -g .ai/know/spec-graph.json nodes rename code-link:test-rename workflow-branch-entity-code -y
```
Expected: first command renames ref + updates graph refs, second reverses it

### A2: nodes update works on references

```bash
know -g .ai/know/spec-graph.json nodes update code-link:workflow-branch-entity-code '{"status":"tested"}'
```
Expected: shows "Updated reference 'code-link:...'" (not "entity")

```bash
know -g .ai/know/spec-graph.json nodes update code-link:workflow-branch-entity-code '{"status":"complete"}'
```
Expected: reverts the test change

### A3: check stats shows references by type

```bash
know -g .ai/know/spec-graph.json graph check stats
```
Expected: table includes ref counts, "References by Type:" section below entities

### A4: link warns on nonexistent targets

```bash
know -g .ai/know/spec-graph.json link feature:graph-visualization data-model:nonexistent-test
```
Expected: "Warning: source/target node not found..." before "Added dependency"

```bash
know -g .ai/know/spec-graph.json unlink feature:graph-visualization data-model:nonexistent-test -y
```
Expected: cleans up test link

### A6: graph coverage --refs includes references

```bash
know -g .ai/know/spec-graph.json graph coverage
know -g .ai/know/spec-graph.json graph coverage --refs
```
Expected: first shows entity-only count, second shows higher count (entities + references)

### B1-B6: Template patches present

```bash
grep -c "3G. Add References" know/templates/commands/fill-out.md
grep -c "Reference Orphan Check" know/templates/commands/connect.md
grep -c "Reference Completeness Gate" know/templates/commands/done.md
grep -c "Reference Accuracy Check" know/templates/commands/review.md
grep -c "Reference Drift Detection" know/templates/commands/validate.md
grep -c "reference counts" know/templates/commands/list.md
```
Expected: all return 1

---

## Batch Operations
**Date:** 2026-02-18
**Session:** 94bdd7a6-db71-4ba6-8622-b403ad53e48d
**Commit:** eb7c519

### Multi-key add (shared data)

```bash
know add feature x y z '{"name":"Test","description":"Temp"}'
```
Expected: 3 entities created, `✓ Added entity 'feature:x'` for each

### Single-key add backward compat

```bash
know add feature solo '{"name":"Solo","description":"One"}'
```
Expected: 1 entity created, same behavior as before

### Multi-target link

```bash
know link feature:solo feature:x feature:y feature:z
```
Expected: 3 `✓ Added dependency: feature:solo -> feature:*` lines

### Multi-target unlink (single confirm)

```bash
know unlink feature:solo feature:x feature:y feature:z -y
```
Expected: 3 `✓ Removed dependency` lines, no prompt with `-y`

### Batch delete (validate-all-first)

```bash
know nodes delete feature:x feature:y feature:z feature:solo -y
```
Expected: all 4 deleted in one pass, no partial failures

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
know -g .ai/know/spec-graph.json add feature review-diff-test '{"name": "Review", "description": "test"}'
tail -1 .ai/know/diff-graph.jsonl | python3 -m json.tool
```
Expected: `entities_added: ["feature:review-diff-test"]`

### Verify — link change is logged

```bash
know -g .ai/know/spec-graph.json link feature:review-diff-test feature:<any-existing>
tail -1 .ai/know/diff-graph.jsonl | python3 -m json.tool
```
Expected: `links_added` contains the added edge.

### Verify — entity remove is logged

```bash
know -g .ai/know/spec-graph.json nodes delete feature:review-diff-test --yes
tail -1 .ai/know/diff-graph.jsonl | python3 -m json.tool
```
Expected: `entities_removed: ["feature:review-diff-test"]`

### Verify — code graph writes are NOT logged

```bash
line_count=$(wc -l < .ai/know/diff-graph.jsonl)
know -g .ai/know/code-graph.json add module test-no-log '{"name": "no log"}' 2>/dev/null || true
[[ $(wc -l < .ai/know/diff-graph.jsonl) -eq $line_count ]] && echo "PASS: code graph write not logged"
```

---
