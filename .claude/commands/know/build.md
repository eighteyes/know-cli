---
name: Know: Build Feature
description: 5-phase workflow: Discover, Clarify, Architect, Implement, Wrapup
category: Know
tags: [know, build, feature-dev, workflow]
---

**Main Objective**
Guide feature development through 5 phases with spec-graph tracking.

**Prerequisites**
- Activate know-tool skill
- Clean git state: If uncommitted changes, ask to commit first

**Entry Points**
- Existing: `/know:build existing-feature` (has `.ai/know/features/<feature>/`)
- Inline: `/know:build "description"` → delegates to `/know:add` first

---

## Phase 1: Discover

**Goal**: Clarify requirements AND explore codebase in parallel

**Steps**:
1. Load `overview.md` if exists
2. **Launch parallel agents** (single message):
   - Explore agent (thoroughness: "medium"): Codebase patterns, conventions
   - Task agent: "Find similar features, trace data flows"
   - Task agent: "Identify architecture patterns, component boundaries"
3. Query spec-graph (haiku): `know deps feature:<name>`, `know used-by feature:<name>`
4. Ask clarifying questions: success criteria, constraints, out of scope, edge cases
5. Consolidate findings

**Outputs**:
- `.ai/know/features/<feature>/qa/discovery.md` - Q&A session
- `.ai/know/features/<feature>/exploration.md` - Codebase findings
- Updated `overview.md` with constraints, success criteria

---

## Phase 2: Clarify

**Goal**: HITL - resolve remaining ambiguities with explicit answers

**Steps**:
1. Based on discovery, identify gaps: edge cases, error handling, integration points, security
2. Present organized questions to user
3. Collect explicit answers (no assumptions)
4. Update spec-graph if new requirements discovered (haiku)

**Outputs**:
- `.ai/know/features/<feature>/qa/clarification.md` - Decisions made
- Updated spec-graph entities if needed

---

## Phase 3: Architect

**Goal**: Design with trade-off analysis, populate graph

**Steps**:
1. **Launch 3 agents in parallel** (single message):
   - Agent 1: Minimal changes approach
   - Agent 2: Clean architecture approach
   - Agent 3: Pragmatic balance
2. Consolidate proposals with trade-offs (cost, risk, maintainability)
3. Present recommendation, **wait for explicit approval**
4. Create ADR in `adrs.md`: Context, Decision, Consequences, Alternatives
5. **Populate spec-graph** (haiku, with confirmation):
   - Add component entities
   - Add operation entities
   - Add references: `source-file`, `signature`, `data-model`, `api-schema`, `business-logic`
   - Link dependencies
6. **Validate**: `know validate`

**Outputs**:
- `.ai/know/features/<feature>/adrs.md` - Architecture Decision Record
- Updated spec-graph with components, operations, references
- Validated graph

---

## Phase 4: Implement

**Goal**: Build in git worktree with continuous documentation

**Worktree Setup**:
```bash
git worktree add ../<repo>-<feature> -b feature/<feature>
# Copy .ai/ to worktree, work there
```

**Steps**:
1. Require explicit approval: "Ready to implement?"
2. Create worktree, switch to it
3. Follow architecture strictly
4. **Update docs continuously**:
   - `todo.md`: Mark complete after EACH task
   - `implementation.md`: Log each significant change
   - `adrs.md`: Add ADR for any architectural pivots
5. Update phase status to "in-progress" (haiku)
6. Commit as you go in feature branch

**Outputs**:
- Worktree at `../<repo>-<feature>/`
- Feature branch: `feature/<feature>`
- Implemented code
- Updated `todo.md`, `implementation.md`
- Phase status: "in-progress"

---

## Phase 5: Wrapup

**Goal**: Review, summarize, generate QA steps

**Steps**:
1. **Launch 3 review agents in parallel** (single message):
   - Simplicity reviewer: DRY violations, over-engineering (≥80% confidence)
   - Bug reviewer: Edge cases, error handling (≥80% confidence)
   - Conventions reviewer: Pattern consistency (≥80% confidence)
2. Present issues, user chooses: Fix now / Fix later / Proceed
3. **Validate graphs**: `know validate`, `know gap-analysis feature:<name>`
4. Write `summary.md`: accomplishments, modified files, follow-ups
5. Write `QA_STEPS.md`:
   - **Human-only tests**: UX, visual, usability (exclude machine-testable items)
   - Numbered steps with expected outcomes
   - Checkbox format
6. **Update spec-graph**:
   - `know -g .ai/spec-graph.json phases status feature:<name> review-ready`
7. Update `todo.md` final status:
   ```markdown
   ## Build Complete
   - [x] Implementation (Phase 4)
   - [x] Review & Summary (Phase 5)
   - [ ] User testing (`/know:review`)
   - [ ] Merge & archive (`/know:done`)
   ```
8. Sync `.ai/` back to main repo
9. Inform user: "Run `/know:review <feature>` to test"

**Outputs**:
- `.ai/know/features/<feature>/review.md` - Quality findings
- `.ai/know/features/<feature>/summary.md` - Completion summary
- `.ai/know/features/<feature>/QA_STEPS.md` - Human test steps
- Updated `todo.md` with final status
- Spec-graph: feature status set to "review-ready"
- `.ai/` synced to main repo

---

## File Structure

```
.ai/know/features/<feature>/
├── overview.md          # Requirements
├── todo.md              # Task checklist
├── plan.md              # Implementation plan
├── qa/
│   ├── discovery.md     # Phase 1 Q&A
│   └── clarification.md # Phase 2 Q&A
├── exploration.md       # Phase 1 codebase findings
├── adrs.md              # Phase 3+ decisions
├── implementation.md    # Phase 4 notes
├── review.md            # Phase 5 findings
├── summary.md           # Phase 5 summary
└── QA_STEPS.md          # Phase 5 test steps
```

---

## Notes

- **Parallel agents**: Always launch in single message for true parallelism
- **Haiku agents**: Use for all graph queries (fast, cheap)
- **Continuous docs**: Update immediately, never batch
- **User approval**: Required at architecture and implementation start
- **Resumable**: Can pause/resume at any phase
- When complete: `/know:review` to test, `/know:done` to archive

---
`r4`
