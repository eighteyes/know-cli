---
name: Know: Add Feature
description: 5-step workflow to add a feature to spec-graph with HITL clarification
category: Know
tags: [know, feature, overview]
---

**Prerequisites**
- Activate the know-tool skill for graph operations

**Workflow**

## 1. Identify
- Extract feature name from conversation or prompt user if not provided
- Verify uniqueness in `.ai/know/features/`
- Use kebab-case for feature names

## 2. Check for Duplicates (CRITICAL)

**Before adding a new feature, search for existing similar functionality:**

### Search Strategy
Use parallel searches to find potential duplicates:

```bash
# Search for similar feature names in spec-graph
know -g .ai/spec-graph.json list-type feature | grep -i "<keyword>"

# Search codebase for similar implementations
rg -i "<keyword>" --type py --type js --type ts -l

# Search for similar patterns/functions
rg "class.*<Keyword>|function.*<keyword>|def.*<keyword>" --type py --type js
```

### Examples
If adding "api-client" feature:
- Search for: "api", "client", "http", "request", "fetch"
- Check for: existing API clients, HTTP wrappers, request handlers

If adding "authentication" feature:
- Search for: "auth", "login", "session", "token", "credential"
- Check for: existing auth modules, login flows, session management

If adding "database-sync" feature:
- Search for: "sync", "database", "db", "persist", "save"
- Check for: existing sync mechanisms, database handlers

### Ask User About Duplicates

**If potential duplicates found**, use AskUserQuestion:

```
Question: "Found existing functionality that may overlap with <feature-name>:

• <duplicate-1>: <brief-description>
  Location: <file-path>

• <duplicate-2>: <brief-description>
  Location: <file-path>

How would you like to proceed?"

Options:
1. "Reuse existing implementation" - Use what's already there
   Description: Cancel new feature, document existing solution instead

2. "Generalize existing code" - Extend current implementation
   Description: Refactor existing code to support both use cases

3. "Replace existing code" - Deprecate old, implement new
   Description: Mark old implementation for removal, proceed with new feature

4. "Create separate implementation" - Both are needed
   Description: Proceed with new feature, document why both exist
```

**Based on user choice**:
- **Reuse**: Cancel add workflow, create documentation pointing to existing code
- **Generalize**: Proceed but mark in overview.md that this extends `<existing>`
- **Replace**: Proceed, add deprecation task to todo.md for old implementation
- **Create separate**: Proceed, add justification to overview.md

### If No Duplicates Found
Proceed to Clarify step.

## 3. Clarify (HITL)
Ask user essential questions using AskUserQuestion:
- What does this feature do? (1-2 sentence description)
- Which user(s) need this feature? (from spec-graph users)
- Which objective(s) does this feature support? (from spec-graph objectives)
- Any known components needed? (optional, can defer to /know:build)
- **Are there reference materials for this feature?** (research papers, RFCs, API docs, specs, blog posts, GitHub repos)

**CRITICAL: Capture reference materials**

If user provides references, collect:
- **Research Papers**: ArXiv links, DOIs, paper titles
- **Specifications**: RFCs, W3C specs, API documentation
- **Technical Docs**: Official documentation, architecture guides
- **Prior Art**: GitHub repos, blog posts, tutorials
- **Standards**: IEEE, ISO, industry standards

**Format for references**:
```
Title: <descriptive name>
Type: <research-paper|rfc|api-doc|spec|github|blog|standard>
URL: <link>
Summary: <1-2 sentence summary of relevance>
```

**Examples**:
```
Title: Attention Is All You Need (Transformer Architecture)
Type: research-paper
URL: https://arxiv.org/abs/1706.03762
Summary: Original transformer architecture paper - foundation for implementation

Title: RFC 7519 - JSON Web Tokens
Type: rfc
URL: https://datatracker.ietf.org/doc/html/rfc7519
Summary: JWT specification for token-based authentication

Title: Anthropic Claude API Documentation
Type: api-doc
URL: https://docs.anthropic.com/claude/reference
Summary: Official API reference for Claude integration
```

## 4. Scaffold
- Create directory `.ai/know/features/<feature-name>/`
- Create files from templates:
  - `overview.md` - Populated with answers from Clarify step (+ duplicate handling notes if applicable)
  - `references.md` - **Reference materials section** (research papers, docs, specs, prior art)
  - `todo.md` - Empty checklist (+ deprecation tasks if replacing existing)
  - `plan.md` - Empty implementation plan
  - `spec.md` - Empty spec file
  - `config.json` - **Feature tracking config** (watch paths, baseline)
- Replace `{feature_name}` placeholder in all templates

**Create config.json for feature tracking**:

```json
{
  "watch": {
    "paths": [],
    "exclude": []
  },
  "baseline": {}
}
```

The `config.json` bridges spec and code:
- **watch.paths**: Glob patterns for files this feature owns (added during `/know:build`)
- **watch.exclude**: Patterns to ignore
- **baseline**: Auto-populated with timestamp/commit when feature moves to in-progress

Use `know validate-feature <name>` to check if watched files changed since baseline.
Use `know tag-feature <name>` to tag commits with git notes when done.

**CRITICAL: Populate references.md**

If user provided reference materials, create `.ai/know/features/<feature-name>/references.md`:

```markdown
# References for <feature-name>

## Research Papers
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
  - Original transformer architecture paper - foundation for implementation
  - Key sections: 3.2 (Multi-head attention), 5.4 (Training details)

## Specifications
- [RFC 7519 - JSON Web Tokens](https://datatracker.ietf.org/doc/html/rfc7519)
  - JWT specification for token-based authentication
  - Sections: 4.1 (Registered claims), 7 (Security considerations)

## API Documentation
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)
  - Official API reference for Claude integration
  - Endpoints: /v1/messages, /v1/complete

## Prior Art
- [similar-project](https://github.com/user/repo)
  - Example implementation of similar feature
  - See: src/feature.py for approach

## Implementation Notes
- Key algorithms from papers implemented in: <files>
- Deviations from spec: <list any intentional differences>
- Open questions: <anything unclear from references>
```

**Also update overview.md** to include:
```markdown
## References
See [references.md](references.md) for research papers, specifications, and documentation.
```

## 5. Register
Add feature to spec-graph using answers from step 3:
- `know -g .ai/spec-graph.json add feature <name> '{"name":"...","description":"..."}'`
- `know -g .ai/spec-graph.json link objective:<name> feature:<name>` for each objective
- `know -g .ai/spec-graph.json phases add pending feature:<name>`

**CRITICAL: Add reference materials to spec-graph**

If user provided references, add them to `.ai/spec-graph.json` → `references` section:

Edit `.ai/spec-graph.json` to add a new reference type for documentation:

```json
"references": {
  "documentation": {
    "feature-name-paper": {
      "title": "Attention Is All You Need",
      "type": "research-paper",
      "url": "https://arxiv.org/abs/1706.03762",
      "summary": "Original transformer architecture paper",
      "sections": ["3.2", "5.4"],
      "feature": "feature:transformer-implementation"
    },
    "feature-name-api-docs": {
      "title": "Anthropic Claude API Documentation",
      "type": "api-doc",
      "url": "https://docs.anthropic.com/claude/reference",
      "summary": "Official API reference for Claude integration",
      "endpoints": ["/v1/messages", "/v1/complete"],
      "feature": "feature:claude-integration"
    },
    "feature-name-rfc": {
      "title": "RFC 7519 - JSON Web Tokens",
      "type": "rfc",
      "url": "https://datatracker.ietf.org/doc/html/rfc7519",
      "summary": "JWT specification",
      "sections": ["4.1", "7"],
      "feature": "feature:jwt-auth"
    }
  }
}
```

**Benefits**:
- References queryable via graph: `know -g .ai/spec-graph.json refs documentation`
- Links preserved in version control
- LLMs can query for context: "What papers is this feature based on?"
- Traceability from implementation → research

## 6. Update Feature Index
Maintain `.ai/know/features/feature-index.md` with a summary of all features:

**Steps**:
1. Read existing `feature-index.md` (create if doesn't exist)
2. Add new feature entry in alphabetical order
3. Update summary counts at top

**File structure**:
```markdown
# Feature Index

## Summary
- **Total Features**: N
- **Pending**: X
- **In Progress**: Y
- **Complete**: Z

## Features

### <feature-name>
- **Status**: pending
- **Objectives**: objective:name1, objective:name2
- **Description**: <1-2 sentence description>
- **Added**: YYYY-MM-DD
- **Directory**: `.ai/know/features/<feature-name>/`

### <another-feature>
...
```

**Note**: Keep entries alphabetically sorted for easy lookup.

## 7. Connect
- Run `/know:connect` to validate graph coverage
- Ensure new feature is reachable from root users
- If coverage < 100%, assist with connecting disconnected entities
- Guide user: "Feature added! Run `/know:build <feature-name>` to begin development"

**Example Usage**
```
User: /know:add transformer-attention
Assistant:
  1. Identify: feature name = "transformer-attention"
  2. Check Duplicates: Searches for "transformer", "attention", "neural"
     → No duplicates found
  3. Clarify: Asks user questions
     User provides:
     - Description: "Multi-head attention mechanism from Transformer paper"
     - Users: ai-assistant, developer
     - Objectives: improve-model-performance
     - References: https://arxiv.org/abs/1706.03762 (Attention Is All You Need)
  4. Scaffold: Creates .ai/know/features/transformer-attention/
     → overview.md with description
     → references.md with paper link, key sections (3.2, 5.4)
     → todo.md, plan.md, spec.md
  5. Register:
     → Adds feature to spec-graph
     → Links to objective:improve-model-performance
     → Adds documentation reference to spec-graph.json
  6. Update Feature Index:
     → Adds entry to .ai/know/features/feature-index.md
     → Updates summary counts
  7. Connect: Validates coverage, guides to /know:build
```

**Notes**
- ALWAYS check for duplicates before proceeding (step 2) - prevents wasted effort
- Search broadly: use synonyms, related terms, common patterns
- If duplicates found, stop and ask user - don't assume which path to take
- **ALWAYS ask for reference materials** (step 3) - critical for research-based features
  - Research papers (ArXiv, DOI)
  - Specifications (RFCs, W3C)
  - API documentation
  - Prior art (GitHub repos, blog posts)
- Create `references.md` file for human-readable links
- Add references to spec-graph for machine-queryable traceability
- Always ask clarifying questions before scaffolding (step 3)
- Link features to objectives immediately (avoids disconnected chains)
- Let `/know:build` handle detailed component architecture
- Use `/know:connect` to maintain graph coverage

---
`r8` - Added config.json for feature tracking (watch paths, baseline, git notes bridge)
`r7` - Added feature-index.md maintenance step
`r6` - Added reference materials tracking (research papers, specs, docs)
`r5` - Added duplicate detection step (CRITICAL for preventing redundant work)
`r4` - Consolidated to 5 steps with HITL clarification flow
`r3` - Added /know:connect step to ensure graph coverage
`r2`
