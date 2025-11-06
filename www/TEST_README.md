# Lucid Dream Playwright Tests

This directory contains Playwright end-to-end tests that verify all workflows documented in `WORKFLOWS.md`.

## Setup

Tests are already configured with Playwright and browsers installed.

## Running Tests

```bash
# Run simplified workflow tests (recommended)
npm test

# Run all tests including detailed ones
npm run test:all

# Run tests with UI mode (interactive)
npm run test:ui

# Run tests in headed mode (see browser)
npm run test:headed

# Debug tests step by step
npm run test:debug

# View test reports
npm run test:report
```

## Test Files

- `tests/workflows-simple.spec.js` - **Recommended**: Simplified, robust tests (Chrome only)
- `tests/workflows.spec.js` - Detailed tests matching exact WORKFLOWS.md steps

## Test Coverage

The test suite covers all workflows from `WORKFLOWS.md`:

### 1. Text Entry Workflow
- ✅ Enter text → Navigate to Discover page
- ✅ Verify sidebar visibility
- ✅ Verify QA interface loads

### 2. JSON Load Workflow
- ✅ Select spec-graph.json
- ✅ Verify data loads in sidebar with counts
- ✅ Verify navigation to Discover page

### 3. QA Refinement Workflow
- ✅ Mock AI command activation
- ✅ Sequential question answering (3 questions)
- ✅ Transition to modification screen after Q3

### 4. Modification/Connection Workflow
- ✅ QA section hidden during modifications
- ✅ Modification interface visibility
- ✅ Connection list population
- ✅ Adding modifications and connections
- ✅ Pending changes tracking
- ✅ Commit functionality
- ✅ Sidebar updates (count changes)
- ✅ Return to QA mode

### 5. QA Expansion Workflow
- ✅ Expand Options button functionality
- ✅ Multiple choice sections display
- ✅ Collapse Options functionality

### 6. QA Reorientation Workflow
- ✅ "add user tron" command processing
- ✅ Modification screen activation
- ✅ Entity suggestions for "tron"
- ✅ Connection detection

### 7. Complete End-to-End Workflow
- ✅ Integration test covering all workflows sequentially

## Test Configuration

- **Base URL**: `http://localhost:8880`
- **Mock Mode**: All tests run with `?mock=true` to use test data
- **Browsers**: Chromium, Firefox, WebKit
- **Auto-start**: Server automatically starts before tests
- **Retries**: 2 retries on CI, 0 locally
- **Screenshots**: On failure only
- **Traces**: On first retry

## Test Files

- `tests/workflows.spec.js` - Main test suite covering all workflows
- `playwright.config.js` - Playwright configuration
- `TEST_README.md` - This documentation

## Notes

- Tests use mock mode (`?mock=true`) to ensure consistent, predictable behavior
- Server must be running on port 8880 (handled automatically by config)
- Tests validate both UI interactions and data state changes
- Each test is independent and can run in isolation