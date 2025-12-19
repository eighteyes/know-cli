# Architecture Decision Records: Beads Integration

## ADR-001: Architecture Approach Selection

**Date**: 2025-12-19

**Status**: ACCEPTED

**Context**:
We evaluated three architectural approaches for integrating Beads task management into know-cli:

1. **MINIMAL WRAPPER** (283 LOC, 4-6 hours)
   - Thin subprocess wrapper around `bd` commands
   - Store task metadata in graph references only
   - Minimal abstraction, direct command passthrough

2. **FULL-FEATURED MVP** (2450 LOC, 25-30 hours)
   - Abstract factory pattern with TaskManager interface
   - Complete bidirectional sync with auto-triggers
   - Full dependency type support (blocks, parent-child, discovered-from, related)
   - Advanced conflict resolution UI

3. **PRAGMATIC BALANCED** (900 LOC, 10-12 hours)
   - Three-layer architecture (CLI → Business Logic → Data)
   - Both Beads AND native task systems in Phase 1
   - Manual sync (auto-sync deferred to Phase 2)
   - Plugin-ready via dependency injection
   - Subset of dependencies (blocks + related only)

**Decision**:
We selected the **PRAGMATIC BALANCED** approach for Phase 1 MVP.

**Rationale**:

**Why NOT MINIMAL**:
- Too limited: No native task system, missing core functionality
- No extensibility path without major refactoring
- Would require rewrite for Phase 2 features
- Doesn't deliver enough user value (just a subprocess wrapper)

**Why NOT FULL-FEATURED**:
- Over-engineered for MVP: 2450 LOC is excessive
- 25-30 hour timeline too long for initial delivery
- Complex factory patterns add unnecessary abstraction
- High risk of scope creep and bugs
- Delays user feedback cycle

**Why PRAGMATIC BALANCED**:
- **Best value**: Delivers both Beads AND native task systems
- **User choice**: Users can choose system without lock-in
- **Extensibility**: Plugin architecture via abstract base classes
- **Reasonable timeline**: 10-12 hours achievable in 1-2 days
- **Clear upgrade path**: Phase 2 features can be added incrementally
- **Well-documented**: Comprehensive risk analysis and mitigation
- **Pragmatic trade-offs**: Manual sync is acceptable for MVP

**Accepted Trade-offs**:

1. **Manual sync in Phase 1**
   - Trade-off: Users must run `know bd sync` explicitly
   - Benefit: Simpler implementation, predictable behavior
   - Phase 2: Add auto-sync with configurable triggers

2. **Subset of dependency types**
   - Trade-off: Only blocks + related (no parent-child, discovered-from)
   - Benefit: Simpler JSONL schema, focus on core workflow
   - Phase 2: Add full dependency type support

3. **No caching layer**
   - Trade-off: Re-parse JSONL on every read
   - Benefit: Simpler code, no cache invalidation complexity
   - Phase 2: Add GraphCache integration if performance issues

4. **No conflict resolution UI**
   - Trade-off: Beads-first strategy is hardcoded
   - Benefit: Predictable behavior, clear source of truth
   - Phase 2: Add interactive conflict resolution

5. **No bidirectional sync**
   - Trade-off: Graph → Beads is one-way (create tasks only)
   - Benefit: Simpler sync logic, fewer edge cases
   - Phase 2: Add full bidirectional sync

**Consequences**:

**Positive**:
- Delivers user value quickly (10-12 hours)
- Both task systems available from day one
- Plugin-ready architecture enables future backends
- Clear separation of concerns (CLI, Business Logic, Data)
- Comprehensive error handling (fail early, help fast)
- Well-tested with clear success criteria

**Negative**:
- Users must manually sync (Phase 1 limitation)
- Limited dependency types initially
- No automatic task creation hooks (Phase 1)

**Risks and Mitigations**:

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Beads CLI changes | Medium | High | Version detection, graceful degradation |
| JSONL corruption | Low | High | Atomic writes, backup on corruption |
| Hash collision | Very Low | Medium | SHA256 truncation, collision detection |
| Subprocess failure | Medium | Medium | Comprehensive error handling, user feedback |
| Sync conflicts | Medium | Medium | Beads-first strategy, conflict logging |

**Implementation Plan**:

**Phase 1 MVP** (10-12 hours):
- BeadsBridge (200 LOC): Subprocess wrapper, JSONL parsing
- TaskManager (250 LOC): Native JSONL task management
- TaskSync (150 LOC): Import, link, status sync
- CLI Commands (200 LOC): `know bd` + `know task` groups
- Tests (100 LOC): Core functionality coverage
- Integration (100 LOC): Manager initialization

**Phase 2 Enhancements** (8-10 hours, deferred):
- Auto-sync hooks on graph changes
- Bidirectional sync (graph → Beads updates)
- Full dependency type support
- Interactive conflict resolution
- GraphCache integration

**Success Criteria**:
- [ ] `know bd init` creates `.ai/beads/` with symlink
- [ ] `know bd add "task title"` creates task via Beads
- [ ] `know bd list` shows tasks from Beads JSONL
- [ ] `know bd sync` imports Beads tasks to graph references
- [ ] `know task init` creates `.ai/tasks/tasks.jsonl`
- [ ] `know task add "task title"` creates native task
- [ ] `know task list` shows tasks from native JSONL
- [ ] `know task ready` shows auto-detected ready tasks
- [ ] Missing `bd` executable shows helpful error
- [ ] All tests pass
- [ ] Graph validates successfully

**Alternatives Considered**:
- SQLite backend: Rejected (overkill for MVP, JSONL is git-friendly)
- Auto-sync in Phase 1: Rejected (increases complexity, delays delivery)
- Beads-only (no native): Rejected (creates vendor lock-in)
- Native-only (no Beads): Rejected (doesn't meet user request)

---

## ADR-002: Error Handling Philosophy

**Date**: 2025-12-19

**Status**: ACCEPTED

**Decision**: "Fail Early, Help Fast" error handling strategy

**Context**:
Beads integration involves subprocess execution, JSONL parsing, and external tool dependencies. Error handling philosophy affects user experience and debugging.

**Philosophy**:
1. **FAIL EARLY**: Detect errors at operation boundaries, no silent fallbacks
2. **HELP FAST**: Provide actionable error messages with next steps
3. **NO SURPRISES**: Explicit user choice, no automatic system switching

**Implementation**:

```python
# Missing bd executable
if not shutil.which('bd'):
    console.print("[red]✗ bd not found. Install Beads first:[/red]")
    console.print("  https://github.com/steveyegge/beads")
    sys.exit(1)

# Subprocess failure
result = subprocess.run(['bd'] + args, capture_output=True, text=True)
if result.returncode != 0:
    console.print(f"[red]✗ bd command failed:[/red] {result.stderr}")
    console.print(f"[yellow]Command:[/yellow] bd {' '.join(args)}")
    return {'success': False, 'error': result.stderr}

# JSONL parsing error
try:
    task = json.loads(line)
except json.JSONDecodeError as e:
    console.print(f"[red]✗ Corrupted JSONL at line {line_num}:[/red]")
    console.print(f"  {line[:100]}...")
    console.print(f"[yellow]Run 'know task validate' to check file integrity[/yellow]")
    return None
```

**Rationale**:
- Users prefer clear error messages over silent failures
- Explicit failures enable debugging and troubleshooting
- Actionable next steps reduce user frustration
- No silent fallbacks prevents unexpected behavior

---

## ADR-003: Beads-First Conflict Resolution

**Date**: 2025-12-19

**Status**: ACCEPTED

**Decision**: Beads is the source of truth for task status

**Context**:
When syncing between Beads and spec-graph, task status may differ (e.g., Beads shows "done" but graph shows "in-progress").

**Resolution Strategy**:
```
BEADS → GRAPH (status updates)
GRAPH → BEADS (new task creation only)
```

**Rationale**:
1. **Beads is the execution layer**: Tasks are worked on in Beads CLI
2. **Graph is the planning layer**: Features/objectives are higher-level
3. **Users work in both contexts**: Tasks may be updated outside know
4. **Clear ownership**: Beads owns task state, graph owns feature state

**Implementation**:
```python
def sync_status(self):
    """Sync task status from Beads to graph references."""
    beads_tasks = self.bridge.parse_beads_jsonl()

    for task in beads_tasks:
        # Beads status overwrites graph status
        graph_ref = self.graph.get_reference('beads', task['id'])
        if graph_ref and graph_ref.get('status') != task['status']:
            logger.info(f"Overwriting graph status for {task['id']}: "
                       f"{graph_ref['status']} → {task['status']}")
            self.graph.update_reference('beads', task['id'], {
                'status': task['status'],
                'updated': datetime.utcnow().isoformat()
            })
```

**Consequences**:
- Graph references may be stale until sync runs
- Manual sync required to update graph (Phase 1 limitation)
- Clear audit trail via logging

---

## ADR-004: Hash-Based Task IDs

**Date**: 2025-12-19

**Status**: ACCEPTED

**Decision**: Use SHA256(title + timestamp) truncated to 4 hex chars

**Format**: `tk-a1b2` (native tasks), `bd-a1b2` (Beads tasks)

**Rationale**:
1. **Git-merge friendly**: Hash-based IDs avoid conflicts in distributed workflows
2. **Collision-resistant**: SHA256[:4] = 65,536 combinations per second
3. **Deterministic**: Reproducible from inputs (title + timestamp)
4. **Matches Beads pattern**: Consistent with Beads ID format

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

**Collision Probability**:
- 65,536 IDs per second before 50% collision probability
- Expected collision: ~256 tasks created in same second with same title
- Mitigation: Add millisecond precision if collisions detected

---

## ADR-005: MVP Dependency Types

**Date**: 2025-12-19

**Status**: ACCEPTED

**Decision**: Support only `blocks` and `related` dependency types in Phase 1

**Supported**:
1. **blocks**: Task A blocks task B (essential for auto-ready detection)
2. **related**: Tasks are connected but non-blocking (useful for context)

**Deferred to Phase 2**:
- `parent-child`: Hierarchical task structure
- `discovered-from`: Task provenance tracking

**Rationale**:
1. **MVP scope**: Focus on core workflow (blocking dependencies)
2. **Simpler schema**: Easier JSONL format, fewer edge cases
3. **Auto-ready detection**: `blocks` enables task readiness calculation
4. **Extensible**: Can add more types without breaking schema

**JSONL Format**:
```jsonl
{"id":"tk-a1b2","title":"Auth","feature":"feature:auth","blocks":["tk-f3e4"],"related":[],"status":"ready"}
{"id":"tk-f3e4","title":"JWT","feature":"feature:auth","blocks":[],"related":["tk-a1b2"],"status":"blocked"}
```

**Upgrade Path**:
Phase 2 can add new fields without breaking existing data:
```jsonl
{"id":"tk-a1b2","title":"Auth","blocks":["tk-f3e4"],"related":[],"parent":"tk-root","discovered_from":"tk-spike","status":"ready"}
```

---

## Summary

These ADRs document the foundational decisions for the Beads integration feature:

1. **ADR-001**: PRAGMATIC BALANCED approach (900 LOC, 10-12 hours)
2. **ADR-002**: Fail Early, Help Fast error handling
3. **ADR-003**: Beads-First conflict resolution
4. **ADR-004**: SHA256-based hash IDs
5. **ADR-005**: MVP dependency types (blocks + related)

All decisions prioritize:
- **Fast delivery**: 10-12 hour implementation timeline
- **User value**: Both Beads AND native task systems
- **Clear behavior**: No silent fallbacks, explicit errors
- **Extensibility**: Plugin architecture for Phase 2+ features
- **Pragmatic trade-offs**: Defer complexity, ship MVP quickly
