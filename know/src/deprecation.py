"""
deprecation.py - Soft deprecation system for graph entities
Manages deprecated entities with warnings and migration paths
"""

from datetime import date, datetime
from typing import Optional


class DeprecationManager:
    """Manage soft-deprecated entities in the spec graph."""

    def __init__(self, graph_manager):
        """Initialize with a GraphManager instance.

        Args:
            graph_manager: GraphManager instance for graph operations
        """
        self.graph = graph_manager

    def _ensure_deprecated_section(self):
        """Ensure meta.deprecated section exists."""
        data = self.graph.load()
        if 'meta' not in data:
            data['meta'] = {}
        if 'deprecated' not in data['meta']:
            data['meta']['deprecated'] = {}
        return data

    def deprecate(
        self,
        entity_id: str,
        reason: str,
        replacement: Optional[str] = None,
        removal_target: Optional[str] = None
    ) -> bool:
        """Mark an entity as deprecated.

        Args:
            entity_id: Full entity ID (e.g., 'component:old-auth')
            reason: Why the entity is deprecated
            replacement: Entity ID of replacement (optional)
            removal_target: ISO date when entity will be removed (optional)

        Returns:
            True if deprecation was added, False if entity doesn't exist
        """
        data = self._ensure_deprecated_section()

        entity_type, entity_key = entity_id.split(':', 1)
        if entity_type not in data.get('entities', {}):
            return False
        if entity_key not in data['entities'][entity_type]:
            return False

        deprecation_info = {
            'reason': reason,
            'deprecated_date': date.today().isoformat()
        }

        if replacement:
            deprecation_info['replacement'] = replacement
        if removal_target:
            deprecation_info['removal_target'] = removal_target

        data['meta']['deprecated'][entity_id] = deprecation_info
        self.graph.save(data)
        return True

    def undeprecate(self, entity_id: str) -> bool:
        """Remove deprecation status from an entity.

        Args:
            entity_id: Full entity ID

        Returns:
            True if deprecation was removed, False if entity wasn't deprecated
        """
        data = self.graph.load()
        deprecated = data.get('meta', {}).get('deprecated', {})

        if entity_id not in deprecated:
            return False

        del data['meta']['deprecated'][entity_id]
        self.graph.save(data)
        return True

    def is_deprecated(self, entity_id: str) -> bool:
        """Check if an entity is deprecated.

        Args:
            entity_id: Full entity ID

        Returns:
            True if entity is deprecated
        """
        data = self.graph.load()
        return entity_id in data.get('meta', {}).get('deprecated', {})

    def get_deprecation_info(self, entity_id: str) -> Optional[dict]:
        """Get deprecation details for an entity.

        Args:
            entity_id: Full entity ID

        Returns:
            Deprecation info dict or None if not deprecated
        """
        data = self.graph.load()
        return data.get('meta', {}).get('deprecated', {}).get(entity_id)

    def list_deprecated(self) -> list:
        """List all deprecated entities with their info.

        Returns:
            List of (entity_id, info) tuples
        """
        data = self.graph.load()
        deprecated = data.get('meta', {}).get('deprecated', {})
        return [(entity_id, info) for entity_id, info in deprecated.items()]

    def check_deprecated_usage(self, entity_id: str) -> list:
        """Check if any entities depend on deprecated entities.

        Args:
            entity_id: Entity to check dependencies for

        Returns:
            List of warning strings for deprecated dependencies
        """
        data = self.graph.load()
        deprecated = data.get('meta', {}).get('deprecated', {})
        graph = data.get('graph', {})
        warnings = []

        if entity_id not in graph:
            return warnings

        deps = graph[entity_id].get('depends_on', [])
        for dep in deps:
            if dep in deprecated:
                info = deprecated[dep]
                warning = f"Depends on deprecated entity '{dep}': {info['reason']}"
                if info.get('replacement'):
                    warning += f" (replacement: {info['replacement']})"
                warnings.append(warning)

        return warnings

    def get_deprecated_dependents(self, entity_id: str) -> list:
        """Find entities that depend on a deprecated entity.

        Args:
            entity_id: The deprecated entity ID

        Returns:
            List of entity IDs that depend on this deprecated entity
        """
        data = self.graph.load()
        graph = data.get('graph', {})
        dependents = []

        for source_id, edge_data in graph.items():
            if entity_id in edge_data.get('depends_on', []):
                dependents.append(source_id)

        return dependents

    def is_removal_due(self, entity_id: str) -> bool:
        """Check if a deprecated entity's removal target date has passed.

        Args:
            entity_id: The entity ID to check

        Returns:
            True if removal_target is set and has passed
        """
        info = self.get_deprecation_info(entity_id)
        if not info or not info.get('removal_target'):
            return False

        try:
            removal_date = datetime.fromisoformat(info['removal_target']).date()
            return date.today() >= removal_date
        except ValueError:
            return False

    def get_overdue_removals(self) -> list:
        """Get all deprecated entities past their removal target date.

        Returns:
            List of (entity_id, info) for overdue removals
        """
        overdue = []
        for entity_id, info in self.list_deprecated():
            if self.is_removal_due(entity_id):
                overdue.append((entity_id, info))
        return overdue
