"""
op_manager.py - Operation-level progress tracking for feature implementation

Responsibilities:
- Track op-level progress within features (meta.ops section)
- Mark ops as started/completed with timestamps
- Store commit hashes for completed ops
- Compute next op number based on completion status
"""

from datetime import date
from typing import List, Optional, Dict, Any


class OpManager:
    """Manage op-level progress tracking for feature implementation."""

    VALID_STATUSES = ['pending', 'in-progress', 'complete']

    def __init__(self, graph_manager):
        """Initialize with graph manager.

        Args:
            graph_manager: GraphManager instance
        """
        self.graph = graph_manager

    def _ensure_ops_section(self, feature_id: str) -> dict:
        """Ensure meta.ops.feature_id section exists.

        Args:
            feature_id: Feature identifier (e.g., 'feature:auth')

        Returns:
            Graph data dict with ops section initialized
        """
        data = self.graph.load()

        if 'meta' not in data:
            data['meta'] = {}
        if 'ops' not in data['meta']:
            data['meta']['ops'] = {}
        if feature_id not in data['meta']['ops']:
            data['meta']['ops'][feature_id] = {}

        return data

    def start(self, feature_id: str, op_num: int) -> bool:
        """Mark an op as in-progress with start date.

        Args:
            feature_id: Feature identifier (e.g., 'feature:auth')
            op_num: Operation number (1-indexed)

        Returns:
            True if started successfully
        """
        data = self._ensure_ops_section(feature_id)
        op_key = str(op_num)

        if op_key in data['meta']['ops'][feature_id]:
            existing = data['meta']['ops'][feature_id][op_key]
            if existing.get('status') == 'complete':
                return False

        data['meta']['ops'][feature_id][op_key] = {
            'status': 'in-progress',
            'started': date.today().isoformat()
        }

        self.graph.save(data)
        return True

    def done(self, feature_id: str, op_num: int, commits: List[str]) -> bool:
        """Mark an op as complete with commits.

        Args:
            feature_id: Feature identifier (e.g., 'feature:auth')
            op_num: Operation number (1-indexed)
            commits: List of commit hashes

        Returns:
            True if marked complete successfully
        """
        data = self._ensure_ops_section(feature_id)
        op_key = str(op_num)

        op_data = data['meta']['ops'][feature_id].get(op_key, {})
        started = op_data.get('started', date.today().isoformat())

        data['meta']['ops'][feature_id][op_key] = {
            'status': 'complete',
            'started': started,
            'completed': date.today().isoformat(),
            'commits': commits
        }

        self.graph.save(data)
        return True

    def status(self, feature_id: str) -> Dict[str, Any]:
        """Get all ops status for a feature.

        Args:
            feature_id: Feature identifier (e.g., 'feature:auth')

        Returns:
            Dict with op numbers as keys and status data as values
        """
        data = self._ensure_ops_section(feature_id)
        return data['meta']['ops'].get(feature_id, {})

    def next(self, feature_id: str) -> int:
        """Return the next op number (highest complete + 1).

        Args:
            feature_id: Feature identifier (e.g., 'feature:auth')

        Returns:
            Next op number to execute (1 if no ops completed)
        """
        ops = self.status(feature_id)

        if not ops:
            return 1

        max_complete = 0
        for op_key, op_data in ops.items():
            if op_data.get('status') == 'complete':
                op_num = int(op_key)
                if op_num > max_complete:
                    max_complete = op_num

        return max_complete + 1

    def get_op(self, feature_id: str, op_num: int) -> Optional[Dict[str, Any]]:
        """Get status data for a specific op.

        Args:
            feature_id: Feature identifier
            op_num: Operation number

        Returns:
            Op status dict or None if not found
        """
        ops = self.status(feature_id)
        return ops.get(str(op_num))

    def reset(self, feature_id: str, op_num: int) -> bool:
        """Reset an op to pending state (remove from tracking).

        Args:
            feature_id: Feature identifier
            op_num: Operation number

        Returns:
            True if reset, False if op not found
        """
        data = self._ensure_ops_section(feature_id)
        op_key = str(op_num)

        if op_key not in data['meta']['ops'].get(feature_id, {}):
            return False

        del data['meta']['ops'][feature_id][op_key]
        self.graph.save(data)
        return True

    def get_in_progress(self, feature_id: str) -> List[int]:
        """Get list of in-progress op numbers for a feature.

        Args:
            feature_id: Feature identifier

        Returns:
            List of op numbers currently in-progress
        """
        ops = self.status(feature_id)
        return [
            int(op_key)
            for op_key, op_data in ops.items()
            if op_data.get('status') == 'in-progress'
        ]

    def get_completed(self, feature_id: str) -> List[int]:
        """Get list of completed op numbers for a feature.

        Args:
            feature_id: Feature identifier

        Returns:
            List of completed op numbers, sorted ascending
        """
        ops = self.status(feature_id)
        return sorted([
            int(op_key)
            for op_key, op_data in ops.items()
            if op_data.get('status') == 'complete'
        ])

    def summary(self, feature_id: str) -> Dict[str, Any]:
        """Get summary statistics for feature ops.

        Args:
            feature_id: Feature identifier

        Returns:
            Dict with total, complete, in_progress counts and next op
        """
        ops = self.status(feature_id)

        complete = sum(1 for o in ops.values() if o.get('status') == 'complete')
        in_progress = sum(1 for o in ops.values() if o.get('status') == 'in-progress')

        return {
            'total_tracked': len(ops),
            'complete': complete,
            'in_progress': in_progress,
            'next_op': self.next(feature_id),
            'all_commits': self._collect_commits(ops)
        }

    def _collect_commits(self, ops: Dict[str, Any]) -> List[str]:
        """Collect all commits from completed ops.

        Args:
            ops: Ops status dict

        Returns:
            List of all commit hashes
        """
        commits = []
        for op_data in ops.values():
            if op_data.get('status') == 'complete':
                commits.extend(op_data.get('commits', []))
        return commits
