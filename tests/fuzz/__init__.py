"""
Fuzzing harness for the know CLI tool.

This package provides comprehensive fuzzing for the know CLI's graph validation
system. It generates intentionally malformed and rule-violating graphs to
stress-test and find bugs in the validator.

Key modules:
- generator.py: Mutation generators for spec-graphs, code-graphs, and cross-graph
- run_fuzz.py: Campaign orchestrator and reporting engine

See README.md for detailed documentation.
"""

__version__ = "0.1.0"
