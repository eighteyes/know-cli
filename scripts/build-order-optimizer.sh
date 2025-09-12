#!/bin/bash

# Optimize build/processing order based on dependency graph using topological sort
# Usage: ./scripts/build-order-optimizer.sh [knowledge-map.json] [strategy]
# Strategies: topological, parallel, critical-path, size-optimized

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
⚙️ Build Order Optimizer - Dependency-Based Processing Order

USAGE:
    ./scripts/build-order-optimizer.sh [knowledge-map.json] [strategy]
    ./scripts/build-order-optimizer.sh -h|--help

DESCRIPTION:
    Optimizes build/processing order based on dependency graph using various strategies

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: knowledge-map-cmd.json)
    strategy             Optimization strategy (default: topological)

STRATEGIES:
    topological     Standard dependency-respecting order using Kahn's algorithm
    parallel        Group entities into parallel build levels for concurrent processing
    critical-path   Prioritize longest dependency chains first
    size-optimized  Build simple entities before complex ones
    makefile        Generate Makefile with proper dependencies
    analysis        Show overview of all strategies

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/build-order-optimizer.sh                                    # Topological
    ./scripts/build-order-optimizer.sh knowledge-map.json parallel        # Parallel levels
    ./scripts/build-order-optimizer.sh knowledge-map.json makefile        # Generate Makefile
    ./scripts/build-order-optimizer.sh knowledge-map.json analysis        # All strategies

OUTPUT:
    Optimized build order with parallelization recommendations and efficiency metrics
EOF
}

# Check for help flag
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

KNOWLEDGE_MAP="${1:-knowledge-map-cmd.json}"
STRATEGY="${2:-topological}"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    echo "💡 Use -h for help"
    exit 1
fi

echo "⚙️ BUILD ORDER OPTIMIZER: $KNOWLEDGE_MAP"
echo "📋 Strategy: $STRATEGY"
echo "=" | tr '=' '=' | head -c 60
echo

# Function to perform topological sort
topological_sort() {
    jq -r '
    # Kahns algorithm for topological sorting
    def topological_sort:
        # Calculate in-degrees
        [.graph | .[] | .depends_on[]?] as $all_deps |
        (.graph | keys) as $nodes |
        
        # Create in-degree map
        [$nodes[] as $node |
         {node: $node, in_degree: ($all_deps | map(select(. == $node)) | length)}] |
        
        # Initialize queue with nodes that have no dependencies
        ([.[] | select(.in_degree == 0) | .node]) as $queue |
        
        # Process queue
        {queue: $queue, result: [], in_degrees: (map({key: .node, value: .in_degree}) | from_entries)} |
        
        until(.queue | length == 0;
            .queue[0] as $current |
            .queue = .queue[1:] |
            .result += [$current] |
            
            # Update in-degrees of dependents
            (.graph[$current].depends_on // []) as $deps |
            reduce $deps[] as $dep (.;
                if .in_degrees[$dep] then
                    .in_degrees[$dep] -= 1 |
                    if .in_degrees[$dep] == 0 then
                        .queue += [$dep]
                    else . end
                else . end
            )
        ) |
        
        .result;
    
    topological_sort[]
    ' "$KNOWLEDGE_MAP"
}

# Function to create parallel build levels
parallel_build_levels() {
    jq -r '
    def build_levels:
        [.graph | .[] | .depends_on[]?] as $all_deps |
        (.graph | keys) as $nodes |
        
        # Calculate levels based on dependency depth
        def calculate_level($node; $visited):
            if ($visited | index($node)) then 0
            else
                (.graph[$node].depends_on // []) as $deps |
                if ($deps | length) == 0 then 0
                else
                    [$deps[] | calculate_level(.; $visited + [$node])] |
                    (max // 0) + 1
                end
            end;
        
        # Group nodes by their build level
        [$nodes[] as $node |
         {node: $node, level: calculate_level($node; [])}] |
        
        group_by(.level) |
        map({level: .[0].level, nodes: map(.node)}) |
        sort_by(.level) |
        reverse;  # Reverse so level 0 (deepest dependencies) come first
    
    build_levels[] |
    "Level \(.level): \(.nodes | join(", "))"
    ' "$KNOWLEDGE_MAP"
}

# Function to find critical path for build optimization
critical_path_order() {
    jq -r '
    def max_depth($entity; $visited):
        if ($visited | index($entity)) then 0
        else
            (.graph[$entity].depends_on // []) as $deps |
            if ($deps | length) == 0 then 0
            else
                [$deps[] | max_depth(.; $visited + [$entity])] |
                (max // 0) + 1
            end
        end;
    
    # Find critical path (longest dependency chain)
    [.graph | keys[] as $entity |
     {entity: $entity, depth: max_depth($entity; [])}] |
    
    # Sort by depth (deepest first for build order)
    sort_by(-.depth) |
    
    # Group by depth for parallel processing within levels
    group_by(.depth) |
    map({depth: .[0].depth, entities: map(.entity)}) |
    reverse |  # Build deepest dependencies first
    
    .[] |
    "Depth \(.depth): \(.entities | join(", "))"
    ' "$KNOWLEDGE_MAP"
}

# Function to optimize based on entity size/complexity
size_optimized_order() {
    jq -r '
    def calculate_complexity($entity):
        (.graph[$entity].depends_on // [] | length) as $out_degree |
        ([.graph | .[] | .depends_on[]?] | map(select(. == $entity)) | length) as $in_degree |
        ($out_degree * 2) + ($in_degree * 1.5);  # Weighted complexity score
    
    # Create build order optimized for size/complexity
    [.graph | keys[] as $entity |
     {
         entity: $entity,
         complexity: calculate_complexity($entity),
         dependencies: (.graph[$entity].depends_on // [] | length),
         level: (
             # Calculate dependency level
             def calculate_level($node; $visited):
                 if ($visited | index($node)) then 0
                 else
                     (.graph[$node].depends_on // []) as $deps |
                     if ($deps | length) == 0 then 0
                     else
                         [$deps[] | calculate_level(.; $visited + [$node])] |
                         (max // 0) + 1
                     end
                 end;
             calculate_level($entity; [])
         )
     }] |
    
    # Group by level, then sort by complexity within each level
    group_by(.level) |
    map({
        level: .[0].level,
        entities: (sort_by(.complexity) | map(.entity + " (complexity:" + (.complexity | tostring) + ")"))
    }) |
    sort_by(.level) |
    reverse |
    
    .[] |
    "Level \(.level): \(.entities | join(", "))"
    ' "$KNOWLEDGE_MAP"
}

# Function to generate Makefile-style dependencies
generate_makefile() {
    jq -r '
    "# Generated Makefile from dependency graph" +
    "\n# Usage: make <entity-name>" +
    "\n" +
    "\n.PHONY: all clean " + ([.graph | keys[]] | join(" ")) +
    "\n" +
    "\nall: " + ([.graph | keys[] as $entity |
                 ([.graph | .[] | .depends_on[]?] | map(select(. == $entity)) | length) as $dependents |
                 select($dependents == 0) | $entity] | join(" ")) +
    "\n" +
    "\n" +
    (.graph | to_entries[] |
     .key + ": " + ((.value.depends_on // []) | join(" ")) + 
     "\n\t@echo \"Building " + .key + "...\"" +
     "\n\t@# Add your build commands here for " + .key +
     "\n\t@touch " + .key +  # Placeholder build action
     "\n"
    ) +
    "\nclean:" +
    "\n\t@echo \"Cleaning all artifacts...\"" +
    "\n\t@rm -f " + ([.graph | keys[]] | join(" ")) +
    "\n"
    ' "$KNOWLEDGE_MAP"
}

# Function to detect build parallelization opportunities
analyze_parallelization() {
    jq -r '
    def build_levels:
        [.graph | .[] | .depends_on[]?] as $all_deps |
        (.graph | keys) as $nodes |
        
        def calculate_level($node; $visited):
            if ($visited | index($node)) then 0
            else
                (.graph[$node].depends_on // []) as $deps |
                if ($deps | length) == 0 then 0
                else
                    [$deps[] | calculate_level(.; $visited + [$node])] |
                    (max // 0) + 1
                end
            end;
        
        [$nodes[] as $node |
         {node: $node, level: calculate_level($node; [])}] |
        
        group_by(.level) |
        map({level: .[0].level, count: length, nodes: map(.node)});
    
    build_levels as $levels |
    
    "📊 PARALLELIZATION ANALYSIS:" + "\n" +
    "=" * 30 + "\n" +
    
    ($levels | map("Level \(.level): \(.count) entities can build in parallel") | join("\n")) + 
    
    "\n\n📈 PARALLELIZATION METRICS:" + "\n" +
    "Total entities: " + ($levels | map(.count) | add | tostring) + "\n" +
    "Build levels: " + ($levels | length | tostring) + "\n" +
    "Max parallelization: " + ($levels | map(.count) | max | tostring) + " entities" + "\n" +
    "Sequential time units: " + ($levels | length | tostring) + "\n" +
    "Parallel efficiency: " + (($levels | map(.count) | add) / ($levels | length) | . * 100 | round / 100 | tostring) + " entities/level" +
    
    "\n\n🎯 OPTIMIZATION OPPORTUNITIES:" + "\n" +
    (($levels | map(select(.count == 1))) as $sequential |
     if ($sequential | length) > 0 then
         "• " + ($sequential | length | tostring) + " levels with only 1 entity (potential bottlenecks)"
     else
         "• All levels have multiple entities - good parallelization"
     end) + "\n" +
    
    (($levels | map(.count) | max) as $max_parallel |
     "• Peak parallelization: " + ($max_parallel | tostring) + " concurrent builds") + "\n" +
     
    (if ($levels | length) > 10 then
         "• Consider dependency flattening - deep hierarchy (" + ($levels | length | tostring) + " levels)"
     else
         "• Reasonable build depth (" + ($levels | length | tostring) + " levels)"
     end)
    ' "$KNOWLEDGE_MAP"
}

# Main execution based on strategy
case "$STRATEGY" in
    "topological")
        echo "📋 TOPOLOGICAL BUILD ORDER:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        TOPO_ORDER=$(topological_sort)
        if [[ -z "$TOPO_ORDER" ]]; then
            echo "❌ Cannot create topological order - circular dependencies detected"
            echo "🔄 Run ./scripts/find-disconnects.sh to identify cycles"
        else
            echo "Build order (dependencies first):"
            echo "$TOPO_ORDER" | nl -v0 -s'. ' | while read -r line; do
                echo "   $line"
            done
            
            ORDER_COUNT=$(echo "$TOPO_ORDER" | wc -l | tr -d ' ')
            echo
            echo "📊 Total entities: $ORDER_COUNT"
            echo "⏱️  Sequential build time: $ORDER_COUNT time units"
        fi
        ;;
        
    "parallel")
        echo "🏗️ PARALLEL BUILD LEVELS:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        PARALLEL_LEVELS=$(parallel_build_levels)
        if [[ -z "$PARALLEL_LEVELS" ]]; then
            echo "❌ Cannot create parallel build levels"
        else
            echo "$PARALLEL_LEVELS" | while read -r level; do
                echo "   $level"
            done
            echo
            analyze_parallelization
        fi
        ;;
        
    "critical-path")
        echo "🎯 CRITICAL PATH BUILD ORDER:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        CRITICAL_ORDER=$(critical_path_order)
        if [[ -z "$CRITICAL_ORDER" ]]; then
            echo "❌ Cannot determine critical path"
        else
            echo "Build order (critical path first):"
            echo "$CRITICAL_ORDER" | while read -r depth_line; do
                echo "   $depth_line"
            done
        fi
        ;;
        
    "size-optimized")
        echo "⚖️ SIZE-OPTIMIZED BUILD ORDER:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        SIZE_ORDER=$(size_optimized_order)
        if [[ -z "$SIZE_ORDER" ]]; then
            echo "❌ Cannot create size-optimized order"
        else
            echo "Build order (simple entities first):"
            echo "$SIZE_ORDER" | while read -r level_line; do
                echo "   $level_line"
            done
        fi
        ;;
        
    "makefile")
        echo "📝 GENERATING MAKEFILE:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━"
        MAKEFILE_CONTENT=$(generate_makefile)
        echo "$MAKEFILE_CONTENT" > "Makefile.deps"
        echo "✅ Makefile generated: Makefile.deps"
        echo
        echo "💡 Usage:"
        echo "   make -f Makefile.deps all          # Build all targets"
        echo "   make -f Makefile.deps <entity>     # Build specific entity"
        echo "   make -f Makefile.deps -j4 all      # Parallel build with 4 jobs"
        ;;
        
    "analysis")
        echo "📊 BUILD ORDER ANALYSIS:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Show all strategies briefly
        echo "🔍 Topological Order (first 10):"
        topological_sort | head -10 | nl -v0 -s'. ' | sed 's/^/   /'
        
        echo
        echo "🏗️ Parallel Levels:"
        parallel_build_levels | head -5 | sed 's/^/   /'
        
        echo
        analyze_parallelization
        ;;
        
    *)
        echo "❌ Unknown strategy: $STRATEGY"
        echo
        echo "📖 Available strategies:"
        echo "   topological    - Standard dependency-respecting order"
        echo "   parallel       - Group entities into parallel build levels"  
        echo "   critical-path  - Prioritize longest dependency chains"
        echo "   size-optimized - Build simple entities before complex ones"
        echo "   makefile       - Generate Makefile with dependencies"
        echo "   analysis       - Show overview of all strategies"
        echo
        echo "📝 Usage examples:"
        echo "   $0 knowledge-map.json topological"
        echo "   $0 knowledge-map.json parallel"
        echo "   $0 knowledge-map.json makefile"
        exit 1
        ;;
esac

# Common footer information
echo
echo "🔧 BUILD OPTIMIZATION RECOMMENDATIONS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BUILD_RECOMMENDATIONS=$(jq -r '
(.graph | keys | length) as $total_entities |
[.graph | .[] | .depends_on[]?] as $all_deps |

# Calculate build metrics
def calculate_level($node; $visited):
    if ($visited | index($node)) then 0
    else
        (.graph[$node].depends_on // []) as $deps |
        if ($deps | length) == 0 then 0
        else
            [$deps[] | calculate_level(.; $visited + [$node])] |
            (max // 0) + 1
        end
    end;

[.graph | keys[] as $node |
 {node: $node, level: calculate_level($node; [])}] |

group_by(.level) as $levels |

{
    total_entities: $total_entities,
    build_levels: ($levels | length),
    max_parallel: ($levels | map(length) | max),
    bottlenecks: ($levels | map(select(length == 1)) | length),
    avg_parallel: (($levels | map(length) | add) / ($levels | length))
} |

[
    "• Total entities to build: \(.total_entities)",
    "• Sequential build depth: \(.build_levels) levels",
    "• Maximum parallel jobs: \(.max_parallel)",
    (if .bottlenecks > 0 then "⚠️  Warning: \(.bottlenecks) sequential bottlenecks detected" else "✅ Good parallelization potential" end),
    "• Average parallelism: \(.avg_parallel | . * 100 | round / 100) entities/level",
    "",
    "Optimization strategies:",
    (if .build_levels > 8 then "  - Consider flattening deep dependency chains" else "  - Build depth is reasonable" end),
    (if .max_parallel < 3 then "  - Limited parallelization - consider dependency restructuring" else "  - Good parallelization opportunities available" end),
    (if .bottlenecks > (.build_levels / 3) then "  - Many sequential bottlenecks - review critical dependencies" else "  - Bottlenecks are within acceptable range" end)
] |
.[]
' "$KNOWLEDGE_MAP")

echo "$BUILD_RECOMMENDATIONS" | while read -r rec; do
    echo "   $rec"
done

echo