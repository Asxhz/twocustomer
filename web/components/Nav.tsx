import Link from "next/link";
import NavAuth from "./NavAuth";

const LINKS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/insights", label: "Insights" },
  { href: "/admin/campaigns", label: "Campaigns" },
  { href: "/admin/fix", label: "Fix" },
  { href: "/admin/studio", label: "Studio" },
  { href: "/monitor", label: "Monitor" },
  { href: "/status", label: "Status" },
];

export default function Nav() {
  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-black/70 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
        <Link href="/" className="text-sm font-semibold tracking-tight">
          Two<span className="text-emerald-400">Customer</span>
        </Link>
        <div className="flex flex-1 items-center gap-4 text-sm text-white/60">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="hover:text-white">
              {l.label}
            </Link>
          ))}
        </div>
        <NavAuth />
      </nav>
    </header>
  );
}
