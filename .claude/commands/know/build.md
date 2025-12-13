---
name: Know: Build Feature (7-Phase Workflow)
description: Structured 7-phase workflow for building features with discovery, exploration, design, implementation, and review
category: Know
tags: [know, build, feature-dev, workflow]
---

**Main Objective**

Guide feature development through a structured 7-phase workflow adapted from Claude Code's feature-dev plugin, integrated with the know ecosystem for spec-graph tracking and documentation.

**Prerequisites**
- Activate the know-tool skill for graph operations
- **Clean git state required**: Check `git status` before proceeding
  - If uncommitted changes exist, ask user: "Uncommitted changes detected. Commit before starting build? [Yes/No]"
  - If Yes: Help user commit (use `/lb:commit` or manual commit)
  - If No: Warn that worktree will not include uncommitted changes, proceed only with explicit confirmation

**Exploration Strategy**
- **Use parallel agents** throughout this workflow for speed and depth
- **Explore agent**: Discovers codebase nuances, patterns, and perspectives (use `thoroughness: "medium"` or `"very thorough"`)
- **Custom Task agents**: Create specialized agents with specific objectives
- **Launch in parallel**: Use SINGLE message with multiple Task tool calls to run agents concurrently
- Phases 2, 4, and 6 explicitly require parallel agent launches

**Documentation Strategy**
- **Update feature docs continuously** throughout the workflow
- After completing work in each phase, immediately update the corresponding feature file
- Keep documentation in sync with actual progress—never batch updates
- Each phase has specific docs to update (see phase outputs)

**Entry Points**

1. **Existing feature**: `/know:build existing-feature` (directory exists at `.ai/know/features/existing-feature/`)
2. **Inline feature**: `/know:build "Add user authentication"` (no directory yet)

**Initialization Logic**

```
IF feature directory exists (.ai/know/features/<feature>/):
  → Load context from overview.md, todo.md, plan.md
  → Verify feature exists in spec-graph.json
  → Update meta.phases status to "in-progress"
  → Proceed to Phase 1

ELSE (inline feature description or non-existent feature):
  → Delegate to /know:add to scaffold feature
  → Wait for /know:add completion
  → Load created context
  → Proceed to Phase 1
```

---

## 7-Phase Workflow

### Phase 1: Discovery

**Goal**: Clarify requirements and constraints

**Steps**:
1. Read `.ai/know/features/<feature>/overview.md` if exists
2. Ask clarifying questions:
   - What are the success criteria?
   - What constraints exist?
   - What is out of scope?
   - Who are the users of this feature?
   - What are the edge cases?
3. **Update docs immediately**:
   - Save Q&A to `.ai/know/features/<feature>/qa/discovery.md` (create if missing)
   - Format: Question → Answer → Implications
4. Query spec-graph (using **haiku agents**):
   - `know -g .ai/spec-graph.json deps feature:<name>` - What does this feature depend on?
   - `know -g .ai/spec-graph.json used-by feature:<name>` - What depends on this feature?
5. **Update overview.md immediately**:
   - Add "Success Criteria" section if discovered
   - Add "Constraints" section with limits
   - Add "Out of Scope" section with exclusions
   - Refine existing requirements based on clarifications

**Outputs**:
- `.ai/know/features/<feature>/qa/discovery.md` - Discovery Q&A session
- Updated `.ai/know/features/<feature>/overview.md`

---

### Phase 2: Codebase Exploration

**Goal**: Understand existing implementation patterns and architecture

**CRITICAL: Use parallel exploration for speed and depth**

**Steps**:
1. **Launch multiple agents in parallel** (single message with multiple Task tool calls):
   - **Explore agent (thoroughness: "medium")**: Discover codebase nuances, patterns, and conventions
   - **Custom Task agents** (2-3 specialized agents):
     - Agent 1: "Find similar features and trace their data flows"
     - Agent 2: "Identify architecture patterns and component boundaries"
     - Agent 3: "Map UI/UX conventions and existing abstractions"
   - Launch ALL agents in a single message for true parallelism
2. **Know-enhanced exploration** (using **haiku agents**):
   - Query code-graph: `know -g .ai/code-graph.json list-type module`
   - Find related components via product-component references
   - Query: `know -g .ai/code-graph.json uses component:<name> --recursive`
3. **Spec-graph exploration** (using **haiku agents**):
   - Query related actions: `know -g .ai/spec-graph.json list-type action`
   - Find component dependencies
   - Check data-model references
4. **Consolidate findings** from all explorers (Explore + custom Task agents)
5. **Update exploration.md immediately**:
   - Document all patterns discovered
   - List relevant files with descriptions
   - Note architectural conventions
   - Identify similar features and their approaches
   - Save consolidated findings to `.ai/know/features/<feature>/exploration.md`

**Example parallel launch**:
```
Send SINGLE message with:
- Task(subagent_type="Explore", thoroughness="medium", prompt="Explore authentication patterns...")
- Task(subagent_type="general-purpose", prompt="Trace data flow for user sessions...")
- Task(subagent_type="general-purpose", prompt="Identify security middleware patterns...")
```

**Outputs**:
- `.ai/know/features/<feature>/exploration.md` - Consolidated codebase understanding
- List of files to reference during implementation

---

### Phase 3: Clarifying Questions

**Goal**: Identify and resolve remaining ambiguities

**Steps**:
1. Based on discovery and exploration, identify gaps:
   - Edge cases not yet addressed
   - Error handling approaches
   - Integration points unclear
   - Performance/security considerations
2. Present organized list of questions to user
3. Collect explicit answers (no assumptions)
4. **Update docs immediately**:
   - Save Q&A to `.ai/know/features/<feature>/qa/clarification.md` (create if missing)
   - Format: Question → Answer → Decision Made
   - Include which alternative approaches were rejected and why
5. **Update spec-graph if new requirements discovered** (using **haiku agents**):
   - Add requirement entities if needed
   - Update feature description
   - Link new requirements to feature in graph

**Outputs**:
- `.ai/know/features/<feature>/qa/clarification.md` - Clarification Q&A
- Updated spec-graph entities (if needed)

---

### Phase 4: Architecture Design

**Goal**: Design implementation approach with trade-off analysis

**CRITICAL: Launch custom Task agents in parallel for multiple perspectives**

**Steps**:
1. **Launch 3 custom Task agents in parallel** (single message with 3 Task tool calls):
   - **Agent 1 (Minimal changes)**: "Design architecture minimizing changes to existing code. Reuse components, avoid refactors. What's the quickest path?"
   - **Agent 2 (Clean architecture)**: "Design ideal architecture ignoring existing code. What's the cleanest, most maintainable approach?"
   - **Agent 3 (Pragmatic balance)**: "Design architecture balancing new patterns with existing code. What's the best trade-off?"
   - Each agent should consult spec-graph and code-graph
   - Launch ALL 3 in a single message for true parallelism
2. **Know-enhanced architecture** - Each agent consults:
   - Spec-graph component dependencies (using **haiku agents**)
   - Data model references from spec-graph
   - Interface definitions
   - Existing component contracts
3. **Consolidate 3 proposals** with trade-off analysis (cost, risk, maintainability, time)
4. **Present recommendation** to user with clear pros/cons
5. **Wait for explicit approval** before proceeding
6. **Update ADR immediately** after approval in `.ai/know/features/<feature>/adrs.md`:
   - Create file if it doesn't exist
   - Add ADR-001 (or next number) with:
     - **Context**: Why architecture decision needed
     - **Decision**: Chosen approach (from 3 proposals)
     - **Consequences**: Trade-offs, pros/cons
     - **Alternatives**: Other 2 proposals considered and why rejected
   - Include date and status (Accepted)
7. **Update spec-graph immediately** with architecture (using **haiku agents**, WITH CONFIRMATION):
   - Add/update component entities with name and description
   - Add operation entities for each component's operations
   - Add `source-file:<name>` references with file paths
   - Add `signature:<name>` references with params[] and returns
   - Add `data-model:<name>` references with TypeScript schemas
   - Add `api-schema:<name>` references for public APIs
   - Add `business-logic:<name>` references for execution flows
   - Link dependencies in graph:
     - `feature → component`
     - `component → operation`
     - `component → source-file`
     - `operation → signature`
     - `operation → data-model`
     - `feature → business-logic`
8. **Validate graph**: Run `know validate` to confirm structure

**Outputs**:
- `.ai/know/features/<feature>/adrs.md` - Architecture Decision Records (starting with ADR-001)
- Updated spec-graph with entities, operations, and references
- Validated graph (no errors)

---

### Phase 5: Implementation

**Goal**: Build the feature following chosen architecture in a git worktree

**Git Worktree Setup**:
1. **Detect main repository location**: Get absolute path to current repo (e.g., `/path/to/abc/`)
2. **Determine worktree path**: Sibling directory with pattern `<repo-name>-<feature-name>/`
   - Example: Main repo at `/path/to/abc/` → Worktree at `/path/to/abc-user-auth/`
3. **Create git worktree**:
   ```bash
   git worktree add ../abc-<feature-name> -b feature/<feature-name>
   ```
4. **Switch to worktree**: All subsequent work happens inside the worktree
5. **Copy .ai/ directory** to worktree for context access

**Implementation Steps**:
1. **Require explicit user approval**: "Ready to implement? [Yes/No]"
2. **Create and switch to worktree** (see Git Worktree Setup above)
3. Read all relevant files from exploration phase
4. Follow chosen architecture strictly
5. **CRITICAL: Update feature files continuously as you work** (not at the end!):

   **todo.md updates** (after completing each task):
   - Read `.ai/know/features/<feature>/todo.md` before starting each task
   - Mark task as complete immediately after finishing
   - Format: `- [ ] Task name` → `- [x] Task name`
   - Update after EACH completed task (one at a time)

   **implementation.md updates** (as you write code):
   - Add entry for each significant change/addition
   - Document decisions made during implementation
   - Note deviations from original architecture (with rationale)
   - Track file changes: "Created `auth/handler.ts` with JWT validation"
   - Format:
     ```markdown
     ## [Timestamp] Component Name
     - Created/Updated: `file/path.ts`
     - What: Brief description of change
     - Why: Reason for approach chosen
     - Notes: Any important details
     ```

   **overview.md updates** (when requirements evolve):
   - If user clarifies/changes requirements during implementation
   - Add to "Requirements Refinements" section
   - Document what changed and when

   **adrs.md updates** (for architectural decisions):
   - Add Architecture Decision Record (ADR) for each significant choice
   - Format: ADR-NNN: [Decision Title]
   - Include: Date, Status, Context, Decision, Consequences, Alternatives considered
   - Update when pivoting from original architecture

6. Update phase status in spec-graph: `"status": "in-progress"` (using **haiku agent**)
7. As code is written, link modules to spec-graph components:
   - Add to code-graph: `know -g .ai/code-graph.json add module <name> {...}`
   - Link via product-component references
8. Commit changes as you go in the worktree branch (include updated .ai/ files)
9. **Sync pattern**: After each meaningful milestone, sync .ai/ to main repo

**Outputs**:
- Git worktree created at `../<repo-name>-<feature-name>/`
- Feature branch: `feature/<feature-name>`
- Implemented code files (in worktree)
- Updated `.ai/know/features/<feature>/todo.md` with progress
- Updated `.ai/know/features/<feature>/implementation.md` with notes
- Updated code-graph with new modules
- Phase status: "in-progress" in spec-graph
- Git commits in feature branch
- Phase status: "in-progress" in spec-graph

---

### Phase 6: Quality Review

**Goal**: Validate correctness, quality, and integration

**CRITICAL: Launch custom Task agents in parallel for comprehensive review**

**Steps**:
1. **Launch 3 custom Task agents in parallel** (single message with 3 Task tool calls):
   - **Reviewer 1 (Simplicity)**: "Review for simplicity, DRY violations, over-engineering. Report only high-confidence issues (≥80%)."
   - **Reviewer 2 (Bugs)**: "Review for bugs, edge cases, error handling gaps. Report only high-confidence issues (≥80%)."
   - **Reviewer 3 (Conventions)**: "Review for consistency with existing patterns, naming conventions, architectural violations. Report only high-confidence issues (≥80%)."
   - Launch ALL 3 in a single message for true parallelism
2. **Know-enhanced validation** (using **haiku agents**):
   - Gap analysis: `know -g .ai/spec-graph.json gap-analysis feature:<name>`
   - Verify all component dependencies satisfied
   - Check code-graph completeness
   - Validate both graphs: `know validate`
3. **Update review.md immediately** with findings:
   - Document all issues found by each reviewer
   - Include confidence levels (≥80% only)
   - Categorize: Simplicity, Bugs, Conventions
   - Save to `.ai/know/features/<feature>/review.md`
4. Present issues to user with confidence levels
5. User chooses: "Fix now", "Fix later", or "Proceed"
6. **Update review.md with resolutions**:
   - Mark which issues were fixed
   - Note which are deferred
   - Update with validation results

**Outputs**:
- `.ai/know/features/<feature>/review.md` - Quality review findings
- Fixed issues (if "Fix now" chosen)
- Graph validation results

---

### Phase 7: Summary

**Goal**: Document completion and update tracking

**Steps**:
1. **Update summary.md immediately**:
   - Document accomplishments
   - List modified files with descriptions
   - Note integration points
   - Identify follow-up tasks
   - Save to `.ai/know/features/<feature>/summary.md`
2. **Generate QA_STEPS.md immediately** for end-user testing:
   - Read overview.md (what was requested)
   - Read adrs.md (architectural decisions)
   - Read implementation.md (how it works)
   - Translate technical implementation into user-facing test steps
   - **CRITICAL: Human-only steps**:
     - Include ONLY tests requiring human judgment (UX, visual, usability, edge cases)
     - EXCLUDE machine-testable items (unit tests, API responses, function outputs)
     - Focus on user experience, visual correctness, workflow completeness
   - Create `.ai/know/features/<feature>/QA_STEPS.md` with:
     - Objective (user perspective)
     - Prerequisites (setup needed)
     - Numbered test steps with expected outcomes (human evaluation required)
     - Acceptance criteria (clear pass/fail from user perspective)
   - Use checkbox format for tracking during `/know:review`
3. **Update spec-graph immediately** (using **haiku agents**):
   - Mark feature status as **"review-ready"** in `meta.phases`
   - **Populate `meta.feature_specs.<feature>`** with:
     - `status`: "review-ready"
     - `phase`: Current phase (e.g., "Phase I (Foundation)")
     - `priority`: Feature priority (P0-P3)
     - `use_cases[]`: Array of use case objects with name, description, config
     - `testing{}`: Object with unit[], integration[], performance[] arrays
     - `security[]`: Array of security/privacy requirements
     - `monitoring[]`: Array of observability requirements
     - `performance{}`: Object with latency, cost, quality characteristics
   - Update code-graph with all new modules
   - **Validate both graphs**: `know validate`
   - Run gap-summary: `know -g .ai/spec-graph.json gap-summary`
4. **Update todo.md immediately with final status**:
   - Read `.ai/know/features/<feature>/todo.md`
   - Verify all implementation tasks are checked
   - Add final completion note at bottom:
     ```markdown
     ## Build Complete
     - [x] Implementation finished (Phase 5)
     - [x] Quality review passed (Phase 6)
     - [x] Summary and QA steps generated (Phase 7)
     - [ ] User testing (run `/know:review <feature>`)
     - [ ] Merge and archive (run `/know:done <feature>`)
     ```
5. **Sync .ai/ directory back to main repo immediately**:
   - Copy updated `.ai/` from worktree to main repo
   - This preserves all documentation and graph updates
   - Ensures main repo has latest feature docs
6. **Stay in worktree** - remain here until user runs `/know:done`
7. **Inform user**: "Feature ready for review in worktree. Run `/know:review <feature>` to test, or `/know:done` to merge and archive."

**Outputs**:
- `.ai/know/features/<feature>/summary.md` - Completion summary
- `.ai/know/features/<feature>/QA_STEPS.md` - End-user test instructions
- Updated `.ai/know/features/<feature>/todo.md` - Final status with next steps
- Updated spec-graph (feature marked **"review-ready"**)
- Validated graphs
- Worktree remains active with feature branch
- .ai/ directory synced to main repo

---

## Know Query Agents

**All graph queries use haiku agents for speed and cost efficiency:**

```
Task tool with:
  model: "haiku"
  subagent_type: "general-purpose"
  prompt: "Run this know command and return the output: know -g .ai/spec-graph.json deps feature:auth"
```

**Common know queries to launch as haiku agents:**
- `know -g .ai/spec-graph.json deps feature:<name>`
- `know -g .ai/spec-graph.json used-by feature:<name>`
- `know -g .ai/spec-graph.json gap-analysis feature:<name>`
- `know -g .ai/spec-graph.json gap-summary`
- `know -g .ai/code-graph.json list-type module`
- `know -g .ai/code-graph.json uses component:<name> --recursive`
- `know validate`

---

## File Structure Created

```
.ai/know/features/<feature>/
├── overview.md              # Requirements (from /know:add, updated during Phase 5)
├── todo.md                  # Task checklist (updated continuously, final status in Phase 7)
├── plan.md                  # Implementation plan (from /know:add)
├── qa/
│   ├── discovery.md         # Phase 1 Q&A
│   └── clarification.md     # Phase 3 Q&A
├── exploration.md           # Phase 2 findings
├── adrs.md                  # Phase 4+ Architecture Decision Records
├── implementation.md        # Phase 5 implementation notes (updated continuously)
├── review.md                # Phase 6 quality findings
├── summary.md               # Phase 7 completion summary
├── QA_STEPS.md              # Phase 7 end-user test steps
├── review-results.md        # From /know:review (test execution)
├── review-feedback.md       # From /know:review (summary of issues)
├── bugs/                    # From /know:review (structured bug tracking)
│   ├── 001-description.md
│   └── 002-description.md
├── changes/                 # From /know:review (structured change requests)
│   └── 001-description.md
└── plans/                   # From /know:review (implementation plans for fixes)
    └── review-fixes-YYYYMMDD.md
```

---

## Continuous Documentation Updates

**CRITICAL RULE**: Update feature docs IMMEDIATELY after completing work in each phase. Never batch updates or defer documentation.

| Phase | When | What to Update | How |
|-------|------|----------------|-----|
| **1: Discovery** | After Q&A complete | `qa/discovery.md`, `overview.md` | Add Q&A with implications; refine requirements with success criteria, constraints, out-of-scope |
| **2: Exploration** | After agent consolidation | `exploration.md` | Document patterns, list files, note conventions, identify similar features |
| **3: Clarification** | After answers collected | `qa/clarification.md`, spec-graph | Add Q&A with decisions; update graph if new requirements discovered |
| **4: Architecture** | After user approval | `adrs.md`, spec-graph | Create ADR-NNN with decision, alternatives, consequences; add components/operations/references to graph |
| **5: Implementation** | After EACH task/file | `todo.md`, `implementation.md`, `overview.md`, `adrs.md` | Mark todos complete one-by-one; log each code change; update requirements if evolved; add ADRs for pivots |
| **6: Review** | After agents report findings | `review.md` | Document issues by category with confidence; mark resolutions after user decides |
| **7: Summary** | After consolidating | `summary.md`, `QA_STEPS.md`, `todo.md`, spec-graph | Write accomplishments; generate human-only test steps (UX/visual/usability); add final status; update graph to review-ready |

**Key Principles**:
- ✅ Update immediately after completing work
- ✅ One task → one todo update (not batched)
- ✅ Each code change → implementation.md entry
- ✅ Each decision → ADR or Q&A entry
- ✅ Sync .ai/ to main repo at phase boundaries
- ❌ Never batch documentation updates
- ❌ Never defer "I'll document later"
- ❌ Never skip intermediate updates

---

## Example Usage

**Existing feature:**
```
User: /know:build user-authentication
Assistant: Found feature at .ai/know/user-authentication/
          Loading context from overview.md...
          Updating phase status to in-progress...

          === Phase 1: Discovery ===
          Let me clarify a few things about user authentication...
```

**Inline feature:**
```
User: /know:build "Add real-time notifications"
Assistant: Feature not found in .ai/know/
          Running /know:add real-time-notifications first...

          [/know:add completes]

          Feature scaffolded. Beginning 7-phase build workflow.

          === Phase 1: Discovery ===
          ...
```

---

## Notes

- **Structured workflow** ensures exploration before implementation
- **Know integration** ensures spec-graph and code-graph stay synchronized
- **Haiku agents** keep graph queries fast and cost-effective
- **User approval required** at key decision points (architecture, implementation)
- **Resumable** - Can pause and resume at any phase
- **Documentation-driven** - All decisions captured in `.ai/know/features/<feature>/`
- When complete, use `/know:done` to archive and mark in "done" phase

---
`r3`
