# Know Command Workflow Review

## Executive Summary

Reviewed 10 commands in `.claude/commands/know/`, the know-tool skill, and the Python CLI. Found a sophisticated but incomplete system with several workflow gaps that need addressing before it can reliably support feature-driven development.

**Grade: B-** - Solid foundation, but missing critical connections between commands and undocumented capabilities.

## User Clarifications (Applied)

- **Worktrees**: Independent concern, removed from workflows
- **Phase vs Status**: Phase = Roman numerals (I, II, III) for WHEN (planning waves). Status = in-progress/complete for current state. Phase is the plan, status is the territory.
- **Phase:done**: Redundant with status:complete - remove it
- **Canon directory**: `.ai/know/features/<feature>/`
- **Spec generation**: Must be DETERMINISTIC (no LLM enrichment) - the challenge
- **LLM commands**: Remove from know tool and skill - not the focus
- **Requirements.md**: Use for task counts, show "--" for empty

---

## 1. PROPOSED WORKFLOWS

### 1.1 Greenfield Project Workflow

For projects with no existing code or specification:

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 0: INITIALIZATION                                         │
├─────────────────────────────────────────────────────────────────┤
│ /know:schema (optional)  → Custom domain schema if needed       │
│         ↓                                                       │
│ /know:plan [Start]       → Capture intent, scope, users         │
│         ↓                                                       │
│ Creates: input.md, revised-input.md                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: DISCOVERY                                              │
├─────────────────────────────────────────────────────────────────┤
│ /know:plan [Discovery]   → Users, objectives, features          │
│         ↓                                                       │
│ Creates: user-stories.md, requirements.md, features.md          │
│ Populates: spec-graph (user, objective, feature entities)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: ARCHITECTURE                                           │
├─────────────────────────────────────────────────────────────────┤
│ /know:plan [Architect]   → Components, data models, flows       │
│         ↓                                                       │
│ /know:plan [API]         → Endpoints, contracts (if applicable) │
│         ↓                                                       │
│ /know:plan [UI]          → Screens, navigation (if applicable)  │
│         ↓                                                       │
│ Populates: spec-graph (component, action, operation, interface) │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: PLANNING                                               │
├─────────────────────────────────────────────────────────────────┤
│ /know:plan [Quality]     → Testing strategy                     │
│         ↓                                                       │
│ /know:plan [PM]          → Build order, horizons, acceptance      │
│         ↓                                                       │
│ Creates: todo.md, plan tasks, horizons in spec-graph              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: IMPLEMENTATION (per feature)                           │
├─────────────────────────────────────────────────────────────────┤
│ /know:add <feature>      → Create feature scaffold              │
│         ↓                                                       │
│ /know:build <feature>    → 5-phase development cycle            │
│         ↓                                                       │
│ /know:review <feature>   → Acceptance testing                   │
│         ↓                                                       │
│ /know:done <feature>     → Archive and merge                    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Mature Project Workflow

For projects with existing code but no spec-graph:

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 0: REVERSE ENGINEERING                                    │
├─────────────────────────────────────────────────────────────────┤
│ /know:prepare            → Auto-populate both graphs from code  │
│         ↓                                                       │
│ Creates: spec-graph.json, code-graph.json, project.md           │
│ Links: code modules → spec components (product-component refs)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: GRAPH ENRICHMENT                                       │
├─────────────────────────────────────────────────────────────────┤
│ /know:connect            → Connect floating entities to users   │
│         ↓                                                       │
│ /know:plan [Discovery]   → Fill user/objective gaps (optional)  │
│         ↓                                                       │
│ Target: ≥80% coverage (all entities reachable from users)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: FEATURE DEVELOPMENT (same as greenfield Phase 4)       │
├─────────────────────────────────────────────────────────────────┤
│ /know:add → /know:build → /know:review → /know:done             │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Bug Fix / Hotfix Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ BUG TRACKING                                                    │
├─────────────────────────────────────────────────────────────────┤
│ /know:bug <feature>      → Create structured bug report         │
│         ↓                                                       │
│ Updates: bugs/NNN-slug.md, todo.md with bug fix task            │
│ Optional: Move feature back to "in-progress" phase              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FIX IMPLEMENTATION                                              │
├─────────────────────────────────────────────────────────────────┤
│ /know:build <feature>    → Resume at Phase 4 (Implement)        │
│         ↓                                                       │
│ /know:review <feature>   → Verify fix                           │
│         ↓                                                       │
│ /know:done <feature>     → Re-archive if complete               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. LOGIC GAPS, INCONSISTENCIES & EDGE CASES

### 2.1 CRITICAL GAPS

#### GAP-1: No Command to Resume Partially Complete Builds
**Problem**: `/know:build` has no mechanism to resume if interrupted mid-phase.
**Edge Case**: User runs Phase 1-3, closes terminal, returns later. How do they resume at Phase 4?
**Fix**: Add phase detection to `/know:build` that reads existing artifacts (`discovery.md`, `clarification.md`, `adrs.md`) and offers to resume at the appropriate phase.

#### GAP-2: `/know:prepare` → `/know:plan` Handoff Needs Deduplication
**Problem**: Both commands can populate spec-graph. `/know:prepare` auto-generates from code, `/know:plan` uses QA.
**Resolution**: Deduplication is needed, but `/know:plan` should still run to capture product assumptions not visible from code.
**Fix**: Add deduplication logic that merges/updates existing entities rather than duplicating.

#### GAP-3: `/know:fill-out` Exists But Untracked
**Problem**: Command exists but is untracked in git.
**Fix**: `git add .claude/commands/know/fill-out.md`

#### GAP-4: Code-Graph Never Updated in Feature Workflows ✅ CONFIRMED
**Problem**: `/know:build` and `/know:add` only operate on spec-graph.
**Fix**: Add code-graph update step to `/know:build` Phase 5 (Wrapup).

### 2.2 INCONSISTENCIES (RESOLVED)

#### INC-1: Phase vs Status Semantics ✅ CLARIFIED
**Phase** = Roman numerals (I, II, III) - WHEN to do this feature (planning waves)
**Status** = in-progress, complete, planned - current state of the work

**Analogy**: Phase is the plan, status is the territory.

**Example**: A feature can be `phase: III` (planned for wave 3) but `status: in-progress` (started early).

**Action**: Remove `phase: done` - it's redundant with `status: complete`. Phases are ONLY for planning waves (I, II, III, pending).

#### INC-2: `/know:review` Creates changes/ Without Command ✅ FIX PLANNED
**Problem**: The command can create `changes/NNN-slug.md` files but there's no `/know:change` command.
**Fix**: Create `/know:change` command to match `/know:bug`.

#### INC-3: Directory Paths ✅ RESOLVED
**Canon**: `.ai/know/features/<feature>/`
**Action**: Update any references to `.ai/know/<feature>/` to use the canon path.

### 2.3 EDGE CASES

#### EDGE-1: Feature Name Already Exists ✅ FIX PLANNED
**Current**: `/know:add` checks for uniqueness but what if feature was archived?
**Fix**: Check both `/features/` and `/features/archive/` for name conflicts.

#### EDGE-2: Circular Feature Dependencies ✅ FIX PLANNED
**Current**: Spec-graph validates entity dependencies but features can depend on other features.
**Problem**: What if feature:A needs feature:B which needs feature:A?
**Fix**: Add feature-level cycle detection to know tool, have `/know:add` use it.

#### EDGE-3: Empty Requirements Count
**Current**: `/know:list` shows task counts from todo.md files.
**Change**: Use `requirements.md` for counts instead.
**Fix**: Show "--" for empty/missing requirements.

---

## 3. KNOW-TOOL SKILL REVIEW

### 3.1 Currency Assessment

| Area | Status | Action |
|------|--------|--------|
| Core Commands | ✅ Current | Keep |
| Phase Commands | ⚠️ Incomplete | Add subcommands (add/move/status/remove) |
| LLM Commands | ❌ Remove | Not in scope - remove from skill entirely |
| Coverage Command | ❌ Missing | Add `know coverage` |
| Rules Subsystem | ⚠️ Sparse | Add more examples |
| Reference Guides | ❌ 6 Missing | Create or remove promises |

### 3.2 Backup Version ✅ DELETE
**Action**: Remove `know-tool-backup/` entirely - contains obsolete API.

### 3.3 Commands to Add to Skill

```bash
know coverage                    # % entities connected to root users
know horizons list                 # List all horizons
know horizons add <horizon> <entity> # Add entity to horizon
know horizons move <entity> <horizon># Move entity
know horizons status <entity> <st>   # Change status
know horizons remove <entity>        # Remove from horizons
know trace-matrix                # Requirement traceability (NEW)
```

### 3.4 Commands to REMOVE from Skill

```bash
# Remove all LLM commands - not in scope
know llm-providers
know llm-workflows
know llm-run
know llm-chain
know llm-chains
know llm-info
know llm-test
know feature-spec              # Remove - use know spec only
```

### 3.5 Spec Generation

**Keep only**: `know spec <entity>` - generates complete spec deterministically

**Remove**:
- `know feature-spec` - redundant
- All LLM workflow commands
- Template references

**The Challenge**: `know spec` must generate complete, LLM-quality specifications WITHOUT LLM enrichment. This is deterministic spec generation.

### 3.6 Effectiveness Improvements

**What Works Well**:
- Mental model (WHAT vs HOW chains) is excellent
- Command organization by category is clear
- Graph structure documentation is accurate

**What Needs Improvement**:
- Document phase management workflow
- Create missing reference guides OR remove promises
- Add troubleshooting guide with common errors
- Add `know trace-matrix` for requirement traceability

---

## 4. SPEC & REQUIREMENT GENERATION CAPABILITY

### 4.1 Design Principle: DETERMINISTIC SPEC GENERATION

**Core Challenge**: `know spec <entity>` must generate complete, LLM-quality specifications WITHOUT LLM enrichment.

Why this matters:
- Reproducible outputs across runs
- No API dependencies
- Consistent quality
- Version controllable
- Auditable

### 4.2 Current Capability

**Single command**: `know spec <entity>` - generates markdown/JSON spec

The spec is assembled entirely from graph data:
- Entity metadata (name, description)
- Dependencies (upstream/downstream)
- References (business_logic, data-model, etc.)
- Phase and status information
- Related entities

### 4.3 Generation Completeness Assessment

| Artifact | Can Generate? | Source |
|----------|--------------|--------|
| Entity Spec | ✅ Yes | `know spec <entity>` |
| User Stories | ✅ Yes | Derived from user → objective chain |
| Requirements | ✅ Yes | Derived from requirement entities |
| API Specs | ✅ Yes | Derived from interface entities + api-surface refs |
| Test Plans | ⚠️ Partial | Derived from acceptance_criterion refs |
| ADRs | ⚠️ Manual | Created via /know:build |
| QA Steps | ⚠️ Manual | Created via /know:build |

### 4.4 GAPS IN DETERMINISTIC SPEC GENERATION

#### SPECGAP-1: `know spec` Output Not Rich Enough
**Problem**: Current spec output is basic. To match LLM-quality, it needs:
- Full dependency chain narrative
- Cross-referenced related entities
- Inferred acceptance criteria from references
- Generated user story format from user → objective → action chain

**Fix**: Enhance `know spec` template to traverse and narrate the full graph context.

#### SPECGAP-2: Requirement Traceability Matrix ✅ PLANNED
**Add**: `know trace-matrix` command that shows:
```
user:developer → objective:efficiency → feature:auto-complete → component:suggestion-engine
```

#### SPECGAP-3: Bulk Generation (DEFERRED)
**Defer**: Focus on making single-entity generation complete first.
**Future**: Add `know spec --all [--type feature]` once basics work.

---

## 5. RECOMMENDATIONS

### 5.1 Immediate Fixes (Priority 1)

1. **Stage `/know:fill-out`** - `git add .claude/commands/know/fill-out.md`
2. **Delete backup skill** - `rm -rf .claude/skills/know-tool-backup/`
3. **Update know-tool skill** - add horizons, coverage; remove LLM commands
4. **Document horizon vs status** - horizon=plan (I,II,III), status=territory (in-progress,complete)
5. **Remove horizon:done** - redundant with status:complete

### 5.2 Workflow Improvements (Priority 2)

1. **Add resume detection to `/know:build`** - detect existing artifacts, offer to resume
2. **Add code-graph updates** to `/know:build` wrapup phase
3. **Add deduplication** when running `/know:plan` on existing entities
4. **Create `/know:change`** command to match `/know:bug`
5. **Add `know trace-matrix`** for requirement traceability
6. **Fix `/know:list`** to use requirements.md with "--" for empty

### 5.3 Spec Generation Enhancements (Priority 3)

1. **Enhance `know spec`** to generate complete specs deterministically
2. **Add full dependency chain narrative** to spec output
3. **Add cross-referenced related entities** to spec output
4. **Create/remove promised reference guides** in skill

---

## 6. WORKFLOW VALIDATION CHECKLIST

Use this to verify workflow soundness:

- [ ] Can create project from scratch (greenfield)
- [ ] Can reverse-engineer existing codebase (mature)
- [ ] Can add new feature without breaking existing graph
- [ ] Can resume interrupted build (GAP-1)
- [ ] Can track and fix bugs
- [ ] Can track and implement changes (needs /know:change)
- [ ] Can archive completed features
- [ ] Can generate complete specs DETERMINISTICALLY
- [ ] Can validate both graphs independently
- [ ] Can link code to spec (cross-graph)
- [ ] Can show progress/status of all features
- [ ] Can show requirement traceability (needs trace-matrix)

---

## 7. ACTION ITEMS

### Immediate (This Session)
- [ ] Stage fill-out.md
- [ ] Delete know-tool-backup
- [ ] Update know-tool skill
- [ ] Create /know:change command

### Next Session
- [ ] Add resume detection to /know:build
- [ ] Add code-graph update to /know:build wrapup
- [ ] Add `know trace-matrix` command
- [ ] Enhance `know spec` for richer output

---

*Review completed by Patches, Your Obsequious Graph Wrangler*
*Revision: 2*
