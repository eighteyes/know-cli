"""
Task management integration for know-cli.

Provides:
- BeadsBridge: Interface to Beads task system (bd CLI)
- TaskManager: Native JSONL task management
- TaskSync: Link tasks to spec-graph features
- Abstract interfaces for plugin architecture
"""

from .interfaces import TaskStorage, TaskSync as TaskSyncInterface
from .beads_bridge import BeadsBridge
from .task_manager import TaskManager
from .task_sync import TaskSync

__all__ = [
    'TaskStorage',
    'TaskSyncInterface',
    'BeadsBridge',
    'TaskManager',
    'TaskSync'
]
