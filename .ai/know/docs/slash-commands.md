# Know Slash Commands (Claude Skills)

These are the `/know:*` commands available in Claude Code for working with the know system.

## Feature Development Workflow

### `/know:add <feature-name>`
**Add new feature to spec-graph with guided workflow**

Creates feature directory structure, adds to spec-graph, gathers requirements.

**Creates:**
- `.ai/know/<feature>/` directory
- `overview.md` - Feature context
- `todo.md` - Task list
- `plan.md` - Implementation plan
- `spec.md` - Technical spec
- Entry in `spec-graph.json`

**Usage:**
```
/know:add user-authentication
/know:add "Add payment processing"
```

---

### `/know:build <feature>`
**Execute feature development through 7-phase workflow**

Structured workflow: Discovery → Exploration → Design → Implementation → Integration → Testing → Review

**7 Phases:**
1. **Discovery** - Clarify requirements and constraints
2. **Exploration** - Understand codebase patterns (parallel agents)
3. **Design** - Create implementation plan
4. **Implementation** - Write code with checkpoint-based execution
   - Generates XML task spec with `know gen spec --format xml`
   - Uses BuildExecutor to parse and execute tasks
   - Handles checkpoints (auto, human-verify, decision, human-action)
   - Tracks progress in `.ai/know/build-progress.json`
5. **Integration** - Connect to existing systems
6. **Testing** - Verify functionality (parallel agents)
7. **Review** - Final checks and documentation

**Usage:**
```
/know:build auth
/know:build feature:payment-processing
```

**Works with:**
- Existing features (loads from `.ai/know/<feature>/`)
- Inline descriptions (calls `/know:add` first)

**Implementation Features:**
- **Checkpoint workflow**: Tasks are marked as auto, checkpoint:human-verify, checkpoint:decision, or checkpoint:human-action
- **BuildExecutor integration**: Parses XML specs and manages task execution
- **Progress tracking**: Saves state to `.ai/know/build-progress.json` for resumability
- **Wave-based execution**: Tasks are organized by dependency waves

---

### `/know:done <feature>`
**Complete feature and update phase**

Marks feature complete, updates spec-graph phase, archives artifacts.

**Updates:**
- `meta.phases` in spec-graph → "done"
- Feature directory status
- Git notes (if feature tracking enabled)

**Usage:**
```
/know:done auth
/know:done feature:payment-processing
```

---

## Planning & Design

### `/know:plan <topic>`
**Create implementation plan for complex tasks**

Explores codebase, designs approach, creates step-by-step plan.

**Usage:**
```
/know:plan "Refactor authentication system"
/know:plan "Add Redis caching layer"
```

---

### `/know:schema <feature>`
**Generate data schemas and type definitions**

Creates TypeScript interfaces, data models, API schemas from feature requirements.

**Usage:**
```
/know:schema auth
/know:schema payment-processing
```

---

## Documentation & Review

### `/know:review <feature>`
**Review feature implementation for completeness**

Checks:
- Code quality
- Test coverage
- Documentation
- Spec compliance
- Integration points

**Usage:**
```
/know:review auth
/know:review feature:payment-processing
```

---

### `/know:fill-out <feature>`
**Fill gaps in feature documentation**

Reviews feature directory and fills in missing:
- Technical details in `spec.md`
- Implementation notes in `plan.md`
- Acceptance criteria in `overview.md`

**Usage:**
```
/know:fill-out auth
/know:fill-out incomplete-feature
```

---

## Maintenance & Updates

### `/know:change <feature> <changes>`
**Update existing feature with new requirements**

Modifies feature to accommodate new requirements, updates docs and spec-graph.

**Usage:**
```
/know:change auth "Add OAuth support"
/know:change payment "Support cryptocurrency"
```

---

### `/know:bug <feature> <bug-description>`
**Track and fix bugs in features**

Creates bug entry, investigates, proposes fix, tracks resolution.

**Usage:**
```
/know:bug auth "Login fails with special characters"
/know:bug payment "Race condition in checkout"
```

---

## Validation & Connection

### `/know:validate`
**Validate spec-graph structure and completeness**

Runs comprehensive validation:
- Graph structure integrity
- Dependency rules compliance
- Missing connections
- Orphaned references
- Completeness scores

**Usage:**
```
/know:validate
```

Wraps: `know check validate` + analysis

---

### `/know:connect <entity>`
**Suggest valid graph connections for entity**

Analyzes entity and suggests valid dependencies based on:
- Dependency rules
- Existing patterns
- Related entities

**Usage:**
```
/know:connect component:login
/know:connect feature:incomplete
```

Wraps: `know graph connect`

---

### `/know:list [type]`
**List entities from spec-graph**

Quick access to graph entities with filtering.

**Usage:**
```
/know:list                    # All entities
/know:list feature           # All features
/know:list component         # All components
```

Wraps: `know list --type <type>`

---

### `/know:prepare`
**Initialize project with know system**

Full project setup:
1. Explore codebase (parallel agents)
2. Create both graphs (spec + code)
3. Populate project.md
4. Set up know directory structure

**Usage:**
```
/know:prepare
```

---

## Common Workflows

### Starting New Feature
```
1. /know:add payment-processing
2. /know:build payment-processing
   → Goes through 7 phases automatically
3. /know:done payment-processing
```

### Fixing a Bug
```
1. /know:bug auth "Session timeout issues"
   → Investigates and proposes fix
2. Implement fix
3. /know:review auth
```

### Updating Feature
```
1. /know:change auth "Add 2FA support"
   → Updates docs and spec
2. /know:build auth
   → Implements changes
3. /know:review auth
```

### Initial Setup
```
1. /know:prepare
   → Sets up entire system
2. /know:add first-feature
3. /know:build first-feature
```

---

## Integration with CLI

Slash commands are wrappers around or use the know CLI:

| Slash Command | CLI Equivalent |
|---------------|----------------|
| `/know:list` | `know list` |
| `/know:validate` | `know check validate` |
| `/know:connect` | `know graph connect` |
| `/know:build` | Uses `know gen spec --format xml` + BuildExecutor |

**Important: `/know:build` is slash-command only**

The `/know:build` slash command uses CLI utilities but is NOT itself a CLI command:
- Generates XML with: `know gen spec feature:X --format xml`
- Uses BuildExecutor class (from `know/src/build_executor.py`) to execute tasks
- Checkpoint logic and task execution handled by Claude agent
- Progress tracking in `.ai/know/build-progress.json`

---

## Behind the Scenes

### Directory Structure
```
.ai/know/<feature>/
├── overview.md      # Created by /know:add
├── todo.md          # Task tracking
├── plan.md          # Implementation plan
└── spec.md          # Technical spec
```

### Graph Integration
All slash commands interact with:
- **spec-graph.json** - Product intent
- **code-graph.json** - Codebase structure
- **project.md** - Project context

### Phase Tracking
Features move through phases in `meta.phases`:
- `pending` → `/know:add`
- `in-progress` → `/know:build`
- `review-ready` → `/know:review`
- `done` → `/know:done`

---

## Tips

1. **Use parallel agents**: `/know:build`, `/know:prepare`, and `/know:plan` leverage parallel exploration
2. **Tab completion**: Type `/know:` and tab to see all commands
3. **Feature names**: Can use with or without `feature:` prefix
4. **Idempotent**: Commands can be run multiple times safely
5. **Context aware**: Commands load existing feature context automatically

---

## Comparison: Slash vs CLI

**Slash Commands** (`/know:*`)
- Interactive, guided workflows
- Agent-powered exploration
- Rich documentation generation
- Best for: Feature development, planning, review

**CLI Commands** (`know`)
- Direct graph operations
- Scripting and automation
- Precise control
- Best for: Queries, validation, build automation

**Use together:**
```bash
# Use slash command for guided development
/know:build auth

# Use CLI for utilities and queries
know gen code-graph           # Generate code-graph from codemap
know gen spec auth --format xml  # Generate XML task spec
know check validate           # Validate graph structure
know graph uses feature:auth  # Query dependencies
```
