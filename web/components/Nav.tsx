import Link from "next/link";
import NavAuth from "./NavAuth";
import ProjectPicker from "./ProjectPicker";

const LINKS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/projects", label: "Projects" },
  { href: "/admin/settings", label: "Settings" },
];

// Minimal, sandstone-style app header: brand · a few quiet links · project
// picker · auth. Deliberately uncluttered — login leads here, then Dashboard.
export default function Nav() {
  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-surface/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center gap-8 px-6 py-3.5">
        <Link href="/admin" className="text-[15px] font-semibold tracking-tight">
          Two<span className="text-accent-soft">Customer</span>
        </Link>
        <div className="flex flex-1 items-center gap-6 text-sm text-white/55">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="transition hover:text-white">
              {l.label}
            </Link>
          ))}
        </div>
        <ProjectPicker />
        <NavAuth />
      </nav>
    </header>
  );
}
