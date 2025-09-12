#!/bin/bash

# Validate architectural patterns and constraints in knowledge graph
# Usage: ./scripts/architecture-validator.sh [knowledge-map.json] [rules.json]

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
🏛️ Architecture Validator - Architectural Pattern Compliance

USAGE:
    ./scripts/architecture-validator.sh [knowledge-map.json] [rules.json]
    ./scripts/architecture-validator.sh -h|--help

DESCRIPTION:
    Validates architectural patterns and constraints in knowledge graphs:
    • Layered architecture compliance (UI->Service->Domain->Data)
    • Dependency and dependents limits validation
    • Dependency chain depth limits
    • Forbidden pattern detection
    • Naming convention compliance
    • Circular dependency detection
    • Overall compliance scoring and remediation suggestions

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: knowledge-map-cmd.json)
    rules.json           Path to validation rules file (default: architecture-rules.json)

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/architecture-validator.sh
    ./scripts/architecture-validator.sh my-map.json my-rules.json
    ./scripts/architecture-validator.sh knowledge-map.json

VALIDATION RULES:
    layered_architecture  - Enforce layer hierarchy (ui->service->domain->data)
    max_dependencies     - Limit entity fan-out (default: 7)
    max_dependents       - Limit entity fan-in (default: 10)
    max_depth           - Limit dependency chain depth (default: 6)
    forbidden_patterns   - Block specific dependency patterns
    naming_conventions   - Enforce naming patterns by layer
    circular_dependencies - Detect and prevent cycles

RULE CONFIGURATION:
    If rules.json doesn't exist, a default configuration is created automatically.
    Edit the rules file to customize validation criteria for your architecture.

OUTPUT:
    Comprehensive validation report with violations, compliance scoring, and remediation guidance
EOF
}

# Check for help flag
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

KNOWLEDGE_MAP="${1:-knowledge-map-cmd.json}"
RULES_FILE="${2:-architecture-rules.json}"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    exit 1
fi

# Create default rules if none provided
if [[ ! -f "$RULES_FILE" ]]; then
    echo "📋 Creating default architecture rules: $RULES_FILE"
    cat > "$RULES_FILE" << 'EOF'
{
  "layered_architecture": {
    "enabled": true,
    "layers": ["ui", "service", "domain", "data", "infrastructure"],
    "description": "UI -> Service -> Domain -> Data/Infrastructure only"
  },
  "max_dependencies": {
    "enabled": true,
    "limit": 7,
    "description": "No entity should depend on more than 7 others"
  },
  "max_dependents": {
    "enabled": true,
    "limit": 10,
    "description": "No entity should be depended upon by more than 10 others"
  },
  "max_depth": {
    "enabled": true,
    "limit": 6,
    "description": "Dependency chains should not exceed 6 levels"
  },
  "forbidden_patterns": {
    "enabled": true,
    "patterns": [
      {"from": "data", "to": "ui", "reason": "Data layer should not depend on UI"},
      {"from": "domain", "to": "ui", "reason": "Domain layer should not depend on UI"},
      {"from": "infrastructure", "to": "domain", "reason": "Infrastructure should not depend on domain"}
    ]
  },
  "naming_conventions": {
    "enabled": true,
    "patterns": {
      "ui": ".*\\.(component|view|page)$",
      "service": ".*\\.service$",
      "domain": ".*\\.(model|entity|domain)$",
      "data": ".*\\.(repository|dao|data)$"
    }
  },
  "circular_dependencies": {
    "enabled": true,
    "description": "No circular dependencies allowed"
  }
}
EOF
    echo "✅ Default rules created. Edit $RULES_FILE to customize."
    echo
fi

echo "🏛️ ARCHITECTURE VALIDATION: $KNOWLEDGE_MAP"
echo "📋 Using rules: $RULES_FILE"
echo "=" | tr '=' '=' | head -c 60
echo

# Load rules
RULES=$(cat "$RULES_FILE")

# 1. Validate layered architecture
echo "🏗️ LAYERED ARCHITECTURE VALIDATION:"
LAYER_ENABLED=$(echo "$RULES" | jq -r '.layered_architecture.enabled')
if [[ "$LAYER_ENABLED" == "true" ]]; then
    LAYER_VIOLATIONS=$(apply_pattern "architecture_validation" "layered_architecture_violations" "$KNOWLEDGE_MAP")
    
    if [[ -z "$LAYER_VIOLATIONS" ]]; then
        echo "   ✅ No layered architecture violations found"
    else
        echo "   🚨 Layer violations detected:"
        echo "$LAYER_VIOLATIONS" | while read -r violation; do
            echo "     - $violation"
        done
    fi
else
    echo "   ⏸️  Layered architecture validation disabled"
fi

echo

# 2. Validate dependency limits
echo "📊 DEPENDENCY LIMITS VALIDATION:"
MAX_DEPS_ENABLED=$(echo "$RULES" | jq -r '.max_dependencies.enabled')
if [[ "$MAX_DEPS_ENABLED" == "true" ]]; then
    MAX_DEPS_LIMIT=$(echo "$RULES" | jq -r '.max_dependencies.limit')
    
    DEPS_VIOLATIONS=$(jq -r --argjson limit "$MAX_DEPS_LIMIT" "$(load_jq_pattern "architecture_validation" "dependency_limit_violations")" "$KNOWLEDGE_MAP")
    
    if [[ -z "$DEPS_VIOLATIONS" ]]; then
        echo "   ✅ All entities within dependency limit ($MAX_DEPS_LIMIT)"
    else
        echo "   🚨 Entities exceeding dependency limit ($MAX_DEPS_LIMIT):"
        echo "$DEPS_VIOLATIONS" | while read -r violation; do
            echo "     - $violation"
        done
    fi
fi

MAX_DEPENDENTS_ENABLED=$(echo "$RULES" | jq -r '.max_dependents.enabled')
if [[ "$MAX_DEPENDENTS_ENABLED" == "true" ]]; then
    MAX_DEPENDENTS_LIMIT=$(echo "$RULES" | jq -r '.max_dependents.limit')
    
    DEPENDENTS_VIOLATIONS=$(jq -r --argjson limit "$MAX_DEPENDENTS_LIMIT" "$(load_jq_pattern "architecture_validation" "dependent_limit_violations")" "$KNOWLEDGE_MAP")
    
    if [[ -z "$DEPENDENTS_VIOLATIONS" ]]; then
        echo "   ✅ All entities within dependents limit ($MAX_DEPENDENTS_LIMIT)"
    else
        echo "   🚨 Entities exceeding dependents limit ($MAX_DEPENDENTS_LIMIT):"
        echo "$DEPENDENTS_VIOLATIONS" | while read -r violation; do
            echo "     - $violation"
        done
    fi
fi

echo

# 3. Validate depth limits
echo "📏 DEPTH LIMITS VALIDATION:"
MAX_DEPTH_ENABLED=$(echo "$RULES" | jq -r '.max_depth.enabled')
if [[ "$MAX_DEPTH_ENABLED" == "true" ]]; then
    MAX_DEPTH_LIMIT=$(echo "$RULES" | jq -r '.max_depth.limit')
    
    DEPTH_VIOLATIONS=$(jq -r --argjson limit "$MAX_DEPTH_LIMIT" "$(load_jq_pattern "architecture_validation" "depth_limit_violations")" "$KNOWLEDGE_MAP")
    
    if [[ -z "$DEPTH_VIOLATIONS" ]]; then
        echo "   ✅ All dependency chains within depth limit ($MAX_DEPTH_LIMIT)"
    else
        echo "   🚨 Entities exceeding depth limit ($MAX_DEPTH_LIMIT):"
        echo "$DEPTH_VIOLATIONS" | while read -r violation; do
            echo "     - $violation"
        done
    fi
fi

echo

# 4. Validate forbidden patterns
echo "🚫 FORBIDDEN PATTERNS VALIDATION:"
FORBIDDEN_ENABLED=$(echo "$RULES" | jq -r '.forbidden_patterns.enabled')
if [[ "$FORBIDDEN_ENABLED" == "true" ]]; then
    PATTERN_VIOLATIONS=$(jq -r --argjson rules "$RULES" '
    $rules.forbidden_patterns.patterns as $patterns |
    
    # Check each pattern
    [$patterns[] as $pattern |
     .graph | to_entries[] |
     select(.key | test($pattern.from)) as $from_entry |
     ($from_entry.value.depends_on // [])[] as $dep |
     select($dep | test($pattern.to)) |
     "\($from_entry.key) -> \($dep): \($pattern.reason)"] |
    if length > 0 then .[] else empty end
    ' "$KNOWLEDGE_MAP")
    
    if [[ -z "$PATTERN_VIOLATIONS" ]]; then
        echo "   ✅ No forbidden patterns detected"
    else
        echo "   🚨 Forbidden pattern violations:"
        echo "$PATTERN_VIOLATIONS" | while read -r violation; do
            echo "     - $violation"
        done
    fi
else
    echo "   ⏸️  Forbidden patterns validation disabled"
fi

echo

# 5. Validate naming conventions
echo "📝 NAMING CONVENTIONS VALIDATION:"
NAMING_ENABLED=$(echo "$RULES" | jq -r '.naming_conventions.enabled')
if [[ "$NAMING_ENABLED" == "true" ]]; then
    NAMING_VIOLATIONS=$(jq -r --argjson rules "$RULES" '
    $rules.naming_conventions.patterns as $patterns |
    
    [.graph | keys[] as $entity |
     # Try to classify entity and check naming
     if ($entity | test($patterns.ui // "^$")) then {entity: $entity, expected: "ui", actual: "matches"}
     elif ($entity | test($patterns.service // "^$")) then {entity: $entity, expected: "service", actual: "matches"}
     elif ($entity | test($patterns.domain // "^$")) then {entity: $entity, expected: "domain", actual: "matches"}
     elif ($entity | test($patterns.data // "^$")) then {entity: $entity, expected: "data", actual: "matches"}
     else {entity: $entity, expected: "unknown", actual: "no_pattern_match"}
     end] |
    
    map(select(.actual == "no_pattern_match" and .expected == "unknown")) |
    if length > 0 then
        .[] | "\(.entity): doesn\'t match any naming convention"
    else empty
    end
    ' "$KNOWLEDGE_MAP")
    
    if [[ -z "$NAMING_VIOLATIONS" ]]; then
        echo "   ✅ All entities follow naming conventions"
    else
        echo "   🚨 Naming convention violations:"
        echo "$NAMING_VIOLATIONS" | while read -r violation; do
            echo "     - $violation"
        done
    fi
else
    echo "   ⏸️  Naming conventions validation disabled"
fi

echo

# 6. Validate circular dependencies
echo "🔄 CIRCULAR DEPENDENCIES VALIDATION:"
CIRCULAR_ENABLED=$(echo "$RULES" | jq -r '.circular_dependencies.enabled')
if [[ "$CIRCULAR_ENABLED" == "true" ]]; then
    CIRCULAR_VIOLATIONS=$(apply_pattern "architecture_validation" "circular_dependency_violations" "$KNOWLEDGE_MAP")
    
    if [[ -z "$CIRCULAR_VIOLATIONS" ]]; then
        echo "   ✅ No circular dependencies detected"
    else
        echo "   🚨 Circular dependency violations:"
        echo "$CIRCULAR_VIOLATIONS" | while read -r violation; do
            echo "     - $violation"
        done
    fi
else
    echo "   ⏸️  Circular dependencies validation disabled"
fi

echo

# 7. Overall validation summary
echo "📋 VALIDATION SUMMARY:"
echo "=" | tr '=' '=' | head -c 25
echo

# Count total violations
TOTAL_VIOLATIONS=0
[[ -n "$LAYER_VIOLATIONS" && "$LAYER_ENABLED" == "true" ]] && TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(echo "$LAYER_VIOLATIONS" | wc -l | tr -d ' ')))
[[ -n "$DEPS_VIOLATIONS" && "$MAX_DEPS_ENABLED" == "true" ]] && TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(echo "$DEPS_VIOLATIONS" | wc -l | tr -d ' ')))
[[ -n "$DEPENDENTS_VIOLATIONS" && "$MAX_DEPENDENTS_ENABLED" == "true" ]] && TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(echo "$DEPENDENTS_VIOLATIONS" | wc -l | tr -d ' ')))
[[ -n "$DEPTH_VIOLATIONS" && "$MAX_DEPTH_ENABLED" == "true" ]] && TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(echo "$DEPTH_VIOLATIONS" | wc -l | tr -d ' ')))
[[ -n "$PATTERN_VIOLATIONS" && "$FORBIDDEN_ENABLED" == "true" ]] && TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(echo "$PATTERN_VIOLATIONS" | wc -l | tr -d ' ')))
[[ -n "$NAMING_VIOLATIONS" && "$NAMING_ENABLED" == "true" ]] && TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(echo "$NAMING_VIOLATIONS" | wc -l | tr -d ' ')))
[[ -n "$CIRCULAR_VIOLATIONS" && "$CIRCULAR_ENABLED" == "true" ]] && TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(echo "$CIRCULAR_VIOLATIONS" | wc -l | tr -d ' ')))

echo "   🚨 Total violations: $TOTAL_VIOLATIONS"

if [[ $TOTAL_VIOLATIONS -eq 0 ]]; then
    echo "   ✅ ARCHITECTURE VALIDATION PASSED"
    echo "   🏆 All architectural constraints satisfied"
elif [[ $TOTAL_VIOLATIONS -le 3 ]]; then
    echo "   🟡 ARCHITECTURE NEEDS MINOR FIXES"
    echo "   📝 Address violations to improve compliance"
elif [[ $TOTAL_VIOLATIONS -le 10 ]]; then
    echo "   🟠 ARCHITECTURE NEEDS MODERATE REFACTORING"
    echo "   🔧 Multiple violations require attention"
else
    echo "   🔴 ARCHITECTURE NEEDS MAJOR REFACTORING"
    echo "   ⚠️  Significant architectural issues detected"
fi

# 8. Remediation suggestions
if [[ $TOTAL_VIOLATIONS -gt 0 ]]; then
    echo
    echo "🔧 REMEDIATION SUGGESTIONS:"
    echo "=" | tr '=' '=' | head -c 25
    echo
    
    [[ -n "$LAYER_VIOLATIONS" && "$LAYER_ENABLED" == "true" ]] && echo "   1. Restructure dependencies to follow layer hierarchy"
    [[ -n "$DEPS_VIOLATIONS" && "$MAX_DEPS_ENABLED" == "true" ]] && echo "   2. Break down entities with too many dependencies"
    [[ -n "$DEPENDENTS_VIOLATIONS" && "$MAX_DEPENDENTS_ENABLED" == "true" ]] && echo "   3. Reduce coupling for highly-depended entities"
    [[ -n "$DEPTH_VIOLATIONS" && "$MAX_DEPTH_ENABLED" == "true" ]] && echo "   4. Flatten deep dependency chains"
    [[ -n "$PATTERN_VIOLATIONS" && "$FORBIDDEN_ENABLED" == "true" ]] && echo "   5. Remove dependencies that violate architectural patterns"
    [[ -n "$NAMING_VIOLATIONS" && "$NAMING_ENABLED" == "true" ]] && echo "   6. Rename entities to follow naming conventions"
    [[ -n "$CIRCULAR_VIOLATIONS" && "$CIRCULAR_ENABLED" == "true" ]] && echo "   7. Break circular dependencies using interfaces or events"
    
    echo "   8. Run validation after each fix to track progress"
    echo "   9. Consider updating rules in $RULES_FILE if needed"
fi

echo