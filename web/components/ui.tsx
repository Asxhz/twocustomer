// Shared UI primitives — cohesive dark-editorial design system.
import { type ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-white/10 bg-white/[0.02] p-5 ${className}`}>
      {children}
    </div>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "good" | "bad" | "warn" }) {
  const tones = {
    neutral: "bg-white/10 text-white/60",
    good: "bg-emerald-500/15 text-emerald-300",
    bad: "bg-red-500/15 text-red-300",
    warn: "bg-amber-400/15 text-amber-200",
  };
  return <span className={`rounded-full px-2 py-0.5 text-xs ${tones[tone]}`}>{children}</span>;
}

export function Button({ children, onClick, disabled, variant = "primary", type = "button" }: {
  children: ReactNode; onClick?: () => void; disabled?: boolean;
  variant?: "primary" | "ghost"; type?: "button" | "submit";
}) {
  const base = "rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50";
  const v = variant === "primary"
    ? "bg-emerald-500 text-black hover:bg-emerald-400"
    : "border border-white/15 text-white/80 hover:border-white/30";
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${v}`}>
      {children}
    </button>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-white/45">{label}</span>
      {children}
    </label>
  );
}

export const inputCls =
  "rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-emerald-400/50";

export function Spinner() {
  return <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-emerald-400" />;
}
