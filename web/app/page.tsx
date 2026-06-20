import Link from "next/link";

const STEPS = [
  { n: "01", t: "Connect", d: "Plug in your data sources, social handles, and Discord in under two minutes." },
  { n: "02", t: "Monitor & interview", d: "Agents watch every signal surface 24/7 and talk to your customers by voice, SMS, or chat." },
  { n: "03", t: "Act", d: "Get insights, campaigns, and founder packets with a shippable fix attached." },
];

const METRICS = [
  { v: "24/7", l: "always-on coverage" },
  { v: "9", l: "live integrations" },
  { v: "<2 min", l: "to first monitor" },
];

const FEATURES = [
  ["Listen — find insight", "Monitor every signal surface 24/7 — web, news, Reddit. Surface revenue opportunities, cost leaks, and anomalies, then recommend marketing grounded in real feedback."],
  ["Talk — live interviews", "Interview your customers by Discord, browser voice, SMS, phone call, or video + screen share. Their answers become validated product work."],
  ["Fix — forward-deployed", "A bug on your site? It diagnoses, patches a copy in an isolated sandbox (never prod), validates, and ships a live preview URL."],
  ["Edit — make it better", "‘Make the product photo cleaner, less hefty.’ AI edits the image, copy, and format — by voice or text."],
];

const STACK = ["Anthropic", "Browserbase", "Gemini", "Daily", "Deepgram", "Twilio", "Discord", "Convex", "Redis"];

function Section({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`mx-auto max-w-5xl px-6 ${className}`}>{children}</section>;
}

export default function Home() {
  return (
    <div className="flex flex-col gap-24 pb-24">
      {/* Top bar */}
      <header className="sticky top-0 z-20 border-b border-white/10 bg-black/70 backdrop-blur">
        <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <span className="text-sm font-semibold tracking-tight">
            Two<span className="text-emerald-400">Customer</span>
          </span>
          <div className="flex items-center gap-3 text-sm">
            <Link href="/sign-in" className="text-white/60 hover:text-white">
              Sign in
            </Link>
            <Link href="/admin" className="rounded-md bg-emerald-500 px-3 py-1.5 text-xs font-medium text-black hover:bg-emerald-400">
              Open dashboard
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <Section className="flex min-h-[78vh] flex-col items-center justify-center gap-7 text-center">
        <span className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-widest text-white/50">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Live · 9 integrations connected
        </span>
        <h1 className="text-balance text-5xl font-semibold leading-tight sm:text-6xl">
          The AI forward-deployed agent team for consumer brands.
        </h1>
        <p className="max-w-2xl text-balance text-lg text-white/60">
          Connect your data and channels. TwoCustomer works 24/7 to monitor every
          signal, interview your customers, fix what&apos;s broken, and act —
          before you miss it.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/sign-in" className="rounded-lg bg-emerald-500 px-5 py-2.5 text-sm font-medium text-black hover:bg-emerald-400">
            Sign in →
          </Link>
          <Link href="/monitor" className="rounded-lg border border-white/15 px-5 py-2.5 text-sm font-medium hover:border-emerald-400/50">
            Watch it work (live feed)
          </Link>
        </div>
        <div className="mt-6 flex gap-10">
          {METRICS.map((m) => (
            <div key={m.l} className="text-center">
              <div className="text-2xl font-semibold text-emerald-400">{m.v}</div>
              <div className="text-xs text-white/45">{m.l}</div>
            </div>
          ))}
        </div>
      </Section>

      {/* How it works */}
      <Section>
        <h2 className="mb-8 text-center text-sm uppercase tracking-widest text-white/40">How it works</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="text-3xl font-semibold text-white/15">{s.n}</div>
              <h3 className="mt-2 text-lg font-medium">{s.t}</h3>
              <p className="mt-1 text-sm text-white/55">{s.d}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* Features */}
      <Section>
        <h2 className="mb-8 text-center text-sm uppercase tracking-widest text-white/40">Four loops, one team</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {FEATURES.map(([t, d]) => (
            <div key={t} className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
              <h3 className="font-medium text-emerald-300">{t}</h3>
              <p className="mt-1 text-sm text-white/60">{d}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* Stack strip */}
      <Section className="text-center">
        <h2 className="mb-5 text-sm uppercase tracking-widest text-white/40">Built on</h2>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {STACK.map((s) => (
            <span key={s} className="rounded-full border border-white/10 bg-white/[0.02] px-3 py-1 text-xs text-white/55">
              {s}
            </span>
          ))}
        </div>
      </Section>

      {/* CTA */}
      <Section className="text-center">
        <h2 className="text-3xl font-semibold">Stop flying blind on your data.</h2>
        <p className="mt-2 text-white/55">One agent team. Nine integrations. Working while you sleep.</p>
        <Link href="/sign-in" className="mt-5 inline-block rounded-lg bg-emerald-500 px-6 py-3 text-sm font-medium text-black hover:bg-emerald-400">
          Sign in & open the dashboard
        </Link>
      </Section>
    </div>
  );
}
