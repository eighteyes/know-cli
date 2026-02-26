# Prepare QA: know-cli - ANSWERS

## 1. Users & Objectives

**Q1: Who are the distinct user personas for know-cli?**
A1:
- `user:solo-developer` — Primary user: solo technical lead (includes teams-of-one) doing rapid prototyping with AI assistance
- `user:ai-agent` — Secondary user: AI agents (Claude, GPT) consuming structured graph context
- `user:know-maintainer` — Contributor maintaining/extending the know-cli tool itself

**Q2: What does each user type want to accomplish?**
A2:
- `objective:structure-product-context` (solo-developer) — Convert conversations into queryable graphs
- `objective:generate-ai-specs` (solo-developer) — Produce specs that AI agents understand without token waste
- `objective:track-implementation-progress` (solo-developer) — Link features to code, track completion
- `objective:build-features` (solo-developer) — Use graph to guide feature development
- `objective:review-features` (solo-developer) — Validate features against graph requirements
- `objective:adapt-existing-codebase` (solo-developer) — Integrate know into existing projects
- `objective:be-source-of-truth` (solo-developer) — Make graph the authoritative product spec
- `objective:query-graph-intelligence` (ai-agent) — Get product context via structured queries
- `objective:maintain-tool-quality` (know-maintainer) — Keep codebase healthy, add features, fix bugs

**Q3: How do user goals and access levels differ?**
A3: All users have same CLI access (no auth system - it's a local tool). Goals differ by role:
- Solo-dev: Speed of development, AI alignment
- AI-agent: Context quality, query efficiency
- Maintainer: Code quality, test coverage, backwards compatibility

**Q4: Are there secondary actors beyond human users?**
A4: External dependencies (not modeled as users):
- CI/CD systems running validation
- Git hooks for graph protection
- External tools (ast-grep, jq, fzf)

**Q5: What does success look like for each user type?**
A5:
- Solo-dev: Features built faster with better AI alignment, less rework
- AI-agent: Accurate implementation plans without repeated exploration
- Maintainer: 80%+ test coverage, zero breaking changes, clear contribution path
- CI/CD: All graphs valid, no orphans, 100% coverage

---

## 2. Features

**Q6: What are the distinct named capabilities visible in know-cli?**
A6: Based on command groups (LLM features REMOVED - old thinking):
- `feature:graph-management` — CRUD operations, migration, deprecation, phases (add, list, get, link, unlink, delete, deprecate, phases)
- `feature:graph-validation` — Multi-level validation (syntax, structure, semantics, health, cycles)
- `feature:spec-generation` — Generate markdown/XML specs from graph entities
- `feature:feature-lifecycle` — Track features from conception to completion (contracts, git integration)
- `feature:graph-visualization` — Multi-format rendering (tree, mermaid, dot, HTML, fzf)
- `feature:search-discovery` — Semantic search and entity discovery (TF-IDF indexing)
- `feature:cross-graph-linking` — Connect spec-graph ↔ code-graph
- `feature:code-analysis` — Generate code-graph from AST (codemap)
- `feature:impact-analysis` — Analyze feature dependencies and blast radius

**Q7: Graph Lifecycle vs Feature-Specific — Are these separate or bundled?**
A7: Separate features:
- `feature:graph-management` — link/unlink, add/delete entities (structural changes)
- `feature:graph-validation` — check validate, health, cycles (quality checks)
- `feature:graph-visualization` — tree, mermaid, dot outputs (representation)
These share components but serve distinct user objectives.

**Q8: Is there a feature:spec-generation and feature:code-mapping?**
A8:
- `feature:spec-generation` — YES: `know gen spec`, `know gen sitemap`, markdown/XML output
- `feature:code-mapping` — YES: `know gen codemap`, code-graph generation from AST
- `feature:cross-graph-linking` — Separate feature maintaining spec↔code bridges via implementation/code-link refs

**Q9: Is there a feature:feature-lifecycle?**
A9: YES — `feature:feature-lifecycle`:
- `know feature contract` — Initialize/update contracts
- `know feature done` — Mark complete and archive
- `know feature impact` — Analyze dependencies
- `know feature coverage` — Track implementation status
Distinct from entity CRUD because it includes git integration, contract tracking, and drift analysis.

**Q10: Search/visualization/navigation — separate or bundled?**
A10: TWO distinct features:
- `feature:search-discovery` — Semantic search (TF-IDF), entity finding
- `feature:graph-visualization` — Multi-format rendering
- Dependency navigation (`uses`, `used-by`) is part of `feature:graph-management`

---

## 3. Actions & Operations

**Q11: User-initiated entity management actions and operations**
A11:
Actions:
- `action:create-entity` → operations: validate-entity-schema, check-unique-key, write-graph-file
- `action:link-entities` → operations: validate-dependency-rule, detect-cycle, update-graph-section
- `action:delete-entity` → operations: check-dependents, remove-links, update-graph-file
- `action:rename-entity` → operations: update-all-references, preserve-dependencies, validate-new-key

**Q12: Validation workflow operations**
A12:
- `operation:validate-json-syntax` — Parse JSON, check structure
- `operation:validate-entity-schema` — Check name/description fields
- `operation:validate-dependency-rules` — Load rules, check allowed_dependencies
- `operation:detect-circular-dependencies` — Build DiGraph, run NetworkX cycle detection
- `operation:find-orphaned-nodes` — Identify entities with no incoming edges
- `operation:calculate-completeness-score` — Count references vs expected references
- `operation:build-topological-order` — NetworkX topological_sort for build order

**Q13: Feature lifecycle actions and operations**
A13:
Actions:
- `action:initialize-feature-contract` → operations: create-yaml-template, populate-metadata
- `action:mark-feature-complete` → operations: update-contract-status, tag-git-commit, archive-feature
- `action:assess-feature-drift` → operations: query-git-changed-files, compare-declared-vs-observed, calculate-confidence-score

**Q14: Spec generation actions and operations**
A14:
Actions:
- `action:generate-entity-spec` → operations: resolve-dependency-chain, build-user-story, format-markdown-template
- `action:generate-codemap` → operations: parse-ast, extract-imports, map-to-modules
- `action:generate-xml-tasks` → operations: traverse-build-order, create-task-nodes, serialize-xml

**Q15: Cross-graph integration actions**
A15:
Actions:
- `action:connect-code-to-feature` → operations: find-spec-feature, create-code-link-reference, update-both-graphs
- `action:generate-coverage-report` → operations: traverse-spec-graph, find-implementations, compute-percentage
- `action:migrate-graph-schema` → operations: load-old-format, transform-structure, validate-new-schema

---

## 4. Components

**Q16: Graph persistence & state management**
A16:
- `component:graph-cache-manager` — GraphCache class (thread-safe, mtime tracking, atomic writes)
- `component:file-persistence-layer` — GraphManager save/load methods
Boundary: Cache handles in-memory state, persistence handles disk I/O. Separate responsibilities.

**Q17: Graph transformation & algorithm execution**
A17:
- `component:graph-algorithm-engine` — NetworkX DiGraph construction and traversal
- Part of GraphManager but distinct responsibility
- Diff logging (diff-graph.jsonl) belongs to `component:file-persistence-layer`

**Q18: Rule enforcement & schema validation**
A18: TWO components:
- `component:dependency-validator` — DependencyManager (checks allowed_dependencies rules)
- `component:schema-validator` — GraphValidator (checks entity schema, references, completeness)
Entity metadata validation lives in schema-validator.

**Q19: CLI output formatting & terminal rendering**
A19:
- `component:visualization-engine` — BaseVisualizer (extraction logic, filtering, depth limiting)
- `component:format-renderer-{type}` — Separate per format (dot, mermaid, html, tree, fzf)
- Rich terminal styling is part of each format-renderer, not separate component

**Q20: External service integration**
A20:
- `component:semantic-search-indexer` — SemanticSearcher (TF-IDF for entity search)
- `component:git-integration` — FeatureTracker (git commands, commit tagging)
Note: LLM/API integration is deprecated (old thinking), code exists but feature removed from spec.

---

## 5. Data Models

**Q21: Primary data entities and key fields**
A21:
- `data-model:graph-document` —
  - Required: meta (dict), entities (dict), references (dict), graph (dict)
  - Optional: None (all 4 sections required)
  - Constraints: JSON serializable

- `data-model:entity` —
  - Required: name (str), description (str)
  - Optional: metadata (dict, allowed fields per rules)
  - Constraints: kebab-case key, no relationship fields

- `data-model:reference` —
  - Required: None (flexible schema)
  - Optional: Any fields
  - Constraints: JSON serializable

- `data-model:dependency-link` —
  - Required: depends_on (list of entity/reference IDs)
  - Optional: None
  - Format: {"entity:key": {"depends_on": ["other:entity", "ref:type"]}}

**Q22: Entity relationships and links**
A22:
- Entities reference entities: via graph.depends_on array (unidirectional)
- Entities reference references: via graph.depends_on array (always valid)
- Spec↔code cross-linking: via `code-link` (spec→code modules) and `implementation` (code→spec feature) references
- Foreign key pattern: `type:name` string references (e.g., "feature:auth")

**Q23: Central domain entities**
A23: Most central:
1. `data-model:graph-document` — Root container for all data
2. `data-model:entity` — Core node type (everything is entities or references)
3. `data-model:dependency-link` — Defines all relationships

**Q24: Lifecycle of Graph entity**
A24:
- **Created**: `know init` creates template, or manually via JSON
- **Loaded**: GraphCache reads JSON, validates syntax, caches in memory with mtime
- **Modified**: EntityManager/DependencyManager mutate in-memory structure
- **Validated**: GraphValidator runs before/after saves (configurable)
- **Saved**: Atomic write (temp file → rename), diff logged to diff-graph.jsonl
- **Deleted/Archived**: Soft-delete via meta.deprecated, or file deletion

**Q25: Implied data entities without clear schemas**
A25:
- `data-model:cache-entry` — TODO: Document GraphCache._cache structure
- `data-model:diff-record` — Structure of diff-graph.jsonl entries (before/after snapshots, timestamps)
- `data-model:validation-result` — Error objects with type, message, entity_id, severity
- `data-model:search-index` — TF-IDF term weights, document vectors, SHA256 hashes
- `data-model:build-state` — build-progress.json structure (current task, checkpoints, wave status)

---

## 6. Interfaces & API Contracts

**Q26: CLI command interface**
A26:
- `interface:cli-commands` — Click framework, 80+ commands in 11 groups
- Common patterns: `-g` (graph path), `-r` (rules path), `-v` (verbose), `--format` (output format)
- Standard structure: `know [group] [command] [args] [options]`

**Q27: LLM provider API contracts**
A27: REMOVED — LLM integration is deprecated (old thinking). Code exists in src/llm.py but feature not in active spec.

**Q28: Graph JSON schema**
A28:
- `api_contract:graph-json-schema` —
  - Root: {meta, entities, references, graph}
  - meta: {project, phases, decisions, deprecated, feature_commits}
  - entities: {entity_type: {entity_key: {name, description, metadata}}}
  - references: {ref_type: {ref_key: {...}}}
  - graph: {entity_id: {depends_on: [...]}}

**Q29: AsyncGraphManager server API**
A29: REMOVED — Async API is deprecated (old thinking). Code exists in src/async_graph.py but feature not in active spec.

**Q30: Contract YAML format**
A30:
- `api_contract:feature-contract-yaml` —
  - version, status, confidence, last_updated, declared (actions, files, entities), observed (files, entities, actions)
  - Drift calculation: declared - observed = missing/extra items
  - Confidence: based on age, drift amount, verification_count

---

## 7. Business Logic & Security

**Q31: Validation state machine**
A31:
- States: valid (no errors), invalid (errors present), warnings (non-fatal issues)
- Transitions: invalid → valid requires fixing all errors; warnings → valid requires --strict mode
- Entity type changes: Must manually update all dependency links (no auto-migration)
- Orphaned nodes: Always errors, cannot be grandfathered

**Q32: Dependency rule conflict resolution**
A32:
- Local `.ai/know/config/dependency-rules.json` OVERRIDES package defaults entirely (no merge)
- Conflicts: First matching rule wins (order matters in allowed_dependencies list)
- Circular dependencies: Detected and rejected (no auto-break, must manually fix)
- Cross-graph links: Reference dependencies bypass entity rules (always allowed)

**Q33: Reference vs entity promotion**
A33:
- `constraint:references-never-promote` — References NEVER become entities
- References are terminal nodes with flexible schema
- Entities are structural nodes with fixed schema (name, description)
- No conversion mechanism exists or should exist

**Q34: Graph merge/diff logic**
A34:
- Conflicting edits: Last-write-wins (no merge conflict resolution)
- `know graph link`: Validates BEFORE writing (fail-fast)
- Metadata during diffs: Timestamps updated, authors preserved if in entity.metadata
- Soft-delete: meta.deprecated with reason/date, hard-delete removes from JSON

**Q35: Build order enforcement**
A35:
- Topological sort considers: depends_on edges ONLY (references treated as edges)
- Circular relationships: Forbidden even across graph partitions (spec/code graphs validated separately)
- Roots: Entities with no depends_on (typically users, projects)
- Leaves: Entities with no dependents (typically operations, detailed components)

**Q36: Graph file integrity**
A36:
- Manual JSON edits: Detected via validation on next load (syntax/schema checks)
- Checksums: SHA256 hash for search index staleness, not for file integrity
- Direct file writes: No prevention mechanism (trust-based, local tool)
- Audit log: diff-graph.jsonl captures structural changes, Git history for file-level tracking

**Q37: Sensitive data handling**
A37:
- Validation error messages: Include entity content (descriptions) for debugging
- Graph exports: No filtering (assumes local use, trusted environment)
- Verbose logs: Include full entity data, reference values
- PII/secret masking: None (user responsible for not storing secrets in graphs)

**Q38: Access control**
A38:
- Protected entity types: None (all deletable via CLI)
- External scripts: Can bypass know and mutate JSON directly (no lock files)
- Dangerous operations: No confirmation flags (assumes expert users)
- Future consideration: Undo command for mistake recovery

**Q39: Dependency rule override**
A39:
- No --force flag (validation always runs)
- Users can edit local dependency-rules.json (trusted local environment)
- Administrative entity types: meta section ignores hierarchy
- Malicious rules: No prevention (local file system access required)

**Q40: External tool integration**
A40:
- Input sanitization: None (trusted local tools)
- Export escaping: HTML format escapes special characters, others assume safe consumption
- Injection risks: Entity IDs validated as kebab-case (no path traversal risk)
- [UNCERTAIN - NEED INPUT: Should we add sanitization for external tool integration?]

---

## 8. Configuration & Constraints

**Q41: Environment variable dependencies**
A41:
- `configuration:env-vars` —
  - Optional: KNOW_GRAPH_PATH, GIT_* (inherited from shell)
  - Working directory: Must contain .ai/know/ or specify path via -g
  - Note: LLM API keys removed (deprecated features)

**Q42: Hard-coded limits (should be configurable)**
A42:
- `configuration:git-command-timeout` — 30 seconds (src/feature_tracker.py:77) — SHOULD BE CONFIGURABLE
- `configuration:max-validation-warnings` — 10 items (src/validation.py:455, 524) — SHOULD BE CONFIGURABLE
- Note: LLM limits removed (deprecated features)

**Q43: Test-driven acceptance criteria**
A43:
- `acceptance_criterion:graph-four-sections` — Graph must have meta, entities, references, graph
- `acceptance_criterion:kebab-case-names` — Entity names use kebab-case, not underscores
- `acceptance_criterion:typed-graph-keys` — Graph keys follow type:name format
- `acceptance_criterion:no-circular-dependencies` — Cycle detection must reject loops
- `acceptance_criterion:no-orphaned-nodes` — Disconnected entities are errors
- `acceptance_criterion:unidirectional-dependencies` — All edges flow one direction

**Q44: Deployment & runtime assumptions**
A44:
- `constraint:python-version` — Python 3.8+ required
- `configuration:file-system-access` — Read/write to .ai/know/, package config directory
- `configuration:git-in-path` — Git CLI available for feature tracking
- `configuration:directory-structure` — .ai/know/ exists, optional .ai/know/config/ for local rules

**Q45: Schema validation rules — constraint or implementation detail?**
A45:
- `constraint:meta-phases-must-be-dict` — Not list/array
- `constraint:entities-require-name-description` — Both fields mandatory
- `constraint:no-relationship-fields-in-entities` — refs/parent/screen forbidden (must use graph)
- `constraint:references-flexible-schema` — No required fields
- `constraint:entities-allowed-metadata-only` — Only fields from rules.entity_note permitted

These are constraints (documented requirements), not just implementation details.

---

**Summary:**
- 45 questions answered
- 9 marked [UNCERTAIN - NEED INPUT]
- Ready to build graphs once uncertainties resolved
