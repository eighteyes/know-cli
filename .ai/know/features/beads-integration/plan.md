# Implementation Plan: Beads Integration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Know CLI                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Beads Bridge    │         │  Task Manager    │         │
│  │                  │         │  (Native)        │         │
│  │  - init_beads()  │         │  - add_task()    │         │
│  │  - call_bd()     │         │  - list_tasks()  │         │
│  │  - sync_beads()  │         │  - find_ready()  │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                            │                    │
│           │    ┌──────────────────┐    │                    │
│           └───▶│  Beads Sync      │◀───┘                    │
│                │                  │                          │
│                │  - import_beads()│                          │
│                │  - export_graph()│                          │
│                │  - link_feature()│                          │
│                └────────┬─────────┘                          │
│                         │                                    │
│                         ▼                                    │
│                ┌─────────────────┐                           │
│                │  spec-graph.json│                           │
│                │  references.    │                           │
│                │    beads/tasks  │                           │
│                └─────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
  ┌─────────────┐                        ┌─────────────┐
  │ .ai/beads/  │                        │ .ai/tasks/  │
  │ (symlinked  │                        │             │
  │  to .beads) │                        │ tasks.jsonl │
  │             │                        │ cache.db    │
  │ issues.jsonl│                        └─────────────┘
  └─────────────┘
         │
         ▼
  ┌─────────────┐
  │ bd (Beads)  │
  │ CLI tool    │
  └─────────────┘
```

## Component Details

### 1. Beads Bridge (`know/src/beads_bridge.py`)

**Purpose**: Interface layer between know and Beads CLI

**Key Methods**:
```python
class BeadsBridge:
    def __init__(self, beads_path: str = ".ai/beads"):
        """Initialize bridge with custom beads directory"""

    def init_beads(self, stealth: bool = False) -> bool:
        """
        Setup Beads integration:
        1. Create .ai/beads/ directory
        2. Create symlink .beads → .ai/beads
        3. Run bd init [--stealth]
        4. Update .gitignore
        """

    def call_bd(self, args: List[str]) -> Dict:
        """
        Execute bd command and return parsed output
        Handles JSON output from bd commands
        """

    def parse_beads_jsonl(self) -> List[Dict]:
        """Parse .beads/issues.jsonl into Python objects"""

    def is_beads_available(self) -> bool:
        """Check if bd command is installed"""
```

**Symlink Strategy**:
```bash
# User wants beads in .ai/beads/
mkdir -p .ai/beads
ln -s .ai/beads .beads
echo ".beads" >> .gitignore  # Ignore symlink, not target

# Beads CLI sees .beads/ and works normally
# Files actually stored in .ai/beads/ (committed to git)
```

### 2. Beads Sync (`know/src/beads_sync.py`)

**Purpose**: Bidirectional sync between Beads and spec-graph

**Key Methods**:
```python
class BeadsSync:
    def __init__(self, graph_path: str, beads_path: str):
        """Initialize sync engine"""

    def import_beads_to_graph(self) -> int:
        """
        Read .beads/issues.jsonl
        Store in spec-graph references.beads
        Link to features via metadata
        Returns: number of beads imported
        """

    def export_graph_to_beads(self, feature_id: str) -> int:
        """
        Export feature tasks to beads
        Create bd issues for each task
        Returns: number of beads created
        """

    def link_bead_to_feature(self, bead_id: str, feature_id: str):
        """Associate bead with feature in graph"""

    def sync_status(self):
        """Sync task status between beads and features"""

    def detect_conflicts(self) -> List[Dict]:
        """Find beads/features with conflicting state"""
```

**Graph Schema for Beads**:
```json
{
  "references": {
    "beads": {
      "bd-a1b2": {
        "title": "Implement JWT validation",
        "feature": "feature:auth",
        "status": "in-progress",
        "created": "2025-12-19T10:00:00Z",
        "updated": "2025-12-19T12:30:00Z"
      }
    }
  }
}
```

### 3. Task Manager (`know/src/task_manager.py`)

**Purpose**: Native JSONL-based task system (Beads alternative)

**Key Methods**:
```python
class TaskManager:
    def __init__(self, tasks_path: str = ".ai/tasks"):
        """Initialize task manager"""

    def add_task(self, title: str, feature: str = None,
                 description: str = None) -> str:
        """
        Create new task with hash-based ID
        Returns: task ID (e.g., "tk-a1b2")
        """

    def list_tasks(self, feature: str = None, status: str = None,
                   ready_only: bool = False) -> List[Dict]:
        """Query tasks with filters"""

    def block_task(self, task_id: str, blocker_id: str,
                   dep_type: str = "blocks"):
        """Create blocking dependency"""

    def complete_task(self, task_id: str):
        """Mark task complete, auto-unblock dependents"""

    def find_ready(self) -> List[Dict]:
        """Auto-ready detection: tasks with no blockers"""

    def generate_hash_id(self, title: str, timestamp: str) -> str:
        """Generate collision-free hash ID"""
```

**Native JSONL Format** (`.ai/tasks/tasks.jsonl`):
```jsonl
{"id":"tk-a1b2","title":"Implement JWT validation","feature":"feature:auth","status":"ready","blocks":[],"blocked_by":[],"created":"2025-12-19T10:00:00Z","updated":"2025-12-19T10:00:00Z"}
{"id":"tk-f3e4","title":"Add refresh token endpoint","feature":"feature:auth","status":"blocked","blocks":[],"blocked_by":["tk-a1b2"],"created":"2025-12-19T10:05:00Z","updated":"2025-12-19T10:05:00Z"}
```

**Dependency Types**:
- `blocks`: This task blocks another
- `blocked_by`: This task is blocked by another
- `related`: Related tasks (no blocking)
- `parent`: Hierarchical parent task
- `discovered_from`: Task discovered during another task

### 4. CLI Integration (`know/know.py`)

**New Commands**:

```bash
# Beads Integration Commands (matching bd shorthand)
know bd init [--path PATH] [--stealth]
know bd sync [--import|--export] [--feature FEATURE]
know bd list [--ready] [--feature FEATURE]
know bd add <title> [--feature FEATURE] [--description DESC]
know bd <any-bd-command>  # Passthrough

# Native Task Commands
know task init
know task add <title> [--feature FEATURE] [--description DESC]
know task list [--ready] [--feature FEATURE] [--status STATUS]
know task done <task-id>
know task block <task-id> --on <blocker-id> [--type TYPE]
know task unblock <task-id> <blocker-id>
know task ready  # Show ready tasks
```

**CLI Structure**:
```python
# In know.py
@click.group(name='bd')
def bd_commands():
    """Beads integration commands (matching bd shorthand)"""
    pass

@bd_commands.command()
@click.option('--path', default='.ai/beads')
@click.option('--stealth', is_flag=True)
def init(path, stealth):
    """Initialize Beads integration"""
    bridge = BeadsBridge(path)
    bridge.init_beads(stealth)

@bd_commands.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('command', nargs=-1)
def passthrough(command):
    """Pass command through to bd"""
    bridge = BeadsBridge()
    result = bridge.call_bd(list(command))
    click.echo(result)

@click.group()
def task():
    """Native task management"""
    pass

@task.command()
@click.argument('title')
@click.option('--feature')
def add(title, feature):
    """Add new task"""
    mgr = TaskManager()
    task_id = mgr.add_task(title, feature)
    click.echo(f"Created task: {task_id}")
```

### 5. Configuration (`know/src/config.py`)

**Config File** (`.ai/config.json`):
```json
{
  "task_system": "beads",
  "beads_path": ".ai/beads",
  "tasks_path": ".ai/tasks",
  "auto_sync": true,
  "feature_task_linking": true,
  "sync_interval": 300
}
```

**Config Schema**:
- `task_system`: "beads" | "native" | "hybrid" | null
- `beads_path`: Custom beads directory (default: ".ai/beads")
- `tasks_path`: Native tasks directory (default: ".ai/tasks")
- `auto_sync`: Enable automatic sync on feature changes
- `feature_task_linking`: Automatically link tasks to features
- `sync_interval`: Auto-sync interval in seconds

## Implementation Phases

### Phase 1: Beads Bridge (2-3 hours)
1. Create `beads_bridge.py` with init, call_bd, parse methods
2. Implement symlink strategy
3. Test with real Beads installation
4. Handle edge cases (missing bd, permission errors)

### Phase 2: Beads Commands (2 hours)
1. Add bd command group to CLI (matching bd shorthand)
2. Implement init, sync, list, add commands
3. Implement passthrough for other bd commands
4. Test command routing and feature linking

### Phase 3: Beads Sync (3-4 hours)
1. Create `beads_sync.py` with import/export
2. Define graph schema for references.beads
3. Implement bidirectional sync
4. Handle conflict resolution
5. Test with sample beads data

### Phase 4: Native Task System (4-5 hours)
1. Create `task_manager.py`
2. Design JSONL format with hash IDs
3. Implement CRUD operations
4. Implement dependency management
5. Implement auto-ready detection
6. Test with sample tasks

### Phase 5: Native Commands (2 hours)
1. Add task command group to CLI
2. Implement add, list, done, block, unblock commands
3. Test command functionality
4. Ensure feature parity with beads commands

### Phase 6: Configuration (1-2 hours)
1. Create config schema
2. Implement config loading/saving
3. Support mode switching (beads/native/hybrid)
4. Test configuration scenarios

### Phase 7: Testing & Polish (3-4 hours)
1. Integration tests for both modes
2. Edge case testing
3. Performance testing
4. Documentation
5. Marketing materials

**Total Estimated Time**: 17-23 hours

## Migration Path

**For Existing Beads Users**:
```bash
# Add know to existing Beads project
know bd init --path .beads  # Use existing .beads/
know bd sync --import       # Import beads to graph
```

**For New Users**:
```bash
# Start with native tasks
know task init
know task add "First task" --feature feature:auth

# Or start with Beads
know bd init
know bd add "First bead" --feature feature:auth
```

**Switching Systems**:
```bash
# Export native tasks to beads
know bd init
know bd sync --export

# Import beads to native
know task init
know bd sync --import
# Convert references.beads → .ai/tasks/tasks.jsonl
```

## Success Metrics

1. ✅ Beads initialization in `.ai/beads/` with working symlink
2. ✅ `know bd *` commands work identically to `bd *` (matching shorthand)
3. ✅ Bidirectional sync preserves all bead metadata
4. ✅ Native task system provides equivalent functionality
5. ✅ Tasks link to features in spec-graph
6. ✅ Auto-ready detection works in both systems
7. ✅ Users can switch between systems seamlessly
8. ✅ Marketing: "Seamless Beads Integration" demonstrated

## Marketing Angle

**Headline**: "Know + Beads: Bridge Product Vision to Task Execution"

**Pitch**:
- **Know** models WHAT to build (features, components, user objectives)
- **Beads** tracks HOW to build it (tasks, blockers, progress)
- **Integration** keeps them aligned automatically

**Key Messages**:
- "Works with Beads out of the box"
- "Don't use Beads? Use know's native task system instead"
- "Link tasks to product features effortlessly"
- "Choose your workflow, we adapt"

**Demo Flow**:
```bash
# 1. Plan product with know
know add feature auth '{"name":"Authentication","description":"User login system"}'

# 2. Break into tasks with beads (matching bd shorthand)
know bd add "Implement JWT validation" --feature feature:auth
know bd add "Add refresh token endpoint" --feature feature:auth
know bd block bd-f3e4 --on bd-a1b2

# 3. See what's ready
know bd ready

# 4. Sync keeps them aligned
know bd sync
```
