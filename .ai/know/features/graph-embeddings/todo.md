# TODO: graph-embeddings

See [plan.md](./plan.md) for implementation details.

## Checklist

- [ ] 1. Add `sentence-transformers` dependency
- [ ] 2. Create `know/src/embeddings.py` module
- [ ] 3. Implement text extraction from graph nodes
- [ ] 4. Implement embedding generation with MiniLM
- [ ] 5. Implement embeddings file I/O (`.ai/embeddings.json`)
- [ ] 6. Implement incremental update logic (hash-based change detection)
- [ ] 7. Add `know embed` command (rebuild all embeddings)
- [ ] 8. Add `know find <query>` command (semantic search)
- [ ] 9. Add `know suggest <entity>` command (similar nodes)
- [ ] 10. Hook embedding regeneration into `know add/link/unlink`
- [ ] 11. Add graph entities to spec-graph.json
- [ ] 12. Validate graph
- [ ] 13. Test implementation

## Notes
- Model: `all-MiniLM-L6-v2` (384 dimensions)
- First run will download ~90MB model to cache
- Embeddings file will be ~10-50KB for typical graphs
