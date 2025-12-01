---
name: Know: List Features
description: Show all planned, in-progress, and completed features
category: Know
tags: [know, list, status]
---

**Workflow**

1. Scan `.ai/know/` directory for feature directories (exclude `archive/`)
2. For each feature directory:
   - Check `todo.md` for completion status
   - Determine state: planned (no checkmarks), in-progress (some checkmarks), completed (all checkmarks)
3. Scan `.ai/know/archive/` for completed features
4. Display organized table showing:
   - Feature name
   - Status (planned/in-progress/completed)
   - Location (active or archived)
   - Brief summary from overview.md if available

**Output Format**
```
Active Features:
  [in-progress] user-authentication (3/8 tasks complete)
  [planned]     payment-gateway

Archived Features:
  [completed]   initial-setup
  [completed]   database-migration
```

**Notes**
- Read first line of overview.md for feature description
- Count checked/total items in todo.md for progress
- Highlight features that might be stale
