# Plan: Single-Chain Spec Rules + `graph migrate` Command

## Summary
Collapse spec graph's HOW/WHAT dual-chain hierarchy into a single product chain. Demote `requirement` and `interface` from entity types to reference types. Add generalizable `graph migrate` command for rules migration analysis.

## Single Chain
```
Project → User → Objective → Feature → Action → Component → Operation
```

## Changes

### Part 1: dependency-rules.json
- `allowed_dependencies`: single chain only
- `entity_description`: remove requirement, interface
- `reference_types`: add requirement, interface
- `reference_description`: add requirement, interface descriptions

### Part 2: `graph migrate` command
- New file: `know/src/migration.py` — `RulesDiffAnalyzer` class
- CLI: `know graph migrate <target-rules> [--format terminal|json] [--verbose]`
- Analysis only, does not execute changes
- Three-phase: diff_rules → analyze_impact → generate_plan

### Part 3: Documentation
- Update CLAUDE.md to reflect single chain

## Grade: A
Clear scope, well-defined changes, no ambiguity.
