import { useState } from "react";

const STEPS = [
  {
    num: "01",
    title: "Plan",
    desc: "Specialised agents design the premise, cast, chapter structure, and style profile from your creative brief. You approve the direction before anything gets written.",
  },
  {
    num: "02",
    title: "Draft",
    desc: "Every scene is drafted three to five times in parallel, each attempt pursuing a different rhetorical strategy — one restrained and subtext-heavy, another lyrical, another stripped back to the bone. The strongest version is selected.",
  },
  {
    num: "03",
    title: "Validate",
    desc: "Fifteen specialised critics evaluate each draft for continuity, point of view, dramatic tension, voice consistency, dialogue quality, thematic integration, and more.",
  },
  {
    num: "04",
    title: "Repair",
    desc: "When a draft fails validation, a targeted rewriter fixes the specific problems — a POV slip, a banned phrase, a continuity error — while leaving everything else intact.",
  },
  {
    num: "05",
    title: "Analyse",
    desc: "The system tracks fifty-four types of literary device across the manuscript, flagging overuse, clumping, imagery monoculture, and the kind of rhetorical habits that make AI prose feel monotonous.",
  },
  {
    num: "06",
    title: "Revise",
    desc: "After all scenes are drafted, manuscript-level audits check that promises pay off, character arcs land, and themes are dramatised rather than stated. If a late chapter exposes weak preparation, the system revises earlier scenes.",
  },
];

const FEATURES = [
  {
    title: "Explicit story state",
    desc: "Character knowledge, timelines, and narrative promises are tracked in a database, so the system reasons about the story rather than guessing from prose alone.",
  },
  {
    title: "Deliberate variation",
    desc: "Branches represent genuine rhetorical alternatives — subtext-heavy, lyrical, compressed, intimate — rather than random paraphrases of the same approach.",
  },
  {
    title: "Fifty-four device types",
    desc: "The system detects literary devices from alliteration to subtext exchange, using both rule-based pattern matching and model-based analysis, and alerts when any device becomes a crutch.",
  },
  {
    title: "Model tiering",
    desc: "The most capable model handles pivotal creative decisions, a fast workhorse model drafts and critiques, and a lightweight model runs mechanical validation. You pay for intelligence where it matters.",
  },
  {
    title: "Backward propagation",
    desc: "When a payoff in chapter thirty falls flat, the system identifies which earlier scenes need strengthening and rewrites them to seed better preparation.",
  },
  {
    title: "Context files",
    desc: "You can drop style guides, character sketches, sample prose, or plot outlines into a folder, and the system incorporates them into every decision it makes.",
  },
];

function App() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-border bg-paper/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <span className="text-lg font-semibold tracking-tight">postwriter</span>
          <div className="flex items-center gap-6">
            <a href="#how" className="text-sm text-muted hover:text-ink transition-colors">How it works</a>
            <a href="#features" className="text-sm text-muted hover:text-ink transition-colors">Features</a>
            <a href="#install" className="text-sm text-muted hover:text-ink transition-colors">Install</a>
            <a
              href="https://github.com/avigold/postwriter"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted hover:text-ink transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-3xl px-6 pt-24 pb-20 text-center">
        <div className="mb-6 inline-block rounded-full border border-accent/20 bg-accent/5 px-4 py-1.5 text-sm font-medium text-accent">
          Early access &mdash; free during beta
        </div>
        <h1 className="text-5xl font-bold tracking-tight leading-[1.1] sm:text-6xl">
          A novel is an
          <br />
          <span className="text-accent">engineering problem.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted">
          Postwriter generates complete, manuscript-length fiction through
          multi-pass orchestration — planning the structure, drafting each scene
          in competing stylistic variations, validating against explicit story state,
          and revising at the level of the whole book.
        </p>
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <a
            href="#install"
            className="rounded-lg bg-accent px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-accent/25 transition-all hover:bg-accent-light hover:shadow-xl hover:shadow-accent/30"
          >
            Get started
          </a>
          <a
            href="https://github.com/avigold/postwriter"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-border px-6 py-3 text-sm font-semibold transition-colors hover:bg-ink/5"
          >
            View on GitHub
          </a>
        </div>
      </section>

      {/* Terminal preview */}
      <section className="mx-auto max-w-4xl px-6 pb-20">
        <div className="overflow-hidden rounded-xl border border-border bg-ink shadow-2xl">
          <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
            <div className="h-3 w-3 rounded-full bg-red-500/70" />
            <div className="h-3 w-3 rounded-full bg-yellow-500/70" />
            <div className="h-3 w-3 rounded-full bg-green-500/70" />
            <span className="ml-3 font-mono text-xs text-white/40">postwriter</span>
          </div>
          <pre className="overflow-x-auto p-6 font-mono text-sm leading-relaxed text-green-400/90">
{`$ postwriter --profile high_quality

  POSTWRITER
  Orchestrated Long-Form Fiction

  Context Files
  ────────────────────────────────────────
    Found 5 context file(s):
      characters: characters.md
      plot: premise.md
      style: style-guide.md

  ⠧ Designing the premise...
  ✓ Premise approved

  ⠧ Building the structural spine...
  ✓ 3 acts, 34 chapters, 112 scenes

  Drafting Chapter 1: The Invitation
    ⠧ Chasing the voice...
    ✓ restrained_subtext_heavy (1,203 words, score=0.81)
    ⠧ Fabulating...
    ✓ intimate_free_indirect (987 words, score=0.77)

  Drafting ██████████░░░░░░░░░░ 34% — 28,441 words`}
          </pre>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="border-t border-border bg-white py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-3xl font-bold tracking-tight">
            How it works
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-muted">
            A single generation pass can't sustain a novel. Postwriter runs
            six distinct phases, each with its own agents and objectives,
            to produce fiction that holds together across a full manuscript.
          </p>
          <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {STEPS.map((step) => (
              <div key={step.num} className="group">
                <div className="mb-3 font-mono text-sm font-semibold text-accent">
                  {step.num}
                </div>
                <h3 className="mb-2 text-lg font-semibold">{step.title}</h3>
                <p className="text-sm leading-relaxed text-muted">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-border py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-3xl font-bold tracking-tight">
            What makes it different
          </h2>
          <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="rounded-xl border border-border p-6 transition-colors hover:border-accent/30 hover:bg-accent/[0.02]"
              >
                <h3 className="mb-2 text-base font-semibold">{f.title}</h3>
                <p className="text-sm leading-relaxed text-muted">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Install */}
      <section id="install" className="border-t border-border bg-white py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold tracking-tight">Get started</h2>
          <div className="mx-auto mt-10 max-w-xl text-left">
            <div className="overflow-hidden rounded-xl border border-border bg-ink">
              <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
                <div className="h-3 w-3 rounded-full bg-red-500/70" />
                <div className="h-3 w-3 rounded-full bg-yellow-500/70" />
                <div className="h-3 w-3 rounded-full bg-green-500/70" />
              </div>
              <pre className="overflow-x-auto p-6 font-mono text-sm leading-loose text-green-400/90">
{`$ git clone https://github.com/avigold/postwriter.git
$ cd postwriter && uv sync
$ uv run postwriter`}
              </pre>
            </div>
          </div>
          <p className="mt-6 text-sm text-muted">
            Requires Python 3.12+ and Docker for the database layer.
            The{" "}
            <a
              href="https://github.com/avigold/postwriter#quick-start"
              className="text-accent underline decoration-accent/30 hover:decoration-accent"
            >
              setup guide
            </a>{" "}
            covers everything in detail.
          </p>
        </div>
      </section>

      {/* Waitlist */}
      <section className="border-t border-border py-20">
        <div className="mx-auto max-w-xl px-6 text-center">
          <h2 className="text-3xl font-bold tracking-tight">Hosted version coming soon</h2>
          <p className="mt-4 text-muted">
            We're building a hosted version that handles the infrastructure
            for you. Leave your email if you'd like early access when it launches.
          </p>
          {submitted ? (
            <div className="mt-8 rounded-lg border border-green-200 bg-green-50 px-6 py-4 text-green-800">
              You're on the list.
            </div>
          ) : (
            <form
              className="mt-8 flex flex-col gap-3 sm:flex-row"
              onSubmit={(e) => {
                e.preventDefault();
                if (email) setSubmitted(true);
              }}
            >
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="flex-1 rounded-lg border border-border px-4 py-3 text-sm outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent/20"
              />
              <button
                type="submit"
                className="rounded-lg bg-accent px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-accent/25 transition-all hover:bg-accent-light"
              >
                Notify me
              </button>
            </form>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-10">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 text-sm text-muted">
          <span>&copy; {new Date().getFullYear()} Postwriter</span>
          <a
            href="https://github.com/avigold/postwriter"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-ink transition-colors"
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}

export default App;
