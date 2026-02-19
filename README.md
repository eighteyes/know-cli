# KNOW CLI / Spec Graphs - v 0.1.2
Opinionated LLM tooling and knowledge base for product driven software development. 

Know CLI turns conversations into context construction for AI-driven *feature development* . 

Know commands are for end users to manually utilize the Know graph.

## Why Know?
Every AI toolset for making software implicitly carries the creator's mental model for software development. This is a point of friction for experienced developers, and my recommendation is to roll your own tooling for the best results. My model is not your model, and that's ok. I made `know` to give my mental model hands to work with, and it works for me.

### The Model
My background is entirely with startups, including a stint with an incubator / venture builder studio. I've done a few 0->1s but mostly 0->0.1s, usually in a client / customer / founder facing role as the technical lead. Rapid prototyping to learn quickly is my typical objective

`know` was designed to find and capture context around what you're asking an AI to accomplish. The WHAT and WHY in addition to the HOW.

*Why pollute context with product signals?*

Just like humans, LLMs need to make decisions as they go, as the map is not the territory. Having this contextual information helps make those decisions, because the last thing we want, as AI-powered builders, is to have the thing guess wrong and we don't find out until later.

*Why not spec files?*

I started with spec files, then I hit a wall. Spec files are fine for humans, token overhead for language exists when you use these for AI. Spec files are BRITTLE, they represent your thinking and the project at a point in history, and they get bloated and are not adaptable. Necessarily, you store information in multiple places, and that information is subject to rot. What we need to defeat this are data structures which are not flat, which support branching and nesting. What we need are spec graphs.

*Spec graphs...*

Yes, single directional dependency graphs which link the WHAT with the HOW of a project. A clear link which is *generated* when needed. The human concerns, who is using it, what are they trying to accomplish, how are they doing it, are linked with the technical details needed to execute. Information lives in one place and it's trivial to reason between feature and implementation, because traversing that information space is just a query. 

With `know` feature delivery is not a checklist, it is a deterministic state of your codebase. Getting to Done still requires human review.

*... cool ... what's next?*

```
```
```
npm install -g know-cli

# cd to your project
know init - installs skill and commands 
```

## LLM Workflow
```
# main
/know:add - Add more features as you go
/know:prebuild - Ensure the specs are aligned with the graph
/know:build <feature> - Spin up some agents to knock it out
/know:review <feature> - Your checklist for validation
/know:done <feature> - Mark it as finished. 

# as needed
/know:prepare - init on an existing codebase, runs know:plan after setup
/know:plan - Kick off a new project with a phased Product discovery conversation.
/know:bug - track an issue with a feature
/know:connect - if the graph gets sparse
/know:list - whats out there to work on
/know:change <feature> - things change
/know:validate - check the graph

# skills
know-tool - teaches AI how to use Know CLI
```

### My model is not your model
Perfect! You can modify the `dependency-rules.yaml` file to change the paradigm to work for you! I would be especially interested to see if this approach could apply to domains outside of software.  

## Pure Alpha
This is a work in progress. Primary intents:
1) Provide a surface area for LLMs to understand the product and codebase without conducting token-wasting, repetitive manual analysis. 
2) Output current spec files for "traditional" spec-driven development.
3) Create a kick-ass `project.md` file.
 
Generally speaking, the cli is not intended for human use, as the ergonomics are somewhere between `tar` and `aws-cli`. That being said, a skill is provided for use `.claude/skills/know-tool/marketplace.json`, give it a spin with `know init` in your project directory.

## Results
I get considerably better plans made with `know` then with other tools used by generalist agents. Instead of assuming my intent, the plans intuit where I want to go. I spend less time guiding the agent when it has a prepared knowledgebase that understands both the codebase and how it connects to features.

Plans made with stock Claude Code sometimes miss the mark, even with Explore Agents.

## Installation

```bash
npm install -g know-cli
```

## Usage
`know` is ideally used via an LLM, examine [tx](https://github.com/eighteyes/tx) for an immediately useful implementation.

## Dual Graph System

Know supports two types of graphs with separate validation rules:

1. **Spec Graph** (`.ai/know/spec-graph.json`): Maps user intent to features
   - Entity types: user, objective, feature, component, action, operation, etc.
   - Rules: `config/dependency-rules.json`

2. **Code Graph** (`.ai/know/code-graph.json`): Maps codebase architecture
   - Entity types: module, package, class, function, layer, interface, etc.
   - Rules: `config/code-dependency-rules.json`

**Auto-detection**: The CLI automatically selects the correct rules based on graph filename:
```bash
# Spec graph - auto-uses dependency-rules.json
know -g .ai/know/spec-graph.json add entity user developer '{"name":"Developer","description":"..."}'

# Code graph - auto-uses code-dependency-rules.json
know -g .ai/know/code-graph.json add entity module auth '{"name":"Auth Module","description":"..."}'
```

**Manual override**: Use `-r` to specify custom rules:
```bash
know -g custom-graph.json -r my-rules.json add entity entity-type key '{"name":"...","description":"..."}'
```

## Commands Reference

### Adding to Graph (`know add`)

```bash
# Add entities
know add entity <type> <key> '{"name":"Name","description":"Description"}'
know -g .ai/know/code-graph.json add entity module auth-handler '{"name":"Auth Handler","description":"..."}'
know -g .ai/know/spec-graph.json add entity feature user-login '{"name":"User Login","description":"..."}'

# Add references (validated against dependency-rules.json)
know add reference <ref_type> <key> '{"field":"value"}'
know add reference documentation api-spec '{"title":"API Spec","url":"..."}'

# Add meta sections
know add meta project name '{"value":"My Project"}'
know add meta decision auth-choice '{"title":"JWT vs Sessions","rationale":"..."}'
```

### Entity Management (`know list` / `know get`)

```bash
know list                           # List all entities
know list --type feature            # List entities of a specific type
know get <entity_id>                # Get details of a specific entity
```

### Node Operations (`know nodes`)

```bash
# Deprecation
know nodes deprecate <entity_id> --reason "..." [--replacement <entity>] [--removal-date YYYY-MM-DD]
know nodes undeprecate <entity_id>
know nodes deprecated               # List all deprecated entities[]
know nodes deprecated --overdue     # List overdue for removal

# Modification
know nodes update <entity_id> '{"name":"New Name"}'  # Update properties
know nodes rename <entity_id> <new_key>              # Rename entity key
know nodes clone <entity_id> <new_key>               # Clone with all dependencies
know nodes clone <entity_id> <new_key> --no-upstream # Clone without incoming deps

# Removal
know nodes delete <entity_id>       # Remove entity and clean up dependencies
know nodes cut <entity_id>          # Remove entity only, leave deps orphaned

# Merging
know nodes merge <from> <into>      # Merge entities, transfer dependencies
know nodes merge <from> <into> --keep  # Keep source after merge
```

### Graph Operations (`know graph`)

```bash
know graph uses <entity_id>         # Show dependencies
know graph used-by <entity_id>      # Show dependents
know graph up <entity_id>           # Alias for uses
know graph down <entity_id>         # Alias for used-by
know graph link <from> <to>         # Add dependency
know graph unlink <from> <to>       # Remove dependency
know graph connect <entity_id>      # Suggest valid connections
know graph build-order              # Topological sort
know graph diff graph1.json graph2.json  # Compare graphs
```

### Checks & Validation (`know check`)

```bash
know check validate                 # Validate graph structure
know check health                   # Comprehensive health check
know check cycles                   # Detect circular dependencies
know check stats                    # Show graph statistics
know check completeness <entity_id> # Completeness score
```

### Reference & Gap Analysis (`know check link`)

```bash
know check link orphans             # Find orphaned references
know check link usage               # Reference usage statistics
know check link suggest             # Suggest connections for orphans
know check link clean [--remove]    # Clean up unused referencesb
know check link gap-analysis [entity_id]  # Analyze gaps
know check link gap-missing         # List missing connections
know check link gap-summary         # Implementation summary
```

### Generation (`know gen`)

```bash
know gen spec <entity_id>           # Generate entity specification
know gen spec <feature_id> --format xml  # Generate XML task specification (GSD format)
know gen feature-spec <feature_id>  # Generate feature specification
know gen feature-spec <feature_id> --format xml  # Generate XML task specification
know gen sitemap                    # Generate interface sitemap
know gen codemap <source_dir>       # Generate code structure map
know gen trace <entity_id>          # Trace across product-code boundary
know gen trace-matrix               # Requirement traceability matrix
know gen rules describe <type>      # Describe entity/reference type
know gen rules before <type>        # What can depend on this type
know gen rules after <type>         # What can this type depend on
know gen rules graph                # Visualize dependency structure
```

### Feature Lifecycle (`know feature`)

```bash
know feature contract <name>        # Display contract info
know feature validate-contracts     # Validate all contracts
know feature validate <name>        # Check if changes warrant re-planning
know feature tag <name>             # Tag commits with git notes
know feature done <name>            # Complete and archive feature
know feature impact <target>        # Show affected features
know feature coverage <name>        # Test coverage from feature level
```## Graph Structure

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
