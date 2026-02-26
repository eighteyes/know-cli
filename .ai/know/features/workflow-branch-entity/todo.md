# TODO: workflow-branch-entity

## Schema & Configuration
- [x] Update `.ai/know/config/dependency-rules.json`
  - [x] Add `workflow` to entity types
  - [x] Allow `feature → workflow`
  - [x] Allow `workflow → action`
- [ ] Document `depends_on_ordered` field in schema

## Core Implementation
- [x] Add `depends_on_ordered` support to graph module
- [x] Implement workflow entity creation (workflow.py WorkflowManager)
- [x] Implement ordered linking (workflow.py link_actions)
- [x] Update graph traversal to handle `depends_on_ordered`
- [x] Preserve array order in JSON read/write

## Validation
- [x] Validate `depends_on_ordered` targets exist
- [x] Check for circular dependencies with ordered deps
- [x] Ensure DAG invariants maintained
- [x] Add workflow-specific validation rules

## CLI Commands
- [x] `know add workflow <key>`
- [x] `know link workflow:<key> <actions...>` (preserves order)
- [x] `know link --position N` flag
- [x] `know link --after ACTION` flag
- [x] `know link --auto-create` flag
- [x] `know unlink workflow:<key> <actions...>` with -y flag
- [x] `know graph down workflow:<key>` (shows ordered list)
- [x] `know graph up action:<key>` (includes workflows)

## Testing
- [ ] Unit tests for `depends_on_ordered` parsing
- [ ] Integration tests for workflow creation
- [ ] Validation tests for circular deps
- [ ] Graph traversal tests with workflows

## Documentation
- [ ] Update CLAUDE.md with workflow hierarchy
- [ ] Document `depends_on_ordered` semantics
- [ ] Add workflow examples
- [ ] Update dependency rules documentation
