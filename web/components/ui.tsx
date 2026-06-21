// Shared UI primitives for the clean light-minimal design system.
// Colors come from theme tokens: text-white -> ink, bg-surface -> card/base,
// border-white/N -> subtle ink-tinted border. One indigo accent.
import { type ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={
        "rounded-xl border border-white/10 bg-surface p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_1px_1px_rgba(0,0,0,0.03)] " +
        className
      }
    >
      {children}
    </div>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "good" | "bad" | "warn" | "accent" }) {
  const tones = {
    neutral: "bg-white/[0.06] text-white/60 ring-1 ring-white/10",
    good: "bg-emerald-500/12 text-emerald-600 ring-1 ring-emerald-500/20",
    bad: "bg-red-500/12 text-red-600 ring-1 ring-red-500/20",
    warn: "bg-amber-500/12 text-amber-600 ring-1 ring-amber-500/20",
    accent: "bg-accent/10 text-accent ring-1 ring-accent/20",
  };
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

export function Button({ children, onClick, disabled, variant = "primary", type = "button", className = "" }: {
  children: ReactNode; onClick?: () => void; disabled?: boolean;
  variant?: "primary" | "secondary" | "ghost"; type?: "button" | "submit"; className?: string;
}) {
  const base = "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50";
  const variants = {
    primary: "bg-accent text-white hover:brightness-110 shadow-[0_1px_2px_rgba(0,0,0,0.08)]",
    secondary: "border border-white/15 text-white/80 hover:bg-white/[0.04] hover:text-white",
    ghost: "text-white/60 hover:bg-white/[0.04] hover:text-white",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]} ${className}`}>
      {children}
    </button>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-white/55">{label}</span>
      {children}
    </label>
  );
}

export const inputCls =
  "w-full rounded-lg border border-white/15 bg-surface px-3 py-2 text-sm text-white outline-none transition placeholder:text-white/35 focus:border-accent focus:ring-2 focus:ring-accent/20";

export function Stat({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div>
      <div className="text-2xl font-semibold tracking-tight">{value}</div>
      <div className="mt-0.5 text-xs text-white/50">{label}</div>
    </div>
  );
}

export function Spinner() {
  return <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/15 border-t-accent" />;
}
