# Component: {{entity.name}}

## Overview
{{entity.resolved_description}}

## Functionality
{{#each entity.functionality}}
- {{this}}
{{/each}}

## Acceptance Criteria

{{#each acceptance_criteria.functional}}
### Functional Requirements
- [ ] {{this}}
{{/each}}

{{#each acceptance_criteria.performance}}
### Performance Requirements
- [ ] {{this}}
{{/each}}

{{#each acceptance_criteria.integration}}
### Integration Requirements
- [ ] {{this}}
{{/each}}

{{#each acceptance_criteria.reliability}}
### Reliability Requirements
- [ ] {{this}}
{{/each}}

## Technical Stack
{{#each references.libraries}}
- **{{@key}}**: {{this}}
{{/each}}
- **UI Components**: {{graph.outbound.uses_ui}}
- **Data Models**: {{graph.outbound.displays}}

## Integration Points
- **Parent Screens**: {{graph.inbound.contained_by}}
- **Features**: {{graph.outbound.implements}}
- **APIs**: {{references.endpoints.api_endpoints}}

## Design System
{{#each graph.outbound.uses_ui}}
- **{{this}}**: {{references.ui.components}}
{{/each}}

## Implementation Details

### Component Structure
```typescript
interface {{entity.name}}Props {
  // Props based on features and data models
}

export const {{entity.name}}: React.FC<{{entity.name}}Props> = () => {
  // Component implementation
}
```

### State Management
- **Local State**: Component-specific state using React hooks
- **Global State**: {{references.libraries.frontend_libraries}} for shared state
- **Real-time Updates**: WebSocket integration for live data

### Styling
{{#each references.ui}}
- **{{@key}}**: {{this}}
{{/each}}

## Dependencies

### Data Dependencies
{{#each graph.outbound.displays}}
- **{{this}}**: Data model must be implemented
{{/each}}

### Feature Dependencies
{{#each graph.outbound.implements}}
- **{{this}}**: Feature logic must be available
{{/each}}

### UI Dependencies
{{#each graph.outbound.uses_ui}}
- **{{this}}**: UI component from design system
{{/each}}

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