# Feature Implementation: {{entity.name}}

**IMPLEMENTATION CONTEXT FOR CLAUDE:**
- Project: {{entity_ref}} in {{meta.project.name}}
- Tech Stack: {{references.libraries.frontend_libraries}}
- API Base: {{references.technical_architecture.api_gateway}}
- Database: {{references.technical_architecture.database}}

## Overview
{{entity.resolved_description}}

**Implementation Priority:** {{entity.evolution.v1.priority}}
**Current Status:** {{entity.evolution.v1.status}}

## Acceptance Criteria (IMPLEMENT ALL AS REQUIREMENTS)

{{#each acceptance_criteria.performance}}
### Performance Requirements
- [ ] **REQUIRED:** {{this}}
{{/each}}

{{#each acceptance_criteria.functional}}
### Functional Requirements  
- [ ] **REQUIRED:** {{this}}
{{/each}}

{{#each acceptance_criteria.integration}}
### Integration Requirements
- [ ] **REQUIRED:** {{this}}
{{/each}}

{{#each acceptance_criteria.reliability}}
### Reliability Requirements
- [ ] **REQUIRED:** {{this}}
{{/each}}

{{#each acceptance_criteria.security}}
### Security Requirements
- [ ] **REQUIRED:** {{this}}
{{/each}}

{{#each acceptance_criteria.safety}}
### Safety Requirements
- [ ] **REQUIRED:** {{this}}
{{/each}}

## IMPLEMENTATION PLAN

### Step 1: TypeScript Interfaces & Types
Create data models for:
{{#each graph.outbound.uses}}
- {{this}} (from knowledge map schema)
{{/each}}

### Step 2: Service Layer & Business Logic
Implement core functionality using:
- **Protocol:** {{references.protocols.communication_protocols}}
- **Data Format:** {{references.protocols.data_formats}}
- **Authentication:** {{references.protocols.authentication}}

### Step 3: UI Components
Build using design system:
- **UI Framework:** {{references.libraries.frontend_libraries}}
- **Design System:** {{references.ui}}
- **Component Library:** {{references.ui.components}}

### Step 4: API Integration
Connect to endpoints:
{{#each references.endpoints.api_endpoints}}
- {{this}}
{{/each}}

### Step 5: Testing & Validation
Write tests validating ALL acceptance criteria above.

## TECHNICAL ARCHITECTURE REQUIREMENTS

### Infrastructure Integration
- **Database:** {{references.technical_architecture.database}}
- **Message Broker:** {{references.technical_architecture.message_broker}}
- **Cache Layer:** {{references.technical_architecture.cache_layer}}
- **API Gateway:** {{references.technical_architecture.api_gateway}}

### Dependencies
{{#each graph.outbound.requires}}
- **{{this}}**: Must be implemented first
{{/each}}

### Related Functionality
{{#each graph.outbound.uses}}
- **{{this}}**: Technical service dependency
{{/each}}

## FILE STRUCTURE RECOMMENDATION
```
src/features/{{entity.id}}/
├── types.ts              # TypeScript interfaces
├── service.ts            # Business logic & API calls
├── hooks/                # React hooks
│   ├── use{{entity.name}}.ts
│   └── useWebSocket.ts
├── components/           # React components
│   ├── {{entity.name}}Dashboard.tsx
│   └── {{entity.name}}Controls.tsx
├── api/                  # API integration
│   ├── endpoints.ts
│   └── websocket.ts
└── __tests__/            # Tests for acceptance criteria
    ├── service.test.ts
    ├── components.test.ts
    └── integration.test.ts
```

## IMPLEMENTATION NOTES FOR CLAUDE

### Error Handling Patterns
- Use try/catch for all async operations
- Implement circuit breaker pattern for WebSocket connections
- Add proper loading and error states to React components

### Performance Considerations
- Implement WebSocket connection pooling
- Use React.memo for expensive components
- Add proper cleanup in useEffect hooks

### Security Requirements
- Validate all API responses
- Implement proper JWT token handling
- Add rate limiting on client side

### Testing Requirements
Each acceptance criterion MUST have corresponding tests:
- Unit tests for business logic
- Integration tests for API calls
- Component tests for UI behavior
- E2E tests for complete workflows

**START WITH:** TypeScript interfaces based on the data models, then implement the service layer, then React components, then tests.