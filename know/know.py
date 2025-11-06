#!/usr/bin/env python3
"""
Know Tool - Python implementation for efficient graph operations
Command-line interface for managing the specification graph
"""

import sys
import json
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint

from know_lib import (
    GraphManager, EntityManager, DependencyManager,
    GraphValidator, SpecGenerator, LLMManager, get_graph_stats
)


console = Console()


@click.group()
@click.option('--graph-path', '-g', default='.ai/spec-graph.json',
              help='Path to graph file')
@click.pass_context
def cli(ctx, graph_path):
    """Know Tool - Manage specification graph efficiently"""
    # Ensure parent path exists, adjust for running from know_python dir
    graph_path = Path(graph_path)
    if not graph_path.is_absolute():
        # Check if we're in know_python dir and adjust path
        if Path.cwd().name == 'know_python':
            graph_path = Path('..') / graph_path

    ctx.ensure_object(dict)
    ctx.obj['graph'] = GraphManager(str(graph_path))
    ctx.obj['entities'] = EntityManager(ctx.obj['graph'])
    ctx.obj['deps'] = DependencyManager(ctx.obj['graph'])
    ctx.obj['validator'] = GraphValidator(ctx.obj['graph'])
    ctx.obj['generator'] = SpecGenerator(
        ctx.obj['graph'],
        ctx.obj['entities'],
        ctx.obj['deps']
    )
    ctx.obj['llm'] = LLMManager()


@cli.command()
@click.pass_context
def list(ctx):
    """List all entities in the graph"""
    entities = ctx.obj['entities'].list_entities()

    if not entities:
        console.print("[yellow]No entities found[/yellow]")
        return

    # Group by type
    by_type = {}
    for entity in entities:
        entity_type = entity.split(':')[0]
        if entity_type not in by_type:
            by_type[entity_type] = []
        by_type[entity_type].append(entity)

    table = Table(title="Entities", show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Entity", style="green")
    table.add_column("Count", justify="right", style="yellow")

    for entity_type, items in sorted(by_type.items()):
        for i, item in enumerate(items):
            if i == 0:
                table.add_row(entity_type, item.split(':', 1)[1], str(len(items)))
            else:
                table.add_row("", item.split(':', 1)[1], "")

    console.print(table)


@cli.command()
@click.argument('entity_type')
@click.pass_context
def list_type(ctx, entity_type):
    """List entities of a specific type"""
    entities = ctx.obj['entities'].list_entities(entity_type)

    if not entities:
        console.print(f"[yellow]No entities of type '{entity_type}' found[/yellow]")
        return

    table = Table(title=f"{entity_type.capitalize()} Entities",
                  show_header=True, header_style="bold magenta")
    table.add_column("Entity", style="green")

    for entity in entities:
        table.add_row(entity.split(':', 1)[1])

    console.print(table)


@cli.command()
@click.argument('entity_path')
@click.pass_context
def get(ctx, entity_path):
    """Get details of a specific entity"""
    entity = ctx.obj['entities'].get_entity(entity_path)

    if not entity:
        console.print(f"[red]Entity '{entity_path}' not found[/red]")
        sys.exit(1)

    console.print(f"\n[bold cyan]{entity_path}[/bold cyan]")
    rprint(entity)


@cli.command()
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependencies or just direct ones')
@click.pass_context
def deps(ctx, entity_path, recursive):
    """Show dependencies for an entity"""
    deps = ctx.obj['graph'].find_dependencies(entity_path, recursive)

    if not deps:
        console.print(f"[yellow]No dependencies found for '{entity_path}'[/yellow]")
        return

    if recursive:
        console.print(f"\n[bold]All dependencies for {entity_path}:[/bold]")
    else:
        console.print(f"\n[bold]Direct dependencies for {entity_path}:[/bold]")

    for dep in sorted(deps):
        console.print(f"  • {dep}")


@cli.command()
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependents or just direct ones')
@click.pass_context
def dependents(ctx, entity_path, recursive):
    """Show what depends on an entity"""
    deps = ctx.obj['graph'].find_dependents(entity_path, recursive)

    if not deps:
        console.print(f"[yellow]No dependents found for '{entity_path}'[/yellow]")
        return

    if recursive:
        console.print(f"\n[bold]All dependents of {entity_path}:[/bold]")
    else:
        console.print(f"\n[bold]Direct dependents of {entity_path}:[/bold]")

    for dep in sorted(deps):
        console.print(f"  • {dep}")


@cli.command()
@click.pass_context
def validate(ctx):
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


@cli.command()
@click.pass_context
def cycles(ctx):
    """Detect circular dependencies"""
    cycles = ctx.obj['deps'].detect_cycles()

    if not cycles:
        console.print("[green]✓ No circular dependencies found[/green]")
        return

    console.print("[red]✗ Circular dependencies detected:[/red]\n")
    for i, cycle in enumerate(cycles, 1):
        console.print(f"Cycle {i}: {' → '.join(cycle)}")

    sys.exit(1)


@cli.command()
@click.pass_context
def stats(ctx):
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


@cli.command()
@click.argument('entity_type')
@click.argument('entity_key')
@click.argument('data', required=False)
@click.option('--json-file', '-f', help='Read entity data from JSON file')
@click.option('--skip-validation', is_flag=True, help='Skip validation checks')
@click.pass_context
def add(ctx, entity_type, entity_key, data, json_file, skip_validation):
    """Add a new entity"""
    if json_file:
        with open(json_file, 'r') as f:
            entity_data = json.load(f)
    elif data:
        try:
            entity_data = json.loads(data)
        except json.JSONDecodeError as e:
            console.print(f"[red]✗ Invalid JSON data: {e}[/red]")
            sys.exit(1)
    else:
        entity_data = {}

    success, error = ctx.obj['entities'].add_entity(
        entity_type, entity_key, entity_data, skip_validation=skip_validation
    )

    if success:
        console.print(f"[green]✓ Added entity '{entity_type}:{entity_key}'[/green]")
    else:
        console.print(f"[red]✗ Failed to add entity: {error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('from_entity')
@click.argument('to_entity')
@click.pass_context
def add_dep(ctx, from_entity, to_entity):
    """Add a dependency between entities"""
    success = ctx.obj['entities'].add_dependency(from_entity, to_entity)

    if success:
        console.print(f"[green]✓ Added dependency: {from_entity} -> {to_entity}[/green]")
    else:
        console.print(f"[red]✗ Dependency already exists or failed to add[/red]")
        sys.exit(1)


@cli.command()
@click.argument('from_entity')
@click.argument('to_entity')
@click.pass_context
def remove_dep(ctx, from_entity, to_entity):
    """Remove a dependency between entities"""
    success = ctx.obj['entities'].remove_dependency(from_entity, to_entity)

    if success:
        console.print(f"[green]✓ Removed dependency: {from_entity} -> {to_entity}[/green]")
    else:
        console.print(f"[red]✗ Dependency not found or failed to remove[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def build_order(ctx):
    """Show topological build order"""
    order = ctx.obj['deps'].topological_sort()

    if not order:
        console.print("[red]Cannot determine build order (graph has cycles)[/red]")
        sys.exit(1)

    console.print("[bold]Build Order:[/bold]\n")
    for i, entity in enumerate(order, 1):
        console.print(f"{i:3}. {entity}")


@cli.command()
@click.argument('entity_id')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def spec(ctx, entity_id, output):
    """Generate specification for an entity"""
    spec_text = ctx.obj['generator'].generate_entity_spec(entity_id)

    if output:
        Path(output).write_text(spec_text)
        console.print(f"[green]✓ Specification written to {output}[/green]")
    else:
        console.print(spec_text)


@cli.command()
@click.argument('feature_id')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def feature_spec(ctx, feature_id, output):
    """Generate detailed feature specification"""
    spec_text = ctx.obj['generator'].generate_feature_spec(feature_id)

    if output:
        Path(output).write_text(spec_text)
        console.print(f"[green]✓ Feature spec written to {output}[/green]")
    else:
        console.print(spec_text)


@cli.command()
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def sitemap(ctx, output):
    """Generate sitemap of all interfaces"""
    sitemap_text = ctx.obj['generator'].generate_sitemap()

    if output:
        Path(output).write_text(sitemap_text)
        console.print(f"[green]✓ Sitemap written to {output}[/green]")
    else:
        console.print(sitemap_text)


@cli.command()
@click.argument('entity_id')
@click.option('--max', '-m', default=5, help='Maximum suggestions per type')
@click.pass_context
def suggest(ctx, entity_id, max):
    """Suggest valid connections for an entity"""
    suggestions = ctx.obj['deps'].suggest_connections(entity_id, max)

    if not suggestions:
        console.print(f"[yellow]No suggestions found for {entity_id}[/yellow]")
        return

    console.print(f"\n[bold]Valid connections for {entity_id}:[/bold]\n")

    for entity_type, entities in suggestions.items():
        if entities:
            console.print(f"[cyan]{entity_type}:[/cyan]")
            for entity in entities:
                console.print(f"  • {entity}")
            console.print()


@cli.command()
@click.argument('entity_id')
@click.pass_context
def completeness(ctx, entity_id):
    """Check completeness score for an entity"""
    score = ctx.obj['validator'].get_completeness_score(entity_id)

    if score['total'] == 0:
        console.print(f"[red]Entity {entity_id} not found[/red]")
        sys.exit(1)

    console.print(f"\n[bold]Completeness Score for {entity_id}:[/bold]")
    console.print(f"\nScore: [cyan]{score['percentage']}%[/cyan] ({score['completed']}/{score['total']})")
    console.print("\n[bold]Checks:[/bold]")

    for check, passed in score['checks'].items():
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {status} {check.replace('_', ' ').title()}")


@cli.command()
@click.pass_context
def health(ctx):
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

    console.print("\n[dim]Run 'know validate' for detailed results[/dim]")

    # Only exit with error if there are critical issues
    if has_critical_issues:
        sys.exit(1)


@cli.command()
@click.pass_context
def llm_providers(ctx):
    """List available LLM providers"""
    providers = ctx.obj['llm'].list_providers()

    if not providers:
        console.print("[yellow]No LLM providers configured[/yellow]")
        return

    table = Table(title="LLM Providers", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Models", style="green")

    for provider in providers:
        models = ", ".join(provider['models']) if provider['models'] else "N/A"
        table.add_row(provider['display_name'], provider['type'], models)

    console.print(table)


@cli.command()
@click.pass_context
def llm_workflows(ctx):
    """List available LLM workflows"""
    workflows = ctx.obj['llm'].list_workflows()

    if not workflows:
        console.print("[yellow]No workflows configured[/yellow]")
        return

    for workflow in workflows:
        console.print(f"\n[bold cyan]{workflow['name']}[/bold cyan]")
        console.print(f"  {workflow['description']}")
        console.print(f"  [dim]Inputs: {', '.join(workflow['inputs'].keys())}[/dim]")


@cli.command()
@click.argument('workflow_name')
@click.argument('inputs_json')
@click.option('--provider', '-p', help='LLM provider to use')
@click.pass_context
def llm_run(ctx, workflow_name, inputs_json, provider):
    """Run an LLM workflow with JSON inputs"""
    try:
        inputs = json.loads(inputs_json)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON inputs: {e}[/red]")
        sys.exit(1)

    # Validate inputs
    is_valid, errors = ctx.obj['llm'].validate_workflow_inputs(workflow_name, inputs)
    if not is_valid:
        console.print("[red]✗ Input validation failed:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        sys.exit(1)

    console.print(f"[cyan]Running workflow: {workflow_name}[/cyan]")
    if provider:
        console.print(f"[dim]Using provider: {provider}[/dim]")

    try:
        result = ctx.obj['llm'].execute_workflow(workflow_name, inputs, provider)
        console.print("\n[green]✓ Workflow completed[/green]\n")
        rprint(result)
    except Exception as e:
        console.print(f"[red]✗ Workflow failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('chain_name')
@click.argument('inputs_json')
@click.option('--provider', '-p', help='LLM provider to use')
@click.pass_context
def llm_chain(ctx, chain_name, inputs_json, provider):
    """Run an LLM workflow chain"""
    try:
        inputs = json.loads(inputs_json)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON inputs: {e}[/red]")
        sys.exit(1)

    console.print(f"[cyan]Running workflow chain: {chain_name}[/cyan]")
    if provider:
        console.print(f"[dim]Using provider: {provider}[/dim]")

    try:
        results = ctx.obj['llm'].execute_chain(chain_name, inputs, provider)
        console.print("\n[green]✓ Chain completed[/green]\n")

        for step in results:
            console.print(f"[bold]{step['workflow']}:[/bold]")
            rprint(step['output'])
            console.print()
    except Exception as e:
        console.print(f"[red]✗ Chain failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def llm_chains(ctx):
    """List available workflow chains"""
    chains = ctx.obj['llm'].workflows_config.get('workflow_chains', {})

    if not chains:
        console.print("[yellow]No workflow chains configured[/yellow]")
        return

    table = Table(title="Workflow Chains", show_header=True, header_style="bold magenta")
    table.add_column("Chain", style="cyan")
    table.add_column("Workflows", style="green")

    for chain_name, workflows in chains.items():
        workflows_str = " → ".join(workflows)
        table.add_row(chain_name, workflows_str)

    console.print(table)


@cli.command()
@click.argument('workflow_name')
@click.pass_context
def llm_info(ctx, workflow_name):
    """Show detailed information about a workflow"""
    workflows = ctx.obj['llm'].workflows_config.get('workflows', {})

    if workflow_name not in workflows:
        console.print(f"[red]Workflow '{workflow_name}' not found[/red]")
        sys.exit(1)

    workflow = workflows[workflow_name]

    console.print(f"\n[bold cyan]{workflow.get('name', workflow_name)}[/bold cyan]")
    console.print(f"{workflow.get('description', 'No description')}\n")

    console.print("[bold]Input Schema:[/bold]")
    for field, type_spec in workflow.get('input_schema', {}).items():
        required = "" if type_spec.endswith('?') else " (required)"
        console.print(f"  • {field}: {type_spec}{required}")

    console.print("\n[bold]Output Schema:[/bold]")
    output_schema = workflow.get('output_schema', {})
    rprint(f"  {output_schema}")

    prefs = workflow.get('model_preferences', {})
    if prefs:
        console.print("\n[bold]Model Preferences:[/bold]")
        console.print(f"  • Temperature: {prefs.get('temperature', 'default')}")
        console.print(f"  • Max Tokens: {prefs.get('max_tokens', 'default')}")


@cli.command()
@click.argument('provider_name', required=False)
@click.pass_context
def llm_test(ctx, provider_name):
    """Test LLM provider connection with a simple prompt"""
    provider_name = provider_name or 'mock'

    console.print(f"[cyan]Testing provider: {provider_name}[/cyan]")

    try:
        test_inputs = {
            "vision": "A simple test project",
            "context": {}
        }

        result = ctx.obj['llm'].execute_workflow(
            'vision_statement',
            test_inputs,
            provider_name
        )

        console.print("\n[green]✓ Provider test successful[/green]\n")
        rprint(result)

    except Exception as e:
        console.print(f"\n[red]✗ Provider test failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('entity_id', required=False)
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def gap_analysis(ctx, entity_id, json_output):
    """Analyze implementation gaps in dependency chains"""
    from know_lib.gap_analysis import GapAnalyzer, ChainStatus

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


@cli.command()
@click.pass_context
def gap_missing(ctx):
    """List missing connections in dependency chains"""
    from know_lib.gap_analysis import GapAnalyzer

    analyzer = GapAnalyzer(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])
    missing = analyzer.list_missing_connections()

    console.print("\n[bold cyan]Missing Connections[/bold cyan]\n")

    for gap_type, entities in missing.items():
        if entities:
            label = gap_type.replace('_', ' ').title()
            console.print(f"[yellow]{label}:[/yellow]")
            for entity in entities:
                console.print(f"  • {entity}")
            console.print()


@cli.command()
@click.pass_context
def gap_summary(ctx):
    """Show implementation summary"""
    from know_lib.gap_analysis import GapAnalyzer

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


@cli.command()
@click.pass_context
def ref_orphans(ctx):
    """Find orphaned references"""
    from know_lib.reference_tools import ReferenceManager

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


@cli.command()
@click.pass_context
def ref_usage(ctx):
    """Show reference usage statistics"""
    from know_lib.reference_tools import ReferenceManager

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


@cli.command()
@click.option('--remove/--keep', default=False, help='Remove unused references')
@click.option('--dry-run/--execute', default=True, help='Dry run mode')
@click.pass_context
def ref_clean(ctx, remove, dry_run):
    """Clean up unused references"""
    from know_lib.reference_tools import ReferenceManager

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


@cli.command()
@click.option('--max', '-m', default=10, help='Maximum suggestions')
@click.pass_context
def ref_suggest(ctx, max):
    """Suggest connections for orphaned references"""
    from know_lib.reference_tools import ReferenceManager

    ref_mgr = ReferenceManager(ctx.obj['graph'], ctx.obj['entities'], ctx.obj['deps'])
    suggestions = ref_mgr.suggest_reference_connections(max_suggestions=max)

    if not suggestions:
        console.print("[yellow]No suggestions found[/yellow]")
        return

    console.print(f"\n[bold]Suggested Connections[/bold]\n")

    for ref_id, entity_id, score in suggestions:
        console.print(f"[cyan]{ref_id}[/cyan] → [green]{entity_id}[/green] ({score}%)")


# Rules command group
@cli.group()
def rules():
    """Query dependency rules and graph structure"""
    pass


def _load_rules():
    """Load dependency rules from config file"""
    rules_path = Path(__file__).parent / "config" / "dependency-rules.json"
    with open(rules_path, 'r') as f:
        return json.load(f)


@rules.command(name='describe')
@click.argument('type_name')
def rules_describe(type_name):
    """Describe entity, reference, or meta type, or list all types

    Examples:
        know rules describe feature
        know rules describe business_logic
        know rules describe phases
        know rules describe entities       # List all entity types
        know rules describe references     # List all reference types
        know rules describe meta           # List all meta sections
    """
    rules = _load_rules()
    type_lower = type_name.lower()

    # Handle list commands
    if type_lower in ['entities', 'entity']:
        console.print("\n[bold cyan]Available Entity Types:[/bold cyan]\n")
        for entity_type in sorted(rules.get('entity_description', {}).keys()):
            console.print(f"  • [green]{entity_type}[/green]")
        console.print("\n[dim]Use: know rules describe <type> for details[/dim]")
        return

    if type_lower in ['references', 'reference', 'refs']:
        console.print("\n[bold cyan]Available Reference Types:[/bold cyan]\n")
        for ref_type in sorted(rules.get('reference_description', {}).keys()):
            console.print(f"  • [green]{ref_type}[/green]")
        console.print("\n[dim]Use: know rules describe <type> for details[/dim]")
        return

    if type_lower == 'meta':
        console.print("\n[bold cyan]Available Meta Sections:[/bold cyan]\n")
        for meta_section in sorted(rules.get('meta_description', {}).keys()):
            console.print(f"  • [green]{meta_section}[/green]")
        console.print("\n[dim]Use: know rules describe <section> for details[/dim]")
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
def rules_before(entity_type):
    """Show what entity types can come before this type in dependency graph

    Example:
        know rules before component
        # Shows: action, component
    """
    rules = _load_rules()
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
def rules_after(entity_type):
    """Show what entity types can come after this type in dependency graph

    Example:
        know rules after feature
        # Shows: action
    """
    rules = _load_rules()
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
def rules_graph():
    """Visualize the high-level dependency graph structure"""
    rules = _load_rules()

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


if __name__ == '__main__':
    cli()