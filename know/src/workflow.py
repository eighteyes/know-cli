"""
Workflow Management Module

Name: workflow.py
Description: Manages workflow entities with ordered action dependencies
Responsibilities:
- CRUD operations for workflow entities
- Ordered dependency management (depends_on_ordered)
- Position-based insertion (--after, --position)
- Auto-creation of missing actions with minimal data
"""

from typing import List, Tuple, Optional, Dict, Any


class WorkflowManager:
    """Manages workflow entities with ordered action dependencies"""

    def __init__(self, graph_manager, entity_manager):
        """
        Initialize WorkflowManager

        Args:
            graph_manager: GraphManager instance for graph operations
            entity_manager: EntityManager instance for entity CRUD
        """
        self.graph = graph_manager
        self.entities = entity_manager

    def add_workflow(self, workflow_key: str, name: str, description: str) -> Tuple[bool, Optional[str]]:
        """
        Add a new workflow entity

        Args:
            workflow_key: Unique key for workflow
            name: Display name
            description: Workflow description

        Returns:
            Tuple of (success, error_message)
        """
        return self.entities.add_entity(
            "workflow",
            workflow_key,
            {"name": name, "description": description}
        )

    def link_actions(
        self,
        workflow_id: str,
        action_ids: List[str],
        position: Optional[int] = None,
        after_action: Optional[str] = None,
        auto_create: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Link actions to workflow in order

        Args:
            workflow_id: Workflow entity ID (e.g., 'workflow:onboarding')
            action_ids: List of action IDs to link
            position: Insert at this index (0-based)
            after_action: Insert after this action ID
            auto_create: Auto-create missing actions with minimal data

        Returns:
            Tuple of (success, error messages)
        """
        errors = []
        graph_data = self.graph.get_graph()

        # Auto-create missing actions if enabled
        if auto_create:
            missing_actions = []
            for action_id in action_ids:
                if ':' not in action_id or not action_id.startswith('action:'):
                    errors.append(f"Invalid action ID format: {action_id}")
                    continue

                entity_data = self.entities.get_entity(action_id)
                if not entity_data:
                    action_key = action_id.split(':', 1)[1]
                    missing_actions.append((
                        "action",
                        action_key,
                        {
                            "name": action_key.replace('-', ' ').title(),
                            "description": f"Action for {workflow_id}"
                        }
                    ))

            if missing_actions:
                success, batch_errors = self.entities.add_entities_batch(missing_actions, auto_create_missing=True)
                if not success:
                    errors.extend(batch_errors)
                    return False, errors

        # Get current ordered dependencies
        if "graph" not in graph_data:
            graph_data["graph"] = {}

        if workflow_id not in graph_data["graph"]:
            graph_data["graph"][workflow_id] = {}

        workflow_node = graph_data["graph"][workflow_id]
        current_ordered = workflow_node.get("depends_on_ordered", [])

        # Determine insertion point
        if position is not None:
            insert_idx = max(0, min(position, len(current_ordered)))
        elif after_action is not None:
            try:
                insert_idx = current_ordered.index(after_action) + 1
            except ValueError:
                errors.append(f"Action {after_action} not found in workflow")
                return False, errors
        else:
            insert_idx = len(current_ordered)

        # Insert actions
        new_ordered = current_ordered[:insert_idx] + list(action_ids) + current_ordered[insert_idx:]

        # Update graph
        workflow_node["depends_on_ordered"] = new_ordered

        success = self.graph.save_graph(graph_data)
        return success, [] if success else ["Failed to save graph"]

    def unlink_actions(self, workflow_id: str, action_ids: List[str]) -> Tuple[bool, List[str]]:
        """
        Remove actions from workflow

        Args:
            workflow_id: Workflow entity ID
            action_ids: List of action IDs to remove

        Returns:
            Tuple of (success, error messages)
        """
        graph_data = self.graph.get_graph()

        if workflow_id not in graph_data.get("graph", {}):
            return False, [f"Workflow {workflow_id} not found"]

        workflow_node = graph_data["graph"][workflow_id]
        current_ordered = workflow_node.get("depends_on_ordered", [])
        new_ordered = [a for a in current_ordered if a not in action_ids]

        if not new_ordered:
            # Remove depends_on_ordered if empty
            del workflow_node["depends_on_ordered"]
            if not workflow_node:
                del graph_data["graph"][workflow_id]
        else:
            workflow_node["depends_on_ordered"] = new_ordered

        success = self.graph.save_graph(graph_data)
        return success, [] if success else ["Failed to save graph"]

    def get_ordered_actions(self, workflow_id: str) -> List[str]:
        """
        Get ordered list of actions for a workflow

        Args:
            workflow_id: Workflow entity ID

        Returns:
            List of action IDs in order
        """
        graph_data = self.graph.get_graph()

        if workflow_id not in graph_data.get("graph", {}):
            return []

        workflow_node = graph_data["graph"][workflow_id]
        return workflow_node.get("depends_on_ordered", [])

    def delete_workflow(self, workflow_id: str, confirmed: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Delete workflow with confirmation

        Args:
            workflow_id: Workflow entity ID
            confirmed: Whether deletion is confirmed

        Returns:
            Tuple of (success, error_message)
        """
        if not confirmed:
            return False, "Deletion requires -y flag for confirmation"

        return self.entities.delete_entity(workflow_id, force=True), None
