"""
requirements.py - Requirements management for spec-graph features
Replaces todo.md-based tracking with first-class requirement entities
"""

from datetime import date
from typing import Optional


class RequirementManager:
    """Manage requirement entities and their status tracking."""

    VALID_STATUSES = ['pending', 'in-progress', 'blocked', 'complete', 'verified']

    def __init__(self, graph_manager, entity_manager=None):
        """Initialize with graph and entity managers.

        Args:
            graph_manager: GraphManager instance
            entity_manager: EntityManager instance (optional, for add operations)
        """
        self.graph = graph_manager
        self.entities = entity_manager

    def _ensure_requirements_section(self):
        """Ensure meta.requirements section exists."""
        data = self.graph.load()
        if 'meta' not in data:
            data['meta'] = {}
        if 'requirements' not in data['meta']:
            data['meta']['requirements'] = {}
        return data

    def add_requirement(
        self,
        feature_name: str,
        req_key: str,
        name: str,
        description: str
    ) -> str:
        """Add a new requirement entity linked to a feature.

        Args:
            feature_name: Feature key (without 'feature:' prefix)
            req_key: Requirement key (will be prefixed with feature name)
            name: Human-readable requirement name
            description: Testable specification description

        Returns:
            Full requirement ID (e.g., 'requirement:auth-login-validation')
        """
        data = self._ensure_requirements_section()

        full_key = f"{feature_name}-{req_key}"
        req_id = f"requirement:{full_key}"
        feature_id = f"feature:{feature_name}"

        if feature_name not in data.get('entities', {}).get('feature', {}):
            raise ValueError(f"Feature '{feature_name}' not found")

        if 'requirement' not in data['entities']:
            data['entities']['requirement'] = {}

        data['entities']['requirement'][full_key] = {
            'name': name,
            'description': description
        }

        if feature_id not in data['graph']:
            data['graph'][feature_id] = {'depends_on': []}

        if req_id not in data['graph'][feature_id]['depends_on']:
            data['graph'][feature_id]['depends_on'].append(req_id)

        data['meta']['requirements'][full_key] = {
            'status': 'pending'
        }

        self.graph.save(data)
        return req_id

    def update_status(
        self,
        req_id: str,
        status: str,
        **metadata
    ) -> bool:
        """Update requirement status with optional metadata.

        Args:
            req_id: Requirement ID (with or without 'requirement:' prefix)
            status: New status (pending|in-progress|blocked|complete|verified)
            **metadata: Additional fields (started_date, completed_date, etc.)

        Returns:
            True if updated, False if requirement not found
        """
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {self.VALID_STATUSES}")

        req_key = req_id.replace('requirement:', '')
        data = self._ensure_requirements_section()

        if req_key not in data.get('entities', {}).get('requirement', {}):
            return False

        if req_key not in data['meta']['requirements']:
            data['meta']['requirements'][req_key] = {}

        data['meta']['requirements'][req_key]['status'] = status

        if status == 'in-progress' and 'started_date' not in data['meta']['requirements'][req_key]:
            data['meta']['requirements'][req_key]['started_date'] = date.today().isoformat()

        if status == 'complete' and 'completed_date' not in data['meta']['requirements'][req_key]:
            data['meta']['requirements'][req_key]['completed_date'] = date.today().isoformat()

        if status == 'verified' and 'verified_date' not in data['meta']['requirements'][req_key]:
            data['meta']['requirements'][req_key]['verified_date'] = date.today().isoformat()

        for key, value in metadata.items():
            if key in ['started_date', 'completed_date', 'verified_date', 'blocked_by', 'effort_hours', 'notes']:
                data['meta']['requirements'][req_key][key] = value

        self.graph.save(data)
        return True

    def get_feature_requirements(self, feature_name: str) -> list:
        """Get all requirements for a feature with their status.

        Args:
            feature_name: Feature key (without prefix)

        Returns:
            List of dicts with requirement data and status
        """
        data = self.graph.load()
        feature_id = f"feature:{feature_name}"

        if feature_id not in data.get('graph', {}):
            return []

        deps = data['graph'][feature_id].get('depends_on', [])
        requirements = []

        for dep in deps:
            if dep.startswith('requirement:'):
                req_key = dep.replace('requirement:', '')
                req_data = data.get('entities', {}).get('requirement', {}).get(req_key, {})
                status_data = data.get('meta', {}).get('requirements', {}).get(req_key, {})

                requirements.append({
                    'id': dep,
                    'key': req_key,
                    'name': req_data.get('name', ''),
                    'description': req_data.get('description', ''),
                    'status': status_data.get('status', 'pending'),
                    **status_data
                })

        return requirements

    def get_requirement_status(self, req_id: str) -> Optional[dict]:
        """Get status details for a requirement.

        Args:
            req_id: Requirement ID

        Returns:
            Status dict or None if not found
        """
        req_key = req_id.replace('requirement:', '')
        data = self.graph.load()

        req_data = data.get('entities', {}).get('requirement', {}).get(req_key)
        if not req_data:
            return None

        status_data = data.get('meta', {}).get('requirements', {}).get(req_key, {})

        return {
            'id': f'requirement:{req_key}',
            'key': req_key,
            'name': req_data.get('name', ''),
            'description': req_data.get('description', ''),
            'status': status_data.get('status', 'pending'),
            **status_data
        }

    def calculate_feature_completion(self, feature_name: str) -> dict:
        """Calculate completion metrics for a feature.

        Args:
            feature_name: Feature key

        Returns:
            Dict with complete, total, and percent fields
        """
        reqs = self.get_feature_requirements(feature_name)
        total = len(reqs)
        complete = sum(1 for r in reqs if r['status'] in ('complete', 'verified'))

        return {
            'complete': complete,
            'total': total,
            'percent': round(complete / total * 100, 1) if total > 0 else 0,
            'by_status': self._count_by_status(reqs)
        }

    def _count_by_status(self, requirements: list) -> dict:
        """Count requirements by status."""
        counts = {status: 0 for status in self.VALID_STATUSES}
        for req in requirements:
            status = req.get('status', 'pending')
            if status in counts:
                counts[status] += 1
        return counts

    def link_requirement_to_impl(
        self,
        req_id: str,
        impl_id: str
    ) -> bool:
        """Link a requirement to implementation entity (component, action, etc).

        Args:
            req_id: Requirement ID
            impl_id: Implementation entity ID (component:x, action:y, etc)

        Returns:
            True if linked, False if requirement not found
        """
        req_key = req_id.replace('requirement:', '')
        data = self.graph.load()

        if req_key not in data.get('entities', {}).get('requirement', {}):
            return False

        if req_id not in data.get('graph', {}):
            data['graph'][req_id] = {'depends_on': []}

        if impl_id not in data['graph'][req_id]['depends_on']:
            data['graph'][req_id]['depends_on'].append(impl_id)

        self.graph.save(data)
        return True

    def get_blocked_requirements(self) -> list:
        """Get all blocked requirements across features.

        Returns:
            List of requirement status dicts
        """
        data = self.graph.load()
        blocked = []

        for req_key, status_data in data.get('meta', {}).get('requirements', {}).items():
            if status_data.get('status') == 'blocked':
                req_data = data.get('entities', {}).get('requirement', {}).get(req_key, {})
                blocked.append({
                    'id': f'requirement:{req_key}',
                    'key': req_key,
                    'name': req_data.get('name', ''),
                    'blocked_by': status_data.get('blocked_by', 'Unknown'),
                    **status_data
                })

        return blocked

    def get_all_requirements_summary(self) -> dict:
        """Get summary of all requirements in the graph.

        Returns:
            Dict with counts by status and total
        """
        data = self.graph.load()
        requirements = data.get('meta', {}).get('requirements', {})

        counts = {status: 0 for status in self.VALID_STATUSES}
        total = 0

        for req_key, status_data in requirements.items():
            status = status_data.get('status', 'pending')
            if status in counts:
                counts[status] += 1
            total += 1

        return {
            'total': total,
            'by_status': counts,
            'complete_percent': round(
                (counts['complete'] + counts['verified']) / total * 100, 1
            ) if total > 0 else 0
        }
