# QA Steps: Spec Generation Enrichment

**Date Created:** 2025-12-24
**Feature:** spec-generation-enrichment

## Objective

Verify that the enhanced spec generation system produces rich, comprehensive feature specifications with metadata, components, operations, and proper TypeScript rendering.

## Prerequisites

- Know CLI is installed and accessible
- Spec-graph.json is available at `.ai/know/spec-graph.json`
- Test features exist in the spec graph (spec-generation-enrichment, beads-integration)
- Terminal/command line access to run know commands

## Test Steps

### 1. Verify New Reference Types in dependency-rules.json

**Action:** Check that 4 new reference types were added to the schema
**Expected:** The following reference types exist in `know/config/dependency-rules.json`:
- `api-schema` - TypeScript interface definitions for public APIs
- `signature` - Function/method signatures with parameters and return types
- `test-spec` - Reusable test specifications
- `security-spec` - Reusable security requirements

### 2. Generate Basic Feature Spec

**Action:** Run `know -g .ai/know/spec-graph.json feature-spec feature:spec-generation-enrichment`
**Expected:**
- Command executes without errors
- Output includes "# Feature: Spec Generation Enrichment"
- Output includes "## Overview" section with description
- Output includes "## User Actions" section

### 3. Verify Enhanced Component Display

**Action:** Generate spec for a feature with components (e.g., beads-integration)
**Expected:**
- Components section shows component names and descriptions
- If components have file paths (source-file references), they are displayed
- If components have operations, they are listed under each component

### 4. Test TypeScript Data Model Rendering

**Action:** Create a test data-model reference and generate a spec that uses it
**Expected:**
- Data model is rendered as a TypeScript interface (not raw JSON)
- Interface name matches the model name
- Fields are formatted as `fieldName: type;`
- Proper TypeScript syntax (interface, braces, semicolons)

### 5. Test Function Signature Rendering

**Action:** Create a test signature reference and verify rendering
**Expected:**
- Signature is formatted as: `function name(param1: type1, param2?: type2): returnType`
- Optional parameters use `?:` syntax
- Parameters are comma-separated
- Return type is shown after `:`

### 6. Verify Graceful Degradation

**Action:** Generate spec for a feature without meta.feature_specs metadata
**Expected:**
- Spec generation completes successfully (no errors)
- Only available sections are shown
- Missing metadata sections are simply omitted (not shown as "Not specified")
- Backward compatible with existing features

### 7. Test Meta Feature Specs Integration

**Action:** Add metadata to meta.feature_specs for a test feature, then generate spec
**Expected:**
- Status/Phase/Priority section appears if metadata present
- Use Cases section renders from meta.feature_specs.use_cases
- Testing Requirements section shows unit/integration/performance tests
- Security & Privacy section displays security requirements
- Monitoring & Observability section shows metrics

### 8. Validate Graph Structure

**Action:** Run `know -g .ai/know/spec-graph.json validate`
**Expected:**
- Validation passes (no errors)
- May have warnings (acceptable)
- Graph structure remains valid after enhancements

### 9. Check Backward Compatibility

**Action:** Generate specs for existing features (beads-integration, graph-embeddings)
**Expected:**
- All existing features generate specs without errors
- Features without new metadata still work
- No breaking changes to existing functionality

### 10. Verify Helper Methods Work

**Action:** Test the 5 new helper methods indirectly through spec generation
**Expected:**
- `_get_feature_spec_meta()`: Metadata retrieved when present
- `_render_data_model_typescript()`: TypeScript interfaces render correctly
- `_render_signature()`: Function signatures format properly
- `_get_component_operations()`: Operations listed under components
- `_get_component_file()`: File paths shown for components

## Acceptance Criteria

- [ ] All 4 new reference types are documented in dependency-rules.json
- [ ] Feature spec generation works for all features (old and new)
- [ ] TypeScript rendering produces valid interface syntax
- [ ] Signature rendering shows proper function syntax
- [ ] Graceful degradation works (no errors when metadata missing)
- [ ] Meta.feature_specs sections appear when metadata is present
- [ ] Graph validation passes after all changes
- [ ] Backward compatible with existing features
- [ ] All 11 sections render when full metadata is available
- [ ] No breaking changes to existing spec generation

## Notes

This is a backend/CLI feature, so all testing can be automated through command execution and file inspection. Manual validation is primarily for verifying output formatting and readability.
