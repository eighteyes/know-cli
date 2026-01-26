"""
coverage.py - Test coverage analysis from feature level
Traverses spec-graph to code-graph to aggregate test coverage metrics
"""

import json
from pathlib import Path
from typing import Optional


class CoverageAnalyzer:
    """Analyze test coverage by traversing spec-graph to code-graph."""

    def __init__(self, spec_graph_manager, code_graph_path: Optional[str] = None):
        """Initialize with spec and code graph managers.

        Args:
            spec_graph_manager: GraphManager for spec-graph.json
            code_graph_path: Path to code-graph.json (optional)
        """
        self.spec = spec_graph_manager
        self.code_graph_path = code_graph_path or '.ai/code-graph.json'
        self._code_graph_data = None

    def _load_code_graph(self):
        """Load code graph data lazily."""
        if self._code_graph_data is None:
            path = Path(self.code_graph_path)
            if path.exists():
                with open(path, 'r') as f:
                    self._code_graph_data = json.load(f)
            else:
                self._code_graph_data = {'entities': {}, 'graph': {}, 'references': {}}
        return self._code_graph_data

    def get_feature_components(self, feature_name: str) -> list:
        """Get all components linked to a feature.

        Args:
            feature_name: Feature key (without prefix)

        Returns:
            List of component IDs
        """
        data = self.spec.load()
        feature_id = f"feature:{feature_name}"

        if feature_id not in data.get('graph', {}):
            return []

        components = []
        visited = set()

        def traverse(entity_id):
            if entity_id in visited:
                return
            visited.add(entity_id)

            if entity_id.startswith('component:'):
                components.append(entity_id)

            if entity_id in data.get('graph', {}):
                for dep in data['graph'][entity_id].get('depends_on', []):
                    traverse(dep)

        traverse(feature_id)
        return components

    def get_component_modules(self, component_id: str) -> list:
        """Find code modules that implement a spec component.

        Args:
            component_id: Component ID (e.g., 'component:auth-form')

        Returns:
            List of module IDs from code-graph
        """
        code_data = self._load_code_graph()
        product_refs = code_data.get('references', {}).get('product-component', {})
        modules = []

        for module_key, ref_data in product_refs.items():
            if ref_data.get('component') == component_id:
                modules.append(f"module:{module_key}")

        return modules

    def get_module_test_suites(self, module_id: str) -> list:
        """Find test suites that cover a module.

        Args:
            module_id: Module ID (e.g., 'module:auth-handler')

        Returns:
            List of test suite data dicts
        """
        code_data = self._load_code_graph()
        test_suites = code_data.get('references', {}).get('test-suite', {})
        module_key = module_id.replace('module:', '')
        matching_suites = []

        for suite_key, suite_data in test_suites.items():
            target = suite_data.get('target_module', '')
            if target == module_id or target == module_key:
                matching_suites.append({
                    'key': suite_key,
                    **suite_data
                })

        return matching_suites

    def get_feature_coverage(self, feature_name: str) -> dict:
        """Get aggregated test coverage for a feature.

        Traverses: feature -> components -> modules -> test-suites
        Aggregates coverage percentages across all test suites.

        Args:
            feature_name: Feature key (without prefix)

        Returns:
            Coverage metrics dict
        """
        components = self.get_feature_components(feature_name)

        all_modules = []
        all_test_suites = []
        comp_coverage = []

        for comp_id in components:
            modules = self.get_component_modules(comp_id)
            comp_suites = []

            for mod_id in modules:
                all_modules.append(mod_id)
                suites = self.get_module_test_suites(mod_id)
                comp_suites.extend(suites)
                all_test_suites.extend(suites)

            comp_coverage.append({
                'component': comp_id,
                'modules': modules,
                'test_suites': len(comp_suites),
                'coverage': self._aggregate_coverage(comp_suites)
            })

        aggregated = self._aggregate_coverage(all_test_suites)

        return {
            'feature': f"feature:{feature_name}",
            'components': len(components),
            'modules': len(all_modules),
            'test_suites': len(all_test_suites),
            'coverage_percent': aggregated['coverage_percent'],
            'test_count': aggregated['test_count'],
            'test_types': aggregated['types'],
            'by_component': comp_coverage
        }

    def _aggregate_coverage(self, test_suites: list) -> dict:
        """Aggregate coverage from multiple test suites.

        Args:
            test_suites: List of test suite data dicts

        Returns:
            Aggregated metrics
        """
        if not test_suites:
            return {
                'coverage_percent': 0,
                'test_count': 0,
                'suites': 0,
                'types': []
            }

        total_coverage = sum(ts.get('coverage_percent', 0) for ts in test_suites)
        total_tests = sum(ts.get('test_count', 0) for ts in test_suites)
        test_types = list(set(ts.get('test_type', 'unknown') for ts in test_suites))

        return {
            'coverage_percent': round(total_coverage / len(test_suites), 1),
            'test_count': total_tests,
            'suites': len(test_suites),
            'types': test_types
        }

    def get_all_features_coverage(self) -> list:
        """Get coverage summary for all features.

        Returns:
            List of coverage dicts per feature
        """
        data = self.spec.load()
        features = data.get('entities', {}).get('feature', {})
        coverage_list = []

        for feature_name in features:
            coverage = self.get_feature_coverage(feature_name)
            coverage_list.append(coverage)

        coverage_list.sort(key=lambda x: x['coverage_percent'])
        return coverage_list

    def get_untested_components(self) -> list:
        """Find components with no test coverage.

        Returns:
            List of component IDs without any test suites
        """
        data = self.spec.load()
        components = data.get('entities', {}).get('component', {})
        untested = []

        for comp_key in components:
            comp_id = f"component:{comp_key}"
            modules = self.get_component_modules(comp_id)

            has_tests = False
            for mod_id in modules:
                if self.get_module_test_suites(mod_id):
                    has_tests = True
                    break

            if not has_tests:
                untested.append(comp_id)

        return untested

    def get_coverage_gaps(self, feature_name: str) -> dict:
        """Identify testing gaps for a feature.

        Args:
            feature_name: Feature key

        Returns:
            Dict with gaps analysis
        """
        components = self.get_feature_components(feature_name)

        gaps = {
            'unmapped_components': [],
            'untested_modules': [],
            'low_coverage_modules': []
        }

        for comp_id in components:
            modules = self.get_component_modules(comp_id)

            if not modules:
                gaps['unmapped_components'].append(comp_id)
                continue

            for mod_id in modules:
                suites = self.get_module_test_suites(mod_id)

                if not suites:
                    gaps['untested_modules'].append({
                        'module': mod_id,
                        'component': comp_id
                    })
                else:
                    avg_coverage = sum(s.get('coverage_percent', 0) for s in suites) / len(suites)
                    if avg_coverage < 50:
                        gaps['low_coverage_modules'].append({
                            'module': mod_id,
                            'component': comp_id,
                            'coverage': round(avg_coverage, 1)
                        })

        return gaps
