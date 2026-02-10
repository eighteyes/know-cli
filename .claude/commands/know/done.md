---
name: Know: Complete Feature
description: Archive a completed feature to .ai/know/archive/
category: Know
tags: [know, archive, complete]
---

**Prerequisites**
- Activate the know-tool skill for graph validation

**Workflow**

### 1. Extract Feature Name

**Steps**:
1. Extract feature name from conversation context or prompt user
2. Verify feature directory exists at `.ai/know/<feature-name>/`

### 2. Execute Done Command

**Steps**:
1. Run the know CLI command:
   ```bash
   know feature done <feature-name>
   ```
2. The command will:
   - Validate completion (implementation linkage, requirements)
   - Check for review-results.md
   - Detect and handle git worktree
   - Merge feature branch (if worktree exists)
   - Mark as done in spec-graph
   - Archive to .ai/know/archive/

### 3. Confirm Completion

**Steps**:
1. Verify the command completed successfully
2. Confirm feature has been archived to `.ai/know/archive/<feature-name>/`
3. Confirm spec-graph updated to "done" phase

**Example Usage**
```
User: /know:done user-authentication
Assistant: Runs `know feature done user-authentication`
          Feature archived to .ai/know/archive/user-authentication/
          Spec-graph updated to "done" phase
```

**Safety Checks (handled by CLI)**
- Validate completion before archiving
- Verify feature was reviewed
- Confirm feature directory exists
- Ensure archive directory exists (create if needed)
- Don't overwrite existing archived features (prompt for new name if conflict)

**Notes**
- **Skill wraps CLI command**: This skill calls `know feature done <feature>` which handles all the logic
- Features can be un-archived by manually moving them back
- Archive maintains full history (proposal, todo, plan, spec, review results)
- **Validation happens first**:
  - CLI command validates completion (graph linkage, requirements)
  - Checks for review-results.md
  - Only proceeds if feature is ready
- **Worktree handling** (automated by CLI):
  - Detects if feature was built in a worktree
  - Switches to main repo if currently in feature worktree
  - Merges feature branch using `--no-ff` for clear history
  - Removes worktree after successful merge
  - Can run from main repo or any worktree (auto-navigates as needed)

---
`r1`
