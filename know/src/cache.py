"""
In-memory caching layer for graph operations
"""

import os
import json
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class GraphCache:
    """Thread-safe in-memory cache for graph data"""

    def __init__(self, graph_path: str = ".ai/know/spec-graph.json"):
        self.graph_path = Path(graph_path)
        self._cache: Optional[Dict[str, Any]] = None
        self._last_mtime: Optional[float] = None
        self._lock = threading.RLock()
        # Lock file lives next to the graph file, named per graph
        self._write_lock_file = self.graph_path.parent / f".{self.graph_path.stem}.lock"

    def get(self) -> Dict[str, Any]:
        """Get cached graph, reloading if file changed"""
        with self._lock:
            current_mtime = self._get_mtime()

            if self._cache is None or current_mtime != self._last_mtime:
                self._load()
                self._last_mtime = current_mtime

            return self._cache

    def invalidate(self):
        """Force cache reload on next access"""
        with self._lock:
            self._cache = None
            self._last_mtime = None

    def write(self, data: Dict[str, Any], wait_for_lock: bool = True) -> bool:
        """Write graph data atomically using fcntl.flock for process-safe locking."""
        import fcntl
        import tempfile

        # Ensure parent directory exists (needed before opening lock file)
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)

        lock_flag = fcntl.LOCK_EX if wait_for_lock else fcntl.LOCK_EX | fcntl.LOCK_NB

        try:
            lock_fd = open(self._write_lock_file, 'w')
        except OSError:
            return False

        try:
            # Block until exclusive lock acquired (or fail immediately if non-blocking)
            fcntl.flock(lock_fd, lock_flag)
        except BlockingIOError:
            lock_fd.close()
            return False

        try:
            # Write atomically using temp file + rename
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.graph_path.parent,
                delete=False,
                suffix='.tmp'
            ) as tmp:
                json.dump(data, tmp, indent=2)
                temp_path = tmp.name

            os.replace(temp_path, self.graph_path)
            self.invalidate()
            return True

        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    def _get_mtime(self) -> Optional[float]:
        """Get file modification time"""
        try:
            return self.graph_path.stat().st_mtime if self.graph_path.exists() else None
        except:
            return None

    def _load(self):
        """Load graph from file"""
        if not self.graph_path.exists():
            self._cache = self._get_default_graph()
        else:
            try:
                with open(self.graph_path, 'r') as f:
                    self._cache = json.load(f)
            except json.JSONDecodeError:
                self._cache = self._get_default_graph()

    def _get_default_graph(self) -> Dict[str, Any]:
        """Return default graph structure"""
        return {
            "meta": {
                "version": "1.0.0",
                "phases": {}
            },
            "references": {},
            "entities": {},
            "graph": {}
        }