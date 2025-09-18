# JSON Graph Learning Log

## 2025-01-17: Reference Validation and Connection Tools

### Problem
After flattening references, discovered that all 110 reference keys were orphaned (not connected to any entities). The graph structure stores dependencies as `entity -> reference:key`, but there was no tooling to:
1. Validate which reference keys lack parent entities
2. Connect orphaned references to appropriate entities
3. Understand the dependency graph structure differences

### Solution
Created comprehensive tooling for reference management:
1. **Check tool** (`know check references`) - Validates all reference keys have parent entities
2. **Connect tool** (`know connect-references`) - Interactive and batch modes for connection
3. **Graph structure understanding** - Dependencies stored as object with `depends_on` arrays, not edge list

### Key Insights

1. **Graph Structure is Object-Based, Not Edge-Based**
   - Graph is `{ "entity:id": { "depends_on": [...] } }`
   - NOT an array of edges like `[{ source, target }]`
   - Must traverse backwards to find parents (who depends on this?)

2. **Reference Keys Must Be Fully Qualified**
   - References connect as `category:key` (e.g., `technical_architecture:api_gateway`)
   - Entities check requires parsing type:id format
   - Must handle singular/plural conversions (feature/features)

3. **Interactive Tools Need Non-Interactive Fallbacks**
   - FZF tools won't work in CI/CD or non-terminal environments
   - Default to list mode when not interactive
   - Provide batch mode for automation

4. **Entity Types vs Individual Entities**
   - `.entities` contains types (features, components, etc.)
   - Individual entities are nested: `.entities.components["fleet-status-map"]`
   - Must check entity existence differently than simple key lookup

### Implementation Details

**check-reference-parents.sh**:
- Traverses graph backwards using jq to find parents
- Checks if parents are entities (not just other references)
- Groups orphaned keys by reference category for readability
- Supports JSON output for programmatic use

**connect-references.sh**:
- Lists all individual entities (not just types)
- Shows reference value and entity description side-by-side
- Multi-select with Tab for connecting to multiple entities
- Batch mode for connecting all keys from a reference at once

### Results
- Identified 110 orphaned reference keys immediately
- Connected 4 technical_architecture keys as proof of concept
- Tools now integrated into main `know` command
- Clear path forward for connecting remaining references

### Lessons for Future Tools

1. **Always understand the data structure first**
   - Don't assume edge lists or standard graph formats
   - Check actual JSON structure before writing traversal logic

2. **Build for both interactive and automated use**
   - Interactive mode for developer experience
   - List/batch modes for CI/CD and automation
   - JSON output for integration with other tools

3. **Test with real data immediately**
   - Initial script checked wrong entity structure
   - Testing revealed need for type:id parsing
   - Real usage exposed the 110 orphaned keys issue

## 2025-01-17: Reference Structure Simplification

### Problem
References had become overly nested with unnecessary metadata:
- Generic categories like `content` and `design` containing nested structures
- Each reference had `name`, `description`, `id` fields adding no value
- References like `design.button-styles.id` were awkward to use
- 70% of references were orphaned (not connected to any entities)

### Solution
Flattened references to granular, specific items:
- Removed wrapper categories (buttons, button-styles, chart-styles, etc.)
- Created specific keys: `labels:emergency-stop-btn`, `styles:primary-btn`
- Removed all metadata fields (name, description, id)
- Preserved arrays where appropriate (typography.sizes, spacing)

### Key Insights
1. **References should be granular items, not collections**
   - DO: `labels:login-btn`, `styles:modal-overlay`
   - DON'T: `buttons.primary_actions.submit`

2. **Reference keys should be specific and meaningful**
   - The key itself is the identifier, no need for an `id` field
   - Keys should describe what they are, not what category they're in

3. **Flat is better than nested for references**
   - Makes references more discoverable
   - Easier to connect to entities
   - Clearer what each reference represents

### Implementation
- Created `know/lib/ref-usage-simple.sh` for usage analysis
- Added `ref-usage` command to query-graph.sh
- Used grep-based counting instead of complex jq queries for performance
- Temp file approach for dependency lookup to avoid blocking

### Results
- Reduced reference complexity by ~60%
- Improved reference discoverability
- Cleaner, more maintainable structure
- Better alignment with "nodes are granular items" principle

## 2025-01-11: Entity Naming Conventions & WHAT vs HOW Clarification

### Entity Naming Improvements
- **Role-Based Components**: `fleet-table-owner` pattern (suffix indicates specialization)
- **Feature Suffixes**: Consistent `-system` suffix for feature systems
- **Schema Clarity**: All data models use `-model` suffix
- **Learning**: Naming patterns should be category-specific and avoid cross-category duplicates

### WHAT vs HOW Dependency Flow Clarification
- **WHAT (Business)**: Project → User → Objectives → Actions
- **HOW (Technical)**: Platform → Requirements → Interface → Feature → Action → Component → UI → Data
- **Integration Points**: User→Requirements, Objectives→Features, Actions→Components
- **Learning**: Actions bridge WHAT and HOW - they're business-level implementation

### Graph Structure Normalization
- Removed duplicate `project` section (kept only meta.project)
- Migrated descriptions from references directly into entities
- Phase requirements moved to graph for consistent traversal
- **Learning**: Avoid indirection; embed frequently accessed data

### Unified Graph Implementation
- Fixed dependency lookups (`.depends_on[]` not `.outbound`)
- Renamed `user_actions` to `actions` for clarity
- **Learning**: Query functions must match data structure evolution

## 2025-01-13: Specification Generation Standards

### Template Quality Issues Fixed
- Removed technical key name exposure
- Eliminated emoji overuse in professional docs
- Stopped fabricating implementation details not in graph
- **Learning**: Only include information present in knowledge graph

### Graph Completeness Analysis
- Discovered 9 features with 0% completeness rate
- All features missing descriptions and dependencies
- **Learning**: Template generation reveals data quality issues

## 2025-01-15: Tool Consolidation & Validation Infrastructure

### Scripts → Know Tool Migration
- Consolidated 21 scripts into unified Know tool
- Added `know health` and `know repair` commands
- **Learning**: 80/20 rule - integrate the 20% of features used 80% of the time

### Graph Validation Infrastructure Created
- Comprehensive validator for structure, references, and dependency chains
- Created `dependency-rules.json` encoding CLAUDE.md rules
- Fixed 20+ dependency violations and reference inconsistencies
- **Learning**: Systematic validation critical; manual maintenance leads to drift

## 2025-01-16: Path Resolution & Dependency Restoration

### Dynamic Path Resolution
- Fixed hardcoded `/workspace/lb-www` paths
- Pattern: `PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"`
- Environment variables with fallbacks: `${KNOWLEDGE_MAP:-$PROJECT_ROOT/.ai/spec-graph.json}`
- **Learning**: Always use relative paths or environment variables

### Graph Dependency Recovery
- Restored ~2000 dependency relationships from backup
- Fixed entity type pluralization (singular in graph, plural in entities)
- **Learning**: Dependencies are the core value - without them it's just a list

## 2025-01-17: Entity Type Renaming & Structure Analysis

### Renamed Functionality to Objectives
- Better reflects business goals vs implementation
- Updated throughout: CLAUDE.md, spec-graph.json, scripts
- **Learning**: Clear terminology improves understanding

### Critical Warning: AI Hallucinations
- AI fabricated fields (priority, tags) that didn't exist
- Mixed different structure versions when explaining
- **Learning**: NEVER trust AI explanations without verification against actual data

## 2025-01-18: Graph Redundancy Removal & Script Centralization

### Removed Presentation Entity Duplication
- Eliminated `entities.presentation` that duplicated `references.design`
- Flattened design structure: `design.components.buttons` → `design.button-styles`
- Updated dependencies from `presentation:*` to `design:*`
- Fixed entity prefixes: `actions:` → `action:`
- **Learning**: Don't duplicate references as entities; maintain prefix consistency

### Centralized Graph Operations
- Replaced direct JQ with mod-graph.sh and query-graph.sh
- Benefits: Consistency, maintainability, cleaner API
- **Learning**: Centralize operations through dedicated scripts

### Graph Relationship Management Principles
- **Critical**: Relationships ONLY in graph section, never as entity attributes
- References are flat key-value stores, not complex structures
- **Learning**: Graph is the single source of truth for all relationships

## Key Architectural Principles Established

### Structure Evolution Summary
1. **Hierarchical → Graph Database**: Enables traversal and impact analysis
2. **Redundant → Single Source**: 50% size reduction, zero redundancy
3. **Mixed Concerns → Separation**: Entities (WHAT), References (HOW), Graph (RELATIONSHIPS)
4. **Deep Nesting → Flat Structure**: O(1) access, faster queries
5. **Inconsistent → Standardized**: `type:id` format throughout

### Validation & Maintenance
- Run `npm run validate-graph` after changes
- Dependency chains must follow CLAUDE.md hierarchy
- All entity references must match exactly across sections
- Use atomic transformations for structural changes

### Common Pitfalls
1. Adding relationships as entity attributes (use graph instead)
2. Creating complex reference structures (keep them flat)
3. Inconsistent naming (singular vs plural confusion)
4. Forgetting to validate after bulk changes
5. Trusting AI explanations without verification

## Historical Context: Evolution from knowledge-map.json → spec-graph.json

### Major Optimizations Applied
- Component specialization pattern (base + context)
- Structured acceptance criteria (functional, performance, integration)
- Technical architecture separation (references vs entities)
- Versioned feature evolution (v1, v2 in same feature)
- Git-friendly structure for better collaboration
- Universal tooling compatibility (standard JSON)

### Performance Improvements
- Query performance: Deep nesting → flat O(1) access
- File size: 50% reduction through deduplication
- Maintenance: Single source of truth for all data
- Validation: Automated quality assurance

## Current Best Practices

### Graph Modifications
1. Backup before structural changes
2. Use atomic transformations
3. Validate after each step
4. Test dependent tools

### Naming Conventions
- Entity types: plural (users, features)
- Graph prefixes: singular (user:, feature:)
- References: category:name format

### Dependency Management
- Follow CLAUDE.md hierarchy
- Update dependency-rules.json when changing
- Validate chains after modifications

### Tool Usage
- Prefer mod-graph/query-graph over direct JQ
- Handle colored output appropriately
- Maintain abstraction layer