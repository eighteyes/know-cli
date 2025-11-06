
# Graph TOP LEVEL
```
meta - all project level concerns, phases, name, out of scope
meta.phases - ONLY location for planning / temporal information
references - terminal graph nodes used for template generation, flexible schema, biz logic, acceptance criteria, ui concerns, they use plaintext, not `key_object_notation` in final nodes
entities - fundamental graph nodes used in dependency map below, fixed schema. the contents of these are granular items, not categories. 
graph - unidirectional graph, ONLY depends_on links
```

# Graph Dependency Map (spec-graph.json)
Product specification chains - maps user intent to implementation.
```
HOW: Project → Requirement → Interface → Feature → Action → Component → Operation
WHAT: Project → User → Objective → Action
Integration: User → [Requirement], Objective → [Action, Feature], Action → [Component]
```
Every entity MUST have a reference or another entity as dependent. Any reference can be depended upon by an entity.

# Code Dependency Map (code-graph.json)
Code architecture chains - maps modules and packages in the codebase.
```
module → [module, package, external-dep]
package → [package, module, external-dep]
layer → [layer]
namespace → [namespace, module, package]
interface → [module, type-def]
class → [class, interface, module]
function → [function, module, class]
```
Code entities represent the actual implementation structure.

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

Know Tool: !`./know/know`

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