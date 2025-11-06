## Contributing to Know Tool

Thank you for considering contributing to Know Tool! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## How to Contribute

### Reporting Bugs

1. Check if the bug already exists in Issues
2. Provide a clear description
3. Include steps to reproduce
4. Add relevant error messages
5. Specify your environment (OS, Python version)

### Suggesting Features

1. Check if the feature has been requested
2. Explain the use case
3. Describe the expected behavior
4. Provide examples if possible

### Submitting Code

#### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourproject/know
cd know

# Create virtual environment
python3 -m venv ~/.local/venvs/know
source ~/.local/venvs/know/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .[dev]

# Run tests
pytest tests/ -v
```

#### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all functions
- Keep functions focused and small

```python
def parse_entity_id(entity_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse an entity ID into type and name.

    Args:
        entity_id: Entity ID in format "type:name"

    Returns:
        Tuple of (entity_type, entity_name) or (None, None) if invalid
    """
    # Implementation
```

#### Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for >80% code coverage

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=know_lib --cov-report=html

# Run specific test
pytest tests/test_dependencies.py -v
```

#### Formatting

```bash
# Format code
black know_lib/ tests/

# Check formatting
black --check know_lib/ tests/

# Type checking
mypy know_lib/ --ignore-missing-imports

# Linting
pylint know_lib/
```

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commits:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `test:` - Tests
   - `refactor:` - Code refactoring
   - `perf:` - Performance improvement

5. **Push to your fork**
   ```bash
   git push origin feature/my-feature
   ```

6. **Create pull request**
   - Clear title and description
   - Reference related issues
   - Include test results
   - Add screenshots if UI changes

### Review Process

1. Automated checks run (tests, linting, type checking)
2. Maintainer reviews code
3. Address feedback
4. Merge when approved

## Development Guidelines

### Module Structure

```
know_lib/
├── __init__.py       # Package exports
├── graph.py          # Graph operations
├── entities.py       # Entity CRUD
├── dependencies.py   # Dependency management
├── validation.py     # Validation
├── generators.py     # Spec generation
├── llm.py           # LLM integration
├── async_graph.py   # Async support
└── utils.py         # Utilities
```

### Adding a New Feature

1. **Plan the feature**
   - Define requirements
   - Design API
   - Consider backward compatibility

2. **Implement**
   - Add to appropriate module
   - Follow existing patterns
   - Use type hints

3. **Test**
   - Write unit tests
   - Test edge cases
   - Test integration

4. **Document**
   - Add docstrings
   - Update README if needed
   - Add examples

5. **Submit PR**

### Performance Considerations

- Use caching where appropriate
- Avoid unnecessary file I/O
- Use generators for large datasets
- Profile before optimizing

```python
# Good - uses caching
@cached_property
def entity_count(self):
    return len(self.list_entities())

# Good - uses generator
def iter_entities(self):
    for entity_type, entities in self.data['entities'].items():
        for name, data in entities.items():
            yield f"{entity_type}:{name}", data
```

### Error Handling

- Use specific exceptions
- Provide helpful error messages
- Include context in errors

```python
# Good
if not entity_id:
    raise ValueError("Entity ID cannot be empty")

# Better
if not entity_id:
    raise ValueError(
        "Entity ID cannot be empty. "
        "Expected format: 'type:name' (e.g., 'features:analytics')"
    )
```

## Benchmarking

Run benchmarks before and after changes:

```bash
# Run benchmark
python benchmark.py

# Compare results
python benchmark.py > before.txt
# Make changes
python benchmark.py > after.txt
diff before.txt after.txt
```

## Documentation

- Update README for user-facing changes
- Update API docs for code changes
- Add examples for new features
- Keep CHANGELOG.md current

## Questions?

- Open an issue for questions
- Tag with `question` label
- Be specific and provide context

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

Thank you for contributing! 🎉
