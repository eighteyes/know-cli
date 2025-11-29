"""Graph diff utilities for comparing two graph files."""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any


class GraphDiff:
    """Compare two graph files and generate structured diffs."""

    def __init__(self, graph1_path: str, graph2_path: str):
        """Initialize with paths to two graph files.

        Args:
            graph1_path: Path to first graph (old/base)
            graph2_path: Path to second graph (new/compare)
        """
        with open(graph1_path, 'r') as f:
            self.graph1 = json.load(f)

        with open(graph2_path, 'r') as f:
            self.graph2 = json.load(f)

        self.graph1_path = Path(graph1_path).name
        self.graph2_path = Path(graph2_path).name

    def compute_diff(self) -> Dict[str, Any]:
        """Compute structured diff between the two graphs.

        Returns:
            Dict with keys:
            - meta: Changes in meta section
            - entities: Added/removed/modified entities
            - graph: Added/removed/modified dependencies
            - references: Added/removed/modified references
            - summary: High-level counts
        """
        diff = {
            'meta': self._diff_meta(),
            'entities': self._diff_entities(),
            'graph': self._diff_graph(),
            'references': self._diff_references(),
        }

        # Compute summary
        diff['summary'] = {
            'entities_added': len(diff['entities']['added']),
            'entities_removed': len(diff['entities']['removed']),
            'entities_modified': len(diff['entities']['modified']),
            'dependencies_added': len(diff['graph']['added']),
            'dependencies_removed': len(diff['graph']['removed']),
            'dependencies_modified': len(diff['graph']['modified']),
            'references_added': len(diff['references']['added']),
            'references_removed': len(diff['references']['removed']),
            'meta_changed': len(diff['meta']['changed']) > 0,
        }

        return diff

    def _diff_meta(self) -> Dict[str, Any]:
        """Compute differences in meta section."""
        meta1 = self.graph1.get('meta', {})
        meta2 = self.graph2.get('meta', {})

        changed = {}
        for key in set(meta1.keys()) | set(meta2.keys()):
            val1 = meta1.get(key)
            val2 = meta2.get(key)

            if val1 != val2:
                changed[key] = {
                    'old': val1,
                    'new': val2
                }

        return {'changed': changed}

    def _diff_entities(self) -> Dict[str, Any]:
        """Compute differences in entities section."""
        entities1 = self._flatten_entities(self.graph1.get('entities', {}))
        entities2 = self._flatten_entities(self.graph2.get('entities', {}))

        keys1 = set(entities1.keys())
        keys2 = set(entities2.keys())

        added = []
        removed = []
        modified = []

        # Added entities
        for key in sorted(keys2 - keys1):
            entity_type, name = key.split(':', 1)
            added.append({
                'key': key,
                'type': entity_type,
                'name': name,
                'data': entities2[key]
            })

        # Removed entities
        for key in sorted(keys1 - keys2):
            entity_type, name = key.split(':', 1)
            removed.append({
                'key': key,
                'type': entity_type,
                'name': name,
                'data': entities1[key]
            })

        # Modified entities
        for key in sorted(keys1 & keys2):
            if entities1[key] != entities2[key]:
                entity_type, name = key.split(':', 1)
                modified.append({
                    'key': key,
                    'type': entity_type,
                    'name': name,
                    'old': entities1[key],
                    'new': entities2[key]
                })

        return {
            'added': added,
            'removed': removed,
            'modified': modified
        }

    def _diff_graph(self) -> Dict[str, Any]:
        """Compute differences in graph section (dependencies)."""
        graph1 = self.graph1.get('graph', {})
        graph2 = self.graph2.get('graph', {})

        keys1 = set(graph1.keys())
        keys2 = set(graph2.keys())

        added = []
        removed = []
        modified = []

        # Added dependencies
        for key in sorted(keys2 - keys1):
            added.append({
                'entity': key,
                'depends_on': graph2[key].get('depends_on', [])
            })

        # Removed dependencies
        for key in sorted(keys1 - keys2):
            removed.append({
                'entity': key,
                'depends_on': graph1[key].get('depends_on', [])
            })

        # Modified dependencies
        for key in sorted(keys1 & keys2):
            deps1 = set(graph1[key].get('depends_on', []))
            deps2 = set(graph2[key].get('depends_on', []))

            if deps1 != deps2:
                added_deps = sorted(deps2 - deps1)
                removed_deps = sorted(deps1 - deps2)

                modified.append({
                    'entity': key,
                    'added_deps': added_deps,
                    'removed_deps': removed_deps
                })

        return {
            'added': added,
            'removed': removed,
            'modified': modified
        }

    def _diff_references(self) -> Dict[str, Any]:
        """Compute differences in references section."""
        refs1 = self._flatten_references(self.graph1.get('references', {}))
        refs2 = self._flatten_references(self.graph2.get('references', {}))

        keys1 = set(refs1.keys())
        keys2 = set(refs2.keys())

        added = []
        removed = []

        # Added references
        for key in sorted(keys2 - keys1):
            ref_type, name = key.split(':', 1)
            added.append({
                'key': key,
                'type': ref_type,
                'name': name
            })

        # Removed references
        for key in sorted(keys1 - keys2):
            ref_type, name = key.split(':', 1)
            removed.append({
                'key': key,
                'type': ref_type,
                'name': name
            })

        return {
            'added': added,
            'removed': removed
        }

    def _flatten_entities(self, entities: Dict) -> Dict[str, Dict]:
        """Flatten entities dict to {entity_type:name: data}."""
        flattened = {}
        for entity_type, entity_dict in entities.items():
            for name, data in entity_dict.items():
                key = f"{entity_type}:{name}"
                flattened[key] = data
        return flattened

    def _flatten_references(self, references: Dict) -> Dict[str, Dict]:
        """Flatten references dict to {ref_type:name: data}."""
        flattened = {}
        for ref_type, ref_dict in references.items():
            for name, data in ref_dict.items():
                key = f"{ref_type}:{name}"
                flattened[key] = data
        return flattened
