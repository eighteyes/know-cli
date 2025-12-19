# Feature: Beads Integration

## User Request
Integrate Beads task management into know-cli, allowing users to choose between Beads integration or native task system while maintaining know's product specification focus.

## Description
Enable seamless integration with Beads (Steve Yegge's task management system) while providing a native JSONL-based task system as an alternative. Tasks link to feature entities in spec-graph, bridging product planning (know) with task execution (beads).

## Primary User
- **developer**: Developers managing tasks alongside product specs

## Objectives Supported
- Enable task execution tracking linked to product features
- Provide choice between Beads integration and native task system
- Bridge product specification layer with implementation tasks

## Capabilities

### 1. Initialize Beads in .ai/beads/
- Create `.ai/beads/` directory structure
- Symlink `.beads → .ai/beads` for Beads compatibility
- Configure `.gitignore` appropriately
- Run `bd init` with custom path configuration

### 2. Sync Tasks Between Beads and Know Features
- Bidirectional sync: beads ↔ spec-graph feature entities
- Store bead references in `references.beads` section
- Link beads to features via metadata
- Auto-sync on feature changes (optional)

### 3. Passthrough bd Commands via Know
- `know bd list` → `bd list`
- `know bd add` → `bd add` with feature linking
- `know bd sync` → custom sync operation
- `know bd ready` → `bd ready` (auto-ready detection)

### 4. Native Task System Alternative
- JSONL-based task storage in `.ai/tasks/`
- Hash-based IDs (`tk-a1b2`) for collision-free merging
- Rich dependency types: blocks, related, parent-child, discovered-from
- Auto-ready detection without Beads dependency
- Compatible command structure with Beads

## Components Needed
- `beads-bridge`: Integration layer between know and bd commands
- `task-manager`: Native JSONL task system implementation
- `task-sync`: Bidirectional sync between tasks and features
- `task-cli`: CLI commands for task management

## Success Criteria
- Users can choose Beads or native task system
- Tasks stored in `.ai/beads/` or `.ai/tasks/`
- `know bd *` commands work seamlessly (matching bd shorthand)
- Native `know task *` commands provide equivalent functionality
- Beads/tasks link to feature entities in spec-graph
- Auto-sync keeps tasks aligned with features
- Marketing value: "Seamless Beads Integration"
