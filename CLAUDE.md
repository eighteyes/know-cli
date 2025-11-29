<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->


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
meta.phases - ONLY location for planning / temporal information
references - terminal graph nodes, flexible schema (external-dep, product-component, etc.)
entities - fundamental graph nodes, fixed schema per graph type
graph - unidirectional graph, ONLY depends_on links
```

Every entity MUST have a reference or another entity as dependent. Any reference can be depended upon by an entity.

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

Know Tool: `./know/know`

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