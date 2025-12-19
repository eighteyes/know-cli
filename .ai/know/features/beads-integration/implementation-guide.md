# Beads Integration Implementation Guide
## Code Outlines & Integration Points

---

## File 1: `know/src/beads_bridge.py` (~80 lines)

```python
"""
Minimal wrapper around Beads (bd) task management CLI.
Single responsibility: Execute bd commands, return results.
"""

import subprocess
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BeadsBridge:
    """
    Thin wrapper around the bd (Beads) CLI tool.

    Design principles:
    - Direct subprocess passthrough (no command validation)
    - Fail-fast on missing bd (no silent fallbacks)
    - Return structured results, let caller handle errors
    - Trust user input (subprocess.run with list args prevents injection)
    """

    def __init__(self, executable: str = 'bd', default_path: str = '.ai/beads'):
        """
        Initialize bridge.

        Args:
            executable: Name or path to bd command (default: 'bd' in PATH)
            default_path: Default Beads data directory
        """
        self.executable = executable
        self.default_path = Path(default_path)

    def is_available(self) -> Tuple[bool, Optional[str]]:
        """
        Check if bd executable is available in PATH.

        Returns:
            Tuple of (is_available, error_message)
            If not available, error_message contains install instructions
        """
        if shutil.which(self.executable):
            return True, None

        error_msg = f"""bd not found in PATH

Install Beads first:
  npm install -g https://github.com/steveyegge/beads

Or set custom path in .claude/settings.local.json:
  {{
    "beads": {{
      "executable": "/path/to/bd"
    }}
  }}"""

        return False, error_msg

    def run(self, *args, capture_output: bool = True) -> Dict[str, any]:
        """
        Execute bd command with given arguments.

        Args:
            *args: Command arguments (passed directly to bd)
            capture_output: Capture stdout/stderr (default: True)

        Returns:
            Dict with keys:
            - success: bool (returncode == 0)
            - stdout: Command output
            - stderr: Error messages
            - returncode: Exit code

        Example:
            result = bridge.run('task', 'list')
            result = bridge.run('task-add', 'Title', 'Description')
        """
        try:
            cmd = [self.executable] + list(args)

            proc = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=30  # Prevent hangs
            )

            return {
                'success': proc.returncode == 0,
                'stdout': proc.stdout,
                'stderr': proc.stderr,
                'returncode': proc.returncode
            }

        except FileNotFoundError:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'{self.executable} not found',
                'returncode': 127
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'{self.executable} command timed out',
                'returncode': 124
            }

        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }

    def create_task(self, title: str, description: str = '') -> Optional[str]:
        """
        Create a new task in Beads.

        Args:
            title: Task title
            description: Optional task description

        Returns:
            Task ID on success (e.g., 'bd-a1b2'), None on failure

        NOTE: Implementation depends on Beads CLI output format.
        This is a placeholder that should be updated after testing with real bd.
        """
        args = ['task-add', title]
        if description:
            args.append(description)

        result = self.run(*args)

        if not result['success']:
            return None

        # Parse task ID from stdout
        # This is placeholder - actual format depends on bd CLI output
        # Example: "Created task: bd-a1b2"
        stdout = result['stdout'].strip()

        # Try to extract ID (implementation depends on bd format)
        if 'bd-' in stdout:
            parts = stdout.split('bd-')
            if len(parts) > 1:
                return 'bd-' + parts[1].split()[0]

        return None

    def list_tasks(self) -> Optional[List[Dict]]:
        """
        List all tasks in Beads.

        Returns:
            List of task dicts with keys: id, title, status, etc.
            Returns None on error

        NOTE: Placeholder - depends on bd CLI output format.
        """
        result = self.run('task', 'list', '--json')

        if not result['success']:
            return None

        try:
            # Try to parse JSON output
            return json.loads(result['stdout'])
        except json.JSONDecodeError:
            # Fall back to parsing text output if needed
            return None

    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get status of a specific task.

        Returns:
            Status string (e.g., 'pending', 'complete') or None
        """
        result = self.run('task', 'get', task_id)

        if not result['success']:
            return None

        # Parse status from output (depends on bd format)
        # Placeholder: this needs testing
        stdout = result['stdout']
        if 'status:' in stdout:
            return stdout.split('status:')[1].strip().split()[0]

        return None


class BeadsError(Exception):
    """Raised when Beads operation fails"""
    pass
```

### Key Design Points:
1. **NO external dependencies** - uses stdlib only
2. **NO validation** - subprocess.run with list args prevents injection
3. **NO error recovery** - returns structured results, caller decides
4. **NO assumptions** about bd output format - documented as placeholders
5. **Fail-fast** on missing bd - explicit error, not silent fallback

---

## File 2: `know/src/task_sync.py` (~60 lines)

```python
"""
Bidirectional sync between Beads tasks and spec-graph references.
Single responsibility: Update references based on Beads state.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .beads_bridge import BeadsBridge
from .graph import GraphManager


class TaskSync:
    """
    Sync Beads tasks with spec-graph references.

    Direction: Beads → Graph (Beads is source of truth)
    Strategy: Store task ID in references, update status on sync
    """

    def __init__(self, graph_manager: GraphManager, beads_bridge: BeadsBridge, config: Optional[Dict] = None):
        """
        Initialize sync engine.

        Args:
            graph_manager: GraphManager instance
            beads_bridge: BeadsBridge instance
            config: Optional config dict with auto_sync settings
        """
        self.graph = graph_manager
        self.beads = beads_bridge
        self.config = config or {}
        self._last_sync = 0  # For debouncing

    def _should_sync(self, trigger: str) -> bool:
        """Check if sync should proceed based on config and trigger"""
        beads_config = self.config.get('beads', {})

        if not beads_config.get('auto_sync', True):
            return False

        # Check specific trigger type
        if trigger == 'status_change':
            return beads_config.get('sync_on_status_change', True)
        elif trigger == 'graph_save':
            return beads_config.get('sync_on_save', True)
        elif trigger == 'explicit':
            return True  # Always sync on explicit request

        return False

    def _apply_debounce(self) -> bool:
        """Apply 1-second debounce to prevent rapid syncs"""
        now = time.time()
        debounce_secs = self.config.get('beads', {}).get('sync_debounce_seconds', 1)

        if (now - self._last_sync) < debounce_secs:
            return False  # Skip this sync

        self._last_sync = now
        return True

    def sync_feature_to_beads(self, feature_id: str) -> bool:
        """
        Create Beads task for a feature if it doesn't exist.

        Args:
            feature_id: Feature ID (e.g., 'feature:auth')

        Returns:
            True if task exists or was created

        Flow:
        1. Check references.beads for existing task ID
        2. If found: return True
        3. If not found: create task via BeadsBridge
        4. Store task ID in references
        5. Return True on success
        """
        graph_data = self.graph.load()
        beads_refs = graph_data.get('references', {}).get('beads', {})

        # Check if feature already has task
        for task_key, task_ref in beads_refs.items():
            if task_ref.get('feature') == feature_id:
                return True  # Already linked

        # Get feature name for task title
        feature_type, feature_name = feature_id.split(':', 1)
        entity = self.graph.get_entities().get('feature', {}).get(feature_name, {})

        title = entity.get('name', feature_name)
        description = entity.get('description', f'Implement {feature_name}')

        # Create task in Beads
        task_id = self.beads.create_task(title, description)

        if not task_id:
            return False  # Creation failed

        # Store reference
        if 'references' not in graph_data:
            graph_data['references'] = {}
        if 'beads' not in graph_data['references']:
            graph_data['references']['beads'] = {}

        # Create reference key from feature name
        ref_key = f"{feature_name}-{task_id[-4:]}"  # e.g., "auth-a1b2"

        graph_data['references']['beads'][ref_key] = {
            'feature': feature_id,
            'task_id': task_id,
            'title': title,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }

        self.graph.save_graph(graph_data)
        return True

    def sync_beads_to_graph(self) -> Dict[str, any]:
        """
        Update graph status from Beads (Beads wins on conflicts).

        Returns:
            Dict with keys:
            - synced: number of tasks synced
            - updated: list of feature IDs updated
            - errors: list of error messages

        Flow:
        1. Get all tasks from Beads
        2. For each task linked to a feature:
           a. Read task status
           b. Find feature in graph
           c. If status changed: update feature phase/status
           d. Log overwrite as warning if conflicted
        3. Return results
        """
        result = {
            'synced': 0,
            'updated': [],
            'errors': []
        }

        # Get Beads tasks
        tasks = self.beads.list_tasks()
        if tasks is None:
            result['errors'].append('Failed to retrieve Beads tasks')
            return result

        # Get current graph
        graph_data = self.graph.load()
        beads_refs = graph_data.get('references', {}).get('beads', {})

        # Sync each linked task
        for task_key, task_ref in beads_refs.items():
            task_id = task_ref.get('task_id')
            feature_id = task_ref.get('feature')

            # Find task in Beads list
            beads_task = next((t for t in tasks if t.get('id') == task_id), None)

            if not beads_task:
                result['errors'].append(f'Task {task_id} not found in Beads')
                continue

            # Update reference status
            old_status = task_ref.get('status')
            new_status = beads_task.get('status', 'pending')

            if old_status != new_status:
                graph_data['references']['beads'][task_key]['status'] = new_status
                graph_data['references']['beads'][task_key]['updated_at'] = datetime.utcnow().isoformat()
                result['updated'].append(feature_id)

            result['synced'] += 1

        # Save updates
        if result['updated']:
            self.graph.save_graph(graph_data)

        return result

    def sync_all(self, trigger: str = 'explicit') -> Dict[str, any]:
        """
        Run full bidirectional sync.

        Args:
            trigger: 'explicit' | 'status_change' | 'graph_save'

        Returns:
            Combined results from both sync directions
        """
        # Check if sync should proceed
        if not self._should_sync(trigger):
            return {'synced': 0, 'skipped': True, 'reason': f'auto_sync disabled for {trigger}'}

        # Apply debounce
        if not self._apply_debounce():
            return {'synced': 0, 'skipped': True, 'reason': 'debounce active'}

        # Sync in both directions
        # Direction 1: Graph → Beads (create tasks for new features)
        graph_data = self.graph.load()
        features = graph_data.get('entities', {}).get('feature', {})

        created = 0
        for feature_key in features.keys():
            feature_id = f'feature:{feature_key}'
            if self.sync_feature_to_beads(feature_id):
                created += 1

        # Direction 2: Beads → Graph (update status from Beads)
        beads_result = self.sync_beads_to_graph()

        return {
            'synced': beads_result['synced'],
            'created': created,
            'updated': beads_result['updated'],
            'errors': beads_result['errors'],
            'trigger': trigger
        }
```

### Key Design Points:
1. **References-only storage** - no new graph entities
2. **Beads-first conflict resolution** - Beads status always wins
3. **Non-blocking auto-creation** - can be spawned async
4. **Configurable behavior** - respects auto_sync settings
5. **Clear results** - caller gets structured feedback

---

## File 3: `know/know.py` - CLI Additions (~40 lines)

**Location**: Add to bottom of existing `know/know.py` file, after existing commands

```python
# ============================================================================
# BEADS INTEGRATION COMMANDS (Added at end of file)
# ============================================================================

@cli.group()
@click.pass_context
def bd(ctx):
    """Beads task management integration

    Commands:
        know bd init      - Initialize Beads in project
        know bd list      - List Beads tasks with spec mappings
        know bd sync      - Sync Beads status with spec-graph
        know bd <cmd>     - Pass through to bd CLI

    Example:
        know bd init
        know bd task-add "Feature title" "Description"
        know bd sync
    """
    from src.beads_bridge import BeadsBridge, BeadsError

    # Check if Beads is available
    bridge = BeadsBridge()
    is_available, error_msg = bridge.is_available()

    if not is_available:
        console.print(f"[red]{error_msg}[/red]")
        sys.exit(1)

    # Store bridge in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['beads_bridge'] = bridge


@bd.command(name='init')
@click.pass_context
def bd_init(ctx):
    """Initialize Beads in the current project

    This creates the .ai/beads directory and initializes Beads.
    """
    bridge = ctx.obj['beads_bridge']

    result = bridge.run('init')

    if result['success']:
        console.print("[green]✓ Beads initialized successfully[/green]")
        console.print("[dim]Tasks will be stored in .ai/beads[/dim]")
    else:
        console.print(f"[red]✗ Failed to initialize Beads[/red]")
        console.print(f"[dim]{result['stderr']}[/dim]")
        sys.exit(1)


@bd.command(name='list')
@click.pass_context
def bd_list(ctx):
    """List Beads tasks with spec-graph feature mappings"""
    bridge = ctx.obj['beads_bridge']
    graph = ctx.obj['graph']

    # Get Beads tasks
    tasks = bridge.list_tasks()
    if tasks is None:
        console.print("[red]✗ Failed to retrieve Beads tasks[/red]")
        sys.exit(1)

    if not tasks:
        console.print("[yellow]No Beads tasks found[/yellow]")
        return

    # Get feature mappings
    graph_data = graph.load()
    beads_refs = graph_data.get('references', {}).get('beads', {})

    # Build task ID → feature mapping
    task_to_feature = {}
    for ref_key, ref_data in beads_refs.items():
        task_id = ref_data.get('task_id')
        feature = ref_data.get('feature', '(not linked)')
        task_to_feature[task_id] = feature

    # Display table
    table = Table(title="Beads Tasks", show_header=True, header_style="bold magenta")
    table.add_column("Task ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Linked Feature", style="blue")

    for task in tasks:
        task_id = task.get('id', 'unknown')
        title = task.get('title', 'Untitled')
        status = task.get('status', 'pending')
        feature = task_to_feature.get(task_id, '[not linked]')

        table.add_row(task_id, title, status, feature)

    console.print(table)


@bd.command(name='sync')
@click.pass_context
def bd_sync(ctx):
    """Sync Beads tasks with spec-graph

    Updates feature status in spec-graph based on Beads task status.
    Beads is the source of truth (overwrites graph on conflicts).
    """
    from src.task_sync import TaskSync

    bridge = ctx.obj['beads_bridge']
    graph = ctx.obj['graph']

    # Load config
    config = {}  # TODO: Load from .claude/settings.local.json

    # Create sync engine
    sync = TaskSync(graph, bridge, config)

    # Run sync
    result = sync.sync_all(trigger='explicit')

    if result.get('skipped'):
        console.print(f"[yellow]Sync skipped: {result.get('reason')}[/yellow]")
        return

    # Report results
    console.print(f"[green]✓ Sync complete[/green]")
    console.print(f"  Synced: {result.get('synced', 0)} tasks")

    if result.get('created'):
        console.print(f"  [green]Created: {result['created']} new tasks[/green]")

    if result.get('updated'):
        console.print(f"  [blue]Updated: {len(result['updated'])} feature statuses[/blue]")
        for feature_id in result['updated'][:5]:
            console.print(f"    • {feature_id}")
        if len(result['updated']) > 5:
            console.print(f"    ... and {len(result['updated']) - 5} more")

    if result.get('errors'):
        console.print(f"  [yellow]Errors: {len(result['errors'])}[/yellow]")
        for error in result['errors'][:3]:
            console.print(f"    • {error}")


@bd.command(name='passthrough', context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def bd_passthrough(ctx, args):
    """Pass through any command to Beads CLI

    Examples:
        know bd task-add "Title" "Description"
        know bd task get bd-a1b2
        know bd task list
    """
    bridge = ctx.obj['beads_bridge']

    result = bridge.run(*args)

    # Print output
    if result['stdout']:
        console.print(result['stdout'])

    if result['stderr']:
        console.print(f"[yellow]{result['stderr']}[/yellow]")

    # Exit with same code as bd
    if not result['success']:
        sys.exit(result['returncode'])
```

### Integration Points:
1. **Add after existing commands** (at end of file)
2. **No modifications** to existing command group
3. **Import statements** at method level (lazy loading)
4. **Reuse existing patterns**: click decorators, console output, error handling

---

## File 4: `know/src/entities.py` - Minimal Modification (+3 lines)

**Location**: Modify `add_entity()` method in existing `EntityManager` class

**Before** (current code):
```python
def add_entity(self, entity_type, entity_key, entity_data,
               skip_validation=False):
    """Add a new entity"""
    # ... validation code ...

    success = self._save_entity(entity_type, entity_key, entity_data)

    if success:
        console.print(f"[green]✓ Added entity '{entity_type}:{entity_key}'[/green]")
    else:
        console.print(f"[red]✗ Failed to add entity: {error}[/red]")
        sys.exit(1)

    return success, error
```

**After** (with Beads hook):
```python
def add_entity(self, entity_type, entity_key, entity_data,
               skip_validation=False):
    """Add a new entity"""
    # ... validation code ...

    success = self._save_entity(entity_type, entity_key, entity_data)

    if success:
        console.print(f"[green]✓ Added entity '{entity_type}:{entity_key}'[/green]")

        # NEW: Auto-create Beads task for features (non-blocking)
        if entity_type == 'feature' and self._should_auto_create_beads_task():
            self._spawn_beads_task_creation(f'{entity_type}:{entity_key}', entity_data)
    else:
        console.print(f"[red]✗ Failed to add entity: {error}[/red]")
        sys.exit(1)

    return success, error

# NEW: Add helper methods
def _should_auto_create_beads_task(self) -> bool:
    """Check if auto-create is enabled and Beads is available"""
    # TODO: Load from .claude/settings.local.json
    # For now: return False (feature can be enabled later)
    return False

def _spawn_beads_task_creation(self, feature_id: str, feature_data: Dict):
    """Spawn non-blocking Beads task creation"""
    import threading
    from .task_sync import TaskSync
    from .beads_bridge import BeadsBridge

    def create_task():
        try:
            bridge = BeadsBridge()
            if bridge.is_available()[0]:
                sync = TaskSync(self.graph, bridge)
                sync.sync_feature_to_beads(feature_id)
        except Exception:
            pass  # Silently fail - don't block entity creation

    # Run in background thread
    thread = threading.Thread(target=create_task, daemon=True)
    thread.start()
```

---

## Export Changes

**File**: `know/src/__init__.py`

**Add** (at end of imports):
```python
from .beads_bridge import BeadsBridge, BeadsError
from .task_sync import TaskSync

__all__ = [
    # ... existing exports ...
    'BeadsBridge',
    'BeadsError',
    'TaskSync'
]
```

---

## Configuration File

**File**: `.claude/settings.local.json` (optional, extend existing)

```json
{
  "beads": {
    "executable": "bd",
    "enabled": true,
    "auto_create_tasks": false,
    "auto_sync": true,
    "sync_on_status_change": false,
    "sync_on_save": false,
    "sync_debounce_seconds": 1,
    "conflict_resolution": "beads-first"
  }
}
```

**Loading** (in BeadsBridge.__init__):
```python
def _load_config(self):
    """Load Beads config from .claude/settings.local.json"""
    config_path = Path('.claude/settings.local.json')

    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            data = json.load(f)
            return data.get('beads', {})
    except Exception:
        return {}
```

---

## Testing Structure

**File**: `know/tests/test_beads_integration.py`

```python
"""Tests for Beads integration"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.beads_bridge import BeadsBridge, BeadsError
from src.task_sync import TaskSync


class TestBeadsBridge:
    """Test BeadsBridge subprocess wrapper"""

    def test_is_available_found(self):
        """Test that is_available() returns True when bd is in PATH"""
        with patch('shutil.which', return_value='/usr/bin/bd'):
            bridge = BeadsBridge()
            is_avail, error = bridge.is_available()
            assert is_avail is True
            assert error is None

    def test_is_available_not_found(self):
        """Test that is_available() returns False when bd not found"""
        with patch('shutil.which', return_value=None):
            bridge = BeadsBridge()
            is_avail, error = bridge.is_available()
            assert is_avail is False
            assert 'Install Beads' in error

    def test_run_success(self):
        """Test successful command execution"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='output',
                stderr=''
            )

            bridge = BeadsBridge()
            result = bridge.run('init')

            assert result['success'] is True
            assert result['stdout'] == 'output'
            assert result['returncode'] == 0

    def test_run_failure(self):
        """Test failed command execution"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout='',
                stderr='error message'
            )

            bridge = BeadsBridge()
            result = bridge.run('invalid-command')

            assert result['success'] is False
            assert result['returncode'] == 1


class TestTaskSync:
    """Test bidirectional sync logic"""

    def test_sync_feature_to_beads_new_task(self):
        """Test creating new Beads task for feature"""
        mock_graph = Mock()
        mock_graph.load.return_value = {
            'references': {'beads': {}},
            'entities': {'feature': {'auth': {'name': 'Auth', 'description': 'Auth feature'}}}
        }
        mock_graph.get_entities.return_value = {'feature': {'auth': {...}}}

        mock_bridge = Mock()
        mock_bridge.create_task.return_value = 'bd-a1b2'

        sync = TaskSync(mock_graph, mock_bridge)
        result = sync.sync_feature_to_beads('feature:auth')

        assert result is True
        mock_bridge.create_task.assert_called_once()
        mock_graph.save_graph.assert_called_once()

    def test_sync_beads_to_graph(self):
        """Test updating graph from Beads status"""
        mock_graph = Mock()
        mock_graph.load.return_value = {
            'references': {
                'beads': {
                    'auth-a1b2': {
                        'feature': 'feature:auth',
                        'task_id': 'bd-a1b2',
                        'status': 'pending'
                    }
                }
            }
        }

        mock_bridge = Mock()
        mock_bridge.list_tasks.return_value = [
            {
                'id': 'bd-a1b2',
                'title': 'Auth',
                'status': 'complete'
            }
        ]

        sync = TaskSync(mock_graph, mock_bridge)
        result = sync.sync_beads_to_graph()

        assert result['synced'] == 1
        assert 'feature:auth' in result['updated']
        mock_graph.save_graph.assert_called_once()
```

---

## Summary of Changes

| File | Type | Lines | Changes |
|------|------|-------|---------|
| `beads_bridge.py` | NEW | 80 | Complete file |
| `task_sync.py` | NEW | 60 | Complete file |
| `know.py` | MODIFY | +40 | Add 4 commands |
| `entities.py` | MODIFY | +10 | Add 2 helper methods, 1 call in add_entity |
| `__init__.py` | MODIFY | +3 | Add exports |
| `test_beads_integration.py` | NEW | 100 | Test suite |
| **TOTAL** | | **~293** | Low risk |

---

## Implementation Order

1. **Create BeadsBridge** - Test with mock subprocess
2. **Create TaskSync** - Test with mock GraphManager
3. **Add CLI commands** - Integrate with existing know.py
4. **Add config loading** - Extend settings.local.json
5. **Add auto-create hook** - Modify entities.py
6. **Write tests** - Full coverage of happy path + errors
7. **Integration test** - Test with real Beads instance

---

**Status**: Ready for implementation
**Estimated Time**: 4-6 hours total
**Risk Level**: LOW (thin wrapper, zero coupling)
