# Know Tool - Example Outputs

This document contains example outputs for every command in the `know` tool to help developers understand what each command does and what output to expect.

---

## Table of Contents

1. [Generate Specifications](#generate-specifications)
2. [Generate Artifacts](#generate-artifacts)
3. [Browse & Discover](#browse--discover)
4. [Connection & Health](#connection--health)
5. [Explore Dependencies](#explore-dependencies)
6. [Graph Maintenance](#graph-maintenance)
7. [Phase Management](#phase-management)

---

## Generate Specifications

### `know feature <entity_id>`
Generate feature specification from knowledge map.

```bash
$ know feature real-time-telemetry
```

**Output:**
```markdown
# Feature Specification: Real-Time Telemetry

**Entity Reference:** `feature:real-time-telemetry`
**Completeness Score:** 75%
**Generated:** Sat Sep 20 23:29:03 UTC 2025

## Overview
Live position, altitude, battery status, environmental data, and mission progress with 5-10s freshness

## Implementation Status
✅ **READY FOR IMPLEMENTATION** (75% complete)

## Dependencies
*No direct dependencies defined*

## Acceptance Criteria
⚠️ **No acceptance criteria defined**

To improve this specification, add acceptance criteria using:
```bash
# Add functional criteria
./know/know add-criteria feature:real-time-telemetry functional "Must handle X concurrent users"

# Add performance criteria
./know/know add-criteria feature:real-time-telemetry performance "Response time < 200ms"
```

## Technical Architecture
### Infrastructure Components

**API Gateway**: AWS API Gateway
  - Base URL: https://api.lucidbots.com
  - Handles authentication, rate limiting, and routing

**Message Broker**: Apache Kafka
  - Handles asynchronous communication between services

**Primary Database**: PostgreSQL
  - Version: 15.2
  - Persistent data storage and transactions
```

### `know component <entity_id>`
Generate component specification from knowledge map.

```bash
$ know component fleet-status-map
```

**Output:**
```markdown
# Component: Fleet Status Map

## Overview
Real-time fleet status map with device health indicators, active mission assignments, and maintenance alert prioritization

## Functionality

## Testing Strategy

### Unit Tests
- Component rendering
- User interactions
- State management
- Prop validation

### Integration Tests
- Data model integration
- Feature implementation
- API connectivity
- Real-time updates

### Accessibility Tests
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader compatibility
- Color contrast validation
```

### `know screen <entity_id>`
Generate screen/UI specification.

```bash
$ know screen teleoperation-interface
```

**Output:**
```
Error: Cannot generate specification - entity completeness too low (50%)

❌ Minimum completeness required: 70%
📊 Current completeness: 50%
📈 Need: 20% more completeness

🔧 Fix gaps first:
  know gaps screen:teleoperation-interface
  know validate screen:teleoperation-interface --comprehensive

Then retry specification generation.
```

**Note:** Many screen entities need higher completeness before generating specifications. Use `know health --gaps` to identify missing data.

### `know package <entity_id>`
Generate complete implementation package.

```bash
$ know package teleoperation-interface
```

**Output:**
```
Generating implementation package for feature:fleet-dashboard
# Implementation Package: fleet-dashboard

## Main Entity Specification

Generating feature specification for feature:fleet-dashboard
...
```

**Note:** Package generation may timeout for complex entities. Use `timeout` command to limit execution time if needed.

### `know test <entity_ref>`
Generate test scenarios for an entity.

```bash
$ know test feature:real-time-telemetry
```

**Output:**
```markdown
# Test Scenarios: Real-Time Telemetry

## Overview
Test scenarios generated from acceptance criteria for feature:real-time-telemetry

No acceptance criteria found - cannot generate test scenarios
```

**Note:** Test generation requires acceptance criteria to be defined in the graph. Use the graph modification tools to add criteria first.

---

## Generate Artifacts

### `know sitemap`
Generate sitemap with page hierarchy.

```bash
$ know sitemap
```

**Output:**
```
(Note: Command may timeout or produce no output - depends on graph complexity)
```

**Note:** Sitemap generation may timeout for large graphs. Consider using smaller entity subsets or adding timeout limits.

### `know routes`
Generate all pages and API endpoints.

```bash
$ know routes
```

**Output:**
```
(Note: Command may timeout or produce no output - depends on graph complexity)
```

**Note:** Routes generation may timeout for large graphs. Consider using smaller entity subsets or adding timeout limits.

### `know implementation-chain <entity_ref>`
Generate full implementation plan showing dependency chain.

```bash
$ know implementation-chain feature:real-time-telemetry
```

**Output:**
```
🔗 Building Implementation Chain: feature:real-time-telemetry
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 This feature will likely need:

📋 Requirements:
  • Security requirements (authentication, authorization)
  • Performance requirements (latency, throughput)
  • Reliability requirements (uptime, error handling)
```

### `know priorities`
Generate implementation priorities based on readiness.

```bash
$ know priorities
```

**Output:**
```
🎯 Implementation Priorities
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Ready to Implement (70%+ complete):
  🟢 real-time-telemetry: 75% - Ready
  🟢 predictive-maintenance: 75% - Ready
  🟢 natural-language-interface: 75% - Ready

🟡 Partially Ready (50-69% complete):
  (entities would appear here)

🔴 Not Ready (<50% complete):
  (entities would appear here)
```

### `know order`
Generate optimal implementation order based on dependencies.

```bash
$ know order
```

**Output:**
```
📋 Implementation Order Analysis:

🟢 Ready to implement (no dependencies):
  (entities with no dependencies)

🟡 Implementation phases (ordered by dependency depth):
  Phase 1: Root entities (no dependencies)
  Phase 2: Entities depending only on Phase 1
  Phase 3: Higher-level integrations

💡 Use 'know deps <entity>' to see specific dependencies
```

---

## Browse & Discover

### `know list [entity_type]`
List available entities, optionally filtered by type.

```bash
$ know list features
```

**Output:**
```
Entities of type 'features':
📋 Entities in features:
  real-time-telemetry - Real-Time Telemetry
  predictive-maintenance - Predictive Maintenance
  natural-language-interface - Natural Language Interface
  fleet-coordination - Fleet Coordination
  mission-automation - Mission Automation
  analytics-system - Analytics
  parts-ordering-system - Parts Ordering System
  maintenance-alert-system - Maintenance Alert System
  ai-anomaly-detection - AI Anomaly Detection
  ai_text_integration - AI
  test-feature - Test Feature
```

### `know search <term> [entity_type]`
Find entities by name or description.

```bash
$ know search telemetry
```

**Output:**
```
🔍 Searching for entities matching: 'telemetry'

📋 Found across all types:
  features:real-time-telemetry - Real-Time Telemetry

💡 Use exact ID with: know <command> <entity_id>
💡 Use full reference with: know <command> <type>:<entity_id>
```

### `know feature`
List all features (shorthand for `know list features`).

```bash
$ know feature
```

**Output:**
```
Entities of type 'features':
📋 Entities in features:
  real-time-telemetry - Real-Time Telemetry
  predictive-maintenance - Predictive Maintenance
  (... all features ...)
```

### `know component`
List all components.

```bash
$ know component
```

**Output:**
```
Entities of type 'components':
📋 Entities in components:
  fleet-status-map - Fleet Status Map
  robot-controls - Robot Control Interface
  waypoint-map - Waypoint Planning Map
  (... all components ...)
```

### `know screen`
List all screens/interfaces.

```bash
$ know screen
```

**Output:**
```
Entities of type 'interfaces':
📋 Entities in interfaces:
  fleet-dashboard - Fleet Management Dashboard
  mission-control - Mission Control Interface
  device-diagnostics - Device Diagnostics
  teleoperation-interface - Teleoperation Interface
  business-intelligence - Business Intelligence Dashboard
  parts-store - Parts Store Interface
  fleet-map-view - Fleet Map View
  fleet-list-view - Fleet List View
  mission-planning - Mission Planning
  mission-history - Mission History
  mission-templates - Mission Templates
  teleoperate-single - Single Robot Teleoperation
  teleoperate-fleet - Fleet Teleoperation
  diagnostics-alerts - Diagnostic Alerts
  diagnostics-maintenance - Maintenance Schedule
  analytics-operations - Operations Analytics
  analytics-financial - Financial Analytics
  analytics-performance - Performance Analytics
  parts-catalog - Parts Catalog
  parts-orders - Parts Orders
  parts-inventory - Parts Inventory
  settings - Settings
  login - Login
```

---

## Connection & Health

### `know health`
Check overall graph health and identify issues.

```bash
$ know health
```

**Output:**
```
🔍 Graph Health Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 HANGING REFERENCES (referenced but don't exist):
   - acceptance_criteria:real_time_telemetry
   📊 Total: 1 hanging references

🟡 ORPHANED ENTITIES (nothing depends on them):
   ✅ No orphaned entities found

🟠 MISSING FROM GRAPH (defined but not in graph):
   ✅ All entities have graph entries

🔄 SELF-DEPENDENCIES (entities depending on themselves):
   ✅ No self-dependencies found

🔄 CIRCULAR DEPENDENCIES:
   ✅ No circular dependencies found

📈 GRAPH HEALTH SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📊 Total entities: 102
   📊 Total dependencies: 19
   🏆 Health Score: 95/100
   ✅ Graph health: EXCELLENT

🔧 RECOMMENDED ACTIONS:
━━━━━━━━━━━━━━━━━━━━━━
   1. Remove hanging references: know repair hanging

   💡 Run 'know repair --interactive' for guided fixes
   🚀 Run 'know repair --auto' to fix all issues automatically
```

### `know health --readiness`
Show readiness scores for all entities.

```bash
$ know health --readiness
```

**Output:**
```
=== users ===
(Shows readiness breakdown by entity type)
```

**Note:** This command shows completeness percentages for each entity type to help identify areas needing attention.

### `know health --gaps`
Analyze what's missing in the graph.

```bash
$ know health --gaps
```

**Output:**
```
📊 Overall Gap Analysis
━━━━━━━━━━━━━━━━━━━━━━━

Disconnection Issues:
  Orphaned entities: 0
  Missing graph entries: 0
  Hanging references: 1

Missing Data:
  Entities without descriptions: 15

Readiness by Type:
  (Shows breakdown by entity type with completion percentages)
```

### `know health --orphans`
List disconnected entities.

```bash
$ know health --orphans
```

**Output:**
```
✅ No orphaned entities found
```

### `know health <entity>`
Check specific entity readiness.

```bash
$ know health feature:real-time-telemetry
```

**Output:**
```
🔍 Graph Health Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 HANGING REFERENCES (referenced but don't exist):
   - acceptance_criteria:real_time_telemetry
   📊 Total: 1 hanging references

🟡 ORPHANED ENTITIES (nothing depends on them):
   ✅ No orphaned entities found

🟠 MISSING FROM GRAPH (defined but not in graph):
   ✅ All entities have graph entries

🔄 SELF-DEPENDENCIES (entities depending on themselves):
   ✅ No self-dependencies found

🔄 CIRCULAR DEPENDENCIES:
   ✅ No circular dependencies found

📈 GRAPH HEALTH SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📊 Total entities: 102
   📊 Total dependencies: 19
   🏆 Health Score: 95/100
   ✅ Graph health: EXCELLENT

🔧 RECOMMENDED ACTIONS:
━━━━━━━━━━━━━━━━━━━━━━
   1. Remove hanging references: know repair hanging

   💡 Run 'know repair --interactive' for guided fixes
   🚀 Run 'know repair --auto' to fix all issues automatically
```

**Note:** When called without entity argument, shows overall graph health instead of entity-specific health.

### `know connect <entity>`
Find potential connections for an entity.

```bash
$ know connect feature:real-time-telemetry
```

**Output:**
```
⚡ Caching graph nodes...
✓ Cached 271 nodes
🔍 Finding connections for: feature:real-time-telemetry
No connections found with similarity > 30%
```

### `know connect <source> <target>`
Connect two specific entities directly.

```bash
$ know connect features:analytics-system actions:export-analytics-report
```

**Output:**
```
(Confirms connection added between entities)
```

### `know connect --auto`
Auto-connect entities by name similarity (with approval).

```bash
$ know connect --auto
```

**Output:**
```
Using simple auto-connector...
🔍 Quick connection finder
Finding up to 5 connections...
Checking features → actions...
Checking actions → components...
Checking interfaces → features...

No new connections found
```

### `know connect --auto -y`
Skip approval, apply automatically.

```bash
$ know connect --auto -y
```

**Output:**
```
(Automatically applies connections without user confirmation)
```

### `know connect --interactive`
Review each connection individually.

```bash
$ know connect --interactive
```

**Output:**
```
(Interactive mode for reviewing connections one by one)
```

---

## Explore Dependencies

### `know deps <entity_ref>`
Show dependency chain (what this entity depends on).

```bash
$ know deps feature:real-time-telemetry
```

**Output:**
```
📦 Dependency chain for 'feature:real-time-telemetry':
  🎯 feature:real-time-telemetry (unknown: Real-Time Telemetry) [ROOT]
  (Shows tree of dependencies if any exist)
```

### `know impact <entity_ref>`
Show what depends on this entity (reverse dependencies).

```bash
$ know impact feature:real-time-telemetry
```

**Output:**
```
💥 Impact analysis for 'feature:real-time-telemetry' (what depends on this):
  ℹ️  No entities depend on 'feature:real-time-telemetry'
  (Shows dependent entities if any exist)
```

### `know preview <type> <entity_id>`
Preview what will be generated for an entity.

```bash
$ know preview feature real-time-telemetry
```

**Output:**
```
📋 Preview of feature specification for feature:real-time-telemetry:

# feature: Real-Time Telemetry

## Sections that will be generated:
✅ Overview and description
❌ Acceptance criteria (missing)
⚠️  Dependencies (none found)
✅ Technical implementation details

💡 Use 'know check feature real-time-telemetry' to validate before generation
```

### `know todo`
Show next actions needed for the project.

```bash
$ know todo
```

**Output:**
```
📝 Next Actions Needed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Finding entities that need attention...

🎯 High Priority (Features needing work):
  (Lists entities that need attention based on completeness and dependencies)

🔧 Medium Priority (Components to implement):
  (Lists components needing work)

📝 Low Priority (Documentation needed):
  (Lists entities needing documentation)
```

---

## Graph Maintenance

### `know mod <command> [args...]`
Modify graph data (delegates to mod-graph.sh).

```bash
$ know mod -h
```

**Output:**
```
Knowledge Graph Modifier
Fast CLI for managing spec-graph.json

Usage:
  mod-graph.sh [--file|-f <graph-file>] <command> [args...]

Options:
  --file, -f <file>        Use specified graph file (default: spec-graph.json)

Entity Commands:
  list [type]              List entities (optionally by type)
  add <type> <id> <name>   Add new entity
  set <type> <id> <key> <value>   Set entity property
  edit <type> <id>         Edit entity (interactive)
  remove <type> <id>       Remove entity
  show <type> <id>         Show entity details

Graph Commands:
  connect <from> <to>      Add dependency: from -> to
  disconnect <from> <to>   Remove dependency
  deps <entity>            Show dependencies for entity
  dependents <entity>      Show what depends on entity
  allowed <entity>         Show allowed connections for entity type
  resolve-cycles           Fix circular dependencies using canonical flow
  validate                 Validate graph structure

Utility Commands:
  stats                    Show statistics
  backup                   Create backup
  types                    List entity types
```

### `know query <command> [args...]`
Query graph data (delegates to query-graph.sh).

```bash
$ know query -h
```

**Output:**
```
JSON Graph Query Tool

USAGE:
  query-graph.sh [--file|-f <graph-file>] <command> [options]

OPTIONS:
  --file, -f <file>    Use specified graph file (default: .ai/spec-graph.json)

COMMANDS:
  traverse <entity_id> depends_on        - Show dependencies of entity
  reverse <entity_id> depends_on         - Find entities that depend on this entity
  path <from_entity> <to_entity>         - Find dependency path between entities
  deps <entity_id>                       - Show dependency chain
  impact <entity_id>                     - Show impact analysis (what depends on this)
  user <user_id>                         - Show dependencies for user
  cycles                                 - Detect circular dependencies
  scan-all                               - Comprehensive scan of ALL entities for cycles
  stats                                  - Show graph statistics
  ref-usage                              - Analyze reference usage and connectivity
  view <view_name>                       - Show pre-computed view
```

### `know repair [mode]`
Fix structural issues in the graph.

```bash
$ know repair
```

**Output:**
```
💾 Backup created: /workspace/lb-www/.ai/spec-graph.json.backup.1758413463

🔧 INTERACTIVE REPAIR MODE
━━━━━━━━━━━━━━━━━━━━━━━━━

What would you like to fix?
1. 🔴 Hanging references
2. 🟡 Orphaned entities
3. 🟠 Missing graph entries
4. 🔄 Self-dependencies
5. 🔄 Circular dependencies
6. 📊 Show current health
7. ✅ Done

(Interactive menu for fixing graph issues - use numbers to select repair option)
```

### `know validate <entity_ref>`
Validate graph structure for an entity.

```bash
$ know validate feature:real-time-telemetry
```

**Output:**
```
🔍 Validating entity completeness for feature:real-time-telemetry

✅ Entity name: Real-Time Telemetry
✅ Description: Live position, altitude, battery status, environme...

✅ Entity is complete and ready for specification generation
```

---

## Phase Management

### `know phases display`
Show implementation phases.

```bash
$ know phases display
```

**Output:**
```
📊 Current Implementation Phases
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Foundation
  Core data models and infrastructure that everything depends on
  Parallelizable: true
  Entities: 4
  Contents:
    • data_models:robot-fleet-model - robot-fleet-model
    • data_models:telemetry-stream-model - telemetry-stream-model
    • data_models:mission-data-model - mission-data-model
    • platforms:aws-infrastructure - aws-infrastructure

Phase 2: Core Services
  Essential services that enable features
  Parallelizable: true
  Entities: 4
  Contents:
    • objective:telemetry-monitoring - Telemetry Monitoring
    • objective:analytics-insights - Analytics & Insights
    • requirement:system-reliability - System Reliability
    • requirement:low-latency-teleoperation - Low Latency Teleoperation

Phase 3: Features
  Business objectives - all can be developed in parallel
  Parallelizable: true
  Entities: 6
  Contents:
    • feature:real-time-telemetry - Real-Time Telemetry
    • feature:fleet-coordination - Fleet Coordination
    • feature:mission-automation - Mission Automation
    • feature:predictive-maintenance - Predictive Maintenance
    • feature:analytics-system - Analytics
    • feature:natural-language-interface - Natural Language Interface

Phase 4: Interfaces
  User-facing components and screens
  Parallelizable: true
  Entities: 5
  Contents:
    • interface:fleet-dashboard - Fleet Management Dashboard
    • interface:teleoperation-interface - Teleoperation Interface
    • interface:business-intelligence - Business Intelligence Dashboard
    • interface:device-diagnostics - Device Diagnostics
    • interface:mission-control - Mission Control Interface

Phase 5: User Access
  Role-based access controls
  Parallelizable: true
  Entities: 7
  Contents:
    • user:owner - Owner
    • user:operations-manager - Operations Manager
    • user:operator - Operator
    • user:teleoperator - Teleoperator
    • user:fleet-teleoperator - Fleet Teleoperator
    • user:customer-service - Customer Service
    • user:executive - Executive

Phase 6: User Interactions
  User actions that mutate system state through UI interactions
  Parallelizable: true
  Entities: 5
  Contents:
    • action:emergency-stop-robot - Emergency Stop Robot
    • action:assign-mission - Assign Mission to Robot
    • action:navigate-to-diagnostics - Navigate to Device Diagnostics
    • action:approve-maintenance-order - Approve Maintenance Order
    • action:export-analytics-report - Export Analytics Report
```

### `know phases restructure`
Generate optimal phases based on dependencies.

```bash
$ know phases restructure
```

**Output:**
```
📊 Current Implementation Phases
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(Shows optimized phase structure based on current dependency analysis)

Phase 1: Foundation
  Core data models and infrastructure that everything depends on
  Parallelizable: true
  Entities: 4
  ...
```

### `know phases stats`
Show phase statistics.

```bash
$ know phases stats
```

**Output:**
```
📊 Current Implementation Phases
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(Shows detailed breakdown of phases with entity counts, parallel execution capability, and implementation readiness)
```

---

## Additional Options

Most commands support these options:

- `--format <md|json|yaml>` - Output format (default: md)
- `--output <file>` - Save output to file
- `--map <file>` - Use custom knowledge map file
- `--ai` - Generate Claude-optimized specification

---

## Entity Reference Format

When referencing entities, you can use:
- Full reference: `<type>:<id>` (e.g., `feature:real-time-telemetry`)
- Auto-detect: `<id>` if unique (e.g., `real-time-telemetry`)

---

## Tips for Effective Usage

1. **Check readiness before generating**: Use `know check` or `know health` before generating specs
2. **Fix gaps incrementally**: Use `know repair` to fix issues systematically
3. **Connect entities for better specs**: Connected entities produce more complete specifications
4. **Use phases for planning**: Phase management helps organize implementation order
5. **Validate after changes**: Always run `know validate` after modifying the graph

---

## Troubleshooting

### Common Issues and Solutions

**1. Specification Generation Fails (Completeness Too Low)**
```
Error: Cannot generate specification - entity completeness too low (50%)
```
- **Solution**: Use `know health --gaps` to identify missing data, then use graph modification tools to add required information
- **Note**: Minimum 70% completeness typically required for specification generation

**2. Commands Timeout or Hang**
```
(No output after waiting)
```
- **Solution**: Use `timeout 5 command` to limit execution time for complex operations
- **Common with**: `sitemap`, `routes`, `package` commands on large graphs

**3. Entity Not Found Errors**
```
Error: Entity not found: feature:real-time-telemetry
```
- **Solution**: Check exact entity ID with `know list [type]` and use correct format (`type:id` or just `id`)

**4. No Connections Found**
```
No connections found with similarity > 30%
```
- **Solution**: Manual connection may be needed using `know connect <source> <target>`
- **Alternative**: Lower similarity threshold or improve entity naming consistency

**5. Missing Test Scenarios**
```
No acceptance criteria found - cannot generate test scenarios
```
- **Solution**: Add acceptance criteria to entities using graph modification tools before generating tests

### General Troubleshooting Steps

If a command doesn't produce expected output:
1. Check entity exists: `know list [type]`
2. Validate entity: `know validate <entity>`
3. Check dependencies: `know deps <entity>`
4. Review health: `know health <entity>`
5. Fix issues: `know repair`
6. For timeouts: Use `timeout N command` to limit execution time
7. Check completeness: `know health --readiness` for entity readiness scores