import Nav from "@/components/Nav";
import LiveBadge from "@/components/LiveBadge";
import SourceGraph from "@/components/SourceGraph";
import { graphForBrand } from "@/lib/convexHttp";

export default async function GraphPage() {
  const { nodes, edges, source } = await graphForBrand();

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-1 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Signal graph</h1>
          <LiveBadge source={source} />
        </div>
        <p className="mb-6 text-sm text-white/50">
          How raw chatter becomes action: sources → mentions → insights → campaigns &amp; packets.
        </p>
        {nodes.length === 0 ? (
          <p className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-sm text-white/50">
            Nothing to graph yet. once the monitor finds mentions and the analyst forms
            insights, the connections appear here.
          </p>
        ) : (
          <SourceGraph nodes={nodes} edges={edges} />
        )}
      </main>
    </>
  );
}
