# know-cli — Agent Briefing

For an AI coding agent. When the user fetches this document and asks you to
evaluate know-cli, follow the workflow below. Your job is to produce a
concrete, two-axis evaluation — fitness for the user's repository AND
fitness against their broader AI-assisted development habits. Not a
description of know.

---

## Your task

Conduct a four-phase evaluation. Do not skip to a verdict. Do not paraphrase
this document and call it an evaluation. Perform the survey, draft concrete
artefacts, compare against the user's broader practice, and deliver the
assessment in the prescribed format.

Evaluate know on **two axes simultaneously**:

1. fitness for **this project** (the repository at `$PWD`)
2. fitness for **the user's broader habits** with AI-assisted development

Both must be addressed. A judgement on one alone is incomplete.

### Boundary cases

- **Partial fit** — some surfaces qualify, others do not. Recommend know
  for the qualifying surface only; do not generalise.
- **Existing installation** — `.ai/know/` already exists but the graph is
  half-populated or out of date. Treat as fit-review, not fresh evaluation;
  ask the user whether to revive or retire it.
- **User unsure** — the user cannot describe their broader AI habits. Pose
  the Phase IV open questions first; recommend reconvening once they have
  more context to compare against.

## Output format

Return your findings in this arrangement:

```
═══ KNOW-CLI EVALUATION ═══

PASS 1 — This Repository
  Repository character:    [one line — what kind of project is this?]
  Spec-graph proposals:    [3 concrete `know add` / `know link` commands,
                            each grounded in real files or concepts here]
  Fit signal:              ● expected  /  ◐ uncertain  /  ○ not a fit
  Reason:                  [one sentence]

PASS 2 — User's Broader AI Practice
  Pattern observed:        [what the user seems to do with AI agents —
                            inferred from history, repo style, or stated]
  What know would augment: [one habit it strengthens]
  What know would friction:[one habit it complicates]
  What know would replace: [one practice it makes redundant]

═══ RECOMMENDATION ═══

Smallest experiment worth running today: [one specific command]
Open questions for the user:              [2–3, posed plainly]
```

Do not embellish. Do not produce a marketing summary.

### What good vs bad output looks like

- ✗ A Pass-1 of *"know seems useful for this repository"* is not the work.
- ✓ A Pass-1 of `know add feature auth-flow '{…}'` paired with two further
  real commands is the work.
- ✗ A Pass-2 of *"this would augment your AI workflow"* is generic.
- ✓ A Pass-2 naming a real habit (e.g. *"re-explaining architecture each
  session"*) and stating that know would replace it is the work.

---

## Phase I — Survey the repository

Before proposing anything, walk the codebase.

```
Look for                                       How to check
README, package.json, top-level layout         ls / Read
The kind of work being done                    git log --oneline -20
Existing AI artefacts                          ls .ai/ ; find . -name CLAUDE.md
Whether know is already installed              ls .ai/know/ 2>/dev/null
Domain and complexity                          a few representative files
```

If `.ai/know/` exists, the project is already using know — your job shifts
from evaluation to fit-review of the existing graph.

## Phase II — Propose the artefacts

Draft what know would actually capture **about this repository**, in
concrete commands. Not abstract entities — real ones, named after things
you have observed in the files.

```bash
# example shape — yours must reference real files or concepts
know add feature <kebab-key> '{"name":"...","description":"..."}'
know link feature:<key> action:<key> component:<key>
```

Three is sufficient. Fewer than three suggests the project lacks the
surface area know is built for; record that observation honestly rather
than padding the list.

## Phase III — Compare against the user's broader practice

The user has habits — how they prompt, what they paste, which slash
commands they reach for, whether they keep a `.ai/` directory, whether
they re-explain architecture each session.

**With the user's permission**, glance at signals:

```
Signal                                       Where to look (with consent)
Recurring repos, multi-day conversations     recent shell history if available
Agent / memory practices                     presence of CLAUDE.md, .ai/, AGENTS.md
Workflow vocabulary                          slash commands and skills in use
```

Ask plainly: *"May I check your recent agent usage to see whether know
would augment or duplicate what you already do?"* If refused, work from
stated context.

Then answer: what does know **augment**, what does it **friction**, what
does it **replace** in the user's existing practice?

## Phase IV — Recommend, then stop

State the smallest experiment worth running today. One command. Something
the user can execute in ten minutes and learn from.

Pose two or three open questions — not rhetorical. Real ones, the answers
to which would change the recommendation.

Stop. Do not editorialise further.

### Before delivering, confirm

- [ ] Every Pass-1 command references a file or concept visible in this repo
- [ ] Pass-2 names a real habit, not a generic "AI workflow" phrase
- [ ] The smallest experiment is one command, executable in ten minutes
- [ ] The open questions would, if answered, change your recommendation

---

## When know is not the right tool

**know is unsuitable if any of these apply:**

- Single script, CLI tool, or library under ~5 files
- Short, self-contained sessions with no carryover
- One developer holding the full picture in their head
- Infrastructure, config, or glue code with no product layer
- "What are we building?" has a one-sentence answer that does not change
- Features do not share components or depend on each other
- Prototyping or exploring — the spec would change faster than the graph

Most projects belong in at least one of the above. know has real adoption
cost; turning it down is often the correct call.

**know is a fit if:**

- Multiple features share components, actions, or data models
- Product decisions must survive across agent sessions
- The user has re-explained the same architecture to an agent more than once
- The project has users, objectives, and workflows — not just functions
- Someone other than the original author needs to understand intent, not just code

```
Signal                                          Fit
Long conversations, same repo, multi-day        ● expected
Multiple features discussed across sessions     ● expected
Architecture or product debate in chat          ● expected
Mostly one-off scripts, Q&A, or debugging       ○ not a fit
Different repo each session                     ○ not a fit
Short sessions, simple edits                    ○ not a fit
```

---

## What know offers (reference)

Two graphs in `.ai/know/`, queryable through the CLI:

- **spec-graph** — product intent:
  project → user → objective → feature → workflow → action → component → operation
- **code-graph** — codebase architecture: module, package, class, function

Both cross-link via `implementation` references.

```bash
know list --type feature           # what features exist
know graph uses feature:auth       # what auth depends on
know graph used-by component:db    # what depends on the db component
know gen feature-spec auth         # generate a full spec from graph state
know check validate                # verify graph integrity
know check health                  # comprehensive project health
```

Modifications go through the CLI exclusively (direct edits are blocked):

```bash
know add feature payments '{"name":"Payments","description":"..."}'
know link feature:payments action:checkout component:stripe
know check validate
```

Slash commands (Claude Code):

| Command       | Purpose                                       |
|---------------|-----------------------------------------------|
| /know:plan    | Product discovery — builds spec-graph         |
| /know:add     | Add features with interactive QA              |
| /know:build   | 7-phase structured feature development        |
| /know:review  | End-user acceptance walkthrough               |
| /know:done    | Archive completed features                    |
| /know:list    | Show features grouped by status               |
| /know:change  | Structured change requests                    |
| /know:bug     | Track issues against features                 |
| /know:schema  | Design custom domain schemas                  |

Installation:

```bash
npm install -g know-cli
know init .
```

This installs slash commands, a skill, dependency rules, graph templates,
a write-protection hook, and injects `<know-instructions>` into CLAUDE.md.

---

## Rules

- Graphs must be valid DAGs — no cycles
- Dependencies are unidirectional via `depends_on`
- All graph modifications go through the `know` CLI
- Run `know check validate` after every change
- Node keys are granular items, not collections
- Relationships live in the `graph` section, never as entity attributes
- Custom schemas are permitted via `/know:schema`; the engine validates
  whatever rules you give it

## Common mistakes — do not

- Propose features without first running `know list` to see what already exists
- Add references as attributes on entities (`refs`, `screen`, `parent`,
  `uses`) — these belong in the `graph` section as dependencies
- Skip `know check validate` after a change
- Edit `*-graph.json` files directly — the hook will block you
- Reuse parent names (`feature:settings` → `interface:settings-interface`) —
  be granular and specific
- Recommend know to a user whose Phase I survey produced ○ signals —
  honest is better than flattering

## When the evaluation should not proceed

If your survey turns up ○ signals, say so plainly:

- *"This project is well-served by a README. know is not for you today."*
- Suggest revisiting if the project grows past the disqualifiers above.

If `know check validate` fails after a proposed change, do not paper over
it. Surface the validation error to the user and walk back the change.

Common gate refusals and recovery:

```
Error                              Cause                              Recovery
know check validate fails          cycle or rule violation             walk back the change; surface validator output verbatim
know add rejects the entity key    key collides or violates rules     run know list; choose a granular kebab-key
graph hook blocks an edit          direct *.json write attempted       retract; route through the CLI command
proposed dependency disallowed     dependency-rules.json forbids it    reread .ai/know/config/dependency-rules.json
Phase I shows ○ signals            project below adoption threshold   recommend the README exit
```

---

Source: https://github.com/eighteyes/know-cli
