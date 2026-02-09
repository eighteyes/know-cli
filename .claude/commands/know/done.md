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

### 1. Verify Feature Completion

**Steps**:
1. Extract feature name from conversation or prompt user
2. Verify feature exists in `.ai/know/features/<feature-name>/`
3. Check that all requirements are complete: `know req list <feature-name>`
   - If not all complete/verified, warn user and ask for confirmation
4. Check spec-graph status is "review-ready" or "complete"

### 2. Archive Feature Directory

**Steps**:
1. Create archive directory if needed: `.ai/know/features/archive/`
2. Move entire feature directory:
   - FROM: `.ai/know/features/<feature-name>/`
   - TO: `.ai/know/features/archive/<feature-name>/`
3. Confirm the move was successful

### 3. Update Feature Index

**Steps**:
1. Read `.ai/know/features/feature-index.md` (create if missing)
2. Move feature entry from "Features" to "Archived Features" section
3. Update summary counts (decrement active, increment archived)
4. Update feature status to "archived" and add archived date

### 4. Update Spec-Graph Status

**Steps**:
1. Update feature status to "complete" (using **haiku agent**):
   ```bash
   know phases status feature:<feature-name> complete
   ```
2. Validate both spec-graph and code-graph:
   ```bash
   know -g .ai/spec-graph.json validate
   know -g .ai/code-graph.json validate
   ```
3. Confirm graphs are consistent

### 5. Identify Related Commits

**Steps**:
1. Get feature baseline from config.json or directory mtime:
   ```bash
   cat .ai/know/features/archive/<feature-name>/config.json 2>/dev/null | jq '.baseline'
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

### 6. Tag Commits with Git Notes

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

### 7. Store Commits in Spec-Graph

**Steps**:
1. Update `meta.feature_commits` in spec-graph:
   ```json
   "feature_commits": {
     "<feature-name>": ["sha1", "sha2", "sha3"]
   }
   ```

2. Validate spec-graph:
   ```bash
   know validate
   ```

**Example Usage**
```
User: /know:done user-authentication
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
- Git branching/merging is an independent concern - handle separately if needed
