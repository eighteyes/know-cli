# Bug: `meta set` crashes when section value is a string

**From:** lucid-command
**Priority:** low

## Issue

`know meta set project id lucid-command` crashes with `TypeError: 'str' object does not support item assignment` when `meta.project` is a bare string instead of a dict.

## Reproduction

1. Have a graph where `meta.project` is a string (e.g. `"lucid-nexus"`)
2. Run `know meta set project id lucid-command`

## Error

```
File "know.py", line 325, in meta_set
    graph_data['meta'][section][key] = meta_data
TypeError: 'str' object does not support item assignment
```

## Expected

`meta set` should detect that the existing section value is not a dict and either:
- Replace it with `{}` then set the key
- Give a clear error suggesting `meta delete` first

## Additional context

`meta delete` also can't fix this — it requires a KEY argument and doesn't support deleting an entire section that's a bare string. Only workaround is direct `jq` on the graph file.
