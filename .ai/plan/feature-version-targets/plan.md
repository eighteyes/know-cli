# Feature Version Targets

Add version tracking to feature entries in `meta.horizons` so shipped features can be grouped into a generated changelog.

## Spec (locked via MCQ)

- **Schema**: `meta.horizons.<I|II|III|IV|V>.feature:<key>.version` — optional string, sits beside `status`
- **Value**: plain semver string, e.g. `"0.2.1"`
- **Validation**: warn (not error) if `status == complete` and no `version`
- **Backfill**: 5 recently-completed features (horizons-migration, decisions-logging, mcq-planning, args-injection, confirmation-removal) → `0.2.1`; in-progress features stay blank
- **CLI**: both `know horizons add/status --version …` and new `know feature version feature:X X.Y.Z`
- **Bonus**: `know feature log <version>` emits markdown changelog

## Phases (one sitting)

1. **Data** — backfill 5 features with `version: "0.2.1"`
2. **CLI** — `--version` on `horizons add`, preserve-field patch for `horizons status`, new `feature version` command
3. **Validator** — warn on `status=complete` + missing version
4. **Featurelog** — `know feature log <version>` → markdown grouped by objective

## Grade
B+. Narrow, all edits live in `know/know.py` and `src/validation.py`. Main risk: `horizons status` currently clobbers the whole entry — must patch not overwrite.
