import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import "./globals.css";

// Inter — the clean modern grotesk used across the sandstone-style redesign.
const geistSans = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TwoCustomer. AI agents for consumer brands",
  description:
    "Connect your data. TwoCustomer monitors signal 24/7, interviews your customers, and ships fixes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // suppressHydrationWarning: browser extensions (Grammarly, etc.) inject
    // attributes on <html>/<body> before React hydrates. Without this, the
    // mismatch aborts hydration and the whole page becomes non-interactive
    // (buttons/inputs dead. "doesn't talk or load").
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} light h-full antialiased`}
    >
      <head>
        {/* No-flash theme init: apply the saved theme before first paint.
            Light by default; only switch to dark if the user previously chose it. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('tc-theme');var d=document.documentElement;d.classList.remove('dark','light');d.classList.add(t==='dark'?'dark':'light');}catch(e){}})();`,
          }}
        />
      </head>
      <body suppressHydrationWarning className="min-h-full flex flex-col">
        {children}
      </body>
    </html>
  );
}
