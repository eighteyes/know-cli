#!/bin/bash
# check-command-versions.sh
# Pre-commit hook to enforce version increment on /know command changes
#
# Checks if any .claude/commands/know/*.md files are staged for commit
# and verifies the version was incremented if content changed.

COMMANDS_DIR=".claude/commands/know"

# Get list of staged command files
STAGED_COMMANDS=$(git diff --cached --name-only -- "$COMMANDS_DIR/*.md" 2>/dev/null)

if [ -z "$STAGED_COMMANDS" ]; then
    exit 0  # No command files staged, nothing to check
fi

ERRORS=0

for file in $STAGED_COMMANDS; do
    if [ ! -f "$file" ]; then
        continue  # File was deleted, skip
    fi

    # Extract version from staged content
    STAGED_VERSION=$(git show ":$file" | grep -E '^\`r[0-9]+\`$' | tail -1 | tr -d '`')

    # Extract version from HEAD (previous commit)
    HEAD_VERSION=$(git show "HEAD:$file" 2>/dev/null | grep -E '^\`r[0-9]+\`$' | tail -1 | tr -d '`')

    # If file is new (not in HEAD), just check it has a version
    if [ -z "$HEAD_VERSION" ]; then
        if [ -z "$STAGED_VERSION" ]; then
            echo "ERROR: New command file '$file' missing version footer (add \`r1\` at end)"
            ERRORS=$((ERRORS + 1))
        fi
        continue
    fi

    # Check if content changed (excluding the version line itself)
    STAGED_CONTENT=$(git show ":$file" | grep -v -E '^\`r[0-9]+\`$')
    HEAD_CONTENT=$(git show "HEAD:$file" | grep -v -E '^\`r[0-9]+\`$')

    if [ "$STAGED_CONTENT" != "$HEAD_CONTENT" ]; then
        # Content changed, version must be incremented
        if [ -z "$STAGED_VERSION" ]; then
            echo "ERROR: '$file' changed but missing version footer"
            ERRORS=$((ERRORS + 1))
        elif [ "$STAGED_VERSION" = "$HEAD_VERSION" ]; then
            # Extract version number and suggest next
            CURRENT_NUM=$(echo "$HEAD_VERSION" | sed 's/r//')
            NEXT_NUM=$((CURRENT_NUM + 1))
            echo "ERROR: '$file' changed but version not incremented"
            echo "       Current: \`$HEAD_VERSION\` → Expected: \`r$NEXT_NUM\`"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "Commit blocked: $ERRORS command file(s) need version updates"
    echo "Increment the version at the bottom of each changed file (e.g., \`r1\` → \`r2\`)"
    exit 1
fi

exit 0
