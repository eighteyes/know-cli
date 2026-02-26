#!/bin/bash
# codemap.sh - Extract code structure using ast-grep
#
# Scans a codebase and outputs structured JSON representing:
# - Modules/files
# - Classes, functions, methods
# - Data schemas (interfaces, types, dataclasses, etc.)
# - Import/export relationships
#
# Usage: ./codemap.sh <source_dir> [--lang python|typescript|auto] [--output file.json]
# Default: ./codemap.sh . --lang auto --output .ai/codemap.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATTERNS_DIR="$SCRIPT_DIR/patterns"

# Defaults
SOURCE_DIR="."
LANG="auto"
OUTPUT=".ai/codemap.json"
HEAT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --lang)
      LANG="$2"
      shift 2
      ;;
    --output|-o)
      OUTPUT="$2"
      shift 2
      ;;
    --heat)
      HEAT=true
      shift
      ;;
    --help|-h)
      echo "Usage: codemap.sh <source_dir> [--lang python|typescript|auto] [--output file.json] [--heat]"
      echo ""
      echo "Options:"
      echo "  --lang     Language to scan (python, typescript, auto)"
      echo "  --output   Output JSON file (default: .ai/codemap.json)"
      echo "  --heat     Enrich output with git-based heat scores"
      exit 0
      ;;
    *)
      SOURCE_DIR="$1"
      shift
      ;;
  esac
done

# Find ast-grep binary (may be installed as 'ast-grep' or 'sg')
AST_GREP=""
find_ast_grep() {
  # Try ast-grep first (more explicit name)
  if command -v ast-grep &> /dev/null; then
    # Verify it's actually ast-grep
    if ast-grep --version 2>&1 | grep -qi "ast-grep"; then
      AST_GREP="ast-grep"
      return 0
    fi
  fi

  # Try sg (common alias)
  if command -v sg &> /dev/null; then
    # Verify it's ast-grep, not the shadow group utility
    if sg --version 2>&1 | grep -qi "ast-grep"; then
      AST_GREP="sg"
      return 0
    fi
    # Check if sg scan works (ast-grep has scan subcommand)
    if sg scan --help &> /dev/null; then
      AST_GREP="sg"
      return 0
    fi
  fi

  return 1
}

if ! find_ast_grep; then
  echo "Error: ast-grep not found." >&2
  echo "" >&2
  echo "Install ast-grep using one of:" >&2
  echo "  npm install -g @ast-grep/cli" >&2
  echo "  cargo install ast-grep --locked" >&2
  echo "  brew install ast-grep" >&2
  exit 1
fi

echo "Using ast-grep: $AST_GREP" >&2

# Detect language if auto
detect_language() {
  local py_count=$(find "$SOURCE_DIR" -name "*.py" 2>/dev/null | head -100 | wc -l | tr -d ' ')
  local ts_count=$(find "$SOURCE_DIR" \( -name "*.ts" -o -name "*.tsx" \) 2>/dev/null | head -100 | wc -l | tr -d ' ')
  local js_count=$(find "$SOURCE_DIR" \( -name "*.js" -o -name "*.jsx" \) 2>/dev/null | head -100 | wc -l | tr -d ' ')

  local ts_total=$((ts_count + js_count))

  if [[ $py_count -gt $ts_total ]]; then
    echo "python"
  elif [[ $ts_total -gt 0 ]]; then
    echo "typescript"
  else
    echo "unknown"
  fi
}

if [[ "$LANG" == "auto" ]]; then
  LANG=$(detect_language)
  echo "Detected language: $LANG" >&2
fi

# Select pattern file
case "$LANG" in
  python)
    PATTERN_FILE="$PATTERNS_DIR/python.yml"
    FILE_GLOB="*.py"
    ;;
  typescript|javascript|ts|js)
    PATTERN_FILE="$PATTERNS_DIR/typescript.yml"
    FILE_GLOB="*.ts,*.tsx,*.js,*.jsx"
    ;;
  *)
    echo "Error: Unknown language '$LANG'. Use: python, typescript" >&2
    exit 1
    ;;
esac

if [[ ! -f "$PATTERN_FILE" ]]; then
  echo "Error: Pattern file not found: $PATTERN_FILE" >&2
  exit 1
fi

echo "Scanning $SOURCE_DIR with $LANG patterns..." >&2

# Create output directory if needed
mkdir -p "$(dirname "$OUTPUT")"

# Run ast-grep and collect results
# Note: sg scan outputs JSON with file, rule, range, message
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Use --inline-rules with multi-doc YAML
$AST_GREP scan --inline-rules "$(cat "$PATTERN_FILE")" --json "$SOURCE_DIR" 2>/dev/null > "$TEMP_FILE" || true

# Check if we got any results
if [[ ! -s "$TEMP_FILE" ]]; then
  echo "Warning: No matches found" >&2
  echo '{"language":"'"$LANG"'","source":"'"$SOURCE_DIR"'","modules":[],"schemas":[],"imports":[]}' > "$OUTPUT"
  exit 0
fi

# Process raw ast-grep output into structured codemap
python3 - "$TEMP_FILE" "$SOURCE_DIR" "$LANG" "$OUTPUT" << 'PYTHON_SCRIPT'
import json
import sys
from pathlib import Path
from collections import defaultdict

def parse_message(msg):
    """Parse ast-grep message format into structured data."""
    parts = msg.split(":")
    if len(parts) >= 2:
        return {"type": parts[0], "name": parts[1], "extra": parts[2:] if len(parts) > 2 else []}
    # Single-word message - use as type (e.g., "function" -> type="function")
    return {"type": msg, "name": msg, "extra": []}

def extract_name_from_text(text, rule_id, message=''):
    """Extract entity name from matched text or message metavariables."""
    import re

    # TypeScript patterns use metavariables in messages like "class:$NAME"
    # ast-grep replaces $NAME with actual value in output message
    if ':' in message:
        parts = message.split(':')
        if len(parts) >= 2 and parts[1] and not parts[1].startswith('$'):
            return parts[1]  # Return captured name from message

    # Python: class definition
    if rule_id == 'class-definition':
        m = re.match(r'class\s+(\w+)', text)
        return m.group(1) if m else None

    # Python: function definition
    if rule_id == 'function-definition':
        m = re.match(r'(?:async\s+)?def\s+(\w+)', text)
        return m.group(1) if m else None

    # Python: method definition (function inside class)
    if rule_id == 'method-definition':
        m = re.match(r'(?:async\s+)?def\s+(\w+)', text)
        return m.group(1) if m else None

    # Python: decorated schemas
    if rule_id in ('dataclass', 'pydantic-basemodel', 'typeddict', 'enum-class'):
        m = re.search(r'class\s+(\w+)', text)
        return m.group(1) if m else None

    # Python: imports
    if rule_id == 'import-statement':
        m = re.match(r'import\s+(\w+)', text)
        return m.group(1) if m else text.strip()

    if rule_id == 'import-from':
        m = re.match(r'from\s+([.\w]+)\s+import', text)
        return m.group(1) if m else text.strip()

    # TypeScript: class/function from text
    if rule_id in ('class-declaration', 'class-extends', 'export-class'):
        m = re.match(r'(?:export\s+)?class\s+(\w+)', text)
        return m.group(1) if m else None

    if rule_id in ('function-declaration', 'async-function', 'export-function'):
        m = re.match(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', text)
        return m.group(1) if m else None

    if rule_id in ('arrow-function-const', 'export-arrow-function'):
        m = re.match(r'(?:export\s+)?const\s+(\w+)\s*=', text)
        return m.group(1) if m else None

    # TypeScript: interfaces and types
    if rule_id in ('interface-declaration', 'interface-extends', 'export-interface'):
        m = re.match(r'(?:export\s+)?interface\s+(\w+)', text)
        return m.group(1) if m else None

    if rule_id in ('type-alias', 'export-type-alias'):
        m = re.match(r'(?:export\s+)?type\s+(\w+)', text)
        return m.group(1) if m else None

    if rule_id in ('enum-declaration', 'export-enum'):
        m = re.match(r'(?:export\s+)?(?:const\s+)?enum\s+(\w+)', text)
        return m.group(1) if m else None

    # TypeScript: zod schemas
    if rule_id in ('zod-schema', 'zod-schema-export'):
        m = re.match(r'(?:export\s+)?const\s+(\w+)\s*=\s*z\.object', text)
        return m.group(1) if m else None

    # TypeScript: imports
    if rule_id == 'import-default':
        m = re.match(r'import\s+(\w+)\s+from', text)
        return m.group(1) if m else None

    if rule_id in ('import-named', 'import-star'):
        m = re.search(r"from\s+['\"]([^'\"]+)['\"]", text)
        return m.group(1) if m else None

    return None

def main():
    temp_file = sys.argv[1]
    source_dir = sys.argv[2]
    lang = sys.argv[3]
    output_file = sys.argv[4]

    # Load ast-grep results
    with open(temp_file, 'r') as f:
        content = f.read().strip()
        if not content:
            raw_matches = []
        else:
            # ast-grep outputs JSON array
            try:
                raw_matches = json.loads(content)
                if not isinstance(raw_matches, list):
                    raw_matches = [raw_matches]
            except json.JSONDecodeError:
                raw_matches = []

    # Organize by file
    files = defaultdict(lambda: {
        "classes": [],
        "functions": [],
        "schemas": [],
        "imports": [],
        "exports": []
    })

    for match in raw_matches:
        file_path = match.get("file", "")
        message = match.get("message", "")
        rule_id = match.get("ruleId", "")
        text = match.get("text", "")

        # Make path relative to source_dir
        try:
            rel_path = str(Path(file_path).relative_to(source_dir))
        except ValueError:
            rel_path = file_path

        # Extract name from matched text or message
        name = extract_name_from_text(text, rule_id, message)
        if not name:
            continue  # Skip matches where we couldn't extract a name

        parsed = parse_message(message)

        entry = {
            "name": name,
            "rule": rule_id,
            "line": match.get("range", {}).get("start", {}).get("line", 0),
            "text_preview": text[:100] if len(text) > 100 else text
        }

        # Categorize by type
        t = parsed["type"]
        if t in ["class", "export:class"]:
            files[rel_path]["classes"].append(entry)
        elif t in ["function", "async-function", "export:function", "arrow-function", "export:arrow-function"]:
            files[rel_path]["functions"].append(entry)
        elif t.startswith("schema:") or t.startswith("export:schema:"):
            schema_type = t.replace("export:", "").replace("schema:", "")
            entry["schema_type"] = schema_type
            files[rel_path]["schemas"].append(entry)
        elif t.startswith("import"):
            files[rel_path]["imports"].append(entry)
        elif t.startswith("export"):
            files[rel_path]["exports"].append(entry)
        elif t in ["method", "async-method"]:
            # Methods are nested - add to parent class context
            entry["is_method"] = True
            files[rel_path]["functions"].append(entry)
        elif t == "decorated":
            # Decorated functions
            entry["decorator"] = parsed["extra"][0] if parsed["extra"] else None
            files[rel_path]["functions"].append(entry)

    # Build module list
    modules = []
    all_schemas = []
    all_imports = []

    for path, data in sorted(files.items()):
        module = {
            "path": path,
            "classes": data["classes"],
            "functions": [f for f in data["functions"] if not f.get("is_method")],
            "methods": [f for f in data["functions"] if f.get("is_method")],
            "schemas": data["schemas"],
            "imports": data["imports"],
            "exports": data["exports"]
        }
        modules.append(module)

        # Aggregate schemas
        for schema in data["schemas"]:
            all_schemas.append({**schema, "file": path})

        # Aggregate imports for dependency analysis
        for imp in data["imports"]:
            all_imports.append({**imp, "file": path})

    # Build summary stats
    stats = {
        "total_files": len(modules),
        "total_classes": sum(len(m["classes"]) for m in modules),
        "total_functions": sum(len(m["functions"]) for m in modules),
        "total_methods": sum(len(m["methods"]) for m in modules),
        "total_schemas": len(all_schemas),
        "schema_types": list(set(s.get("schema_type", "unknown") for s in all_schemas))
    }

    # Output structure
    codemap = {
        "version": "1.0",
        "language": lang,
        "source": source_dir,
        "stats": stats,
        "modules": modules,
        "schemas": all_schemas,
        "imports": all_imports
    }

    with open(output_file, 'w') as f:
        json.dump(codemap, f, indent=2)

    print(f"Codemap written to: {output_file}", file=sys.stderr)
    print(f"  Files: {stats['total_files']}", file=sys.stderr)
    print(f"  Classes: {stats['total_classes']}", file=sys.stderr)
    print(f"  Functions: {stats['total_functions']}", file=sys.stderr)
    print(f"  Methods: {stats['total_methods']}", file=sys.stderr)
    print(f"  Schemas: {stats['total_schemas']} ({', '.join(stats['schema_types']) or 'none'})", file=sys.stderr)

if __name__ == "__main__":
    main()
PYTHON_SCRIPT

# Optionally enrich with heat scores
if [[ "$HEAT" == "true" ]]; then
  echo "Computing heat scores..." >&2
  python3 "$SCRIPT_DIR/heatmap.py" "$OUTPUT" --source-dir "$SOURCE_DIR" --output "$OUTPUT"
fi

echo "Done: $OUTPUT" >&2
