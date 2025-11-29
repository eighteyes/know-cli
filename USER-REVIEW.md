# Know CLI - Feature Review

Features completed and awaiting user review.

## Completed Features

### Property-Based Testing Oracle (2025-11-28)
**Status:** ✅ Complete

Added comprehensive property-based testing using Hypothesis to validate graph operations.

**What it does:**
- Generates thousands of test graphs automatically
- Tests invariants like "valid graphs always pass validation"
- Validates the Golden Thread (user→objective→action→component→module)
- Shrinks failures to minimal examples
- Complements the fuzzer with infinite auto-generated test cases

**Location:**
- Tests: `tests/property/`
- Documentation: `tests/property/README.md`
- Fuzzer: `tests/fuzz/`

**Usage:**
```bash
venv/bin/pytest tests/property/ -v
venv/bin/pytest tests/property/ --hypothesis-show-statistics
```

**Test Coverage:**
- 20 property tests
- 600+ graphs tested per run
- Tests both spec-graph and code-graph
- Cross-graph Golden Thread validation

---

### Graph Diff Tool (2025-11-28)
**Status:** ✅ Complete

Added `know diff` command for semantic comparison of graph files.

**What it does:**
- Compares two graph files and shows structured differences
- Shows added/removed/modified entities, dependencies, and references
- Colored terminal output (git-style) or JSON for scripting
- Summary mode (default) or verbose mode with full details

**Location:**
- Implementation: `know/src/diff.py`
- Command: `know/know.py` (diff command)

**Usage:**
```bash
# Summary diff (colored terminal)
know diff graph1.json graph2.json

# Verbose diff with full details
know diff graph1.json graph2.json --verbose

# JSON output for scripting
know diff graph1.json graph2.json --format json
```

**Features:**
- Entity changes (added/removed/modified with name and description)
- Dependency changes (added/removed/modified relationships)
- Reference changes (added/removed)
- Meta changes (version, format, project info)
- Summary counts for quick overview

---

## Pending Review

None currently.

---

## Reviewed & Deployed

None yet.
