# Plan: Spec Generation Enrichment

## Objective

Enable `know spec feature:<name>` to generate rich, comprehensive specifications by:
1. Keeping entity nodes lightweight (name, description only)
2. Using references for reusable, cross-ref-able content (data-models, signatures, api-schemas)
3. Using `meta.feature_specs.<feature>` for feature-specific prose (use_cases, testing, security, monitoring)
4. Using graph relationships to link components → operations → references

## Architecture

```
Entity (lightweight)          Reference (reusable)           Meta (feature-specific)
├── name                      ├── data-model:fork            ├── feature_specs:
├── description               ├── data-model:fork-result     │   └── ensemble-meshes:
                              ├── api-schema:ensemble-api    │       ├── use_cases[]
Graph (relationships)         ├── signature:execute          │       ├── testing{}
├── feature:x → action:y      ├── signature:aggregate        │       ├── security[]
├── component:x → operation:y                                │       └── monitoring[]
├── operation:x → signature:y
├── component:x → data-model:y
```

## Schema Changes

### 1. New Reference Types (dependency-rules.json)

Add to `reference_types` array:
```json
"api-schema",      // TypeScript interface definitions for public APIs
"signature",       // Function/method signatures with params and returns
"test-spec",       // Reusable test specifications (can cross-ref)
"security-spec"    // Reusable security requirements (can cross-ref)
```

Add to `reference_description`:
```json
"api-schema": "TypeScript interface definitions for public APIs including request/response types",
"signature": "Function or method signature with name, parameters, and return type",
"test-spec": "Reusable test specification that may apply to multiple components",
"security-spec": "Reusable security requirement that may apply to multiple components"
```

### 2. Meta Schema Extension (dependency-rules.json)

Add to `meta_schema`:
```json
"feature_specs": {
  "schema": "OBJECT<FEATURE_NAME:FEATURE_SPEC_OBJECT>",
  "feature_spec_object": {
    "use_cases": "ARRAY<USE_CASE_OBJECT>",
    "testing": "TESTING_OBJECT",
    "security": "ARRAY<STRING>",
    "monitoring": "ARRAY<STRING>",
    "performance": "PERFORMANCE_OBJECT"
  },
  "use_case_object": {
    "name": "STRING - Use case name",
    "description": "STRING - What this use case accomplishes",
    "config": "OBJECT - Example configuration for this use case"
  },
  "testing_object": {
    "unit": "ARRAY<STRING> - Unit test requirements",
    "integration": "ARRAY<STRING> - Integration test requirements",
    "performance": "ARRAY<STRING> - Performance test requirements"
  },
  "performance_object": {
    "latency": "STRING - Expected latency characteristics",
    "cost": "STRING - Cost implications",
    "quality": "STRING - Quality characteristics"
  }
}
```

### 3. Component Entity Extensions

Components can now link to:
- `source-file:<path>` reference (already exists) - file location
- `operation:<name>` entity via graph - what it does

### 4. Operation Entity Extensions

Operations link to:
- `signature:<name>` reference via graph - function signature
- `data-model:<name>` reference via graph - input/output types

## Example Graph Structure (ensemble-meshes)

```json
{
  "entities": {
    "feature": {
      "ensemble-meshes": {
        "name": "Ensemble Meshes",
        "description": "Run multiple agents in parallel and aggregate outputs"
      }
    },
    "component": {
      "ensemble-runner": {
        "name": "Ensemble Runner",
        "description": "Orchestrates fork spawning, parallel execution, and completion handling"
      },
      "ensemble-aggregator": {
        "name": "Ensemble Aggregator",
        "description": "Routes to appropriate strategy and aggregates fork results"
      }
    },
    "operation": {
      "execute-ensemble": {
        "name": "Execute Ensemble",
        "description": "Main entry point for ensemble execution"
      },
      "spawn-forks": {
        "name": "Spawn Forks",
        "description": "Create N parallel forks"
      },
      "aggregate-results": {
        "name": "Aggregate Results",
        "description": "Apply strategy to fork results"
      }
    }
  },
  "references": {
    "source-file": {
      "ensemble-runner": {
        "path": "src/ensemble/runner.ts",
        "module": "ensemble"
      },
      "ensemble-aggregator": {
        "path": "src/ensemble/aggregator.ts",
        "module": "ensemble"
      }
    },
    "signature": {
      "execute": {
        "name": "execute",
        "params": [
          {"name": "task", "type": "Task"},
          {"name": "config", "type": "EnsembleConfig"}
        ],
        "returns": "Promise<AggregatedResult>"
      },
      "spawn-forks": {
        "name": "spawnForks",
        "params": [
          {"name": "task", "type": "Task"},
          {"name": "n", "type": "number"}
        ],
        "returns": "Promise<Fork[]>"
      }
    },
    "data-model": {
      "fork": {
        "name": "Fork",
        "language": "typescript",
        "schema": {
          "id": "string",
          "sessionId": "string",
          "model": "'sonnet' | 'opus' | 'haiku'",
          "status": "'pending' | 'running' | 'complete' | 'failed'"
        }
      },
      "fork-result": {
        "name": "ForkResult",
        "language": "typescript",
        "schema": {
          "forkId": "string",
          "output": "string",
          "model": "string",
          "duration": "number",
          "error": "Error | undefined"
        }
      },
      "ensemble-config": {
        "name": "EnsembleConfig",
        "language": "typescript",
        "schema": {
          "enabled": "boolean",
          "forkCount": "number",
          "strategy": "'vote' | 'synthesize' | 'best_of' | 'consensus' | 'union'",
          "models": "('sonnet' | 'opus' | 'haiku')[] | undefined",
          "aggregatorModel": "'sonnet' | 'opus' | 'haiku'",
          "timeout": "number | undefined"
        }
      }
    },
    "api-schema": {
      "ensemble-api": {
        "name": "Ensemble API",
        "description": "Public API for ensemble execution",
        "methods": [
          {
            "name": "execute",
            "signature": "signature:execute",
            "description": "Main entry point"
          }
        ]
      }
    },
    "business-logic": {
      "ensemble-execution-flow": {
        "name": "Execution Flow",
        "steps": [
          "Dispatcher receives task with ensemble config",
          "Runner spawns N forks in parallel",
          "Each fork calls query() with forkSession: true",
          "Forks execute independently (no cross-talk)",
          "Promise.allSettled waits for all forks",
          "Aggregator applies strategy to results",
          "Single result written back to message queue"
        ]
      },
      "ensemble-error-handling": {
        "name": "Error Handling",
        "rules": [
          "Fork failures don't block ensemble",
          "Timeouts kill slow forks, aggregate completed ones",
          "All forks fail → error message to requester",
          "Aggregator failure → raw fork outputs with error flag"
        ]
      }
    }
  },
  "graph": {
    "feature:ensemble-meshes": {
      "depends_on": [
        "component:ensemble-runner",
        "component:ensemble-aggregator",
        "api-schema:ensemble-api",
        "business-logic:ensemble-execution-flow",
        "business-logic:ensemble-error-handling"
      ]
    },
    "component:ensemble-runner": {
      "depends_on": [
        "operation:execute-ensemble",
        "operation:spawn-forks",
        "source-file:ensemble-runner",
        "data-model:fork",
        "data-model:ensemble-config"
      ]
    },
    "component:ensemble-aggregator": {
      "depends_on": [
        "operation:aggregate-results",
        "source-file:ensemble-aggregator",
        "data-model:fork-result"
      ]
    },
    "operation:execute-ensemble": {
      "depends_on": [
        "signature:execute",
        "data-model:ensemble-config"
      ]
    },
    "operation:spawn-forks": {
      "depends_on": [
        "signature:spawn-forks",
        "data-model:fork"
      ]
    }
  },
  "meta": {
    "feature_specs": {
      "ensemble-meshes": {
        "status": "planned",
        "phase": "Phase 5 (Future)",
        "priority": "P2",
        "use_cases": [
          {
            "name": "Code Review Ensemble",
            "description": "Catch more bugs through multiple reviewers",
            "config": {"forkCount": 3, "strategy": "union"}
          },
          {
            "name": "Research Ensemble",
            "description": "Comprehensive reports through synthesis",
            "config": {"forkCount": 5, "strategy": "synthesize"}
          }
        ],
        "testing": {
          "unit": [
            "Each aggregation strategy tested independently",
            "Fork isolation verified",
            "Error recovery tested",
            "Timeout handling tested"
          ],
          "integration": [
            "End-to-end ensemble execution",
            "Message protocol compatibility",
            "Queue integration"
          ],
          "performance": [
            "Parallel execution confirmed (not sequential)",
            "Load testing with high N values (N=10+)",
            "Latency vs single agent compared"
          ]
        },
        "security": [
          "Fork isolation must prevent cross-contamination",
          "Each fork has independent context",
          "No information leakage between forks"
        ],
        "monitoring": [
          "Log fork spawning events",
          "Track fork completion times",
          "Monitor aggregation strategy performance",
          "Alert on high failure rates"
        ],
        "performance": {
          "latency": "~1× single agent (parallel execution)",
          "cost": "N× single agent + aggregation cost",
          "quality": "Higher through diversity/consensus"
        }
      }
    }
  }
}
```

## Generator Changes (generators.py)

### Enhanced `generate_feature_spec()`

```python
def generate_feature_spec(self, feature_id: str) -> str:
    """Generate comprehensive feature specification."""

    # 1. Header + Description (from entity)
    # 2. Status/Phase/Priority (from meta.feature_specs)
    # 3. Dependencies (from graph - other features)
    # 4. Components (from graph → component entities)
    #    - For each component:
    #      - File (from source-file reference)
    #      - Purpose (from entity description)
    #      - Operations (from graph → operation entities)
    #        - For each operation: signature reference
    # 5. Interfaces (from api-schema references)
    # 6. Data Models (from data-model references, render as TypeScript)
    # 7. Business Logic (from business-logic references)
    # 8. Use Cases (from meta.feature_specs.use_cases)
    # 9. Testing Requirements (from meta.feature_specs.testing)
    # 10. Security & Privacy (from meta.feature_specs.security)
    # 11. Monitoring & Observability (from meta.feature_specs.monitoring)
```

### New Helper Methods

```python
def _render_data_model_typescript(self, model_data: dict) -> str:
    """Render a data-model reference as TypeScript interface."""

def _render_signature(self, sig_data: dict) -> str:
    """Render a signature reference as function signature."""

def _get_feature_spec_meta(self, feature_name: str) -> dict:
    """Get feature-specific meta from meta.feature_specs."""

def _get_component_file(self, component_id: str) -> str:
    """Get source file path from source-file reference."""

def _get_component_operations(self, component_id: str) -> list:
    """Get operations linked to a component via graph."""
```

## Implementation Tasks

1. [ ] Update `dependency-rules.json` with new reference types
2. [ ] Update `dependency-rules.json` with meta.feature_specs schema
3. [ ] Add `api-schema` and `signature` reference type handling
4. [ ] Update `generators.py` with enhanced `generate_feature_spec()`
5. [ ] Add TypeScript rendering helpers
6. [ ] Add meta.feature_specs query methods
7. [ ] Update validation to handle new structures
8. [ ] Test with ensemble-meshes example
9. [ ] Update SKILL.md with new reference types

## Validation Rules

- Components SHOULD have `source-file` reference dependency
- Operations SHOULD have `signature` reference dependency
- Features with complex specs SHOULD have `meta.feature_specs` entry
- `data-model` references MUST have `schema` object
- `signature` references MUST have `params` array and `returns` string

## Migration Path

Existing graphs continue to work. New reference types and meta sections are additive.
Generator gracefully handles missing sections (outputs "Not specified" or omits section).
