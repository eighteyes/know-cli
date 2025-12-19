# Beads Integration - QA Checklist

## User Acceptance Testing Checklist

**Testing Date**: _____________
**Tester**: _____________
**Environment**: know-cli (feature/beads-integration branch)

---

## Pre-Testing Setup

- [ ] **Checkout branch**: `git checkout feature/beads-integration`
- [ ] **Review implementation summary**: Read `IMPLEMENTATION_SUMMARY.md`
- [ ] **Review architecture**: Skim `architecture.md` for context
- [ ] **Check Python environment**: Verify Python 3.11+ installed

---

## Section 1: Native Task System (`know task`)

### 1.1 Initialization

**Test**: Initialize native task system

```bash
python3 know/know.py task init
```

**Expected Result**:
- ✓ Creates `.ai/tasks/` directory
- ✓ Creates `.ai/tasks/tasks.jsonl` file
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 1.2 Create Tasks

**Test 1**: Create task with feature link

```bash
python3 know/know.py task add "Implement user authentication" --feature feature:beads-integration
```

**Expected Result**:
- ✓ Task created with hash ID (e.g., `tk-a1b2`)
- ✓ Task linked to feature
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 2**: Create task without feature link

```bash
python3 know/know.py task add "Fix typo in README"
```

**Expected Result**:
- ✓ Task created with hash ID
- ✓ No feature link
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 3**: Create task with description

```bash
python3 know/know.py task add "Add logging" --description "Add comprehensive logging to all modules" --feature feature:beads-integration
```

**Expected Result**:
- ✓ Task created with description
- ✓ Hash ID generated
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 1.3 List Tasks

**Test 1**: List all tasks

```bash
python3 know/know.py task list
```

**Expected Result**:
- ✓ Shows all tasks in rich table format
- ✓ Columns: ID, Title, Status, Feature, Blocks
- ✓ Task count displayed at bottom

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 2**: Filter by feature

```bash
python3 know/know.py task list --feature feature:beads-integration
```

**Expected Result**:
- ✓ Shows only tasks linked to beads-integration
- ✓ Other tasks filtered out

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 3**: Show only ready tasks

```bash
python3 know/know.py task list --ready
```

**Expected Result**:
- ✓ Shows only tasks with no blockers
- ✓ Blocked tasks filtered out

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 1.4 Blocking Dependencies

**Test 1**: Add blocking dependency

```bash
# Create two tasks first
python3 know/know.py task add "Task A"
python3 know/know.py task add "Task B"

# Get task IDs from list command
python3 know/know.py task list

# Add blocking dependency (Task B blocks Task A)
python3 know/know.py task block <task-a-id> --on <task-b-id>
```

**Expected Result**:
- ✓ Dependency added successfully
- ✓ Task A status updated to "blocked"
- ✓ Task B's "blocks" list updated
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 1.5 Ready Task Detection

**Test**: Show ready tasks (auto-detection)

```bash
python3 know/know.py task ready
```

**Expected Result**:
- ✓ Shows only tasks with no blockers
- ✓ Blocked tasks excluded
- ✓ Rich table format with ID, Title, Feature

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 1.6 Mark Task Done

**Test 1**: Mark task complete

```bash
# Get a task ID
python3 know/know.py task list

# Mark it done
python3 know/know.py task done <task-id>
```

**Expected Result**:
- ✓ Task status updated to "done"
- ✓ Success message displayed
- ✓ Task removed from ready list

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 2**: Auto-unblock dependent tasks

```bash
# Setup: Create Task C blocked by Task D
python3 know/know.py task add "Task C"
python3 know/know.py task add "Task D"
python3 know/know.py task block <task-c-id> --on <task-d-id>

# Mark Task D done
python3 know/know.py task done <task-d-id>

# Check if Task C is now ready
python3 know/know.py task ready
```

**Expected Result**:
- ✓ Task D marked as done
- ✓ Task C auto-unblocked
- ✓ Task C appears in ready tasks
- ✓ Message shows "auto-unblocked 1 task"

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 1.7 Sync to Spec-Graph

**Test**: Sync native tasks to spec-graph

```bash
python3 know/know.py task sync
```

**Expected Result**:
- ✓ Tasks imported to spec-graph references
- ✓ Count of synced tasks displayed
- ✓ Statistics shown (total, linked to features)
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Verify in spec-graph**:

```bash
# Check references.task section
cat .ai/spec-graph.json | grep -A 10 '"task":'
```

**Expected Result**:
- ✓ Tasks appear in `references.task` section
- ✓ Task metadata preserved (title, status, feature)

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

## Section 2: Beads Integration (`know bd`)

### 2.1 Pre-Requisite Check

**Test**: Check if `bd` is available

```bash
which bd
```

**Expected Result**:
- ✓ If bd installed: Shows path (e.g., `/usr/local/bin/bd`)
- ✓ If not installed: Empty output

**Actual Result**:
- [ ] bd installed at: _____________
- [ ] bd not installed (skip to Section 2.8)

---

### 2.2 Initialize Beads

**Test 1**: Initialize Beads integration

```bash
python3 know/know.py bd init
```

**Expected Result**:
- ✓ Creates `.ai/beads/` directory
- ✓ Creates symlink `.beads → .ai/beads`
- ✓ Runs `bd init`
- ✓ Updates `.gitignore` with `.beads/`
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 2**: Initialize with stealth mode

```bash
# Clean up first
rm -rf .ai/beads .beads

# Initialize with stealth
python3 know/know.py bd init --stealth
```

**Expected Result**:
- ✓ Beads initialized in stealth mode
- ✓ Same directory structure created

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 2.3 Create Beads Tasks

**Test 1**: Create task with feature link

```bash
python3 know/know.py bd add "Implement JWT validation" --feature feature:beads-integration
```

**Expected Result**:
- ✓ Task created via bd CLI
- ✓ Task ID displayed (e.g., `bd-a1b2`)
- ✓ Linked to feature in graph
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 2**: Create task with description

```bash
python3 know/know.py bd add "Add refresh token" --description "Implement refresh token endpoint" --feature feature:beads-integration
```

**Expected Result**:
- ✓ Task created with description
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 2.4 List Beads Tasks

**Test 1**: List all Beads tasks

```bash
python3 know/know.py bd list
```

**Expected Result**:
- ✓ Shows all Beads tasks in rich table
- ✓ Columns: ID, Title, Status, Feature
- ✓ Task count displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 2**: Filter by ready tasks

```bash
python3 know/know.py bd list --ready
```

**Expected Result**:
- ✓ Shows only ready Beads tasks
- ✓ Blocked/completed tasks filtered out

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Test 3**: Filter by feature

```bash
python3 know/know.py bd list --feature feature:beads-integration
```

**Expected Result**:
- ✓ Shows only tasks linked to beads-integration

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 2.5 Sync Beads to Spec-Graph

**Test**: Sync Beads tasks to spec-graph

```bash
python3 know/know.py bd sync
```

**Expected Result**:
- ✓ Tasks imported to spec-graph references
- ✓ Count of synced tasks displayed
- ✓ Statistics shown (total, linked to features)
- ✓ Success message displayed

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

**Verify in spec-graph**:

```bash
# Check references.beads section
cat .ai/spec-graph.json | grep -A 10 '"beads":'
```

**Expected Result**:
- ✓ Tasks appear in `references.beads` section
- ✓ Task metadata preserved

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 2.6 JSONL Parsing

**Test**: Verify Beads JSONL is parsed correctly

```bash
# Check .ai/beads/issues.jsonl file
cat .ai/beads/issues.jsonl | head -5
```

**Expected Result**:
- ✓ File exists and contains valid JSON per line
- ✓ Each line is a complete JSON object

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 2.7 Conflict Resolution (Beads-First)

**Test**: Verify Beads-first conflict resolution

```bash
# 1. Create and sync a task
python3 know/know.py bd add "Test conflict" --feature feature:beads-integration
python3 know/know.py bd sync

# 2. Update task status in Beads CLI directly
bd update <task-id> --status in-progress

# 3. Sync again
python3 know/know.py bd sync

# 4. Check spec-graph
cat .ai/spec-graph.json | grep -A 5 "<task-id>"
```

**Expected Result**:
- ✓ Spec-graph status updated to "in-progress"
- ✓ Beads status wins over graph status

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 2.8 Error Handling (bd not installed)

**Test**: Verify error message when bd is missing

```bash
# Temporarily rename bd (if installed)
sudo mv /usr/local/bin/bd /usr/local/bin/bd.backup 2>/dev/null || true

# Try to initialize
python3 know/know.py bd init

# Restore bd
sudo mv /usr/local/bin/bd.backup /usr/local/bin/bd 2>/dev/null || true
```

**Expected Result**:
- ✓ Error message: "bd not found. Install Beads first"
- ✓ Install link provided: https://github.com/steveyegge/beads
- ✓ No silent fallback
- ✓ Exit code non-zero

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

## Section 3: Spec-Graph Integration

### 3.1 Graph Validation

**Test**: Validate spec-graph structure

```bash
python3 know/know.py validate
```

**Expected Result**:
- ✓ Validation passes with no errors
- ✓ No invalid dependencies
- ✓ All beads-integration entities valid

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 3.2 Dependency Chain

**Test**: Verify full dependency chain

```bash
python3 know/know.py down feature:beads-integration --recursive
```

**Expected Result**:
- ✓ Shows all 25 operations
- ✓ Shows 4 components
- ✓ Shows 3 actions
- ✓ Complete chain visible

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 3.3 Phase Management

**Test**: Check feature phase

```bash
python3 know/know.py phases list | grep beads
```

**Expected Result**:
- ✓ Feature appears in review-ready phase
- ✓ Status shows "complete"

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

## Section 4: Edge Cases & Error Handling

### 4.1 Empty JSONL Files

**Test**: Handle empty task files gracefully

```bash
# Remove all tasks
rm .ai/tasks/tasks.jsonl

# Try to list
python3 know/know.py task list
```

**Expected Result**:
- ✓ Message: "No tasks found"
- ✓ No errors or crashes

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 4.2 Invalid Task IDs

**Test**: Handle non-existent task IDs

```bash
python3 know/know.py task done tk-9999
```

**Expected Result**:
- ✓ Error message: "Task tk-9999 not found"
- ✓ Non-zero exit code

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 4.3 Circular Dependencies

**Test**: Prevent circular blocking dependencies

```bash
# Create Task E and Task F
python3 know/know.py task add "Task E"
python3 know/know.py task add "Task F"

# Try to create circular dependency
python3 know/know.py task block <task-e-id> --on <task-f-id>
python3 know/know.py task block <task-f-id> --on <task-e-id>
```

**Expected Result**:
- ✓ Second block command should succeed (circular dependency allowed in MVP)
- ⚠ Note: Circular dependency detection deferred to Phase 2

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

## Section 5: Integration Tests

### 5.1 End-to-End Workflow (Native)

**Test**: Complete native task workflow

```bash
# 1. Initialize
python3 know/know.py task init

# 2. Create tasks
python3 know/know.py task add "Design API" --feature feature:beads-integration
python3 know/know.py task add "Implement API" --feature feature:beads-integration
python3 know/know.py task add "Test API" --feature feature:beads-integration

# 3. Add dependencies
python3 know/know.py task block <implement-id> --on <design-id>
python3 know/know.py task block <test-id> --on <implement-id>

# 4. Show ready tasks (should only show "Design API")
python3 know/know.py task ready

# 5. Mark Design API done
python3 know/know.py task done <design-id>

# 6. Check ready tasks again (should show "Implement API")
python3 know/know.py task ready

# 7. Sync to graph
python3 know/know.py task sync

# 8. Verify in graph
python3 know/know.py -g .ai/spec-graph.json get-feature-tasks feature:beads-integration
```

**Expected Result**:
- ✓ All steps complete without errors
- ✓ Auto-unblocking works correctly
- ✓ Ready detection accurate
- ✓ Graph sync successful

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 5.2 End-to-End Workflow (Beads)

**Test**: Complete Beads workflow (requires bd installed)

```bash
# 1. Initialize
python3 know/know.py bd init

# 2. Create tasks
python3 know/know.py bd add "Fix bug #123" --feature feature:beads-integration
python3 know/know.py bd add "Add feature X" --feature feature:beads-integration

# 3. List tasks
python3 know/know.py bd list

# 4. Sync to graph
python3 know/know.py bd sync

# 5. Verify in graph
cat .ai/spec-graph.json | grep -A 10 '"beads":'
```

**Expected Result**:
- ✓ All steps complete without errors
- ✓ Tasks created via bd CLI
- ✓ Sync successful

**Actual Result**:
- [ ] PASS (bd installed)
- [ ] SKIP (bd not installed)
- [ ] FAIL (Notes: _____________)

---

## Section 6: Code Quality

### 6.1 Python Syntax

**Test**: Verify all Python files compile

```bash
python3 -m py_compile know/know.py
python3 -m py_compile know/src/tasks/*.py
```

**Expected Result**:
- ✓ No syntax errors
- ✓ All files compile successfully

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

### 6.2 Import Check

**Test**: Verify imports work

```bash
python3 -c "from know.src.tasks import BeadsBridge, TaskManager, TaskSync; print('Imports OK')"
```

**Expected Result**:
- ✓ Output: "Imports OK"
- ✓ No import errors

**Actual Result**:
- [ ] PASS
- [ ] FAIL (Notes: _____________)

---

## Summary

**Total Tests**: 40+
**Passed**: _____ / _____
**Failed**: _____ / _____
**Skipped**: _____ / _____ (bd not installed)

**Overall Assessment**:
- [ ] **APPROVE** - Ready to merge
- [ ] **APPROVE WITH MINOR CHANGES** - Small fixes needed
- [ ] **REQUEST CHANGES** - Significant issues found
- [ ] **REJECT** - Does not meet requirements

**Notes**:
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

---

**Tester Signature**: _____________
**Date**: _____________
