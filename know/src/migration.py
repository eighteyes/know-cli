"""
Migration tools for graph conformance and rules transitions.
GraphConformanceChecker — graph vs current rules structural check.
RulesDiffAnalyzer — compare two rule sets, analyze impact, generate migration plan.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

from .utils import parse_entity_id


class GraphConformanceChecker:
    """Check a graph's structural conformance against its rules.

    Lighter than full validation. Focuses on:
    - Entity types not defined in rules
    - Dependency paths not in allowed_dependencies
    - Graph nodes referencing missing entities
    """

    def __init__(self, rules_path: str, graph_data: Dict[str, Any]):
        self.rules_path = rules_path
        self.graph_data = graph_data

        with open(rules_path, 'r') as f:
            self.rules = json.load(f)

        self.valid_entity_types = set(self.rules.get('entity_description', {}).keys())
        self.allowed_deps = self._flatten_allowed_deps(self.rules)
        self.ref_types = set(
            self.rules.get('reference_dependency_rule', {}).get('reference_types', [])
        )

    def check(self) -> Dict[str, Any]:
        """Run all conformance checks. Returns structured results."""
        unknown_types = self._check_entity_types()
        invalid_links = self._check_dependency_paths()
        dangling = self._check_dangling_refs()

        issues = unknown_types + invalid_links + dangling
        return {
            'rules_path': str(Path(self.rules_path).name),
            'issues': issues,
            'counts': {
                'unknown_entity_types': len(unknown_types),
                'invalid_dependency_paths': len(invalid_links),
                'dangling_graph_refs': len(dangling),
                'total': len(issues),
            },
        }

    def _check_entity_types(self) -> List[Dict[str, Any]]:
        """Find entity types in graph not defined in rules."""
        issues = []
        entities = self.graph_data.get('entities', {})
        for entity_type, entries in entities.items():
            if entity_type not in self.valid_entity_types:
                for key in entries:
                    issues.append({
                        'type': 'unknown_entity_type',
                        'entity_id': f"{entity_type}:{key}",
                        'entity_type': entity_type,
                        'message': f"Entity type '{entity_type}' not in rules",
                    })
        return issues

    def _check_dependency_paths(self) -> List[Dict[str, Any]]:
        """Find graph links whose from→to type pair isn't in allowed_dependencies."""
        issues = []
        graph = self.graph_data.get('graph', {})
        for source_id, node_data in graph.items():
            source_type, _ = parse_entity_id(source_id)
            if source_type is None:
                continue
            for dep in node_data.get('depends_on', []):
                dep_type, _ = parse_entity_id(dep)
                if dep_type is None:
                    continue
                if dep_type in self.ref_types:
                    continue
                if (source_type, dep_type) not in self.allowed_deps:
                    issues.append({
                        'type': 'invalid_dependency_path',
                        'from': source_id,
                        'to': dep,
                        'path': f"{source_type} → {dep_type}",
                        'message': f"Path {source_type} → {dep_type} not in allowed_dependencies",
                    })
        return issues

    def _check_dangling_refs(self) -> List[Dict[str, Any]]:
        """Find graph nodes that depend on entities not in the entities or references sections."""
        issues = []
        graph = self.graph_data.get('graph', {})
        entities = self.graph_data.get('entities', {})
        references = self.graph_data.get('references', {})

        known_ids = set()
        for etype, entries in entities.items():
            for key in entries:
                known_ids.add(f"{etype}:{key}")
        for rtype, entries in references.items():
            for key in entries:
                known_ids.add(f"{rtype}:{key}")

        for source_id, node_data in graph.items():
            for dep in node_data.get('depends_on', []):
                if dep not in known_ids:
                    issues.append({
                        'type': 'dangling_graph_ref',
                        'from': source_id,
                        'to': dep,
                        'message': f"Dependency target '{dep}' not found in entities or references",
                    })
        return issues

    def _flatten_allowed_deps(self, rules: Dict) -> Set[Tuple[str, str]]:
        """Flatten allowed_dependencies into (from_type, to_type) tuples."""
        result = set()
        for from_type, to_types in rules.get('allowed_dependencies', {}).items():
            for to_type in to_types:
                result.add((from_type, to_type))
        return result


class RulesDiffAnalyzer:
    """Compare two dependency rule files and analyze migration impact on a graph.

    Produces a migration plan with executable know commands.
    Analysis only — does not modify the graph.
    """

    def __init__(self, current_rules_path: str, target_rules_path: str, graph_data: Dict[str, Any]):
        self.current_rules_path = current_rules_path
        self.target_rules_path = target_rules_path
        self.graph_data = graph_data

        with open(current_rules_path, 'r') as f:
            self.current_rules = json.load(f)

        with open(target_rules_path, 'r') as f:
            self.target_rules = json.load(f)

    def diff_rules(self) -> Dict[str, Any]:
        """Pure rules-to-rules comparison.

        Returns dict with entity_types, dependency_paths, and reference_types diffs.
        """
        current_entities = set(self.current_rules.get('entity_description', {}).keys())
        target_entities = set(self.target_rules.get('entity_description', {}).keys())

        current_ref_types = set(
            self.current_rules.get('reference_dependency_rule', {}).get('reference_types', [])
        )
        target_ref_types = set(
            self.target_rules.get('reference_dependency_rule', {}).get('reference_types', [])
        )

        current_deps = self._flatten_allowed_deps(self.current_rules)
        target_deps = self._flatten_allowed_deps(self.target_rules)

        removed_entities = current_entities - target_entities
        added_entities = target_entities - current_entities

        # Classify removed entities: demoted to reference or removed entirely
        entity_dispositions = {}
        for entity_type in removed_entities:
            if entity_type in target_ref_types:
                entity_dispositions[entity_type] = 'demoted_to_reference'
            else:
                entity_dispositions[entity_type] = 'removed_entirely'

        return {
            'entity_types': {
                'removed': sorted(removed_entities),
                'added': sorted(added_entities),
                'dispositions': entity_dispositions,
            },
            'dependency_paths': {
                'removed': sorted(current_deps - target_deps),
                'added': sorted(target_deps - current_deps),
            },
            'reference_types': {
                'removed': sorted(current_ref_types - target_ref_types),
                'added': sorted(target_ref_types - current_ref_types),
            },
        }

    def analyze_impact(self, diff: Dict[str, Any]) -> Dict[str, Any]:
        """Scan graph for nodes affected by the rules diff.

        Returns counts and lists of affected entities, links, references, and horizons.
        """
        entities = self.graph_data.get('entities', {})
        graph = self.graph_data.get('graph', {})
        references = self.graph_data.get('references', {})
        horizons = self.graph_data.get('meta', {}).get('horizons', {})

        affected_entities = []
        affected_links = []
        affected_references = []
        affected_horizons = []

        removed_entity_types = set(diff['entity_types']['removed'])
        removed_paths = set(tuple(p) for p in diff['dependency_paths']['removed'])
        removed_ref_types = set(diff['reference_types']['removed'])

        # Find entity instances of removed types
        for entity_type in removed_entity_types:
            if entity_type in entities:
                for key, data in entities[entity_type].items():
                    entity_id = f"{entity_type}:{key}"
                    dependents = self._find_dependents(entity_id, graph)
                    dependencies = self._find_dependencies(entity_id, graph)
                    affected_entities.append({
                        'id': entity_id,
                        'type': entity_type,
                        'key': key,
                        'data': data,
                        'disposition': diff['entity_types']['dispositions'].get(entity_type, 'unknown'),
                        'dependents': dependents,
                        'dependencies': dependencies,
                    })

        # Find graph links matching removed dependency paths
        for source_id, node_data in graph.items():
            source_type, _ = parse_entity_id(source_id)
            if source_type is None:
                continue
            for dep in node_data.get('depends_on', []):
                dep_type, _ = parse_entity_id(dep)
                if dep_type is None:
                    continue
                # Skip reference dependencies — they bypass entity rules
                if self._is_reference_dep(dep_type):
                    continue
                if (source_type, dep_type) in removed_paths:
                    affected_links.append({
                        'from': source_id,
                        'to': dep,
                        'path': f"{source_type} → {dep_type}",
                    })

        # Find reference instances of removed reference types
        for ref_type in removed_ref_types:
            if ref_type in references:
                for key, data in references[ref_type].items():
                    affected_references.append({
                        'id': f"{ref_type}:{key}",
                        'type': ref_type,
                        'key': key,
                    })

        # Scan horizons for affected entity IDs
        affected_entity_ids = {e['id'] for e in affected_entities}
        for horizon_name, horizon_entries in horizons.items():
            if isinstance(horizon_entries, dict):
                for entity_id in horizon_entries:
                    if entity_id in affected_entity_ids:
                        affected_horizons.append({
                            'horizon': horizon_name,
                            'entity_id': entity_id,
                        })

        return {
            'entities': affected_entities,
            'links': affected_links,
            'references': affected_references,
            'horizons': affected_horizons,
            'counts': {
                'entities': len(affected_entities),
                'links': len(affected_links),
                'references': len(affected_references),
                'horizons': len(affected_horizons),
            },
        }

    def generate_plan(self, diff: Dict[str, Any], impact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ordered migration steps with executable know commands.

        Returns a list of steps grouped by phase.
        """
        steps = []

        # Phase 0: Pre-migration validation
        steps.append({
            'phase': 'pre-validation',
            'description': 'Validate graph against current rules before migration',
            'command': 'know check validate',
            'type': 'validation',
        })

        # Phase 1: Create reference equivalents for demoted entities
        for entity in impact['entities']:
            if entity['disposition'] == 'demoted_to_reference':
                data_json = json.dumps({
                    'name': entity['data'].get('name', entity['key']),
                    'description': entity['data'].get('description', ''),
                })
                steps.append({
                    'phase': 'create-references',
                    'description': f"Create reference equivalent for demoted entity {entity['id']}",
                    'command': f"know add reference {entity['type']} {entity['key']} '{data_json}'",
                    'type': 'create',
                    'entity_id': entity['id'],
                })

        # Phase 2: Re-route invalid dependency links
        for link in impact['links']:
            from_type, _ = parse_entity_id(link['from'])
            to_type, _ = parse_entity_id(link['to'])

            steps.append({
                'phase': 'reroute-links',
                'description': f"Remove invalid link {link['from']} → {link['to']} (path {from_type} → {to_type} no longer allowed)",
                'command': f"know graph unlink {link['from']} {link['to']}",
                'type': 'unlink',
            })

            # If the target was demoted, suggest re-linking to the new reference
            to_disposition = diff['entity_types']['dispositions'].get(to_type)
            if to_disposition == 'demoted_to_reference':
                steps.append({
                    'phase': 'reroute-links',
                    'description': f"Re-link {link['from']} to reference {link['to']} (now a reference type)",
                    'command': f"know graph link {link['from']} {link['to']}",
                    'type': 'link',
                    'note': 'Reference dependencies bypass entity-to-entity rules',
                })

        # Phase 3: Remove demoted entity entries
        for entity in impact['entities']:
            if entity['disposition'] == 'demoted_to_reference':
                steps.append({
                    'phase': 'remove-entities',
                    'description': f"Remove demoted entity {entity['id']} from entities section",
                    'command': f"know nodes remove {entity['id']}",
                    'type': 'remove',
                    'entity_id': entity['id'],
                })
            elif entity['disposition'] == 'removed_entirely':
                steps.append({
                    'phase': 'remove-entities',
                    'description': f"Remove entity {entity['id']} (type no longer exists)",
                    'command': f"know nodes remove {entity['id']}",
                    'type': 'remove',
                    'entity_id': entity['id'],
                })

        # Phase 4: Update horizons metadata
        for horizon_entry in impact['horizons']:
            steps.append({
                'phase': 'update-phases',
                'description': f"Remove {horizon_entry['entity_id']} from horizon '{horizon_entry['horizon']}'",
                'command': f"know horizons remove {horizon_entry['horizon']} {horizon_entry['entity_id']}",
                'type': 'phase-update',
            })

        # Phase 5: Post-migration validation
        steps.append({
            'phase': 'post-validation',
            'description': 'Validate graph against target rules after migration',
            'command': f"know -r {self.target_rules_path} check validate",
            'type': 'validation',
        })

        return {
            'steps': steps,
            'phase_order': [
                'pre-validation',
                'create-references',
                'reroute-links',
                'remove-entities',
                'update-phases',
                'post-validation',
            ],
        }

    def run(self) -> Dict[str, Any]:
        """Execute full analysis pipeline: diff → impact → plan."""
        diff = self.diff_rules()
        impact = self.analyze_impact(diff)
        plan = self.generate_plan(diff, impact)

        return {
            'summary': {
                'current_rules': str(Path(self.current_rules_path).name),
                'target_rules': str(Path(self.target_rules_path).name),
                'entity_types_removed': len(diff['entity_types']['removed']),
                'entity_types_added': len(diff['entity_types']['added']),
                'dependency_paths_removed': len(diff['dependency_paths']['removed']),
                'dependency_paths_added': len(diff['dependency_paths']['added']),
                'affected_entities': impact['counts']['entities'],
                'affected_links': impact['counts']['links'],
                'affected_references': impact['counts']['references'],
                'affected_horizons': impact['counts']['horizons'],
                'total_steps': len(plan['steps']),
            },
            'diff': diff,
            'impact': impact,
            'plan': plan,
        }

    def _flatten_allowed_deps(self, rules: Dict) -> Set[Tuple[str, str]]:
        """Flatten allowed_dependencies into (from_type, to_type) tuples."""
        result = set()
        for from_type, to_types in rules.get('allowed_dependencies', {}).items():
            for to_type in to_types:
                result.add((from_type, to_type))
        return result

    def _find_dependents(self, entity_id: str, graph: Dict) -> List[str]:
        """Find entities that depend on the given entity."""
        dependents = []
        for source_id, node_data in graph.items():
            if entity_id in node_data.get('depends_on', []):
                dependents.append(source_id)
        return dependents

    def _find_dependencies(self, entity_id: str, graph: Dict) -> List[str]:
        """Find entities that the given entity depends on."""
        node_data = graph.get(entity_id, {})
        return node_data.get('depends_on', [])

    def _is_reference_dep(self, dep_type: str) -> bool:
        """Check if a dependency type is a reference type in current rules."""
        ref_types = set(
            self.current_rules.get('reference_dependency_rule', {}).get('reference_types', [])
        )
        return dep_type in ref_types
