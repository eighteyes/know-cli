---
name: Know: Review Feature
description: Interactive QA walkthrough for end-user acceptance testing of completed features
category: Know
tags: [know, review, qa, testing, acceptance]
---

**Main Objective**

Guide user through interactive end-user acceptance testing of a completed feature using the generated QA_STEPS.md, recording results and updating feature status based on approval.

**CRITICAL: ACTIVE TESTING WORKFLOW**
This is NOT just a code review. The assistant should:
1. **Test what can be automated**: Run CLI commands, execute scripts, check file outputs, verify logs
2. **Guide user to validate the rest**: UI behavior, visual elements, user experience, edge cases requiring judgment

**Testing Responsibilities**:
- **AI tests**: CLI output, file generation, data validation, error handling, API responses, calculations
- **User validates**: UI appearance, visual feedback, usability, subjective quality, cross-browser behavior

**Workflow**:
- For each QA step, determine if it's automatable
- If automatable: Execute the test, show results, ask user to confirm
- If not automatable: Guide user through manual validation
- Record all results (Pass/Fail/Skip) and collect failure details

**Prerequisites**
- Feature must have completed `/know:build` (status: "complete" or "review-ready")
- `.ai/know/features/<feature>/QA_STEPS.md` must exist
- **Application must be running and ready to test**

**Usage**

```
/know:review <feature-name>
```

**Workflow**

### 1. Initialization

**Steps**:
1. Verify feature directory exists at `.ai/know/features/<feature>/`
2. Check that `QA_STEPS.md` exists (if not, inform user to run `/know:build` Phase 7 first)
3. Check spec-graph status (using **haiku agent**):
   - `know -g .ai/spec-graph.json show feature:<name>`
   - Verify status is "complete", "review-ready", or "in-progress"
4. Load `QA_STEPS.md` content

### 2. Display Context and Confirm User is Ready to Test

**Steps**:
1. Show feature objective from QA_STEPS.md
2. Display prerequisites/setup requirements
3. **Explicitly remind user**: "You will need to manually test the feature in your running application. I will guide you through each test step and record your results."
4. Ask user: "Is your application running and are you ready to begin testing? [Yes/No]"
   - If No: Exit with message "Start your application and complete prerequisites first"
   - If Yes: Proceed to interactive testing

### 3. Interactive Test Execution

**For each test step in QA_STEPS.md**:

1. **Display step number, description, and expected outcome**
2. **All steps are human-executed** (QA_STEPS contains NO automation):
   - Instruct user: "Please test this in your running application"
   - Describe what to do and what to look for
   - Ask: "Did this step work as expected? [Pass/Fail/Skip]"
3. **If "Fail"**:
   - Ask follow-up: "What happened instead? Describe the issue."
   - Record detailed failure description
4. **Track results for summary**

**Tracking format**:
```
Step 1: [PASS/FAIL/SKIP]
  Description: ...
  Expected: ...
  Actual: [if failed, user's description]
```

### 3a. Contract Action Verification

**After QA_STEPS testing, verify declared actions**:

1. **Load contract.yaml** from `.ai/know/features/<feature>/contract.yaml`
2. **For each declared action** in `declared.actions[]`:
   - Display action entity and description
   - Ask: "Did you verify that '{action description}' works correctly? [Yes/No/Skip]"
   - **If "Yes"**: Toggle `verified: true` for this action
   - **If "No"**: Record as unverified, add to discrepancies
   - **If "Skip"**: Leave as unverified
3. **Update contract.yaml** with verification status
4. **If all actions verified**:
   - Set `observed.verified_date` to current timestamp
   - Set `observed.verified_commit` to current HEAD

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
     - Proceed to "Create Action Items" (section 5a)
   - **Defer**:
     - Keep current status
     - Save progress for next review session

### 5a. Create Action Items (if "Needs Work" selected)

**Steps**:
1. **Categorize each failed test step**:
   - For each failure, ask user: "How should this issue be tracked?"
     - "Bug" - Defect that needs fixing
     - "Change" - Modification to requirements or approach
     - "Enhancement" - Improvement suggestion
     - "Skip" - Don't track this one
2. **Assign severity** for each bug/change:
   - Ask: "What is the severity?"
   - Options: Critical / High / Medium / Low
3. **Create structured tracking files**:
   - Create directories if they don't exist:
     - `.ai/know/features/<feature>/bugs/`
     - `.ai/know/features/<feature>/changes/`
   - For each bug: Create `bugs/NNN-slug.md` (numbered sequentially)
   - For each change: Create `changes/NNN-slug.md`
4. **Create requirements for fixes** (replaces todo.md approach):
   - For each bug/change, add a requirement to track the fix:
     ```bash
     # For bug fix:
     know req add <feature> fix-bug-NNN --name "Fix: [Bug title]" \
       --description "See bugs/NNN-slug.md for details"

     # For change:
     know req add <feature> impl-change-NNN --name "Change: [Change title]" \
       --description "See changes/NNN-slug.md for details"
     ```
   - These requirements will show in `know req list <feature>`
5. **Offer to create implementation plan**:
   - If 3+ bugs/changes, ask: "Create implementation plan for these fixes? [Yes/No]"
   - If Yes: Create `.ai/know/features/<feature>/plans/review-fixes-YYYYMMDD.md`

**Bug file template** (`.ai/know/features/<feature>/bugs/001-description.md`):
```markdown
# Bug #001: [Title from test step]

**Severity:** [Critical/High/Medium/Low]
**Status:** Open
**Found:** YYYY-MM-DD Review
**Test Step:** [Step number from QA_STEPS.md]

## Description
[From review feedback - what went wrong]

## Steps to Reproduce
[Copy from QA_STEPS.md]

## Expected Behavior
[From QA_STEPS.md expected outcome]

## Actual Behavior
[User's description of what happened]

## Tracking
**Requirement:** requirement:<feature>-fix-bug-NNN
**Query:** `know req status requirement:<feature>-fix-bug-NNN`
```

**Change file template** (`.ai/know/features/<feature>/changes/001-description.md`):
```markdown
# Change #001: [Title]

**Priority:** [Critical/High/Medium/Low]
**Status:** Proposed
**Identified:** YYYY-MM-DD Review
**Test Step:** [Step number that triggered this]

## Current Behavior
[What exists now]

## Proposed Change
[What should be different]

## Rationale
[Why this change is needed - from review feedback]

## Impact
- [Areas affected by this change]

## Tracking
**Requirement:** requirement:<feature>-impl-change-NNN
**Query:** `know req status requirement:<feature>-impl-change-NNN`
```

### 6. Generate Review Artifacts

**Always create**:
- `.ai/know/features/<feature>/review-results.md`:
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
- `.ai/know/features/<feature>/review-feedback.md`:
  ```markdown
  # Review Feedback: <Feature Name>
  Date: YYYY-MM-DD

  ## Summary
  - Test Steps: X passed, Y failed
  - Bugs Created: Z
  - Changes Proposed: W

  ## Issues Found

  ### Issue 1: [From failed step]
  - Step: Step X
  - Expected: ...
  - Actual: ...
  - Tracked As: Bug #001 (see bugs/001-description.md)
  - Severity: [Critical/High/Medium/Low]
  - Requirement: requirement:<feature>-fix-bug-001

  [... for each failed step]

  ## Requirements Created

  Bug fixes and changes are tracked as requirements in spec-graph:
  - `know req list <feature>` to see all requirements
  - `know req status requirement:<feature>-fix-bug-NNN complete` to mark done

  ## Next Steps

  1. Address bugs/changes by working through requirements
  2. Update requirement status as items are completed
  3. Re-run `/know:review <feature>` after fixes
  ```
- Structured bug/change files in:
  - `.ai/know/features/<feature>/bugs/NNN-description.md`
  - `.ai/know/features/<feature>/changes/NNN-description.md`
- Requirements added to spec-graph for tracking (replaces todo.md)

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
- `.ai/know/features/<feature>/review-results.md` - Test execution results
- `.ai/know/features/<feature>/review-feedback.md` - Summary of issues (if Needs Work)
- `.ai/know/features/<feature>/bugs/NNN-*.md` - Structured bug tracking files (if bugs found)
- `.ai/know/features/<feature>/changes/NNN-*.md` - Structured change requests (if changes needed)
- `.ai/know/features/<feature>/plans/review-fixes-*.md` - Implementation plan (if 3+ issues)
- New requirements in spec-graph for bug fixes/changes (tracked via `know req list`)
- Updated spec-graph status (if Approved)
- Optional: Feature ready for `/know:done` archival (if Approved)

---

## Example Session

```
User: /know:review user-authenticationAssistant: Found feature at .ai/know/features/user-authentication/
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

- **Human-only QA_STEPS** - All testing steps are manual human verification:
  - UI test: "Does the login button appear blue?"
  - Flow test: "Complete the checkout process and verify confirmation"
  - Edge case: "Try an invalid input and verify error message"
  - NO automated tests in QA_STEPS (those go in test files)
- **Contract action verification** (Section 3a):
  - Each declared action must be verified by user
  - Verification updates contract.yaml `verified: true`
  - All verified → sets verified_date and verified_commit
- Use AskUserQuestion tool for all yes/no and multi-choice prompts
- Keep language user-facing (not technical) in QA_STEPS.md
- Record actual vs expected for all failures
- Update spec-graph only on "Approve" decision
- **Worktree compatibility**:
  - Can run from feature worktree (recommended - test in isolation)
  - Can run from main repo (also works - reads `.ai/know/features/<feature>/`)
  - Can run from any location with access to `.ai/` directory
  - Feature remains in worktree until `/know:done` is run

---
`r2` - Requirements replace todo.md: bug fixes and changes tracked as requirements in spec-graph
`r1` - Added contract action verification (Section 3a), human-only QA_STEPS
