# Scripts Index

Tracking all scripts in the `/scripts` directory with their descriptions and maturity levels.

## Scripts Inventory

### Graph Management & Reporting

| Script | Status | Description |
|--------|--------|-------------|
| `graph-reporter.sh` | **Functional** | Interactive graph analysis tool with queries, dependency analysis, and visual reporting for spec-graph.json |
| `mod-graph.sh` | **Functional** | Clean CLI tool for managing knowledge graph entities and connections. Fast command-line interface for CRUD operations |
| `mod-graph-tui.sh` | **Deprecated** | Dialog-based TUI version (replaced by cleaner CLI approach) |

### Graph Analysis Tools

| Script | Status | Description |
|--------|--------|-------------|
| `dependency-metrics.sh` | **Functional** | Calculate comprehensive dependency metrics (fan-in/out, complexity, depth) |
| `critical-path.sh` | **Functional** | Find critical paths and longest dependency chains in the graph |
| `dependency-impact.sh` | **Functional** | Analyze impact of removing or changing specific entities |
| `dependency-explorer.sh` | **Functional** | Interactive dependency graph explorer with search and filtering |
| `dependency-tree-walker.sh` | **Functional** | Walk dependency trees showing detailed paths (up/down/both directions) |
| `tight-coupling.sh` | **Functional** | Find tightly coupled components and strongly connected components |
| `complexity-scorer.sh` | **Functional** | Score complexity of entities and overall graph architecture |

### Graph Visualization

| Script | Status | Description |
|--------|--------|-------------|
| `graph-visualizer.sh` | **Functional** | Generate visual representations in multiple formats (dot, ascii, mermaid, svg, png) |

### Graph Health & Maintenance

| Script | Status | Description |
|--------|--------|-------------|
| `find-disconnects.sh` | **Functional** | Find disconnected, orphaned, and missing entities in dependency graph |
| `fix-disconnects.sh` | **Functional** | Interactive tool to fix disconnected entities |
| `fix-disconnects-cli.sh` | **Functional** | CLI version with options for fixing disconnected entities |
| `dead-code-detector.sh` | **Functional** | Detect potentially unused/dead entities in the graph |
| `check-externals.sh` | **Functional** | Analyze external dependencies usage and patterns |

### Build & Optimization

| Script | Status | Description |
|--------|--------|-------------|
| `build-order-optimizer.sh` | **Functional** | Optimize build/processing order using topological sort with multiple strategies |
| `bundle-analyzer.sh` | **Functional** | Analyze dependency bundles and identify optimization opportunities |

### Architecture & Validation

| Script | Status | Description |
|--------|--------|-------------|
| `architecture-validator.sh` | **Functional** | Validate architectural patterns and constraints against rules |

## Status Levels

- **Functional**: Production-ready, tested, documented
- **Beta**: Working but may need refinement
- **Alpha**: Basic functionality, needs testing
- **Draft**: Initial implementation, incomplete
- **Deprecated**: No longer maintained or replaced

## Usage Examples

### Graph Reporter
```bash
./scripts/graph-reporter.sh
# Interactive menu-driven graph analysis
```

### Graph Modifier
```bash
# Entity management
./scripts/mod-graph.sh list features
./scripts/mod-graph.sh add features new-feature "New Feature Name"
./scripts/mod-graph.sh show features new-feature

# Graph connections
./scripts/mod-graph.sh connect feature:new-feature platform:aws-infrastructure
./scripts/mod-graph.sh deps user:owner

# Utilities
./scripts/mod-graph.sh search telemetry
./scripts/mod-graph.sh stats
```

---
*Last updated: $(date '+%Y-%m-%d')*