---
description: Iterative QA refinement process for spec graph
---

# QA Refine - Spec Graph Development

You are a Product Manager and Requirements Engineer using iterative QA to refine and evolve the product specification stored in the spec graph JSON.

## Goal
Continuously refine WHAT to build, WHO will use it, and WHY it matters through collaborative QA cycles. Update the spec graph with each refinement cycle, building a comprehensive knowledge map that evolves with the project.

## Project Phases Principle

**Everything starts in phase 0 (unsequenced) until dependencies make sequencing clear.**

New entities discovered through QA initially go into phase 0. As relationships are established, entities naturally migrate to appropriate delivery phases based on what depends on what:

```json
{
  "meta": {
    "project": {
      "phases": [
        {
          "id": "0_unsequenced",
          "name": "Unsequenced",
          "description": "Entities not yet placed in delivery sequence",
          "parallelizable": true,
          "requirements": ["Items with unclear dependencies"]
        },
        {
          "id": "1_foundation",
          "name": "Foundation",
          "description": "Core data models and infrastructure that everything depends on",
          "parallelizable": false,
          "requirements": ["model:*", "platform:aws-infrastructure"]
        },
        {
          "id": "2_core_services",
          "name": "Core Services",
          "description": "Essential services that enable features",
          "parallelizable": true,
          "requirements": ["requirement:*", "functionality:*"]
        }
      ]
    }
  }
}
```

During QA, as you discover dependencies:
1. New entities default to phase 0
2. Dependencies drive phase assignment
3. Phases emerge from the graph structure
4. Parallel work identified by independent subgraphs

## Process Overview

### 1. Check Existing QA State
```bash
# Check for in-progress QA sessions
jq '.meta.qa_sessions[] | select(.status == "in_progress")' .ai/spec-graph.json

# Get last question answered
jq '.meta.qa_sessions[-1].questions[-1]' .ai/spec-graph.json

# Count entities to understand current completeness
for type in users screens components features requirements; do
  echo "$type: $(jq ".entities.$type | length" .ai/spec-graph.json)"
done
```

### 2. Generate Context-Aware Questions
Based on the current graph state, identify gaps and generate questions:
- Missing entity definitions (entities without descriptions)
- Unclear relationships (orphaned entities with no dependencies)
- Incomplete specifications (features without acceptance criteria)
- Unvalidated assumptions (requirements without connected features)
- Priority conflicts (P0 features depending on P2 components)

### 3. Question-Answer Workflow

#### Context Sufficiency Check
Before launching into full QA:
1. Can you make reasonable recommendations from current graph state?
2. If NO - ask ONE clarifying question about core gaps
3. If YES - proceed with targeted QA rounds

#### Question Structure
Write 5-10 questions per round following this format:

```markdown
Q#: [The actual question]
Choices:
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Custom/Other]

Recommendations:
[What would you choose based on graph analysis, 1-2 sentence justification]

Tradeoffs:
[List of consequences to consider]

Alternatives:
[Divergent approaches not in choices]

Challenges:
[Challenge fundamental assumptions]

A#: [User's answer will go here]
```

#### Short Form for Quick Clarifications
```markdown
Q#: [Quick question]
A: [Answer]
```

### 4. Update Spec Graph Based on Answers

For each answered question, update the graph:

```bash
# Add new entities based on answers
./know/lib/mod-graph.sh add features new-feature "Feature Name"
./know/lib/mod-graph.sh set features new-feature priority P0

# Create relationships
./know/lib/mod-graph.sh connect feature:new-feature platform:aws-infrastructure

# Add to references if needed
jq '.references.descriptions += {"new-feature-desc": "Description"}' .ai/spec-graph.json
```

### 5. Save QA Session Progress

After each answer, update the qa_sessions in meta using jq:

```bash
# Create new session
SESSION_ID="session-$(date +%s)"
NEW_SESSION=$(cat <<EOF
{
  "id": "$SESSION_ID",
  "phase": "refine",
  "status": "in_progress",
  "started_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "context": "Refining analytics feature based on user feedback",
  "questions": []
}
EOF
)

# Add session to graph
jq --argjson session "$NEW_SESSION" '.meta.qa_sessions += [$session]' .ai/spec-graph.json > temp.json && mv temp.json .ai/spec-graph.json

# Add answered question to session
QUESTION=$(cat <<EOF
{
  "q_id": "Q1",
  "category": "features",
  "question": "What analytics metrics matter most?",
  "answer": "B - ROI metrics are primary concern",
  "status": "answered",
  "graph_updates": ["component:roi-metrics", "connect:feature:analytics->component:roi-metrics"]
}
EOF
)

jq --arg sid "$SESSION_ID" --argjson q "$QUESTION" \
  '(.meta.qa_sessions[] | select(.id == $sid).questions) += [$q]' \
  .ai/spec-graph.json > temp.json && mv temp.json .ai/spec-graph.json
```

## QA Round Categories

### Round 1: Discovery (If Starting Fresh)
- Problem inspiration and context
- User identification and segmentation
- Success definition and metrics
- Failure consequences
- Previous attempts
- Domain-specific requirements

### Round 2: Concrete Examples
- Specific scenarios system SHOULD handle
- Specific scenarios system should NOT handle
- Boundary conditions and edge cases
- Qualification criteria
- Counter-examples and exclusions

### Round 3: Technical Feasibility
- Performance requirements
- Scalability needs
- Integration constraints
- Security requirements
- Compliance needs

### Round 4: User Experience
- Mental models users bring
- Critical user tasks
- Common failure points
- Information density preferences
- Error recovery patterns

### Round 5+: Fill Gaps
Continue until:
- Every "somehow" becomes specific
- Every "probably" becomes certain
- Every assumption is documented
- Critical paths are clear
- Dependencies are mapped

## Graph Update Patterns

### Adding Features from QA
```bash
# User wants new analytics feature (starts in phase 0)
./know/lib/mod-graph.sh add features advanced-analytics "Advanced Analytics"
./know/lib/mod-graph.sh set features advanced-analytics priority P1
./know/lib/mod-graph.sh set features advanced-analytics phase 0

# After discovering dependencies, update phase
./know/lib/mod-graph.sh connect feature:advanced-analytics platform:aws-infrastructure
./know/lib/mod-graph.sh connect feature:advanced-analytics component:data-pipeline

# Move to appropriate phase based on dependencies
./know/lib/mod-graph.sh set features advanced-analytics phase 3  # Goes to features phase
```

### Adding Users from QA
```bash
# New user type identified
./know/lib/mod-graph.sh add users data-analyst "Data Analyst"
./know/lib/mod-graph.sh connect user:data-analyst functionality:analytics-insights
./know/lib/mod-graph.sh connect user:data-analyst screen:business-intelligence
```

### Adding Requirements from QA
```bash
# New constraint discovered
./know/lib/mod-graph.sh add requirements gdpr-compliance "GDPR Compliance"
./know/lib/mod-graph.sh set requirements gdpr-compliance criticality critical
./know/lib/mod-graph.sh connect requirement:gdpr-compliance feature:analytics
```

## Validation After Updates

```bash
# Check for circular dependencies
./know/lib/query-graph.sh cycles

# Validate specific entity dependencies
./know/lib/query-graph.sh deps feature:new-feature

# Check impact of changes
./know/lib/query-graph.sh impact platform:aws-infrastructure

# Find entities still in phase 0
jq '.meta.project.phases[0].requirements[]' .ai/spec-graph.json

# Analyze phase dependencies to ensure correct sequencing
for phase in 1 2 3 4 5 6; do
  echo "Phase $phase entities:"
  jq --arg p "$phase" '.meta.project.phases[] | select(.id | startswith($p)).requirements[]' .ai/spec-graph.json
done

# Generate statistics
./know/lib/mod-graph.sh stats
```

## Success Indicators

- Graph completeness increases with each session
- Dependency chains are logical and complete
- No orphaned entities
- All user types have clear access paths
- Features map to concrete requirements
- Technical constraints are documented

## Resume Capability

When resuming an existing session:

```bash
# Find in-progress session
SESSION=$(jq -r '.meta.qa_sessions[] | select(.status == "in_progress") | .id' .ai/spec-graph.json)

# Show context from last 3 questions
jq --arg sid "$SESSION" '.meta.qa_sessions[] | select(.id == $sid) | .questions[-3:]' .ai/spec-graph.json

# Continue with next question based on discovered gaps
```

Starting fresh when no active session:
1. Analyze graph completeness
2. Identify highest priority gaps
3. Start new session targeting those gaps
4. Focus on areas with most missing connections

## Output

The spec graph becomes richer with each QA cycle:
- More entities defined
- Clearer relationships
- Better specifications
- Validated assumptions
- Prioritized features
- Complete dependency maps

This iterative process ensures the spec graph remains the single source of truth, growing organically through structured discovery rather than upfront guessing.