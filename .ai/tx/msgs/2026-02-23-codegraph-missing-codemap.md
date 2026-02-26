---
from: tx-core
to: know-cli
type: bug
priority: low
---

# Bug: `know gen code-graph` fails without helpful recovery when codemap missing

## Observed

```
$ know gen code-graph
✗ Codemap not found: .ai/codemap.json
Run: know gen codemap know/src
```

## Problem

The suggested recovery command `know gen codemap know/src` hardcodes `know/src` as the path argument. This is only correct when run from within the know-cli project itself. For any other project, the suggested path is wrong and misleading.

## Expected

Either:
1. Auto-detect the project's source root and suggest the correct path (e.g., from package.json `main`, tsconfig `rootDir`, or convention like `src/`)
2. Use a generic placeholder in the suggestion: `Run: know gen codemap <src-dir>`
3. If a spec-graph.json exists, infer the source root from its metadata

## Repro

Run `know gen code-graph` from any project that isn't know-cli itself.
