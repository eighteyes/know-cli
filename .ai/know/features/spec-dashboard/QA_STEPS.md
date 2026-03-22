# QA Steps: spec-dashboard

## Prerequisites
- Run `know serve` from the project root
- Browser opens to http://127.0.0.1:5173

## Test Steps

### 1. Initial Load
- [ ] Dashboard loads with kanban board showing features in phase columns
- [ ] Master nav shows user and objective filter pills at top
- [ ] Validation banner appears if graph has structural issues
- [ ] All features from spec-graph.json appear in their correct phase column
- [ ] Features with no phase assignment appear in "Unphased" column

### 2. Feature Card Display
- [ ] Each card shows feature name and description snippet
- [ ] Entity count pills show on cards (e.g. "3 actions", "2 components")
- [ ] Cards have a left border colored for the feature type

### 3. Sidecard Drilldown
- [ ] Click a feature card → sidecard slides in from right
- [ ] Sidecard header shows feature name (click to edit inline)
- [ ] Breadcrumb shows parent chain: user › objective › feature
- [ ] Actions, components, operations listed in accordion sections
- [ ] Click accordion item → expands to show description and sub-dependencies
- [ ] References section shows linked reference types

### 4. Master Nav Filtering
- [ ] Click a user pill → kanban filters to features under that user's objectives
- [ ] Click same user pill again → filter clears
- [ ] Click an objective pill → kanban filters to features under that objective
- [ ] Filters compose correctly (user + objective)

### 5. CRUD: Add Entity
- [ ] Click "+ Feature" in nav → modal opens
- [ ] Fill in type, key, name, description → click Create
- [ ] New entity appears (in kanban if feature, in sidecard if other type)
- [ ] Click "+ Add entity" in sidecard → modal opens with parent pre-set
- [ ] Created entity is automatically linked to the parent

### 6. CRUD: Edit Entity
- [ ] Click feature name in sidecard → becomes editable input
- [ ] Change name, press Enter → name updates
- [ ] Click description → becomes editable textarea
- [ ] Change description, click away → description updates

### 7. CRUD: Link/Unlink
- [ ] Click "+ Link existing" in sidecard → link modal opens
- [ ] Search for entity by name/type → click to link
- [ ] Entity appears in sidecard's dependency list
- [ ] Click × (unlink) button on an entity row → entity removed from dependencies

### 8. CRUD: Change Phase (Drag & Drop)
- [ ] Drag a feature card from one column to another
- [ ] Card moves to the target column
- [ ] Phase assignment persists (refresh page to verify)

### 9. Validation
- [ ] Banner shows issue count and first few issues on load
- [ ] Click × to dismiss banner
- [ ] Entities with issues show relevant pills/badges

### 10. Error Handling
- [ ] Try adding entity with empty key → error toast appears
- [ ] Try linking to non-existent entity → error toast with CLI message
- [ ] Close sidecard with × button → returns to kanban-only view

## Acceptance Criteria
- [ ] All features visible in correct kanban columns
- [ ] Sidecard shows correct parent + child hierarchy
- [ ] All CRUD operations persist to spec-graph.json
- [ ] Validation banner shows on structural issues
- [ ] No console errors during normal operation
