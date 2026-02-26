# Task Integration with /know:build

## Summary

Integrated native JSONL task management into the `/know:build` workflow to enable automatic task tracking and completion during feature development.

## Changes Made

### 1. Task Import Command
- **Command**: `know task import`
- **Function**: Imports markdown todos from `.ai/know/features/*/todo.md`
- **Features**:
  - Auto-links tasks to features based on directory name
  - Converts nested checkboxes to blocking dependencies
  - Idempotent (skips duplicates based on title matching)
- **Location**: `know/know.py:2408-2436`, `know/src/tasks/task_manager.py:357-447`

### 2. Auto-Import on Init
- **Trigger**: `know init` after task system setup
- **Behavior**: Automatically detects and imports existing feature todos
- **Location**: `know/know.py:1500-1512`, `know/know.py:1524-1536`

### 3. Updated /know:build Workflow

#### Phase 4: Implementation
- AI marks tasks as done during implementation
- Auto-detection: matches implemented work to task titles
- Commands: `know task list --feature`, `know task done tk-xxxx`
- Shows summary of marked tasks

#### Phase 5: Wrapup  
- Run `know task sync` to sync tasks to spec-graph
- Show completion summary: "X/Y tasks completed"
- List remaining tasks
- Include task stats in summary.md
- Feature marked as "review-ready" (human approval required)

### 4. File Updates
- `.claude/commands/know/build.md` (r4 → r5)
- `know/templates/commands/build.md`
- `know/src/tasks/task_manager.py`
- `know/know.py`

## Test Results

✅ Imported 206 tasks from existing markdown todos
✅ Skipped 13 duplicates (idempotency verified)
✅ Blocking relationships work correctly
✅ Task system integrated with feature workflow

## Workflow

```
/know:build feature:my-feature
  ↓
[Phase 4: Implement]
  ↓
AI implements code → Auto-marks matching tasks done
  ↓
[Phase 5: Wrapup]
  ↓
know task sync → Sync to spec-graph
  ↓
Feature → "review-ready" phase (awaiting human approval)
  ↓
/know:review → Human tests feature
  ↓
Human approves → Feature complete
```

## Key Principles

- **AI marks tasks done** - Based on auto-detection of implemented work
- **Humans approve features** - Features stay "review-ready" until human testing
- **Sync at end** - Task list synced to spec-graph in Phase 5
- **No time tracking** - Focus on completion, not estimates

## Commands Reference

```bash
# Import todos (manual or auto on init)
know task import

# List tasks for a feature
know task list --feature feature:my-feature

# Mark task done
know task done tk-xxxx

# Show ready tasks
know task ready

# Sync to spec-graph
know task sync
```

