// Shared UI primitives. cohesive dark design system (violet accent).
import { type ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={
        "rounded-2xl border border-white/[0.08] bg-white/[0.025] p-5 shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset,0_8px_30px_-12px_rgba(0,0,0,0.6)] " +
        className
      }
    >
      {children}
    </div>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "good" | "bad" | "warn" | "accent" }) {
  const tones = {
    neutral: "bg-white/10 text-white/65",
    good: "bg-accent/15 text-accent-soft",
    bad: "bg-red-500/15 text-red-300",
    warn: "bg-amber-400/15 text-amber-200",
    accent: "bg-accent/15 text-accent-soft",
  };
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

export function Button({ children, onClick, disabled, variant = "primary", type = "button" }: {
  children: ReactNode; onClick?: () => void; disabled?: boolean;
  variant?: "primary" | "ghost"; type?: "button" | "submit";
}) {
  const base = "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50";
  const v = variant === "primary"
    ? "bg-accent text-white shadow-[0_4px_20px_-6px_rgba(139,92,246,0.7)] hover:brightness-110"
    : "border border-white/15 text-white/80 hover:border-white/30 hover:bg-white/[0.03]";
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${v}`}>
      {children}
    </button>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium uppercase tracking-wide text-white/45">{label}</span>
      {children}
    </label>
  );
}

export const inputCls =
  "w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none transition focus:border-accent-soft/60 focus:ring-1 focus:ring-accent-soft/30";

export function Stat({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div>
      <div className="text-2xl font-semibold text-accent-soft">{value}</div>
      <div className="text-xs text-white/45">{label}</div>
    </div>
  );
}

export function Spinner() {
  return <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-accent-soft" />;
}
