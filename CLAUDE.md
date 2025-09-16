Graph File : `.ai/spec-graph.json`

# Graph TOP LEVEL
```
meta - all project level concerns, phases, name, out of scope
meta.phases - ONLY location for planning / temporal information
references - terminal graph nodes used for template generation, flexible schema, biz logic, acceptance criteria, ui concerns, they use plaintext, not `key_object_notation` in final nodes
entities - fundamental graph nodes used in dependency map below, fixed schema
graph - unidirectional graph, ONLY depends_on links
```

# Graph Dependency Map
If you need to resolve circular dependencies, refer to this.
```
HOW: Project → Requirements → Interface → Feature → Component → ( UI + Data Models )
WHAT: Project → User → Objectives → Actions
Integration: User → Requirements, Objectives → Features, Actions → Components
```

# GRAPH SCRIPTS
Use these to modify / query the graph file. Utilize these instead of `jq` when writing other scripts.

Query: !`./know/lib/query-graph.sh -h`
Modify: !`./know/lib/mod-graph.sh -h`

All Scripts: !`ls scripts/`

# Work Notes
IMPORTANT: Your assumptions about graphs are WRONG for this project. Validate any graph work with me before touching the spec-graph.json file.
DO NOT ADD FEATURES without approval. 

Double check with me about graph schema changes, be precise.
IMPORTANT: NO `refs`, `requires`, or other direct dependencies in objects, we are using a graph. 
When we improve the approach, save a learning entry to `json-graph-learning.md`
