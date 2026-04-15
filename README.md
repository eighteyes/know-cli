# know

Structured context for AI-driven software development. Spec graphs, not spec files.

Know turns product decisions into dependency graphs that LLMs can traverse — linking **what** you're building and **why** to **how** it gets implemented. Instead of brittle markdown specs that rot over time, you get a queryable graph where information lives in one place and relationships are first-class.

## Install

```bash
npm install -g know-cli
```

Requires Node.js >= 14 and Python >= 3.8.

## Quick Start

```bash
# Initialize in your project
know init .

# Start building your spec graph
/know:plan          # Product discovery conversation
/know:add           # Add features interactively
/know:build <feat>  # Build with structured context
/know:review <feat> # Acceptance testing walkthrough
/know:done <feat>   # Archive completed work
```

`know init` installs slash commands and a skill into your project for use with [Claude Code](https://claude.com/claude-code).

## Why Graphs Over Spec Files

Spec files are fine for humans. For AI, they're token overhead — brittle snapshots that bloat, duplicate information, and rot. Spec graphs solve this:

- **Single source of truth** — information lives in one place, not scattered across files
- **Queryable relationships** — traverse from user intent to implementation in a single query
- **Generated on demand** — specs are produced from the graph when needed, always current
- **Deterministic completion** — feature delivery is a graph state, not a checklist

## Dual Graph System

Know maintains two graphs in `.ai/know/`:

### Spec Graph (`spec-graph.json`) — Product Intent

Maps who uses your product, what they need, and how it works:

```
Project -> User -> Objective -> Feature -> Workflow -> Action -> Component -> Operation
```

### Code Graph (`code-graph.json`) — Codebase Architecture

Maps your actual code structure and dependencies:

```
module -> [module, package, external-dep]
package -> [package, module, external-dep]
class   -> [class, interface, module]
function -> [function, module, class]
```

Graphs cross-link via `implementation` (spec->code) and `graph-link` (code->spec) references.

## LLM Workflow

The primary interface is through slash commands in Claude Code:

| Command | Purpose |
|---------|---------|
| `/know:plan` | Phased product discovery conversation |
| `/know:add` | Add features with interactive QA |
| `/know:prepare` | Bootstrap an existing codebase |
| `/know:prebuild` | Validate specs align with graph |
| `/know:build <feat>` | 7-phase structured build workflow |
| `/know:review <feat>` | End-user acceptance testing |
| `/know:done <feat>` | Archive completed features |
| `/know:bug` | Track issues against features |
| `/know:change <feat>` | Structured change requests |
| `/know:connect` | Cross-link sparse graphs |
| `/know:validate` | Graph integrity checks |
| `/know:list` | Show features by status |
| `/know:schema` | Design custom graph schemas |
| `/know:fill-out` | Expand graph to full coverage |

## CLI Reference

The CLI is organized into two groups:

### Graph — Structure and Data

```bash
# Add entities and references
know add <type> <key> [<key2>...] '{"name":"...","description":"..."}'

# Dependencies
know link <from> <to> [<to2> <to3>...]
know unlink <from> <to> [<to2>...]

# Query
know list [--type <type>]
know get <entity_id>
know search <query>
know find <query>              # Semantic search
know related <entity_id>

# Graph traversal
know graph uses <entity_id>    # What does this depend on?
know graph used-by <entity_id> # What depends on this?
know graph build-order         # Topological sort
know graph diff a.json b.json  # Compare graphs

# Node operations
know nodes update <id> '{"name":"New Name"}'
know nodes rename <id> <new_key>
know nodes merge <from> <into>
know nodes clone <id> <new_key>
know nodes delete <id> [-y]
know nodes deprecate <id> --reason "..."

# Validation
know check validate            # Full graph validation
know check syntax              # Fast structural check
know check structure           # Schema and orphan check
know check semantics           # Dependency rules and cycles
know check health              # Comprehensive health report
know check stats               # Graph statistics

# Generation
know gen spec <entity_id>      # Generate entity specification
know gen feature-spec <feat>   # Feature specification
know gen sitemap               # Interface sitemap
know gen codemap <src_dir>     # Code structure map
know gen trace <entity_id>     # Cross product-code boundary
know gen trace-matrix          # Requirement traceability matrix
know gen rules graph           # Visualize dependency topology

# Visualization
know viz tree                  # ASCII tree
know viz mermaid               # Mermaid diagram
know viz dot                   # Graphviz DOT
know viz html                  # Interactive HTML (pyvis)
know viz d3                    # D3.js visualization
know viz fzf                   # Fuzzy finder
```

### Project — Feature Lifecycle

```bash
know feature contract <name>         # Display contract info
know feature validate-contracts      # Validate all contracts
know feature validate <name>         # Check if re-planning needed
know feature done <name>             # Complete and archive
know feature impact <target>         # Show affected features
know feature coverage <name>         # Test coverage

know meta get <section>              # Read meta sections
know meta set <section> <key> <val>  # Write meta sections
know horizons list                   # Show project horizons
know op status <feature>             # Operation-level progress
know req list <feature>              # Feature requirements
```

### Global Options

```bash
know -g <path>    # Use a specific graph file (default: .ai/know/spec-graph.json)
know -r <path>    # Override dependency rules file
```

Rules auto-detect based on graph filename. Spec graph uses `dependency-rules.json`, code graph uses `code-dependency-rules.json`.

## Customization

The graph schema is defined by dependency rules in `.ai/know/config/`. After `know init`, you get local copies you can modify:

- `dependency-rules.json` — spec graph entity types, allowed dependencies, reference types
- `code-dependency-rules.json` — code graph rules

Change the rules to reshape the graph model for your domain.

## Architecture

```
bin/know.js          # Node wrapper for npm distribution
know/know            # Bash entrypoint (venv + Python)
know/know.py         # Click CLI (~6400 lines)
know/src/            # Python modules (25 files)
  graph.py           #   Graph I/O and algorithms
  entities.py        #   Entity CRUD
  dependencies.py    #   Dependency rules and validation
  validation.py      #   Graph structure validation
  generators.py      #   Spec generation
  diff.py            #   Graph comparison
  visualizers/       #   tree, mermaid, dot, html, d3, fzf
know/config/         #   Default dependency rules
know/templates/      #   Slash command templates, feature scaffolds
```

## License

MIT
