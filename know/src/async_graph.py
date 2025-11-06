"""
Async wrapper for graph operations to support web server integration.
Provides non-blocking access to graph data with caching.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import wraps

from .graph import GraphManager
from .entities import EntityManager
from .dependencies import DependencyManager
from .validation import GraphValidator
from .generators import SpecGenerator
from .cache import GraphCache


def async_cached(func):
    """Decorator to add async caching to methods."""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Create cache key from function name and args
        cache_key = f"{func.__name__}:{args}:{kwargs}"

        # Check cache
        if hasattr(self, '_async_cache') and cache_key in self._async_cache:
            return self._async_cache[cache_key]

        # Execute function
        result = await func(self, *args, **kwargs)

        # Store in cache
        if hasattr(self, '_async_cache'):
            self._async_cache[cache_key] = result

        return result

    return wrapper


class AsyncGraphManager:
    """Async wrapper for GraphManager operations."""

    def __init__(self, graph_path: str):
        """
        Initialize async graph manager.

        Args:
            graph_path: Path to graph file
        """
        self.graph_path = graph_path
        self._graph = GraphManager(graph_path)
        self._entities = EntityManager(self._graph)
        self._deps = DependencyManager(self._graph)
        self._validator = GraphValidator(self._graph)
        self._generator = SpecGenerator(self._graph, self._entities, self._deps)
        self._async_cache: Dict[str, Any] = {}

    async def load_graph(self) -> Dict:
        """Load graph data asynchronously."""
        return await asyncio.to_thread(self._graph.load)

    async def save_graph(self, data: Dict) -> None:
        """Save graph data asynchronously."""
        await asyncio.to_thread(self._graph.save, data)

    @async_cached
    async def get_entity(self, entity_id: str) -> Optional[Dict]:
        """Get entity data asynchronously."""
        return await asyncio.to_thread(self._entities.get_entity, entity_id)

    @async_cached
    async def list_entities(self, entity_type: Optional[str] = None) -> List[str]:
        """List entities asynchronously."""
        return await asyncio.to_thread(self._entities.list_entities, entity_type)

    async def add_entity(
        self,
        entity_type: str,
        entity_key: str,
        entity_data: Dict
    ) -> bool:
        """Add entity asynchronously."""
        result = await asyncio.to_thread(
            self._entities.add_entity,
            entity_type,
            entity_key,
            entity_data
        )
        # Invalidate cache
        self._async_cache.clear()
        return result

    async def update_entity(
        self,
        entity_id: str,
        updates: Dict
    ) -> bool:
        """Update entity asynchronously."""
        result = await asyncio.to_thread(
            self._entities.update_entity,
            entity_id,
            updates
        )
        # Invalidate cache
        self._async_cache.clear()
        return result

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete entity asynchronously."""
        result = await asyncio.to_thread(
            self._entities.delete_entity,
            entity_id
        )
        # Invalidate cache
        self._async_cache.clear()
        return result

    @async_cached
    async def get_dependencies(self, entity_id: str) -> List[str]:
        """Get dependencies asynchronously."""
        return await asyncio.to_thread(self._deps.get_dependencies, entity_id)

    @async_cached
    async def get_dependents(self, entity_id: str) -> List[str]:
        """Get dependents asynchronously."""
        return await asyncio.to_thread(self._deps.get_dependents, entity_id)

    async def add_dependency(
        self,
        from_id: str,
        to_id: str,
        validate: bool = True
    ) -> tuple[bool, Optional[str]]:
        """Add dependency asynchronously."""
        result = await asyncio.to_thread(
            self._deps.add_dependency,
            from_id,
            to_id,
            validate
        )
        # Invalidate cache
        self._async_cache.clear()
        return result

    async def remove_dependency(self, from_id: str, to_id: str) -> bool:
        """Remove dependency asynchronously."""
        result = await asyncio.to_thread(
            self._deps.remove_dependency,
            from_id,
            to_id
        )
        # Invalidate cache
        self._async_cache.clear()
        return result

    @async_cached
    async def validate_graph(self) -> tuple[bool, Dict[str, List[str]]]:
        """Validate graph asynchronously."""
        return await asyncio.to_thread(self._validator.validate_all)

    @async_cached
    async def detect_cycles(self) -> List[List[str]]:
        """Detect cycles asynchronously."""
        return await asyncio.to_thread(self._deps.detect_cycles)

    @async_cached
    async def topological_sort(self) -> List[str]:
        """Get topological sort asynchronously."""
        return await asyncio.to_thread(self._deps.topological_sort)

    @async_cached
    async def suggest_connections(
        self,
        entity_id: str,
        max_suggestions: int = 5
    ) -> Dict[str, List[str]]:
        """Suggest connections asynchronously."""
        return await asyncio.to_thread(
            self._deps.suggest_connections,
            entity_id,
            max_suggestions
        )

    @async_cached
    async def generate_spec(self, entity_id: str) -> str:
        """Generate entity spec asynchronously."""
        return await asyncio.to_thread(
            self._generator.generate_entity_spec,
            entity_id
        )

    @async_cached
    async def generate_feature_spec(self, feature_id: str) -> str:
        """Generate feature spec asynchronously."""
        return await asyncio.to_thread(
            self._generator.generate_feature_spec,
            feature_id
        )

    @async_cached
    async def generate_sitemap(self) -> str:
        """Generate sitemap asynchronously."""
        return await asyncio.to_thread(self._generator.generate_sitemap)

    @async_cached
    async def get_completeness_score(self, entity_id: str) -> Dict:
        """Get completeness score asynchronously."""
        return await asyncio.to_thread(
            self._validator.get_completeness_score,
            entity_id
        )

    @async_cached
    async def get_stats(self) -> Dict:
        """Get graph statistics asynchronously."""
        from .utils import get_graph_stats
        data = await self.load_graph()
        return await asyncio.to_thread(get_graph_stats, data)

    def invalidate_cache(self):
        """Clear async cache."""
        self._async_cache.clear()
        if hasattr(self._graph, 'cache'):
            self._graph.cache.invalidate()

    async def batch_get_entities(self, entity_ids: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Get multiple entities in parallel.

        Args:
            entity_ids: List of entity IDs

        Returns:
            Dictionary mapping entity IDs to their data
        """
        tasks = [self.get_entity(entity_id) for entity_id in entity_ids]
        results = await asyncio.gather(*tasks)
        return dict(zip(entity_ids, results))

    async def batch_validate_dependencies(
        self,
        connections: List[tuple[str, str]]
    ) -> List[tuple[bool, Optional[str]]]:
        """
        Validate multiple dependencies in parallel.

        Args:
            connections: List of (from_id, to_id) tuples

        Returns:
            List of validation results
        """
        async def validate_one(from_id: str, to_id: str):
            from_type = from_id.split(':')[0] if ':' in from_id else from_id
            to_type = to_id.split(':')[0] if ':' in to_id else to_id

            is_valid = await asyncio.to_thread(
                self._deps.is_valid_dependency,
                from_type,
                to_type
            )

            if is_valid:
                return True, None
            else:
                allowed = await asyncio.to_thread(
                    self._deps.get_allowed_targets,
                    from_type
                )
                return False, f"{from_type} can only depend on: {', '.join(allowed)}"

        tasks = [validate_one(from_id, to_id) for from_id, to_id in connections]
        return await asyncio.gather(*tasks)

    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search entities by query string.

        Args:
            query: Search query
            entity_type: Optional entity type filter
            limit: Maximum results

        Returns:
            List of matching entities with metadata
        """
        from .utils import find_fuzzy_match

        # Get all entities
        entities = await self.list_entities(entity_type)

        # Fuzzy match on entity names
        matches = await asyncio.to_thread(
            find_fuzzy_match,
            query,
            entities,
            threshold=3
        )

        # Get entity data for matches
        results = []
        for entity_id in matches[:limit]:
            entity_data = await self.get_entity(entity_id)
            if entity_data:
                results.append({
                    'id': entity_id,
                    'name': entity_data.get('name', entity_id),
                    'description': entity_data.get('description', ''),
                    'type': entity_id.split(':')[0] if ':' in entity_id else 'unknown'
                })

        return results


class AsyncGraphPool:
    """Pool of async graph managers for handling multiple graph files."""

    def __init__(self):
        """Initialize graph pool."""
        self._graphs: Dict[str, AsyncGraphManager] = {}

    async def get_graph(self, graph_path: str) -> AsyncGraphManager:
        """
        Get or create graph manager for path.

        Args:
            graph_path: Path to graph file

        Returns:
            AsyncGraphManager instance
        """
        # Normalize path
        normalized = str(Path(graph_path).resolve())

        if normalized not in self._graphs:
            self._graphs[normalized] = AsyncGraphManager(normalized)

        return self._graphs[normalized]

    async def close_all(self):
        """Close all graph managers."""
        for graph in self._graphs.values():
            graph.invalidate_cache()
        self._graphs.clear()

    def invalidate_all(self):
        """Invalidate all caches."""
        for graph in self._graphs.values():
            graph.invalidate_cache()


# Global pool instance
_global_pool = AsyncGraphPool()


async def get_graph(graph_path: str = '.ai/spec-graph.json') -> AsyncGraphManager:
    """
    Get async graph manager from global pool.

    Args:
        graph_path: Path to graph file

    Returns:
        AsyncGraphManager instance
    """
    return await _global_pool.get_graph(graph_path)
