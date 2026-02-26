# Feature: graph-visualization

## Summary
Visualize the spec-graph and code-graph in multiple output formats via `know viz` CLI commands. Supports Rich tree (terminal), Mermaid flowcharts, Graphviz DOT/SVG/PNG, interactive HTML (PyVis), and fzf fuzzy picking.

## Objectives
- `objective:query-graph` — Visual exploration of graph structure
- `objective:architect-system` — Understand dependency topology at a glance

## Users
- `user:developer` — Quick terminal tree view while coding
- `user:software-architect` — SVG/HTML exports for architecture review
- `user:ai-assistant` — Programmatic graph rendering

## Commands
| Command | Output | Dependencies |
|---|---|---|
| `know viz tree [entity]` | Rich Tree in terminal | none (rich installed) |
| `know viz mermaid [-o file]` | Mermaid flowchart syntax | none |
| `know viz dot [-o file] [-f svg\|png\|pdf]` | Graphviz file | graphviz (optional) |
| `know viz html [-o file] [--open]` | PyVis interactive HTML | pyvis (optional) |
| `know viz fzf` | fzf picker with entity details | iterfzf (optional) |

## Common Options
- `--type/-t TYPE` (multiple) — filter to entity type(s)
- `--depth/-d N` — limit BFS traversal depth
- `--refs/--no-refs` — include reference nodes
- `--entity/-e ID` — focus on entity neighborhood

## Architecture
- `know/src/visualizers/theme.py` — shared color map (entity type to fill/stroke/rich_style)
- `know/src/visualizers/base.py` — BaseVisualizer ABC + VisualizationData dataclass
- `know/src/visualizers/tree.py` — RichTreeVisualizer
- `know/src/visualizers/mermaid.py` — MermaidVisualizer (+ MermaidGenerator compat alias)
- `know/src/visualizers/dot.py` — DotVisualizer (optional graphviz)
- `know/src/visualizers/html.py` — HtmlVisualizer (optional pyvis)
- `know/src/visualizers/fzf.py` — FzfPicker (optional iterfzf)

## Status
**Complete** — implemented and smoke-tested Feb 2026.
