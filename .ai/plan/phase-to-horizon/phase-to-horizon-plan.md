# Phase → Horizon Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the "phase" concept to "horizon" throughout the know CLI, server, dashboard, and graph schema — plus an auto-migration shim that converts existing `meta.phases` to `meta.horizons` on first graph load.

**Architecture:** Migration shim lives in `GraphManager.load()` — one choke-point for all graph reads. CLI group renamed from `phases` to `horizons`. Dashboard labels updated. Done features simply have no horizon (already the behavior — removing from horizons = no entry). No new dependencies.

**Tech Stack:** Python (Click CLI), Preact+HTM (dashboard), stdlib http.server

---

## File Map

  File                                      Change
  `know/src/graph.py`                       Add `_migrate_phases_to_horizons()`, call in `get_graph()`
  `know/know.py`                            ~200 changes: CLI group, meta key, output strings
  `know/src/server.py`                      `/api/phase` → `/api/horizon`, CLI proxy calls
  `know/www/index.html`                     `meta.phases` → `meta.horizons`, UI labels
  `know/www/api.js`                         `changePhase` → `changeHorizon`, endpoint path
  `know/templates/commands/build.md`        `phases status` → `horizons status` (source of truth)
  `know/templates/commands/prebuild.md`     same
  `.claude/commands/know/build.md`          synced via `know init .` after templates updated
  `.claude/commands/know/prebuild.md`       synced via `know init .`

---

## Task 1: Migration shim in graph.py

**Files:**
- Modify: `know/src/graph.py:31-33` (the `load()` / `get_graph()` methods)

- [ ] **Step 1: Add migration helper and hook it into `get_graph()`**

Add this function and call it from `get_graph()`:

```python
@staticmethod
def _migrate_phases_to_horizons(data: Dict[str, Any]) -> Dict[str, Any]:
    """One-time migration: rename meta.phases → meta.horizons in loaded graph data."""
    meta = data.get('meta', {})
    if 'phases' in meta and 'horizons' not in meta:
        meta['horizons'] = meta.pop('phases')
        data['meta'] = meta
    return data
```

In `get_graph()`, wrap the return:
```python
def get_graph(self) -> Dict[str, Any]:
    """Get the complete graph"""
    return self._migrate_phases_to_horizons(self.cache.get())
```

- [ ] **Step 2: Verify migration fires on existing graph**

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from know.src.graph import GraphManager
g = GraphManager('.ai/know/spec-graph.json')
data = g.load()
print('horizons key present:', 'horizons' in data.get('meta', {}))
print('phases key gone:', 'phases' not in data.get('meta', {}))
print('horizons content:', list(data['meta']['horizons'].keys()))
"
```
Expected: `horizons key present: True`, `phases key gone: True`, keys like `['I', 'II']`

> The shim only migrates the in-memory view — it does NOT save automatically. The first CLI command that writes the graph will persist `horizons`. This is intentional: read-only commands (like `know list`) won't modify the file unexpectedly.

- [ ] **Step 3: Commit**

```bash
git add know/src/graph.py
git commit -m "feat(graph): auto-migrate meta.phases → meta.horizons on load"
```

---

## Task 2: Rename `phases` CLI group → `horizons` in know.py

**Files:**
- Modify: `know/know.py` — the `phases` Click group and all subcommands

This is the largest task. Work in sub-steps.

**Step 2a: Section command registry**

- [ ] Find line 77: `'Project': ['feature', 'phases', 'req', 'op', 'meta', 'serve']`
  Change `'phases'` → `'horizons'`

**Step 2b: Rename the Click group and subcommands**

The `phases` group is at line ~5559. Rename:

```python
# BEFORE
@cli.group(name='phases', invoke_without_command=True)
def phases(ctx):
    """Manage project phases and entity assignments"""

# AFTER
@cli.group(name='horizons', invoke_without_command=True)
def horizons(ctx):
    """Manage project horizons and entity assignments"""
```

All `@phases.command(...)` → `@horizons.command(...)`

All function names: `phases_list` → `horizons_list`, `phases_add` → `horizons_add`, `phases_move` → `horizons_move`, `phases_status` → `horizons_status`, `phases_remove` → `horizons_remove`

- [ ] **Step 2c: Update all docstrings and help text in the group**

Replace all "phase" / "phases" in docstrings and example strings within the `horizons` group:
- `know phases` → `know horizons`
- `know phases list` → `know horizons list`
- `"phase_id"` → `"horizon_id"` (parameter names)
- `"phase"` → `"horizon"` in `@click.argument` names
- Help text: "phase" → "horizon"

- [ ] **Step 3: Verify CLI group renamed**

```bash
python3 know/know.py horizons --help
```
Expected: shows `list`, `add`, `move`, `status`, `remove` subcommands with "horizon" language

```bash
python3 know/know.py phases --help
```
Expected: error "No such command 'phases'"

- [ ] **Step 4: Commit**

```bash
git add know/know.py
git commit -m "feat(cli): rename phases group → horizons"
```

---

## Task 3: Update meta key references in know.py

**Files:**
- Modify: `know/know.py` — all `meta.get('phases', {})` and `graph_data['meta']['phases']` references

All occurrences outside the `horizons` group itself (impact analysis, feature info, complete command, list commands):

- [ ] **Step 1: Global replace meta key references**

Replace all occurrences of:
- `meta.get('phases', {})` → `meta.get('horizons', {})`
- `graph_data['meta']['phases']` → `graph_data['meta']['horizons']`
- `graph_data.get('meta', {}).get('phases', {})` → `graph_data.get('meta', {}).get('horizons', {})`
- `'phases' not in graph_data['meta']` → `'horizons' not in graph_data['meta']`
- `'phases' not in meta` → `'horizons' not in meta`
- `graph_data['meta']['phases'] = {}` → `graph_data['meta']['horizons'] = {}`
- `del graph_data['meta']['phases']` → `del graph_data['meta']['horizons']`

Key locations:
- Line ~3375: `feature_info` function
- Line ~4354-4474: `feature` command (status/info display)
- Line ~5033-5047: another feature display block
- Line ~5333-5351: `complete` command (removing from horizons on done)
- Line ~5592-5596: `horizons_list`
- Line ~5823-5843: `horizons_add`
- Line ~5901-5929: `horizons_move`
- Line ~5975-5983: `horizons_status`
- Line ~6010-6019: `horizons_remove`

- [ ] **Step 2: Update user-facing output strings**

Replace in output `console.print` / f-strings:
- `"Phase:"` → `"Horizon:"`
- `"phase"` → `"horizon"` in user messages (e.g., "Not assigned to any phase" → "Not assigned to any horizon")
- `"No phases defined"` → `"No horizons defined"`
- `"Removed from phase"` → `"Removed from horizon"`
- `"Affected phases:"` → `"Affected horizons:"`
- `impact['counts']['phases']` → `impact['counts']['horizons']` (if exists)
- `impact['phases']` → `impact['horizons']` (check impact analysis section ~2009-2031)

- [ ] **Step 3: Update any `_migrate_deprecated_names` if it references phases**

Line ~2065: Check `_migrate_deprecated_names` — add phases→horizons migration there as well for consistency.

- [ ] **Step 4: Update feature overview generation strings**

Lines ~3411, 3424, 3437, 3451, 3459, 3463-3467:
- `"**Phase**: {feature_phase}"` → `"**Horizon**: {feature_phase}"`
- `feature_phase` variable rename to `feature_horizon` for clarity

- [ ] **Step 5: Smoke test**

```bash
python3 know/know.py horizons list
```
Expected: shows horizons I, II with their entities

```bash
python3 know/know.py feature spec-dashboard
```
Expected: shows "Horizon: I" (not "Phase: I")

- [ ] **Step 6: Commit**

```bash
git add know/know.py
git commit -m "feat(cli): update all meta.phases → meta.horizons references in know.py"
```

---

## Task 4: Update server.py

**Files:**
- Modify: `know/src/server.py`

- [ ] **Step 1: Rename endpoint path**

Line ~449: `if path == '/api/phase':` → `if path == '/api/horizon':`

- [ ] **Step 2: Rename CLI proxy calls**

Lines ~457-462:
```python
# BEFORE
ok, stdout, stderr = self._run_know(['phases', 'move', entity_id, phase])
if not ok and 'not found in any phase' in stderr:
    ok, stdout, stderr = self._run_know(['phases', 'add', phase, entity_id])
if ok and body.get('status'):
    self._run_know(['phases', 'status', entity_id, body['status']])

# AFTER
ok, stdout, stderr = self._run_know(['horizons', 'move', entity_id, horizon])
if not ok and 'not found in any horizon' in stderr:
    ok, stdout, stderr = self._run_know(['horizons', 'add', horizon, entity_id])
if ok and body.get('status'):
    self._run_know(['horizons', 'status', entity_id, body['status']])
```

- [ ] **Step 3: Rename local variables**

Lines ~451-453:
```python
# BEFORE
phase = body.get('phase', '')
if not entity_id or not phase:
    self._json_response({"ok": False, "error": "entity_id and phase are required"}, status=400)

# AFTER
horizon = body.get('horizon', '')
if not entity_id or not horizon:
    self._json_response({"ok": False, "error": "entity_id and horizon are required"}, status=400)
```

- [ ] **Step 4: Update _build_chat_context**

Lines ~234-242: update `phases` → `horizons` in the graph context builder:
```python
horizons = list(graph.get('meta', {}).get('horizons', {}).keys())
# ...
f"- Horizons: {', '.join(horizons) or 'none'}\n\n"
```

- [ ] **Step 5: Verify endpoint still responds**

Start server, then:
```bash
curl -s -X POST http://localhost:5174/api/horizon \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "feature:spec-dashboard", "horizon": "II"}'
```
Expected: `{"ok": true, ...}`

- [ ] **Step 6: Commit**

```bash
git add know/src/server.py
git commit -m "feat(server): rename /api/phase → /api/horizon, phases CLI calls → horizons"
```

---

## Task 5: Update index.html

**Files:**
- Modify: `know/www/index.html`

- [ ] **Step 1: Update graph data key**

`graph.meta?.phases` → `graph.meta?.horizons`

Line ~1048: `for (const [phaseId, phaseEntities] of Object.entries(graph.meta?.phases || {}))`
→ `for (const [horizonId, horizonEntities] of Object.entries(graph.meta?.horizons || {}))`

Line ~1046-1057: rename `phases` object to `horizons`, `phaseId` to `horizonId`

- [ ] **Step 2: Update KanbanColumn component signature and internals**

Line ~1176: `function KanbanColumn({ phase, features, ...` → `function KanbanColumn({ horizon, features, ...`

All `phase.id`, `phase.label` → `horizon.id`, `horizon.label`

- [ ] **Step 3: Update handleDrop and column logic**

Line ~1606: `const handleDrop = async (featureId, phaseId)` → `(featureId, horizonId)`
Line ~1608: `await api.changePhase(featureId, phaseId)` → `await api.changeHorizon(featureId, horizonId)`

Lines ~1630-1670:
- `getPhaseInfo` → `getHorizonInfo` (function name and call)
- `const { phases, assignments }` → `const { horizons, assignments }`
- `assignments[entityId] = { phase: phaseId, ... }` → `{ horizon: horizonId, ... }`
- `assignments[f.id]?.phase === pid` → `assignments[f.id]?.horizon === pid`
- `phaseKeys`, `sortedPhaseKeys` → `horizonKeys`, `sortedHorizonKeys`
- Column push: `phase: phases[pid]` → `horizon: horizons[pid]`

- [ ] **Step 4: Update unphased fallback label**

Line ~1659: `{ id: '_unphased', label: 'Unphased' }` → `{ id: '_unphased', label: 'No Horizon' }`

- [ ] **Step 5: Update CSS class**

Line ~310: `.column-header .phase-name` → `.column-header .horizon-name`

In the JSX: `<span class="phase-name">` → `<span class="horizon-name">`

- [ ] **Step 6: Update KanbanColumn call site**

Line ~1670: `<${KanbanColumn} phase=${col.phase}` → `<${KanbanColumn} horizon=${col.horizon}`

- [ ] **Step 7: Visual smoke test**

Open `http://localhost:5174` — columns should show "I", "II" headers, unassigned features show in "No Horizon" column.

- [ ] **Step 8: Commit**

```bash
git add know/www/index.html
git commit -m "feat(dashboard): rename phases → horizons in kanban UI"
```

---

## Task 6: Update api.js

**Files:**
- Modify: `know/www/api.js`

- [ ] **Step 1: Rename function and endpoint**

Lines 41-43:
```js
// BEFORE
export async function changePhase(entityId, phase, status) {
  return request('POST', '/api/phase', { entity_id: entityId, phase, status });
}

// AFTER
export async function changeHorizon(entityId, horizon, status) {
  return request('POST', '/api/horizon', { entity_id: entityId, horizon, status });
}
```

- [ ] **Step 2: Verify no remaining `/api/phase` references**

```bash
grep -n "phase" know/www/api.js
```
Expected: no results

- [ ] **Step 3: Commit**

```bash
git add know/www/api.js
git commit -m "feat(api): rename changePhase → changeHorizon, /api/phase → /api/horizon"
```

---

## Task 7: Update command templates and sync

**Files:**
- Modify: `know/templates/commands/build.md`
- Modify: `know/templates/commands/prebuild.md`
- Sync: `know init .` updates `.claude/commands/know/`

- [ ] **Step 1: Update build.md**

All occurrences of `phases status` → `horizons status`:
- Line ~54: `3. Update meta.phases status` → `meta.horizons status`
- Line ~256, 413, 416: `phases status feature:<name> review-ready` → `horizons status feature:<name> review-ready`
- Line ~648: "mark in 'done' phase" → "mark as done (no horizon)"

- [ ] **Step 2: Update prebuild.md**

- Line ~152: `"phase, status"` → `"horizon, status"`
- Line ~210: "Order phases bottom-up" → "Order horizons bottom-up"
- Line ~223-225: `phases status feature:<name> review-ready` → `horizons status feature:<name> review-ready`
- Line ~281: "just feature entity + phase" → "just feature entity + horizon"

- [ ] **Step 3: Sync downstream command files**

```bash
python3 know/know.py init .
```

- [ ] **Step 4: Verify sync worked**

```bash
diff know/templates/commands/build.md .claude/commands/know/build.md
```
Expected: no diff (or only template wrapper differences)

- [ ] **Step 5: Commit**

```bash
git add know/templates/commands/build.md know/templates/commands/prebuild.md \
        .claude/commands/know/build.md .claude/commands/know/prebuild.md
git commit -m "feat(commands): update phase → horizon in build and prebuild templates"
```

---

## Task 8: Persist migration and end-to-end verify

- [ ] **Step 1: Trigger a write to persist the migrated graph**

```bash
python3 know/know.py horizons list
```

This reads the graph (triggering in-memory migration) and displays, but doesn't save. To persist:

```bash
python3 know/know.py horizons status feature:spec-dashboard in-progress
```

Or just re-check that any mutation command triggers the save with `horizons` key.

- [ ] **Step 2: Verify spec-graph.json on disk now uses `horizons`**

```bash
python3 -c "import json; g=json.load(open('.ai/know/spec-graph.json')); print('horizons' in g['meta'], 'phases' in g['meta'])"
```
Expected: `True False`

- [ ] **Step 3: Full smoke test sequence**

```bash
# CLI
python3 know/know.py horizons list
python3 know/know.py horizons add III feature:spec-dashboard
python3 know/know.py horizons move feature:spec-dashboard I
python3 know/know.py feature spec-dashboard  # should show "Horizon: I"

# Validate graph
npm run validate-graph
```

- [ ] **Step 4: Final commit**

```bash
git add .ai/know/spec-graph.json .ai/know/diff-graph.jsonl
git commit -m "chore(graph): persist horizons migration in spec-graph.json"
```

---

## Rollback note

If something goes wrong, the migration is safe to reverse: `meta.horizons` → `meta.phases` in the JSON file directly (read-only ops are still allowed on the graph file, or use `jq` on a copy and re-import). The shim only fires when `phases` key is present and `horizons` is absent — idempotent.
