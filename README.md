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

## Installation

```bash
npm install
```

The `postinstall` script will automatically install Python dependencies from `know/requirements.txt`.

## Commands Reference

### Core Graph Operations

```bash
# List all entities in the graph
./know/know list

# List entities of a specific type
./know/know list-type <entity_type>

# Get details of a specific entity
./know/know get <entity_id>

# Add a new entity
./know/know add <entity_id> --name "Name" --description "Description"

# Show graph statistics
./know/know stats

# Generate sitemap of all interfaces
./know/know sitemap
```

### Dependency Management

```bash
# Show dependencies for an entity
./know/know deps <entity_id>

# Show what depends on an entity
./know/know dependents <entity_id>

# Add a dependency between entities
./know/know add-dep <from_entity> <to_entity>

# Remove a dependency between entities
./know/know remove-dep <from_entity> <to_entity>

# Suggest valid connections for an entity
./know/know suggest <entity_id>

# Show topological build order
./know/know build-order
```

### Analysis & Validation

```bash
# Validate graph structure and dependencies
./know/know validate

# Comprehensive graph health check
./know/know health

# Detect circular dependencies
./know/know cycles

# Check completeness score for an entity
./know/know completeness <entity_id>
```

### Gap Analysis

```bash
# Analyze implementation gaps in dependency chains
./know/know gap-analysis [entity_id] [--json]

# List missing connections in dependency chains
./know/know gap-missing

# Show implementation summary
./know/know gap-summary
```

### Reference Management

```bash
# Find orphaned references
./know/know ref-orphans

# Show reference usage statistics
./know/know ref-usage

# Suggest connections for orphaned references
./know/know ref-suggest

# Clean up unused references
./know/know ref-clean [--remove] [--dry-run]
```

### Dependency Rules

```bash
# Describe entity, reference, or meta type
./know/know rules describe [type_name]

# Show what entity types can come after this type
./know/know rules after <entity_type>

# Show what entity types can come before this type
./know/know rules before <entity_type>

# Visualize the high-level dependency graph structure
./know/know rules graph
```

### Specification Generation

```bash
# Generate specification for an entity
./know/know spec <entity_id>

# Generate detailed feature specification
./know/know feature-spec <feature_id>
```

### LLM Workflows

```bash
# List available LLM providers
./know/know llm-providers

# List available LLM workflows
./know/know llm-workflows

# List available workflow chains
./know/know llm-chains

# Show detailed information about a workflow
./know/know llm-info <workflow_name>

# Test LLM provider connection
./know/know llm-test <provider> <prompt>

# Run an LLM workflow with JSON inputs
./know/know llm-run <workflow_name> <json_inputs>

# Run an LLM workflow chain
./know/know llm-chain <chain_name>
```

## Graph Structure

The spec graph uses a unidirectional dependency model with the following hierarchy:

**How (Implementation):**
```
Project → Requirements → Interface → Feature → Component → (Behaviors + Presentation + Data Models + Assets)
```

**What (User Journey):**
```
Project → User → Objectives → Actions
```

**Integration:**
```
User → Requirements
Objectives → Features
Actions → Behaviors
```

Every entity MUST have a reference or another entity as dependent. References are terminal nodes that can be depended upon by any entity type.

## Dependency Rules

Refer to `./know/config/dependency-rules.json` for:
- Allowed dependencies between entity types
- Reference types and their descriptions
- Entity type descriptions
- Meta schema definitions

## Claude Code Skill

A Claude Code skill is available at `.claude/skills/know-tool/marketplace.json` for AI-assisted graph management. 
