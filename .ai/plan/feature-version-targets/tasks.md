# Tasks

## Phase 1 — Data
- [x] Set `version=0.2.1` on 5 complete features (manual JSON patch via python since no CLI yet)

## Phase 2 — CLI
- [x] `horizons_add`: accept `--version`, persist to entry
- [x] `horizons_status`: preserve existing fields (don't clobber version)
- [x] `horizons_move`: preserve version when moving
- [x] New `feature version <feature:key> <semver>` command — sets version on whichever horizon entry the feature currently lives in
- [x] Semver regex validation `^\d+\.\d+\.\d+(-[\w.]+)?$`

## Phase 3 — Validator
- [x] `validation.py`: warn if feature has `status=complete` and no `version`

## Phase 4 — Featurelog
- [x] New `feature log <semver>` command
- [x] Output: markdown, grouped by objective, sections per feature with name + description
- [x] Include features whose horizon entry matches the requested version

## Verification
- [x] `know graph check validate` runs without new errors
- [x] `know feature log 0.2.1` prints all 5 shipped features
- [x] `know horizons status feature:X merge-ready` preserves pre-existing version
