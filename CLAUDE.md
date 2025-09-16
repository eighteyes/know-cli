Graph File : `.ai/spec-graph.json`

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
HOW: Project → Requirements → Interface → Feature → Component → ( UI + Data Models )
WHAT: Project → User → Objectives → Actions
Integration: User → Requirements, Objectives → Features, Actions → Components
```
Every entity MUST have a reference as dependents. Any reference may link to any dependent. 

## Dependency Rules
`./know/lib/dependency-rules.json`
- Read to learn more about the graph structure.
- Do NOT change this file without agreement. 
- Defer to this file for inconsistencies in the graph.

# Graph Notes


# GRAPH SCRIPTS
Use these to modify / query the graph file. ALWAYS utilize these instead of `jq`, when using bash & when writing other scripts.

Query: !`./know/lib/query-graph.sh -h`
Modify: !`./know/lib/mod-graph.sh -h`

All Scripts: !`ls scripts/`

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

Validate the graph after every change with `npm run validate-graph`. 