#!/bin/bash

# Generate visual representations of the dependency graph in multiple formats
# Usage: ./scripts/graph-visualizer.sh [knowledge-map.json] [-f format] [-o output-file]
# Formats: dot, ascii, mermaid, svg, png (requires graphviz for svg/png)

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
🎨 Graph Visualizer - Multi-format Dependency Visualization

USAGE:
    ./scripts/graph-visualizer.sh [knowledge-map.json] [-f format] [-o output-file]
    ./scripts/graph-visualizer.sh -h|--help

DESCRIPTION:
    Generates visual representations of dependency graphs in multiple formats

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: spec-graph.json)

OPTIONS:
    -f, --format FORMAT   Output format (default: ascii)
    -o, --output FILE     Output file path (auto-generated if not specified)
    -h, --help           Show this help message

FORMATS:
    ascii     ASCII tree visualization (console output)
    dot       Graphviz DOT format for further processing
    mermaid   Mermaid diagram format for web rendering
    svg       SVG image format (requires graphviz)
    png       PNG image format (requires graphviz)
    stats     Visualization statistics and recommendations

EXAMPLES:
    ./scripts/graph-visualizer.sh                                    # ASCII to console
    ./scripts/graph-visualizer.sh -f dot                             # DOT format to knowledge-map-cmd.dot
    ./scripts/graph-visualizer.sh knowledge-map.json -f mermaid      # Mermaid to knowledge-map.mmd
    ./scripts/graph-visualizer.sh -f svg -o custom.svg               # SVG to custom.svg
    ./scripts/graph-visualizer.sh knowledge-map.json -f stats        # Statistics

DEPENDENCIES:
    For SVG/PNG: graphviz (brew install graphviz)

OUTPUT:
    Visual representation with color-coded nodes based on dependency patterns
EOF
}

# Parse command line arguments
KNOWLEDGE_MAP=""
FORMAT="ascii"
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -*)
            echo "❌ Unknown option: $1"
            echo "💡 Use -h for help"
            exit 1
            ;;
        *)
            if [[ -z "$KNOWLEDGE_MAP" ]]; then
                KNOWLEDGE_MAP="$1"
            else
                echo "❌ Too many arguments: $1"
                echo "💡 Use -h for help"
                exit 1
            fi
            shift
            ;;
    esac
done

# Set default knowledge map if not provided
KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-spec-graph.json}"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    echo "💡 Use -h for help"
    exit 1
fi

# Set default output file based on format if not provided
if [[ -z "$OUTPUT_FILE" ]]; then
    BASENAME=$(basename "$KNOWLEDGE_MAP" .json)
    case "$FORMAT" in
        dot) OUTPUT_FILE="${BASENAME}.dot" ;;
        mermaid) OUTPUT_FILE="${BASENAME}.mmd" ;;
        svg) OUTPUT_FILE="${BASENAME}.svg" ;;
        png) OUTPUT_FILE="${BASENAME}.png" ;;
        ascii) OUTPUT_FILE="" ;;  # ASCII goes to stdout
        *) OUTPUT_FILE="${BASENAME}.${FORMAT}" ;;
    esac
fi

echo "🎨 GRAPH VISUALIZER: $KNOWLEDGE_MAP"
echo "📊 Format: $FORMAT"
[[ -n "$OUTPUT_FILE" ]] && echo "📁 Output: $OUTPUT_FILE"
echo "=" | tr '=' '=' | head -c 50
echo

case "$FORMAT" in
    "dot")
        echo "🔗 Generating DOT format..."
        
        # Use centralized patterns
        DOT_NODES=$(apply_pattern "graph_visualization" "dot_nodes" "$KNOWLEDGE_MAP")
        DOT_EDGES=$(apply_pattern "graph_visualization" "dot_edges" "$KNOWLEDGE_MAP")
        
        DOT_CONTENT="digraph DependencyGraph {
  rankdir=TB;
  node [shape=box, style=rounded,filled,fillcolor=lightblue];
  edge [color=darkblue];

$DOT_NODES

$DOT_EDGES

}"
        
        if [[ -n "$OUTPUT_FILE" ]]; then
            echo "$DOT_CONTENT" > "$OUTPUT_FILE"
            echo "✅ DOT file generated: $OUTPUT_FILE"
            echo "💡 To render: dot -Tsvg $OUTPUT_FILE -o ${OUTPUT_FILE%.dot}.svg"
        else
            echo "$DOT_CONTENT"
        fi
        ;;
        
    "mermaid")
        echo "🧜‍♀️ Generating Mermaid format..."
        
        # Use centralized patterns
        MERMAID_NODES=$(apply_pattern "graph_visualization" "mermaid_nodes" "$KNOWLEDGE_MAP")
        MERMAID_EDGES=$(apply_pattern "graph_visualization" "mermaid_edges" "$KNOWLEDGE_MAP")
        
        MERMAID_CONTENT="graph TD
$MERMAID_NODES

$MERMAID_EDGES

  classDef root fill:#90EE90,stroke:#2e7d32
  classDef leaf fill:#FFB6C1,stroke:#c62828
  classDef critical fill:#FFA500,stroke:#ef6c00
  classDef complex fill:#FFFF99,stroke:#f57f17"
        
        if [[ -n "$OUTPUT_FILE" ]]; then
            echo "$MERMAID_CONTENT" > "$OUTPUT_FILE"
            echo "✅ Mermaid file generated: $OUTPUT_FILE"
            echo "💡 View online: https://mermaid.live/"
        else
            echo "$MERMAID_CONTENT"
        fi
        ;;
        
    "ascii")
        echo "📝 Generating ASCII tree visualization..."
        ASCII_VIZ=$(jq -r '
        # Find root nodes (no dependents)  
        [.graph | keys] as $all_entities |
        [.graph | .[] | .depends_on[]?] as $all_deps |
        [$all_entities[] | select($all_deps | index(.) | not)] as $roots |
        
        # Simple tree display
        "📦 Root entities (" + ($roots | length | tostring) + " found):\n" +
        (if ($roots | length) > 0 then
            ($roots | map("├── " + .) | join("\n"))
        else
            "  (No root entities - graph has cycles)"
        end) + "\n\n" +
        
        "📦 All dependency relationships:\n" +
        (.graph | to_entries | map(
            .key as $entity |
            if (.value.depends_on // [] | length) > 0 then
                "📦 " + $entity + " depends on:\n" +
                ((.value.depends_on // []) | map("  ├── " + .) | join("\n"))
            else
                "📦 " + $entity + " (no dependencies)"
            end
        ) | join("\n"))
        ' "$KNOWLEDGE_MAP")
        
        if [[ -n "$OUTPUT_FILE" ]]; then
            echo "$ASCII_VIZ" > "$OUTPUT_FILE"
            echo "✅ ASCII visualization saved: $OUTPUT_FILE"
        else
            echo "$ASCII_VIZ"
        fi
        ;;
        
    "svg"|"png")
        echo "🖼️ Generating $FORMAT format..."
        
        # Check if graphviz is available
        if ! command -v dot &> /dev/null; then
            echo "❌ Graphviz 'dot' command not found. Install with:"
            echo "   macOS: brew install graphviz"
            echo "   Ubuntu: sudo apt-get install graphviz"
            echo "   CentOS: sudo yum install graphviz"
            exit 1
        fi
        
        # Use centralized patterns for enhanced DOT generation
        DOT_NODES=$(apply_pattern "graph_visualization" "dot_nodes_enhanced" "$KNOWLEDGE_MAP")
        DOT_EDGES=$(apply_pattern "graph_visualization" "dot_edges" "$KNOWLEDGE_MAP")
        
        DOT_CONTENT="digraph DependencyGraph {
  rankdir=TB;
  bgcolor=white;
  node [shape=box, style=\"rounded,filled\", fontname=Arial, fontsize=10];
  edge [color=\"#333333\", fontname=Arial, fontsize=8];

$DOT_NODES

$DOT_EDGES

  labelloc=\"t\";
  label=\"Dependency Graph - Generated $(date)\";
  fontsize=16;
}"
        
        # Generate the image
        if [[ "$FORMAT" == "svg" ]]; then
            echo "$DOT_CONTENT" | dot -Tsvg -o "$OUTPUT_FILE"
        else
            echo "$DOT_CONTENT" | dot -Tpng -o "$OUTPUT_FILE"
        fi
        
        if [[ $? -eq 0 ]]; then
            echo "✅ $FORMAT file generated: $OUTPUT_FILE"
        else
            echo "❌ Failed to generate $FORMAT file"
            exit 1
        fi
        ;;
        
    "stats")
        echo "📊 Generating visualization statistics..."
        
        # Use centralized pattern for stats
        VIZ_STATS=$(apply_pattern "graph_visualization" "visualization_stats" "$KNOWLEDGE_MAP")
        
        # Format the output using the JSON data  
        STATS=$(echo "$VIZ_STATS" | jq -r '
        "Graph Statistics:" + "\n" +
        "=================" + "\n" +
        "Nodes (entities): \(.total_entities)" + "\n" +
        "Edges (dependencies): \(.total_edges)" + "\n" +
        "Root nodes: \(.root_nodes)" + "\n" +
        "Leaf nodes: \(.leaf_nodes)" + "\n" +
        "Maximum fan-out: \(.max_fan_out)" + "\n" +
        "Maximum fan-in: \(.max_fan_in)" + "\n" +
        "Average fan-out: \(.avg_fan_out | . * 100 | round / 100)" + "\n" +
        "Graph density: \(.density * 100 | . * 1000 | round / 1000)%" + "\n" +
        "\nVisualization Recommendations:" + "\n" +
        "=============================" + "\n" +
        (if .total_entities <= 10 then "✅ Perfect for all visualization formats"
         elif .total_entities <= 25 then "✅ Good for DOT/SVG, consider filtering for ASCII"
         elif .total_entities <= 50 then "⚠️  Use DOT/SVG with clustering, ASCII may be cluttered"
         else "❌ Large graph - consider filtering or subgraph visualization" end) + "\n" +
        (if .density > 0.3 then "⚠️  High density - consider hierarchical layout or filtering"
         else "✅ Reasonable density for visualization" end) + "\n" +
        (if .max_fan_out > 10 then "⚠️  High fan-out entities may clutter visualization"
         else "✅ Fan-out levels are reasonable" end)
        ')
        
        if [[ -n "$OUTPUT_FILE" ]]; then
            echo "$STATS" > "$OUTPUT_FILE"
            echo "✅ Statistics saved: $OUTPUT_FILE"
        else
            echo "$STATS"
        fi
        ;;
        
    *)
        echo "❌ Unknown format: $FORMAT"
        echo "📖 Supported formats:"
        echo "   ascii   - ASCII tree visualization (default)"
        echo "   dot     - Graphviz DOT format"
        echo "   mermaid - Mermaid diagram format"
        echo "   svg     - SVG image (requires graphviz)"
        echo "   png     - PNG image (requires graphviz)"
        echo "   stats   - Visualization statistics and recommendations"
        echo
        echo "📝 Usage examples:"
        echo "   $0 -f ascii"
        echo "   $0 -f dot -o deps.dot"
        echo "   $0 knowledge-map.json -f mermaid"
        echo "   $0 -f svg -o deps.svg"
        echo "   $0 -f stats"
        exit 1
        ;;
esac

# Show additional info based on format
case "$FORMAT" in
    "dot")
        echo
        echo "💡 Next steps:"
        echo "   View online: http://magjac.com/graphviz-visual-editor/"
        echo "   Generate SVG: dot -Tsvg $OUTPUT_FILE -o ${OUTPUT_FILE%.dot}.svg"
        echo "   Generate PNG: dot -Tpng $OUTPUT_FILE -o ${OUTPUT_FILE%.dot}.png"
        ;;
    "mermaid")
        echo
        echo "💡 Next steps:"
        echo "   View online: https://mermaid.live/"
        echo "   VS Code: Install Mermaid Preview extension"
        echo "   GitHub: Paste in .md files with \`\`\`mermaid code blocks"
        ;;
    "ascii")
        echo
        echo "💡 Legend:"
        echo "   📦 Entity    🔄 Circular dependency"
        echo "   ├── Direct dependency    └── Last dependency"
        ;;
    "svg"|"png")
        echo
        echo "💡 Color coding:"
        echo "   🟢 Green: Root nodes (no dependents)"
        echo "   🔴 Pink: Leaf nodes (no dependencies)"  
        echo "   🟠 Orange: High fan-in (3+ dependents)"
        echo "   🟡 Yellow: High fan-out (5+ dependencies)"
        echo "   🔵 Blue: Regular nodes"
        ;;
esac

echo