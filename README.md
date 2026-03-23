# Postwriter

An orchestrated system for generating long-form fiction. Postwriter treats novel writing as a multi-pass engineering problem — planning at multiple narrative scales, drafting with stylistic variation, validating against explicit story state, and revising with manuscript-level awareness.

The target is not one-shot draft generation. The target is sustained narrative control, stylistic freshness, and cumulative artistic pressure across an entire manuscript.

## What it does

Postwriter generates a complete novel (~80k words) through a pipeline of specialized AI agents:

1. **Plan** — An architect agent designs the premise, structural spine, characters, style profile, chapters, and scenes. You approve the premise and act structure at human checkpoints.

2. **Draft** — Each scene is drafted 3–5 times in parallel using distinct stylistic profiles (subtext-heavy, lyrical, compressed, etc.). Branches are not random paraphrases — they represent different rhetorical strategies.

3. **Validate** — 5 hard validators (continuity, timeline, POV, knowledge state, banned patterns) gate acceptance. 10 soft critics score tension, emotion, prose vitality, voice consistency, dialogue, thematic integration, redundancy, transitions, scene purpose, and symbolic restraint.

4. **Repair** — Failed drafts enter a targeted repair loop (up to 3 rounds). The repair planner prioritizes issues, and a local rewriter fixes specific problems while preserving what works.

5. **Analyze** — Literary devices are detected across the manuscript (54 types, rule-based and model-based), tracked in temporal graphs, and evaluated for overuse, burstiness, imagery monoculture, and functional repetition.

6. **Revise** — Manuscript-level audits check promises, character arcs, device ecology, rhythm, and thematic overstatement. A backward propagation engine modifies earlier scenes to strengthen later payoffs.

7. **Export** — The final manuscript exports as markdown, with a full JSON canonical state dump and a generation report.

## How it works

The manuscript is maintained as four linked representations:

- **Text layer** — the prose itself
- **Story-state layer** — facts, causality, character states, timeline, unresolved obligations
- **Stylistic layer** — voice targets, device preferences, imagery ecology, banned phrases
- **Analytical layer** — validator outputs, scores, device distributions, revision lineage

No important reasoning depends on prose alone when it can instead depend on structured state.

## Quick start

### Prerequisites

- Python 3.12+
- Docker (for PostgreSQL and Redis)
- An Anthropic API key

### Install

```bash
git clone https://github.com/avigold/postwriter.git
cd postwriter
uv sync
```

### Start infrastructure

```bash
docker compose up -d
uv run alembic upgrade head
```

### Configure

```bash
echo "PW_LLM_ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
```

### Run

```bash
uv run postwriter new
```

This walks you through an interactive bootstrap, then runs the full pipeline: plan → draft → revise → export.

### Options

```bash
# Use a generation profile
uv run postwriter new --profile fast_draft      # Fewer branches, faster
uv run postwriter new --profile high_quality    # More branches, more repair rounds
uv run postwriter new --profile budget_conscious # Minimize API costs

# Export a completed manuscript
uv run postwriter export <manuscript-id> --format all

# View manuscript dashboard
uv run postwriter dashboard <manuscript-id>

# List profiles
uv run postwriter profiles
```

## Context files

Drop markdown or image files into a `context/` directory to inform the writing. These are optional — if they're there, the system uses them; if not, it asks you everything interactively.

```
context/
  style-guide.md      # Voice and prose preferences
  characters.md       # Character sketches
  plot-outline.md     # Story beats or synopsis
  mood-board.png      # Visual references
```

Files can include YAML frontmatter to specify their type:

```markdown
---
type: style
---
Write in short, declarative sentences. Avoid adverbs.
```

Supported types: `sample_writing`, `plot`, `guidelines`, `characters`, `world`, `style`, `reference`. Without frontmatter, the system infers type from the filename.

Context files can be added at any time during generation. New files affect future scenes (forward-only — no retroactive re-evaluation).

## Architecture

```
postwriter/
  agents/          # 10 specialized agents (architect, planner, writer, critics, rewriter)
  canon/           # Canonical data store, context slicing, event logging
  cli/             # Interactive CLI with rich terminal dashboards
  context/         # User-provided reference file loader
  db/              # Async PostgreSQL via SQLAlchemy 2.0, Alembic migrations
  devices/         # Literary device detection (54 types), imagery classification
  export/          # Markdown, JSON, and report exporters
  graphs/          # Temporal device graphs and ecology metrics
  llm/             # Anthropic SDK wrapper with Opus/Sonnet/Haiku tiering
  models/          # 21 database tables covering the full canonical data model
  orchestrator/    # Scene loop, branch management, global revision, checkpointing
  prompts/         # Jinja2 prompt templates for all agent roles
  repair/          # Repair planner and action specifications
  revision/        # 5 manuscript-level audit passes + backward propagation
  scoring/         # 11-dimension score vectors, Pareto comparison, device balance
  validation/      # 5 hard validators + 10 soft critics
```

### Model tiering

| Tier | Role | Used for |
|------|------|----------|
| Opus | Creative judgment | Premise design, act structure, pivotal scene branches |
| Sonnet | Workhorse | Scene drafting, soft critics, repair, chapter/scene planning |
| Haiku | Mechanical checks | Hard validators, device detection, state extraction |

### Key design principles

- Structured state outside prose — the database is the source of truth, not the text
- Narrow agents — each agent does one thing well
- Hard legality vs soft quality — separate concerns, separate priorities
- Repair locally before rewriting globally
- Branches represent rhetorical strategies, not random variation
- Graphs are advisory but consequential
- Human review at genuinely aesthetic decision points
- Plain prose is sometimes superior to ornamental variation

## Tests

```bash
uv run pytest tests/ -v
```

165 tests covering models, canon store, all validators and critics, device detection, graph metrics, scoring, repair planning, revision audits, export, and configuration profiles. Tests use a real PostgreSQL instance (Docker) for database tests and mock LLM responses for agent tests.

## License

TBD
