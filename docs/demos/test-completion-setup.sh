#!/bin/bash

# Test the completion setup process with simulated user input

echo "=== Testing Interactive Completion Setup ==="
echo

# Create a test directory and backup real config
test_dir="/tmp/know-test-$$"
mkdir -p "$test_dir"

# Set temporary HOME for testing
export OLD_HOME="$HOME"
export HOME="$test_dir"

# Test the setup function directly
source ./know/lib/autocomplete.sh

echo "Testing setup_shell_config with mock completion file..."
echo

# Create a fake completion file
completion_file="$test_dir/know-completion"
echo "# Mock completion" > "$completion_file"

echo "=== Test 1: Show manual instructions (option 2) ==="
echo "2" | setup_shell_config "$completion_file"

echo
echo "=== Test 2: Create custom config file (option 3) ==="
echo "3
$test_dir/my-custom-config" | setup_shell_config "$completion_file"

echo
echo "=== Test 3: Check custom file was created ==="
if [[ -f "$test_dir/my-custom-config" ]]; then
    echo "✅ Custom config file created:"
    cat "$test_dir/my-custom-config"
else
    echo "❌ Custom config file not created"
fi

echo
echo "=== Test 4: Auto-setup for bash (option 1) ==="
# Create a mock .bashrc
touch "$test_dir/.bashrc"
echo "1" | setup_shell_config "$completion_file"

echo
echo "=== Test 5: Check .bashrc was modified ==="
if [[ -f "$test_dir/.bashrc" ]] && grep -q "know" "$test_dir/.bashrc"; then
    echo "✅ .bashrc updated:"
    tail -3 "$test_dir/.bashrc"
else
    echo "❌ .bashrc not updated correctly"
fi

# Restore HOME
export HOME="$OLD_HOME"

# Cleanup
rm -rf "$test_dir"

echo
echo "✅ Interactive setup tests complete"