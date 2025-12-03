---
name: Know: Review Feature
description: Interactive QA walkthrough for end-user acceptance testing of completed features
category: Know
tags: [know, review, qa, testing, acceptance]
---

**Main Objective**

Guide user through interactive end-user acceptance testing of a completed feature using the generated QA_STEPS.md, recording results and updating feature status based on approval.

**Prerequisites**
- Feature must have completed `/know:build` (status: "complete" or "review-ready")
- `.ai/know/<feature>/QA_STEPS.md` must exist

**Usage**

```
/know:review <feature-name>
```

**Workflow**

### 1. Initialization

**Steps**:
1. Verify feature directory exists at `.ai/know/<feature>/`
2. Check that `QA_STEPS.md` exists (if not, inform user to run `/know:build` Phase 7 first)
3. Check spec-graph status (using **haiku agent**):
   - `know -g .ai/spec-graph.json show feature:<name>`
   - Verify status is "complete", "review-ready", or "in-progress"
4. Load `QA_STEPS.md` content

### 2. Display Context

**Steps**:
1. Show feature objective from QA_STEPS.md
2. Display prerequisites/setup requirements
3. Ask user: "Are prerequisites met? Ready to begin testing? [Yes/No]"
   - If No: Exit with message "Complete prerequisites first"
   - If Yes: Proceed

### 3. Interactive Test Execution

**For each test step in QA_STEPS.md**:

1. Display step number and description
2. Display expected outcome
3. Use AskUserQuestion tool:
   - Question: "Did this step work as expected?"
   - Options:
     - "Pass" - Works as expected
     - "Fail" - Does not work as expected
     - "Skip" - Unable to test right now
4. If "Fail":
   - Ask follow-up: "What happened instead? Describe the issue."
   - Record detailed failure description
5. Track results for summary

**Tracking format**:
```
Step 1: [PASS/FAIL/SKIP]
  Description: ...
  Expected: ...
  Actual: [if failed, user's description]
```

### 4. Acceptance Criteria Check

**After all test steps**:

1. Display acceptance criteria from QA_STEPS.md
2. For each criterion:
   - Ask: "Is this criterion met? [Yes/No]"
   - Record response
3. Calculate pass rate:
   - Passed steps / Total steps (excluding skipped)

### 5. Final Decision

**Steps**:
1. Display summary:
   - Test steps: X passed, Y failed, Z skipped
   - Acceptance criteria: A/B met
   - Overall pass rate: XX%
2. Use AskUserQuestion:
   - Question: "What is your decision on this feature?"
   - Options:
     - "Approve" - Feature meets requirements, ready for deployment
     - "Needs Work" - Issues found, requires fixes
     - "Defer" - Testing incomplete, review again later
3. Based on decision:
   - **Approve**:
     - Update spec-graph status to "done" (using **haiku agent**)
     - Offer: "Run `/know:done` to archive feature? [Yes/No]"
   - **Needs Work**:
     - Keep status as "in-progress"
     - Create action items for fixes
   - **Defer**:
     - Keep current status
     - Save progress for next review session

### 6. Generate Review Artifacts

**Always create**:
- `.ai/know/<feature>/review-results.md`:
  ```markdown
  # Review Results: <Feature Name>
  Date: YYYY-MM-DD
  Reviewer: [User name if available]

  ## Summary
  - Test Steps: X passed, Y failed, Z skipped
  - Acceptance Criteria: A/B met
  - Pass Rate: XX%
  - Decision: [Approve/Needs Work/Defer]

  ## Test Step Results

  ### Step 1: [Description]
  - Status: [PASS/FAIL/SKIP]
  - Expected: ...
  - Actual: ...

  [... for each step]

  ## Acceptance Criteria

  - [x] Criterion 1
  - [ ] Criterion 2

  ## Notes
  [Any additional comments from user]
  ```

**If "Needs Work" selected**:
- `.ai/know/<feature>/review-feedback.md`:
  ```markdown
  # Review Feedback: <Feature Name>
  Date: YYYY-MM-DD

  ## Issues Found

  ### Issue 1: [From failed step]
  - Step: Step X
  - Expected: ...
  - Actual: ...
  - Severity: [Critical/High/Medium/Low] (ask user)

  [... for each failed step]

  ## Action Items

  - [ ] Fix Issue 1
  - [ ] Fix Issue 2
  - [ ] Re-run review after fixes
  ```

### 7. Update Spec-Graph

**Using haiku agent**:
- If Approved:
  - `know -g .ai/spec-graph.json update feature:<name> '{"status": "done"}'` (or similar update)
  - Add review completion date to meta if possible
- If Needs Work:
  - Keep status as "in-progress"
- If Deferred:
  - No status change

**Outputs**:
- `.ai/know/<feature>/review-results.md` - Test execution results
- `.ai/know/<feature>/review-feedback.md` - Issues found (if Needs Work)
- Updated spec-graph status (if Approved)
- Optional: Feature ready for `/know:done` archival

---

## Example Session

```
User: /know:review user-authenticationAssistant: Found feature at .ai/know/user-authentication/
          Loading QA_STEPS.md...

          === Feature: User Authentication ===
          Objective: Enable users to securely log in and manage sessions

          Prerequisites:
          - Test database seeded with user test@example.com / password123
          - Application running on localhost:3000

          Are prerequisites met? Ready to begin testing?

User: [Selects "Yes"]
Assistant: Found feature. Loading QA steps...
          Test step 1: Login with valid credentials
          Expected: User redirected to dashboard
          
          Did this step work as expected?

User: [Selects "Pass"]

Assistant: Test step 2: Login with invalid password
          Expected: Error message displayed
          
          Did this step work as expected?

User: [Selects "Fail" and enters "No error message shown"]

Assistant: ...
          
          === Summary ===
          Test Steps: 4 passed, 1 failed, 0 skipped
          Pass Rate: 80%
          
          What is your decision on this feature?

User: [Selects "Needs Work"]

Assistant: Created review-results.md and review-feedback.md
          Status kept as "in-progress"
          
          Review complete. Fix issues and re-run /know:review when ready.
```

---

## Notes

- Use AskUserQuestion tool for all yes/no and multi-choice prompts
- Keep language user-facing (not technical) in QA_STEPS.md
- Record actual vs expected for all failures
- Update spec-graph only on "Approve" decision
- **Worktree compatibility**:
  - Can run from feature worktree (recommended - test in isolation)
  - Can run from main repo (also works - reads `.ai/know/<feature>/`)
  - Can run from any location with access to `.ai/` directory
  - Feature remains in worktree until `/know:done` is run
