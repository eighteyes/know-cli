---
name: Know: Complete Feature
description: Archive a completed feature to .ai/know/archive/
category: Know
tags: [know, archive, complete]
---

**Prerequisites**
- Activate the know-tool skill for graph validation

**Workflow**

1. Extract feature name from conversation or prompt user
2. Verify feature exists in `.ai/know/<feature-name>/`
3. Check that all tasks in `todo.md` are completed (all checkboxes checked)
   - If not all complete, warn user and ask for confirmation
4. Move entire feature directory:
   - FROM: `.ai/know/<feature-name>/`
   - TO: `.ai/know/archive/<feature-name>/`
5. Confirm the move was successful
6. Use know-tool skill to validate the graph and ensure it's still consistent

**Example Usage**
```
User: /know-done user-authentication
Assistant: Checks completion, moves to archive, confirms success
```

**Safety Checks**
- Verify all todos are checked before archiving
- Confirm feature directory exists
- Ensure archive directory exists (create if needed)
- Don't overwrite existing archived features (prompt for new name if conflict)

**Notes**
- Features can be un-archived by manually moving them back
- Archive maintains full history (proposal, todo, plan, spec)
