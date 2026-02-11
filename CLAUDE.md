
# Graph Model

Know uses two graphs in `.ai/know/`. The `-g` flag defaults to `.ai/know/spec-graph.json` and auto-selects rules based on filename.

## Spec Graph (`.ai/know/spec-graph.json`) — Product Intent

Rules: `know/config/dependency-rules.json`

```
Project → User → Objective → Feature → Action → Component → Operation
```

Entities: project, user, objective, feature, action, component, operation
References include: requirement, interface (demoted from entities), plus data-model, business_logic, etc.

## Code Graph (`.ai/know/code-graph.json`) — Codebase Architecture

Rules: `know/config/code-dependency-rules.json`

```
module → [module, package, external-dep]    class → [class, interface, module]
package → [package, module, external-dep]   function → [function, module, class]
layer → [layer]                             namespace → [namespace, module, package]
```

## Graph Structure (both graphs)

```
meta        — project concerns, phases, name, out of scope
references  — terminal nodes, flexible schema
entities    — fundamental nodes, fixed schema per graph type
graph       — unidirectional, ONLY depends_on links
```

Every entity MUST have a reference or another entity as dependent.

Graphs cross-link via `implementation` (spec→code) and `graph-link` (code→spec) references at the feature level.

## Rules

`know init` copies rules to `.ai/know/config/`. Local copies take precedence over package defaults.

- `.ai/know/config/dependency-rules.json` — spec graph rules (local)
- `.ai/know/config/code-dependency-rules.json` — code graph rules (local)
- Read these to learn allowed dependencies. Do NOT change without agreement.
- Use `-r` to override auto-detected rules.
- Spec entities → `.ai/know/spec-graph.json`, code entities → `.ai/know/code-graph.json`

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
- `graph uses <entity>` / `graph down <entity>` - Show what an entity uses (dependencies)
- `graph used-by <entity>` / `graph up <entity>` - Show what uses this entity (dependents)
- `graph link <from> <to>` - Add dependency
- `graph unlink <from> <to>` - Remove dependency
- `check validate` - Validate graph structure
- `check stats` - Show graph statistics

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