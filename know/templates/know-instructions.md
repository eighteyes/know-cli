<!-- know:start -->
<know-instructions>
When discussing architecture, product decisions, features, or system design,
use the `know` CLI to capture decisions in the spec-graph.

Run `know -h` for commands. Run `know <command> -h` for usage details.

Spec graph entities: project, user, objective, feature, workflow, action, component, operation
Code graph entities: module, package, layer, namespace, interface, class, function

Common reference types: data-model, endpoint, api-contract, business-logic,
  acceptance-criterion, validation-rule, source-file, external-dep, code-link

Run `know check ref-types` for reference types with descriptions.
Run `know gen rules describe entities` for entity types.
Run `know gen rules graph` for the dependency topology.

When adding features, use the `know:add` slash command (/know:add).
Run /know:list to see existing features before adding new ones.
Run `know check validate` after graph changes.
Graph files are write-protected — use `know` CLI commands for all modifications.

Persist architectural decisions as graph entities, not prose.
The spec-graph is the source of truth for product intent.
</know-instructions>
<!-- know:end -->
