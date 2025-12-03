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

**Entry Points**

1. **Existing feature**: `/know:build existing-feature` (directory exists at `.ai/know/existing-feature/`)
2. **Inline feature**: `/know:build "Add user authentication"` (no directory yet)

**Initialization Logic**

```
IF feature directory exists (.ai/know/<feature>/):
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
1. Read `.ai/know/<feature>/overview.md` if exists
2. Ask clarifying questions:
   - What are the success criteria?
   - What constraints exist?
   - What is out of scope?
   - Who are the users of this feature?
   - What are the edge cases?
3. Update `.ai/know/<feature>/qa/discovery.md` with Q&A
4. Query spec-graph (using **haiku agents**):
   - `know -g .ai/spec-graph.json deps feature:<name>` - What does this feature depend on?
   - `know -g .ai/spec-graph.json used-by feature:<name>` - What depends on this feature?
5. Update `.ai/know/<feature>/overview.md` with refined requirements

**Outputs**:
- `.ai/know/<feature>/qa/discovery.md` - Discovery Q&A session
- Updated `.ai/know/<feature>/overview.md`

---

### Phase 2: Codebase Exploration

**Goal**: Understand existing implementation patterns and architecture

**Steps**:
1. Launch 2-3 `code-explorer` agents in parallel (Task tool):
   - Explore similar features in codebase
   - Identify architecture patterns
   - Find UI/UX conventions
   - Trace data flows
2. **Know-enhanced exploration** (using **haiku agents**):
   - Query code-graph: `know -g .ai/code-graph.json list-type module`
   - Find related components via product-component references
   - Query: `know -g .ai/code-graph.json uses component:<name> --recursive`
3. **Spec-graph exploration** (using **haiku agents**):
   - Query related actions: `know -g .ai/spec-graph.json list-type action`
   - Find component dependencies
   - Check data-model references
4. Consolidate findings from all explorers
5. Save to `.ai/know/<feature>/exploration.md`

**Outputs**:
- `.ai/know/<feature>/exploration.md` - Consolidated codebase understanding
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
4. Save to `.ai/know/<feature>/qa/clarification.md`
5. Update spec-graph if new requirements discovered (using **haiku agents**):
   - Add requirement entities if needed
   - Update feature description

**Outputs**:
- `.ai/know/<feature>/qa/clarification.md` - Clarification Q&A
- Updated spec-graph entities (if needed)

---

### Phase 4: Architecture Design

**Goal**: Design implementation approach with trade-off analysis

**Steps**:
1. Launch 3 `code-architect` agents in parallel (Task tool):
   - **Agent 1**: Minimal changes approach
   - **Agent 2**: Clean architecture approach
   - **Agent 3**: Pragmatic balance approach
2. **Know-enhanced architecture** - Each agent consults:
   - Spec-graph component dependencies (using **haiku agents**)
   - Data model references from spec-graph
   - Interface definitions
   - Existing component contracts
3. Consolidate 3 proposals with trade-off analysis
4. Present recommendation to user
5. **Wait for explicit approval** before proceeding
6. Save chosen architecture to `.ai/know/<feature>/architecture/chosen.md`
7. Save alternatives to `.ai/know/<feature>/architecture/alternatives.md`
8. **Update spec-graph** with architecture (using **haiku agents**, WITH CONFIRMATION):
   - Add/update component entities
   - Add operation entities
   - Link dependencies (feature → action → component → operation)
   - Add references (business_logic, data-models, tech-decisions)

**Outputs**:
- `.ai/know/<feature>/architecture/chosen.md` - Approved architecture
- `.ai/know/<feature>/architecture/alternatives.md` - Other options considered
- Updated spec-graph with architectural entities

---

### Phase 5: Implementation

**Goal**: Build the feature following chosen architecture in a git worktree

**Git Worktree Setup**:
1. **Detect current location and worktree status**:
   ```bash
   MAIN_WORKTREE=$(git worktree list | head -1 | awk '{print $1}')
   CURRENT_TOPLEVEL=$(git rev-parse --show-toplevel)
   CURRENT_BRANCH=$(git branch --show-current)
   ```
2. **Intelligent worktree handling**:
   - **If in main repo**: Proceed to step 3
   - **If in a worktree**:
     - Extract feature name from target (e.g., "user-auth" from `/know:build user-auth`)
     - Check if current branch matches `feature/<feature-name>`
     - **If match**: Reuse current worktree (already in the right place!)
     - **If no match**: Switch to main repo automatically, then proceed to step 3
       ```bash
       cd $MAIN_WORKTREE
       ```
3. **Detect main repository location**: Get absolute path to main repo (e.g., `/path/to/abc/`)
4. **Determine worktree path**: Sibling directory with pattern `<repo-name>-<feature-name>/`
   - Example: Main repo at `/path/to/abc/` → Worktree at `/path/to/abc-user-auth/`
5. **Create or reuse git worktree**:
   ```bash
   # Check if worktree already exists
   if git worktree list | grep -q "feature/$FEATURE_NAME"; then
     # Worktree exists - switch to it
     cd ../<repo-name>-<feature-name>
   else
     # Create new worktree
     git worktree add ../<repo-name>-<feature-name> -b feature/<feature-name>
     cd ../<repo-name>-<feature-name>
   fi
   ```
6. **Copy .ai/ directory** to worktree if not already present:
   ```bash
   if [ ! -d ".ai" ]; then
     cp -r $MAIN_WORKTREE/.ai .
   fi
   ```

**Implementation Steps**:
1. **Require explicit user approval**: "Ready to implement? [Yes/No]"
2. **Create and switch to worktree** (see Git Worktree Setup above)
3. Read all relevant files from exploration phase
4. Follow chosen architecture strictly
5. **Track and update todo items as you work**:
   - Before starting each task: Read `.ai/know/<feature>/todo.md` to see current checklist
   - Identify which checkbox corresponds to the work you're about to do
   - As you complete each task, edit todo.md to mark it complete
   - Format: Change `- [ ] Task name` to `- [x] Task name`
   - Example: `- [ ] 1. Implement auth handler` becomes `- [x] 1. Implement auth handler`
   - Update immediately after completing each task (don't batch updates)
6. Update phase status in spec-graph: `"status": "in-progress"` (using **haiku agent**)
7. As code is written, link modules to spec-graph components:
   - Add to code-graph: `know -g .ai/code-graph.json add module <name> {...}`
   - Link via product-component references
8. Track implementation in `.ai/know/<feature>/implementation.md`
9. Commit changes as you go in the worktree branch

**Outputs**:
- Git worktree created at `../<repo-name>-<feature-name>/`
- Feature branch: `feature/<feature-name>`
- Implemented code files (in worktree)
- Updated `.ai/know/<feature>/todo.md` with progress
- Updated `.ai/know/<feature>/implementation.md` with notes
- Updated code-graph with new modules
- Phase status: "in-progress" in spec-graph
- Git commits in feature branch

---

### Phase 6: Quality Review

**Goal**: Validate correctness, quality, and integration

**Steps**:
1. Launch 3 `code-reviewer` agents in parallel (Task tool):
   - **Reviewer 1**: Simplicity/DRY/elegance focus
   - **Reviewer 2**: Bugs/correctness focus
   - **Reviewer 3**: Conventions/abstractions focus
   - Report only high-confidence issues (≥80% confidence)
2. **Know-enhanced validation** (using **haiku agents**):
   - Gap analysis: `know -g .ai/spec-graph.json gap-analysis feature:<name>`
   - Verify all component dependencies satisfied
   - Check code-graph completeness
   - Validate both graphs: `know validate`
3. Present issues to user with confidence levels
4. User chooses: "Fix now", "Fix later", or "Proceed"
5. Save review to `.ai/know/<feature>/review.md`

**Outputs**:
- `.ai/know/<feature>/review.md` - Quality review findings
- Fixed issues (if "Fix now" chosen)
- Graph validation results

---

### Phase 7: Summary

**Goal**: Document completion and prepare for review

**Steps**:
1. Document accomplishments
2. List modified files
3. Note integration points
4. Suggest follow-up tasks
5. **Generate QA_STEPS.md** for end-user testing:
   - Read overview.md (what was requested)
   - Read architecture/chosen.md (what was built)
   - Read implementation.md (how it works)
   - Translate technical implementation into user-facing test steps
   - Create `.ai/know/<feature>/QA_STEPS.md` with:
     - Objective (user perspective)
     - Prerequisites (setup needed)
     - Numbered test steps with expected outcomes
     - Acceptance criteria (clear pass/fail)
   - Use checkbox format for tracking during `/know:review`
6. **Update spec-graph** (using **haiku agents**):
   - Mark feature status as **"review-ready"** (not "complete" or "done")
   - Update code-graph with all new modules
   - Validate both graphs
   - Run gap-summary: `know -g .ai/spec-graph.json gap-summary`
7. Save summary to `.ai/know/<feature>/summary.md`
8. **Sync .ai/ directory back to main repo**:
   - Copy updated `.ai/` from worktree to main repo
   - This preserves all documentation and graph updates
9. **Stay in worktree** - Don't switch back to main repo yet
10. **Inform user**: "Feature ready for review in worktree. Run `/know:review <feature>` to test, or `/know:done` after review to merge and archive."

**Outputs**:
- `.ai/know/<feature>/summary.md` - Completion summary
- `.ai/know/<feature>/QA_STEPS.md` - End-user test instructions
- Updated spec-graph (feature marked **"review-ready"**)
- Validated graphs
- Worktree remains active with feature branch
- .ai/ directory synced to main repo
- Ready for `/know:review` or `/know:done`

**Phase Status Lifecycle**:
```
incomplete → in-progress → review-ready → [/know:done] → done
```

**Notes**:
- **review-ready** is the terminal state for /know:build
- Feature stays in worktree for review/testing
- Use `/know:done` after successful review to:
  - Merge feature branch
  - Remove worktree
  - Move phase status to "done"
  - Archive feature directory

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
.ai/know/<feature>/
├── overview.md              # Requirements (from /know:add)
├── todo.md                  # Task checklist (from /know:add)
├── plan.md                  # Implementation plan (from /know:add)
├── qa/
│   ├── discovery.md         # Phase 1 Q&A
│   └── clarification.md     # Phase 3 Q&A
├── exploration.md           # Phase 2 findings
├── architecture/
│   ├── chosen.md            # Phase 4 approved design
│   └── alternatives.md      # Phase 4 other options
├── implementation.md        # Phase 5 implementation notes
├── review.md                # Phase 6 quality findings
├── summary.md               # Phase 7 completion summary
├── QA_STEPS.md              # Phase 7 end-user test steps
├── review-results.md        # From /know:review (test execution)
└── review-feedback.md       # From /know:review (issues found)
```

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

- **Structured workflow** prevents jumping to code prematurely
- **Know integration** ensures spec-graph and code-graph stay synchronized
- **Haiku agents** keep graph queries fast and cost-effective
- **User approval required** at key decision points (architecture, implementation)
- **Resumable** - Can pause and resume at any phase
- **Documentation-driven** - All decisions captured in `.ai/know/<feature>/`
- **Git worktree handling**:
  - Can run from main repo OR from any worktree
  - If in wrong worktree, auto-switches to main and creates new worktree
  - If in correct worktree (matching feature branch), reuses it
  - Each feature gets its own worktree at `../<repo-name>-<feature>/`
  - Worktrees are cleaned up by `/know:done` after merge
- When complete, use `/know:done` to archive and mark in "done" phase
