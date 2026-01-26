---
name: Know: Build Feature (8-Phase Workflow)
description: Structured 8-phase workflow for building features with discovery, exploration, design, experiments, implementation, and review
category: Know
tags: [know, build, feature-dev, workflow]
---

**Main Objective**

Guide feature development through a structured 8-phase workflow adapted from Claude Code's feature-dev plugin, integrated with the know ecosystem for spec-graph tracking and documentation.

**Prerequisites**
- Activate the know-tool skill for graph operations

**Auto-creates**: `contract.yaml` if missing, sets baseline when moving to in-progress

**Exploration Strategy**
- **Use parallel agents** throughout this workflow for speed and depth
- **Explore agent**: Discovers codebase nuances, patterns, and perspectives (use `thoroughness: "medium"` or `"very thorough"`)
- **Custom Task agents**: Create specialized agents with specific objectives
- **Launch in parallel**: Use SINGLE message with multiple Task tool calls to run agents concurrently
- Phases 2, 4, and 7 explicitly require parallel agent launches

**Entry Points**

1. **Existing feature**: `/know:build existing-feature` (directory exists at `.ai/know/features/existing-feature/`)
2. **Inline feature**: `/know:build "Add user authentication"` (no directory yet)

**Initialization Logic**

```
IF feature directory exists (.ai/know/features/<feature>/):
  → Load context from overview.md, notes.md, plan.md
  → Load requirements from spec-graph: know req list <feature>
  → Verify feature exists in spec-graph.json
  → Update meta.phases status to "in-progress"
  → Proceed to Phase 1

ELSE (inline feature description or non-existent feature):
  → Delegate to /know:add to scaffold feature (creates requirements)
  → Wait for /know:add completion
  → Load created context
  → Proceed to Phase 1
```

---

## 8-Phase Workflow

### Phase 1: Discovery

**Goal**: Clarify requirements and constraints (and collect reference materials!)

**Steps**:
1. Read `.ai/know/features/<feature>/overview.md` if exists
2. **Check for existing `references.md`** - if exists, read it to understand research basis
3. Ask clarifying questions:
   - What are the success criteria?
   - What constraints exist?
   - What is out of scope?
   - Who are the users of this feature?
   - What are the edge cases?
   - **Are there reference materials?** (research papers, specs, API docs, RFCs, prior art)
4. **If user provides new references**, add to `.ai/know/features/<feature>/references.md`:
   ```markdown
   # References for <feature-name>

   ## Research Papers
   - [Title](URL) - Summary, key sections

   ## Specifications
   - [RFC/Spec](URL) - Summary, relevant sections

   ## API Documentation
   - [API Docs](URL) - Endpoints, authentication

   ## Prior Art
   - [Similar Implementation](URL) - What to learn from it
   ```
5. Update `.ai/know/features/<feature>/qa/discovery.md` with Q&A
6. Query spec-graph (using **haiku agents**):
   - `know -g .ai/spec-graph.json deps feature:<name>` - What does this feature depend on?
   - `know -g .ai/spec-graph.json used-by feature:<name>` - What depends on this feature?
   - Check if references exist: Look in spec-graph.json → references.documentation
7. Update `.ai/know/features/<feature>/overview.md` with refined requirements
8. **Add references to spec-graph if not already there** (see /know:add step 5)

**Outputs**:
- `.ai/know/features/<feature>/qa/discovery.md` - Discovery Q&A session
- `.ai/know/features/<feature>/references.md` - Reference materials (if provided)
- Updated `.ai/know/features/<feature>/overview.md`
- Updated spec-graph.json references section (if new refs provided)

---

### Phase 2: Codebase Exploration

**Goal**: Understand existing implementation patterns and architecture (and check for duplicates!)

**CRITICAL: Check for duplicates BEFORE exploring**

**Steps**:
1. **Check for duplicate functionality** (CRITICAL):

   **Search Strategy**:
   - Extract key concepts from feature name/description
   - Search for similar features in spec-graph
   - Search codebase for similar implementations
   - Search for related patterns/classes/functions

   ```bash
   # Example for "api-client" feature:
   # Search spec-graph
   know -g .ai/spec-graph.json list-type feature | grep -i "api\|client\|http"
   know -g .ai/spec-graph.json list-type component | grep -i "api\|client\|http"

   # Search codebase
   rg -i "api.*client|http.*client|request.*handler" --type py --type js -l
   rg "class.*(Api|Client|Http)|def.*(api|client|fetch)" --type py --type js -l
   ```

   **If potential duplicates found**:
   - Read the duplicate code/modules to understand what they do
   - Use AskUserQuestion to present findings:

   ```
   Question: "Found existing functionality that may overlap with <feature-name>:

   • <duplicate-1>: <description>
     Location: <file/module>
     Current usage: <where it's used>

   • <duplicate-2>: <description>
     Location: <file/module>
     Current usage: <where it's used>

   How would you like to proceed?"

   Options:
   1. "Reuse existing" - Use what's there, don't build new
   2. "Generalize existing" - Extend current code for both use cases
   3. "Replace existing" - Deprecate old, build new
   4. "Create separate" - Both needed, proceed with new
   ```

   **Based on user choice**:
   - **Reuse**: STOP workflow, document existing solution in overview.md, exit
   - **Generalize**: Continue exploration, note in plan.md to refactor existing code
   - **Replace**: Continue exploration, deprecate old implementation via `know deprecate <entity>`
   - **Create separate**: Continue exploration, add justification to plan.md

   **If no duplicates found**: Proceed to parallel exploration

2. **Launch multiple agents in parallel** (single message with multiple Task tool calls):
   - **Explore agent (thoroughness: "medium")**: Discover codebase nuances, patterns, and conventions
   - **Custom Task agents** (2-3 specialized agents):
     - Agent 1: "Find similar features and trace their data flows"
     - Agent 2: "Identify architecture patterns and component boundaries"
     - Agent 3: "Map UI/UX conventions and existing abstractions"
   - Launch ALL agents in a single message for true parallelism
3. **Know-enhanced exploration** (using **haiku agents**):
   - Query code-graph: `know -g .ai/code-graph.json list-type module`
   - Find related components via product-component references
   - Query: `know -g .ai/code-graph.json uses component:<name> --recursive`
4. **Spec-graph exploration** (using **haiku agents**):
   - Query related actions: `know -g .ai/spec-graph.json list-type action`
   - Find component dependencies
   - Check data-model references
5. **Consolidate findings** from all explorers (Explore + custom Task agents)
   - If duplicates were found and user chose "Generalize" or "Replace", include analysis of how to refactor
6. Save to `.ai/know/features/<feature>/exploration.md`
   - Include duplicate handling notes if applicable

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
4. Save to `.ai/know/features/<feature>/qa/clarification.md`
5. Update spec-graph if new requirements discovered (using **haiku agents**):
   - Add requirement entities if needed
   - Update feature description

**Outputs**:
- `.ai/know/features/<feature>/qa/clarification.md` - Clarification Q&A
- Updated spec-graph entities (if needed)

---

### Phase 4: Architecture Design

**Goal**: Design implementation approach with trade-off analysis

**CRITICAL: Launch custom Task agents in parallel for multiple perspectives**

**Steps**:
1. **Read `references.md`** if it exists - understand the research/spec basis for this feature
2. **Launch 3 custom Task agents in parallel** (single message with 3 Task tool calls):
   - **Agent 1 (Minimal changes)**: "Design architecture minimizing changes to existing code. Reuse components, avoid refactors. What's the quickest path? Reference: [references.md if exists]"
   - **Agent 2 (Clean architecture)**: "Design ideal architecture ignoring existing code. What's the cleanest, most maintainable approach following best practices from [references]?"
   - **Agent 3 (Pragmatic balance)**: "Design architecture balancing new patterns with existing code. What's the best trade-off? How closely should we follow the reference papers/specs?"
   - **CRITICAL**: Each agent should reference:
     - Research papers from `references.md` (if feature is research-based)
     - API specs/RFCs (if implementing standard)
     - Prior art implementations (what worked, what didn't)
   - Each agent should consult spec-graph and code-graph
   - Launch ALL 3 in a single message for true parallelism
3. **Know-enhanced architecture** - Each agent consults:
   - Spec-graph component dependencies (using **haiku agents**)
   - Data model references from spec-graph
   - Interface definitions
   - Existing component contracts
   - **Documentation references** from spec-graph.json → references.documentation
4. **Consolidate 3 proposals** with trade-off analysis (cost, risk, maintainability, time)
   - Include analysis of how closely design follows reference materials
   - Note any deviations from research papers/specs and why
5. **Present recommendation** to user with clear pros/cons
6. **Wait for explicit approval** before proceeding
7. Save chosen architecture to `.ai/know/features/<feature>/architecture/chosen.md`
   - Include section on "Alignment with References" if research-based
   - Document which parts follow the paper/spec exactly
   - Document intentional deviations and rationale
8. Save alternatives to `.ai/know/features/<feature>/architecture/alternatives.md`
9. **Update spec-graph** with architecture (using **haiku agents**, WITH CONFIRMATION):
   - Add/update component entities
   - Add operation entities
   - Link dependencies (feature → action → component → operation)
   - Add references (business_logic, data-models, tech-decisions)

**Outputs**:
- `.ai/know/features/<feature>/architecture/chosen.md` - Approved architecture
- `.ai/know/features/<feature>/architecture/alternatives.md` - Other options considered
- Updated spec-graph with architectural entities

---

### Phase 5: Experiments (if applicable)

**Goal**: Validate risky elements before committing to full implementation

**Gate**: This phase BLOCKS implementation until experiments pass or are explicitly skipped.

**Steps**:
1. **Check for experiments.md**: Read `.ai/know/features/<feature>/experiments.md`
   - If file doesn't exist or empty: Skip to Phase 6
   - If experiments exist: Continue with validation
2. **Present experiments to user**:
   ```
   This feature has N experiments that should be validated before implementation:

   1. <Experiment Name>
      Type: <type>
      Risk: <what goes wrong if skipped>
      Validation: <pass/fail criteria>

   2. ...

   Run experiments now? [Yes / Skip (accept risk)]
   ```
3. **If user chooses "Skip"**: Document in experiments.md under Results, proceed to Phase 6
4. **If user chooses "Yes"**: For each experiment:
   a. Implement minimal validation code (scope from experiment definition)
   b. Run validation against criteria
   c. **Ask user to confirm result**: "Experiment '<name>' - does this pass your validation? [Pass / Fail / Needs adjustment]"
   d. Record result in experiments.md
5. **Gate check**: If ANY experiment fails:
   - Present failures to user
   - Ask: "How to proceed? [Fix and retry / Skip (accept risk) / Abort build]"
   - If "Abort": Exit workflow, leave feature in current state
6. **Update experiments.md** with all results:
   ```markdown
   ## Results

   ### <Experiment Name>
   - **Status**: passed | failed | skipped
   - **Date**: YYYY-MM-DD
   - **Notes**: <what was learned>
   - **Artifacts**: <links to prototype code, if any>
   ```
7. **Clean up**: Move experiment code to `.ai/tmp/experiments/<feature>/` or delete if user prefers

**Outputs**:
- Updated `.ai/know/features/<feature>/experiments.md` with results
- Validation artifacts in `.ai/tmp/experiments/<feature>/` (optional)
- Gate cleared for implementation

---

### Phase 6: Implementation

**Goal**: Build the feature following chosen architecture

**Steps**:
1. **Require explicit user approval**: "Ready to implement? [Yes/No]"
2. Read all relevant files from exploration phase
3. Follow chosen architecture strictly
4. **Track progress using requirements** (NOT todo.md):
   - Before starting: Query requirements: `know req list <feature>`
   - As you complete each requirement:
     - `know req status requirement:<feature>-<key> in-progress` (when starting)
     - `know req status requirement:<feature>-<key> complete` (when done)
   - Example workflow:
     ```bash
     # Starting work on login validation
     know req status requirement:auth-login-validation in-progress
     # ... implement ...
     know req status requirement:auth-login-validation complete
     ```
   - Update status immediately after completing each requirement
5. Update phase status in spec-graph: `"status": "in-progress"` (using **haiku agent**)
6. As code is written, link modules to spec-graph components:
   - Add to code-graph: `know -g .ai/code-graph.json add module <name> {...}`
   - Link via product-component references
7. Track implementation notes in `.ai/know/features/<feature>/notes.md`
8. **Track observed changes for contract** (during/after implementation):
   - Track files created/modified during implementation
   - Track entities added to spec-graph
   - Update contract.yaml `observed` section with actual files/entities
   - This enables drift detection in Phase 8

**Outputs**:
- Implemented code files
- Updated requirement statuses in spec-graph (`know req list <feature>` shows progress)
- Updated `.ai/know/features/<feature>/notes.md` with implementation notes
- Updated code-graph with new modules
- Updated contract.yaml with observed files/entities
- Phase status: "in-progress" in spec-graph

---

### Phase 7: Quality Review

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
3. Present issues to user with confidence levels
4. User chooses: "Fix now", "Fix later", or "Proceed"
5. Save review to `.ai/know/features/<feature>/review.md`

**Outputs**:
- `.ai/know/features/<feature>/review.md` - Quality review findings
- Fixed issues (if "Fix now" chosen)
- Graph validation results

---

### Phase 8: Summary

**Goal**: Document completion and update tracking

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
   - Create `.ai/know/features/<feature>/QA_STEPS.md` with:
     - Objective (user perspective)
     - Prerequisites (setup needed)
     - Numbered test steps with expected outcomes
     - Acceptance criteria (clear pass/fail)
   - Use checkbox format for tracking during `/know:review`
   - **HUMAN-ONLY**: QA_STEPS must contain only manual human testing steps
   - **NO automated tests** (those go in test files, not QA_STEPS)
   - Focus on: UI flows, user experience, visual verification, edge cases requiring judgment
6. **Update spec-graph** (using **haiku agents**):
   - Mark feature phase as "complete" (or move to "done" if fully deployed)
   - Update code-graph with all new modules
   - Validate both graphs
   - Run gap-summary: `know -g .ai/spec-graph.json gap-summary`
7. Save summary to `.ai/know/features/<feature>/summary.md`
8. **Validate contract and calculate confidence**:
   - Run: `know validate-contracts -f <feature>`
   - Display validation status (verified/pending/drifted)
   - Display any discrepancies found
   - Display confidence score with contributing factors
   - If drifted: warn user to review before proceeding
9. **Inform user**: "Feature complete. Run `/know:review <feature>` to test, or `/know:done` to archive."

**Outputs**:
- `.ai/know/features/<feature>/summary.md` - Completion summary
- `.ai/know/features/<feature>/QA_STEPS.md` - End-user test instructions (human-only steps)
- Updated spec-graph (feature marked complete/done)
- Updated contract.yaml with validation results
- Validated graphs
- Ready for `/know:review` or `/know:done`

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
├── overview.md              # Requirements (from /know:add)
├── notes.md                 # Freeform working notes (replaces todo.md)
├── plan.md                  # Implementation plan (from /know:add)
├── contract.yaml            # Feature contract: declared vs observed (from /know:add)
├── experiments.md           # Validation experiments (from /know:add, results from Phase 5)
├── qa/
│   ├── discovery.md         # Phase 1 Q&A
│   └── clarification.md     # Phase 3 Q&A
├── exploration.md           # Phase 2 findings
├── architecture/
│   ├── chosen.md            # Phase 4 approved design
│   └── alternatives.md      # Phase 4 other options
├── implementation.md        # Phase 6 implementation notes
├── review.md                # Phase 7 quality findings
├── summary.md               # Phase 8 completion summary
├── QA_STEPS.md              # Phase 8 end-user test steps (human-only, NO automation)
├── review-results.md        # From /know:review (test execution)
├── review-feedback.md       # From /know:review (summary of issues)
├── bugs/                    # From /know:review (structured bug tracking)
│   ├── 001-description.md
│   └── 002-description.md
├── changes/                 # From /know:review (structured change requests)
│   └── 001-description.md
└── plans/                   # From /know:review (implementation plans for fixes)
    └── review-fixes-YYYYMMDD.md

# Progress is tracked via requirements in spec-graph.json:
#   - meta.requirements[feature-key].status
#   - Query with: know req list <feature>
```

---

## Example Usage

**Existing feature:**
```
User: /know:build user-authentication
Assistant: Found feature at .ai/know/features/user-authentication/
          Loading context from overview.md...
          Updating phase status to in-progress...

          === Phase 1: Discovery ===
          Let me clarify a few things about user authentication...
```

**Inline feature:**
```
User: /know:build "Add real-time notifications"
Assistant: Feature not found in .ai/know/features/
          Running /know:add real-time-notifications first...

          [/know:add completes]

          Feature scaffolded. Beginning 7-phase build workflow.

          === Phase 1: Discovery ===
          ...
```

---

## Notes

- **CRITICAL: Reference materials tracking** - Always capture research papers, specs, API docs
  - Ask for references in Phase 1 (Discovery)
  - Store in `references.md` for human readability
  - Add to spec-graph for machine queryability
  - Reference materials inform architecture design (Phase 4)
  - Document alignment/deviations in architecture docs
- **CRITICAL: Duplicate detection in Phase 2** - Always check for existing functionality before building
  - Prevents wasted effort reimplementing what already exists
  - Encourages code reuse and refactoring over duplication
  - Gives user control: reuse, generalize, replace, or create separate
- **Structured workflow** prevents jumping to code prematurely
- **Know integration** ensures spec-graph and code-graph stay synchronized
- **Haiku agents** keep graph queries fast and cost-effective
- **User approval required** at key decision points (architecture, implementation, duplicates)
- **Resumable** - Can pause and resume at any phase
- **Documentation-driven** - All decisions captured in `.ai/know/features/<feature>/`
  - `references.md` - Research papers, specs, API docs, prior art
  - `qa/discovery.md` - Discovery questions and answers
  - `exploration.md` - Codebase understanding
  - `architecture/chosen.md` - Selected design with reference alignment
- When complete, use `/know:done` to archive and mark in "done" phase
- **Experiments gate implementation** - If experiments.md exists, Phase 5 validates risky elements before code
  - User must confirm experiment results pass
  - Can skip with explicit risk acceptance
  - Failed experiments block build until resolved or skipped

