# Feature Added: Schema-Agnostic Know

## What Was Created

✅ **Feature Directory**: `.ai/know/features/schema-agnostic-know/`
- `overview.md` - Requirements and success criteria
- `todo.md` - Detailed implementation checklist (8 phases)
- `plan.md` - Step-by-step implementation plan
- `spec.md` - Placeholder for component specs

✅ **Spec Graph Entities**:
- `feature:schema-agnostic-know` - Main feature
- `action:load-custom-schema` - Load and normalize schemas
- `action:validate-entity-fields` - Validate entity fields
- `action:detect-schema-path` - Auto-detect schema location
- `component:schema-loader` - Schema loading component
- `component:field-validator` - Field validation component
- `component:schema-detector` - Schema detection component

✅ **Graph Structure**:
```
feature:schema-agnostic-know
  → action:load-custom-schema
      → component:schema-loader
  → action:validate-entity-fields
      → component:field-validator
  → action:detect-schema-path
      → component:schema-detector
```

✅ **Phase Assignment**: Added to `pending` phase with status `incomplete`

## Implementation Resources

**Detailed Plan**: `.ai/plan/schema-agnostic-know.md`
- Architecture overview
- Code changes needed (with examples)
- 8 implementation phases
- Testing strategy
- Risk mitigation

**Todo Checklist**: `.ai/know/features/schema-agnostic-know/todo.md`
- Phase 1: Schema Loader (1-2 hours)
- Phase 2: Update Validation (2-3 hours)
- Phase 3: Update Entity Manager (1-2 hours)
- Phase 4: Update Dependency Manager (1 hour)
- Phase 5: Update CLI (1 hour)
- Phase 6: Integration (1 hour)
- Phase 7: Documentation (1 hour)
- Phase 8: Testing (2-3 hours)

**Total Estimate**: 8-12 hours

## Key Design Decisions

1. **100% Backward Compatible**: Existing graphs with `dependency-rules.json` continue to work
2. **Schema Abstraction Layer**: `SchemaLoader` class normalizes both formats
3. **Field Validation**: Enforce required/optional fields per entity type
4. **Auto-Detection**: Load schema from `meta.schema_path` in graph
5. **Minimal Changes**: Only 4-5 files need updates

## Next Steps

1. **Review the plan**: `.ai/plan/schema-agnostic-know.md`
2. **Start implementation**: Follow todo.md checklist
3. **Test with example**: Use conversation-memory schema from `/know:schema`
4. **Validate end-to-end**: Create custom graph and verify all commands work

## Success Criteria

- [ ] Know validates against custom schemas from `/know:schema`
- [ ] Field validation enforces required/optional fields
- [ ] Existing graphs work unchanged (backward compatible)
- [ ] Graphs reference schema via `meta.schema_path`
- [ ] All validation errors are clear
- [ ] Documentation includes custom schema examples

## Related Work

- `/know:schema` command - Generates custom schemas
- `/know:bug` command - Bug tracking workflow
- `schemas/` directory - Will store custom schemas
- `graphs/` directory - Will store graphs using custom schemas

---

**Status**: Feature scaffolded and added to spec-graph
**Phase**: Pending (status: incomplete)
**Ready for**: Implementation (follow plan.md)
