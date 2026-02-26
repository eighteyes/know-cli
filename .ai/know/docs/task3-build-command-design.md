# Task #3: /know:build Command Design

## Goal

Execute tasks from XML spec autonomously until hitting checkpoint for human review.

## MVP Scope (v0.1)

**Simple task executor that:**
1. Parses XML spec
2. Displays tasks sequentially
3. Shows full context per task (action, files, verify, done)
4. Stops at checkpoints for review
5. Tracks progress

**NOT in v0.1:**
- Full autonomous LLM execution (future)
- Complex dependency resolution
- Parallel execution

## Command Interface

```bash
# Execute from XML file
/know:build .ai/plans/feature-auth.xml

# Generate and execute inline
know gen spec feature:auth --format xml | /know:build

# Resume from checkpoint
/know:build .ai/plans/feature-auth.xml --resume
```

## Implementation

### 1. XML Parser (`know/src/build_executor.py`)

```python
class BuildExecutor:
    def __init__(self, xml_path: str):
        self.xml_path = xml_path
        self.spec = self._parse_xml()
        self.progress = {}  # task_id -> status

    def _parse_xml(self) -> dict:
        """Parse XML spec into task structure"""
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        return {
            "meta": self._parse_meta(root.find('meta')),
            "context": self._parse_context(root.find('context')),
            "tasks": self._parse_tasks(root.find('tasks'))
        }

    def execute(self):
        """Execute tasks until checkpoint"""
        for task in self.spec['tasks']:
            if task['type'] == 'auto':
                self._display_task(task)
                self._mark_complete(task['id'])
            elif task['type'].startswith('checkpoint:'):
                self._handle_checkpoint(task)
                break  # Stop at checkpoint
```

### 2. Checkpoint Handlers

```python
def _handle_checkpoint(self, task):
    checkpoint_type = task['type']

    if checkpoint_type == 'checkpoint:human-verify':
        # Display task, mark for review
        self._display_task(task)
        console.print("[yellow]⏸ CHECKPOINT: Human review required[/yellow]")
        console.print("[dim]Review implementation and run: /know:build --resume[/dim]")

    elif checkpoint_type == 'checkpoint:decision':
        # Display decision options
        self._display_decision(task)
        # Wait for user choice

    elif checkpoint_type == 'checkpoint:human-action':
        # Display manual action needed
        self._display_manual_action(task)
```

### 3. Task Display Format

```
╔═══════════════════════════════════════════════════════╗
║ Task #1: Generate Rich Feature Spec                  ║
║ Type: checkpoint:human-verify | Wave: 1               ║
╚═══════════════════════════════════════════════════════╝

📁 Files:
   • know/src/generators.py

📝 Action:
   Implement Generate Rich Feature Spec:

   Component: Spec Generator
   Enhanced SpecGenerator class with helper methods

   Operation: Enhanced feature spec generation...

   Implementation guidance:
   - Use existing SpecGenerator class
   - Add helper methods for metadata access
   - Render using Jinja2 templates

✅ Verify:
   Test: pytest know/tests/test_generators.py::test_generate_rich
   Expected: All sections populated correctly

🎯 Done:
   Generate Rich Feature Spec implemented and verified.
   CHECKPOINT: Human reviews implementation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏸ CHECKPOINT: Review implementation before continuing

   Options:
   1. Mark complete and continue
   2. Skip this task
   3. Exit and resume later
```

### 4. Progress Tracking

Store progress in `.ai/build-progress.json`:

```json
{
  "spec_file": ".ai/plans/feature-auth.xml",
  "feature": "feature:auth",
  "started_at": "2026-02-09T12:00:00Z",
  "tasks": {
    "task-1": {
      "status": "completed",
      "completed_at": "2026-02-09T12:15:00Z"
    },
    "task-2": {
      "status": "in_progress"
    }
  }
}
```

## CLI Skill Integration

Since this is a slash command (`/know:build`), integrate as a skill:

```yaml
# .claude/skills/know-tool/commands/build.md
name: build
description: Execute tasks from XML spec until checkpoint
trigger: /know:build
```

## Future Enhancements (v0.2+)

1. **LLM Execution** - Actually execute tasks via Claude API
2. **Parallel Execution** - Run same-wave tasks in parallel
3. **Dependency Resolution** - Recompute waves on failure
4. **Rollback** - Undo task execution
5. **Test Automation** - Run verify commands automatically
6. **File Modification Tracking** - Git integration

## Implementation Order

1. ✅ XML parser
2. ✅ Task display
3. ✅ Progress tracking
4. ✅ Checkpoint handling
5. ⏳ CLI command integration
6. ⏳ Skill wrapper for /know:build
