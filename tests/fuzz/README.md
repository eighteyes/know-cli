# Know CLI Fuzzing Harness

A comprehensive fuzzing suite for stress-testing the `know` CLI tool's graph validation system.

## Overview

The fuzzing harness generates malformed, edge-case, and rule-violating graphs to test the robustness of the know tool's validation logic. It produces **intentionally broken** test cases across multiple categories to find bugs, validation gaps, and edge cases.

## Architecture

```
tests/fuzz/
├── generator.py          # Main fuzzing generator with mutation classes
├── run_fuzz.py          # Campaign runner and reporting engine
├── corpus/              # Generated test graphs (auto-populated)
│   ├── spec/           # Malformed spec-graphs
│   ├── code/           # Malformed code-graphs
│   └── cross/          # Cross-graph validation issues
├── crashes/            # Graphs that cause crashes (auto-populated)
└── README.md           # This file
```

## Key Concepts

### The Golden Thread

The most critical validation in a dual-graph system is the **"Golden Thread"** - a complete chain from spec-graph to code-graph:

```
spec-graph:  user → objective → action → feature → component
                                                        ↓
code-graph:  module ← product-component reference
```

A valid system requires:
1. At least one complete `user → component` chain in spec-graph
2. That component has a corresponding `product-component` reference in code-graph
3. That reference points to a real module in code-graph
4. The module can implement the component's functionality

### Graph Types

**Spec Graph (spec-graph.json)**
- Represents product intent and architecture
- Entity types: user, objective, action, feature, component, operation
- Dependency rules prevent invalid chains (e.g., component can't depend on user)
- References: Technical details, acceptance criteria, business logic, etc.

**Code Graph (code-graph.json)**
- Represents actual codebase architecture
- Entity types: module, package, layer, class, function, interface, namespace
- Dependency rules enforce clean architecture (no upward dependencies, no cycles)
- References: Source files, external deps, product-component mappings, etc.

**Cross-Graph Integration**
- Via `product-component` references in code-graph
- Links implementation (modules) to specification (components)
- Validates that everything in the spec has a corresponding implementation

## Mutation Categories

### 1. Structural Mutations

Tests for missing or malformed top-level sections:

- `generate_empty_graph()` - Completely empty JSON
- `generate_missing_meta()` - No `meta` section
- `generate_missing_entities()` - No `entities` section
- `generate_missing_references()` - No `references` section
- `generate_missing_graph()` - No `graph` section
- `generate_non_dict_entities()` - `entities` is list instead of dict
- `generate_non_dict_references()` - `references` is list instead of dict
- `generate_non_dict_graph()` - `graph` is list instead of dict
- `generate_massive_graph()` - 1000+ entities to test performance

### 2. Unicode & Special Characters

Tests for handling non-ASCII input:

- `generate_unicode_emoji_names()` - Entities with emoji and Unicode
- `generate_special_characters_names()` - Quotes, newlines, tabs, backslashes in names

### 3. Spec-Graph Rule Violations

Tests for invalid dependency chains in the spec graph:

- `generate_invalid_dependency_direction()` - component→user instead of user→objective
- `generate_circular_dependencies()` - A→B→C→A cycles
- `generate_self_referencing()` - Entity depending on itself
- `generate_orphaned_entities()` - Entities without graph entries
- `generate_reference_to_nonexistent_entity()` - Depends on non-existent entity
- `generate_wrong_entity_types_in_chain()` - Invalid type sequences

### 4. Edge Cases

Tests for boundary conditions:

- `generate_empty_depends_on_array()` - Empty `depends_on: []`
- `generate_null_depends_on()` - `depends_on: null` instead of array
- `generate_missing_depends_on()` - No `depends_on` field at all
- `generate_extremely_long_description()` - 10k+ character descriptions
- `generate_duplicate_entity_keys()` - Duplicate keys (JSON behavior)
- `generate_missing_entity_name()` - Entity without `name` field
- `generate_missing_entity_description()` - Entity without `description` field
- `generate_null_values_in_entity()` - `name: null`, `description: null`
- `generate_invalid_graph_node_id_format()` - Wrong format (missing `:` separator)

### 5. Code-Graph Mutations

Tests for architectural violations in code graphs:

- `generate_upward_layer_dependency()` - Layer N depends on N+1
- `generate_invalid_layer_cycles()` - Circular layer dependencies
- `generate_module_with_invalid_dependency_type()` - Invalid entity types
- `generate_broken_namespace_hierarchy()` - Namespaces without parents
- `generate_orphaned_product_component_reference()` - References non-existent component
- `generate_product_component_with_wrong_graph_path()` - Invalid graph paths

### 6. Naming Convention Violations

Tests for improper naming:

- `generate_underscores_in_names()` - Uses `_` instead of `-`
- `generate_camelcase_names()` - Uses `camelCase` instead of `kebab-case`
- `generate_uppercase_names()` - Uses `UPPERCASE` instead of lowercase

### 7. Cross-Graph Validation Issues (THE INTERESTING STUFF)

These test the **Golden Thread** - the most critical validation:

- `generate_spec_without_code()` - Valid spec-graph but empty code-graph
- `generate_code_without_spec()` - Valid code-graph but empty spec-graph
- `generate_broken_golden_thread()` - Spec has component but code points to wrong one
- `generate_missing_component_in_spec()` - User→objective→action but no component
- `generate_missing_product_component_mapping()` - Code module has no mapping to spec
- `generate_orphaned_code_module()` - Code module with no purpose in spec

## Running the Fuzzer

### Quick Start

```bash
cd tests/fuzz

# Generate corpus and run fuzzing campaign
python run_fuzz.py

# With custom timeout and specific graph types
python run_fuzz.py --timeout 10 --types spec code

# Save detailed report
python run_fuzz.py --report fuzz_report.json
```

### Only Generate Corpus

```bash
python generator.py tests/fuzz

# With seed for reproducibility
python generator.py tests/fuzz 42
```

### Run on Existing Corpus

```bash
python run_fuzz.py --corpus tests/fuzz/corpus --timeout 5
```

## Expected vs Actual Behavior

### Expected Behavior

**Graphs that should FAIL validation:**
- Any mutation marked as "rule violation" or "structural corruption"
- Should exit with non-zero code and print detailed error messages
- Errors should be categorized and actionable

**Graphs that should PASS validation:**
- Currently: None - all generated graphs are intentionally broken
- In the future: Add a `generate_valid_variants()` set for regression testing

**Performance expectations:**
- Each test should complete in <1 second
- 100 tests should complete in <2 minutes total
- Massive graphs (1000+ entities) might take 5-10 seconds

### Actual Behavior (Testing Framework)

The fuzzer captures:
- Exit code (0 = pass, non-zero = fail)
- stdout/stderr output
- Execution duration
- Crash status (segfault, panic, etc.)
- Timeout status (hangs)
- Error categorization

Results are compared to detect:
- **Unexpected passes** - Broken graph validates as correct (false negative)
- **Unexpected failures** - Valid graph fails validation (false positive)
- **Crashes** - Validator crashes instead of graceful error handling
- **Timeouts** - Validator hangs on certain inputs
- **Performance anomalies** - Tests slower than threshold

## Reproducing Specific Failures

Each crash is saved with full details:

```bash
# List all crashes
ls tests/fuzz/crashes/

# View crash details
cat tests/fuzz/crashes/generate_circular_dependencies_crash.crash_report.json

# Reproduce specific test
know -g tests/fuzz/crashes/generate_circular_dependencies.json validate

# Debug with verbose output
know -g tests/fuzz/crashes/generate_circular_dependencies.json validate --verbose
```

## Report Format

The fuzzing campaign generates a comprehensive JSON report:

```json
{
  "timestamp": "2025-11-26T10:30:45Z",
  "total_tests": 45,
  "passed": 0,
  "failed": 45,
  "crashed": 2,
  "timed_out": 1,
  "summary_by_type": {
    "spec": {"passed": 0, "failed": 15, "crashed": 1, "timed_out": 0},
    "code": {"passed": 0, "failed": 12, "crashed": 1, "timed_out": 1},
    "cross": {"passed": 0, "failed": 18, "crashed": 0, "timed_out": 0}
  },
  "error_categories": {
    "validation_failed": 42,
    "crash": 2,
    "timeout": 1
  },
  "slowest_tests": [...],
  "interesting_failures": [...]
}
```

## Golden Thread Validation Deep Dive

The cross-graph fuzzer specifically tests the most critical validation rule:

**Rule:** A valid system must have a complete chain from user intent to code implementation.

**The Chain:**
```
spec-graph:
  user:owner ─→ objective:goal ─→ action:perform ─→ feature:tracking ─→ component:dashboard

code-graph:
  module:dashboard ←─ product-component:dashboard
                      └─ references: component:dashboard in spec-graph.json
```

**Failure Modes Tested:**

1. **Broken at Spec Level**
   - User exists but no objective: ❌ Orphaned user
   - Objective exists but no action: ❌ Dead-end objective
   - Action exists but no feature: ❌ Dead-end action
   - Feature exists but no component: ❌ Dead-end feature

2. **Broken at Cross-Graph Level**
   - Component has no code mapping: ❌ Orphaned component
   - Code module has no spec mapping: ❌ Orphaned implementation
   - Product-component points to wrong component: ❌ Wrong implementation

3. **Broken at Code Level**
   - Module doesn't implement anything: ❌ Orphaned module
   - Module depends on invalid types: ❌ Architectural violation
   - Upward layer dependencies: ❌ Circular architecture

## Adding New Mutations

To add a new mutation:

1. Add method to appropriate fuzzer class:
   ```python
   def generate_my_mutation(self) -> Dict[str, Any]:
       """Description of what mutation tests."""
       return {
           "meta": {...},
           "entities": {...},
           "references": {...},
           "graph": {...}
       }
   ```

2. Method name must start with `generate_`

3. Implement the malformed graph structure

4. Add docstring describing what validation should catch

5. Regenerate corpus: `python generator.py tests/fuzz`

## Integration with CI/CD

Add to GitHub Actions or similar:

```yaml
- name: Run fuzzing campaign
  run: |
    cd tests/fuzz
    python run_fuzz.py --timeout 10 --report fuzz_report.json

- name: Check fuzzing results
  run: |
    python -c "
    import json
    with open('tests/fuzz/fuzz_report.json') as f:
        report = json.load(f)
    crashes = report['crashed'] + report['timed_out']
    if crashes > 0:
        print(f'FAILED: {crashes} crashes/timeouts')
        exit(1)
    print(f'PASSED: {report[\"total_tests\"]} tests')
    "
```

## Known Limitations

1. **JSON Parser Behavior** - Python's JSON parser doesn't handle duplicate keys the way we expect
2. **No Oracle** - Currently all graphs are expected to fail; need valid test set
3. **No Parallelization** - Single-threaded for now; can be parallelized later
4. **Timeout Heuristic** - 5-second default might be too strict or too loose
5. **No State Mutations** - Tests don't check if validator modifies graph

## Next Steps for Oracle Construction

An "oracle" is a ground truth of what the correct behavior should be:

1. **Build Valid Test Set**
   - Create 10-20 "golden" spec-graphs with complete chains
   - Create corresponding code-graphs with proper product-component mappings
   - Verify these pass validation

2. **Create Mutation Regression Suite**
   - Each valid graph → apply single, targeted mutation
   - Document expected error for that mutation
   - Compare actual vs expected errors

3. **Implement Error Matching**
   - Categorize errors by type (structural, semantic, architectural)
   - Match error messages to mutation types
   - Detect when validator gives wrong error for a mutation

4. **Build Differential Testing**
   - Compare against external validators (if available)
   - Compare against previous versions of know
   - Detect behavioral changes

5. **Add Invariant Checking**
   - Validator should never crash
   - Validator should never hang
   - Error messages should be actionable
   - Validation should complete in bounded time

## Files

- **generator.py** - All mutation generators (SpecGraphFuzzer, CodeGraphFuzzer, CrossGraphFuzzer)
- **run_fuzz.py** - Campaign orchestrator and reporting engine
- **corpus/** - Auto-generated test graphs (not in git)
- **crashes/** - Auto-saved crash cases (for debugging)
- **README.md** - This file

## References

- Spec Graph Rules: `/know/config/dependency-rules.json`
- Code Graph Rules: `/know/config/code-dependency-rules.json`
- Validator Implementation: `/know/src/validation.py`
- CLI Tool: `/know/know.py`
