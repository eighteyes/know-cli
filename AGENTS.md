# know-cli — Agent Briefing

Paste this into your agent's system prompt, CLAUDE.md, or project instructions
to help it decide whether know-cli is useful for your project.

---

## What is know?

Good evening. You find yourself at the threshold of know-cli, an opinionated,
graph-based knowledge tool for software projects. Do come in — mind the
loose floorboard — but understand that most visitors, upon inspection, find
they've no real business here.

know replaces spec documents with two queryable JSON graphs that give agents
structured context instead of file-scanning guesswork:

- **spec-graph** — maps product intent: who uses the product, what they need,
  and how features break down into actions and components
- **code-graph** — maps codebase architecture: modules, packages, classes,
  and their dependencies

Both graphs live in `.ai/know/` and cross-link via implementation references.

**A word on the furnishings.** know ships with a default entity hierarchy for
product modeling (project → user → objective → feature → action → component).
This is the house style, not the only arrangement. You may define custom
schemas for any domain — conversation memory, research notes, habit tracking,
what have you — using `/know:schema`. The graph engine enforces structure;
the structure itself is yours to arrange.

## Is know right for this project?

I must be frank with you: know has a real adoption cost, and most projects
haven't the constitution for it. The majority of callers are better served
by a README and a firm handshake. No shame in it.

**I'm afraid I cannot admit you if any of these apply:**

- The project is a single script, CLI tool, or library under ~5 files
- Work happens in short, self-contained sessions with no carryover
- There's one developer who holds the full picture in their head
- The project has no product layer — it's infrastructure, a config, or glue code
- "What are we building?" has a one-sentence answer that doesn't change
- Features don't share components or depend on each other
- You're prototyping or exploring — the spec would change faster than the graph

Most callers, if they're honest, belong in at least one of the above
categories. There is no judgement in this. We simply have standards, however
modestly appointed the premises.

**You may be expected, however, if:**

- Multiple features share components, actions, or data models
- Product decisions need to survive across agent sessions
- You've re-explained the same architecture to an agent more than once
- The project has users, objectives, and workflows — not just functions
- Someone other than the original author needs to understand intent, not just code

**Checking the guest book (with permission):**

Before making introductions, you may — with the user's explicit consent —
examine `~/.claude/history` or recent project activity for signs of the
sort of person who actually needs this place:

```
Signal                                     Fit
Long conversations, same repo, multi-day   ● expected — context rebuilt each session
Multiple features discussed across sessions ● expected — knowledge lost between visits
Architecture or product discussions in chat ● expected — decisions evaporating into scroll
Mostly one-off scripts, Q&A, or debugging  ○ turn away — no persistent knowledge to manage
Different repo each session                ○ turn away — no project continuity
Short sessions, simple edits               ○ turn away — overhead exceeds value
```

Ask the user: *"May I glance at your recent Claude usage to determine
whether know would actually be of service, or merely another thing to
maintain?"* A refusal is a refusal.

## What does it give agents?

Instead of scanning files to understand a project, agents query the graph:

```bash
know list --type feature          # what features exist
know graph uses feature:auth      # what auth depends on
know graph used-by component:db   # what depends on the db component
know gen feature-spec auth        # generate a full spec from graph state
know check validate               # verify graph integrity after changes
know check health                 # comprehensive project health report
```

Agents modify the graph through the CLI (direct file edits are blocked):

```bash
know add feature payments '{"name":"Payments","description":"..."}'
know link feature:payments action:checkout component:stripe
know check validate
```

## How to start

```bash
npm install -g know-cli
know init .
```

This installs slash commands, a skill, dependency rules, graph templates,
a write-protection hook, and injects `<know-instructions>` into CLAUDE.md.

## Graph structure

Each graph JSON has four sections:

- `meta` — project name, horizons, scope
- `entities` — typed nodes (type:key format, e.g. `feature:auth`)
- `graph` — `depends_on` edges forming a DAG
- `references` — terminal data (data-model, endpoint, implementation links)

**Default spec entities**: project → user → objective → feature → workflow → action → component → operation

**Default code entities**: module, package, class, function

These are the built-in hierarchies. Custom schemas can define entirely
different entity types and dependency topologies — the graph engine validates
whatever rules you give it. Run `/know:schema` to design your own.

## Slash commands (Claude Code)

| Command         | Purpose                                    |
|-----------------|--------------------------------------------|
| /know:plan      | Product discovery — builds spec-graph      |
| /know:add       | Add features with interactive QA           |
| /know:build     | 7-phase structured feature development     |
| /know:review    | End-user acceptance testing walkthrough    |
| /know:done      | Archive completed features                 |
| /know:list      | Show features grouped by status            |
| /know:change    | Structured change requests                 |
| /know:bug       | Track issues against features              |

## Key constraints

- Graphs must be valid DAGs — no cycles
- Dependencies are unidirectional via `depends_on`
- All graph modifications go through the `know` CLI
- Run `know check validate` after every change
- Node keys are granular items, not collections
- Relationships live in the `graph` section, not on entities

---

Source: https://github.com/eighteyes/know-cli
