#!/usr/bin/env python3
"""
graph-builder.py - Convert codemap.json to code-graph.json

Takes the structured output from ast-grep scanning and builds a proper
code-graph.json with:
- module entities
- package entities (from directory structure)
- class entities (optional, for OOP codebases)
- dependencies in graph section
- references (product-component, data-models, etc.)

Usage: python graph-builder.py codemap.json [--output code-graph.json]
"""

import argparse
import json
import re
from pathlib import Path
from collections import defaultdict


def slugify(name: str) -> str:
    """Convert name to kebab-case slug."""
    # Handle camelCase and PascalCase
    s = re.sub(r'([a-z])([A-Z])', r'\1-\2', name)
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s)
    return s.lower().strip('-')


def path_to_module_key(path: str) -> str:
    """Convert file path to module key."""
    # Remove extension and convert to kebab-case
    stem = Path(path).stem
    if stem in ('index', '__init__', 'main'):
        # Use parent directory name
        parent = Path(path).parent.name
        if parent and parent != '.':
            stem = parent
    return slugify(stem)


def path_to_package_key(path: str) -> str:
    """Convert directory path to package key."""
    parts = Path(path).parent.parts
    if not parts or parts == ('.',):
        return 'root'
    return slugify('-'.join(parts))


PYTHON_STDLIB = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'base64',
    'bdb', 'binascii', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
    'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections', 'colorsys',
    'compileall', 'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy',
    'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses',
    'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'doctest', 'email', 'encodings',
    'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch',
    'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob',
    'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'idlelib',
    'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
    'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox',
    'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'multiprocessing',
    'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
    'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib',
    'poplib', 'posix', 'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile',
    'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'resource',
    'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex',
    'shutil', 'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver',
    'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
    'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny', 'tarfile',
    'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading', 'time', 'timeit',
    'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
    'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid',
    'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref',
    'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', '_thread'
}

def extract_import_module(imp: dict, lang: str) -> tuple[str | None, str]:
    """Extract the module being imported and its category.

    Returns: (module_name, category) where category is 'stdlib', 'relative', or 'external'
    """
    name = imp.get('name', '')

    if lang == 'python':
        if name.startswith('.'):
            return None, 'relative'  # Relative import
        top_level = name.split('.')[0]
        if top_level in PYTHON_STDLIB:
            return None, 'stdlib'  # Skip stdlib
        return top_level, 'external'

    # TypeScript: check if local or node_modules
    if lang in ('typescript', 'javascript'):
        if name.startswith('.') or name.startswith('/'):
            return None, 'relative'
        if name.startswith('@'):
            # Scoped package like @types/node
            return name.split('/')[0] + '/' + name.split('/')[1] if '/' in name else name, 'external'
        return name.split('/')[0], 'external'

    return None, 'unknown'


def build_graph(codemap: dict, options: dict) -> dict:
    """Build code-graph.json from codemap."""

    lang = codemap.get('language', 'unknown')
    modules = codemap.get('modules', [])
    schemas = codemap.get('schemas', [])
    imports = codemap.get('imports', [])

    # Initialize graph structure
    graph = {
        "entities": {
            "module": {},
            "package": {}
        },
        "references": {
            "data-models": {},
            "external-dep": {}
        },
        "graph": {},
        "meta": {
            "name": options.get('name', 'Code Graph'),
            "description": f"Auto-generated from {lang} codebase",
            "generated_from": "codemap.json"
        }
    }

    # Track packages (directories)
    packages = set()
    module_to_package = {}
    module_dependencies = defaultdict(set)

    # Process each file as a module
    for mod in modules:
        path = mod['path']
        mod_key = path_to_module_key(path)
        pkg_key = path_to_package_key(path)

        # Avoid duplicate keys
        if mod_key in graph['entities']['module']:
            # Append path hash
            mod_key = f"{mod_key}-{hash(path) % 1000:03d}"

        packages.add(pkg_key)
        module_to_package[mod_key] = pkg_key

        # Build module entity
        classes = [c['name'] for c in mod.get('classes', [])]
        functions = [f['name'] for f in mod.get('functions', [])]
        exports = [e['name'] for e in mod.get('exports', [])]

        graph['entities']['module'][mod_key] = {
            "name": Path(path).stem,
            "description": f"Module at {path}",
            "file": path,
            "classes": classes if classes else None,
            "functions": functions if functions else None,
            "exports": exports if exports else None
        }

        # Clean up None values
        graph['entities']['module'][mod_key] = {
            k: v for k, v in graph['entities']['module'][mod_key].items() if v is not None
        }

        # Track import dependencies
        for imp in mod.get('imports', []):
            imp_module, category = extract_import_module(imp, lang)
            if imp_module and category == 'external':
                ext_key = slugify(imp_module)
                graph['references']['external-dep'][ext_key] = {
                    "name": imp_module,
                    "type": "library"
                }
                module_dependencies[mod_key].add(f"external-dep:{ext_key}")

    # Add package entities
    for pkg_key in sorted(packages):
        if pkg_key == 'root':
            continue
        graph['entities']['package'][pkg_key] = {
            "name": pkg_key.replace('-', '/'),
            "description": f"Package directory"
        }

    # Process schemas into data-models references
    schema_types_map = {
        'interface': 'interface',
        'type': 'type-alias',
        'dataclass': 'dataclass',
        'pydantic': 'pydantic-model',
        'typeddict': 'typed-dict',
        'namedtuple': 'named-tuple',
        'enum': 'enum',
        'zod': 'zod-schema',
        'const-enum': 'const-enum'
    }

    for schema in schemas:
        name = schema.get('name', 'Unknown')
        schema_type = schema.get('schema_type', 'unknown')
        file_path = schema.get('file', '')

        key = slugify(name)
        if key in graph['references']['data-models']:
            key = f"{key}-{slugify(schema_type)}"

        graph['references']['data-models'][key] = {
            "name": name,
            "type": schema_types_map.get(schema_type, schema_type),
            "file": file_path
        }

    # Build dependency graph
    for mod_key, pkg_key in module_to_package.items():
        deps = list(module_dependencies.get(mod_key, []))

        # Add package dependency
        if pkg_key != 'root' and pkg_key in graph['entities']['package']:
            deps.append(f"package:{pkg_key}")

        if deps:
            graph['graph'][f"module:{mod_key}"] = {
                "depends_on": deps
            }

    # Add package to package dependencies (parent directories)
    for pkg_key in sorted(packages):
        if pkg_key == 'root':
            continue
        parts = pkg_key.split('-')
        if len(parts) > 1:
            parent = '-'.join(parts[:-1])
            if parent in packages and parent != 'root':
                if f"package:{pkg_key}" not in graph['graph']:
                    graph['graph'][f"package:{pkg_key}"] = {"depends_on": []}
                graph['graph'][f"package:{pkg_key}"]["depends_on"].append(f"package:{parent}")

    return graph


def main():
    parser = argparse.ArgumentParser(description='Build code-graph.json from codemap.json')
    parser.add_argument('codemap', help='Path to codemap.json')
    parser.add_argument('--output', '-o', default='.ai/know/code-graph.json', help='Output path')
    parser.add_argument('--name', default='Code Graph', help='Graph name')
    parser.add_argument('--merge', action='store_true', help='Merge with existing code-graph.json')

    args = parser.parse_args()

    # Load codemap
    with open(args.codemap, 'r') as f:
        codemap = json.load(f)

    print(f"Processing codemap: {codemap.get('stats', {})}")

    # Build graph
    graph = build_graph(codemap, {'name': args.name})

    # Optionally merge with existing
    if args.merge and Path(args.output).exists():
        with open(args.output, 'r') as f:
            existing = json.load(f)

        # Merge entities
        for entity_type, entities in graph['entities'].items():
            if entity_type not in existing['entities']:
                existing['entities'][entity_type] = {}
            existing['entities'][entity_type].update(entities)

        # Merge references
        for ref_type, refs in graph['references'].items():
            if ref_type not in existing.get('references', {}):
                if 'references' not in existing:
                    existing['references'] = {}
                existing['references'][ref_type] = {}
            existing['references'][ref_type].update(refs)

        # Merge graph
        existing['graph'].update(graph['graph'])

        graph = existing
        print(f"Merged with existing {args.output}")

    # Write output
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(graph, f, indent=2)

    print(f"Wrote: {args.output}")
    print(f"  Modules: {len(graph['entities'].get('module', {}))}")
    print(f"  Packages: {len(graph['entities'].get('package', {}))}")
    print(f"  Data models: {len(graph['references'].get('data-models', {}))}")
    print(f"  External deps: {len(graph['references'].get('external-dep', {}))}")


if __name__ == '__main__':
    main()
