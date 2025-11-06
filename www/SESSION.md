# WWW_V2 Website Session Documentation

## Overview
A dark-themed MVP web application for graph-based knowledge management with a question-answer discovery workflow. Built with vanilla JavaScript, Express.js backend, and a custom graph management system.

## Current Implementation Status

### Core Features Implemented

#### 1. **Multi-Page SPA Architecture**
- Hash-based routing (/#start, /#discover, etc.)
- Pages: Start, Discover, Arrange, Validate, Define, Build
- Currently active: Start, Discover, Define
- Disabled: Validate, Build

#### 2. **Graph Management System**
- Load existing graph files from `graphs/` directory
- Create new graphs from vision statements
- Track unsaved changes with `*` indicator
- Save/Revert functionality with dedicated buttons
- Auto-saves to both local graphs folder and main spec-graph.json

#### 3. **Start Page**
- Vision input field for new projects
- Graph file selector dropdown
- Automatic navigation to Discover on graph load
- Clean centered design with gradient branding

#### 4. **Discover Page - Q&A Workflow**
- Question-Answer interface for knowledge extraction
- Multiple choice expansion with multi-select support
- Entity/Reference detection from answers
- Question queue management (answered, current, upcoming, skipped)
- Collapsible question list view
- Mock AI integration endpoints ready for Anthropic API

#### 5. **Right Sidebar (Auto-shows on graph load)**
- Collapsible accordion sections for entities and references
- Title case formatting for entity names
- Inline editing with stacked layout:
  - Name field on top
  - Description field below
  - Save/Cancel buttons at bottom
- Add new entity with expanding form (name + description)
- Grey pencil edit icon on hover
- Tooltips showing descriptions

#### 6. **UI/UX Features**
- Dark wireframe theme (rgba(18, 18, 20, 1) background)
- Right-side sidebar with arrow toggle (◀/▶)
- Top bar with page navigation buttons
- AI command bar (hidden by default)
- Responsive design with mobile support
- Smooth transitions and hover effects

### Technical Architecture

#### Frontend (`/public`)
- **index.html**: Main SPA structure
- **js/app.js**: Core application logic
  - State management with unsaved changes tracking
  - Entity/Reference CRUD operations
  - Q&A session management
  - Graph file operations
- **css/styles.css**: Dark theme with CSS variables
  - Custom styling for all components
  - Edit mode layouts
  - Responsive breakpoints

#### Backend (`/server`)
- **index.js**: Express server (port 8880)
  - `/api/graphs` - List available graphs
  - `/api/graphs/:filename` - Load specific graph
  - `/api/graphs/save` - Save graph (handles filename)
  - Mock AI endpoints:
    - `/api/ai/generate-questions`
    - `/api/ai/extract-entities`
    - `/api/ai/expand-question`
    - `/api/ai/process-command`

#### Data Structure
```javascript
{
  meta: {
    project_name: string,
    vision_statement: string,
    qa_sessions: array,
    phases: array
  },
  entities: {
    [entityType]: {
      [entityKey]: {
        description: string
      }
    }
  },
  references: {
    [category]: {
      [key]: value
    }
  },
  graph: array // Dependency relationships
}
```

### Recent Updates
1. **Sidebar Edit Mode Enhancement**: Stacked layout with fields expanding vertically
2. **Add New Entity**: Includes description field that appears on focus
3. **Unsaved Changes Tracking**:
   - Asterisk (*) indicator in filename
   - Save (✓) and Revert (✕) buttons
   - Deep copy of original graph for reverting
4. **Auto-show Sidebar**: Opens automatically when graph loads
5. **Multiple Choice UI**: Clickable div options with multi-select support
6. **Inline Editing**: Direct editing without prompts/modals

### File Structure
```
www_v2/
├── package.json          # Node dependencies
├── server/
│   └── index.js         # Express backend
├── public/
│   ├── index.html       # Main HTML
│   ├── css/
│   │   └── styles.css   # Dark theme styles
│   └── js/
│       └── app.js       # Core application logic
├── graphs/              # Graph JSON files
│   └── *.json
├── TODO.md             # Development tasks
└── SESSION.md          # This file
```

### Known Working Features
- Graph file loading and saving
- Entity/Reference management with inline editing
- Question-answer workflow
- Multiple choice selection
- Sidebar accordion navigation
- Unsaved changes tracking
- Auto-sidebar display on graph load

### Pending/Mock Features
- Real AI integration (currently returns mock data)
- Arrange, Validate, Build pages (UI exists but disabled)
- Graph dependency visualization
- Real entity extraction from answers
- Question generation from vision/answers

### Important Notes
1. Server runs on port 8880
2. Graph files stored in `www_v2/graphs/`
3. Also syncs with parent `.ai/spec-graph.json`
4. All AI endpoints return mock data
5. Uses vanilla JavaScript (no frameworks)
6. Dark wireframe theme throughout
7. Right-side collapsible sidebar
8. Inline editing pattern (no modals/prompts)

### How to Run
```bash
cd www_v2
npm install
npm start
# Navigate to http://localhost:8880
```

### Next Session TODOs
- Implement real AI integration with Anthropic API
- Complete Arrange page functionality
- Add graph visualization
- Implement Validate and Build pages
- Add real-time collaboration features
- Enhance dependency graph management