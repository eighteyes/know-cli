---
name: Know: Add Feature
description: 5-step workflow to add a feature to spec-graph with HITL clarification
category: Know
tags: [know, feature, overview]
---

**Prerequisites**
- Activate the know-tool skill for graph operations

**Workflow**

## 1. Identify
- Extract feature name from conversation or prompt user if not provided
- Verify uniqueness in `.ai/know/features/`
- Use kebab-case for feature names

## 2. Check for Duplicates (CRITICAL)

**Before adding a new feature, search for existing similar functionality:**

### Search Strategy
Use parallel searches to find potential duplicates:

```bash
# Search for similar feature names in spec-graph
know -g .ai/spec-graph.json list-type feature | grep -i "<keyword>"

# Search codebase for similar implementations
rg -i "<keyword>" --type py --type js --type ts -l

# Search for similar patterns/functions
rg "class.*<Keyword>|function.*<keyword>|def.*<keyword>" --type py --type js
```

### Examples
If adding "api-client" feature:
- Search for: "api", "client", "http", "request", "fetch"
- Check for: existing API clients, HTTP wrappers, request handlers

If adding "authentication" feature:
- Search for: "auth", "login", "session", "token", "credential"
- Check for: existing auth modules, login flows, session management

If adding "database-sync" feature:
- Search for: "sync", "database", "db", "persist", "save"
- Check for: existing sync mechanisms, database handlers

### Ask User About Duplicates

**If potential duplicates found**, use AskUserQuestion:

```
Question: "Found existing functionality that may overlap with <feature-name>:

• <duplicate-1>: <brief-description>
  Location: <file-path>

• <duplicate-2>: <brief-description>
  Location: <file-path>

How would you like to proceed?"

Options:
1. "Reuse existing implementation" - Use what's already there
   Description: Cancel new feature, document existing solution instead

2. "Generalize existing code" - Extend current implementation
   Description: Refactor existing code to support both use cases

3. "Replace existing code" - Deprecate old, implement new
   Description: Mark old implementation for removal, proceed with new feature

4. "Create separate implementation" - Both are needed
   Description: Proceed with new feature, document why both exist

5. "Extend existing feature" - Add to existing feature
   Description: Move feature to pending with changes-planned status, append extension context
```

**Based on user choice**:
- **Reuse**: Cancel add workflow, create documentation pointing to existing code
- **Generalize**: Proceed but mark in overview.md that this extends `<existing>`
- **Replace**: Proceed, add deprecation requirement for old implementation via `know deprecate`
- **Create separate**: Proceed, add justification to overview.md
- **Extend**: Enter Extension Workflow (see Section 2b below)

### If No Duplicates Found
Proceed to Clarify step.

## 2b. Extension Workflow (NEW - triggered by "Extend existing feature" choice)

**Triggered when**: User selects "Extend existing feature" from duplicate detection

### Steps:

**1. Identify Feature**: Ask user which feature to extend (or auto-select if only one match)

**2. Validate**:
- Verify feature directory exists: `ls -d .ai/know/features/<extending_feature_name>/`
- Check feature not archived: Read spec-graph.json → meta.archived_features
- Verify feature in spec-graph: `know -g .ai/spec-graph.json get feature:<extending_feature_name>`
- If feature is archived: Error - "Cannot extend archived feature. Consider creating new feature instead."

**3. Load Current State**:
- Read overview.md, notes.md, plan.md
- Get current phase and status from spec-graph
- Check existing requirements: `know req list <extending_feature_name>`

**4. Clarify Extension** (HITL):
Ask user essential questions using AskUserQuestion:
- What is changing? (1-2 sentence description)
- Why is this change needed? (motivation, problem solved)
- Any new components needed? (optional)
- Any new reference materials? (research papers, specs, docs)

**5. Update Files**:

**overview.md** (append at end before any footer):
```markdown

---

## Extensions

### Extension: YYYY-MM-DD

**Change Description**: <extension_description>

**Motivation**: <extension_reason>

**New Components**: <extension_components or "To be determined during /know:build">

**Phase**: Moved to pending (from <previous_phase>)
**Status**: changes-planned

**Previous Status**: <previous_status> in phase <previous_phase>
```

**requirements** (add via CLI):
```bash
# Create extension requirements in spec-graph
know req add <extending_feature_name> ext-<slug>-main --name "Extension: <brief_description>" \
  --description "<extension_description>"

# Add specific tasks as requirements
know req add <extending_feature_name> ext-<slug>-integration --name "Integration: update components" \
  --description "Update existing components for extension compatibility"

know req add <extending_feature_name> ext-<slug>-testing --name "Testing: verify compatibility" \
  --description "Test compatibility with existing functionality"

know req add <extending_feature_name> ext-<slug>-docs --name "Docs: update documentation" \
  --description "Update documentation for extension"
```

**notes.md** (append extension context):
```markdown

---

## Extension: YYYY-MM-DD

**Context**: <extension_description>

**Motivation**: <extension_reason>

**Requirements created**: See `know req list <extending_feature_name>`
```

**plan.md** (prepend at top):
```markdown
# Plan: <feature-name> (EXTENSION IN PROGRESS)

> **Extension Planned**: YYYY-MM-DD
>
> **Changes**: <extension_description>
>
> **Status**: Moved to pending/changes-planned for re-planning
>
> **Original Plan Below** - Review and update during /know:build

---

[Rest of original plan.md content]
```

**contract.yaml**: DO NOT MODIFY (preserve baseline timestamp and commit)

**references.md** (if extension_references provided, append):
```markdown

---

## Extension References (Added YYYY-MM-DD)

### <Category: Research Papers / Specifications / API Documentation / Prior Art>
- [Title](URL)
  - Summary
  - Relevant sections/endpoints
```

**6. Move Phase**: Execute command:
```bash
know -g .ai/spec-graph.json phases move feature:<extending_feature_name> pending --status changes-planned
```

**7. Confirm**: Show summary message:
```
Feature extended successfully!

Feature: <extending_feature_name>
Phase: pending → changes-planned
Extensions recorded in overview.md
Requirements created: `know req list <extending_feature_name>`

Next steps:
1. Review updated plan.md and notes.md
2. Check extension requirements: `know req list <extending_feature_name>`
3. Run /know:build <extending_feature_name> to begin implementation
4. Use /know:connect to validate graph coverage

Files updated:
- .ai/know/features/<extending_feature_name>/overview.md (Extensions section added)
- .ai/know/features/<extending_feature_name>/notes.md (Extension context appended)
- .ai/know/features/<extending_feature_name>/plan.md (Extension notice added)
- .ai/spec-graph.json (Phase: pending, Status: changes-planned, requirements added)
```

**After extension complete**:
- Skip steps 3-7 of normal /know:add workflow
- Do NOT create new feature directory
- Do NOT register as new feature in spec-graph
- Do NOT run /know:connect (feature already connected)

## 3. Clarify (HITL)
Ask user essential questions using AskUserQuestion:
- What does this feature do? (1-2 sentence description)
- Which user(s) need this feature? (from spec-graph users, or new ones)
- Which objective(s) does this feature support? (from spec-graph objectives, or new ones)
- **What components are needed?** (data handlers, processors, managers, services)
- **What actions does the user perform?** (verbs: upload, configure, view, export)
- **What interfaces are involved?** (screens, API endpoints, CLI commands)
- **What requirements/constraints exist?** (performance, security, compatibility)
- **Are there reference materials?** (research papers, RFCs, API docs, specs, prior art)
- **What needs validation before full build?** (risky integrations, novel tech, UI prototypes)

**CONTRACT QUESTIONS** (for drift detection):
- **What files will be created?** (glob patterns: `src/auth/*.py`, `tests/test_auth.py`)
- **What files will be modified?** (existing files that need changes)
- **What entities will be created?** (component:auth-handler, action:user-login)
- **What existing entities does this depend on?** (component:validation-engine)

**Goal**: Gather enough to populate spec-graph with feature's full context. Not every question needs an answer - capture what's KNOWN now, refine during `/know:build`.

**Surface Assumptions**:
Before proceeding, state any assumptions about scope, approach, or integration.
For each assumption: confidence ≥95% → state and proceed. <95% → ask user.
*Assumption economics: -5 if wrong, +1 if right, 0 if ask.*

**CRITICAL: Capture reference materials**

If user provides references, collect:
- **Research Papers**: ArXiv links, DOIs, paper titles
- **Specifications**: RFCs, W3C specs, API documentation
- **Technical Docs**: Official documentation, architecture guides
- **Prior Art**: GitHub repos, blog posts, tutorials
- **Standards**: IEEE, ISO, industry standards

**Format for references**:
```
Title: <descriptive name>
Type: <research-paper|rfc|api-doc|spec|github|blog|standard>
URL: <link>
Summary: <1-2 sentence summary of relevance>
```

**CRITICAL: Capture experiments needed**

If the feature involves risk, novel tech, or untested assumptions, capture experiments:

**Experiment types**:
- **Tech Integration**: Novel API, unfamiliar library, uncertain compatibility
- **UI Prototype**: User flow validation, interaction patterns, layout feasibility
- **Performance**: Load handling, latency, resource consumption
- **Assumption Validation**: Unverified beliefs about how something works

**Format for experiments**:
```
Name: <short experiment name>
Type: <tech-integration|ui-prototype|performance|assumption>
Risk: <what goes wrong if skipped>
Validation: <pass/fail criteria>
Scope: <minimal effort to validate>
```

**If no experiments needed**: State "No high-risk elements identified" and proceed.

**Examples**:
```
Title: Attention Is All You Need (Transformer Architecture)
Type: research-paper
URL: https://arxiv.org/abs/1706.03762
Summary: Original transformer architecture paper - foundation for implementation

Title: RFC 7519 - JSON Web Tokens
Type: rfc
URL: https://datatracker.ietf.org/doc/html/rfc7519
Summary: JWT specification for token-based authentication

Title: Anthropic Claude API Documentation
Type: api-doc
URL: https://docs.anthropic.com/claude/reference
Summary: Official API reference for Claude integration
```

## 3b. Define Requirements (NEW)

**Goal**: Break feature into testable requirements that replace todo.md

**Steps**:
1. Based on Clarify answers, identify discrete requirements:
   - Each action becomes a requirement
   - Each component responsibility becomes a requirement
   - Each constraint becomes a requirement
2. Ask user to confirm/modify requirements list using AskUserQuestion
3. For each requirement:
   - Generate kebab-case key: `{feature}-{requirement-slug}`
   - Write name (1 line)
   - Write description (testable specification)
4. Link requirements to components/actions identified in Clarify

**Output**:
- List of requirement entities to create in Register step
- Each requirement linked to implementation entities

**Example Requirements**:
```
Requirement: auth-login-validation
Name: "Login form validates credentials"
Description: "User credentials must be validated against auth service before session creation"
Links to: component:auth-form, action:submit-login

Requirement: auth-session-persistence
Name: "Sessions persist across page reload"
Description: "User session token stored in secure cookie, validated on each request"
Links to: component:session-store
```

## 4. Scaffold
- Create directory `.ai/know/features/<feature-name>/`
- Create files from templates:
  - `overview.md` - Populated with answers from Clarify step (+ duplicate handling notes if applicable)
  - `references.md` - **Reference materials section** (research papers, docs, specs, prior art)
  - `experiments.md` - **Validation experiments** (if any identified in Clarify, otherwise omit)
  - `notes.md` - **Freeform working notes** (replaces todo.md)
  - `plan.md` - Empty implementation plan
  - `spec.md` - Empty spec file
  - `contract.yaml` - **Feature contract** (declared intent, files, entities, actions)
- Replace `{feature_name}` placeholder in all templates
- **NOTE**: Requirements are tracked in spec-graph.json, NOT in markdown files

**Create contract.yaml for feature tracking and drift detection**:

```yaml
version: 1
feature: <feature-name>
created: <ISO timestamp>
baseline_commit: <current HEAD or null>

declared:  # populated during /know:add Clarify step
  actions:
    - entity: action:<action-name>
      description: "<description from clarify>"
      verified: false
  files:
    creates: ["<glob-patterns-from-clarify>"]
    modifies: ["<glob-patterns-from-clarify>"]
  entities:
    creates: [<entity-ids-from-clarify>]
    depends_on: [<dependency-entity-ids-from-clarify>]

observed:  # populated during /know:build
  files: {created: [], modified: [], deleted: []}
  entities: {created: [], modified: []}
  verified_date: null
  verified_commit: null
  commit_range: null

validation:
  status: pending  # pending | verified | drifted
  discrepancies: []

confidence:
  score: 100
  factors: []
  manual_override: null

watch:  # paths to monitor for changes
  paths: []
  exclude: []
```

The `contract.yaml` bridges declared intent with observed reality:
- **declared**: What you plan to create (populated from Clarify step)
- **observed**: What was actually created (populated during /know:build)
- **validation**: Drift detection status and discrepancies
- **confidence**: Calculated score based on age, drift, verification
- **watch**: Glob patterns for files this feature owns

**CLI commands for contracts**:
- `know validate-contracts -f <name>` - Check declared vs observed
- `know impact <entity-or-file>` - Show features affected by changes
- `know contract <name>` - Display contract summary
- `know contract <name> --show` - Show full YAML
- `know contract <name> --confidence` - Show confidence calculation
- `know migrate-contracts --all` - Migrate old config.json files

**Populate experiments.md** (if experiments identified)

Create `.ai/know/features/<feature-name>/experiments.md`:

```markdown
# Experiments for <feature-name>

> Run these experiments during /know:build BEFORE full implementation.
> Gate build on experiment success.

## <Experiment Name>
- **Type**: <tech-integration|ui-prototype|performance|assumption>
- **Risk**: <consequence of skipping>
- **Validation**: <pass/fail criteria>
- **Scope**: <minimal implementation>
- **Status**: pending

## Results
<!-- Populated during /know:build -->
```

**CRITICAL: Populate references.md**

If user provided reference materials, create `.ai/know/features/<feature-name>/references.md`:

```markdown
# References for <feature-name>

## Research Papers
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
  - Original transformer architecture paper - foundation for implementation
  - Key sections: 3.2 (Multi-head attention), 5.4 (Training details)

## Specifications
- [RFC 7519 - JSON Web Tokens](https://datatracker.ietf.org/doc/html/rfc7519)
  - JWT specification for token-based authentication
  - Sections: 4.1 (Registered claims), 7 (Security considerations)

## API Documentation
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)
  - Official API reference for Claude integration
  - Endpoints: /v1/messages, /v1/complete

## Prior Art
- [similar-project](https://github.com/user/repo)
  - Example implementation of similar feature
  - See: src/feature.py for approach

## Implementation Notes
- Key algorithms from papers implemented in: <files>
- Deviations from spec: <list any intentional differences>
- Open questions: <anything unclear from references>
```

**Also update overview.md** to include:
```markdown
## References
See [references.md](references.md) for research papers, specifications, and documentation.
```

## 5. Register
Populate spec-graph with ALL entities identified during Clarify and Define Requirements:

**5a. Add feature**:
```bash
know -g .ai/spec-graph.json add feature <name> '{"name":"...","description":"..."}'
know -g .ai/spec-graph.json phases add pending feature:<name>
```

**5b. Link to users and objectives**:
```bash
know -g .ai/spec-graph.json link user:<name> objective:<name>       # if new user→objective
know -g .ai/spec-graph.json link objective:<name> feature:<name>    # for each objective
```

**5c. Add requirements** (from Define Requirements step):
```bash
# For each requirement from step 3b:
know -g .ai/spec-graph.json req add <feature> <key> --name "..." --description "..."

# Link requirements to implementation entities:
know -g .ai/spec-graph.json link requirement:<feature>-<key> component:<target>
know -g .ai/spec-graph.json link requirement:<feature>-<key> action:<target>
```

**Example**:
```bash
# Add requirements for auth feature
know -g .ai/spec-graph.json req add auth login-validation \
  --name "Login form validates credentials" \
  --description "User credentials must be validated against auth service"

know -g .ai/spec-graph.json req add auth session-persistence \
  --name "Sessions persist across page reload" \
  --description "Session token stored in secure cookie"

# Link to implementation
know -g .ai/spec-graph.json link requirement:auth-login-validation component:auth-form
know -g .ai/spec-graph.json link requirement:auth-session-persistence component:session-store
```

**5d. Add components** (if identified during Clarify):
```bash
know -g .ai/spec-graph.json add component <name> '{"name":"...","description":"..."}'
know -g .ai/spec-graph.json link feature:<feature> component:<name>
```

**5e. Add actions** (if user flows identified):
```bash
know -g .ai/spec-graph.json add action <name> '{"name":"...","description":"..."}'
know -g .ai/spec-graph.json link feature:<feature> action:<name>
know -g .ai/spec-graph.json link action:<name> component:<name>     # if component known
```

**5f. Add interfaces** (if UI/API touchpoints identified):
```bash
know -g .ai/spec-graph.json add interface <name> '{"name":"...","description":"..."}'
know -g .ai/spec-graph.json link interface:<name> action:<name>
```

**Principle**: Capture what we KNOW now. `/know:build` refines and adds more during Architecture phase. Better to have a partial graph than lose information.

**CRITICAL: Add reference materials to spec-graph**

If user provided references, add them to `.ai/spec-graph.json` → `references` section:

Edit `.ai/spec-graph.json` to add a new reference type for documentation:

```json
"references": {
  "documentation": {
    "feature-name-paper": {
      "title": "Attention Is All You Need",
      "type": "research-paper",
      "url": "https://arxiv.org/abs/1706.03762",
      "summary": "Original transformer architecture paper",
      "sections": ["3.2", "5.4"],
      "feature": "feature:transformer-implementation"
    },
    "feature-name-api-docs": {
      "title": "Anthropic Claude API Documentation",
      "type": "api-doc",
      "url": "https://docs.anthropic.com/claude/reference",
      "summary": "Official API reference for Claude integration",
      "endpoints": ["/v1/messages", "/v1/complete"],
      "feature": "feature:claude-integration"
    },
    "feature-name-rfc": {
      "title": "RFC 7519 - JSON Web Tokens",
      "type": "rfc",
      "url": "https://datatracker.ietf.org/doc/html/rfc7519",
      "summary": "JWT specification",
      "sections": ["4.1", "7"],
      "feature": "feature:jwt-auth"
    }
  }
}
```

**Benefits**:
- References queryable via graph: `know -g .ai/spec-graph.json refs documentation`
- Links preserved in version control
- LLMs can query for context: "What papers is this feature based on?"
- Traceability from implementation → research

## 6. Update Feature Index
Maintain `.ai/know/features/feature-index.md` with a summary of all features:

**Steps**:
1. Read existing `feature-index.md` (create if doesn't exist)
2. Add new feature entry in alphabetical order
3. Update summary counts at top

**File structure**:
```markdown
# Feature Index

## Summary
- **Total Features**: N
- **Pending**: X
- **In Progress**: Y
- **Complete**: Z

## Features

### <feature-name>
- **Status**: pending
- **Objectives**: objective:name1, objective:name2
- **Description**: <1-2 sentence description>
- **Added**: YYYY-MM-DD
- **Directory**: `.ai/know/features/<feature-name>/`

### <another-feature>
...
```

**Note**: Keep entries alphabetically sorted for easy lookup.

## 7. Connect
- Run `/know:connect` to validate graph coverage
- Ensure new feature is reachable from root users
- If coverage < 100%, assist with connecting disconnected entities
- Guide user: "Feature added! Run `/know:build <feature-name>` to begin development"

**Example Usage**
```
User: /know:add transformer-attention
Assistant:
  1. Identify: feature name = "transformer-attention"
  2. Check Duplicates: Searches for "transformer", "attention", "neural"
     → No duplicates found
  3. Clarify: Asks user questions
     User provides:
     - Description: "Multi-head attention mechanism from Transformer paper"
     - Users: ai-assistant, developer
     - Objectives: improve-model-performance
     - Components: attention-calculator, weight-matrix-handler
     - Actions: compute-attention, apply-softmax
     - Interfaces: model-api
     - Requirements: gpu-acceleration
     - References: https://arxiv.org/abs/1706.03762
     - Experiments: "Validate CUDA kernel performance"
  4. Scaffold: Creates .ai/know/features/transformer-attention/
     → overview.md, references.md, experiments.md, notes.md, plan.md, spec.md
  5. Register: Populates spec-graph with ALL identified entities
     → feature:transformer-attention
     → component:attention-calculator, component:weight-matrix-handler
     → action:compute-attention, action:apply-softmax
     → interface:model-api
     → requirement:gpu-acceleration
     → Links: feature→components, feature→actions, actions→components
     → documentation references
  6. Update Feature Index
  7. Connect: Validates coverage, guides to /know:build
```

**Notes**
- ALWAYS check for duplicates before proceeding (step 2) - prevents wasted effort
- Search broadly: use synonyms, related terms, common patterns
- If duplicates found, stop and ask user - don't assume which path to take
- **ALWAYS ask for reference materials** (step 3) - critical for research-based features
  - Research papers (ArXiv, DOI)
  - Specifications (RFCs, W3C)
  - API documentation
  - Prior art (GitHub repos, blog posts)
- Create `references.md` file for human-readable links
- Add references to spec-graph for machine-queryable traceability
- Always ask clarifying questions before scaffolding (step 3)
- Link features to objectives immediately (avoids disconnected chains)
- Let `/know:build` handle detailed component architecture
- Use `/know:connect` to maintain graph coverage

---
`r15` - Extension workflow uses requirements: replaced todo.md tracking with `know req add`, updated confirmation messages
`r14` - Requirements replace todos: Added step 3b (Define Requirements), updated Register to use req add, scaffold creates notes.md instead of todo.md
`r13` - Replaced config.json with contract.yaml: bidirectional spec for declared vs observed, drift detection, confidence scoring
`r12` - Clarified role: /know:add is THE authority on per-feature details (called by /know:plan for each feature). Separation: plan identifies WHICH features, add handles HOW (dup detection, HITL, scaffolding, graph registration)
`r11` - Expanded Register step to populate full spec-graph (components, actions, interfaces, requirements) from Clarify
`r10` - Added experiments capture during Clarify, experiments.md scaffold for validation before build
`r9` - Added feature extension workflow (preserve baseline, track extensions in overview.md)
`r8` - Added config.json for feature tracking (watch paths, baseline, git notes bridge)
`r7` - Added feature-index.md maintenance step
`r6` - Added reference materials tracking (research papers, specs, docs)
`r5` - Added duplicate detection step (CRITICAL for preventing redundant work)
`r4` - Consolidated to 5 steps with HITL clarification flow
`r3` - Added /know:connect step to ensure graph coverage
`r2`
