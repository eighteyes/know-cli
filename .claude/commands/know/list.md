---
name: Know: List Features
description: Show all planned, in-progress, and completed features grouped by phase
category: Know
tags: [know, list, status]
---

**Objective**

Display all features grouped by phase with task completion counts.

**Implementation**

Run the `know phases` command:

```bash
know phases
```

This command displays features grouped by phase (I, II, III, pending) with:
- Phase shortname, name, and description
- Features within each phase
- Requirement completion counts from spec-graph (e.g., "3/13" or "--" if none defined)
- Status icons (✅ complete, 🔄 in-progress, 📋 planned)
- Summary footer with totals

**Note**: Phase is the plan (WHEN), status is the territory (current state). A feature can be phase III but status in-progress.

