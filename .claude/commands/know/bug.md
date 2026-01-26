---
name: Know: Report Bug
description: Create a structured bug report for a feature with requirement tracking in spec-graph
category: Know
tags: [know, bug, tracking, issue]
---

**Main Objective**

Create a structured bug report for a feature, automatically numbering it, creating a fix requirement in spec-graph, and optionally updating feature status.

**Prerequisites**
- Activate the know-tool skill for graph operations
- Feature directory must exist at `.ai/know/features/<feature>/`

**Usage**

```
/know:bug <feature-name>
```

**Workflow**

### 1. Initialization

**Steps**:
1. Verify feature directory exists at `.ai/know/features/<feature>/`
2. Create bugs directory if it doesn't exist: `.ai/know/features/<feature>/bugs/`
3. Determine next bug number by reading existing bug files
4. Check current feature status in spec-graph (using **haiku agent**):
   - `know -g .ai/spec-graph.json show feature:<name>`

### 2. Collect Bug Information

**Use AskUserQuestion to gather details**:

1. **Bug title**:
   - Question: "What is the bug in one sentence?"
   - Collect as free text input

2. **Severity**:
   - Question: "What is the severity of this bug?"
   - Header: "Severity"
   - Options:
     - "Critical" - System crash, data loss, security vulnerability
     - "High" - Major feature broken, no workaround
     - "Medium" - Feature degraded, workaround exists
     - "Low" - Minor issue, cosmetic problem

3. **Description**:
   - Question: "Describe what went wrong in detail"
   - Collect as free text input

4. **Steps to reproduce**:
   - Question: "What are the steps to reproduce this bug? (List them numbered)"
   - Collect as free text input

5. **Expected behavior**:
   - Question: "What should happen instead?"
   - Collect as free text input

6. **Actual behavior**:
   - Question: "What actually happens?"
   - Collect as free text input

7. **Context** (optional):
   - Question: "Any additional context? (environment, logs, screenshots mentioned)"
   - Collect as free text input

### 3. Create Bug File

**Steps**:
1. Generate slug from bug title (lowercase, hyphens, max 40 chars)
2. Create file: `.ai/know/features/<feature>/bugs/NNN-slug.md`
3. Use template below with collected information

**Bug file template**:
```markdown
# Bug #NNN: [Title]

**Severity:** [Critical/High/Medium/Low]
**Status:** Open
**Reported:** YYYY-MM-DD
**Reporter:** [User or context if available]

## Description
[User's detailed description]

## Steps to Reproduce
[User's numbered steps]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Context
[Additional context, environment details, logs]

## Tracking
**Requirement:** requirement:<feature>-fix-bug-NNN
**Query:** `know req status requirement:<feature>-fix-bug-NNN`

## Resolution
<!-- Updated when bug is fixed -->
**Fixed:** [Date]
**Fixed By:** [Person/commit]
**Solution:** [Description of fix]
```

### 4. Create Bug Fix Requirement

**Steps**:
1. Create a requirement in spec-graph for the bug fix:
   ```bash
   know req add <feature> fix-bug-NNN --name "Fix: [Bug title]" \
     --description "See bugs/NNN-slug.md for details. Severity: [Level]"
   ```
2. The requirement will be linked to the feature automatically
3. Track progress with: `know req status requirement:<feature>-fix-bug-NNN in-progress`

### 5. Update Spec-Graph (Optional)

**If feature status is "done" or "review-ready"**:
- Ask user: "This feature is marked as done/review-ready. Change status to 'in-progress'? [Yes/No]"
- If Yes (using **haiku agent**):
  - Update `meta.phases` to move feature back to "in-progress" phase
  - Update `meta.feature_specs.<feature>.status` to "in-progress"
  - Validate: `know validate`

### 6. Confirmation

**Display summary**:
```
Bug #NNN created: [Title]
Severity: [Level]
Location: .ai/know/features/<feature>/bugs/NNN-slug.md
Requirement: requirement:<feature>-fix-bug-NNN
Status: [Updated to in-progress / Kept as <current>]

Next steps:
- Fix the bug: `know req status requirement:<feature>-fix-bug-NNN in-progress`
- Update bug file when resolved
- Mark complete: `know req complete requirement:<feature>-fix-bug-NNN`
- Run /know:review <feature> to verify fix
```

---

## Outputs

- `.ai/know/features/<feature>/bugs/NNN-slug.md` - Structured bug report
- New requirement in spec-graph: `requirement:<feature>-fix-bug-NNN`
- Updated spec-graph status (if changed to in-progress)

---

## Example Usage

```
User: /know:bug user-authentication
Assistant: Found feature at .ai/know/features/user-authentication/
          Creating bugs directory...
          Next bug number: #001

          [Collects information via AskUserQuestion]

          Creating bug file: bugs/001-password-reset-email-not-sent.md
          Creating requirement: requirement:user-authentication-fix-bug-001

          Bug #001 created: Password reset email not being sent
          Severity: High
          Location: .ai/know/features/user-authentication/bugs/001-password-reset-email-not-sent.md
          Requirement: requirement:user-authentication-fix-bug-001
          Status: Feature is in-progress (no change needed)

          Next steps:
          - Fix the bug: `know req status requirement:user-authentication-fix-bug-001 in-progress`
          - Update bugs/001-password-reset-email-not-sent.md when resolved
          - Mark complete: `know req complete requirement:user-authentication-fix-bug-001`
          - Run /know:review user-authentication to verify the fix
```

---

## Notes

- **Quick bug reporting**: Streamlined workflow for capturing bugs outside of review process
- **Automatic numbering**: Bugs are numbered sequentially (001, 002, 003...)
- **Slug generation**: File names are human-readable slugs from bug titles
- **Requirement tracking**: Bug fixes tracked as requirements in spec-graph (`know req list <feature>`)
- **Status management**: Can reopen features marked as done/review-ready
- **Haiku agents**: Graph operations use haiku for speed and cost efficiency
- **Resolution tracking**: Bug files include a Resolution section to document fixes
- **Related to /know:review**: Bugs can be created during review or independently

