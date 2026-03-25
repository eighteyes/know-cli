# Architectural Decisions

---

## 2026-03-25 — Rename `phase` → `horizon`

**Decision:** Replace "phase" with "horizon" as the term for planning waves in the spec-graph.

**Rationale:**
Projects don't move through discrete phases like assembly lines — work exists at different distances from the present. Horizon I is imminent and clear. Horizon II is approaching and roughly defined. Horizon III is forming in the distance; its shape may change before you reach it.

"Phase" implies a waterfall sequence: you complete phase 1, then enter phase 2. "Horizon" implies perspective and uncertainty: what's close is clear, what's far is hazy. Features in H:III may not survive contact with reality — and that's expected, not a failure.

Done features have no horizon. They exist outside the planning wave entirely.

**Tradeoffs considered:**
- `Ring` — concentric priority, no uncertainty signal
- `Wave` — literal but reads awkward as a label ("Wave III")
- `Reach` — nautical, clean, but obscure
- `Horizon` — planning pedigree (McKinsey Three Horizons), distance = uncertainty, reads naturally in sentences

**Scope of change:** CLI (`know horizons`), dashboard kanban columns, spec-graph `meta.horizons`, all source files. Migration shim in `GraphManager.get_graph()` auto-upgrades old graphs on first load.

**Commit range:** `53727228` → `5d1d076` on `main`
