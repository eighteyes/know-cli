# Spec: Spec Generation Enrichment

_To be populated during `/know:build` phase_

## Architecture

See [plan.md](./plan.md) for detailed architecture.

## Three-Tier Data Model

| Tier | Contents | Cross-Ref? |
|------|----------|------------|
| **Entities** | name, description only | Yes (via graph) |
| **References** | Reusable schemas, signatures, data-models | Yes |
| **Meta.feature_specs** | Feature-specific prose (use_cases, testing, etc.) | No |

## New Reference Types

- `api-schema` - TypeScript interface definitions for public APIs
- `signature` - Function/method signatures with params and returns
- `test-spec` - Reusable test specifications
- `security-spec` - Reusable security requirements

## Meta.feature_specs Structure

Feature-specific metadata including:
- Status, phase, priority
- Use cases with configurations
- Testing requirements (unit/integration/performance)
- Security & privacy requirements
- Monitoring & observability
- Performance characteristics
