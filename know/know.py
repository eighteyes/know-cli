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
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint

from src import (
    GraphManager, EntityManager, DependencyManager,
    GraphValidator, SpecGenerator, GraphDiff, get_graph_stats
)


console = Console()


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


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


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--graph-path', '-g', default='.ai/spec-graph.json',
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
    if rules_path is None:
        config_dir = Path(__file__).parent / "config"
        if 'code-graph' in str(graph_path):
            rules_path = str(config_dir / "code-dependency-rules.json")
        else:
            rules_path = str(config_dir / "dependency-rules.json")

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


# =============================================================================
# ADD command - Unified add for entities and references (auto-detects)
# =============================================================================
@cli.command(name='add')
@click.argument('type_name')
@click.argument('key')
@click.argument('data', required=False)
@click.option('--json-file', '-f', help='Read data from JSON file')
@click.option('--skip-validation', is_flag=True, help='Skip validation (entities only)')
@click.pass_context
def add_item(ctx, type_name, key, data, json_file, skip_validation):
    """Add an entity or reference to the graph (auto-detects based on type)

    Examples:
        know add feature auth '{"name":"Auth","description":"User authentication"}'
        know add component login-form '{"name":"Login Form"}'
        know add business_logic login-flow '{"pre_conditions":[],"workflow":[]}'
        know add documentation auth-rfc '{"title":"RFC 7519","url":"https://..."}'
        know add -f entity.json feature analytics
    """
    # Parse data
    if json_file:
        with open(json_file, 'r') as f:
            item_data = json.load(f)
    elif data:
        try:
            item_data = json.loads(data)
        except json.JSONDecodeError as e:
            console.print(f"[red]✗ Invalid JSON data: {e}[/red]")
            sys.exit(1)
    else:
        item_data = {}

    # Determine if entity or reference
    category = _get_type_category(ctx.obj['rules_path'], type_name)

    if category == 'entity':
        success, error = ctx.obj['entities'].add_entity(
            type_name, key, item_data, skip_validation=skip_validation
        )

        if success:
            console.print(f"[green]✓ Added entity '{type_name}:{key}'[/green]")
        else:
            console.print(f"[red]✗ Failed to add entity: {error}[/red]")
            sys.exit(1)

    elif category == 'reference':
        # Load graph and add reference
        graph_data = ctx.obj['graph'].load()

        if 'references' not in graph_data:
            graph_data['references'] = {}

        if type_name not in graph_data['references']:
            graph_data['references'][type_name] = {}

        # Check for duplicates
        if key in graph_data['references'][type_name]:
            console.print(f"[red]✗ Reference '{type_name}:{key}' already exists[/red]")
            sys.exit(1)

        graph_data['references'][type_name][key] = item_data
        ctx.obj['graph'].save_graph(graph_data)

        console.print(f"[green]✓ Added reference '{type_name}:{key}'[/green]")

    else:
        console.print(f"[red]✗ Unknown type '{type_name}'[/red]")
        console.print(f"[dim]Use 'know gen rules describe entities' to list entity types[/dim]")
        console.print(f"[dim]Use 'know gen rules describe references' to list reference types[/dim]")
        sys.exit(1)


# =============================================================================
# META group - Get/set meta sections
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def meta(ctx):
    """Get and set meta sections (project, phases, decisions, etc.)"""
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
        know meta set project name '{"value":"My Project"}'
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
        except json.JSONDecodeError as e:
            console.print(f"[red]✗ Invalid JSON data: {e}[/red]")
            sys.exit(1)
    else:
        meta_data = {}

    # Load graph and set meta
    graph_data = ctx.obj['graph'].load()

    if 'meta' not in graph_data:
        graph_data['meta'] = {}

    if section not in graph_data['meta']:
        graph_data['meta'][section] = {}

    # Check if overwriting
    if key in graph_data['meta'][section]:
        console.print(f"[yellow]⚠ Overwriting meta.{section}.{key}[/yellow]")

    graph_data['meta'][section][key] = meta_data
    ctx.obj['graph'].save_graph(graph_data)

    console.print(f"[green]✓ Set meta.{section}.{key}[/green]")


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
        know -g .ai/code-graph.json get module:graph
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
            sys.exit(1)
        console.print(f"\n[bold cyan]{path}[/bold cyan]")
        rprint(e)

    elif category == 'reference':
        ref_type, ref_key = path.split(':', 1)
        graph_data = ctx.obj['graph'].load()
        refs = graph_data.get('references', {})

        if ref_type not in refs or ref_key not in refs[ref_type]:
            console.print(f"[red]Reference '{path}' not found[/red]")
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
        know -g .ai/code-graph.json list --type module
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


# =============================================================================
# TOP-LEVEL DEPRECATION commands
# =============================================================================
@cli.command(name='deprecate')
@click.argument('entity_id')
@click.option('--reason', '-r', required=True, help='Why the entity is deprecated')
@click.option('--replacement', help='Entity ID of replacement')
@click.option('--remove-by', help='Target removal date (YYYY-MM-DD)')
@click.pass_context
def deprecate(ctx, entity_id, reason, replacement, remove_by):
    """Mark an entity as deprecated with warnings on use.

    Examples:
        know deprecate component:old-auth --reason "Replaced by new-auth"
        know deprecate feature:legacy --reason "Obsolete" --replacement feature:modern
        know deprecate action:old-flow --reason "Removed" --remove-by 2026-03-01
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
        sys.exit(1)


@cli.command(name='undeprecate')
@click.argument('entity_id')
@click.pass_context
def undeprecate(ctx, entity_id):
    """Remove deprecation status from an entity.

    Examples:
        know undeprecate component:old-auth
    """
    from src.deprecation import DeprecationManager

    dm = DeprecationManager(ctx.obj['graph'])

    if dm.undeprecate(entity_id):
        console.print(f"[green]✓ Removed deprecation from '{entity_id}'[/green]")
    else:
        console.print(f"[yellow]⚠ Entity '{entity_id}' was not deprecated[/yellow]")


@cli.command(name='deprecated')
@click.option('--overdue', is_flag=True, help='Show only entities past removal date')
@click.pass_context
def deprecated(ctx, overdue):
    """List all deprecated entities.

    Examples:
        know deprecated
        know deprecated --overdue
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


# =============================================================================
# GRAPH group
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def graph(ctx):
    """Manage graph dependencies and structure"""
    pass


@graph.command(name='link')
@click.argument('from_entity')
@click.argument('to_entity')
@click.pass_context
def graph_link(ctx, from_entity, to_entity):
    """Add a dependency between entities"""
    success = ctx.obj['entities'].add_dependency(from_entity, to_entity)

    if success:
        console.print(f"[green]✓ Added dependency: {from_entity} -> {to_entity}[/green]")
    else:
        console.print(f"[red]✗ Dependency already exists or failed to add[/red]")
        sys.exit(1)


@graph.command(name='unlink')
@click.argument('from_entity')
@click.argument('to_entity')
@click.pass_context
def graph_unlink(ctx, from_entity, to_entity):
    """Remove a dependency between entities"""
    success = ctx.obj['entities'].remove_dependency(from_entity, to_entity)

    if success:
        console.print(f"[green]✓ Removed dependency: {from_entity} -> {to_entity}[/green]")
    else:
        console.print(f"[red]✗ Dependency not found or failed to remove[/red]")
        sys.exit(1)


@graph.command(name='uses')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependencies or just direct ones')
@click.pass_context
def graph_uses(ctx, entity_path, recursive):
    """Show what an entity uses (its dependencies)"""
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
    """Show what uses this entity (dependents)"""
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
    """Suggest valid connections for an entity (formerly 'suggest')"""
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
    """Show topological build order"""
    order = ctx.obj['deps'].topological_sort()

    if not order:
        console.print("[red]Cannot determine build order (graph has cycles)[/red]")
        sys.exit(1)

    console.print("[bold]Build Order:[/bold]\n")
    for i, e in enumerate(order, 1):
        console.print(f"{i:3}. {e}")


@graph.command(name='diff')
@click.argument('graph1', type=click.Path(exists=True))
@click.argument('graph2', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed diff')
@click.option('--format', '-f', type=click.Choice(['terminal', 'json']), default='terminal',
              help='Output format')
def graph_diff(graph1, graph2, verbose, format):
    """Compare two graph files and show differences

    Shows added/removed/modified entities, dependencies, and references.

    Examples:
        know graph diff spec-graph.json spec-graph-backup.json
        know graph diff .ai/spec-graph.json /tmp/spec-graph.json --verbose
        know graph diff graph1.json graph2.json --format json
    """
    try:
        differ = GraphDiff(graph1, graph2)
        diff_result = differ.compute_diff()

        if format == 'json':
            # JSON output for scripting
            print(json.dumps(diff_result, indent=2))
            return

        # Terminal output (colored, human-readable)
        summary = diff_result['summary']

        # Header
        console.print(f"\n[bold cyan]Graph Diff:[/bold cyan] {differ.graph1_path} → {differ.graph2_path}\n")

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


# =============================================================================
# CHECK group
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def check(ctx):
    """Validate graph structure and analyze health"""
    pass


@check.command(name='validate')
@click.pass_context
def check_validate(ctx):
    """Validate graph structure and dependencies"""
    # Run comprehensive validation
    is_valid, results = ctx.obj['validator'].validate_all()

    # Also validate dependencies
    dep_valid, dep_errors = ctx.obj['deps'].validate_graph()

    if not dep_valid:
        results['errors'].extend(dep_errors)
        is_valid = False

    # Display results
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
    else:
        sys.exit(1)


@check.command(name='health')
@click.pass_context
def check_health(ctx):
    """Comprehensive graph health check"""
    console.print("[bold]Running health checks...[/bold]\n")

    # Validation
    is_valid, results = ctx.obj['validator'].validate_all()

    # Cycles
    cycles = ctx.obj['deps'].detect_cycles()

    # Disconnected subgraphs (informational only)
    disconnected = ctx.obj['validator'].find_disconnected_subgraphs()

    # Summary
    console.print("[bold cyan]Health Summary:[/bold cyan]\n")

    # Critical issues (cause failure)
    has_critical_issues = not is_valid or cycles

    if not has_critical_issues and not results['warnings']:
        console.print("[green]✓ Graph is healthy![/green]")
        if disconnected:
            console.print(f"\n[cyan]ℹ {len(disconnected)} disconnected subgraphs (expected for initial graphs)[/cyan]")
        return

    if not is_valid:
        console.print(f"[red]✗ {len(results['errors'])} validation errors[/red]")

    if cycles:
        console.print(f"[red]✗ {len(cycles)} circular dependencies[/red]")

    if disconnected:
        console.print(f"[cyan]ℹ {len(disconnected)} disconnected subgraphs (expected for initial/incremental graphs)[/cyan]")

    if results['warnings']:
        console.print(f"[yellow]⚠ {len(results['warnings'])} warnings[/yellow]")

    console.print("\n[dim]Run 'know check validate' for detailed results[/dim]")

    # Only exit with error if there are critical issues
    if has_critical_issues:
        sys.exit(1)


@check.command(name='stats')
@click.pass_context
def check_stats(ctx):
    """Show graph statistics"""
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


@check.command(name='completeness')
@click.argument('entity_id')
@click.pass_context
def check_completeness(ctx, entity_id):
    """Check completeness score for an entity"""
    score = ctx.obj['validator'].get_completeness_score(entity_id)

    if score['total'] == 0:
        console.print(f"[red]Entity {entity_id} not found[/red]")
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
    """Detect circular dependencies"""
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
    """Find orphaned references"""
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
    """Show reference usage statistics"""
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


@check.command(name='clean')
@click.option('--remove/--keep', default=False, help='Remove unused references')
@click.option('--dry-run/--execute', default=True, help='Dry run mode')
@click.pass_context
def check_link_clean(ctx, remove, dry_run):
    """Clean up unused references"""
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


@check.command(name='suggest')
@click.option('--max', '-m', default=10, help='Maximum suggestions')
@click.pass_context
def check_link_suggest(ctx, max):
    """Suggest connections for orphaned references"""
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
    """Analyze implementation gaps in dependency chains"""
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
    """List missing connections in dependency chains"""
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
    """Show implementation summary"""
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
    """Generate detailed feature specification"""
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


@gen.command(name='sitemap')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def gen_sitemap(ctx, output):
    """Generate sitemap of all interfaces"""
    sitemap_text = ctx.obj['generator'].generate_sitemap()

    if output:
        Path(output).write_text(sitemap_text)
        console.print(f"[green]✓ Sitemap written to {output}[/green]")
    else:
        console.print(sitemap_text)


@gen.command(name='code-graph')
@click.option('--codemap', '-c', default='.ai/codemap.json', help='Input codemap.json path')
@click.option('--existing', '-e', help='Existing code-graph.json to preserve references')
@click.option('--output', '-o', default='.ai/code-graph.json', help='Output code-graph.json path')
@click.option('--source-dir', '-s', default='know/src', help='Source directory for file paths')
def gen_code_graph(codemap, existing, output, source_dir):
    """Generate code-graph from codemap AST parsing.

    This command regenerates code-graph entities (modules, classes, functions)
    from codemap.json while preserving manually curated references
    (product-component, external-dep).

    Examples:
        # Generate from existing codemap
        know gen code-graph

        # Preserve existing references
        know gen code-graph --existing .ai/code-graph.json

        # Custom paths
        know gen code-graph -c .ai/codemap.json -o .ai/code-graph-new.json
    """
    from src.codemap_to_graph import CodeGraphGenerator

    # Check if codemap exists
    if not Path(codemap).exists():
        console.print(f"[red]✗ Codemap not found: {codemap}[/red]")
        console.print(f"[dim]Run: know gen codemap {source_dir}[/dim]")
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
        know -g .ai/spec-graph.json gen trace component:cli-commands -c .ai/code-graph.json
        know -g .ai/code-graph.json gen trace module:auth-handler -s .ai/spec-graph.json
    """
    from pathlib import Path
    import json

    current_graph = ctx.obj['graph']
    current_graph_data = current_graph.load()

    # Determine which graph we're starting from
    current_graph_path = ctx.obj.get('graph_path', '.ai/spec-graph.json')
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
        console.print(f"[dim]Example: know -g .ai/spec-graph.json gen trace {entity_id} -c .ai/code-graph.json[/dim]")

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
        know -g .ai/spec-graph.json gen rules describe feature
        know -g .ai/code-graph.json gen rules describe module
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
        know -g .ai/spec-graph.json gen rules before component
        know -g .ai/code-graph.json gen rules before module
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
        know -g .ai/spec-graph.json gen rules after feature
        know -g .ai/code-graph.json gen rules after module
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
    """Visualize the high-level dependency graph structure

    Examples:
        know -g .ai/spec-graph.json gen rules graph
        know -g .ai/code-graph.json gen rules graph
    """
    rules_path = ctx.obj.get('rules_path') if ctx.obj else None
    rules = _load_rules(rules_path)

    console.print("\n[bold cyan]Dependency Graph Structure[/bold cyan]\n")

    # Show WHAT chain
    console.print("[bold yellow]WHAT Chain (User Intent → Actions):[/bold yellow]")
    what_chain = rules.get('notes', {}).get('what', [])
    console.print("  " + " → ".join(what_chain))
    console.print()

    # Show HOW chain
    console.print("[bold yellow]HOW Chain (Implementation):[/bold yellow]")
    how_chain = rules.get('notes', {}).get('how', [])
    console.print("  " + " → ".join(how_chain))
    console.print()

    # Show dependency rules as graph (non-redundant)
    console.print("[bold yellow]Entity Relationships:[/bold yellow]\n")

    allowed = rules.get('allowed_dependencies', {})

    # Build reverse lookup: what depends on each type
    depended_on_by = {}
    for entity_type, deps in allowed.items():
        for dep in deps:
            if dep not in depended_on_by:
                depended_on_by[dep] = []
            depended_on_by[dep].append(entity_type)

    # Get all entity types (both as sources and targets)
    all_types = set(allowed.keys()) | set(depended_on_by.keys())

    # Print each entity type once with both relationships
    for entity_type in sorted(all_types):
        deps = allowed.get(entity_type, [])
        dependents = depended_on_by.get(entity_type, [])

        # Build the line
        line = f"[cyan]{entity_type}[/cyan]"

        if deps:
            line += f" → [green]{', '.join(deps)}[/green]"

        if dependents:
            line += f" [dim](← {', '.join(dependents)})[/dim]"

        if not deps and not dependents:
            line += " [dim](isolated)[/dim]"

        console.print(f"  {line}")

    console.print("\n[dim]Legend: → depends on | ← depended on by[/dim]")


# =============================================================================
# FEATURE group
# =============================================================================
@cli.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def feature(ctx):
    """Manage feature lifecycle, contracts, and coverage"""
    pass


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
    """Validate feature contracts for drift between declared and observed."""
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
@click.option('--code-graph', '-c', default='.ai/code-graph.json', help='Code graph path')
@click.pass_context
def feature_validate(ctx, feature_name, since, json_output, code_graph):
    """Check if codebase changes warrant revisiting feature plan."""
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
@click.option('--code-graph', '-c', default='.ai/code-graph.json', help='Code graph path')
@click.pass_context
def feature_tag(ctx, feature_name, since, auto_tag, code_graph):
    """Tag commits related to a feature with git notes."""
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
    code_graph_path = graph_data.get('meta', {}).get('code_graph_path', '.ai/code-graph.json')
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
@click.pass_context
def feature_review(ctx, feature_name, skip_validation):
    """Review feature for completion: validate graph linkage and check QA readiness.

    This command validates that:
    - Feature has implementation references
    - Graph-links exist in code graph
    - Bidirectional consistency (graph-links point back to feature)
    - QA_STEPS.md exists
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

    console.print(f"\n[bold]Reviewing feature: {feature_name}[/bold]\n")

    # 2. Validate graph completion
    if not skip_validation:
        console.print("[bold]Graph Completion Validation:[/bold]")
        validation = _validate_feature_completion(ctx, feature_name)

        for msg in validation['messages']:
            console.print(f"  {msg}")

        console.print()

        if not validation['passed']:
            console.print("[yellow]⚠ Feature incomplete - missing proper graph linkage[/yellow]")
            if not click.confirm("Continue with review anyway?"):
                console.print("\n[dim]Run `/know:connect` to establish graph links[/dim]")
                sys.exit(0)

    # 3. Check for QA_STEPS.md
    qa_steps_path = feature_dir / "QA_STEPS.md"
    if not qa_steps_path.exists():
        console.print("[yellow]⚠ QA_STEPS.md not found[/yellow]")
        console.print("[dim]  Run `/know:build` Phase 7 to generate QA steps[/dim]")
        sys.exit(1)

    console.print("[green]✓ QA_STEPS.md found[/green]")
    console.print(f"\n[bold cyan]Feature is ready for interactive QA review[/bold cyan]")
    console.print("[dim]The Claude skill /know:review will guide you through QA testing[/dim]\n")


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
    if feature_id not in graph_data.get('entities', {}).get('feature', {}):
        console.print(f"[red]✗ Feature not found in spec-graph: {feature_id}[/red]")
        sys.exit(1)

    # 2. Load code-graph
    code_graph_path = graph_data.get('meta', {}).get('code_graph_path', '.ai/code-graph.json')
    code_graph_file = Path(code_graph_path)

    if not code_graph_file.exists():
        console.print(f"[red]✗ Code graph not found: {code_graph_path}[/red]")
        console.print("[dim]  Set meta.code_graph_path in spec-graph or ensure .ai/code-graph.json exists[/dim]")
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
    """Complete a feature: tag commits, update phase, optionally archive."""
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
@click.option('--code-graph', '-c', default='.ai/code-graph.json', help='Code graph path')
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
    """Show all phases with their entities grouped by phase"""
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

            # Print feature line
            console.print(f"  {icon} {name:<45} {task_display}")

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
    """Add an entity to a phase"""
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
    """Move an entity to a different phase"""
    # Validate phase - Roman numerals only
    valid_phases = {'I', 'II', 'III', 'IV', 'V'}
    if phase_id not in valid_phases:
        console.print(f"[red]✗ Invalid phase: {phase_id}[/red]")
        console.print(f"[dim]  Valid phases: {', '.join(sorted(valid_phases))}[/dim]")
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
    """Update the status of an entity in its current phase"""
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
    """Remove an entity from all phases"""
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
    7. Detects and optionally sets up task management (Beads or native)
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
            console.print(f"[yellow]⚠[/yellow] know-tool skill already exists at {skill_dest}")
        else:
            shutil.copytree(skill_source, skill_dest)
            console.print(f"[green]✓[/green] Installed know-tool skill")
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
    know_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Created {know_dir}")

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
    spec_graph = project_path / ".ai" / "spec-graph.json"
    code_graph = project_path / ".ai" / "code-graph.json"

    if spec_graph.exists():
        console.print(f"[green]✓[/green] spec-graph.json exists")
    else:
        console.print(f"[yellow]⚠[/yellow] spec-graph.json not found (create manually or use existing tools)")

    if code_graph.exists():
        console.print(f"[green]✓[/green] code-graph.json exists")
    else:
        console.print(f"[dim]  code-graph.json not found (optional)[/dim]")

    console.print(f"\n[bold green]✓ Initialization complete![/bold green]")
    console.print(f"\n[dim]Next steps:[/dim]")
    console.print(f"  • Edit {project_md} to add project context")
    console.print(f"  • Use /know:add <feature-name> to start a new feature")
    console.print(f"  • Use /know:list to see all features")


if __name__ == '__main__':
    cli()
