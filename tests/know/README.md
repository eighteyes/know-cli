# Know CLI Test Suite

Comprehensive test suite for the `know` CLI tool that generates implementation specifications from knowledge graphs.

## Overview

This test suite validates all commands and functionality of the `know` tool using real entities from the knowledge graph (`knowledge-map-cmd.json`). Tests use TAP (Test Anything Protocol) format for standardized output and reporting.

## Test Structure

```
tests/know/
├── lib/
│   └── test-utils.sh           # Test utilities and assertion functions
├── test-entity-specs.sh        # Entity specification generation tests
├── test-analysis.sh            # Analysis commands (deps, impact, order, validate)
├── test-discovery.sh           # Discovery commands (list, search, preview, check)
├── test-packages.sh            # Package generation (package, test)
├── test-errors.sh              # Error handling and edge cases
├── run-tests.sh                # Main test runner script
└── README.md                   # This file
```

## Running Tests

### Quick Start
```bash
# Run all tests
./tests/know/run-tests.sh

# Run with verbose output
./tests/know/run-tests.sh -v

# Run specific test pattern
./tests/know/run-tests.sh --pattern entity
```

### Test Runner Options
```bash
./tests/know/run-tests.sh [options] [test-pattern]

OPTIONS:
    -v, --verbose           Verbose output
    -p, --parallel          Run test suites in parallel  
    -t, --timeout SECONDS   Test timeout (default: 300)
    --junit FILE            Generate JUnit XML output
    --pattern PATTERN       Run only tests matching pattern
    --list                  List available test suites
    -h, --help              Show help
```

### Examples
```bash
# Run all tests with verbose output
./tests/know/run-tests.sh -v

# Run only entity specification tests
./tests/know/run-tests.sh --pattern entity

# Run tests in parallel with JUnit output
./tests/know/run-tests.sh --parallel --junit results.xml

# Run with timeout of 60 seconds
./tests/know/run-tests.sh --timeout 60
```

## Test Suites

### 1. Entity Specification Tests (`test-entity-specs.sh`)
Tests all entity specification generation commands:
- `know feature <id>` - Feature specifications
- `know component <id>` - Component specifications  
- `know screen <id>` - Screen/UI specifications
- `know functionality <id>` - Technical functionality specs
- `know requirement <id>` - Requirement specifications
- `know api <id>` - API specifications

**Key Features:**
- Uses real entities from knowledge graph
- Tests multiple output formats (md, json, yaml)
- Tests file output vs stdout
- Tests AI mode vs standard mode

### 2. Analysis Tests (`test-analysis.sh`)
Tests dependency and impact analysis commands:
- `know deps <entity_ref>` - Dependency analysis
- `know impact <entity_ref>` - Impact analysis  
- `know order` - Implementation order optimization
- `know validate` - Knowledge map validation

**Key Features:**
- Tests with entities that have complex relationships
- Validates graph traversal functionality
- Tests entity reference resolution

### 3. Discovery Tests (`test-discovery.sh`)
Tests entity discovery and exploration commands:
- `know list [entity_type]` - List entities
- `know search <term> [type]` - Fuzzy search
- `know preview <type> <id>` - Preview specifications
- `know check <type> <id>` - Completeness validation

**Key Features:**
- Tests search with partial matches and case insensitivity
- Validates autocomplete functionality
- Tests preview for all generator types

### 4. Package Tests (`test-packages.sh`)
Tests comprehensive package generation:
- `know package <entity_id>` - Complete implementation packages
- `know test <entity_ref>` - Test scenario generation

**Key Features:**
- Tests package generation for complex entities
- Validates AI mode package generation
- Tests multiple output formats

### 5. Error Handling Tests (`test-errors.sh`)
Comprehensive error condition and edge case testing:
- Invalid commands and options
- Nonexistent entities and files
- Permission errors
- Resource limits
- Malformed inputs

**Key Features:**
- Tests all error paths
- Validates proper error messages
- Tests edge cases and boundary conditions

## Dynamic Entity Loading

The test suite dynamically loads real entities from the knowledge graph:

```bash
# Load entities of a specific type
load_test_entities "features"      # Returns: ai-anomaly-detection, analytics, ...

# Get all entity types
get_entity_types                   # Returns: features, components, screens, ...

# Get a sample entity reference
get_sample_entity                  # Returns: features:ai-anomaly-detection
```

This ensures tests always use current, valid data from the knowledge graph.

## Test Utilities

### Assertion Functions
```bash
assert_success "test name" "command" ["expected_pattern"]
assert_failure "test name" "command" ["expected_error_pattern"] 
assert_contains "test name" "command" "required_pattern"
```

### Test Management
```bash
setup_test        # Create temporary test environment
cleanup_test      # Remove temporary files
print_summary     # Show final test results
skip_test "name" "reason"  # Skip test with reason
```

### TAP Output
All tests produce TAP-compatible output:
```
TAP version 13
ok 1 - feature spec generation
ok 2 - component spec generation
not ok 3 - invalid entity handling
# Expected error pattern not found
1..3
```

## Configuration

### Environment Variables
```bash
KNOW_CMD="/path/to/know"                    # Path to know command
KNOWLEDGE_MAP="/path/to/knowledge-map.json" # Path to knowledge map
```

### Prerequisites
- `bash` 4.0+
- `jq` (JSON processor)
- `know` command accessible
- `knowledge-map-cmd.json` file

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run know CLI tests
  run: |
    cd tests/know
    ./run-tests.sh --junit results.xml
    
- name: Publish test results
  uses: mikepenz/action-junit-report@v3
  with:
    report_paths: 'tests/know/results.xml'
```

### Exit Codes
- `0` - All tests passed
- `1` - One or more tests failed
- Other - System error (missing dependencies, etc.)

## Troubleshooting

### Common Issues

**Test failures due to missing entities:**
- Verify `knowledge-map-cmd.json` exists and has entities
- Check that entity types match expected structure

**Permission errors:**
- Ensure test scripts are executable: `chmod +x tests/know/*.sh`
- Check write permissions for test output directory

**Timeout errors:**
- Increase timeout with `--timeout` option
- Check if `know` command is hanging

**Missing dependencies:**
- Ensure `jq` is installed: `command -v jq`
- Verify `know` command exists and is executable

### Debug Mode
```bash
# Run single test suite with debug output
bash -x ./tests/know/test-entity-specs.sh

# Check test utilities
source ./tests/know/lib/test-utils.sh
get_entity_types  # Should list available types
```

## Contributing

When adding new tests:
1. Use dynamic entity loading from knowledge graph
2. Follow TAP output format
3. Include both success and failure scenarios
4. Add comprehensive error condition testing
5. Update this README with new test descriptions

### Test Naming Convention
- Test files: `test-<category>.sh`
- Test functions: `test_<specific_functionality>()`
- Test names: Descriptive, lowercase with spaces