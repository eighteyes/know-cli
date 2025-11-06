"""
Reference management tools for knowledge graph
Validates, cleans, and connects reference nodes
"""

from typing import Dict, List, Set, Optional, Tuple
import json


class ReferenceManager:
    """Manages reference nodes in the graph"""

    def __init__(self, graph_manager, entity_manager, dependency_manager):
        """
        Initialize reference manager.

        Args:
            graph_manager: GraphManager instance
            entity_manager: EntityManager instance
            dependency_manager: DependencyManager instance
        """
        self.graph = graph_manager
        self.entities = entity_manager
        self.deps = dependency_manager

    def check_reference_parents(self) -> Dict[str, List[str]]:
        """
        Check that every reference has at least one parent entity.

        Returns:
            Dictionary with orphaned references by category
        """
        data = self.graph.load()
        references = data.get('references', {})
        graph = data.get('graph', {})

        # Collect all dependencies
        all_dependencies = set()
        for entity_id, entity_graph in graph.items():
            for dep in entity_graph.get('depends_on', []):
                all_dependencies.add(dep)

        orphaned = {}

        # Check each reference category
        for ref_category, ref_items in references.items():
            if not isinstance(ref_items, dict):
                continue

            category_orphans = []
            for ref_key in ref_items.keys():
                ref_id = f"{ref_category}:{ref_key}"

                # Check if any entity depends on this reference
                if ref_id not in all_dependencies:
                    category_orphans.append(ref_key)

            if category_orphans:
                orphaned[ref_category] = category_orphans

        return orphaned

    def get_reference_usage(self) -> Dict[str, Dict[str, int]]:
        """
        Count how many times each reference is used.

        Returns:
            Dictionary mapping reference IDs to usage count
        """
        data = self.graph.load()
        references = data.get('references', {})
        graph = data.get('graph', {})

        # Count usage
        usage_count = {}

        for ref_category, ref_items in references.items():
            if not isinstance(ref_items, dict):
                continue

            usage_count[ref_category] = {}

            for ref_key in ref_items.keys():
                ref_id = f"{ref_category}:{ref_key}"
                count = 0

                # Count in all dependencies
                for entity_id, entity_graph in graph.items():
                    if ref_id in entity_graph.get('depends_on', []):
                        count += 1

                usage_count[ref_category][ref_key] = count

        return usage_count

    def find_unused_references(self) -> Dict[str, List[str]]:
        """
        Find all references that are not used by any entity.

        Returns:
            Dictionary mapping categories to lists of unused reference keys
        """
        usage = self.get_reference_usage()
        unused = {}

        for category, refs in usage.items():
            category_unused = [key for key, count in refs.items() if count == 0]
            if category_unused:
                unused[category] = category_unused

        return unused

    def flatten_nested_references(self, dry_run: bool = True) -> Dict[str, any]:
        """
        Flatten nested reference structures to root level.

        Args:
            dry_run: If True, don't modify the graph

        Returns:
            Dictionary with flattening results
        """
        data = self.graph.load()
        references = data.get('references', {})

        flattened_count = 0
        flattened_refs = []

        new_references = {}

        for ref_category, ref_items in references.items():
            if not isinstance(ref_items, dict):
                new_references[ref_category] = ref_items
                continue

            new_category = {}

            for ref_key, ref_value in ref_items.items():
                # Check if value is nested object
                if isinstance(ref_value, dict):
                    # Flatten nested object
                    for nested_key, nested_value in ref_value.items():
                        if isinstance(nested_value, (str, int, float, bool, list)):
                            # Simple value - keep at root
                            flattened_key = f"{ref_key}-{nested_key}"
                            new_category[flattened_key] = nested_value
                            flattened_count += 1
                            flattened_refs.append(f"{ref_category}:{flattened_key}")
                        else:
                            # Keep nested structure
                            new_category[ref_key] = ref_value
                            break
                else:
                    # Simple value - keep as is
                    new_category[ref_key] = ref_value

            new_references[ref_category] = new_category

        if not dry_run:
            data['references'] = new_references
            self.graph.save(data)

        return {
            'flattened_count': flattened_count,
            'flattened_refs': flattened_refs,
            'dry_run': dry_run
        }

    def clean_references(self, remove_unused: bool = False, dry_run: bool = True) -> Dict[str, any]:
        """
        Clean up references by removing unused ones and validating structure.

        Args:
            remove_unused: If True, remove unused references
            dry_run: If True, don't modify the graph

        Returns:
            Dictionary with cleaning results
        """
        data = self.graph.load()
        references = data.get('references', {})

        results = {
            'total_refs': 0,
            'orphaned_refs': 0,
            'removed_refs': [],
            'dry_run': dry_run
        }

        if remove_unused:
            unused = self.find_unused_references()
            new_references = {}

            for ref_category, ref_items in references.items():
                if not isinstance(ref_items, dict):
                    new_references[ref_category] = ref_items
                    continue

                category_unused = unused.get(ref_category, [])
                new_category = {}

                for ref_key, ref_value in ref_items.items():
                    results['total_refs'] += 1

                    if ref_key in category_unused:
                        results['orphaned_refs'] += 1
                        results['removed_refs'].append(f"{ref_category}:{ref_key}")
                    else:
                        new_category[ref_key] = ref_value

                new_references[ref_category] = new_category

            if not dry_run:
                data['references'] = new_references
                self.graph.save(data)
        else:
            # Just count
            for ref_category, ref_items in references.items():
                if isinstance(ref_items, dict):
                    results['total_refs'] += len(ref_items)

            orphaned = self.check_reference_parents()
            for category, orphan_list in orphaned.items():
                results['orphaned_refs'] += len(orphan_list)

        return results

    def suggest_reference_connections(self, max_suggestions: int = 10) -> List[Tuple[str, str, int]]:
        """
        Suggest connections between orphaned references and entities.

        Uses keyword matching to find likely connections.

        Args:
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of (reference_id, entity_id, score) tuples
        """
        orphaned = self.check_reference_parents()
        suggestions = []

        # Get all entities
        data = self.graph.load()
        entities = data.get('entities', {})

        for ref_category, orphan_list in orphaned.items():
            for orphan_key in orphan_list:
                ref_id = f"{ref_category}:{orphan_key}"

                # Extract keywords from reference key
                ref_keywords = set(orphan_key.replace('-', ' ').replace('_', ' ').lower().split())

                # Find matching entities
                for entity_type, entity_items in entities.items():
                    if not isinstance(entity_items, dict):
                        continue

                    for entity_key, entity_data in entity_items.items():
                        entity_id = f"{entity_type}:{entity_key}"

                        # Extract keywords from entity
                        entity_keywords = set(entity_key.replace('-', ' ').replace('_', ' ').lower().split())

                        # Add keywords from name and description
                        if isinstance(entity_data, dict):
                            if 'name' in entity_data:
                                entity_keywords.update(entity_data['name'].lower().split())
                            if 'description' in entity_data:
                                entity_keywords.update(entity_data['description'].lower().split())

                        # Calculate match score
                        common = ref_keywords & entity_keywords
                        if common:
                            score = len(common) * 100 // max(len(ref_keywords), len(entity_keywords))
                            if score > 30:  # Threshold
                                suggestions.append((ref_id, entity_id, score))

        # Sort by score and limit
        suggestions.sort(key=lambda x: x[2], reverse=True)
        return suggestions[:max_suggestions]
