# Knowledge Graph Builder - Implementation TODO

## Overview
Three core features to implement:
1. Enhanced Q&A stepping for graph discovery
2. Arrange phase for manual node connections
3. Artifacts phase for spec generation

---

## Phase 1: Enhanced Q&A Stepping (Discover Phase)

### Backend Tasks
- [ ] **Session Management** (`server/index.js`)
  - [ ] Add session tracking to `/api/discover/save-qa` endpoint
  - [ ] Create `/api/discover/session/history` to get Q&A history
  - [ ] Add `/api/discover/session/navigate` to move through history
  - [ ] Implement `/api/discover/session/progress` for completion tracking

- [ ] **Entity Extraction Enhancement**
  - [ ] Improve `/api/discover/extract` to return confidence scores
  - [ ] Add entity validation before committing to graph
  - [ ] Support bulk entity extraction from single answer
  - [ ] Add entity name/description editing endpoint

- [ ] **Smart Question Generation**
  - [ ] Enhance `/api/discover/next-question` with gap analysis
  - [ ] Add question categories (exploration, dependency, completion)
  - [ ] Implement question chains based on entity types
  - [ ] Add skip/back navigation support

### Frontend Tasks (`public/js/discover.js`)
- [ ] **Q&A History Navigation**
  - [ ] Add history sidebar showing all questions
  - [ ] Implement back/forward buttons
  - [ ] Show answered/skipped status for each question
  - [ ] Add progress indicator (% complete)

- [ ] **Entity Review Modal**
  - [ ] Create modal for reviewing extracted entities
  - [ ] Add inline editing for entity names
  - [ ] Add inline editing for entity descriptions
  - [ ] Support accept/reject for individual entities
  - [ ] Batch operations (accept all, reject all)

- [ ] **UI Improvements**
  - [ ] Add question context expansion (guidance, examples)
  - [ ] Implement multiple choice suggestions
  - [ ] Show upcoming questions preview
  - [ ] Add session save/resume capability

---

## Phase 2: Arrange Phase - Connection Builder

### Backend Tasks (`server/index.js`)
- [ ] **Connection Management**
  - [ ] Create `/api/graph/connect` endpoint
    - [ ] Validate connection based on dependency rules
    - [ ] Support entity-to-entity connections
    - [ ] Support reference-to-entity connections (any direction)
  - [ ] Create `/api/graph/disconnect` endpoint
  - [ ] Add `/api/graph/connections/:entity` to list connections
  - [ ] Implement `/api/graph/valid-targets/:entity` endpoint
    - [ ] Return valid entities based on rules
    - [ ] Return all references (always valid)
    - [ ] Include connection type info

- [ ] **Validation & Rules**
  - [ ] Load dependency rules from `know/lib/dependency-rules.json`
  - [ ] Implement connection validation logic
  - [ ] Add batch connection support
  - [ ] Create undo/redo capability

### Frontend Tasks
- [ ] **Create Arrange Phase** (`public/js/arrange.js`)
  - [ ] Two-panel layout implementation
    - [ ] Left panel: Entity browser
    - [ ] Right panel: Reference browser
  - [ ] Category filters for both panels
    - [ ] Multi-select checkboxes
    - [ ] Show/hide entity types
    - [ ] Show/hide reference categories
  - [ ] Connection interaction flow
    - [ ] Click entity to select
    - [ ] Highlight valid targets
    - [ ] Gray out invalid targets
    - [ ] Click target to connect
  - [ ] Connection management
    - [ ] Show existing connections list
    - [ ] Delete connections
    - [ ] Undo/redo support

- [ ] **Visual Feedback**
  - [ ] Highlight valid connection targets
  - [ ] Different styling for references vs entities
  - [ ] Connection count badges
  - [ ] Success/error notifications

- [ ] **Navigation Integration** (`public/index.html`, `app.js`)
  - [ ] Add "Arrange" to phase navigation
  - [ ] Create phase button and routing
  - [ ] Add phase switching logic

---

## Phase 3: Artifacts Phase - Spec Generation

### Backend Tasks (`server/index.js`)
- [ ] **Universal Artifact Generation**
  - [ ] Create `/api/artifacts/generate` endpoint
    - [ ] Support all entity types (features, components, interfaces, data_models, etc.)
    - [ ] Support all reference types
    - [ ] Handle format options (md, json, yaml)
  - [ ] Implement `/api/artifacts/batch` for multiple specs
  - [ ] Add `/api/artifacts/types` to list available artifacts
  - [ ] Create `/api/artifacts/export` for file downloads

- [ ] **Know CLI Integration**
  - [ ] Map entity types to know commands
    - [ ] `feature` → `know feature <id>`
    - [ ] `component` → `know component <id>`
    - [ ] `interface` → `know screen <id>`
    - [ ] `data_model` → `know functionality <id>`
    - [ ] Add mappings for all entity types
  - [ ] Handle special artifacts
    - [ ] Sitemap generation (`know sitemap`)
    - [ ] Component map (`know component-map`)
    - [ ] Gap analysis (`know gaps`)
    - [ ] Implementation order (`know order`)

- [ ] **Agent Integration**
  - [ ] Create `/api/artifacts/build` endpoint
  - [ ] Add queue management for build requests
  - [ ] Implement status tracking
  - [ ] Add webhook support for build completion

### Frontend Tasks
- [ ] **Create Artifacts Phase** (`public/js/artifacts.js`)
  - [ ] Three-panel layout
    - [ ] Entity selector (left)
    - [ ] Artifact viewer (center)
    - [ ] Actions panel (right)
  - [ ] Entity browser
    - [ ] Tree view of all entity types
    - [ ] Multi-select capability
    - [ ] Search/filter functionality
    - [ ] Category toggles
  - [ ] Artifact display
    - [ ] Markdown renderer with syntax highlighting
    - [ ] Code block formatting
    - [ ] Collapsible sections
    - [ ] Full-screen mode

- [ ] **Action Buttons**
  - [ ] Copy to clipboard
    - [ ] Use Clipboard API
    - [ ] Show success notification
  - [ ] Build button
    - [ ] Send to agent endpoint
    - [ ] Show build status
    - [ ] Queue management UI
  - [ ] Export functionality
    - [ ] Download as .md file
    - [ ] Batch export to zip
    - [ ] Format selection (md/json/yaml)

- [ ] **Special Artifacts**
  - [ ] Sitemap viewer
    - [ ] Interactive tree display
    - [ ] Click to generate specs
  - [ ] Component map
    - [ ] Matrix view
    - [ ] Usage statistics
  - [ ] Reports section
    - [ ] Gap analysis
    - [ ] Completeness scores
    - [ ] Implementation order

- [ ] **Navigation Integration**
  - [ ] Add "Artifacts" to phase navigation
  - [ ] Update routing and phase switching

---

## Phase 4: Styling and Polish

### CSS Tasks
- [ ] **Create new stylesheets**
  - [ ] `public/css/arrange.css` for Arrange phase
  - [ ] `public/css/artifacts.css` for Artifacts phase
  - [ ] `public/css/discover-enhanced.css` for Q&A improvements

- [ ] **Theme Integration**
  - [ ] Apply existing theme system to new components
  - [ ] Ensure consistency with current design
  - [ ] Add responsive layouts

---

## Phase 5: Testing and Integration

### Testing Tasks
- [ ] **Manual Testing**
  - [ ] Test Q&A history navigation
  - [ ] Verify connection validation rules
  - [ ] Test artifact generation for all entity types
  - [ ] Verify copy/build functionality
  - [ ] Test batch operations

- [ ] **Integration Testing**
  - [ ] Test WebSocket updates across features
  - [ ] Verify graph persistence
  - [ ] Test session management
  - [ ] Validate know CLI integration

- [ ] **Error Handling**
  - [ ] Add error boundaries
  - [ ] Implement retry logic
  - [ ] User-friendly error messages
  - [ ] Validation feedback

---

## Technical Notes

### API Endpoints Summary
```
# Q&A Enhancement
GET  /api/discover/session/history
POST /api/discover/session/navigate
GET  /api/discover/session/progress

# Connection Management
POST /api/graph/connect
POST /api/graph/disconnect
GET  /api/graph/connections/:entity
GET  /api/graph/valid-targets/:entity

# Artifact Generation
POST /api/artifacts/generate
POST /api/artifacts/batch
GET  /api/artifacts/types
POST /api/artifacts/export
POST /api/artifacts/build
```

### File Structure
```
www/
├── public/
│   ├── js/
│   │   ├── discover.js (enhance)
│   │   ├── arrange.js (create)
│   │   ├── artifacts.js (create)
│   │   └── app.js (update)
│   ├── css/
│   │   ├── arrange.css (create)
│   │   ├── artifacts.css (create)
│   │   └── discover-enhanced.css (create)
│   └── index.html (update navigation)
├── server/
│   └── index.js (add all new endpoints)
└── TODO.md (this file)
```

### Priority Order
1. Q&A Enhancement (improve existing functionality)
2. Arrange Phase (critical for graph completion)
3. Artifacts Phase (enable spec generation)

### Completion Criteria
- [ ] All three phases accessible from navigation
- [ ] Q&A stepping allows forward/backward navigation
- [ ] Connections can be made without seeing graph structure
- [ ] Any entity type can generate an artifact
- [ ] Artifacts display in code blocks with copy/build actions
- [ ] System feels intuitive and hides complexity

---

## Notes
- Keep graph complexity hidden from users
- References can connect to any entity (no restrictions)
- Focus on intuitive UX over technical accuracy
- All features should work with existing know CLI
- Maintain compatibility with current WebSocket updates