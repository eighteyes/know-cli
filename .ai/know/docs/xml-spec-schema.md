# Know XML Spec Schema

## Overview

This schema defines the XML output format for `know gen spec --format=xml`. It's designed to provide executable task specifications for `/know:build` with minimal agent guessing.

Based on GSD (Get Shit Done) framework with Know-specific extensions for graph cross-referencing.

## Root Structure

```xml
<spec version="1.0">
  <meta>
    <feature>feature:auth</feature>
    <phase>II</phase>
    <status>in-progress</status>
  </meta>

  <context>
    <!-- Full feature context to minimize agent guessing -->
  </context>

  <dependencies>
    <!-- Cross-graph references -->
  </dependencies>

  <tasks>
    <!-- Ordered executable tasks derived from operations -->
  </tasks>
</spec>
```

## Meta Section

Feature metadata from spec-graph:

```xml
<meta>
  <feature>feature:spec-generation-enrichment</feature>
  <name>Spec Generation Enrichment</name>
  <description>Enhanced feature spec generation with metadata and structure</description>
  <phase>in-progress</phase>
  <status>incomplete</status>
</meta>
```

## Context Section

Full context for agent execution, derived from graph traversal:

```xml
<context>
  <!-- Users this feature serves -->
  <users>
    <user id="developer">Software Developer</user>
    <user id="ai-assistant">AI Assistant</user>
  </users>

  <!-- Objectives this feature addresses -->
  <objectives>
    <objective id="manage-specs">Create and update spec graphs</objective>
  </objectives>

  <!-- Actions required -->
  <actions>
    <action id="enrich-feature-specs">
      <name>Enrich Feature Specs</name>
      <description>Generate rich feature specifications with metadata</description>
    </action>
  </actions>

  <!-- Components to implement -->
  <components>
    <component id="spec-generator">
      <name>Spec Generator</name>
      <description>Core spec generation logic</description>
    </component>
  </components>
</context>
```

## Dependencies Section

Cross-references to code-graph for integration points:

```xml
<dependencies>
  <!-- Code modules this feature integrates with -->
  <code-modules>
    <module id="module:graph-loader" graph="code-graph.json">
      <purpose>Load and parse graph files</purpose>
      <integration-point>Spec generator reads graph structure</integration-point>
    </module>
  </code-modules>

  <!-- Required interfaces from code-graph -->
  <interfaces>
    <interface id="interface:graph-api" graph="code-graph.json">
      <methods>
        <method>get_entity(type, key)</method>
        <method>get_dependencies(entity_id)</method>
      </methods>
    </interface>
  </interfaces>

  <!-- External dependencies -->
  <external>
    <package>click</package>
    <package>jinja2</package>
  </external>
</dependencies>
```

## Tasks Section

Executable tasks derived from operations, ordered by dependencies:

```xml
<tasks>
  <!-- Regular auto task (no checkpoint) -->
  <task id="task-1" type="auto" wave="1">
    <operation>operation:generate-rich-feature-spec</operation>
    <name>Generate Rich Feature Spec</name>

    <files>
      <file>know/src/generators/spec_generator.py</file>
      <file>know/templates/feature-spec.md.j2</file>
    </files>

    <action>
      Implement spec generator that:
      1. Reads feature entity from graph (feature:spec-generation-enrichment)
      2. Traverses dependencies: action → component → operation
      3. Gathers context: users, objectives from reverse dependencies
      4. Renders using Jinja2 template

      Use rich.console for formatting.
      Use existing graph_loader.GraphLoader (module:graph-loader).
      Avoid creating new graph traversal logic - reuse graph.get_dependencies().
    </action>

    <verify>
      <test>know gen spec feature:spec-generation-enrichment --format=md</test>
      <assertion>Output includes users, objectives, actions, components, operations</assertion>
    </verify>

    <done>
      Running `know gen spec <feature>` outputs complete markdown spec with all graph-derived context.
      No manual lookups needed - everything automated from graph traversal.
    </done>
  </task>

  <!-- Task with human verification checkpoint (90% of checkpoints) -->
  <task id="task-2" type="checkpoint:human-verify" wave="2">
    <operation>operation:render-typescript</operation>
    <name>Implement TypeScript Reference Rendering</name>

    <files>
      <file>know/src/renderers/typescript_renderer.py</file>
    </files>

    <action>
      Create TypeScript interface renderer:
      1. Takes data-model reference from spec-graph
      2. Converts to TypeScript interface syntax
      3. Handles nested types, arrays, optional fields

      Use existing reference schema from spec-graph.
      Emit valid TypeScript (test with tsc --noEmit).
    </action>

    <verify>
      <test>pytest know/tests/test_typescript_renderer.py</test>
      <assertion>Renders valid TypeScript interfaces from data-model refs</assertion>
    </verify>

    <done>
      TypeScript renderer converts data-models to valid TS interfaces.
      CHECKPOINT: Human reviews rendered output for type accuracy.
    </done>
  </task>

  <!-- Decision checkpoint (9% of checkpoints) - requires user choice -->
  <task id="task-3" type="checkpoint:decision" wave="2">
    <name>Choose Template Engine Strategy</name>

    <decision>
      <question>Which template engine for spec rendering?</question>
      <options>
        <option id="jinja2">
          <name>Jinja2</name>
          <pros>Already in requirements.txt, familiar, powerful</pros>
          <cons>Another dependency, Python-specific</cons>
        </option>
        <option id="string-format">
          <name>String Formatting</name>
          <pros>No dependency, simple</pros>
          <cons>Hard to maintain for complex specs</cons>
        </option>
      </options>
    </decision>

    <done>
      User selects template engine approach.
      Decision recorded for subsequent tasks.
    </done>
  </task>

  <!-- Human action checkpoint (1% of checkpoints) - requires manual user work -->
  <task id="task-4" type="checkpoint:human-action" wave="3">
    <name>Create Feature Spec Template</name>

    <files>
      <file>know/templates/feature-spec.md.j2</file>
    </files>

    <action>
      HUMAN ACTION REQUIRED:
      Create Jinja2 template for feature spec output.
      Review existing feature specs for format.
      Define sections: users, objectives, actions, components, operations.
    </action>

    <done>
      User creates template file.
      Agent verifies template exists and is valid Jinja2.
    </done>
  </task>
</tasks>
```

## Wave System

**Wave = execution grouping based on dependency order**

Computed from graph dependencies at plan time (NOT stored in spec-graph):

```python
def compute_waves(operations):
    """Compute wave/tier for parallel execution"""
    waves = {}
    visited = set()

    def get_wave(op_id, depth=0):
        if op_id in visited:
            return waves.get(op_id, 0)

        visited.add(op_id)
        deps = graph.get_dependencies(op_id)

        if not deps:
            waves[op_id] = 1
        else:
            max_dep_wave = max(get_wave(dep) for dep in deps)
            waves[op_id] = max_dep_wave + 1

        return waves[op_id]

    for op in operations:
        get_wave(op)

    return waves
```

**Wave execution rules:**
- Tasks in wave N execute in parallel (no dependencies between them)
- Wave N+1 starts only after all wave N tasks complete
- Checkpoints pause execution within a wave

## Checkpoint Types

### checkpoint:human-verify (90%)
Agent executes, human reviews output:
- Code review
- Test result verification
- Output correctness check
- Integration testing

### checkpoint:decision (9%)
Human makes implementation choice:
- Library selection
- Architecture approach
- Trade-off decisions
- Conflicting requirements resolution

### checkpoint:human-action (1%)
Human performs manual work:
- Create design assets
- Write documentation
- Configure external services
- Manual testing in production

## Mapping Know Graph to XML

### Spec-Graph Entities → XML Elements

| Spec Graph | XML Element | Notes |
|------------|-------------|-------|
| user | `<context><users><user>` | Who uses this feature |
| objective | `<context><objectives><objective>` | Why this feature exists |
| action | `<context><actions><action>` | What user-facing actions |
| component | `<context><components><component>` | What software components |
| operation | `<tasks><task><operation>` | Executable implementation task |

### Code-Graph References → Dependencies

| Code Graph | XML Element | Notes |
|------------|-------------|-------|
| module | `<dependencies><code-modules><module>` | Code integration points |
| interface | `<dependencies><interfaces><interface>` | API contracts |
| external-dep | `<dependencies><external><package>` | Third-party libraries |

### GSD Concept Mapping

| GSD Concept | Know Equivalent | Location |
|-------------|-----------------|----------|
| must_haves.truths | requirement acceptance criteria | Future: `meta.requirements` |
| must_haves.artifacts | component outputs | `<components>` in context |
| must_haves.key_links | integration points | `<code-modules>` in dependencies |
| wave | computed from graph deps | `wave` attribute on `<task>` |

## Example: Full Feature Spec XML

```xml
<spec version="1.0">
  <meta>
    <feature>feature:auth</feature>
    <name>User Authentication</name>
    <description>Secure user authentication with JWT tokens</description>
    <phase>II</phase>
    <status>in-progress</status>
  </meta>

  <context>
    <users>
      <user id="end-user">End User</user>
      <user id="admin">Administrator</user>
    </users>

    <objectives>
      <objective id="secure-access">Secure user access control</objective>
    </objectives>

    <actions>
      <action id="login">
        <name>User Login</name>
        <description>Authenticate user credentials</description>
      </action>
    </actions>

    <components>
      <component id="auth-service">
        <name>Authentication Service</name>
        <description>JWT token generation and validation</description>
      </component>
    </components>
  </context>

  <dependencies>
    <code-modules>
      <module id="module:auth" graph="code-graph.json">
        <purpose>Authentication logic</purpose>
      </module>
    </code-modules>

    <interfaces>
      <interface id="interface:user-db" graph="code-graph.json">
        <methods>
          <method>get_user(username)</method>
          <method>verify_password(username, password)</method>
        </methods>
      </interface>
    </interfaces>

    <external>
      <package>PyJWT</package>
      <package>bcrypt</package>
    </external>
  </dependencies>

  <tasks>
    <task id="task-1" type="auto" wave="1">
      <operation>operation:generate-jwt</operation>
      <name>Implement JWT Generation</name>

      <files>
        <file>src/auth/jwt_service.py</file>
      </files>

      <action>
        Create JWT token generator:
        1. Install PyJWT via pip
        2. Create JWTService class with generate_token(user_id, expiry)
        3. Use HS256 algorithm with secret from environment
        4. Include user_id, exp, iat claims

        Use PyJWT library (avoid rolling crypto).
        Load secret from JWT_SECRET env var.
        Default expiry: 1 hour.
      </action>

      <verify>
        <test>pytest tests/test_jwt_service.py::test_generate_token</test>
        <assertion>Token is valid and contains expected claims</assertion>
      </verify>

      <done>
        JWTService generates valid tokens.
        Tests pass with proper claim validation.
      </done>
    </task>

    <task id="task-2" type="checkpoint:human-verify" wave="2">
      <operation>operation:verify-jwt</operation>
      <name>Implement JWT Verification</name>

      <files>
        <file>src/auth/jwt_service.py</file>
      </files>

      <action>
        Add JWT verification to JWTService:
        1. Add verify_token(token) method
        2. Validate signature with same secret
        3. Check expiration
        4. Return decoded claims or raise InvalidTokenError

        Handle expired tokens gracefully.
        Log verification failures for security monitoring.
      </action>

      <verify>
        <test>pytest tests/test_jwt_service.py::test_verify_token</test>
        <assertion>Valid tokens decode, invalid/expired tokens raise error</assertion>
      </verify>

      <done>
        JWT verification works correctly.
        CHECKPOINT: Human reviews security handling.
      </done>
    </task>
  </tasks>
</spec>
```

## Open Questions

1. **How to handle operations without clear file targets?**
   - Some operations are conceptual (e.g., "define data model")
   - Solution: Include in `<action>` as prerequisite step

2. **Cross-graph references - how detailed?**
   - Full interface signatures vs just module names?
   - Solution: Start with module names + purpose, expand if needed

3. **Wave computation timing?**
   - Compute once at spec generation or dynamically during build?
   - Solution: Compute at spec generation, include as `wave` attribute

4. **Checkpoint frequency?**
   - Every operation? Only on critical paths?
   - Solution: Default to 90% human-verify, user can configure

5. **How to represent operation dependencies that span features?**
   - Cross-feature operations (shared components)
   - Solution: Include in `<dependencies>` with feature context

## Next Steps

1. Validate schema with user ✓ (this document)
2. Implement XML generator (Task #1)
3. Test with real features from spec-graph
4. Iterate on schema based on real-world usage
