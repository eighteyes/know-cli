
# Graph Model

Know uses two graphs in `.ai/know/`. The `-g` flag defaults to `.ai/know/spec-graph.json` and auto-selects rules based on filename.

## Spec Graph (`.ai/know/spec-graph.json`) — Product Intent

Rules: `know/config/dependency-rules.json`

```
Project → User → Objective → Feature → Workflow → Action → Component → Operation
                                     ↘ Action (direct, for simple features)
```

Entities: project, user, objective, feature, workflow, action, component, operation

**Workflow Entity:**
- Ordered sequence of actions forming a complete process
- Uses `depends_on_ordered` field in graph section (array order is significant)
- Features can depend on workflows (complex, ordered sequences) or actions directly (simple cases)
- Actions can be reused across multiple workflows with different orderings

References include: requirement, interface (demoted from entities), plus data-model, business-logic, etc.

## Code Graph (`.ai/know/code-graph.json`) — Codebase Architecture

Rules: `know/config/code-dependency-rules.json`

```
module → [module, package, external-dep]    class → [class, interface, module]
package → [package, module, external-dep]   function → [function, module, class]
layer → [layer]                             namespace → [namespace, module, package]
```

## Graph Structure (both graphs)

```
meta        — project concerns, horizons, name, out of scope
references  — terminal nodes, flexible schema
entities    — fundamental nodes, fixed schema per graph type
graph       — unidirectional, depends_on links (unordered) and depends_on_ordered (workflows only)
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

**CRITICAL: Direct mutation of graph files is blocked by `.claude/hooks/protect-graph-files.sh`**
- Edit/Write tools on `*-graph.json` files → blocked
- Bash commands using `jq`/`sed`/`awk` on graph files → blocked
- Output redirection (`>`, `>>`) to graph files → blocked
- Read-only operations (`cat`, `grep`, `head`, `tail`) → allowed
- Use `know` CLI commands for all graph modifications

## Workflow Entity (Ordered Action Sequences)

**Creating workflows:**
```bash
know add workflow <key> '{"name":"...","description":"..."}'
```

**Linking actions (ordered):**
```bash
# Append to end
know link workflow:onboarding action:signup action:verify action:profile

# Insert at position
know link workflow:onboarding action:welcome --position 0

# Insert after specific action
know link workflow:onboarding action:tour --after action:profile

# Auto-create missing actions
know link workflow:onboarding action:new-step --auto-create
```

**Unlinking actions:**
```bash
know unlink workflow:onboarding action:tour -y
```

**Mixed mode (ordered + unordered):**
```bash
# Workflow can have both depends_on and depends_on_ordered
know link workflow:complex action:step1 action:step2  # ordered
know link workflow:complex component:logger           # unordered utility
```

**Graph structure:**
```json
"graph": {
  "workflow:onboarding": {
    "depends_on_ordered": ["action:signup", "action:verify", "action:profile"]
  }
}
```

Know Tool: `know`

**Key Commands:**
- `graph uses <entity>` / `graph down <entity>` - Show what an entity uses (dependencies)
- `graph used-by <entity>` / `graph up <entity>` - Show what uses this entity (dependents)
- `link <from> <to> [<to2> <to3>...]` - Add one or more dependencies in a single call
- `unlink <from> <to> [<to2> <to3>...]` - Remove one or more dependencies in a single call
- `add <type> <key1> [<key2>...]` - Add one or more entities/references in a single call
- `check validate` - Validate graph structure
- `check stats` - Show graph statistics

**Batch operations:** Always prefer a single call with multiple targets over multiple sequential calls.
```bash
# Good: one call, multiple targets
know link feature:auth action:login action:logout component:session

# Avoid: three separate calls for the same result
know link feature:auth action:login
know link feature:auth action:logout
know link feature:auth component:session
```

**Cross-linking:** The graph is NOT a strict chain. Any valid parent→child relationship should be added, even if it skips levels or connects siblings. A→B, C→D, and A→D are all valid and encouraged when the dependency exists.
```bash
# Example: objective depends on two features; one action used by two features
know link objective:onboarding feature:auth feature:profile
know link feature:dashboard action:filter-results  # same action reused across features
know link feature:reporting action:filter-results
```

# WWW_v2 Map
@www_v2/ASTDOM_MAP.md

# Work Notes
DO NOT ADD FEATURES without approval.
Double check with me about graph schema changes, be precise.
When we improve the approach, save a learning entry to `json-graph-learning.md`

Slash commands: Edit `know/templates/commands/*.md` (source of truth for `know init`), NOT `.claude/commands/know/` (downstream copies). After editing templates, run `know init .` to sync.
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

<!-- know commands revision: 12 - add: codify full QA answers into graph entities/references, open-question reference type for unanswered items -->

<!-- know:start -->
<know-instructions>
When discussing architecture, product decisions, features, or system design,
use the `know` CLI to capture decisions in the spec-graph.

Run `know -h` for commands. Run `know <command> -h` for usage details.

Spec graph entities: project, user, objective, feature, workflow, action, component, operation
Code graph entities: module, package, layer, namespace, interface, class, function

Common reference types: data-model, endpoint, api-contract, business-logic,
  acceptance-criterion, validation-rule, source-file, external-dep, code-link

Run `know check ref-types` for reference types with descriptions.
Run `know gen rules describe entities` for entity types.
Run `know gen rules graph` for the dependency topology.

When adding features, use the `know:add` slash command (/know:add).
Run /know:list to see existing features before adding new ones.
Run `know check validate` after graph changes.
Graph files are write-protected — use `know` CLI commands for all modifications.

Persist architectural decisions as graph entities, not prose.
The spec-graph is the source of truth for product intent.
</know-instructions>
<!-- know:end -->











