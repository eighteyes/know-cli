# Architecture Alternatives: workflow-branch-entity

## Summary Comparison

| Aspect | Minimal Changes | Clean Architecture | Pragmatic Balanced |
|--------|----------------|-------------------|-------------------|
| **LOC** | ~170 new | ~600 new | ~300 new |
| **Files touched** | 4 | 8+ (new modules) | 6 |
| **Effort** | 70 min | 2-3 days | 8 hours |
| **Maintainability** | Medium | Excellent | Good |
| **Extensibility** | Low | Excellent | Medium |
| **Risk** | Low | Medium | Low |
| **Grade** | B | A | B+ |

---

## Minimal Changes Approach

**Philosophy:** Reuse everything. Quick path to MVP.

**Key decisions:**
- Direct graph manipulation in CLI commands
- No new modules, inline workflow logic
- Minimal validation (reuse existing)
- NetworkX doesn't track order (stored in JSON only)
- ~170 LOC, 4 files, 70 minutes

**Pros:**
- ✅ Fastest implementation
- ✅ Minimal risk (small change surface)
- ✅ Reuses all existing patterns

**Cons:**
- ❌ Workflow logic scattered (know.py, graph.py, validation.py)
- ❌ No abstraction for ordered dependencies
- ❌ Hard to extend (add workflow features later)
- ❌ Mixed concerns in CLI commands

**Trade-offs cut:**
- No migration script
- NetworkX ignores order (can't use graph algorithms on ordered deps)
- No transaction safety for batch operations
- No workflow-specific visualization

---

## Clean Architecture Approach

**Philosophy:** Ideal design. Long-term maintainability.

**Key decisions:**
- New domain abstractions (DependencyCollection, WorkflowEntity, OrderedDependencyManager)
- Strategy pattern for dependency types
- Layered architecture (CLI → Application → Domain → Infrastructure)
- Rich validation with suggestions
- ~600 LOC, 8+ files, 2-3 days

**Pros:**
- ✅ Single Responsibility everywhere
- ✅ Highly testable (domain logic isolated)
- ✅ Easy to extend (plugin system, hooks)
- ✅ Type safety with value objects
- ✅ Clear boundaries

**Cons:**
- ❌ Significant implementation effort
- ❌ Overengineered for current scope
- ❌ More code to maintain
- ❌ Learning curve for contributors

**Extension points:**
- Registry pattern for entity types
- Hook system for lifecycle events
- Strategy pattern for dependency types
- Validation rule plugins

---

## Pragmatic Balanced Approach (RECOMMENDED)

**Philosophy:** Best trade-off between clean design and speed.

**Key decisions:**
- New `workflow.py` module (single-purpose)
- NetworkX edge attributes for order
- Extend existing validators (don't replace)
- Reuse CLI patterns (add flags, not commands)
- ~300 LOC, 6 files, 8 hours

**Pros:**
- ✅ Clean separation (workflow.py)
- ✅ NetworkX understands order (edge attributes)
- ✅ Extends existing patterns
- ✅ Testable in isolation
- ✅ Zero breaking changes
- ✅ Reasonable effort (8 hours)

**Cons:**
- ⚠️ Mixed mode might confuse users (mitigated with validation)
- ⚠️ Auto-create could create noise (opt-in flag)

**Implementation order:**
1. Config (dependency-rules.json) - 0.5h
2. Core (graph.py, entities.py) - 3h
3. New module (workflow.py) - 2h
4. Validation extensions - 1h
5. CLI commands - 1.5h

---

## Recommendation

**Choose: Pragmatic Balanced**

**Rationale:**
- 8 hours vs 70 min (acceptable) vs 2-3 days (excessive)
- Clean enough for future extension
- Fast enough to ship this week
- Low risk (extends, doesn't replace)
- NetworkX edge attributes give us ordering for free

**Next steps if approved:**
1. Update dependency-rules.json
2. Modify graph.py (edge attributes, diff tracking)
3. Create workflow.py module
4. Extend validation
5. Add CLI commands
6. Manual testing checklist
