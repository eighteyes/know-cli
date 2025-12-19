"""
Abstract base classes for task storage backends.

Enables plugin architecture for swappable task systems:
- BeadsStorage (subprocess wrapper)
- JsonlStorage (native JSONL format)
- Future: DatabaseStorage, GithubIssuesStorage, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class TaskStorage(ABC):
    """Abstract storage backend for tasks"""

    @abstractmethod
    def create(self, task: Dict) -> str:
        """
        Create a new task.

        Args:
            task: Task dictionary with title, feature, etc.

        Returns:
            Task ID (e.g., "tk-a1b2", "bd-x1y2")
        """
        pass

    @abstractmethod
    def read(self, task_id: str) -> Optional[Dict]:
        """
        Read a single task by ID.

        Args:
            task_id: Unique task identifier

        Returns:
            Task dictionary or None if not found
        """
        pass

    @abstractmethod
    def list(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        List tasks with optional filters.

        Args:
            filters: Optional dict of filters (e.g., {"status": "ready", "feature": "feature:auth"})

        Returns:
            List of task dictionaries
        """
        pass

    @abstractmethod
    def update(self, task_id: str, updates: Dict) -> bool:
        """
        Update an existing task.

        Args:
            task_id: Task to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task to delete

        Returns:
            True if successful, False otherwise
        """
        pass


class TaskSync(ABC):
    """Abstract sync interface for task-to-feature linking"""

    @abstractmethod
    def import_tasks(self) -> int:
        """
        Import tasks from storage to spec-graph references.

        Returns:
            Number of tasks imported
        """
        pass

    @abstractmethod
    def link_task_to_feature(self, task_id: str, feature_id: str) -> bool:
        """
        Associate a task with a feature in the spec-graph.

        Args:
            task_id: Task identifier
            feature_id: Feature entity ID (e.g., "feature:auth")

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_feature_tasks(self, feature_id: str) -> List[Dict]:
        """
        Get all tasks linked to a feature.

        Args:
            feature_id: Feature entity ID

        Returns:
            List of task dictionaries
        """
        pass

    @abstractmethod
    def sync_status(self) -> Dict:
        """
        Sync task status between storage and spec-graph.

        Returns:
            Dict with sync statistics (e.g., {"imported": 5, "updated": 2})
        """
        pass
