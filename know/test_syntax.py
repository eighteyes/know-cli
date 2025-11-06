#!/usr/bin/env python3
"""
Syntax validation test - verifies all Python files compile correctly.
Does not require external dependencies.
"""

import py_compile
import sys
from pathlib import Path


def test_file_syntax(filepath):
    """Test if a Python file has valid syntax."""
    try:
        py_compile.compile(filepath, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def main():
    """Test all Python files."""
    print("=" * 70)
    print("Syntax Validation Test")
    print("=" * 70)
    print()

    # Find all Python files
    python_files = []
    for pattern in ['know_lib/*.py', 'tests/*.py', '*.py']:
        python_files.extend(Path('.').glob(pattern))

    python_files = [f for f in python_files if f.name != '__pycache__']

    passed = 0
    failed = 0
    errors = []

    print(f"Testing {len(python_files)} Python files...\n")

    for filepath in sorted(python_files):
        success, error = test_file_syntax(filepath)
        if success:
            print(f"  ✓ {filepath}")
            passed += 1
        else:
            print(f"  ✗ {filepath}")
            print(f"    Error: {error}")
            failed += 1
            errors.append((filepath, error))

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        print("\nErrors:")
        for filepath, error in errors:
            print(f"  {filepath}: {error}")
        sys.exit(1)
    else:
        print("\n✓ All Python files have valid syntax!")

    # Additional checks
    print("\n" + "=" * 70)
    print("Structure Validation")
    print("=" * 70)
    print()

    # Check for required files
    required_files = [
        'know.py',
        'know_lib/__init__.py',
        'know_lib/graph.py',
        'know_lib/entities.py',
        'know_lib/dependencies.py',
        'know_lib/validation.py',
        'know_lib/generators.py',
        'know_lib/llm.py',
        'know_lib/async_graph.py',
        'know_lib/utils.py',
        'setup.py',
        'requirements.txt',
    ]

    missing = []
    for filepath in required_files:
        if Path(filepath).exists():
            print(f"  ✓ {filepath}")
        else:
            print(f"  ✗ {filepath} (missing)")
            missing.append(filepath)

    print()
    if missing:
        print(f"✗ Missing {len(missing)} required files")
        sys.exit(1)
    else:
        print("✓ All required files present")

    # Count lines of code
    print("\n" + "=" * 70)
    print("Code Statistics")
    print("=" * 70)
    print()

    total_lines = 0
    for filepath in Path('know_lib').glob('*.py'):
        with open(filepath) as f:
            lines = len(f.readlines())
            total_lines += lines
            print(f"  {filepath.name:<20} {lines:>5} lines")

    print(f"\n  {'Total:':<20} {total_lines:>5} lines")

    # Test files
    test_total = 0
    for filepath in Path('tests').glob('*.py'):
        with open(filepath) as f:
            lines = len(f.readlines())
            test_total += lines

    print(f"  {'Tests total:':<20} {test_total:>5} lines")

    print("\n" + "=" * 70)
    print("✓ ALL VALIDATION CHECKS PASSED")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
