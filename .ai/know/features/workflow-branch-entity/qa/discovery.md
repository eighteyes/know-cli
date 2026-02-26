# Discovery Q&A: workflow-branch-entity

## Success Criteria

**Q1: What defines "complete" for this feature?**
- [ ] `know add workflow <key>` command works
- [ ] `know link workflow:X action:a action:b` preserves order
- [ ] `know graph down workflow:X` shows ordered actions
- [ ] Validation detects circular dependencies with workflows
- [ ] `dependency-rules.json` updated with workflow entity type
- [ ] CLAUDE.md documents workflow hierarchy
- [ ] Existing spec-graph files continue to validate (backwards compatibility)
- [ ] Other success criteria?

**Q2: What does "validation passed" mean for workflows?**
- All `depends_on_ordered` targets exist as action entities?
- No circular dependencies when workflows are in the graph?
- Array order preserved when reading/writing JSON?
- Workflow dependencies follow allowed rules (workflow→action only)?
- Other validation rules?

## Constraints

**Q3: Backwards compatibility requirements?**
- Must existing spec-graph files work without modification?
- Should validation gracefully handle graphs without workflows?
- Can we change the graph schema structure, or only add fields?
- Are there version constraints?

**Q4: Performance considerations?**
- How large can `depends_on_ordered` arrays get (max actions per workflow)?
- Any concerns about graph traversal performance with workflows?
- Does order preservation add noticeable overhead?

## Scope Boundaries

**Q5: What workflow features are OUT of scope for this iteration?**
- [ ] Workflow nesting (workflow→workflow)?
- [ ] Parallel action execution (forking/joining)?
- [ ] Conditional branching in workflows?
- [ ] Workflow templates/reuse mechanisms?
- [ ] Workflow execution tracking/state?
- [ ] Workflow versioning?
- [ ] Other advanced features?

**Q6: Are workflows ONLY for spec-graph, or also code-graph?**
- Should code-graph support workflows too (e.g., execution flows)?
- Or is this strictly a product spec concern?

## Edge Cases

**Q7: What happens when:**
- A workflow references an action that doesn't exist yet?
- An action is deleted that's referenced by a workflow?
- The same action appears multiple times in one workflow?
- A workflow has zero actions (empty `depends_on_ordered`)?
- A feature depends on the same action both directly AND via workflow?

**Q8: Validation error messages:**
- What error message for circular dependency involving workflow?
- What error message for invalid workflow→entity dependency (not action)?
- What error message for malformed `depends_on_ordered` (not array)?

## Migration & Integration

**Q9: Existing graphs without workflows:**
- Do existing features need to migrate to workflows?
- Or can features continue using direct action dependencies?
- Is there a migration guide/tool needed?

**Q10: Integration with existing know commands:**
- Does `know list --type workflow` need to exist?
- Does `know get workflow:X` work automatically?
- Does `know search` find workflows?
- Any other command interactions?

---

**Answers:**

**Q1:** ✓ All listed success criteria confirmed
**Q2:** ✓ All listed validation rules confirmed
**Q3:** No backwards compatibility constraints for initial release
**Q4:** No performance concerns for now
**Q5:** OUT of scope: workflow nesting, parallel execution, conditional branching, templates, execution tracking, versioning
**Q6:** Spec-graph ONLY (product specs), not code-graph
**Q7 Edge Cases:**
- Missing action: Auto-create if referenced by workflow
- Deleted action: Throw warning, allow override flag to delete from workflow
- Duplicate action: Allowed (same action can appear multiple times in workflow)
- Empty workflow: Allowed (zero actions is valid)
- Feature with both workflow + direct action: Allowed (confirmed)
**Q8:** Error messages to be designed during implementation
**Q9:** No migration needed - existing features keep direct action dependencies
**Q10:** All entity commands work: `know list --type workflow`, `know get workflow:X`, `know search`
