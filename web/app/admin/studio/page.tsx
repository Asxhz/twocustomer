"use client";

import { useState } from "react";
import Nav from "@/components/Nav";
import { Badge, Button, Card, Field, inputCls, Spinner } from "@/components/ui";

export default function Studio() {
  const [instruction, setInstruction] = useState("A clean, minimal studio product photo of a silver concert flute on a white background");
  const [imageUrl, setImageUrl] = useState("");
  const [out, setOut] = useState<{ url?: string | null; data_url?: string | null; message?: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    setOut(null);
    try {
      const r = await fetch("/api/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction, image_url: imageUrl || undefined }),
      });
      setOut(await r.json());
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <header className="mb-6 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Edit studio</h1>
          <Badge tone="good">Gemini</Badge>
        </header>
        <p className="mb-6 text-sm text-white/55">
          Generate or edit product imagery from a prompt — e.g. <em>&quot;make it cleaner, less hefty, better lighting.&quot;</em>
          {" "}Paste an image URL to edit an existing photo.
        </p>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="flex flex-col gap-4">
            <Field label="Instruction">
              <textarea value={instruction} onChange={(e) => setInstruction(e.target.value)}
                rows={4} className={inputCls} />
            </Field>
            <Field label="Source image URL (optional — to edit)">
              <input value={imageUrl} onChange={(e) => setImageUrl(e.target.value)}
                placeholder="https://…/product.png" className={inputCls} />
            </Field>
            <div>
              <Button onClick={run} disabled={busy}>
                {busy ? <Spinner /> : imageUrl ? "Edit image" : "Generate image"}
              </Button>
            </div>
          </Card>

          <Card className="flex min-h-72 items-center justify-center">
            {!out && <span className="text-sm text-white/40">Result appears here</span>}
            {(out?.data_url || out?.url) && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={out.data_url || out.url || ""} alt="result" className="max-h-[28rem] rounded-lg" />
            )}
            {out && !out.data_url && !out.url && (
              <span className="text-sm text-amber-200">{out.message}</span>
            )}
          </Card>
        </div>
      </main>
    </>
  );
}
