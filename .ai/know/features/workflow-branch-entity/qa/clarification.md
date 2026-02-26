# Clarification Q&A: workflow-branch-entity

## Implementation Details

**Q1: Diff Detection Behavior**
When workflow action order changes (e.g., `[a,b,c]` → `[b,a,c]`), should this create a diff entry in `diff-graph.jsonl`?
- Option A: Yes, track reordering as a change
- Option B: No, only track add/remove of dependencies
- **Answer:**

**Q2: CLI Positioning UX**
For ordered linking, which syntax?
- Option A: `know link workflow:X action:a action:b action:c` (append in order)
- Option B: `know link workflow:X action:new --position 2` (insert at index)
- Option C: `know link workflow:X action:new --after action:existing`
- **Answer:**

**Q3: Empty Ordered Array**
Is `depends_on_ordered: []` valid (workflow with zero actions)?
- Option A: Yes, valid (discovery Q7 said "empty is fine")
- Option B: No, must have at least one action
- **Answer:**

**Q4: Mixed Dependency Fields**
Can a workflow have BOTH `depends_on` (unordered) AND `depends_on_ordered`?
- Option A: No, mutually exclusive - use one or the other
- Option B: Yes, allow both (e.g., ordered actions + standalone config references)
- **Answer:**

**Q5: Auto-Create Missing Actions**
Discovery Q7 said "make the action" when workflow references non-existent action. Should this be:
- Option A: Auto-create with minimal data (name only)
- Option B: Prompt user for action description
- Option C: Create as stub/placeholder with special flag
- **Answer:**

**Q6: Delete Workflow Warning**
When deleting an action referenced by workflow, discovery Q7 said "throw warning, allow override to delete in workflow". Implementation:
- Option A: `know nodes delete action:X --cascade` (removes from all workflows)
- Option B: `know nodes delete action:X` (fails with warning listing workflows, requires `--force`)
- Option C: Interactive prompt: "Remove from N workflows? [y/N]"
- **Answer:**

## Error Message Templates

**Q7: Validation Error Messages**
For each scenario, what error message?

**Scenario: Circular dependency with workflow**
```
workflow:onboarding → action:setup
action:setup → workflow:onboarding  // circular!
```
- Message: ?

**Scenario: Invalid workflow dependency (not action)**
```
workflow:onboarding → component:form  // workflows can only depend on actions
```
- Message: ?

**Scenario: Malformed `depends_on_ordered` (not array)**
```
"depends_on_ordered": "action:login"  // should be array
```
- Message: ?

## Graph Structure Details

**Q8: workflow entity in dependency-rules.json**
Where should workflow fit in the allowed_dependencies chain?

- Option A: `feature → workflow → action` (workflow between feature and action)
- Option B: `feature → [action | workflow]`, `workflow → action` (workflow as peer to action)
- **Answer:**

**Q9: `depends_on_ordered` field location**
The `depends_on_ordered` field goes in which section?
- Option A: In entity data (entities.workflow.X.depends_on_ordered)
- Option B: In graph section (graph["workflow:X"].depends_on_ordered)
- **Answer:** (Exploration suggests graph section, confirm)

**Q10: Order preservation in NetworkX**
When building NetworkX DiGraph, how to preserve order?
- Option A: Store order as edge attribute: `G.add_edge(workflow, action, order=1)`
- Option B: Rely on Python 3.7+ dict iteration order (edges added in sequence)
- Option C: Don't store in NetworkX, keep separate ordered list
- **Answer:**

---

**Answers:**

**Q1:** YES - track reordering in diffs
**Q2:** BOTH - `--after action:X` (insert after) AND `--position N` (replace at index)
**Q3:** YES - empty `depends_on_ordered: []` is valid
**Q4:** YES - allow both `depends_on` (unordered) and `depends_on_ordered` simultaneously (mixed mode)
**Q5:** MINIMAL - auto-create with name only (derived from key)
**Q6:** `-y` option to auto-confirm deletion from workflows
**Q8:** OPTION B - `feature → [action | workflow]`, `workflow → action` (workflow as peer)
**Q9:** CONFIRMED - `depends_on_ordered` field in graph section
**Q10:** OPTION A - store order as NetworkX edge attribute: `G.add_edge(workflow, action, order=1)`

**Error Messages:** (to be designed during implementation)
