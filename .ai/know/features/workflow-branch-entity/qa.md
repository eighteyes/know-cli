# QA: workflow-branch-entity
_Each answer maps to a graph entity or reference. See type hints per section._

## Actions & Operations  [→ action:*, operation:*]

1. **What's the complete sequence from "I want a workflow" to "it's working in my graph"?** Walk through every discrete step - from the command to create it, how you define which actions go in what order, how you attach it to a feature, and what validates it's all wired up proper.

2. **When a workflow goes wrong during creation or execution, what specific failure states exist and what does the system do about each one?** What breaks when actions are missing? When ordering is invalid? When dependencies conflict? When a workflow references actions that don't exist?

3. **What's the most complex action a developer takes when working with workflows, and what are ALL the sub-operations that fire under the hood?** Is it reordering? Is it dependency validation? Break down the gnarliest bit into every component operation.

4. **What discrete actions does a developer take to modify or inspect an existing workflow?** How do they view the current sequence? Change action order? Add/remove actions mid-workflow? Validate it still makes sense?

5. **What state transitions occur in the graph when a workflow is added, modified, or removed?** What entities get created/updated/linked in what order? What happens to the actions it references? What validation runs between each state change?

## Components & Responsibilities  [→ component:*]

6. **What component validates workflow dependencies and ordering constraints?** What does it receive as input (workflow entity, action list) and what does it produce (validation errors, dependency graph)?

7. **What component handles serialization/deserialization of `depends_on_ordered` field?** How does it preserve array order when reading/writing JSON?

8. **What component enforces dependency rules specific to workflows?** Does it reuse existing validation, or need workflow-specific logic for ordered dependencies?

9. **What component handles workflow-to-action linking operations?** What's different from regular entity linking?

10. **What component manages graph traversal for ordered dependencies?** How does it differentiate between `depends_on` and `depends_on_ordered` when traversing?

## Data Models & Interfaces  [→ data-model:*, interface:*, api_contract:*]

11. **Data Model - Workflow Entity Schema**: What properties must a workflow entity contain (id, name, description, status fields, etc.), and specifically how should the `depends_on_ordered` field be structured in the JSON?

12. **Interface - CLI Commands**: What exact CLI commands and flags should be available for workflow operations? Command syntax for creating workflows, linking actions to workflows in sequence, reordering workflow steps, querying workflow execution order?

13. **Data Validation - Workflow Constraints**: What validation rules must pass before accepting workflow data? Can workflows depend on other workflows? Must all linked actions already exist? Can the same action appear multiple times in one workflow? Circular dependency checks?

14. **Data Model - Graph JSON Structure**: What does the actual JSON structure look like in `spec-graph.json` for workflows? Show the exact format for a workflow entity entry, how `depends_on_ordered` appears in the graph section, and an example workflow with 3 ordered actions.

15. **API Contract - Graph Query Interface**: What data structures must the graph traversal functions return when querying workflows? When running `know graph uses workflow:X`, does it return ordered or unordered dependencies? How does the system differentiate between ordered workflow dependencies and regular `depends_on` relationships?

## Rules, Config & Constraints  [→ business_logic:*, configuration:*, security-spec:*, constraint:*, acceptance_criterion:*]

16. **Business Logic - Dependency Ordering Rules**: When a workflow contains ordered actions (A→B→C), what are the exact rules for how this translates to the dependency graph? Does workflow→action create regular depends_on edges, or only ordered ones? Can actions appear in multiple workflows with different orderings?

17. **Configuration - Graph Selection & Rule Loading**: What determines which graph file and dependency rules apply when working with workflows? Should workflow validation use spec-graph rules exclusively, or workflow-specific rules? What's the precedence chain for finding the right rules file?

18. **Security Spec - Graph Mutation Boundaries**: Given that direct graph file mutation is blocked by hooks, what are the specific allowed and forbidden operations for workflow entities? Can workflows reference code-graph entities or only spec-graph entities?

19. **Constraint - DAG Invariants Under Ordered Dependencies**: What are the hard rules that prevent workflow-ordered dependencies from creating cycles or violating the DAG structure? If workflow W contains actions A→B→C, and elsewhere we have C→A as a regular dependency, is that forbidden?

20. **Acceptance Criterion - Observable Correctness**: From a user's perspective, what specific commands and outputs prove this feature works? What should `know check validate` report? What's the expected output of `know graph down workflow:X` that distinguishes ordered from unordered dependencies?

---
_Design Notes:_
- Only workflows have `depends_on_ordered` (for now)
- Hierarchy: Feature → Workflow → Actions (ordered)
- Features can also depend on actions directly (simple cases)
- `depends_on_ordered` is explicit, no semantic overloading

_Answers:_

**11. Workflow Entity Schema:**
Standard entity fields: `name`, `description` (like all entities)

**14. Graph JSON Structure:**
```json
"workflow:login-flow": {
  "depends_on_ordered": ["action:show-form", "action:validate", "action:create-session"]
}
```
`depends_on_ordered` is a `string[]` - array of entity keys

**16. Dependency Ordering Rules:**
Normal `depends_on` semantics, but array order is significant for workflows.
No circular dependencies created.
Hierarchy: `feature → workflow → action`, `feature → action` (mixed case)
Actions can appear in multiple workflows with different orderings.

**20. Acceptance Criteria:**
- `know graph down workflow:X` returns ordered action list
- Validation ensures all actions in `depends_on_ordered` exist as entities
- Validation ensures workflow dependencies don't create cycles
- `know check validate` passes with workflow entities present
