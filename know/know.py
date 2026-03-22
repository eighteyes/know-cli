#!/usr/bin/env python3
"""
Know Tool - Python implementation for efficient graph operations
Command-line interface for managing the specification graph

Responsibilities:
- CLI entry point and command group definitions
- Command routing to underlying managers
- Rich console output formatting
"""

import sys
import json
import click
import shutil
import subprocess
import tempfile
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint

from src import (
    GraphManager, EntityManager, DependencyManager,
    GraphValidator, SpecGenerator, GraphDiff,
    RulesDiffAnalyzer, get_graph_stats
)
from src.workflow import WorkflowManager


console = Console()


def suggest_did_you_mean(graph_data, query, include_refs=True):
    """Print 'did you mean?' suggestions for a failed node lookup."""
    from src.utils import find_fuzzy_match

    candidates = []
    for etype, elist in graph_data.get('entities', {}).items():
        if isinstance(elist, dict):
            candidates.extend(f"{etype}:{k}" for k in elist)
    if include_refs:
        for rtype, rlist in graph_data.get('references', {}).items():
            if isinstance(rlist, dict):
                candidates.extend(f"{rtype}:{k}" for k in rlist)

    # Match against full ID and also just the key portion
    query_key = query.split(':', 1)[1] if ':' in query else query
    matches = find_fuzzy_match(query, candidates, threshold=3)
    if not matches:
        matches = find_fuzzy_match(query_key, [c.split(':', 1)[1] for c in candidates], threshold=2)
        # Map back to full IDs
        if matches:
            key_to_ids = {}
            for c in candidates:
                key_to_ids.setdefault(c.split(':', 1)[1], []).append(c)
            matches = [cid for m in matches for cid in key_to_ids.get(m, [])]

    if matches:
        console.print("[yellow]  Did you mean:[/yellow]")
        for m in matches[:5]:
            console.print(f"[yellow]    {m}[/yellow]")


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class SectionedGroup(click.Group):
    """Click Group that organizes commands into sections."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.section_commands = {
            'Initialization': ['init'],
            'Graph': ['add', 'get', 'list', 'search', 'find', 'related', 'link', 'unlink', 'graph', 'check', 'gen', 'nodes', 'viz'],
            'Project': ['feature', 'phases', 'req', 'op', 'meta', 'serve'],
        }

    def format_commands(self, ctx, formatter):
        """Custom command formatting with sections."""
        # Organize commands by section
        sections = {}
        unassigned = []

        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None:
                continue

            # Find which section this command belongs to
            found = False
            for section, commands in self.section_commands.items():
                if name in commands:
                    if section not in sections:
                        sections[section] = []
                    sections[section].append((name, cmd))
                    found = True
                    break

            if not found:
                unassigned.append((name, cmd))

        # Format sections
        for section in ['Initialization', 'Graph', 'Project']:
            if section in sections:
                with formatter.section(section):
                    self._format_command_list(formatter, sections[section])

        # Add unassigned commands if any
        if unassigned:
            with formatter.section('Other Commands'):
                self._format_command_list(formatter, unassigned)

    def _format_command_list(self, formatter, commands):
        """Format a list of commands."""
        rows = []
        for name, cmd in commands:
            help_text = cmd.get_short_help_str(limit=60)
            rows.append((name, help_text))

        if rows:
            formatter.write_dl(rows)


def _get_type_category(rules_path: str, type_name: str) -> str:
    """Determine if a type is an entity or reference based on rules.

    Returns: 'entity', 'reference', or 'unknown'
    """
    with open(rules_path, 'r') as f:
        rules = json.load(f)

    entity_types = set(rules.get('entity_description', {}).keys())
    reference_types = set(rules.get('reference_dependency_rule', {}).get('reference_types', []))

    if type_name in entity_types:
        return 'entity'
    elif type_name in reference_types:
        return 'reference'
    return 'unknown'


@click.command(cls=SectionedGroup, context_settings=CONTEXT_SETTINGS)
@click.option('--graph-path', '-g', default='.ai/know/spec-graph.json',
              help='Path to graph file')
@click.option('--rules-path', '-r', default=None,
              help='Path to dependency rules file (auto-detects based on graph name if not specified)')
@click.pass_context
def cli(ctx, graph_path, rules_path):
    """Know Tool - Manage specification graph efficiently"""
    # Ensure parent path exists, adjust for running from know_python dir
    graph_path = Path(graph_path)
    if not graph_path.is_absolute():
        # Check if we're in know_python dir and adjust path
        if Path.cwd().name == 'know_python':
            graph_path = Path('..') / graph_path

    # Auto-detect rules path based on graph name if not specified
    # Prefer local project copy (.ai/know/config/), fall back to package config
    if rules_path is None:
        local_config_dir = Path('.ai/know/config')
        package_config_dir = Path(__file__).parent / "config"
        if 'code-graph' in str(graph_path):
            rules_file = "code-dependency-rules.json"
        else:
            rules_file = "dependency-rules.json"
        local_rules = local_config_dir / rules_file
        rules_path = str(local_rules) if local_rules.exists() else str(package_config_dir / rules_file)

    ctx.ensure_object(dict)
    ctx.obj['graph'] = GraphManager(str(graph_path))
    ctx.obj['rules_path'] = rules_path
    ctx.obj['entities'] = EntityManager(ctx.obj['graph'], rules_path=rules_path)
    ctx.obj['deps'] = DependencyManager(ctx.obj['graph'], rules_path=rules_path)
    ctx.obj['validator'] = GraphValidator(ctx.obj['graph'], rules_path=rules_path)
    ctx.obj['generator'] = SpecGenerator(
        ctx.obj['graph'],
        ctx.obj['entities'],
        ctx.obj['deps']
    )
    ctx.obj['workflow'] = WorkflowManager(ctx.obj['graph'], ctx.obj['entities'])


# =============================================================================
# ADD command - Unified add for entities and references (auto-detects)
# =============================================================================
@cli.command(name='add')
@click.argument('type_name')
@click.argument('keys', nargs=-1, required=True)
@click.option('--json-file', '-f', help='Read data from JSON file')
@click.option('--skip-validation', is_flag=True, help='Skip validation (entities only)')
@click.pass_context
def add_item(ctx, type_name, keys, json_file, skip_validation):
    """Add one or more entities or references to the graph (auto-detects based on type)

    For a single item, trailing JSON is treated as inline data (backward compat).
    For multiple items, all share the same data (from --json-file or empty).

    Examples:
        know add feature auth '{"name":"Auth","description":"User authentication"}'
        know add feature auth dashboard profile
        know add component login-form '{"name":"Login Form"}'
        know add -f entity.json feature analytics
    """
    # Detect trailing inline JSON arg (backward compat for single-item case)
    inline_data = None
    if keys and keys[-1].strip().startswith('{'):
        try:
            inline_data = json.loads(keys[-1])
            keys = keys[:-1]
        except json.JSONDecodeError:
            pass  # Not JSON, treat as a key

    if not keys:
        console.print("[red]✗ No keys provided[/red]")
        sys.exit(1)

    # Parse shared data
    if json_file:
        with open(json_file, 'r') as f:
            item_data = json.load(f)
    elif inline_data is not None:
        item_data = inline_data
    else:
        item_data = {}

    # Determine if entity or reference
    category = _get_type_category(ctx.obj['rules_path'], type_name)

    if category not in ('entity', 'reference'):
        console.print(f"[red]✗ Unknown type '{type_name}'[/red]")
        console.print(f"[dim]Use 'know gen rules describe entities' to list entity types[/dim]")
        console.print(f"[dim]Use 'know gen rules describe references' to list reference types[/dim]")
        sys.exit(1)

    failed = False

    for key in keys:
        if category == 'entity':
            success, error = ctx.obj['entities'].add_entity(
                type_name, key, item_data, skip_validation=skip_validation
            )
            if success:
                console.print(f"[green]✓ Added entity '{type_name}:{key}'[/green]")
            else:
                console.print(f"[red]✗ Failed to add entity '{type_name}:{key}': {error}[/red]")
                failed = True

        else:  # reference
            graph_data = ctx.obj['graph'].load()
            if 'references' not in graph_data:
                graph_data['references'] = {}
            if type_name not in graph_data['references']:
                graph_data['references'][type_name] = {}

            if key in graph_data['references'][type_name]:
                console.print(f"[red]✗ Reference '{type_name}:{key}' already exists[/red]")
                failed = True
                continue

            graph_data['references'][type_name][key] = item_data
            ctx.obj['graph'].save_graph(graph_data)
            console.print(f"[green]✓ Added reference '{type_name}:{key}'[/green]")

    if failed:
        sys.exit(1)


# =============================================================================
# META group - Get/set meta sections
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def meta(ctx):
    """Get, set, and delete meta sections (project, phases, decisions, etc.)"""
    pass


@meta.command(name='get')
@click.argument('section')
@click.argument('key', required=False)
@click.pass_context
def meta_get(ctx, section, key):
    """Get meta section or specific key

    Examples:
        know meta get project              # Show all project meta
        know meta get project name         # Show specific key
        know meta get phases               # Show all phases
        know meta get decisions            # Show all decisions
    """
    graph_data = ctx.obj['graph'].load()

    if 'meta' not in graph_data:
        console.print("[yellow]No meta section in graph[/yellow]")
        return

    if section not in graph_data['meta']:
        console.print(f"[yellow]No '{section}' section in meta[/yellow]")
        return

    section_data = graph_data['meta'][section]

    if key:
        if key not in section_data:
            console.print(f"[yellow]Key '{key}' not found in meta.{section}[/yellow]")
            return
        console.print(f"\n[bold cyan]meta.{section}.{key}[/bold cyan]")
        rprint(section_data[key])
    else:
        console.print(f"\n[bold cyan]meta.{section}[/bold cyan]")
        rprint(section_data)


@meta.command(name='set')
@click.argument('section')
@click.argument('key')
@click.argument('data', required=False)
@click.option('--json-file', '-f', help='Read data from JSON file')
@click.pass_context
def meta_set(ctx, section, key, data, json_file):
    """Set a meta section key

    Examples:
        know meta set project name "My Project"
        know meta set decisions auth-approach '{"title":"JWT vs Sessions"}'
        know meta set assumptions user-volume '{"description":"<1000 concurrent users"}'
        know meta set -f decision.json decisions caching
    """
    # Parse data
    if json_file:
        with open(json_file, 'r') as f:
            meta_data = json.load(f)
    elif data:
        try:
            meta_data = json.loads(data)
        except (json.JSONDecodeError, ValueError):
            meta_data = data
    else:
        meta_data = {}

    # Load graph and set meta
    graph_data = ctx.obj['graph'].load()

    if 'meta' not in graph_data:
        graph_data['meta'] = {}

    if section not in graph_data['meta']:
        graph_data['meta'][section] = {}
    elif not isinstance(graph_data['meta'][section], dict):
        old_val = graph_data['meta'][section]
        graph_data['meta'][section] = {'_previous': old_val}
        console.print(f"[yellow]⚠ meta.{section} was a bare value ({old_val!r}), promoted to dict[/yellow]")

    # Check if overwriting
    if key in graph_data['meta'][section]:
        console.print(f"[yellow]⚠ Overwriting meta.{section}.{key}[/yellow]")

    graph_data['meta'][section][key] = meta_data
    ctx.obj['graph'].save_graph(graph_data)

    console.print(f"[green]✓ Set meta.{section}.{key}[/green]")


@meta.command(name='delete')
@click.argument('section')
@click.argument('key')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def meta_delete(ctx, section, key, yes):
    """Delete a key from a meta section

    Examples:
        know meta delete phases I                    # Delete phase I
        know meta delete requirements auth-login     # Delete requirement
        know meta delete deprecated component:old    # Undeprecate entity
        know meta delete decisions caching-approach  # Delete decision
        know meta delete phases II -y                # Skip confirmation
    """
    graph_data = ctx.obj['graph'].load()

    # Check if section exists
    if 'meta' not in graph_data:
        console.print("[yellow]No meta section in graph[/yellow]")
        return

    if section not in graph_data['meta']:
        console.print(f"[yellow]No '{section}' section in meta[/yellow]")
        return

    # Check if key exists
    if key not in graph_data['meta'][section]:
        console.print(f"[yellow]Key '{key}' not found in meta.{section}[/yellow]")
        return

    # Show what will be deleted
    console.print(f"\n[bold]Deleting meta.{section}.{key}:[/bold]")
    rprint(graph_data['meta'][section][key])
    console.print()

    # Confirm deletion
    if not yes:
        if not click.confirm(f"Delete meta.{section}.{key}?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Delete the key
    del graph_data['meta'][section][key]

    # If section is now empty, optionally remove it
    if not graph_data['meta'][section]:
        console.print(f"[dim]Section '{section}' is now empty[/dim]")
        if yes or click.confirm(f"Remove empty section meta.{section}?"):
            del graph_data['meta'][section]
            console.print(f"[green]✓ Deleted meta.{section}.{key} and removed empty section[/green]")
        else:
            # Save with empty section
            ctx.obj['graph'].save_graph(graph_data)
            console.print(f"[green]✓ Deleted meta.{section}.{key} (kept empty section)[/green]")
    else:
        # Save graph
        ctx.obj['graph'].save_graph(graph_data)
        console.print(f"[green]✓ Deleted meta.{section}.{key}[/green]")


# =============================================================================
# TOP-LEVEL GET command
# =============================================================================
@cli.command(name='get')
@click.argument('path')
@click.pass_context
def get_item(ctx, path):
    """Get details of an entity or reference

    Auto-detects whether the path refers to an entity or reference
    based on the type prefix.

    Examples:
        know get feature:auth              # Entity
        know get business_logic:login      # Reference
        know get component:login-form      # Entity
        know -g .ai/know/code-graph.json get module:graph
    """
    if ':' not in path:
        console.print(f"[red]Invalid path '{path}'. Use format: type:key[/red]")
        sys.exit(1)

    type_name = path.split(':', 1)[0]
    category = _get_type_category(ctx.obj['rules_path'], type_name)

    if category == 'entity':
        e = ctx.obj['entities'].get_entity(path)
        if not e:
            console.print(f"[red]Entity '{path}' not found[/red]")
            suggest_did_you_mean(ctx.obj['graph'].load(), path)
            sys.exit(1)
        console.print(f"\n[bold cyan]{path}[/bold cyan]")
        rprint(e)

    elif category == 'reference':
        ref_type, ref_key = path.split(':', 1)
        graph_data = ctx.obj['graph'].load()
        refs = graph_data.get('references', {})

        if ref_type not in refs or ref_key not in refs[ref_type]:
            console.print(f"[red]Reference '{path}' not found[/red]")
            suggest_did_you_mean(graph_data, path)
            sys.exit(1)

        console.print(f"\n[bold cyan]{path}[/bold cyan]")
        rprint(refs[ref_type][ref_key])

    else:
        console.print(f"[red]Unknown type '{type_name}'. Check dependency rules.[/red]")
        sys.exit(1)


# =============================================================================
# TOP-LEVEL LIST command
# =============================================================================
@cli.command(name='list')
@click.option('--type', '-t', 'type_filter', default=None, help='Filter by type (entity or reference)')
@click.pass_context
def list_items(ctx, type_filter):
    """List entities and references, optionally filtered by type

    Auto-detects whether the type is an entity or reference type.

    Examples:
        know list                          # All entities and references
        know list --type feature           # Entity type
        know list -t business_logic        # Reference type
        know -g .ai/know/code-graph.json list --type module
    """
    graph_data = ctx.obj['graph'].load()

    if type_filter:
        category = _get_type_category(ctx.obj['rules_path'], type_filter)

        if category == 'entity':
            entities = ctx.obj['entities'].list_entities(type_filter)
            if not entities:
                console.print(f"[yellow]No entities of type '{type_filter}' found[/yellow]")
                return

            table = Table(title=f"{type_filter.capitalize()} Entities",
                          show_header=True, header_style="bold magenta")
            table.add_column("Key", style="green")

            for e in sorted(entities):
                table.add_row(e.split(':', 1)[1])

            console.print(table)

        elif category == 'reference':
            refs = graph_data.get('references', {}).get(type_filter, {})
            if not refs:
                console.print(f"[yellow]No references of type '{type_filter}' found[/yellow]")
                return

            table = Table(title=f"{type_filter} References",
                          show_header=True, header_style="bold magenta")
            table.add_column("Key", style="green")

            for key in sorted(refs.keys()):
                table.add_row(key)

            console.print(table)

        else:
            console.print(f"[red]Unknown type '{type_filter}'. Check dependency rules.[/red]")
            sys.exit(1)
        return

    # No filter - show all entities and references
    entities = ctx.obj['entities'].list_entities()
    refs = graph_data.get('references', {})

    # Group entities by type
    entity_by_type = {}
    for e in entities:
        etype = e.split(':')[0]
        if etype not in entity_by_type:
            entity_by_type[etype] = []
        entity_by_type[etype].append(e)

    # Display entities
    if entity_by_type:
        table = Table(title="Entities", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Key", style="green")
        table.add_column("Count", justify="right", style="yellow")

        for etype, items in sorted(entity_by_type.items()):
            for i, item in enumerate(sorted(items)):
                if i == 0:
                    table.add_row(etype, item.split(':', 1)[1], str(len(items)))
                else:
                    table.add_row("", item.split(':', 1)[1], "")

        console.print(table)
    else:
        console.print("[yellow]No entities found[/yellow]")

    # Display references
    if refs:
        console.print()
        table = Table(title="References", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Key", style="green")
        table.add_column("Count", justify="right", style="yellow")

        for rtype in sorted(refs.keys()):
            items = refs[rtype]
            keys = sorted(items.keys())
            for i, key in enumerate(keys):
                if i == 0:
                    table.add_row(rtype, key, str(len(keys)))
                else:
                    table.add_row("", key, "")

        console.print(table)


@cli.command(name='search')
@click.argument('pattern')
@click.option('--regex', '-r', is_flag=True, help='Treat pattern as regex')
@click.option('--case-sensitive', '-c', is_flag=True, help='Case-sensitive search')
@click.option('--section', '-s', type=click.Choice(['entities', 'references', 'meta', 'all']),
              default='all', help='Section to search')
@click.option('--field', '-f', help='Specific field to search (name, description, etc.)')
@click.pass_context
def search(ctx, pattern, regex, case_sensitive, section, field):
    """Search through all text content in the graph

    Searches entity names, descriptions, and all text fields in the graph.
    Supports plain text and regex patterns.

    Examples:
        know search "authentication"              # Plain text search
        know search "auth.*login" --regex         # Regex search
        know search "API" --section references    # Search only references
        know search "user" --field description    # Search only descriptions
        know search "Feature.*" -rc               # Regex, case-sensitive
    """
    import re

    graph_data = ctx.obj['graph'].load()

    # Compile pattern
    if regex:
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            compiled_pattern = re.compile(pattern, flags)
        except re.error as e:
            console.print(f"[red]✗ Invalid regex pattern: {e}[/red]")
            sys.exit(1)
    else:
        # Plain text search - escape regex special chars and use simple match
        if case_sensitive:
            compiled_pattern = re.compile(re.escape(pattern))
        else:
            compiled_pattern = re.compile(re.escape(pattern), re.IGNORECASE)

    results = {'entities': [], 'references': [], 'meta': []}

    def search_dict(data, path=""):
        """Recursively search through dictionary values"""
        matches = []
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key

                # Check if we should search this field
                if field and key != field:
                    # If field filter is set and this isn't the field, skip (unless nested)
                    if isinstance(value, (dict, list)):
                        matches.extend(search_dict(value, current_path))
                    continue

                if isinstance(value, str):
                    if compiled_pattern.search(value):
                        matches.append({
                            'field': current_path,
                            'value': value,
                            'match': compiled_pattern.search(value).group(0)
                        })
                elif isinstance(value, (dict, list)):
                    matches.extend(search_dict(value, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if isinstance(item, str):
                    if compiled_pattern.search(item):
                        matches.append({
                            'field': current_path,
                            'value': item,
                            'match': compiled_pattern.search(item).group(0)
                        })
                elif isinstance(item, (dict, list)):
                    matches.extend(search_dict(item, current_path))
        return matches

    # Search entities
    if section in ['entities', 'all']:
        entities = graph_data.get('entities', {})
        for entity_type, entities_of_type in entities.items():
            for entity_key, entity_data in entities_of_type.items():
                entity_id = f"{entity_type}:{entity_key}"

                # Check entity ID itself
                if compiled_pattern.search(entity_id):
                    results['entities'].append({
                        'id': entity_id,
                        'field': 'id',
                        'value': entity_id,
                        'match': compiled_pattern.search(entity_id).group(0)
                    })

                # Search entity data
                matches = search_dict(entity_data)
                for match in matches:
                    results['entities'].append({
                        'id': entity_id,
                        'field': match['field'],
                        'value': match['value'],
                        'match': match['match']
                    })

    # Search references
    if section in ['references', 'all']:
        references = graph_data.get('references', {})
        for ref_type, refs_of_type in references.items():
            for ref_key, ref_data in refs_of_type.items():
                ref_id = f"{ref_type}:{ref_key}"

                # Check reference ID itself
                if compiled_pattern.search(ref_id):
                    results['references'].append({
                        'id': ref_id,
                        'field': 'id',
                        'value': ref_id,
                        'match': compiled_pattern.search(ref_id).group(0)
                    })

                # Search reference data
                matches = search_dict(ref_data)
                for match in matches:
                    results['references'].append({
                        'id': ref_id,
                        'field': match['field'],
                        'value': match['value'],
                        'match': match['match']
                    })

    # Search meta
    if section in ['meta', 'all']:
        meta = graph_data.get('meta', {})
        matches = search_dict(meta, 'meta')
        for match in matches:
            results['meta'].append({
                'field': match['field'],
                'value': match['value'],
                'match': match['match']
            })

    # Display results
    total_matches = sum(len(v) for v in results.values())

    if total_matches == 0:
        console.print(f"[yellow]No matches found for '{pattern}'[/yellow]")
        return

    mode = "regex" if regex else "text"
    sensitivity = "case-sensitive" if case_sensitive else "case-insensitive"
    console.print(f"\n[bold cyan]Search Results:[/bold cyan] {total_matches} matches for '{pattern}' ({mode}, {sensitivity})\n")

    # Display entities results
    if results['entities']:
        console.print(f"[bold]Entities ({len(results['entities'])} matches):[/bold]")
        for result in results['entities']:
            console.print(f"  [green]{result['id']}[/green]")
            console.print(f"    field: [cyan]{result['field']}[/cyan]")

            # Truncate long values
            value = result['value']
            if len(value) > 100:
                value = value[:100] + "..."

            # Highlight match in value
            match = result['match']
            if match in value:
                highlighted = value.replace(match, f"[yellow]{match}[/yellow]")
                console.print(f"    match: {highlighted}")
            else:
                console.print(f"    match: [yellow]{match}[/yellow]")
        console.print()

    # Display references results
    if results['references']:
        console.print(f"[bold]References ({len(results['references'])} matches):[/bold]")
        for result in results['references']:
            console.print(f"  [green]{result['id']}[/green]")
            console.print(f"    field: [cyan]{result['field']}[/cyan]")

            # Truncate long values
            value = result['value']
            if len(value) > 100:
                value = value[:100] + "..."

            # Highlight match
            match = result['match']
            if match in value:
                highlighted = value.replace(match, f"[yellow]{match}[/yellow]")
                console.print(f"    match: {highlighted}")
            else:
                console.print(f"    match: [yellow]{match}[/yellow]")
        console.print()

    # Display meta results
    if results['meta']:
        console.print(f"[bold]Meta ({len(results['meta'])} matches):[/bold]")
        for result in results['meta']:
            console.print(f"  field: [cyan]{result['field']}[/cyan]")

            # Truncate long values
            value = result['value']
            if len(value) > 100:
                value = value[:100] + "..."

            # Highlight match
            match = result['match']
            if match in value:
                highlighted = value.replace(match, f"[yellow]{match}[/yellow]")
                console.print(f"    match: {highlighted}")
            else:
                console.print(f"    match: [yellow]{match}[/yellow]")
        console.print()


@cli.command(name='find')
@click.argument('query')
@click.option('--limit', '-n', type=int, default=10, help='Maximum results to return')
@click.option('--threshold', '-t', type=float, default=0.3, help='Minimum similarity score (0-1)')
@click.option('--section', '-s', type=click.Choice(['all', 'entities', 'references']),
              default='all', help='Section to search')
@click.pass_context
def find(ctx, query, limit, threshold, section):
    """Semantic search for entities by meaning

    Uses TF-IDF to find conceptually related entities beyond exact text matches.
    More powerful than 'search' for discovering related concepts.

    Examples:
        know find "user authentication flow"
        know find "API endpoints" --limit 20
        know find "data validation" --section entities
    """
    from src import SearchIndex, SemanticSearcher

    # Initialize search index
    search_index = SearchIndex(str(ctx.obj["graph"].cache.graph_path))
    searcher = SemanticSearcher(search_index)

    # Execute search
    results = searcher.find(query, limit=limit, threshold=threshold, section=section)

    if not results:
        console.print(f"[dim]No results found for '{query}'[/dim]")
        return

    console.print(f"[bold]Found {len(results)} semantic matches:[/bold]\n")

    for result in results:
        score_pct = int(result['score'] * 100)
        console.print(f"  [green]{result['id']}[/green] [dim]({score_pct}% match)[/dim]")

        # Truncate long text
        text = result['text']
        if len(text) > 100:
            text = text[:100] + "..."
        console.print(f"    {text}")
        console.print()


@cli.command(name='related')
@click.argument('entity_id')
@click.option('--limit', '-n', type=int, default=10, help='Maximum results')
@click.pass_context
def related(ctx, entity_id, limit):
    """Find entities related to a given entity

    Discovers entities with similar descriptions and concepts.

    Examples:
        know related feature:auth
        know related component:api-client --limit 20
    """
    from src import SearchIndex, SemanticSearcher

    # Initialize search index
    search_index = SearchIndex(str(ctx.obj["graph"].cache.graph_path))
    searcher = SemanticSearcher(search_index)

    # Find related entities
    results = searcher.related(entity_id, limit=limit, include_graph_proximity=True)

    if not results:
        console.print(f"[dim]No related entities found for '{entity_id}'[/dim]")
        return

    console.print(f"[bold]Related to {entity_id}:[/bold]\n")

    for result in results:
        score_pct = int(result['score'] * 100)
        console.print(f"  [green]{result['id']}[/green] [dim]({score_pct}% similar)[/dim]")

        # Show snippet
        text = result['text']
        if len(text) > 100:
            text = text[:100] + "..."
        console.print(f"    {text}")
        console.print()



# =============================================================================
# NODES group - Node-level operations
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def nodes(ctx):
    """Node-level operations: deprecate, merge, rename, delete, cut, update, clone"""
    pass


@nodes.command(name='deprecate')
@click.argument('entity_id')
@click.option('--reason', '-r', required=True, help='Why the entity is deprecated')
@click.option('--replacement', help='Entity ID of replacement')
@click.option('--remove-by', help='Target removal date (YYYY-MM-DD)')
@click.pass_context
def nodes_deprecate(ctx, entity_id, reason, replacement, remove_by):
    """Mark an entity as deprecated with warnings on use.

    Examples:
        know nodes deprecate component:old-auth --reason "Replaced by new-auth"
        know nodes deprecate feature:legacy --reason "Obsolete" --replacement feature:modern
    """
    from src.deprecation import DeprecationManager

    dm = DeprecationManager(ctx.obj['graph'])

    if dm.is_deprecated(entity_id):
        console.print(f"[yellow]⚠ Entity '{entity_id}' is already deprecated[/yellow]")
        return

    if dm.deprecate(entity_id, reason, replacement=replacement, removal_target=remove_by):
        console.print(f"[green]✓ Deprecated '{entity_id}'[/green]")
        console.print(f"  Reason: {reason}")
        if replacement:
            console.print(f"  Replacement: {replacement}")
        if remove_by:
            console.print(f"  Removal target: {remove_by}")
    else:
        console.print(f"[red]✗ Entity not found: {entity_id}[/red]")
        suggest_did_you_mean(ctx.obj['graph'].load(), entity_id)
        sys.exit(1)


@nodes.command(name='undeprecate')
@click.argument('entity_id')
@click.pass_context
def nodes_undeprecate(ctx, entity_id):
    """Remove deprecation status from an entity.

    Examples:
        know nodes undeprecate component:old-auth
    """
    from src.deprecation import DeprecationManager

    dm = DeprecationManager(ctx.obj['graph'])

    if dm.undeprecate(entity_id):
        console.print(f"[green]✓ Removed deprecation from '{entity_id}'[/green]")
    else:
        console.print(f"[yellow]⚠ Entity '{entity_id}' was not deprecated[/yellow]")


@nodes.command(name='deprecated')
@click.option('--overdue', is_flag=True, help='Show only entities past removal date')
@click.pass_context
def nodes_deprecated(ctx, overdue):
    """List all deprecated entities.

    Examples:
        know nodes deprecated
        know nodes deprecated --overdue
    """
    from src.deprecation import DeprecationManager

    dm = DeprecationManager(ctx.obj['graph'])

    if overdue:
        items = dm.get_overdue_removals()
        title = "Overdue Deprecated Entities"
    else:
        items = dm.list_deprecated()
        title = "Deprecated Entities"

    if not items:
        if overdue:
            console.print("[green]✓ No overdue deprecated entities[/green]")
        else:
            console.print("[dim]No deprecated entities[/dim]")
        return

    console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

    for entity_id, info in items:
        console.print(f"[yellow]{entity_id}[/yellow]")
        console.print(f"  Reason: {info['reason']}")
        console.print(f"  Deprecated: {info['deprecated_date']}")
        if info.get('replacement'):
            console.print(f"  Replacement: [green]{info['replacement']}[/green]")
        if info.get('removal_target'):
            console.print(f"  Remove by: {info['removal_target']}")
        console.print()


@nodes.command(name='merge')
@click.argument('from_entity')
@click.argument('into_entity')
@click.option('--keep', is_flag=True, help='Keep the source entity after merge')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def nodes_merge(ctx, from_entity, into_entity, keep, yes):
    """Merge one entity into another, transferring all dependencies.

    Transfers all incoming dependencies (things pointing to FROM) to INTO.
    Transfers all outgoing dependencies (things FROM depends on) to INTO.
    Deletes FROM unless --keep is specified.

    Examples:
        know nodes merge component:old-auth component:new-auth
        know nodes merge feature:duplicate feature:original --keep
        know nodes merge action:old action:new -y
    """
    graph_data = ctx.obj['graph'].load()

    # Parse entity paths
    from_type, from_key = from_entity.split(':', 1)
    into_type, into_key = into_entity.split(':', 1)

    # Verify both entities exist
    if from_type not in graph_data.get('entities', {}) or \
       from_key not in graph_data['entities'].get(from_type, {}):
        console.print(f"[red]✗ Source entity not found: {from_entity}[/red]")
        suggest_did_you_mean(graph_data, from_entity)
        sys.exit(1)

    if into_type not in graph_data.get('entities', {}) or \
       into_key not in graph_data['entities'].get(into_type, {}):
        console.print(f"[red]✗ Target entity not found: {into_entity}[/red]")
        suggest_did_you_mean(graph_data, into_entity)
        sys.exit(1)

    # Preview changes before merge
    graph_section = graph_data.get('graph', {})

    if not yes:
        from src.utils import get_all_deps
        outgoing_count = len(get_all_deps(graph_section.get(from_entity, {})))
        incoming_count = sum(1 for deps in graph_section.values()
                           if from_entity in get_all_deps(deps))

        console.print(f"[yellow]Will merge '{from_entity}' into '{into_entity}':[/yellow]")
        console.print(f"  Outgoing dependencies to transfer: {outgoing_count}")
        console.print(f"  Incoming dependencies to redirect: {incoming_count}")
        if not keep:
            console.print(f"  Will delete '{from_entity}' after merge")

        if not click.confirm("\nProceed?"):
            console.print("[dim]Cancelled[/dim]")
            return

    changes = {'incoming': 0, 'outgoing': 0}

    # Transfer outgoing dependencies (what FROM depends on)
    if from_entity in graph_section:
        for dep_key in ('depends_on', 'depends_on_ordered'):
            from_deps = graph_section[from_entity].get(dep_key, [])
            if from_deps:
                if into_entity not in graph_section:
                    graph_section[into_entity] = {}
                if dep_key not in graph_section[into_entity]:
                    graph_section[into_entity][dep_key] = []

                for dep in from_deps:
                    if dep not in graph_section[into_entity][dep_key]:
                        graph_section[into_entity][dep_key].append(dep)
                        changes['outgoing'] += 1

    # Transfer incoming dependencies (what points to FROM)
    for entity_id, entity_deps in graph_section.items():
        for dep_key in ('depends_on', 'depends_on_ordered'):
            dep_list = entity_deps.get(dep_key, [])
            if from_entity in dep_list:
                dep_list.remove(from_entity)
                if into_entity not in dep_list:
                    dep_list.append(into_entity)
                changes['incoming'] += 1

    # Remove FROM entity unless --keep
    if not keep:
        # Remove from entities
        if from_key in graph_data['entities'].get(from_type, {}):
            del graph_data['entities'][from_type][from_key]
        # Remove from graph
        if from_entity in graph_section:
            del graph_section[from_entity]

    ctx.obj['graph'].save_graph(graph_data)

    console.print(f"[green]✓ Merged '{from_entity}' into '{into_entity}'[/green]")
    console.print(f"  Transferred {changes['incoming']} incoming dependencies")
    console.print(f"  Transferred {changes['outgoing']} outgoing dependencies")
    if not keep:
        console.print(f"  Removed '{from_entity}'")


@nodes.command(name='rename')
@click.argument('entity_id')
@click.argument('new_key')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def nodes_rename(ctx, entity_id, new_key, yes):
    """Rename an entity's key, updating all graph references.

    NEW_KEY can be a bare key or a fully-qualified id — both are accepted:

    Examples:
        know nodes rename objective:foo bar
        know nodes rename objective:foo objective:bar
        know nodes rename feature:auth authentication
        know nodes rename action:setup action:initialize -y
    """
    graph_data = ctx.obj['graph'].load()

    # Parse entity path
    entity_type, old_key = entity_id.split(':', 1)

    # Strip redundant type prefix if user passed "type:key" instead of just "key"
    if new_key.startswith(f"{entity_type}:"):
        new_key = new_key[len(entity_type) + 1:]

    new_entity_id = f"{entity_type}:{new_key}"

    # Verify node exists in entities or references
    in_entities = (entity_type in graph_data.get('entities', {}) and
                   old_key in graph_data['entities'].get(entity_type, {}))
    in_references = (entity_type in graph_data.get('references', {}) and
                     old_key in graph_data['references'].get(entity_type, {}))

    if not in_entities and not in_references:
        console.print(f"[red]✗ Node not found: {entity_id}[/red]")
        suggest_did_you_mean(graph_data, entity_id)
        sys.exit(1)

    # Check new key doesn't conflict
    section = 'entities' if in_entities else 'references'
    if new_key in graph_data[section].get(entity_type, {}):
        console.print(f"[red]✗ Node already exists: {new_entity_id}[/red]")
        sys.exit(1)

    # Preview changes before rename
    if not yes:
        from src.utils import get_all_deps
        graph_section = graph_data.get('graph', {})
        ref_count = sum(1 for deps in graph_section.values()
                       if entity_id in get_all_deps(deps))

        console.print(f"[yellow]Will rename '{entity_id}' to '{new_entity_id}':[/yellow]")
        console.print(f"  References to update: {ref_count}")

        if not click.confirm("\nProceed?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Rename in entities or references section
    if entity_type in graph_data.get('entities', {}) and \
       old_key in graph_data['entities'].get(entity_type, {}):
        graph_data['entities'][entity_type][new_key] = graph_data['entities'][entity_type].pop(old_key)
    elif entity_type in graph_data.get('references', {}) and \
         old_key in graph_data['references'].get(entity_type, {}):
        graph_data['references'][entity_type][new_key] = graph_data['references'][entity_type].pop(old_key)

    # Update graph section
    graph_section = graph_data.get('graph', {})

    # Rename the key if it exists
    if entity_id in graph_section:
        graph_section[new_entity_id] = graph_section.pop(entity_id)

    # Update all references to this entity in both dep lists
    ref_count = 0
    for eid, deps in graph_section.items():
        for dep_key in ('depends_on', 'depends_on_ordered'):
            dep_list = deps.get(dep_key, [])
            if entity_id in dep_list:
                dep_list.remove(entity_id)
                dep_list.append(new_entity_id)
                ref_count += 1

    ctx.obj['graph'].save_graph(graph_data)

    console.print(f"[green]✓ Renamed '{entity_id}' to '{new_entity_id}'[/green]")
    console.print(f"  Updated {ref_count} references in graph")


@nodes.command(name='delete')
@click.argument('entity_ids', nargs=-1, required=True)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def nodes_delete(ctx, entity_ids, yes):
    """Remove one or more entities or references and clean up their dependencies.

    Removes nodes from entities or references section.
    Removes all dependencies to/from each node in graph section.
    Use 'cut' if you want to preserve orphaned dependencies.

    Examples:
        know nodes delete component:obsolete
        know nodes delete feature:cancelled -y
        know nodes delete feature:a feature:b feature:c -y
    """
    graph_data = ctx.obj['graph'].load()
    graph_section = graph_data.get('graph', {})

    # Validate and collect info for all nodes first
    nodes_info = []
    for entity_id in entity_ids:
        node_type, node_key = entity_id.split(':', 1)
        is_entity = (node_type in graph_data.get('entities', {}) and
                     node_key in graph_data['entities'].get(node_type, {}))
        is_reference = (node_type in graph_data.get('references', {}) and
                        node_key in graph_data['references'].get(node_type, {}))

        if not is_entity and not is_reference:
            console.print(f"[red]✗ Node not found: {entity_id}[/red]")
            suggest_did_you_mean(graph_data, entity_id)
            sys.exit(1)

        from src.utils import get_all_deps
        outgoing = get_all_deps(graph_section.get(entity_id, {}))
        incoming = [eid for eid, deps in graph_section.items()
                    if entity_id in get_all_deps(deps)]

        nodes_info.append({
            'id': entity_id,
            'type': node_type,
            'key': node_key,
            'is_entity': is_entity,
            'outgoing': outgoing,
            'incoming': incoming,
        })

    if not yes:
        console.print(f"[yellow]Will delete {len(nodes_info)} node(s):[/yellow]")
        for n in nodes_info:
            category = "entity" if n['is_entity'] else "reference"
            total_links = len(n['outgoing']) + len(n['incoming'])
            console.print(f"  • {n['id']} ({category}, {total_links} links affected)")

        if not click.confirm("\nProceed?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Delete all nodes
    for n in nodes_info:
        if n['is_entity']:
            del graph_data['entities'][n['type']][n['key']]
        else:
            del graph_data['references'][n['type']][n['key']]

        if n['id'] in graph_section:
            del graph_section[n['id']]

        for eid in n['incoming']:
            if eid in graph_section:
                for dep_key in ('depends_on', 'depends_on_ordered'):
                    dep_list = graph_section[eid].get(dep_key, [])
                    if n['id'] in dep_list:
                        dep_list.remove(n['id'])

    ctx.obj['graph'].save_graph(graph_data)

    for n in nodes_info:
        console.print(f"[green]✓ Deleted '{n['id']}'[/green]")


@nodes.command(name='cut')
@click.argument('entity_id')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def nodes_cut(ctx, entity_id, yes):
    """Remove an entity or reference only, leaving dependencies orphaned.

    Removes the node from entities or references section.
    Leaves graph dependencies intact (may create dangling references).
    Use 'delete' for clean removal with dependency cleanup.

    Examples:
        know nodes cut component:to-replace
        know nodes cut feature:swap-out -y
        know nodes cut data-model:old-schema
    """
    graph_data = ctx.obj['graph'].load()

    # Parse node path
    node_type, node_key = entity_id.split(':', 1)

    # Determine if this is an entity or reference
    is_entity = False
    is_reference = False

    if node_type in graph_data.get('entities', {}) and \
       node_key in graph_data['entities'].get(node_type, {}):
        is_entity = True
    elif node_type in graph_data.get('references', {}) and \
         node_key in graph_data['references'].get(node_type, {}):
        is_reference = True
    else:
        console.print(f"[red]✗ Node not found: {entity_id}[/red]")
        suggest_did_you_mean(graph_data, entity_id)
        sys.exit(1)

    node_category = "entity" if is_entity else "reference"

    # Collect dependencies that will be orphaned
    from src.utils import get_all_deps
    graph_section = graph_data.get('graph', {})
    outgoing_deps = get_all_deps(graph_section.get(entity_id, {}))
    incoming_deps = [eid for eid, deps in graph_section.items()
                     if entity_id in get_all_deps(deps)]

    if not yes and (outgoing_deps or incoming_deps):
        console.print(f"[yellow]Will cut {node_category} '{entity_id}' leaving orphaned dependencies:[/yellow]")

        if outgoing_deps:
            console.print(f"\n[dim]Orphaned outgoing ({len(outgoing_deps)}):[/dim]")
            for dep in outgoing_deps:
                console.print(f"  • {entity_id} → {dep}")

        if incoming_deps:
            console.print(f"\n[dim]Dangling incoming refs ({len(incoming_deps)}):[/dim]")
            for dep in incoming_deps:
                console.print(f"  • {dep} → {entity_id}")

        if not click.confirm("\nProceed?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Remove from entities or references only
    if is_entity:
        del graph_data['entities'][node_type][node_key]
    else:
        del graph_data['references'][node_type][node_key]

    ctx.obj['graph'].save_graph(graph_data)

    console.print(f"\n[green]✓ Cut {node_category} '{entity_id}'[/green]")
    if outgoing_deps or incoming_deps:
        total = len(outgoing_deps) + len(incoming_deps)
        console.print(f"[yellow]  ⚠ {total} orphaned dependencies remain in graph[/yellow]")
        console.print(f"  Run 'know check validate' to see issues")


@nodes.command(name='update')
@click.argument('entity_id')
@click.argument('data')
@click.pass_context
def nodes_update(ctx, entity_id, data):
    """Update a node's properties (name, description, etc.).

    Merges provided JSON with existing entity or reference data.

    Examples:
        know nodes update feature:auth '{"name":"Authentication System"}'
        know nodes update component:api '{"description":"Updated description"}'
        know nodes update code-link:my-ref '{"status":"tested"}'
    """
    graph_data = ctx.obj['graph'].load()

    # Parse node path
    entity_type, entity_key = entity_id.split(':', 1)

    # Determine section (entities or references)
    in_entities = (entity_type in graph_data.get('entities', {}) and
                   entity_key in graph_data['entities'].get(entity_type, {}))
    in_references = (entity_type in graph_data.get('references', {}) and
                     entity_key in graph_data['references'].get(entity_type, {}))

    if not in_entities and not in_references:
        console.print(f"[red]✗ Node not found: {entity_id}[/red]")
        suggest_did_you_mean(graph_data, entity_id)
        sys.exit(1)

    # Parse update data
    try:
        update_data = json.loads(data)
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Invalid JSON: {e}[/red]")
        sys.exit(1)

    # Merge with existing
    section = 'entities' if in_entities else 'references'
    existing = graph_data[section][entity_type][entity_key]
    if isinstance(existing, dict):
        existing.update(update_data)
    else:
        graph_data[section][entity_type][entity_key] = update_data

    ctx.obj['graph'].save_graph(graph_data)

    node_label = "entity" if in_entities else "reference"
    console.print(f"[green]✓ Updated {node_label} '{entity_id}'[/green]")
    for key, value in update_data.items():
        console.print(f"  {key}: {value}")


@nodes.command(name='clone')
@click.argument('entity_id')
@click.argument('new_key')
@click.option('--no-upstream', is_flag=True, help='Skip copying upstream dependencies')
@click.option('--no-downstream', is_flag=True, help='Skip copying downstream dependencies')
@click.pass_context
def nodes_clone(ctx, entity_id, new_key, no_upstream, no_downstream):
    """Clone an entity with both upstream and downstream dependencies.

    Creates a copy of the entity with a new key.
    Copies downstream dependencies (what the entity depends on).
    Copies upstream dependencies (things that depend on the entity also depend on clone).

    Examples:
        know nodes clone component:auth component:auth-v2
        know nodes clone feature:login feature:login-mobile --no-upstream
    """
    graph_data = ctx.obj['graph'].load()

    # Parse entity path
    entity_type, old_key = entity_id.split(':', 1)
    new_entity_id = f"{entity_type}:{new_key}"

    # Verify source exists
    if entity_type not in graph_data.get('entities', {}) or \
       old_key not in graph_data['entities'].get(entity_type, {}):
        console.print(f"[red]✗ Entity not found: {entity_id}[/red]")
        suggest_did_you_mean(graph_data, entity_id)
        sys.exit(1)

    # Check new key doesn't exist
    if new_key in graph_data['entities'].get(entity_type, {}):
        console.print(f"[red]✗ Entity already exists: {new_entity_id}[/red]")
        sys.exit(1)

    # Clone entity properties
    import copy
    graph_data['entities'][entity_type][new_key] = copy.deepcopy(
        graph_data['entities'][entity_type][old_key]
    )

    graph_section = graph_data.get('graph', {})
    downstream_count = 0
    upstream_count = 0

    # Clone downstream dependencies (what entity depends on)
    if not no_downstream and entity_id in graph_section:
        clone_node = {}
        for dep_key in ('depends_on', 'depends_on_ordered'):
            deps = graph_section[entity_id].get(dep_key, [])
            if deps:
                clone_node[dep_key] = list(deps)
                downstream_count += len(deps)
        if clone_node:
            graph_section[new_entity_id] = clone_node

    # Clone upstream dependencies (things that depend on entity)
    if not no_upstream:
        for eid, edeps in graph_section.items():
            for dep_key in ('depends_on', 'depends_on_ordered'):
                dep_list = edeps.get(dep_key, [])
                if entity_id in dep_list:
                    if new_entity_id not in dep_list:
                        dep_list.append(new_entity_id)
                        upstream_count += 1

    ctx.obj['graph'].save_graph(graph_data)

    console.print(f"[green]✓ Cloned '{entity_id}' to '{new_entity_id}'[/green]")
    console.print(f"  Copied {downstream_count} downstream dependencies")
    console.print(f"  Copied {upstream_count} upstream dependencies")


# =============================================================================
# GRAPH group
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def graph(ctx):
    """Manage graph dependencies and structure"""
    pass


@cli.command(name='link')
@click.argument('from_entity')
@click.argument('to_entities', nargs=-1, required=True)
@click.option('--position', type=int, help='Insert at this position (workflow only)')
@click.option('--after', help='Insert after this action ID (workflow only)')
@click.option('--auto-create', is_flag=True, help='Auto-create missing actions with minimal data (workflow only)')
@click.pass_context
def link(ctx, from_entity, to_entities, position, after, auto_create):
    """Add one or more dependencies from an entity

    Examples:
        know link feature:auth action:login
        know link feature:auth action:login action:logout component:session
        know link workflow:onboarding action:signup action:verify --position 0
        know link workflow:onboarding action:welcome --after action:verify
        know link workflow:onboarding action:new-step --auto-create
    """
    # Check if this is a workflow (ordered dependencies)
    if from_entity.startswith('workflow:'):
        # Use WorkflowManager for ordered linking
        success, errors = ctx.obj['workflow'].link_actions(
            from_entity,
            list(to_entities),
            position=position,
            after_action=after,
            auto_create=auto_create
        )
        if success:
            console.print(f"[green]✓ Added {len(to_entities)} ordered action(s) to {from_entity}[/green]")
            ordered = ctx.obj['workflow'].get_ordered_actions(from_entity)
            console.print(f"[dim]Order: {' → '.join(ordered)}[/dim]")
        else:
            console.print(f"[red]✗ Failed to link actions:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
    else:
        # Use regular entity linking (unordered)
        if position is not None or after is not None or auto_create:
            console.print("[yellow]⚠ Workflow flags ignored for non-workflow entities[/yellow]")

        failed = False
        for to_entity in to_entities:
            success = ctx.obj['entities'].add_dependency(from_entity, to_entity)
            if success:
                console.print(f"[green]✓ Added dependency: {from_entity} -> {to_entity}[/green]")
            else:
                console.print(f"[red]✗ Already exists or failed: {from_entity} -> {to_entity}[/red]")
                failed = True

        if failed:
            sys.exit(1)


@cli.command(name='unlink')
@click.argument('from_entity')
@click.argument('to_entities', nargs=-1, required=True)
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def unlink(ctx, from_entity, to_entities, yes):
    """Remove one or more dependencies from an entity

    Examples:
        know unlink feature:auth action:login
        know unlink feature:auth action:login action:logout -y
        know unlink workflow:onboarding action:signup -y
    """
    if not yes:
        targets = ', '.join(to_entities)
        if not click.confirm(f"Remove {len(to_entities)} link(s) from {from_entity} -> {targets}?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Check if this is a workflow (ordered dependencies)
    if from_entity.startswith('workflow:'):
        # Use WorkflowManager for ordered unlinking
        success, errors = ctx.obj['workflow'].unlink_actions(from_entity, list(to_entities))
        if success:
            console.print(f"[green]✓ Removed {len(to_entities)} action(s) from {from_entity}[/green]")
            ordered = ctx.obj['workflow'].get_ordered_actions(from_entity)
            if ordered:
                console.print(f"[dim]New order: {' → '.join(ordered)}[/dim]")
            else:
                console.print(f"[dim]Workflow now empty[/dim]")
        else:
            console.print(f"[red]✗ Failed to unlink actions:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
    else:
        # Use regular entity unlinking (unordered)
        failed = False
        for to_entity in to_entities:
            success = ctx.obj['entities'].remove_dependency(from_entity, to_entity)
            if success:
                console.print(f"[green]✓ Removed dependency: {from_entity} -> {to_entity}[/green]")
            else:
                console.print(f"[red]✗ Not found or failed: {from_entity} -> {to_entity}[/red]")
                failed = True

        if failed:
            sys.exit(1)


@graph.command(name='uses')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependencies or just direct ones')
@click.pass_context
def graph_uses(ctx, entity_path, recursive):
    """Show what an entity uses (its dependencies)

    Examples:
        know graph uses feature:auth
        know graph uses feature:auth --direct
        know graph uses component:login-form --recursive
    """
    deps = ctx.obj['graph'].find_dependencies(entity_path, recursive)

    if not deps:
        console.print(f"[yellow]{entity_path} uses nothing[/yellow]")
        return

    if recursive:
        console.print(f"\n[bold]{entity_path} uses (recursively):[/bold]")
    else:
        console.print(f"\n[bold]{entity_path} uses (directly):[/bold]")

    for dep in sorted(deps):
        console.print(f"  • {dep}")


@graph.command(name='up')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependencies or just direct ones')
@click.pass_context
def graph_up(ctx, entity_path, recursive):
    """Alias for 'uses' - show what an entity uses (go up the dependency chain)"""
    ctx.invoke(graph_uses, entity_path=entity_path, recursive=recursive)


@graph.command(name='used-by')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependents or just direct ones')
@click.pass_context
def graph_used_by(ctx, entity_path, recursive):
    """Show what uses this entity (dependents)

    Examples:
        know graph used-by component:auth-handler
        know graph used-by action:login --direct
        know graph used-by data-model:user-profile
    """
    deps = ctx.obj['graph'].find_dependents(entity_path, recursive)

    if not deps:
        console.print(f"[yellow]{entity_path} is not used by anything[/yellow]")
        return

    if recursive:
        console.print(f"\n[bold]{entity_path} is used by (recursively):[/bold]")
    else:
        console.print(f"\n[bold]{entity_path} is used by (directly):[/bold]")

    for dep in sorted(deps):
        console.print(f"  • {dep}")


@graph.command(name='down')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependents or just direct ones')
@click.pass_context
def graph_down(ctx, entity_path, recursive):
    """Alias for 'used-by' - show what uses this entity (go down the dependency chain)"""
    ctx.invoke(graph_used_by, entity_path=entity_path, recursive=recursive)


@graph.command(name='connect')
@click.argument('entity_id')
@click.option('--max', '-m', default=5, help='Maximum suggestions per type')
@click.pass_context
def graph_connect(ctx, entity_id, max):
    """Suggest valid connections for an entity (formerly 'suggest')

    Examples:
        know graph connect feature:auth
        know graph connect component:api-client --max 10
    """
    suggestions = ctx.obj['deps'].suggest_connections(entity_id, max)

    if not suggestions:
        console.print(f"[yellow]No suggestions found for {entity_id}[/yellow]")
        return

    console.print(f"\n[bold]Valid connections for {entity_id}:[/bold]\n")

    for entity_type, entities in suggestions.items():
        if entities:
            console.print(f"[cyan]{entity_type}:[/cyan]")
            for e in entities:
                console.print(f"  • {e}")
            console.print()


@graph.command(name='build-order')
@click.pass_context
def graph_build_order(ctx):
    """Show topological build order

    Examples:
        know graph build-order
        know -g .ai/know/code-graph.json graph build-order
    """
    order = ctx.obj['deps'].topological_sort()

    if not order:
        console.print("[red]Cannot determine build order (graph has cycles)[/red]")
        sys.exit(1)

    console.print("[bold]Build Order:[/bold]\n")
    for i, e in enumerate(order, 1):
        console.print(f"{i:3}. {e}")


@graph.command(name='diff')
@click.argument('graph1', type=click.Path(exists=True), required=False, default=None)
@click.argument('graph2', type=click.Path(exists=True), required=False, default=None)
@click.option('--base', '-b', default=None, metavar='REF',
              help='Git ref to compare against (e.g. main, origin/main, HEAD~1). '
                   'Uses current graph file vs that ref. Mutually exclusive with GRAPH2.')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed diff')
@click.option('--format', '-f', type=click.Choice(['terminal', 'json']), default='terminal',
              help='Output format')
@click.pass_context
def graph_diff(ctx, graph1, graph2, base, verbose, format):
    """Compare two graph files and show differences

    Shows added/removed/modified entities, dependencies, and references.

    Two-file mode:
        know graph diff old-graph.json new-graph.json
        know graph diff .ai/know/spec-graph.json /tmp/spec-graph.json --verbose

    Git mode (compare current graph vs a git ref):
        know graph diff --base main
        know graph diff --base origin/main --verbose
        know graph diff --base HEAD~1 --format json

    Examples:
        know graph diff graph1.json graph2.json --format json
    """
    # Resolve which files to compare
    tmp_file = None
    try:
        if base is not None:
            if graph2 is not None:
                console.print("[red]✗ --base and GRAPH2 are mutually exclusive[/red]")
                sys.exit(1)

            # Infer current graph path from context
            current_graph_path = str(ctx.obj['graph'].cache.graph_path)
            if graph1 is None:
                graph1 = current_graph_path

            # Compute git-root-relative path for git show
            try:
                git_root = subprocess.check_output(
                    ['git', 'rev-parse', '--show-toplevel'],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
            except subprocess.CalledProcessError:
                console.print("[red]✗ Not inside a git repository[/red]")
                sys.exit(1)

            graph1_abs = str(Path(graph1).resolve())
            try:
                rel_path = Path(graph1_abs).relative_to(git_root)
            except ValueError:
                console.print(f"[red]✗ Graph file is outside the git root: {graph1_abs}[/red]")
                sys.exit(1)

            try:
                base_content = subprocess.check_output(
                    ['git', 'show', f'{base}:{rel_path}'],
                    stderr=subprocess.PIPE
                )
            except subprocess.CalledProcessError as e:
                err = e.stderr.decode().strip()
                console.print(f"[red]✗ Could not read {rel_path} at ref '{base}': {err}[/red]")
                sys.exit(1)

            tmp = tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False)
            tmp.write(base_content)
            tmp.close()
            tmp_file = tmp.name

            # base is the OLD version; graph1 (current) is the NEW version
            graph2 = graph1
            graph1 = tmp_file

        else:
            if graph1 is None or graph2 is None:
                console.print("[red]✗ Provide GRAPH1 and GRAPH2, or use --base <ref>[/red]")
                sys.exit(1)

        differ = GraphDiff(graph1, graph2)
        diff_result = differ.compute_diff()

        if format == 'json':
            # JSON output for scripting
            print(json.dumps(diff_result, indent=2))
            return

        # Terminal output (colored, human-readable)
        summary = diff_result['summary']

        # Header
        if base is not None:
            header_label = f"[dim]{base}[/dim] → [dim]current[/dim]"
        else:
            header_label = f"{differ.graph1_path} → {differ.graph2_path}"
        console.print(f"\n[bold cyan]Graph Diff:[/bold cyan] {header_label}\n")

        # Summary
        if not any([
            summary['entities_added'],
            summary['entities_removed'],
            summary['entities_modified'],
            summary['dependencies_added'],
            summary['dependencies_removed'],
            summary['dependencies_modified'],
            summary['references_added'],
            summary['references_removed'],
            summary['meta_changed']
        ]):
            console.print("[green]✓ Graphs are identical[/green]")
            return

        # Summary counts
        console.print("[bold]Summary:[/bold]")
        if summary['entities_added']:
            console.print(f"  [green]+ {summary['entities_added']} entities added[/green]")
        if summary['entities_removed']:
            console.print(f"  [red]- {summary['entities_removed']} entities removed[/red]")
        if summary['entities_modified']:
            console.print(f"  [yellow]~ {summary['entities_modified']} entities modified[/yellow]")
        if summary['dependencies_added']:
            console.print(f"  [green]+ {summary['dependencies_added']} dependencies added[/green]")
        if summary['dependencies_removed']:
            console.print(f"  [red]- {summary['dependencies_removed']} dependencies removed[/red]")
        if summary['dependencies_modified']:
            console.print(f"  [yellow]~ {summary['dependencies_modified']} dependencies modified[/yellow]")
        if summary['references_added']:
            console.print(f"  [green]+ {summary['references_added']} references added[/green]")
        if summary['references_removed']:
            console.print(f"  [red]- {summary['references_removed']} references removed[/red]")
        if summary['meta_changed']:
            console.print(f"  [yellow]~ meta changed[/yellow]")

        console.print()

        # Verbose output
        if verbose:
            # Meta changes
            if diff_result['meta']['changed']:
                console.print("[bold]Meta Changes:[/bold]")
                for key, change in diff_result['meta']['changed'].items():
                    console.print(f"  [yellow]~ {key}[/yellow]")
                    console.print(f"    [red]- {change['old']}[/red]")
                    console.print(f"    [green]+ {change['new']}[/green]")
                console.print()

            # Entity changes
            if diff_result['entities']['added']:
                console.print("[bold]Added Entities:[/bold]")
                for e in diff_result['entities']['added']:
                    console.print(f"  [green]+ {e['key']}[/green]")
                    console.print(f"    name: {e['data'].get('name', 'N/A')}")
                    console.print(f"    description: {e['data'].get('description', 'N/A')}")
                console.print()

            if diff_result['entities']['removed']:
                console.print("[bold]Removed Entities:[/bold]")
                for e in diff_result['entities']['removed']:
                    console.print(f"  [red]- {e['key']}[/red]")
                    console.print(f"    name: {e['data'].get('name', 'N/A')}")
                    console.print(f"    description: {e['data'].get('description', 'N/A')}")
                console.print()

            if diff_result['entities']['modified']:
                console.print("[bold]Modified Entities:[/bold]")
                for e in diff_result['entities']['modified']:
                    console.print(f"  [yellow]~ {e['key']}[/yellow]")
                    for key in e['old'].keys() | e['new'].keys():
                        old_val = e['old'].get(key)
                        new_val = e['new'].get(key)
                        if old_val != new_val:
                            console.print(f"    {key}:")
                            console.print(f"      [red]- {old_val}[/red]")
                            console.print(f"      [green]+ {new_val}[/green]")
                console.print()

            # Dependency changes
            if diff_result['graph']['added']:
                console.print("[bold]Added Dependencies:[/bold]")
                for dep in diff_result['graph']['added']:
                    console.print(f"  [green]+ {dep['entity']}[/green]")
                    console.print(f"    depends_on: {dep['depends_on']}")
                console.print()

            if diff_result['graph']['removed']:
                console.print("[bold]Removed Dependencies:[/bold]")
                for dep in diff_result['graph']['removed']:
                    console.print(f"  [red]- {dep['entity']}[/red]")
                    console.print(f"    depends_on: {dep['depends_on']}")
                console.print()

            if diff_result['graph']['modified']:
                console.print("[bold]Modified Dependencies:[/bold]")
                for dep in diff_result['graph']['modified']:
                    console.print(f"  [yellow]~ {dep['entity']}[/yellow]")
                    if dep['added_deps']:
                        console.print(f"    [green]+ added: {dep['added_deps']}[/green]")
                    if dep['removed_deps']:
                        console.print(f"    [red]- removed: {dep['removed_deps']}[/red]")
                console.print()

            # Reference changes
            if diff_result['references']['added']:
                console.print("[bold]Added References:[/bold]")
                for ref in diff_result['references']['added']:
                    console.print(f"  [green]+ {ref['key']}[/green]")
                console.print()

            if diff_result['references']['removed']:
                console.print("[bold]Removed References:[/bold]")
                for ref in diff_result['references']['removed']:
                    console.print(f"  [red]- {ref['key']}[/red]")
                console.print()

    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Invalid JSON: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)
    finally:
        if tmp_file is not None:
            Path(tmp_file).unlink(missing_ok=True)


@graph.command(name='migrate-rules')
@click.argument('target_rules', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['terminal', 'json']), default='terminal',
              help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed migration plan')
@click.pass_context
def graph_migrate_rules(ctx, target_rules, format, verbose):
    """Analyze migration impact from current rules to target rules

    Compares current dependency rules against target rules and reports
    affected entities, invalid links, and generates a migration plan.
    Analysis only — does not execute changes.

    Examples:
        know graph migrate-rules new-rules.json
        know graph migrate-rules new-rules.json --format json
        know graph migrate-rules new-rules.json --verbose
    """
    try:
        graph_data = ctx.obj['graph'].load()
        current_rules = ctx.obj['rules_path']

        analyzer = RulesDiffAnalyzer(current_rules, target_rules, graph_data)
        result = analyzer.run()

        if format == 'json':
            print(json.dumps(result, indent=2))
            return

        summary = result['summary']
        diff = result['diff']
        impact = result['impact']
        plan = result['plan']

        # Header
        console.print(f"\n[bold cyan]Rules Migration:[/bold cyan] {summary['current_rules']} → {summary['target_rules']}\n")

        # Rules Diff
        console.print("[bold]Rules Diff:[/bold]")
        if diff['entity_types']['removed']:
            for et in diff['entity_types']['removed']:
                disp = diff['entity_types']['dispositions'].get(et, 'unknown')
                console.print(f"  [red]- entity type: {et}[/red] ({disp})")
        if diff['entity_types']['added']:
            for et in diff['entity_types']['added']:
                console.print(f"  [green]+ entity type: {et}[/green]")
        if diff['dependency_paths']['removed']:
            for fr, to in diff['dependency_paths']['removed']:
                console.print(f"  [red]- path: {fr} → {to}[/red]")
        if diff['dependency_paths']['added']:
            for fr, to in diff['dependency_paths']['added']:
                console.print(f"  [green]+ path: {fr} → {to}[/green]")
        if diff['reference_types']['added']:
            for rt in diff['reference_types']['added']:
                console.print(f"  [green]+ ref type: {rt}[/green]")
        if diff['reference_types']['removed']:
            for rt in diff['reference_types']['removed']:
                console.print(f"  [red]- ref type: {rt}[/red]")

        if not any([
            diff['entity_types']['removed'], diff['entity_types']['added'],
            diff['dependency_paths']['removed'], diff['dependency_paths']['added'],
            diff['reference_types']['removed'], diff['reference_types']['added'],
        ]):
            console.print("  [green]✓ Rules are identical[/green]")
            return

        console.print()

        # Impact Analysis
        console.print("[bold]Impact Analysis:[/bold]")
        console.print(f"  Affected entities:   {impact['counts']['entities']}")
        console.print(f"  Affected links:      {impact['counts']['links']}")
        console.print(f"  Affected references: {impact['counts']['references']}")
        console.print(f"  Affected phases:     {impact['counts']['phases']}")
        console.print()

        if verbose:
            if impact['entities']:
                console.print("[bold]Affected Entities:[/bold]")
                for e in impact['entities']:
                    console.print(f"  [yellow]{e['id']}[/yellow] — {e['disposition']}")
                    if e['dependents']:
                        console.print(f"    depended on by: {', '.join(e['dependents'])}")
                    if e['dependencies']:
                        console.print(f"    depends on: {', '.join(e['dependencies'])}")
                console.print()

            if impact['links']:
                console.print("[bold]Invalid Links:[/bold]")
                for link in impact['links']:
                    console.print(f"  [red]{link['from']} → {link['to']}[/red] ({link['path']})")
                console.print()

            if impact['phases']:
                console.print("[bold]Affected Phases:[/bold]")
                for p in impact['phases']:
                    console.print(f"  [yellow]{p['phase']}[/yellow]: {p['entity_id']}")
                console.print()

        # Migration Plan
        console.print(f"[bold]Migration Plan:[/bold] ({len(plan['steps'])} steps)")
        for i, step in enumerate(plan['steps'], 1):
            phase_color = {
                'pre-validation': 'cyan',
                'create-references': 'green',
                'reroute-links': 'yellow',
                'remove-entities': 'red',
                'update-phases': 'magenta',
                'post-validation': 'cyan',
            }.get(step['phase'], 'white')
            console.print(f"  {i:3}. [{phase_color}][{step['phase']}][/{phase_color}] {step['description']}")
            if verbose:
                console.print(f"       [dim]$ {step['command']}[/dim]")

        console.print()

    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Invalid JSON: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


def _migrate_deprecated_names(graph_data, rules):
    """Rename deprecated reference types in graph data.

    Returns list of change descriptions (empty if nothing to do).
    Mutates graph_data in place.
    """
    deprecated = rules.get('reference_note', {}).get('deprecated_names', {})
    if not deprecated:
        deprecated = rules.get('reference_dependency_rule', {}).get('deprecated_names', {})
    if not deprecated:
        return []

    changes = []

    # Rename reference type keys
    refs = graph_data.get('references', {})
    for old_type, new_type in deprecated.items():
        if old_type in refs:
            refs[new_type] = refs.pop(old_type)
            changes.append(f"renamed reference type '{old_type}' → '{new_type}'")

    # Rename graph dependency IDs
    graph_section = graph_data.get('graph', {})
    for entity_id, deps in list(graph_section.items()):
        old_prefix = entity_id.split(':', 1)[0] if ':' in entity_id else None
        if old_prefix and old_prefix in deprecated:
            new_id = deprecated[old_prefix] + ':' + entity_id.split(':', 1)[1]
            graph_section[new_id] = graph_section.pop(entity_id)
            changes.append(f"renamed graph key '{entity_id}' → '{new_id}'")
            deps = graph_section[new_id]

        for dep_field in ['depends_on', 'depends_on_ordered']:
            dep_list = deps.get(dep_field, [])
            for i, dep_id in enumerate(dep_list):
                dep_prefix = dep_id.split(':', 1)[0] if ':' in dep_id else None
                if dep_prefix and dep_prefix in deprecated:
                    new_dep = deprecated[dep_prefix] + ':' + dep_id.split(':', 1)[1]
                    dep_list[i] = new_dep
                    changes.append(f"renamed graph dep '{dep_id}' → '{new_dep}'")

    return changes


@graph.command(name='migrate')
@click.option('--dry-run', is_flag=True, help='Show changes without saving')
@click.pass_context
def graph_migrate(ctx, dry_run):
    """Apply all available migrations to the graph

    Discovers and runs migration steps from the rules file.
    Currently supported: deprecated_names (reference type renames).
    Idempotent — safe to re-run.

    Examples:
        know graph migrate
        know graph migrate --dry-run
        know -g .ai/know/spec-graph.json graph migrate
    """
    try:
        graph_manager = ctx.obj['graph']
        graph_data = graph_manager.load()
        rules_path = ctx.obj['rules_path']

        with open(rules_path) as f:
            rules = json.load(f)

        all_changes = {}

        # Migration 1: deprecated reference type names
        naming_changes = _migrate_deprecated_names(graph_data, rules)
        if naming_changes:
            all_changes['Deprecated Names'] = naming_changes

        # Future migrations go here as additional steps

        if not all_changes:
            console.print("[green]✓ Graph is up to date — no migrations needed[/green]")
            return

        total = sum(len(v) for v in all_changes.values())
        console.print(f"\n[bold cyan]Graph Migration:[/bold cyan] {total} changes across {len(all_changes)} migration(s)\n")

        for section, changes in all_changes.items():
            console.print(f"[bold]{section}:[/bold] ({len(changes)})")
            for change in changes:
                console.print(f"  {change}")
            console.print()

        if dry_run:
            console.print("[yellow]Dry run — no changes saved[/yellow]")
            return

        graph_manager.save_graph(graph_data)
        console.print(f"[green]✓ Applied {total} migration changes[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found: {e}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Invalid JSON: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@graph.command(name='traverse')
@click.argument('entity_id')
@click.option('--direction', '-d', type=click.Choice(['impl', 'spec']),
              help='Direction: "impl" for spec→code, "spec" for code→spec')
@click.pass_context
def graph_traverse(ctx, entity_id, direction):
    """Traverse between spec and code graphs

    Shows implementation mappings between specification and code entities.
    Uses meta.code_graph_path / meta.spec_graph_path for cross-graph lookups.

    Examples:
        know graph traverse feature:auth --direction impl
        know graph traverse module:auth --direction spec
        know graph traverse feature:profile   # Auto-detects direction
    """
    graph_manager = ctx.obj['graph']

    # Check if counterpart graph is configured
    counterpart_path = graph_manager.get_counterpart_graph_path()
    if not counterpart_path:
        console.print("[yellow]⚠ No counterpart graph configured in meta[/yellow]")
        console.print("\nAdd to your graph's meta section:")
        console.print('  "code_graph_path": ".ai/know/code-graph.json"  (in spec-graph.json)')
        console.print('  "spec_graph_path": ".ai/know/spec-graph.json"  (in code-graph.json)')
        sys.exit(1)

    # Auto-detect direction if not specified
    if not direction:
        if entity_id.startswith('feature:') or entity_id.startswith('component:'):
            direction = 'impl'
        elif entity_id.startswith('module:') or entity_id.startswith('package:'):
            direction = 'spec'
        else:
            console.print(f"[yellow]⚠ Cannot auto-detect direction for {entity_id}[/yellow]")
            console.print("Specify --direction impl (spec→code) or --direction spec (code→spec)")
            sys.exit(1)

    try:
        if direction == 'impl':
            # Spec → Code: Show implementations
            if entity_id.startswith('feature:'):
                results = graph_manager.get_feature_implementations(entity_id)

                if not results:
                    console.print(f"[yellow]⚠ No implementations found for {entity_id}[/yellow]")
                    console.print("\nFeatures link to code via implementation references:")
                    console.print('  1. Add graph-link in code-graph.json referencing code entities')
                    console.print('  2. Add implementation reference in spec-graph.json')
                    console.print('  3. Link feature to implementation reference')
                    sys.exit(0)

                console.print(f"[bold cyan]Implementations for {entity_id}:[/bold cyan]\n")
                for code_id, code_data in results:
                    name = code_data.get('name', code_id)
                    desc = code_data.get('description', '')
                    console.print(f"  • [green]{code_id}[/green]: {name}")
                    if desc:
                        console.print(f"    {desc}")

            else:
                console.print(f"[yellow]⚠ Implementation lookup only supported for features[/yellow]")
                console.print(f"Use: know graph traverse feature:<name> --direction impl")
                sys.exit(1)

        elif direction == 'spec':
            # Code → Spec: Show feature mapping
            result = graph_manager.get_code_feature_mapping(entity_id)

            if not result:
                console.print(f"[yellow]⚠ No feature mapping found for {entity_id}[/yellow]")
                console.print("\nCode entities link to features via graph-link references:")
                console.print('  1. Add graph-link in code-graph.json')
                console.print('  2. Reference it from spec implementation')
                console.print('  3. Link feature to the implementation')
                sys.exit(0)

            feature_id, feature_data = result
            name = feature_data.get('name', feature_id)
            desc = feature_data.get('description', '')

            console.print(f"[bold cyan]Feature for {entity_id}:[/bold cyan]\n")
            console.print(f"  • [green]{feature_id}[/green]: {name}")
            if desc:
                console.print(f"    {desc}")

    except Exception as e:
        console.print(f"[red]✗ Error traversing graphs: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


# =============================================================================
# CHECK group
# =============================================================================
@graph.group(name='check', context_settings=CONTEXT_SETTINGS)
@click.pass_context
def check(ctx):
    """Validate graph structure and analyze health"""
    pass


def _display_validation_results(results: dict, is_valid: bool) -> None:
    """Display validation results in a formatted way."""
    if results['errors']:
        console.print("[red]✗ Errors:[/red]")
        for error in results['errors']:
            console.print(f"  • {error}")
        console.print()

    if results['warnings']:
        console.print("[yellow]⚠ Warnings:[/yellow]")
        for warning in results['warnings']:
            console.print(f"  • {warning}")
        console.print()

    if results['info']:
        console.print("[cyan]ℹ Info:[/cyan]")
        for info in results['info'][:10]:  # Limit to first 10
            console.print(f"  • {info}")
        console.print()

    if is_valid:
        console.print("[green]✓ Graph validation passed![/green]")


@check.command(name='syntax')
@click.pass_context
def check_syntax(ctx):
    """Fast syntax validation (~ms) - structure and format only

    Examples:
        know check syntax
        know -g .ai/know/code-graph.json check syntax
    """
    is_valid, results = ctx.obj['validator'].validate_syntax()
    _display_validation_results(results, is_valid)

    if not is_valid:
        sys.exit(1)


@check.command(name='structure')
@click.pass_context
def check_structure(ctx):
    """Structure validation (~50ms) - schema and relationships

    Examples:
        know check structure
        know -g .ai/know/code-graph.json check structure
    """
    is_valid, results = ctx.obj['validator'].validate_structure()
    _display_validation_results(results, is_valid)

    if not is_valid:
        sys.exit(1)


@check.command(name='semantics')
@click.pass_context
def check_semantics(ctx):
    """Semantic validation (~200ms) - dependencies and conventions

    Examples:
        know check semantics
        know -g .ai/know/code-graph.json check semantics
    """
    is_valid, results = ctx.obj['validator'].validate_semantics(ctx.obj['deps'])
    _display_validation_results(results, is_valid)

    if not is_valid:
        sys.exit(1)


@check.command(name='full')
@click.pass_context
def check_full(ctx):
    """Full validation (all layers) - comprehensive check

    Examples:
        know check full
        know -g .ai/know/code-graph.json check full
    """
    is_valid, results = ctx.obj['validator'].validate_full(ctx.obj['deps'])
    _display_validation_results(results, is_valid)

    if not is_valid:
        sys.exit(1)


@check.command(name='validate')
@click.pass_context
def check_validate(ctx):
    """Validate graph structure and dependencies (alias for 'full')

    Examples:
        know check validate
        know -g .ai/know/code-graph.json check validate
    """
    # Redirect to full validation for backward compatibility
    is_valid, results = ctx.obj['validator'].validate_full(ctx.obj['deps'])
    _display_validation_results(results, is_valid)

    # Check for deprecated reference type names
    try:
        rules_path = ctx.obj['rules_path']
        with open(rules_path) as f:
            rules = json.load(f)
        deprecated = rules.get('reference_note', {}).get('deprecated_names', {})
        if deprecated:
            graph_data = ctx.obj['graph'].load()
            refs = graph_data.get('references', {})
            graph_section = graph_data.get('graph', {})
            found_old = set()
            for old_name in deprecated:
                if old_name in refs:
                    found_old.add(old_name)
                for deps in graph_section.values():
                    for dep_id in deps.get('depends_on', []) + deps.get('depends_on_ordered', []):
                        if ':' in dep_id and dep_id.split(':', 1)[0] == old_name:
                            found_old.add(old_name)
            if found_old:
                console.print(f"\n[yellow]⚠ Found {len(found_old)} deprecated reference type names: {', '.join(sorted(found_old))}[/yellow]")
                console.print("[yellow]  Run 'know graph migrate' to update them[/yellow]")
    except Exception:
        pass  # Non-fatal — validation result is what matters

    if not is_valid:
        sys.exit(1)


@check.command(name='health')
@click.pass_context
def check_health(ctx):
    """Comprehensive graph health check

    Examples:
        know check health
    """
    console.print("[bold]Running health checks...[/bold]\n")

    # Full validation (includes cycles via validate_semantics)
    is_valid, results = ctx.obj['validator'].validate_full(ctx.obj['deps'])

    # Disconnected subgraphs (informational only)
    disconnected = ctx.obj['validator'].find_disconnected_subgraphs()

    # Summary
    console.print("[bold cyan]Health Summary:[/bold cyan]\n")

    # Critical issues (cause failure)
    has_critical_issues = not is_valid

    if not has_critical_issues and not results['warnings']:
        console.print("[green]✓ Graph is healthy![/green]")
        if disconnected:
            console.print(f"\n[cyan]ℹ {len(disconnected)} disconnected subgraphs (expected for initial graphs)[/cyan]")
        return

    if not is_valid:
        console.print(f"[red]✗ {len(results['errors'])} validation errors[/red]")

    if disconnected:
        console.print(f"[cyan]ℹ {len(disconnected)} disconnected subgraphs (expected for initial/incremental graphs)[/cyan]")

    if results['warnings']:
        console.print(f"[yellow]⚠ {len(results['warnings'])} warnings[/yellow]")

    console.print("\n[dim]Run 'know check full' for detailed results[/dim]")

    # Only exit with error if there are critical issues
    if has_critical_issues:
        sys.exit(1)


@check.command(name='stats')
@click.pass_context
def check_stats(ctx):
    """Show graph statistics

    Examples:
        know check stats
        know -g .ai/know/code-graph.json check stats
    """
    graph_data = ctx.obj['graph'].load()
    stats = get_graph_stats(graph_data)

    table = Table(title="Graph Statistics", show_header=True,
                  header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right", style="yellow")

    table.add_row("Entity Types", str(stats['entity_types']))
    table.add_row("Total Entities", str(stats['total_entities']))
    table.add_row("Reference Types", str(stats['reference_types']))
    table.add_row("Total References", str(stats['total_references']))
    table.add_row("Graph Nodes", str(stats['graph_nodes']))
    table.add_row("Total Dependencies", str(stats['total_dependencies']))

    console.print(table)
    console.print("\n[bold]Entities by Type:[/bold]")

    for entity_type, count in sorted(stats['entities_by_type'].items()):
        console.print(f"  • {entity_type}: {count}")

    if stats.get('references_by_type'):
        console.print("\n[bold]References by Type:[/bold]")
        for ref_type, count in sorted(stats['references_by_type'].items()):
            console.print(f"  • {ref_type}: {count}")


@check.command(name='completeness')
@click.argument('entity_id')
@click.pass_context
def check_completeness(ctx, entity_id):
    """Check completeness score for an entity

    Examples:
        know check completeness feature:auth
        know check completeness component:api-client
    """
    score = ctx.obj['validator'].get_completeness_score(entity_id)

    if score['total'] == 0:
        console.print(f"[red]Entity {entity_id} not found[/red]")
        suggest_did_you_mean(ctx.obj['graph'].load(), entity_id)
        sys.exit(1)

    console.print(f"\n[bold]Completeness Score for {entity_id}:[/bold]")
    console.print(f"\nScore: [cyan]{score['percentage']}%[/cyan] ({score['completed']}/{score['total']})")
    console.print("\n[bold]Checks:[/bold]")

    for c, passed in score['checks'].items():
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {status} {c.replace('_', ' ').title()}")


@check.command(name='cycles')
@click.pass_context
def check_cycles(ctx):
    """Detect circular dependencies

    Examples:
        know check cycles
    """
    cycles = ctx.obj['deps'].detect_cycles()

    if not cycles:
        console.print("[green]✓ No circular dependencies found[/green]")
        return

    console.print("[red]✗ Circular dependencies detected:[/red]\n")
    for i, cycle in enumerate(cycles, 1):
        console.print(f"Cycle {i}: {' → '.join(cycle)}")

    sys.exit(1)


# --- CHECK commands (flattened from check link) ---
@check.command(name='orphans')
@click.pass_context
def check_orphans(ctx):
    """Find orphaned references

    Examples:
        know check orphans
    """
    from src.reference_tools import ReferenceManager

    ref_mgr = ReferenceManager(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])
    orphaned = ref_mgr.check_reference_parents()

    if not orphaned:
        console.print("[green]✓ No orphaned references found[/green]")
        return

    console.print("\n[bold yellow]Orphaned References[/bold yellow]\n")

    total = 0
    for category, refs in orphaned.items():
        console.print(f"[cyan]{category}:[/cyan]")
        for ref in refs:
            console.print(f"  • {ref}")
            total += 1
        console.print()

    console.print(f"Total orphaned: {total}")


@check.command(name='usage')
@click.pass_context
def check_link_usage(ctx):
    """Show reference usage statistics

    Examples:
        know check usage
    """
    from src.reference_tools import ReferenceManager

    ref_mgr = ReferenceManager(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])
    usage = ref_mgr.get_reference_usage()

    table = Table(title="Reference Usage", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Reference", style="green")
    table.add_column("Usage Count", justify="right", style="yellow")

    for category, refs in sorted(usage.items()):
        for ref_key, count in sorted(refs.items(), key=lambda x: -x[1]):
            color = "green" if count > 0 else "red"
            table.add_row(category, ref_key, f"[{color}]{count}[/{color}]")

    console.print(table)


@graph.command(name='clean')
@click.option('--remove/--keep', default=False, help='Remove unused references')
@click.option('--dry-run/--execute', default=True, help='Dry run mode')
@click.pass_context
def graph_clean(ctx, remove, dry_run):
    """Clean up unused references

    Examples:
        know graph clean                    # Dry run
        know graph clean --execute          # Show what would be removed
        know graph clean --remove --execute # Actually remove
    """
    from src.reference_tools import ReferenceManager

    ref_mgr = ReferenceManager(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])
    results = ref_mgr.clean_references(remove_unused=remove, dry_run=dry_run)

    console.print(f"\n[bold]Reference Cleanup Results[/bold]\n")
    console.print(f"Total References: {results['total_refs']}")
    console.print(f"Orphaned: {results['orphaned_refs']}")

    if remove and results['removed_refs']:
        console.print(f"\n[yellow]Removed ({len(results['removed_refs'])}):[/yellow]")
        for ref in results['removed_refs'][:10]:
            console.print(f"  • {ref}")
        if len(results['removed_refs']) > 10:
            console.print(f"  ... and {len(results['removed_refs']) - 10} more")

    if dry_run:
        console.print("\n[dim]This was a dry run. Use --execute to apply changes.[/dim]")


@graph.command(name='coverage')
@click.option('--json', 'json_output', is_flag=True, help='Machine-readable JSON output')
@click.option('--refs', is_flag=True, help='Include reference nodes in coverage metrics')
@click.pass_context
def graph_coverage(ctx, json_output, refs):
    """Show what percentage of entities are reachable from root users

    Measures spec-graph coverage: how many entities are connected to the
    root user chain (project → user → objective → feature → ...).

    Examples:
        know graph coverage
        know graph coverage --refs
        know -g .ai/know/spec-graph.json graph coverage
        know graph coverage --json
    """
    graph_data = ctx.obj['graph'].load()
    entities = graph_data.get('entities', {})
    references = graph_data.get('references', {})
    deps = graph_data.get('graph', {})

    # Find root users: entities with type 'user' or reachable from 'project'
    all_entity_ids = set()
    for etype, emap in entities.items():
        for key in emap:
            all_entity_ids.add(f"{etype}:{key}")

    # Optionally include reference IDs in the trackable set
    all_ref_ids = set()
    if refs:
        for rtype, rmap in references.items():
            if isinstance(rmap, dict):
                for key in rmap:
                    all_ref_ids.add(f"{rtype}:{key}")

    all_trackable = all_entity_ids | all_ref_ids

    # BFS from all project/user nodes to find reachable nodes
    roots = set()
    for etype in ('project', 'user'):
        for key in entities.get(etype, {}):
            roots.add(f"{etype}:{key}")

    from src.utils import get_all_deps
    entity_types = set(entities.keys())
    ref_types = set(references.keys()) if refs else set()
    valid_types = entity_types | ref_types

    reachable = set(roots)
    queue = list(roots)
    while queue:
        node = queue.pop()
        for dep in get_all_deps(deps.get(node, {})):
            dep_type = dep.split(':')[0] if ':' in dep else ''
            if dep_type in valid_types and dep not in reachable:
                reachable.add(dep)
                queue.append(dep)

    total = len(all_trackable)
    covered = len(reachable & all_trackable)
    disconnected = sorted(all_trackable - reachable)
    pct = round(covered / total * 100, 1) if total > 0 else 0.0

    if json_output:
        import json as json_mod
        result = {
            'total': total,
            'covered': covered,
            'coverage_percent': pct,
            'disconnected': sorted(disconnected)
        }
        if refs:
            result['includes_references'] = True
        console.print(json_mod.dumps(result))
        return

    label = "Entity + Reference" if refs else "Entity"
    color = 'green' if pct >= 80 else 'yellow' if pct >= 50 else 'red'
    console.print(f"\n[bold]Spec-Graph {label} Coverage[/bold]")
    console.print(f"[{color}]{covered}/{total} nodes reachable ({pct}%)[/{color}]\n")

    if disconnected:
        console.print(f"[yellow]Disconnected ({len(disconnected)}):[/yellow]")
        for eid in disconnected:
            console.print(f"  • {eid}")
    else:
        noun = "entity + references" if refs else "entities"
        console.print(f"[green]All {noun} connected to root users.[/green]")


@graph.command(name='suggest')
@click.option('--max', '-m', default=10, help='Maximum suggestions')
@click.pass_context
def graph_suggest(ctx, max):
    """Suggest connections for orphaned references

    Examples:
        know graph suggest              # Show top 10 suggestions
        know graph suggest --max 20     # Show top 20
    """
    from src.reference_tools import ReferenceManager

    ref_mgr = ReferenceManager(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])
    suggestions = ref_mgr.suggest_reference_connections(max_suggestions=max)

    if not suggestions:
        console.print("[yellow]No suggestions found[/yellow]")
        return

    console.print(f"\n[bold]Suggested Connections[/bold]\n")

    for ref_id, entity_id, score in suggestions:
        console.print(f"[cyan]{ref_id}[/cyan] → [green]{entity_id}[/green] ({score}%)")


@check.command(name='gap-analysis')
@click.argument('entity_id', required=False)
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def check_link_gap_analysis(ctx, entity_id, json_output):
    """Analyze implementation gaps in dependency chains

    Examples:
        know check gap-analysis feature:auth
        know check gap-analysis
        know check gap-analysis feature:checkout --json
    """
    from src.gap_analysis import GapAnalyzer, ChainStatus

    analyzer = GapAnalyzer(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])

    if entity_id:
        # Analyze specific entity
        chains = analyzer.analyze_chain(entity_id)

        if json_output:
            import json
            result = {
                'entity': entity_id,
                'chains': [(path, status.value) for path, status in chains]
            }
            console.print(json.dumps(result, indent=2))
        else:
            console.print(f"\n[bold]Gap Analysis for {entity_id}:[/bold]\n")
            for path, status in chains:
                if status == ChainStatus.COMPLETE:
                    console.print(f"[green]✓[/green] {path}")
                elif status == ChainStatus.PARTIAL:
                    console.print(f"[yellow]⚠[/yellow] {path} (partial)")
                else:
                    console.print(f"[red]✗[/red] {path} ({status.value})")
    else:
        # Analyze all users and objectives
        results = analyzer.analyze_all_users_and_objectives()

        if json_output:
            import json
            output = {
                'summary': results['summary'],
                'chains': [(path, status.value) for path, status in results['chains']]
            }
            console.print(json.dumps(output, indent=2))
        else:
            summary = results['summary']
            console.print("\n[bold cyan]Gap Analysis Summary[/bold cyan]\n")
            console.print(f"Total Entities: {summary['total']}")
            console.print(f"[green]Complete: {summary['complete']}[/green]")
            console.print(f"[yellow]Partial: {summary['partial']}[/yellow]")
            console.print(f"[red]Incomplete: {summary['incomplete']}[/red]")


@check.command(name='gap-missing')
@click.pass_context
def check_link_gap_missing(ctx):
    """List missing connections in dependency chains

    Examples:
        know check gap-missing
    """
    from src.gap_analysis import GapAnalyzer

    analyzer = GapAnalyzer(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])
    missing = analyzer.list_missing_connections()

    console.print("\n[bold cyan]Missing Connections[/bold cyan]\n")

    for gap_type, entities in missing.items():
        if entities:
            label = gap_type.replace('_', ' ').title()
            console.print(f"[yellow]{label}:[/yellow]")
            for e in entities:
                console.print(f"  • {e}")
            console.print()


@check.command(name='gap-summary')
@click.pass_context
def check_link_gap_summary(ctx):
    """Show implementation summary

    Examples:
        know check gap-summary
    """
    from src.gap_analysis import GapAnalyzer

    analyzer = GapAnalyzer(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])
    summary = analyzer.get_implementation_summary()

    console.print("\n[bold cyan]Implementation Summary[/bold cyan]\n")

    entities = summary['entities']
    console.print(f"Users: {entities['users']}")
    console.print(f"Objectives: {entities['objectives']}")
    console.print(f"Features: {entities['features']}")
    console.print(f"Actions: {entities['actions']}")
    console.print(f"Components: {entities['components']['total']}")
    console.print(f"  └─ With Dependencies: {entities['components']['with_dependencies']}")

    rate = summary['completion_rate']
    color = "green" if rate >= 80 else "yellow" if rate >= 50 else "red"
    console.print(f"\nOverall Completion: [{color}]{rate}%[/{color}]")


@check.command(name='ref-types')
@click.option('--filter', '-f', 'filter_term', default='', help='Filter by name or description')
@click.pass_context
def check_ref_types(ctx, filter_term):
    """List all available reference types and their descriptions

    Shows every valid reference type from the active dependency rules,
    with descriptions. Use this when deciding which reference type to
    add to an entity.

    Examples:
        know check ref-types
        know -g .ai/know/code-graph.json check ref-types
        know check ref-types --filter config
        know check ref-types --filter model
    """
    rules_path = ctx.obj.get('rules_path')
    if not rules_path:
        console.print("[red]✗ No rules file loaded. Use -g to specify a graph.[/red]")
        return

    import json as json_mod
    from pathlib import Path

    rp = Path(rules_path)
    if not rp.exists():
        console.print(f"[red]✗ Rules file not found: {rules_path}[/red]")
        return

    with open(rp) as f:
        rules = json_mod.load(f)

    ref_types = rules.get('reference_dependency_rule', {}).get('reference_types', [])
    descriptions = rules.get('reference_description', {})

    term = filter_term.lower()
    rows = []
    for rt in sorted(ref_types):
        desc = descriptions.get(rt, '')
        if term and term not in rt.lower() and term not in desc.lower():
            continue
        deprecated = '[DEPRECATED' in desc
        rows.append((rt, desc, deprecated))

    table = Table(
        title=f"Reference Types ({rp.name}){f'  filter: {filter_term}' if term else ''}",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Description")

    for rt, desc, deprecated in rows:
        style = "dim" if deprecated else ""
        table.add_row(rt, desc, style=style)

    console.print(table)
    console.print(f"\n[dim]{len(rows)} types shown. Add with: know add <type> <key> '<json>'[/dim]")


# =============================================================================
# GRAPH CROSS subgroup — cross-graph (spec ↔ code) operations
# =============================================================================
@graph.group(name='cross', context_settings=CONTEXT_SETTINGS)
@click.pass_context
def graph_cross(ctx):
    """Cross-graph operations linking spec-graph ↔ code-graph"""
    pass


@graph_cross.command(name='connect')
@click.argument('feature', required=False)
@click.option('--dry-run', is_flag=True, help='Show what would be linked without writing')
@click.option('--spec-graph', 'spec_graph_path', default='.ai/know/spec-graph.json',
              help='Path to spec-graph.json')
@click.option('--code-graph', 'code_graph_path', default='.ai/know/code-graph.json',
              help='Path to code-graph.json')
@click.pass_context
def graph_cross_connect(ctx, feature, dry_run, spec_graph_path, code_graph_path):
    """Auto-connect spec features/components to code modules/classes via code-link refs

    Uses token overlap matching on entity keys to find likely matches.
    Operates on ALL unlinked features if no feature argument given.

    Examples:
        know graph cross connect                          # Connect all unlinked features
        know graph cross connect feature:auth             # Connect one feature
        know graph cross connect --dry-run                # Preview matches
        know graph cross connect --spec-graph .ai/know/spec-graph.json
    """
    import json as json_mod
    from pathlib import Path

    spec_path = Path(spec_graph_path)
    code_path = Path(code_graph_path)

    if not spec_path.exists():
        console.print(f"[red]✗ spec-graph not found: {spec_path}[/red]")
        return
    if not code_path.exists():
        console.print(f"[red]✗ code-graph not found: {code_path}[/red]")
        return

    with open(spec_path) as f:
        spec_data = json_mod.load(f)
    with open(code_path) as f:
        code_data = json_mod.load(f)

    spec_entities = spec_data.get('entities', {})
    code_entities = code_data.get('entities', {})
    spec_refs = spec_data.get('references', {})
    code_refs = code_data.get('references', {})
    spec_graph = spec_data.get('graph', {})
    code_graph_section = code_data.get('graph', {})

    def tokenize(key):
        """Split entity key into tokens, strip type prefix."""
        bare = key.split(':', 1)[-1] if ':' in key else key
        return set(bare.replace('_', '-').split('-'))

    def has_code_link(entity_id, graph_section, refs):
        """Return True if entity already has a code-link dependency."""
        deps = graph_section.get(entity_id, {}).get('depends_on', [])
        return any(d.startswith('code-link:') for d in deps)

    # Collect spec entities to process
    spec_entity_types = ('feature', 'component')
    spec_targets = []
    for etype in spec_entity_types:
        for key in spec_entities.get(etype, {}):
            eid = f"{etype}:{key}"
            if feature and eid != feature and not key == feature:
                continue
            if not has_code_link(eid, spec_graph, spec_refs):
                spec_targets.append(eid)

    if not spec_targets:
        console.print("[green]All spec entities already have code-link refs.[/green]")
        return

    # Collect code entities to match against
    code_entity_types = ('module', 'class', 'package', 'function')
    code_candidates = []
    for etype in code_entity_types:
        for key in code_entities.get(etype, {}):
            code_candidates.append((f"{etype}:{key}", tokenize(key)))

    console.print(f"\n[bold cyan]Cross-Graph Auto-Connect{'  (dry run)' if dry_run else ''}[/bold cyan]\n")

    matched_count = 0
    unmatched = []

    for spec_eid in spec_targets:
        spec_tokens = tokenize(spec_eid)
        # Score each code candidate by token overlap
        scored = []
        for (code_eid, code_tokens) in code_candidates:
            overlap = len(spec_tokens & code_tokens)
            if overlap > 0:
                scored.append((overlap, code_eid))
        scored.sort(reverse=True)

        if not scored:
            unmatched.append(spec_eid)
            console.print(f"  [yellow]⚠[/yellow]  {spec_eid} — no match")
            continue

        matched_code = [eid for _, eid in scored]
        score_display = ", ".join(f"{eid}(+{s})" for s, eid in scored[:3])
        console.print(f"  [green]✓[/green]  {spec_eid} → {score_display}")
        matched_count += 1

        if dry_run:
            continue

        # --- Write spec-graph code-link ---
        link_key = spec_eid.replace(':', '-') + '-code'
        modules = [e for e in matched_code if e.startswith('module:')]
        classes = [e for e in matched_code if e.startswith('class:')]
        packages = [e for e in matched_code if e.startswith('package:')]

        spec_refs.setdefault('code-link', {})[link_key] = {
            'modules': modules,
            'classes': classes,
            'packages': packages,
            'status': 'in-progress'
        }
        ref_id = f"code-link:{link_key}"
        spec_graph.setdefault(spec_eid, {}).setdefault('depends_on', [])
        if ref_id not in spec_graph[spec_eid]['depends_on']:
            spec_graph[spec_eid]['depends_on'].append(ref_id)

        # --- Write code-graph code-link for each matched entity ---
        spec_type, spec_key = spec_eid.split(':', 1)
        for code_eid in matched_code[:3]:  # top 3 matches
            code_link_key = code_eid.replace(':', '-') + '-spec'
            existing = code_refs.get('code-link', {}).get(code_link_key, {})
            # Merge: don't overwrite existing feature/component if already set
            code_refs.setdefault('code-link', {})[code_link_key] = {
                'feature': existing.get('feature') or (spec_eid if spec_type == 'feature' else ''),
                'component': existing.get('component') or (spec_eid if spec_type == 'component' else ''),
                'status': 'in-progress'
            }
            code_ref_id = f"code-link:{code_link_key}"
            code_graph_section.setdefault(code_eid, {}).setdefault('depends_on', [])
            if code_ref_id not in code_graph_section[code_eid]['depends_on']:
                code_graph_section[code_eid]['depends_on'].append(code_ref_id)

    if not dry_run:
        spec_data['references'] = spec_refs
        spec_data['graph'] = spec_graph
        with open(spec_path, 'w') as f:
            json_mod.dump(spec_data, f, indent=2)

        code_data['references'] = code_refs
        code_data['graph'] = code_graph_section
        with open(code_path, 'w') as f:
            json_mod.dump(code_data, f, indent=2)

    console.print(f"\n[bold]Matched: {matched_count}/{len(spec_targets)}[/bold]")
    if unmatched:
        console.print(f"[yellow]Unmatched ({len(unmatched)}): {', '.join(unmatched)}[/yellow]")
    if not dry_run and matched_count > 0:
        console.print("[dim]Run 'know graph cross coverage' to see updated metrics.[/dim]")


@graph_cross.command(name='coverage')
@click.option('--spec-graph', 'spec_graph_path', default='.ai/know/spec-graph.json',
              help='Path to spec-graph.json')
@click.option('--code-graph', 'code_graph_path', default='.ai/know/code-graph.json',
              help='Path to code-graph.json')
@click.option('--spec-only', is_flag=True, help='Show only spec-side coverage')
@click.option('--code-only', is_flag=True, help='Show only code-side coverage')
@click.option('--json', 'json_output', is_flag=True, help='Machine-readable JSON output')
def graph_cross_coverage(spec_graph_path, code_graph_path, spec_only, code_only, json_output):
    """Show cross-graph code-link coverage: which entities lack spec↔code links

    Reports what percentage of features/components have code-link refs (spec side)
    and what percentage of modules/classes have code-link refs (code side).

    Examples:
        know graph cross coverage
        know graph cross coverage --spec-only
        know graph cross coverage --json
    """
    import json as json_mod
    from pathlib import Path

    spec_path = Path(spec_graph_path)
    code_path = Path(code_graph_path)

    def load_graph(path):
        if not path.exists():
            return None
        with open(path) as f:
            return json_mod.load(f)

    def has_code_link(entity_id, graph_section):
        deps = graph_section.get(entity_id, {}).get('depends_on', [])
        return any(d.startswith('code-link:') for d in deps)

    def coverage_for(entities, graph_section, entity_types):
        results = {}
        for etype in entity_types:
            emap = entities.get(etype, {})
            total = list(emap.keys())
            linked = [k for k in total if has_code_link(f"{etype}:{k}", graph_section)]
            missing = [f"{etype}:{k}" for k in total if f"{etype}:{k}" not in [f"{etype}:{x}" for x in linked]]
            results[etype] = {
                'total': len(total),
                'linked': len(linked),
                'missing': missing,
                'pct': round(len(linked) / len(total) * 100, 1) if total else 0.0
            }
        return results

    spec_data = load_graph(spec_path)
    code_data = load_graph(code_path)

    spec_results = {}
    code_results = {}

    if spec_data and not code_only:
        spec_results = coverage_for(
            spec_data.get('entities', {}),
            spec_data.get('graph', {}),
            ('feature', 'component')
        )

    if code_data and not spec_only:
        code_results = coverage_for(
            code_data.get('entities', {}),
            code_data.get('graph', {}),
            ('module', 'class')
        )

    if json_output:
        console.print(json_mod.dumps({'spec': spec_results, 'code': code_results}, indent=2))
        return

    console.print("\n[bold]Cross-Graph Coverage[/bold]")
    console.print("─" * 44)

    def print_section(label, results):
        console.print(f"\n[bold]{label}[/bold]")
        for etype, data in results.items():
            pct = data['pct']
            color = 'green' if pct >= 80 else 'yellow' if pct >= 50 else 'red'
            console.print(
                f"  {etype.capitalize():12s} {data['linked']:3d}/{data['total']:3d}  "
                f"[{color}]({pct}%)[/{color}]  ← has code-link"
            )

    def print_missing(label, results):
        all_missing = []
        for data in results.values():
            all_missing.extend(data['missing'])
        if all_missing:
            console.print(f"\n[yellow]Missing code-link ({label}, {len(all_missing)}):[/yellow]")
            for eid in all_missing:
                console.print(f"  • {eid}")

    if spec_results:
        print_section("Spec → Code", spec_results)
    if code_results:
        print_section("Code → Spec", code_results)

    if spec_results:
        print_missing("spec side", spec_results)
    if code_results:
        print_missing("code side", code_results)

    console.print()


# =============================================================================
# GEN group
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def gen(ctx):
    """Generate specifications, maps, and traces"""
    pass


@gen.command(name='spec')
@click.argument('entity_id')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'xml']), default='markdown',
              help='Output format')
@click.pass_context
def gen_spec(ctx, entity_id, format):
    """Generate specification for a single entity

    This command generates a specification document for an entity from the graph.
    Run multiple times to build up a complete feature specification.

    Examples:
        know gen spec feature:login-form
        know gen spec component:auth-button >> .ai/know/user-auth/spec.md
        know gen spec action:submit-credentials --format json
    """
    generator = ctx.obj['generator']

    # Verify entity exists
    try:
        entity_data = ctx.obj['entities'].get_entity(entity_id)
        if not entity_data:
            console.print(f"[red]✗ Entity not found: {entity_id}[/red]")
            suggest_did_you_mean(ctx.obj['graph'].load(), entity_id)
            return
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return

    # Generate spec
    try:
        if format == 'xml':
            # Check if this is a feature entity for XML generation
            entity_type = entity_id.split(':')[0]
            if entity_type == 'feature':
                xml_content = generator.generate_feature_spec_xml(entity_id)
                print(xml_content)
            else:
                console.print(f"[yellow]⚠ XML format only supported for feature entities[/yellow]")
                console.print(f"[dim]Use: know gen spec feature:NAME --format xml[/dim]")
                return
        elif format == 'json':
            # Output as JSON
            spec_content = generator.generate_entity_spec(entity_id, include_deps=True)
            spec_data = {
                'entity_id': entity_id,
                'entity_data': entity_data,
                'spec': spec_content
            }
            print(json.dumps(spec_data, indent=2))
        else:
            # Output as markdown
            spec_content = generator.generate_entity_spec(entity_id, include_deps=True)
            entity_type = entity_id.split(':')[0]
            entity_name = entity_id.split(':', 1)[1]

            print(f"\n## {entity_type.capitalize()}: {entity_name}\n")
            print(f"**Entity ID:** `{entity_id}`\n")

            # Print entity details
            if entity_data.get('description'):
                print(f"**Description:** {entity_data['description']}\n")

            # Print dependencies
            deps = ctx.obj['deps'].get_dependencies(entity_id)
            if deps:
                print(f"**Dependencies:**")
                for dep in deps:
                    print(f"- `{dep}`")
                print()

            # Print references if any
            refs = entity_data.get('refs', [])
            if refs:
                print(f"**References:**")
                for ref in refs:
                    print(f"- `{ref}`")
                print()

            # Print spec content
            if spec_content and spec_content.strip():
                print(f"**Generated Specification:**\n")
                print(spec_content)

            print("\n---\n")

    except Exception as e:
        console.print(f"[red]✗ Error generating spec: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


@gen.command(name='feature-spec')
@click.argument('feature_id')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', type=click.Choice(['markdown', 'xml']), default='markdown',
              help='Output format')
@click.pass_context
def gen_feature_spec(ctx, feature_id, output, format):
    """Generate detailed feature specification

    Examples:
        know gen feature-spec feature:auth
        know gen feature-spec feature:checkout -o spec.md
        know gen feature-spec feature:auth --format xml
    """
    generator = ctx.obj['generator']

    if format == 'xml':
        spec_text = generator.generate_feature_spec_xml(feature_id)
    else:
        spec_text = generator.generate_feature_spec(feature_id)

    if output:
        Path(output).write_text(spec_text)
        console.print(f"[green]✓ Feature spec written to {output}[/green]")
    else:
        console.print(spec_text)


@gen.command(name='docs')
@click.argument('feature_id')
@click.option('--compare', is_flag=True, help='Compare with existing .md files and show differences')
@click.pass_context
def gen_docs(ctx, feature_id, compare):
    """Generate .md files from graph for a feature (validation baseline)

    Generates markdown files from the graph structure to validate completeness.
    Output goes to .ai/know/features/<feature-name>/.generated/

    Examples:
        know gen docs feature:auth
        know gen docs feature:auth --compare
    """
    from pathlib import Path
    import json

    graph = ctx.obj['graph']
    graph_data = graph.load()

    # Parse feature ID
    if not feature_id.startswith('feature:'):
        console.print(f"[red]✗ Must be a feature entity (e.g., feature:auth)[/red]")
        return

    feature_key = feature_id.split(':', 1)[1]

    # Get feature entity
    features = graph_data.get('entities', {}).get('feature', {})
    if feature_key not in features:
        console.print(f"[red]✗ Feature not found: {feature_id}[/red]")
        return

    feature_data = features[feature_key]
    feature_name = feature_data.get('name', feature_key)
    feature_desc = feature_data.get('description', '')

    # Create output directory
    output_dir = Path(f".ai/know/features/{feature_key}/.generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[cyan]Generating docs for {feature_id}...[/cyan]\n")

    # Get dependencies
    deps = graph_data.get('graph', {}).get(feature_id, {}).get('depends_on', [])

    # Separate by type
    users = [d for d in deps if d.startswith('user:')]
    objectives = [d for d in deps if d.startswith('objective:')]
    actions = [d for d in deps if d.startswith('action:')]
    components = []
    operations = []
    references = [d for d in deps if ':' in d and d.split(':')[0] in graph_data.get('references', {})]

    # Get components and operations from actions
    for action_id in actions:
        action_deps = graph_data.get('graph', {}).get(action_id, {}).get('depends_on', [])
        for dep in action_deps:
            if dep.startswith('component:'):
                components.append(dep)
                # Get operations from components
                comp_deps = graph_data.get('graph', {}).get(dep, {}).get('depends_on', [])
                operations.extend([d for d in comp_deps if d.startswith('operation:')])

    # Get meta data
    meta = graph_data.get('meta', {})
    phases = meta.get('phases', {})
    requirements = meta.get('requirements', {})
    qa_sessions = meta.get('qa_sessions', {})
    architecture = meta.get('architecture', {})

    # Find feature phase and status
    feature_phase = None
    feature_status = None
    for phase_name, phase_features in phases.items():
        if feature_id in phase_features or feature_key in phase_features:
            feature_phase = phase_name
            phase_data = phase_features.get(feature_id) or phase_features.get(feature_key)
            if isinstance(phase_data, dict):
                feature_status = phase_data.get('status', 'unknown')
            break

    # === GENERATE overview.md ===
    overview_content = f"""# Feature: {feature_name}

## Description

{feature_desc}

## Users

"""

    # Add users
    if users:
        for user_id in users:
            user_key = user_id.split(':', 1)[1]
            user_data = graph_data.get('entities', {}).get('user', {}).get(user_key, {})
            user_name = user_data.get('name', user_key)
            user_desc = user_data.get('description', '')
            overview_content += f"- `{user_id}` - {user_desc}\n"
    else:
        overview_content += "To be determined during `/know:add` phase.\n"

    overview_content += "\n## Objectives\n\n"

    # Add objectives
    if objectives:
        for obj_id in objectives:
            obj_key = obj_id.split(':', 1)[1]
            obj_data = graph_data.get('entities', {}).get('objective', {}).get(obj_key, {})
            obj_name = obj_data.get('name', obj_key)
            obj_desc = obj_data.get('description', '')
            overview_content += f"- `{obj_id}` - {obj_desc}\n"
    else:
        overview_content += "To be determined during `/know:add` phase.\n"

    overview_content += "\n## Components\n\n"

    # Add components
    if components:
        for comp_id in sorted(set(components)):
            comp_key = comp_id.split(':', 1)[1]
            comp_data = graph_data.get('entities', {}).get('component', {}).get(comp_key, {})
            comp_name = comp_data.get('name', comp_key)
            comp_desc = comp_data.get('description', '')
            overview_content += f"- `{comp_id}` - {comp_desc}\n"
    else:
        overview_content += "To be determined during `/know:build` phase.\n"

    # Add success criteria from feature data or requirements
    overview_content += "\n## Success Criteria\n\n"
    if 'success_criteria' in feature_data:
        for i, criterion in enumerate(feature_data['success_criteria'], 1):
            overview_content += f"{i}. {criterion}\n"
    elif requirements:
        feature_reqs = [k for k, v in requirements.items() if v.get('feature') == feature_id]
        for i, req_key in enumerate(feature_reqs, 1):
            req = requirements[req_key]
            status_icon = "✅" if req.get('status') == 'complete' else "⏳"
            overview_content += f"{i}. {status_icon} {req.get('description', req_key)}\n"
    else:
        overview_content += "To be determined during `/know:add` phase.\n"

    # Add constraints
    overview_content += "\n## Constraints\n\n"
    if 'constraints' in feature_data:
        for constraint in feature_data['constraints']:
            overview_content += f"- **{constraint.get('name', 'Constraint')}**: {constraint.get('description', '')}\n"
    else:
        overview_content += "To be determined during `/know:add` phase.\n"

    # Add status
    overview_content += f"\n## Status\n\n"
    if feature_phase:
        overview_content += f"- **Phase**: {feature_phase}\n"
    if feature_status:
        overview_content += f"- **Status**: {feature_status}\n"
    if not feature_phase and not feature_status:
        overview_content += "- **Phase**: Not yet scheduled\n"

    # Write overview.md
    overview_path = output_dir / "overview.md"
    overview_path.write_text(overview_content)
    console.print(f"[green]✓[/green] {overview_path}")

    # === GENERATE spec.md ===
    spec_content = f"""# Spec: {feature_name}

_Generated from graph structure_

## Architecture

See [plan.md](./plan.md) for detailed architecture.

## Components

"""

    if components:
        for comp_id in sorted(set(components)):
            comp_key = comp_id.split(':', 1)[1]
            comp_data = graph_data.get('entities', {}).get('component', {}).get(comp_key, {})
            comp_name = comp_data.get('name', comp_key)
            comp_desc = comp_data.get('description', '')
            spec_content += f"### {comp_name}\n\n{comp_desc}\n\n"

            # Get operations for this component
            comp_ops = [op for op in operations if op in graph_data.get('graph', {}).get(comp_id, {}).get('depends_on', [])]
            if comp_ops:
                spec_content += "**Operations:**\n\n"
                for op_id in comp_ops:
                    op_key = op_id.split(':', 1)[1]
                    op_data = graph_data.get('entities', {}).get('operation', {}).get(op_key, {})
                    op_name = op_data.get('name', op_key)
                    spec_content += f"- `{op_id}`: {op_name}\n"
                spec_content += "\n"
    else:
        spec_content += "To be determined during `/know:build` phase.\n\n"

    # Add references if any
    if references:
        spec_content += "## References\n\n"
        for ref_id in references:
            ref_type, ref_key = ref_id.split(':', 1)
            ref_data = graph_data.get('references', {}).get(ref_type, {}).get(ref_key, {})
            if isinstance(ref_data, dict):
                ref_title = ref_data.get('title') or ref_data.get('name') or ref_key
                spec_content += f"- `{ref_id}`: {ref_title}\n"

    # Write spec.md
    spec_path = output_dir / "spec.md"
    spec_path.write_text(spec_content)
    console.print(f"[green]✓[/green] {spec_path}")

    # === GENERATE plan.md ===
    plan_content = f"""# Plan: {feature_name}

## Objective

{feature_desc}

## Architecture

"""

    # Add architecture decisions if exist
    if feature_id in architecture or feature_key in architecture:
        arch_data = architecture.get(feature_id) or architecture.get(feature_key)
        if isinstance(arch_data, dict):
            if 'approach' in arch_data:
                plan_content += f"### Chosen Approach\n\n{arch_data['approach']}\n\n"
            if 'alternatives' in arch_data:
                plan_content += "### Alternatives Considered\n\n"
                for alt in arch_data['alternatives']:
                    plan_content += f"- {alt}\n"
                plan_content += "\n"
            if 'rationale' in arch_data:
                plan_content += f"### Rationale\n\n{arch_data['rationale']}\n\n"
    else:
        plan_content += "To be determined during `/know:build` phase.\n\n"

    plan_content += "## Implementation Approach\n\n"

    # List components and their operations
    if components:
        for comp_id in sorted(set(components)):
            comp_key = comp_id.split(':', 1)[1]
            comp_data = graph_data.get('entities', {}).get('component', {}).get(comp_key, {})
            comp_name = comp_data.get('name', comp_key)
            plan_content += f"### {comp_name}\n\n"

            # Get operations
            comp_deps = graph_data.get('graph', {}).get(comp_id, {}).get('depends_on', [])
            comp_ops = [d for d in comp_deps if d.startswith('operation:')]

            if comp_ops:
                for op_id in comp_ops:
                    op_key = op_id.split(':', 1)[1]
                    op_data = graph_data.get('entities', {}).get('operation', {}).get(op_key, {})
                    op_name = op_data.get('name', op_key)
                    op_desc = op_data.get('description', '')
                    plan_content += f"**{op_name}**\n\n{op_desc}\n\n"
            else:
                plan_content += "Operations to be determined.\n\n"
    else:
        plan_content += "To be determined during `/know:build` phase.\n\n"

    # Write plan.md
    plan_path = output_dir / "plan.md"
    plan_path.write_text(plan_content)
    console.print(f"[green]✓[/green] {plan_path}")

    # === GENERATE todo.md (if requirements exist) ===
    feature_reqs = {k: v for k, v in requirements.items() if v.get('feature') == feature_id}
    if feature_reqs:
        todo_content = f"""# TODO: {feature_name}

## Requirements

"""
        for req_key, req_data in feature_reqs.items():
            status = req_data.get('status', 'pending')
            status_icons = {
                'pending': '⏳',
                'in-progress': '🔄',
                'blocked': '🚫',
                'complete': '✅',
                'verified': '✅'
            }
            icon = status_icons.get(status, '⏳')
            desc = req_data.get('description', req_key)
            todo_content += f"- [{icon}] {desc} ({status})\n"

        todo_path = output_dir / "todo.md"
        todo_path.write_text(todo_content)
        console.print(f"[green]✓[/green] {todo_path}")

    # === GENERATE adrs.md (if architecture decisions exist) ===
    if feature_id in architecture or feature_key in architecture:
        arch_data = architecture.get(feature_id) or architecture.get(feature_key)
        if isinstance(arch_data, dict) and arch_data:
            adrs_content = f"""# Architecture Decisions: {feature_name}

"""
            if 'decisions' in arch_data:
                for i, decision in enumerate(arch_data['decisions'], 1):
                    adrs_content += f"## ADR-{i}: {decision.get('title', 'Decision')}\n\n"
                    adrs_content += f"**Status**: {decision.get('status', 'accepted')}\n\n"
                    adrs_content += f"### Context\n\n{decision.get('context', '')}\n\n"
                    adrs_content += f"### Decision\n\n{decision.get('decision', '')}\n\n"
                    if 'consequences' in decision:
                        adrs_content += f"### Consequences\n\n{decision['consequences']}\n\n"
            else:
                adrs_content += "## Primary Architecture Decision\n\n"
                if 'approach' in arch_data:
                    adrs_content += f"**Chosen Approach**: {arch_data['approach']}\n\n"
                if 'rationale' in arch_data:
                    adrs_content += f"**Rationale**: {arch_data['rationale']}\n\n"
                if 'alternatives' in arch_data:
                    adrs_content += "**Alternatives Considered**:\n\n"
                    for alt in arch_data['alternatives']:
                        adrs_content += f"- {alt}\n"

            adrs_path = output_dir / "adrs.md"
            adrs_path.write_text(adrs_content)
            console.print(f"[green]✓[/green] {adrs_path}")

    # === GENERATE exploration.md (if qa_sessions exist) ===
    feature_qa = {k: v for k, v in qa_sessions.items() if feature_id in str(v)}
    if feature_qa:
        exploration_content = f"""# Exploration: {feature_name}

## Questions & Answers

"""
        for qa_key, qa_data in feature_qa.items():
            if isinstance(qa_data, dict):
                exploration_content += f"### {qa_data.get('question', qa_key)}\n\n"
                exploration_content += f"{qa_data.get('answer', '')}\n\n"

        exploration_path = output_dir / "exploration.md"
        exploration_path.write_text(exploration_content)
        console.print(f"[green]✓[/green] {exploration_path}")

    console.print(f"\n[green]✓ Generated docs in {output_dir}[/green]")

    # === COMPARE with existing files if requested ===
    if compare:
        console.print(f"\n[cyan]Comparing with existing files...[/cyan]\n")
        existing_dir = output_dir.parent

        for gen_file in output_dir.glob("*.md"):
            existing_file = existing_dir / gen_file.name
            if existing_file.exists():
                # Simple line count comparison
                gen_lines = gen_file.read_text().strip().split('\n')
                existing_lines = existing_file.read_text().strip().split('\n')

                if gen_lines == existing_lines:
                    console.print(f"[green]✓[/green] {gen_file.name}: Identical")
                else:
                    console.print(f"[yellow]△[/yellow] {gen_file.name}: Differs ({len(gen_lines)} vs {len(existing_lines)} lines)")
                    console.print(f"  [dim]Generated: {gen_file}[/dim]")
                    console.print(f"  [dim]Existing:  {existing_file}[/dim]")
            else:
                console.print(f"[blue]○[/blue] {gen_file.name}: No existing file to compare")


@gen.command(name='sitemap')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def gen_sitemap(ctx, output):
    """Generate sitemap of all interfaces

    Examples:
        know gen sitemap
        know gen sitemap -o .ai/know/sitemap.md
    """
    sitemap_text = ctx.obj['generator'].generate_sitemap()

    if output:
        Path(output).write_text(sitemap_text)
        console.print(f"[green]✓ Sitemap written to {output}[/green]")
    else:
        console.print(sitemap_text)


@gen.command(name='code-graph')
@click.option('--codemap', '-c', default='.ai/codemap.json', help='Input codemap.json path')
@click.option('--existing', '-e', help='Existing code-graph.json to preserve references')
@click.option('--output', '-o', default='.ai/know/code-graph.json', help='Output code-graph.json path')
@click.option('--source-dir', '-s', default=None, help='Source directory for file paths (auto-reads from codemap.json if omitted)')
def gen_code_graph(codemap, existing, output, source_dir):
    """Generate code-graph from codemap AST parsing.

    This command regenerates code-graph entities (modules, classes, functions)
    from codemap.json while preserving manually curated references
    (product-component, external-dep).

    Examples:
        # Generate from existing codemap
        know gen code-graph

        # Preserve existing references
        know gen code-graph --existing .ai/know/code-graph.json

        # Custom paths
        know gen code-graph -c .ai/codemap.json -o .ai/code-graph-new.json
    """
    from src.codemap_to_graph import CodeGraphGenerator

    # Check if codemap exists
    if not Path(codemap).exists():
        console.print(f"[red]✗ Codemap not found: {codemap}[/red]")
        console.print(f"[dim]First generate a codemap:  know gen codemap <src-dir>[/dim]")
        console.print(f"[dim]Then retry:                 know gen code-graph[/dim]")
        return

    # If no existing specified but output exists, use output as existing
    if not existing and Path(output).exists():
        existing = output
        console.print(f"[dim]Using existing code-graph for reference preservation: {output}[/dim]")

    try:
        generator = CodeGraphGenerator(source_dir=source_dir)
        code_graph = generator.generate_from_codemap(
            codemap_path=codemap,
            existing_graph_path=existing,
            output_path=output
        )

        # Stats
        module_count = len(code_graph['entities'].get('module', {}))
        class_count = len(code_graph['entities'].get('class', {}))
        func_count = len(code_graph['entities'].get('function', {}))
        prod_comp_count = len(code_graph['references'].get('product-component', {}))
        ext_dep_count = len(code_graph['references'].get('external-dep', {}))

        console.print(f"[green]✓ Code-graph generated: {output}[/green]")
        console.print(f"  Modules: {module_count}")
        console.print(f"  Classes: {class_count}")
        console.print(f"  Functions: {func_count}")
        console.print(f"  Product-component refs: {prod_comp_count} (preserved)")
        console.print(f"  External deps: {ext_dep_count} (merged)")

    except Exception as e:
        console.print(f"[red]✗ Error generating code-graph: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


@gen.command(name='codemap')
@click.argument('source_dir')
@click.option('--lang', '-l', default='auto', help='Language (python, typescript, auto)')
@click.option('--output', '-o', default='.ai/codemap.json', help='Output file path')
@click.option('--heat', is_flag=True, help='Enrich output with git-based heat scores')
def gen_codemap(source_dir, lang, output, heat):
    """Generate code structure map with optional heat scoring.

    Scans source directory with ast-grep and outputs structured JSON
    of modules, classes, functions, imports.

    Examples:
        know gen codemap know/src
        know gen codemap know/src --heat
        know gen codemap know/src --heat --output .ai/codemap-heated.json
        know gen codemap www_v2/src --lang typescript
    """
    import subprocess as sp

    script = Path(__file__).parent.parent / "scripts" / "codemap" / "codemap.sh"
    if not script.exists():
        console.print(f"[red]✗ codemap.sh not found at {script}[/red]")
        sys.exit(1)

    cmd = [str(script), source_dir, "--lang", lang, "--output", output]
    if heat:
        cmd.append("--heat")

    result = sp.run(cmd, capture_output=False)
    sys.exit(result.returncode)


@gen.command(name='trace')
@click.argument('entity_id')
@click.option('--code-graph', '-c', help='Path to code-graph.json (required for cross-graph tracing)')
@click.option('--spec-graph', '-s', help='Path to spec-graph.json (required for cross-graph tracing)')
@click.pass_context
def gen_trace(ctx, entity_id, code_graph, spec_graph):
    """Trace entity across product-code boundary showing full upstream/downstream chain

    Examples:
        know -g .ai/know/spec-graph.json gen trace component:cli-commands -c .ai/know/code-graph.json
        know -g .ai/know/code-graph.json gen trace module:auth-handler -s .ai/know/spec-graph.json
    """
    from pathlib import Path
    import json

    current_graph = ctx.obj['graph']
    current_graph_data = current_graph.load()

    # Determine which graph we're starting from
    current_graph_path = ctx.obj.get('graph_path', '.ai/know/spec-graph.json')
    is_spec_graph = 'spec-graph' in str(current_graph_path).lower()

    console.print(f"\n[bold cyan]Tracing {entity_id}[/bold cyan]\n")

    # === UPSTREAM (what this entity depends on) ===
    console.print("[bold yellow]⬆ UPSTREAM (Dependencies):[/bold yellow]\n")

    upstream = current_graph.find_dependencies(entity_id, recursive=True)
    if upstream:
        for dep in sorted(upstream):
            console.print(f"  • {dep}")
    else:
        console.print("  [dim](no upstream dependencies)[/dim]")

    # === CURRENT ===
    console.print(f"\n[bold green]→ CURRENT:[/bold green] {entity_id}")

    # === DOWNSTREAM (what depends on this entity) ===
    console.print(f"\n[bold yellow]⬇ DOWNSTREAM (Dependents):[/bold yellow]\n")

    downstream = current_graph.find_dependents(entity_id, recursive=True)
    if downstream:
        for dep in sorted(downstream):
            console.print(f"  • {dep}")
    else:
        console.print("  [dim](no downstream dependents)[/dim]")

    # === CROSS-GRAPH LINKS ===
    if is_spec_graph and code_graph:
        # Starting from spec-graph, look for modules that link to this component
        console.print(f"\n[bold magenta]🔗 CROSS-GRAPH LINKS (Code Graph):[/bold magenta]\n")

        code_graph_path = Path(code_graph)
        if code_graph_path.exists():
            with open(code_graph_path, 'r') as f:
                code_graph_data = json.load(f)

            # Find product-component references that point to this entity
            linked_modules = []
            for ref_key, ref_data in code_graph_data.get('references', {}).get('product-component', {}).items():
                if ref_data.get('component') == entity_id:
                    linked_modules.append(f"module:{ref_key}")

            if linked_modules:
                for mod in sorted(linked_modules):
                    console.print(f"  • {mod} (implements this component)")
            else:
                console.print("  [dim](no code modules implement this component)[/dim]")
        else:
            console.print(f"  [red]Code graph not found: {code_graph}[/red]")

    elif not is_spec_graph and spec_graph:
        # Starting from code-graph, show what spec components this module implements
        console.print(f"\n[bold magenta]🔗 CROSS-GRAPH LINKS (Spec Graph):[/bold magenta]\n")

        # Extract module name from entity_id (e.g., "module:auth-handler" -> "auth-handler")
        if entity_id.startswith('module:'):
            module_key = entity_id.split(':', 1)[1]

            # Check product-component references
            product_refs = current_graph_data.get('references', {}).get('product-component', {})
            if module_key in product_refs:
                ref_data = product_refs[module_key]
                component = ref_data.get('component', 'N/A')
                feature = ref_data.get('feature', 'N/A')

                console.print(f"  • Implements: {component}")
                console.print(f"  • Part of feature: {feature}")

                # Load spec graph and show upstream/downstream for the component
                if spec_graph:
                    spec_graph_path = Path(spec_graph)
                    if spec_graph_path.exists():
                        console.print(f"\n  [dim]Tracing {component} in spec graph...[/dim]")
                    else:
                        console.print(f"  [red]Spec graph not found: {spec_graph}[/red]")
            else:
                console.print("  [dim](this module doesn't implement any spec components)[/dim]")
        else:
            console.print("  [dim](cross-graph links only work for module entities)[/dim]")

    elif not code_graph and not spec_graph:
        console.print(f"\n[dim]Tip: Use -c and -s flags to trace across graphs[/dim]")
        console.print(f"[dim]Example: know -g .ai/know/spec-graph.json gen trace {entity_id} -c .ai/know/code-graph.json[/dim]")

    console.print()


@gen.command(name='trace-matrix')
@click.option('--type', '-t', 'entity_type', default='feature',
              help='Entity type to trace (default: feature)')
@click.option('--full', '-f', is_flag=True, help='Show full chain including operations')
@click.pass_context
def gen_trace_matrix(ctx, entity_type, full):
    """Show requirement traceability matrix - chains from users to implementation

    Displays how requirements flow through the graph:
    user → objective → feature → action → component → operation

    Examples:
        know gen trace-matrix                    # Trace all features
        know gen trace-matrix -t component       # Trace all components
        know gen trace-matrix --full             # Include operations in chain
    """
    graph = ctx.obj['graph']
    deps = ctx.obj['deps']
    entities = ctx.obj['entities']

    graph_data = graph.load()

    console.print(f"\n[bold cyan]Requirement Traceability Matrix[/bold cyan]\n")

    # Get all entities of the specified type
    target_entities = []
    entity_section = graph_data.get('entities', {}).get(entity_type, {})
    for key in entity_section.keys():
        target_entities.append(f"{entity_type}:{key}")

    if not target_entities:
        console.print(f"[yellow]No {entity_type} entities found[/yellow]")
        return

    # Chain order for tracing upward
    chain_order = ['operation', 'component', 'action', 'feature', 'objective', 'user']
    if not full:
        chain_order = ['component', 'action', 'feature', 'objective', 'user']

    for entity_id in sorted(target_entities):
        # Build the trace chain going upstream
        chain = [entity_id]
        current = entity_id

        # Find upstream path
        visited = set()
        while current and current not in visited:
            visited.add(current)
            # Get what this entity depends on (upstream)
            upstream = deps.get_dependencies(current)
            if not upstream:
                break

            # Find the next entity in the chain order
            current_type = current.split(':')[0]
            try:
                current_idx = chain_order.index(current_type)
            except ValueError:
                current_idx = -1

            next_entity = None
            for up in upstream:
                up_type = up.split(':')[0]
                try:
                    up_idx = chain_order.index(up_type)
                    if up_idx > current_idx:
                        next_entity = up
                        break
                except ValueError:
                    continue

            if next_entity:
                chain.append(next_entity)
                current = next_entity
            else:
                break

        # Also trace downstream for context
        downstream_chain = []
        current = entity_id
        visited = set()
        while current and current not in visited:
            visited.add(current)
            # Get what depends on this entity (downstream)
            downstream = deps.get_dependents(current)
            if not downstream:
                break

            current_type = current.split(':')[0]
            try:
                current_idx = chain_order.index(current_type)
            except ValueError:
                current_idx = len(chain_order)

            next_entity = None
            for down in downstream:
                down_type = down.split(':')[0]
                try:
                    down_idx = chain_order.index(down_type)
                    if down_idx < current_idx:
                        next_entity = down
                        break
                except ValueError:
                    continue

            if next_entity:
                downstream_chain.append(next_entity)
                current = next_entity
            else:
                break

        # Combine: downstream (reversed) + current chain (reversed to show user first)
        full_chain = list(reversed(chain))
        if downstream_chain:
            full_chain.extend(downstream_chain)

        # Print the chain
        if len(full_chain) > 1:
            chain_str = " → ".join(full_chain)
            console.print(f"  {chain_str}")
        else:
            console.print(f"  {entity_id} [dim](no chain)[/dim]")

    console.print()

    # Summary
    console.print(f"[dim]Traced {len(target_entities)} {entity_type} entities[/dim]")
    console.print(f"[dim]Use --full to include operations in the chain[/dim]\n")


# Rules subgroup under gen
@gen.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def rules(ctx):
    """Query dependency rules and graph structure"""
    pass


def _load_rules(rules_path=None):
    """Load dependency rules from config file"""
    if rules_path is None:
        rules_path = Path(__file__).parent / "config" / "dependency-rules.json"
    else:
        rules_path = Path(rules_path)

    with open(rules_path, 'r') as f:
        return json.load(f)


@rules.command(name='describe')
@click.argument('type_name')
@click.pass_context
def rules_describe(ctx, type_name):
    """Describe entity, reference, or meta type, or list all types

    Examples:
        know -g .ai/know/spec-graph.json gen rules describe feature
        know -g .ai/know/code-graph.json gen rules describe module
        know gen rules describe business_logic
        know gen rules describe phases
        know gen rules describe entities       # List all entity types
        know gen rules describe references     # List all reference types
        know gen rules describe meta           # List all meta sections
    """
    rules_path = ctx.obj.get('rules_path') if ctx.obj else None
    rules = _load_rules(rules_path)
    type_lower = type_name.lower()

    # Handle list commands
    if type_lower in ['entities', 'entity']:
        console.print("\n[bold cyan]Available Entity Types:[/bold cyan]\n")
        for entity_type in sorted(rules.get('entity_description', {}).keys()):
            console.print(f"  • [green]{entity_type}[/green]")
        console.print("\n[dim]Use: know gen rules describe <type> for details[/dim]")
        return

    if type_lower in ['references', 'reference', 'refs']:
        console.print("\n[bold cyan]Available Reference Types:[/bold cyan]\n")
        for ref_type in sorted(rules.get('reference_description', {}).keys()):
            console.print(f"  • [green]{ref_type}[/green]")
        console.print("\n[dim]Use: know gen rules describe <type> for details[/dim]")
        return

    if type_lower == 'meta':
        console.print("\n[bold cyan]Available Meta Sections:[/bold cyan]\n")
        for meta_section in sorted(rules.get('meta_description', {}).keys()):
            console.print(f"  • [green]{meta_section}[/green]")
        console.print("\n[dim]Use: know gen rules describe <section> for details[/dim]")
        return

    # Try to find in entities
    if type_lower in rules.get('entity_description', {}):
        desc = rules['entity_description'][type_lower]
        console.print(f"\n[bold cyan]Entity Type: {type_lower}[/bold cyan]\n")
        console.print(f"[green]{desc}[/green]\n")

        # Show allowed dependencies
        allowed = rules.get('allowed_dependencies', {}).get(type_lower, [])
        if allowed:
            console.print(f"[bold]Can depend on:[/bold] {', '.join(allowed)}")
        else:
            console.print("[dim]No dependencies allowed[/dim]")

        # Show what can depend on this
        dependents = [k for k, v in rules.get('allowed_dependencies', {}).items()
                     if type_lower in v]
        if dependents:
            console.print(f"[bold]Can be depended on by:[/bold] {', '.join(dependents)}")

        # Show schema note
        entity_note = rules.get('entity_note', {})
        if 'schema' in entity_note:
            console.print(f"\n[dim]Schema: {entity_note['schema']}[/dim]")

        return

    # Try to find in references
    if type_lower in rules.get('reference_description', {}):
        desc = rules['reference_description'][type_lower]
        console.print(f"\n[bold cyan]Reference Type: {type_lower}[/bold cyan]\n")
        console.print(f"[green]{desc}[/green]\n")

        ref_note = rules.get('reference_note', {})
        console.print(f"[bold]Purpose:[/bold] {ref_note.get('purpose', 'N/A')}")
        console.print(f"[bold]Schema:[/bold] {ref_note.get('schema', 'Flexible')}")
        console.print(f"[bold]Naming:[/bold] {ref_note.get('naming', 'N/A')}")

        return

    # Try to find in meta
    if type_lower in rules.get('meta_description', {}):
        desc = rules['meta_description'][type_lower]
        console.print(f"\n[bold cyan]Meta Section: {type_lower}[/bold cyan]\n")
        console.print(f"[green]{desc}[/green]\n")

        # Show schema if available
        meta_schema = rules.get('meta_schema', {})
        if type_lower in meta_schema:
            schema = meta_schema[type_lower]
            console.print("[bold]Schema:[/bold]")

            if isinstance(schema, dict):
                for key, value in schema.items():
                    if key == 'schema':
                        console.print(f"  [yellow]Type:[/yellow] {value}")
                    elif key == 'note':
                        console.print(f"  [dim]{value}[/dim]")
                    elif key == 'examples':
                        console.print(f"  [yellow]Examples:[/yellow]")
                        if isinstance(value, list):
                            for ex in value[:3]:  # Show first 3 examples
                                console.print(f"    • {ex}")
                        elif isinstance(value, dict):
                            for k, v in list(value.items())[:3]:
                                console.print(f"    • {k}: {v}")
                    else:
                        console.print(f"  [yellow]{key}:[/yellow] {value}")
            else:
                console.print(f"  {schema}")

        return

    # Not found
    console.print(f"[red]✗ Type '{type_name}' not found[/red]")
    console.print("\n[dim]Try: entity types (feature, component, etc.), "
                 "reference types (business_logic, data-models, etc.), "
                 "or meta sections (project, phases, etc.)[/dim]")


@rules.command(name='before')
@click.argument('entity_type')
@click.pass_context
def rules_before(ctx, entity_type):
    """Show what entity types can come before this type in dependency graph

    Examples:
        know -g .ai/know/spec-graph.json gen rules before component
        know -g .ai/know/code-graph.json gen rules before module
    """
    rules_path = ctx.obj.get('rules_path') if ctx.obj else None
    rules = _load_rules(rules_path)
    type_lower = entity_type.lower()

    # Find entity types that can depend on this type
    allowed_deps = rules.get('allowed_dependencies', {})
    predecessors = [k for k, v in allowed_deps.items() if type_lower in v]

    if not predecessors:
        console.print(f"[yellow]No entity types can depend on '{entity_type}'[/yellow]")
        return

    console.print(f"\n[bold cyan]Entity types that can depend on {entity_type}:[/bold cyan]\n")
    for pred in sorted(predecessors):
        console.print(f"  • [green]{pred}[/green]")

    console.print(f"\n[dim]Meaning: These types can have {entity_type} as a dependency[/dim]")


@rules.command(name='after')
@click.argument('entity_type')
@click.pass_context
def rules_after(ctx, entity_type):
    """Show what entity types can come after this type in dependency graph

    Examples:
        know -g .ai/know/spec-graph.json gen rules after feature
        know -g .ai/know/code-graph.json gen rules after module
    """
    rules_path = ctx.obj.get('rules_path') if ctx.obj else None
    rules = _load_rules(rules_path)
    type_lower = entity_type.lower()

    allowed_deps = rules.get('allowed_dependencies', {})
    successors = allowed_deps.get(type_lower, [])

    if not successors:
        console.print(f"[yellow]'{entity_type}' cannot depend on other entities[/yellow]")
        return

    console.print(f"\n[bold cyan]{entity_type} can depend on:[/bold cyan]\n")
    for succ in sorted(successors):
        console.print(f"  • [green]{succ}[/green]")

    console.print(f"\n[dim]Meaning: {entity_type} entities can list these types as dependencies[/dim]")


@rules.command(name='graph')
@click.pass_context
def rules_graph(ctx):
    """Visualize the dual-graph architecture (spec ↔ code)

    Shows dependency structure for the current graph and how it links to its counterpart.

    Examples:
        know -g .ai/know/spec-graph.json gen rules graph     # Show spec graph structure
        know -g .ai/know/code-graph.json gen rules graph     # Show code graph structure
    """
    rules_path = ctx.obj.get('rules_path') if ctx.obj else None
    rules = _load_rules(rules_path)

    # Detect graph type
    is_code_graph = 'code-graph' in rules_path if rules_path else False
    is_spec_graph = not is_code_graph

    if is_spec_graph:
        console.print("\n[bold cyan]Spec Graph Structure[/bold cyan] (Product Intent)\n")

        # Show main chain
        console.print("[bold yellow]Product Chain:[/bold yellow]")
        chain = rules.get('notes', {}).get('chain', [])
        if chain:
            console.print("  " + " → ".join(chain))
        console.print()

        # Show entity relationships
        console.print("[bold yellow]Entity Dependencies:[/bold yellow]\n")
        allowed = rules.get('allowed_dependencies', {})

        # Build reverse lookup
        depended_on_by = {}
        for entity_type, deps in allowed.items():
            for dep in deps:
                if dep not in depended_on_by:
                    depended_on_by[dep] = []
                depended_on_by[dep].append(entity_type)

        all_types = set(allowed.keys()) | set(depended_on_by.keys())

        for entity_type in sorted(all_types):
            deps = allowed.get(entity_type, [])
            dependents = depended_on_by.get(entity_type, [])

            line = f"[cyan]{entity_type}[/cyan]"
            if deps:
                line += f" → [green]{', '.join(deps)}[/green]"
            if dependents:
                line += f" [dim](← {', '.join(dependents)})[/dim]"

            console.print(f"  {line}")

        console.print("\n[bold yellow]Cross-Graph Linking:[/bold yellow]")
        console.print("  [cyan]feature[/cyan] → [green]implementation[/green] → [yellow]graph-link[/yellow] (in code-graph)")
        console.print("  Spec features link to code via implementation references")
        console.print("  Implementation references point to graph-link IDs in code-graph")

    else:  # code-graph
        console.print("\n[bold cyan]Code Graph Structure[/bold cyan] (Codebase Architecture)\n")

        console.print("[bold yellow]Purpose:[/bold yellow]")
        purpose = rules.get('notes', {}).get('purpose', 'Universal code architecture graph')
        console.print(f"  {purpose}\n")

        # Show entity relationships
        console.print("[bold yellow]Entity Dependencies:[/bold yellow]\n")
        allowed = rules.get('allowed_dependencies', {})

        # Build reverse lookup
        depended_on_by = {}
        for entity_type, deps in allowed.items():
            for dep in deps:
                if dep not in depended_on_by:
                    depended_on_by[dep] = []
                depended_on_by[dep].append(entity_type)

        all_types = set(allowed.keys()) | set(depended_on_by.keys())

        for entity_type in sorted(all_types):
            deps = allowed.get(entity_type, [])
            dependents = depended_on_by.get(entity_type, [])

            line = f"[cyan]{entity_type}[/cyan]"
            if deps:
                line += f" → [green]{', '.join(deps)}[/green]"
            if dependents:
                line += f" [dim](← {', '.join(dependents)})[/dim]"

            console.print(f"  {line}")

        console.print("\n[bold yellow]Implementation Metadata:[/bold yellow]")
        console.print("  [cyan]implementation_type[/cyan]: full | partial | stub | aspirational")
        console.print("  [cyan]implementation_status[/cyan]: complete | in-progress | planned | deprecated")
        console.print("  [cyan]aspirational[/cyan]: true = preserve during code-graph regeneration")

        console.print("\n[bold yellow]Cross-Graph Linking:[/bold yellow]")
        console.print("  [cyan]graph-link[/cyan] reference → points to spec [yellow]feature[/yellow] and [yellow]component[/yellow]")
        console.print("  Code modules reference graph-link to indicate what spec feature they implement")

    console.print("\n[dim]═══════════════════════════════════════════════════════════[/dim]")
    console.print("\n[bold]Dual Graph Architecture:[/bold]")
    console.print("  [yellow]spec-graph.json[/yellow] ← [cyan]implementation[/cyan] → [green]graph-link[/green] ← [yellow]code-graph.json[/yellow]")
    console.print("  Bidirectional: spec features ↔ code modules")
    console.print("\n[dim]Use 'know graph traverse' to navigate between graphs[/dim]")
    console.print("[dim]Legend: → depends on | ← depended on by[/dim]")


# =============================================================================
# FEATURE group
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def feature(ctx):
    """Manage feature lifecycle, contracts, and coverage"""
    pass


@feature.command(name='status')
@click.argument('feature_id')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def feature_status(ctx, feature_id, json_output):
    """Show feature lifecycle status (planned, implemented, reviewed)

    Virtual flags computed from graph state:
    - planned: Feature exists in meta.phases
    - implemented: Code-graph links exist for this feature
    - reviewed: Git commit with [feature:id] merged to main

    Examples:
        know feature status feature:auth
        know feature status auth             # Auto-detects feature: prefix
        know feature status auth --json
    """
    import subprocess
    from pathlib import Path

    # Auto-add feature: prefix if missing
    if not feature_id.startswith('feature:'):
        feature_id = f'feature:{feature_id}'

    graph = ctx.obj['graph']
    graph_data = graph.load()

    # === CHECK PLANNED ===
    # Feature exists in meta.phases (any phase)
    phases = graph_data.get('meta', {}).get('phases', {})
    planned = False
    current_phase = None
    phase_status = None

    for phase_name, phase_features in phases.items():
        if feature_id in phase_features:
            planned = True
            current_phase = phase_name
            phase_data = phase_features[feature_id]
            if isinstance(phase_data, dict):
                phase_status = phase_data.get('status', 'unknown')
            break

    # === CHECK IMPLEMENTED ===
    # Code-graph links exist for this feature
    implemented = False
    code_modules = []

    # Check if feature has implementation references
    feature_deps = graph_data.get('graph', {}).get(feature_id, {}).get('depends_on', [])
    impl_refs = [d for d in feature_deps if d.startswith('implementation:')]

    if impl_refs:
        # Get code graph path from meta
        code_graph_path = graph_data.get('meta', {}).get('code_graph_path')
        if code_graph_path:
            code_graph_path = Path(code_graph_path)
            if code_graph_path.exists():
                with open(code_graph_path, 'r') as f:
                    code_graph_data = json.load(f)

                # Check for graph-link references pointing to this feature
                graph_links = code_graph_data.get('references', {}).get('graph-link', {})
                for link_key, link_data in graph_links.items():
                    if isinstance(link_data, dict):
                        if link_data.get('feature') == feature_id:
                            implemented = True
                            code_modules.append(f"module:{link_key}")

    # === CHECK REVIEWED ===
    # Git commit with [feature:id] merged to main
    reviewed = False
    merge_commit = None
    merge_date = None

    try:
        feature_key = feature_id.split(':', 1)[1]
        # Search for commits with [feature:key] in message on main branch
        result = subprocess.run(
            ['git', 'log', '--oneline', '--grep', f'\\[{feature_id}\\]', 'main'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            reviewed = True
            # Get first (most recent) commit
            first_line = result.stdout.strip().split('\n')[0]
            merge_commit = first_line.split()[0]

            # Get commit date
            date_result = subprocess.run(
                ['git', 'log', '-1', '--format=%ci', merge_commit],
                capture_output=True,
                text=True,
                timeout=5
            )
            if date_result.returncode == 0:
                merge_date = date_result.stdout.strip()

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Git not available or timeout
        pass

    # === OUTPUT ===
    if json_output:
        output = {
            'feature_id': feature_id,
            'planned': planned,
            'implemented': implemented,
            'reviewed': reviewed,
            'phase': current_phase,
            'phase_status': phase_status,
            'code_modules': code_modules,
            'merge_commit': merge_commit,
            'merge_date': merge_date
        }
        print(json.dumps(output, indent=2))
    else:
        console.print(f"\n[bold cyan]Feature Status: {feature_id}[/bold cyan]\n")

        # Planned
        planned_icon = "✅" if planned else "⏳"
        planned_text = f"[green]Yes[/green]" if planned else "[dim]No[/dim]"
        console.print(f"{planned_icon} [bold]Planned:[/bold] {planned_text}")
        if planned and current_phase:
            console.print(f"   Phase: {current_phase}")
            if phase_status:
                console.print(f"   Status: {phase_status}")

        # Implemented
        impl_icon = "✅" if implemented else "⏳"
        impl_text = f"[green]Yes[/green]" if implemented else "[dim]No[/dim]"
        console.print(f"{impl_icon} [bold]Implemented:[/bold] {impl_text}")
        if implemented and code_modules:
            console.print(f"   Modules: {', '.join(code_modules[:5])}")
            if len(code_modules) > 5:
                console.print(f"   ... and {len(code_modules) - 5} more")

        # Reviewed
        reviewed_icon = "✅" if reviewed else "⏳"
        reviewed_text = f"[green]Yes[/green]" if reviewed else "[dim]No[/dim]"
        console.print(f"{reviewed_icon} [bold]Reviewed:[/bold] {reviewed_text}")
        if reviewed:
            console.print(f"   Commit: {merge_commit}")
            if merge_date:
                console.print(f"   Date: {merge_date[:10]}")

        # Summary
        console.print()
        if planned and implemented and reviewed:
            console.print("[green]✓ Feature is fully complete![/green]")
        elif planned and implemented:
            console.print("[yellow]⚠ Feature implemented but not reviewed/merged[/yellow]")
        elif planned:
            console.print("[blue]📋 Feature planned but not implemented[/blue]")
        else:
            console.print("[dim]Feature not yet planned[/dim]")

        console.print()


@feature.command(name='contract')
@click.argument('feature_name')
@click.option('--show', is_flag=True, help='Show full contract YAML')
@click.option('--confidence', is_flag=True, help='Show confidence calculation')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def feature_contract(ctx, feature_name, show, confidence, json_output):
    """Display contract info for a feature.

    Examples:
        know feature contract my-feature
        know feature contract my-feature --show
        know feature contract my-feature --confidence
    """
    from src.contract_manager import ContractManager
    import yaml

    cm = ContractManager()
    contract_data = cm.load_contract(feature_name)

    if not contract_data:
        console.print(f"[red]✗ No contract found for: {feature_name}[/red]")
        sys.exit(1)

    if json_output:
        if show:
            print(json.dumps(contract_data, indent=2))
        elif confidence:
            conf = cm.calculate_confidence(feature_name)
            print(json.dumps(conf, indent=2))
        else:
            summary = cm.get_contract_summary(feature_name)
            print(json.dumps(summary, indent=2))
        return

    if show:
        console.print(f"\n[bold cyan]Contract: {feature_name}[/bold cyan]\n")
        print(yaml.dump(contract_data, default_flow_style=False, sort_keys=False))
        return

    if confidence:
        conf = cm.calculate_confidence(feature_name)
        console.print(f"\n[bold cyan]Confidence for {feature_name}[/bold cyan]\n")
        console.print(f"[bold]Score:[/bold] {conf['score']}%")
        console.print(f"\n[bold]Factors:[/bold]")
        for factor in conf['factors']:
            console.print(f"  • {factor}")
        return

    # Default: show summary
    summary = cm.get_contract_summary(feature_name)
    if not summary:
        console.print(f"[red]✗ Could not load contract summary[/red]")
        sys.exit(1)

    status_color = {
        'verified': 'green',
        'pending': 'yellow',
        'drifted': 'red'
    }.get(summary['validation_status'], 'white')

    console.print(f"\n[bold cyan]Contract: {feature_name}[/bold cyan]\n")
    console.print(f"[bold]Created:[/bold] {summary['created'][:10] if summary['created'] else 'N/A'}")
    console.print(f"[bold]Baseline:[/bold] {summary['baseline_commit'][:7] if summary['baseline_commit'] else 'N/A'}")
    console.print(f"[bold]Status:[/bold] [{status_color}]{summary['validation_status']}[/{status_color}]")
    console.print(f"[bold]Confidence:[/bold] {summary['confidence_score']}%")

    console.print(f"\n[bold]Declared:[/bold]")
    df = summary['declared_files']
    de = summary['declared_entities']
    da = summary['declared_actions']
    console.print(f"  Files: {df['creates']} creates, {df['modifies']} modifies")
    console.print(f"  Entities: {de['creates']} creates, {de['depends_on']} depends_on")
    console.print(f"  Actions: {da['verified']}/{da['total']} verified")

    console.print(f"\n[bold]Observed:[/bold]")
    of = summary['observed_files']
    console.print(f"  Files: {of['created']} created, {of['modified']} modified, {of['deleted']} deleted")

    if summary['discrepancy_count'] > 0:
        console.print(f"\n[red]Discrepancies: {summary['discrepancy_count']}[/red]")


@feature.command(name='validate-contracts')
@click.option('--feature', '-f', 'feature_filter', help='Specific feature to validate (validates all if not specified)')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def feature_validate_contracts(ctx, feature_filter, json_output):
    """Validate feature contracts for drift between declared and observed.

    Examples:
        know feature validate-contracts
        know feature validate-contracts --feature auth
        know feature validate-contracts --json"""
    from src.contract_manager import ContractManager
    from src.validation import ContractValidator

    cm = ContractManager()
    cv = ContractValidator()

    if feature_filter:
        features = [feature_filter]
    else:
        features = cm.list_all_features_with_contracts()

    if not features:
        console.print("[yellow]No features with contracts found[/yellow]")
        return

    results = []
    for feature_name in features:
        # Run validation
        validation = cm.validate_contract(feature_name)
        confidence = cm.calculate_confidence(feature_name)
        summary = cm.get_contract_summary(feature_name)

        results.append({
            'feature': feature_name,
            'status': validation['status'],
            'confidence': confidence['score'],
            'discrepancies': len(validation['discrepancies']),
            'summary': summary,
            'validation': validation
        })

    if json_output:
        print(json.dumps(results, indent=2))
        return

    # Pretty output
    has_issues = False
    for r in results:
        status_color = {
            'verified': 'green',
            'pending': 'yellow',
            'drifted': 'red',
            'error': 'red'
        }.get(r['status'], 'white')

        status_icon = {
            'verified': '✓',
            'pending': '⚠',
            'drifted': '✗',
            'error': '✗'
        }.get(r['status'], '?')

        console.print(f"\n[{status_color}]{status_icon}[/{status_color}] [bold]{r['feature']}[/bold]")
        console.print(f"  Status: [{status_color}]{r['status']}[/{status_color}]")
        console.print(f"  Confidence: {r['confidence']}%")

        if r['discrepancies'] > 0:
            has_issues = True
            console.print(f"  [red]Discrepancies: {r['discrepancies']}[/red]")
            for disc in r['validation']['discrepancies'][:5]:
                console.print(f"    • {disc['message']}")
            if len(r['validation']['discrepancies']) > 5:
                console.print(f"    ... and {len(r['validation']['discrepancies']) - 5} more")

    if has_issues:
        console.print(f"\n[yellow]⚠ Some features have contract issues[/yellow]")
        sys.exit(1)
    else:
        console.print(f"\n[green]✓ All contracts validated[/green]")


@feature.command(name='validate')
@click.argument('feature_name')
@click.option('--since', help='Override baseline (YYYY-MM-DD or commit SHA)')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.option('--code-graph', '-c', default='.ai/know/code-graph.json', help='Code graph path')
@click.pass_context
def feature_validate(ctx, feature_name, since, json_output, code_graph):
    """Check if codebase changes warrant revisiting feature plan.

    Examples:
        know feature validate auth
        know feature validate checkout --since 2026-01-01
        know feature validate auth --json"""
    from src.feature_tracker import FeatureTracker

    tracker = FeatureTracker(
        spec_graph_path=str(ctx.obj['graph'].cache.graph_path),
        code_graph_path=code_graph if Path(code_graph).exists() else None
    )

    # Verify feature exists
    feature_dir = tracker.get_feature_dir(feature_name)
    if not feature_dir:
        console.print(f"[red]✗ Feature not found: {feature_name}[/red]")
        console.print(f"[dim]  Expected: .ai/know/features/{feature_name}/[/dim]")
        sys.exit(1)

    # Ensure config.json exists (touch it = track it)
    created, _ = tracker.ensure_config(feature_name)
    if created:
        console.print(f"[dim]Created config.json for {feature_name}[/dim]")

    # Get baseline info
    baseline_ts, baseline_commit = tracker.get_feature_baseline(feature_name)
    if not baseline_ts and not baseline_commit:
        console.print(f"[yellow]⚠ No baseline found for {feature_name}[/yellow]")

    # Get changes and risk assessment
    changes = tracker.get_changed_files(feature_name, since)
    risk = tracker.assess_risk(feature_name, changes)

    if json_output:
        import json as json_module
        output = {
            'feature': feature_name,
            'baseline': {
                'timestamp': baseline_ts.isoformat() if baseline_ts else None,
                'commit': baseline_commit
            },
            'changes': changes,
            'risk': risk
        }
        print(json_module.dumps(output, indent=2))
    else:
        # Rich console output
        console.print(f"\n[bold]Feature:[/bold] {feature_name}")
        if baseline_ts:
            console.print(f"[bold]Baseline:[/bold] {baseline_ts.strftime('%Y-%m-%d %H:%M')}", end="")
            if baseline_commit:
                console.print(f" (commit: {baseline_commit[:7]})")
            else:
                console.print()
        console.print()

        # Risk summary
        console.print("[bold]Risk Assessment:[/bold]")
        counts = risk['counts']
        console.print(f"  [red]HIGH:[/red]   {counts['HIGH']} files")
        console.print(f"  [yellow]MEDIUM:[/yellow] {counts['MEDIUM']} files")
        console.print(f"  [green]LOW:[/green]    {counts['LOW']} files")
        console.print(f"  [dim]INFO:[/dim]   {counts['INFO']} files")
        console.print()

        # Changed files
        if changes:
            console.print("[bold]Changed Files:[/bold]")
            for cf in changes:
                risk_color = {'HIGH': 'red', 'MEDIUM': 'yellow', 'LOW': 'green', 'INFO': 'dim'}.get(cf['risk'], 'white')
                console.print(f"  [{risk_color}][{cf['risk']}][/{risk_color}] {cf['file']} ({len(cf['commits'])} commits)")
            console.print()

        # Recommendation
        console.print(f"[bold]Recommendation:[/bold] {risk['recommendation']}")


@feature.command(name='tag')
@click.argument('feature_name')
@click.option('--since', help='Override baseline (YYYY-MM-DD or commit SHA)')
@click.option('--auto', 'auto_tag', is_flag=True, help='Auto-tag all matching commits without prompting')
@click.option('--code-graph', '-c', default='.ai/know/code-graph.json', help='Code graph path')
@click.pass_context
def feature_tag(ctx, feature_name, since, auto_tag, code_graph):
    """Tag commits related to a feature with git notes.

    Examples:
        know feature tag auth
        know feature tag checkout --auto
        know feature tag auth --since abc123f"""
    from src.feature_tracker import FeatureTracker

    tracker = FeatureTracker(
        spec_graph_path=str(ctx.obj['graph'].cache.graph_path),
        code_graph_path=code_graph if Path(code_graph).exists() else None
    )

    # Verify feature exists
    feature_dir = tracker.get_feature_dir(feature_name)
    if not feature_dir:
        console.print(f"[red]✗ Feature not found: {feature_name}[/red]")
        sys.exit(1)

    # Ensure config.json exists (touch it = track it)
    created, _ = tracker.ensure_config(feature_name)
    if created:
        console.print(f"[dim]Created config.json for {feature_name}[/dim]")

    # Get commits
    commits = tracker.get_feature_commits(feature_name, since)

    if not commits:
        console.print(f"[yellow]⚠ No commits found for {feature_name} since baseline[/yellow]")
        sys.exit(0)

    console.print(f"\n[bold]Commits related to {feature_name}:[/bold]\n")

    for i, commit in enumerate(commits, 1):
        console.print(f"  [{i}] {commit['short_sha']} - {commit['message'][:60]}")
        if commit['files']:
            console.print(f"      [dim]Files: {', '.join(commit['files'][:3])}{'...' if len(commit['files']) > 3 else ''}[/dim]")

    console.print()

    if auto_tag:
        shas = [c['sha'] for c in commits]
    else:
        # Interactive selection
        selection = click.prompt(
            "Select commits to tag (comma-separated numbers, 'all', or 'none')",
            default='all'
        )

        if selection.lower() == 'none':
            console.print("[yellow]No commits tagged[/yellow]")
            sys.exit(0)
        elif selection.lower() == 'all':
            shas = [c['sha'] for c in commits]
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                shas = [commits[i]['sha'] for i in indices if 0 <= i < len(commits)]
            except (ValueError, IndexError):
                console.print("[red]Invalid selection[/red]")
                sys.exit(1)

    if not shas:
        console.print("[yellow]No commits selected[/yellow]")
        sys.exit(0)

    # Tag commits
    success, error = tracker.tag_commits(feature_name, shas)
    if not success:
        console.print(f"[red]✗ {error}[/red]")
        sys.exit(1)

    # Store in spec-graph
    if tracker.store_commits(feature_name, shas):
        console.print(f"[green]✓ Tagged {len(shas)} commits with know:feature:{feature_name}[/green]")
        console.print(f"[green]✓ Stored commit SHAs in spec-graph[/green]")
    else:
        console.print(f"[yellow]⚠ Tagged commits but failed to update spec-graph[/yellow]")


def _validate_feature_completion(ctx, feature_name: str) -> dict:
    """Validate feature completion via bidirectional graph linkage.

    Returns dict with:
        - passed: bool
        - has_implementation: bool
        - graph_links_valid: bool
        - bidirectional_valid: bool
        - messages: List[str]
    """
    result = {
        'passed': False,
        'has_implementation': False,
        'graph_links_valid': False,
        'bidirectional_valid': False,
        'messages': []
    }

    graph_data = ctx.obj['graph'].load()
    entity_id = f"feature:{feature_name}"

    # Check if feature has implementation references
    feature_graph = graph_data.get('graph', {}).get(entity_id, {})
    deps = feature_graph.get('depends_on', [])

    implementation_refs = [d for d in deps if d.startswith('implementation:')]

    if not implementation_refs:
        result['messages'].append(f"[yellow]⚠ Feature has no implementation references[/yellow]")
        return result

    result['has_implementation'] = True
    result['messages'].append(f"[green]✓ Feature has {len(implementation_refs)} implementation reference(s)[/green]")

    # Get code graph path from meta
    code_graph_path = graph_data.get('meta', {}).get('code_graph_path', '.ai/know/code-graph.json')
    code_graph_file = Path(code_graph_path)

    if not code_graph_file.exists():
        result['messages'].append(f"[yellow]⚠ Code graph not found: {code_graph_path}[/yellow]")
        return result

    with open(code_graph_file, 'r') as f:
        code_graph = json.load(f)

    # Check each implementation reference
    all_valid = True
    for impl_ref in implementation_refs:
        impl_key = impl_ref.split(':', 1)[1]
        impl_data = graph_data.get('references', {}).get('implementation', {}).get(impl_key)

        if not impl_data:
            result['messages'].append(f"[red]✗ Implementation reference not found: {impl_ref}[/red]")
            all_valid = False
            continue

        # Should be an array of graph-link IDs
        if not isinstance(impl_data, list):
            result['messages'].append(f"[red]✗ Implementation reference is not an array: {impl_ref}[/red]")
            all_valid = False
            continue

        # Check each graph-link exists in code graph
        for graph_link_id in impl_data:
            if not graph_link_id.startswith('graph-link:'):
                result['messages'].append(f"[red]✗ Invalid graph-link ID: {graph_link_id}[/red]")
                all_valid = False
                continue

            link_key = graph_link_id.split(':', 1)[1]
            link_data = code_graph.get('references', {}).get('graph-link', {}).get(link_key)

            if not link_data:
                result['messages'].append(f"[red]✗ Graph-link not found in code graph: {graph_link_id}[/red]")
                all_valid = False
                continue

            # Check if graph-link points back to this feature
            linked_feature = link_data.get('feature')
            if linked_feature != entity_id:
                result['messages'].append(f"[red]✗ Graph-link {graph_link_id} doesn't point back to {entity_id} (points to {linked_feature})[/red]")
                all_valid = False
            else:
                result['messages'].append(f"[dim]  ✓ {graph_link_id} → {entity_id}[/dim]")

    result['graph_links_valid'] = all_valid
    result['bidirectional_valid'] = all_valid
    result['passed'] = result['has_implementation'] and all_valid

    return result


@feature.command(name='review')
@click.argument('feature_name')
@click.option('--skip-validation', is_flag=True, help='Skip graph completion validation')
@click.option('--check-only', is_flag=True, help='Only check readiness, do not proceed to QA')
@click.pass_context
def feature_review(ctx, feature_name, skip_validation, check_only):
    """Review feature for completion: validate graph linkage and check QA readiness.

    Examples:
        know feature review auth
        know feature review checkout --check-only
        know feature review auth --skip-validation

    Shows comprehensive readiness status including:
    - Implementation linkage (spec ↔ code graph)
    - QA readiness (QA_STEPS.md, review status)
    - Requirements completion
    - Meta status

    Use --check-only to see readiness without proceeding to interactive QA.
    """
    from src.feature_tracker import FeatureTracker

    tracker = FeatureTracker(
        spec_graph_path=str(ctx.obj['graph'].cache.graph_path)
    )

    # 1. Verify feature exists
    feature_dir = tracker.get_feature_dir(feature_name)
    if not feature_dir:
        console.print(f"[red]✗ Feature not found: {feature_name}[/red]")
        console.print(f"[dim]  Expected: .ai/know/features/{feature_name}/[/dim]")
        sys.exit(1)

    console.print(f"\n[bold cyan]Feature Readiness Check: {feature_name}[/bold cyan]\n")

    ready_for_review = True
    ready_for_done = True

    # 2. Implementation Linkage Check
    console.print("[bold]Implementation Linkage:[/bold]")
    if not skip_validation:
        validation = _validate_feature_completion(ctx, feature_name)

        for msg in validation['messages']:
            console.print(f"  {msg}")

        if not validation['passed']:
            ready_for_review = False
            ready_for_done = False
    else:
        console.print("  [dim]⊘ Validation skipped[/dim]")

    console.print()

    # 3. QA Readiness Check
    console.print("[bold]QA Readiness:[/bold]")
    qa_steps_path = feature_dir / "QA_STEPS.md"
    if qa_steps_path.exists():
        console.print("  [green]✓[/green] QA_STEPS.md exists")
    else:
        console.print("  [red]✗[/red] QA_STEPS.md missing")
        console.print("  [dim]  Run `/know:build` Phase 7 to generate[/dim]")
        ready_for_review = False
        ready_for_done = False

    review_results_path = feature_dir / "review-results.md"
    if review_results_path.exists():
        console.print("  [green]✓[/green] Feature has been reviewed")
        # Could parse review-results.md to show pass/fail status
    else:
        console.print("  [yellow]⚠[/yellow] Not yet reviewed")
        ready_for_done = False

    console.print()

    # 4. Requirements Check (if they exist)
    graph_data = ctx.obj['graph'].load()
    feature_id = f"feature:{feature_name}"
    requirements = graph_data.get('meta', {}).get('requirements', {}).get(feature_id, {})

    if requirements:
        console.print("[bold]Requirements:[/bold]")
        total = len(requirements)
        complete = sum(1 for req in requirements.values() if req.get('status') == 'complete')
        verified = sum(1 for req in requirements.values() if req.get('status') == 'verified')

        if complete == total or verified == total:
            console.print(f"  [green]✓[/green] {complete + verified}/{total} requirements complete")
        else:
            console.print(f"  [yellow]⚠[/yellow] {complete + verified}/{total} requirements complete")
            ready_for_review = False
            ready_for_done = False
        console.print()

    # 5. Meta Status
    phases = graph_data.get('meta', {}).get('phases', {})
    current_phase = None
    current_status = None
    for phase_id, entities in phases.items():
        if feature_id in entities:
            current_phase = phase_id
            current_status = entities[feature_id].get('status', 'unknown')
            break

    console.print("[bold]Meta Status:[/bold]")
    if current_phase:
        console.print(f"  Phase: {current_phase}")
        console.print(f"  Status: {current_status}")
    else:
        console.print("  [dim]Not assigned to any phase[/dim]")
    console.print()

    # 6. Readiness Summary
    console.print("[bold]Readiness Summary:[/bold]")
    if ready_for_review:
        console.print("  [bold green]✓ Ready for review[/bold green]")
    else:
        console.print("  [bold yellow]⚠ Not ready for review[/bold yellow]")
        console.print("  [dim]  Address issues above before reviewing[/dim]")

    if ready_for_done:
        console.print("  [bold green]✓ Ready to mark done[/bold green]")
    else:
        console.print("  [bold yellow]⚠ Not ready for done[/bold yellow]")
        if not review_results_path.exists():
            console.print("  [dim]  Needs review first[/dim]")

    console.print()

    # 7. Proceed or exit
    if check_only:
        sys.exit(0 if ready_for_review else 1)

    if not ready_for_review:
        if not click.confirm("Feature not ready. Continue anyway?"):
            sys.exit(1)

    console.print(f"[bold cyan]Proceeding to interactive QA review[/bold cyan]")
    console.print("[dim]The Claude skill /know:review will guide you through testing[/dim]\n")


@feature.command(name='connect')
@click.argument('feature_name')
@click.argument('code_entities', nargs=-1, required=True)
@click.option('--component', '-c', help='Spec-graph component this links to (optional)')
@click.pass_context
def feature_connect(ctx, feature_name, code_entities, component):
    """Create bidirectional graph linkage between feature and code entities.

    Links a spec-graph feature to code-graph entities (modules, functions, classes).
    Creates implementation references in spec-graph and graph-link references in code-graph.

    Examples:
        know feature connect auth module:auth-handler function:authenticate
        know feature connect checkout module:payment-processor --component component:payment
    """
    graph_data = ctx.obj['graph'].load()
    feature_id = f"feature:{feature_name}"

    # 1. Verify feature exists in spec-graph
    if feature_name not in graph_data.get('entities', {}).get('feature', {}):
        console.print(f"[red]✗ Feature not found in spec-graph: {feature_id}[/red]")
        suggest_did_you_mean(graph_data, feature_id)
        sys.exit(1)

    # 2. Load code-graph
    code_graph_path = graph_data.get('meta', {}).get('code_graph_path', '.ai/know/code-graph.json')
    code_graph_file = Path(code_graph_path)

    if not code_graph_file.exists():
        console.print(f"[red]✗ Code graph not found: {code_graph_path}[/red]")
        console.print("[dim]  Set meta.code_graph_path in spec-graph or ensure .ai/know/code-graph.json exists[/dim]")
        sys.exit(1)

    with open(code_graph_file, 'r') as f:
        code_graph = json.load(f)

    # 3. Verify all code entities exist in code-graph
    console.print(f"\n[bold]Connecting {feature_id} to code entities:[/bold]\n")

    verified_entities = []
    for entity_id in code_entities:
        # Parse entity type and key
        if ':' not in entity_id:
            console.print(f"[red]✗ Invalid entity ID format: {entity_id}[/red]")
            console.print("[dim]  Use format: type:key (e.g., module:auth, function:login)[/dim]")
            sys.exit(1)

        entity_type, entity_key = entity_id.split(':', 1)

        # Check if entity exists in code-graph
        if entity_type not in code_graph.get('entities', {}):
            console.print(f"[red]✗ Unknown entity type in code-graph: {entity_type}[/red]")
            sys.exit(1)

        if entity_key not in code_graph['entities'][entity_type]:
            console.print(f"[red]✗ Entity not found in code-graph: {entity_id}[/red]")
            sys.exit(1)

        verified_entities.append(entity_id)
        console.print(f"  [green]✓[/green] {entity_id}")

    console.print()

    # 4. Create implementation reference in spec-graph
    impl_key = f"{feature_name}-impl"
    graph_link_ids = []

    # Create graph-link references for each code entity
    for entity_id in verified_entities:
        # Generate graph-link key from entity
        entity_type, entity_key = entity_id.split(':', 1)
        link_key = entity_key  # Use entity key as link key

        graph_link_ids.append(f"graph-link:{link_key}")

        # Create/update graph-link in code-graph
        if 'references' not in code_graph:
            code_graph['references'] = {}
        if 'graph-link' not in code_graph['references']:
            code_graph['references']['graph-link'] = {}

        link_data = {
            'feature': feature_id
        }
        if component:
            link_data['component'] = component

        code_graph['references']['graph-link'][link_key] = link_data

    # 5. Create/update implementation reference in spec-graph
    if 'references' not in graph_data:
        graph_data['references'] = {}
    if 'implementation' not in graph_data['references']:
        graph_data['references']['implementation'] = {}

    graph_data['references']['implementation'][impl_key] = graph_link_ids

    # 6. Add dependency from feature to implementation reference
    if 'graph' not in graph_data:
        graph_data['graph'] = {}
    if feature_id not in graph_data['graph']:
        graph_data['graph'][feature_id] = {'depends_on': []}

    impl_ref_id = f"implementation:{impl_key}"
    if impl_ref_id not in graph_data['graph'][feature_id].get('depends_on', []):
        if 'depends_on' not in graph_data['graph'][feature_id]:
            graph_data['graph'][feature_id]['depends_on'] = []
        graph_data['graph'][feature_id]['depends_on'].append(impl_ref_id)

    # 7. Save both graphs
    if not ctx.obj['graph'].save_graph(graph_data):
        console.print(f"[red]✗ Failed to save spec-graph[/red]")
        sys.exit(1)

    with open(code_graph_file, 'w') as f:
        json.dump(code_graph, f, indent=2)

    # 8. Display results
    console.print("[bold green]✓ Bidirectional linkage established![/bold green]\n")
    console.print(f"[bold]Spec-graph:[/bold]")
    console.print(f"  {feature_id} → implementation:{impl_key}")
    console.print(f"  implementation:{impl_key} → {graph_link_ids}")
    console.print()
    console.print(f"[bold]Code-graph:[/bold]")
    for link_id in graph_link_ids:
        link_key = link_id.split(':', 1)[1]
        link_data = code_graph['references']['graph-link'][link_key]
        console.print(f"  {link_id} → {link_data}")
    console.print()

    # Validate the connection
    console.print("[bold]Validating connection...[/bold]")
    validation = _validate_feature_completion(ctx, feature_name)
    for msg in validation['messages']:
        console.print(f"  {msg}")

    if validation['passed']:
        console.print(f"\n[bold green]Connection validated successfully![/bold green]")
    else:
        console.print(f"\n[yellow]⚠ Connection created but validation found issues[/yellow]")


@feature.command(name='done')
@click.argument('feature_name')
@click.option('--skip-todos', is_flag=True, help='Skip todo completion check')
@click.option('--skip-archive', is_flag=True, help='Skip archiving feature directory')
@click.option('--auto', 'auto_tag', is_flag=True, help='Auto-tag all commits without prompting')
@click.pass_context
def feature_done(ctx, feature_name, skip_todos, skip_archive, auto_tag):
    """Complete a feature: tag commits, update phase, optionally archive.

    Examples:
        know feature done auth
        know feature done checkout --auto
        know feature done auth --skip-archive"""
    import re
    import shutil
    from src.feature_tracker import FeatureTracker

    tracker = FeatureTracker(
        spec_graph_path=str(ctx.obj['graph'].cache.graph_path)
    )

    # 1. Verify feature exists
    feature_dir = tracker.get_feature_dir(feature_name)
    if not feature_dir:
        console.print(f"[red]✗ Feature not found: {feature_name}[/red]")
        sys.exit(1)

    console.print(f"\n[bold]Completing feature: {feature_name}[/bold]\n")

    # Ensure config.json exists
    created, _ = tracker.ensure_config(feature_name)
    if created:
        console.print(f"[dim]Created config.json[/dim]")

    # 1.5. Validate graph completion (bidirectional linkage)
    console.print("[bold]Graph Completion Validation:[/bold]")
    validation = _validate_feature_completion(ctx, feature_name)

    for msg in validation['messages']:
        console.print(f"  {msg}")

    console.print()

    if not validation['passed']:
        console.print("[yellow]⚠ Feature incomplete - missing proper graph linkage[/yellow]")
        if not click.confirm("Mark as done anyway?"):
            console.print("\n[dim]Run `/know:connect` to establish graph links[/dim]")
            sys.exit(0)

    # 1.6. Check for review-results.md
    review_results_path = feature_dir / "review-results.md"
    if not review_results_path.exists():
        console.print("[yellow]⚠ Feature not reviewed (review-results.md missing)[/yellow]")
        console.print("[dim]  Run `know feature review {feature_name}` or `/know:review` first[/dim]")
        if not click.confirm("Mark as done anyway?"):
            sys.exit(0)
    else:
        console.print("[green]✓ Feature has been reviewed[/green]")

    # 2. Check todo completion (legacy)
    todo_path = feature_dir / "todo.md"
    if todo_path.exists() and not skip_todos:
        with open(todo_path, 'r') as f:
            content = f.read()
        completed = len(re.findall(r'- \[x\]', content, re.IGNORECASE))
        total = len(re.findall(r'- \[[x ]\]', content, re.IGNORECASE))

        if total > 0 and completed < total:
            console.print(f"[yellow]⚠ Todos incomplete: {completed}/{total}[/yellow]")
            if not click.confirm("Continue anyway?"):
                sys.exit(0)
        else:
            console.print(f"[green]✓ Todos complete: {completed}/{total}[/green]")

    # 3. Find and tag commits
    commits = tracker.get_feature_commits(feature_name)

    if commits:
        console.print(f"\n[bold]Related commits ({len(commits)}):[/bold]")
        for i, commit in enumerate(commits[:10], 1):
            console.print(f"  {commit['short_sha']} - {commit['message'][:50]}")
        if len(commits) > 10:
            console.print(f"  ... and {len(commits) - 10} more")

        if auto_tag:
            shas = [c['sha'] for c in commits]
        else:
            selection = click.prompt(
                "\nTag commits? (all/none/comma-separated numbers)",
                default='all'
            )
            if selection.lower() == 'none':
                shas = []
            elif selection.lower() == 'all':
                shas = [c['sha'] for c in commits]
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    shas = [commits[i]['sha'] for i in indices if 0 <= i < len(commits)]
                except (ValueError, IndexError):
                    shas = []

        if shas:
            success, error = tracker.tag_commits(feature_name, shas)
            if success:
                tracker.store_commits(feature_name, shas)
                console.print(f"[green]✓ Tagged {len(shas)} commits[/green]")
            else:
                console.print(f"[yellow]⚠ Tagging failed: {error}[/yellow]")
    else:
        console.print("[dim]No commits to tag[/dim]")

    # 4. Remove from phases (done = out of phases entirely)
    graph_data = ctx.obj['graph'].load()
    entity_id = f"feature:{feature_name}"

    # Find and remove from current phase
    current_phase = None
    for phase_id, entities in graph_data.get('meta', {}).get('phases', {}).items():
        if entity_id in entities:
            current_phase = phase_id
            del graph_data['meta']['phases'][phase_id][entity_id]
            break

    if ctx.obj['graph'].save_graph(graph_data):
        if current_phase:
            console.print(f"[green]✓ Removed from phase '{current_phase}'[/green]")
        else:
            console.print(f"[dim]Feature was not in any phase[/dim]")
    else:
        console.print(f"[red]✗ Failed to update phases[/red]")

    # 5. Archive feature directory
    if not skip_archive:
        archive_dir = feature_dir.parent / "archive"
        archive_dir.mkdir(exist_ok=True)
        archive_path = archive_dir / feature_name

        if archive_path.exists():
            console.print(f"[yellow]⚠ Archive already exists: {archive_path}[/yellow]")
        else:
            try:
                shutil.move(str(feature_dir), str(archive_path))
                console.print(f"[green]✓ Archived to {archive_path}[/green]")
            except OSError as e:
                console.print(f"[yellow]⚠ Archive failed: {e}[/yellow]")

    console.print(f"\n[bold green]Feature '{feature_name}' completed![/bold green]")


@feature.command(name='impact')
@click.argument('target')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def feature_impact(ctx, target, json_output):
    """Show features that depend on an entity or file.

    Examples:
        know feature impact component:validation-engine
        know feature impact src/auth/handler.py
    """
    from src.impact_analyzer import ImpactAnalyzer

    analyzer = ImpactAnalyzer()
    report = analyzer.get_impact_report(target)

    if json_output:
        print(json.dumps(report, indent=2))
        return

    console.print(f"\n[bold cyan]Impact Report: {target}[/bold cyan]\n")

    if report['target_type'] == 'entity':
        if report['features_creating']:
            console.print("[bold]Features creating this entity:[/bold]")
            for f in report['features_creating']:
                console.print(f"  • {f['name']} (confidence: {f['confidence']}%)")
            console.print()

        if report['features_depending']:
            console.print("[bold]Features depending on this entity:[/bold]")
            for f in report['features_depending']:
                console.print(f"  • {f['name']} (confidence: {f['confidence']}%)")
            console.print()

        console.print(f"[bold]Impact Severity:[/bold] {report['impact_severity']}")
    else:
        if report['features_creating']:
            console.print("[bold]Features creating this file:[/bold]")
            for f in report['features_creating']:
                console.print(f"  • {f['name']}")

        if report['features_modifying']:
            console.print("[bold]Features modifying this file:[/bold]")
            for f in report['features_modifying']:
                console.print(f"  • {f['name']}")

        if report['features_watching']:
            console.print("[bold]Features watching this file:[/bold]")
            for f in report['features_watching']:
                console.print(f"  • {f['name']}")

    console.print(f"\n[bold]Total affected features:[/bold] {report['total_affected_features']}")

    console.print("\n[bold]Recommendations:[/bold]")
    for rec in report['recommendations']:
        console.print(f"  • {rec}")


@feature.command(name='coverage')
@click.argument('feature_name')
@click.option('--detail', is_flag=True, help='Show per-component breakdown')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.option('--code-graph', '-c', default='.ai/know/code-graph.json', help='Code graph path')
@click.pass_context
def feature_coverage(ctx, feature_name, detail, json_output, code_graph):
    """Show test coverage aggregated from feature level.

    Traverses: feature -> components -> modules -> test-suites

    Examples:
        know feature coverage auth
        know feature coverage checkout --detail
        know feature coverage api-client --json
    """
    from src.coverage import CoverageAnalyzer

    analyzer = CoverageAnalyzer(ctx.obj['graph'], code_graph_path=code_graph)
    cov = analyzer.get_feature_coverage(feature_name)

    if json_output:
        print(json.dumps(cov, indent=2))
        return

    console.print(f"\n[bold cyan]Test Coverage: {cov['feature']}[/bold cyan]\n")

    # Summary
    pct = cov['coverage_percent']
    color = 'green' if pct >= 80 else 'yellow' if pct >= 50 else 'red'
    console.print(f"[{color}]Coverage: {pct}%[/{color}]")
    console.print(f"Components: {cov['components']}")
    console.print(f"Modules: {cov['modules']}")
    console.print(f"Test Suites: {cov['test_suites']}")
    console.print(f"Test Count: {cov['test_count']}")
    if cov['test_types']:
        console.print(f"Test Types: {', '.join(cov['test_types'])}")

    if detail and cov['by_component']:
        console.print(f"\n[bold]Per-Component Breakdown:[/bold]\n")
        for comp in cov['by_component']:
            comp_cov = comp['coverage']['coverage_percent']
            comp_color = 'green' if comp_cov >= 80 else 'yellow' if comp_cov >= 50 else 'red'
            console.print(f"  [cyan]{comp['component']}[/cyan]")
            console.print(f"    Modules: {len(comp['modules'])}")
            console.print(f"    Test Suites: {comp['test_suites']}")
            console.print(f"    Coverage: [{comp_color}]{comp_cov}%[/{comp_color}]")
            console.print()

    # Gaps
    gaps = analyzer.get_coverage_gaps(feature_name)
    if any([gaps['unmapped_components'], gaps['untested_modules'], gaps['low_coverage_modules']]):
        console.print(f"\n[bold yellow]Coverage Gaps:[/bold yellow]")
        if gaps['unmapped_components']:
            console.print(f"  Unmapped components: {len(gaps['unmapped_components'])}")
            for comp in gaps['unmapped_components'][:3]:
                console.print(f"    • {comp}")
        if gaps['untested_modules']:
            console.print(f"  Untested modules: {len(gaps['untested_modules'])}")
            for mod in gaps['untested_modules'][:3]:
                console.print(f"    • {mod['module']} ({mod['component']})")
        if gaps['low_coverage_modules']:
            console.print(f"  Low coverage (<50%): {len(gaps['low_coverage_modules'])}")
            for mod in gaps['low_coverage_modules'][:3]:
                console.print(f"    • {mod['module']}: {mod['coverage']}%")


@feature.command(name='block')
@click.argument('feature_name')
@click.argument('req_key')
@click.option('--by', required=True, help='What is blocking this requirement')
@click.pass_context
def feature_block(ctx, feature_name, req_key, by):
    """Mark a feature's requirement as blocked.

    Examples:
        know feature block auth login --by "Waiting for API key"
        know feature block checkout payment --by "component:payment not ready"
    """
    from src.requirements import RequirementManager

    rm = RequirementManager(ctx.obj['graph'])

    # Build requirement ID
    req_id = f"requirement:{feature_name}-{req_key}" if not req_key.startswith('requirement:') else req_key

    if rm.update_status(req_id, 'blocked', blocked_by=by):
        console.print(f"[yellow]⚠ Blocked '{req_id}'[/yellow]")
        console.print(f"  Blocked by: {by}")
    else:
        console.print(f"[red]✗ Requirement not found: {req_id}[/red]")
        sys.exit(1)


@feature.command(name='complete')
@click.argument('feature_name')
@click.argument('req_key')
@click.option('--effort', type=float, help='Effort in hours')
@click.pass_context
def feature_complete(ctx, feature_name, req_key, effort):
    """Mark a feature's requirement as complete.

    Examples:
        know feature complete auth login
        know feature complete checkout payment --effort 4.5
    """
    from src.requirements import RequirementManager

    rm = RequirementManager(ctx.obj['graph'])

    # Build requirement ID
    req_id = f"requirement:{feature_name}-{req_key}" if not req_key.startswith('requirement:') else req_key

    kwargs = {}
    if effort:
        kwargs['effort_hours'] = effort

    if rm.update_status(req_id, 'complete', **kwargs):
        console.print(f"[green]✓ Marked '{req_id}' as complete[/green]")
    else:
        console.print(f"[red]✗ Requirement not found: {req_id}[/red]")
        sys.exit(1)


# =============================================================================
# PHASES group (kept as-is)
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def phases(ctx):
    """Manage project phases and entity assignments"""
    pass


@phases.command(name='list')
@click.pass_context
def phases_list(ctx):
    """Show all phases with their entities grouped by phase

    Examples:
        know phases
        know phases list
    """
    import re
    import subprocess
    from pathlib import Path

    # Get current branch name if in a git repo
    branch_name = None
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        branch_name = result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    graph_data = ctx.obj['graph'].load()

    if 'meta' not in graph_data or 'phases' not in graph_data['meta']:
        console.print("[yellow]No phases defined in meta.phases[/yellow]")
        return

    phases_data = graph_data['meta']['phases']
    phases_metadata = graph_data['meta'].get('phases_metadata', {})

    if not phases_data:
        console.print("[yellow]No phases defined[/yellow]")
        return

    def count_todos(entity_id):
        """Count completed/total todos for an entity"""
        # Extract feature name from entity_id (e.g., "feature:auth" -> "auth")
        if ':' not in entity_id:
            return None, None

        entity_type, entity_name = entity_id.split(':', 1)

        # Only features have todo files in .ai/know/
        if entity_type != 'feature':
            return None, None

        # Try to read todo.md
        todo_path = Path('.ai/know') / entity_name / 'todo.md'
        if not todo_path.exists():
            return None, None

        try:
            content = todo_path.read_text()
            completed = len(re.findall(r'- \[x\]', content, re.IGNORECASE))
            total = len(re.findall(r'- \[[x ]\]', content, re.IGNORECASE))
            return completed, total
        except Exception:
            return None, None

    def get_status_icon(status):
        """Get emoji icon for status"""
        status_map = {
            'complete': '✅',
            'done': '✅',
            'in-progress': '🔄',
            'review-ready': '🔄',
            'changes-planned': '🔧',
            'incomplete': '📋',
            'pending': '📋',
            'planned': '📋'
        }
        return status_map.get(status, '⚪')

    # Collect stats
    total_features = 0
    total_completed = 0
    total_tasks = 0

    # Print each phase
    for phase_key, phase_entities in phases_data.items():
        # Skip phases_metadata if it somehow ended up in phases dict
        if phase_key == 'phases_metadata':
            continue

        if not phase_entities:
            continue

        # Get phase metadata
        phase_meta = phases_metadata.get(phase_key, {})
        phase_name = phase_meta.get('name', phase_key)
        phase_desc = phase_meta.get('description', '')

        # Count features in this phase
        feature_count = len(phase_entities)
        total_features += feature_count

        # Print phase header
        console.print(f"\n[bold cyan]{'━' * 80}[/bold cyan]")
        header = f"Phase {phase_key}: {phase_name} ({feature_count} features)"
        if phase_desc:
            header += f" - {phase_desc}"
        console.print(f"[bold cyan]{header}[/bold cyan]")
        console.print(f"[bold cyan]{'━' * 80}[/bold cyan]")

        # Print each entity
        for entity_id, entity_meta in phase_entities.items():
            # Extract entity type and name
            if ':' in entity_id:
                entity_type, entity_name = entity_id.split(':', 1)
            else:
                entity_type = "unknown"
                entity_name = entity_id

            # Get status
            if isinstance(entity_meta, dict):
                status = entity_meta.get('status', 'planned')
            else:
                # If entity_meta is a string, treat it as the status
                status = entity_meta if isinstance(entity_meta, str) else 'planned'
            icon = get_status_icon(status)

            # Look up entity details
            entity_details = None
            if 'entities' in graph_data and entity_type in graph_data['entities']:
                entity_details = graph_data['entities'][entity_type].get(entity_name, {})

            # Get name (truncate if too long)
            name = entity_details.get('name', entity_name) if entity_details else entity_name
            if len(name) > 40:
                name = name[:37] + "..."

            # Count todos
            completed, total = count_todos(entity_id)

            if completed is not None and total is not None:
                total_completed += completed
                total_tasks += total
                task_display = f"({completed}/{total})"
            else:
                task_display = ""

            # Check virtual status flags (planned, implemented, reviewed)
            virtual_status = []

            # Planned: always true if in phases
            virtual_status.append("📋")

            # Implemented: check for code-graph links
            if entity_type == 'feature':
                implemented = False
                feature_deps = graph_data.get('graph', {}).get(entity_id, {}).get('depends_on', [])
                impl_refs = [d for d in feature_deps if d.startswith('implementation:')]

                if impl_refs:
                    code_graph_path = graph_data.get('meta', {}).get('code_graph_path')
                    if code_graph_path:
                        code_graph_path = Path(code_graph_path)
                        if code_graph_path.exists():
                            try:
                                with open(code_graph_path, 'r') as f:
                                    code_graph_data = json.load(f)
                                graph_links = code_graph_data.get('references', {}).get('graph-link', {})
                                for link_data in graph_links.values():
                                    if isinstance(link_data, dict) and link_data.get('feature') == entity_id:
                                        implemented = True
                                        break
                            except Exception:
                                pass

                virtual_status.append("✅" if implemented else "⏳")

                # Reviewed: check for git commit with [feature:name]
                reviewed = False
                try:
                    result = subprocess.run(
                        ['git', 'log', '--oneline', '--grep', f'\\[{entity_id}\\]', 'main'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        reviewed = True
                except Exception:
                    pass

                virtual_status.append("✅" if reviewed else "⏳")

            status_display = f"[{' '.join(virtual_status)}]" if entity_type == 'feature' else ""

            # Print feature line
            console.print(f"  {icon} {name:<45} {task_display:>8} {status_display}")

    # Print summary
    console.print(f"\n[bold cyan]{'━' * 80}[/bold cyan]")
    if total_tasks > 0:
        pct = int((total_completed / total_tasks) * 100)
        console.print(f"[bold]Total: {total_features} features, {total_completed}/{total_tasks} tasks ({pct}% complete)[/bold]")
    else:
        console.print(f"[bold]Total: {total_features} features[/bold]")
    if branch_name:
        console.print(f"[dim]Branch: {branch_name}[/dim]")
    console.print(f"[dim]Legend: ✅ completed  🔄 in-progress  🔧 changes-planned  📋 planned  ⚪ no status[/dim]")


@phases.command(name='add')
@click.argument('phase_id')
@click.argument('entity_id')
@click.option('--status', '-s', default='build-ready', help='Lifecycle status (build-ready, in-progress, etc.)')
@click.pass_context
def phases_add(ctx, phase_id, entity_id, status):
    """Add an entity to a phase

    Examples:
        know phases add I feature:auth
        know phases add II feature:checkout --status in-progress
    """
    # Validate phase - Roman numerals only
    valid_phases = {'I', 'II', 'III', 'IV', 'V'}
    if phase_id not in valid_phases:
        console.print(f"[red]✗ Invalid phase: {phase_id}[/red]")
        console.print(f"[dim]  Valid phases: {', '.join(sorted(valid_phases))}[/dim]")
        sys.exit(1)

    # Validate status - lifecycle states
    valid_statuses = {
        'build-ready',      # Ready to start (in phase, waiting)
        'build-not-ready',  # Blocked/invalidated (needs re-planning)
        'changes-planned',  # Extension planned for existing feature
        'in-progress',      # /know:build active
        'review-ready',     # /know:build complete
        'in-review',        # /know:review started
        'merge-ready',      # /know:review passed (human approved)
        'complete',         # /know:done
    }
    if status not in valid_statuses:
        console.print(f"[red]✗ Invalid status: {status}[/red]")
        console.print(f"[dim]  Valid: {', '.join(sorted(valid_statuses))}[/dim]")
        sys.exit(1)

    # Validate entity type - only features allowed in phases
    if ':' in entity_id:
        entity_type = entity_id.split(':', 1)[0]
        if entity_type != 'feature':
            console.print(f"[red]✗ Only features can be added to phases, not '{entity_type}'[/red]")
            sys.exit(1)
    else:
        console.print(f"[red]✗ Entity ID must include type prefix (e.g., feature:auth)[/red]")
        sys.exit(1)

    graph_data = ctx.obj['graph'].load()

    # Initialize meta.phases if it doesn't exist
    if 'meta' not in graph_data:
        graph_data['meta'] = {}
    if 'phases' not in graph_data['meta']:
        graph_data['meta']['phases'] = {}

    # Initialize phase if it doesn't exist
    if phase_id not in graph_data['meta']['phases']:
        graph_data['meta']['phases'][phase_id] = {}

    # Check if entity already exists in another phase
    current_phase = None
    for pid, entities in graph_data['meta']['phases'].items():
        if entity_id in entities:
            current_phase = pid
            break

    if current_phase:
        console.print(f"[yellow]⚠ Entity '{entity_id}' already in phase '{current_phase}'[/yellow]")
        console.print(f"[yellow]  Use 'phases move' to move between phases[/yellow]")
        sys.exit(1)

    # Add entity to phase
    graph_data['meta']['phases'][phase_id][entity_id] = {'status': status}

    # Save graph
    if ctx.obj['graph'].save_graph(graph_data):
        console.print(f"[green]✓ Added '{entity_id}' to phase '{phase_id}' with status '{status}'[/green]")
    else:
        console.print(f"[red]✗ Failed to save graph[/red]")
        sys.exit(1)


@phases.command(name='move')
@click.argument('entity_id')
@click.argument('phase_id')
@click.option('--status', '-s', default=None, help='Update status (pending, in-progress, complete)')
@click.pass_context
def phases_move(ctx, entity_id, phase_id, status):
    """Move an entity to a different phase

    Examples:
        know phases move feature:auth done
        know phases move feature:checkout II --status in-progress
    """
    # Validate phase - Roman numerals only
    valid_phases = {'I', 'II', 'III', 'IV', 'V'}
    if phase_id not in valid_phases:
        console.print(f"[red]✗ Invalid phase: {phase_id}[/red]")
        console.print(f"[dim]  Valid phases: {', '.join(sorted(valid_phases))}[/dim]")
        sys.exit(1)

    # Validate entity type - only features allowed in phases
    if ':' in entity_id:
        entity_type = entity_id.split(':', 1)[0]
        if entity_type != 'feature':
            console.print(f"[red]✗ Only features can be moved between phases, not '{entity_type}'[/red]")
            sys.exit(1)
    else:
        console.print(f"[red]✗ Entity ID must include type prefix (e.g., feature:auth)[/red]")
        sys.exit(1)

    # Validate status if provided - lifecycle states
    if status:
        valid_statuses = {
            'build-ready',      # Ready to start (in phase, waiting)
            'build-not-ready',  # Blocked/invalidated (needs re-planning)
            'changes-planned',  # Extension planned for existing feature
            'in-progress',      # /know:build active
            'review-ready',     # /know:build complete
            'in-review',        # /know:review started
            'merge-ready',      # /know:review passed (human approved)
            'complete',         # /know:done
        }
        if status not in valid_statuses:
            console.print(f"[red]✗ Invalid status: {status}[/red]")
            console.print(f"[dim]  Valid: {', '.join(sorted(valid_statuses))}[/dim]")
            sys.exit(1)

    graph_data = ctx.obj['graph'].load()

    if 'meta' not in graph_data or 'phases' not in graph_data['meta']:
        console.print("[red]✗ No phases defined in graph[/red]")
        sys.exit(1)

    # Find current phase
    current_phase = None
    current_status = None
    for pid, entities in graph_data['meta']['phases'].items():
        if entity_id in entities:
            current_phase = pid
            entity_meta = entities[entity_id]
            current_status = entity_meta.get('status', 'planned') if isinstance(entity_meta, dict) else entity_meta
            break

    if not current_phase:
        console.print(f"[yellow]⚠ Entity '{entity_id}' not found in any phase[/yellow]")
        console.print(f"[yellow]  Use 'phases add' to add it first[/yellow]")
        sys.exit(1)

    # Remove from current phase
    del graph_data['meta']['phases'][current_phase][entity_id]

    # Initialize target phase if it doesn't exist
    if phase_id not in graph_data['meta']['phases']:
        graph_data['meta']['phases'][phase_id] = {}

    # Add to new phase with updated or preserved status
    new_status = status if status else current_status
    graph_data['meta']['phases'][phase_id][entity_id] = {'status': new_status}

    # Save graph
    if ctx.obj['graph'].save_graph(graph_data):
        console.print(f"[green]✓ Moved '{entity_id}' from '{current_phase}' to '{phase_id}'[/green]")
        if status:
            console.print(f"[green]  Status updated to '{new_status}'[/green]")

        # Auto-set baseline when feature status becomes in-progress
        if new_status == 'in-progress' and entity_id.startswith('feature:'):
            from src.feature_tracker import FeatureTracker
            feature_name = entity_id.replace('feature:', '')
            tracker = FeatureTracker(
                spec_graph_path=str(ctx.obj['graph'].cache.graph_path)
            )
            created, _ = tracker.ensure_config(feature_name)
            if tracker.set_baseline(feature_name):
                console.print(f"[green]  Baseline set for {feature_name}[/green]")
    else:
        console.print(f"[red]✗ Failed to save graph[/red]")
        sys.exit(1)


@phases.command(name='status')
@click.argument('entity_id')
@click.argument('status_value')
@click.pass_context
def phases_status(ctx, entity_id, status_value):
    """Update the status of an entity in its current phase

    Examples:
        know phases status feature:auth in-progress
        know phases status feature:checkout complete
    """
    # Validate entity type - only features allowed in phases
    if ':' in entity_id:
        entity_type = entity_id.split(':', 1)[0]
        if entity_type != 'feature':
            console.print(f"[red]✗ Only features can have phase status updates, not '{entity_type}'[/red]")
            sys.exit(1)
    else:
        console.print(f"[red]✗ Entity ID must include type prefix (e.g., feature:auth)[/red]")
        sys.exit(1)

    graph_data = ctx.obj['graph'].load()

    if 'meta' not in graph_data or 'phases' not in graph_data['meta']:
        console.print("[red]✗ No phases defined in graph[/red]")
        sys.exit(1)

    # Find entity in phases
    found = False
    for phase_id, entities in graph_data['meta']['phases'].items():
        if entity_id in entities:
            graph_data['meta']['phases'][phase_id][entity_id] = {'status': status_value}
            found = True

            if ctx.obj['graph'].save_graph(graph_data):
                console.print(f"[green]✓ Updated '{entity_id}' status to '{status_value}' in phase '{phase_id}'[/green]")
            else:
                console.print(f"[red]✗ Failed to save graph[/red]")
                sys.exit(1)
            break

    if not found:
        console.print(f"[yellow]⚠ Entity '{entity_id}' not found in any phase[/yellow]")
        console.print(f"[yellow]  Use 'phases add' to add it first[/yellow]")
        sys.exit(1)


@phases.command(name='remove')
@click.argument('entity_id')
@click.pass_context
def phases_remove(ctx, entity_id):
    """Remove an entity from all phases

    Examples:
        know phases remove feature:cancelled
    """
    graph_data = ctx.obj['graph'].load()

    if 'meta' not in graph_data or 'phases' not in graph_data['meta']:
        console.print("[red]✗ No phases defined in graph[/red]")
        sys.exit(1)

    # Find and remove entity
    removed = False
    removed_from = None
    for phase_id, entities in graph_data['meta']['phases'].items():
        if entity_id in entities:
            del graph_data['meta']['phases'][phase_id][entity_id]
            removed = True
            removed_from = phase_id
            break

    if removed:
        if ctx.obj['graph'].save_graph(graph_data):
            console.print(f"[green]✓ Removed '{entity_id}' from phase '{removed_from}'[/green]")
        else:
            console.print(f"[red]✗ Failed to save graph[/red]")
            sys.exit(1)
    else:
        console.print(f"[yellow]⚠ Entity '{entity_id}' not found in any phase[/yellow]")
        sys.exit(1)


# =============================================================================
# REQ group (kept as-is)
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def req(ctx):
    """Manage feature requirements"""
    pass


@req.command(name='add')
@click.argument('feature')
@click.argument('key')
@click.option('--name', '-n', required=True, help='Human-readable requirement name')
@click.option('--description', '-d', required=True, help='Testable specification')
@click.pass_context
def req_add(ctx, feature, key, name, description):
    """Add a requirement to a feature.

    Examples:
        know req add auth login --name "User can log in" --description "..."
        know req add checkout payment --name "Process payment" --description "..."
    """
    from src.requirements import RequirementManager

    rm = RequirementManager(ctx.obj['graph'])

    try:
        req_id = rm.add_requirement(feature, key, name, description)
        console.print(f"[green]✓ Added requirement '{req_id}'[/green]")
        console.print(f"  Name: {name}")
        console.print(f"  Linked to: feature:{feature}")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        sys.exit(1)


@req.command(name='status')
@click.argument('req_id')
@click.argument('status_value')
@click.option('--notes', help='Additional notes')
@click.option('--blocked-by', help='What is blocking this requirement')
@click.option('--effort', type=float, help='Effort in hours')
@click.pass_context
def req_status(ctx, req_id, status_value, notes, blocked_by, effort):
    """Update requirement status.

    Examples:
        know req status requirement:auth-login in-progress
        know req status requirement:checkout-payment blocked --blocked-by "API not ready"
        know req status auth-login complete --effort 8
    """
    from src.requirements import RequirementManager

    rm = RequirementManager(ctx.obj['graph'])

    kwargs = {}
    if notes:
        kwargs['notes'] = notes
    if blocked_by:
        kwargs['blocked_by'] = blocked_by
    if effort:
        kwargs['effort_hours'] = effort

    try:
        if rm.update_status(req_id, status_value, **kwargs):
            console.print(f"[green]✓ Updated '{req_id}' to '{status_value}'[/green]")
        else:
            console.print(f"[red]✗ Requirement not found: {req_id}[/red]")
            sys.exit(1)
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        sys.exit(1)


@req.command(name='list')
@click.argument('feature')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def req_list(ctx, feature, json_output):
    """List requirements for a feature with status.

    Examples:
        know req list auth
        know req list checkout --json
    """
    from src.requirements import RequirementManager

    rm = RequirementManager(ctx.obj['graph'])
    reqs = rm.get_feature_requirements(feature)

    if json_output:
        print(json.dumps(reqs, indent=2))
        return

    if not reqs:
        console.print(f"[yellow]No requirements for feature '{feature}'[/yellow]")
        return

    completion = rm.calculate_feature_completion(feature)

    console.print(f"\n[bold cyan]Requirements for {feature}[/bold cyan]")
    console.print(f"[dim]Progress: {completion['complete']}/{completion['total']} ({completion['percent']}%)[/dim]\n")

    status_icons = {
        'pending': '⚪',
        'in-progress': '🔄',
        'blocked': '🚫',
        'complete': '✅',
        'verified': '✅✅'
    }

    for r in reqs:
        icon = status_icons.get(r['status'], '❓')
        console.print(f"{icon} [bold]{r['name']}[/bold]")
        console.print(f"   [dim]{r['id']}[/dim] - {r['status']}")
        if r.get('blocked_by'):
            console.print(f"   [red]Blocked by: {r['blocked_by']}[/red]")
        console.print()


@req.command(name='complete')
@click.argument('req_id')
@click.option('--effort', type=float, help='Effort in hours')
@click.pass_context
def req_complete(ctx, req_id, effort):
    """Mark a requirement as complete (shorthand for status complete).

    Examples:
        know req complete requirement:auth-login
        know req complete auth-login --effort 4.5
    """
    from src.requirements import RequirementManager

    rm = RequirementManager(ctx.obj['graph'])

    kwargs = {}
    if effort:
        kwargs['effort_hours'] = effort

    if rm.update_status(req_id, 'complete', **kwargs):
        console.print(f"[green]✓ Marked '{req_id}' as complete[/green]")
    else:
        console.print(f"[red]✗ Requirement not found: {req_id}[/red]")
        sys.exit(1)


@req.command(name='block')
@click.argument('req_id')
@click.option('--by', required=True, help='What is blocking this requirement')
@click.pass_context
def req_block(ctx, req_id, by):
    """Mark a requirement as blocked.

    Examples:
        know req block auth-login --by "Waiting for API key"
        know req block requirement:checkout --by "component:payment not ready"
    """
    from src.requirements import RequirementManager

    rm = RequirementManager(ctx.obj['graph'])

    if rm.update_status(req_id, 'blocked', blocked_by=by):
        console.print(f"[yellow]⚠ Blocked '{req_id}'[/yellow]")
        console.print(f"  Blocked by: {by}")
    else:
        console.print(f"[red]✗ Requirement not found: {req_id}[/red]")
        sys.exit(1)


# =============================================================================
# OP group (operation-level tracking)
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def op(ctx):
    """Manage op-level progress tracking for features"""
    pass


@op.command(name='start')
@click.argument('feature_id')
@click.argument('op_num', type=int)
@click.pass_context
def op_start(ctx, feature_id, op_num):
    """Mark an op as in-progress.

    Examples:
        know op start feature:auth 1
        know op start feature:checkout 2
    """
    from src.op_manager import OpManager

    om = OpManager(ctx.obj['graph'])

    if om.start(feature_id, op_num):
        console.print(f"[green]✓ Started op {op_num} for '{feature_id}'[/green]")
    else:
        console.print(f"[yellow]⚠ Op {op_num} already complete for '{feature_id}'[/yellow]")


@op.command(name='done')
@click.argument('feature_id')
@click.argument('op_num', type=int)
@click.option('--commits', '-c', multiple=True, help='Commit hashes (can specify multiple)')
@click.pass_context
def op_done(ctx, feature_id, op_num, commits):
    """Mark an op as complete with commits.

    Examples:
        know op done feature:auth 1 --commits abc123f
        know op done feature:auth 1 -c abc123f -c def456a
    """
    from src.op_manager import OpManager

    om = OpManager(ctx.obj['graph'])
    commit_list = list(commits) if commits else []

    if om.done(feature_id, op_num, commit_list):
        console.print(f"[green]✓ Completed op {op_num} for '{feature_id}'[/green]")
        if commit_list:
            console.print(f"  Commits: {', '.join(commit_list)}")
    else:
        console.print(f"[red]✗ Failed to mark op {op_num} as complete[/red]")
        sys.exit(1)


@op.command(name='status')
@click.argument('feature_id')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def op_status(ctx, feature_id, json_output):
    """Show op status for a feature.

    Examples:
        know op status feature:auth
        know op status feature:checkout --json
    """
    from src.op_manager import OpManager

    om = OpManager(ctx.obj['graph'])
    ops = om.status(feature_id)

    if json_output:
        print(json.dumps(ops, indent=2))
        return

    if not ops:
        console.print(f"[yellow]No ops tracked for '{feature_id}'[/yellow]")
        return

    summary = om.summary(feature_id)

    console.print(f"\n[bold cyan]Op Status for {feature_id}[/bold cyan]")
    console.print(f"[dim]Complete: {summary['complete']} | In Progress: {summary['in_progress']} | Next: op {summary['next_op']}[/dim]\n")

    status_icons = {
        'pending': '⚪',
        'in-progress': '🔄',
        'complete': '✅'
    }

    for op_key in sorted(ops.keys(), key=int):
        op_data = ops[op_key]
        icon = status_icons.get(op_data.get('status', 'pending'), '❓')
        status = op_data.get('status', 'pending')

        console.print(f"{icon} [bold]Op {op_key}[/bold] - {status}")

        if op_data.get('started'):
            console.print(f"   Started: {op_data['started']}")
        if op_data.get('completed'):
            console.print(f"   Completed: {op_data['completed']}")
        if op_data.get('commits'):
            console.print(f"   Commits: {', '.join(op_data['commits'])}")
        console.print()


@op.command(name='next')
@click.argument('feature_id')
@click.pass_context
def op_next(ctx, feature_id):
    """Print the next op number for a feature.

    Examples:
        know op next feature:auth
    """
    from src.op_manager import OpManager

    om = OpManager(ctx.obj['graph'])
    next_op = om.next(feature_id)
    print(next_op)


@op.command(name='reset')
@click.argument('feature_id')
@click.argument('op_num', type=int)
@click.pass_context
def op_reset(ctx, feature_id, op_num):
    """Reset an op to pending (remove tracking).

    Examples:
        know op reset feature:auth 2
    """
    from src.op_manager import OpManager

    om = OpManager(ctx.obj['graph'])

    if om.reset(feature_id, op_num):
        console.print(f"[green]✓ Reset op {op_num} for '{feature_id}'[/green]")
    else:
        console.print(f"[yellow]⚠ Op {op_num} not found for '{feature_id}'[/yellow]")


# NOTE: The build command has been removed from the CLI.
# Use the /know:build slash command in Claude Code instead.
# The slash command provides checkpoint-based workflow execution
# with agent integration for task implementation.

# =============================================================================
# INIT (standalone)
# =============================================================================
@cli.command()
@click.option('--project-dir', '-p', default='.', help='Project directory to initialize')
def init(project_dir):
    """Initialize know workflow in a project

    This command:
    1. Copies slash commands to .claude/commands/know/
    2. Copies know-tool skill to .claude/skills/know-tool/
    3. Copies agents to .claude/agents/
    4. Creates .ai/know/ directory structure
    5. Initializes project.md with template
    6. Creates initial graphs if they don't exist
    7. Installs graph protection hook (prevents direct file edits)
    8. Injects <know-instructions> into CLAUDE.md

    Examples:
        know init .
        know init /path/to/project
    """
    project_path = Path(project_dir).resolve()

    if not project_path.exists():
        console.print(f"[red]✗ Directory not found: {project_path}[/red]")
        return

    console.print(f"[bold cyan]Initializing know workflow in {project_path}[/bold cyan]\n")

    # 1. Copy slash commands
    templates_dir = Path(__file__).parent / "templates" / "commands"
    commands_dir = project_path / ".claude" / "commands" / "know"

    if not templates_dir.exists():
        console.print(f"[red]✗ Templates directory not found: {templates_dir}[/red]")
        return

    commands_dir.mkdir(parents=True, exist_ok=True)

    copied_commands = []
    for cmd_file in templates_dir.glob("*.md"):
        dest_file = commands_dir / cmd_file.name
        shutil.copy2(cmd_file, dest_file)
        copied_commands.append(cmd_file.stem)

    if copied_commands:
        console.print(f"[green]✓[/green] Copied slash commands: {', '.join(copied_commands)}")

    # 2. Copy know-tool skill
    skill_source = Path(__file__).parent.parent / ".claude" / "skills" / "know-tool"
    skill_dest = project_path / ".claude" / "skills" / "know-tool"

    if skill_source.exists():
        skill_dest.parent.mkdir(parents=True, exist_ok=True)
        if skill_dest.exists():
            shutil.rmtree(skill_dest)
        shutil.copytree(skill_source, skill_dest)
        console.print(f"[green]✓[/green] Installed know-tool skill (replaced)")
    else:
        console.print(f"[yellow]⚠[/yellow] know-tool skill not found at {skill_source}")

    # 2a. Copy agents
    agents_templates_dir = Path(__file__).parent / "templates" / "agents"
    agents_dest_dir = project_path / ".claude" / "agents"

    if agents_templates_dir.exists():
        if agents_dest_dir.exists() and not agents_dest_dir.is_dir():
            console.print(f"[yellow]⚠[/yellow] {agents_dest_dir} exists as a file, skipping agents installation")
        else:
            agents_dest_dir.mkdir(parents=True, exist_ok=True)
            copied_agents = []
            for agent_file in agents_templates_dir.glob("*.md"):
                dest_file = agents_dest_dir / agent_file.name
                if dest_file.exists():
                    console.print(f"[yellow]⚠[/yellow] Agent {agent_file.stem} already exists")
                else:
                    shutil.copy2(agent_file, dest_file)
                    copied_agents.append(agent_file.stem)

            if copied_agents:
                console.print(f"[green]✓[/green] Installed agents: {', '.join(copied_agents)}")
    else:
        console.print(f"[dim]  No agents to install[/dim]")

    # 3. Create .ai/know/ directory structure
    know_dir = project_path / ".ai" / "know"
    archive_dir = know_dir / "archive"
    config_dir = know_dir / "config"
    know_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Created {know_dir}")

    # 3a. Copy dependency rules to local config
    rules_source_dir = Path(__file__).parent / "config"
    rules_copied = []
    for rules_file in ["dependency-rules.json", "code-dependency-rules.json"]:
        source = rules_source_dir / rules_file
        dest = config_dir / rules_file
        if source.exists():
            shutil.copy2(source, dest)
            rules_copied.append(rules_file)
    if rules_copied:
        console.print(f"[green]✓[/green] Copied rules: {', '.join(rules_copied)}")

    # 4. Initialize project.md
    project_md = know_dir / "project.md"
    if not project_md.exists():
        template_path = Path(__file__).parent / "templates" / "project.md"
        if template_path.exists():
            shutil.copy2(template_path, project_md)
            console.print(f"[green]✓[/green] Created {project_md}")
        else:
            console.print(f"[yellow]⚠[/yellow] Template not found: {template_path}")
    else:
        console.print(f"[yellow]⚠[/yellow] {project_md} already exists")

    # 5. Check for graphs
    spec_graph = know_dir / "spec-graph.json"
    code_graph = know_dir / "code-graph.json"

    if spec_graph.exists():
        console.print(f"[green]✓[/green] spec-graph.json exists")
    else:
        console.print(f"[yellow]⚠[/yellow] spec-graph.json not found (create manually or use existing tools)")

    if code_graph.exists():
        console.print(f"[green]✓[/green] code-graph.json exists")
    else:
        console.print(f"[dim]  code-graph.json not found (optional)[/dim]")

    # 6. Install graph protection hook
    hooks_source = Path(__file__).parent / "templates" / "hooks"
    hooks_dest = project_path / ".claude" / "hooks"

    if hooks_source.exists():
        hooks_dest.mkdir(parents=True, exist_ok=True)

        # Copy hook script
        hook_script = "protect-graph-files.sh"
        hook_source_file = hooks_source / hook_script
        hook_dest_file = hooks_dest / hook_script

        if hook_source_file.exists():
            shutil.copy2(hook_source_file, hook_dest_file)
            hook_dest_file.chmod(0o755)  # Make executable
            console.print(f"[green]✓[/green] Installed graph protection hook")

            # Update settings.json to configure the hook
            settings_file = project_path / ".claude" / "settings.json"

            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {}

            # Add hook configuration
            if 'hooks' not in settings:
                settings['hooks'] = {}

            if 'PreToolUse' not in settings['hooks']:
                settings['hooks']['PreToolUse'] = []

            # Check if hook already configured
            hook_exists = any(
                hook.get('hooks', [{}])[0].get('command', '').endswith('protect-graph-files.sh')
                for hook in settings['hooks']['PreToolUse']
                if isinstance(hook, dict) and 'hooks' in hook
            )

            if not hook_exists:
                settings['hooks']['PreToolUse'].append({
                    "matcher": "Read|Edit|Write",
                    "hooks": [{
                        "type": "command",
                        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-graph-files.sh"
                    }]
                })

                with open(settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)

                console.print(f"[green]✓[/green] Configured hook in settings.json")
            else:
                console.print(f"[dim]  Graph protection hook already configured[/dim]")
        else:
            console.print(f"[yellow]⚠[/yellow] Hook script not found: {hook_source_file}")

    else:
        console.print(f"[yellow]⚠[/yellow] Hooks template directory not found: {hooks_source}")

    # 7. Inject <know-instructions> into CLAUDE.md
    claude_md = project_path / "CLAUDE.md"
    know_instructions_template = Path(__file__).parent / "templates" / "know-instructions.md"

    if know_instructions_template.exists():
        instructions_block = know_instructions_template.read_text()
        start_marker = "<!-- know:start -->"
        end_marker = "<!-- know:end -->"

        if claude_md.exists():
            content = claude_md.read_text()
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)

            if start_idx != -1 and end_idx != -1:
                # Replace existing block
                content = content[:start_idx] + instructions_block + content[end_idx + len(end_marker):]
                claude_md.write_text(content)
                console.print(f"[green]✓[/green] Updated <know-instructions> in CLAUDE.md")
            else:
                # Append block
                content = content.rstrip() + "\n\n" + instructions_block + "\n"
                claude_md.write_text(content)
                console.print(f"[green]✓[/green] Added <know-instructions> to CLAUDE.md")
        else:
            claude_md.write_text(instructions_block + "\n")
            console.print(f"[green]✓[/green] Created CLAUDE.md with <know-instructions>")
    else:
        console.print(f"[yellow]⚠[/yellow] know-instructions template not found")

    console.print(f"\n[bold green]✓ Initialization complete![/bold green]")
    console.print(f"\n[dim]Next steps:[/dim]")
    console.print(f"  • Edit {project_md} to add project context")
    console.print(f"  • Use /know:add <feature-name> to start a new feature")
    console.print(f"  • Use /know:list to see all features")


# =============================================================================
# VIZ group - Graph visualization
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def viz(ctx):
    """Visualize the graph in various formats"""
    pass


@viz.command(name='tree')
@click.argument('entity', required=False)
@click.option('--type', '-t', 'types', multiple=True, help='Filter to entity type(s)')
@click.option('--depth', '-d', type=int, default=None, help='Limit traversal depth')
@click.option('--refs/--no-refs', default=False, help='Include reference nodes')
@click.option('--entity', '-e', 'entity_opt', default=None, help='Focus on entity neighborhood')
@click.pass_context
def viz_tree(ctx, entity, types, depth, refs, entity_opt):
    """Render graph as a Rich tree in the terminal

    Examples:
        know viz tree
        know viz tree feature:auth
        know viz tree --type feature --type action
        know viz tree -e feature:auth --depth 2
    """
    from src.visualizers.tree import RichTreeVisualizer

    focus = entity or entity_opt
    v = RichTreeVisualizer(
        ctx.obj['graph'],
        entity_types=types or None,
        entity_focus=focus,
        depth=depth,
        include_refs=refs,
    )
    tree = v.run()
    console.print(tree)


@viz.command(name='mermaid')
@click.option('--output', '-o', default=None, help='Write to file instead of stdout')
@click.option('--type', '-t', 'types', multiple=True, help='Filter to entity type(s)')
@click.option('--depth', '-d', type=int, default=None, help='Limit traversal depth')
@click.option('--refs/--no-refs', default=False, help='Include reference nodes')
@click.option('--entity', '-e', default=None, help='Focus on entity neighborhood')
@click.pass_context
def viz_mermaid(ctx, output, types, depth, refs, entity):
    """Generate Mermaid flowchart syntax

    Examples:
        know viz mermaid
        know viz mermaid -o graph.mmd
        know viz mermaid --type feature --type action
    """
    from src.visualizers.mermaid import MermaidVisualizer

    v = MermaidVisualizer(
        ctx.obj['graph'],
        entity_types=types or None,
        entity_focus=entity,
        depth=depth,
        include_refs=refs,
    )
    result = v.run()

    if output:
        with open(output, 'w') as f:
            f.write(result)
        console.print(f"[green]✓ Written to {output}[/green]")
    else:
        click.echo(result)


@viz.command(name='dot')
@click.option('--output', '-o', default='graph', help='Output file path (without extension)')
@click.option('--format', '-f', 'fmt', default='svg',
              type=click.Choice(['svg', 'png', 'pdf']), help='Output format')
@click.option('--type', '-t', 'types', multiple=True, help='Filter to entity type(s)')
@click.option('--depth', '-d', type=int, default=None, help='Limit traversal depth')
@click.option('--refs/--no-refs', default=False, help='Include reference nodes')
@click.option('--entity', '-e', default=None, help='Focus on entity neighborhood')
@click.pass_context
def viz_dot(ctx, output, fmt, types, depth, refs, entity):
    """Render graph using Graphviz (SVG/PNG/PDF)

    Requires: pip install graphviz + system graphviz

    Examples:
        know viz dot -o graph -f svg
        know viz dot --entity feature:auth --depth 3
    """
    from src.visualizers.dot import DotVisualizer

    ok, msg = DotVisualizer.check_available()
    if not ok:
        console.print(f"[red]✗ Graphviz not available: {msg}[/red]")
        sys.exit(1)

    v = DotVisualizer(
        ctx.obj['graph'],
        entity_types=types or None,
        entity_focus=entity,
        depth=depth,
        include_refs=refs,
    )
    data = v.extract()
    rendered = v.render_to_file(data, output, fmt=fmt)
    console.print(f"[green]✓ Rendered to {rendered}[/green]")


@viz.command(name='html')
@click.option('--output', '-o', default='graph.html', help='Output HTML file')
@click.option('--open', 'open_browser', is_flag=True, help='Open in browser after rendering')
@click.option('--type', '-t', 'types', multiple=True, help='Filter to entity type(s)')
@click.option('--depth', '-d', type=int, default=None, help='Limit traversal depth')
@click.option('--refs/--no-refs', default=False, help='Include reference nodes')
@click.option('--entity', '-e', default=None, help='Focus on entity neighborhood')
@click.pass_context
def viz_html(ctx, output, open_browser, types, depth, refs, entity):
    """Generate interactive HTML graph using PyVis

    Requires: pip install pyvis

    Examples:
        know viz html -o graph.html --open
        know viz html --type feature --depth 2
    """
    from src.visualizers.html import HtmlVisualizer

    ok, msg = HtmlVisualizer.check_available()
    if not ok:
        console.print(f"[red]✗ PyVis not available: {msg}[/red]")
        sys.exit(1)

    v = HtmlVisualizer(
        ctx.obj['graph'],
        entity_types=types or None,
        entity_focus=entity,
        depth=depth,
        include_refs=refs,
    )
    data = v.extract()
    rendered = v.render_to_file(data, output)
    console.print(f"[green]✓ Written to {rendered}[/green]")

    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{Path(rendered).resolve()}")


@viz.command(name='d3')
@click.option('--output', '-o', default='graph.html', help='Output HTML file')
@click.option('--open', 'open_browser', is_flag=True, help='Open in browser after rendering')
@click.option('--type', '-t', 'types', multiple=True, help='Filter to entity type(s)')
@click.option('--depth', '-d', type=int, default=None, help='Limit traversal depth')
@click.option('--refs/--no-refs', default=False, help='Include reference nodes')
@click.option('--entity', '-e', default=None, help='Focus on entity neighborhood')
@click.pass_context
def viz_d3(ctx, output, open_browser, types, depth, refs, entity):
    """Generate interactive D3 force-directed graph (standalone HTML)

    No Python dependencies required — uses D3.js via CDN.

    Examples:
        know viz d3
        know viz d3 -o my-graph.html --open
        know viz d3 --entity feature:auth --depth 3
        know viz d3 --type feature --type action --refs
    """
    from src.visualizers.d3 import D3Visualizer

    v = D3Visualizer(
        ctx.obj['graph'],
        entity_types=types or None,
        entity_focus=entity,
        depth=depth,
        include_refs=refs,
    )
    data = v.extract()
    rendered = v.render_to_file(data, output)
    console.print(f"[green]✓ Written to {rendered}[/green]")

    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{Path(rendered).resolve()}")


@viz.command(name='d3-tree')
@click.option('--output', '-o', default='graph-tree.html', help='Output HTML file')
@click.option('--open', 'open_browser', is_flag=True, help='Open in browser after rendering')
@click.option('--type', '-t', 'types', multiple=True, help='Filter to entity type(s)')
@click.option('--depth', '-d', type=int, default=None, help='Limit traversal depth')
@click.option('--refs/--no-refs', default=False, help='Include reference nodes')
@click.option('--entity', '-e', default=None, help='Focus on entity neighborhood')
@click.pass_context
def viz_d3_tree(ctx, output, open_browser, types, depth, refs, entity):
    """Generate interactive collapsible D3 tree (standalone HTML)

    Click nodes to expand/collapse branches. No Python deps required.

    Examples:
        know viz d3-tree
        know viz d3-tree -o tree.html --open
        know viz d3-tree --entity feature:auth --depth 3
    """
    from src.visualizers.d3_tree import D3TreeVisualizer

    v = D3TreeVisualizer(
        ctx.obj['graph'],
        entity_types=types or None,
        entity_focus=entity,
        depth=depth,
        include_refs=refs,
    )
    data = v.extract()
    rendered = v.render_to_file(data, output)
    console.print(f"[green]✓ Written to {rendered}[/green]")

    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{Path(rendered).resolve()}")


@viz.command(name='fzf')
@click.option('--type', '-t', 'types', multiple=True, help='Filter to entity type(s)')
@click.option('--refs/--no-refs', default=False, help='Include reference nodes')
@click.pass_context
def viz_fzf(ctx, types, refs):
    """Fuzzy-pick an entity with fzf and show its details

    Requires: pip install iterfzf + fzf binary

    Examples:
        know viz fzf
        know viz fzf --type feature
    """
    from src.visualizers.fzf import FzfPicker

    ok, msg = FzfPicker.check_available()
    if not ok:
        console.print(f"[red]✗ fzf not available: {msg}[/red]")
        sys.exit(1)

    v = FzfPicker(
        ctx.obj['graph'],
        entity_types=types or None,
        include_refs=refs,
    )
    selected = v.run()

    if selected:
        # Invoke the existing get_item command to show details
        ctx.invoke(get_item, path=selected)
    else:
        console.print("[dim]No selection made[/dim]")


@cli.command(name='serve')
@click.option('--port', '-p', default=5173, type=int, help='Port to listen on')
@click.option('--no-open', is_flag=True, help='Do not open browser on start')
@click.pass_context
def serve_cmd(ctx, port, no_open):
    """Start the spec-dashboard web server

    Serves an interactive HTML dashboard for exploring and editing
    the spec-graph. Kanban board with drillable feature cards.

    Examples:
        know serve
        know serve --port 8080
        know serve -g .ai/know/code-graph.json
    """
    from src.server import serve
    graph_path = str(ctx.obj['graph'].cache.graph_path)
    serve(graph_path, port=port, open_browser=not no_open, project_cwd=Path.cwd())


if __name__ == '__main__':
    cli()
