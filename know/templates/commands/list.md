---
name: Know: List Features
description: Show all planned, in-progress, and completed features grouped by status
category: Know
tags: [know, list, status]
---

**Workflow**

1. Scan `.ai/know/` directory for feature directories (exclude `archive/`, `qa/`, `flows/`, `product/`, etc.)
2. For each feature directory:
   - Read `todo.md` to count completed vs total checkboxes
   - Read `overview.md` first line for feature name
   - Determine status:
     - ✅ completed: All checkboxes marked [x]
     - 🔄 in-progress: Some checkboxes marked [x]
     - 📋 planned: No checkboxes marked [x]
3. Scan `.ai/know/archive/` for archived features
4. Group features by status and display in phase-style format

**Output Format**

Match the style of `know phases` command:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
In Progress (3 features)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔄 User Authentication                              (3/8)
  🔄 Payment Gateway Integration                      (12/25)
  🔄 Dashboard Redesign                               (1/15)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Planned (2 features)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📋 Email Notifications                              (0/10)
  📋 Admin Panel                                      (0/22)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Archived (1 features)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Initial Setup                                    (8/8)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 6 features, 24/88 tasks (27% complete)
Legend: ✅ completed  🔄 in-progress  📋 planned
```

**Implementation Steps**

1. Scan `.ai/know/` and identify feature directories (dirs with `todo.md`)
2. For each feature:
   - Count checkboxes in `todo.md`: `- [x]` vs `- [ ]`
   - Read first line of `overview.md` for display name
   - Calculate status: 0% = planned, 100% = completed, else in-progress
3. Group features by status (in-progress, planned, completed/archived)
4. Print using Rich console with:
   - Bold cyan headers with ━ separators (80 chars wide)
   - Status icon + feature name (left-aligned, 45 chars wide) + task count
   - Summary footer with totals and legend
5. Use same status icons as `know phases`: ✅ 🔄 📋

**Notes**

- Only scan directories that contain `todo.md` (ignore metadata dirs)
- Feature name comes from `overview.md` first line, fallback to directory name
- Empty `todo.md` = 0 tasks
- Match exact formatting of `know phases` for consistency
