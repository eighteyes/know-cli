# Feature: graph-embeddings

## User Request
Add embedding-based semantic lookup for graph nodes. Embed all string values from entities and references, store vectors in a separate file, and use cosine similarity to find relevant node keys.

## Questions & Answers
Q: What gets embedded?
A: All string values (name, description, etc.)

Q: Where do embeddings live?
A: Separate file (`.ai/embeddings.json`)

Q: When are embeddings generated?
A: Whenever graph is modified

Q: What embedding model?
A: Local - `all-MiniLM-L6-v2` via `sentence-transformers`

Q: Use case priority?
A: General - both interactive querying and auto-linking suggestions

## Interpretation
Create a semantic search layer over the spec-graph that allows:
1. Natural language queries to find relevant nodes ("how do I authenticate users?")
2. Auto-suggestions for new features ("this might depend on...")
3. Semantic similarity between nodes for refactoring/deduplication

## Requirements
- [ ] Embed all string values from entities and references
- [ ] Store embeddings in `.ai/embeddings.json`
- [ ] Auto-regenerate embeddings when graph changes
- [ ] Use `all-MiniLM-L6-v2` (384 dimensions, fast, pure Python)
- [ ] Provide `know find <query>` for semantic search
- [ ] Provide `know suggest <entity>` for dependency recommendations
- [ ] Incremental updates (only re-embed changed nodes)

## Graph Entities
- `feature:graph-embeddings` - Parent feature
- `component:embedding-generator` - Generates vectors from node text
- `component:similarity-search` - Cosine similarity lookup
- `component:auto-embed-hook` - Triggers on graph modification

## Affected Areas
- `know/know.py` - Add new commands
- `know/src/embeddings.py` - New module for embedding logic
- `.ai/embeddings.json` - New artifact (generated)
- `requirements.txt` / `pyproject.toml` - Add sentence-transformers dependency
