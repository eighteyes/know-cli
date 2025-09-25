# TODO - Lucid Dream v2

## Current MVP Features (Completed)
- ✅ Start page with vision input
- ✅ Dark wireframe theme
- ✅ Top bar navigation (80px)
- ✅ AI bar input (30px)
- ✅ Collapsible sidebar with WHAT/HOW/SPECS sections
- ✅ Basic Discover page with QA workflow
- ✅ Multiple choice selection (click to multi-select)
- ✅ Graph file management
- ✅ Mock AI endpoints

## Immediate Tasks

### AI Integration
- [x] Connect to real Anthropic API for question generation - ✅ COMPLETED: Added @anthropic-ai/sdk, implemented real Claude API integration with intelligent fallback to mock data when API key not configured. Includes robust JSON parsing and maintains existing response format.
- [x] Implement actual entity/reference extraction from answers - ✅ COMPLETED: Enhanced /api/ai/extract-entities with real Claude API, comprehensive entity types (11+), reference categories (15+), dependency rules, kebab-case naming, and intelligent fallback.
- [x] AI-powered question expansion (multiple choice, recommendations, tradeoffs) - ✅ COMPLETED: Enhanced /api/ai/expand-question with Claude API, context-aware choices, best practice recommendations, tradeoff analysis, alternatives, and challenges.
- [x] AI command parsing in AI bar for graph modifications - ✅ COMPLETED: Enhanced /api/ai/command with Claude API, natural language understanding, support for add/remove/modify/connect operations, bulk operations, entity validation.
- [x] Question refinement based on previous answers - ✅ ALREADY COMPLETED: Sophisticated refinement logic built into /api/ai/generate-questions with 4 progressive phases, pattern recognition, gap analysis, duplicate avoidance, and context-aware generation

### Discover Page Enhancements
- [ ] Persist QA sessions to graph.meta.qa_sessions
- [ ] Skip question functionality
- [ ] Question queue management (show skipped questions differently)
- [ ] Auto-save answers as user types (debounced)
- [ ] Show question count and progress indicator
- [ ] Better visual hierarchy for extraction choices
- [ ] Connection suggestions between entities

### Graph Management
- [ ] Create new graph from vision statement
- [ ] Auto-save graph changes
- [ ] Graph validation before save
- [ ] Backup graph versions
- [ ] Import/export graph files
- [ ] Graph diff viewer

### Sidebar Improvements
- [ ] Inline editing for entity/reference descriptions
- [ ] Delete entity/reference functionality
- [ ] Drag and drop to reorder
- [ ] Search/filter within sections
- [ ] Show entity relationships on hover
- [ ] Bulk operations (select multiple, delete, move)
- [ ] Dynamic reference categories from graph

### Know Tool Integration
- [ ] Connect to actual know CLI commands
- [ ] Generate artifacts from entities
- [ ] Display know tool output in UI
- [ ] Error handling for know tool failures

## Version 2 Features

### Arrange Page
- [ ] Visual graph editor
- [ ] Drag and drop entity relationships
- [ ] Auto-layout algorithms
- [ ] Zoom and pan controls
- [ ] Mini-map navigation
- [ ] Relationship type selector
- [ ] Batch connection tools

### Validate Page
- [ ] Dependency validation
- [ ] Circular dependency detection
- [ ] Missing connection warnings
- [ ] Entity completeness checks
- [ ] Graph health score
- [ ] Validation report generation

### Define Page
- [ ] Entity detail forms
- [ ] Reference value editing
- [ ] Acceptance criteria editor
- [ ] Business logic definition
- [ ] UI concern specifications
- [ ] Template generation from references

### Build Page
- [ ] Code generation from graph
- [ ] File scaffold creation
- [ ] Component boilerplate
- [ ] Test generation
- [ ] Documentation generation
- [ ] Export to project structure

## Technical Improvements

### Performance
- [ ] Lazy load graph sections
- [ ] Virtual scrolling for long lists
- [ ] Debounce API calls
- [ ] Client-side caching
- [ ] Optimize graph queries

### UX Enhancements
- [ ] Keyboard shortcuts
- [ ] Undo/redo functionality
- [ ] Command palette (Cmd+K)
- [ ] Toast notifications
- [ ] Loading states
- [ ] Error boundaries
- [ ] Tooltips for complex features
- [ ] Guided tour for new users

### Developer Experience
- [ ] TypeScript migration
- [ ] Component library (design system)
- [ ] Unit tests
- [ ] E2E tests
- [ ] API documentation
- [ ] Storybook for components
- [ ] Hot reload in development

### Infrastructure
- [ ] WebSocket for real-time updates
- [ ] Database integration (PostgreSQL/SQLite)
- [ ] User authentication
- [ ] Multi-tenant support
- [ ] Cloud deployment ready
- [ ] Docker containerization
- [ ] CI/CD pipeline

## Bug Fixes & Polish
- [ ] Handle empty graph file list gracefully
- [ ] Prevent duplicate entity names
- [ ] Validate graph structure on load
- [ ] Better error messages
- [ ] Responsive design for mobile
- [ ] Cross-browser testing
- [ ] Accessibility improvements (ARIA labels, keyboard navigation)
- [ ] Print styles for reports

## Future Considerations
- [ ] Collaborative editing (CRDT/OT)
- [ ] Version control integration (Git)
- [ ] Plugin system
- [ ] Custom themes
- [ ] Export to various formats (Mermaid, PlantUML, GraphViz)
- [ ] Import from existing codebases
- [ ] AI-powered code review based on graph
- [ ] Metrics and analytics dashboard