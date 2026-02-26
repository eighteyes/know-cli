# Know CLI Command Reference

## Quick Reference

### Essential Commands

```bash
# Query
know list --type feature                  # List all features
know get feature:auth                     # Get entity details
know graph uses feature:auth              # What does this use?
know graph used-by component:login        # What uses this?

# Build & Execute
know build auth                           # 🆕 Generate spec + execute tasks

# Modify
know add entity feature auth '{"name":"..."}'
know graph link feature:auth component:login
know meta set project name '{"value":"My Project"}'

# Validate
know check validate                       # Validate graph structure
know check health                         # Comprehensive health check
know check gap-summary                    # Show implementation gaps

# Generate
know gen spec feature:auth --format xml   # Generate XML task spec
know gen feature-spec feature:auth        # Generate markdown spec
know gen codemap know/src                 # Generate code structure map
know gen code-graph                       # 🆕 Generate code-graph from AST
```

---

## Command Groups

### 📊 Core Operations

#### `know add`
Add entities or references to the graph.

```bash
# Add entity
know add entity feature auth '{"name":"Authentication","description":"User login/logout"}'
know add entity component login '{"name":"Login Component"}'
know add entity operation hash-password '{"name":"Hash Password"}'

# Add reference
know add reference data-model user '{"fields":[{"name":"email","type":"string"}]}'
know add reference external-dep bcrypt '{"version":">=5.0","purpose":"Password hashing"}'

# Add meta
know add meta project name '{"value":"My Project"}'
know add meta decision auth-method '{"title":"JWT vs Sessions","rationale":"..."}'
```

#### `know get`
Get detailed information about an entity or reference.

```bash
know get feature:auth
know get component:login
know get data-model:user
```

#### `know list`
List entities or references, optionally filtered by type.

```bash
know list                           # List all entities
know list --type feature            # List only features
know list --type component          # List only components
know list --refs                    # List references
know list --refs --type data-model  # List data models
```

#### `know build` 🆕
Execute tasks for a feature from generated XML spec.

```bash
# Execute feature tasks
know build auth

# Resume from checkpoint
know build auth --resume

# Auto-execute non-checkpoint tasks
know build auth --auto
```

**What it does:**
1. Generates XML spec: `.ai/know/plans/auth.xml`
2. Parses into executable tasks
3. Displays task details with rich formatting
4. Stops at checkpoints for human review
5. Tracks progress: `.ai/know/build-progress.json`

---

### 🔍 Graph Operations (`know graph`)

#### Querying Dependencies

```bash
# What does this entity depend on?
know graph uses feature:auth
know graph up feature:auth          # Alias

# What depends on this entity?
know graph used-by component:login
know graph down component:login     # Alias

# Show build order (topological sort)
know graph build-order
```

#### Modifying Graph

```bash
# Add dependency link
know graph link feature:auth component:login

# Remove dependency link
know graph unlink feature:auth component:old-login

# Suggest valid connections
know graph connect component:login
```

#### Analysis

```bash
# Compare two graphs
know graph diff .ai/know/spec-graph.json .ai/spec-graph-old.json
```

---

### ✅ Validation (`know check`)

#### Basic Validation

```bash
# Validate graph structure
know check validate

# Show statistics
know check stats

# Comprehensive health check
know check health
```

#### Gap Analysis

```bash
# Show implementation gaps
know check gap-summary

# Show missing connections
know check gap-missing

# Detailed gap analysis
know check gap-analysis
```

#### Advanced Checks

```bash
# Find circular dependencies
know check cycles

# Find orphaned references
know check orphans

# Show reference usage
know check usage

# Check completeness score
know check completeness feature:auth

# Clean unused references
know check clean
```

---

### 📝 Generation (`know gen`)

#### Specifications

```bash
# Generate entity spec (markdown)
know gen spec feature:auth
know gen spec component:login

# Generate XML task spec 🆕
know gen spec feature:auth --format xml
know gen spec feature:auth --format json

# Generate detailed feature spec
know gen feature-spec feature:auth
know gen feature-spec feature:auth --format xml  # 🆕
```

#### Code Analysis

```bash
# Generate code structure map (AST parsing)
know gen codemap know/src
know gen codemap know/src --heat              # With git heat scores
know gen codemap www_v2/src --lang typescript

# Generate code-graph from codemap 🆕
know gen code-graph
know gen code-graph -c .ai/codemap.json -o .ai/know/code-graph.json
```

**Code-graph generation:**
- Parses codemap AST → generates modules/classes/functions
- Adds file paths to all entities
- **Preserves** product-component references (manual curation)
- **Merges** detected imports with existing external deps

#### Other Generators

```bash
# Generate sitemap of interfaces
know gen sitemap

# Trace entity across graphs
know gen trace feature:auth

# Show traceability matrix
know gen trace-matrix --type feature
```

#### Rules Queries

```bash
# Describe entity type
know gen rules describe feature

# What can depend on this type?
know gen rules before component

# What can this type depend on?
know gen rules after feature

# Visualize dependency structure
know gen rules graph
```

---

### 🎯 Feature Management (`know feature`)

#### Lifecycle

```bash
# Complete a feature
know feature done auth

# Tag commits
know feature tag auth
```

#### Requirements

```bash
# Mark requirement complete
know feature complete auth auth-req-1

# Block requirement
know feature block auth auth-req-2 --reason "Waiting on API"
```

#### Contracts & Coverage

```bash
# Show contract info
know feature contract auth

# Validate contracts
know feature validate-contracts

# Show test coverage
know feature coverage auth
```

#### Impact Analysis

```bash
# Show what features depend on an entity
know feature impact component:login

# Show what features are affected by file changes
know feature impact --file src/auth.py
```

---

### 📋 Requirements (`know req`)

```bash
# List requirements for a feature
know req list auth

# Add requirement
know req add auth auth-login "User can login with email/password"

# Update requirement status
know req update auth auth-login --status in-progress
```

---

### 📅 Phases (`know phases`)

```bash
# Show all phase assignments
know phases

# Show assignments for a feature
know phases feature:auth

# Move feature to phase
know phases assign feature:auth II
```

---

### 🚫 Deprecation

```bash
# Mark entity as deprecated
know deprecate component:old-login --reason "Use new-login instead"

# List deprecated entities
know deprecated

# Remove deprecation
know undeprecate component:old-login
```

---

### ⚙️ Meta Management (`know meta`)

```bash
# Get meta value
know meta get project name

# Set meta value
know meta set project name '{"value":"My Project"}'

# List meta keys
know meta list
```

---

### 🔧 Operations (`know op`)

Op-level progress tracking for features.

```bash
# Show ops for a feature
know op list auth

# Mark operation complete
know op complete auth hash-password
```

---

## Common Workflows

### 1. Starting a New Feature

```bash
# 1. Add feature entity
know add entity feature auth '{"name":"Authentication","description":"User auth system"}'

# 2. Add dependencies
know graph link feature:auth action:login
know graph link feature:auth component:auth-service

# 3. Validate
know check validate
```

### 2. Building a Feature

```bash
# 1. Generate and execute tasks
know build auth

# 2. Review task at checkpoint
# (implement the task)

# 3. Resume
know build auth --resume
```

### 3. Maintaining Code-Graph

```bash
# 1. Update codebase → regenerate codemap
know gen codemap know/src --heat

# 2. Regenerate code-graph (preserves references!)
know gen code-graph

# 3. Verify
know check validate -g .ai/know/code-graph.json
```

### 4. Analyzing Dependencies

```bash
# What does this feature need?
know graph uses feature:auth

# What uses this component?
know graph used-by component:login

# Show full dependency chain
know gen trace feature:auth
```

### 5. Finding Gaps

```bash
# Show implementation gaps
know check gap-summary

# Show missing connections
know check gap-missing

# Get suggestions
know graph connect component:orphaned-comp
```

---

## Graph Types

### Spec Graph (`.ai/know/spec-graph.json`)
**Product intent and requirements**

Entities: user, objective, feature, action, component, operation, requirement, interface, project

```bash
know -g .ai/know/spec-graph.json list --type feature
know -g .ai/know/spec-graph.json add entity feature auth '{...}'
```

### Code Graph (`.ai/know/code-graph.json`)
**Actual codebase structure**

Entities: module, package, class, function, layer, interface, namespace

```bash
know -g .ai/know/code-graph.json list --type module
know gen code-graph  # Regenerate from codemap
```

---

## Output Formats

### XML Spec Generation 🆕

```bash
# Generate GSD-style executable task spec
know gen spec feature:auth --format xml

# Save to file
know gen spec feature:auth --format xml > .ai/know/plans/auth.xml
```

**XML Structure:**
- `<meta>` - Feature metadata
- `<context>` - Users, objectives, actions, components
- `<dependencies>` - Code modules, interfaces, external deps
- `<tasks>` - Executable operations with checkpoints

### JSON Format

```bash
# JSON output
know gen spec feature:auth --format json
know list --type feature --format json  # (if supported)
```

---

## Tips

1. **Auto-detection**: `-g` flag auto-selects dependency rules based on filename
   - `spec-graph.json` → uses `dependency-rules.json`
   - `code-graph.json` → uses `code-dependency-rules.json`

2. **References are preserved**: Running `know gen code-graph` preserves your manual `product-component` and `external-dep` curation

3. **Build is feature-level**: `know build auth` generates spec and executes in one command

4. **Progress is tracked**: Build progress saved to `.ai/know/build-progress.json`

5. **Checkpoints control flow**: Tasks with `checkpoint:*` types pause for human review

---

## New in This Session 🆕

- **`know gen code-graph`** - Generate code-graph from AST with reference preservation
- **`know build <feature>`** - Feature-level task execution with checkpoints
- **XML spec format** - `--format xml` for executable task specifications
- **Organized artifacts** - All runtime data in `.ai/know/`
