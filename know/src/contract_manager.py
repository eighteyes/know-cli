"""
ContractManager: Bidirectional spec for declared intent vs observed reality.

Responsibilities:
- Load/save contract.yaml files per feature
- Track declared actions, files, entities
- Record observed files, entities during implementation
- Validate declared vs observed for drift detection
- Calculate confidence scores based on age, drift, verification
- Migrate config.json to contract.yaml
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fnmatch import fnmatch

import yaml


class ContractManager:
    """Manage feature contract.yaml files for drift detection."""

    CONTRACT_VERSION = 1
    CONTRACT_FILENAME = "contract.yaml"
    CONFIG_FILENAME = "config.json"

    def __init__(
        self,
        features_dir: str = ".ai/know/features",
        spec_graph_path: str = ".ai/know/spec-graph.json"
    ):
        """
        Initialize ContractManager.

        Args:
            features_dir: Path to features directory
            spec_graph_path: Path to spec-graph.json
        """
        self.features_dir = Path(features_dir)
        self.spec_graph_path = Path(spec_graph_path)

    def _get_feature_dir(self, feature_name: str) -> Optional[Path]:
        """Get feature directory path if it exists."""
        feature_dir = self.features_dir / feature_name
        if feature_dir.exists():
            return feature_dir
        return None

    def _get_contract_path(self, feature_name: str) -> Path:
        """Get path to contract.yaml for a feature."""
        return self.features_dir / feature_name / self.CONTRACT_FILENAME

    def _get_config_path(self, feature_name: str) -> Path:
        """Get path to config.json for a feature."""
        return self.features_dir / feature_name / self.CONFIG_FILENAME

    def _get_current_commit(self) -> Optional[str]:
        """Get current HEAD commit SHA."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _create_empty_contract(self, feature_name: str) -> Dict:
        """Create empty contract structure."""
        now = datetime.now(timezone.utc).isoformat()
        return {
            'version': self.CONTRACT_VERSION,
            'feature': feature_name,
            'created': now,
            'baseline_commit': self._get_current_commit(),
            'declared': {
                'actions': [],
                'files': {
                    'creates': [],
                    'modifies': []
                },
                'entities': {
                    'creates': [],
                    'depends_on': []
                }
            },
            'observed': {
                'files': {
                    'created': [],
                    'modified': [],
                    'deleted': []
                },
                'entities': {
                    'created': [],
                    'modified': []
                },
                'verified_date': None,
                'verified_commit': None,
                'commit_range': None
            },
            'validation': {
                'status': 'pending',
                'discrepancies': []
            },
            'confidence': {
                'score': 100,
                'factors': [],
                'manual_override': None
            },
            'watch': {
                'paths': [],
                'exclude': []
            }
        }

    def load_contract(self, feature_name: str) -> Optional[Dict]:
        """
        Load contract.yaml for a feature.

        Falls back to config.json migration if contract doesn't exist.

        Args:
            feature_name: Feature name

        Returns:
            Contract dict or None if not found
        """
        contract_path = self._get_contract_path(feature_name)

        if contract_path.exists():
            with open(contract_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        # Fall back to config.json
        config_path = self._get_config_path(feature_name)
        if config_path.exists():
            return self.migrate_from_config_json(feature_name, save=False)

        return None

    def save_contract(self, feature_name: str, contract: Dict) -> bool:
        """
        Save contract.yaml for a feature.

        Args:
            feature_name: Feature name
            contract: Contract data

        Returns:
            True if successful
        """
        contract_path = self._get_contract_path(feature_name)

        if not contract_path.parent.exists():
            return False

        try:
            with open(contract_path, 'w', encoding='utf-8') as f:
                yaml.dump(contract, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            return True
        except OSError:
            return False

    def ensure_contract(self, feature_name: str) -> Tuple[bool, Optional[Path]]:
        """
        Ensure contract.yaml exists for a feature. Create if missing.

        Args:
            feature_name: Feature name

        Returns:
            (created, contract_path) - created=True if file was just created
        """
        feature_dir = self._get_feature_dir(feature_name)
        if not feature_dir:
            return False, None

        contract_path = self._get_contract_path(feature_name)

        if contract_path.exists():
            return False, contract_path

        # Try to migrate from config.json first
        config_path = self._get_config_path(feature_name)
        if config_path.exists():
            self.migrate_from_config_json(feature_name, save=True)
            return True, contract_path

        # Create new empty contract
        contract = self._create_empty_contract(feature_name)
        if self.save_contract(feature_name, contract):
            return True, contract_path

        return False, None

    def set_declared_actions(self, feature_name: str, actions: List[Dict]) -> bool:
        """
        Set declared actions for a feature.

        Args:
            feature_name: Feature name
            actions: List of action dicts with 'entity' and 'description' keys

        Returns:
            True if successful
        """
        contract = self.load_contract(feature_name)
        if not contract:
            self.ensure_contract(feature_name)
            contract = self.load_contract(feature_name)
            if not contract:
                return False

        # Add 'verified' field if not present
        for action in actions:
            if 'verified' not in action:
                action['verified'] = False

        contract['declared']['actions'] = actions
        return self.save_contract(feature_name, contract)

    def set_declared_files(
        self,
        feature_name: str,
        creates: Optional[List[str]] = None,
        modifies: Optional[List[str]] = None
    ) -> bool:
        """
        Set declared files for a feature.

        Args:
            feature_name: Feature name
            creates: List of glob patterns for files to create
            modifies: List of glob patterns for files to modify

        Returns:
            True if successful
        """
        contract = self.load_contract(feature_name)
        if not contract:
            self.ensure_contract(feature_name)
            contract = self.load_contract(feature_name)
            if not contract:
                return False

        if creates is not None:
            contract['declared']['files']['creates'] = creates
        if modifies is not None:
            contract['declared']['files']['modifies'] = modifies

        return self.save_contract(feature_name, contract)

    def set_declared_entities(
        self,
        feature_name: str,
        creates: Optional[List[str]] = None,
        depends_on: Optional[List[str]] = None
    ) -> bool:
        """
        Set declared entities for a feature.

        Args:
            feature_name: Feature name
            creates: List of entity IDs to create (e.g., 'component:auth-handler')
            depends_on: List of entity IDs this feature depends on

        Returns:
            True if successful
        """
        contract = self.load_contract(feature_name)
        if not contract:
            self.ensure_contract(feature_name)
            contract = self.load_contract(feature_name)
            if not contract:
                return False

        if creates is not None:
            contract['declared']['entities']['creates'] = creates
        if depends_on is not None:
            contract['declared']['entities']['depends_on'] = depends_on

        return self.save_contract(feature_name, contract)

    def record_observed_files(
        self,
        feature_name: str,
        created: Optional[List[str]] = None,
        modified: Optional[List[str]] = None,
        deleted: Optional[List[str]] = None,
        commit_range: Optional[str] = None
    ) -> bool:
        """
        Record observed file changes during implementation.

        Args:
            feature_name: Feature name
            created: List of created file paths
            modified: List of modified file paths
            deleted: List of deleted file paths
            commit_range: Git commit range (e.g., 'abc123..def456')

        Returns:
            True if successful
        """
        contract = self.load_contract(feature_name)
        if not contract:
            return False

        if created is not None:
            contract['observed']['files']['created'] = created
        if modified is not None:
            contract['observed']['files']['modified'] = modified
        if deleted is not None:
            contract['observed']['files']['deleted'] = deleted
        if commit_range is not None:
            contract['observed']['commit_range'] = commit_range

        return self.save_contract(feature_name, contract)

    def record_observed_entities(
        self,
        feature_name: str,
        created: Optional[List[str]] = None,
        modified: Optional[List[str]] = None
    ) -> bool:
        """
        Record observed entity changes during implementation.

        Args:
            feature_name: Feature name
            created: List of created entity IDs
            modified: List of modified entity IDs

        Returns:
            True if successful
        """
        contract = self.load_contract(feature_name)
        if not contract:
            return False

        if created is not None:
            contract['observed']['entities']['created'] = created
        if modified is not None:
            contract['observed']['entities']['modified'] = modified

        return self.save_contract(feature_name, contract)

    def toggle_action_verified(
        self,
        feature_name: str,
        action_entity: str,
        verified: bool = True
    ) -> bool:
        """
        Toggle verified status for a declared action.

        Args:
            feature_name: Feature name
            action_entity: Action entity ID (e.g., 'action:user-login')
            verified: Whether action is verified

        Returns:
            True if successful
        """
        contract = self.load_contract(feature_name)
        if not contract:
            return False

        # Find and update the action
        for action in contract['declared']['actions']:
            if action.get('entity') == action_entity:
                action['verified'] = verified
                break
        else:
            # Action not found
            return False

        # Update verified_date if all actions are now verified
        all_verified = all(a.get('verified', False) for a in contract['declared']['actions'])
        if all_verified and contract['declared']['actions']:
            contract['observed']['verified_date'] = datetime.now(timezone.utc).isoformat()
            contract['observed']['verified_commit'] = self._get_current_commit()

        return self.save_contract(feature_name, contract)

    def validate_contract(self, feature_name: str) -> Dict:
        """
        Validate declared vs observed and return discrepancies.

        Args:
            feature_name: Feature name

        Returns:
            Dict with 'status' and 'discrepancies' list
        """
        contract = self.load_contract(feature_name)
        if not contract:
            return {'status': 'error', 'discrepancies': ['Contract not found']}

        discrepancies = []
        declared = contract.get('declared', {})
        observed = contract.get('observed', {})

        # Check declared file creates vs observed
        declared_creates = declared.get('files', {}).get('creates', [])
        observed_created = observed.get('files', {}).get('created', [])

        for pattern in declared_creates:
            matched = any(self._matches_pattern(f, pattern) for f in observed_created)
            if not matched:
                discrepancies.append({
                    'type': 'file_not_created',
                    'severity': 'high',
                    'pattern': pattern,
                    'message': f"Declared file pattern '{pattern}' not matched by any created file"
                })

        # Check for unexpected files
        declared_patterns = declared_creates + declared.get('files', {}).get('modifies', [])
        for created_file in observed_created:
            matched = any(self._matches_pattern(created_file, p) for p in declared_patterns)
            if not matched:
                discrepancies.append({
                    'type': 'file_unexpected',
                    'severity': 'medium',
                    'file': created_file,
                    'message': f"Created file '{created_file}' was not declared"
                })

        # Check declared entities vs observed
        declared_entity_creates = declared.get('entities', {}).get('creates', [])
        observed_entity_created = observed.get('entities', {}).get('created', [])

        for entity_id in declared_entity_creates:
            if entity_id not in observed_entity_created:
                discrepancies.append({
                    'type': 'entity_not_created',
                    'severity': 'high',
                    'entity': entity_id,
                    'message': f"Declared entity '{entity_id}' was not created"
                })

        # Check unverified actions
        for action in declared.get('actions', []):
            if not action.get('verified', False):
                discrepancies.append({
                    'type': 'action_unverified',
                    'severity': 'medium',
                    'action': action.get('entity'),
                    'message': f"Action '{action.get('entity')}' has not been verified"
                })

        # Determine status
        high_severity = any(d['severity'] == 'high' for d in discrepancies)
        has_discrepancies = len(discrepancies) > 0

        if high_severity:
            status = 'drifted'
        elif has_discrepancies:
            status = 'pending'
        else:
            status = 'verified'

        # Update contract with validation results
        contract['validation']['status'] = status
        contract['validation']['discrepancies'] = discrepancies
        self.save_contract(feature_name, contract)

        return {'status': status, 'discrepancies': discrepancies}

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a glob pattern."""
        if '**' in pattern:
            # Handle ** glob patterns
            return fnmatch(path, pattern) or fnmatch(path, pattern.replace('**/', '*/'))
        return fnmatch(path, pattern)

    def calculate_confidence(self, feature_name: str) -> Dict:
        """
        Calculate confidence score based on various factors.

        Confidence = 100
          - (days_since_baseline - 7) if > 7 days (max -20)
          - (file_drift_count * 5) (max -30)
          - (unverified_actions * 10)
          - (discrepancy_count * 5)
        = final score (min 0)

        Args:
            feature_name: Feature name

        Returns:
            Dict with 'score' and 'factors' list
        """
        contract = self.load_contract(feature_name)
        if not contract:
            return {'score': 0, 'factors': ['Contract not found']}

        score = 100
        factors = []

        # Age penalty
        created_str = contract.get('created')
        if created_str:
            try:
                created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                days_old = (datetime.now(timezone.utc) - created).days
                if days_old > 7:
                    penalty = min((days_old - 7), 20)
                    score -= penalty
                    factors.append(f"Age: -{penalty} ({days_old} days since baseline)")
            except ValueError:
                pass

        # File drift penalty
        validation = contract.get('validation', {})
        discrepancies = validation.get('discrepancies', [])

        file_drift = sum(1 for d in discrepancies if d.get('type') in ['file_not_created', 'file_unexpected'])
        if file_drift > 0:
            penalty = min(file_drift * 5, 30)
            score -= penalty
            factors.append(f"File drift: -{penalty} ({file_drift} files)")

        # Unverified actions penalty
        declared_actions = contract.get('declared', {}).get('actions', [])
        unverified = sum(1 for a in declared_actions if not a.get('verified', False))
        if unverified > 0:
            penalty = unverified * 10
            score -= penalty
            factors.append(f"Unverified actions: -{penalty} ({unverified} actions)")

        # General discrepancy penalty
        other_discrepancies = sum(1 for d in discrepancies if d.get('type') not in ['file_not_created', 'file_unexpected', 'action_unverified'])
        if other_discrepancies > 0:
            penalty = other_discrepancies * 5
            score -= penalty
            factors.append(f"Discrepancies: -{penalty} ({other_discrepancies} issues)")

        # Apply manual override if set
        manual_override = contract.get('confidence', {}).get('manual_override')
        if manual_override is not None:
            score = manual_override
            factors.append(f"Manual override: {manual_override}")

        # Ensure score is in valid range
        score = max(0, min(100, score))

        # Update contract with confidence
        contract['confidence']['score'] = score
        contract['confidence']['factors'] = factors
        self.save_contract(feature_name, contract)

        return {'score': score, 'factors': factors}

    def migrate_from_config_json(self, feature_name: str, save: bool = True) -> Optional[Dict]:
        """
        Migrate config.json to contract.yaml format.

        Args:
            feature_name: Feature name
            save: Whether to save the migrated contract

        Returns:
            Migrated contract dict or None if config.json not found
        """
        config_path = self._get_config_path(feature_name)
        if not config_path.exists():
            return None

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        # Create new contract from config data
        contract = self._create_empty_contract(feature_name)

        # Migrate watch paths
        watch = config.get('watch', {})
        contract['watch']['paths'] = watch.get('paths', [])
        contract['watch']['exclude'] = watch.get('exclude', [])

        # Migrate baseline
        baseline = config.get('baseline', {})
        if baseline.get('commit'):
            contract['baseline_commit'] = baseline['commit']
        if baseline.get('timestamp'):
            contract['created'] = baseline['timestamp']

        if save:
            self.save_contract(feature_name, contract)
            # Rename config.json to config.json.migrated for rollback
            try:
                config_path.rename(config_path.with_suffix('.json.migrated'))
            except OSError:
                pass

        return contract

    def get_watched_paths(self, feature_name: str) -> List[str]:
        """
        Get watched paths for a feature. Compatible with FeatureTracker.

        Args:
            feature_name: Feature name

        Returns:
            List of glob patterns to watch
        """
        contract = self.load_contract(feature_name)
        if not contract:
            return []

        paths = contract.get('watch', {}).get('paths', [])

        # Always include feature directory
        feature_dir = self._get_feature_dir(feature_name)
        if feature_dir:
            paths.append(f"{feature_dir}/**")

        return list(set(paths))

    def add_watch_path(self, feature_name: str, path: str) -> bool:
        """
        Add a path to the feature's watch list. Compatible with FeatureTracker.

        Args:
            feature_name: Feature name
            path: Glob pattern to watch

        Returns:
            True if successful
        """
        contract = self.load_contract(feature_name)
        if not contract:
            self.ensure_contract(feature_name)
            contract = self.load_contract(feature_name)
            if not contract:
                return False

        if path not in contract['watch']['paths']:
            contract['watch']['paths'].append(path)

        return self.save_contract(feature_name, contract)

    def set_baseline(self, feature_name: str, commit: Optional[str] = None) -> bool:
        """
        Set baseline commit for a feature. Compatible with FeatureTracker.

        Args:
            feature_name: Feature name
            commit: Optional commit SHA (defaults to HEAD)

        Returns:
            True if successful
        """
        contract = self.load_contract(feature_name)
        if not contract:
            self.ensure_contract(feature_name)
            contract = self.load_contract(feature_name)
            if not contract:
                return False

        contract['baseline_commit'] = commit or self._get_current_commit()
        contract['created'] = datetime.now(timezone.utc).isoformat()

        return self.save_contract(feature_name, contract)

    def get_contract_summary(self, feature_name: str) -> Optional[Dict]:
        """
        Get a summary of contract status for display.

        Args:
            feature_name: Feature name

        Returns:
            Summary dict or None if contract not found
        """
        contract = self.load_contract(feature_name)
        if not contract:
            return None

        declared = contract.get('declared', {})
        observed = contract.get('observed', {})
        validation = contract.get('validation', {})
        confidence = contract.get('confidence', {})

        actions = declared.get('actions', [])
        verified_actions = sum(1 for a in actions if a.get('verified', False))

        return {
            'feature': feature_name,
            'created': contract.get('created'),
            'baseline_commit': contract.get('baseline_commit'),
            'validation_status': validation.get('status', 'pending'),
            'confidence_score': confidence.get('score', 100),
            'declared_files': {
                'creates': len(declared.get('files', {}).get('creates', [])),
                'modifies': len(declared.get('files', {}).get('modifies', []))
            },
            'declared_entities': {
                'creates': len(declared.get('entities', {}).get('creates', [])),
                'depends_on': len(declared.get('entities', {}).get('depends_on', []))
            },
            'declared_actions': {
                'total': len(actions),
                'verified': verified_actions
            },
            'observed_files': {
                'created': len(observed.get('files', {}).get('created', [])),
                'modified': len(observed.get('files', {}).get('modified', [])),
                'deleted': len(observed.get('files', {}).get('deleted', []))
            },
            'discrepancy_count': len(validation.get('discrepancies', []))
        }

    def list_all_features_with_contracts(self) -> List[str]:
        """List all features that have contracts (either contract.yaml or config.json)."""
        features = []
        if not self.features_dir.exists():
            return features

        for feature_dir in self.features_dir.iterdir():
            if not feature_dir.is_dir():
                continue
            if feature_dir.name == 'archive':
                continue
            contract_path = feature_dir / self.CONTRACT_FILENAME
            config_path = feature_dir / self.CONFIG_FILENAME
            if contract_path.exists() or config_path.exists():
                features.append(feature_dir.name)

        return sorted(features)
