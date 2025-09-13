- IMPORTANT: Keep ~/ai/commands/lb/knowledge-graph.md and json-graph-approach.md updated with the latest evolution of the structure in `spec-graph.json` approach
- IMPORTANT: When we improve the approach, save a learning entry to `json-graph-learning.md`
- string together multiple `jq` commands into a single BASH call

# Graph Dependency
If you need to resolve circular dependencies, refer to this.
```
HOW: Project → Platform → Requirements → Interface → Feature → Action → Component → UI → Data Models
WHAT: Project → User → Functionality → Actions
Integration: User → Requirements, Functionality → Features, Actions → Components
```

# GRAPH SCRIPTS
All in `scripts/`. Favor using these scripts to read, analyze and change the chart, if it would be more efficient then reading / writing the file directly. When you write other utilities, rely on these scripts to help. 

Query: !`./know/lib/query-graph.sh -h`
Modify: !`./know/lib/mod-graph.sh -h`

All Scripts: !`ls scripts/`


# Graph
!`cat spec-graph.json`