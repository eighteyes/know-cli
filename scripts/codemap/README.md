# Codemap - AST-based Code Structure Extraction

Extract code structure using ast-grep, output to JSON, convert to code-graph format.

## Requirements

- ast-grep (`brew install ast-grep`)
- Python 3.8+

## Usage

### 1. Generate Codemap

```bash
# Auto-detect language
./codemap.sh <source_dir>

# Specify language
./codemap.sh <source_dir> --lang python
./codemap.sh <source_dir> --lang typescript

# Custom output
./codemap.sh <source_dir> --output .ai/codemap.json
```

### 2. Convert to Code-Graph

```bash
python3 graph-builder.py codemap.json --output .ai/know/code-graph.json

# Merge with existing code-graph
python3 graph-builder.py codemap.json --merge --output .ai/know/code-graph.json
```

## Output Format

### codemap.json

```json
{
  "version": "1.0",
  "language": "python",
  "source": "src/",
  "stats": {
    "total_files": 20,
    "total_classes": 22,
    "total_functions": 264,
    "total_schemas": 5,
    "schema_types": ["dataclass", "pydantic"]
  },
  "modules": [
    {
      "path": "auth/login.py",
      "classes": [{"name": "AuthService", "rule": "class-definition", "line": 10}],
      "functions": [{"name": "validate_token", "rule": "function-definition", "line": 45}],
      "schemas": [],
      "imports": [{"name": "jwt", "rule": "import-statement", "line": 1}]
    }
  ],
  "schemas": [],
  "imports": []
}
```

### code-graph.json

```json
{
  "entities": {
    "module": {
      "auth-login": {
        "name": "login",
        "file": "auth/login.py",
        "classes": ["AuthService"],
        "functions": ["validate_token"]
      }
    },
    "package": {
      "auth": {"name": "auth"}
    }
  },
  "references": {
    "external-dep": {
      "jwt": {"name": "jwt", "type": "library"}
    }
  },
  "graph": {
    "module:auth-login": {
      "depends_on": ["external-dep:jwt", "package:auth"]
    }
  }
}
```

## Supported Patterns

### Python
- Classes (including inheritance)
- Functions (sync and async)
- Dataclasses (`@dataclass`)
- Pydantic models (`class X(BaseModel)`)
- TypedDict
- Enums
- Imports

### TypeScript/JavaScript
- Classes (with extends/implements)
- Functions (regular, async, arrow)
- Interfaces
- Type aliases
- Enums
- Zod schemas
- Imports/exports

## Adding New Patterns

Edit `patterns/python.yml` or `patterns/typescript.yml`. Each rule uses multi-doc YAML format:

```yaml
---
id: my-pattern
language: python
rule:
  kind: class_definition
message: "schema:mytype"
---
```

Then add name extraction logic to `codemap.sh` in `extract_name_from_text()`.

## Integration with Know

After generating code-graph.json, link modules to spec-graph components:

```bash
# Add product-component reference
know -g .ai/know/code-graph.json ref add product-component auth-login \
  '{"component": "component:authentication", "feature": "feature:auth"}'
```
