# Property-Based Testing Oracle

This directory contains **property-based tests** using [Hypothesis](https://hypothesis.readthedocs.io/) to validate the `know` CLI tool's graph validation logic.

## What is Property-Based Testing?

Unlike traditional example-based testing (where you write specific test cases), property-based testing defines **invariants** - things that must ALWAYS be true - and lets the testing framework generate thousands of test cases automatically.

### Example

**Traditional test:**
```python
def test_user_depends_on_objective():
    graph = {"user:dev": {"depends_on": ["objective:goal"]}}
    assert validate(graph) == True
```

**Property-based test:**
```python
@given(spec_graph=valid_spec_graph())
def test_valid_graphs_always_pass(spec_graph):
    # Hypothesis generates 100+ different valid graphs
    assert validate(spec_graph) == True
```

The second approach finds edge cases you didn't think of.

## The Oracle's Purpose

The Oracle serves three purposes:

1. **Validation Testing**: Ensures the `know validate` command correctly accepts valid graphs and rejects invalid ones
2. **Invariant Documentation**: Codifies the rules that define valid graphs as executable tests
3. **Regression Detection**: Automatically finds cases that break when you change validation logic

## Key Concepts

### The Golden Thread

The **Golden Thread** is the core requirement for a complete specification system:

```
USER (who wants something)
  ↓
OBJECTIVE (what they want)
  ↓
ACTION (how to achieve it)
  ↓
COMPONENT (the thing that does it)
  ↓ [DIMENSIONAL BRIDGE]
  ↓
MODULE (the code that implements it)
```

A valid system MUST have at least one complete thread from user intent (spec-graph) to implementation (code-graph).

### Graph Strategies

Located in `strategies.py`, these generate graphs for testing:

**Spec Graph Strategies:**
- `minimal_spec_graph()` - Minimal valid graph with Golden Thread
- `valid_spec_graph()` - Larger valid graphs with guaranteed Golden Thread
- `broken_golden_thread_graph()` - Invalid graphs with broken user→component chains

**Code Graph Strategies:**
- `minimal_code_graph()` - Minimal valid code graph
- `valid_code_graph()` - Larger valid code architecture graphs

**Cross-Graph Strategies:**
- `linked_graphs()` - Spec + Code graphs with product-component links
- `unlinked_graphs()` - Valid graphs with NO connection (violates Golden Thread)
- `broken_link_graphs()` - Graphs where links point to non-existent components

## Test Files

### `test_invariants.py`

Tests single-graph properties:

- ✅ Valid spec graphs always pass validation
- ✅ Valid code graphs always pass validation
- ✅ All entities have required fields (name, description)
- ✅ Graph section only contains `depends_on` relationships
- ✅ Dependencies point to entities that exist
- ✅ Dependencies follow `allowed_dependencies` rules
- ⚠️  Broken Golden Thread graphs should be detectable

### `test_golden_thread.py`

Tests cross-graph properties:

- ✅ Linked graphs have at least one Golden Thread
- ✅ Unlinked graphs have zero Golden Threads
- ✅ Broken links don't create valid threads
- ✅ product-component refs point to existing components
- ✅ Golden Thread preserves user→objective→action→component sequence
- 📊 Documents reachability analysis

## Running the Tests

### Run all property tests
```bash
venv/bin/pytest tests/property/ -v
```

### Run with more examples (slower, more thorough)
```bash
venv/bin/pytest tests/property/ -v --hypothesis-show-statistics
```

### Run specific test file
```bash
venv/bin/pytest tests/property/test_invariants.py -v
```

### Run single test
```bash
venv/bin/pytest tests/property/test_golden_thread.py::test_linked_graphs_have_at_least_one_golden_thread -v
```

### See Hypothesis shrinking in action

Uncomment the assertion in `test_hypothesis_shrinks_to_minimal_example` in `test_invariants.py`, then run:

```bash
venv/bin/pytest tests/property/test_invariants.py::test_hypothesis_shrinks_to_minimal_example -v
```

You'll see Hypothesis take a large failing graph and shrink it to the MINIMAL example that still fails.

## Configuration

Tests use these Hypothesis settings:

- `max_examples=50` - Run 50 test cases per property (increase for more thorough testing)
- `suppress_health_check=[HealthCheck.too_slow]` - Allow slower tests involving subprocess calls

You can override these via pytest args:
```bash
pytest tests/property/ --hypothesis-seed=12345  # Reproducible test run
pytest tests/property/ -v --hypothesis-verbosity=verbose  # See what's generated
```

## Integration with Fuzzer

The property tests **complement** the fuzzer (`tests/fuzz/`):

| Tool | Purpose | Approach |
|------|---------|----------|
| **Fuzzer** | Find specific failure modes | Hand-crafted malicious graphs |
| **Oracle** | Verify invariants hold | Auto-generated graphs from rules |

**Workflow:**
1. Fuzzer finds a bug → Add it as a regression test
2. Oracle finds an edge case → Investigate if it's a real bug
3. Fix validator → Both fuzzer and oracle verify fix

## Writing New Property Tests

### 1. Define the invariant

What must ALWAYS be true?

Example: "All dependencies must point to entities that exist"

### 2. Choose a strategy

Which graph generator matches your test?

```python
from .strategies import valid_spec_graph, broken_golden_thread_graph
```

### 3. Write the test

```python
from hypothesis import given

@given(spec_graph=valid_spec_graph())
def test_your_invariant(spec_graph):
    # Your assertion here
    assert some_property_holds(spec_graph)
```

### 4. Run it

```bash
venv/bin/pytest tests/property/test_invariants.py::test_your_invariant -v
```

## Example: Finding Unknown Edge Cases

Let's say you add a new entity type `interface` to the spec graph. You update the rules:

```json
{
  "allowed_dependencies": {
    "requirement": ["interface", "component"],
    ...
  }
}
```

Now run the oracle:

```bash
venv/bin/pytest tests/property/ -v
```

**Hypothesis will automatically:**
- Generate graphs with `interface` entities
- Test that they validate correctly
- Find edge cases like circular `interface` dependencies
- Shrink failures to minimal examples

You didn't write a single new test - the oracle adapts to your rules.

## Understanding Test Output

### ✅ All tests pass
Your validator correctly handles all generated cases. Confidence: HIGH.

### ❌ Test fails with large graph
Hypothesis will shrink it:
```
Falsifying example:
spec_graph={'entities': {'user': {'user:a': {...}}}, ...}
```

This is the MINIMAL failing case. Debug this.

### ⚠️  Test marked as "informational"
Some tests document behavior without asserting:
```python
# This test documents that orphans CAN exist
# No assertion - informational
```

These help understand graph properties without enforcing strict rules.

## Advanced: Custom Strategies

Want to test a specific graph pattern?

```python
from hypothesis import strategies as st
from .strategies import entity_key, entity_value

@st.composite
def graph_with_circular_deps(draw):
    # Create a graph with A→B→C→A
    ...
```

See `strategies.py` for examples.

## Gotchas

1. **Slow tests**: Subprocess calls to `know validate` are slow. Use `suppress_health_check=[HealthCheck.too_slow]`

2. **Non-deterministic failures**: If a test fails once but not again, use `--hypothesis-seed` to reproduce:
   ```bash
   pytest --hypothesis-seed=12345
   ```

3. **Shrinking takes time**: When Hypothesis finds a failure, it tries to shrink it. This can take a few seconds. Be patient.

4. **Database persistence**: Hypothesis saves examples in `.hypothesis/`. Commit this to git to share findings.

## Resources

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Intro](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Strategies Guide](https://hypothesis.readthedocs.io/en/latest/data.html)

## Next Steps

1. **Add more invariants**: What other properties MUST hold for valid graphs?
2. **Test mutation operators**: Can you generate invalid graphs by mutating valid ones?
3. **Cross-graph validation**: Write validators that check both graphs together
4. **Performance properties**: Test that validation completes in reasonable time for large graphs

The Oracle grows with your system. Feed it new rules, and it finds new bugs.
