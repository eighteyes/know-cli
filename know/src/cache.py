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
        self._write_lock_file = Path(".spec-graph.lock")

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
        """Write graph data atomically with simple lock file coordination"""
        import tempfile
        import time

        # Wait for any existing write to complete
        if wait_for_lock:
            wait_count = 0
            while self._write_lock_file.exists():
                time.sleep(0.1)
                wait_count += 1
                if wait_count > 50:  # 5 second timeout
                    # Check if lock is stale (older than 5 seconds)
                    try:
                        lock_age = time.time() - self._write_lock_file.stat().st_mtime
                        if lock_age > 5:
                            self._write_lock_file.unlink()  # Remove stale lock
                            break
                    except:
                        break
                    return False

        # Create lock file
        try:
            self._write_lock_file.touch(exist_ok=False)
        except FileExistsError:
            if not wait_for_lock:
                return False

        try:
            # Ensure parent directory exists
            self.graph_path.parent.mkdir(parents=True, exist_ok=True)

            # Write atomically using temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.graph_path.parent,
                delete=False,
                suffix='.tmp'
            ) as tmp:
                json.dump(data, tmp, indent=2)
                temp_path = tmp.name

            # Atomic rename
            os.replace(temp_path, self.graph_path)

            # Invalidate cache after successful write
            self.invalidate()
            return True

        finally:
            # Always remove lock file
            try:
                self._write_lock_file.unlink()
            except:
                pass

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