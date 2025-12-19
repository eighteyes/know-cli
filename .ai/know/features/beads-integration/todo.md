# Todo: Beads Integration

## Phase 1: Beads Bridge Foundation

- [ ] Research Beads CLI interface and JSONL format
  - [ ] Study `bd` command structure
  - [ ] Analyze `.beads/issues.jsonl` format
  - [ ] Document Beads dependency types
  - [ ] Map Beads concepts to know entities
- [ ] Design integration architecture
  - [ ] Symlink strategy for `.ai/beads/`
  - [ ] Reference schema for `references.beads`
  - [ ] Sync protocol design
  - [ ] Passthrough command architecture
- [ ] Create `know/src/beads_bridge.py`
  - [ ] `BeadsBridge` class
  - [ ] `init_beads()` - Setup .ai/beads with symlink
  - [ ] `call_bd()` - Execute bd commands
  - [ ] `parse_beads_output()` - Parse bd command results

## Phase 2: Beads Commands

- [ ] Add bd subcommands to know CLI (matching bd shorthand)
  - [ ] `know bd init [--path]`
  - [ ] `know bd sync`
  - [ ] `know bd list [--ready]`
  - [ ] `know bd add <title> [--feature]`
  - [ ] Passthrough for other bd commands
- [ ] Update `know/know.py`
  - [ ] Add bd command group (name='bd')
  - [ ] Route to BeadsBridge methods
  - [ ] Handle feature linking
- [ ] Create tests
  - [ ] Test bd init with custom path
  - [ ] Test command passthrough
  - [ ] Test feature linking

## Phase 3: Beads ↔ Know Sync

- [ ] Create `know/src/beads_sync.py`
  - [ ] `BeadsSync` class
  - [ ] `import_beads()` - Read .beads/issues.jsonl
  - [ ] `export_to_graph()` - Store in references.beads
  - [ ] `sync_status()` - Sync bead status with features
  - [ ] `link_to_feature()` - Associate beads with features
- [ ] Update spec-graph schema
  - [ ] Add `references.beads` section
  - [ ] Document bead reference format
  - [ ] Add feature-to-bead linking
- [ ] Implement bidirectional sync
  - [ ] Beads → Graph sync
  - [ ] Graph → Beads sync
  - [ ] Conflict resolution strategy
  - [ ] Auto-sync configuration

## Phase 4: Native Task System

- [ ] Create `know/src/task_manager.py`
  - [ ] `TaskManager` class
  - [ ] `add_task()` - Create task with hash ID
  - [ ] `list_tasks()` - Query tasks
  - [ ] `update_task()` - Modify task
  - [ ] `complete_task()` - Mark done
  - [ ] `find_ready()` - Auto-ready detection
- [ ] Design native JSONL format
  - [ ] Hash-based IDs (`tk-a1b2`)
  - [ ] Dependency types (blocks, related, parent-child)
  - [ ] Feature linking metadata
  - [ ] Status tracking
- [ ] Create `.ai/tasks/` structure
  - [ ] `tasks.jsonl` - All tasks
  - [ ] `.gitignore` for cache.db
  - [ ] Documentation

## Phase 5: Native Task Commands

- [ ] Add task subcommands to know CLI
  - [ ] `know task init`
  - [ ] `know task add <title> [--feature]`
  - [ ] `know task list [--ready] [--feature]`
  - [ ] `know task done <task-id>`
  - [ ] `know task block <task-id> --on <blocker-id>`
  - [ ] `know task unblock <task-id>`
- [ ] Update `know/know.py`
  - [ ] Add task command group
  - [ ] Route to TaskManager methods
  - [ ] Handle feature linking
- [ ] Create tests
  - [ ] Test task CRUD operations
  - [ ] Test dependency management
  - [ ] Test auto-ready detection
  - [ ] Test feature linking

## Phase 6: Configuration & Documentation

- [ ] Create `.ai/config.json` schema
  - [ ] `task_system` field (beads/native/hybrid)
  - [ ] `beads_path` field
  - [ ] `auto_sync` field
  - [ ] `feature_bead_linking` field
- [ ] Update documentation
  - [ ] Add Beads integration guide
  - [ ] Add native task system guide
  - [ ] Add comparison: Beads vs Native
  - [ ] Add migration guide
  - [ ] Marketing copy: "Works with Beads!"
- [ ] Update README.md
  - [ ] Add task management section
  - [ ] Add Beads integration highlights
  - [ ] Add command examples

## Phase 7: Testing & Polish

- [ ] Integration tests
  - [ ] Test Beads mode end-to-end
  - [ ] Test native mode end-to-end
  - [ ] Test hybrid mode
  - [ ] Test switching between modes
- [ ] Edge cases
  - [ ] Handle missing bd command
  - [ ] Handle corrupt JSONL
  - [ ] Handle sync conflicts
  - [ ] Handle orphaned tasks
- [ ] Performance testing
  - [ ] Large task sets (1000+ tasks)
  - [ ] Sync performance
  - [ ] Auto-ready query performance

## Validation & Release

- [ ] Run all tests
- [ ] Manual testing with real Beads instance
- [ ] Update CHANGELOG.md
- [ ] Create marketing materials
- [ ] Tag release

---

**See also**: `plan.md` for detailed implementation architecture
