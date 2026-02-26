# Bug: `feature connect` crashes with dict TypeError on code_graph_path

**From:** lucid-command
**Priority:** high (blocks code→spec cross-linking)

## Issue

`know feature connect` crashes at line 4982 trying to create a `Path()` from a dict. The `code_graph_path` variable is a dict instead of a string.

## Traceback

```
File "know.py", line 4982, in feature_connect
    code_graph_file = Path(code_graph_path)
TypeError: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'dict'
```

## Context

- `meta.project` in both spec-graph and code-graph are strings (`"lucid-command"`)
- Verified both graphs have string values via `jq '.meta.project'`
- Still crashes — so `code_graph_path` is being derived from something else, or there's a config/option being parsed as a dict

## Previous bug

This replaces the earlier "feature not found" bug (2026-02-23-feature-connect-broken.md). That error may have been masking this one, or the fix for `meta set` string promotion changed the code path.

## Reproduction

```bash
know feature connect job-notes module:controllers.jobs.controller.ts
# TypeError: argument should be a str or os.PathLike, not 'dict'
```

## Impact

Blocks all code→spec bidirectional linking. Spec→code is done (74/74 features), but 70 code modules and 3 classes have zero links back to spec features.
