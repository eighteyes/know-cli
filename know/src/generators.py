"""
Spec generators for the know tool.
Generate documentation and templates based on graph data.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path


class SpecGenerator:
    """Generates specifications and documentation from graph data."""

    def __init__(self, graph_manager, entity_manager, dependency_manager):
        """
        Initialize spec generator.

        Args:
            graph_manager: GraphManager instance
            entity_manager: EntityManager instance
            dependency_manager: DependencyManager instance
        """
        self.graph = graph_manager
        self.entities = entity_manager
        self.deps = dependency_manager

    def generate_entity_spec(self, entity_id: str, include_deps: bool = True) -> str:
        """
        Generate a comprehensive specification for an entity.

        Produces LLM-quality output deterministically by traversing
        the full graph context including:
        - Full dependency chain narrative
        - Cross-referenced related entities
        - User story format for user/objective/action chains
        - Phase and status information
        - Related references

        Args:
            entity_id: Entity identifier
            include_deps: Whether to include dependencies

        Returns:
            Markdown formatted specification
        """
        entity_type, entity_name = entity_id.split(':', 1)
        entity_data = self.entities.get_entity(entity_id)

        if not entity_data:
            return f"# Error: Entity {entity_id} not found\n"

        lines = []
        lines.append(f"# {entity_data.get('name', entity_name)}")
        lines.append("")
        lines.append(f"**Type:** {entity_type}")
        lines.append(f"**ID:** `{entity_id}`")
        lines.append("")

        # Phase and Status from meta
        phase_info = self._get_entity_phase_status(entity_id)
        if phase_info:
            lines.append(f"**Horizon:** {phase_info.get('horizon', 'N/A')}")
            lines.append(f"**Status:** {phase_info.get('status', 'N/A')}")
            lines.append("")

        # Description
        if entity_data.get('description'):
            lines.append("## Description")
            lines.append("")
            lines.append(entity_data['description'])
            lines.append("")

        # User Story (for features, actions, components)
        user_story = self._generate_user_story(entity_id)
        if user_story:
            lines.append("## User Story")
            lines.append("")
            lines.append(user_story)
            lines.append("")

        # Traceability Chain
        trace_chain = self._build_trace_chain(entity_id)
        if trace_chain and len(trace_chain) > 1:
            lines.append("## Traceability")
            lines.append("")
            lines.append("**Chain:** " + " → ".join(trace_chain))
            lines.append("")

        # Dependencies with context
        if include_deps:
            dependencies = self.deps.get_dependencies(entity_id)
            if dependencies:
                # Group by type for better organization
                dep_by_type: Dict[str, List[str]] = {}
                for dep in dependencies:
                    dep_type = dep.split(':')[0] if ':' in dep else 'other'
                    if dep_type not in dep_by_type:
                        dep_by_type[dep_type] = []
                    dep_by_type[dep_type].append(dep)

                lines.append("## Dependencies")
                lines.append("")

                for dep_type, deps in sorted(dep_by_type.items()):
                    lines.append(f"### {dep_type.replace('-', ' ').title()}")
                    lines.append("")
                    for dep in deps:
                        dep_data = self.entities.get_entity(dep)
                        if dep_data:
                            dep_name = dep_data.get('name', dep)
                            dep_desc = dep_data.get('description', '')
                            lines.append(f"- **`{dep}`** - {dep_name}")
                            if dep_desc:
                                lines.append(f"  - {dep_desc[:150]}{'...' if len(dep_desc) > 150 else ''}")
                        else:
                            # It's a reference, get reference data
                            ref_data = self._get_reference_data(dep)
                            if ref_data:
                                lines.append(f"- **`{dep}`** (reference)")
                            else:
                                lines.append(f"- `{dep}`")
                    lines.append("")

            # Dependents (what uses this)
            dependents = self.deps.get_dependents(entity_id)
            if dependents:
                lines.append("## Used By")
                lines.append("")
                for dep in dependents:
                    dep_data = self.entities.get_entity(dep)
                    if dep_data:
                        dep_name = dep_data.get('name', dep)
                        lines.append(f"- **`{dep}`** - {dep_name}")
                    else:
                        lines.append(f"- `{dep}`")
                lines.append("")

        # Requirements (if this is a feature)
        if entity_type == 'feature':
            requirements = self._get_feature_requirements(entity_name)
            if requirements:
                lines.append("## Requirements")
                lines.append("")
                for req_key, req_data in requirements.items():
                    status = req_data.get('status', 'pending')
                    name = req_data.get('name', req_key)
                    status_icon = '✅' if status == 'complete' else '🔄' if status == 'in-progress' else '📋'
                    lines.append(f"- {status_icon} **{name}** ({status})")
                    if req_data.get('description'):
                        lines.append(f"  - {req_data['description']}")
                lines.append("")

        # Related references (data-models, business_logic, etc.)
        related_refs = self._get_related_references(entity_id)
        if related_refs:
            lines.append("## Related References")
            lines.append("")
            for ref_type, refs in related_refs.items():
                lines.append(f"### {ref_type.replace('_', ' ').title()}")
                lines.append("")
                for ref_id, ref_data in refs.items():
                    lines.append(f"**{ref_id}:**")
                    if isinstance(ref_data, dict):
                        lines.append("```json")
                        import json
                        lines.append(json.dumps(ref_data, indent=2))
                        lines.append("```")
                    else:
                        lines.append(f"```\n{ref_data}\n```")
                lines.append("")

        # Filter out any None values
        return "\n".join(str(line) if line is not None else '' for line in lines)

    def _get_entity_phase_status(self, entity_id: str) -> dict:
        """Get horizon and status for an entity from meta.horizons."""
        data = self.graph.get_graph()
        horizons = data.get('meta', {}).get('horizons', {})

        for horizon_name, horizon_entries in horizons.items():
            if entity_id in horizon_entries:
                return {
                    'horizon': horizon_name,
                    'status': horizon_entries[entity_id].get('status', 'unknown')
                }
        return {}

    def _generate_user_story(self, entity_id: str) -> str:
        """
        Generate a user story by tracing up to user/objective.

        Returns format: "As a [user], I want to [action] so that [objective]"
        """
        # Trace upstream to find user and objective
        chain = self._build_trace_chain(entity_id)

        user = None
        objective = None
        action = None

        for item in chain:
            if item.startswith('user:'):
                user_data = self.entities.get_entity(item)
                user = user_data.get('name', item) if user_data else item
            elif item.startswith('objective:'):
                obj_data = self.entities.get_entity(item)
                objective = obj_data.get('description', obj_data.get('name', item)) if obj_data else item
            elif item.startswith('action:'):
                act_data = self.entities.get_entity(item)
                action = act_data.get('name', item) if act_data else item

        if user and (objective or action):
            story = f"As a **{user}**"
            if action:
                story += f", I want to **{action}**"
            if objective:
                story += f" so that **{objective}**"
            return story

        return ""

    def _build_trace_chain(self, entity_id: str) -> List[str]:
        """Build traceability chain from entity up to user."""
        chain_order = ['operation', 'component', 'action', 'feature', 'objective', 'user']
        chain = [entity_id]
        current = entity_id
        visited = set()

        while current and current not in visited:
            visited.add(current)
            upstream = self.deps.get_dependencies(current)
            if not upstream:
                break

            current_type = current.split(':')[0]
            try:
                current_idx = chain_order.index(current_type)
            except ValueError:
                current_idx = -1

            next_entity = None
            for up in upstream:
                up_type = up.split(':')[0]
                try:
                    up_idx = chain_order.index(up_type)
                    if up_idx > current_idx:
                        next_entity = up
                        break
                except ValueError:
                    continue

            if next_entity:
                chain.append(next_entity)
                current = next_entity
            else:
                break

        return list(reversed(chain))

    def _get_feature_requirements(self, feature_name: str) -> dict:
        """Get requirements for a feature from meta.requirements."""
        data = self.graph.get_graph()
        all_reqs = data.get('meta', {}).get('requirements', {})

        feature_reqs = {}
        for req_key, req_data in all_reqs.items():
            if req_key.startswith(f"{feature_name}-"):
                feature_reqs[req_key] = req_data

        return feature_reqs

    def _get_related_references(self, entity_id: str) -> Dict[str, Dict]:
        """Get references that this entity depends on, grouped by type."""
        dependencies = self.deps.get_dependencies(entity_id)
        data = self.graph.get_graph()
        references = data.get('references', {})

        related = {}
        for dep in dependencies:
            if ':' not in dep:
                continue
            dep_type, dep_name = dep.split(':', 1)

            # Check if it's a reference type
            if dep_type in references:
                if dep_type not in related:
                    related[dep_type] = {}
                ref_data = references[dep_type].get(dep_name)
                if ref_data:
                    related[dep_type][dep_name] = ref_data

        return related

    def generate_feature_spec(self, feature_id: str) -> str:
        """
        Generate a detailed feature specification with rich metadata.

        Args:
            feature_id: Feature entity ID

        Returns:
            Markdown formatted feature spec with 11 sections
        """
        entity_data = self.entities.get_entity(feature_id)
        if not entity_data:
            return f"# Error: Feature {feature_id} not found\n"

        # Extract feature name without prefix for metadata lookup
        feature_name = feature_id.split(':', 1)[1] if ':' in feature_id else feature_id

        lines = []
        lines.append(f"# Feature: {entity_data.get('name', feature_id)}")
        lines.append("")

        # 1. Overview
        lines.append("## Overview")
        lines.append("")
        lines.append(entity_data.get('description', 'No description provided'))
        lines.append("")

        # 2. Status/Phase/Priority from meta.feature_specs (NEW)
        feature_meta = self._get_feature_spec_meta(feature_name)
        if feature_meta:
            status = feature_meta.get('status')
            phase = feature_meta.get('phase')
            priority = feature_meta.get('priority')

            if status or phase or priority:
                lines.append("## Status")
                lines.append("")
                if status:
                    lines.append(f"**Status:** {status}")
                if phase:
                    lines.append(f"**Phase:** {phase}")
                if priority:
                    lines.append(f"**Priority:** {priority}")
                lines.append("")

        # Dependencies breakdown
        dependencies = self.deps.get_dependencies(feature_id)

        # Group dependencies by type
        dep_by_type: Dict[str, List[str]] = {}
        for dep in dependencies:
            dep_type = dep.split(':')[0] if ':' in dep else 'unknown'
            if dep_type not in dep_by_type:
                dep_by_type[dep_type] = []
            dep_by_type[dep_type].append(dep)

        # 3. User Actions (existing)
        if 'action' in dep_by_type:
            lines.append("## User Actions")
            lines.append("")
            actions = dep_by_type.get('action', [])
            for action_id in actions:
                action_data = self.entities.get_entity(action_id)
                if action_data:
                    lines.append(f"### {action_data.get('name', action_id)}")
                    lines.append("")
                    lines.append(action_data.get('description', ''))
                    lines.append("")

        # 4. Components with file paths and operations (ENHANCED)
        if 'component' in dep_by_type:
            lines.append("## Components")
            lines.append("")
            components = dep_by_type.get('component', [])
            for comp_id in components:
                comp_data = self.entities.get_entity(comp_id)
                if comp_data:
                    comp_name = comp_data.get('name', comp_id)
                    comp_desc = comp_data.get('description', '')

                    # Get file path if available
                    file_path = self._get_component_file(comp_id)

                    # Get operations
                    operations = self._get_component_operations(comp_id)

                    lines.append(f"### {comp_name}")
                    lines.append("")
                    lines.append(comp_desc)

                    if file_path:
                        lines.append("")
                        lines.append(f"**File:** `{file_path}`")

                    if operations:
                        lines.append("")
                        lines.append("**Operations:**")
                        for op_id in operations:
                            op_data = self.entities.get_entity(op_id)
                            if op_data:
                                op_name = op_data.get('name', op_id)
                                lines.append(f"- {op_name}")

                    lines.append("")

        # 5. Interfaces with api-schema rendering (NEW)
        if 'interface' in dep_by_type:
            lines.append("## Interfaces")
            lines.append("")
            interfaces = dep_by_type.get('interface', [])
            for intf_id in interfaces:
                intf_data = self.entities.get_entity(intf_id)
                if intf_data:
                    lines.append(f"### {intf_data.get('name', intf_id)}")
                    lines.append("")
                    lines.append(intf_data.get('description', ''))

                    # Check for api-schema dependencies
                    intf_deps = self.deps.get_dependencies(intf_id)
                    api_schemas = [d for d in intf_deps if d.startswith('api-schema:')]

                    if api_schemas:
                        lines.append("")
                        lines.append("**API Schema:**")
                        for schema_id in api_schemas:
                            schema_data = self._get_reference_data(schema_id)
                            if schema_data:
                                lines.append("```")
                                lines.append(str(schema_data))
                                lines.append("```")

                    lines.append("")

        # 6. Data Models as TypeScript (NEW)
        if 'data-model' in dep_by_type:
            lines.append("## Data Models")
            lines.append("")
            data_models = dep_by_type.get('data-model', [])
            for model_id in data_models:
                model_data = self._get_reference_data(model_id)
                if model_data:
                    model_name = model_id.split(':', 1)[1] if ':' in model_id else model_id

                    lines.append(f"### {model_name}")
                    lines.append("")
                    lines.append("```typescript")
                    lines.append(self._render_data_model_typescript(model_data, model_name))
                    lines.append("```")
                    lines.append("")

        # 7. Business Logic (existing, enhanced)
        if 'business-logic' in dep_by_type:
            lines.append("## Business Logic")
            lines.append("")
            for ref_id in dep_by_type['business-logic']:
                ref_data = self._get_reference_data(ref_id)
                if ref_data is not None:
                    lines.append(f"### {ref_id}")
                    lines.append("```")
                    lines.append(str(ref_data))
                    lines.append("```")
                    lines.append("")

        # Other reference types (acceptance-criterion, api-contract, validation-rule)
        ref_types = ['acceptance-criterion', 'api-contract', 'validation-rule']
        for ref_type in ref_types:
            if ref_type in dep_by_type:
                lines.append(f"## {ref_type.replace('-', ' ').title()}")
                lines.append("")
                for ref_id in dep_by_type[ref_type]:
                    ref_data = self._get_reference_data(ref_id)
                    if ref_data is not None:
                        lines.append(f"### {ref_id}")
                        lines.append("```")
                        lines.append(str(ref_data))
                        lines.append("```")
                        lines.append("")

        # 8. Use Cases from meta.feature_specs (NEW)
        if feature_meta and 'use_cases' in feature_meta:
            use_cases = feature_meta['use_cases']
            if use_cases:
                lines.append("## Use Cases")
                lines.append("")
                for uc in use_cases:
                    if isinstance(uc, dict):
                        uc_name = uc.get('name', 'Unnamed Use Case')
                        uc_desc = uc.get('description', '')
                        uc_config = uc.get('config', {})

                        lines.append(f"### {uc_name}")
                        lines.append("")
                        if uc_desc:
                            lines.append(uc_desc)
                            lines.append("")
                        if uc_config:
                            lines.append("**Configuration:**")
                            lines.append("```json")
                            import json
                            lines.append(json.dumps(uc_config, indent=2))
                            lines.append("```")
                            lines.append("")
                    else:
                        lines.append(f"- {uc}")
                        lines.append("")

        # 9. Testing Requirements from meta.feature_specs (NEW)
        if feature_meta and 'testing' in feature_meta:
            testing = feature_meta['testing']
            if testing:
                lines.append("## Testing Requirements")
                lines.append("")

                if 'unit' in testing and testing['unit']:
                    lines.append("### Unit Tests")
                    lines.append("")
                    for test in testing['unit']:
                        lines.append(f"- {test}")
                    lines.append("")

                if 'integration' in testing and testing['integration']:
                    lines.append("### Integration Tests")
                    lines.append("")
                    for test in testing['integration']:
                        lines.append(f"- {test}")
                    lines.append("")

                if 'performance' in testing and testing['performance']:
                    lines.append("### Performance Tests")
                    lines.append("")
                    for test in testing['performance']:
                        lines.append(f"- {test}")
                    lines.append("")

        # 10. Security & Privacy from meta.feature_specs (NEW)
        if feature_meta and 'security' in feature_meta:
            security = feature_meta['security']
            if security:
                lines.append("## Security & Privacy")
                lines.append("")
                for sec_req in security:
                    lines.append(f"- {sec_req}")
                lines.append("")

        # 11. Monitoring & Observability from meta.feature_specs (NEW)
        if feature_meta and 'monitoring' in feature_meta:
            monitoring = feature_meta['monitoring']
            if monitoring:
                lines.append("## Monitoring & Observability")
                lines.append("")
                for metric in monitoring:
                    lines.append(f"- {metric}")
                lines.append("")

        # Performance characteristics from meta.feature_specs
        if feature_meta and 'performance' in feature_meta:
            performance = feature_meta['performance']
            if isinstance(performance, dict):
                lines.append("## Performance Characteristics")
                lines.append("")

                if 'latency' in performance:
                    lines.append(f"**Latency:** {performance['latency']}")
                if 'cost' in performance:
                    lines.append(f"**Cost:** {performance['cost']}")
                if 'quality' in performance:
                    lines.append(f"**Quality:** {performance['quality']}")

                lines.append("")

        # Filter out any None values that might have slipped in
        return "\n".join(str(line) if line is not None else '' for line in lines)

    def generate_feature_spec_xml(self, feature_id: str, code_graph_path: str = '.ai/know/code-graph.json') -> str:
        """
        Generate XML specification for a feature based on GSD framework.

        This generates executable task specifications with minimal agent guessing,
        designed for consumption by /know:build command.

        Args:
            feature_id: Feature entity ID
            code_graph_path: Path to code-graph.json for file path lookups

        Returns:
            XML formatted feature spec with meta, context, dependencies, and tasks
        """
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        from pathlib import Path
        import json

        entity_data = self.entities.get_entity(feature_id)
        if not entity_data:
            return f"<!-- Error: Feature {feature_id} not found -->\n"

        feature_name = feature_id.split(':', 1)[1] if ':' in feature_id else feature_id

        # Load code-graph for file path lookups
        code_graph = None
        if Path(code_graph_path).exists():
            with open(code_graph_path) as f:
                code_graph = json.load(f)

        # Create root element
        root = ET.Element('spec', version='1.0')

        # META section
        meta_el = ET.SubElement(root, 'meta')
        ET.SubElement(meta_el, 'feature').text = feature_id
        ET.SubElement(meta_el, 'name').text = entity_data.get('name', feature_id)
        ET.SubElement(meta_el, 'description').text = entity_data.get('description', '')

        # Get phase and status
        phase_info = self._get_entity_phase_status(feature_id)
        if phase_info:
            ET.SubElement(meta_el, 'horizon').text = phase_info.get('horizon', 'pending')
            ET.SubElement(meta_el, 'status').text = phase_info.get('status', 'incomplete')

        # CONTEXT section - full graph context to minimize agent guessing
        context_el = ET.SubElement(root, 'context')

        # Get dependencies breakdown
        dependencies = self.deps.get_dependencies(feature_id)
        dep_by_type: Dict[str, List[str]] = {}
        for dep in dependencies:
            dep_type = dep.split(':')[0] if ':' in dep else 'unknown'
            if dep_type not in dep_by_type:
                dep_by_type[dep_type] = []
            dep_by_type[dep_type].append(dep)

        # Users this feature serves (from reverse dependencies)
        users_el = ET.SubElement(context_el, 'users')
        dependents = self.deps.get_dependents(feature_id)
        user_dependents = [d for d in dependents if d.startswith('user:')]
        for user_id in user_dependents:
            user_data = self.entities.get_entity(user_id)
            if user_data:
                user_el = ET.SubElement(users_el, 'user', id=user_id.split(':', 1)[1])
                user_el.text = user_data.get('name', user_id)

        # Objectives this feature addresses
        objectives_el = ET.SubElement(context_el, 'objectives')
        obj_dependents = [d for d in dependents if d.startswith('objective:')]
        for obj_id in obj_dependents:
            obj_data = self.entities.get_entity(obj_id)
            if obj_data:
                obj_el = ET.SubElement(objectives_el, 'objective', id=obj_id.split(':', 1)[1])
                obj_el.text = obj_data.get('description', obj_data.get('name', obj_id))

        # Actions required
        if 'action' in dep_by_type:
            actions_el = ET.SubElement(context_el, 'actions')
            for action_id in dep_by_type['action']:
                action_data = self.entities.get_entity(action_id)
                if action_data:
                    action_el = ET.SubElement(actions_el, 'action', id=action_id.split(':', 1)[1])
                    ET.SubElement(action_el, 'name').text = action_data.get('name', action_id)
                    ET.SubElement(action_el, 'description').text = action_data.get('description', '')

        # Components to implement
        if 'component' in dep_by_type:
            components_el = ET.SubElement(context_el, 'components')
            for comp_id in dep_by_type['component']:
                comp_data = self.entities.get_entity(comp_id)
                if comp_data:
                    comp_el = ET.SubElement(components_el, 'component', id=comp_id.split(':', 1)[1])
                    ET.SubElement(comp_el, 'name').text = comp_data.get('name', comp_id)
                    ET.SubElement(comp_el, 'description').text = comp_data.get('description', '')

        # Gather all components early (needed for dependencies section)
        all_components = []
        if 'action' in dep_by_type:
            for action_id in dep_by_type['action']:
                action_deps = self.deps.get_dependencies(action_id)
                for dep in action_deps:
                    if dep.startswith('component:'):
                        all_components.append(dep)
        # Also include direct component dependencies
        if 'component' in dep_by_type:
            all_components.extend(dep_by_type['component'])

        # DEPENDENCIES section - code-graph cross-references
        deps_el = ET.SubElement(root, 'dependencies')

        # Code modules (from code-graph references if available)
        # TODO: Cross-reference code-graph when available
        code_modules_el = ET.SubElement(deps_el, 'code-modules')
        ET.Comment(' Code module integration points will be added here ')

        # Interfaces
        if 'interface' in dep_by_type:
            interfaces_el = ET.SubElement(deps_el, 'interfaces')
            for intf_id in dep_by_type['interface']:
                intf_data = self.entities.get_entity(intf_id)
                if intf_data:
                    intf_el = ET.SubElement(interfaces_el, 'interface',
                                          id=intf_id.split(':', 1)[1],
                                          graph='spec-graph.json')
                    ET.SubElement(intf_el, 'name').text = intf_data.get('name', intf_id)
                    ET.SubElement(intf_el, 'description').text = intf_data.get('description', '')

        # External dependencies - extract from code-graph
        external_el = ET.SubElement(deps_el, 'external')
        if code_graph and all_components:
            # Get external deps for components via module lookups
            external_deps = self._get_external_deps_for_components(
                all_components, code_graph
            )
            for dep_name, dep_data in external_deps.items():
                dep_el = ET.SubElement(external_el, 'package')
                dep_el.text = dep_name
                if dep_data.get('purpose'):
                    dep_el.set('purpose', dep_data['purpose'])

        # TASKS section - executable tasks derived from operations
        tasks_el = ET.SubElement(root, 'tasks')

        # Generate tasks from operations (all_components gathered earlier)
        if all_components:
            # Also gather components from context section
            if not all_components and 'action' in dep_by_type:
                # Traverse actions to find components
                for action_id in dep_by_type['action']:
                    action_comps = [d for d in self.deps.get_dependencies(action_id) if d.startswith('component:')]
                    all_components.extend(action_comps)

            # Add components to context if we found them via traversal
            if all_components and 'component' not in dep_by_type:
                components_el = ET.SubElement(context_el, 'components')
                for comp_id in set(all_components):  # Use set to deduplicate
                    comp_data = self.entities.get_entity(comp_id)
                    if comp_data:
                        comp_el = ET.SubElement(components_el, 'component', id=comp_id.split(':', 1)[1])
                        ET.SubElement(comp_el, 'name').text = comp_data.get('name', comp_id)
                        ET.SubElement(comp_el, 'description').text = comp_data.get('description', '')

            wave = 1
            for comp_id in set(all_components):  # Use set to deduplicate
                operations = self._get_component_operations(comp_id)
                comp_data = self.entities.get_entity(comp_id)
                comp_file = self._get_component_file(comp_id)

                for op_id in operations:
                    op_data = self.entities.get_entity(op_id)
                    if op_data:
                        task_id = f"task-{wave}"
                        task_el = ET.SubElement(tasks_el, 'task',
                                              id=task_id,
                                              type='checkpoint:human-verify',
                                              wave=str(wave))

                        ET.SubElement(task_el, 'operation').text = op_id
                        ET.SubElement(task_el, 'name').text = op_data.get('name', op_id)

                        # Files - look up from code-graph via product-component
                        files_el = ET.SubElement(task_el, 'files')
                        file_path = None

                        if code_graph and comp_data:
                            # Look up module for this component
                            file_path = self._get_file_path_from_code_graph(
                                comp_id, code_graph
                            )

                        if not file_path and comp_file:
                            file_path = comp_file

                        if file_path:
                            ET.SubElement(files_el, 'file').text = file_path
                        else:
                            files_el.append(ET.Comment(' File path to be determined '))

                        # Action - detailed HOW
                        action_text = f"""Implement {op_data.get('name', 'operation')}:

Component: {comp_data.get('name', comp_id) if comp_data else comp_id}
{comp_data.get('description', '') if comp_data else ''}

Operation: {op_data.get('description', '')}

TODO: Add specific implementation guidance with library choices and constraints.
"""
                        ET.SubElement(task_el, 'action').text = action_text

                        # Verify
                        verify_el = ET.SubElement(task_el, 'verify')
                        ET.SubElement(verify_el, 'test').text = '# TODO: Add test command'
                        ET.SubElement(verify_el, 'assertion').text = '# TODO: Add expected outcome'

                        # Done
                        done_text = f"{op_data.get('name', 'Operation')} implemented and verified.\nCHECKPOINT: Human reviews implementation."
                        ET.SubElement(task_el, 'done').text = done_text

                        wave += 1

        # Pretty print XML
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent='  ')

    def generate_interface_spec(self, interface_id: str) -> str:
        """
        Generate a UI interface specification.

        Args:
            interface_id: Interface entity ID

        Returns:
            Markdown formatted interface spec
        """
        entity_data = self.entities.get_entity(interface_id)
        if not entity_data:
            return f"# Error: Interface {interface_id} not found\n"

        lines = []
        lines.append(f"# Interface: {entity_data.get('name', interface_id)}")
        lines.append("")

        # Description
        lines.append("## Description")
        lines.append("")
        lines.append(entity_data.get('description', 'No description provided'))
        lines.append("")

        # Features on this interface
        dependents = self.deps.get_dependents(interface_id)
        features = [d for d in dependents if d.startswith('feature:')]

        if features:
            lines.append("## Features")
            lines.append("")
            for feature_id in features:
                feature_data = self.entities.get_entity(feature_id)
                if feature_data:
                    lines.append(f"### {feature_data.get('name', feature_id)}")
                    lines.append("")
                    lines.append(feature_data.get('description', ''))
                    lines.append("")

        # Layout and styling
        dependencies = self.deps.get_dependencies(interface_id)
        layout_refs = [d for d in dependencies if any(d.startswith(f"{t}:") for t in ['layouts', 'styles', 'patterns'])]

        if layout_refs:
            lines.append("## Layout & Styling")
            lines.append("")
            for ref_id in layout_refs:
                ref_data = self._get_reference_data(ref_id)
                if ref_data:
                    lines.append(f"### {ref_id}")
                    lines.append("```")
                    lines.append(str(ref_data))
                    lines.append("```")
                    lines.append("")

        # Filter out any None values
        return "\n".join(str(line) if line is not None else '' for line in lines)

    def generate_component_spec(self, component_id: str) -> str:
        """
        Generate a component specification.

        Args:
            component_id: Component entity ID

        Returns:
            Markdown formatted component spec
        """
        entity_data = self.entities.get_entity(component_id)
        if not entity_data:
            return f"# Error: Component {component_id} not found\n"

        lines = []
        lines.append(f"# Component: {entity_data.get('name', component_id)}")
        lines.append("")

        # Description
        lines.append("## Description")
        lines.append("")
        lines.append(entity_data.get('description', 'No description provided'))
        lines.append("")

        # Dependencies breakdown
        dependencies = self.deps.get_dependencies(component_id)

        # Group by type
        presentation = [d for d in dependencies if d.startswith('presentation:')]
        behavior = [d for d in dependencies if d.startswith('behavior:')]
        data_models = [d for d in dependencies if d.startswith('data-model:')]

        # Presentation
        if presentation:
            lines.append("## Presentation")
            lines.append("")
            for pres_id in presentation:
                pres_data = self.entities.get_entity(pres_id)
                if pres_data:
                    lines.append(f"- **{pres_data.get('name', pres_id)}**: {pres_data.get('description', '')}")
            lines.append("")

        # Behavior
        if behavior:
            lines.append("## Behavior")
            lines.append("")
            for beh_id in behavior:
                beh_data = self.entities.get_entity(beh_id)
                if beh_data:
                    lines.append(f"### {beh_data.get('name', beh_id)}")
                    lines.append("")
                    lines.append(beh_data.get('description', ''))
                    lines.append("")

        # Data Models
        if data_models:
            lines.append("## Data Models")
            lines.append("")
            for model_id in data_models:
                model_data = self.entities.get_entity(model_id)
                if model_data:
                    lines.append(f"### {model_data.get('name', model_id)}")
                    lines.append("")
                    lines.append(model_data.get('description', ''))
                    lines.append("")

        # Filter out any None values
        return "\n".join(str(line) if line is not None else '' for line in lines)

    def generate_dependency_report(self, entity_id: Optional[str] = None) -> str:
        """
        Generate a dependency report for an entity or the whole graph.

        Args:
            entity_id: Optional entity ID to focus on

        Returns:
            Markdown formatted dependency report
        """
        lines = []

        if entity_id:
            entity_data = self.entities.get_entity(entity_id)
            name = entity_data.get('name', entity_id) if entity_data else entity_id

            lines.append(f"# Dependency Report: {name}")
            lines.append("")

            # Direct dependencies
            deps = self.deps.get_dependencies(entity_id)
            if deps:
                lines.append("## Direct Dependencies")
                lines.append("")
                for dep in deps:
                    dep_data = self.entities.get_entity(dep)
                    dep_name = dep_data.get('name', dep) if dep_data else dep
                    lines.append(f"- `{dep}` - {dep_name}")
                lines.append("")

            # Dependents
            dependents = self.deps.get_dependents(entity_id)
            if dependents:
                lines.append("## Direct Dependents")
                lines.append("")
                for dep in dependents:
                    dep_data = self.entities.get_entity(dep)
                    dep_name = dep_data.get('name', dep) if dep_data else dep
                    lines.append(f"- `{dep}` - {dep_name}")
                lines.append("")

            # Full chain
            chain = self.deps.resolve_chain(entity_id)
            if len(chain) > 1:
                lines.append("## Full Dependency Chain")
                lines.append("")
                lines.append(" → ".join(chain))
                lines.append("")

        else:
            # Whole graph report
            lines.append("# Dependency Report: Full Graph")
            lines.append("")

            # Check for cycles
            cycles = self.deps.detect_cycles()
            if cycles:
                lines.append("## ⚠️ Circular Dependencies Detected")
                lines.append("")
                for cycle in cycles:
                    lines.append(f"- {' → '.join(cycle)}")
                lines.append("")

            # Topological sort
            sorted_entities = self.deps.topological_sort()
            lines.append("## Build Order")
            lines.append("")
            lines.append("Entities in dependency order:")
            lines.append("")
            for i, entity in enumerate(sorted_entities, 1):
                lines.append(f"{i}. `{entity}`")
            lines.append("")

        # Filter out any None values
        return "\n".join(str(line) if line is not None else '' for line in lines)

    def _get_reference_data(self, reference_id: str) -> Optional[Any]:
        """Get reference data from the graph."""
        data = self.graph.get_graph()
        references = data.get('references', {})

        if ':' not in reference_id:
            return None

        ref_type, ref_name = reference_id.split(':', 1)
        return references.get(ref_type, {}).get(ref_name)

    def _get_file_path_from_code_graph(self, component_id: str, code_graph: dict) -> str:
        """
        Look up file path for a component via code-graph product-component refs.

        Args:
            component_id: Component entity ID (e.g., "component:spec-generator")
            code_graph: Loaded code-graph dictionary

        Returns:
            File path string or empty string if not found
        """
        # Get component name without prefix
        comp_name = component_id.split(':', 1)[1] if ':' in component_id else component_id

        # Look through product-component references
        product_components = code_graph.get('references', {}).get('product-component', {})

        for module_name, ref_data in product_components.items():
            ref_component = ref_data.get('component', '')
            if ref_component == component_id:
                # Found module that maps to this component
                # Look up module entity for file path
                module_entity = code_graph.get('entities', {}).get('module', {}).get(module_name)
                if module_entity:
                    return module_entity.get('file_path', '')

        return ''

    def _get_external_deps_for_components(self, component_ids: List[str], code_graph: dict) -> Dict[str, Any]:
        """
        Get external dependencies for components via code-graph.

        Args:
            component_ids: List of component entity IDs
            code_graph: Loaded code-graph dictionary

        Returns:
            Dictionary of external dependencies {dep_name: dep_data}
        """
        external_deps = {}
        product_components = code_graph.get('references', {}).get('product-component', {})
        all_external_deps = code_graph.get('references', {}).get('external-dep', {})

        # Find modules for these components
        module_names = []
        for comp_id in component_ids:
            for module_name, ref_data in product_components.items():
                if ref_data.get('component') == comp_id:
                    module_names.append(module_name)

        # Get external deps for these modules from graph
        for module_name in module_names:
            module_key = f"module:{module_name}"
            module_deps = code_graph.get('graph', {}).get(module_key, {}).get('depends_on', [])

            for dep in module_deps:
                if dep.startswith('external-dep:'):
                    dep_name = dep.split(':', 1)[1]
                    if dep_name in all_external_deps:
                        external_deps[dep_name] = all_external_deps[dep_name]

        return external_deps

    def _get_feature_spec_meta(self, feature_name: str) -> dict:
        """
        Query meta.feature_specs for a feature.

        Args:
            feature_name: Feature name (without 'feature:' prefix)

        Returns:
            Dictionary of feature metadata, or empty dict if not found
        """
        data = self.graph.get_graph()
        feature_specs = data.get('meta', {}).get('feature_specs', {})
        return feature_specs.get(feature_name, {})

    def _render_data_model_typescript(self, model_data: dict, model_name: str) -> str:
        """
        Convert data-model reference to TypeScript interface.

        Args:
            model_data: Data model reference data
            model_name: Name for the interface

        Returns:
            TypeScript interface definition as string
        """
        if not isinstance(model_data, dict):
            return str(model_data)

        language = model_data.get('language', '')
        schema = model_data.get('schema', {})

        if language != 'typescript' or not schema:
            return str(model_data)

        # Build TypeScript interface
        lines = []
        interface_name = model_data.get('name', model_name)
        lines.append(f"interface {interface_name} {{")

        for field_name, field_type in schema.items():
            lines.append(f"  {field_name}: {field_type};")

        lines.append("}")

        return "\n".join(lines)

    def _render_signature(self, sig_data: dict) -> str:
        """
        Convert signature reference to readable function signature.

        Args:
            sig_data: Signature reference data

        Returns:
            Formatted function signature string
        """
        if not isinstance(sig_data, dict):
            return str(sig_data)

        func_name = sig_data.get('name', 'unknownFunction')
        params = sig_data.get('params', [])
        returns = sig_data.get('returns', 'void')

        # Format parameters
        param_strs = []
        for param in params:
            if isinstance(param, dict):
                param_name = param.get('name', 'arg')
                param_type = param.get('type', 'any')
                optional = param.get('optional', False)

                if optional:
                    param_strs.append(f"{param_name}?: {param_type}")
                else:
                    param_strs.append(f"{param_name}: {param_type}")
            else:
                param_strs.append(str(param))

        params_formatted = ", ".join(param_strs)

        return f"function {func_name}({params_formatted}): {returns}"

    def _get_component_operations(self, component_id: str) -> List[str]:
        """
        Query graph for operation entities linked to component.

        Args:
            component_id: Component entity ID (e.g., 'component:auth')

        Returns:
            List of operation IDs (e.g., ['operation:login', 'operation:logout'])
        """
        # Get dependencies of the component
        dependencies = self.deps.get_dependencies(component_id)

        # Filter for operation entities
        operations = [dep for dep in dependencies if dep.startswith('operation:')]

        return operations

    def _get_component_file(self, component_id: str) -> str:
        """
        Query source-file reference for component.

        Args:
            component_id: Component entity ID

        Returns:
            File path from source-file reference, or empty string if not found
        """
        # Get dependencies of the component
        dependencies = self.deps.get_dependencies(component_id)

        # Find source-file reference
        for dep in dependencies:
            if dep.startswith('source-file:'):
                ref_data = self._get_reference_data(dep)
                if ref_data and isinstance(ref_data, dict):
                    return ref_data.get('path', '')

        return ''

    def generate_sitemap(self) -> str:
        """
        Generate a sitemap of all interfaces.

        Returns:
            Markdown formatted sitemap
        """
        lines = []
        lines.append("# Sitemap")
        lines.append("")

        # Get all interfaces
        data = self.graph.load()
        interfaces = data.get('entities', {}).get('interface', {})

        for interface_name, interface_data in interfaces.items():
            interface_id = f"interface:{interface_name}"
            name = interface_data.get('name', interface_name)
            desc = interface_data.get('description', '')

            lines.append(f"## {name}")
            lines.append("")
            lines.append(desc)
            lines.append("")

            # Get features on this interface
            dependents = self.deps.get_dependents(interface_id)
            features = [d for d in dependents if d.startswith('feature:')]

            if features:
                lines.append("**Features:**")
                lines.append("")
                for feature_id in features:
                    feature_data = self.entities.get_entity(feature_id)
                    if feature_data:
                        lines.append(f"- {feature_data.get('name', feature_id)}")
                lines.append("")

        # Filter out any None values
        return "\n".join(str(line) if line is not None else '' for line in lines)

    def generate_user_flow(self, user_id: str) -> str:
        """
        Generate user flow documentation.

        Args:
            user_id: User entity ID

        Returns:
            Markdown formatted user flow
        """
        entity_data = self.entities.get_entity(user_id)
        if not entity_data:
            return f"# Error: User {user_id} not found\n"

        lines = []
        lines.append(f"# User Flow: {entity_data.get('name', user_id)}")
        lines.append("")

        # Description
        lines.append("## User Profile")
        lines.append("")
        lines.append(entity_data.get('description', 'No description provided'))
        lines.append("")

        # Objectives
        dependencies = self.deps.get_dependencies(user_id)
        objectives = [d for d in dependencies if d.startswith('objective:')]

        if objectives:
            lines.append("## Objectives")
            lines.append("")
            for obj_id in objectives:
                obj_data = self.entities.get_entity(obj_id)
                if obj_data:
                    lines.append(f"### {obj_data.get('name', obj_id)}")
                    lines.append("")
                    lines.append(obj_data.get('description', ''))
                    lines.append("")

                    # Actions for this objective
                    obj_deps = self.deps.get_dependencies(obj_id)
                    actions = [d for d in obj_deps if d.startswith('action:')]

                    if actions:
                        lines.append("**Actions:**")
                        lines.append("")
                        for action_id in actions:
                            action_data = self.entities.get_entity(action_id)
                            if action_data:
                                lines.append(f"- {action_data.get('name', action_id)}: {action_data.get('description', '')}")
                        lines.append("")

        # Filter out any None values
        return "\n".join(str(line) if line is not None else '' for line in lines)
