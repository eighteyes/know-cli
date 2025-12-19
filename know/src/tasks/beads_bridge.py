"""
BeadsBridge: Interface to Beads task management system (Steve Yegge's bd CLI).

Responsibilities:
- Check if `bd` executable is available
- Initialize .ai/beads directory with symlink
- Execute `bd` subprocess commands
- Parse Beads JSONL output
- Create tasks linked to features

MVP Scope (Phase 1):
- Simple subprocess wrapper
- JSONL parsing
- No caching, no event listeners
"""

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BeadsBridge:
    """Interface to Beads CLI (bd command)"""

    def __init__(self, beads_path: str = ".ai/beads"):
        """
        Initialize Beads bridge.

        Args:
            beads_path: Path to Beads directory (default: .ai/beads)
        """
        self.beads_path = Path(beads_path)
        self.symlink_path = Path(".beads")
        self.issues_jsonl = self.beads_path / "issues.jsonl"

    def is_bd_available(self) -> bool:
        """
        Check if bd executable is available in PATH.

        Returns:
            True if bd is installed, False otherwise
        """
        return shutil.which('bd') is not None

    def init_beads(self, stealth: bool = False) -> tuple[bool, Optional[str]]:
        """
        Initialize Beads integration.

        Steps:
        1. Create .ai/beads/ directory
        2. Create symlink .beads → .ai/beads
        3. Run bd init [--stealth]
        4. Update .gitignore (if needed)

        Args:
            stealth: If True, run bd init --stealth (silent mode)

        Returns:
            (success, error_message)
        """
        # Check if bd is available
        if not self.is_bd_available():
            return False, (
                "bd not found. Install Beads first:\n"
                "  https://github.com/steveyegge/beads"
            )

        # Create .ai/beads directory
        try:
            self.beads_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"Failed to create {self.beads_path}: {e}"

        # Create symlink .beads → .ai/beads
        if not self.symlink_path.exists():
            try:
                self.symlink_path.symlink_to(self.beads_path)
            except OSError as e:
                return False, f"Failed to create symlink: {e}"

        # Run bd init
        init_args = ['init', '--stealth'] if stealth else ['init']
        result = self.call_bd(init_args)

        if not result['success']:
            return False, f"bd init failed: {result.get('error', 'Unknown error')}"

        # Update .gitignore
        self._update_gitignore()

        return True, None

    def call_bd(self, args: List[str]) -> Dict:
        """
        Execute bd command and return parsed output.

        Args:
            args: Command arguments (e.g., ['list', '--format', 'json'])

        Returns:
            Dict with 'success', 'output', and optional 'error' keys
        """
        try:
            result = subprocess.run(
                ['bd'] + args,
                cwd=str(self.beads_path.parent) if self.beads_path.exists() else None,
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )

            if result.returncode == 0:
                return {'success': True, 'output': result.stdout, 'stderr': result.stderr}
            else:
                return {'success': False, 'error': result.stderr or result.stdout, 'returncode': result.returncode}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'bd command timed out after 30 seconds'}
        except FileNotFoundError:
            return {'success': False, 'error': 'bd command not found'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}

    def parse_beads_jsonl(self) -> List[Dict]:
        """
        Parse .beads/issues.jsonl into Python objects.

        Returns:
            List of task dictionaries from Beads JSONL
        """
        if not self.issues_jsonl.exists():
            return []

        tasks = []
        try:
            with open(self.issues_jsonl, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue

                    try:
                        task = json.loads(line)
                        tasks.append(task)
                    except json.JSONDecodeError as e:
                        # Log error but continue parsing
                        print(f"Warning: Corrupted JSONL at line {line_num}: {e}")
                        print(f"  Line: {line[:100]}...")
                        continue

        except OSError as e:
            print(f"Error reading {self.issues_jsonl}: {e}")
            return []

        return tasks

    def create_task_for_feature(self, title: str, feature_id: str, description: str = "") -> Optional[str]:
        """
        Create a Beads task linked to a feature.

        Args:
            title: Task title
            feature_id: Feature entity ID (e.g., "feature:auth")
            description: Optional task description

        Returns:
            Task ID (e.g., "bd-a1b2") or None if failed
        """
        if not self.is_bd_available():
            print("Error: bd not available")
            return None

        # Create task via bd add command
        args = ['add', title]
        if description:
            args.extend(['--description', description])

        result = self.call_bd(args)

        if not result['success']:
            print(f"Error creating task: {result.get('error')}")
            return None

        # Parse output to extract task ID
        # bd add usually returns the task ID in stdout
        output = result.get('output', '').strip()

        # Extract ID from output (format may vary, but usually "Created bd-xxxx")
        # For now, parse the last token that starts with "bd-"
        tokens = output.split()
        for token in reversed(tokens):
            if token.startswith('bd-'):
                # Clean up any trailing punctuation
                task_id = token.rstrip('.,!?')
                return task_id

        # If we can't parse the ID, try reading the JSONL to find the latest task
        tasks = self.parse_beads_jsonl()
        if tasks:
            # Return the last task ID (most recently created)
            return tasks[-1].get('id')

        return None

    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Get a single task by ID from Beads JSONL.

        Args:
            task_id: Beads task ID (e.g., "bd-a1b2")

        Returns:
            Task dictionary or None if not found
        """
        tasks = self.parse_beads_jsonl()
        for task in tasks:
            if task.get('id') == task_id:
                return task
        return None

    def list_tasks(self, status: Optional[str] = None, ready_only: bool = False) -> List[Dict]:
        """
        List tasks from Beads with optional filters.

        Args:
            status: Filter by status (e.g., "ready", "in-progress", "blocked")
            ready_only: If True, only return ready tasks

        Returns:
            List of task dictionaries
        """
        tasks = self.parse_beads_jsonl()

        # Apply filters
        if status:
            tasks = [t for t in tasks if t.get('status') == status]

        if ready_only:
            tasks = [t for t in tasks if t.get('status') == 'ready']

        return tasks

    def _update_gitignore(self):
        """
        Add .beads/ to .gitignore if not already present.

        This is a helper method to ensure Beads data isn't committed by accident.
        """
        gitignore_path = Path('.gitignore')

        # Entries to add
        entries = ['.beads/']

        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if entries already exist
            missing_entries = [e for e in entries if e not in content]

            if missing_entries:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write('\n' + '\n'.join(missing_entries) + '\n')
        else:
            # Create .gitignore with entries
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(entries) + '\n')
