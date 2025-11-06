# Bug Fix Test Suite

This test suite verifies the fixes for bugs reported on 2025-10-30.

## Bug Fixes Tested

### Bug #1: Entity Type "operation" Not Recognized
**Problem:** `dependency-rules.json` defines "operation" but code had hardcoded entity types
**Fix:** Refactored `EntityManager` to load entity types dynamically from rules
**Tests:**
- `test_operation_recognized()` - Verifies 'operation' is in VALID_ENTITY_TYPES
- `test_all_types_from_rules()` - Verifies ALL entity types match rules file

### Bug #2: Build Order Incorrectly Reports Cycles
**Problem:** `topological_sort()` returned partial results instead of detecting cycles
**Fix:** Added check: if result length != graph length, return empty list
**Tests:**
- `test_build_order_no_cycles()` - Verifies build order works with acyclic graph
- `test_build_order_with_cycles()` - Verifies empty list returned when cycles exist

### Bug #3: Disconnected Subgraphs Treated as Errors
**Problem:** Health check failed for disconnected subgraphs in initial/incremental graphs
**Fix:** Changed to informational message, doesn't cause health check failure
**Tests:**
- `test_disconnected_subgraphs()` - Verifies disconnected graphs don't fail validation

### Bug #4: Custom Metadata Fields Trigger Warnings
**Problem:** Useful fields like 'path', 'status' triggered "unexpected field" warnings
**Fix:** Added `allowed_metadata` to rules, validator loads dynamically
**Tests:**
- `test_metadata_loaded_from_rules()` - Verifies metadata fields loaded from rules
- `test_path_metadata_no_warning()` - Verifies 'path' doesn't trigger warning

## Running the Tests

### Option 1: With pytest (recommended)
```bash
cd know
pip install -r requirements.txt  # Install dependencies
pytest tests/test_bug_fixes.py -v
```

### Option 2: Without pytest (simple runner)
```bash
cd know
pip install -r requirements.txt  # Install dependencies
python3 tests/run_bug_fix_tests.py
```

### Option 3: Manual verification
If dependencies aren't available, you can verify the fixes manually:

```bash
cd know

# Verify rules file defines everything correctly
python3 -c "
import json
with open('config/dependency-rules.json') as f:
    rules = json.load(f)
print('Entity types:', sorted(rules['entity_description'].keys()))
print('operation present:', 'operation' in rules['entity_description'])
print('Allowed metadata:', rules['entity_note']['allowed_metadata'])
"
```

## Test Coverage

The test suite covers:
- ✓ Dynamic entity type loading from dependency-rules.json
- ✓ Topological sort behavior with and without cycles
- ✓ Cycle detection consistency with build order
- ✓ Metadata field validation using rules-based schema
- ✓ Disconnected subgraph detection without validation failure

## Architecture Changes

All fixes follow the principle: **Schema should be defined in `dependency-rules.json`, not hardcoded in Python.**

Before:
```python
# Hardcoded - BAD
VALID_ENTITY_TYPES = {'user', 'feature', 'component', ...}
```

After:
```python
# Loaded from rules - GOOD
def __init__(self, ...):
    with open('config/dependency-rules.json') as f:
        rules = json.load(f)
    self.VALID_ENTITY_TYPES = set(rules['entity_description'].keys())
```

This prevents schema drift between the rules file and implementation.

## Dependencies

Tests require:
- `networkx` - Graph algorithms
- `pytest` - Test framework (optional, can use simple runner)
- `rich` - Console output formatting

Install via:
```bash
pip install -r requirements.txt
```

## Future Work

- Add integration tests with real project graphs
- Test edge cases (empty graphs, malformed dependencies)
- Performance tests for large graphs (1000+ entities)
- Validation error message clarity tests
