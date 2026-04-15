---
name: Know: List Features
description: Show all planned, in-progress, and completed features grouped by horizon
category: Know
tags: [know, list, status]
---
Show all features grouped by horizon with task completion counts.

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
