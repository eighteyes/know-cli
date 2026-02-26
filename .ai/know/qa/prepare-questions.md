# Prepare QA: know-cli
_Each answer maps to a graph entity or reference. See type hints per section._

**Context**: These questions are for populating **know-cli's own spec-graph** (the tool's self-documentation), NOT template questions for end users.

---

## 1. Users & Objectives  [→ user:*, objective:*]

**Clarification needed**: Are we defining who uses know-cli itself, or template questions for know-cli to ask its users?
**Answer**: Option A — Who uses know-cli itself (e.g., `user:solo-dev`, `user:tech-lead`)

1. **Who are the distinct user personas for know-cli?** — Primary users appear to be solo technical leads doing rapid AI-assisted prototyping with Claude Code. Are there other distinct user types (maintainers, contributors, team leads, end-users of generated specs)?

2. **What does each user type want to accomplish with know-cli?** — What are the core objectives? (e.g., objective:structure-product-context, objective:generate-ai-specs, objective:track-implementation-progress, objective:validate-graph-integrity)

3. **How do user goals and access levels differ?** — Do all users have the same capabilities, or are there admin/contributor/viewer roles? Do objectives differ by experience level (beginner vs advanced use cases)?

4. **Are there secondary actors beyond human users?** — Does know-cli interact with CI/CD systems, GitHub Actions workflows, LLM APIs, or git hooks as "users" with their own objectives?

5. **What does success look like for each user type?** — For a solo dev, is success "faster feature development"? For a maintainer, is it "complete graph coverage"? Define success criteria per user.

---

## 2. Features  [→ feature:*]

6. **What are the distinct named capabilities visible in the know-cli codebase?** — From 80+ commands and 11 groups, which are user-facing features vs implementation details? (e.g., feature:graph-management, feature:validation-suite, feature:spec-generation)

7. **Graph Lifecycle Management vs Feature-Specific Operations** — Are `graph link/unlink`, `check validate`, and visualization separate features, or all part of feature:graph-management? Where's the boundary?

8. **Specification-to-Implementation Pipeline** — Is there a feature:spec-generation that creates entities from requirements? A feature:code-mapping that maintains spec↔code bridges? Or is cross-linking embedded across multiple features?

9. **Feature Lifecycle Tracking (Meta-Features)** — The phrase "feature lifecycle" appears in the code. Is there a feature:feature-lifecycle that tracks features from conception→implementation→deprecation, or is this just entity CRUD with extra steps?

10. **Search, Discovery, and Navigation** — Are search indexing, visualization (tree, HTML, mermaid, dot, fzf), and dependency navigation separate features (feature:search-index, feature:graph-visualization, feature:dependency-navigation), or all part of feature:graph-exploration?

---

## 3. Actions & Operations  [→ action:*, operation:*]

11. **User-Initiated Entity Management** — When a user modifies the graph (adding nodes, linking dependencies, removing entities, renaming keys), what are the discrete named user actions? What are the prerequisite validation operations and persistence operations for each action?

12. **Graph Validation and Health Checks** — When validation runs (syntax, structure, semantics, full, health, cycles, orphans), what are the specific internal processing steps? Which operations build intermediate data structures (adjacency lists, topological sort)? Which operations are reused across validation layers?

13. **Feature Lifecycle Management Workflow** — When managing features (contract creation, validation, tagging, archiving), what are the user actions (action:initialize-feature-contract, action:mark-feature-complete) and system operations (operation:query-changed-files, operation:tag-commits-with-notes, operation:compare-declared-vs-observed)?

14. **Spec and Documentation Generation Workflow** — What are the user generation requests (action:generate-entity-spec, action:generate-codemap, action:generate-trace-matrix) and internal processing operations (operation:resolve-dependency-chain, operation:build-user-story, operation:format-markdown-spec, operation:parse-xml-spec)?

15. **Cross-Graph Integration and Migration** — For workflows that cross graph boundaries (spec↔code), what are the user actions (action:connect-code-to-feature, action:generate-coverage-report) and graph traversal operations (operation:find-spec-implementation, operation:compute-coverage-percentage, operation:migrate-graph-schema)? What failure paths exist?

---

## 4. Components  [→ component:*]

16. **Graph Persistence & State Management** — What component handles atomic file writes, concurrent access control, and cache invalidation? Is this component:graph-cache-manager, component:file-persistence-layer, or bundled? Where's the boundary between caching (GraphCache) and persistence (GraphManager)?

17. **Graph Transformation & Algorithm Execution** — What component builds the NetworkX DiGraph and executes traversal algorithms? Is this component:graph-algorithm-engine, component:networkx-adapter, or part of GraphManager? Does diff-graph.jsonl logging belong here?

18. **Rule Enforcement & Schema Validation** — DependencyManager and GraphValidator both touch rules but serve different purposes. Are these one component (component:validation-engine) or two (component:dependency-rules-enforcer + component:schema-validator)? Where does entity metadata validation live?

19. **CLI Output Formatting & Terminal Rendering** — The visualizers/ package has BaseVisualizer extraction logic plus format-specific renderers. Is this one component (component:multi-format-visualizer) or should each format be its own component? Where does Rich terminal styling fit?

20. **External Service Integration** — What component manages HTTP requests to LLM providers, handles API authentication, formats prompts, and parses responses? Is this component:llm-api-client, component:http-provider-adapter, or part of a larger AI integration? Does semantic search indexing belong in the same component or separate?

---

## 5. Data Models  [→ data-model:*]

21. **Primary Data Entities and Key Fields** — What are the core data entities (Graph, Entity, Reference, Dependency, Meta) and their essential fields? For each, list: required fields, optional fields, data types, constraints.

22. **Entity Relationships and Links** — How do entities reference other entities (through graph.depends_on)? How do spec-graph and code-graph cross-link (via code-link and implementation references)? What are the foreign key patterns?

23. **Central Domain Entities** — Which data entities are most central to Know's domain model? Rank by: how many other entities depend on them, how frequently they appear in operations, whether they're required for the system to function.

24. **Lifecycle of the Graph Entity** — Trace the complete lifecycle: Created (how initialized?), Loaded (through GraphCache with validation?), Modified (what operations mutate it?), Validated (what checks run?), Saved (atomic write with diff logging?), Deleted/Archived (soft-delete patterns?).

25. **Implied Data Entities Without Clear Schemas** — Are there entities implied by the code that lack explicit schemas? (Cache entries in GraphCache._cache, Diff records in diff-graph.jsonl, NetworkX graph nodes, Validation results, Search indices, Build state in build-progress.json)

---

## 6. Interfaces & API Contracts  [→ interface:*, api_contract:*]

**Clarification needed**: Agent 6 needs file paths for:
- CLI command definitions (know.py? know/commands/?)
- LLM provider integration (where are actual API calls?)
- Graph JSON schema validation (in-code or JSON Schema files?)
- AsyncGraphManager API (where defined?)
- Contract YAML format (where is parsing/generation?)

26. **CLI Command Interface** — What are the main CLI commands (from 80+ commands in 11 groups)? What is the Click framework structure? What flags/options/arguments are common patterns?

27. **LLM Provider API Contracts** — What are the API contracts for Anthropic, OpenAI, and custom providers? What are the request/response shapes, authentication patterns, and error handling?

28. **Graph JSON Schema** — What is the formal schema for spec-graph.json and code-graph.json? What are the validation rules, required vs optional fields, and allowed values?

29. **AsyncGraphManager Server API** — What is the async API surface for server integration? What methods are exposed, what are the threading/concurrency guarantees, and what are the performance characteristics?

30. **Contract YAML Format** — What is the schema for feature contracts in contract.yaml? What fields are tracked (declared vs observed), and how is drift calculated?

---

## 7. Business Logic & Security  [→ business_logic:*, security-spec:*]

31. **Validation State Machine** — What are the transition rules between invalid/valid states? Are there intermediate states (warnings vs errors)? What happens to dependencies when entity types change? Can orphaned nodes be grandfathered in?

32. **Dependency Rule Conflict Resolution** — When local dependency-rules.json conflicts with package defaults, which fields merge vs override? If a dependency is simultaneously allowed and forbidden, which wins? How are circular dependencies handled?

33. **Reference vs Entity Promotion** — What complexity threshold forces a reference to become an entity? Are there forbidden conversions? What's the execution order for batch operations touching both?

34. **Graph Merge/Diff Logic** — How are conflicting edits reconciled? Does `know graph link` validate before writing or write-then-validate? What happens to metadata during diffs? Are there soft-delete mechanics?

35. **Build Order Enforcement** — Does topological sort consider only depends_on edges or also reference usage? Can circular relationships exist in different graph partitions? What entities are roots vs leaves?

36. **Graph File Integrity** — Does the system detect manual JSON edits that bypass validation? Are there checksums or fingerprints? What prevents direct file writes from creating invalid states?

37. **Sensitive Data Handling** — Do validation error messages leak entity content? Are graph exports filtered? What data is excluded from logs in verbose mode? Are there PII/secret patterns that get masked?

38. **Access Control in Graph Operations** — Are there protected entity types that cannot be deleted? Can external scripts bypass know and mutate JSON directly? Are there dangerous operations requiring confirmation flags?

39. **Dependency Rule Override** — Is there a --force flag? Can users edit local dependency-rules.json to permit invalid structures? Are there administrative entity types that ignore hierarchy? What prevents malicious rule injection?

40. **External Tool Integration** — When scripts (ast-grep, jq, txlit) interact with the graph, are inputs sanitized? Do exports escape special characters? Are there injection risks in dynamically generated commands? What validation exists on entity IDs to prevent path traversal?

---

## 8. Configuration & Constraints  [→ configuration:*, constraint:*, acceptance_criterion:*]

41. **Environment Variable Dependencies** — LLM system requires ANTHROPIC_API_KEY and OPENAI_API_KEY. What other env vars does the system rely on (GIT_*, PYTHONPATH, working directory)? Should these be captured in configuration references?

42. **Hard-Coded Limits & Invariants** — The codebase has limits: LLM retry attempts (3), retry delay (2s), request timeout (30s), max tokens (4096), git command timeout (30s), max validation warnings displayed (10). Should these become constraint references? Which are invariants vs tunable parameters?

43. **Test-Driven Acceptance Criteria** — Tests assert: graph must have 4 top-level keys, entity names must use kebab-case, graph keys must follow type:name format, no circular dependencies, orphaned nodes are errors, rules must be unidirectional. Which assertions should become acceptance_criterion references? Are they ALL criteria, or do some belong in constraint?

44. **Deployment & Runtime Environment Assumptions** — System assumes: Python with urllib, file system access for config, git in PATH, local rules override package defaults, specific directory structure (.ai/know/). What configuration is MISSING that the system clearly needs? Should we document expected structure, Python version, required external tools?

45. **Schema Validation & Data Integrity Constraints** — Validation enforces: meta.phases must be dict, entities must have name/description, entities cannot have relationship fields (must be in graph), references have flexible schema, only allowed metadata fields. Are these constraint references or implementation details? Where's the line between "documented constraint" and "code-level validation logic"?

---

_Answers:_

