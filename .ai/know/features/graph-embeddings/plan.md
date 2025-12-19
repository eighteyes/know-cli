# Plan: graph-embeddings

See [spec.md](./spec.md) for generated specifications from the graph.

## Architecture

```
spec-graph.json ──────────────────┐
                                  │ on modify
code-graph.json ──────────────────┼──→ know embed ──→ .ai/embeddings.json
                                  │
                                  ↓
                         ┌─────────────────────┐
                         │ .ai/embeddings.json │
                         ├─────────────────────┤
                         │ {                   │
                         │   "model": "...",   │
                         │   "dimensions": 384,│
                         │   "graph_hash": "x",│
                         │   "vectors": {      │
                         │     "feature:login":│
                         │       [0.12, -0.3,] │
                         │   }                 │
                         │ }                   │
                         └─────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
            know find "auth"           know suggest feature:new-thing
            → cosine similarity        → "might depend on..."
```

## Implementation Steps

### 1. Add dependency
**What:** Add sentence-transformers to project dependencies
**How:** Update requirements.txt or pyproject.toml
**Files:** `requirements.txt`, `pyproject.toml`

### 2. Create embeddings module
**What:** Core module for embedding operations
**How:** Create `know/src/embeddings.py` with:
  - `extract_text(node_key, node_data)` - Concatenate all string values
  - `generate_embeddings(texts)` - Batch embed via MiniLM
  - `cosine_similarity(vec1, vec2)` - Similarity calculation
  - `find_similar(query, embeddings, top_k)` - Top-k lookup
**Files:** `know/src/embeddings.py`

### 3. Implement embeddings file management
**What:** Load/save embeddings with hash-based change detection
**How:**
  - Hash each node's text content
  - Store hash alongside vector
  - On rebuild, skip unchanged nodes
**Files:** `know/src/embeddings.py`

### 4. Add `know embed` command
**What:** Full rebuild of embeddings
**How:** Add command to CLI that:
  - Loads graph
  - Extracts text from all nodes
  - Generates embeddings
  - Saves to `.ai/embeddings.json`
**Files:** `know/know.py`

### 5. Add `know find <query>` command
**What:** Semantic search across graph
**How:**
  - Embed query string
  - Compute cosine similarity against all vectors
  - Return top-k results with scores
**Files:** `know/know.py`

### 6. Add `know suggest <entity>` command
**What:** Find similar nodes for dependency suggestions
**How:**
  - Get embedding for specified entity
  - Find most similar nodes (excluding self)
  - Filter by valid dependency rules
  - Present as suggestions
**Files:** `know/know.py`

### 7. Hook into modification commands
**What:** Auto-regenerate embeddings on graph changes
**How:** After `add`, `link`, `unlink` complete:
  - Check if embeddings file exists
  - If yes, incrementally update affected nodes
**Files:** `know/know.py`

## Dependencies
- Steps 2-7 depend on Step 1 (dependency installed)
- Steps 4-7 depend on Step 2 (core module)
- Step 7 depends on Steps 4-6 (commands exist)

## Validation
- [ ] All tests pass
- [ ] Graph validates successfully
- [ ] `know embed` generates embeddings file
- [ ] `know find "query"` returns relevant results
- [ ] `know suggest entity:x` returns valid suggestions
- [ ] Incremental updates work correctly
