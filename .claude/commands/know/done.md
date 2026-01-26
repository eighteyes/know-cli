---
name: Know: Complete Feature
description: Archive a completed feature to .ai/know/features/archive/
category: Know
tags: [know, archive, complete]
---

**Prerequisites**
- Activate the know-tool skill for graph validation

**Auto-creates**: `config.json` if missing (touch it = track it)

**Workflow**

### 1. Detect Git Worktree Status

**Steps**:
1. Check if feature has an associated worktree:
   ```bash
   git worktree list | grep "feature/<feature-name>"
   ```
2. Determine current location:
   ```bash
   MAIN_WORKTREE=$(git worktree list | head -1 | awk '{print $1}')
   CURRENT_TOPLEVEL=$(git rev-parse --show-toplevel)
   ```
3. **If worktree exists**:
   - If currently IN that worktree: Switch to main repo first
   - If in main or different worktree: Proceed from current location

### 2. Verify Feature Completion

**Steps**:
1. Extract feature name from conversation or prompt user
2. Verify feature exists in `.ai/know/features/<feature-name>/`
3. Check that all requirements are complete: `know req list <feature-name>`
   - If not all complete/verified, warn user and ask for confirmation
4. Check spec-graph status is "done" or "complete"

### 3. Merge Feature Branch (if worktree exists)

**Steps**:
1. **Ensure in main repo**:
   ```bash
   cd $MAIN_WORKTREE
   ```
2. **Sync .ai/ from worktree** (if it hasn't been synced yet):
   ```bash
   cp -r ../<repo-name>-<feature-name>/.ai/know/features/<feature-name>/ .ai/know/features/<feature-name>/
   ```
3. **Merge feature branch**:
   ```bash
   git checkout main
   git merge --no-ff feature/<feature-name> -m "Merge feature: <feature-name>"
   ```
4. **Ask user**: "Delete feature branch? [Yes/No]"
   - If Yes: `git branch -d feature/<feature-name>`

### 4. Remove Git Worktree (if exists)

**Steps**:
1. Remove the worktree:
   ```bash
   git worktree remove ../<repo-name>-<feature-name>
   ```
2. Verify removal was successful

### 5. Archive Feature Directory

**Steps**:
1. Move entire feature directory:
   - FROM: `.ai/know/features/<feature-name>/`
   - TO: `.ai/know/features/archive/<feature-name>/`
2. Confirm the move was successful

### 6. Update Feature Index

**Steps**:
1. Read `.ai/know/features/feature-index.md`
2. Move feature entry from "Features" to "Archived Features" section (create if doesn't exist)
3. Update summary counts (decrement active, increment archived)
4. Update feature status to "archived" and add archived date

### 7. Update Spec-Graph Phase

**Steps**:
1. Update phase status to "done" (using **haiku agent**)
2. Validate both spec-graph and code-graph
3. Confirm graphs are consistent

### 8. Identify Related Commits

**Steps**:
1. Get feature baseline from config.json or directory mtime:
   ```bash
   cat .ai/know/features/<feature-name>/config.json 2>/dev/null | jq '.baseline'
   ```

2. Find commits since baseline using CLI:
   ```bash
   know tag-feature <feature-name> --json
   ```

3. Present commits to user:
   ```
   The following commits touch files related to this feature:

   [1] 0a42a87 - chore(spec-generation): move feature to in-progress
   [2] f570887 - feat(spec-generation): implement rich spec generation
   [3] e987c75 - feat: add feature and enhance bd list

   Select commits to tag (comma-separated numbers, 'all', or 'none'):
   ```

4. Confirm selection with user

### 9. Tag Commits with Git Notes

**Steps**:
1. Tag each selected commit:
   ```bash
   git notes --ref=refs/notes/know-features add -f -m "know:feature:<feature-name>" <sha>
   ```

2. Verify tagging:
   ```bash
   git notes --ref=refs/notes/know-features show <sha>
   ```

3. Report success:
   ```
   Tagged 4 commits with know:feature:<feature-name>
   ```

### 10. Store Commits in Spec-Graph

**Steps**:
1. Update `meta.feature_commits` in spec-graph:
   ```json
   "feature_commits": {
     "<feature-name>": ["sha1", "sha2", "sha3"]
   }
   ```

2. Use jq or direct edit to add entry:
   ```bash
   # Verify current state
   jq '.meta.feature_commits' .ai/spec-graph.json
   ```

3. Validate spec-graph:
   ```bash
   know validate
   ```

**Example Usage**
```
User: /know-done user-authentication
Assistant: Checks completion, moves to archive, confirms success
```

**Safety Checks**
- Verify all requirements are complete before archiving (`know req list <feature>`)
- Confirm feature directory exists
- Ensure archive directory exists (create if needed)
- Don't overwrite existing archived features (prompt for new name if conflict)

**Notes**
- Features can be un-archived by manually moving them back
- Archive maintains full history (proposal, notes, plan, spec, requirements in graph)
- **Worktree handling**:
  - Automatically detects if feature was built in a worktree
  - Switches to main repo if currently in feature worktree
  - Merges feature branch using `--no-ff` for clear history
  - Removes worktree after successful merge
  - Can run from main repo or any worktree (auto-navigates as needed)

