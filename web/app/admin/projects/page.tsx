"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Nav from "@/components/Nav";
import ResearchPanel from "@/components/ResearchPanel";

interface Project {
  _id: string;
  name: string;
  slug: string;
  type?: string;
  repoUrl?: string;
  ownerEmail?: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [err, setErr] = useState("");

  async function load() {
    try {
      const r = await fetch("/api/projects", { cache: "no-store" });
      if (!r.ok) throw new Error();
      const d = await r.json();
      setProjects(d.projects ?? []);
      setSelected(d.selected ?? null);
    } catch {
      setErr("Couldn't load projects. is the backend reachable?");
    } finally {
      setLoaded(true);
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function pick(slug: string) {
    await fetch("/api/projects/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug }),
    });
    setSelected(slug);
    location.reload();
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-1 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Projects</h1>
          <Link
            href="/admin/onboarding"
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110"
          >
            + Add project
          </Link>
        </div>
        <p className="mb-6 text-sm text-white/50">
          Brands &amp; products TwoCustomer monitors and operates on. Pick the active one.
        </p>

        {err && (
          <p className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {err}
          </p>
        )}

        {selected && (
          <div className="mb-5">
            <ResearchPanel slug={selected} />
          </div>
        )}

        {loaded && projects.length === 0 && !err ? (
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-sm text-white/50">
            No projects yet.{" "}
            <Link href="/admin/onboarding" className="text-accent-soft">
              Add your first
            </Link>{" "}
            to arm the monitor.
          </div>
        ) : (
          <div className="grid gap-3">
            {projects.map((p) => {
              const active = p.slug === selected;
              return (
                <div
                  key={p._id ?? p.slug}
                  className={`flex items-center gap-3 rounded-xl border p-4 ${
                    active ? "border-accent/50 bg-accent/[0.06]" : "border-white/10 bg-white/[0.02]"
                  }`}
                >
                  <span className="rounded-md bg-white/10 px-2 py-0.5 text-xs uppercase">
                    {p.type ?? "brand"}
                  </span>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium">{p.name}</h3>
                    <p className="text-xs text-white/45">
                      {p.repoUrl ? p.repoUrl : p.slug}
                    </p>
                  </div>
                  {active ? (
                    <span className="rounded-full bg-accent/15 px-2 py-0.5 text-xs text-accent-soft">
                      active
                    </span>
                  ) : (
                    <button
                      onClick={() => pick(p.slug)}
                      className="rounded-lg border border-white/15 px-3 py-1 text-xs hover:border-accent/50"
                    >
                      Set active
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </>
  );
}
