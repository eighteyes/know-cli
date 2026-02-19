#!/usr/bin/env python3
"""
Quick demo of graph visualization using Mermaid.
Usage: python scripts/viz-demo.py .ai/know/spec-graph.json
"""

import json
import sys
from pathlib import Path


def generate_mermaid(graph_path, entity_types=None, max_nodes=50):
    """Generate Mermaid diagram from graph."""

    with open(graph_path, 'r') as f:
        graph_data = json.load(f)

    output = ["flowchart TD"]

    # Get entities
    entities_section = graph_data.get('entities', {})
    graph_section = graph_data.get('graph', {})

    # Add nodes (limited to avoid overwhelming diagram)
    node_count = 0
    entity_ids = []

    for entity_type, entities in entities_section.items():
        if entity_types and entity_type not in entity_types:
            continue

        for name, data in entities.items():
            if node_count >= max_nodes:
                break

            entity_id = f"{entity_type}:{name}"
            entity_ids.append(entity_id)

            clean_id = entity_id.replace(':', '_').replace('-', '_')
            display_name = data.get('name', name)

            # Truncate long names
            if len(display_name) > 30:
                display_name = display_name[:27] + "..."

            # Add node with styling
            output.append(f'    {clean_id}["{display_name}"]')
            output.append(f'    class {clean_id} {entity_type}Class')

            node_count += 1

    # Add edges
    for from_id in entity_ids:
        if from_id in graph_section:
            deps = graph_section[from_id].get('depends_on', [])
            for to_id in deps:
                if to_id in entity_ids:
                    clean_from = from_id.replace(':', '_').replace('-', '_')
                    clean_to = to_id.replace(':', '_').replace('-', '_')
                    output.append(f'    {clean_from} --> {clean_to}')

    # Add styling
    output.extend([
        "",
        "    %% Styling",
        "    classDef featureClass fill:#e1f5ff,stroke:#0288d1,stroke-width:2px,color:#000",
        "    classDef actionClass fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000",
        "    classDef componentClass fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000",
        "    classDef userClass fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#000",
        "    classDef objectiveClass fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000",
        "    classDef requirementClass fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000",
        "    classDef interfaceClass fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#000",
        "    classDef operationClass fill:#f1f8e9,stroke:#558b2f,stroke-width:2px,color:#000"
    ])

    return "\n".join(output)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/viz-demo.py <graph-path> [entity-types]")
        print("Example: python scripts/viz-demo.py .ai/know/spec-graph.json feature,action")
        sys.exit(1)

    graph_path = sys.argv[1]
    entity_types = sys.argv[2].split(',') if len(sys.argv) > 2 else None

    mermaid = generate_mermaid(graph_path, entity_types)
    print(mermaid)

    # Save to file
    output_path = Path(graph_path).parent / 'graph-viz.mmd'
    with open(output_path, 'w') as f:
        f.write(mermaid)

    print(f"\n✓ Saved to {output_path}", file=sys.stderr)
    print(f"\nView at: https://mermaid.live/edit or paste into GitHub/VSCode", file=sys.stderr)
