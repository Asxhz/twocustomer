"use client";

import { useEffect, useState } from "react";

interface Project { slug: string; name: string; type?: string }

export default function ProjectPicker() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetch("/api/projects")
      .then((r) => r.json())
      .then((d) => {
        setProjects(d.projects || []);
        setSelected(d.selected || d.projects?.[0]?.slug || "");
      })
      .catch(() => {})
      .finally(() => setLoaded(true));
  }, []);

  async function switchTo(slug: string) {
    setSelected(slug);
    await fetch("/api/projects/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug }),
    });
    window.location.reload();
  }

  if (!loaded || projects.length === 0) return null;

  return (
    <select
      value={selected}
      onChange={(e) => switchTo(e.target.value)}
      className="rounded-md border border-white/10 bg-black/40 px-2 py-1 text-xs text-white/70 outline-none hover:border-accent-soft/50"
      title="Active project"
    >
      {projects.map((p) => (
        <option key={p.slug} value={p.slug} className="bg-black">
          {p.name}{p.type === "software" ? " ⌁" : ""}
        </option>
      ))}
    </select>
  );
}
