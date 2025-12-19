# Clean Architecture Summary: Beads Integration

**Comprehensive Design Document**
**Status**: Complete - Ready for Implementation
**Date**: 2025-12-19

---

## Executive Summary

This document provides a complete clean architecture design for integrating Beads task management with know-cli. The design emphasizes:

- **Separation of Concerns**: Abstract factory pattern with independent implementations
- **Extensibility**: Easy to add future task systems without refactoring
- **Testability**: All components mockable with high test coverage
- **Long-term Maintainability**: SOLID principles throughout
- **User Experience**: Seamless Beads integration with native alternative

---

## Key Architectural Decisions

### 1. Abstract Factory Pattern

**Why**: Allows runtime switching between task systems without code changes

```
TaskManager (abstract interface)
├── BeadsTaskSystem (Beads wrapper)
└── NativeTaskSystem (JSONL-based)
```

**Benefits**:
- Clean interface contracts
- Testable with mocks
- Extensible for future systems
- Configuration-driven instantiation

**Trade-off**: More classes initially (~12 files), but pays off quickly with complexity

---

### 2. Beads as Source of Truth

**Decision** (from clarification.md #2):
- During sync conflicts: Beads status always wins
- Rationale: Beads is execution layer; tasks may be worked on outside know
- Graph status derives from reality via auto-sync

**Implementation**:
```python
# In TaskSyncCore._sync_beads_to_graph()
if beads_status != graph_status:
    conflicts.append({...})
    # Use beads status (policy: "beads-first")
```

---

### 3. Native JSONL System

**Why**: Zero external dependencies, git-friendly, collision-resistant IDs

**Format** (per clarification.md #6, #7):
- Hash ID: `tk-XXXX` (SHA256(title+timestamp)[:4])
- Dependencies: `blocks` and `related` (MVP scope)
- One JSON object per line (JSONL format)
- Supports basic task queries and auto-ready detection

**Schema**:
```jsonl
{"id":"tk-a1b2","title":"Task","feature_id":"feature:auth","status":"ready","dependencies":{"blocks":[],"related":[]},"created_at":"2025-12-19T10:00:00Z","updated_at":"2025-12-19T10:00:00Z","metadata":{}}
```

---

## Complete Class Hierarchy

### Task System Layer

```python
# Base abstractions
Task                    # Dataclass: canonical task representation
TaskStatus              # Enum: ready, in-progress, blocked, done, paused
DependencyType          # Enum: blocks, related
TaskManager             # ABC: abstract interface for all systems

# Implementations
BeadsTaskSystem(TaskManager)        # ~200 LOC
NativeTaskSystem(TaskManager)       # ~300 LOC

# Factory
TaskSystemFactory                   # Creates appropriate implementation
```

### Integration Layer

```python
# Beads specific
BeadsBridge             # Subprocess calls, JSONL parsing (~300 LOC)
  - is_available()
  - init_beads()
  - call_bd()
  - parse_jsonl()
  - read_issues()

# Sync engine
TaskSyncCore            # Bidirectional sync (~300 LOC)
  - sync(direction)
  - _sync_beads_to_graph()
  - _sync_graph_to_beads()

ConflictResolver        # Conflict resolution (~80 LOC)
  - resolve(task_id, beads_state, graph_state, policy)

# Infrastructure
HookRegistry            # Event system for auto-sync (~70 LOC)
ServiceContainer        # Dependency injection (~80 LOC)
```

### CLI Layer

```python
# Commands
know bd init            # Initialize Beads
know bd sync            # Manual sync
know bd list [--ready]  # List tasks
know bd add <title>     # Create task

know task init          # Initialize native tasks
know task add <title>   # Create task
know task list          # List tasks
know task done <id>     # Mark complete
know task block <id> --on <blocker>
know task ready         # Show ready tasks
```

---

## Data Flow Diagrams

### 1. Task Creation Flow

```
User runs: know bd add "Implement JWT"
          ↓
    BeadsTaskSystem.add_task()
          ↓
    BeadsBridge.call_bd(["add", "Implement JWT"])
          ↓
    subprocess.run(["bd", "add", "Implement JWT"])
          ↓
    Parse response → extract bead ID (bd-a1b2)
          ↓
    Create Task object
          ↓
    Emit TASK_CREATED hook
          ↓
    Auto-sync (if enabled)
          ↓
    Update spec-graph references.beads
```

### 2. Sync Flow

```
know bd sync
      ↓
TaskSyncCore.sync(direction=BIDIRECTIONAL)
      ├→ _sync_beads_to_graph()
      │   ├─ Get all tasks from TaskManager
      │   ├─ Check for conflicts with graph
      │   ├─ Apply beads-first policy
      │   └─ Update references.beads/tasks
      │
      └→ _sync_graph_to_beads()
          ├─ Find features without linked tasks
          ├─ Create new tasks in TaskManager
          └─ Update references

      ↓
Return SyncResult {
  tasks_synced: 5,
  conflicts_found: 1,
  conflicts: [{task_id: "bd-x", resolution: "beads won"}]
}
```

### 3. Auto-Ready Detection

```
Task completed: know task done tk-a1b2
        ↓
NativeTaskSystem.complete_task(tk-a1b2)
        ├─ Mark tk-a1b2 as DONE
        ├─ Find all tasks blocked by tk-a1b2
        ├─ Remove from blockers
        └─ Return updated task
        ↓
Emit TASK_COMPLETED hook
        ↓
Dependent tasks now appear in find_ready_tasks()
```

---

## Error Handling Strategy

### Exception Hierarchy

```
KnowTaskError (base)
├── TaskSystemError          # Config/availability
├── BeadsError              # Beads-specific
│   └── BeadsUnavailableError
├── TaskSyncError           # Sync operations
│   └── ConflictError
├── TaskValidationError     # Data validation
└── GraphError              # Graph operations
```

### Recovery Strategies

1. **Missing bd executable**
   ```
   raise BeadsUnavailableError(
     "bd not found. Install: https://github.com/steveyegge/beads"
   )
   ```

2. **Corrupt JSONL**
   ```
   # Skip malformed lines, log warning, continue
   # Doesn't break entire file parsing
   ```

3. **Sync conflicts**
   ```
   # Log conflict, apply policy, continue
   # Return conflicts in SyncResult for inspection
   ```

4. **Graph integration errors**
   ```
   # Graceful degradation
   # Native tasks work even if graph unavailable
   ```

---

## Integration Points with Know

### 1. Graph Save Hook

**Where**: `GraphManager.save_graph()`

```python
def save_graph(self, data):
    self._write_json(data)
    hooks.emit(HookEvent.GRAPH_SAVED)  # Trigger auto-sync
```

### 2. Auto-Create Tasks on Feature Add

**Where**: Entity add commands in CLI

```python
@cli.command('add')
def add(entity_type, name, ...):
    # Add entity to graph
    entities.add(entity_type, name, ...)

    # Auto-create task for features (if enabled)
    if entity_type == 'feature' and config['auto_create_tasks']:
        try:
            task_manager.add_task(
                title=name,
                feature_id=f"feature:{name}"
            )
        except:
            pass  # Silent fail - not all projects use tasks
```

### 3. Phase Status Changes

**Where**: Phase management commands

```python
# When feature moves to new phase
hooks.emit(HookEvent.FEATURE_STATUS_CHANGED,
    feature_id=feature_id,
    new_phase=phase,
    old_phase=old_phase)
```

---

## Configuration Schema

**Location**: `.ai/config.json`

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

## Complexity & Estimation

### Lines of Code by Component

| Component | Files | LOC | Complexity |
|-----------|-------|-----|------------|
| Base abstractions | 1 | 350 | Low |
| Beads bridge | 1 | 300 | Medium |
| Beads wrapper | 1 | 200 | Medium |
| Native system | 1 | 300 | Medium |
| Task sync | 1 | 300 | High |
| Conflict resolution | 1 | 100 | Medium |
| Hooks & DI | 2 | 150 | Medium |
| CLI commands | 2 | 400 | Low-Medium |
| Tests | 4 | 800 | High |
| **Total** | **14** | **2700** | **Medium-High** |

### Implementation Timeline

| Phase | Task | Duration | Type |
|-------|------|----------|------|
| 1 | Base abstractions & models | 2h | Design |
| 2 | Beads bridge & subprocess | 3h | Core |
| 3 | Beads wrapper implementation | 2h | Core |
| 4 | Native JSONL system | 3h | Core |
| 5 | Task sync & conflict resolution | 4h | Complex |
| 6 | Hooks & dependency injection | 2h | Infrastructure |
| 7 | CLI commands integration | 3h | Integration |
| 8 | Error handling & edge cases | 2h | Polish |
| 9 | Unit tests | 4h | QA |
| 10 | Integration tests | 3h | QA |
| 11 | Edge case & performance tests | 2h | QA |
| 12 | Documentation & release prep | 2h | Polish |
| **Total** | | **32 hours** | |

---

## File Structure

```
know/
├── src/
│   ├── task_system.py            # Base abstractions (350 LOC)
│   ├── beads_bridge.py           # Beads integration (300 LOC)
│   ├── beads_task_system.py      # Beads wrapper (200 LOC)
│   ├── native_task_system.py     # JSONL impl (300 LOC)
│   ├── task_sync.py              # Sync engine (300 LOC)
│   ├── conflict_resolution.py    # Conflicts (100 LOC)
│   ├── hooks.py                  # Event system (70 LOC)
│   ├── di.py                     # Dependency injection (80 LOC)
│   ├── exceptions.py             # Error hierarchy (60 LOC)
│   ├── schemas.py                # Type safety (100 LOC)
│   └── cli/
│       ├── beads_commands.py     # BD commands (200 LOC)
│       ├── task_commands.py      # Task commands (200 LOC)
│       └── error_messages.py     # User messages (100 LOC)
├── config/
│   └── task-system-config.json   # Default config
└── tests/
    ├── test_task_system.py
    ├── test_beads_bridge.py
    ├── test_beads_task_system.py
    ├── test_native_task_system.py
    ├── test_task_sync.py
    ├── test_cli_commands.py
    └── test_integration.py

.ai/
├── tasks/                        # Native tasks (if used)
│   ├── tasks.jsonl
│   └── .gitignore
├── beads/                        # Beads (if used)
│   ├── issues.jsonl
│   └── ...
└── config.json                   # Task system config
```

---

## Testing Strategy

### Unit Tests (70% coverage)

```python
# 8 test files, ~100 LOC each = 800 LOC

test_task_system.py
  - Task creation and properties
  - TaskStatus and DependencyType enums
  - TaskManager abstract methods

test_beads_bridge.py
  - Subprocess execution
  - JSONL parsing with error recovery
  - Symlink creation
  - bd availability check

test_beads_task_system.py
  - Task creation via bd
  - List/filter operations
  - Dependency management
  - Status updates

test_native_task_system.py
  - Hash ID generation
  - JSONL CRUD operations
  - Atomic updates
  - Auto-ready detection

test_task_sync.py
  - Beads-to-graph sync
  - Graph-to-beads sync (new tasks only)
  - Conflict detection and resolution
  - SyncResult validation

test_hooks.py
  - Hook registration
  - Event emission
  - Error handling in handlers

test_di.py
  - Service registration
  - Singleton management
  - Configuration loading

test_cli_commands.py
  - Command argument parsing
  - Error handling in CLI
  - Help text generation
```

### Integration Tests (10% additional coverage)

```python
test_beads_end_to_end.py
  - Full Beads workflow: init → create → sync → verify
  - Requires real bd or mock subprocess

test_native_end_to_end.py
  - Full native workflow: init → create → link → query
  - No external dependencies
```

### Edge Case Tests

```
- Missing bd executable → helpful error
- Corrupt JSONL → graceful recovery
- Sync conflicts → beads-first policy
- Large task sets (1000+) → performance OK
- Circular dependencies → detection/prevention
- Orphaned references → cleanup
```

**Target Coverage**: 80%+ overall

---

## Trade-offs & Justification

### Complexity vs Completeness

**Selected**: Abstract Factory Pattern (Score: A)

| Approach | Pros | Cons | Score |
|----------|------|------|-------|
| **Monolithic** | Simple initially | Hard to switch, not extensible | C |
| **Adapter Pattern** | Good for Beads | Still need full native impl | B |
| **Factory (Selected)** | Clean separation, extensible, testable | More files initially | A |

**Justification**: While factory pattern requires more initial setup (~2700 LOC), it provides:
- Zero coupling between implementations
- Easy to swap or add systems
- Testable with mocks
- Follows SOLID principles
- Pays for itself within 2 phases of development

---

## Success Criteria

1. ✅ Both systems work independently
2. ✅ `know bd` and `know task` command groups functional
3. ✅ Sync preserves all metadata
4. ✅ Conflicts resolved per policy (beads-first)
5. ✅ Native system requires zero external dependencies
6. ✅ JSONL format human-readable and git-mergeable
7. ✅ Feature parity between Beads and Native
8. ✅ Error messages guide users to solutions
9. ✅ No breaking changes to existing know
10. ✅ 80%+ test coverage
11. ✅ Docs explain architecture and usage
12. ✅ Marketing: "Seamless Beads Integration"

---

## Next Steps

### Phase 1: Foundation (Days 1-2)
- [ ] Implement base abstractions (task_system.py)
- [ ] Create Beads bridge (beads_bridge.py)
- [ ] Add error hierarchy (exceptions.py)
- [ ] 100% test coverage for Phase 1

### Phase 2: Core Implementation (Days 3-4)
- [ ] Beads TaskManager wrapper
- [ ] Native JSONL system
- [ ] Task sync engine
- [ ] Conflict resolution
- [ ] 80%+ test coverage

### Phase 3: Integration (Days 5)
- [ ] CLI commands
- [ ] DI & hooks
- [ ] Config system
- [ ] Auto-sync integration
- [ ] Edge case handling

### Phase 4: Testing & Polish (Days 6-7)
- [ ] Integration tests
- [ ] Performance testing
- [ ] Documentation
- [ ] Release preparation

---

## References

- **Clarification Q&A**: `qa/clarification.md` (all decisions justified)
- **Architecture Details**: `architecture-design.md` (full class specs)
- **Implementation Guide**: `implementation-guide.md` (concrete code examples)
- **Feature Overview**: `overview.md`
- **Planning Notes**: `plan.md`
- **Todo Checklist**: `todo.md`
- **Beads Repository**: https://github.com/steveyegge/beads
- **Know Core**: See `CLAUDE.md` for dual graph system details

---

## Architecture Principles

### 1. Separation of Concerns
Each class has one responsibility:
- `BeadsBridge`: Subprocess calls only
- `BeadsTaskSystem`: Logic for Beads
- `NativeTaskSystem`: Logic for native JSONL
- `TaskSyncCore`: Sync orchestration
- `HookRegistry`: Event management

### 2. Dependency Injection
All dependencies injected, enabling:
- Easy mocking for tests
- Configuration-driven behavior
- Future feature toggles

### 3. Graceful Degradation
- Native tasks work without Beads
- Auto-sync fails silently if disabled
- Missing features don't break core
- Helpful errors guide users

### 4. SOLID Principles

| Principle | Implementation |
|-----------|-----------------|
| Single Responsibility | Each class has one job |
| Open/Closed | Open for extension (new systems), closed for modification |
| Liskov Substitution | BeadsTaskSystem & NativeTaskSystem interchangeable |
| Interface Segregation | TaskManager interface is minimal |
| Dependency Inversion | Depends on abstractions, not implementations |

---

**Design Status**: Complete & Ready for Implementation
**Confidence Level**: 95% (architecture is sound, will adjust details during implementation)
**Next Action**: Begin Phase 1 implementation with base abstractions
