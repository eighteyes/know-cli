# Know Codebase Architecture Analysis

## Overview
Know is a Python-based CLI tool for managing specification and code graphs. It uses a modular architecture with clear separation of concerns, comprehensive testing, and LLM integration capabilities.

**Project Location:** `/workspace/know-cli/know/`
**Main Entry Point:** `know.py` (1,999 lines)
**Core Modules:** `src/` (4,075 lines total across 13 modules)
**Tests:** `tests/` and `/workspace/know-cli/tests/`

---

## 1. Module Structure in know/src/

### Core Modules (Fundamental Operations)

| Module | Lines | Purpose | Key Classes/Functions |
|--------|-------|---------|----------------------|
| **graph.py** | 165 | Graph loading, saving, and basic operations | `GraphManager` |
| **cache.py** | 124 | Thread-safe in-memory caching with file sync | `GraphCache` |
| **entities.py** | 262 | Entity CRUD operations | `EntityManager` |
| **dependencies.py** | 375 | Dependency management and validation | `DependencyManager` |
| **validation.py** | 512 | Graph structure and schema validation | `GraphValidator` |

### Advanced/Integration Modules

| Module | Lines | Purpose | Key Classes/Functions |
|--------|-------|---------|----------------------|
| **llm.py** | 562 | LLM provider integration with multiple backends | `LLMManager`, `LLMProvider`, `MockProvider` |
| **generators.py** | 474 | Specification generation and enhancement | `SpecGenerator` |
| **async_graph.py** | 374 | Async/await wrapper for graph operations | `AsyncGraphManager`, `AsyncGraphPool` |
| **diff.py** | 225 | Graph diff and change tracking | `GraphDiff` |
| **utils.py** | 399 | Utility functions (parsing, formatting, validation) | Various helper functions |
| **reference_tools.py** | 281 | Reference node management | `ReferenceManager` |
| **gap_analysis.py** | 280 | Gap analysis and coverage metrics | Analysis functions |

### Supporting Modules

| Module | Lines | Purpose |
|--------|-------|---------|
| **visualizers/__init__.py** | - | Graph visualization interface |
| **visualizers/mermaid.py** | - | Mermaid diagram generation |
| **__init__.py** | 42 | Package exports and public API |

---

## 2. Component Separation Strategy

### Separation by Responsibility

#### Data Layer (`graph.py`, `cache.py`)
- **GraphManager**: Raw graph I/O, lazy loading, NetworkX integration
- **GraphCache**: Thread-safe caching with file modification tracking
- **Responsibility**: File I/O, in-memory representation, basic algorithms

```python
# Example: GraphManager handles basic operations
class GraphManager:
    - get_graph()
    - save_graph()
    - get_entities() / get_references() / get_dependencies()
    - find_dependencies() / find_dependents()
    - topological_sort(), detect_cycles()
    - validate_dependencies()
```

#### Entity Management (`entities.py`)
- **EntityManager**: Entity CRUD, validation, dependency linkage
- **Responsibility**: Entity creation/updating/deletion, schema enforcement
- **Interacts with**: GraphManager for persistence, rules for validation

```python
class EntityManager:
    - list_entities(type)
    - get_entity(path)
    - add_entity()
    - update_entity()
    - delete_entity()
    - add_dependency() / remove_dependency()
```

#### Dependency Management (`dependencies.py`)
- **DependencyManager**: Dependency rules, resolution, chain detection
- **Responsibility**: Validate allowed dependencies, resolve chains, detect issues
- **Rules-driven**: Loads dependency-rules.json or code-dependency-rules.json

```python
class DependencyManager:
    - is_valid_dependency(from, to)
    - get_allowed_targets(type)
    - get_dependencies() / get_dependents()
    - resolve_chain()
    - detect_cycles()
```

#### Validation (`validation.py`)
- **GraphValidator**: Comprehensive graph validation
- **Responsibility**: Schema validation, reference integrity, completeness checks
- **Rules-based**: Uses entity_description and entity_note from rules

```python
class GraphValidator:
    - validate_all()
    - validate_entities()
    - validate_references()
    - validate_dependencies()
```

#### LLM Integration (`llm.py`)
- **LLMProvider**: Base provider interface for different LLM backends
- **LLMManager**: Orchestrates providers, handles workflows
- **MockProvider**: Testing/local provider
- **Responsibility**: Multi-provider LLM abstraction, request/response handling

#### Async Layer (`async_graph.py`)
- **AsyncGraphManager**: Async wrapper around core operations
- **AsyncGraphPool**: Connection pool for concurrent access
- **Responsibility**: Non-blocking I/O for web server integration

#### CLI Layer (`know.py`)
- **Large Click-based CLI**: 1,999 lines
- Commands: add, list, remove, link, unlink, review, build, prepare, validate, etc.
- Uses all core modules via dependency injection
- Rich formatting for output

---

## 3. Testing Patterns and Structure

### Test Locations
```
/workspace/know-cli/tests/          # Integration tests, property tests
  - test_commands.py                # CLI command tests
  - test_bug_fixes.py              # Bug fix regression tests
  - test_dependencies.py           # Dependency validation
  - test_entities.py               # Entity operations
  - test_graph.py                  # Graph operations
  - test_llm.py                    # LLM provider tests
  - test_utils.py                  # Utility function tests
  - test_validation.py             # Validation logic tests
  - property/                      # Property-based tests
    - test_invariants.py
    - test_golden_thread.py
    - strategies.py               # Hypothesis strategies
  - fuzz/                          # Fuzzing tests
    - generator.py
    - run_fuzz.py
```

### Testing Patterns

#### 1. Fixture-based Setup
```python
@pytest.fixture
def temp_graph_setup():
    """Create temporary graph with entities for testing"""
    # Create temp file with test data
    # Return manager instances ready for use
    return em, temp_file
```

#### 2. Snapshot/Comparison Testing
- Tests verify graph structure consistency
- Check topological ordering
- Validate dependency chains

```python
def test_topological_sort(temp_graph_file):
    """Verify build order is correct"""
    gm = GraphManager(str(temp_graph_file))
    order = gm.topological_sort()

    # Dependencies come before dependents
    assert order.index("user:owner") < order.index("feature:auth")
```

#### 3. Error Case Testing
```python
def test_add_entity(temp_graph_setup):
    """Test both success and duplicate detection"""
    em, _ = temp_graph_setup

    # Success case
    success = em.add_entity("user", "dev", {...})
    assert success

    # Duplicate case
    success = em.add_entity("user", "dev", {...})
    assert not success  # Should fail
```

#### 4. Property-Based Testing
- **strategies.py**: Hypothesis strategies for graph generation
- **test_invariants.py**: Graph invariants that must always hold
- **test_golden_thread.py**: Core workflow validation

#### 5. Fuzzing
- **run_fuzz.py**: Mutation-based fuzzing
- **generator.py**: Graph mutation strategies

### Test Running
```bash
pytest tests/ -v              # Run all tests
python -m pytest tests/property/  # Run property tests
python tests/fuzz/run_fuzz.py     # Run fuzzing
```

---

## 4. Where New Python Modules Should Be Added

### Recommended Structure for New Modules

```
know/src/
├── __init__.py              # Update with new exports
├── core/                    # ← NEW: If adding multiple related modules
│   ├── __init__.py
│   ├── module_a.py
│   └── module_b.py
└── new_module.py           # ← OR: Single module at top level

tests/
├── test_new_module.py       # Mirror src structure
└── core/
    └── test_module_a.py
```

### Placement Guidelines

| Type of Module | Location | Example |
|----------------|----------|---------|
| **Data structure/model** | `src/` top-level | `task_manager.py` |
| **Integration point** | `src/` top-level | `beads_bridge.py` |
| **Synchronization/coordination** | `src/` top-level | `task_sync.py` |
| **Multiple related utilities** | `src/{category}/` | `src/sync/task_sync.py` + `src/sync/task_manager.py` |
| **External system bridge** | `src/{system_name}/` | `src/beads/` or `src/bridge/` |

### For the Three Modules in Question

**Recommended placement:**
```
know/src/
├── beads_bridge.py          # External system integration
├── task_manager.py          # Task/queue management
└── task_sync.py             # Synchronization logic
```

**Alternative (if grouped logically):**
```
know/src/
└── sync/                     # Task synchronization subsystem
    ├── __init__.py
    ├── manager.py           # → task_manager.py
    ├── sync.py              # → task_sync.py
    └── beads.py             # → beads_bridge.py
```

### Module Registration Pattern
All modules must be registered in `src/__init__.py`:

```python
# src/__init__.py
from .beads_bridge import BeadsBridge
from .task_manager import TaskManager
from .task_sync import TaskSync

__all__ = [
    # ... existing exports ...
    "BeadsBridge",
    "TaskManager",
    "TaskSync"
]
```

---

## 5. Import Patterns and Dependencies

### Import Strategy

#### Internal Imports (Relative)
```python
# Standard pattern: relative imports within src/
from .graph import GraphManager
from .dependencies import DependencyManager
from .validation import GraphValidator
```

#### External Dependencies
```python
import asyncio
import json
import click
from pathlib import Path
from typing import Dict, List, Optional, Any
import networkx as nx
from rich.console import Console
```

#### Circular Dependency Avoidance
The architecture avoids circular dependencies through:
1. **Dependency Injection**: Managers pass instances rather than importing
2. **Minimal Coupling**: Each module depends on GraphManager, not on each other
3. **Late Imports**: Some imports are deferred (e.g., in LLM modules)

```python
# Good: DependencyManager depends on GraphManager
class DependencyManager:
    def __init__(self, graph_manager, rules_path=None):
        self.graph = graph_manager  # Injected dependency
```

### Dependency Graph

```
CLI (know.py)
    ↓
[All Core Modules]
    ↓
GraphManager ← GraphCache
    ↓
EntityManager ← DependencyManager ← GraphManager
    ↓
GraphValidator
    ↓
SpecGenerator (uses Entities + Dependencies)
    ↓
LLMManager (uses LLMProvider)
    ↓
AsyncGraphManager (wraps all above)
    ↓
ReferenceManager, GapAnalysis, Diff, Utils
```

### Import Convention in Tests

```python
# tests/test_entities.py
import pytest
from pathlib import Path
from src import GraphManager, EntityManager

@pytest.fixture
def temp_graph_setup():
    gm = GraphManager(str(temp_file))
    em = EntityManager(gm)
    return em, temp_file
```

---

## 6. How CLI Commands Map to Internal Modules

### Command Mapping Architecture

```python
# know.py: Global Click group sets up all managers
@click.group()
@click.option('--graph-path', '-g', default='.ai/spec-graph.json')
@click.option('--rules-path', '-r', default=None)
@click.pass_context
def cli(ctx, graph_path, rules_path):
    """Initialize all managers once, inject into context"""
    ctx.obj['graph'] = GraphManager(str(graph_path))
    ctx.obj['entities'] = EntityManager(ctx.obj['graph'], rules_path=rules_path)
    ctx.obj['deps'] = DependencyManager(ctx.obj['graph'], rules_path=rules_path)
    ctx.obj['validator'] = GraphValidator(ctx.obj['graph'], rules_path=rules_path)
    ctx.obj['generator'] = SpecGenerator(...)
    ctx.obj['llm'] = LLMManager()
```

### Sample Command Implementations

#### Simple CRUD Commands
```python
@cli.command()
@click.argument('entity_type')
@click.pass_context
def list_type(ctx, entity_type):
    """List entities of specific type"""
    entities = ctx.obj['entities'].list_entities(entity_type)
    # Format and display
```

**Modules used:** `EntityManager`

#### Dependency Commands
```python
@cli.command()
@click.argument('from_entity')
@click.argument('to_entity')
@click.pass_context
def link(ctx, from_entity, to_entity):
    """Add dependency"""
    success = ctx.obj['deps'].add_dependency(from_entity, to_entity)
    # Validate and save
```

**Modules used:** `DependencyManager`, `GraphValidator`

#### Validation Commands
```python
@cli.command()
@click.pass_context
def validate(ctx):
    """Validate entire graph"""
    is_valid, results = ctx.obj['validator'].validate_all()
    dep_valid, dep_errors = ctx.obj['deps'].validate_graph()
    # Display results
```

**Modules used:** `GraphValidator`, `DependencyManager`

#### Generation Commands
```python
@cli.command()
@click.argument('entity_type')
@click.pass_context
def review(ctx, entity_type):
    """Review and enhance specifications"""
    # Uses generator with LLM
    ctx.obj['generator'].generate_description(...)
    ctx.obj['llm'].process(...)
```

**Modules used:** `SpecGenerator`, `LLMManager`

#### Analysis Commands
```python
@cli.command()
@click.pass_context
def coverage(ctx):
    """Analyze graph coverage"""
    # Uses gap analysis and traversal
    graph_data = ctx.obj['graph'].load()
    # Compute coverage metrics
```

**Modules used:** `GraphManager`, `gap_analysis` utilities

### Command Categories

| Category | Commands | Key Modules |
|----------|----------|-------------|
| **Entity CRUD** | add, remove, update, list, list-type | EntityManager |
| **Dependencies** | link, unlink, uses, used-by, up, down | DependencyManager |
| **Validation** | validate, cycles | GraphValidator |
| **Generation** | review, plan, build, prepare | SpecGenerator, LLMManager |
| **Analysis** | coverage, diff, stats, gaps | GapAnalysis, Diff, Utils |
| **Meta** | phases, phases-done | GraphManager |

---

## 7. Integration Points for New Modules

### Where beads_bridge.py Would Fit

**Purpose:** External system integration
**Location:** `know/src/beads_bridge.py`
**Dependencies:** Likely needs:
- `GraphManager` for reading/writing graph data
- `EntityManager` for creating/updating task entities
- `DependencyManager` for linking tasks to features

```python
class BeadsBridge:
    """Interface to external Beads system"""

    def __init__(self, graph_manager, entity_manager, dep_manager):
        self.graph = graph_manager
        self.entities = entity_manager
        self.deps = dep_manager

    def sync_tasks_to_beads(self, feature_id: str) -> bool:
        """Push tasks from graph to Beads"""
        # Get feature tasks
        # Map to Beads format
        # Send to external API
        pass

    def pull_beads_updates(self) -> Dict:
        """Get updates from Beads, update graph"""
        # Fetch from external API
        # Update entity status
        # Record dependencies
        pass
```

### Where task_manager.py Would Fit

**Purpose:** Task lifecycle and state management
**Location:** `know/src/task_manager.py`
**Dependencies:** Likely needs:
- `EntityManager` for task entity operations
- `DependencyManager` for task dependencies
- `GraphValidator` for state validation

```python
class TaskManager:
    """Manage task lifecycle"""

    def __init__(self, entity_manager, dep_manager, validator):
        self.entities = entity_manager
        self.deps = dep_manager
        self.validator = validator

    def create_task(self, feature_id: str, name: str, **metadata) -> bool:
        """Create new task, link to feature"""
        pass

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        pass

    def get_task_chain(self, task_id: str) -> List[str]:
        """Get dependency chain"""
        pass
```

### Where task_sync.py Would Fit

**Purpose:** Synchronization and coordination between systems
**Location:** `know/src/task_sync.py`
**Dependencies:** Likely needs:
- `TaskManager` for local task operations
- `BeadsBridge` for external synchronization
- `GraphValidator` for consistency checks

```python
class TaskSync:
    """Synchronize tasks between graph and Beads"""

    def __init__(self, task_manager, beads_bridge, validator):
        self.tasks = task_manager
        self.beads = beads_bridge
        self.validator = validator

    def sync_all(self) -> Dict:
        """Two-way sync: graph ↔ Beads"""
        pass

    def detect_conflicts(self) -> List[str]:
        """Find inconsistencies"""
        pass

    def resolve_conflicts(self, strategy: str = 'graph-source') -> bool:
        """Resolve by preferred source"""
        pass
```

### CLI Integration Pattern

```python
# In know.py, add to main CLI setup:
@click.group()
@click.pass_context
def cli(ctx, graph_path, rules_path):
    # ... existing setup ...

    # Add new managers
    ctx.obj['task_manager'] = TaskManager(
        ctx.obj['entities'],
        ctx.obj['deps'],
        ctx.obj['validator']
    )
    ctx.obj['beads_bridge'] = BeadsBridge(
        ctx.obj['graph'],
        ctx.obj['entities'],
        ctx.obj['deps']
    )
    ctx.obj['task_sync'] = TaskSync(
        ctx.obj['task_manager'],
        ctx.obj['beads_bridge'],
        ctx.obj['validator']
    )

# New commands can then use:
@cli.command()
@click.pass_context
def sync(ctx):
    """Sync graph with Beads"""
    result = ctx.obj['task_sync'].sync_all()
    console.print(result)
```

---

## 8. Configuration and Rules

### Configuration Files Location: `/workspace/know-cli/know/config/`

| File | Purpose | Usage |
|------|---------|-------|
| **dependency-rules.json** | Spec graph entity types and dependencies | Loaded by DependencyManager for spec graphs |
| **code-dependency-rules.json** | Code graph entity types and dependencies | Loaded by DependencyManager for code graphs |
| **llm-providers.json** | LLM provider configurations | Loaded by LLMManager |
| **llm-workflows.json** | LLM workflow definitions | Used for generation tasks |

### Auto-Detection Logic
```python
# In know.py and validation.py
if rules_path is None:
    if 'code-graph' in str(graph_path):
        rules_path = "code-dependency-rules.json"
    else:
        rules_path = "dependency-rules.json"
```

---

## 9. Key Design Patterns

### 1. Manager Pattern
Each major subsystem has a `Manager` class:
- `GraphManager`: Core graph operations
- `EntityManager`: Entity operations
- `DependencyManager`: Dependency operations
- `AsyncGraphManager`: Async operations

### 2. Validator Pattern
Validation is separated from operations:
- `GraphValidator`: Comprehensive validation
- `DependencyManager.validate_graph()`: Dependency-specific validation
- `EntityManager.validate_entity()`: Entity-specific validation

### 3. Provider Pattern (LLM)
Multiple implementations of abstract provider:
- `LLMProvider`: Base interface
- Implementations for different backends
- `MockProvider`: Testing implementation

### 4. Dependency Injection
Managers are injected via CLI context:
```python
ctx.obj['manager'] = ManagerClass(dependencies)
```

### 5. Caching Strategy
- Thread-safe in-memory cache (`GraphCache`)
- Automatic invalidation on writes
- Modification time tracking for reload detection

### 6. Rules-Based Behavior
- Entity types and dependencies defined in JSON rules
- Rules loaded at startup, not hardcoded
- Enables multi-graph support (spec vs code)

---

## 10. Development Workflow

### Running Tests
```bash
cd /workspace/know-cli/know
python -m pytest tests/ -v          # All tests
python -m pytest tests/test_graph.py -v  # Specific test
python -m pytest tests/property/ -v      # Property tests
python tests/fuzz/run_fuzz.py            # Fuzzing
```

### Adding a New Test
1. Create `tests/test_new_feature.py`
2. Use fixtures from other tests as templates
3. Create temporary graph files with `tempfile`
4. Test both success and error cases
5. Run: `pytest tests/test_new_feature.py -v`

### Module Development Checklist

- [ ] Create module at `src/new_module.py`
- [ ] Implement class with clear interface
- [ ] Add proper docstrings (Google style)
- [ ] Use dependency injection for dependencies
- [ ] Create `tests/test_new_module.py`
- [ ] Add tests for normal and error cases
- [ ] Update `src/__init__.py` exports
- [ ] Run validation: `npm run validate-graph`
- [ ] Run tests: `pytest tests/ -v`

---

## Summary Table: Module Purposes

| Module | Role | Dependencies | Exports |
|--------|------|-------------|---------|
| `graph.py` | Data layer | networkx, pathlib | GraphManager |
| `cache.py` | In-memory persistence | os, json, threading | GraphCache |
| `entities.py` | Entity CRUD | GraphManager, rules | EntityManager |
| `dependencies.py` | Dependency logic | GraphManager, rules | DependencyManager |
| `validation.py` | Graph validation | GraphManager, rules | GraphValidator |
| `llm.py` | LLM integration | urllib, json, os | LLMManager, LLMProvider, MockProvider |
| `generators.py` | Spec generation | EntityManager, DependencyManager, LLMManager | SpecGenerator |
| `async_graph.py` | Async wrapper | All core modules | AsyncGraphManager, AsyncGraphPool |
| `diff.py` | Change tracking | GraphManager | GraphDiff |
| `utils.py` | Utilities | re, pathlib | parse_entity_id, format_entity_id, etc. |
| `reference_tools.py` | Reference management | GraphManager, EntityManager, DependencyManager | ReferenceManager |
| `gap_analysis.py` | Gap analysis | GraphManager | Analysis functions |
| `__init__.py` | Package exports | All modules | All public APIs |

---

## Technical Stack

```
Core Framework:
- click (CLI framework)
- networkx (Graph algorithms)
- pydantic (Data validation)

I/O & Async:
- aiofiles (Async file operations)
- pathlib (Path handling)

Testing:
- pytest (Test framework)
- pytest-asyncio (Async test support)
- pytest-cov (Coverage reporting)

Presentation:
- rich (Terminal formatting)

Development:
- black (Code formatting)
- mypy (Type checking)
- python-dotenv (Environment management)
```

---

## Notes for Implementation

1. **Thread Safety**: GraphCache uses `threading.RLock()` for concurrent access
2. **Async Ready**: AsyncGraphManager can wrap synchronous operations
3. **Error Handling**: All operations return `(success: bool, error: Optional[str])`
4. **Type Hints**: Full type annotations throughout
5. **Docstrings**: Google-style docstrings on all public APIs
6. **Testing**: Comprehensive fixture-based testing with multiple strategies
