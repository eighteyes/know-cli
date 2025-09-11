#!/bin/bash
set -e

KNOWLEDGE_MAP="knowledge-map-structured.json"
VALIDATION_REPORT="validation-report.json"

echo "🔍 Validating Knowledge Map Structure..."

# Check if knowledge map exists
if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    exit 1
fi

# Initialize validation report
cat > "$VALIDATION_REPORT" << 'EOF'
{
  "validation_timestamp": "",
  "errors": [],
  "warnings": [],
  "stats": {},
  "summary": {
    "total_errors": 0,
    "total_warnings": 0,
    "status": "unknown"
  }
}
EOF

# Add timestamp
jq --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '.validation_timestamp = $timestamp' "$VALIDATION_REPORT" > temp.json && mv temp.json "$VALIDATION_REPORT"

echo "📊 Collecting entity statistics..."

# Get entity counts
USERS_COUNT=$(jq '.entities.users | length' "$KNOWLEDGE_MAP")
SCREENS_COUNT=$(jq '.entities.screens | length' "$KNOWLEDGE_MAP")
COMPONENTS_COUNT=$(jq '.entities.components | length' "$KNOWLEDGE_MAP")
FEATURES_COUNT=$(jq '.entities.features | length' "$KNOWLEDGE_MAP")
MODELS_COUNT=$(jq '.entities.models | length' "$KNOWLEDGE_MAP")
REQUIREMENTS_COUNT=$(jq '.entities.requirements | length' "$KNOWLEDGE_MAP")
CONTENT_LIBRARY_COUNT=$(jq '.content_library | length' "$KNOWLEDGE_MAP")

# Update stats in validation report
jq --arg users "$USERS_COUNT" --arg screens "$SCREENS_COUNT" --arg components "$COMPONENTS_COUNT" \
   --arg features "$FEATURES_COUNT" --arg models "$MODELS_COUNT" --arg requirements "$REQUIREMENTS_COUNT" \
   --arg content "$CONTENT_LIBRARY_COUNT" \
   '.stats = {
     "users": ($users | tonumber),
     "screens": ($screens | tonumber), 
     "components": ($components | tonumber),
     "features": ($features | tonumber),
     "models": ($models | tonumber),
     "requirements": ($requirements | tonumber),
     "content_library_entries": ($content | tonumber)
   }' "$VALIDATION_REPORT" > temp.json && mv temp.json "$VALIDATION_REPORT"

echo "🔗 Checking content_library references..."

# Extract all description_ref values and check if they exist in content_library
jq -r '
  [.entities[][] | select(type == "object" and has("description_ref")) | .description_ref] | 
  unique[]
' "$KNOWLEDGE_MAP" | while read -r ref; do
    if ! jq -e --arg ref "$ref" '.content_library | has($ref)' "$KNOWLEDGE_MAP" > /dev/null; then
        echo "❌ Missing content_library entry: $ref"
        jq --arg ref "$ref" '.errors += [{
          "type": "missing_content_reference",
          "message": ("Missing content_library entry: " + $ref),
          "reference": $ref
        }]' "$VALIDATION_REPORT" > temp.json && mv temp.json "$VALIDATION_REPORT"
    fi
done

echo "🔗 Checking entity cross-references..."

# Check if referenced entities exist
check_entity_references() {
    local entity_type="$1"
    local field_name="$2"
    
    jq -r --arg type "$entity_type" --arg field "$field_name" '
      .entities[$type] // {} | 
      to_entries[] | 
      select(.value | type == "object" and has($field)) |
      .key as $entity_key | 
      (.value[$field] // []) | 
      if type == "array" then .[] else . end |
      "\($entity_key)|\(.)"
    ' "$KNOWLEDGE_MAP" | while IFS='|' read -r entity_key referenced_entity; do
        
        # Check if the referenced entity exists in any entity type
        found=false
        for check_type in users screens components features models requirements robot_types ai_capabilities integration_points; do
            if jq -e --arg type "$check_type" --arg entity "$referenced_entity" '.entities[$type] | has($entity)' "$KNOWLEDGE_MAP" > /dev/null 2>&1; then
                found=true
                break
            fi
        done
        
        if [[ "$found" == false ]]; then
            echo "❌ Broken reference in $entity_type:$entity_key -> $field_name: $referenced_entity"
            jq --arg entity_type "$entity_type" --arg entity_key "$entity_key" --arg field "$field_name" --arg ref "$referenced_entity" \
               '.errors += [{
                 "type": "broken_entity_reference",
                 "entity_type": $entity_type,
                 "entity_key": $entity_key,
                 "field": $field,
                 "broken_reference": $ref,
                 "message": ("Broken reference in " + $entity_type + ":" + $entity_key + " -> " + $field + ": " + $ref)
               }]' "$VALIDATION_REPORT" > temp.json && mv temp.json "$VALIDATION_REPORT"
        fi
    done
}

# Check various reference fields
echo "  Checking accessible_screens references..."
check_entity_references "users" "accessible_screens"

echo "  Checking accessible_features references..."
check_entity_references "users" "accessible_features"

echo "  Checking components references..."
check_entity_references "screens" "components"

echo "  Checking features references..."  
check_entity_references "screens" "features"

echo "  Checking used_by_screens references..."
check_entity_references "components" "used_by_screens"

echo "  Checking used_by_features references..."
check_entity_references "components" "used_by_features"

echo "  Checking uses_models references..."
check_entity_references "components" "uses_models"

echo "🔍 Checking for orphaned entities..."

# Find entities not referenced by others
find_orphaned_entities() {
    local entity_type="$1"
    
    jq -r --arg type "$entity_type" '.entities[$type] | keys[]' "$KNOWLEDGE_MAP" | while read -r entity_key; do
        # Check if this entity is referenced anywhere
        referenced=$(jq -r --arg entity "$entity_key" '
          [
            (.entities.users // {} | to_entries[] | .value.accessible_screens // [], .value.accessible_features // []),
            (.entities.screens // {} | to_entries[] | .value.components // [], .value.features // []),
            (.entities.components // {} | to_entries[] | .value.used_by_screens // [], .value.used_by_features // [], .value.uses_models // []),
            (.relationships // {} | to_entries[] | [.value[]] | flatten)
          ] | 
          flatten | 
          any(. == $entity)
        ' "$KNOWLEDGE_MAP")
        
        if [[ "$referenced" == "false" ]]; then
            echo "⚠️  Orphaned entity: $entity_type:$entity_key"
            jq --arg entity_type "$entity_type" --arg entity_key "$entity_key" \
               '.warnings += [{
                 "type": "orphaned_entity",
                 "entity_type": $entity_type,
                 "entity_key": $entity_key,
                 "message": ("Orphaned entity not referenced by others: " + $entity_type + ":" + $entity_key)
               }]' "$VALIDATION_REPORT" > temp.json && mv temp.json "$VALIDATION_REPORT"
        fi
    done
}

find_orphaned_entities "components"
find_orphaned_entities "features"
find_orphaned_entities "models"

echo "📋 Checking required fields..."

# Check for required fields in entities
jq -r '.entities | to_entries[] | .key as $entity_type | .value | to_entries[] | 
  select(.value | type == "object") |
  .key as $entity_key | 
  .value |
  if has("id") and has("type") and has("name") then empty 
  else "\($entity_type)|\($entity_key)|missing_required_fields" 
  end
' "$KNOWLEDGE_MAP" | while IFS='|' read -r entity_type entity_key issue; do
    if [[ -n "$issue" ]]; then
        echo "❌ Missing required fields in $entity_type:$entity_key"
        jq --arg entity_type "$entity_type" --arg entity_key "$entity_key" \
           '.errors += [{
             "type": "missing_required_fields",
             "entity_type": $entity_type,
             "entity_key": $entity_key,
             "message": ("Missing required fields (id, type, name) in " + $entity_type + ":" + $entity_key)
           }]' "$VALIDATION_REPORT" > temp.json && mv temp.json "$VALIDATION_REPORT"
    fi
done

echo "🔢 Generating final summary..."

# Calculate totals and update summary
ERROR_COUNT=$(jq '.errors | length' "$VALIDATION_REPORT")
WARNING_COUNT=$(jq '.warnings | length' "$VALIDATION_REPORT")

if [[ "$ERROR_COUNT" -eq 0 && "$WARNING_COUNT" -eq 0 ]]; then
    STATUS="✅ VALID"
elif [[ "$ERROR_COUNT" -eq 0 ]]; then
    STATUS="⚠️ VALID_WITH_WARNINGS"
else
    STATUS="❌ INVALID"
fi

jq --arg errors "$ERROR_COUNT" --arg warnings "$WARNING_COUNT" --arg status "$STATUS" \
   '.summary.total_errors = ($errors | tonumber) | 
    .summary.total_warnings = ($warnings | tonumber) |
    .summary.status = $status' "$VALIDATION_REPORT" > temp.json && mv temp.json "$VALIDATION_REPORT"

echo ""
echo "📊 VALIDATION COMPLETE"
echo "======================="
echo "Errors: $ERROR_COUNT"
echo "Warnings: $WARNING_COUNT" 
echo "Status: $STATUS"
echo ""
echo "📄 Full report saved to: $VALIDATION_REPORT"

if [[ "$ERROR_COUNT" -gt 0 ]]; then
    echo ""
    echo "❌ ERRORS FOUND:"
    jq -r '.errors[] | "  - \(.message)"' "$VALIDATION_REPORT"
fi

if [[ "$WARNING_COUNT" -gt 0 ]]; then
    echo ""
    echo "⚠️  WARNINGS:"
    jq -r '.warnings[] | "  - \(.message)"' "$VALIDATION_REPORT"
fi

# Exit with error code if there are errors
if [[ "$ERROR_COUNT" -gt 0 ]]; then
    exit 1
fi