"""
FeatureTracker: Track feature-related code changes and git commits.

Responsibilities:
- Get feature baseline timestamp/commit from config.json or directory mtime
- Resolve feature → file paths mapping (explicit + graph-derived)
- Query git for changed files since baseline
- Tag commits with git notes (refs/notes/know-features)
- Store commit SHAs in spec-graph meta.feature_commits
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class FeatureTracker:
    """Track feature-related code changes and git commits."""

    GIT_NOTES_REF = "refs/notes/know-features"

    def __init__(
        self,
        spec_graph_path: str = ".ai/spec-graph.json",
        code_graph_path: Optional[str] = ".ai/code-graph.json",
        features_dir: str = ".ai/know/features"
    ):
        """
        Initialize FeatureTracker.

        Args:
            spec_graph_path: Path to spec-graph.json
            code_graph_path: Path to code-graph.json (optional)
            features_dir: Path to features directory
        """
        self.spec_graph_path = Path(spec_graph_path)
        self.code_graph_path = Path(code_graph_path) if code_graph_path else None
        self.features_dir = Path(features_dir)

        self._spec_graph: Optional[Dict] = None
        self._code_graph: Optional[Dict] = None

    @property
    def spec_graph(self) -> Dict:
        """Lazy-load spec-graph."""
        if self._spec_graph is None:
            self._spec_graph = self._load_json(self.spec_graph_path)
        return self._spec_graph

    @property
    def code_graph(self) -> Optional[Dict]:
        """Lazy-load code-graph."""
        if self._code_graph is None and self.code_graph_path and self.code_graph_path.exists():
            self._code_graph = self._load_json(self.code_graph_path)
        return self._code_graph

    def _load_json(self, path: Path) -> Dict:
        """Load JSON file."""
        if not path.exists():
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_json(self, path: Path, data: Dict) -> bool:
        """Save JSON file with proper formatting."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except OSError as e:
            print(f"Error saving {path}: {e}")
            return False

    def _run_git(self, args: List[str], timeout: int = 30) -> Dict:
        """
        Execute git command and return result.

        Args:
            args: Git command arguments (without 'git' prefix)
            timeout: Command timeout in seconds

        Returns:
            Dict with 'success', 'output', and optional 'error' keys
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout
            )
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout.strip(), 'stderr': result.stderr}
            else:
                return {'success': False, 'error': result.stderr or result.stdout, 'returncode': result.returncode}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': f'git command timed out after {timeout} seconds'}
        except FileNotFoundError:
            return {'success': False, 'error': 'git command not found'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}

    def get_feature_dir(self, feature_name: str) -> Optional[Path]:
        """Get feature directory path if it exists."""
        feature_dir = self.features_dir / feature_name
        if feature_dir.exists():
            return feature_dir
        return None

    def get_feature_config(self, feature_name: str) -> Dict:
        """
        Load feature config.json.

        Args:
            feature_name: Feature name (without 'feature:' prefix)

        Returns:
            Config dict or empty dict if not found
        """
        feature_dir = self.get_feature_dir(feature_name)
        if not feature_dir:
            return {}
        config_path = feature_dir / "config.json"
        if config_path.exists():
            return self._load_json(config_path)
        return {}

    def get_feature_baseline(self, feature_name: str) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Get feature baseline timestamp and commit.

        Resolution order:
        1. config.json baseline.timestamp / baseline.commit
        2. Feature directory mtime

        Args:
            feature_name: Feature name

        Returns:
            Tuple of (datetime, commit_sha) - either may be None
        """
        config = self.get_feature_config(feature_name)

        # Check config.json first
        if config.get('baseline'):
            baseline = config['baseline']
            ts = None
            if baseline.get('timestamp'):
                try:
                    ts = datetime.fromisoformat(baseline['timestamp'].replace('Z', '+00:00'))
                except ValueError:
                    pass
            return ts, baseline.get('commit')

        # Fall back to directory mtime
        feature_dir = self.get_feature_dir(feature_name)
        if feature_dir:
            mtime = feature_dir.stat().st_mtime
            return datetime.fromtimestamp(mtime), None

        return None, None

    def get_watched_paths(self, feature_name: str) -> List[str]:
        """
        Resolve all watched paths for a feature.

        Three-tier resolution:
        1. Explicit paths from config.json watch.paths
        2. Module files from code-graph product-component refs
        3. Feature directory (always included)

        Args:
            feature_name: Feature name

        Returns:
            List of glob patterns/paths to watch
        """
        paths = []

        # 1. Explicit from config.json
        config = self.get_feature_config(feature_name)
        if config.get('watch', {}).get('paths'):
            paths.extend(config['watch']['paths'])

        # 2. From code-graph product-component refs
        if self.code_graph:
            product_components = self.code_graph.get('references', {}).get('product-component', {})
            modules = self.code_graph.get('entities', {}).get('module', {})

            for ref_key, ref_data in product_components.items():
                # Check if this component is linked to our feature
                if ref_data.get('feature') == f"feature:{feature_name}":
                    # Get the module's file path
                    module = modules.get(ref_key, {})
                    if module.get('file'):
                        paths.append(module['file'])

        # 3. Feature directory always included
        feature_dir = self.get_feature_dir(feature_name)
        if feature_dir:
            paths.append(f"{feature_dir}/**")

        return list(set(paths))

    def get_changed_files(self, feature_name: str, since: Optional[str] = None) -> List[Dict]:
        """
        Get files changed since feature baseline.

        Args:
            feature_name: Feature name
            since: Override baseline (ISO date or commit SHA)

        Returns:
            List of dicts with 'file', 'commits', 'risk' keys
        """
        # Determine baseline
        if since:
            since_arg = since
        else:
            baseline_ts, baseline_commit = self.get_feature_baseline(feature_name)
            if baseline_commit:
                since_arg = baseline_commit
            elif baseline_ts:
                since_arg = baseline_ts.strftime('%Y-%m-%d')
            else:
                return []

        # Get watched paths
        watched = self.get_watched_paths(feature_name)
        if not watched:
            return []

        # Query git for changes
        # Using --name-only to get file list, --since for date, or commit range for SHA
        if len(since_arg) == 40 or (len(since_arg) >= 7 and since_arg.isalnum()):
            # Looks like a commit SHA
            git_args = ['log', f'{since_arg}..HEAD', '--name-only', '--pretty=format:%H']
        else:
            # Treat as date
            git_args = ['log', f'--since={since_arg}', '--name-only', '--pretty=format:%H']

        result = self._run_git(git_args)
        if not result['success']:
            return []

        # Parse output: alternating commit SHA and file names
        changed_files: Dict[str, List[str]] = {}
        current_commit = None

        for line in result['output'].split('\n'):
            line = line.strip()
            if not line:
                continue
            if len(line) == 40 and line.isalnum():
                current_commit = line
            elif current_commit and line:
                if line not in changed_files:
                    changed_files[line] = []
                changed_files[line].append(current_commit)

        # Filter to watched paths and assess risk
        results = []
        for file_path, commits in changed_files.items():
            if self._matches_watched(file_path, watched):
                risk = self._assess_file_risk(file_path, feature_name)
                results.append({
                    'file': file_path,
                    'commits': commits,
                    'risk': risk
                })

        # Sort by risk level
        risk_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'INFO': 3}
        results.sort(key=lambda x: risk_order.get(x['risk'], 99))

        return results

    def _matches_watched(self, file_path: str, watched: List[str]) -> bool:
        """Check if file matches any watched pattern."""
        from fnmatch import fnmatch

        for pattern in watched:
            if '**' in pattern:
                # Glob pattern
                if fnmatch(file_path, pattern) or fnmatch(file_path, pattern.replace('**', '*')):
                    return True
            elif file_path == pattern or file_path.startswith(pattern.rstrip('/')):
                return True
        return True  # Include all by default for now

    def _assess_file_risk(self, file_path: str, feature_name: str) -> str:
        """
        Assess risk level for a changed file.

        HIGH: Direct feature component file
        MEDIUM: Same directory/package
        LOW: Test files, config files
        INFO: Documentation, comments
        """
        path_lower = file_path.lower()

        # INFO: Documentation
        if path_lower.endswith(('.md', '.txt', '.rst')):
            return 'INFO'

        # LOW: Tests
        if 'test' in path_lower or path_lower.startswith('tests/'):
            return 'LOW'

        # LOW: Config files
        if path_lower.endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg')):
            return 'LOW'

        # Check if in feature directory
        if f'.ai/know/features/{feature_name}' in file_path:
            return 'MEDIUM'

        # HIGH: Source files in watched paths
        if path_lower.endswith(('.py', '.ts', '.js', '.tsx', '.jsx', '.go', '.rs')):
            return 'HIGH'

        return 'MEDIUM'

    def assess_risk(self, feature_name: str, changed_files: List[Dict]) -> Dict:
        """
        Generate risk assessment summary.

        Args:
            feature_name: Feature name
            changed_files: Output from get_changed_files()

        Returns:
            Dict with counts per risk level and recommendation
        """
        counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
        for cf in changed_files:
            counts[cf.get('risk', 'INFO')] += 1

        # Generate recommendation
        if counts['HIGH'] > 0:
            recommendation = "Review plan immediately - direct component changes detected"
        elif counts['MEDIUM'] > 2:
            recommendation = "Consider reviewing plan - multiple related changes"
        elif counts['MEDIUM'] > 0:
            recommendation = "Plan likely valid - minor related changes"
        else:
            recommendation = "Plan is current - no significant changes"

        return {
            'feature': feature_name,
            'counts': counts,
            'total': sum(counts.values()),
            'recommendation': recommendation
        }

    def get_feature_commits(self, feature_name: str, since: Optional[str] = None) -> List[Dict]:
        """
        Get commits since baseline that touch watched files.

        Args:
            feature_name: Feature name
            since: Override baseline

        Returns:
            List of dicts with 'sha', 'message', 'files' keys
        """
        # Get changed files first to identify relevant commits
        changed = self.get_changed_files(feature_name, since)

        # Collect unique commits
        commit_shas = set()
        for cf in changed:
            commit_shas.update(cf['commits'])

        if not commit_shas:
            return []

        # Get commit details
        commits = []
        for sha in sorted(commit_shas):
            result = self._run_git(['log', '-1', '--pretty=format:%s', sha])
            if result['success']:
                files = [cf['file'] for cf in changed if sha in cf['commits']]
                commits.append({
                    'sha': sha,
                    'short_sha': sha[:7],
                    'message': result['output'],
                    'files': files
                })

        return commits

    def tag_commits(self, feature_name: str, shas: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Tag commits with git notes.

        Args:
            feature_name: Feature name
            shas: List of commit SHAs to tag

        Returns:
            (success, error_message)
        """
        note_content = f"know:feature:{feature_name}"
        tagged = 0

        for sha in shas:
            # Check if already tagged
            check = self._run_git(['notes', '--ref', self.GIT_NOTES_REF, 'show', sha])
            if check['success'] and f"know:feature:{feature_name}" in check['output']:
                continue  # Already tagged

            # Add note
            result = self._run_git([
                'notes', '--ref', self.GIT_NOTES_REF,
                'add', '-f', '-m', note_content, sha
            ])
            if not result['success']:
                return False, f"Failed to tag {sha[:7]}: {result.get('error', 'Unknown error')}"
            tagged += 1

        return True, None

    def store_commits(self, feature_name: str, shas: List[str]) -> bool:
        """
        Store commit SHAs in spec-graph meta.feature_commits.

        Args:
            feature_name: Feature name
            shas: List of commit SHAs

        Returns:
            True if successful
        """
        # Reload spec-graph to get fresh data
        spec_graph = self._load_json(self.spec_graph_path)

        if 'meta' not in spec_graph:
            spec_graph['meta'] = {}

        if 'feature_commits' not in spec_graph['meta']:
            spec_graph['meta']['feature_commits'] = {}

        # Store simplified format: feature_name -> [sha1, sha2, ...]
        # Use short SHAs for readability
        short_shas = [sha[:7] for sha in shas]
        spec_graph['meta']['feature_commits'][feature_name] = short_shas

        return self._save_json(self.spec_graph_path, spec_graph)

    def get_stored_commits(self, feature_name: str) -> List[str]:
        """Get stored commit SHAs for a feature."""
        return self.spec_graph.get('meta', {}).get('feature_commits', {}).get(feature_name, [])

    def ensure_config(self, feature_name: str) -> Tuple[bool, Path]:
        """
        Ensure config.json exists for a feature. Create if missing.

        Args:
            feature_name: Feature name

        Returns:
            (created, config_path) - created=True if file was just created
        """
        feature_dir = self.get_feature_dir(feature_name)
        if not feature_dir:
            return False, None

        config_path = feature_dir / "config.json"
        if config_path.exists():
            return False, config_path

        # Create default config
        config = {
            "watch": {
                "paths": [],
                "exclude": []
            },
            "baseline": {}
        }
        if self._save_json(config_path, config):
            return True, config_path
        return False, None

    def set_baseline(self, feature_name: str, commit: Optional[str] = None) -> bool:
        """
        Set baseline timestamp and commit for a feature.

        Args:
            feature_name: Feature name
            commit: Optional commit SHA (defaults to HEAD)

        Returns:
            True if successful
        """
        feature_dir = self.get_feature_dir(feature_name)
        if not feature_dir:
            return False

        # Ensure config exists
        self.ensure_config(feature_name)

        config_path = feature_dir / "config.json"
        config = self._load_json(config_path)

        # Get current HEAD if no commit specified
        if not commit:
            result = self._run_git(['rev-parse', 'HEAD'])
            if result['success']:
                commit = result['output'].strip()

        # Set baseline
        config['baseline'] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'commit': commit
        }

        return self._save_json(config_path, config)

    def add_watch_path(self, feature_name: str, path: str) -> bool:
        """
        Add a path to the feature's watch list.

        Args:
            feature_name: Feature name
            path: Glob pattern to watch

        Returns:
            True if successful
        """
        feature_dir = self.get_feature_dir(feature_name)
        if not feature_dir:
            return False

        self.ensure_config(feature_name)

        config_path = feature_dir / "config.json"
        config = self._load_json(config_path)

        if 'watch' not in config:
            config['watch'] = {'paths': [], 'exclude': []}

        if path not in config['watch']['paths']:
            config['watch']['paths'].append(path)

        return self._save_json(config_path, config)


def create_feature_config(feature_dir: Path, watch_paths: Optional[List[str]] = None) -> bool:
    """
    Create initial config.json for a feature.

    Args:
        feature_dir: Path to feature directory
        watch_paths: Optional initial watch paths

    Returns:
        True if successful
    """
    config = {
        "watch": {
            "paths": watch_paths or [],
            "exclude": []
        },
        "baseline": {}
    }

    config_path = feature_dir / "config.json"
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except OSError as e:
        print(f"Error creating config.json: {e}")
        return False
