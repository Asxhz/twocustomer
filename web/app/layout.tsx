import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TwoCustomer. AI agent team for consumer brands",
  description:
    "Connect your data. TwoCustomer monitors signal 24/7, interviews your customers, and acts.",
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
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body
        suppressHydrationWarning
        className="min-h-full flex flex-col bg-black text-white"
      >
        {children}
      </body>
    </html>
  );
}
