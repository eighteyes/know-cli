# Know-CLI Project Context Analysis

**Date**: 2025-12-05
**Version**: 0.0.1
**Status**: Pre-Launch Alpha

---

## Executive Summary

Know-CLI is an opinionated graph-based knowledge management tool designed primarily for AI-assisted software development. It replaces brittle spec.md files with interconnected dual-graph architecture that maps both user intent (product specifications) and implementation (code architecture). The project is functionally complete with 13 Python modules, comprehensive testing, and proven performance improvements (10-20x faster than original bash implementation). Primary gaps before public launch are around documentation, npm packaging, examples/demos, and community building.

---

## 1. Project Overview: What is Know-CLI?

### The Problem It Solves

**Traditional Spec Files Are Brittle:**
- spec.md files are prone to hallucination by LLMs
- Resistant to change and never internally consistent
- No single source of truth for relationships
- Token-wasting repetitive manual analysis by AI agents
- Difficult to maintain alignment between product intent and code implementation

**Example Pain Point**: When a developer asks an LLM "what features are affected by changing the authentication system?", traditional spec files require:
1. Reading entire spec document (high token cost)
2. Manual inference of relationships
3. Searching codebase separately
4. No guarantee of completeness or accuracy

### The Know-CLI Solution

**Dual Graph Architecture:**
1. **Spec Graph** (.ai/know/spec-graph.json): Maps user intent → features → components
   - Entity types: user, objective, feature, component, action, operation, requirement, interface
   - Answers "WHAT does the product do and WHY?"

2. **Code Graph** (.ai/know/code-graph.json): Maps implementation structure
   - Entity types: module, package, class, function, layer, interface, namespace
   - Answers "HOW is it built?"

3. **Product-Component References**: Links between the two graphs
   - Maps spec components to code modules
   - Enables tracing from user objectives → code implementation

**Core Dependency Model:**
- Unidirectional "depends_on" relationships
- Rule-based validation (dependency-rules.json, code-dependency-rules.json)
- Graph traversal enables impact analysis, gap detection, build ordering

**Key Capabilities:**
- Query relationships: "What uses this entity?" / "What does this entity use?"
- Validate graph structure automatically
- Detect circular dependencies and orphaned references
- Generate specifications from graph data
- Analyze implementation gaps
- Topological build ordering
- LLM integration for AI-assisted graph management

---

## 2. Current State: Development Progress

### Implementation Status: **Functionally Complete**

**Python Implementation (v0.0.1):**
- 13 core modules implemented (know/src/)
- 8 test modules with comprehensive coverage
- 40+ CLI commands operational
- Dual graph system with auto-detection
- Performance optimized with in-memory caching

**Core Modules (100% Complete):**
1. **graph.py**: Core graph operations with NetworkX integration
2. **cache.py**: Thread-safe in-memory caching with atomic writes
3. **entities.py**: Entity CRUD operations with validation
4. **dependencies.py**: Dependency management, cycle detection, topological sorting
5. **validation.py**: Rule-based graph validation
6. **generators.py**: Spec generation from templates
7. **llm.py**: LLM provider integration
8. **gap_analysis.py**: Implementation gap detection
9. **reference_tools.py**: Orphaned reference management
10. **async_graph.py**: Async operations for concurrent access
11. **utils.py**: Common utilities and helpers
12. **diff.py**: Graph diffing capabilities
13. **know.py**: CLI entry point with Click framework

**Testing Infrastructure:**
- 8 test files covering all major modules
- Pytest framework with async support
- Coverage reporting via pytest-cov
- Bug fix regression tests
- Benchmark suite for performance monitoring

**Documentation:**
- README.md with installation and usage examples
- CHANGELOG.md documenting evolution from bash → Python
- CLAUDE.md with AI agent instructions
- json-graph-learning.md with architectural insights
- Template files for workflow initialization

**Performance:**
- 10-20x faster than original bash/jq implementation
- Handles graphs with 1000+ entities efficiently
- In-memory caching for near-instantaneous repeated access

### Phase Tracking (from spec-graph.json)

**Phase I - Foundation (In Progress):**
- feature:auth (in-progress)
- feature:database (in-progress)

**Phase II - Features (Planned):**
- feature:api (planned)
- feature:ui (planned)

**Done:**
- feature:test-phase-feature (complete)

**Core Features (Deployed in 0.0.1):**
- CLI operations
- Graph validation
- Gap detection
- Spec generation
- LLM workflows

### What's Working Right Now

**Proven Capabilities:**
1. **Graph Management**: Add/remove entities, link dependencies, validate structure
2. **Query Operations**: Trace dependencies up/down, find orphaned references
3. **Analysis**: Gap detection, completeness scoring, health checks
4. **Generation**: Spec documents, feature specs, sitemaps
5. **Workflow**: /know-add, /know-list, /know-done commands for feature management
6. **Integration**: Claude Code skill available (.claude/skills/know-tool/)

**Real-World Usage:**
- Author reports "considerably better plans made with `know` than with other tools"
- LLMs intuit user intent instead of assuming
- Less time spent guiding AI agents
- Successful self-hosting (project's own spec-graph and code-graph are populated)

### Known Limitations

**From CLAUDE.md and code analysis:**
1. Graph validation currently uses spec-graph rules only; code-graph validation needs separate rules path support
2. CLI operates on one graph at a time (requires -g flag to switch)
3. No database backend (file-based JSON storage only)
4. Python 3.8+ dependency required

**From git status:**
- Multiple modified command templates not committed
- New .ai/ directory with transaction system (tx/) not fully integrated
- OpenSpec proposal system partially implemented
- Agent infrastructure (.claude/agents/) under development

---

## 3. Target Audience: Who Benefits?

### Primary Users

**1. AI Coding Assistants (Primary)**
- **Profile**: LLMs like Claude, GPT-4, Cursor, etc.
- **Use Case**: Query project structure without token-wasting analysis
- **Benefit**: Structured knowledge graph enables better planning and fewer hallucinations
- **Evidence**: "Designed primarily for automated access" (README), Claude Code skill provided

**2. Software Developers Using AI Tools**
- **Profile**: Developers working with AI pair programmers
- **Use Case**: Maintain single source of truth for product specs and code structure
- **Benefit**: AI assistants give better suggestions when they have structured context
- **Pain Point Addressed**: Specs that drift from implementation

**3. Solo Developers / Indie Hackers**
- **Profile**: Individual developers managing complex products
- **Use Case**: Track product intent and implementation relationships
- **Benefit**: Graph queries answer "what breaks if I change this?" instantly
- **Workflow**: Prefer automation over manual documentation

### Secondary Users (Potential)

**4. Small Development Teams (2-5 people)**
- **Use Case**: Shared understanding of system architecture
- **Benefit**: Graph serves as living documentation
- **Adoption Barrier**: Team must embrace CLI-first workflow

**5. Technical Architects**
- **Use Case**: Model system dependencies and detect architectural issues
- **Benefit**: Cycle detection, gap analysis, topological ordering
- **Value**: Architecture decisions backed by graph analysis

### User Characteristics

**What They Value:**
- Automation over manual work
- Single source of truth over scattered docs
- Queryable structure over prose
- AI-friendly formats
- Fast, deterministic tools

**What They Don't Need:**
- Beautiful GUIs (ergonomics "between tar and aws-cli")
- Human-readable spec documents as primary artifacts
- Traditional project management features
- Team collaboration features (v0.0.1)

**Technical Sophistication:**
- Comfortable with CLI tools
- Familiar with graph concepts (nodes, edges, dependencies)
- Using AI coding assistants regularly
- Interested in developer tooling experimentation

### Anti-Patterns (Who This ISN'T For)

- Teams requiring visual diagram editors
- Organizations needing compliance documentation
- Non-technical product managers
- Developers who don't use AI assistants
- Teams with established spec management processes

---

## 4. Unique Value Proposition

### What Makes Know-CLI Different?

**1. Dual-Graph Architecture**

**Competitors/Alternatives:**
- Traditional spec files (spec.md, PRD documents)
- Architecture documentation tools (C4 diagrams, PlantUML)
- Knowledge graphs (Obsidian, Roam Research)
- Code documentation (Sphinx, JSDoc)

**Know-CLI's Advantage:**
- **Two graphs, one truth**: Separate but linked graphs for product intent and code implementation
- **Bidirectional tracing**: From user objective → code module and back
- **Product-component references**: Explicit mapping between WHAT and HOW
- Example: `know trace component:cli-commands -c .ai/know/code-graph.json` shows both spec and code relationships

**2. LLM-First Design**

**Why It Matters:**
- Graph structure is machine-readable by default
- No prompt engineering needed to extract structure
- Eliminates hallucinations about relationships ("the graph IS the truth")
- Reduces token costs (query instead of reading entire spec)

**Competitive Advantage:**
- Spec files require LLM to infer relationships (unreliable, high-token)
- Code documentation doesn't capture user intent
- Know-CLI provides structured API for LLM queries

**Evidence:**
- Claude Code skill ships with the tool
- Author's direct experience: "considerably better plans"
- Integration points designed for AI workflows

**3. Dependency-Based Validation**

**The Problem:**
- Most specs/docs have no validation (anything goes)
- Code structure validation is syntax-only (linters, type checkers)
- No validation of product-code alignment

**Know-CLI's Solution:**
- `dependency-rules.json` defines allowed relationships for spec-graph
- `code-dependency-rules.json` defines allowed relationships for code-graph
- `know validate` catches violations automatically
- Example: Can't create action:login-user depending on user:developer (wrong direction)

**Impact:**
- Graph structure stays consistent
- Prevents architectural drift
- Catches errors before they compound

**4. Gap Analysis & Completeness Tracking**

**Unique Capability:**
- `know gap-analysis` identifies missing implementations in dependency chains
- `know completeness <entity>` scores entity data quality
- `know ref-orphans` finds references not connected to entities

**Why This Matters:**
- Traditional docs don't know what's missing
- Code analysis can't detect unimplemented features
- Know-CLI bridges intent and implementation

**Use Case:**
- Before sprint: "What's missing to complete feature:user-auth?"
- After refactor: "Did we break any dependency chains?"
- During planning: "What components lack descriptions?"

**5. Workflow Integration**

**The `/know` Command System:**
- `/know-add <feature>`: Scaffold feature directory + graph entries
- `/know-list`: Show all features by phase with task counts
- `/know-done <feature>`: Archive completed feature

**Competitive Advantage:**
- Most tools separate planning from execution
- Know-CLI workflow creates graph entries immediately
- Feature directories link to graph (overview.md → spec-graph entity)

**Result:**
- Graph stays in sync with development
- No "update the docs later" technical debt
- Living documentation system

**6. Performance at Scale**

**Benchmarked Results:**
- 10-20x faster than bash/jq implementation
- Handles 1000+ entity graphs efficiently
- In-memory caching with atomic writes

**Why This Matters:**
- Large projects (500+ components) are queryable instantly
- AI agents don't timeout waiting for graph operations
- Real-time validation during development

---

## 5. Launch Readiness Assessment

### What's Ready for Public Launch

**Core Functionality: READY**
- [x] Dual graph system operational
- [x] 40+ CLI commands implemented
- [x] Validation engine with rule-based checks
- [x] Gap analysis and completeness scoring
- [x] Spec generation from templates
- [x] LLM integration framework
- [x] Workflow commands (/know-add, /know-list, /know-done)
- [x] Performance optimized (10-20x improvement)
- [x] Thread-safe caching with atomic writes

**Testing: READY**
- [x] 8 test modules covering major functionality
- [x] Pytest framework with async support
- [x] Bug fix regression tests
- [x] Benchmark suite for performance monitoring

**Basic Documentation: READY**
- [x] README with installation and usage
- [x] CHANGELOG documenting version history
- [x] CLI help text for all commands
- [x] CLAUDE.md for AI integration
- [x] MIT License

**Code Quality: READY**
- [x] Type hints throughout
- [x] Black code formatting
- [x] MyPy type checking
- [x] Consistent architecture (manager pattern)

### What's Missing Before Public Launch

**CRITICAL (Blocks Launch):**

**1. npm Package Publishing**
- [ ] Issue: package.json exists but package not published to npm
- [ ] Blocker: Users can't run `npm install -g know-cli`
- [ ] Required: Publish to npm registry, verify cross-platform installation
- [ ] Estimated effort: 1-2 days (account setup, CI/CD integration, testing)

**2. Installation Documentation**
- [ ] Issue: README says `npm install -g know-cli` but package not available
- [ ] Blocker: Users hit dead end on first step
- [ ] Required: Update README with actual installation method
  - Manual installation from source
  - Python environment setup
  - Dependencies installation
  - Verification steps
- [ ] Estimated effort: 1 day

**3. Getting Started Guide**
- [ ] Issue: README has reference docs but no tutorial
- [ ] Blocker: High learning curve for new users
- [ ] Required:
  - "Your First Graph" tutorial (15 minutes)
  - Example project walkthrough
  - Common workflows documented
  - Troubleshooting section
- [ ] Estimated effort: 2-3 days

**HIGH PRIORITY (Significantly Improves Launch):**

**4. Example Projects**
- [ ] Issue: No reference implementations
- [ ] Impact: Users don't know what "good" looks like
- [ ] Required:
  - Sample spec-graph.json for different project types (CLI tool, web app, API)
  - Sample code-graph.json showing integration
  - Commented examples explaining design decisions
- [ ] Estimated effort: 3-4 days

**5. Video Demo / Walkthrough**
- [ ] Issue: Text-only documentation for visual tool
- [ ] Impact: Reduces adoption friction significantly
- [ ] Required:
  - 5-minute intro video: "What is Know-CLI?"
  - 10-minute tutorial: "Building Your First Graph"
  - 5-minute showcase: "Know-CLI + Claude Code"
- [ ] Estimated effort: 2-3 days (scripting, recording, editing)

**6. GitHub Repository Polish**
- [ ] Issue: Repo exists but not optimized for discovery
- [ ] Impact: Affects community trust and adoption
- [ ] Required:
  - Clean commit history (rebase if needed)
  - GitHub topics/tags for discoverability
  - Issue templates
  - Contributing guidelines
  - Code of conduct
- [ ] Estimated effort: 1-2 days

**7. Claude Code Skill Documentation**
- [ ] Issue: Skill exists (.claude/skills/know-tool/) but undocumented
- [ ] Impact: Primary use case (AI integration) not showcased
- [ ] Required:
  - Skill installation guide
  - Example prompts/workflows
  - Integration patterns with Claude Code
  - Comparison: "Before Know-CLI vs After"
- [ ] Estimated effort: 2 days

**MEDIUM PRIORITY (Nice to Have):**

**8. Website / Landing Page**
- [ ] Impact: Legitimacy signal, SEO, easier onboarding
- [ ] Required:
  - Single-page site explaining value proposition
  - Installation instructions
  - Live examples / interactive demo
  - Link to GitHub, npm, docs
- [ ] Estimated effort: 3-5 days
- [ ] Can defer until post-launch

**9. CI/CD Pipeline**
- [ ] Issue: GitHub Actions not configured (no .github/ directory)
- [ ] Impact: Manual testing/releasing is error-prone
- [ ] Required:
  - Run tests on PR
  - Automated PyPI publishing
  - Automated npm publishing
  - Cross-platform testing (macOS, Linux, Windows)
- [ ] Estimated effort: 2-3 days
- [ ] Can defer until first community contributions

**10. Community Building Prep**
- [ ] Issue: No audience, no distribution channels
- [ ] Impact: Launch to silence without preparation
- [ ] Required (per original task context):
  - Reddit community identification (r/AI, r/programming, r/MachineLearning, r/ChatGPT, r/ClaudeAI)
  - Reputation building in target communities
  - Launch announcement drafts (Reddit, HN, Twitter/X, Dev.to)
  - Demo assets ready to share
- [ ] Estimated effort: 2-4 weeks (reputation building takes time)

**11. Testimonials / Social Proof**
- [ ] Issue: Only one user (author) has used it
- [ ] Impact: Adoption barrier without validation
- [ ] Required:
  - 3-5 beta users to test and provide feedback
  - Written testimonials or video demos
  - GitHub stars from credible accounts
- [ ] Estimated effort: 2-3 weeks (recruiting, testing, collecting feedback)

**LOW PRIORITY (Post-Launch):**

**12. Advanced Documentation**
- [ ] Architecture deep-dive
- [ ] Performance tuning guide
- [ ] LLM integration best practices
- [ ] Graph design patterns
- [ ] Estimated effort: 1-2 weeks

**13. Community Infrastructure**
- [ ] Discord server for support
- [ ] GitHub Discussions enabled
- [ ] Office hours / demo sessions
- [ ] Estimated effort: Ongoing

### Known Issues to Address

**From git status analysis:**

**1. Uncommitted Changes**
- Modified: .claude/commands/know/build.md
- Modified: .claude/settings.local.json
- Modified: .claude/skills/know-tool/SKILL.md
- Modified: know/know.py
- Modified: know/src/dependencies.py
- Modified: Multiple template files
- **Action**: Review and commit or revert before launch

**2. Untracked Files**
- New: .ai/ directory with tx/ system
- New: .claude/agents/
- New: openspec/ directory
- New: Multiple know command files
- **Action**: Decide what's part of v0.0.1 launch vs future features

**3. Feature Status Ambiguity**
- Phase I features marked "in-progress" (auth, database) but core CLI is complete
- **Action**: Clarify if these are example features or actual project features

### Pre-Launch Checklist

**Week 1: Critical Path**
- [ ] Day 1-2: Publish npm package, verify installation
- [ ] Day 3: Write installation documentation
- [ ] Day 4-5: Create "Getting Started" tutorial

**Week 2: High Priority**
- [ ] Day 1-2: Create example projects (CLI tool, web app)
- [ ] Day 3-4: Record demo videos
- [ ] Day 5: Polish GitHub repository

**Week 3: Community Prep**
- [ ] Recruit 3-5 beta testers
- [ ] Draft launch announcements
- [ ] Identify target Reddit communities
- [ ] Build reputation in communities

**Week 4: Launch**
- [ ] Collect testimonials from beta testers
- [ ] Finalize documentation
- [ ] Announce on Reddit, HN, Twitter
- [ ] Monitor and respond to feedback

---

## Positioning Strategy

### Target Communities for Launch

**Primary Targets (Immediate Fit):**

1. **r/ClaudeAI** (AI coding assistant users)
   - Hook: "I built a knowledge graph system that makes Claude 10x better at planning"
   - Angle: Show before/after planning quality
   - Demo: Claude Code skill integration

2. **r/ChatGPT** (AI enthusiasts)
   - Hook: "Stop feeding your entire codebase to ChatGPT—use graphs instead"
   - Angle: Token cost savings, better results
   - Demo: Compare token usage with/without know-cli

3. **r/MachineLearning** (AI researchers/practitioners)
   - Hook: "Structured knowledge graphs eliminate LLM hallucinations in code planning"
   - Angle: Technical rigor, graph theory + LLMs
   - Demo: Validation prevents AI errors

**Secondary Targets (Broader Reach):**

4. **Hacker News** (developer tools enthusiasts)
   - Hook: "Show HN: Know-CLI – Graph-based specs that don't lie to LLMs"
   - Angle: Novel approach to old problem
   - Demo: Performance benchmarks, real-world usage

5. **r/programming** (general developers)
   - Hook: "Tired of spec files that drift? Try graphs."
   - Angle: Practical developer productivity
   - Demo: Workflow integration

6. **r/developersIndia** / **r/ExperiencedDevs** (professional developers)
   - Hook: "How I replaced brittle spec.md files with queryable graphs"
   - Angle: War story, lessons learned
   - Demo: json-graph-learning.md insights

**Niche Targets (High Relevance):**

7. **r/DevTools** / **r/CLI** (tool enthusiasts)
   - Hook: Direct showcase of capabilities
   - Angle: Ergonomics, performance, design
   - Demo: Command walkthroughs

### Key Messaging

**Primary Value Proposition:**
"Know-CLI gives AI coding assistants a structured understanding of your project, so they make better plans and fewer mistakes."

**Supporting Points:**
- 10-20x faster than traditional spec parsing
- Dual graphs map both product intent and code structure
- Built-in validation prevents architectural drift
- Designed for AI-first development workflows

**Proof Points:**
- Self-hosting (tool manages its own spec graphs)
- Performance benchmarks
- Real usage testimonial from author
- Open source, MIT licensed

### Pre-Launch Reputation Building

**Week 1-2: Soft Engagement**
- Comment helpfully on AI coding assistant threads
- Share insights from json-graph-learning.md when relevant
- Build credibility in target communities

**Week 2-3: Teaser Content**
- "I've been experimenting with graph-based specs for AI agents..."
- Share small wins, screenshots, interesting findings
- Gauge interest without launching

**Week 3-4: Beta Testing**
- Recruit interested community members
- Collect feedback and testimonials
- Refine based on real usage

**Launch: High-Quality Announcement**
- Polished README
- Working demos
- Video walkthrough
- Beta user testimonials
- Clear value proposition

---

## Risk Assessment

### Technical Risks: LOW

- Core functionality is stable and tested
- Performance is proven
- No major refactoring needed
- Python dependencies are mature and stable

### Adoption Risks: MEDIUM

**Challenges:**
1. **Niche Audience**: Targets developers using AI assistants (subset of developers)
2. **Learning Curve**: Graph concepts + CLI ergonomics
3. **Network Effects**: Value increases with community contributions (examples, patterns)

**Mitigation:**
- Focus marketing on AI coding assistant communities
- Invest in excellent getting started docs
- Create high-quality examples to bootstrap ecosystem

### Ecosystem Risks: MEDIUM

**Challenges:**
1. **No Community Yet**: Solo developer, no contributors
2. **Dependency on AI Tools**: Value tied to AI coding assistant adoption (growing market)
3. **Competition**: Other approaches to spec management may emerge

**Mitigation:**
- Time to market advantage (ship now while novel)
- Focus on integration with popular AI tools (Claude Code, Cursor)
- Build community early through excellent docs and support

### Reputational Risks: LOW

- MIT licensed, transparent
- No controversial dependencies
- Solves real problem author experienced firsthand
- "Pure alpha" messaging sets expectations

---

## Strategic Recommendations

### For Reddit-Sleuth Session

**Primary Goal**: Identify high-engagement communities for reputation building

**Recommended Search Targets:**

1. **AI Coding Assistant Keywords**:
   - "Claude Code", "Cursor AI", "GitHub Copilot workflow"
   - "LLM for programming", "AI pair programming"
   - "ChatGPT code generation problems"

2. **Spec Management Keywords**:
   - "spec file maintenance", "documentation drift"
   - "keeping specs updated", "living documentation"
   - "product requirements management"

3. **Developer Tooling Keywords**:
   - "CLI tools", "developer productivity"
   - "graph databases", "knowledge graphs for code"

**Engagement Strategy:**

**Phase 1 (Weeks 1-2): Build Credibility**
- Find threads about AI coding assistant limitations
- Comment with helpful insights (don't mention know-cli yet)
- Share learnings from json-graph-learning.md
- Establish expertise in AI-assisted development

**Phase 2 (Week 3): Soft Launch**
- "I built a tool that solves this..." comments
- Link to GitHub (not npm yet if not ready)
- Invite beta testers from engaged respondents

**Phase 3 (Week 4): Official Launch**
- Dedicated announcement posts in high-karma communities
- Video demos ready
- Testimonials from beta testers
- Clear installation path (npm)

### Launch Timeline Recommendation

**Conservative (8 weeks total):**
- Weeks 1-2: Fix critical gaps (npm, docs, examples)
- Weeks 3-4: Beta testing with 5-10 users
- Weeks 5-6: Reputation building in communities
- Weeks 7-8: Polished launch with proof points

**Aggressive (4 weeks total):**
- Week 1: Critical fixes (npm, installation docs)
- Week 2: Minimal examples + getting started
- Week 3: Recruit beta testers, build reputation
- Week 4: Launch with "alpha" disclaimer, iterate fast

**Recommended**: Conservative approach
- Higher quality launch
- Community validation
- Lower risk of negative first impressions

---

## Conclusion

Know-CLI is a **functionally complete, technically sound tool** addressing a real pain point in AI-assisted development. The core implementation is ready for public use. Success depends on:

1. **Removing adoption barriers**: npm package, installation docs, getting started guide
2. **Building credibility**: Examples, demos, beta testimonials
3. **Finding the right audience**: AI coding assistant users who value automation
4. **Timing the launch**: Build reputation before announcing

**Biggest Risk**: Launching to silence (no audience, no distribution)
**Biggest Opportunity**: First-mover advantage in graph-based specs for AI agents

**Recommendation**: Execute conservative 8-week launch plan with focus on community building before announcement.

---

## Appendix: Key Metrics

**Codebase:**
- 13 Python modules (5,500+ lines of core code)
- 8 test modules
- 40+ CLI commands
- 2 graph types (spec, code)
- 10-20x performance improvement over bash

**Current Graphs:**
- Spec graph: 16 entities, 15 dependencies
- Code graph: 25 entities, 43 dependencies, 19 references

**Dependencies:**
- 6 runtime dependencies (click, pydantic, networkx, aiofiles, python-dotenv, rich)
- 5 dev dependencies (pytest, pytest-asyncio, pytest-cov, black, mypy)

**Repository:**
- GitHub: github.com/eighteyes/know-cli
- License: MIT
- Version: 0.0.1
- Python: 3.8+
- Node: 14+ (for npm packaging)

**Author:**
- Sean Canton (eighteyes)
- Solo developer
- Real user of the tool (self-hosting)
