# Discovery Q&A: Beads Integration

## Context

Integrating Beads task management system into know-cli, providing both Beads integration (`know bd`) and native task system (`know task`) as options.

## Codebase Analysis Complete

✅ **Architecture Patterns Identified:**
- Manager pattern for all subsystems
- Dependency injection via Click context
- Configuration-driven external integrations
- Reference-based storage for external entities
- Comprehensive testing with fixtures

✅ **Integration Points Mapped:**
- CLI command structure (Click subgroups)
- Manager layer (`BeadsBridge`, `TaskManager`, `TaskSync`)
- Reference storage in spec-graph
- Configuration patterns
- Testing strategies

✅ **Similar Patterns Found:**
- LLM integration (configuration-driven providers)
- Product-component linking (cross-graph references)
- External dependency tracking
- Phase management

## Initial Requirements Captured

**From overview.md:**
1. Initialize Beads in `.ai/beads/` with symlink to `.beads`
2. Bidirectional sync between Beads/native tasks and features
3. Passthrough `bd` commands via `know bd`
4. Native JSONL task system as alternative
5. Hash-based IDs for collision-free merging
6. Auto-ready detection
7. Feature linking for all tasks

## Questions for Clarification Phase

The following areas need user input before architecture design:

### 1. Error Handling & Edge Cases
- How to handle missing `bd` executable?
- What if Beads isn't installed but user runs `know bd init`?
- Corrupted JSONL files - recover or fail?
- Sync conflicts - which system wins?

### 2. Security & Permissions
- Should we validate/sanitize `bd` command arguments?
- File permissions for `.ai/beads/` directory?
- API keys or auth for Beads (if applicable)?

### 3. Auto-Sync Behavior
- When should auto-sync trigger? (on feature status change?)
- Should sync be blocking or background?
- Sync frequency if time-based?

### 4. Conflict Resolution
- If bead status differs from graph feature status, which wins?
- Merge strategies: graph-first, beads-first, manual, or timestamp-based?

### 5. Task Lifecycle
- Should completed tasks be archived/removed?
- Task retention policy?
- History tracking?

### 6. Integration Scope
- Should ALL features auto-create beads, or opt-in per feature?
- Which graph changes trigger sync? (status only? description? dependencies?)

## Next Steps

Proceed to **Phase 2: Clarify** with targeted questions to user.
