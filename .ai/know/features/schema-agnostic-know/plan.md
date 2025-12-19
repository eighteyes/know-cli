# Implementation Plan: Schema-Agnostic Know

**Goal**: Enable know CLI to validate against custom schemas while maintaining 100% backward compatibility.

**Reference**: See `.ai/plan/schema-agnostic-know.md` for detailed design document.

---

## Architecture Overview

```
Graph File
  ↓
  meta.schema_path (optional)
  ↓
SchemaLoader (NEW)
  ↓ (normalizes both formats)
  ↓
GraphValidator, EntityManager, DependencyManager
  ↓ (use normalized schema)
  ↓
Validation & Operations
```

**Key Insight**: Create an abstraction layer (SchemaLoader) that normalizes both schema formats, then update existing classes to use it.

---

## Phase 1: Schema Loader

**File**: `know/src/schema_loader.py`

**Purpose**: Abstract away differences between legacy and new schema formats.

### Schema Loader Interface

```python
class SchemaLoader:
    def __init__(self, schema_path: str)
    def get_allowed_dependencies(self) -> dict
    def get_reference_types(self) -> list
    def get_reference_description(self, ref_type: str) -> str
    def get_entity_description(self, entity_type: str) -> str
    def get_required_fields(self, entity_type: str) -> list
    def get_optional_fields(self, entity_type: str) -> list
    def get_entity_types(self) -> list
```

### Implementation Steps

1. Create file `know/src/schema_loader.py`
2. Implement format detection:
   - Check for `schema_name` key → new format
   - Check for `allowed_dependencies` key → legacy format
   - Raise error if neither found
3. Implement getter methods that normalize both formats
4. Add comprehensive docstrings
5. Handle edge cases (missing keys, invalid formats)

### Testing

Create `know/tests/test_schema_loader.py`:
- Test loading legacy dependency-rules.json
- Test loading new schema format
- Test format auto-detection
- Test all getter methods with both formats
- Test error handling for invalid schemas

**Success Criteria**: SchemaLoader can load and normalize both formats.

---

## Phase 2: Update Validation

**File**: `know/src/validation.py`

**Changes**:
1. Import `SchemaLoader`
2. Replace direct JSON loading with SchemaLoader
3. Add field validation method
4. Integrate into existing validation flow

### New Method: validate_entity_fields()

```python
def validate_entity_fields(self, entity_type: str, entity_data: dict) -> List[str]:
    """Validate entity has required fields and only allowed fields."""
    errors = []

    required = self.schema_loader.get_required_fields(entity_type)
    optional = self.schema_loader.get_optional_fields(entity_type)
    allowed = set(required + optional)

    # Check required fields
    for field in required:
        if field not in entity_data:
            errors.append(f"Missing required field '{field}' for {entity_type}")

    # Check for unknown fields
    for field in entity_data.keys():
        if field not in allowed:
            errors.append(f"Unknown field '{field}' for {entity_type}")

    return errors
```

### Integration Steps

1. Update `__init__()` to create `SchemaLoader`
2. Replace all `self.rules[...]` with `self.schema_loader.get_...()`
3. Add `validate_entity_fields()` method
4. Call field validation in `validate_all()`
5. Update error messages to be schema-aware

### Testing

- Test field validation with required fields missing
- Test field validation with unknown fields
- Test field validation with all valid fields
- Test backward compatibility with legacy format
- Test new schema format validation

**Success Criteria**: Validation works with both schema formats and includes field validation.

---

## Phase 3: Update Entity Manager

**File**: `know/src/entities.py`

**Changes**:
1. Use SchemaLoader instead of direct rules access
2. Add field validation when adding entities
3. Provide clear error messages

### Implementation Steps

1. Import `SchemaLoader`
2. Update `__init__()` to use SchemaLoader
3. Update `add_entity()` to validate fields:
   ```python
   def add_entity(self, entity_type: str, name: str, data: dict):
       # Validate fields
       required = self.schema_loader.get_required_fields(entity_type)
       for field in required:
           if field not in data:
               raise ValueError(f"Missing required field: {field}")

       # Add entity
       # ... existing code
   ```
4. Update any other methods accessing rules directly

### Testing

- Test adding entity with valid fields
- Test adding entity with missing required field (should fail)
- Test adding entity with unknown field (should fail)
- Test with both schema formats

**Success Criteria**: Entities can only be added with valid fields per schema.

---

## Phase 4: Update Dependency Manager

**File**: `know/src/dependencies.py`

**Changes**:
1. Use SchemaLoader for dependency rules
2. Use SchemaLoader for reference types

### Implementation Steps

1. Import `SchemaLoader`
2. Update `__init__()`:
   ```python
   def __init__(self, graph_manager, rules_path: str):
       self.graph = graph_manager
       self.schema_loader = SchemaLoader(rules_path)
       self.allowed_deps = self.schema_loader.get_allowed_dependencies()
       self.reference_types = self.schema_loader.get_reference_types()
   ```
3. Update any methods accessing rules directly

### Testing

- Test dependency validation with new schema
- Test dependency validation with legacy format
- Test reference type checking

**Success Criteria**: Dependency validation works with both schema formats.

---

## Phase 5: Update CLI

**File**: `know/know.py`

**Changes**:
1. Check graph metadata for `schema_path`
2. Update auto-detection logic
3. Preserve explicit `-r` override

### Implementation Steps

1. Update `cli()` function:
   ```python
   if rules_path is None:
       # Try to load from graph metadata
       try:
           with open(graph_path, 'r') as f:
               graph_data = json.load(f)
               meta = graph_data.get('meta', {})

               if 'schema_path' in meta:
                   schema_path = Path(graph_path).parent / meta['schema_path']
                   if schema_path.exists():
                       rules_path = str(schema_path)
       except:
           pass  # Fall through to auto-detection

       # Fall back to existing auto-detection
       if rules_path is None:
           config_dir = Path(__file__).parent / "config"
           if 'code-graph' in str(graph_path):
               rules_path = str(config_dir / "code-dependency-rules.json")
           else:
               rules_path = str(config_dir / "dependency-rules.json")
   ```

### Testing

- Test graph with `meta.schema_path` loads correct schema
- Test legacy graphs without schema_path work
- Test explicit `-r` override still works
- Test error handling for missing schema file

**Success Criteria**: CLI auto-detects schema from graph metadata.

---

## Phase 6: Integration

### Export SchemaLoader

Update `know/src/__init__.py`:
```python
from .schema_loader import SchemaLoader

__all__ = [
    # ... existing exports
    'SchemaLoader',
]
```

### Create Example Schemas

1. Copy conversation-memory schema from `/know:schema` output
2. Create sample graph using that schema
3. Test end-to-end workflow

### Integration Testing

1. Create new graph with custom schema
2. Add entities with field validation
3. Validate dependencies
4. Run all know commands
5. Verify no regressions with legacy graphs

**Success Criteria**: Custom schemas work end-to-end with all know commands.

---

## Phase 7: Documentation

### Update README.md

Add section:
```markdown
## Custom Schemas

Know supports custom schemas for modeling any domain:

1. Generate schema: `/know:schema <name>`
2. Create graph with schema reference:
   ```json
   {
     "meta": {
       "schema_path": "schemas/<name>.json"
     }
   }
   ```
3. Use know commands normally - validation happens automatically

See docs/custom-schemas.md for details.
```

### Create docs/custom-schemas.md

Document:
- Schema format specification
- Example schemas (conversation, research, habits)
- Migration guide
- Best practices
- Troubleshooting

### Update Existing Docs

- Architecture documentation
- API reference
- Contributing guide

**Success Criteria**: Documentation explains custom schemas clearly with examples.

---

## Phase 8: Testing

### Test Schemas

Create test schemas:
1. **test-simple.json** - 2 entity types, minimal
2. **test-complex.json** - 10+ entity types, complex dependencies
3. **test-references.json** - Heavy reference usage
4. **test-cycles.json** - Intentional cycles for testing

### End-to-End Tests

Test complete workflows:
1. Conversation memory system
2. Research note graph
3. Habit tracking graph
4. Mixed usage (switch between schemas)

### Edge Cases

Test:
- Empty schema
- Schema with only references
- Schema with orphaned entity types
- Invalid schema format
- Missing schema file
- Circular schema references

### Performance

Test:
- Large graphs (1000+ entities)
- Schema loading performance
- Validation performance
- Switching between schemas

**Success Criteria**: All tests pass, no regressions, custom schemas work smoothly.

---

## Validation Checklist

Before considering this feature complete:

- [ ] All tests pass (unit + integration)
- [ ] Backward compatibility verified (existing graphs work)
- [ ] Custom schema workflow tested end-to-end
- [ ] Documentation complete and accurate
- [ ] Code reviewed
- [ ] Performance acceptable (no regressions)
- [ ] Error messages are clear and helpful
- [ ] Examples work as documented

---

## Risk Mitigation

**Risk**: Breaking existing graphs
**Mitigation**:
- Extensive backward compatibility testing
- Keep legacy format support indefinitely
- Add migration tools if needed

**Risk**: Schema format needs changes after usage
**Mitigation**:
- Start with minimal schema format
- Make it extensible
- Version schemas from the start

**Risk**: Field validation too strict
**Mitigation**:
- Make warnings initially, not errors
- Add `--strict` flag for strict validation
- Allow disabling field validation

---

## Next Steps After Implementation

Future enhancements (out of scope for this feature):
1. Schema versioning and migration tools
2. Schema validation command (`know validate-schema`)
3. Schema visualization
4. Schema inheritance
5. Multi-schema graphs
6. JSON schema generation for IDE support
7. Schema import/export

---

**Estimated Total Time**: 8-12 hours

**Priority**: High (enables major new use cases for know)

**Dependencies**: None (internal refactor)

**Breaking Changes**: None (100% backward compatible)
