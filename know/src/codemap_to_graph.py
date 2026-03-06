"""
Generate code-graph from codemap AST parsing.

This module transforms codemap.json (AST parsing output) into code-graph.json
while preserving manually curated references (product-component, external-dep).
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class CodeGraphGenerator:
    """Generate code-graph entities from codemap AST data."""

    def __init__(self, source_dir: Optional[str] = None):
        """
        Initialize code-graph generator.

        Args:
            source_dir: Source directory path for file path resolution.
                        If None, reads from codemap.json "source" field.
        """
        self.source_dir = source_dir

    def generate_from_codemap(
        self,
        codemap_path: str,
        existing_graph_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate code-graph from codemap with reference preservation.

        Args:
            codemap_path: Path to codemap.json
            existing_graph_path: Path to existing code-graph.json (to preserve refs)
            output_path: Optional output path to write generated graph

        Returns:
            Generated code-graph dictionary
        """
        # Load codemap
        with open(codemap_path) as f:
            codemap = json.load(f)

        # Auto-read source dir from codemap when not explicitly provided
        if self.source_dir is None:
            source_field = codemap.get("source", "src")
            if isinstance(source_field, list):
                # Multiple source dirs - use first as primary
                self.source_dir = source_field[0] if source_field else "src"
                self._source_dirs = source_field
            else:
                self.source_dir = source_field
                self._source_dirs = [source_field]
        else:
            self._source_dirs = [self.source_dir]

        # Load existing graph for reference preservation
        existing_refs = {}
        if existing_graph_path and Path(existing_graph_path).exists():
            with open(existing_graph_path) as f:
                existing = json.load(f)
                existing_refs = existing.get('references', {})

        # Initialize code-graph structure
        code_graph = {
            "meta": {
                "version": "1.0.0",
                "project": {
                    "name": "know-cli",
                    "language": codemap.get('language', 'python'),
                    "architecture": "cli-tool"
                },
                "phases": {}
            },
            "references": {
                "external-dep": {},
                "product-component": {}
            },
            "entities": {
                "module": {},
                "class": {},
                "function": {}
            },
            "graph": {}
        }

        # PRESERVE: Copy existing product-component references (manual curation)
        if 'product-component' in existing_refs:
            code_graph['references']['product-component'] = existing_refs['product-component']

        # PRESERVE: Copy existing external-dep references
        if 'external-dep' in existing_refs:
            code_graph['references']['external-dep'] = existing_refs['external-dep']

        # GENERATE: Entities from codemap modules
        self._generate_entities(codemap, code_graph)

        # GENERATE: Import dependency graph
        self._generate_import_graph(codemap, code_graph)

        # MERGE: Detect and add new external deps from imports
        self._merge_external_deps(codemap, code_graph)

        # Write to file if output path specified
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(code_graph, f, indent=2)

        return code_graph

    def _generate_entities(self, codemap: Dict, code_graph: Dict) -> None:
        """Generate module, class, and function entities from codemap."""
        modules = codemap.get('modules', [])

        for module in modules:
            module_path = module.get('path', '')
            if not module_path:
                continue

            # Skip __init__.py for now (or handle specially)
            if module_path == '__init__.py':
                continue

            # Module entity
            module_name = module_path.replace('.py', '')
            module_id = module_name.replace('/', '.')

            resolved_dir = self._resolve_source_dir(module_path)
            code_graph['entities']['module'][module_id] = {
                "name": self._format_name(module_id),
                "description": f"Module at {resolved_dir}/{module_path}",
                "file_path": f"{resolved_dir}/{module_path}"
            }

            # Class entities
            for cls in module.get('classes', []):
                class_name = cls.get('name')
                if not class_name:
                    continue

                class_id = f"{module_id}.{class_name}"
                code_graph['entities']['class'][class_id] = {
                    "name": class_name,
                    "description": f"Class in {module_path}",
                    "file_path": f"{resolved_dir}/{module_path}",
                    "line": cls.get('line')
                }

                # Link class → module
                graph_key = f"class:{class_id}"
                if graph_key not in code_graph['graph']:
                    code_graph['graph'][graph_key] = {"depends_on": []}
                code_graph['graph'][graph_key]['depends_on'].append(f"module:{module_id}")

            # Function entities (top-level functions only, not methods)
            for func in module.get('functions', []):
                func_name = func.get('name')
                if not func_name or func_name.startswith('_'):  # Skip private functions
                    continue

                func_id = f"{module_id}.{func_name}"
                code_graph['entities']['function'][func_id] = {
                    "name": func_name,
                    "description": f"Function in {module_path}",
                    "file_path": f"{resolved_dir}/{module_path}",
                    "line": func.get('line')
                }

                # Link function → module
                graph_key = f"function:{func_id}"
                if graph_key not in code_graph['graph']:
                    code_graph['graph'][graph_key] = {"depends_on": []}
                code_graph['graph'][graph_key]['depends_on'].append(f"module:{module_id}")

    def _generate_import_graph(self, codemap: Dict, code_graph: Dict) -> None:
        """Generate module dependency graph from imports."""
        modules = codemap.get('modules', [])

        for module in modules:
            module_path = module.get('path', '')
            if not module_path or module_path == '__init__.py':
                continue

            module_name = module_path.replace('.py', '').replace('/', '.')
            graph_key = f"module:{module_name}"

            if graph_key not in code_graph['graph']:
                code_graph['graph'][graph_key] = {"depends_on": []}

            # Parse imports
            for imp in module.get('imports', []):
                import_name = imp.get('name', '')
                if not import_name:
                    continue

                # Relative imports (internal modules)
                if import_name.startswith('.'):
                    # Convert relative to absolute within project
                    imported_module = self._resolve_relative_import(
                        module_name, import_name
                    )
                    if imported_module:
                        dep_key = f"module:{imported_module}"
                        if dep_key not in code_graph['graph'][graph_key]['depends_on']:
                            code_graph['graph'][graph_key]['depends_on'].append(dep_key)
                else:
                    # External imports - track as external-dep reference
                    # Extract root package name (e.g., "rich.console" → "rich")
                    root_package = import_name.split('.')[0]
                    if root_package not in ['typing', 'pathlib', 'json', 'os', 'sys']:
                        # Link to external-dep reference
                        ext_dep_key = f"external-dep:{root_package}"
                        if ext_dep_key not in code_graph['graph'][graph_key]['depends_on']:
                            code_graph['graph'][graph_key]['depends_on'].append(ext_dep_key)

    def _merge_external_deps(self, codemap: Dict, code_graph: Dict) -> None:
        """Detect external deps from imports and merge with existing."""
        # Collect all external imports from modules
        detected_deps = set()
        modules = codemap.get('modules', [])

        for module in modules:
            for imp in module.get('imports', []):
                import_name = imp.get('name', '')
                if import_name and not import_name.startswith('.'):
                    # Extract root package
                    root_package = import_name.split('.')[0]
                    # Skip stdlib
                    if root_package not in ['typing', 'pathlib', 'json', 'os', 'sys',
                                           'collections', 'dataclasses', 're', 'datetime',
                                           'functools', 'itertools', 'subprocess', 'shutil',
                                           'xml', 'io', 'tempfile', 'asyncio', 'time']:
                        detected_deps.add(root_package)

        # Add detected deps that aren't already documented
        existing_deps = code_graph['references']['external-dep']
        for dep in detected_deps:
            if dep not in existing_deps:
                existing_deps[dep] = {
                    "identifier": f"pypi:{dep}",
                    "version": "auto-detected",
                    "type": "pypi",
                    "purpose": "TODO: Document purpose",
                    "detected": True
                }

    def _resolve_relative_import(self, from_module: str, relative_import: str) -> Optional[str]:
        """
        Resolve relative import to absolute module name.

        Args:
            from_module: Current module name (e.g., "generators")
            relative_import: Relative import (e.g., ".graph", "..utils")

        Returns:
            Absolute module name or None
        """
        # Count leading dots
        level = 0
        for char in relative_import:
            if char == '.':
                level += 1
            else:
                break

        # Get the rest of the import
        import_tail = relative_import[level:]

        # Resolve
        if level == 1:
            # Same directory: .graph → graph
            return import_tail if import_tail else from_module
        elif level == 2:
            # Parent directory
            # For now, simplify - assume flat structure
            return import_tail if import_tail else None
        else:
            return None

    def _resolve_source_dir(self, module_path: str) -> str:
        """Resolve which source directory contains the given module path."""
        if hasattr(self, '_source_dirs') and len(self._source_dirs) > 1:
            for src_dir in self._source_dirs:
                if Path(f"{src_dir}/{module_path}").exists():
                    return src_dir
        return self.source_dir

    def _format_name(self, module_id: str) -> str:
        """Format module ID into human-readable name."""
        # generators → Generators
        # graph_operations → Graph Operations
        words = module_id.replace('_', ' ').replace('.', ' ').split()
        return ' '.join(word.capitalize() for word in words)


def load_codemap(path: str) -> Dict[str, Any]:
    """Load codemap JSON file."""
    with open(path) as f:
        return json.load(f)


def load_code_graph(path: str) -> Dict[str, Any]:
    """Load code-graph JSON file."""
    with open(path) as f:
        return json.load(f)
