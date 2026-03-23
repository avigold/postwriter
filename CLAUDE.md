# CLAUDE.md

## Project: Orchestrated Long-Form Fiction System

This document specifies an ambitious system for generating, repairing, analysing, and iterating long-form fiction using a hierarchy of specialised agents, explicit story state, multi-pass critique, graph-based stylistic analytics, and global revision loops. The target is not mere draft generation. The target is a system that can sustain long-horizon narrative control, stylistic variety, and cumulative artistic pressure across an entire manuscript.

The system should assume that raw one-pass generation is inadequate for serious fiction.

---

## 1. Objective

Build an orchestration framework for long-form fiction that:

- plans at multiple narrative scales
- drafts at scene level
- maintains explicit canonical story state outside the prose
- audits continuity, causality, voice, and device use
- performs constrained repair loops
- tracks literary and stylistic devices across the manuscript as graphs
- detects overuse, clumping, monotony, and functional repetition
- suggests or applies stylistic interventions when appropriate
- supports branching and late global restructuring
- preserves optional human intervention at high-aesthetic decision points

The system should optimise for:

- narrative coherence
- long-range payoff integrity
- emotional credibility
- stylistic freshness
- voice stability
- thematic density without explicit overstatement
- avoidance of repetitive rhetorical crutches
- revision traceability

The system should not assume that literary merit is fully specifiable. It should therefore distinguish between:
- hard violations
- soft weaknesses
- aesthetic risks
- human-judgement nodes

---

## 2. Non-goals

This system is not a generic chatbot.
This system is not a one-shot novel generator.
This system is not a simple outline-to-prose expander.
This system is not merely a grammar-polishing pipeline.
This system is not limited to genre pulp, though it should be able to operate there.

---

## 3. Core design principle

Treat the manuscript as four linked but distinct representations:

1. **Text layer**
   - the prose itself

2. **Story-state layer**
   - facts, causality, character states, timeline, unresolved obligations, thematic seeds, world state

3. **Stylistic layer**
   - voice targets, diction band, rhythm band, imagery ecology, rhetorical preferences, banned tics, tolerated densities

4. **Analytical layer**
   - validator outputs, soft scores, graph metrics, device distributions, revision lineage, branch comparisons

No important reasoning should depend on prose alone if it can instead depend on structured state.

---

## 4. Manuscript operating model

The system should work hierarchically:

- premise
- controlling design / spine
- acts or macro-movements
- chapters
- scenes
- beats
- local prose spans
- sentence-level stylistic repair

Each level should have:
- its own representation
- its own goals
- its own validator types
- its own revision loop
- explicit dependency links upward and downward

A scene writer should not be forced to infer the entire novel.
A global reviser should not flatten local scene energy.

---

## 5. Architecture overview

### 5.1 Primary subsystems

- Orchestrator
- Canon store
- Narrative planning layer
- Drafting layer
- Validation layer
- Soft criticism layer
- Device annotation layer
- Graph analytics layer
- Repair planner
- Local rewriter
- Branch manager
- Global revision manager
- Human review interface
- Observability and trace layer

### 5.2 Execution model

The system should run as a stateful orchestration graph rather than a single loop.

Possible execution phases:

1. project bootstrap
2. narrative design
3. chapter and scene planning
4. branch drafting
5. scene-level validation
6. scene-level repair
7. branch selection or retention
8. chapter-level harmonisation
9. manuscript-level graph analysis
10. backward repair propagation
11. global revision passes
12. export, inspection, and optional human intervention

---

## 6. Canonical data model

The prose must not be treated as the source of truth for the manuscript. Use explicit state objects.

### 6.1 Character model

Each character should include:

- stable identifier
- name
- aliases
- age / apparent age if relevant
- biography
- motives
- fears
- desires
- secrets
- social position
- relationship graph
- speaking traits
- movement traits
- recurring gestures
- moral constraints
- knowledge state by scene
- emotional state by scene
- intention state by scene
- world-state influence links
- unresolved pressures
- arc hypotheses
- realised arc history

### 6.2 Scene model

Each scene should include:

- stable identifier
- chapter affiliation
- absolute and relative ordering
- POV
- location
- time marker
- immediate purpose
- conflict
- stakes
- revelation
- emotional turn
- dominant dramatic function
- setup links
- payoff links
- themes touched
- symbols touched
- relevant promises
- canonical state mutations
- expected stylistic profile
- expected device functions
- current accepted draft
- branch set
- local scores
- validator issues
- downstream dependency links

### 6.3 Chapter model

Each chapter should include:

- title or placeholder
- chapter function
- emotional contour target
- scene list
- transition profile
- opening and closing pressure
- thematic density target
- motif target
- contrast relation to neighbouring chapters
- rhythm profile

### 6.4 Promise / obligation model

A promise is anything that creates a future burden.

Include:
- plot promises
- emotional promises
- thematic promises
- symbolic promises
- tonal promises
- rhetorical promises

Each promise should include:

- identifier
- type
- description
- introducer scene
- salience
- maturity window
- expected resolution window
- current status
- linked scenes
- actual resolution scene
- strength of payoff

### 6.5 Timeline event model

Each event should include:

- identifier
- description
- absolute time if known
- relative time if known
- participants
- preconditions
- consequences
- witnesses
- knowledge propagation rules
- contradiction risk flags

### 6.6 Theme model

Each theme should include:

- identifier
- name
- description
- associated symbols
- associated conflicts
- associated character tensions
- target density over manuscript
- intensity target by chapter
- current manifestation history
- risk of overstatement
- preferred modes of embodiment

### 6.7 Style profile model

The style profile should be explicit and evolveable.

Include:

- narrative voice description
- degree of directness
- subtext target
- irony target
- lyricism target
- sentence length bands
- sentence variance bands
- dialogue density band
- metaphor density band
- simile density band
- fragment tolerance
- exposition tolerance
- abstraction tolerance
- preferred imagery domains
- banned imagery domains
- banned phrases
- banned moves
- disfavoured rhetorical devices
- maximum recurrence caps for selected devices
- chapter-level modulation rules

---

## 7. Agent roles

### 7.1 Master orchestrator

Responsibilities:

- task decomposition
- state coordination
- ordering of passes
- conflict resolution between critics
- repair priority ranking
- branch retention policy
- stop conditions
- escalation to stronger models or human review
- revision budget allocation
- long-range dependency management

The orchestrator should reason in terms of system state, not just prose.

### 7.2 Architect agent

Responsibilities:

- define controlling design
- define structural spine
- propose act logic or equivalent macro shape
- define chapter progression
- identify burdens of setup and payoff
- define arc hypotheses

### 7.3 Chapter planner

Responsibilities:

- convert macro shape into chapter-level units
- define chapter role
- define local contrast
- distribute pressure and release
- distribute revelations and concealments

### 7.4 Scene planner

Responsibilities:

- create precise scene briefs
- define conflict, turn, revelation, burden, target functions
- define prohibited moves
- define expected state mutations
- define optional stylistic envelope

### 7.5 Scene writer

Responsibilities:

- generate scene prose from brief plus local canon slice
- obey POV, chronology, and state constraints
- preserve intended dramatic movement
- write to profile without imitating surface gimmicks

### 7.6 Critic agents

Use narrow critic roles rather than one universal critic.

Possible critics:

- continuity critic
- timeline critic
- POV critic
- knowledge-state critic
- dramatic-tension critic
- emotional-credibility critic
- thematic critic
- dialogue critic
- prose-vitality critic
- voice-consistency critic
- redundancy critic
- symbolic-overstatement critic
- stylistic-device critic
- imagery-ecology critic
- scene-purpose critic
- chapter-transition critic
- branch-diversity critic

### 7.7 Repair planner

Responsibilities:

- merge hard issues, soft weaknesses, graph penalties, and scene objectives
- produce ordered, isolated rewrite tasks
- preserve what works
- avoid global rewrite when local repair suffices

### 7.8 Local rewriter

Responsibilities:

- rewrite only targeted spans or dimensions
- obey preserve constraints
- avoid collateral damage
- avoid gratuitous paraphrase

### 7.9 Global reviser

Responsibilities:

- inspect whole-book effects
- propose backward propagation
- reshape earlier setup if later payoff is weak
- reduce stylistic monoculture
- smooth chapter-level rhythm problems
- strengthen underprepared emotional turns

### 7.10 Human reviewer

The system should assume human review is valuable at:
- tie-breaks between strong branches
- structurally important scenes
- symbolic density risk
- late global revisions
- cases where prose is compliant but inert

---

## 8. Validation model

Distinguish hard and soft validation.

### 8.1 Hard validators

Hard validators should emit pass/fail plus evidence.

Examples:

- canon consistency
- timeline legality
- POV legality
- name and referent integrity
- knowledge-state legality
- relationship-state legality
- location continuity
- forbidden phrase detection
- prohibited move detection
- setup/payoff ledger legality
- branch-state compatibility
- duplication of banned passages
- world-rule legality

Hard failure should block acceptance.

### 8.2 Soft critics

Soft critics should emit:
- scalar scores
- textual diagnosis
- span references
- repair opportunities
- confidence

Examples:

- tension
- emotional credibility
- scene purpose clarity
- prose vitality
- voice stability
- thematic integration
- dialogue force
- subtlety
- redundancy
- chapter opening distinctiveness
- chapter closing distinctiveness
- transition quality
- image freshness
- symbolic restraint
- stylistic freshness

Soft critics should never be treated as ground truth. They are advisory with influence.

---

## 9. Device annotation and graphing system

This is central.

The system should detect, classify, track, score, and visualise literary and stylistic devices over the entire manuscript.

### 9.1 Goals

- detect overuse of a device
- detect burstiness or clumping
- detect monotony of device-function mapping
- detect character-specific tics unless intended
- detect narrator tics
- detect imagery-domain monoculture
- detect symbolic monoculture
- identify underused but suitable device families
- support scene-level repair and manuscript-level revision

### 9.2 Device taxonomy

This should be broad and extensible.

#### Lexical / syntactic devices
- alliteration
- assonance where tractable
- anaphora
- epistrophe
- polyptoton
- parallelism
- rhetorical question
- triadic construction
- sentence fragment
- periodic sentence
- cumulative sentence
- inversion
- parataxis
- hypotaxis
- polysyndeton
- asyndeton
- deliberate lexical recurrence

#### Figurative devices
- metaphor
- simile
- metonymy
- synecdoche
- personification
- hyperbole
- understatement
- irony
- paradox
- symbol recurrence
- motif recurrence
- objective correlative candidate patterns

#### Narrative / discourse devices
- foreshadowing
- callback
- echo
- delayed revelation
- withheld information
- free indirect discourse
- interior monologue
- exposition block
- scenic expansion
- summary compression
- tonal pivot
- misdirection
- recognition beat
- reversal beat
- silence beat
- evasive reply
- loaded object reference
- subtext exchange

#### Rhythm and prose-motion devices
- long periodic build
- clipped acceleration
- dialogue volley
- paragraph contraction
- paragraph dilation
- rhythmic echo
- syntax-pressure cluster

### 9.3 Device instance schema

Each detected device instance should include:

- id
- scene id
- chapter id
- paragraph or span references
- device type
- subtype if relevant
- estimated function
- speaker / focaliser if relevant
- imagery domain if relevant
- intensity
- confidence
- novelty score relative to rolling window
- local burden relation if any
- whether it is intentional or accidental if inferable

### 9.4 Graph types

#### Temporal device graph
Nodes:
- scenes or chapters
- device types

Purpose:
- find burstiness
- find clustering
- find dry zones
- find patterned alternation

#### Character-device graph
Nodes:
- characters
- device types

Purpose:
- detect voice tics
- detect accidental homogenisation
- detect narrator dominance

#### Theme-device graph
Nodes:
- themes
- symbols
- devices
- scenes

Purpose:
- detect over-explicit theming
- detect one-note symbolic strategy
- inspect embodiment diversity

#### Function-device graph
Nodes:
- narrative functions
- device types

Purpose:
- detect overreliance on the same rhetorical solution for the same dramatic problem

Example:
If every concealment beat becomes evasive dialogue plus rhetorical questions, penalise.

#### Imagery-domain graph
Nodes:
- imagery domains
- scenes
- characters
- functions

Purpose:
- detect metaphor source-domain monoculture
- detect domain crowding in local windows
- detect poor scene-to-scene variation

#### Rhythm graph
Nodes:
- scenes / chapters
- sentence-length stats
- paragraph-length stats
- dialogue/exposition ratio
- punctuation-density profile

Purpose:
- detect monotony in prose motion

### 9.5 Metrics

Track at least:

- count
- density per 1000 words
- rolling-window density
- burstiness
- average gap between occurrences
- functional diversity
- character concentration
- narrator concentration
- imagery-domain concentration
- novelty mean
- recurrence regularity
- local clumping severity
- chapter-level repetition index

### 9.6 Device overuse rules

Overuse should not be defined only by raw count.

A device may be overused if any of these hold:
- high local density in a short rolling window
- repeated use for the same function in adjacent scenes
- repeated use by the same character beyond intended voice profile
- repeated use in chapter openings or closings
- repeated use with the same imagery domain
- repeated use in moments of similar dramatic pressure

### 9.7 Underuse / appropriateness rules

The system should sometimes recommend device usage when functionally suitable.

Examples:
- a concealment scene may benefit from subtext exchange
- an obsession scene may benefit from controlled lexical recurrence
- a formal public scene may benefit from periodic syntax or parallelism
- a panic scene may benefit from syntactic contraction or clipped sequencing
- a scene of brittle politeness may benefit from silence beats or loaded object references

These are suggestions, not compulsory ornamentation.

The system should never chase device diversity for its own sake.

---

## 10. Appropriateness model

The system needs a model that answers:
“Would a device help here, and if so which family is apt?”

This should combine:

- scene purpose
- emotional turn
- POV
- chapter context
- local style profile
- recent device use
- character-specific voice rules
- imagery saturation
- thematic explicitness risk

The model should output:
- candidate device families
- reasons
- estimated appropriateness score
- risks of use in this context

The model should be conservative.
Plain prose is often preferable.

---

## 11. Branching model

The system should branch deliberately.

### 11.1 Branch purpose

Branches should represent:
- different rhetorical modes
- different scene temperatures
- different concealment strategies
- different symbolic intensities
- different pacing strategies

Branches should not represent random paraphrases.

### 11.2 Possible branch labels

Examples:
- restrained_subtext_heavy
- lyrical_image_forward
- sparse_pressure_through_silence
- formal_cold_surface
- intimate_free_indirect
- aggressively compressed
- scenic_expansion_high_tension

### 11.3 Retention policy

Do not collapse branches too early.

Retain multiple branches when:
- scores are close
- later scenes may reveal downstream superiority
- scene is structurally pivotal
- local compliance is high but aesthetic profile differs meaningfully

### 11.4 Downstream evaluation

A branch should be scored partly by how well it supports:
- later payoff
- arc plausibility
- thematic burden
- stylistic ecology
- chapter rhythm

---

## 12. Repair system

### 12.1 Repair philosophy

Repair should be:
- narrow
- ordered
- traceable
- reversible
- minimally destructive

### 12.2 Repair priority

1. hard legality
2. canon continuity
3. knowledge-state legality
4. setup/payoff burden errors
5. dramatic clarity failures
6. emotional credibility failures
7. voice drift
8. device overuse or monotony
9. rhythmic stagnation
10. optional enrichment

### 12.3 Repair action schema

Each repair action should include:
- priority
- target dimension
- target span
- issue reference
- instruction
- preserve constraints
- allowed intervention classes
- banned interventions

### 12.4 Typical repair classes

- continuity correction
- POV correction
- knowledge correction
- burden reinforcement
- tension intensification
- dialogue de-explication
- rhythm variation
- imagery diversification
- device substitution
- device removal
- device softening
- chapter transition smoothing
- motif restraint

### 12.5 Example repair prompts

#### Device overuse
Revise only the marked span.
The scene currently overuses rhetorical questions and triadic parallelism.
Preserve emotional force and voice.
Replace the repeated rhetorical strategy with one of:
- silence beat
- loaded object reference
- asymmetrical reply
- sentence compression
Avoid weather and fire imagery.

#### Directness reduction
The scene states concealed resentment too openly.
Increase subtext through evasion, selection of detail, and refusal of direct answer.
Do not add irony.
Keep POV and chronology intact.

#### Imagery ecology repair
This chapter overuses body and fire imagery in adjacent scenes.
Revise the marked paragraph so that its pressure comes from syntax and object relation rather than figurative comparison.

---

## 13. Scoring model

The system should keep separate:
- hard pass status
- local soft quality
- graph ecology
- downstream stability
- risk

### 13.1 Suggested soft score dimensions

- tension
- emotional credibility
- prose vitality
- voice stability
- thematic integration
- dialogue quality
- redundancy inverse
- stylistic freshness
- transition quality
- symbolic restraint

### 13.2 Device-balance component

Device-balance should include:
- overuse penalty
- burstiness penalty
- same-function same-device penalty
- same-character tic penalty
- narrator tic penalty
- imagery saturation penalty
- underuse opportunity penalty where critics already find the scene flat

### 13.3 Candidate selection

A candidate should be selected based on:
- hard pass
- local quality
- graph ecology
- downstream stability
- canon risk
- chapter fit

No single scalar should dominate absolutely.
Keep the vector, even if a composite is used for ranking.

---

## 14. Global revision passes

After local acceptance, run manuscript-level passes.

### 14.1 Promise audit
Inspect:
- unresolved promises
- prematurely discharged promises
- underprepared resolutions
- duplicated resolutions
- weak emotional payoffs

### 14.2 Character arc audit
Inspect:
- emotional jumps
- motivational collapse
- knowledge contradictions
- weak accumulations
- unearned transformations

### 14.3 Device ecology audit
Inspect:
- chapter-level clumping
- narrator tic accumulation
- same-function same-device recurrence
- repetitive openings and closings
- imagery monoculture
- motif over-regularity

### 14.4 Rhythm audit
Inspect:
- sentence-length monotony
- paragraph-size monotony
- dialogue ratio stagnation
- repeated cadence in climactic scenes
- chapter opening sameness
- chapter ending sameness

### 14.5 Thematic overstatement audit
Inspect:
- themes stated instead of dramatised
- too-regular symbol recurrence
- explicitness spikes
- repeated “meaning delivery” sentences

### 14.6 Backward propagation
If late scenes expose weaknesses in earlier preparation, the system should propose and optionally execute backward repairs.

Examples:
- strengthen an early glance into obsession
- seed a later betrayal more quietly
- reduce on-the-nose thematic summary in a midpoint chapter
- diversify early symbolic scaffolding

---

## 15. Human-in-the-loop policy

Human review should be available anywhere, but especially at:

- premise and controlling design approval
- chapter-sequence approval
- structurally pivotal scene selection
- branch tie-breaks
- symbol-density disputes
- late backward propagation
- manuscript final pass

The system should expose evidence for decisions rather than merely producing revised text.

---

## 16. Observability

A system like this is useless if opaque.

Expose:

- scene score cards
- validator logs
- repair history
- branch comparisons
- device graphs
- imagery-domain heatmaps
- rhythm charts
- promise ledgers
- knowledge-state maps
- chapter pressure maps
- unresolved obligation dashboards

### 16.1 Essential dashboards

#### Scene dashboard
Show:
- accepted draft
- branch list
- hard issues
- soft scores
- device detections
- repair actions
- downstream dependency notes

#### Manuscript dashboard
Show:
- promise map
- chapter pressure contour
- device frequency over time
- imagery-domain distribution
- theme embodiment map
- rhythm graph
- character arc state graph
- unresolved obligation ledger

---

## 17. Storage and infrastructure

A practical implementation could use:

- PostgreSQL for canonical state and metadata
- object storage for draft text and diff snapshots
- Redis or a work queue for orchestration jobs
- Python services for orchestration, validation, graphing, and model calls
- vector retrieval only for local canon slicing if helpful
- notebook or dashboard layer for analytics
- append-only event log for traceability

Do not make the graph database choice premature.
Simple adjacency structures are sufficient initially.

---

## 18. Suggested Python module layout

```text
fiction_system/
  orchestrator/
    engine.py
    policies.py
    stop_conditions.py
    branch_management.py

  canon/
    models.py
    store.py
    serializers.py
    mutation_rules.py

  planning/
    architect.py
    chapter_planner.py
    scene_planner.py
    burden_allocator.py

  drafting/
    scene_writer.py
    branch_profiles.py
    prompt_builders.py

  validation/
    hard/
      continuity.py
      timeline.py
      pov.py
      knowledge.py
      banned_patterns.py
      setup_payoff.py
    soft/
      tension.py
      emotion.py
      prose_vitality.py
      dialogue.py
      thematic.py
      redundancy.py
      transitions.py

  devices/
    taxonomy.py
    detectors_rule_based.py
    detectors_model_based.py
    function_inference.py
    imagery_domains.py
    annotation.py

  graphs/
    temporal.py
    character_device.py
    theme_device.py
    function_device.py
    imagery.py
    rhythm.py
    metrics.py
    snapshots.py

  repair/
    planner.py
    actions.py
    local_rewriter.py
    prompts.py

  revision/
    promise_audit.py
    arc_audit.py
    device_ecology.py
    rhythm_audit.py
    theme_overstatement.py
    backward_propagation.py

  scoring/
    composite.py
    vectors.py
    thresholds.py

  ui/
    dashboards.py
    scene_views.py
    manuscript_views.py

  infra/
    llm_client.py
    queue.py
    storage.py
    logging.py
```

---

## 19. Pseudocode skeleton

```python
class FictionOrchestrator:
    def run(self, manuscript):
        self.bootstrap(manuscript)
        self.plan_manuscript(manuscript)

        for chapter in manuscript.chapters:
            self.process_chapter(manuscript, chapter)

        self.run_global_revision_passes(manuscript)
        self.finalise(manuscript)
        return manuscript

    def process_chapter(self, manuscript, chapter):
        for scene_id in chapter.scene_ids:
            brief = manuscript.scenes[scene_id]
            branches = self.generate_branches(manuscript, brief)

            evaluated = []
            for draft in branches:
                repaired = self.repair_loop(manuscript, brief, draft)
                evaluated.append(repaired)

            chosen = self.select_or_retain(manuscript, brief, evaluated)
            self.commit_scene(manuscript, brief, chosen)

    def repair_loop(self, manuscript, brief, draft):
        prev_score = None

        for _ in range(self.max_repair_rounds):
            hard_issues = self.run_hard_validators(manuscript, brief, draft)
            soft = self.run_soft_critics(manuscript, brief, draft)
            devices = self.annotate_devices(brief, draft)
            graph_snapshot = self.preview_graph_impact(manuscript, brief, draft, devices)

            decision = self.evaluate_candidate(
                hard_issues=hard_issues,
                soft_scores=soft.scores,
                graph_snapshot=graph_snapshot,
                manuscript=manuscript,
                brief=brief,
                draft=draft,
            )

            if decision.accept:
                return draft

            if prev_score is not None and decision.score - prev_score < self.min_delta:
                return draft

            repair_plan = self.plan_repairs(
                manuscript=manuscript,
                brief=brief,
                draft=draft,
                hard_issues=hard_issues,
                soft=soft,
                graph_snapshot=graph_snapshot,
            )

            draft = self.apply_repairs(manuscript, brief, draft, repair_plan)
            prev_score = decision.score

        return draft
```

---

## 20. Ambitious research extensions

These are optional but within scope.

### 20.1 Learned aesthetic preference model
Train a manuscript-level preference model from:
- human pairwise scene judgements
- branch-selection history
- revision acceptance behaviour
- strong-vs-weak passage comparisons

### 20.2 Delayed downstream scoring
Allow a scene’s final score to update after later scenes are drafted, based on:
- payoff adequacy
- arc support
- thematic burden
- symbolic preparation
- chapter rhythm contribution

### 20.3 Style memory beyond surface mimicry
Model:
- syntactic distribution
- image ecology
- explanatory habits
- concealment patterns
- scene transition habits
rather than mere lexical imitation

### 20.4 Symbolic burden ledger
Track symbols with:
- current salience
- ambiguity level
- overstatement risk
- last manifestation mode
- character association
- thematic load

### 20.5 Counterfactual branch simulation
Estimate downstream effects if a branch is chosen:
- does it narrow later emotional options?
- does it overdetermine a theme?
- does it consume a symbol too early?
- does it lock a voice pattern into monotony?

---

## 21. Failure modes

The system should explicitly guard against these:

### 21.1 Proxy optimisation
Writing to the metric rather than to the effect.

### 21.2 Decorative diversity
Varying devices mechanically without making prose better.

### 21.3 Repair flattening
Too many passes draining force from scenes.

### 21.4 Symbol inflation
Themes becoming visible scaffolding rather than lived structure.

### 21.5 False device certainty
Weak detector guesses being treated as truth.

### 21.6 Critic monoculture
All critics inheriting the same bland preferences.

### 21.7 Voice sterilisation
Over-regularising prose into expensive mediocrity.

### 21.8 Premature convergence
Selecting a merely competent branch too early.

### 21.9 Hidden canon drift
Unrecorded local changes breaking global logic.

### 21.10 Analytics tyranny
Graphs dominating judgement in places where judgement should dominate graphs.

---

## 22. Implementation principles

- Preserve structured state outside prose.
- Keep agents narrow.
- Separate hard legality from soft quality.
- Repair locally before rewriting globally.
- Preserve branches when uncertainty is real.
- Make graphs advisory but consequential.
- Prefer evidence-rich diagnostics to vague critique.
- Use human review at genuinely aesthetic decision points.
- Track all state mutations and revision lineage.
- Allow ambition in scope without pretending quality is fully measurable.

---

## 23. Operating assumptions for Claude

When implementing or extending this system:

- assume one-shot long-form excellence is unreliable
- assume long-range narrative burdens must be explicit
- assume stylistic freshness degrades without monitoring
- assume device overuse is often local and cumulative
- assume “appropriate use” of devices depends on function, context, and recent ecology
- assume plainness is sometimes superior to ornamental variation
- assume backward revision is often necessary
- assume human judgement remains necessary in literary edge cases

---

## 24. Deliverables Claude should be prepared to produce from this spec

Claude should be able to generate any of the following on request:

- Python class structures for the canonical models
- scoring formulas and threshold policies
- graph schemas and graph metric implementations
- rule-based device detectors
- model-based device annotation prompts
- repair planner logic
- branch selection logic
- scene dashboard specifications
- manuscript dashboard specifications
- queue/job orchestration patterns
- database schema proposals
- end-to-end pseudocode
- concrete repo layout
- prompt templates for each agent role
- evaluation harnesses
- example test fixtures for scenes, chapters, and full manuscripts

---

## 25. Immediate next task suggestion

A good first implementation step is to define:

1. canonical Python dataclasses
2. hard validator interfaces
3. soft critic interfaces
4. device annotation schema
5. graph metric service
6. repair plan schema
7. scene orchestration loop
8. branch scoring function

Build those first. Do not begin with a complete aesthetic engine.
