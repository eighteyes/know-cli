# Clarification Q&A: Beads Integration

## Session Date
2025-12-19

## Questions & Answers

### 1. Missing bd Executable

**Question**: How should we handle missing bd executable when user runs 'know bd init'?

**Answer**: **Fail with helpful error**
- Show error: "bd not found. Install Beads first: https://github.com/steveyegge/beads"
- Check for `bd` in PATH before attempting operations
- Provide clear installation instructions
- Exit gracefully with error code

**Implementation Impact**:
- Add `is_bd_available()` check in BeadsBridge
- Show helpful error message with install link
- No silent fallbacks - user must explicitly choose system

---

### 2. Conflict Resolution Strategy

**Question**: When beads and spec-graph have conflicting task status, which should win?

**Answer**: **Beads is source of truth**
- Beads status always overwrites spec-graph during sync
- Rationale: Beads is the execution layer, graph is the planning layer
- Tasks may be worked on outside know context
- Graph status derives from Beads status

**Implementation Impact**:
- Sync direction: Beads → Graph (status updates)
- Graph → Beads (new task creation only)
- Conflict resolution logic always favors Beads state
- Log warnings when overwriting graph status

---

### 3. Task Creation Mode

**Question**: Should task creation be automatic when features are added, or manual?

**Answer**: **Auto-create on feature add**
- Automatically create initial task when feature added to graph
- Create one root task per feature by default
- User can add more tasks manually
- Simplifies onboarding workflow

**Implementation Impact**:
- Hook into `know add feature` command
- After feature creation, call `beads_bridge.create_task_for_feature()`
- Store bead ID in `references.beads`
- Link bead to feature entity

**Edge Cases**:
- If Beads not initialized, skip auto-creation (warn user)
- If using native tasks, create in `.ai/tasks/tasks.jsonl`
- Allow opt-out via config: `auto_create_tasks: false`

---

### 4. Security & Command Validation

**Question**: Should we validate/sanitize bd command arguments for security?

**Answer**: **Trust user input**
- Pass arguments directly to bd - user runs own tool
- No command injection risk (subprocess.run with list args)
- User has full control over their system
- Simplest implementation

**Implementation Impact**:
- Use `subprocess.run(['bd'] + args)` with list (not shell=True)
- No argument escaping needed
- No command whitelisting
- Trust model: user controls their environment

---

### 5. Sync Timing

**Question**: When should bidirectional sync occur?

**Answer**: **Multiple triggers** (selected: On command, On status change, On commit/save)

**Triggers**:
1. **Explicit sync**: `know bd sync` - Manual user-initiated sync
2. **Feature status change**: Auto-sync when feature moves between phases
3. **On graph save**: After any spec-graph modification

**Implementation Impact**:
- Add sync hook to phase status changes
- Add sync hook to graph save operations
- Config option to disable auto-sync: `auto_sync: false`
- Rate limiting to prevent excessive syncs (debounce 1 second)

**Sync Logic**:
```python
def auto_sync(trigger: str):
    if not config.get('auto_sync', True):
        return

    if trigger == 'status_change':
        sync_feature_status()
    elif trigger == 'graph_save':
        sync_all_tasks()
```

---

### 6. Hash ID Generation (Native Tasks)

**Question**: For the native task system, where should hash IDs come from?

**Answer**: **SHA256(title+timestamp) truncated**
- First 4 hex chars of SHA256 hash
- Input: `title + timestamp`
- Format: `tk-a1b2`
- Collision-resistant and deterministic

**Implementation**:
```python
import hashlib
from datetime import datetime

def generate_task_id(title: str) -> str:
    timestamp = datetime.utcnow().isoformat()
    content = f"{title}{timestamp}"
    hash_hex = hashlib.sha256(content.encode()).hexdigest()
    return f"tk-{hash_hex[:4]}"
```

**Benefits**:
- Reproducible from inputs
- Low collision probability
- Git-merge friendly
- Matches Beads pattern (`bd-a1b2`)

---

### 7. Native Task Dependency Types

**Question**: Should native tasks support ALL Beads dependency types or subset?

**Answer**: **Subset - blocks + related** (selected 2 of 4)

**Supported**:
1. **blocks**: Task A blocks task B (essential for auto-ready detection)
2. **related**: Tasks are connected but non-blocking (useful for context)

**Not Supported** (can add later):
- `parent-child`: Hierarchical structure (defer to MVP+)
- `discovered-from`: Task provenance tracking (defer to MVP+)

**Implementation Impact**:
- Simpler JSONL schema for MVP
- Focus on core workflow (blocking dependencies)
- Related tasks provide context without complexity
- Can extend schema later without breaking changes

**JSONL Format**:
```jsonl
{"id":"tk-a1b2","title":"Auth","feature":"feature:auth","blocks":["tk-f3e4"],"related":[],"status":"ready"}
{"id":"tk-f3e4","title":"JWT","feature":"feature:auth","blocks":[],"related":["tk-a1b2"],"status":"blocked"}
```

---

## Summary of Decisions

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| Missing bd | Fail with error | Clear user guidance, explicit choice |
| Conflicts | Beads wins | Execution layer is source of truth |
| Task Creation | Auto-create | Smooth onboarding, less friction |
| Security | Trust user | Subprocess safety, user autonomy |
| Sync Timing | Multi-trigger | Flexible, configurable |
| Hash IDs | SHA256 truncated | Collision-resistant, git-friendly |
| Dependencies | blocks + related | MVP scope, extensible |

---

## Configuration Schema

Based on decisions, the config file structure:

```json
{
  "beads": {
    "executable": "bd",
    "default_path": ".ai/beads",
    "auto_create_tasks": true,
    "auto_sync": true,
    "sync_on_status_change": true,
    "sync_on_save": true,
    "sync_debounce_seconds": 1,
    "conflict_resolution": "beads-first"
  },
  "tasks": {
    "native_path": ".ai/tasks",
    "hash_algorithm": "sha256-4",
    "dependency_types": ["blocks", "related"]
  }
}
```

---

## Next Steps

✅ **Phase 2 Complete** - All ambiguities resolved

→ **Phase 3: Architect** - Design solution with trade-off analysis:
1. Class interfaces (BeadsBridge, TaskManager, TaskSync)
2. Data flow diagrams (sync logic)
3. Error handling patterns
4. Trade-off analysis (3 approaches)
5. ADR (Architecture Decision Record)
6. Populate spec-graph with components/operations
