#!/bin/bash

# Template Engine for know CLI
# Generates implementation specifications using jq templates

# Generate specification for an entity
generate_spec() {
    local entity_type="$1"
    local entity_id="$2"
    local output_format="${3:-markdown}"
    
    local normalized_type
    normalized_type=$(normalize_type "$entity_type")
    
    if ! validate_entity "$normalized_type" "$entity_id"; then
        error "Entity not found: $normalized_type:$entity_id"
    fi
    
    local entity_ref="$normalized_type:$entity_id"
    
    case "$normalized_type" in
        screens)
            generate_screen_spec "$entity_ref" "$output_format"
            ;;
        components)
            generate_component_spec "$entity_ref" "$output_format"
            ;;
        features)
            generate_feature_spec "$entity_ref" "$output_format"
            ;;
        functionality)
            generate_functionality_spec "$entity_ref" "$output_format"
            ;;
        schema)
            generate_model_spec "$entity_ref" "$output_format"
            ;;
        users)
            generate_user_spec "$entity_ref" "$output_format"
            ;;
        requirements)
            generate_requirement_spec "$entity_ref" "$output_format"
            ;;
        platforms)
            generate_platform_spec "$entity_ref" "$output_format"
            ;;
        ui_components)
            generate_ui_component_spec "$entity_ref" "$output_format"
            ;;
        *)
            error "No template available for entity type: $normalized_type"
            ;;
    esac
}

# Generate screen implementation specification
generate_screen_spec() {
    local entity_ref="$1"
    local format="$2"
    
    local type="${entity_ref%%:*}"
    local id="${entity_ref#*:}"
    
    cat << 'EOF' | jq -r --arg type "$type" --arg id "$id" -f - "$KNOWLEDGE_MAP"
# Extract screen entity and related data
.entities[$type][$id] as $screen |
($type + ":" + $id) as $entity_ref |

# Get resolved description
(if $screen.description_ref then
    .references.descriptions[$screen.description_ref] // $screen.description_ref
else
    $screen.description // "No description available"
end) as $description |

# Get components from graph relationships
[.graph[$entity_ref].outbound.contains[]? // empty] as $components |

# Get features from graph relationships
[.graph[$entity_ref].outbound.implements[]? // empty] as $features |

# Get users who can access this screen
[.graph | to_entries[] | select(.value.outbound.accesses[]? == $entity_ref) | .key] as $users |

# Get UI components used
[.graph[$entity_ref].outbound.uses_ui[]? // empty] as $ui_components |

# Get acceptance criteria if available
($screen.acceptance_criteria // {}) as $acceptance_criteria |

# Generate the specification
"# Screen Implementation Specification

## Entity: " + $screen.name + "
**Type:** " + $screen.type + "  
**ID:** " + $screen.id + "  
**Priority:** " + ($screen.priority // "Not specified") + "

## Description
" + $description + "

## Components
" + (if ($components | length) > 0 then
    ($components | map("- " + . + " (" + ((.[] as $comp | .entities | to_entries[] | select(.value | to_entries[] | select(.key == ($comp | split(\":")[1]))) | .value | to_entries[] | select(.key == ($comp | split(\":")[1])) | .value.name) // "Unknown") + ")") | join(\"\n\"))
else
    "No components specified"
end) + "

## Features Implemented
" + (if ($features | length) > 0 then
    ($features | map("- " + . + " (" + ((.[] as $feat | .entities | to_entries[] | select(.value | to_entries[] | select(.key == ($feat | split(\":")[1]))) | .value | to_entries[] | select(.key == ($feat | split(\":")[1])) | .value.name) // "Unknown") + ")") | join(\"\n\"))
else
    "No features specified"
end) + "

## User Access
" + (if ($users | length) > 0 then
    ($users | map("- " + . + " (" + ((.[] as $user | .entities | to_entries[] | select(.value | to_entries[] | select(.key == ($user | split(\":")[1]))) | .value | to_entries[] | select(.key == ($user | split(\":")[1])) | .value.name) // "Unknown") + ")") | join(\"\n\"))
else
    "No users specified"
end) + "

## UI Design System
" + (if ($ui_components | length) > 0 then
    ($ui_components | map("- " + . + " (" + ((.[] as $ui | .entities | to_entries[] | select(.value | to_entries[] | select(.key == ($ui | split(\":")[1]))) | .value | to_entries[] | select(.key == ($ui | split(\":")[1])) | .value.name) // "Unknown") + ")") | join(\"\n\"))
else
    "Standard UI components from design system"
end) + "

" + (if $acceptance_criteria and ($acceptance_criteria | length) > 0 then
"## Acceptance Criteria

" + ($acceptance_criteria | to_entries | map(
    "### " + (.key | ascii_upcase) + " Requirements\n" +
    (.value | map("- " + .) | join(\"\n\"))
) | join(\"\n\n\"))
else
""
end) + "

## Technical Requirements

### UI Framework
- **Library:** " + (.references.libraries.frontend_libraries // "React") + "
- **Styling:** " + (.references.ui.implementation[0] // "CSS-in-JS") + "
- **Design System:** Component-based with " + (.references.ui.colors | keys | join(\", \")) + " color palette

### Performance
- **Loading:** Progressive web app capabilities
- **Responsiveness:** Mobile-first responsive design
- **Accessibility:** WCAG 2.1 AA compliance

### Architecture  
- **Communication:** " + (.references.technical_architecture.api_gateway // "REST APIs") + " + WebSocket for real-time data
- **State Management:** React Context or Redux for global state
- **Data Flow:** Real-time updates via " + (.references.technical_architecture.message_broker // "WebSocket") + "

## Implementation Tasks

1. **Create Screen Component**
   - Set up React component structure
   - Implement responsive layout using design system
   - Add proper TypeScript interfaces

2. **Integrate Components**" + 
   (if ($components | length) > 0 then
       \"\n\" + ($components | map(\"   - Integrate \" + . + \" component\") | join(\"\n\"))
   else
       \"\n   - No specific components to integrate\"
   end) + "

3. **Implement Features**" +
   (if ($features | length) > 0 then
       \"\n\" + ($features | map(\"   - Implement \" + . + \" functionality\") | join(\"\n\"))
   else
       \"\n   - No specific features to implement\"
   end) + "

4. **Add User Authentication**
   - Implement role-based access control
   - Add permission checks for authorized users
   - Handle unauthorized access gracefully

5. **Testing & Validation**
   - Unit tests for component logic
   - Integration tests for user interactions
   - Accessibility testing
   - Cross-browser compatibility testing

## Dependencies

### Technical Dependencies
- React 18+
- TypeScript
- " + (.references.libraries.frontend_libraries // "UI Framework") + "
- WebSocket client library

### Data Dependencies" +
(if ($features | length) > 0 then
    \"\n\" + ($features | map(\"- \" + . + \" feature must be implemented first\") | join(\"\n\"))
else
    \"\n- No specific data dependencies\"
end) + "

### Component Dependencies" +
(if ($components | length) > 0 then
    \"\n\" + ($components | map(\"- \" + . + \" component must be available\") | join(\"\n\"))
else
    \"\n- No specific component dependencies\"
end)
EOF
}

# Generate component implementation specification
generate_component_spec() {
    local entity_ref="$1"
    local format="$2"
    
    local type="${entity_ref%%:*}"
    local id="${entity_ref#*:}"
    
    cat << 'EOF' | jq -r --arg type "$type" --arg id "$id" -f - "$KNOWLEDGE_MAP"
# Extract component entity and related data
.entities[$type][$id] as $component |
($type + ":" + $id) as $entity_ref |

# Get resolved description
(if $component.description_ref then
    .references.descriptions[$component.description_ref] // $component.description_ref
else
    $component.description // "No description available"
end) as $description |

# Get features implemented
[.graph[$entity_ref].outbound.implements[]? // empty] as $features |

# Get models used
[.graph[$entity_ref].outbound.uses[]? // empty | select(startswith("model:"))] as $models |

# Get functionality dependencies
[.graph[$entity_ref].outbound.uses[]? // empty | select(startswith("functionality:"))] as $functionality |

# Get acceptance criteria if available
($component.acceptance_criteria // {}) as $acceptance_criteria |

# Generate the specification
"# Component Implementation Specification

## Entity: " + $component.name + "
**Type:** " + $component.type + "  
**ID:** " + $component.id + "

## Description
" + $description + "

## Features Implemented
" + (if ($features | length) > 0 then
    ($features | map("- " + . + " (" + ((.[] as $feat | .entities.features[($feat | split(\":")[1])].name) // "Unknown") + ")") | join(\"\n\"))
else
    "No features specified"
end) + "

## Data Models
" + (if ($models | length) > 0 then
    ($models | map("- " + . + " (" + ((.[] as $model | .entities.schema[($model | split(\":")[1])].name) // "Unknown") + ")") | join(\"\n\"))
else
    "No models specified"
end) + "

## Functionality Dependencies
" + (if ($functionality | length) > 0 then
    ($functionality | map("- " + . + " (" + ((.[] as $func | .entities.functionality[($func | split(\":")[1])].name) // "Unknown") + ")") | join(\"\n\"))
else
    "No functionality dependencies"
end) + "

" + (if $acceptance_criteria and ($acceptance_criteria | length) > 0 then
"## Acceptance Criteria

" + ($acceptance_criteria | to_entries | map(
    "### " + (.key | ascii_upcase) + " Requirements\n" +
    (.value | map("- " + .) | join(\"\n\"))
) | join(\"\n\n\"))
else
""
end) + "

## Technical Implementation

### Component Structure
```typescript
interface " + ($component.name | gsub(\" \"; \"\") | gsub(\"-\"; \"\")) + "Props {
  // Props based on features and data models
}

export const " + ($component.name | gsub(\" \"; \"\") | gsub(\"-\"; \"\")) + ": React.FC<" + ($component.name | gsub(\" \"; \"\") | gsub(\"-\"; \"\")) + "Props> = () => {
  // Component implementation
}
```

### Required APIs" +
(if ($functionality | length) > 0 then
    \"\n\" + ($functionality | map(\"- \" + . + \" service integration\") | join(\"\n\"))
else
    \"\n- No specific API requirements\"
end) + "

### State Management" +
(if ($models | length) > 0 then
    \"\n\" + ($models | map(\"- State for \" + . + \" data\") | join(\"\n\"))
else
    \"\n- Local component state\"
end) + "

## Implementation Tasks

1. **Create Component Structure**
   - Set up TypeScript interfaces
   - Create component file and exports
   - Add proper prop validation

2. **Implement Core Logic**" +
(if ($features | length) > 0 then
    \"\n\" + ($features | map(\"   - Implement \" + . + \" functionality\") | join(\"\n\"))
else
    \"\n   - Implement core component behavior\"
end) + "

3. **Data Integration**" +
(if ($models | length) > 0 then
    \"\n\" + ($models | map(\"   - Integrate \" + . + \" data\") | join(\"\n\"))
else
    \"\n   - Set up local state management\"
end) + "

4. **API Integration**" +
(if ($functionality | length) > 0 then
    \"\n\" + ($functionality | map(\"   - Connect to \" + . + \" service\") | join(\"\n\"))
else
    \"\n   - No external API integration required\"
end) + "

5. **Testing**
   - Unit tests for component logic
   - Integration tests with data models
   - Storybook stories for design system
   - Accessibility testing

## Dependencies

### Data Dependencies" +
(if ($models | length) > 0 then
    \"\n\" + ($models | map(\"- \" + . + \" must be defined\") | join(\"\n\"))
else
    \"\n- No data dependencies\"
end) + "

### Service Dependencies" +
(if ($functionality | length) > 0 then
    \"\n\" + ($functionality | map(\"- \" + . + \" must be implemented\") | join(\"\n\"))
else
    \"\n- No service dependencies\"
end) + "

### Feature Dependencies" +
(if ($features | length) > 0 then
    \"\n\" + ($features | map(\"- \" + . + \" business logic must be defined\") | join(\"\n\"))
else
    \"\n- No feature dependencies\"
end)
EOF
}

# Generate feature implementation specification  
generate_feature_spec() {
    local entity_ref="$1"
    local format="$2"
    
    local type="${entity_ref%%:*}"
    local id="${entity_ref#*:}"
    
    cat << 'EOF' | jq -r --arg type "$type" --arg id "$id" -f - "$KNOWLEDGE_MAP"
# Extract feature entity and related data
.entities[$type][$id] as $feature |
($type + ":" + $id) as $entity_ref |

# Get current version details
($feature.evolution[$feature.current_version] // {}) as $current_version |

# Get resolved description for current version
(if $current_version.description_ref then
    .references.descriptions[$current_version.description_ref] // $current_version.description_ref
else
    $feature.description // "No description available"
end) as $description |

# Get requirements dependencies
[.graph[$entity_ref].outbound.depends_on[]? // empty | select(startswith("requirement:"))] as $requirements |

# Get model dependencies  
[.graph[$entity_ref].outbound.uses[]? // empty | select(startswith("model:"))] as $models |

# Get acceptance criteria if available
($feature.acceptance_criteria // {}) as $acceptance_criteria |

# Generate the specification
"# Feature Implementation Specification

## Entity: " + $feature.name + "
**Type:** " + $feature.type + "  
**ID:** " + $feature.id + "  
**Current Version:** " + $feature.current_version + "
**Status:** " + $current_version.status + "
**Priority:** " + ($current_version.priority // "Not specified") + "

## Description
" + $description + "

## Current Version Capabilities
" + (if $current_version.capabilities then
    ($current_version.capabilities | map("- " + .) | join(\"\n\"))
else
    "No capabilities specified"
end) + "

## Requirements
" + (if ($requirements | length) > 0 then
    ($requirements | map("- " + . + " (" + ((.[] as $req | .entities.requirements[($req | split(\":")[1])].name) // "Unknown") + ")") | join(\"\n\"))
else
    "No specific requirements"
end) + "

## Data Models
" + (if ($models | length) > 0 then
    ($models | map("- " + . + " (" + ((.[] as $model | .entities.schema[($model | split(\":")[1])].name) // "Unknown") + ")") | join(\"\n\"))
else
    "No data models specified"
end) + "

" + (if $acceptance_criteria and ($acceptance_criteria | length) > 0 then
"## Acceptance Criteria

" + ($acceptance_criteria | to_entries | map(
    "### " + (.key | ascii_upcase) + " Requirements\n" +
    (.value | map("- " + .) | join(\"\n\"))
) | join(\"\n\n\"))
else
""
end) + "

## Technical Architecture

### Business Logic
```typescript
// Feature service interface
interface " + ($feature.name | gsub(\" \"; \"\") | gsub(\"-\"; \"\")) + "Service {
" + (if $current_version.capabilities then
    ($current_version.capabilities | map("  " + (. | gsub(\"_\"; \" \") | gsub(\"-\"; \" \")) + "(): Promise<void>;") | join(\"\n\"))
else
    "  // Define service methods based on capabilities"
end) + "
}
```

### API Endpoints" +
(if ($models | length) > 0 then
    \"\n\" + ($models | map(\"- \" + . + \" CRUD operations\") | join(\"\n\"))
else
    \"\n- Feature-specific endpoints to be defined\"
end) + "

### State Management
- Feature state using Redux or Context API
- Real-time updates via WebSocket
- Optimistic updates for better UX

## Implementation Tasks

1. **Core Business Logic**" +
(if $current_version.capabilities then
    \"\n\" + ($current_version.capabilities | map(\"   - Implement \" + (. | gsub(\"_\"; \" \")) + \" capability\") | join(\"\n\"))
else
    \"\n   - Define and implement core feature logic\"
end) + "

2. **Data Layer**" +
(if ($models | length) > 0 then
    \"\n\" + ($models | map(\"   - Implement \" + . + \" data operations\") | join(\"\n\"))
else
    \"\n   - Set up feature data structures\"
end) + "

3. **API Development**
   - Create REST endpoints for feature operations
   - Add WebSocket support for real-time features
   - Implement proper error handling

4. **Requirements Compliance**" +
(if ($requirements | length) > 0 then
    \"\n\" + ($requirements | map(\"   - Ensure compliance with \" + .) | join(\"\n\"))
else
    \"\n   - Validate against general requirements\"
end) + "

5. **Testing & Validation**
   - Unit tests for business logic
   - Integration tests with data models
   - End-to-end feature testing
   - Performance testing against requirements

## Dependencies

### Requirement Dependencies" +
(if ($requirements | length) > 0 then
    \"\n\" + ($requirements | map(\"- \" + . + \" must be satisfied\") | join(\"\n\"))
else
    \"\n- No specific requirement dependencies\"
end) + "

### Data Dependencies" +
(if ($models | length) > 0 then
    \"\n\" + ($models | map(\"- \" + . + \" must be implemented\") | join(\"\n\"))
else
    \"\n- No data dependencies\"
end) + "

## Evolution Roadmap

" + (if $feature.evolution then
    ($feature.evolution | to_entries | map(
        "### " + .key + " (" + .value.status + ")\n" +
        (if .value.description_ref then
            (.[] as $v | .references.descriptions[$v.value.description_ref] // $v.value.description_ref)
        else
            (.value.description // "No description")
        end) + \"\n\" +
        \"**Priority:** \" + (.value.priority // \"Not specified\") + \"\n\" +
        (if .value.capabilities then
            \"**Capabilities:**\n\" + (.value.capabilities | map(\"- \" + .) | join(\"\n\"))
        else
            \"\"
        end) +
        (if .value.roadmap_milestone then
            \"\n**Milestone:** \" + .value.roadmap_milestone
        else
            \"\"
        end)
    ) | join(\"\n\n\"))
else
    "No evolution roadmap defined"
end)
EOF
}

# Generate functionality (technical service) specification
generate_functionality_spec() {
    local entity_ref="$1"
    local format="$2"
    
    local type="${entity_ref%%:*}"
    local id="${entity_ref#*:}"
    
    cat << 'EOF' | jq -r --arg type "$type" --arg id "$id" -f - "$KNOWLEDGE_MAP"
# Extract functionality entity and related data
.entities[$type][$id] as $functionality |
($type + ":" + $id) as $entity_ref |

# Get resolved description
(if $functionality.description_ref then
    .references.descriptions[$functionality.description_ref] // $functionality.description_ref
else
    $functionality.description // "No description available"
end) as $description |

# Get acceptance criteria
($functionality.acceptance_criteria // {}) as $acceptance_criteria |

# Generate the specification
"# Technical Service Implementation Specification

## Entity: " + $functionality.name + "
**Type:** " + $functionality.type + "  
**ID:** " + $functionality.id + "

## Description
" + $description + "

" + (if $acceptance_criteria and ($acceptance_criteria | length) > 0 then
"## Acceptance Criteria

" + ($acceptance_criteria | to_entries | map(
    "### " + (.key | ascii_upcase) + " Requirements\n" +
    (.value | map("- " + .) | join(\"\n\"))
) | join(\"\n\n\"))
else
""
end) + "

## Technical Implementation

### Service Architecture
```typescript
// Service interface definition
interface " + ($functionality.name | gsub(\" \"; \"\") | gsub(\"-\"; \"\")) + " {
  // Define service methods based on acceptance criteria
}
```

### Infrastructure Requirements
- **Deployment:** " + (.references.technical_architecture.deployment // "Containerized service") + "
- **Database:** " + (.references.technical_architecture.database // "PostgreSQL") + "
- **Message Broker:** " + (.references.technical_architecture.message_broker // "Apache Kafka") + "
- **Cache Layer:** " + (.references.technical_architecture.cache_layer // "Redis") + "

### API Design
- **Protocol:** " + (.references.protocols.communication_protocols // "REST + WebSocket") + "
- **Data Format:** " + (.references.protocols.data_formats // "JSON") + "
- **Authentication:** " + (.references.protocols.authentication // "JWT + OAuth2") + "

## Implementation Tasks

1. **Core Service Logic**
   - Implement business logic based on acceptance criteria
   - Add proper error handling and logging
   - Implement data validation

2. **Performance Optimization**" +
(if $acceptance_criteria.performance then
    \"\n\" + ($acceptance_criteria.performance | map(\"   - Ensure \" + .) | join(\"\n\"))
else
    \"\n   - Optimize for latency and throughput\"
end) + "

3. **Reliability Implementation**" +
(if $acceptance_criteria.reliability then
    \"\n\" + ($acceptance_criteria.reliability | map(\"   - Implement \" + .) | join(\"\n\"))
else
    \"\n   - Add circuit breakers and retry logic\"
end) + "

4. **Security Implementation**" +
(if $acceptance_criteria.security then
    \"\n\" + ($acceptance_criteria.security | map(\"   - Implement \" + .) | join(\"\n\"))
else
    \"\n   - Add authentication and authorization\"
end) + "

5. **Testing & Validation**
   - Unit tests for all business logic
   - Integration tests with dependencies
   - Load testing for performance requirements
   - Security testing and vulnerability assessment

## Dependencies

### Infrastructure Dependencies
- " + (.references.technical_architecture.api_gateway // "API Gateway") + " for routing
- " + (.references.technical_architecture.database // "Database") + " for persistence
- " + (.references.technical_architecture.message_broker // "Message broker") + " for async communication

### Technical Dependencies
- " + (.references.libraries.backend_libraries // "Backend framework") + "
- Monitoring and logging infrastructure
- Configuration management system

## Monitoring & Observability

### Metrics to Track" +
(if $acceptance_criteria.performance then
    \"\n\" + ($acceptance_criteria.performance | map(\"- \" + .) | join(\"\n\"))
else
    \"\n- Response time and throughput\n- Error rates and success rates\n- Resource utilization\"
end) + "

### Alerting
- Performance degradation alerts
- Error rate threshold alerts
- Resource utilization alerts
- Security incident alerts"
EOF
}

# Generate model (schema) specification
generate_model_spec() {
    local entity_ref="$1"
    local format="$2"
    
    local type="${entity_ref%%:*}"
    local id="${entity_ref#*:}"
    
    cat << 'EOF' | jq -r --arg type "$type" --arg id "$id" -f - "$KNOWLEDGE_MAP"
# Extract schema entity and related data
.entities[$type][$id] as $model |
($type + ":" + $id) as $entity_ref |

# Get model attributes
($model.attributes // {}) as $attributes |

# Find entities that use this model
[.graph | to_entries[] | select(.value.outbound.uses[]? == $entity_ref) | .key] as $used_by |

# Generate the specification
"# Data Model Implementation Specification

## Entity: " + $model.name + "
**Type:** " + $model.type + "  
**ID:** " + $model.id + "

## Description
" + ($model.description // "No description available") + "

## Schema Definition

### Attributes
" + (if $attributes and ($attributes | length) > 0 then
    ($attributes | to_entries | map("- **" + .key + "**: " + .value) | join(\"\n\"))
else
    "No attributes defined"
end) + "

### TypeScript Interface
```typescript
interface " + ($model.name | gsub(\" \"; \"\") | gsub(\"-\"; \"\")) + " {" +
(if $attributes and ($attributes | length) > 0 then
    \"\n\" + ($attributes | to_entries | map(
        \"  \" + .key + \": \" + 
        (if .value == \"STRING\" then \"string\"
         elif .value == \"UUID\" then \"string\"
         elif .value == \"TIMESTAMP\" then \"Date\"
         elif .value == \"JSON\" then \"object\"
         elif .value == \"ARRAY<STRING>\" then \"string[]\"
         elif .value == \"OBJECT\" then \"object\"
         elif (.value | startswith(\"ENUM[\")) then \"string // \" + .value
         else .value | ascii_downcase
         end) + \";\"
    ) | join(\"\n\")) + \"\n\"
else
    \"\n  // Define model attributes\n\"
end) + "}
```

## Database Schema

### Table Definition
```sql
CREATE TABLE " + ($model.id | gsub(\"-\"; \"_\")) + " (" +
(if $attributes and ($attributes | length) > 0 then
    \"\n\" + ($attributes | to_entries | map(
        \"  \" + (.key | gsub(\"-\"; \"_\")) + \" \" + 
        (if .value == \"STRING\" then \"VARCHAR(255)\"
         elif .value == \"UUID\" then \"UUID\"
         elif .value == \"TIMESTAMP\" then \"TIMESTAMP\"
         elif .value == \"JSON\" then \"JSONB\"
         elif .value == \"ARRAY<STRING>\" then \"TEXT[]\"
         elif .value == \"OBJECT\" then \"JSONB\"
         elif (.value | startswith(\"ENUM[\")) then \"VARCHAR(50) -- \" + .value
         else \"VARCHAR(255) -- \" + .value
         end) + \",\"
    ) | join(\"\n\")) + \"\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n\"
else
    \"\n  id UUID PRIMARY KEY,\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n\"
end) + ");
```

## API Endpoints

### REST Operations
```typescript
// CRUD operations for " + $model.name + "
GET    /api/" + ($model.id | gsub(\"-\"; \"-\")) + "          // List all
GET    /api/" + ($model.id | gsub(\"-\"; \"-\")) + "/:id      // Get by ID
POST   /api/" + ($model.id | gsub(\"-\"; \"-\")) + "          // Create new
PUT    /api/" + ($model.id | gsub(\"-\"; \"-\")) + "/:id      // Update
DELETE /api/" + ($model.id | gsub(\"-\"; \"-\")) + "/:id      // Delete
```

## Usage

### Entities Using This Model
" + (if ($used_by | length) > 0 then
    ($used_by | map("- " + . + " (" + ((.[] as $entity | $entity | split(\":\") | .[0]) // "unknown") + ")") | join(\"\n\"))
else
    "No entities currently use this model"
end) + "

## Implementation Tasks

1. **Database Setup**
   - Create database table with proper schema
   - Add indexes for performance
   - Set up foreign key constraints if needed

2. **API Implementation**
   - Create CRUD endpoints
   - Add validation for all attributes
   - Implement proper error handling

3. **Data Access Layer**
   - Create repository/DAO classes
   - Implement query methods
   - Add caching where appropriate

4. **Validation & Security**
   - Input validation for all fields
   - SQL injection prevention
   - Access control based on user permissions

5. **Testing**
   - Unit tests for data access methods
   - Integration tests for API endpoints
   - Data migration testing

## Dependencies

### Infrastructure Dependencies
- " + (.references.technical_architecture.database // "PostgreSQL") + " database server
- Database migration tools
- API framework for REST endpoints

### Security Dependencies
- Authentication system for API access
- Authorization rules for data access
- Data encryption for sensitive fields"
EOF
}

# Generate basic specification for other entity types
generate_user_spec() {
    local entity_ref="$1"
    echo "# User Entity Specification"
    echo "User specifications are defined through their graph relationships."
    echo "Use 'know deps $entity_ref' to see accessible entities."
}

generate_requirement_spec() {
    local entity_ref="$1"
    echo "# Requirement Specification"
    echo "Requirements are cross-cutting concerns validated through acceptance criteria."
    echo "Use 'know impact $entity_ref' to see which entities must satisfy this requirement."
}

generate_platform_spec() {
    local entity_ref="$1"
    echo "# Platform Implementation Specification"
    echo "Platforms implement multiple features and serve multiple users."
    echo "Use 'know deps $entity_ref' to see feature dependencies."
}

generate_ui_component_spec() {
    local entity_ref="$1"
    echo "# UI Component Specification"
    echo "UI components are part of the design system."
    echo "Check references.ui section for implementation details."
}