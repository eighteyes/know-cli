#!/usr/bin/env python3
"""
Know Tool - Python implementation for efficient graph operations
Command-line interface for managing the specification graph
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
    GraphValidator, SpecGenerator, LLMManager, GraphDiff, get_graph_stats
)


console = Console()


@click.group()
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


@cli.command(name='uses')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependencies or just direct ones')
@click.pass_context
def uses(ctx, entity_path, recursive):
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


@cli.command(name='down')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependents or just direct ones')
@click.pass_context
def down(ctx, entity_path, recursive):
    """Alias for 'used-by' - show what uses this entity (go down the dependency chain)"""
    ctx.invoke(used_by, entity_path=entity_path, recursive=recursive)


@cli.command(name='used-by')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependents or just direct ones')
@click.pass_context
def used_by(ctx, entity_path, recursive):
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


@cli.command(name='up')
@click.argument('entity_path')
@click.option('--recursive/--direct', default=True,
              help='Show all dependencies or just direct ones')
@click.pass_context
def up(ctx, entity_path, recursive):
    """Alias for 'uses' - show what an entity uses (go up the dependency chain)"""
    ctx.invoke(uses, entity_path=entity_path, recursive=recursive)


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


@cli.command(name='link')
@click.argument('from_entity')
@click.argument('to_entity')
@click.pass_context
def link(ctx, from_entity, to_entity):
    """Add a dependency between entities"""
    success = ctx.obj['entities'].add_dependency(from_entity, to_entity)

    if success:
        console.print(f"[green]✓ Added dependency: {from_entity} -> {to_entity}[/green]")
    else:
        console.print(f"[red]✗ Dependency already exists or failed to add[/red]")
        sys.exit(1)


@cli.command(name='unlink')
@click.argument('from_entity')
@click.argument('to_entity')
@click.pass_context
def unlink(ctx, from_entity, to_entity):
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
@click.argument('entity_id')
@click.option('--code-graph', '-c', help='Path to code-graph.json (required for cross-graph tracing)')
@click.option('--spec-graph', '-s', help='Path to spec-graph.json (required for cross-graph tracing)')
@click.pass_context
def trace(ctx, entity_id, code_graph, spec_graph):
    """Trace entity across product-code boundary showing full upstream/downstream chain

    Examples:
        know -g .ai/spec-graph.json trace component:cli-commands -c .ai/code-graph.json
        know -g .ai/code-graph.json trace module:auth-handler -s .ai/spec-graph.json
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

                        # We could recursively trace the component here, but that gets complex
                        # For now, just note it exists
                    else:
                        console.print(f"  [red]Spec graph not found: {spec_graph}[/red]")
            else:
                console.print("  [dim](this module doesn't implement any spec components)[/dim]")
        else:
            console.print("  [dim](cross-graph links only work for module entities)[/dim]")

    elif not code_graph and not spec_graph:
        console.print(f"\n[dim]Tip: Use -c and -s flags to trace across graphs[/dim]")
        console.print(f"[dim]Example: know -g .ai/spec-graph.json trace {entity_id} -c .ai/code-graph.json[/dim]")

    console.print()


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


@cli.command()
@click.pass_context
def gap_missing(ctx):
    """List missing connections in dependency chains"""
    from src.gap_analysis import GapAnalyzer

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


@cli.command()
@click.pass_context
def ref_orphans(ctx):
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


@cli.command()
@click.pass_context
def ref_usage(ctx):
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


@cli.command()
@click.option('--remove/--keep', default=False, help='Remove unused references')
@click.option('--dry-run/--execute', default=True, help='Dry run mode')
@click.pass_context
def ref_clean(ctx, remove, dry_run):
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


@cli.command()
@click.option('--max', '-m', default=10, help='Maximum suggestions')
@click.pass_context
def ref_suggest(ctx, max):
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


# Rules command group
@cli.group()
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
        know -g .ai/spec-graph.json rules describe feature
        know -g .ai/code-graph.json rules describe module
        know rules describe business_logic
        know rules describe phases
        know rules describe entities       # List all entity types
        know rules describe references     # List all reference types
        know rules describe meta           # List all meta sections
    """
    rules_path = ctx.obj.get('rules_path') if ctx.obj else None
    rules = _load_rules(rules_path)
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
@click.pass_context
def rules_before(ctx, entity_type):
    """Show what entity types can come before this type in dependency graph

    Examples:
        know -g .ai/spec-graph.json rules before component
        know -g .ai/code-graph.json rules before module
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
        know -g .ai/spec-graph.json rules after feature
        know -g .ai/code-graph.json rules after module
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
        know -g .ai/spec-graph.json rules graph
        know -g .ai/code-graph.json rules graph
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
    console.print(f"  • Use /know-add <feature-name> to start a new feature")
    console.print(f"  • Use /know-list to see all features")


@cli.command()
@click.argument('entity_id')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json']), default='markdown',
              help='Output format')
@click.pass_context
def spec(ctx, entity_id, format):
    """Generate specification for a single entity

    This command generates a specification document for an entity from the graph.
    Run multiple times to build up a complete feature specification.

    Examples:
        know spec feature:login-form
        know spec component:auth-button >> .ai/know/user-auth/spec.md
        know spec action:submit-credentials --format json
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
        spec_content = generator.generate_entity_spec(entity_id, include_deps=True)

        if format == 'json':
            # Output as JSON
            spec_data = {
                'entity_id': entity_id,
                'entity_data': entity_data,
                'spec': spec_content
            }
            print(json.dumps(spec_data, indent=2))
        else:
            # Output as markdown
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


@cli.command()
@click.argument('graph1', type=click.Path(exists=True))
@click.argument('graph2', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed diff')
@click.option('--format', '-f', type=click.Choice(['terminal', 'json']), default='terminal',
              help='Output format')
def diff(graph1, graph2, verbose, format):
    """Compare two graph files and show differences

    Shows added/removed/modified entities, dependencies, and references.

    Examples:
        know diff spec-graph.json spec-graph-backup.json
        know diff .ai/spec-graph.json /tmp/spec-graph.json --verbose
        know diff graph1.json graph2.json --format json
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
                for entity in diff_result['entities']['added']:
                    console.print(f"  [green]+ {entity['key']}[/green]")
                    console.print(f"    name: {entity['data'].get('name', 'N/A')}")
                    console.print(f"    description: {entity['data'].get('description', 'N/A')}")
                console.print()

            if diff_result['entities']['removed']:
                console.print("[bold]Removed Entities:[/bold]")
                for entity in diff_result['entities']['removed']:
                    console.print(f"  [red]- {entity['key']}[/red]")
                    console.print(f"    name: {entity['data'].get('name', 'N/A')}")
                    console.print(f"    description: {entity['data'].get('description', 'N/A')}")
                console.print()

            if diff_result['entities']['modified']:
                console.print("[bold]Modified Entities:[/bold]")
                for entity in diff_result['entities']['modified']:
                    console.print(f"  [yellow]~ {entity['key']}[/yellow]")
                    for key in entity['old'].keys() | entity['new'].keys():
                        old_val = entity['old'].get(key)
                        new_val = entity['new'].get(key)
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


@cli.command()
@click.pass_context
def phases(ctx):
    """Show all phases with their entities grouped by phase"""
    import re
    from pathlib import Path

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
    console.print(f"[dim]Legend: ✅ completed  🔄 in-progress  📋 planned  ⚪ no status[/dim]")


if __name__ == '__main__':
    cli()