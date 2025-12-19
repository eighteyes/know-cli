# Integration Architecture Diagrams

**Visual Reference for Beads Integration Design**
**Companion to**: `ARCHITECTURE-SUMMARY.md` and `architecture-design.md`

---

## 1. System Architecture Layers

```
┌────────────────────────────────────────────────────────────────┐
│  CLI Interface Layer                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ know bd *    │  │ know task *  │  │  know ...    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼───────────────────┼────────────────┼─────────────────┘
          │                   │                │
┌─────────▼───────────────────▼────────────────▼─────────────────┐
│  API/Command Layer                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │  BeadsCommands      │  │  TaskCommands       │            │
│  │  (bd, sync, list)   │  │  (add, done, ready) │            │
│  └──────────┬───────────┘  └──────────┬──────────┘            │
└─────────────┼──────────────────────────┼──────────────────────┘
              │                          │
┌─────────────▼──────────────────────────▼──────────────────────┐
│  Domain/Business Logic Layer                                   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  TaskManager (Abstract Interface)                       │   │
│  │  ├─ add_task()     ├─ list_tasks()   ├─ complete()     │   │
│  │  ├─ find_ready()   ├─ get_task()     ├─ update()       │   │
│  │  └─ dependencies() └─ sync_status()  └─ validate()     │   │
│  └────────────┬──────────────────┬──────────────────────┘    │
└───────────────┼──────────────────┼────────────────────────────┘
                │                  │
      ┌─────────▼──────┐  ┌────────▼─────────┐
      │ BeadsTaskSystem│  │NativeTaskSystem  │
      │                │  │                  │
      │ (200 LOC)      │  │ (300 LOC)        │
      │ - call bd      │  │ - JSONL file I/O │
      │ - parse JSON   │  │ - hash IDs       │
      │ - parse JSONL  │  │ - auto-ready     │
      └────────┬───────┘  └────────┬─────────┘
               │                   │
┌──────────────▼───────────────────▼──────────────────────┐
│  Sync & Integration Layer                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  TaskSyncCore (300 LOC)                            │ │
│  │  ├─ sync(direction)                                │ │
│  │  ├─ _sync_beads_to_graph()                         │ │
│  │  ├─ _sync_graph_to_beads()                         │ │
│  │  ├─ detect_conflicts()                             │ │
│  │  └─ reconcile_state()                              │ │
│  └────────┬──────────────────────────────────────────┘ │
│           │                                             │
│  ┌────────▼──────────────────────────────────────────┐ │
│  │  HookRegistry (Event System)                       │ │
│  │  ├─ TASK_CREATED                                  │ │
│  │  ├─ FEATURE_STATUS_CHANGED                        │ │
│  │  └─ GRAPH_SAVED                                   │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
               │                         │
┌──────────────▼──────────────┐  ┌──────▼──────────────────┐
│ Data/Persistence Layer       │  │ Infrastructure Layer   │
│                              │  │                        │
│ ┌────────────────────────┐  │  │ ┌───────────────────┐  │
│ │ .ai/beads/             │  │  │ │ ServiceContainer  │  │
│ │ issues.jsonl           │  │  │ │ (DI setup)        │  │
│ │                        │  │  │ │                   │  │
│ │ .ai/tasks/             │  │  │ └───────────────────┘  │
│ │ tasks.jsonl            │  │  │                        │
│ │                        │  │  │ ┌───────────────────┐  │
│ │ spec-graph.json        │  │  │ │ BeadsBridge       │  │
│ │ references.beads/      │  │  │ │ (subprocess)      │  │
│ │ references.tasks       │  │  │ │                   │  │
│ └────────────────────────┘  │  │ └───────────────────┘  │
└─────────────────────────────┘  └───────────────────────┘
         │
    ┌────▼────────┬────────────┐
    ▼             ▼            ▼
  Files         bd CLI      Graph
 (JSONL)        (Beads)   (JSON)
```

---

## 2. Class Dependency Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TaskManager                              │
│                    (ABC)                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ + add_task()                                         │  │
│  │ + list_tasks()                                       │  │
│  │ + find_ready_tasks()                                 │  │
│  │ + complete_task()                                    │  │
│  │ + add_dependency()                                   │  │
│  │ + is_available()                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │ implements
      ┌────────────┴────────────┐
      │                         │
      ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│ BeadsTaskSystem  │    │ NativeTaskSystem     │
│                  │    │                      │
│ + __init__()     │    │ + __init__()         │
│ + add_task()     │    │ + add_task()         │
│ + list_tasks()   │    │ + list_tasks()       │
│ + get_task()     │    │ + _generate_id()     │
│ + complete()     │    │ + _read_all_tasks()  │
│ + dependencies() │    │ + _write_all_tasks() │
│ + is_available() │    │ + is_available()     │
│                  │    │                      │
└────────┬─────────┘    └──────────────────────┘
         │
         │ uses
         ▼
   ┌──────────────────────┐
   │ BeadsBridge          │
   │                      │
   │ + is_available()     │
   │ + init_beads()       │
   │ + call_bd()          │
   │ + parse_jsonl()      │
   │ + read_issues()      │
   │ + _update_gitignore()│
   └──────────────────────┘


┌────────────────────────────────────────┐
│ TaskSyncCore                           │
│                                        │
│ - task_manager: TaskManager            │ uses
│ - graph_manager: GraphManager          │─────┐
│                                        │     │
│ + sync(direction)                      │     ▼
│ + _sync_beads_to_graph()               │  ┌──────────────────┐
│ + _sync_graph_to_beads()               │  │ GraphManager     │
│ + detect_conflicts()                   │  │                  │
│ + reconcile_state()                    │  │ (existing know)  │
│                                        │  └──────────────────┘
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ ConflictResolver                       │
│                                        │
│ + resolve(task, beads, graph, policy)  │
│   → returns resolved state              │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ HookRegistry                           │
│                                        │
│ - hooks: Dict[Event, List[Callable]]   │
│ + register(event, handler)             │
│ + emit(event, **kwargs)                │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ ServiceContainer (DI)                  │
│                                        │
│ - services: Dict                       │
│ - singletons: Dict                     │
│ + register(name, factory, singleton)   │
│ + get(name) → instance                 │
│ + load_config()                        │
└────────────────────────────────────────┘
```

---

## 3. Data Flow: Task Creation

```
User enters:  know bd add "Implement JWT" --feature feature:auth

                              ▼

┌─ CLI Layer ─────────────────────────────────────┐
│ beads_add(title="Implement JWT",                │
│           feature="feature:auth")                │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌─ API Layer ──────────────────────────────────────┐
│ task_manager.add_task(                           │
│     title="Implement JWT",                       │
│     feature_id="feature:auth"                    │
│ )                                                │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────────┐
         │ Instance type?          │
         │                         │
         └┬──────────────────────┬─┘
          │                      │
      Beads?                Native?
          │                      │
          ▼                      ▼
   ┌──────────────┐      ┌──────────────┐
   │BeadsBridge   │      │Generate ID   │
   │ call_bd      │      │tk-XXXX       │
   │ ["add", ...] │      │              │
   └──────┬───────┘      └──────┬───────┘
          │                     │
          ▼                     ▼
    subprocess.run       Append to JSONL
    (["bd", "add",       {
      "Implement JWT"])    "id": "tk-a1b2",
                           "title": "...",
          │                "feature_id": "...",
          │                "status": "ready",
          ▼                ...
    Parse output        }
    Extract: bd-a1b2
          │                     │
          └─────────┬───────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │ Return Task object:    │
        │ {                      │
        │   id: "bd-a1b2" | ...  │
        │   title: "...",        │
        │   feature_id: "...",   │
        │   status: "ready",     │
        │   ...                  │
        │ }                      │
        └──────────┬─────────────┘
                   │
                   ▼
        ┌────────────────────────┐
        │ HookRegistry.emit      │
        │ (TASK_CREATED, ...)    │
        └──────────┬─────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
      Auto-sync             Other
      enabled?              handlers
        │
        ▼
    TaskSyncCore.sync()
    (Update graph)
        │
        ▼
    references.beads/tasks
    updated
        │
        ▼
    ✓ Success
```

---

## 4. Data Flow: Bidirectional Sync

```
User enters: know bd sync

                    ▼

┌─ Sync Flow ────────────────────────────────┐
│ TaskSyncCore.sync(direction=BIDIRECTIONAL) │
└────────────────┬──────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
 Phase 1:                  Phase 2:
 Beads → Graph            Graph → Beads

Phase 1: Import Beads Status
──────────────────────────────

Read all tasks from       Compare with
TaskManager               graph state
    │                           │
    ├─ tk-a1b2: ready      ├─ refs.tasks.tk-a1b2
    ├─ tk-f3e4: blocked         │
    └─ tk-x1y2: done           status: "in-progress"
                                 (CONFLICT!)
           │                     │
           └─────────┬───────────┘
                     │
              Apply Policy:
              "beads-first"
                     │
                     ▼
         Use Beads status: "ready"
              Log conflict
                     │
                     ▼
         Update graph:
         references.tasks.tk-a1b2 = {
           "status": "ready",
           "title": "...",
           "feature": "...",
           "updated": "2025-12-19T..."
         }
                     │
                     ▼
         Return SyncResult {
           tasks_synced: 3,
           conflicts_found: 1,
           conflicts: [
             {task_id: "tk-a1b2",
              beads_status: "ready",
              graph_status: "in-progress",
              resolution: "beads won"}
           ]
         }


Phase 2: Create New Tasks from Features
────────────────────────────────────────

Get all features          Get existing
from graph                task refs
    │                           │
    ├─ feature:auth        ├─ tk-a1b2 → auth
    ├─ feature:api             │
    └─ feature:db              ├─ tk-f3e4 → api
                               │
                               └─ none → db
           │                     │
           └─────────┬───────────┘
                     │
              Find unmapped:
              feature:db (no task)
                     │
                     ▼
         Create task in TaskManager
         task_manager.add_task(
           title="db",
           feature_id="feature:db"
         )
                     │
                     ▼
         Returns: Task(
           id="tk-newid",
           feature_id="feature:db",
           status="ready"
         )
                     │
                     ▼
         Update graph:
         references.tasks.tk-newid = {
           "title": "db",
           "feature": "feature:db",
           "status": "ready"
         }
                     │
                     ▼
         Return SyncResult {
           tasks_synced: 1,
           conflicts_found: 0
         }

                 │
                 ▼
    ┌────────────────────────────────┐
    │ Combine results:               │
    │ total_synced: 4                │
    │ total_conflicts: 1             │
    │ all_conflicts: [...]           │
    └────────────────────────────────┘
                 │
                 ▼
    ✓ Sync Complete
```

---

## 5. Auto-Ready Detection Flow

```
Task 1: "Implement JWT"
  - blocks: [Task 2]
  - status: ready

Task 2: "Add refresh endpoint"
  - blocks: []
  - blocked_by: [Task 1]
  - status: blocked

Task 3: "Write tests"
  - blocks: []
  - blocked_by: []
  - status: ready


User: know task done tk-a1b2 (Task 1)

        ▼

TaskManager.complete_task("tk-a1b2")
        │
        ▼
Update Task 1 status: ready → done
        │
        ▼
Find all tasks blocked by tk-a1b2
        │
        ▼
Find Task 2 (blocked_by: [tk-a1b2])
        │
        ▼
Remove tk-a1b2 from Task 2 blocked_by
Task 2 blocked_by: [] ← NOW READY!
        │
        ▼
Rewrite JSONL with updates

Updated state:
──────────────
Task 1: done (no changes to blocking)
Task 2: blocked → ready (auto-promoted!)
Task 3: ready (unchanged)

        ▼

know task ready (shows ready tasks)
──────────────────────────────────────
Ready Tasks:
  tk-f3e4: Add refresh endpoint  ✓ (NOW AVAILABLE)
  tk-x1y2: Write tests
```

---

## 6. Sync Conflict Resolution

```
Scenario: Task status diverged

Beads/Task System:
  bd-a1b2 → status: "done"

Spec-Graph:
  references.beads.bd-a1b2 → status: "in-progress"

                    ▼

ConflictResolver.resolve(
    task_id="bd-a1b2",
    beads_state={status: "done"},
    graph_state={status: "in-progress"},
    policy="beads-first"
)

                    ▼

Apply Policy: "beads-first"
  → return beads_state

                    ▼

Update graph:
  references.beads.bd-a1b2.status = "done"

Log conflict:
  {
    task_id: "bd-a1b2",
    beads_status: "done",
    graph_status: "in-progress",
    resolution: "beads won",
    reason: "Beads is source of truth"
  }

                    ▼

Return to user:
  "⚠ Conflict resolved for bd-a1b2:
   Beads status (done) used, graph was (in-progress)"

Rationale:
──────────
Beads is execution layer. Tasks may be worked on
outside know context. Graph status should derive
from reality, not override it.
```

---

## 7. Configuration Flow

```
Application Start: know ...

        ▼

├─ Try load .ai/config.json
│  (if exists)
│
└─ Use default config if not found

        ▼

┌────────────────────────────────┐
│ Config loaded:                 │
│ {                              │
│   task_system: "native" or     │
│               "beads"          │
│   beads: {                     │
│     auto_sync: true,           │
│     conflict_resolution:       │
│       "beads-first",           │
│     ...                        │
│   },                           │
│   tasks: {                     │
│     native_path: ".ai/tasks",  │
│     ...                        │
│   }                            │
│ }                              │
└────────────┬───────────────────┘
             │
             ▼

ServiceContainer.load_config()

        ▼

┌─ Determine task system ─┐
│                         │
└─ beads? ──┬── native?  ─┘
            │        │
            │        ▼
            │   NativeTaskSystem(
            │     ".ai/tasks"
            │   )
            │
            ▼
      BeadsTaskSystem(
        ".ai/beads"
      )

        ▼

Register in DI:
  container.register(
    'task_manager',
    task_system_instance,
    singleton=True
  )

        ▼

Setup hooks:
  if config['auto_sync']:
    hooks.register(
      HookEvent.GRAPH_SAVED,
      on_graph_saved_handler
    )

        ▼

Ready to use:
  task_manager = container.get('task_manager')
```

---

## 8. Error Handling Flow

```
Operation fails (any layer)

            ▼

┌─ Determine error type ────────────┐
│                                   │
└─ BeadsError?                      │
   ├─ bd not found                  │
   │  └→ BeadsUnavailableError      │
   │     └→ Show install instructions│
   │                                │
   ├─ subprocess timeout            │
   │  └→ BeadsError                 │
   │     └→ Retry with backoff      │
   │                                │
   └─ parse JSONL error             │
      └→ BeadsError                 │
         └→ Skip line, continue     │

└─ TaskSyncError?                   │
   ├─ conflict detected             │
   │  └→ ConflictError              │
   │     └→ Apply policy (beads-win)│
   │                                │
   └─ sync failed                   │
      └→ Log & continue             │

└─ TaskValidationError?             │
   └→ Invalid task data             │
      └→ Reject & inform user       │

└─ GraphError?                      │
   └→ Graph file issue              │
      └→ Fail gracefully            │

            ▼

Error handling strategy:
  1. Log error (all systems see it)
  2. Decide: fail or graceful degrade
  3. If fail: raise user-facing exception
  4. If degrade: skip operation, continue
  5. Return error in result (e.g., SyncResult)

            ▼

User feedback:
  - CLI: Click error output + exit code
  - API: Exception with helpful message
  - Logs: Full stack trace
  - Results: Error list in result objects

Example:
────────
❌ Sync failed: 1 error(s)
  - Task tk-a1b2: Field 'title' required

✓ Synced 4 tasks (1 skipped)
```

---

## 9. Extension Points (Future Systems)

```
Current:
  ├─ BeadsTaskSystem
  └─ NativeTaskSystem

Future possibilities:
  ├─ AsanaTaskSystem(TaskManager)
  ├─ JiraTaskSystem(TaskManager)
  ├─ GithubIssuesTaskSystem(TaskManager)
  ├─ LinearTaskSystem(TaskManager)
  └─ NotionTaskSystem(TaskManager)

All implement TaskManager interface:

  class CustomTaskSystem(TaskManager):
    def is_available(self): ...
    def add_task(self, title, ...): ...
    def list_tasks(self, ...): ...
    def complete_task(self, task_id): ...
    def add_dependency(self, from, to): ...
    def find_ready_tasks(self): ...

Register in factory:
  TaskSystemFactory.create() {
    if config['task_system'] == 'asana':
      return AsanaTaskSystem(config)
    elif config['task_system'] == 'notion':
      return NotionTaskSystem(config)
    ...
  }

No other code changes needed!
```

---

## 10. Testing Architecture

```
┌─ Unit Tests ──────────────────────────────────┐
│                                               │
│  test_beads_bridge.py (150 LOC)               │
│  ├─ test_is_available()                      │
│  ├─ test_init_creates_symlink()              │
│  ├─ test_call_bd_success()                   │
│  ├─ test_call_bd_timeout()                   │
│  └─ test_parse_jsonl_corrupt()               │
│                                               │
│  test_native_task_system.py (200 LOC)        │
│  ├─ test_add_task_hash_id()                  │
│  ├─ test_complete_unblocks_deps()            │
│  ├─ test_find_ready_tasks()                  │
│  ├─ test_jsonl_recovery()                    │
│  └─ test_large_task_set()                    │
│                                               │
│  test_task_sync.py (250 LOC)                 │
│  ├─ test_sync_beads_to_graph()               │
│  ├─ test_conflict_beads_first()              │
│  ├─ test_sync_export_new_only()              │
│  └─ test_sync_result_structure()             │
│                                               │
└─ Mocks ──────────────────────────────────────┘
   ├─ MockBeadsBridge (for testing without bd)
   ├─ MockTaskManager (for testing sync)
   ├─ MockGraphManager (for testing sync)
   └─ MockHookRegistry (for testing events)


┌─ Integration Tests ───────────────────────────┐
│                                               │
│  test_beads_integration.py                   │
│  ├─ End-to-end Beads workflow                │
│  ├─ Requires real bd or mocked subprocess    │
│  └─ Verifies sync with real graph            │
│                                               │
│  test_native_integration.py                  │
│  ├─ End-to-end native workflow               │
│  ├─ Creates real JSONL files                 │
│  └─ Verifies auto-ready detection            │
│                                               │
└───────────────────────────────────────────────┘


┌─ Property-Based Tests ────────────────────────┐
│ (using hypothesis)                            │
│                                               │
│  - Random task creation stays consistent      │
│  - ID collisions impossible (prove math)      │
│  - Dependency cycles prevented                │
│  - Sync is idempotent (run twice = same)      │
│                                               │
└───────────────────────────────────────────────┘
```

---

## Summary

This architecture provides:

1. **Clean Separation** - Independent implementations, testable components
2. **Extensibility** - Factory pattern allows new systems without refactoring
3. **Reliability** - Error handling at every layer, graceful degradation
4. **Performance** - Efficient JSONL handling, no database overhead
5. **Maintainability** - SOLID principles, well-documented interfaces
6. **User Experience** - Helpful errors, seamless task management

The design is ready for implementation!
