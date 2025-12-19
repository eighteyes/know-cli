# Module Placement Guide: beads_bridge, task_manager, task_sync

## Overview

This document provides specific guidance on where and how to add three new modules to the know codebase:
- `beads_bridge.py` - External system integration
- `task_manager.py` - Task lifecycle management
- `task_sync.py` - Synchronization coordination

---

## 1. Recommended Structure

### Option A: Flat Structure (Recommended for Initial Implementation)

```
know/src/
├── __init__.py
├── async_graph.py
├── beads_bridge.py      # ← NEW: External system bridge
├── cache.py
├── dependencies.py
├── diff.py
├── entities.py
├── gap_analysis.py
├── generators.py
├── graph.py
├── llm.py
├── reference_tools.py
├── task_manager.py      # ← NEW: Task lifecycle management
├── task_sync.py         # ← NEW: Synchronization orchestration
├── utils.py
├── validation.py
└── visualizers/
    ├── __init__.py
    └── mermaid.py

know/tests/ (or tests/)
├── test_beads_bridge.py
├── test_task_manager.py
├── test_task_sync.py
├── test_commands.py
├── ... (existing tests)
```

**Rationale:**
- Flat structure matches existing codebase pattern
- Easy to discover all core modules
- Simple imports from CLI
- Good for 13-16 total modules

### Option B: Organized by Feature (For Future Growth)

```
know/src/
├── core/
│   ├── __init__.py
│   ├── graph.py
│   ├── cache.py
│   ├── entities.py
│   ├── dependencies.py
│   └── validation.py
├── generation/
│   ├── __init__.py
│   ├── generators.py
│   └── llm.py
├── sync/                # ← NEW: Task synchronization subsystem
│   ├── __init__.py
│   ├── manager.py       # Previously task_manager.py
│   ├── sync.py          # Previously task_sync.py
│   └── beads.py         # Previously beads_bridge.py
├── utils/
│   ├── __init__.py
│   ├── utils.py
│   ├── diff.py
│   ├── reference_tools.py
│   └── gap_analysis.py
└── visualizers/
    ├── __init__.py
    └── mermaid.py

know/tests/
├── core/
│   └── ...
├── sync/
│   ├── test_manager.py
│   ├── test_sync.py
│   └── test_beads.py
└── ...
```

**Rationale:**
- Better organization at scale
- Clear subsystem boundaries
- Easier to navigate large projects
- Encourages modular thinking

**Recommendation:** Start with **Option A** (flat), migrate to **Option B** when module count exceeds 20.

---

## 2. Module Specifications

### 2.1 beads_bridge.py

**Purpose:** Bridge between Know graph system and Beads project management system

**File Location:** `know/src/beads_bridge.py`

**Dependencies:**
```python
from typing import Dict, List, Optional, Any, Tuple
from .graph import GraphManager
from .entities import EntityManager
from .dependencies import DependencyManager
import json
from pathlib import Path
```

**Class Structure:**
```python
class BeadsBridge:
    """Interface to external Beads system"""

    def __init__(
        self,
        graph_manager: GraphManager,
        entity_manager: EntityManager,
        dependency_manager: DependencyManager,
        beads_config_path: Optional[str] = None
    ):
        """Initialize bridge with required managers and configuration"""
        self.graph = graph_manager
        self.entities = entity_manager
        self.deps = dependency_manager
        self.config = self._load_config(beads_config_path)

    # Configuration
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load Beads connection configuration"""
        pass

    # Push operations (graph → Beads)
    def push_tasks(self, feature_id: str) -> Tuple[bool, Optional[str]]:
        """Push tasks from graph to Beads system"""
        # 1. Get tasks linked to feature from graph
        # 2. Transform to Beads format
        # 3. Send to Beads API
        # 4. Return success/error
        pass

    def push_feature_status(self, feature_id: str, status: str) -> Tuple[bool, Optional[str]]:
        """Update feature status in Beads"""
        pass

    # Pull operations (Beads → graph)
    def pull_updates(self) -> Tuple[bool, Dict]:
        """Fetch updates from Beads, return change summary"""
        # 1. Query Beads API for updates
        # 2. Parse response
        # 3. Return changes (new tasks, status updates)
        # 4. DO NOT modify graph here (task_sync handles that)
        pass

    def pull_task_status(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """Get single task status from Beads"""
        pass

    # Mapping operations
    def map_task_to_beads(self, task_entity: Dict) -> Dict:
        """Transform graph task format to Beads format"""
        pass

    def map_task_from_beads(self, beads_task: Dict) -> Dict:
        """Transform Beads format to graph task format"""
        pass

    # Connection validation
    def validate_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection to Beads system"""
        pass
```

**Key Responsibilities:**
- Authenticate with Beads API
- Transform data formats between systems
- Handle network errors gracefully
- Track what was synced (timestamps, checksums)
- **NOT** responsible for deciding what to sync or conflict resolution

**Testing:**
```python
# tests/test_beads_bridge.py
- Test config loading
- Test data transformation (to/from Beads)
- Test API calls with mocked responses
- Test error handling (network failures, invalid data)
- Test connection validation
```

### 2.2 task_manager.py

**Purpose:** Manage task entity lifecycle and state transitions

**File Location:** `know/src/task_manager.py`

**Dependencies:**
```python
from typing import Dict, List, Optional, Tuple, Any
from .entities import EntityManager
from .dependencies import DependencyManager
from .validation import GraphValidator
from .graph import GraphManager
import json
from pathlib import Path
from datetime import datetime
```

**Class Structure:**
```python
class TaskManager:
    """Manage task lifecycle and operations"""

    def __init__(
        self,
        graph_manager: GraphManager,
        entity_manager: EntityManager,
        dependency_manager: DependencyManager,
        validator: GraphValidator
    ):
        """Initialize with core managers"""
        self.graph = graph_manager
        self.entities = entity_manager
        self.deps = dependency_manager
        self.validator = validator

        # Define task types and allowed transitions
        self.TASK_TYPES = ['task', 'subtask', 'checkpoint']
        self.ALLOWED_STATUSES = ['pending', 'in-progress', 'blocked', 'done', 'cancelled']

    # Task creation
    def create_task(
        self,
        feature_id: str,
        name: str,
        description: str,
        task_type: str = 'task',
        assigned_to: Optional[str] = None,
        **metadata
    ) -> Tuple[bool, Optional[str]]:
        """Create new task linked to feature"""
        # 1. Validate inputs
        # 2. Create task entity
        # 3. Link to feature via dependency
        # 4. Save graph
        # 5. Return success/error
        pass

    # Task status management
    def update_task_status(
        self,
        task_id: str,
        status: str
    ) -> Tuple[bool, Optional[str]]:
        """Update task status, validate transition"""
        pass

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get current task status"""
        pass

    def is_valid_status_transition(
        self,
        current_status: str,
        new_status: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate status transition rules"""
        # Define what transitions are allowed
        # e.g., pending → in-progress, in-progress → done
        pass

    # Task queries
    def get_tasks_for_feature(self, feature_id: str) -> List[Dict]:
        """Get all tasks linked to a feature"""
        pass

    def get_blocked_tasks(self) -> List[Dict]:
        """Get all currently blocked tasks"""
        pass

    def get_overdue_tasks(self) -> List[Dict]:
        """Get tasks past due date"""
        pass

    # Task dependencies
    def add_task_dependency(
        self,
        task_id: str,
        depends_on_task_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Create dependency between tasks"""
        pass

    def get_task_dependencies(self, task_id: str) -> List[str]:
        """Get tasks this task depends on"""
        pass

    def get_blocking_tasks(self, task_id: str) -> List[str]:
        """Get tasks blocked by this task"""
        pass

    # Task assignment
    def assign_task(
        self,
        task_id: str,
        assignee: str
    ) -> Tuple[bool, Optional[str]]:
        """Assign task to user/team"""
        pass

    # Validation
    def validate_task(self, task_entity: Dict) -> Tuple[bool, Optional[str]]:
        """Validate task entity"""
        pass
```

**Key Responsibilities:**
- Create/update/delete task entities
- Manage task status and transitions
- Link tasks to features and other tasks
- Define task types and valid state machines
- Validate task data before operations
- **NOT** responsible for syncing with external systems

**Testing:**
```python
# tests/test_task_manager.py
- Test task creation with valid inputs
- Test invalid inputs and error handling
- Test status transitions (valid and invalid)
- Test task-feature linking
- Test task-task dependencies
- Test queries (by feature, by status, etc.)
- Test assignment operations
```

### 2.3 task_sync.py

**Purpose:** Orchestrate synchronization between graph and external systems

**File Location:** `know/src/task_sync.py`

**Dependencies:**
```python
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from .graph import GraphManager
from .task_manager import TaskManager
from .beads_bridge import BeadsBridge
from .validation import GraphValidator
import json
from datetime import datetime
from collections import defaultdict
```

**Class Structure:**
```python
class SyncStrategy(Enum):
    """Sync strategy for conflict resolution"""
    GRAPH_SOURCE = "graph-source"      # Graph is authoritative
    BEADS_SOURCE = "beads-source"      # Beads is authoritative
    MERGE = "merge"                    # Combine changes
    MANUAL = "manual"                  # Flag for manual review


class ConflictInfo:
    """Metadata about a synchronization conflict"""

    def __init__(self, task_id: str, conflict_type: str, graph_value: Any, beads_value: Any):
        self.task_id = task_id
        self.conflict_type = conflict_type  # status, assignment, metadata, etc.
        self.graph_value = graph_value
        self.beads_value = beads_value
        self.timestamp = datetime.now()


class TaskSync:
    """Synchronize graph and external (Beads) system"""

    def __init__(
        self,
        graph_manager: GraphManager,
        task_manager: TaskManager,
        beads_bridge: BeadsBridge,
        validator: GraphValidator
    ):
        """Initialize synchronizer with all components"""
        self.graph = graph_manager
        self.tasks = task_manager
        self.beads = beads_bridge
        self.validator = validator
        self.conflicts: List[ConflictInfo] = []

    # Full sync operations
    def sync_all(
        self,
        strategy: SyncStrategy = SyncStrategy.MERGE
    ) -> Tuple[bool, Dict[str, Any]]:
        """Perform two-way synchronization: graph ↔ Beads

        Returns:
            (success, summary) where summary includes:
            - pushed: List of tasks pushed to Beads
            - pulled: List of updates from Beads
            - conflicts: List of detected conflicts
            - errors: Any errors during sync
        """
        summary = {
            'pushed': [],
            'pulled': [],
            'conflicts': [],
            'errors': []
        }

        # Step 1: Validate both systems
        graph_valid, graph_errors = self.validator.validate_all()
        beads_valid, beads_errors = self.beads.validate_connection()

        if not graph_valid or not beads_valid:
            summary['errors'].extend(graph_errors or [])
            summary['errors'].extend(beads_errors or [])
            return False, summary

        # Step 2: Get current state from both systems
        graph_state = self._get_graph_task_state()
        beads_state = self._get_beads_task_state()

        # Step 3: Detect changes and conflicts
        changes = self._detect_changes(graph_state, beads_state)
        conflicts = self._detect_conflicts(graph_state, beads_state)
        summary['conflicts'] = conflicts

        # Step 4: Apply strategy to resolve conflicts
        if conflicts:
            resolved = self._resolve_conflicts(conflicts, strategy)
            if not resolved and strategy != SyncStrategy.MANUAL:
                summary['errors'].append("Failed to resolve conflicts")
                return False, summary

        # Step 5: Push graph changes to Beads
        push_result = self._push_changes(changes.get('graph_to_beads', []))
        summary['pushed'] = push_result

        # Step 6: Pull Beads changes to graph
        pull_result = self._pull_changes(changes.get('beads_to_graph', []))
        summary['pulled'] = pull_result

        # Step 7: Validate final state
        final_valid, final_errors = self.validator.validate_all()
        if not final_valid:
            summary['errors'].extend(final_errors)
            return False, summary

        return True, summary

    # Partial sync operations
    def sync_feature(
        self,
        feature_id: str,
        direction: str = 'both'
    ) -> Tuple[bool, Dict[str, Any]]:
        """Sync tasks for specific feature (push, pull, or both)"""
        # direction: 'push', 'pull', 'both'
        pass

    def sync_task(
        self,
        task_id: str,
        direction: str = 'both'
    ) -> Tuple[bool, Dict[str, Any]]:
        """Sync single task"""
        pass

    # Conflict detection and resolution
    def detect_conflicts(self) -> List[ConflictInfo]:
        """Find inconsistencies between systems without syncing"""
        self.conflicts = []
        graph_state = self._get_graph_task_state()
        beads_state = self._get_beads_task_state()
        self.conflicts = self._detect_conflicts(graph_state, beads_state)
        return self.conflicts

    def _detect_conflicts(
        self,
        graph_state: Dict,
        beads_state: Dict
    ) -> List[ConflictInfo]:
        """Analyze differences between systems

        Returns:
            List of ConflictInfo objects describing conflicts
        """
        # Compare status, assignments, metadata, etc.
        pass

    def resolve_conflicts(
        self,
        conflicts: Optional[List[ConflictInfo]] = None,
        strategy: SyncStrategy = SyncStrategy.MERGE
    ) -> Tuple[bool, Optional[str]]:
        """Resolve detected conflicts using strategy"""
        if conflicts is None:
            conflicts = self.conflicts

        return self._resolve_conflicts(conflicts, strategy)

    def _resolve_conflicts(
        self,
        conflicts: List[ConflictInfo],
        strategy: SyncStrategy
    ) -> bool:
        """Apply resolution strategy"""
        if strategy == SyncStrategy.GRAPH_SOURCE:
            # Use graph values
            pass
        elif strategy == SyncStrategy.BEADS_SOURCE:
            # Use beads values
            pass
        elif strategy == SyncStrategy.MERGE:
            # Intelligently merge (e.g., newer timestamp wins)
            pass
        elif strategy == SyncStrategy.MANUAL:
            # Flag for manual resolution, don't auto-fix
            pass
        return True

    # State capture
    def _get_graph_task_state(self) -> Dict[str, Dict]:
        """Capture current state of all tasks in graph"""
        # Returns: {task_id: {status, assigned_to, metadata, ...}}
        pass

    def _get_beads_task_state(self) -> Dict[str, Dict]:
        """Capture current state of all tasks in Beads"""
        pass

    # Change detection
    def _detect_changes(
        self,
        graph_state: Dict,
        beads_state: Dict
    ) -> Dict[str, List]:
        """Detect what changed in each system

        Returns:
            {
                'graph_to_beads': [changes],
                'beads_to_graph': [changes],
                'graph_only': [tasks],
                'beads_only': [tasks]
            }
        """
        pass

    # Synchronization operations
    def _push_changes(self, changes: List) -> List:
        """Send graph changes to Beads"""
        # For each change:
        # 1. Validate
        # 2. Call beads_bridge.push_*()
        # 3. Track results
        pass

    def _pull_changes(self, changes: List) -> List:
        """Apply Beads changes to graph"""
        # For each change:
        # 1. Validate
        # 2. Call task_manager.update_*()
        # 3. Track results
        pass

    # Status and reporting
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and last sync time"""
        pass

    def get_last_sync(self) -> Optional[datetime]:
        """Get timestamp of last successful sync"""
        pass
```

**Key Responsibilities:**
- Orchestrate synchronization between systems
- Detect changes and conflicts
- Apply conflict resolution strategies
- Track sync history and status
- Validate consistency before and after sync
- **NOT** responsible for individual entity operations (use TaskManager) or API calls (use BeadsBridge)

**Testing:**
```python
# tests/test_task_sync.py
- Test basic two-way sync
- Test conflict detection
- Test conflict resolution with different strategies
- Test partial syncs (feature, task)
- Test edge cases (deleted tasks, new tasks, etc.)
- Test validation after sync
- Test error handling (network failures, invalid data)
```

---

## 3. Integration Points

### 3.1 Update src/__init__.py

```python
"""
Know Tool - Python implementation for efficient graph operations
"""

__version__ = "1.0.0"

from .graph import GraphManager
from .entities import EntityManager
from .cache import GraphCache
from .dependencies import DependencyManager
from .validation import GraphValidator
from .generators import SpecGenerator
from .llm import LLMManager, LLMProvider, MockProvider
from .async_graph import AsyncGraphManager, AsyncGraphPool, get_graph
from .diff import GraphDiff
from .utils import (
    parse_entity_id,
    format_entity_id,
    normalize_entity_type,
    validate_name_format,
    get_graph_stats
)

# ← NEW IMPORTS
from .beads_bridge import BeadsBridge
from .task_manager import TaskManager
from .task_sync import TaskSync

__all__ = [
    "GraphManager",
    "EntityManager",
    "GraphCache",
    "DependencyManager",
    "GraphValidator",
    "SpecGenerator",
    "LLMManager",
    "LLMProvider",
    "MockProvider",
    "AsyncGraphManager",
    "AsyncGraphPool",
    "get_graph",
    "GraphDiff",
    "parse_entity_id",
    "format_entity_id",
    "normalize_entity_type",
    "validate_name_format",
    "get_graph_stats",
    # ← NEW EXPORTS
    "BeadsBridge",
    "TaskManager",
    "TaskSync"
]
```

### 3.2 Update know.py CLI Setup

```python
# In the cli() function after existing managers:

@click.group()
@click.option('--graph-path', '-g', default='.ai/spec-graph.json',
              help='Path to graph file')
@click.option('--rules-path', '-r', default=None,
              help='Path to dependency rules file')
@click.option('--beads-config', default=None,
              help='Path to Beads configuration')
@click.pass_context
def cli(ctx, graph_path, rules_path, beads_config):
    """Know Tool - Manage specification graph efficiently"""
    # ... existing setup ...

    # ← NEW: Add task management and sync
    ctx.obj['task_manager'] = TaskManager(
        ctx.obj['graph'],
        ctx.obj['entities'],
        ctx.obj['deps'],
        ctx.obj['validator']
    )

    ctx.obj['beads_bridge'] = BeadsBridge(
        ctx.obj['graph'],
        ctx.obj['entities'],
        ctx.obj['deps'],
        beads_config_path=beads_config
    )

    ctx.obj['task_sync'] = TaskSync(
        ctx.obj['graph'],
        ctx.obj['task_manager'],
        ctx.obj['beads_bridge'],
        ctx.obj['validator']
    )
```

### 3.3 Add CLI Commands

```python
# New commands in know.py

@cli.command()
@click.argument('feature_id')
@click.argument('name')
@click.option('--description', default='', help='Task description')
@click.option('--type', 'task_type', default='task', help='Task type')
@click.option('--assigned-to', default=None, help='Assign to')
@click.pass_context
def create_task(ctx, feature_id, name, description, task_type, assigned_to):
    """Create a new task linked to a feature"""
    success, error = ctx.obj['task_manager'].create_task(
        feature_id=feature_id,
        name=name,
        description=description,
        task_type=task_type,
        assigned_to=assigned_to
    )

    if success:
        console.print(f"[green]✓ Task created: {name}[/green]")
    else:
        console.print(f"[red]✗ Error: {error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.argument('status')
@click.pass_context
def update_task_status(ctx, task_id, status):
    """Update task status"""
    success, error = ctx.obj['task_manager'].update_task_status(task_id, status)

    if success:
        console.print(f"[green]✓ Task status updated to: {status}[/green]")
    else:
        console.print(f"[red]✗ Error: {error}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--feature', default=None, help='Sync specific feature')
@click.option('--strategy', default='merge', help='Conflict resolution strategy')
@click.pass_context
def sync(ctx, feature, strategy):
    """Synchronize tasks with Beads system"""
    if feature:
        success, result = ctx.obj['task_sync'].sync_feature(feature)
    else:
        from src.task_sync import SyncStrategy
        strategy_enum = SyncStrategy[strategy.upper()]
        success, result = ctx.obj['task_sync'].sync_all(strategy=strategy_enum)

    if success:
        console.print("[green]✓ Synchronization complete[/green]")
        console.print(f"Pushed: {len(result.get('pushed', []))} tasks")
        console.print(f"Pulled: {len(result.get('pulled', []))} updates")

        if result.get('conflicts'):
            console.print(f"[yellow]⚠ Conflicts: {len(result['conflicts'])} detected[/yellow]")
    else:
        console.print("[red]✗ Synchronization failed[/red]")
        for error in result.get('errors', []):
            console.print(f"  • {error}")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_tasks(ctx):
    """List all tasks"""
    # Implementation
    pass
```

---

## 4. Configuration Files

### Beads Configuration (Optional)
Create `know/config/beads-config.json`:

```json
{
  "beads": {
    "api_url": "https://api.beads.example.com",
    "api_key_env": "BEADS_API_KEY",
    "timeout": 30,
    "retry_attempts": 3,
    "sync_interval_seconds": 300
  },
  "mapping": {
    "task_status_map": {
      "pending": "todo",
      "in-progress": "in_progress",
      "blocked": "blocked",
      "done": "completed",
      "cancelled": "cancelled"
    },
    "task_fields": [
      "name",
      "description",
      "status",
      "assigned_to",
      "due_date",
      "priority"
    ]
  }
}
```

---

## 5. Testing Strategy

### Test File Organization

```
tests/
├── test_beads_bridge.py        # 200-300 lines
├── test_task_manager.py        # 300-400 lines
├── test_task_sync.py           # 400-500 lines
├── fixtures/                   # Shared test utilities
│   ├── __init__.py
│   ├── graph_fixtures.py       # Graph setup helpers
│   └── mock_beads.py           # Mock Beads API
└── ... (existing tests)
```

### Fixture Example

```python
# tests/fixtures/mock_beads.py
import json
from typing import Dict, Any
from unittest.mock import Mock, patch

class MockBeadsAPI:
    """Mock Beads API responses for testing"""

    def __init__(self):
        self.tasks = {}
        self.push_history = []
        self.pull_history = []

    def add_task(self, task_id: str, task_data: Dict):
        """Add mock task"""
        self.tasks[task_id] = task_data

    def push_task(self, task_data: Dict) -> Dict:
        """Mock push operation"""
        self.push_history.append(task_data)
        return {"status": "success", "id": task_data.get("id")}

    def pull_updates(self) -> List[Dict]:
        """Mock pull operation"""
        return list(self.tasks.values())

    def get_connection_mock(self):
        """Return mock connection"""
        return patch('beads_bridge.BeadsBridge._api_call', self._api_call)

    def _api_call(self, method: str, endpoint: str, **kwargs):
        """Mock API call dispatcher"""
        # Route to appropriate mock method
        pass
```

### Test Example

```python
# tests/test_task_manager.py
import pytest
from src import GraphManager, EntityManager, DependencyManager, GraphValidator, TaskManager
import tempfile
import json

@pytest.fixture
def task_manager_setup():
    """Setup for task manager tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_graph = {
            "meta": {"version": "1.0.0"},
            "references": {},
            "entities": {
                "feature": {
                    "auth": {"name": "Authentication", "description": "Auth feature"}
                }
            },
            "graph": {}
        }
        json.dump(test_graph, f)
        temp_file = Path(f.name)

    gm = GraphManager(str(temp_file))
    em = EntityManager(gm)
    dm = DependencyManager(gm)
    gv = GraphValidator(gm)
    tm = TaskManager(gm, em, dm, gv)

    return tm, temp_file


def test_create_task(task_manager_setup):
    """Test creating a task"""
    tm, _ = task_manager_setup

    success, error = tm.create_task(
        feature_id="feature:auth",
        name="implement-login",
        description="Implement login endpoint",
        task_type="task"
    )

    assert success
    assert error is None

    # Verify task was created
    tasks = tm.get_tasks_for_feature("feature:auth")
    assert len(tasks) == 1
    assert tasks[0]['name'] == 'implement-login'


def test_invalid_status_transition(task_manager_setup):
    """Test that invalid status transitions are rejected"""
    tm, _ = task_manager_setup

    # Create task
    tm.create_task(feature_id="feature:auth", name="test-task", description="test")
    task_id = "task:test-task"

    # Try invalid transition: pending → done (should go through in-progress)
    valid, error = tm.is_valid_status_transition("pending", "done")
    assert not valid
```

---

## 6. Dependency Injection Chain

The complete initialization chain in CLI:

```
GraphManager
    ↓
    ├─→ EntityManager (reads GraphManager)
    ├─→ DependencyManager (reads GraphManager)
    ├─→ GraphValidator (reads GraphManager)
    │
    ├─→ TaskManager (reads all core managers)
    │   └─→ task status/creation operations
    │
    ├─→ BeadsBridge (reads core managers)
    │   └─→ external API integration
    │
    └─→ TaskSync (reads TaskManager + BeadsBridge + GraphValidator)
        └─→ orchestration of sync operations

CLI Context Object:
{
    'graph': GraphManager,
    'entities': EntityManager,
    'deps': DependencyManager,
    'validator': GraphValidator,
    'task_manager': TaskManager,
    'beads_bridge': BeadsBridge,
    'task_sync': TaskSync,
    ... (existing)
}
```

---

## 7. Error Handling Pattern

All methods follow consistent error handling:

```python
def operation(self, arg: str) -> Tuple[bool, Optional[str]]:
    """
    Do something.

    Returns:
        (success, error_message)
        - If success: (True, None)
        - If error: (False, "error description")
    """
    try:
        # Validate inputs
        if not arg:
            return False, "Argument cannot be empty"

        # Perform operation
        result = self._do_operation(arg)

        # Validate result
        if not result:
            return False, "Operation produced no result"

        # Save/persist
        self.graph.save_graph(...)

        return True, None

    except ValueError as e:
        return False, f"Invalid input: {str(e)}"
    except IOError as e:
        return False, f"File error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
```

---

## 8. Version Control Recommendations

### Commit Strategy

```bash
# Initial implementation
git add know/src/beads_bridge.py know/src/task_manager.py know/src/task_sync.py
git add know/tests/test_beads_bridge.py know/tests/test_task_manager.py know/tests/test_task_sync.py
git add know/src/__init__.py  # Updated exports
git add know/config/beads-config.json  # If using config
git commit -m "feat(task-sync): add beads integration and task management

- beads_bridge.py: Interface to external Beads system
- task_manager.py: Task lifecycle and state management
- task_sync.py: Synchronization orchestration
- Includes comprehensive tests and fixtures
"
```

### Feature Branches

```
main
└── feature/beads-integration
    ├── beads-bridge (API integration)
    ├── task-manager (lifecycle)
    └── task-sync (orchestration)
```

---

## 9. Checklist for Implementation

- [ ] Create beads_bridge.py in know/src/
- [ ] Create task_manager.py in know/src/
- [ ] Create task_sync.py in know/src/
- [ ] Create corresponding test files
- [ ] Update src/__init__.py with new exports
- [ ] Update know.py CLI with manager initialization
- [ ] Add CLI commands for new functionality
- [ ] Create beads-config.json if needed
- [ ] Write comprehensive docstrings (Google style)
- [ ] Add full type hints to all functions
- [ ] Create test fixtures in tests/fixtures/
- [ ] Verify all tests pass: `pytest tests/ -v`
- [ ] Run validation: `npm run validate-graph`
- [ ] Update this documentation with any changes
- [ ] Commit with proper message format

---

## 10. Future Enhancement Opportunities

### Phase 2: Enhanced Features
- Conflict resolution strategies beyond basic merge
- Sync history tracking and rollback
- Bi-directional change notifications
- Task templating for common patterns
- Batch operations for efficiency

### Phase 3: Advanced Integration
- Webhook support for real-time updates
- Task scheduling and automation
- Team collaboration features
- Advanced reporting and analytics
- Performance optimization for large graphs

---

## References

- Main Architecture: See `ARCHITECTURE_ANALYSIS.md`
- GraphManager: know/src/graph.py
- EntityManager: know/src/entities.py
- DependencyManager: know/src/dependencies.py
- GraphValidator: know/src/validation.py
- CLI Reference: know/know.py (lines 1-200 for pattern examples)
