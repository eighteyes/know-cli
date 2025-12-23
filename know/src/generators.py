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
        Generate a specification for an entity.

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

        # Description
        if entity_data.get('description'):
            lines.append("## Description")
            lines.append("")
            lines.append(entity_data['description'])
            lines.append("")

        # Dependencies
        if include_deps:
            dependencies = self.deps.get_dependencies(entity_id)
            if dependencies:
                lines.append("## Dependencies")
                lines.append("")
                for dep in dependencies:
                    dep_data = self.entities.get_entity(dep)
                    if dep_data:
                        dep_name = dep_data.get('name', dep)
                        lines.append(f"- `{dep}` - {dep_name}")
                    else:
                        lines.append(f"- `{dep}`")
                lines.append("")

            # Dependents
            dependents = self.deps.get_dependents(entity_id)
            if dependents:
                lines.append("## Used By")
                lines.append("")
                for dep in dependents:
                    dep_data = self.entities.get_entity(dep)
                    if dep_data:
                        dep_name = dep_data.get('name', dep)
                        lines.append(f"- `{dep}` - {dep_name}")
                    else:
                        lines.append(f"- `{dep}`")
                lines.append("")

        # Filter out any None values
        return "\n".join(str(line) if line is not None else '' for line in lines)

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
        if 'business_logic' in dep_by_type:
            lines.append("## Business Logic")
            lines.append("")
            for ref_id in dep_by_type['business_logic']:
                ref_data = self._get_reference_data(ref_id)
                if ref_data is not None:
                    lines.append(f"### {ref_id}")
                    lines.append("```")
                    lines.append(str(ref_data))
                    lines.append("```")
                    lines.append("")

        # Other reference types (acceptance_criteria, api_contract, validation_rule)
        ref_types = ['acceptance_criteria', 'api_contract', 'validation_rule']
        for ref_type in ref_types:
            if ref_type in dep_by_type:
                lines.append(f"## {ref_type.replace('_', ' ').title()}")
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
