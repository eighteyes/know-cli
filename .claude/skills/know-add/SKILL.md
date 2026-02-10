---
name: know-add
description: Add entities to the specification graph. Use when adding new entities (features, actions, components, etc.) to spec-graph.json. Handles type validation, dependency rules, and graph validation automatically.
user_invocable: true
arguments: "<entity_type> <entity_key> [description]"
---

# Know Add - Add Entity to Specification Graph

You are adding a new entity to the specification graph using the `know` CLI tool.

## Parse Arguments

The user invokes this skill as: `/know-add <entity_type> <entity_key> [description]`

- `entity_type` - One of: project, requirement, interface, feature, action, component, operation, user, objective
- `entity_key` - kebab-case key (e.g., `analytics-dashboard`, `export-data`)
- `description` - Optional freeform description text

If arguments are missing, ask the user what entity they want to add.

## Workflow

### Step 1: Validate the entity type

Run: `./know/know rules describe <entity_type>`

If the type is invalid, show the user valid entity types and ask them to pick one.

### Step 2: Check dependency rules

Run these in parallel:
- `./know/know rules after <entity_type>` - what this type can depend on
- `./know/know rules before <entity_type>` - what can depend on this type

Show the user where this entity fits in the graph.

### Step 3: Build entity data

Construct a JSON object with exactly two fields:
- `name` - Title case display name derived from the key or description
- `description` - Clear, concise description of the entity

If the user provided a description argument, use it. Otherwise, ask.

### Step 4: Add the entity

Run: `./know/know add <entity_type> <entity_key> '<json_data>'`

### Step 5: Validate the graph

Run: `npm run validate-graph`

If validation fails, diagnose and fix.

### Step 6: Suggest next steps

Based on the dependency rules from Step 2, suggest:
- What dependencies to add (e.g., "This feature can depend on actions. Add a dependency?")
- What parent entities might depend on this new entity
- Run `./know/know suggest <entity_type>:<entity_key>` to show valid connections

## Key Rules

- Entity keys MUST be kebab-case (use `-` not `_`)
- Entity data MUST only contain `name` and `description` fields
- Always validate after adding
- Node keys are granular items, not collections (DO: `status-map`, DON'T: `display-patterns`)
- Avoid reusing parent type in the key (DO: `camera-feed`, DON'T: `settings-interface`)

## Dependency Chain Reference

```
HOW: project -> requirement -> interface -> feature -> action -> component -> operation
WHAT: project -> user -> objective -> action
Integration: user -> [requirement], objective -> [action, feature], action -> [component]
```
