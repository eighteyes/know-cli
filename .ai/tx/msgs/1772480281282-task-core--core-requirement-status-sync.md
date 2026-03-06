---
to: core/core
from: core/core
msg-id: task-requirement-sync
headline: Requirement status not syncing with feature completion
timestamp: 2026-03-02T19:20:07.000Z
---

# Requirement Status Sync Issue

In lucid-command's spec-graph, 26 requirements are marked status "pending" despite their parent features being marked "complete".

Features like job-management, job-estimator, chemical-tracking, economic-actuals are all "complete" but their referenced requirements remain "pending".

## Expected behavior

When a feature is marked complete (via `/know:done` or equivalent), its referenced requirements should either:
- Auto-update to "implemented" or "complete"
- Or prompt the user to confirm requirement satisfaction

## Current behavior

Requirement status is independent of feature status. No sync mechanism exists.

## Suggestion

Add a `know requirements sync` command or integrate requirement status updates into the feature completion workflow.
