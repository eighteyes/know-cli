---
name: Know: List Features
description: Show all planned, in-progress, and completed features grouped by horizon
category: Know
tags: [know, list, status]
---
Show all features grouped by horizon with task completion counts.

**Arguments**: `$ARGUMENTS` — optional horizon filter (e.g., `/know:list done` or `/know:list in-progress`)

**Objective**

Display all features grouped by horizon with task completion counts.

**Implementation**

Run the `know horizons` command:

```bash
know horizons
```

This command displays features grouped by horizon (I, II, III, in-progress, review-ready, done) with:
- Horizon shortname, name, and description
- Features within each horizon
- Task completion counts from todo.md (e.g., "3/13")
- Status icons (✅ completed, 🔄 in-progress, 📋 planned)
- Summary footer with totals

**Note**: For per-feature reference counts, use `know check stats` which now displays references by type. To see a specific feature's references, run `know graph uses feature:<name>`.
