#!/bin/bash

# Analyze dependency bundles and identify optimization opportunities
# Usage: ./scripts/bundle-analyzer.sh [knowledge-map.json] [analysis-type]
# Analysis types: size, redundancy, splitting, treeshaking, chunks

# Help function
show_help() {
    cat << 'EOF'
📦 Bundle Analyzer - Dependency Bundle Optimization

USAGE:
    ./scripts/bundle-analyzer.sh [knowledge-map.json] [analysis-type]
    ./scripts/bundle-analyzer.sh -h|--help

DESCRIPTION:
    Analyzes dependency bundles and identifies optimization opportunities

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: spec-graph.json)
    analysis-type        Type of analysis to perform (default: size)

ANALYSIS TYPES:
    size          Analyze bundle sizes and distribution
    redundancy    Find shared dependencies and redundancy patterns
    splitting     Suggest bundle splitting strategies
    treeshaking   Identify tree shaking opportunities and dead code
    chunks        Optimize chunk configuration and clustering
    all           Run all analysis types comprehensively

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/bundle-analyzer.sh                                    # Size analysis
    ./scripts/bundle-analyzer.sh knowledge-map.json redundancy     # Redundancy analysis
    ./scripts/bundle-analyzer.sh knowledge-map.json splitting      # Split strategies
    ./scripts/bundle-analyzer.sh knowledge-map.json all           # Complete analysis

OUTPUT:
    Bundle optimization recommendations with splitting and chunking strategies
EOF
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

KNOWLEDGE_MAP="${1:-spec-graph.json}"
ANALYSIS_TYPE="${2:-size}"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    echo "💡 Use -h for help"
    exit 1
fi

echo "📦 BUNDLE ANALYSIS: $KNOWLEDGE_MAP"
echo "🔍 Analysis type: $ANALYSIS_TYPE"
echo "=" | tr '=' '=' | head -c 60
echo

# Function to simulate bundle sizes (since we don't have real file sizes)
estimate_bundle_size() {
    jq -r --arg entity "$1" '
    def estimate_size($node; $visited):
        if ($visited | index($node)) then 0
        else
            # Base size estimation based on complexity
            (.graph[$node].depends_on // [] | length) as $deps_count |
            
            # Simulate size: base + dependencies
            (50 + ($deps_count * 10)) +
            ([$deps_count as $dc | if $dc > 0 then 
                ((.graph[$node].depends_on // [])[] | estimate_size(.; $visited + [$node])) 
             else 0 end] | add // 0)
        end;
    
    if (.graph | has($entity)) then
        estimate_size($entity; [])
    else
        0
    end
    ' "$KNOWLEDGE_MAP"
}

# Function to analyze bundle sizes
analyze_bundle_sizes() {
    jq -r '
    # Calculate transitive dependency count as size proxy
    def count_transitive_deps($node; $visited):
        if ($visited | index($node)) then 0
        else
            (.graph[$node].depends_on // []) as $deps |
            ($deps | length) + 
            ([$deps[] | count_transitive_deps(.; $visited + [$node])] | add // 0)
        end;
    
    [.graph | keys[] as $entity |
     {
         entity: $entity,
         direct_deps: (.graph[$entity].depends_on // [] | length),
         transitive_deps: count_transitive_deps($entity; []),
         estimated_size: (
             # Rough size estimation: base + deps + transitive
             100 + ((.graph[$entity].depends_on // [] | length) * 20) + 
             (count_transitive_deps($entity; []) * 5)
         )
     }] |
    
    sort_by(-.estimated_size) |
    
    "📊 BUNDLE SIZE ANALYSIS (estimated):" + "\n" +
    "Size\tEntity\t\t\t\tDirect\tTransitive" + "\n" +
    "----\t------\t\t\t\t------\t----------" + "\n" +
    
    (.[0:15][] |
     "\(.estimated_size)\t\(.entity)\t\t\(.direct_deps)\t\(.transitive_deps)") + 
     
    "\n\n📈 SIZE DISTRIBUTION:" + "\n" +
    "Large bundles (>500): " + (map(select(.estimated_size > 500)) | length | tostring) + "\n" +
    "Medium bundles (200-500): " + (map(select(.estimated_size >= 200 and .estimated_size <= 500)) | length | tostring) + "\n" +
    "Small bundles (<200): " + (map(select(.estimated_size < 200)) | length | tostring) + "\n" +
    "Average bundle size: " + (map(.estimated_size) | add / length | round | tostring)
    ' "$KNOWLEDGE_MAP"
}

# Function to find dependency redundancy
analyze_redundancy() {
    jq -r '
    # Find shared dependencies across entities
    def find_shared_deps:
        [.graph | to_entries[] |
         .key as $entity |
         (.value.depends_on // [])[] as $dep |
         {entity: $entity, dependency: $dep}] |
        
        group_by(.dependency) |
        map({
            dependency: .[0].dependency,
            used_by: map(.entity),
            usage_count: length
        }) |
        sort_by(-.usage_count);
    
    find_shared_deps as $shared |
    
    "🔄 DEPENDENCY REDUNDANCY ANALYSIS:" + "\n" +
    "=" * 40 + "\n" +
    
    "Most shared dependencies:" + "\n" +
    (($shared | .[0:10][] |
      select(.usage_count > 1) |
      "\(.dependency): used by \(.usage_count) entities")) + 
      
    "\n\n📊 SHARING STATISTICS:" + "\n" +
    "Total dependencies: " + ($shared | length | tostring) + "\n" +
    "Shared dependencies: " + ($shared | map(select(.usage_count > 1)) | length | tostring) + "\n" +
    "Unique dependencies: " + ($shared | map(select(.usage_count == 1)) | length | tostring) + "\n" +
    "Average sharing factor: " + ($shared | map(.usage_count) | add / length | . * 100 | round / 100 | tostring) + "\n" +
    
    "\n🎯 BUNDLING OPPORTUNITIES:" + "\n" +
    (($shared | map(select(.usage_count >= 5)) | length) as $highly_shared |
     if $highly_shared > 0 then
         "• " + ($highly_shared | tostring) + " dependencies used by 5+ entities - consider common chunks"
     else
         "• No highly shared dependencies found"
     end) + "\n" +
    
    (($shared | map(select(.usage_count >= 3 and .usage_count < 5)) | length) as $moderately_shared |
     if $moderately_shared > 0 then
         "• " + ($moderately_shared | tostring) + " dependencies used by 3-4 entities - potential for vendor bundles"
     else
         "• Limited moderate sharing detected"
     end)
    ' "$KNOWLEDGE_MAP"
}

# Function to suggest bundle splitting strategies
analyze_splitting() {
    jq -r '
    def calculate_depth($entity; $visited):
        if ($visited | index($entity)) then 0
        else
            (.graph[$entity].depends_on // []) as $deps |
            if ($deps | length) == 0 then 0
            else
                [$deps[] | calculate_depth(.; $visited + [$entity])] |
                (max // 0) + 1
            end
        end;
    
    [.graph | .[] | .depends_on[]?] as $all_deps |
    
    # Classify entities for splitting strategies
    [.graph | keys[] as $entity |
     {
         entity: $entity,
         dependents: ($all_deps | map(select(. == $entity)) | length),
         dependencies: (.graph[$entity].depends_on // [] | length),
         depth: calculate_depth($entity; []),
         category: (
             ($all_deps | map(select(. == $entity)) | length) as $dependents |
             (.graph[$entity].depends_on // [] | length) as $deps |
             calculate_depth($entity; []) as $depth |
             
             if $dependents == 0 and $deps > 0 then "entry_point"
             elif $dependents >= 5 then "shared_library" 
             elif $deps == 0 then "leaf_utility"
             elif $depth >= 4 then "deep_dependency"
             else "regular"
         )
     }] |
    
    group_by(.category) |
    map({category: .[0].category, entities: map(.entity), count: length}) |
    
    "📂 BUNDLE SPLITTING STRATEGY:" + "\n" +
    "=" * 35 + "\n" +
    
    (.[] |
     if .category == "entry_point" then
         "🚪 ENTRY POINTS (" + (.count | tostring) + "): Create separate bundles\n" +
         (.entities[0:5] | map("   • " + .) | join("\n")) +
         (if (.count > 5) then "\n   ... and " + ((.count - 5) | tostring) + " more" else "" end)
     elif .category == "shared_library" then  
         "\n\n📚 SHARED LIBRARIES (" + (.count | tostring) + "): Extract to vendor/common chunks\n" +
         (.entities[0:5] | map("   • " + .) | join("\n")) +
         (if (.count > 5) then "\n   ... and " + ((.count - 5) | tostring) + " more" else "" end)
     elif .category == "leaf_utility" then
         "\n\n🍃 LEAF UTILITIES (" + (.count | tostring) + "): Can be lazy-loaded\n" +
         (.entities[0:5] | map("   • " + .) | join("\n")) +
         (if (.count > 5) then "\n   ... and " + ((.count - 5) | tostring) + " more" else "" end)
     elif .category == "deep_dependency" then
         "\n\n⚡ DEEP DEPENDENCIES (" + (.count | tostring) + "): Consider async loading\n" +
         (.entities[0:5] | map("   • " + .) | join("\n")) +
         (if (.count > 5) then "\n   ... and " + ((.count - 5) | tostring) + " more" else "" end)
     else
         "\n\n📦 REGULAR ENTITIES (" + (.count | tostring) + "): Standard bundling"
     end) +
     
    "\n\n🎯 SPLITTING RECOMMENDATIONS:" + "\n" +
    "1. Create vendor bundle for shared libraries" + "\n" +
    "2. Separate bundles for each entry point" + "\n" +  
    "3. Lazy load leaf utilities and deep dependencies" + "\n" +
    "4. Use code splitting for entities with 3+ dependents"
    ' "$KNOWLEDGE_MAP"
}

# Function to analyze tree shaking opportunities  
analyze_treeshaking() {
    jq -r '
    [.graph | .[] | .depends_on[]?] as $all_deps |
    
    # Find potentially unused entities and over-dependencies
    [.graph | keys[] as $entity |
     {
         entity: $entity,
         dependents: ($all_deps | map(select(. == $entity)) | length),
         dependencies: (.graph[$entity].depends_on // [] | length),
         utilization_ratio: (
             ($all_deps | map(select(. == $entity)) | length) as $dependents |
             (.graph[$entity].depends_on // [] | length) as $deps |
             if $deps > 0 then $dependents / $deps else 
                if $dependents > 0 then 10 else 0 end  
             end
         )
     }] |
    
    "🌳 TREE SHAKING ANALYSIS:" + "\n" +
    "=" * 30 + "\n" +
    
    "🍂 DEAD CODE CANDIDATES (no dependents):" + "\n" +
    (map(select(.dependents == 0 and .dependencies > 0)) as $dead_code |
     if ($dead_code | length) > 0 then
         ($dead_code[0:8][] | "   • " + .entity + " (" + (.dependencies | tostring) + " deps)")
     else
         "   ✅ No obvious dead code found"
     end) +
     
    "\n\n📉 LOW UTILIZATION (high deps, few dependents):" + "\n" +
    (map(select(.dependencies >= 3 and .dependents <= 1)) as $low_util |
     if ($low_util | length) > 0 then
         ($low_util[0:8][] | "   • " + .entity + " (deps:" + (.dependencies | tostring) + " dependents:" + (.dependents | tostring) + ")")
     else
         "   ✅ No low utilization entities found"
     end) +
     
    "\n\n🎯 TREE SHAKING OPPORTUNITIES:" + "\n" +
    (map(select(.dependents == 0)) | length) as $potential_dead |
    (map(select(.utilization_ratio < 0.5 and .dependencies >= 3)) | length) as $over_deps |
    
    "• Potential dead code: " + ($potential_dead | tostring) + " entities" + "\n" +
    "• Over-dependencies: " + ($over_deps | tostring) + " entities" + "\n" +
    "• Enable tree shaking in bundler configuration" + "\n" +
    "• Use ESM imports for better tree shaking" + "\n" +
    "• Mark side-effect-free modules in package.json"
    ' "$KNOWLEDGE_MAP"
}

# Function to suggest chunk optimization
analyze_chunks() {
    jq -r '
    def find_clusters:
        # Find entities that are commonly used together
        [.graph | to_entries[] |
         .key as $entity |
         (.value.depends_on // []) as $deps |
         {entity: $entity, deps: ($deps | sort)}] |
        
        # Group by dependency patterns to find natural clusters
        group_by(.deps) |
        map(select(length > 1)) |
        map({pattern: .[0].deps, entities: map(.entity), size: length});
    
    [.graph | .[] | .depends_on[]?] as $all_deps |
    
    find_clusters as $clusters |
    
    "📊 CHUNK OPTIMIZATION ANALYSIS:" + "\n" +
    "=" * 35 + "\n" +
    
    "🎯 NATURAL CLUSTERS (shared dependency patterns):" + "\n" +
    (if ($clusters | length) > 0 then
         ($clusters[0:5][] |
          "   📦 Cluster of " + (.size | tostring) + " entities:" + "\n" +
          (.entities | map("      • " + .) | join("\n")) +
          "\n      Dependencies: [" + (.pattern | join(", ")) + "]\n")
     else
         "   ✅ No clear clustering patterns found"
     end) +
     
    "\n📈 CHUNKING STRATEGY:" + "\n" +
    
    # Calculate chunk recommendations
    (.graph | keys | length) as $total_entities |
    
    "Total entities: " + ($total_entities | tostring) + "\n" +
    
    (if $total_entities <= 20 then
         "• Recommended chunks: 2-3 (small codebase)"
     elif $total_entities <= 50 then
         "• Recommended chunks: 4-6 (medium codebase)"  
     else
         "• Recommended chunks: 8-12 (large codebase)"
     end) + "\n" +
     
    "• Vendor chunk: " + 
    ([.graph | keys[] as $entity |
      ($all_deps | map(select(. == $entity)) | length)] |
     map(select(. >= 3)) | length | tostring) + " shared dependencies\n" +
     
    "• Entry chunks: " + 
    ([.graph | keys[] as $entity |
      select(($all_deps | index($entity) | not) and 
             ((.graph[$entity].depends_on // [] | length) > 0))] | length | tostring) + " entry points\n" +
             
    "\n🔧 OPTIMIZATION RECOMMENDATIONS:" + "\n" +
    (if ($clusters | length) >= 3 then
         "• Extract " + ($clusters | length | tostring) + " common chunks based on usage patterns"
     else
         "• Limited clustering - focus on vendor/entry point splitting"
     end) + "\n" +
     
    "• Use dynamic imports for large, infrequently used modules" + "\n" +
    "• Consider route-based code splitting for entry points" + "\n" +
    "• Monitor chunk sizes - aim for 100-300KB per chunk"
    ' "$KNOWLEDGE_MAP"
}

# Main execution based on analysis type
case "$ANALYSIS_TYPE" in
    "size")
        analyze_bundle_sizes
        ;;
        
    "redundancy") 
        analyze_redundancy
        ;;
        
    "splitting")
        analyze_splitting
        ;;
        
    "treeshaking")
        analyze_treeshaking
        ;;
        
    "chunks")
        analyze_chunks
        ;;
        
    "all")
        echo "📊 COMPREHENSIVE BUNDLE ANALYSIS"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo
        
        analyze_bundle_sizes
        echo
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo
        analyze_redundancy
        echo
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"  
        echo
        analyze_splitting
        echo
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo
        analyze_treeshaking  
        echo
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo
        analyze_chunks
        ;;
        
    *)
        echo "❌ Unknown analysis type: $ANALYSIS_TYPE"
        echo
        echo "📖 Available analysis types:"
        echo "   size        - Analyze bundle sizes and distribution"
        echo "   redundancy  - Find shared dependencies and redundancy"
        echo "   splitting   - Suggest bundle splitting strategies"
        echo "   treeshaking - Identify tree shaking opportunities"
        echo "   chunks      - Optimize chunk configuration"
        echo "   all         - Run all analysis types"
        echo
        echo "📝 Usage examples:"
        echo "   $0 knowledge-map.json size"
        echo "   $0 knowledge-map.json redundancy"
        echo "   $0 knowledge-map.json all"
        exit 1
        ;;
esac

# Common footer with general optimization tips
echo
echo "🚀 GENERAL BUNDLE OPTIMIZATION TIPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

OPTIMIZATION_TIPS=$(jq -r '
(.graph | keys | length) as $total_entities |
[.graph | .[] | .depends_on[]?] as $all_deps |

{
    total_entities: $total_entities,
    shared_deps: (
        # Count dependencies used by multiple entities
        [.graph | .[] | .depends_on[]?] |
        group_by(.) |
        map(select(length > 1)) |
        length
    ),
    entry_points: (
        # Count entities that nothing depends on
        [.graph | keys[] as $entity |
         select($all_deps | index($entity) | not)] | length  
    ),
    complexity_score: (
        # Simple complexity: total deps / entities
        ($all_deps | length) / $total_entities
    )
} |

[
    "📦 Codebase Overview:",
    "   • " + (.total_entities | tostring) + " total entities",
    "   • " + (.shared_deps | tostring) + " shared dependencies", 
    "   • " + (.entry_points | tostring) + " potential entry points",
    "   • " + (.complexity_score | . * 100 | round / 100 | tostring) + " average dependencies per entity",
    "",
    "🎯 Optimization Priorities:",
    (if .shared_deps >= 5 then
        "   1. ⭐ HIGH: Extract vendor bundle (" + (.shared_deps | tostring) + " shared deps)"
     else
        "   1. Extract shared dependencies into vendor bundle"
     end),
    (if .entry_points >= 3 then  
        "   2. ⭐ HIGH: Implement code splitting (" + (.entry_points | tostring) + " entry points)"
     else
        "   2. Consider code splitting for entry points"
     end),
    (if .complexity_score > 4 then
        "   3. ⭐ HIGH: Enable tree shaking (high complexity detected)"
     else
        "   3. Enable tree shaking to remove unused code"
     end),
    "   4. Monitor and optimize chunk sizes regularly",
    "   5. Use lazy loading for non-critical dependencies"
] |
.[]
' "$KNOWLEDGE_MAP")

echo "$OPTIMIZATION_TIPS" | while read -r tip; do
    echo "   $tip"
done

echo