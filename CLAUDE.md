
# Graph TOP LEVEL
```
meta - all project level concerns, phases, name, out of scope
meta.phases - ONLY location for planning / temporal information
references - terminal graph nodes used for template generation, flexible schema, biz logic, acceptance criteria, ui concerns, they use plaintext, not `key_object_notation` in final nodes
entities - fundamental graph nodes used in dependency map below, fixed schema. the contents of these are granular items, not categories. 
graph - unidirectional graph, ONLY depends_on links
```

# Graph Dependency Map
If you need to resolve circular dependencies, refer to this.
```
HOW: Project → Requirements → Interface → Feature → Component → ( Behaviors + Presentation + Data Models + assets )
WHAT: Project → User → Objectives → Actions
Integration: User → Requirements, Objectives → Features, Actions → Behaviors
```
Every entity MUST have a reference or another entity as dependent. Any reference can be depended upon by an entity.

## Dependency Rules
`./know/config/dependency-rules.json`
- Read to learn more about the graph structure.
- Do NOT change this file without agreement. 
- Defer to this file for inconsistencies in the graph.
- Descriptions should be written generically, and not reference a particular project.

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

# WWW Rules
Do NOT refer to AI, graph, entities or references in the visible text.
- www is on 8880
- @know/config/dependency-rules.json @.ai/spec-graph.json