# Todo: Schema-Agnostic Know

## Phase 1: Schema Loader (1-2 hours)

- [ ] Create `know/src/schema_loader.py`
- [ ] Implement `SchemaLoader` class
  - [ ] `_detect_format()` - detect schema vs legacy format
  - [ ] `get_allowed_dependencies()` - normalized dependency rules
  - [ ] `get_reference_types()` - list of reference types
  - [ ] `get_reference_description()` - reference descriptions
  - [ ] `get_entity_description()` - entity descriptions
  - [ ] `get_required_fields()` - required fields per entity type
  - [ ] `get_optional_fields()` - optional fields per entity type
  - [ ] `get_entity_types()` - list all entity types
- [ ] Create `know/tests/test_schema_loader.py`
  - [ ] Test legacy format loading
  - [ ] Test new schema format loading
  - [ ] Test format auto-detection
  - [ ] Test field extraction

## Phase 2: Update Validation (2-3 hours)

- [ ] Update `know/src/validation.py`
  - [ ] Import `SchemaLoader`
  - [ ] Replace `json.load()` with `SchemaLoader()`
  - [ ] Use schema loader methods instead of direct dict access
  - [ ] Add `validate_entity_fields()` method
  - [ ] Integrate field validation into `validate_all()`
- [ ] Update validation tests
  - [ ] Test field validation (required fields)
  - [ ] Test field validation (unknown fields)
  - [ ] Test field validation (optional fields)
  - [ ] Test backward compatibility with legacy format

## Phase 3: Update Entity Manager (1-2 hours)

- [ ] Update `know/src/entities.py`
  - [ ] Import `SchemaLoader`
  - [ ] Use `SchemaLoader` in `__init__`
  - [ ] Add field validation to `add_entity()`
  - [ ] Validate required fields before adding
  - [ ] Validate no unknown fields
- [ ] Update entity manager tests
  - [ ] Test adding entity with valid fields
  - [ ] Test adding entity with missing required field (should fail)
  - [ ] Test adding entity with unknown field (should fail)

## Phase 4: Update Dependency Manager (1 hour)

- [ ] Update `know/src/dependencies.py`
  - [ ] Import `SchemaLoader`
  - [ ] Use `SchemaLoader` in `__init__`
  - [ ] Use `schema_loader.get_allowed_dependencies()`
  - [ ] Use `schema_loader.get_reference_types()`
- [ ] Update dependency manager tests
  - [ ] Test with new schema format
  - [ ] Test with legacy format

## Phase 5: Update CLI (1 hour)

- [ ] Update `know/know.py`
  - [ ] Load graph metadata to check for `schema_path`
  - [ ] Support `meta.schema_path` in auto-detection
  - [ ] Fall back to existing auto-detection if no schema_path
  - [ ] Preserve `-r` explicit override
- [ ] Update CLI tests
  - [ ] Test schema_path auto-detection
  - [ ] Test legacy auto-detection still works
  - [ ] Test explicit `-r` override

## Phase 6: Integration (1 hour)

- [ ] Update `know/src/__init__.py`
  - [ ] Export `SchemaLoader`
- [ ] Create example schemas
  - [ ] Copy `schemas/conversation-memory.json` (from /know:schema)
  - [ ] Create `graphs/conversation-memory-sample.json`
- [ ] Integration tests
  - [ ] Test full workflow with custom schema
  - [ ] Test mixed usage (multiple graphs with different schemas)
  - [ ] Test switching between graphs

## Phase 7: Documentation (1 hour)

- [ ] Update `README.md`
  - [ ] Add "Custom Schemas" section
  - [ ] Document schema format
  - [ ] Add examples
  - [ ] Document migration path
- [ ] Create `docs/custom-schemas.md`
  - [ ] Explain schema-agnostic design
  - [ ] Show example schemas
  - [ ] Document best practices
  - [ ] Link to `/know:schema` command
- [ ] Update existing docs
  - [ ] Update architecture docs
  - [ ] Update API docs

## Phase 8: Testing (2-3 hours)

- [ ] Create test schemas
  - [ ] `test-simple.json` - Minimal schema (2 entity types)
  - [ ] `test-complex.json` - Complex schema (10+ types, cycles)
  - [ ] `test-references.json` - Heavy reference usage
- [ ] End-to-end testing
  - [ ] Test with conversation-memory schema
  - [ ] Test with research-notes schema
  - [ ] Test with habit-tracking schema
- [ ] Edge case testing
  - [ ] Empty schema
  - [ ] Schema with cycles
  - [ ] Schema with orphaned entity types
  - [ ] Invalid schema format
- [ ] Performance testing
  - [ ] Large graph with custom schema
  - [ ] Schema switching performance

## Validation & Release

- [ ] Run all tests
- [ ] Manual testing with real schemas
- [ ] Code review
- [ ] Update CHANGELOG.md
- [ ] Tag release

---

**See also**: `.ai/plan/schema-agnostic-know.md` for detailed implementation plan
