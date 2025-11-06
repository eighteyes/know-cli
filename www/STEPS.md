# Lucid Dream Workflow Steps

This document provides plain language step-by-step instructions for all workflows in the Lucid Dream application. These steps are derived from our automated test suite and represent the actual user interactions.

## Prerequisites

- The application should be running on `http://localhost:8880`
- Use mock mode (`?mock=true`) for testing to get predictable AI responses

---

## Text Entry Workflow

**Purpose**: Start a new session by entering your vision/idea and navigating to the main workspace.

Steps:

1. **Open the application** - You'll see the start page with "Lucid Dream" heading
2. **Enter your vision** - Type what you're dreaming about in the text input field
3. **Submit your entry** - Click the arrow button (→) to proceed
4. **Verify navigation** - You should automatically land on the Discover page
5. **Confirm setup** - The sidebar should be visible with navigation buttons and a question should appear

What You'll See:
- Page URL changes to include `#discover`
- Sidebar appears with sections for WHAT, HOW, and SPECS
- A question interface becomes available
- Navigation buttons (Start, Discover, Arrange, etc.) are visible

---

## JSON Load Workflow

**Purpose**: Load an existing graph file to work with pre-defined project data.

Steps:

1. **Start from the home page** - Ensure you're on the main start page
2. **Select a graph file** - Use the dropdown menu to choose `spec-graph.json`
3. **Wait for loading** - The system will automatically navigate to the Discover page
4. **Verify data loaded** - Check that the sidebar shows populated sections

What You'll See:
- Automatic navigation to the Discover page
- Sidebar sections (Users, Objectives, Actions) show with data
- The interface is ready for Q&A sessions
- Graph file selector shows the chosen file

---

## QA Refinement Basic Flow

**Purpose**: Go through the question-and-answer process to refine your project requirements.

**Note**: This workflow assumes starting with a new project. To work with existing data, use the JSON Load Workflow first.

Steps:
1. **Create new project** - Enter your vision/idea and click arrow (creates new empty graph based on your input)
2. **Activate mock mode** - Type `mock` in the AI command bar and press Enter
3. **Answer questions systematically**:
   - Read each question carefully
   - Type your answer in the text area
   - Click the "Answer" button
   - Repeat for the next question (typically 3 questions)
4. **Reach modification screen** - After answering 3 questions, you'll see suggested modifications

What You'll See:
- Questions appear one at a time
- After answering, new questions automatically appear
- Progress through the question sequence
- Eventually, a modifications screen with suggested entities and connections

---

## Modification and Connection Flow

**Purpose**: Review, select, and commit changes to your project structure based on Q&A insights.

Steps:
1. **Complete QA sequence** - Follow steps 1-4 from QA Refinement workflow
2. **Review suggestions** - Examine the list of detected modifications
3. **Select modifications** - Click the "+" button next to items you want to add
4. **Check pending changes** - Verify selected items appear in the "Pending Changes" section
5. **Commit changes** - Click the "Commit" button to save your selections
6. **Return to questions** - The system returns to Q&A mode with updated project data

What You'll See:
- List of suggested entities (users, features, interfaces, etc.)
- List of suggested connections between entities
- Pending changes section showing your selections
- Commit/Discard buttons to finalize or cancel changes
- Return to question interface after committing

---

## QA Expansion Workflow

**Purpose**: Get additional context and options for any question to make better informed decisions.

Steps:
1. **Get to a question** - Follow Text Entry workflow and load a graph file
2. **Activate mock mode** - Type `mock` in the AI command bar and press Enter
3. **Expand question options** - Click the "Expand Options ▼" button
4. **Review additional context** - Read through the multiple choice options and guidance
5. **Collapse when done** - Click "Collapse Options ▲" to return to normal view

What You'll See:
- Button changes from "Expand Options ▼" to "Collapse Options ▲"
- Additional sections appear: Recommendation, Tradeoffs, Alternatives, Challenges
- Multiple choice interface with selectable options
- Guidance text for making informed decisions

---

## QA Reorientation Workflow

**Purpose**: Use AI commands to quickly add specific entities and see related suggestions.

Steps:
1. **Start and load data** - Enter text, navigate to Discover, and load `spec-graph.json`
2. **Use an AI command** - Type a command like `add user tron` in the AI command bar
3. **Press Enter** - Submit the command to the AI system
4. **Review suggestions** - See entities and connections related to your command

What You'll See:
- Immediate transition to modification screen
- Suggested entities related to your command (e.g., "tron" related items)
- Suggested connections between the new and existing entities
- Option to select and commit the suggestions

---

## Basic UI Navigation

**Purpose**: Move between different sections of the application.

Steps:
1. **Start a session** - Enter text and click arrow to reach Discover page
2. **Use navigation buttons** - Click on different page buttons in the top toolbar:
   - **Start** - Returns to the initial input page
   - **Discover** - Main Q&A and project definition area
   - **Arrange** - Project organization view (future feature)
   - **Validate** - Validation tools (future feature)
   - **Define** - Definition refinement (future feature)
   - **Build** - Build preparation (future feature)
3. **Navigate between pages** - Click different buttons to switch views
4. **Return to main workspace** - Click "Discover" to return to the main working area

What You'll See:
- URL changes to reflect current page (e.g., `#arrange`, `#discover`)
- Different content loads for each section
- Navigation buttons highlight the current page
- Sidebar remains available in main working areas

---

## Sub-page Navigation Without Graph

**Purpose**: Understand what happens when navigating to sub-pages before loading project data.

Steps:
1. **Navigate directly to a sub-page** - Go to URLs like `#discover` or `#arrange` without loading a graph
2. **Observe the minimal interface** - Only the top navigation bar will be visible
3. **Try different sub-pages** - Click navigation buttons to move between sections
4. **Load a graph to activate interface** - Select a graph file to reveal working sections

What You'll See:
- **Top navigation bar remains visible** - You can always navigate between sections
- **Working interfaces are hidden** - Q&A sections, sidebars, and main content are not visible
- **Clean, minimal view** - Only essential navigation elements are shown
- **Graph selector available** - You can still load project data from any sub-page
- **Interface activates after loading** - Once you load a graph, all working sections become available

Important Notes:
- This behavior prevents confusion when no project data is loaded
- You must load a graph file to access the full working interface
- The top bar always remains functional for navigation
- This applies to all sub-pages except the Start page

---

## Tips for Success

1. **Use Mock Mode**: Add `?mock=true` to the URL for predictable testing
2. **Load Data First**: Always load `spec-graph.json` for full functionality
3. **Follow the Flow**: Complete Q&A sessions before expecting modification screens
4. **Watch for Visual Cues**: Buttons change text/appearance to show current state
5. **Be Patient**: Allow small delays for UI updates between actions

## Troubleshooting

- **Can't find dropdown**: Make sure you've navigated to Discover page first
- **No questions appearing**: Verify you've loaded a graph file and used mock mode
- **Modifications not showing**: Complete at least 3 Q&A cycles first
- **Navigation not working**: Ensure you're not on a placeholder page (Validate, Build)