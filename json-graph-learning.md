# JSON Graph Learning Log

## JSON Graph Evolution: Learnings from old/knowledge-map.json → spec-graph.json

### Major Structural Optimizations

#### **1. Hierarchical → Graph Database Transformation**
- **Before**: Flat sections with nested arrays (`stakeholders.user_types`, `core_features`, `platform_architecture`)
- **After**: Pure graph structure with explicit `depends_on` relationships
- **Benefit**: Enables graph traversal, dependency analysis, and impact assessment

#### **2. Eliminated Redundant Relationship Storage**
- **Before**: Capabilities stored in both user definitions AND permission matrices
- **After**: Single source of truth in graph section only
- **Benefit**: 50% smaller JSON, zero redundancy, easier maintenance

#### **3. Smart Content Reference Strategy**
- **Before**: No content deduplication, repeated descriptions everywhere
- **After**: References section for shared content, inline for unique content
- **Benefit**: Reduced duplication while avoiding over-abstraction

#### **4. Component Specialization Pattern**
- **Before**: Generic component definitions with unclear variations; UI components too general to capture specific interface needs
- **After**: `base_component` + `specialized_for` pattern with context-specific functionality arrays
- **Benefit**: Same base component, different contexts - owner fleet table focuses on ROI/financials while operator table focuses on real-time controls/emergency actions
- **Real Impact**: Solved the problem where fleet data-table screen has very different needs for owner vs operator users

#### **5. Structured Acceptance Criteria**
- **Before**: Scattered requirements mixed with descriptions
- **After**: Consistent `acceptance_criteria` with `functional`, `performance`, `integration`, `safety`, `reliability` categories
- **Benefit**: Clear validation requirements, testable specifications

#### **6. Versioned Feature Evolution**
- **Before**: Separate entities for different versions ("advanced-analytics" vs "ai-powered-analytics")
- **After**: Single feature with `evolution.v1` and `evolution.v2`
- **Benefit**: Clear feature progression, no duplicate entities

#### **7. Technical Architecture Separation**
- **Before**: Technical details mixed with business logic
- **After**: `references.technical_architecture`, `references.endpoints`, `references.libraries`
- **Benefit**: Clean separation of WHAT (entities) vs HOW (references)

#### **8. Explicit Dependency Modeling**
- **Before**: Implicit relationships buried in descriptions
- **After**: Pure dependency semantics with single `depends_on` arrays
- **Benefit**: Queryable relationships, impact analysis, circular dependency detection

### Query Performance Optimizations

#### **9. Flat Graph Structure**
- **Before**: Deep nesting required recursive traversal
- **After**: Flat `graph` section with direct key access
- **Benefit**: O(1) relationship access, faster jq queries

#### **10. Consistent Entity Naming**
- **Before**: Mixed naming conventions ("user_types", "core_features")
- **After**: Consistent `type:id` format ("user:owner", "feature:analytics")
- **Benefit**: Predictable queries, easier reverse lookups

#### **11. Type-Prefixed Keys**
- **Before**: Entity types unclear from keys alone
- **After**: `user:`, `screen:`, `component:`, `feature:` prefixes
- **Benefit**: Immediate type identification, better filtering

### Data Organization Improvements

#### **12. Entity-First Organization**
- **Before**: Feature-driven sections (`stakeholders`, `platform_architecture`, `core_features`)
- **After**: Entity-type sections (`users`, `screens`, `components`, `features`)
- **Benefit**: Consistent entity management, easier CRUD operations

#### **13. Meta and Project Separation**
- **Before**: System metadata mixed with business logic
- **After**: Clean `meta` section with project info separate from entities
- **Benefit**: Clear project boundaries, better tooling integration

#### **14. Roadmap Integration**
- **Before**: No explicit project planning
- **After**: `project.roadmap`, `project.milestones`, `project.strategic` sections
- **Benefit**: Clear project timeline, dependency tracking

#### **15. Schema Definitions**
- **Before**: Implicit data models buried in descriptions
- **After**: Explicit `schema` section with typed attributes
- **Benefit**: Clear data contracts, code generation potential

### Scalability Improvements

#### **16. Universal Tooling Compatibility**
- **Before**: Custom structure requiring specialized tools
- **After**: Standard JSON queryable with jq, grep, any JSON parser
- **Benefit**: Works anywhere JSON works, no special infrastructure

#### **17. Git-Friendly Structure**
- **Before**: Hard to diff, merge conflicts difficult
- **After**: Structured for readable diffs, mergeable changes
- **Benefit**: Better version control, easier collaboration

#### **18. Incremental Loading Capability**
- **Before**: Monolithic structure, all-or-nothing
- **After**: Modular sections that can be loaded independently
- **Benefit**: Better performance for large knowledge maps

### Maintenance Optimizations

#### **19. Single Responsibility Sections**
- **Before**: Mixed concerns in each section
- **After**: Clear separation: entities (WHAT), references (HOW), graph (WHERE)
- **Benefit**: Easier maintenance, clear ownership

#### **20. Validation-Ready Structure**
- **Before**: Hard to validate consistency
- **After**: Reference integrity, graph validation, acceptance criteria checking
- **Benefit**: Automated quality assurance, fewer inconsistencies

#### **21. Evolution-Friendly Design**
- **Before**: Adding new relationships required restructuring
- **After**: Add new entity types and relationships without breaking existing structure
- **Benefit**: Future-proof architecture, easy extensibility

## Latest Consolidations

### **22. Project Information Consolidation**
- **Action**: Merged root `project` section into `meta.project`
- **Eliminated**: Duplicate project sections causing confusion
- **Added**: Implementation phases based on dependency analysis (5 phases from Foundation → User Access)
- **Benefit**: All project data (roadmap, milestones, strategic, risks, phases) in single logical location

### **23. Removed Deprecated Query Infrastructure**
- **Action**: Eliminated `views` and `queries` sections
- **Reason**: Replaced by jq-based tooling and shell scripts
- **Benefit**: Simpler structure, faster queries, universal JSON tooling

### **24. Added User Actions Entity Type**
- **Action**: Added `user_actions` entity type as system mutation layer
- **Structure**: Clean properties (trigger_type, user_roles, state_mutation, acceptance_criteria)
- **Graph Integration**: Full dependency relationships with components, screens, UI elements
- **Benefit**: Completes user interaction model bridging UI → business logic

### **25. Refined Implementation Phases Structure**
- **Action**: Converted `implementation_phases` → `phases` array with `requirements` lists
- **Eliminated**: `depends_on` arrays from phases (order implies sequence)
- **Added**: Phase 6 "User Interactions" containing all user actions
- **Benefit**: Cleaner planning structure, phases serve as graph reinforcement points

### **26. Enhanced Dependency Detection and Auto-Resolution**
- **Action**: Added depth limiting (3 levels), cycle detection, and auto-resolve to dependency traversal
- **Implementation**: `./know/know query deps <entity> --resolve` triggers automatic circular dependency resolution
- **Traversal Limits**: MAX_DEPTH=3 prevents infinite loops in complex dependency chains
- **Cycle Detection**: Tracks visited entities to identify circular references during traversal
- **Auto-Resolution**: Integrates with canonical hierarchy resolver to fix violations automatically
- **Benefit**: Robust dependency analysis with built-in cycle protection and automatic remediation

### **27. Graph Tooling Parameterization and Semantic Rename**
- **Action**: Parameterized all graph analysis tools and renamed `knowledge-map-cmd.json` → `spec-graph.json`
- **Implementation**:
  - Active tools (`know/lib/mod-graph.sh`, `know/lib/query-graph.sh`) now accept `--file|-f <graph-file>` parameter
  - All 21 legacy analysis scripts updated to use `spec-graph.json` as default
  - Bulk update of 84+ references across scripts, documentation, and examples
- **Semantic Improvement**: New name `spec-graph.json` better reflects content (specification/schema) vs operational nature
- **Flexibility**: All tools can now work with multiple graph files for testing, comparison, or different projects
- **Migration Strategy**: Preserved backward compatibility through parameterization rather than breaking existing workflows
- **Benefit**: Universal tool flexibility while maintaining semantic clarity and avoiding breaking changes

## 2025-01-11: Entity Naming Conventions Improvement

### Problem Identified
Inconsistent naming patterns across entity categories made the graph harder to navigate and maintain:
- Duplicate names across different categories (e.g., `maintenance-orders` in both components and schema)
- Inconsistent role prefixing in components
- Mixed suffix patterns in features
- Unclear UI component names

### Solutions Applied

#### 1. Role-Based Component Naming
**Before:** `owner-fleet-table`, `operator-fleet-table`, `teleoperator-robot-controls`
**After:** `fleet-table-owner`, `fleet-table-operator`, `robot-controls-teleoperator`
**Learning:** Suffix pattern makes the base component clear while indicating specialization

#### 2. Consistent Feature Suffixes
**Before:** `analytics`, `maintenance-alerts`, `parts-ordering-system`
**After:** `analytics-system`, `maintenance-alert-system`, `parts-ordering-system`
**Learning:** Consistent "-system" suffix clarifies these are feature systems, not just concepts

#### 3. Schema/Model Clarity
**Before:** Mixed use of `robot-fleet`, `mission-data`, `maintenance-orders`
**After:** All use `-model` suffix: `robot-fleet-model`, `mission-data-model`, `maintenance-order-model`
**Learning:** Explicit model suffix prevents confusion with similarly named components

#### 4. UI Component Descriptiveness
**Before:** `glass-morphism`, `interactive-buttons`
**After:** `glassmorphism-style`, `button-system`
**Learning:** Technical terms should be single words; systems should be labeled as such

### Implementation Approach

Used jq for safe batch renaming:
```bash
# Safe rename function that checks existence first
def safe_rename_components:
  if .entities.components then
    .entities.components |= with_entries(
      if .key == "old-name" then .key = "new-name"
      else . end
    )
  else . end;

# Update both entities and graph references simultaneously
safe_rename_components |
.graph |= with_entries(
  # Update keys and their connections
)
```

### Key Takeaways

1. **Naming Patterns Should Be Category-Specific:**
   - Components: base-component-role
   - Features: feature-system
   - Schema: entity-model
   - UI: descriptive-type

2. **Avoid Duplicate Names Across Categories:**
   - Even with namespace prefixes, unique names reduce confusion
   - If similar concepts exist, differentiate clearly (e.g., `maintenance-order-manager` vs `maintenance-order-model`)

3. **Batch Operations Need Reference Updates:**
   - Always update graph connections when renaming entities
   - Use transaction-like operations (backup → transform → validate)

4. **Validation is Critical:**
   - Run validation after bulk renames
   - Check for broken references in both directions
   - Remove references to non-existent entities

### Tools Enhanced

The `mod-graph.sh` script's validation caught broken references effectively, though some false positives occurred (e.g., `component:camera-feed` warning despite entity existing).

### Future Improvements

1. Consider adding a naming convention validator to prevent inconsistencies
2. Add automated reference fixing when renaming entities
3. Create naming guidelines documentation for each entity type
4. Implement entity aliasing for backward compatibility during transitions

## 2025-01-11: WHAT vs HOW Dependency Flow Clarification

### Problem Identified
The original dependency flow documentation was confusing:
- **WHAT**: Project → User → Functionality → Implementation
- **HOW**: Project → Platform → Requirements → Interface → Feature → Action → Component → UI → Data Models

The term "Implementation" in the WHAT flow was ambiguous - what entity type does it map to?

### Analysis Process

1. **Initial Confusion**: "Implementation" seemed to suggest it was part of the business flow, but we had no "implementation" entity type
2. **Integration Points Review**: CLAUDE.md stated "Implementation → Action / Component"
3. **Entity Type Analysis**: We have `user_actions` which represents how users interact with the system
4. **Realization**: Actions are the business-level implementation of functionality

### Solution Applied

#### Clarified Dependency Flows:
**WHAT (Business Perspective)**: Project → User → Functionality → **Actions**
- Users define WHO uses the system
- Functionality defines WHAT the system does
- Actions define HOW users interact (business implementation)

**HOW (Technical Infrastructure)**: Platform → Requirements → Interface → Feature → Action → Component → UI → Data
- The technical flow that implements the business needs

**Integration Points**:
- User → Requirements (business needs to technical constraints)
- Functionality → Features (what needs to be done to how it's delivered)
- **Actions → Components** (business actions to technical implementation)

### Implementation in know CLI

Updated `know list` command to properly group entities:

**WHAT Section (20 entities)**:
- `users` (7) - WHO uses the system
- `functionality` (8) - WHAT the system does
- `user_actions` (5) - Actions users take

**HOW Section (68 entities)**:
- `platforms` (3) - Infrastructure foundation
- `requirements` (6) - System constraints
- `screens` (6) - User interfaces
- `features` (9) - System capabilities
- `components` (32) - Technical components
- `ui_components` (6) - UI building blocks
- `schema` (6) - Data structures

### Key Insights

1. **Actions Bridge WHAT and HOW**: User actions are the final step in the business flow that maps directly to technical components
2. **Clear Separation**: WHAT focuses on users and their needs, HOW focuses on technical implementation
3. **Integration is Key**: The three integration points (User→Requirements, Functionality→Features, Actions→Components) are where business meets technical

### Visual Improvement

Added flow visualization to `know list` output:
```
🎯 WHAT (Business Perspective)
Flow: Project → User → Functionality → Actions
Integration: User→Requirements, Functionality→Features, Actions→Components

🔧 HOW (Technical Infrastructure)
Flow: Platform → Requirements → Interface → Feature → Action → Component → UI → Data
```

### Lessons Learned

1. **Terminology Matters**: Ambiguous terms like "Implementation" need clear definition
2. **Entity Mapping**: Every step in a dependency flow should map to actual entity types
3. **User Actions are Business Logic**: Actions represent business-level implementation, not technical
4. **Clear Grouping Helps Understanding**: Separating WHAT from HOW makes the system architecture clearer

### Future Improvements

1. Consider renaming `user_actions` to just `actions` for clarity
2. Add validation to ensure entities follow the dependency hierarchy
3. Create visualization tools that show the WHAT→HOW integration points
4. Document which entity types belong in WHAT vs HOW in the schema itself

## 2025-01-11: Graph Structure Normalization and Cleanup

### Problem Identified
The spec-graph.json file had accumulated redundant and inconsistent structures:
- Duplicate `project` section at root level and in meta
- Unnecessary meta fields (roadmap, milestones, strategic, risks) better suited for separate docs
- Phase requirements stored in meta instead of the graph
- Descriptions stored in a separate references section requiring lookups

### Issues with Original Structure

#### 1. Duplicate Project Data
**Problem:** Project information existed in both root level and meta.project
**Solution:** Removed root `project` section, kept meta.project as single source
**Learning:** Avoid data duplication; maintain single source of truth

#### 2. References Section Indirection
**Problem:** Descriptions stored in `references.descriptions` with `description_ref` pointers
**Example:** `"description_ref": "fleet-dashboard-desc"` requiring lookup
**Solution:** Migrated all descriptions directly into entities
**Learning:** Direct embedding reduces complexity and improves query performance

#### 3. Phase Requirements in Wrong Location
**Problem:** Requirements in `meta.project.phases[].requirements` weren't in the graph
**Solution:** Created proper graph entries for phase requirements with dependencies
**Learning:** All relationships belong in the graph for consistent traversal

### Migration Process

Used jq transformations for safe, atomic migrations:

```bash
# Step 1: Remove redundant sections
jq 'del(.project) |
    del(.meta.project.roadmap) |
    del(.meta.project.milestones) |
    del(.meta.project.strategic) |
    del(.meta.project.risks)' spec-graph.json

# Step 2: Migrate phase requirements to graph
jq '.meta.project.phases as $phases |
    .graph += ($phases | to_entries | map({
      key: "phase:\(.value.id)",
      value: {depends_on: .value.requirements}
    }) | from_entries)'

# Step 3: Migrate descriptions from references
jq '.references as $refs |
    .entities |= with_entries(
      .value |= with_entries(
        .value |= (
          if .description_ref and $refs.descriptions[.description_ref] then
            . + {description: $refs.descriptions[.description_ref]} | del(.description_ref)
          else .
          end
        )
      )
    ) | del(.references)'
```

### Results Achieved

- **File size reduced by ~20%** through redundancy elimination
- **Cleaner structure** with all descriptions embedded in entities
- **No more reference lookups** needed for descriptions
- **Phase requirements** properly represented in dependency graph
- **Validation passes** with only false positives

### Key Learnings

1. **Normalization Benefits:**
   - Eliminates data inconsistency risks
   - Reduces file size and complexity
   - Improves query performance

2. **Migration Best Practices:**
   - Always backup before structural changes
   - Use atomic transformations (all-or-nothing)
   - Validate after each migration step
   - Test dependent tools after changes

3. **Structure Design Principles:**
   - Embed frequently accessed data (descriptions)
   - Keep relationships in the graph
   - Avoid indirection unless necessary
   - Maintain single source of truth

4. **Tool Compatibility:**
   - Component generators needed library sourcing fixes
   - Required proper library loading order: utils → query → resolve → render
   - Template rendering issues surfaced after migration (separate concern)

### Validation Observations

The mod-graph.sh validator reported false positives (e.g., `component:alert-generator` exists but marked as broken), suggesting the validator may need updates for the new structure.

### Future Improvements

1. Update validator to handle embedded descriptions properly
2. Fix template rendering to work with normalized structure
3. Add migration scripts to project for future schema changes
4. Document the canonical structure in a schema file

## 2025-01-11: Unified Graph Implementation and Entity Type Renaming

### Problem Identified
Multiple issues with the knowledge graph implementation:
1. **Fragmented dependency information**: The `know check` command reported "No dependencies defined" even though dependencies existed in the graph section
2. **Confusing entity type**: `user_actions` was verbose and unclear in the WHAT/HOW hierarchy
3. **Lookup mismatch**: Query functions were looking for dependencies in the wrong place (`.graph[$entity].outbound` instead of `.graph[$entity].depends_on`)

### Root Cause Analysis

The spec-graph.json had evolved to have a unified structure where:
- **Entities section**: Contains entity definitions with metadata
- **Graph section**: Contains all relationship information (dependencies, connections, phases)

However, the query functions were still looking for an older structure with `.outbound` relationships that no longer existed.

### Solutions Applied

#### 1. Fixed Dependency Lookups
**Before:**
```bash
get_dependencies() {
    jq -r --arg entity "$entity_ref" '
        .graph[$entity].outbound | to_entries[] |
        select(.key | test("requires|uses|depends_on")) |
        .value[]
    ' "$KNOWLEDGE_MAP"
}
```

**After:**
```bash
get_dependencies() {
    jq -r --arg entity "$entity_ref" '
        .graph[$entity].depends_on[]? // empty
    ' "$KNOWLEDGE_MAP"
}
```

#### 2. Renamed user_actions to actions
**Changes made:**
- Renamed entity type from `user_actions` to `actions` in spec-graph.json
- Updated all references from `user_action:` to `action:`
- Updated type field from `"user_action"` to `"action"`
- Added mapping in `normalize_entity_type()`: `action) echo "actions"`

**Benefits:**
- Cleaner, more concise naming
- Better alignment with WHAT flow: User → Functionality → **Actions**
- Clearer that Actions bridge WHAT and HOW (Actions → Components)

#### 3. Fixed Reverse Dependency Lookups
**Before:**
```bash
get_dependents() {
    jq -r --arg entity "$entity_ref" '
        .graph | to_entries[] |
        select(.value.outbound | to_entries[] |
               select(.key | test("requires|uses|depends_on")) |
               .value[] == $entity) |
        .key
    '
}
```

**After:**
```bash
get_dependents() {
    jq -r --arg entity "$entity_ref" '
        .graph | to_entries[] |
        select(.value.depends_on[]? == $entity) |
        .key
    '
}
```

### Implementation Details

#### Files Modified:
1. **spec-graph.json**:
   - Renamed `.entities.user_actions` to `.entities.actions`
   - Updated all entity types from `"user_action"` to `"action"`
   - Updated all references from `"user_action:"` to `"action:"`

2. **know/lib/query.sh**:
   - Fixed `get_dependencies()` to read from `.graph[$entity].depends_on[]`
   - Fixed `get_dependents()` to search for entity in depends_on arrays

3. **know/lib/utils.sh**:
   - Added `action) echo "actions"` to `normalize_entity_type()`

4. **know/lib/mod-graph.sh**:
   - Updated WHAT section to show `actions` instead of `user_actions`
   - Updated hierarchy references

5. **scripts/mod-graph.sh**:
   - Updated action references in hierarchy documentation

### Testing and Validation

All commands now work correctly:
```bash
# Check command finds dependencies
./know/know check feature real-time-telemetry
✅ Dependencies: 3 found

# Action entities work properly
./know/know check action emergency-stop-robot
✅ Entity name: Emergency Stop Robot
✅ Description: Immediately halt all robot operations...

# Dependencies traverse correctly
./know/know deps action:emergency-stop-robot
📦 Dependency chain for 'action:emergency-stop-robot':
  🎯 action:emergency-stop-robot (action: Emergency Stop Robot) [ROOT]
  📋 component:robot-controls (component: Robot Control Interface)
  ...

# Impact analysis works
./know/know impact component:robot-controls
💥 Impact analysis for 'component:robot-controls':
  ⚡ action:emergency-stop-robot (action: Emergency Stop Robot)
  ...
```

### Key Insights

1. **Unified Structure is Powerful**: Separating entity definitions (entities section) from relationships (graph section) creates a clean, maintainable structure

2. **Naming Matters for Understanding**: Renaming `user_actions` to `actions` immediately clarified the WHAT/HOW relationship

3. **Query Functions Must Match Data Structure**: When the data structure evolves, all query functions must be updated to match

4. **Testing Reveals Integration Issues**: The user's observation that "know check doesn't understand dependencies" revealed the disconnection between data structure and query implementation

### Lessons Learned

1. **Always Test End-to-End**: A change in data structure must be validated through all commands that read that data

2. **Simplify Entity Names**: Shorter, clearer names (actions vs user_actions) improve understanding and reduce typing

3. **Document Structure Changes**: When evolving from one structure to another, document both the old and new patterns

4. **Unified vs Distributed Data**: The unified approach (entities + graph) is cleaner than having dependencies scattered throughout entity definitions

### Future Improvements

1. Add structure validation to ensure graph references only point to existing entities
2. Create migration scripts when renaming entity types to update all references automatically
3. Add integration tests that verify all query commands work after structure changes
4. Consider versioning the spec-graph.json structure for backward compatibility

## 2025-01-13: Specification Generation Template Standards

### Problem Identified
Initial spec generation templates contained formatting issues and included fabricated implementation details not sourced from the knowledge graph.

### Issues Found in Generated Specs

#### 1. Key Name Exposure
**Problem:** Technical key names like `map-rendering_under_2_seconds` were shown to users
**Solution:** Display user-friendly descriptions instead of internal keys
**Learning:** Acceptance criteria should read naturally, not expose internal naming

#### 2. Emoji Overuse
**Problem:** Excessive use of emojis (✅❌⚠️) cluttered the professional documentation
**Solution:** Remove emojis entirely, use markdown checkboxes for acceptance criteria
**Learning:** Professional specs should be clean and emoji-free

#### 3. Fabricated Implementation Details
**Problem:** Templates included implementation notes not derived from knowledge graph data
**Example:** "Use MapBox GL for high-performance map rendering" - not in source data
**Solution:** Only include information that exists in the knowledge graph
**Learning:** Never invent technical details; only document what's explicitly defined

#### 4. Validation/Priority Sections
**Problem:** Added validation criteria and priority ratings without basis in data
**Solution:** Remove sections that aren't supported by knowledge graph content
**Learning:** Stick to what's actually defined in the graph schema

### Template Improvements Applied

#### 1. Dependencies Formatting
**Before:**
```json
{
  "data_sources": ["telemetry-stream", "robot-status-api"],
  "ui_framework": "react"
}
```

**After:**
```markdown
### Dependencies

### Features
- real-time-telemetry

### Data Sources

#### Robot Fleet Model
- **Description**: Window washing drones and pressure washing rovers
- **Attributes**:
  - device-id: UUID
  - model-type: STRING
  - status: ENUM[operational,maintenance,offline,error]
```

#### 2. Acceptance Criteria Format
**Before:** `- ✅ **displays_robot_positions_accurately** - Component must show...`
**After:** `- [ ] Component must show precise robot locations on the map`

#### 3. Data Model Expansion
**Improvement:** Expanded data sources to show full schema with attributes and types
**Learning:** Users need to see the actual data structures they'll work with

### Knowledge Graph Quality Insights

During spec generation analysis, discovered critical completeness issues:
- **9 features analyzed, 0% completeness rate**
- All features missing descriptions and acceptance criteria
- All features isolated (no dependencies defined)
- Best spec candidate: `component:fleet-status-map` (complete with acceptance criteria)

### Template Best Practices Established

1. **Source Truth:** Only include information present in knowledge graph
2. **Clean Formatting:** Use markdown checkboxes, no emojis, readable descriptions
3. **Data Model Transparency:** Show full schema details for data sources
4. **Dependency Clarity:** Expand JSON into readable lists with descriptions
5. **Professional Tone:** Remove validation sections and priority ratings

### Tools Enhanced

The gap analysis revealed the need for:
- Feature completeness validation scripts (`scripts/analyze-features.sh`)
- Best spec candidate identification (`scripts/check-features.sh`)
- Template generation that respects data boundaries

### Future Template Improvements

1. Auto-expand all dependency references to show names and descriptions
2. Validate acceptance criteria format consistency across entity types
3. Add schema validation for required fields before spec generation
4. Create template variants for different entity types (feature vs component vs screen)

## 2025-01-17: Renaming Functionality to Objectives

### Problem Identified
The term "Functionality" in the Graph Dependency Map was ambiguous and didn't clearly convey its purpose as high-level business objectives that the system aims to achieve.

### Solution Applied
Renamed "Functionality" to "Objectives" throughout the system to better reflect that these entities represent business goals and objectives rather than implementation details.

### Changes Made

#### 1. CLAUDE.md Graph Dependency Map
**Before:**
```
WHAT: Project → User → Functionality → Actions
Integration: User → Requirements, Functionality → Features, Actions → Components
```

**After:**
```
WHAT: Project → User → Objectives → Actions
Integration: User → Requirements, Objectives → Features, Actions → Components
```

#### 2. spec-graph.json Entity Structure
- Renamed entity section from `functionality` to `objectives`
- Updated all entity IDs from `functionality:*` to `objectives:*`
- Changed type field from `"functionality"` to `"objectives"`
- Updated all dependency references throughout the graph

#### 3. Script Updates
Updated both `know/lib/mod-graph.sh` and `scripts/mod-graph.sh` to:
- Reference `objectives` instead of `functionality` in entity lists
- Update flow descriptions and comments
- Adjust hierarchy level mappings

## 2025-01-17: Critical Warning - AI Hallucinations During Structure Analysis

### Problem Identified
When asked to explain the core structure of spec-graph.json, the AI completely fabricated fields and relationships that don't exist in the actual data.

### Fabricated Elements
The AI incorrectly claimed entities had:
- **priority** field (doesn't exist)
- **tags** field (doesn't exist)
- Dependency types like "provides", "interacts_with", "requires" (actual graph uses "validates", "allowed_for", etc.)

### Root Cause
The spec-graph.json structure had recently been transformed, with the graph section changing from a flat object (entity IDs as keys) to a structured format with an "edges" array. The AI was mixing up different versions and inventing fields rather than checking the actual current structure.

### Lesson Learned
**NEVER trust AI explanations of data structures without verification.** Always:
1. Check the actual file structure with commands like `jq`
2. Verify field names and relationships exist before accepting explanations
3. Look for backup files when structures seem wrong
4. Question when the AI starts listing fields that seem too generic or convenient

### Recovery Process
1. Located backup files with correct structure (`spec-graph.json.backup` had the original format)
2. Extracted just the graph portion from backup
3. Replaced the corrupted graph section while preserving other changes
4. Validated the restoration worked correctly

### Key Takeaway
When working with evolving data structures, AIs can conflate different versions or completely hallucinate fields. Always verify against the actual data, especially after structural migrations or when the AI's explanation seems suspiciously detailed or generic.
