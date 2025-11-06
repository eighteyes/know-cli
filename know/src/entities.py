"""
Entity CRUD operations for graph management
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from .graph import GraphManager


class EntityManager:
    """Manages entity operations in the graph"""

    def __init__(self, graph_manager: GraphManager, rules_path: Optional[str] = None):
        self.graph = graph_manager

        # Load dependency rules to get valid entity types
        if rules_path is None:
            rules_path = Path(__file__).parent.parent / "config" / "dependency-rules.json"

        with open(rules_path, 'r') as f:
            self.rules = json.load(f)

        # Extract valid entity types from entity_description
        self.VALID_ENTITY_TYPES = set(self.rules.get('entity_description', {}).keys())

        # Extract required fields and allowed metadata from entity_note
        entity_note = self.rules.get('entity_note', {})
        self.REQUIRED_FIELDS = {'name', 'description'}
        self.ALLOWED_METADATA = set(entity_note.get('allowed_metadata', []))

    def list_entities(self, entity_type: Optional[str] = None) -> List[str]:
        """List all entities or entities of a specific type"""
        entities = self.graph.get_entities()

        if not entity_type:
            # Return all entities
            result = []
            for category, items in entities.items():
                if isinstance(items, dict):
                    for key in items.keys():
                        result.append(f"{category}:{key}")
            return sorted(result)

        # Return entities of specific type
        if entity_type in entities and isinstance(entities[entity_type], dict):
            return [f"{entity_type}:{key}" for key in entities[entity_type].keys()]

        return []

    def get_entity(self, entity_path: str) -> Optional[Dict[str, Any]]:
        """Get a specific entity by path (e.g., 'user:owner')"""
        parts = entity_path.split(':', 1)
        if len(parts) != 2:
            return None

        entity_type, entity_key = parts
        entities = self.graph.get_entities()

        if entity_type in entities and isinstance(entities[entity_type], dict):
            return entities[entity_type].get(entity_key)

        return None

    def validate_entity(self, entity_type: str, entity_key: str,
                       entity_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate entity before adding/updating.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check entity type is not empty
        if not entity_type or not entity_type.strip():
            return False, "Entity type cannot be empty"

        # Check entity key is not empty
        if not entity_key or not entity_key.strip():
            return False, "Entity key cannot be empty"

        # Check entity type is valid
        if entity_type not in self.VALID_ENTITY_TYPES:
            valid_types = ', '.join(sorted(self.VALID_ENTITY_TYPES))
            return False, f"Invalid entity type '{entity_type}'. Valid types: {valid_types}"

        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(entity_data.keys())
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        # Check required fields are not empty
        for field in self.REQUIRED_FIELDS:
            value = entity_data.get(field, '')
            if not value or (isinstance(value, str) and not value.strip()):
                return False, f"Field '{field}' cannot be empty"

        return True, None

    def add_entity(self, entity_type: str, entity_key: str,
                   entity_data: Dict[str, Any],
                   skip_validation: bool = False) -> tuple[bool, Optional[str]]:
        """
        Add a new entity.

        Returns:
            Tuple of (success, error_message)
        """
        # Validate entity unless explicitly skipped
        if not skip_validation:
            is_valid, error = self.validate_entity(entity_type, entity_key, entity_data)
            if not is_valid:
                return False, error

        graph_data = self.graph.get_graph()

        # Initialize entities section if needed
        if "entities" not in graph_data:
            graph_data["entities"] = {}

        # Initialize entity type if needed
        if entity_type not in graph_data["entities"]:
            graph_data["entities"][entity_type] = {}

        # Check if entity already exists
        if entity_key in graph_data["entities"][entity_type]:
            return False, f"Entity '{entity_type}:{entity_key}' already exists"

        # Add the entity
        graph_data["entities"][entity_type][entity_key] = entity_data

        # Save the graph
        success = self.graph.save_graph(graph_data)
        return success, None if success else "Failed to save graph"

    def update_entity(self, entity_path: str,
                      entity_data: Dict[str, Any]) -> bool:
        """Update an existing entity"""
        parts = entity_path.split(':', 1)
        if len(parts) != 2:
            return False

        entity_type, entity_key = parts
        graph_data = self.graph.get_graph()

        # Check if entity exists
        if (entity_type not in graph_data.get("entities", {}) or
            entity_key not in graph_data["entities"].get(entity_type, {})):
            return False

        # Update the entity
        graph_data["entities"][entity_type][entity_key] = entity_data

        # Save the graph
        return self.graph.save_graph(graph_data)

    def delete_entity(self, entity_path: str,
                      force: bool = False) -> bool:
        """Delete an entity (checks for dependencies unless force=True)"""
        parts = entity_path.split(':', 1)
        if len(parts) != 2:
            return False

        entity_type, entity_key = parts

        # Check for dependents unless forced
        if not force:
            dependents = self.graph.find_dependents(entity_path)
            if dependents:
                print(f"Entity {entity_path} has dependents: {dependents}")
                return False

        graph_data = self.graph.get_graph()

        # Check if entity exists
        if (entity_type not in graph_data.get("entities", {}) or
            entity_key not in graph_data["entities"].get(entity_type, {})):
            return False

        # Delete the entity
        del graph_data["entities"][entity_type][entity_key]

        # Clean up empty entity type
        if not graph_data["entities"][entity_type]:
            del graph_data["entities"][entity_type]

        # Remove from dependency graph
        if entity_path in graph_data.get("graph", {}):
            del graph_data["graph"][entity_path]

        # Remove references to this entity in other dependencies
        for node, deps in graph_data.get("graph", {}).items():
            if isinstance(deps, dict) and "depends_on" in deps:
                if isinstance(deps["depends_on"], list):
                    deps["depends_on"] = [d for d in deps["depends_on"]
                                          if d != entity_path]

        # Save the graph
        return self.graph.save_graph(graph_data)

    def add_dependency(self, from_entity: str, to_entity: str) -> bool:
        """Add a dependency between entities"""
        graph_data = self.graph.get_graph()

        # Initialize graph section if needed
        if "graph" not in graph_data:
            graph_data["graph"] = {}

        # Initialize entity in graph if needed
        if from_entity not in graph_data["graph"]:
            graph_data["graph"][from_entity] = {"depends_on": []}
        elif "depends_on" not in graph_data["graph"][from_entity]:
            graph_data["graph"][from_entity]["depends_on"] = []

        # Check if dependency already exists
        if to_entity in graph_data["graph"][from_entity]["depends_on"]:
            return False

        # Add the dependency
        graph_data["graph"][from_entity]["depends_on"].append(to_entity)

        # Save the graph
        return self.graph.save_graph(graph_data)

    def remove_dependency(self, from_entity: str, to_entity: str) -> bool:
        """Remove a dependency between entities"""
        graph_data = self.graph.get_graph()

        # Check if the dependency exists
        if (from_entity not in graph_data.get("graph", {}) or
            "depends_on" not in graph_data["graph"][from_entity]):
            return False

        deps = graph_data["graph"][from_entity]["depends_on"]
        if to_entity not in deps:
            return False

        # Remove the dependency
        deps.remove(to_entity)

        # Clean up if no dependencies left
        if not deps:
            del graph_data["graph"][from_entity]["depends_on"]
            if not graph_data["graph"][from_entity]:
                del graph_data["graph"][from_entity]

        # Save the graph
        return self.graph.save_graph(graph_data)

    def get_entity_stats(self) -> Dict[str, int]:
        """Get statistics about entities"""
        entities = self.graph.get_entities()
        stats = {
            "total": 0,
            "by_type": {}
        }

        for entity_type, items in entities.items():
            if isinstance(items, dict):
                count = len(items)
                stats["total"] += count
                stats["by_type"][entity_type] = count

        return stats