#!/bin/bash

# Test autocomplete functionality manually
echo "=== Testing Know Autocomplete ==="
echo

# Source the completion
source /home/node/.local/share/bash-completion/completions/know

# Mock _init_completion and _filedir for testing
_init_completion() {
    return 0
}

_filedir() {
    echo "Would complete files for: $1"
}

# Test command completion
echo "1. Testing command completion:"
cur="f"
prev=""
words=("know" "f")
cword=1
_know_completion
echo "Commands starting with 'f': ${COMPREPLY[*]}"
echo

# Test entity completion for features
echo "2. Testing feature entity completion:"
cur=""
prev="feature"
words=("know" "feature" "")
cword=2
_know_completion
echo "Available features: ${COMPREPLY[*]}"
echo

# Test deps command completion
echo "3. Testing deps command completion:"
cur=""
prev="deps"
words=("know" "deps" "")
cword=2
_know_completion
echo "Available entities for deps: ${COMPREPLY[0]} ${COMPREPLY[1]} ${COMPREPLY[2]}..."
echo

echo "✅ Autocomplete test complete"