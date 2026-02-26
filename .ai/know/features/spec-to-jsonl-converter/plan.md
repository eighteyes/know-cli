# Implementation Plan: spec-to-jsonl-converter

## Simple Scope: JSON to JSONL Conversion Tool

**Goal**: Single command to convert spec-graph.json → entities.jsonl + graph.jsonl

**No migration period, no dual format support - just a one-time conversion tool.**

---

## JSONL Output Format

### File Structure

**Input**: `.ai/know/spec-graph.json` (single monolithic file)

**Output**:
```
.ai/spec-graph/
  ├── entities.jsonl    # Meta, entities, references
  └── graph.jsonl       # Dependency edges
```

### Record Types

#### entities.jsonl

**Meta**:
```jsonl
{"type":"meta","version":"1.0.0","format":"jsonl-graph-v1","project":"know-cli"}
```

**Phase Metadata**:
```jsonl
{"type":"phase-metadata","id":"I","name":"Foundation","description":"Core architecture"}
```

**Phase Assignment**:
```jsonl
{"type":"phase-assignment","phase":"in-progress","entity":"feature:auth","status":"incomplete"}
```

**Feature Spec**:
```jsonl
{"type":"feature-spec","feature":"feature:auth","status":"planned","use_cases":[...],"testing":{...}}
```

**Entity**:
```jsonl
{"type":"entity","entity_type":"user","key":"developer","name":"Software Developer","description":"..."}
```

**Reference**:
```jsonl
{"type":"reference","ref_type":"data-model","key":"user-profile","fields":[...]}
```

#### graph.jsonl

**Edge**:
```jsonl
{"type":"edge","from":"feature:auth","to":"component:login"}
```

---

## Implementation

### Single File: `know/src/converters/jsonl_converter.py`

```python
class JSONLConverter:
    """Convert JSON graph to JSONL format"""

    def convert(self, json_path: str, output_dir: str):
        """Convert spec-graph.json to JSONL files"""
        # 1. Load JSON
        with open(json_path) as f:
            data = json.load(f)

        # 2. Write entities.jsonl
        self._write_entities(data, f"{output_dir}/entities.jsonl")

        # 3. Write graph.jsonl
        self._write_graph(data, f"{output_dir}/graph.jsonl")

    def _write_entities(self, data, path):
        """Write meta, entities, references to entities.jsonl"""
        with open(path, 'w') as f:
            # Write meta
            meta = data.get('meta', {})
            # ... flatten meta.phases into phase-assignment records
            # ... write phase-metadata records
            # ... write feature-spec records

            # Write entities
            for entity_type, entities in data.get('entities', {}).items():
                for key, entity_data in entities.items():
                    record = {
                        'type': 'entity',
                        'entity_type': entity_type,
                        'key': key,
                        **entity_data
                    }
                    f.write(json.dumps(record) + '\n')

            # Write references
            for ref_type, refs in data.get('references', {}).items():
                for key, ref_data in refs.items():
                    record = {
                        'type': 'reference',
                        'ref_type': ref_type,
                        'key': key,
                        **ref_data
                    }
                    f.write(json.dumps(record) + '\n')

    def _write_graph(self, data, path):
        """Write dependency edges to graph.jsonl"""
        with open(path, 'w') as f:
            for from_id, node_data in data.get('graph', {}).items():
                for to_id in node_data.get('depends_on', []):
                    record = {
                        'type': 'edge',
                        'from': from_id,
                        'to': to_id
                    }
                    f.write(json.dumps(record) + '\n')
```

### CLI Command: Add to `know/know.py`

```python
@cli.command()
@click.argument('json_path')
@click.argument('output_dir')
def convert_to_jsonl(json_path, output_dir):
    """Convert JSON graph to JSONL format

    Example:
        know convert-to-jsonl .ai/know/spec-graph.json .ai/spec-graph/
    """
    from .src.converters.jsonl_converter import JSONLConverter

    converter = JSONLConverter()
    converter.convert(json_path, output_dir)

    console.print(f"[green]✓ Converted to JSONL format[/green]")
    console.print(f"  entities.jsonl: {output_dir}/entities.jsonl")
    console.print(f"  graph.jsonl: {output_dir}/graph.jsonl")
```

---

## Usage

```bash
# Convert spec-graph
know convert-to-jsonl .ai/know/spec-graph.json .ai/spec-graph/

# Convert code-graph
know convert-to-jsonl .ai/know/code-graph.json .ai/code-graph/
```

---

## Files to Create

1. **know/src/converters/__init__.py** - Package init
2. **know/src/converters/jsonl_converter.py** - Conversion logic (~150 lines)
3. **know/tests/test_jsonl_converter.py** - Tests (~100 lines)

## Files to Modify

1. **know/know.py** - Add `convert-to-jsonl` command (~20 lines)

---

## Testing

```python
def test_convert_preserves_data():
    """Ensure all data is preserved in conversion"""
    # Load original JSON
    # Convert to JSONL
    # Load JSONL back into JSON structure
    # Assert equality
```

---

## Implementation Time

**1-2 days**:
- Day 1: Implement converter + CLI command
- Day 2: Testing + documentation

---

## Components Needed

Per the /know:add workflow, this feature needs:

1. **JSONL serializer component** - Done via JSONLConverter class
2. **Graph traversal component** - Simple iteration over graph dict

Both implemented in `jsonl_converter.py`.
