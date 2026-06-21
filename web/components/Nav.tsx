import Link from "next/link";
import NavAuth from "./NavAuth";
import NavBell from "./NavBell";
import NavTools from "./NavTools";
import ProjectPicker from "./ProjectPicker";

const LINKS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/projects", label: "Projects" },
  { href: "/admin/settings", label: "Settings" },
];

export default function Nav() {
  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-black/70 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
        <Link href="/admin" className="text-sm font-semibold tracking-tight">
          Two<span className="text-accent-soft">Customer</span>
        </Link>
        <div className="flex flex-1 items-center gap-4 text-sm text-white/60">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="hover:text-white">
              {l.label}
            </Link>
          ))}
          <NavTools />
        </div>
        <ProjectPicker />
        <NavBell />
        <NavAuth />
      </nav>
    </header>
  );
}
