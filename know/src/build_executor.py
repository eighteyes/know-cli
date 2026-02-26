"""
Build executor for XML spec files.

Parses XML task specifications and executes them until hitting a checkpoint.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime


class BuildExecutor:
    """Execute tasks from XML spec."""

    def __init__(self, xml_path: str, progress_file: str = '.ai/know/build-progress.json'):
        """
        Initialize build executor.

        Args:
            xml_path: Path to XML spec file
            progress_file: Path to progress tracking file
        """
        self.xml_path = xml_path
        self.progress_file = progress_file
        self.spec = self._parse_xml()
        self.progress = self._load_progress()

    def _parse_xml(self) -> Dict[str, Any]:
        """Parse XML spec into structured data."""
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        spec = {
            "meta": self._parse_meta(root.find('meta')),
            "context": self._parse_context(root.find('context')),
            "dependencies": self._parse_dependencies(root.find('dependencies')),
            "tasks": self._parse_tasks(root.find('tasks'))
        }

        return spec

    def _parse_meta(self, meta_el: Optional[ET.Element]) -> Dict[str, str]:
        """Parse meta section."""
        if meta_el is None:
            return {}

        meta = {}
        for child in meta_el:
            meta[child.tag] = child.text or ''

        return meta

    def _parse_context(self, context_el: Optional[ET.Element]) -> Dict[str, Any]:
        """Parse context section."""
        if context_el is None:
            return {}

        context = {}

        # Parse users
        users_el = context_el.find('users')
        if users_el is not None:
            context['users'] = []
            for user in users_el.findall('user'):
                context['users'].append({
                    'id': user.get('id', ''),
                    'name': user.text or ''
                })

        # Parse objectives
        objectives_el = context_el.find('objectives')
        if objectives_el is not None:
            context['objectives'] = []
            for obj in objectives_el.findall('objective'):
                context['objectives'].append({
                    'id': obj.get('id', ''),
                    'text': obj.text or ''
                })

        # Parse actions
        actions_el = context_el.find('actions')
        if actions_el is not None:
            context['actions'] = []
            for action in actions_el.findall('action'):
                action_data = {'id': action.get('id', '')}
                name_el = action.find('name')
                desc_el = action.find('description')
                if name_el is not None:
                    action_data['name'] = name_el.text or ''
                if desc_el is not None:
                    action_data['description'] = desc_el.text or ''
                context['actions'].append(action_data)

        # Parse components
        components_el = context_el.find('components')
        if components_el is not None:
            context['components'] = []
            for comp in components_el.findall('component'):
                comp_data = {'id': comp.get('id', '')}
                name_el = comp.find('name')
                desc_el = comp.find('description')
                if name_el is not None:
                    comp_data['name'] = name_el.text or ''
                if desc_el is not None:
                    comp_data['description'] = desc_el.text or ''
                context['components'].append(comp_data)

        return context

    def _parse_dependencies(self, deps_el: Optional[ET.Element]) -> Dict[str, Any]:
        """Parse dependencies section."""
        if deps_el is None:
            return {}

        deps = {}

        # Parse external packages
        external_el = deps_el.find('external')
        if external_el is not None:
            deps['external'] = []
            for pkg in external_el.findall('package'):
                deps['external'].append({
                    'name': pkg.text or '',
                    'purpose': pkg.get('purpose', '')
                })

        return deps

    def _parse_tasks(self, tasks_el: Optional[ET.Element]) -> List[Dict[str, Any]]:
        """Parse tasks section."""
        if tasks_el is None:
            return []

        tasks = []
        for task_el in tasks_el.findall('task'):
            task = {
                'id': task_el.get('id', ''),
                'type': task_el.get('type', 'auto'),
                'wave': task_el.get('wave', '0')
            }

            # Parse task elements
            for child in task_el:
                if child.tag == 'operation':
                    task['operation'] = child.text or ''
                elif child.tag == 'name':
                    task['name'] = child.text or ''
                elif child.tag == 'files':
                    task['files'] = []
                    for file_el in child.findall('file'):
                        task['files'].append(file_el.text or '')
                elif child.tag == 'action':
                    task['action'] = child.text or ''
                elif child.tag == 'verify':
                    task['verify'] = {}
                    test_el = child.find('test')
                    assertion_el = child.find('assertion')
                    if test_el is not None:
                        task['verify']['test'] = test_el.text or ''
                    if assertion_el is not None:
                        task['verify']['assertion'] = assertion_el.text or ''
                elif child.tag == 'done':
                    task['done'] = child.text or ''

            tasks.append(task)

        return tasks

    def _load_progress(self) -> Dict[str, Any]:
        """Load progress from file."""
        if not Path(self.progress_file).exists():
            return {
                'spec_file': self.xml_path,
                'feature': self.spec.get('meta', {}).get('feature', ''),
                'started_at': datetime.utcnow().isoformat(),
                'tasks': {}
            }

        with open(self.progress_file) as f:
            return json.load(f)

    def _save_progress(self):
        """Save progress to file."""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get next pending task."""
        for task in self.spec['tasks']:
            task_id = task['id']
            if task_id not in self.progress['tasks'] or \
               self.progress['tasks'][task_id].get('status') != 'completed':
                return task
        return None

    def mark_task_completed(self, task_id: str):
        """Mark task as completed."""
        self.progress['tasks'][task_id] = {
            'status': 'completed',
            'completed_at': datetime.utcnow().isoformat()
        }
        self._save_progress()

    def mark_task_in_progress(self, task_id: str):
        """Mark task as in progress."""
        self.progress['tasks'][task_id] = {
            'status': 'in_progress',
            'started_at': datetime.utcnow().isoformat()
        }
        self._save_progress()

    def get_summary(self) -> str:
        """Get execution summary."""
        total = len(self.spec['tasks'])
        completed = sum(1 for t in self.progress['tasks'].values()
                       if t.get('status') == 'completed')

        lines = []
        lines.append(f"Feature: {self.spec['meta'].get('name', 'Unknown')}")
        lines.append(f"Progress: {completed}/{total} tasks completed")

        if completed < total:
            next_task = self.get_next_task()
            if next_task:
                lines.append(f"Next: {next_task['name']}")

        return '\n'.join(lines)
