- IMPORTANT: Keep ~/ai/commands/lb/knowledge-graph.md and graph-approach.md updated with the latest evolution of the structure in `.ai/3spec-graph.json` approach
- IMPORTANT: When we improve the approach, save a learning entry to `json-graph-learning.md`
- string together multiple `jq` commands into a single BASH call

# Graph Dependency Map
If you need to resolve circular dependencies, refer to this.
```
HOW: Project → Platform → Requirements → Interface → Feature → Action → Component → UI → Data Models
WHAT: Project → User → Objectives → Actions
Integration: User → Requirements, Objectives → Features, Actions → Components
```

# GRAPH SCRIPTS
All in `scripts/`. Favor using these scripts to read, analyze and change the chart, if it would be more efficient then reading / writing the file directly. When you write other utilities, rely on these scripts to help. 

Query: !`./know/lib/query-graph.sh -h`
Modify: !`./know/lib/mod-graph.sh -h`

All Scripts: !`ls scripts/`


# Graph
!`cat spec-graph.json`

# Work Notes
IMPORTANT: DO NOT ADD FEATURES without approval. 
Double check with me about graph schema changes, be precise.