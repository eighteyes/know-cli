# Clean Architecture Design: Beads Integration Feature

**Design Date**: 2025-12-19
**Status**: Architecture Phase (Phase 3)
**Decisions Base**: See `qa/clarification.md` for resolved ambiguities

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Class Hierarchies](#core-class-hierarchies)
3. [Data Schemas](#data-schemas)
4. [Integration Patterns](#integration-patterns)
5. [Error Handling Strategy](#error-handling-strategy)
6. [Sync & Conflict Resolution](#sync--conflict-resolution)
7. [Dependency Injection](#dependency-injection)
8. [CLI Integration](#cli-integration)
9. [Trade-off Analysis](#trade-off-analysis)
10. [Complexity Estimation](#complexity-estimation)
11. [Test Coverage Plan](#test-coverage-plan)

---

## Architecture Overview

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Know CLI Core                              │
│                   (spec-graph management)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         TaskManager Factory                              │   │
│  │  (Instantiates correct implementation via config)        │   │
│  └────────────┬──────────────────────────────────────────┬──┘   │
│               │                                          │       │
│     ┌─────────▼─────────┐                      ┌────────▼────┐  │
│     │  BeadsTaskSystem  │                      │ NativeTask  │  │
│     │  (Beads wrapper)  │                      │  System     │  │
│     │                   │                      │             │  │
│     │ • BeadsBridge     │                      │ • TaskMgr   │  │
│     │ • BeadsSync       │                      │ • TaskSync  │  │
│     └────────┬──────────┘                      └────────┬────┘  │
│              │                                         │        │
│              │        ┌──────────────────┐            │        │
│              │        │   TaskSyncCore   │◀───────────┘        │
│              └───────▶│  (Shared)        │                      │
│                       │                  │                      │
│                       │ • sync()         │                      │
│                       │ • conflict()     │                      │
│                       │ • reconcile()    │                      │
│                       └────────┬─────────┘                      │
│                                │                                │
│                    ┌───────────▼───────────┐                   │
│                    │  spec-graph.json      │                   │
│                    │  references.beads/    │                   │
│                    │  references.tasks     │                   │
│                    └───────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
         │                                          │
         ▼                                          ▼
    ┌─────────────┐                        ┌──────────────┐
    │ .ai/beads/  │                        │ .ai/tasks/   │
    │ issues.jsonl│                        │ tasks.jsonl  │
    │ (via bd)    │                        │ (native)     │
    └──────┬──────┘                        └──────┬───────┘
           │                                      │
           ▼                                      ▼
      ┌────────────┐                        ┌──────────┐
      │ bd CLI     │                        │ Direct   │
      │ (external) │                        │ file I/O │
      └────────────┘                        └──────────┘
```

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│          CLI Layer                          │
│  (know bd, know task commands)              │
├─────────────────────────────────────────────┤
│          API Layer                          │
│  (TaskManager interface + implementations)  │
├─────────────────────────────────────────────┤
│          Domain Layer                       │
│  (TaskSyncCore, ConflictResolver, hooks)   │
├─────────────────────────────────────────────┤
│          Data Layer                         │
│  (JSONL parsers, graph I/O, file ops)      │
├─────────────────────────────────────────────┤
│          Integration Layer                  │
│  (BeadsBridge, subprocess calls)           │
└─────────────────────────────────────────────┘
```

---

## Core Class Hierarchies

### 1. Task System Factory Pattern

```python
# know/src/task_system.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):
    """Unified task status across both systems"""
    READY = "ready"
    IN_PROGRESS = "in-progress"
    BLOCKED = "blocked"
    DONE = "done"
    PAUSED = "paused"


class DependencyType(Enum):
    """Supported dependency types"""
    BLOCKS = "blocks"          # A blocks B (A must complete first)
    RELATED = "related"        # Related context, no blocking


@dataclass
class Task:
    """Canonical task representation (system-agnostic)"""
    id: str                           # tk-a1b2 or bd-a1b2
    title: str
    description: Optional[str] = None
    feature_id: Optional[str] = None  # feature:auth
    status: TaskStatus = TaskStatus.READY
    dependencies: Dict[str, List[str]] = None  # {BLOCKS: [ids], RELATED: [ids]}
    created_at: str = None            # ISO-8601
    updated_at: str = None
    metadata: Dict[str, Any] = None   # System-specific extras

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {
                DependencyType.BLOCKS.value: [],
                DependencyType.RELATED.value: []
            }
        if self.metadata is None:
            self.metadata = {}


class TaskManager(ABC):
    """Abstract interface for task management systems"""

    @abstractmethod
    def add_task(
        self,
        title: str,
        feature_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create new task. Returns canonical Task object."""
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve single task"""
        pass

    @abstractmethod
    def list_tasks(
        self,
        feature_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        ready_only: bool = False
    ) -> List[Task]:
        """Query tasks with optional filters"""
        pass

    @abstractmethod
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Task:
        """Update task properties"""
        pass

    @abstractmethod
    def complete_task(self, task_id: str) -> Task:
        """Mark task complete, handle dependent tasks"""
        pass

    @abstractmethod
    def add_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        dep_type: DependencyType = DependencyType.BLOCKS
    ) -> None:
        """Create dependency between tasks"""
        pass

    @abstractmethod
    def remove_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        dep_type: DependencyType = DependencyType.BLOCKS
    ) -> None:
        """Remove dependency between tasks"""
        pass

    @abstractmethod
    def find_ready_tasks(self) -> List[Task]:
        """Return tasks with no blocking dependencies"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if system is available (e.g., bd installed)"""
        pass


class TaskSystemFactory:
    """Factory for creating appropriate TaskManager instance"""

    _instance: Optional['TaskManagerImpl'] = None

    @staticmethod
    def create(config: Dict[str, Any]) -> TaskManager:
        """
        Create TaskManager based on config.

        Args:
            config: Dict with 'task_system' key ('beads' or 'native')

        Returns:
            Appropriate TaskManager implementation

        Raises:
            TaskSystemError: If system not available or invalid config
        """
        system_type = config.get('task_system', 'native')

        if system_type == 'beads':
            return BeadsTaskSystem(config.get('beads_path', '.ai/beads'))
        elif system_type == 'native':
            return NativeTaskSystem(config.get('tasks_path', '.ai/tasks'))
        else:
            raise TaskSystemError(f"Unknown task system: {system_type}")
```

### 2. Beads Integration (Wrapper Pattern)

```python
# know/src/beads_bridge.py

import subprocess
import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class BeadsError(Exception):
    """Base exception for Beads operations"""
    pass


class BeadsUnavailableError(BeadsError):
    """Raised when bd command not found"""
    pass


class BeadsBridge:
    """
    Low-level interface to Beads CLI.
    Handles subprocess calls, environment setup, JSONL parsing.
    """

    def __init__(self, beads_path: str = ".ai/beads"):
        self.beads_path = Path(beads_path)
        self.beads_dir = self.beads_path  # .ai/beads
        self.symlink_path = Path(".beads")

    def is_available(self) -> bool:
        """Check if bd command exists in PATH"""
        return shutil.which("bd") is not None

    def check_available(self) -> None:
        """Raise error if bd not available with helpful message"""
        if not self.is_available():
            raise BeadsUnavailableError(
                "bd command not found. Install Beads: "
                "https://github.com/steveyegge/beads"
            )

    def init_beads(self, stealth: bool = False) -> bool:
        """
        Initialize Beads integration:
        1. Create .ai/beads/ directory
        2. Create .beads → .ai/beads symlink
        3. Run bd init
        4. Update .gitignore

        Args:
            stealth: If True, run `bd init --stealth`

        Returns:
            True if successful

        Raises:
            BeadsUnavailableError: If bd not installed
            BeadsError: If initialization fails
        """
        self.check_available()

        # Create .ai/beads directory
        self.beads_dir.mkdir(parents=True, exist_ok=True)

        # Create symlink .beads → .ai/beads
        if self.symlink_path.exists() or self.symlink_path.is_symlink():
            self.symlink_path.unlink()

        try:
            self.symlink_path.symlink_to(self.beads_dir.resolve())
        except OSError as e:
            raise BeadsError(f"Failed to create symlink: {e}")

        # Update .gitignore to ignore .beads symlink (not target)
        self._update_gitignore()

        # Run bd init
        args = ["init"]
        if stealth:
            args.append("--stealth")

        try:
            self.call_bd(args)
        except BeadsError as e:
            raise BeadsError(f"bd init failed: {e}")

        return True

    def call_bd(self, args: List[str]) -> Dict[str, Any]:
        """
        Execute bd command and return result.

        Args:
            args: Command arguments (e.g., ["list", "--json"])

        Returns:
            Dict with 'stdout', 'stderr', 'returncode'

        Raises:
            BeadsError: If command fails
        """
        self.check_available()

        try:
            result = subprocess.run(
                ["bd"] + args,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            raise BeadsError(f"bd command timed out: {' '.join(args)}")
        except Exception as e:
            raise BeadsError(f"bd command failed: {e}")

    def parse_jsonl(self, jsonl_path: str) -> List[Dict[str, Any]]:
        """
        Parse JSONL file (one JSON object per line).

        Args:
            jsonl_path: Path to .jsonl file

        Returns:
            List of parsed JSON objects

        Raises:
            BeadsError: If file invalid
        """
        path = Path(jsonl_path)
        if not path.exists():
            return []

        records = []
        try:
            with open(path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        raise BeadsError(
                            f"Invalid JSON at {path}:{line_num}: {e}"
                        )
        except IOError as e:
            raise BeadsError(f"Cannot read {jsonl_path}: {e}")

        return records

    def read_issues(self) -> List[Dict[str, Any]]:
        """Parse .beads/issues.jsonl"""
        issues_path = self.beads_dir / "issues.jsonl"
        return self.parse_jsonl(str(issues_path))

    def _update_gitignore(self) -> None:
        """Add .beads to .gitignore"""
        gitignore = Path(".gitignore")

        if gitignore.exists():
            content = gitignore.read_text()
            if ".beads" not in content:
                gitignore.write_text(content + "\n.beads\n")
        else:
            gitignore.write_text(".beads\n")


class BeadsTaskSystem(TaskManager):
    """
    Beads implementation of TaskManager.
    Wraps BeadsBridge and provides unified interface.
    """

    def __init__(self, beads_path: str = ".ai/beads"):
        self.bridge = BeadsBridge(beads_path)
        self.beads_dir = Path(beads_path)

    def is_available(self) -> bool:
        return self.bridge.is_available()

    def add_task(
        self,
        title: str,
        feature_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Add task via bd command"""
        # Build bd command
        args = ["add", title]

        if description:
            args.extend(["--description", description])

        # Call bd add
        result = self.bridge.call_bd(args)
        if not result['success']:
            raise BeadsError(f"Failed to add task: {result['stderr']}")

        # Parse newly created bead from output
        # Note: This depends on bd output format
        bead_id = self._extract_bead_id(result['stdout'])

        return Task(
            id=bead_id,
            title=title,
            description=description,
            feature_id=feature_id,
            status=TaskStatus.READY,
            metadata=metadata or {}
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        """Fetch single task from beads"""
        issues = self.bridge.read_issues()
        for issue in issues:
            if issue.get('id') == task_id:
                return self._beads_to_task(issue)
        return None

    def list_tasks(
        self,
        feature_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        ready_only: bool = False
    ) -> List[Task]:
        """List tasks from beads, optionally filtered"""
        issues = self.bridge.read_issues()

        tasks = [self._beads_to_task(issue) for issue in issues]

        # Apply filters
        if feature_id:
            tasks = [t for t in tasks if t.feature_id == feature_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        if ready_only:
            tasks = [t for t in tasks if not t.dependencies[DependencyType.BLOCKS.value]]

        return tasks

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Task:
        """Update task via bd command"""
        # bd has update command, or we use patch
        # Details depend on bd CLI
        raise NotImplementedError("See bd documentation for update")

    def complete_task(self, task_id: str) -> Task:
        """Mark task done via bd"""
        result = self.bridge.call_bd(["done", task_id])
        if not result['success']:
            raise BeadsError(f"Failed to mark done: {result['stderr']}")

        task = self.get_task(task_id)
        if not task:
            raise BeadsError(f"Task not found: {task_id}")

        task.status = TaskStatus.DONE
        return task

    def add_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        dep_type: DependencyType = DependencyType.BLOCKS
    ) -> None:
        """Create dependency: from_task blocks to_task"""
        # bd block <task> --on <blocker>
        result = self.bridge.call_bd(["block", to_task_id, "--on", from_task_id])
        if not result['success']:
            raise BeadsError(f"Failed to add dependency: {result['stderr']}")

    def remove_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        dep_type: DependencyType = DependencyType.BLOCKS
    ) -> None:
        """Remove dependency"""
        # bd unblock <task> <blocker>
        result = self.bridge.call_bd(["unblock", to_task_id, from_task_id])
        if not result['success']:
            raise BeadsError(f"Failed to remove dependency: {result['stderr']}")

    def find_ready_tasks(self) -> List[Task]:
        """Get ready tasks from beads"""
        result = self.bridge.call_bd(["ready"])
        if not result['success']:
            raise BeadsError(f"Failed to fetch ready tasks: {result['stderr']}")

        # Parse output - depends on bd format
        return self.list_tasks(ready_only=True)

    def _beads_to_task(self, issue: Dict[str, Any]) -> Task:
        """Convert Beads issue dict to canonical Task"""
        status_map = {
            "ready": TaskStatus.READY,
            "in-progress": TaskStatus.IN_PROGRESS,
            "blocked": TaskStatus.BLOCKED,
            "done": TaskStatus.DONE,
        }

        return Task(
            id=issue.get('id', 'unknown'),
            title=issue.get('title', ''),
            description=issue.get('description'),
            feature_id=issue.get('feature'),  # Custom field we add
            status=TaskStatus(status_map.get(issue.get('status', 'ready'), 'ready')),
            dependencies={
                DependencyType.BLOCKS.value: issue.get('blocks', []),
                DependencyType.RELATED.value: issue.get('related', [])
            },
            created_at=issue.get('created'),
            updated_at=issue.get('updated'),
            metadata=issue
        )

    def _extract_bead_id(self, output: str) -> str:
        """Extract bead ID from bd command output"""
        # Parse output, likely format: "Created bd-a1b2" or similar
        # Implementation depends on bd output
        import re
        match = re.search(r'bd-[a-f0-9]{4}', output)
        if match:
            return match.group(0)
        raise BeadsError(f"Could not extract bead ID from: {output}")
```

### 3. Native Task System (JSONL-based)

```python
# know/src/native_task_manager.py

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict


class NativeTaskSystem(TaskManager):
    """
    Native JSONL-based task system.
    No external dependencies, Git-friendly, supports basic dependencies.
    """

    def __init__(self, tasks_path: str = ".ai/tasks"):
        self.tasks_dir = Path(tasks_path)
        self.tasks_file = self.tasks_dir / "tasks.jsonl"
        self.cache_file = self.tasks_dir / ".task_cache.json"

        # Ensure directory exists
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        # Initialize empty tasks file if needed
        if not self.tasks_file.exists():
            self.tasks_file.touch()

    def is_available(self) -> bool:
        """Native system is always available"""
        return True

    def add_task(
        self,
        title: str,
        feature_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create new task with hash-based ID"""
        task_id = self._generate_id(title)

        now = datetime.utcnow().isoformat() + "Z"

        task = Task(
            id=task_id,
            title=title,
            description=description,
            feature_id=feature_id,
            status=TaskStatus.READY,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )

        # Append to JSONL
        self._append_task(task)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve single task"""
        for task in self._read_all_tasks():
            if task.id == task_id:
                return task
        return None

    def list_tasks(
        self,
        feature_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        ready_only: bool = False
    ) -> List[Task]:
        """List and filter tasks"""
        tasks = self._read_all_tasks()

        if feature_id:
            tasks = [t for t in tasks if t.feature_id == feature_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        if ready_only:
            tasks = [t for t in tasks if not t.dependencies[DependencyType.BLOCKS.value]]

        return tasks

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Task:
        """Update task properties (JSONL rewrite)"""
        tasks = self._read_all_tasks()

        updated_task = None
        for task in tasks:
            if task.id == task_id:
                # Apply updates
                for key, value in updates.items():
                    if key == 'status' and isinstance(value, str):
                        task.status = TaskStatus(value)
                    else:
                        setattr(task, key, value)

                task.updated_at = datetime.utcnow().isoformat() + "Z"
                updated_task = task
                break

        if not updated_task:
            raise ValueError(f"Task not found: {task_id}")

        # Rewrite all tasks
        self._write_all_tasks(tasks)

        return updated_task

    def complete_task(self, task_id: str) -> Task:
        """Mark task done and auto-unblock dependents"""
        task = self.update_task(task_id, {"status": TaskStatus.DONE})

        # Find and unblock dependent tasks
        tasks = self._read_all_tasks()
        for other_task in tasks:
            if task_id in other_task.dependencies[DependencyType.BLOCKS.value]:
                # Remove from blocked_by if exists
                other_task.dependencies[DependencyType.BLOCKS.value].remove(task_id)
                other_task.updated_at = datetime.utcnow().isoformat() + "Z"

        self._write_all_tasks(tasks)

        return task

    def add_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        dep_type: DependencyType = DependencyType.BLOCKS
    ) -> None:
        """Create: from_task blocks to_task"""
        tasks = self._read_all_tasks()
        dep_key = dep_type.value

        for task in tasks:
            if task.id == to_task_id:
                if from_task_id not in task.dependencies[dep_key]:
                    task.dependencies[dep_key].append(from_task_id)
                    task.updated_at = datetime.utcnow().isoformat() + "Z"
                break

        self._write_all_tasks(tasks)

    def remove_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        dep_type: DependencyType = DependencyType.BLOCKS
    ) -> None:
        """Remove dependency"""
        tasks = self._read_all_tasks()
        dep_key = dep_type.value

        for task in tasks:
            if task.id == to_task_id:
                if from_task_id in task.dependencies[dep_key]:
                    task.dependencies[dep_key].remove(from_task_id)
                    task.updated_at = datetime.utcnow().isoformat() + "Z"
                break

        self._write_all_tasks(tasks)

    def find_ready_tasks(self) -> List[Task]:
        """Find all tasks with no blockers"""
        return self.list_tasks(ready_only=True)

    def _generate_id(self, title: str) -> str:
        """
        Generate collision-free hash ID.
        Format: tk-XXXX (4 hex chars)

        Hash: SHA256(title + timestamp)[:4]
        """
        timestamp = datetime.utcnow().isoformat()
        content = f"{title}{timestamp}".encode()
        hash_hex = hashlib.sha256(content).hexdigest()[:4]
        return f"tk-{hash_hex}"

    def _read_all_tasks(self) -> List[Task]:
        """Read all tasks from JSONL"""
        if not self.tasks_file.exists():
            return []

        tasks = []
        with open(self.tasks_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    task = self._dict_to_task(data)
                    tasks.append(task)
                except json.JSONDecodeError as e:
                    # Log warning but don't fail
                    print(f"Warning: Skipping malformed task line: {e}")

        return tasks

    def _write_all_tasks(self, tasks: List[Task]) -> None:
        """Rewrite all tasks (JSONL)"""
        with open(self.tasks_file, 'w') as f:
            for task in tasks:
                task_dict = asdict(task)
                task_dict['status'] = task.status.value
                line = json.dumps(task_dict) + "\n"
                f.write(line)

    def _append_task(self, task: Task) -> None:
        """Append single task to JSONL"""
        task_dict = asdict(task)
        task_dict['status'] = task.status.value
        line = json.dumps(task_dict) + "\n"

        with open(self.tasks_file, 'a') as f:
            f.write(line)

    def _dict_to_task(self, data: Dict[str, Any]) -> Task:
        """Convert dict from JSONL to Task object"""
        status_str = data.get('status', 'ready')
        status = TaskStatus(status_str) if isinstance(status_str, str) else TaskStatus.READY

        dependencies = data.get('dependencies', {
            DependencyType.BLOCKS.value: [],
            DependencyType.RELATED.value: []
        })

        return Task(
            id=data['id'],
            title=data['title'],
            description=data.get('description'),
            feature_id=data.get('feature_id'),
            status=status,
            dependencies=dependencies,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            metadata=data.get('metadata', {})
        )
```

---

## Data Schemas

### 1. Native JSONL Format (`.ai/tasks/tasks.jsonl`)

**Single Task Record**:
```jsonl
{
  "id": "tk-a1b2",
  "title": "Implement JWT validation",
  "description": "Add JWT token validation to auth middleware",
  "feature_id": "feature:auth",
  "status": "ready",
  "dependencies": {
    "blocks": [],
    "related": []
  },
  "created_at": "2025-12-19T10:00:00Z",
  "updated_at": "2025-12-19T10:00:00Z",
  "metadata": {}
}
```

**Blocked Task Record**:
```jsonl
{
  "id": "tk-f3e4",
  "title": "Add refresh token endpoint",
  "description": "Implement token refresh mechanism",
  "feature_id": "feature:auth",
  "status": "blocked",
  "dependencies": {
    "blocks": [],
    "related": ["tk-a1b2"]
  },
  "created_at": "2025-12-19T10:05:00Z",
  "updated_at": "2025-12-19T10:05:00Z",
  "metadata": {}
}
```

**Schema Validation**:
```python
# know/src/schemas.py

from typing import TypedDict, List, Optional, Dict, Any


class TaskJsonl(TypedDict):
    """JSONL task record schema"""
    id: str                    # tk-XXXX
    title: str
    description: Optional[str]
    feature_id: Optional[str]  # feature:name
    status: str               # ready, in-progress, blocked, done
    dependencies: Dict[str, List[str]]  # {blocks: [], related: []}
    created_at: str           # ISO-8601
    updated_at: str
    metadata: Dict[str, Any]


class BeadsIssue(TypedDict):
    """Beads issue record from issues.jsonl"""
    id: str                   # bd-XXXX
    title: str
    description: Optional[str]
    status: str              # ready, in-progress, blocked, done
    blocks: List[str]        # IDs this issue blocks
    related: List[str]       # Related issue IDs
    created: Optional[str]   # ISO-8601
    updated: Optional[str]
    # Custom fields we add:
    feature: Optional[str]   # feature:name linking
```

### 2. Spec-Graph References Schema

**Location**: `.ai/spec-graph.json` → `references.beads` and `references.tasks`

```json
{
  "references": {
    "beads": {
      "bd-a1b2": {
        "title": "Implement JWT validation",
        "feature": "feature:auth",
        "status": "in-progress",
        "created": "2025-12-19T10:00:00Z",
        "updated": "2025-12-19T12:30:00Z",
        "bead_path": ".ai/beads/issues.jsonl"
      }
    },
    "tasks": {
      "tk-f3e4": {
        "title": "Add refresh token endpoint",
        "feature": "feature:auth",
        "status": "blocked",
        "created": "2025-12-19T10:05:00Z",
        "updated": "2025-12-19T10:05:00Z",
        "task_path": ".ai/tasks/tasks.jsonl"
      }
    }
  }
}
```

### 3. Configuration Schema (`.ai/config.json`)

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

## Integration Patterns

### 1. Dependency Injection

```python
# know/src/di.py

from typing import Dict, Any, Optional
from pathlib import Path
import json


class ServiceContainer:
    """Dependency injection container for task systems"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}

    def register(self, name: str, factory, singleton: bool = False):
        """Register service factory"""
        self._services[name] = {
            'factory': factory,
            'singleton': singleton
        }

    def load_config(self, config_path: str = ".ai/config.json"):
        """Load configuration from file"""
        path = Path(config_path)
        if path.exists():
            self._config = json.loads(path.read_text())
        else:
            self._config = self._default_config()

    def get(self, name: str) -> Any:
        """Get service instance"""
        if name not in self._services:
            raise ValueError(f"Service not registered: {name}")

        info = self._services[name]

        # Return singleton if registered
        if info['singleton']:
            if name not in self._singletons:
                self._singletons[name] = info['factory'](self)
            return self._singletons[name]

        # Create new instance
        return info['factory'](self)

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "beads": {
                "executable": "bd",
                "default_path": ".ai/beads",
                "auto_create_tasks": True,
                "auto_sync": True,
                "sync_debounce_seconds": 1,
                "conflict_resolution": "beads-first"
            },
            "tasks": {
                "native_path": ".ai/tasks",
                "hash_algorithm": "sha256-4",
                "dependency_types": ["blocks", "related"]
            }
        }


# Bootstrap DI container
container = ServiceContainer()

# Register services
container.register(
    'graph',
    lambda c: GraphManager('.ai/spec-graph.json'),
    singleton=True
)

container.register(
    'task_manager',
    lambda c: TaskSystemFactory.create(c.get_config()),
    singleton=True
)

container.register(
    'task_sync',
    lambda c: TaskSyncCore(c.get('task_manager'), c.get('graph')),
    singleton=True
)
```

### 2. Hook System for Auto-Sync

```python
# know/src/hooks.py

from typing import Callable, Dict, List, Optional
from enum import Enum


class HookEvent(Enum):
    """System events that trigger hooks"""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    FEATURE_STATUS_CHANGED = "feature_status_changed"
    GRAPH_SAVED = "graph_saved"
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"


class HookRegistry:
    """Manage event hooks for auto-sync"""

    def __init__(self):
        self._hooks: Dict[HookEvent, List[Callable]] = {}

    def register(self, event: HookEvent, handler: Callable) -> None:
        """Register hook handler"""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(handler)

    def emit(self, event: HookEvent, **kwargs) -> None:
        """Trigger all handlers for event"""
        if event in self._hooks:
            for handler in self._hooks[event]:
                try:
                    handler(**kwargs)
                except Exception as e:
                    # Log but don't fail
                    print(f"Hook error for {event}: {e}")


# Global hook registry
hooks = HookRegistry()


# Example usage
def setup_auto_sync(task_manager: TaskManager, graph: GraphManager, config: Dict):
    """Setup auto-sync hooks based on config"""

    if not config.get('beads', {}).get('auto_sync', True):
        return

    def on_feature_status_changed(**kwargs):
        """Sync when feature status changes"""
        feature_id = kwargs.get('feature_id')
        new_status = kwargs.get('new_status')

        # Sync feature status to linked tasks
        # Implementation in TaskSyncCore

    def on_graph_saved(**kwargs):
        """Sync when graph saved"""
        # Debounce to prevent excessive syncs
        # Implementation in TaskSyncCore

    hooks.register(HookEvent.FEATURE_STATUS_CHANGED, on_feature_status_changed)
    hooks.register(HookEvent.GRAPH_SAVED, on_graph_saved)
```

---

## Error Handling Strategy

### 1. Error Hierarchy

```python
# know/src/exceptions.py

class KnowTaskError(Exception):
    """Base exception for task system"""
    pass


class TaskSystemError(KnowTaskError):
    """Task system configuration/availability error"""
    pass


class BeadsError(KnowTaskError):
    """Beads-specific error"""
    pass


class BeadsUnavailableError(BeadsError):
    """bd command not found"""
    pass


class TaskSyncError(KnowTaskError):
    """Sync operation error"""
    pass


class ConflictError(TaskSyncError):
    """Conflict detected during sync"""
    pass


class TaskValidationError(KnowTaskError):
    """Task data validation error"""
    pass


class GraphError(KnowTaskError):
    """Graph operation error"""
    pass
```

### 2. Error Recovery Strategies

```python
# know/src/error_handling.py

from typing import Optional, Callable, TypeVar, Any
from functools import wraps
import time

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    exceptions: tuple = (Exception,)
):
    """Decorator for retrying failed operations"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt * backoff_factor)
                        print(f"Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)

            raise last_exception

        return wrapper
    return decorator


def graceful_fallback(
    fallback_value: Any,
    log_error: bool = True
):
    """Decorator for graceful error handling with fallback"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    print(f"Error in {func.__name__}: {e}")
                return fallback_value

        return wrapper
    return decorator


# Usage example
class BeadsBridge:
    @retry_with_backoff(max_retries=3)
    def call_bd(self, args: List[str]) -> Dict[str, Any]:
        """Retries on failure"""
        pass
```

### 3. User-Facing Error Messages

```python
# know/src/cli/error_messages.py

class ErrorMessage:
    """Helpful error messages for CLI"""

    BEADS_NOT_FOUND = """
bd command not found. Install Beads:

  https://github.com/steveyegge/beads

Or use the native task system instead:

  know task init
"""

    SYNC_CONFLICT = """
Conflict detected during sync:

  {conflict_details}

Beads status takes precedence. If you want to keep local changes:
1. Manually resolve in spec-graph.json
2. Run 'know bd sync --force' to import Beads state
"""

    TASK_NOT_FOUND = """
Task not found: {task_id}

Available tasks in {system}:
{task_list}
"""
```

---

## Sync & Conflict Resolution

### 1. TaskSyncCore

```python
# know/src/task_sync.py

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SyncDirection(Enum):
    """Sync direction"""
    BEADS_TO_GRAPH = "beads_to_graph"
    GRAPH_TO_BEADS = "graph_to_beads"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class SyncResult:
    """Result of sync operation"""
    direction: SyncDirection
    tasks_synced: int
    conflicts_found: int
    conflicts: List[Dict[str, Any]]
    errors: List[str]


class TaskSyncCore:
    """
    Bidirectional sync between task system and spec-graph.
    Implements conflict resolution per clarification.md decisions.
    """

    def __init__(
        self,
        task_manager: TaskManager,
        graph_manager: 'GraphManager',
        config: Dict[str, Any]
    ):
        self.task_manager = task_manager
        self.graph = graph_manager
        self.config = config

    def sync(
        self,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> SyncResult:
        """
        Perform sync operation.

        By clarification.md decision #5:
        - Default: Beads is source of truth (beads_to_graph)
        - Graph → Beads only for NEW task creation
        - Status always flows: Beads → Graph
        """

        if direction == SyncDirection.BEADS_TO_GRAPH:
            return self._sync_beads_to_graph()
        elif direction == SyncDirection.GRAPH_TO_BEADS:
            return self._sync_graph_to_beads()
        else:
            # Bidirectional: first import beads status, then export new tasks
            result1 = self._sync_beads_to_graph()
            result2 = self._sync_graph_to_beads()

            return SyncResult(
                direction=direction,
                tasks_synced=result1.tasks_synced + result2.tasks_synced,
                conflicts_found=result1.conflicts_found + result2.conflicts_found,
                conflicts=result1.conflicts + result2.conflicts,
                errors=result1.errors + result2.errors
            )

    def _sync_beads_to_graph(self) -> SyncResult:
        """
        Import task states from task manager to spec-graph.

        Beads status takes precedence over graph status.
        """
        errors = []
        conflicts = []
        synced_count = 0

        # Get all tasks from current system
        all_tasks = self.task_manager.list_tasks()

        # Get current references from graph
        graph_data = self.graph.get_graph()
        if 'references' not in graph_data:
            graph_data['references'] = {}

        ref_key = self._get_reference_key()  # 'beads' or 'tasks'
        if ref_key not in graph_data['references']:
            graph_data['references'][ref_key] = {}

        refs = graph_data['references'][ref_key]

        # Process each task
        for task in all_tasks:
            try:
                # Check for conflicts
                if task.id in refs:
                    existing = refs[task.id]
                    if existing.get('status') != task.status.value:
                        conflicts.append({
                            'task_id': task.id,
                            'graph_status': existing.get('status'),
                            'task_status': task.status.value,
                            'resolution': 'beads-first (task status used)'
                        })

                # Update graph with task state (beads wins)
                refs[task.id] = {
                    'title': task.title,
                    'feature': task.feature_id,
                    'status': task.status.value,
                    'created': task.created_at,
                    'updated': task.updated_at,
                    'task_path': str(self.task_manager.tasks_dir)
                }

                synced_count += 1

            except Exception as e:
                errors.append(f"Failed to sync {task.id}: {e}")

        # Save updated graph
        self.graph.save_graph(graph_data)

        return SyncResult(
            direction=SyncDirection.BEADS_TO_GRAPH,
            tasks_synced=synced_count,
            conflicts_found=len(conflicts),
            conflicts=conflicts,
            errors=errors
        )

    def _sync_graph_to_beads(self) -> SyncResult:
        """
        Export NEW tasks from spec-graph to task system.

        Only creates new tasks, doesn't modify existing ones.
        """
        errors = []
        synced_count = 0

        # Get all features from graph
        graph_data = self.graph.get_graph()
        features = graph_data.get('entities', {}).get('feature', {})

        # Get existing task references
        ref_key = self._get_reference_key()
        existing_refs = graph_data.get('references', {}).get(ref_key, {})

        # Find features without linked tasks
        for feature_id, feature in features.items():
            try:
                # Skip if already has task
                has_task = any(
                    ref.get('feature') == f"feature:{feature_id}"
                    for ref in existing_refs.values()
                )

                if has_task:
                    continue

                # Create task for this feature
                task_title = feature.get('name', feature_id)
                task = self.task_manager.add_task(
                    title=task_title,
                    feature_id=f"feature:{feature_id}",
                    description=feature.get('description')
                )

                # Add to graph references
                if 'references' not in graph_data:
                    graph_data['references'] = {}
                if ref_key not in graph_data['references']:
                    graph_data['references'][ref_key] = {}

                graph_data['references'][ref_key][task.id] = {
                    'title': task.title,
                    'feature': task.feature_id,
                    'status': task.status.value,
                    'created': task.created_at,
                    'updated': task.updated_at
                }

                synced_count += 1

            except Exception as e:
                errors.append(f"Failed to create task for {feature_id}: {e}")

        # Save updated graph
        self.graph.save_graph(graph_data)

        return SyncResult(
            direction=SyncDirection.GRAPH_TO_BEADS,
            tasks_synced=synced_count,
            conflicts_found=0,
            conflicts=[],
            errors=errors
        )

    def _get_reference_key(self) -> str:
        """Determine reference key based on task system"""
        if isinstance(self.task_manager, BeadsTaskSystem):
            return "beads"
        else:
            return "tasks"
```

### 2. Conflict Resolution Logic

```python
# know/src/conflict_resolution.py

class ConflictResolver:
    """Handles conflict resolution during sync"""

    @staticmethod
    def resolve(
        task_id: str,
        beads_state: Dict[str, Any],
        graph_state: Dict[str, Any],
        policy: str = "beads-first"
    ) -> Dict[str, Any]:
        """
        Resolve conflict between task and graph states.

        Args:
            task_id: ID of conflicting task
            beads_state: State from task system
            graph_state: State from spec-graph
            policy: Resolution policy (beads-first, graph-first, manual)

        Returns:
            Resolved state
        """

        if policy == "beads-first":
            # By clarification.md decision #2: Beads is source of truth
            return beads_state

        elif policy == "graph-first":
            return graph_state

        elif policy == "manual":
            # User must resolve manually
            raise ConflictError(
                f"Manual resolution required for {task_id}. "
                f"Beads: {beads_state['status']}, "
                f"Graph: {graph_state['status']}"
            )

        else:
            raise ValueError(f"Unknown policy: {policy}")
```

---

## CLI Integration

### 1. Command Structure

```python
# know/src/cli/beads_commands.py

import click
from typing import Optional
from ..task_system import TaskSystemFactory, TaskManager
from ..beads_bridge import BeadsBridge, BeadsError
from ..task_sync import TaskSyncCore


@click.group(name='bd')
@click.pass_context
def beads_group(ctx):
    """Beads integration commands (matching bd shorthand)"""
    ctx.ensure_object(dict)


@beads_group.command(name='init')
@click.option('--path', default='.ai/beads', help='Beads directory')
@click.option('--stealth', is_flag=True, help='Stealth mode')
@click.pass_context
def beads_init(ctx, path, stealth):
    """Initialize Beads integration"""

    bridge = BeadsBridge(path)

    try:
        bridge.init_beads(stealth=stealth)
        click.echo(f"✓ Beads initialized in {path}")
    except BeadsError as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)


@beads_group.command(name='sync')
@click.option('--import', 'sync_import', is_flag=True,
              help='Import from Beads to graph')
@click.option('--export', 'sync_export', is_flag=True,
              help='Export from graph to Beads')
@click.option('--feature', help='Sync specific feature')
@click.pass_context
def beads_sync(ctx, sync_import, sync_export, feature):
    """Sync Beads and spec-graph"""

    # Determine direction
    if sync_import and sync_export:
        direction = "bidirectional"
    elif sync_import:
        direction = "beads_to_graph"
    elif sync_export:
        direction = "graph_to_beads"
    else:
        direction = "bidirectional"  # Default

    try:
        task_manager = TaskSystemFactory.create(config)
        graph = GraphManager()
        sync = TaskSyncCore(task_manager, graph, config)

        result = sync.sync(direction)

        click.echo(f"✓ Synced {result.tasks_synced} tasks")
        if result.conflicts_found > 0:
            click.echo(f"⚠ {result.conflicts_found} conflicts resolved (Beads won)")

        for error in result.errors:
            click.echo(f"✗ {error}", err=True)

    except Exception as e:
        click.echo(f"✗ Sync failed: {e}", err=True)
        raise SystemExit(1)


@beads_group.command(name='list', context_settings=dict(ignore_unknown_options=True))
@click.option('--ready', is_flag=True, help='Show only ready tasks')
@click.option('--feature', help='Filter by feature')
@click.pass_context
def beads_list(ctx, ready, feature):
    """List Beads tasks"""

    try:
        task_manager = TaskSystemFactory.create(config)

        tasks = task_manager.list_tasks(
            feature_id=feature,
            ready_only=ready
        )

        if not tasks:
            click.echo("No tasks found")
            return

        # Display tasks in table
        for task in tasks:
            status_icon = "✓" if task.status.value == "done" else "•"
            click.echo(
                f"{status_icon} {task.id:10} {task.title[:40]:40} {task.status.value:12}"
            )

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)


@beads_group.command(name='add')
@click.argument('title')
@click.option('--description', help='Task description')
@click.option('--feature', help='Link to feature')
@click.pass_context
def beads_add(ctx, title, description, feature):
    """Add Beads task"""

    try:
        task_manager = TaskSystemFactory.create(config)
        task = task_manager.add_task(
            title=title,
            description=description,
            feature_id=feature
        )

        click.echo(f"✓ Created {task.id}: {task.title}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise SystemExit(1)


# ... similar for know task commands
```

---

## Trade-off Analysis

### Design Approach 1: Monolithic (Score: C)

**Description**: Single large class handling all task logic.

**Pros**:
- Simple structure for small feature sets
- Fewer files to manage
- Direct method calls

**Cons**:
- Hard to switch systems
- Coupling increases with features
- Difficult to test independently
- Not extensible for hybrid mode
- Violates single responsibility

**Complexity**: ~200 lines per system, ~400 total

**Verdict**: Not recommended

---

### Design Approach 2: Abstract Factory (Score: A)

**Description**: Clean abstraction with concrete implementations.

**Pros**:
- Easy to switch between Beads/Native
- Unified interface for both systems
- Extensible for future systems
- Testable with mock implementations
- Follows SOLID principles
- Native system works independently

**Cons**:
- More files and classes initially
- Learning curve for developers
- Over-engineered for MVP
- But pays off with complexity later

**Complexity**:
- ~150 lines base abstraction
- ~200 lines Beads implementation
- ~200 lines Native implementation
- ~300 lines Sync core
- Total: ~850 lines

**Verdict**: Recommended - Best long-term maintainability

---

### Design Approach 3: Adapter Pattern (Score: B)

**Description**: Adapt Beads and Native to common interface.

**Pros**:
- Good for integrating external systems
- Clear separation of concerns
- Works with existing Beads code

**Cons**:
- Requires wrapping Beads CLI calls
- Native system still needs full implementation
- Sync logic still complex

**Complexity**: ~700 lines total

**Verdict**: Good middle ground, but less flexible

---

**Selected**: Approach 2 (Abstract Factory) - Best balance

---

## Complexity Estimation

### Lines of Code Breakdown

| Component | Files | LOC | Complexity |
|-----------|-------|-----|------------|
| Base abstractions (Task, TaskManager, enums) | 1 | 150 | Low |
| Beads bridge & subprocess handling | 1 | 250 | Medium |
| Beads TaskManager implementation | 1 | 200 | Medium |
| Native JSONL implementation | 1 | 250 | Medium |
| Task sync core & conflict resolution | 1 | 300 | High |
| Dependency injection & hooks | 1 | 150 | Medium |
| CLI commands (bd + task groups) | 2 | 400 | Low-Medium |
| Tests (unit + integration) | 3 | 600 | High |
| Error handling & utils | 1 | 150 | Low |
| **TOTAL** | **12** | **2450** | **Medium-High** |

### Time Estimation

| Phase | Task | Time | Dependencies |
|-------|------|------|--------------|
| 1 | Base abstractions & data models | 2h | None |
| 2 | Beads bridge implementation | 3h | #1 |
| 3 | Beads TaskManager wrapper | 2h | #1, #2 |
| 4 | Native JSONL implementation | 3h | #1 |
| 5 | Sync core & conflict resolution | 4h | #1, #3, #4 |
| 6 | DI & hooks system | 2h | #1, #5 |
| 7 | CLI commands | 3h | #1, #3, #4, #6 |
| 8 | Error handling & edge cases | 2h | #2, #7 |
| 9 | Unit tests | 4h | #1-8 |
| 10 | Integration tests | 3h | #1-9 |
| 11 | Edge case testing | 2h | #1-10 |
| 12 | Documentation & polish | 2h | #1-11 |
| **Total** | | **32 hours** | |

### File Structure

```
know/
├── src/
│   ├── task_system.py           (350 LOC - abstractions)
│   ├── beads_bridge.py          (250 LOC - subprocess, JSONL)
│   ├── beads_task_system.py     (200 LOC - BeadsTaskSystem impl)
│   ├── native_task_system.py    (250 LOC - NativeTaskSystem impl)
│   ├── task_sync.py             (300 LOC - sync logic)
│   ├── conflict_resolution.py   (80 LOC - conflict handling)
│   ├── hooks.py                 (70 LOC - event system)
│   ├── di.py                    (80 LOC - dependency injection)
│   ├── exceptions.py            (50 LOC - error hierarchy)
│   ├── schemas.py               (60 LOC - TypedDicts)
│   └── cli/
│       ├── beads_commands.py    (200 LOC)
│       ├── task_commands.py     (200 LOC)
│       └── error_messages.py    (100 LOC)
├── tests/
│   ├── test_beads_bridge.py     (150 LOC)
│   ├── test_task_managers.py    (200 LOC)
│   ├── test_task_sync.py        (250 LOC)
│   └── test_integration.py      (200 LOC)
└── config/
    └── task-system-config.json

.ai/
├── tasks/
│   ├── tasks.jsonl
│   └── .gitignore
└── config.json
```

### Test Coverage Plan

**Unit Tests** (8 test files, ~150 LOC each):
1. `test_base_abstractions.py` - Task class, enums, interfaces
2. `test_beads_bridge.py` - BeadsBridge subprocess handling
3. `test_beads_task_system.py` - BeadsTaskSystem implementation
4. `test_native_task_system.py` - NativeTaskSystem JSONL handling
5. `test_task_sync_core.py` - Sync logic and conflict resolution
6. `test_hooks.py` - Event system
7. `test_di.py` - Dependency injection
8. `test_cli_commands.py` - CLI argument parsing

**Integration Tests** (2 test files, ~200 LOC each):
1. `test_beads_integration_end_to_end.py`
   - Full flow: init → create tasks → sync → verify graph
   - Requires real bd installation or mock
2. `test_native_end_to_end.py`
   - Full flow: init → create tasks → link → query ready
   - No external dependencies

**Edge Case Tests**:
- Missing bd executable
- Corrupt JSONL files
- Sync conflicts resolution
- Large task sets (1000+ tasks)
- Circular dependency detection
- Graph reference validation

**Target Coverage**: 80%+

---

## Architecture Decisions

### ADR 1: Factory Pattern for Task Systems

**Context**: Multiple task system implementations (Beads, Native)

**Decision**: Use Abstract Factory + concrete implementations

**Rationale**:
- Cleanly separates concerns
- Supports runtime switching
- Extensible for future systems
- Testable with mocks

**Consequences**:
- More classes initially
- Configuration-driven instantiation
- Better long-term maintainability

---

### ADR 2: Conflict Resolution

**Context**: Beads and spec-graph may diverge

**Decision**: Beads is source of truth (clarification.md decision #2)

**Rationale**:
- Beads is execution layer
- Tasks may be worked on outside Know
- Graph status derives from reality
- Clear tie-breaker for disputes

**Consequences**:
- Graph status might be stale initially
- Auto-sync brings them into alignment
- Users can manually override if needed

---

### ADR 3: Native JSONL Format

**Context**: Need task system without external dependencies

**Decision**: Simple JSONL with SHA256 hash IDs (clarification.md decision #6, #7)

**Rationale**:
- Git-friendly (human-readable, mergeable)
- Collision-resistant IDs
- No database overhead
- Supports both dependency types needed for MVP

**Consequences**:
- Linear performance for large sets
- Can add indexing later
- Format is immutable once written

---

### ADR 4: Dependency Injection

**Context**: Multiple components need shared instances

**Decision**: Custom lightweight DI container

**Rationale**:
- Avoid heavy framework dependency
- Fine-grained control
- Testing with mocks
- Configuration-driven setup

**Consequences**:
- Custom code instead of using framework
- But keeps know lightweight

---

## Next Steps

1. **Implement** Phase 1-2: Core abstractions + Beads bridge
2. **Validate** Phase 3: Sync with real Beads installation
3. **Test** Phase 4-5: Native system with edge cases
4. **Integrate** Phase 6-7: CLI commands + config
5. **Polish** Phase 8-12: Error handling, docs, release

---

## References

- Clarification Q&A: `qa/clarification.md`
- Feature Overview: `overview.md`
- Todo Checklist: `todo.md`
- Beads Repository: https://github.com/steveyegge/beads
- Know Graph System: See `CLAUDE.md` dual graph architecture
