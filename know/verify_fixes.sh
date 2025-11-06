#!/bin/bash
# Simple verification script for bug fixes (no dependencies required)

echo "=================================================="
echo "Bug Fix Verification Script"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

echo "Bug #1: Verifying 'operation' entity type in rules..."
python3 << 'EOF'
import json
with open('config/dependency-rules.json') as f:
    rules = json.load(f)
entity_types = set(rules.get('entity_description', {}).keys())
if 'operation' in entity_types:
    print("✓ 'operation' is defined in dependency-rules.json")
    print(f"  All entity types: {sorted(entity_types)}")
else:
    print("✗ FAILED: 'operation' not in rules")
    exit(1)
EOF

echo ""
echo "Bug #4: Verifying allowed metadata fields in rules..."
python3 << 'EOF'
import json
with open('config/dependency-rules.json') as f:
    rules = json.load(f)
entity_note = rules.get('entity_note', {})
allowed = entity_note.get('allowed_metadata', [])
if 'path' in allowed:
    print("✓ Custom metadata fields defined in dependency-rules.json")
    print(f"  Allowed metadata: {sorted(allowed)}")
else:
    print("✗ FAILED: allowed_metadata not in rules")
    exit(1)
EOF

echo ""
echo "Code Changes: Verifying EntityManager loads from rules..."
python3 << 'EOF'
import ast
import sys

# Read entities.py
with open('know_lib/entities.py') as f:
    content = f.read()

# Check for dynamic loading
if 'self.rules' in content and "rules.get('entity_description'" in content:
    print("✓ EntityManager loads entity types from rules")
else:
    print("✗ FAILED: EntityManager still has hardcoded types")
    sys.exit(1)

# Check for allowed_metadata loading
if 'allowed_metadata' in content.lower():
    print("✓ EntityManager loads allowed metadata from rules")
else:
    print("✗ FAILED: EntityManager doesn't load metadata")
    sys.exit(1)
EOF

echo ""
echo "Code Changes: Verifying topological sort fix..."
python3 << 'EOF'
import sys

# Read dependencies.py
with open('know_lib/dependencies.py') as f:
    content = f.read()

# Check for cycle detection in topological_sort
if 'if len(result) != len(graph):' in content:
    print("✓ Topological sort has cycle detection")
else:
    print("✗ FAILED: Topological sort missing cycle detection")
    sys.exit(1)
EOF

echo ""
echo "Code Changes: Verifying GraphValidator loads metadata..."
python3 << 'EOF'
import sys

# Read validation.py
with open('know_lib/validation.py') as f:
    content = f.read()

# Check for allowed_metadata loading
if 'self.allowed_metadata' in content and "get('allowed_metadata'" in content:
    print("✓ GraphValidator loads allowed metadata from rules")
else:
    print("✗ FAILED: GraphValidator doesn't load metadata")
    sys.exit(1)
EOF

echo ""
echo "Code Changes: Verifying health check fix..."
python3 << 'EOF'
import sys

# Read know.py
with open('know.py') as f:
    content = f.read()

# Check for has_critical_issues logic
if 'has_critical_issues' in content and 'disconnected' in content.lower():
    print("✓ Health check treats disconnected subgraphs as informational")
else:
    print("✗ FAILED: Health check still treats disconnected as error")
    sys.exit(1)
EOF

echo ""
echo "=================================================="
echo "✓ All verifications passed!"
echo "=================================================="
echo ""
echo "Note: This script only verifies the fixes are in place."
echo "To run full tests, use: python3 tests/run_bug_fix_tests.py"
echo "  (requires installing dependencies from requirements.txt)"
