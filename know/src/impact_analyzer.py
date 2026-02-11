"""
ImpactAnalyzer: Cross-feature dependency queries.

Responsibilities:
- Find features depending on a given entity
- Find features using a given file path
- Generate full impact reports for entities or files
"""

from pathlib import Path
from typing import Dict, List, Set

from .contract_manager import ContractManager


class ImpactAnalyzer:
    """Analyze cross-feature dependencies and file impacts."""

    def __init__(
        self,
        features_dir: str = ".ai/know/features",
        spec_graph_path: str = ".ai/know/spec-graph.json"
    ):
        """
        Initialize ImpactAnalyzer.

        Args:
            features_dir: Path to features directory
            spec_graph_path: Path to spec-graph.json
        """
        self.features_dir = Path(features_dir)
        self.spec_graph_path = Path(spec_graph_path)
        self.contract_manager = ContractManager(
            features_dir=str(features_dir),
            spec_graph_path=str(spec_graph_path)
        )

    def get_features_depending_on(self, entity_id: str) -> List[Dict]:
        """
        Find features that declare this entity as a dependency.

        Args:
            entity_id: Entity ID (e.g., 'component:validation-engine')

        Returns:
            List of feature info dicts with 'name', 'relationship', 'contract_status'
        """
        features = self.contract_manager.list_all_features_with_contracts()
        depending_features = []

        for feature_name in features:
            contract = self.contract_manager.load_contract(feature_name)
            if not contract:
                continue

            declared = contract.get('declared', {})
            entities = declared.get('entities', {})
            depends_on = entities.get('depends_on', [])

            if entity_id in depends_on:
                validation = contract.get('validation', {})
                depending_features.append({
                    'name': feature_name,
                    'relationship': 'depends_on',
                    'contract_status': validation.get('status', 'pending'),
                    'confidence': contract.get('confidence', {}).get('score', 100)
                })

        return depending_features

    def get_features_creating(self, entity_id: str) -> List[Dict]:
        """
        Find features that declare they will create this entity.

        Args:
            entity_id: Entity ID (e.g., 'component:auth-handler')

        Returns:
            List of feature info dicts
        """
        features = self.contract_manager.list_all_features_with_contracts()
        creating_features = []

        for feature_name in features:
            contract = self.contract_manager.load_contract(feature_name)
            if not contract:
                continue

            declared = contract.get('declared', {})
            entities = declared.get('entities', {})
            creates = entities.get('creates', [])

            if entity_id in creates:
                validation = contract.get('validation', {})
                creating_features.append({
                    'name': feature_name,
                    'relationship': 'creates',
                    'contract_status': validation.get('status', 'pending'),
                    'confidence': contract.get('confidence', {}).get('score', 100)
                })

        return creating_features

    def get_features_using_file(self, file_path: str) -> List[Dict]:
        """
        Find features that declare this file in their contract.

        Args:
            file_path: File path to search for

        Returns:
            List of feature info dicts with relationship type
        """
        features = self.contract_manager.list_all_features_with_contracts()
        using_features = []

        for feature_name in features:
            contract = self.contract_manager.load_contract(feature_name)
            if not contract:
                continue

            declared = contract.get('declared', {})
            files = declared.get('files', {})
            creates = files.get('creates', [])
            modifies = files.get('modifies', [])

            relationships = []

            # Check creates patterns
            for pattern in creates:
                if self._matches_pattern(file_path, pattern):
                    relationships.append('creates')
                    break

            # Check modifies patterns
            for pattern in modifies:
                if self._matches_pattern(file_path, pattern):
                    relationships.append('modifies')
                    break

            # Check watch paths
            watch_paths = contract.get('watch', {}).get('paths', [])
            for pattern in watch_paths:
                if self._matches_pattern(file_path, pattern):
                    if 'watches' not in relationships:
                        relationships.append('watches')
                    break

            if relationships:
                validation = contract.get('validation', {})
                using_features.append({
                    'name': feature_name,
                    'relationships': relationships,
                    'contract_status': validation.get('status', 'pending'),
                    'confidence': contract.get('confidence', {}).get('score', 100)
                })

        return using_features

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a glob pattern."""
        from fnmatch import fnmatch

        if '**' in pattern:
            return fnmatch(path, pattern) or fnmatch(path, pattern.replace('**/', '*/'))
        return fnmatch(path, pattern)

    def get_impact_report(self, target: str) -> Dict:
        """
        Generate full impact report for an entity or file.

        Args:
            target: Entity ID or file path

        Returns:
            Dict with impact analysis
        """
        is_entity = ':' in target and not target.startswith('/')

        if is_entity:
            return self._get_entity_impact_report(target)
        else:
            return self._get_file_impact_report(target)

    def _get_entity_impact_report(self, entity_id: str) -> Dict:
        """Generate impact report for an entity."""
        creating = self.get_features_creating(entity_id)
        depending = self.get_features_depending_on(entity_id)

        # Collect all affected features
        affected_features: Set[str] = set()
        for f in creating:
            affected_features.add(f['name'])
        for f in depending:
            affected_features.add(f['name'])

        # Calculate overall impact severity
        severity = self._calculate_impact_severity(creating, depending)

        return {
            'target': entity_id,
            'target_type': 'entity',
            'entity_type': entity_id.split(':')[0] if ':' in entity_id else 'unknown',
            'features_creating': creating,
            'features_depending': depending,
            'total_affected_features': len(affected_features),
            'affected_feature_names': sorted(affected_features),
            'impact_severity': severity,
            'recommendations': self._generate_entity_recommendations(entity_id, creating, depending)
        }

    def _get_file_impact_report(self, file_path: str) -> Dict:
        """Generate impact report for a file."""
        using = self.get_features_using_file(file_path)

        # Separate by relationship type
        creating = [f for f in using if 'creates' in f.get('relationships', [])]
        modifying = [f for f in using if 'modifies' in f.get('relationships', [])]
        watching = [f for f in using if 'watches' in f.get('relationships', [])]

        affected_features: Set[str] = {f['name'] for f in using}

        return {
            'target': file_path,
            'target_type': 'file',
            'features_creating': creating,
            'features_modifying': modifying,
            'features_watching': watching,
            'total_affected_features': len(affected_features),
            'affected_feature_names': sorted(affected_features),
            'recommendations': self._generate_file_recommendations(file_path, using)
        }

    def _calculate_impact_severity(
        self,
        creating: List[Dict],
        depending: List[Dict]
    ) -> str:
        """Calculate impact severity based on affected features."""
        total = len(creating) + len(depending)

        if total == 0:
            return 'none'
        elif total <= 2:
            return 'low'
        elif total <= 5:
            return 'medium'
        else:
            return 'high'

    def _generate_entity_recommendations(
        self,
        entity_id: str,
        creating: List[Dict],
        depending: List[Dict]
    ) -> List[str]:
        """Generate recommendations for entity changes."""
        recommendations = []

        if len(creating) > 1:
            names = [f['name'] for f in creating]
            recommendations.append(
                f"Multiple features claim to create this entity: {', '.join(names)}. "
                "Resolve ownership conflict."
            )

        if depending:
            low_confidence = [f for f in depending if f.get('confidence', 100) < 70]
            if low_confidence:
                names = [f['name'] for f in low_confidence]
                recommendations.append(
                    f"Features with low confidence depend on this: {', '.join(names)}. "
                    "Review their contracts before changes."
                )

        if not creating and depending:
            recommendations.append(
                f"Entity is depended upon but no feature claims to create it. "
                "Consider adding it to a feature contract."
            )

        if not recommendations:
            recommendations.append("No issues detected.")

        return recommendations

    def _generate_file_recommendations(
        self,
        file_path: str,
        using: List[Dict]
    ) -> List[str]:
        """Generate recommendations for file changes."""
        recommendations = []

        creating = [f for f in using if 'creates' in f.get('relationships', [])]
        modifying = [f for f in using if 'modifies' in f.get('relationships', [])]

        if len(creating) > 1:
            names = [f['name'] for f in creating]
            recommendations.append(
                f"Multiple features claim to create this file: {', '.join(names)}. "
                "Resolve conflict."
            )

        if creating and modifying:
            creator_names = [f['name'] for f in creating]
            modifier_names = [f['name'] for f in modifying]
            recommendations.append(
                f"File is created by {', '.join(creator_names)} and modified by {', '.join(modifier_names)}. "
                "Ensure proper coordination."
            )

        drifted = [f for f in using if f.get('contract_status') == 'drifted']
        if drifted:
            names = [f['name'] for f in drifted]
            recommendations.append(
                f"Features with drifted contracts use this file: {', '.join(names)}. "
                "Review and validate contracts."
            )

        if not recommendations:
            recommendations.append("No issues detected.")

        return recommendations

    def get_all_feature_summaries(self) -> List[Dict]:
        """Get contract summaries for all features."""
        features = self.contract_manager.list_all_features_with_contracts()
        summaries = []

        for feature_name in features:
            summary = self.contract_manager.get_contract_summary(feature_name)
            if summary:
                summaries.append(summary)

        return summaries
