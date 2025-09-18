# Complete Chain Builder

A comprehensive tool for creating complete implementation chains in the knowledge graph, ensuring every user objective has a fully implemented path through the system.

## Overview

The Chain Builder guides you through creating complete implementation paths following the dependency structure:

```
User → Objectives → Features → Actions → Components (Behavior + Data Model + UI)
```

## Usage

### Interactive Chain Building

Start the interactive chain builder:

```bash
know chain-builder
# or
know gap-qa
```

### Menu Options

1. **Create new complete chain** - Guided workflow through all 5 steps
2. **Extend existing user's chain** - Add objectives/features to existing users
3. **Fill gaps in existing chains** - Identify and fill missing pieces
4. **View all chains status** - See completeness scores for all entities
5. **Generate gap report** - Comprehensive gap analysis report

## Chain Creation Process

### Step 1: Define User Type
- Create or select a user role (e.g., admin, operator, customer)
- Provide a description of their responsibilities

### Step 2: Define Objectives
- Add 2-3 high-level goals the user wants to achieve
- These represent the "WHAT" - business objectives

### Step 3: Define Features
- For each objective, define features that enable it
- Features are major system capabilities

### Step 4: Define Actions
- For each feature, specify user actions
- Use verb-noun format (e.g., create-report, view-dashboard)

### Step 5: Define Components
- For each action, create implementing components
- Each component needs:
  - **Behavior**: Business logic (required)
  - **Data Model**: Data structure (required)
  - **UI Template**: Presentation layer (optional)

## Example Chain

```
user:report-manager
  └─ objective:generate-reports
      └─ feature:reporting-dashboard
          └─ action:create-report
              └─ component:report-generator
                  ├─ behavior:validate-and-generate
                  ├─ data_models:report-schema
                  └─ ui_templates:report-form
```

## Gap Analysis

After creating chains, analyze completeness:

```bash
# Analyze specific user
know gap-analyze user:report-manager

# Analyze all entities
know gap-analyze-all

# Get completeness score
know gap-score user:report-manager

# Generate comprehensive report
know gap-report markdown
```

## Validation

The chain builder automatically:
- Links entities with proper dependencies
- Validates against dependency rules
- Calculates completeness scores
- Identifies missing pieces

## Complete Chain Criteria

A chain is considered complete when:
- User has objectives
- Objectives have features
- Features have actions
- Actions have components
- Components have both behavior AND data model

## Best Practices

1. **Start with Users**: Always begin by defining who uses the system
2. **Think High-Level**: Objectives should be business goals, not technical tasks
3. **Be Specific**: Use clear, descriptive names for all entities
4. **Complete Components**: Always add both behavior and data model
5. **Validate Often**: Run gap analysis to check completeness

## Integration

Once chains are complete, generate specifications:

```bash
# Generate feature spec
know feature reporting-dashboard

# Generate component spec
know component report-generator

# Create implementation package
know package report-generator
```

## Troubleshooting

- **Incomplete chains**: Run `know gap-analyze <entity>` to see what's missing
- **Circular dependencies**: Use `know validate-deps` to check dependency rules
- **Low scores**: Components need both behavior and data model for 100% score

## Tips

- Use the chain builder iteratively - you don't need to complete everything at once
- Start with critical user paths first
- Use existing entities when possible (the tool will detect and reuse them)
- Add UI templates only when needed for user-facing components