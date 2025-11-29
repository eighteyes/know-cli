# KNOW CLI - v 0.0.1
An opinionated graph knowledgebase for product driven software development. 

Intended primarily for automated access.

## Why? 
spec.md is a brittle approach to defining projects for LLM understanding. For months, I've used, built and rebuilt approaches to making spec files and I'm never truly happy with the results. They are brittle, prone to hallucination, resistant to change, and never internally consistent. Despite how "production-ready" and "Perfect!" they are. 

Introducing **SPEC GRAPHS**

## Spec Graphs solve for brittle specs. 
Every piece of information lives in one place, and is referenced by others. Functionally, this approach uses a simple graph with a single relationship type "depends_on" to map the connection between a User, their Objectives, into how they Act on software Components. 

These components serve as the link to a second graph in the same vein, one which describes the software architecture and how components link together. In this way, we can map from a user objective and determine all the software pieces involved in making that happen. It's an exciting vision.

Especially when you add AI, reinforced with tooling, to help you make these graphs. 

## Pure Alpha
This is a work in progress. There are two primary intents with `know`:
1) Provide a surface area for LLMs to understand the product and codebase without conducting token-wasting, repetitive manual analysis. 
2) Output current spec files for "traditional" spec-driven development.
 
Generally speaking, this is not designed for human use, as the ergonomics are somewhere between `tar` and `aws-cli`. That being said, a skill is provided for use `.claude/skills/know-tool/marketplace.json`, give it a spin.

## Results
I get considerably better plans made with `know` then with  other tools used by generalist agents. Instead of assuming my intent, the plans intuit where I want to go. I spend less time guiding the agent when it has a prepared knowledgebase that understands both the codebase and how it connects to features. [

## Installation

```bash
npm install -g know-cli
```

## Usage
`know` is ideally used via an LLM, examine [tx](https://github.com/eighteyes/tx) for an immediately useful implementation.

## Dual Graph System

Know supports two types of graphs with separate validation rules:

1. **Spec Graph** (`.ai/spec-graph.json`): Maps user intent to features
   - Entity types: user, objective, feature, component, action, operation, etc.
   - Rules: `config/dependency-rules.json`

2. **Code Graph** (`.ai/code-graph.json`): Maps codebase architecture
   - Entity types: module, package, class, function, layer, interface, etc.
   - Rules: `config/code-dependency-rules.json`

**Auto-detection**: The CLI automatically selects the correct rules based on graph filename:
```bash
# Spec graph - auto-uses dependency-rules.json
know -g .ai/spec-graph.json add user developer '{"name":"Developer","description":"..."}'

# Code graph - auto-uses code-dependency-rules.json
know -g .ai/code-graph.json add module auth '{"name":"Auth Module","description":"..."}'
```

**Manual override**: Use `-r` to specify custom rules:
```bash
know -g custom-graph.json -r my-rules.json add entity-type key '{"name":"...","description":"..."}'
```

## Commands Reference

**Note**: Most commands accept `-g/--graph-path` to specify which graph to operate on. The `-r/--rules-path` flag is optional as rules are auto-detected from the graph filename.

### Core Graph Operations

```bash
# List all entities in the graph
know list

# List entities of a specific type
know list-type <entity_type>

# Get details of a specific entity
know get <entity_id>

# Add a new entity (entity_type and entity_key are separate arguments)
know add <entity_type> <entity_key> '{"name":"Name","description":"Description"}'

# Example: Add a code module
know -g .ai/code-graph.json add module auth-handler '{"name":"Auth Handler","description":"Handles authentication"}'

# Example: Add a spec feature
know -g .ai/spec-graph.json add feature user-login '{"name":"User Login","description":"User authentication flow"}'

# Show graph statistics
know stats

# Generate sitemap of all interfaces
know sitemap
```

### Dependency Management

```bash
# Show what an entity uses (its dependencies)
know uses <entity_id>
know down <entity_id>  # Alias for 'uses'

# Show what uses an entity (its dependents)
know used-by <entity_id>
know up <entity_id>  # Alias for 'used-by'

# Add a dependency between entities
know link <from_entity> <to_entity>

# Remove a dependency between entities
know unlink <from_entity> <to_entity>

# Suggest valid connections for an entity
know suggest <entity_id>

# Show topological build order
know build-order

# Trace entity across product-code boundary
know -g .ai/spec-graph.json trace component:cli-commands -c .ai/code-graph.json
know -g .ai/code-graph.json trace module:auth-handler -s .ai/spec-graph.json
```

### Analysis & Validation

```bash
# Validate graph structure and dependencies
know validate

# Comprehensive graph health check
know health

# Detect circular dependencies
know cycles

# Check completeness score for an entity
know completeness <entity_id>
```

### Gap Analysis

```bash
# Analyze implementation gaps in dependency chains
know gap-analysis [entity_id] [--json]

# List missing connections in dependency chains
know gap-missing

# Show implementation summary
know gap-summary
```

### Reference Management

```bash
# Find orphaned references
know ref-orphans

# Show reference usage statistics
know ref-usage

# Suggest connections for orphaned references
know ref-suggest

# Clean up unused references
know ref-clean [--remove] [--dry-run]
```

### Dependency Rules

```bash
# Describe entity, reference, or meta type
know rules describe [type_name]

# Show what entity types can come after this type
know rules after <entity_type>

# Show what entity types can come before this type
know rules before <entity_type>

# Visualize the high-level dependency graph structure
know rules graph
```

### Specification Generation

```bash
# Generate specification for an entity
know spec <entity_id>

# Generate detailed feature specification
know feature-spec <feature_id>
```

### User-Friendly Workflow

Know provides a workflow system for managing features with linked documentation and graph integration.

```bash
# Initialize know workflow in a project (one-time setup)
know init

# This creates:
# - .claude/commands/know/ with slash commands
# - .ai/know/ directory structure
# - .ai/know/project.md template
```

Once initialized, use these Claude slash commands:

```bash
# Start a new feature
/know-add <feature-name>
# Creates .ai/know/<feature-name>/{proposal,todo,plan,spec}.md
# Adds stub graph entries immediately

# List all features (planned, in-progress, completed)
/know-list

# Complete and archive a feature
/know-done <feature-name>
# Moves feature to .ai/know/archive/
```

**Workflow Example:**

```bash
# 1. Initialize (one time)
know init

# 2. Start a feature
/know-add user-authentication

# 3. Fill out overview, todo, and plan files

# 4. Generate specs for each component
know spec feature:login-form >> .ai/know/user-authentication/spec.md
know spec component:auth-button >> .ai/know/user-authentication/spec.md
know spec action:submit-credentials >> .ai/know/user-authentication/spec.md

# 5. Complete the feature
/know-done user-authentication
```

**File Structure:**

```
.ai/know/
├── project.md                    # Project context
├── user-auth/                    # Active feature
│   ├── overview.md              # User request + requirements
│   ├── todo.md                  # Checklist → [links to plan]
│   ├── plan.md                  # Implementation → [links to spec]
│   └── spec.md                  # Generated via know spec
└── archive/                     # Completed features
    └── initial-setup/
```

### LLM Workflows

```bash
# List available LLM providers
know llm-providers

# List available LLM workflows
know llm-workflows

# List available workflow chains
know llm-chains

# Show detailed information about a workflow
know llm-info <workflow_name>

# Test LLM provider connection
know llm-test <provider> <prompt>

# Run an LLM workflow with JSON inputs
know llm-run <workflow_name> <json_inputs>

# Run an LLM workflow chain
know llm-chain <chain_name>
```

## Graph Structure

### Product Specification Graph (spec-graph.json)
Maps user intent to implementation with a unidirectional dependency model.

**HOW (Implementation):**
```
Project → Requirement → Interface → Feature → Action → Component → Operation
```

**WHAT (User Journey):**
```
Project → User → Objective → Action
```

**Integration Points:**
```
User → [Requirement]
Objective → [Action, Feature]
Action → [Component]
```

Every entity MUST have a reference or another entity as dependent. References are terminal nodes that can be depended upon by any entity type.

### Code Architecture Graph (code-graph.json)
Maps actual codebase structure and dependencies.

**Entity Dependencies:**
```
module → [module, package, external-dep]
package → [package, module, external-dep]
layer → [layer]
namespace → [namespace, module, package]
interface → [module, type-def]
class → [class, interface, module]
function → [function, module, class]
```

Code entities represent implementation structure, linking to product components via references.

## Dependency Rules

Refer to configuration files for complete rules:
- **`config/dependency-rules.json`** - Product specification graph rules
- **`config/code-dependency-rules.json`** - Code architecture graph rules

Each file defines:
- Allowed dependencies between entity types
- Reference types and their descriptions
- Entity type descriptions
- Schema definitions and examples

## Claude Code Skill

A Claude Code skill is available at `.claude/skills/know-tool/marketplace.json` for AI-assisted graph management. 
