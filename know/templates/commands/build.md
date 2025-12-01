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

**Goal**: Build the feature following chosen architecture

**Steps**:
1. **Require explicit user approval**: "Ready to implement? [Yes/No]"
2. Read all relevant files from exploration phase
3. Follow chosen architecture strictly
4. Update progress continuously in `.ai/know/<feature>/todo.md`
5. Update phase status in spec-graph: `"status": "in-progress"` (using **haiku agent**)
6. As code is written, link modules to spec-graph components:
   - Add to code-graph: `know -g .ai/code-graph.json add module <name> {...}`
   - Link via product-component references
7. Track implementation in `.ai/know/<feature>/implementation.md`

**Outputs**:
- Implemented code files
- Updated `.ai/know/<feature>/todo.md` with progress
- Updated `.ai/know/<feature>/implementation.md` with notes
- Updated code-graph with new modules
- Phase status: "in-progress" in spec-graph

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

**Goal**: Document completion and update tracking

**Steps**:
1. Document accomplishments
2. List modified files
3. Note integration points
4. Suggest follow-up tasks
5. **Update spec-graph** (using **haiku agents**):
   - Mark feature phase as "complete" (or move to "done" if fully deployed)
   - Update code-graph with all new modules
   - Validate both graphs
   - Run gap-summary: `know -g .ai/spec-graph.json gap-summary`
6. Save summary to `.ai/know/<feature>/summary.md`
7. **Offer**: "Run /know:done to archive this feature? [Yes/No]"

**Outputs**:
- `.ai/know/<feature>/summary.md` - Completion summary
- Updated spec-graph (feature marked complete/done)
- Validated graphs
- Optional: Feature archived via /know:done

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
└── summary.md               # Phase 7 completion summary
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
- When complete, use `/know:done` to archive and mark in "done" phase
