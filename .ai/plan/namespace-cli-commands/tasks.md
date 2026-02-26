# Namespace CLI Commands - Tasks

- [x] Define new click groups: entity, graph, check, gen, feature
- [x] Define check link subgroup under check
- [x] Move each command under its group
- [x] Merge list-type into list with --type option
- [x] Rename: suggest → connect, validate-feature → validate, tag-feature → tag
- [x] Delete: migrate-contracts, requirements alias, dead spec (line 469), dead coverage (line 280)
- [x] Pass context_settings to all new groups
- [x] Update CLAUDE.md command examples
- [x] Update .claude/skills/know-tool/SKILL.md
- [x] Update README.md
- [x] Update .claude/commands/know/*.md (13 files)
- [x] Update know/templates/commands/*.md (10 files)
- [x] Update .claude/skills/know-tool/references/*.md
- [x] Update .claude/skills/know-tool/marketplace.json
- [x] Update .claude/agents/feature-effort-estimator.md
- [x] Update .claude/settings.local.json
- [x] Verify all command groups via `know -h`
- [x] Verify functional tests (entity list, check validate, graph uses, etc.)
