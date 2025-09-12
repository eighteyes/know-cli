# Feature: {{entity.name}}

## Overview
{{entity.resolved_description}}
- **Priority**: {{entity.priority}}
- **Status**: {{entity.status}}

## Acceptance Criteria

### Performance
{{#each acceptance_criteria.performance}}
- [ ] {{this}}
{{/each}}

### Functional
{{#each acceptance_criteria.functional}}
- [ ] {{this}}
{{/each}}

### Integration
{{#each acceptance_criteria.integration}}
- [ ] {{this}}
{{/each}}

### Reliability
{{#each acceptance_criteria.reliability}}
- [ ] {{this}}
{{/each}}

### Security
{{#each acceptance_criteria.security}}
- [ ] {{this}}
{{/each}}

### Safety
{{#each acceptance_criteria.safety}}
- [ ] {{this}}
{{/each}}

### Validation
{{#each acceptance_criteria.validation}}
- [ ] {{this}}
{{/each}}

## Technical Implementation

### Implements
{{#each graph.outbound.implements}}
- {{this}}
{{/each}}

### Data Models
{{#each graph.outbound.processes}}
- {{this}}
{{/each}}

### Implemented By
{{#each graph.inbound.implemented_by}}
- {{this}}
{{/each}}

## API Integration
- **Protocol**: {{references.protocols.communication_protocols}}
- **Data Format**: {{references.protocols.data_formats}}
- **Authentication**: {{references.protocols.authentication}}

## Implementation Notes
**Current Version**: {{entity.current_version}}
{{entity.evolution.v2.description_ref}}

## Architecture Requirements
{{#each references.technical_architecture}}
- **{{@key}}**: {{this}}
{{/each}}