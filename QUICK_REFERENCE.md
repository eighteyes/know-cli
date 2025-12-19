# Quick Reference: Know Codebase

## File Organization Quick Lookup

### Core Data Management
```
know/src/graph.py              - Load, save, query graph (GraphManager)
know/src/cache.py              - Thread-safe caching (GraphCache)
know/src/entities.py           - Entity CRUD operations (EntityManager)
know/src/dependencies.py       - Dependency rules and operations (DependencyManager)
know/src/validation.py         - Graph validation (GraphValidator)
```

### Integration & Advanced
```
know/src/llm.py                - LLM providers (LLMManager, LLMProvider)
know/src/generators.py         - Spec generation (SpecGenerator)
know/src/async_graph.py        - Async operations (AsyncGraphManager)
know/src/diff.py               - Change tracking (GraphDiff)
know/src/reference_tools.py    - Reference management (ReferenceManager)
know/src/gap_analysis.py       - Coverage analysis
know/src/utils.py              - Helper functions
```

### New Task Management (To Be Added)
```
know/src/beads_bridge.py       - External system integration (BeadsBridge)
know/src/task_manager.py       - Task lifecycle (TaskManager)
know/src/task_sync.py          - Sync orchestration (TaskSync)
```

## Module Entry Points

### How to Use Each Manager

#### GraphManager - Basic Graph Operations
```python
from src import GraphManager

gm = GraphManager(".ai/spec-graph.json")
graph = gm.get_graph()
entities = gm.get_entities()
refs = gm.get_references()
deps = gm.find_dependencies("feature:auth")
dependents = gm.find_dependents("user:admin")
```

#### EntityManager - Entity CRUD
```python
from src import GraphManager, EntityManager

gm = GraphManager(".ai/spec-graph.json")
em = EntityManager(gm)

# List
entities = em.list_entities()
features = em.list_entities("feature")

# Get
entity = em.get_entity("user:owner")

# Create
em.add_entity("user", "developer", {"name": "Developer", "description": "Dev user"})

# Update
em.update_entity("user:owner", {"name": "Updated"})

# Delete
em.delete_entity("user:viewer")
```

#### DependencyManager - Dependency Operations
```python
from src import GraphManager, DependencyManager

gm = GraphManager(".ai/spec-graph.json")
dm = DependencyManager(gm)

# Query
deps = dm.get_dependencies("feature:auth")
dependents = dm.get_dependents("user:admin")

# Validate
valid = dm.is_valid_dependency("feature", "user")

# Analyze
cycles = dm.detect_cycles()
chain = dm.resolve_chain("feature:dashboard")
```

#### GraphValidator - Validation
```python
from src import GraphManager, GraphValidator

gm = GraphManager(".ai/spec-graph.json")
gv = GraphValidator(gm)

# Full validation
is_valid, results = gv.validate_all()

# Component validation
gv.validate_entities()
gv.validate_references()
gv.validate_dependencies()
```

#### TaskManager - Task Lifecycle (New)
```python
from src import TaskManager

tm = TaskManager(gm, em, dm, gv)

# Create
tm.create_task("feature:auth", "login-endpoint",
               description="Implement login", task_type="task")

# Update status
tm.update_task_status("task:login-endpoint", "in-progress")

# Query
tasks = tm.get_tasks_for_feature("feature:auth")
blocked = tm.get_blocked_tasks()
```

#### BeadsBridge - External Integration (New)
```python
from src import BeadsBridge

bb = BeadsBridge(gm, em, dm)

# Push to external system
bb.push_tasks("feature:auth")
bb.push_feature_status("feature:auth", "in-progress")

# Pull from external system
success, updates = bb.pull_updates()

# Validate connection
bb.validate_connection()
```

#### TaskSync - Synchronization (New)
```python
from src import TaskSync
from src.task_sync import SyncStrategy

ts = TaskSync(gm, tm, bb, gv)

# Two-way sync
success, summary = ts.sync_all(strategy=SyncStrategy.MERGE)

# Detect conflicts
conflicts = ts.detect_conflicts()

# Resolve conflicts
ts.resolve_conflicts(conflicts, strategy=SyncStrategy.GRAPH_SOURCE)
```

## Testing Quick Reference

### Run All Tests
```bash
cd /workspace/know-cli/know
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_graph.py -v
pytest tests/test_entities.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Test New Module
```python
# tests/test_task_manager.py
import pytest
from src import GraphManager, EntityManager, DependencyManager, GraphValidator, TaskManager
import tempfile
import json
from pathlib import Path

@pytest.fixture
def setup():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        graph = {
            "meta": {},
            "entities": {"feature": {"auth": {"name": "Auth", "description": "Auth"}}},
            "references": {},
            "graph": {}
        }
        json.dump(graph, f)
        temp_file = Path(f.name)

    gm = GraphManager(str(temp_file))
    em = EntityManager(gm)
    dm = DependencyManager(gm)
    gv = GraphValidator(gm)
    tm = TaskManager(gm, em, dm, gv)

    return tm

def test_create_task(setup):
    tm = setup
    success, error = tm.create_task("feature:auth", "test", "desc")
    assert success
```

## Configuration Files

### dependency-rules.json
Location: `know/config/dependency-rules.json`
Defines: Valid entity types and allowed dependencies for spec graph

```json
{
  "entity_description": {
    "user": "End user",
    "feature": "Product feature",
    "component": "Implementation component",
    // ...
  },
  "allowed_dependencies": {
    "feature": ["user", "feature"],
    "action": ["component", "action"],
    // ...
  }
}
```

### code-dependency-rules.json
Location: `know/config/code-dependency-rules.json`
Defines: Valid types and dependencies for code graph

```json
{
  "entity_description": {
    "module": "Code module",
    "package": "Package/namespace",
    "function": "Function/method",
    // ...
  }
}
```

### llm-providers.json
Location: `know/config/llm-providers.json`
Defines: LLM provider configurations

### llm-workflows.json
Location: `know/config/llm-workflows.json`
Defines: LLM workflow templates

## CLI Commands Reference

### Entity Commands
```bash
know list                          # List all entities
know list-type user               # List specific type
know add feature auth ...         # Add entity
know remove user:viewer           # Remove entity
know update feature:auth ...      # Update entity
```

### Dependency Commands
```bash
know link feature:auth user:admin             # Add dependency
know unlink feature:auth user:admin           # Remove dependency
know uses feature:auth                        # Show dependencies
know used-by user:admin                       # Show dependents
```

### Validation Commands
```bash
know validate                      # Full validation
know cycles                        # Detect cycles
know gaps                          # Analyze coverage
```

### Generation Commands
```bash
know review feature auth          # Review with LLM
know plan feature auth            # Generate plan
know build feature auth           # Build spec
```

### Analysis Commands
```bash
know stats                         # Graph statistics
know coverage                      # Coverage analysis
know diff                          # Show changes
```

## Common Patterns

### Adding a New Entity Type

1. Update config: `know/config/dependency-rules.json`
2. Add to `entity_description`
3. Add to `allowed_dependencies`
4. Create via CLI: `know add typename name '{"name":"...","description":"..."}'`
5. Validate: `know validate`

### Creating a Dependency

```bash
know link feature:child feature:parent
```

Equivalent code:
```python
from src import DependencyManager
dm = DependencyManager(graph_manager)
dm.add_dependency("feature:child", "feature:parent")
```

### Validating the Graph

```bash
know validate
```

Equivalent code:
```python
from src import GraphValidator
gv = GraphValidator(graph_manager)
is_valid, results = gv.validate_all()
```

## Error Handling Pattern

All operations return `(success: bool, error_message: Optional[str])`

```python
success, error = manager.operation(args)

if success:
    print("Operation succeeded")
else:
    print(f"Error: {error}")
```

## Import Patterns

### In CLI Commands
```python
from src import (
    GraphManager, EntityManager, DependencyManager,
    GraphValidator, SpecGenerator, LLMManager
)
```

### In Tests
```python
from src import GraphManager, EntityManager
import tempfile
import pytest
```

### In New Modules
```python
from .graph import GraphManager
from .entities import EntityManager
from .dependencies import DependencyManager
from typing import Dict, List, Optional, Tuple, Any
```

## Entity ID Format

All entities use `type:name` format:
- `user:admin` - Admin user
- `feature:auth` - Auth feature
- `component:login-form` - Login form component
- `action:submit-login` - Submit login action

Name conventions:
- Use kebab-case (lowercase with dashes)
- No spaces, underscores, or special characters
- No leading/trailing dashes

## Graph Structure

```json
{
  "meta": {
    "version": "1.0.0",
    "phases": {}
  },
  "references": {
    "external-dep": {
      "library-name": {value}
    }
  },
  "entities": {
    "user": {
      "admin": {name, description, ...}
    },
    "feature": {
      "auth": {name, description, ...}
    }
  },
  "graph": {
    "feature:auth": {
      "depends_on": ["user:admin", "component:login"]
    }
  }
}
```

## Quick Troubleshooting

### Graph Won't Load
```bash
know validate        # Check for JSON errors
```

### Circular Dependencies Detected
```bash
know cycles          # See which entities have cycles
```

### Entity Not Found
```bash
know list-type TYPE  # List all entities of that type
```

### Permission Denied
```bash
# Make sure graph file is writable
chmod 644 .ai/spec-graph.json
```

### Import Errors
```bash
# Make sure src/ is in Python path
cd /workspace/know-cli/know
python3 -c "from src import GraphManager"
```

## File Locations Cheat Sheet

| What | Where |
|------|-------|
| Main CLI | `know/know.py` |
| Core modules | `know/src/` |
| Tests | `tests/` |
| Configs | `know/config/` |
| Templates | `know/templates/` |
| Graph file | `.ai/spec-graph.json` |
| Code graph | `.ai/code-graph.json` |
| Requirements | `know/requirements.txt` |

## Performance Tips

1. **Cache**: GraphManager caches graph in memory, reloads if file changes
2. **Async**: Use AsyncGraphManager for concurrent operations
3. **Batch**: Group operations to minimize saves
4. **Validation**: Validate once after batch operations, not individually

## Type Hints Cheat Sheet

```python
from typing import Dict, List, Optional, Tuple, Any, Set

# Return tuples
def operation() -> Tuple[bool, Optional[str]]: pass

# Optional parameters
def func(arg: Optional[str] = None) -> Dict[str, Any]: pass

# Collections
entities: List[str]
entity_data: Dict[str, Any]
graph: Dict[str, Dict]
```

## Python Version

- Minimum: Python 3.10
- Tested with: Python 3.13
- Key features used: Type hints, f-strings, async/await

## Dependencies to Know

```
click          → CLI framework
networkx       → Graph algorithms
pydantic       → Data validation
rich           → Terminal output
aiofiles       → Async I/O
pytest         → Testing
```

## Useful NetworkX Operations

```python
import networkx as nx

graph = nx.DiGraph()
graph.add_edge("from", "to")

# Traversal
nx.ancestors(graph, "node")      # All dependencies
nx.descendants(graph, "node")    # All dependents
nx.topological_sort(graph)       # Build order
nx.simple_cycles(graph)          # Cycles

# Analysis
nx.shortest_path(graph, "a", "b")  # Path between nodes
```

## Common Validation Checks

```python
# Entity exists
gm.get_entities().get("user", {}).get("admin") is not None

# Dependency is valid
dm.is_valid_dependency("feature", "user")

# Graph is acyclic
len(dm.detect_cycles()) == 0

# All nodes are in entities/references
nodes_in_entities = all(node in all_entities for node in graph)
```
