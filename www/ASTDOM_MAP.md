## APP.JS ↔ INDEX.HTML Relationship Map

### **Core Structure**
- **app.js**: Main JavaScript controller (2200+ lines)
- **index.html**: HTML template loaded at line 215: `<script src="js/app.js"></script>`

### **State Management**
```javascript
const state = {
    currentPage: 'start',
    activeGraph: null,
    qaSession: {...},
    pendingModifications: {...},
    entities: {},
    references: {},
    graph: {}
}
```

### **DOM Integration Points**

#### **Top Bar Elements**
- `#top-bar` → Navigation container
- `.page-btn[data-page]` → Page navigation buttons
- `#graph-file-selector` → Graph file dropdown
- `#save-graph-btn` → Save changes button
- `#revert-graph-btn` → Revert changes button

#### **AI Bar**
- `#ai-bar` → AI command interface
- `#ai-input` → AI command input field
- `#ai-submit` → Submit button

#### **Sidebar**
- `#sidebar` → Main sidebar container
- `#sidebar-toggle` → Toggle visibility button
- `.accordion[data-type]` → Entity type accordions (users, objectives, actions, etc.)
- `#references-list` → Specs/references display

#### **Page Containers**
- `#start-page` → Landing page
- `#discover-page` → Q&A discovery interface
- `#arrange-page` → Coming soon
- `#validate-page` → Version 2 feature
- `#define-page` → Coming soon
- `#build-page` → Version 2 feature

#### **Discover Page Components**
- `#current-question` → Active question display
- `#answer-input` → Answer textarea
- `#submit-answer` → Submit answer button
- `#skip-question` → Skip button
- `#expand-toggle` → Expand options toggle
- `#mc-options` → Multiple choice container
- `#extraction-choices` → Entity/connection proposals
- `#question-list` → Question queue display

### **Key Functions & Their DOM Interactions**

1. **navigateToPage()** → Updates page visibility, URL hash, manages top/AI bars
2. **loadSpecificGraph()** → Loads graph data, updates sidebar entities/references
3. **handleVisionSubmit()** → Processes initial vision input, navigates to discover
4. **handleAnswerSubmit()** → Processes Q&A answers, shows entity/connection proposals
5. **updateEntitiesReferences()** → Populates sidebar accordions with graph data
6. **displayCurrentQuestion()** → Renders active question in discover interface
7. **showModificationProposal()** → Displays entity/connection suggestions

### **Data Flow**
1. User enters vision → `#vision-input`
2. Graph loads → Updates state & sidebar
3. Questions generated → Q&A session begins
4. Answers processed → Entity/connections extracted
5. Modifications committed → Graph updated & saved