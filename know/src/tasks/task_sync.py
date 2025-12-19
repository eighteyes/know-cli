"""
TaskSync: Link tasks to spec-graph features.

Responsibilities:
- Import Beads/native tasks into spec-graph references
- Link tasks to features in graph
- Read task-feature associations
- Sync task status (Beads-first strategy)

MVP Scope (Phase 1):
- Import tasks to references.beads or references.task
- Manual sync only (no auto-sync hooks)
- Simple status sync
- No bidirectional sync, no conflict UI
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from ..graph import GraphManager
from .beads_bridge import BeadsBridge
from .task_manager import TaskManager


class TaskSync:
    """Sync tasks between Beads/native and spec-graph"""

    def __init__(
        self,
        graph_path: str = ".ai/spec-graph.json",
        beads_path: str = ".ai/beads",
        tasks_path: str = ".ai/tasks"
    ):
        """
        Initialize sync engine.

        Args:
            graph_path: Path to spec-graph.json
            beads_path: Path to Beads directory
            tasks_path: Path to native tasks directory
        """
        self.graph = GraphManager(graph_path)
        self.beads = BeadsBridge(beads_path)
        self.tasks = TaskManager(tasks_path)

    def import_beads_tasks(self) -> tuple[int, Optional[str]]:
        """
        Import Beads tasks into spec-graph references.

        Reads .beads/issues.jsonl and stores in spec-graph references.beads.
        Links to features via task metadata.

        Returns:
            (number_of_tasks_imported, error_message)
        """
        # Parse Beads JSONL
        beads_tasks = self.beads.parse_beads_jsonl()

        if not beads_tasks:
            return 0, "No Beads tasks found"

        # Get current graph
        graph_data = self.graph.get_graph()

        # Ensure references.beads exists
        if 'references' not in graph_data:
            graph_data['references'] = {}

        if 'beads' not in graph_data['references']:
            graph_data['references']['beads'] = {}

        # Import each task
        imported = 0
        for task in beads_tasks:
            task_id = task.get('id')
            if not task_id:
                continue

            # Store task in references (without the 'bd-' prefix in key)
            # The ID is like "bd-a1b2", we store as key without prefix for clarity
            key = task_id

            graph_data['references']['beads'][key] = {
                'title': task.get('title', ''),
                'description': task.get('description', ''),
                'status': task.get('status', 'ready'),
                'feature': task.get('feature'),  # May be None
                'created': task.get('created', ''),
                'updated': task.get('updated', task.get('created', ''))
            }

            imported += 1

        # Save updated graph
        success = self.graph.save_graph(graph_data)

        if not success:
            return 0, "Failed to save graph"

        return imported, None

    def import_native_tasks(self) -> tuple[int, Optional[str]]:
        """
        Import native tasks into spec-graph references.

        Reads .ai/tasks/tasks.jsonl and stores in spec-graph references.task.

        Returns:
            (number_of_tasks_imported, error_message)
        """
        # Load native tasks
        native_tasks = self.tasks.list_tasks()

        if not native_tasks:
            return 0, "No native tasks found"

        # Get current graph
        graph_data = self.graph.get_graph()

        # Ensure references.task exists
        if 'references' not in graph_data:
            graph_data['references'] = {}

        if 'task' not in graph_data['references']:
            graph_data['references']['task'] = {}

        # Import each task
        imported = 0
        for task in native_tasks:
            task_id = task.get('id')
            if not task_id:
                continue

            graph_data['references']['task'][task_id] = {
                'title': task.get('title', ''),
                'description': task.get('description', ''),
                'status': task.get('status', 'ready'),
                'feature': task.get('feature'),
                'blocks': task.get('blocks', []),
                'blocked_by': task.get('blocked_by', []),
                'related': task.get('related', []),
                'created': task.get('created', ''),
                'updated': task.get('updated', '')
            }

            imported += 1

        # Save updated graph
        success = self.graph.save_graph(graph_data)

        if not success:
            return 0, "Failed to save graph"

        return imported, None

    def link_task_to_feature(self, task_id: str, feature_id: str, task_system: str = "beads") -> tuple[bool, Optional[str]]:
        """
        Associate a task with a feature in the spec-graph.

        Args:
            task_id: Task ID (e.g., "bd-a1b2", "tk-f3e4")
            feature_id: Feature entity ID (e.g., "feature:auth")
            task_system: "beads" or "task" (native)

        Returns:
            (success, error_message)
        """
        # Get current graph
        graph_data = self.graph.get_graph()

        # Ensure references exist
        if 'references' not in graph_data:
            return False, "No references section in graph"

        ref_category = task_system
        if ref_category not in graph_data['references']:
            return False, f"No {ref_category} references in graph"

        # Find task
        if task_id not in graph_data['references'][ref_category]:
            return False, f"Task {task_id} not found in {ref_category} references"

        # Update task with feature link
        graph_data['references'][ref_category][task_id]['feature'] = feature_id

        # Save updated graph
        success = self.graph.save_graph(graph_data)

        if not success:
            return False, "Failed to save graph"

        return True, None

    def get_feature_tasks(self, feature_id: str, task_system: Optional[str] = None) -> List[Dict]:
        """
        Get all tasks linked to a feature.

        Args:
            feature_id: Feature entity ID (e.g., "feature:auth")
            task_system: Optional filter - "beads", "task", or None for both

        Returns:
            List of task dictionaries
        """
        # Get current graph
        graph_data = self.graph.get_graph()
        references = graph_data.get('references', {})

        tasks = []

        # Determine which reference categories to check
        categories = []
        if task_system is None:
            categories = ['beads', 'task']
        else:
            categories = [task_system]

        # Collect tasks from each category
        for category in categories:
            if category not in references:
                continue

            for task_id, task_data in references[category].items():
                if task_data.get('feature') == feature_id:
                    # Add task with full ID
                    task = task_data.copy()
                    task['id'] = task_id
                    task['system'] = category
                    tasks.append(task)

        return tasks

    def sync_status(self) -> Dict:
        """
        Sync task status from Beads/native to spec-graph.

        Beads-first strategy: Beads/native status overwrites graph status.

        Returns:
            Dict with sync statistics:
            {
                "beads_synced": 5,
                "native_synced": 3,
                "errors": []
            }
        """
        stats = {
            'beads_synced': 0,
            'native_synced': 0,
            'errors': []
        }

        # Get current graph
        graph_data = self.graph.get_graph()
        references = graph_data.get('references', {})

        # Sync Beads tasks
        if 'beads' in references:
            beads_tasks = self.beads.parse_beads_jsonl()
            beads_by_id = {t['id']: t for t in beads_tasks}

            for task_id, ref_data in references['beads'].items():
                # Look up task in Beads JSONL
                beads_task = beads_by_id.get(task_id)

                if beads_task:
                    # Update status from Beads (Beads is source of truth)
                    old_status = ref_data.get('status')
                    new_status = beads_task.get('status')

                    if old_status != new_status:
                        ref_data['status'] = new_status
                        ref_data['updated'] = beads_task.get('updated', beads_task.get('created', ''))
                        stats['beads_synced'] += 1

        # Sync native tasks
        if 'task' in references:
            native_tasks = self.tasks.list_tasks()
            native_by_id = {t['id']: t for t in native_tasks}

            for task_id, ref_data in references['task'].items():
                # Look up task in native JSONL
                native_task = native_by_id.get(task_id)

                if native_task:
                    # Update status from native (native is source of truth)
                    old_status = ref_data.get('status')
                    new_status = native_task.get('status')

                    if old_status != new_status:
                        ref_data['status'] = new_status
                        ref_data['updated'] = native_task.get('updated', '')
                        stats['native_synced'] += 1

        # Save updated graph
        if stats['beads_synced'] > 0 or stats['native_synced'] > 0:
            success = self.graph.save_graph(graph_data)

            if not success:
                stats['errors'].append('Failed to save graph after sync')

        return stats

    def get_stats(self) -> Dict:
        """
        Get task sync statistics.

        Returns:
            Dict with task counts by system and status
        """
        graph_data = self.graph.get_graph()
        references = graph_data.get('references', {})

        stats = {
            'beads': {'total': 0, 'by_status': {}, 'linked_to_features': 0},
            'task': {'total': 0, 'by_status': {}, 'linked_to_features': 0}
        }

        # Count Beads tasks
        if 'beads' in references:
            for task_id, task_data in references['beads'].items():
                stats['beads']['total'] += 1

                status = task_data.get('status', 'unknown')
                stats['beads']['by_status'][status] = stats['beads']['by_status'].get(status, 0) + 1

                if task_data.get('feature'):
                    stats['beads']['linked_to_features'] += 1

        # Count native tasks
        if 'task' in references:
            for task_id, task_data in references['task'].items():
                stats['task']['total'] += 1

                status = task_data.get('status', 'unknown')
                stats['task']['by_status'][status] = stats['task']['by_status'].get(status, 0) + 1

                if task_data.get('feature'):
                    stats['task']['linked_to_features'] += 1

        return stats
