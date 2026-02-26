# Task #4 Completion Summary

## ✅ Part A: Code-Graph Generator (Programmatic)

**Created:**
- `know/src/codemap_to_graph.py` - CodeGraphGenerator class
- `know gen code-graph` CLI command

**What It Does:**
Regenerates code-graph entities from codemap AST parsing while preserving manually curated references.

**Usage:**
```bash
# Generate code-graph from codemap
know gen code-graph

# With custom paths
know gen code-graph -c .ai/codemap.json -e .ai/know/code-graph.json -o .ai/code-graph-new.json
```

**Output:**
- 19 modules with file paths
- 22 classes
- 187 functions
- 9 product-component refs (preserved)
- 17 external deps (merged)

**Example Module Entity:**
```json
{
  "generators": {
    "name": "Generators",
    "description": "Module at know/src/generators.py",
    "file_path": "know/src/generators.py"
  }
}
```

## ✅ Part B: XML Enrichment with Code-Graph

**Enhanced `generate_feature_spec_xml()`:**
- Loads code-graph for file path lookups
- Queries product-component refs to map components → modules
- Extracts file paths from module entities
- Gathers external dependencies for components

**New Helper Methods:**
- `_get_file_path_from_code_graph()` - Look up file via product-component
- `_get_external_deps_for_components()` - Extract external deps for components

## ⚠️ Manual Curation Needed

The XML enrichment works, but **product-component mappings need updating** to match actual component names:

**Current Mapping:**
```
generators → component:spec-templates
```

**Needed Mappings for spec-generation-enrichment:**
```
generators → component:spec-generator
generators → component:reference-renderer
generators → component:metadata-accessor
```

**Why:** The components in spec-graph are fine-grained (spec-generator, reference-renderer, metadata-accessor), but they all live in the same `generators.py` module. The product-component refs need to reflect this one-to-many relationship.

**How to Fix:**
Update `.ai/know/code-graph.json`:
```json
{
  "references": {
    "product-component": {
      "generators": {
        "component": "component:spec-generator",
        "graph_path": "spec-graph.json",
        "feature": "feature:spec-generation-enrichment",
        "also_implements": [
          "component:reference-renderer",
          "component:metadata-accessor"
        ]
      }
    }
  }
}
```

Or create multiple entries:
```json
{
  "references": {
    "product-component": {
      "generators.spec-generator": {
        "component": "component:spec-generator",
        "graph_path": "spec-graph.json"
      },
      "generators.reference-renderer": {
        "component": "component:reference-renderer",
        "graph_path": "spec-graph.json"
      },
      "generators.metadata-accessor": {
        "component": "component:metadata-accessor",
        "graph_path": "spec-graph.json"
      }
    }
  }
}
```

## Current XML Output Status

**Working:**
- ✅ Meta section (feature, name, phase, status)
- ✅ Context section (objectives, actions, components)
- ✅ Dependencies section structure
- ✅ Tasks section (operations → tasks)
- ✅ Checkpoint types
- ✅ Code-graph lookup logic

**Still Placeholder:**
- ⚠️ File paths (empty due to missing product-component mappings)
- ⚠️ External deps (empty due to missing mappings)
- ⚠️ Action implementation guidance (still "TODO")
- ⚠️ Verify test commands (still "TODO")

## What's Automated vs Manual

| Aspect | Status | Source |
|--------|--------|--------|
| Module file paths | ✅ Automated | From codemap AST |
| Class/function structure | ✅ Automated | From codemap AST |
| Import dependencies | ✅ Automated | From codemap AST |
| External deps detection | ✅ Automated | From imports |
| **product-component refs** | ❌ **Manual** | Links code → spec |
| External dep purpose | ⚠️ Semi-manual | Auto-detect + manual docs |
| Implementation guidance | ❌ Manual/LLM | Needs domain knowledge |
| Test commands | ❌ Manual/LLM | Needs test strategy |

## Workflow Going Forward

### 1. Generate Code-Graph (Automated)
```bash
# Regenerate code-graph whenever codebase changes
know gen codemap know/src --heat
know gen code-graph
```

### 2. Curate Product-Component Refs (Manual)
```bash
# Edit .ai/know/code-graph.json to map modules to spec components
# This is the bridge between code and product intent
```

### 3. Generate XML Spec (Automated with enrichment)
```bash
# XML now includes file paths and external deps
know gen spec feature:my-feature --format xml > .ai/plans/my-feature.xml
```

### 4. Feed to /know:build (Future Task #3)
```bash
# Build command consumes XML and executes tasks
/know:build .ai/plans/my-feature.xml
```

## Files Created/Modified

**Created:**
- `know/src/codemap_to_graph.py` - Code-graph generator
- `.ai/plan/task4-code-graph-completion-summary.md` - This file
- `.ai/code-graph-new.json` - Generated code-graph with file paths

**Modified:**
- `know/know.py` - Added `gen code-graph` command
- `know/src/generators.py` - Enhanced XML generator with code-graph lookups
- `.ai/know/code-graph.json` - Replaced with new version

## Next Steps

**Task #3: Implement /know:build**
- Parse XML spec
- Chunk into executable tasks
- Execute until checkpoint
- Handle human-verify, decision, human-action checkpoints

**Future Enhancements:**
- LLM-powered implementation guidance in <action> sections
- Auto-generate test commands from operation descriptions
- Wave computation from operation dependency graph
- Code-graph → spec-graph inference (backpressure)
