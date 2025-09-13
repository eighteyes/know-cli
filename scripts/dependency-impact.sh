#!/bin/bash

# Analyze the impact of removing or changing entities in the dependency graph
# Usage: ./scripts/dependency-impact.sh [knowledge-map.json] [entity-name]

# Help function
show_help() {
    cat << 'EOF'
💥 Dependency Impact Analyzer - Change Impact Assessment

USAGE:
    ./scripts/dependency-impact.sh [knowledge-map.json] [entity-name]
    ./scripts/dependency-impact.sh -h|--help

DESCRIPTION:
    Analyzes the impact of removing or changing entities in dependency graphs:
    • Direct impact analysis (immediate dependents)
    • Cascade impact analysis (ripple effects)
    • Critical entities identification (high-impact nodes)
    • Bottleneck analysis (critical path chokepoints)
    • Change ripple effect simulation
    • Impact mitigation strategies
    • Overall risk assessment and scoring

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: spec-graph.json)
    entity-name          Optional: specific entity to analyze (analyzes all if not provided)

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/dependency-impact.sh                                    # Analyze all entities
    ./scripts/dependency-impact.sh knowledge-map.json                # Specific map file
    ./scripts/dependency-impact.sh knowledge-map.json MyEntity       # Focus on MyEntity

ANALYSIS TYPES:
    Direct Impact        - Entities immediately affected by removal
    Cascade Impact       - Entities affected through dependency chains
    Critical Entities    - High-impact nodes (3+ dependents)
    Bottleneck Analysis  - Critical path chokepoints
    Ripple Effect        - Change propagation simulation
    Risk Assessment      - Overall impact vulnerability scoring

OUTPUT:
    Comprehensive impact analysis with risk levels, mitigation strategies, and actionable insights
EOF
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

KNOWLEDGE_MAP="${1:-spec-graph.json}"
TARGET_ENTITY="$2"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    exit 1
fi

echo "💥 DEPENDENCY IMPACT ANALYSIS: $KNOWLEDGE_MAP"
if [[ -n "$TARGET_ENTITY" ]]; then
    echo "🎯 Target entity: $TARGET_ENTITY"
fi
echo "=" | tr '=' '=' | head -c 60
echo

# 1. Find direct impact (entities that directly depend on target)
if [[ -n "$TARGET_ENTITY" ]]; then
    echo "🎯 DIRECT IMPACT ANALYSIS FOR: $TARGET_ENTITY"
    
    # Check if entity exists
    ENTITY_EXISTS=$(jq -r --arg entity "$TARGET_ENTITY" '
    if (.graph | has($entity)) then "true" else "false" end
    ' "$KNOWLEDGE_MAP")
    
    if [[ "$ENTITY_EXISTS" == "false" ]]; then
        echo "   ❌ Entity '$TARGET_ENTITY' not found in dependency graph"
        echo
    else
        DIRECT_DEPENDENTS=$(jq -r --arg target "$TARGET_ENTITY" '
        [.graph | to_entries[] |
         select(.value.depends_on // [] | index($target)) |
         .key] |
        if length > 0 then .[] else empty end
        ' "$KNOWLEDGE_MAP")
        
        if [[ -z "$DIRECT_DEPENDENTS" ]]; then
            echo "   ✅ No entities directly depend on $TARGET_ENTITY"
        else
            echo "   🚨 Entities that would be directly affected:"
            echo "$DIRECT_DEPENDENTS" | while read -r dependent; do
                echo "     - $dependent"
            done
            DIRECT_COUNT=$(echo "$DIRECT_DEPENDENTS" | wc -l | tr -d ' ')
            echo "   📊 Total direct impact: $DIRECT_COUNT entities"
        fi
        
        echo
        
        # Show what the target depends on
        TARGET_DEPS=$(jq -r --arg target "$TARGET_ENTITY" '
        .graph[$target].depends_on // [] | 
        if length > 0 then .[] else empty end
        ' "$KNOWLEDGE_MAP")
        
        if [[ -z "$TARGET_DEPS" ]]; then
            echo "   📦 $TARGET_ENTITY has no dependencies (leaf node)"
        else
            echo "   📦 $TARGET_ENTITY depends on:"
            echo "$TARGET_DEPS" | while read -r dep; do
                echo "     - $dep"
            done
        fi
    fi
    
    echo
fi

# 2. Cascade impact analysis for specific entity or all high-impact entities
echo "🌊 CASCADE IMPACT ANALYSIS:"

if [[ -n "$TARGET_ENTITY" && "$ENTITY_EXISTS" == "true" ]]; then
    # Analyze cascade for specific entity
    CASCADE_IMPACT=$(jq -r --arg target "$TARGET_ENTITY" '
    # Find all entities that would be affected by removing target
    def find_cascade($removed; $affected):
        if ($affected | length) == 0 then $removed
        else
            # Find entities that depend on any in the affected set
            [.graph | to_entries[] |
             select(.value.depends_on // [] | 
                    any(. as $dep | $affected | index($dep))) |
             .key] as $next_affected |
            
            # Remove duplicates and entities already removed
            ($next_affected | map(select(. as $item | $removed | index($item) | not))) as $new_affected |
            
            if ($new_affected | length) == 0 then $removed
            else find_cascade($removed + $new_affected; $new_affected)
            end
        end;
    
    find_cascade([$target]; [$target]) | 
    map(select(. != $target)) |
    if length > 0 then .[] else empty end
    ' "$KNOWLEDGE_MAP")
    
    if [[ -z "$CASCADE_IMPACT" ]]; then
        echo "   ✅ No cascade impact from removing $TARGET_ENTITY"
    else
        echo "   🌊 Entities affected by cascade from removing $TARGET_ENTITY:"
        echo "$CASCADE_IMPACT" | while read -r affected; do
            echo "     - $affected"
        done
        CASCADE_COUNT=$(echo "$CASCADE_IMPACT" | wc -l | tr -d ' ')
        echo "   📊 Total cascade impact: $CASCADE_COUNT entities"
    fi
else
    # Find entities with highest impact potential
    HIGH_IMPACT_ENTITIES=$(jq -r '
    [.graph | .[] | .depends_on[]?] as $all_deps |
    (.graph | keys) as $entities |
    
    # Calculate impact score for each entity
    [$entities[] as $entity |
     {
         entity: $entity,
         direct_impact: ($all_deps | map(select(. == $entity)) | length),
         # Estimate cascade by looking at dependents of dependents
         cascade_estimate: (
             [.graph | to_entries[] |
              select(.value.depends_on // [] | index($entity)) |
              .key] as $direct_deps |
             [$direct_deps[] as $dep |
              ($all_deps | map(select(. == $dep)) | length)] |
             add // 0
         )
     }] |
    
    map(. + {total_impact: (.direct_impact + .cascade_estimate)}) |
    sort_by(-.total_impact) |
    .[0:10][] |
    select(.total_impact > 0) |
    "\(.total_impact)\t\(.entity)\t(direct:\(.direct_impact) cascade:\(.cascade_estimate))"
    ' "$KNOWLEDGE_MAP")
    
    if [[ -z "$HIGH_IMPACT_ENTITIES" ]]; then
        echo "   ✅ No high-impact entities found"
    else
        echo "   Impact  Entity                          Details"
        echo "   ------  ------                          -------"
        echo "$HIGH_IMPACT_ENTITIES" | while IFS=$'\t' read -r impact entity details; do
            printf "   %6s  %-30s %s\n" "$impact" "$entity" "$details"
        done
    fi
fi

echo

# 3. Critical entities analysis (removal would cause major disruption)
echo "⚠️ CRITICAL ENTITIES ANALYSIS:"
CRITICAL_ENTITIES=$(jq -r '
[.graph | .[] | .depends_on[]?] as $all_deps |

# Find entities that many others depend on
[.graph | keys[] as $entity |
 ($all_deps | map(select(. == $entity)) | length) as $dependents |
 select($dependents >= 3) |
 {entity: $entity, dependents: $dependents, criticality: (
   if $dependents >= 10 then "🔴 CRITICAL"
   elif $dependents >= 6 then "🟠 HIGH"
   elif $dependents >= 3 then "🟡 MODERATE"
   else "🟢 LOW"
   end
 )}] |

sort_by(-.dependents) |
.[] |
"\(.criticality)\t\(.entity)\t(\(.dependents) dependents)"
' "$KNOWLEDGE_MAP")

if [[ -z "$CRITICAL_ENTITIES" ]]; then
    echo "   ✅ No critical entities identified"
else
    echo "   Level       Entity                          Dependents"
    echo "   -----       ------                          ----------"
    echo "$CRITICAL_ENTITIES" | while IFS=$'\t' read -r level entity deps; do
        printf "   %-11s %-30s %s\n" "$level" "$entity" "$deps"
    done
fi

echo

# 4. Bottleneck analysis (entities that are critical path chokepoints)
echo "🚧 BOTTLENECK ANALYSIS:"
BOTTLENECKS=$(jq -r '
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

[.graph | .[] | .depends_on[]?] as $all_deps |

# Find entities that are both:
# 1. On critical paths (deep dependency chains)
# 2. Have multiple dependents
[.graph | keys[] as $entity |
 {
     entity: $entity,
     depth: max_depth($entity; []),
     dependents: ($all_deps | map(select(. == $entity)) | length),
     bottleneck_score: (max_depth($entity; []) * ($all_deps | map(select(. == $entity)) | length))
 }] |

sort_by(-.bottleneck_score) |
map(select(.bottleneck_score > 0)) |
.[0:8][] |
"\(.bottleneck_score)\t\(.entity)\t(depth:\(.depth) deps:\(.dependents))"
' "$KNOWLEDGE_MAP")

if [[ -z "$BOTTLENECKS" ]]; then
    echo "   ✅ No significant bottlenecks identified"
else
    echo "   Score  Entity                          Details"
    echo "   -----  ------                          -------"
    echo "$BOTTLENECKS" | while IFS=$'\t' read -r score entity details; do
        printf "   %5s  %-30s %s\n" "$score" "$entity" "$details"
    done
fi

echo

# 5. Change ripple effect simulation
echo "🌊 CHANGE RIPPLE EFFECT SIMULATION:"
RIPPLE_ANALYSIS=$(jq -r '
# Simulate what happens when top entities change
[.graph | .[] | .depends_on[]?] as $all_deps |

[$all_deps[] | [., 1]] | 
from_entries as $dep_counts |

# Find entities most likely to cause ripples
[.graph | keys[] as $entity |
 {
     entity: $entity,
     # Entities depending on this one
     immediate_ripple: ($all_deps | map(select(. == $entity)) | length),
     # Entities this one depends on (potential sources of change)
     change_sources: (.graph[$entity].depends_on // [] | length),
     # Combined ripple potential
     ripple_potential: (
         ($all_deps | map(select(. == $entity)) | length) * 
         (.graph[$entity].depends_on // [] | length)
     )
 }] |

sort_by(-.ripple_potential) |
map(select(.ripple_potential > 0)) |
.[0:8][] |
"\(.ripple_potential)\t\(.entity)\t(affects:\(.immediate_ripple) sources:\(.change_sources))"
' "$KNOWLEDGE_MAP")

if [[ -z "$RIPPLE_ANALYSIS" ]]; then
    echo "   ✅ Low ripple effect potential across the graph"
else
    echo "   Ripple  Entity                          Details"
    echo "   ------  ------                          -------"
    echo "$RIPPLE_ANALYSIS" | while IFS=$'\t' read -r ripple entity details; do
        printf "   %6s  %-30s %s\n" "$ripple" "$entity" "$details"
    done
fi

echo

# 6. Impact mitigation strategies
echo "🛡️ IMPACT MITIGATION STRATEGIES:"
MITIGATION=$(jq -r '
[.graph | .[] | .depends_on[]?] as $all_deps |
(.graph | keys | length) as $total_entities |

{
    high_impact_count: (
        [.graph | keys[] as $entity |
         ($all_deps | map(select(. == $entity)) | length)] | 
        map(select(. >= 3)) | length
    ),
    single_points_of_failure: (
        [.graph | keys[] as $entity |
         ($all_deps | map(select(. == $entity)) | length)] | 
        map(select(. >= 5)) | length
    ),
    avg_dependents: (
        [.graph | keys[] as $entity |
         ($all_deps | map(select(. == $entity)) | length)] | 
        add / length
    ),
    total_entities: $total_entities
} |

[
    (if .high_impact_count > 0 then "1. 🔄 Create backup/alternative implementations for \(.high_impact_count) high-impact entities" else empty end),
    (if .single_points_of_failure > 0 then "2. 🎯 Eliminate \(.single_points_of_failure) single points of failure through redundancy" else empty end),
    (if .avg_dependents > 2 then "3. 📦 Introduce facade patterns to reduce direct coupling" else empty end),
    (if .total_entities > 20 then "4. 🏗️  Create architectural layers to isolate change impact" else empty end),
    "5. 📋 Document critical dependencies and maintain change impact matrix",
    "6. 🧪 Implement dependency injection to enable easier testing/mocking",
    "7. 📊 Set up monitoring for high-impact entities to detect issues early",
    "8. 🔄 Consider event-driven patterns to reduce direct dependencies"
] |
.[]
' "$KNOWLEDGE_MAP")

echo "$MITIGATION" | while read -r strategy; do
    echo "   $strategy"
done

echo

# 7. Risk assessment summary
echo "📊 IMPACT RISK ASSESSMENT:"
echo "=" | tr '=' '=' | head -c 25
echo

RISK_SUMMARY=$(jq -r '
[.graph | .[] | .depends_on[]?] as $all_deps |
(.graph | keys | length) as $total_entities |

{
    critical_entities: (
        [.graph | keys[] as $entity |
         ($all_deps | map(select(. == $entity)) | length)] | 
        map(select(. >= 5)) | length
    ),
    high_impact_entities: (
        [.graph | keys[] as $entity |
         ($all_deps | map(select(. == $entity)) | length)] | 
        map(select(. >= 3)) | length
    ),
    total_dependencies: ($all_deps | length),
    avg_dependencies_per_entity: (($all_deps | length) / $total_entities),
    max_dependents: (
        [.graph | keys[] as $entity |
         ($all_deps | map(select(. == $entity)) | length)] | 
        max // 0
    )
} |

"Critical entities (5+ dependents): \(.critical_entities)" + "\n" +
"High-impact entities (3+ dependents): \(.high_impact_entities)" + "\n" +
"Total dependency relationships: \(.total_dependencies)" + "\n" +
"Average dependencies per entity: \(.avg_dependencies_per_entity | . * 100 | round / 100)" + "\n" +
"Maximum dependents on single entity: \(.max_dependents)" + "\n" +
"Risk level: " + (
    if .critical_entities == 0 and .high_impact_entities <= 2 then "🟢 LOW"
    elif .critical_entities <= 1 and .high_impact_entities <= 5 then "🟡 MODERATE"
    elif .critical_entities <= 3 and .high_impact_entities <= 10 then "🟠 HIGH"
    else "🔴 CRITICAL"
    end
)
' "$KNOWLEDGE_MAP")

echo "$RISK_SUMMARY" | while read -r line; do
    echo "   $line"
done

echo