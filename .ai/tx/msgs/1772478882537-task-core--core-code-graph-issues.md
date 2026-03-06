---
to: core/core
from: core/core
msg-id: task-1772478500
headline: Code-graph structural issues found by documentarian audit
timestamp: 2026-03-02T19:08:20.000Z
---

# Code-Graph Issues — Documentarian Audit Findings

Two structural problems in `.ai/code-graph.json` discovered during divergence analysis of lucid-command project.

## Issue 1: File Path Prefix Wrong on All API Modules

All 73 API module entries use `know/src/` prefix instead of `api/src/`.

**Example:**
- Code-graph says: `"file_path": "know/src/app.ts"`
- Actual path: `api/src/app.ts`

This affects every API module in the graph. Likely a historical artifact from when the project had a different directory structure (or the `know` CLI defaulted its own prefix during graph generation).

**Impact:** Any tooling that uses code-graph paths for module discovery, cross-linking, or validation will fail. `know graph cross connect` references will point to non-existent files.

**Fix needed:** Bulk rename `know/src/` → `api/src/` across all module `file_path` values in code-graph.json.

## Issue 2: WWW Layer Entirely Missing from Code-Graph

The code-graph only tracks API-side modules (73 entries). The entire frontend is absent:

- **24 pages** in `www/src/pages/` (including AddJobPage 38KB, JobDetailPage 33KB)
- **67+ components** in `lib/components/` (30 directories)
- **18 services** in `lib/services/`

The spec-graph defines 25 components, but there's no code-graph counterpart to cross-link against. This means `know graph cross connect` cannot map spec components to frontend implementation.

**Impact:** No traceability between spec-graph components and actual frontend code. Frontend is a blind spot for all graph-based analysis.

**Fix needed:** Run code-graph generation against `www/src/` and `lib/` directories to populate frontend modules.

## Context

- Graph location: `.ai/know/` directory (lucid-command project)  
- Spec-graph: 95 entities including 25 components
- Code-graph: 73 modules (API only)
- Canonical schema: `api/prisma/schema.prisma`
