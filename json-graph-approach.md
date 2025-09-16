# JSON-Only Graph Database Approach

## Core Concept

Instead of hierarchical nesting, treat JSON as a flat graph with explicit relationship modeling. This gives us graph database power with universal JSON tooling compatibility.


## Typical Abstraction Hierarchy (Broad → Granular):

### 1. **Project/Business Level** (Broadest)
- Strategic objectives and evolution phases
- Release milestones and roadmap  
- Business requirements and constraints

### 2. **Platform/Infrastructure Level**
- Deployment platforms (web, mobile, cloud, etc.)
- External dependencies and third-party services
- Infrastructure components and environments

### 3. **User/Stakeholder Level**
- User roles, personas, and access patterns
- Business stakeholders and their needs
- Cross-cutting requirements and constraints

### 4. **Interface/Experience Level** 
- User interfaces and customer touchpoints
- Workflows and user journeys
- Integration points and APIs

### 5. **Feature/Capability Level**
- Business features and domain capabilities
- Functional requirements and use cases
- Cross-cutting concerns and services

### 6. **Component/Module Level**
- Implementation components and modules
- Business logic and domain services
- Integration adapters and controllers

### 7. **UI/Presentation Level**
- Shared design systems and patterns
- Reusable UI components and widgets
- Visual themes and interaction patterns

### 8. **Data/Schema Level**
- Domain models and business entities
- Data relationships and constraints
- Integration schemas and contracts

### 9. **Implementation Level** (Most Granular)
- Technical configurations and settings
- Library versions and framework choices
- API endpoints and communication protocols
- Deployment and runtime specifications

## Typical Dependency Flow:
```
HOW: Project → Platform → Requirements → Interface → Feature -> Component → UI → Data Models 
WHAT: Project ->  User ──────→ Functionality ────────→ Action
Integration: User -> Requirements, Functionality -> Features, Action -> Component
```



## Schema Design Patterns

### Core Design Principles (Refined)

**🎯 Single Source of Truth**: All relationships stored ONLY in graph section  
**🧹 Clean Entity Separation**: Entities contain only static metadata  
**🔄 Versioned Evolution**: Features evolve through versions, not duplicates  
**❌ Zero Redundancy**: No capabilities/permissions arrays in entities  
**🔗 Pure Dependency Model**: Universal relationship semantic:
- Single `depends_on` array per entity (no outbound/inbound nesting)
- Everything is fundamentally a dependency relationship
- 50% smaller JSON (eliminates bidirectional redundancy)  
- Simpler queries (flat array vs nested objects)

```json
{
  "meta": { 
    "project": {
      "name": "Project Name",
      "phases": [
        {
          "id": "1_foundation",
          "name": "Foundation",
          "description": "Core data models and infrastructure", 
          "parallelizable": false,
          "requirements": ["model:user-data", "platform:web-app"]
        },
        {
          "id": "6_interactions", 
          "name": "User Interactions",
          "description": "User actions that mutate system state",
          "parallelizable": true,
          "requirements": ["user_action:admin-login", "user_action:export-report"]
        }
      ]
    }
  },
  "references": { /* All terminal graph nodes, intended for template output. Schema flexible here */
    "technical_architecture": { /* infrastructure configs */ },
    "endpoints": { /* API specifications */ },
    "libraries": { /* dependency versions */ },
    "protocols": { /* communication specs */ },
    "ui": { /* design system colors, typography, spacing */ },
  },
  
  "entities": { /* MUST be in dependency graph, 
    "users": { 
      "admin": {
        "id": "admin",
        "type": "user", 
        "name": "Administrator",
        "description": "System administrator with full access"
        // NO capabilities, permissions, or features arrays!
      }
    },
    "components": {
      "admin-dashboard-table": {
        "id": "admin-dashboard-table",
        "type": "component",
        "base_component": "data-table",
        "specialized_for": ["screen:admin-panel", "user:admin"],
        "acceptance_criteria": {
          "functional": ["displays_user_data_accurately", "sorting_filtering_working"],
          "performance": ["loads_under_2_seconds", "handles_1000_rows"],
          "integration": ["connects_to_user_api", "respects_admin_permissions"]
        }
      }
    },
    "user_actions": {
      "admin-login": {
        "id": "admin-login",
        "type": "user_action",
        "name": "Administrator Login",
        "description": "Authenticate administrator with elevated privileges",
        "trigger_type": "form_submission",
        "user_roles": ["admin"],
        "state_mutation": {
          "target_model": "user_session",
          "mutation_type": "create_record",
          "new_state": "authenticated"
        },
        "acceptance_criteria": {
          "functional": ["credentials_validated", "session_created"],
          "performance": ["login_under_3_seconds"],
          "security": ["password_hashed", "session_encrypted"]
        }
      }
    },
    "features": { 
      "analytics": {
        "id": "analytics",
        "type": "feature",
        "name": "Analytics",
        "current_version": "v1",
        "evolution": {
          "v1": {
            "status": "implemented",
            "description_ref": "basic-analytics-desc",
            "capabilities": ["reporting", "data-visualization"],
            "priority": "P1"
          },
          "v2": {
            "status": "planned", 
            "description_ref": "advanced-analytics-desc",
            "capabilities": ["predictive-analytics", "real-time-dashboards"],
            "priority": "P0",
            "roadmap_milestone": "v2_enhanced_features"
          }
        }
      }
    },
    "schema": { /* domain model definitions */ }
  },

  "graph": {
    "user:admin": {
      "depends_on": [
        "screen:admin-panel", 
        "feature:analytics", 
        "feature:user-management",
        "platform:web-app"
      ]
    },
    "component:admin-dashboard-table": {
      "depends_on": [
        "ui_component:data-table",
        "feature:analytics",
        "model:user-data"
      ]
    },
    "user_action:admin-login": {
      "depends_on": [
        "component:login-form",
        "ui_component:interactive-buttons",
        "model:user-data",
        "screen:admin-panel"
      ]
    }
  }
}
```

## Key Architectural Patterns from Implementation

### Component Specialization Pattern
Handle variations of shared components for different users/contexts. This solves the problem of UI components being too general - a fleet data-table for an owner has very different needs than one for an operator:

```json
"components": {
  "owner-fleet-table": {
    "id": "owner-fleet-table",
    "type": "component",
    "base_component": "fleet-status-map",
    "specialized_for": ["screen:business-intelligence", "user:owner", "user:executive"],
    "functionality": [
      "fleet-utilization-metrics",
      "revenue-per-robot", 
      "operational-costs",
      "roi-analysis",
      "export-financials"
    ]
  },
  "operator-fleet-table": {
    "id": "operator-fleet-table", 
    "type": "component",
    "base_component": "fleet-status-map",
    "specialized_for": ["screen:fleet-dashboard", "user:operator", "user:fleet-teleoperator"],
    "functionality": [
      "real-time-robot-status",
      "mission-assignments",
      "battery-monitoring", 
      "emergency-controls",
      "quick-actions"
    ]
  }
}
```

**Key Benefits:**
- **Clear Inheritance**: `base_component` shows foundational component
- **Focused Functionality**: Each variant has specific capabilities for its context  
- **Explicit Relationships**: Dependencies show exactly which users, screens, and features each variant serves
- **Graph Queryable**: You can trace dependencies to understand component relationships

### Implementation Configuration Pattern
Separate component logic from implementation details:
```json
"references": {
  "component_implementations": {
    "admin-dashboard-table": {
      "base_component": "ui_components.data-table",
      "data_source": "admin_analytics_api",
      "columns": ["id", "email", "role", "last_login"],
      "styling": "admin_theme"
    }
  }
}
```

### Acceptance Criteria Pattern
Structure validation requirements consistently:
```json
"acceptance_criteria": {
  "functional": ["feature_works_correctly", "user_can_complete_task"],
  "performance": ["loads_under_2_seconds", "handles_expected_load"],
  "integration": ["connects_to_dependencies", "respects_permissions"],
  "reliability": ["graceful_error_handling", "data_integrity"],
  "safety": ["fail_safe_mechanisms", "emergency_controls"]
}
```

### References Architecture Pattern
Organize shared configurations and technical details:
```json
"references": {
  "descriptions": { /* shared content */ },
  "technical_architecture": { /* infrastructure */ },
  "endpoints": { /* API specs */ },
  "libraries": { /* versions */ },
  "protocols": { /* communication */ },
  "ui": { /* design system */ }
}
```

These patterns enable clean separation between conceptual entities (WHAT) and implementation details (HOW) while maintaining clear dependency relationships.