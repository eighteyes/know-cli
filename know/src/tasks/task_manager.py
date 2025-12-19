"""
TaskManager: Native JSONL task management system.

Responsibilities:
- Create/read/update/delete tasks in .ai/tasks/tasks.jsonl
- Generate hash-based task IDs (tk-xxxx)
- Track simple dependencies (blocks, blocked_by)
- Auto-ready detection (tasks with no blockers)
- JSONL append-only operations

MVP Scope (Phase 1):
- Simple JSONL operations
- Blocks + blocked_by dependencies only
- No parent-child, no time tracking, no comments
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class TaskManager:
    """Native JSONL task management"""

    def __init__(self, tasks_path: str = ".ai/tasks"):
        """
        Initialize task manager.

        Args:
            tasks_path: Path to tasks directory (default: .ai/tasks)
        """
        self.tasks_path = Path(tasks_path)
        self.tasks_jsonl = self.tasks_path / "tasks.jsonl"

    def init_tasks(self) -> tuple[bool, Optional[str]]:
        """
        Initialize native task system.

        Steps:
        1. Create .ai/tasks/ directory
        2. Create empty tasks.jsonl
        3. Update .gitignore (if needed)

        Returns:
            (success, error_message)
        """
        try:
            # Create directory
            self.tasks_path.mkdir(parents=True, exist_ok=True)

            # Create empty JSONL file if it doesn't exist
            if not self.tasks_jsonl.exists():
                self.tasks_jsonl.touch()

            # Update .gitignore
            self._update_gitignore()

            return True, None

        except OSError as e:
            return False, f"Failed to initialize tasks: {e}"

    def add_task(
        self,
        title: str,
        feature: Optional[str] = None,
        description: str = "",
        status: str = "ready"
    ) -> str:
        """
        Create a new task with hash-based ID.

        Args:
            title: Task title
            feature: Optional feature entity ID (e.g., "feature:auth")
            description: Optional task description
            status: Initial status (default: "ready")

        Returns:
            Task ID (e.g., "tk-a1b2")
        """
        # Generate hash ID
        task_id = self.generate_hash_id(title)

        # Create task object
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "feature": feature,
            "status": status,
            "blocks": [],       # Tasks this task blocks
            "blocked_by": [],   # Tasks blocking this task
            "related": [],      # Related tasks (non-blocking)
            "created": datetime.utcnow().isoformat(),
            "updated": datetime.utcnow().isoformat()
        }

        # Append to JSONL
        self._append_task(task)

        return task_id

    def list_tasks(
        self,
        feature: Optional[str] = None,
        status: Optional[str] = None,
        ready_only: bool = False
    ) -> List[Dict]:
        """
        Query tasks with filters.

        Args:
            feature: Filter by feature ID
            status: Filter by status (e.g., "ready", "in-progress", "done")
            ready_only: If True, only return ready tasks (no blockers)

        Returns:
            List of task dictionaries
        """
        tasks = self._load_all_tasks()

        # Apply filters
        if feature:
            tasks = [t for t in tasks if t.get('feature') == feature]

        if status:
            tasks = [t for t in tasks if t.get('status') == status]

        if ready_only:
            tasks = [t for t in tasks if not t.get('blocked_by') and t.get('status') != 'done']

        return tasks

    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Get a single task by ID.

        Args:
            task_id: Task ID (e.g., "tk-a1b2")

        Returns:
            Task dictionary or None if not found
        """
        tasks = self._load_all_tasks()
        for task in tasks:
            if task.get('id') == task_id:
                return task
        return None

    def mark_done(self, task_id: str) -> tuple[bool, Optional[str]]:
        """
        Mark task complete and auto-unblock dependents.

        Args:
            task_id: Task to mark complete

        Returns:
            (success, error_message)
        """
        tasks = self._load_all_tasks()

        # Find task
        task = None
        for t in tasks:
            if t.get('id') == task_id:
                task = t
                break

        if not task:
            return False, f"Task {task_id} not found"

        # Mark task as done
        task['status'] = 'done'
        task['updated'] = datetime.utcnow().isoformat()

        # Auto-unblock dependents
        unblocked_count = 0
        for other_task in tasks:
            if task_id in other_task.get('blocked_by', []):
                other_task['blocked_by'].remove(task_id)
                other_task['updated'] = datetime.utcnow().isoformat()

                # If no more blockers, mark as ready
                if not other_task['blocked_by'] and other_task['status'] == 'blocked':
                    other_task['status'] = 'ready'
                    unblocked_count += 1

        # Rewrite JSONL with updated tasks
        self._rewrite_all_tasks(tasks)

        message = f"Marked {task_id} as done"
        if unblocked_count > 0:
            message += f" (auto-unblocked {unblocked_count} task{'s' if unblocked_count > 1 else ''})"

        return True, message

    def block_task(self, task_id: str, blocker_id: str) -> tuple[bool, Optional[str]]:
        """
        Create blocking dependency (blocker_id blocks task_id).

        Args:
            task_id: Task to be blocked
            blocker_id: Task that blocks task_id

        Returns:
            (success, error_message)
        """
        tasks = self._load_all_tasks()

        # Find both tasks
        task = None
        blocker = None
        for t in tasks:
            if t.get('id') == task_id:
                task = t
            if t.get('id') == blocker_id:
                blocker = t

        if not task:
            return False, f"Task {task_id} not found"
        if not blocker:
            return False, f"Blocker task {blocker_id} not found"

        # Add blocking relationship
        if blocker_id not in task.get('blocked_by', []):
            task['blocked_by'].append(blocker_id)
            task['updated'] = datetime.utcnow().isoformat()

            # Update blocker's blocks list
            if task_id not in blocker.get('blocks', []):
                blocker['blocks'].append(task_id)
                blocker['updated'] = datetime.utcnow().isoformat()

            # Update task status to blocked if it was ready
            if task['status'] == 'ready':
                task['status'] = 'blocked'

            # Rewrite JSONL
            self._rewrite_all_tasks(tasks)

            return True, f"Task {task_id} is now blocked by {blocker_id}"
        else:
            return False, f"Task {task_id} is already blocked by {blocker_id}"

    def find_ready(self) -> List[Dict]:
        """
        Auto-ready detection: tasks with no blockers.

        Returns:
            List of ready task dictionaries
        """
        tasks = self._load_all_tasks()

        ready_tasks = [
            t for t in tasks
            if not t.get('blocked_by')
            and t.get('status') != 'done'
        ]

        return ready_tasks

    def generate_hash_id(self, title: str) -> str:
        """
        Generate collision-free hash ID from title and timestamp.

        Format: tk-xxxx (4 hex chars from SHA256 hash)

        Args:
            title: Task title

        Returns:
            Task ID (e.g., "tk-a1b2")
        """
        timestamp = datetime.utcnow().isoformat()
        content = f"{title}{timestamp}"
        hash_hex = hashlib.sha256(content.encode()).hexdigest()
        return f"tk-{hash_hex[:4]}"

    def _load_all_tasks(self) -> List[Dict]:
        """
        Load all tasks from JSONL file.

        Returns:
            List of task dictionaries
        """
        if not self.tasks_jsonl.exists():
            return []

        tasks = []
        try:
            with open(self.tasks_jsonl, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue

                    try:
                        task = json.loads(line)
                        tasks.append(task)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Corrupted JSONL at line {line_num}: {e}")
                        print(f"  Line: {line[:100]}...")
                        continue

        except OSError as e:
            print(f"Error reading {self.tasks_jsonl}: {e}")
            return []

        return tasks

    def _append_task(self, task: Dict):
        """
        Append a task to JSONL file.

        Args:
            task: Task dictionary to append
        """
        # Ensure directory exists
        self.tasks_path.mkdir(parents=True, exist_ok=True)

        # Append to JSONL
        with open(self.tasks_jsonl, 'a', encoding='utf-8') as f:
            f.write(json.dumps(task) + '\n')

    def _rewrite_all_tasks(self, tasks: List[Dict]):
        """
        Rewrite entire JSONL file with updated tasks.

        This is used for updates (e.g., marking done, adding dependencies).

        Args:
            tasks: Complete list of tasks to write
        """
        # Ensure directory exists
        self.tasks_path.mkdir(parents=True, exist_ok=True)

        # Rewrite JSONL
        with open(self.tasks_jsonl, 'w', encoding='utf-8') as f:
            for task in tasks:
                f.write(json.dumps(task) + '\n')

    def _update_gitignore(self):
        """
        Add .ai/tasks/ to .gitignore if needed.

        Note: tasks.jsonl should typically be committed,
        but we leave this as a placeholder for future extensions.
        """
        # For now, we don't add anything to .gitignore
        # tasks.jsonl is meant to be committed
        pass
