# Codebase Exploration: Beads Integration

## Summary

Three parallel exploration agents analyzed the know-cli codebase to understand:
1. Overall architecture and CLI patterns
2. Integration patterns and external dependencies
3. Module structure and component boundaries

## Key Findings

### 1. CLI Architecture (Click Framework)

**Entry Point Pattern:**
- Single `@click.group()` with context object storing managers
- Managers initialized once at startup via dependency injection
- Commands access managers through `ctx.obj`

**Command Structure:**
```python
@click.group()
@click.pass_context
def cli(ctx, graph_path, rules_path):
    ctx.obj = {
        'graph': GraphManager(graph_path),
        'entities': EntityManager(...),
        'deps': DependencyManager(...),
        'validator': GraphValidator(...),
        'llm': LLMManager(...)
    }
```

**Command Groups Pattern:**
- Subgroups like `phases` and `rules` use `@cli.group()` decorator
- Example: `know phases list`, `know rules describe`

### 2. Module Architecture

**Core Modules** (`know/src/`):
```
graph.py (165 lines)          → GraphManager: Core I/O & NetworkX integration
cache.py (124 lines)          → GraphCache: Thread-safe caching
entities.py (262 lines)       → EntityManager: CRUD operations
dependencies.py (375 lines)   → DependencyManager: Dependency validation
validation.py (512 lines)     → GraphValidator: Schema validation
llm.py (562 lines)            → LLMManager: Multi-provider integration
```

**Manager Pattern:**
- Each subsystem has a Manager class
- Dependency injection via __init__
- Returns `(bool, Optional[str])` for operations

### 3. External Integration Patterns

**LLM Integration Example** (Configuration-Driven):
- `know/config/llm-providers.json` - Provider definitions
- `know/config/llm-workflows.json` - Workflow templates
- `LLMManager` class orchestrates providers
- Template substitution for dynamic content

**Pattern for Beads Integration:**
```python
class BeadsBridge:
    def __init__(self, graph_manager, entity_manager, dep_manager):
        self.graph = graph_manager
        self.entities = entity_manager
        self.deps = dep_manager

    def init_beads(self, path: str) -> bool:
        # Setup .ai/beads/, create symlink
        pass

    def call_bd(self, args: List[str]) -> Dict:
        # Execute bd command, parse output
        pass
```

### 4. Reference Storage Pattern

**Current Usage:**
```json
{
  "references": {
    "external-dep": {
      "click": {
        "identifier": "pypi:click",
        "version": ">=8.0",
        "type": "pypi",
        "purpose": "CLI framework"
      }
    },
    "product-component": {
      "know-cli": {
        "component": "component:cli-commands",
        "graph_path": "spec-graph.json",
        "feature": "feature:cli-operations"
      }
    }
  }
}
```

**For Beads Tasks:**
```json
{
  "references": {
    "beads": {
      "bd-a1b2": {
        "title": "Implement JWT validation",
        "feature": "feature:auth",
        "status": "in-progress",
        "created": "2025-12-19T10:00:00Z"
      }
    }
  }
}
```

### 5. JSONL Usage

**Current Status:** Not used in codebase yet

**Potential Pattern:**
- Append-only task logs in `.ai/tasks/tasks.jsonl`
- Each line = independent JSON object
- Enables streaming/incremental reads
- Better git diffs than nested JSON

### 6. Subprocess Pattern

**Current Status:** No subprocess usage found

**For Beads Integration:**
```python
import subprocess
import json

def call_bd(command: List[str]) -> Dict:
    """Execute bd command and return parsed output"""
    result = subprocess.run(
        ['bd'] + command,
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode == 0:
        return {'success': True, 'output': result.stdout}
    else:
        return {'success': False, 'error': result.stderr}
```

### 7. File Paths for New Modules

**Recommended Placement:**
```
know/src/
├── beads_bridge.py          # External Beads integration
├── task_manager.py          # Native task management
└── task_sync.py             # Bidirectional sync

tests/
├── test_beads_bridge.py
├── test_task_manager.py
└── test_task_sync.py
```

**Must Update:**
- `know/src/__init__.py` - Add exports
- `know/know.py` - Add CLI commands and manager initialization
- `tests/` - Add comprehensive test coverage

### 8. Testing Patterns

**Fixture-Based:**
```python
@pytest.fixture
def temp_graph_setup():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(test_graph_data, f)
        temp_file = Path(f.name)

    gm = GraphManager(str(temp_file))
    em = EntityManager(gm)
    return em, temp_file
```

**Test Categories:**
- Unit tests: `tests/test_*.py`
- Property tests: `tests/property/`
- Fuzzing: `tests/fuzz/`
- Integration: CLI command tests

### 9. Configuration Pattern

**JSON-Based Config:**
- Location: `know/config/`
- Loaded at manager init
- Template substitution for dynamic values
- Auto-detection based on graph filename

**For Beads:**
```json
{
  "beads": {
    "executable": "bd",
    "default_path": ".ai/beads",
    "sync_interval": 300,
    "auto_link_features": true
  }
}
```

### 10. CLI Command Mapping

**CRUD Commands** → `EntityManager`
- add, remove, update, list, list-type

**Dependency Commands** → `DependencyManager`
- link, unlink, uses, used-by, up, down

**Validation Commands** → `GraphValidator`
- validate, cycles, health

**Generation Commands** → `SpecGenerator` + `LLMManager`
- review, spec, feature-spec

**For Beads Commands:**
```python
@cli.group(name='bd')
@click.pass_context
def bd_commands(ctx):
    """Beads integration commands"""
    pass

@bd_commands.command()
@click.option('--path', default='.ai/beads')
@click.pass_context
def init(ctx, path):
    """Initialize Beads integration"""
    bridge = ctx.obj['beads_bridge']
    success = bridge.init_beads(path)
    console.print(f"✓ Initialized Beads at {path}" if success else "✗ Failed")
```

## Architectural Insights

### Strengths
1. **Clean separation** via Manager pattern
2. **Dependency injection** prevents tight coupling
3. **Configuration-driven** enables extensibility
4. **Comprehensive testing** with multiple strategies
5. **Type hints** throughout codebase

### Integration Points for Beads
1. **Manager layer**: Add BeadsBridge, TaskManager, TaskSync
2. **CLI layer**: Add `bd` command group
3. **Reference layer**: Add `beads` reference type
4. **Config layer**: Add `beads-config.json`
5. **Test layer**: Add test fixtures for Beads operations

### Recommended Approach
1. Follow existing Manager pattern
2. Use dependency injection
3. Store tasks as references in spec-graph
4. Add CLI commands as subgroup
5. Implement comprehensive tests
6. Use subprocess for `bd` commands
7. Implement JSONL for native task system

## Next Steps

1. **Phase 2: Clarify** - Ask user about:
   - Error handling strategies
   - Conflict resolution preferences
   - Security considerations
   - Auto-sync behavior

2. **Phase 3: Architect** - Design:
   - Exact class interfaces
   - Data flow diagrams
   - Error handling patterns
   - Trade-off analysis

3. **Phase 4: Implement** - Build:
   - BeadsBridge with subprocess calls
   - TaskManager with JSONL storage
   - TaskSync with bidirectional logic
   - CLI commands for `know bd` and `know task`

---

**Files Analyzed**: 50+ Python files, 10+ config files, test suite
**Lines Reviewed**: ~4,000 lines of core code
**Patterns Identified**: 10 key architectural patterns
