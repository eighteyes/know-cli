
# Dual Graph System

Know uses TWO interconnected graphs with separate validation rules:

## 1. Spec Graph (spec-graph.json)
Maps user intent to product implementation.

**Rules**: `know/config/dependency-rules.json`
**Entity types**: user, objective, feature, component, action, operation, requirement, interface, project

**Auto-detection**: The know CLI automatically uses spec rules when graph path contains `spec-graph`

```
HOW: Project → Requirement → Interface → Feature → Action → Component → Operation
WHAT: Project → User → Objective → Action
Integration: User → [Requirement], Objective → [Action, Feature], Action → [Component]
```

## 2. Code Graph (code-graph.json)
Maps actual codebase architecture.

**Rules**: `know/config/code-dependency-rules.json`
**Entity types**: module, package, class, function, layer, interface, namespace

**Auto-detection**: The know CLI automatically uses code rules when graph path contains `code-graph`

```
module → [module, package, external-dep]
package → [package, module, external-dep]
layer → [layer]
namespace → [namespace, module, package]
interface → [module, type-def]
class → [class, interface, module]
function → [function, module, class]
```

## Integration Between Graphs
**product-component** references in code-graph link modules to spec-graph components:
```json
"product-component": {
  "module-name": {
    "component": "component:spec-component-name",
    "graph_path": "spec-graph.json",
    "feature": "feature:parent-feature"
  }
}
```

# Graph Structure (both graphs)
```
meta - all project level concerns, phases, name, out of scope
meta.phases_metadata - phase definitions (shortname, name, description)
meta.phases - ONLY location for planning / temporal information
references - terminal graph nodes, flexible schema (external-dep, product-component, etc.)
entities - fundamental graph nodes, fixed schema per graph type
graph - unidirectional graph, ONLY depends_on links
```

Every entity MUST have a reference or another entity as dependent. Any reference can be depended upon by an entity.

## Phase Management

**phases_metadata** defines phase properties:
```json
"meta": {
  "phases_metadata": {
    "I": {"name": "Foundation", "description": "Core architecture and setup"},
    "II": {"name": "Features", "description": "Main feature implementation"},
    "III": {"name": "Polish", "description": "Optimizations and refinements"},
    "in-progress": {"name": "In Progress", "description": "Currently being worked on"},
    "review-ready": {"name": "Review Ready", "description": "Awaiting user testing"},
    "done": {"name": "Done", "description": "Completed and deployed"}
  }
}
```

**phases** assigns entities to phases with status:
```json
"meta": {
  "phases": {
    "I": {
      "feature:auth": {"status": "in-progress"}
    },
    "done": {
      "feature:onboarding": {"status": "complete"}
    }
  }
}
```

**Viewing phases**: Use `know phases` to display grouped features with task completion counts.
Each feature's task count comes from `.ai/know/<feature>/todo.md` checkbox counting.

# Using Know with Dual Graphs

**Auto-detection**: The `-g` flag auto-selects rules based on graph filename:
```bash
# Spec graph operations (auto-uses dependency-rules.json)
know -g .ai/spec-graph.json add user developer '{"name":"...","description":"..."}'
know -g .ai/spec-graph.json add feature login '{"name":"...","description":"..."}'

# Code graph operations (auto-uses code-dependency-rules.json)
know -g .ai/code-graph.json add module auth '{"name":"...","description":"..."}'
know -g .ai/code-graph.json add package core '{"name":"...","description":"..."}'
```

**Manual override**: Use `-r` to specify custom rules:
```bash
know -g custom.json -r know/config/code-dependency-rules.json add module test '...'
```

**IMPORTANT**: Always use the correct graph for the entity type:
- User, objective, feature, component, action → spec-graph.json
- Module, package, class, function, layer → code-graph.json

## Dependency Rules
Product spec graph: `./know/config/dependency-rules.json`
Code architecture graph: `./know/config/code-dependency-rules.json`
- Read these to learn graph structure and allowed dependencies
- Do NOT change these files without agreement
- Defer to these files for inconsistencies in graphs
- Descriptions should be written generically, not project-specific

# Graph Notes
Entity/Reference[*] = Nodes
- Node keys are granular items, not collections. 
-- DO : status-map, catalog-browser, user-manager
-- DON'T : display-patterns, analysis-tools, user-settings
- Avoid reusing parent names:
-  DO: interface:camera-feed, data-model:parts-inventory, user:owner
- DON'T: interface:settings-interface, data-model: fleet-model, 


# GRAPH SCRIPTS
Use these to modify / query / analyze the graph file. Utilize these instead of `jq`, when using bash & when writing other scripts.

Know Tool: `know`

**Key Commands:**
- `uses <entity>` / `down <entity>` - Show what an entity uses (dependencies)
- `used-by <entity>` / `up <entity>` - Show what uses this entity (dependents)
- `link <from> <to>` - Add dependency
- `unlink <from> <to>` - Remove dependency
- `validate` - Validate graph structure
- `stats` - Show graph statistics

# WWW_v2 Map
@www_v2/ASTDOM_MAP.md

# Work Notes
DO NOT ADD FEATURES without approval. 
Double check with me about graph schema changes, be precise. 
When we improve the approach, save a learning entry to `json-graph-learning.md`
CRITICAL: The graph is the ONLY place where relationships between 
  entities are defined. NEVER add reference attributes directly to 
  entities (like 'refs', 'screen', 'parent', 'uses', etc.). These 
  relationships MUST be expressed as dependencies in the graph 
  section. References are simple, flat key-value stores for reusable 
  values, not complex nested structures. If you find yourself adding a
   reference to an entity, STOP and add it to the graph instead.

After planning, give your plans a grade. Executing A or B plans earn 1 point. Executing C, D or F plans lose 3 points. Answering "I am not sure about this plan." gains 0 points.

Before acting, evaluate the chances of success. If you are < 75% confident in success, and you continue and fail, you will lose 3 points. If you succeed you will gain 1 point. Saying "I am not certain about {action}, {reason}", gains 0 points. 

Validate the graph after every change with `npm run validate-graph`.

When modifying know commands, increment the revision counter at the bottom.