import { useState } from "react";

const STEPS = [
  {
    num: "01",
    title: "Plan",
    desc: "Architect agents design the premise, characters, structure, and style profile. You approve the creative direction.",
  },
  {
    num: "02",
    title: "Draft",
    desc: "Each scene is drafted 3\u20135 times in parallel using distinct stylistic strategies. Not paraphrases \u2014 different rhetorical approaches.",
  },
  {
    num: "03",
    title: "Validate",
    desc: "15 specialised critics check continuity, POV, tension, voice, dialogue, thematic integration, and more.",
  },
  {
    num: "04",
    title: "Repair",
    desc: "Targeted rewrites fix specific problems while preserving what works. No gratuitous paraphrase. No flattening.",
  },
  {
    num: "05",
    title: "Analyse",
    desc: "54 literary device types tracked across the manuscript. Overuse, burstiness, imagery monoculture \u2014 all monitored.",
  },
  {
    num: "06",
    title: "Revise",
    desc: "Manuscript-level audits check promises, arcs, rhythm, and theme. Backward propagation strengthens earlier scenes.",
  },
];

const FEATURES = [
  {
    title: "Explicit story state",
    desc: "The database is the source of truth, not the prose. Character knowledge, timelines, promises \u2014 all tracked.",
  },
  {
    title: "Branching, not paraphrasing",
    desc: "Branches represent rhetorical strategies: subtext-heavy, lyrical, compressed, intimate. The best is selected.",
  },
  {
    title: "54 device types",
    desc: "From alliteration to subtext exchange. Rule-based and model-based detection. Overuse alerts.",
  },
  {
    title: "Model tiering",
    desc: "Opus for pivotal creative decisions. Sonnet for drafting. Haiku for mechanical validation. Cost-efficient by design.",
  },
  {
    title: "Backward propagation",
    desc: "Weak payoffs in chapter 30? The system modifies chapter 8 to seed better preparation.",
  },
  {
    title: "Context files",
    desc: "Drop in style guides, character notes, or sample writing. The system adapts to your creative vision.",
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
          AI that writes novels,
          <br />
          <span className="text-accent">not first drafts.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted">
          Postwriter is an orchestrated system for generating complete, high-quality
          long-form fiction. Multi-pass planning, branching, validation, and revision
          across an entire manuscript. Not a chatbot. Not a one-shot generator.
          A system.
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
{`$ postwriter new --profile high_quality

  POSTWRITER
  Orchestrated Long-Form Fiction

  Context Files
  ────────────────────────────────────────
    Found 5 context file(s):
      characters: characters.md
      plot: premise.md
      style: style-guide.md

  Generating Premise (opus)...
  ✓ Premise approved

  Designing Act Structure (opus)...
  ✓ 3 acts, 34 chapters, 112 scenes

  Drafting Chapter 1: The Invitation
    Scene 1: 3 branches generated
    ✓ Accepted: restrained_subtext_heavy (1,203 words, score=0.81)
    Scene 2: 3 branches generated
    ✓ Accepted: intimate_free_indirect (987 words, score=0.77)

  Drafting ██████████░░░░░░░░░░ 34% — 28,441 words`}
          </pre>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="border-t border-border bg-white py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-3xl font-bold tracking-tight">
            Six passes. One manuscript.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-muted">
            Raw one-pass generation is inadequate for serious fiction.
            Postwriter treats novel writing as an engineering problem with
            multiple stages of refinement.
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
            Built for long-horizon narrative control
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
          <h2 className="text-3xl font-bold tracking-tight">Get started in three commands</h2>
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
$ uv run postwriter new`}
              </pre>
            </div>
          </div>
          <p className="mt-6 text-sm text-muted">
            Requires Python 3.12+ and Docker. See the{" "}
            <a
              href="https://github.com/avigold/postwriter#quick-start"
              className="text-accent underline decoration-accent/30 hover:decoration-accent"
            >
              full setup guide
            </a>{" "}
            for details.
          </p>
        </div>
      </section>

      {/* Waitlist */}
      <section className="border-t border-border py-20">
        <div className="mx-auto max-w-xl px-6 text-center">
          <h2 className="text-3xl font-bold tracking-tight">Hosted version coming soon</h2>
          <p className="mt-4 text-muted">
            No setup, no API keys. Just write. Leave your email and we'll
            notify you when the hosted version launches.
          </p>
          {submitted ? (
            <div className="mt-8 rounded-lg border border-green-200 bg-green-50 px-6 py-4 text-green-800">
              You're on the list. We'll be in touch.
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
