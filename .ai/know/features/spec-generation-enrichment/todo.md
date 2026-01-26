# Todo: Spec Generation Enrichment

## Phase 1: Schema Updates

- [ ] Add `api-schema` to reference_types in dependency-rules.json
- [ ] Add `signature` to reference_types in dependency-rules.json
- [ ] Add `test-spec` to reference_types in dependency-rules.json
- [ ] Add `security-spec` to reference_types in dependency-rules.json
- [ ] Add reference_description entries for new types
- [ ] Add `feature_specs` to meta_schema in dependency-rules.json
- [ ] Document use_case_object schema
- [ ] Document testing_object schema
- [ ] Document performance_object schema

## Phase 2: Generator Core

- [ ] Add `_get_feature_spec_meta()` helper to generators.py
- [ ] Add `_render_data_model_typescript()` helper
- [ ] Add `_render_signature()` helper
- [ ] Add `_get_component_file()` helper
- [ ] Add `_get_component_operations()` helper

## Phase 3: Feature Spec Generation

- [ ] Rewrite `generate_feature_spec()` section by section:
  - [ ] Header + Description
  - [ ] Status/Phase/Priority from meta.feature_specs
  - [ ] Dependencies (other features)
  - [ ] Components section with operations
  - [ ] Interfaces section
  - [ ] Data Models as TypeScript
  - [ ] Business Logic narrative
  - [ ] Use Cases
  - [ ] Testing Requirements
  - [ ] Security & Privacy
  - [ ] Monitoring & Observability

## Phase 4: Validation

- [ ] Add soft validation hints for new reference types
- [ ] Graceful handling when sections missing
- [ ] Test with empty graph
- [ ] Test with partial graph

## Phase 5: Testing & Documentation

- [ ] Create example ensemble-meshes graph entry
- [ ] Test `know spec feature:ensemble-meshes` output
- [ ] Compare output to target spec
- [ ] Update SKILL.md with new reference types
- [ ] Update SKILL.md with meta.feature_specs usage
