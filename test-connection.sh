#!/bin/bash
source ./know/lib/connect.sh

load_dependency_rules
echo "Features can connect to: ${ALLOWED_DEPS[features]}"

# Test connections
is_valid_connection_fast "features" "actions" && echo "features->actions: VALID" || echo "features->actions: INVALID"
is_valid_connection_fast "features" "components" && echo "features->components: VALID" || echo "features->components: INVALID"
is_valid_connection_fast "features" "acceptance_criteria" && echo "features->acceptance_criteria: VALID" || echo "features->acceptance_criteria: INVALID"
