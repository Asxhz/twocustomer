import VoiceSession from "@/components/VoiceSession";
import { activeBrandName } from "@/lib/convexHttp";

export default async function CustomerSession({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string }>;
}) {
  const { mode } = await searchParams;
  const voice = mode !== "chat";
  const brand = await activeBrandName();
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col gap-4 px-6 py-10">
      <header>
        <h1 className="text-xl font-semibold">Quick interview</h1>
        <p className="text-sm text-white/50">
          {voice ? "Voice mode (Deepgram). or type below." : "Chat mode. tell us anything."}
        </p>
      </header>
      <VoiceSession voice={voice} />
      <p className="text-xs text-white/40">
        Your responses become validated insight for {brand}. Thank you 💚
      </p>
    </main>
  );
}
