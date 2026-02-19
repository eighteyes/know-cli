#!/bin/bash
# protect-graph-files.sh
# Prevents direct Read/Edit/Write operations on graph files
# Enforces use of know CLI for all graph modifications

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Check if file path matches graph file patterns
if [[ "$FILE_PATH" == *"-graph.json" ]] || [[ "$FILE_PATH" == */spec-graph.json ]] || [[ "$FILE_PATH" == */code-graph.json ]]; then
    cat >&2 <<EOF
❌ Direct $TOOL_NAME access to graph files is not allowed

Graph file: $FILE_PATH

⚠️  Use the know CLI instead:
   • Read: know get <entity-id>
   • List: know list
   • Edit: know add <type> <key> <data>
   • Link: know link <from> <to>
   • Validate: know check validate

📚 See: /know-tool skill or CLAUDE.md for graph operations

This hook prevents accidental corruption of the graph structure.
Use the know CLI commands which ensure graph integrity.
EOF
    exit 2  # Exit 2 = block the action
fi

# Allow all other file operations
exit 0
