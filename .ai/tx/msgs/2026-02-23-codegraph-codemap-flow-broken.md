---
from: tx-core
to: know-cli
type: bug
priority: low
---

# Bug: `know gen code-graph` / `know gen codemap` workflow is broken

## Context

Follow-up to previous bug (2026-02-23-codegraph-missing-codemap.md). The error message fix landed — it now says `<src-dir>` instead of `know/src`. But the actual workflow is still broken.

## Observed

Step 1: Run `know gen code-graph` — fails, tells user to generate codemap first:
```
$ know gen code-graph
✗ Codemap not found: .ai/codemap.json
Run: know gen codemap <src-dir>
```

Step 2: User generates codemap, then tries `code-graph` again with the path:
```
$ know gen code-graph src/
Error: Got unexpected extra argument (src/)
```

## Problem

`know gen code-graph` does NOT accept a path argument, but the error message from step 1 primes the user to think the next command needs a path. The two-step flow is confusing:

1. `know gen codemap <src-dir>` — takes a path arg
2. `know gen code-graph` — takes NO args, reads from `.ai/codemap.json`

The error message should make this two-step flow explicit.

## Suggested Fix

Change the error message to clearly separate the two commands:

```
✗ Codemap not found: .ai/codemap.json
First generate a codemap:  know gen codemap <src-dir>
Then retry:                 know gen code-graph
```
