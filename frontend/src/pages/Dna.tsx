import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { api } from "../lib/api";
import { Empty, ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function Dna() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["dna"], queryFn: () => api("/api/dna") });
  const m = useMutation({ mutationFn: () => api("/api/dna/refresh", { method: "POST" }), onSuccess: () => qc.invalidateQueries({ queryKey: ["dna"] }) });
  const d = data?.dna;
  const btn = <button type="button" onClick={() => m.mutate()} disabled={m.isPending} className="btn-ghost"><RefreshCw className={m.isPending ? "h-4 w-4 animate-spin" : "h-4 w-4"} /> Refresh</button>;
  if (isLoading) return <Spinner />;
  return (
    <div className="space-y-6">
      <PageTitle title="Tastes DNA" sub="Where your two worlds meet — built only from tastes you've chosen to share." right={btn} />
      <ErrorBox error={m.error} />
      {!d ? <Empty image="/img/engagement.jpg" title="No DNA yet" text="Share some tastes (chat with cupl or the Me page), invite your partner, then hit Refresh." /> : (<>
        <div className="relative overflow-hidden rounded-[2rem]">
          <img src="/img/prewedding.jpg" alt="" className="absolute inset-0 h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-r from-white via-white/90 to-white/30" />
          <div className="relative p-6 md:p-8">
            <div className="text-xs uppercase tracking-[.2em] text-mut">Your couple vibe</div>
            <div className="h-serif mt-1 text-3xl text-brand md:text-4xl">{d.vibe || "Still discovering…"}</div>
            {d.description && <p className="mt-2 max-w-lg">{d.description}</p>}
            <div className="mt-4 flex gap-2">{(d.palette || []).map((c: string) => <div key={c} className="h-10 w-10 rounded-2xl border-2 border-white shadow" style={{ background: c }} title={c} />)}</div>
          </div>
        </div>

        {d.cultural_harmony && (
          <div className="card space-y-3 p-6 border-gold/30 bg-gradient-to-br from-white via-[#fffaf5] to-cream">
            <div className="flex items-center gap-2">
              <span className="text-xl">🏛️</span>
              <h2 className="h-serif text-xl text-brand">{d.cultural_harmony.title || "Cultural Harmony"}</h2>
              <span className="badge border-gold/40 bg-gold/10 text-gold text-xs">QLOO Cultural IQ</span>
            </div>
            <p className="text-sm text-mut leading-relaxed">{d.cultural_harmony.summary}</p>
            {d.cultural_harmony.ideas?.length > 0 && (
              <div className="grid gap-3 pt-2 sm:grid-cols-3">
                {d.cultural_harmony.ideas.map((idea: any, idx: number) => (
                  <div key={idx} className="rounded-2xl bg-white p-3.5 border border-line shadow-soft text-xs space-y-1">
                    <span className="font-semibold uppercase tracking-wider text-[10px] text-gold">{idea.category}</span>
                    <div className="font-medium text-brand text-sm">{idea.title}</div>
                    <p className="text-mut leading-relaxed">{idea.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="card p-6">
          <h2 className="h-serif text-xl text-brand">💞 Shared loves</h2>
          {d.shared?.length ? <div className="mt-3 flex flex-wrap gap-2">{d.shared.map((s: any) => (
            <span key={s.category + s.name} className="chip">{s.image && <img src={s.image} alt="" className="h-6 w-6 rounded-full object-cover" />}{s.name}<span className="text-xs text-mut">· {s.category}</span></span>
          ))}</div> : <p className="mt-2 text-sm text-mut">No exact overlaps yet — totally normal early on. Keep sharing!</p>}
        </div>
        {Object.keys(d.overlap || {}).length > 0 && (
          <div className="card space-y-3 p-6"><h2 className="h-serif text-xl text-brand">Overlap by category</h2>
            {Object.entries(d.overlap).map(([k, v]: any) => (
              <div key={k}><div className="flex justify-between text-sm"><span className="capitalize">{k}</span><span>{v}%</span></div>
                <div className="mt-1 h-2 rounded-full bg-blush"><div className="h-2 rounded-full bg-gradient-to-r from-brand to-gold" style={{ width: `${v}%` }} /></div></div>))}
          </div>)}
        <div className="grid gap-4 md:grid-cols-2">
          {(d.unique || []).map((u: any) => (
            <div key={u.name} className="card p-6"><h2 className="h-serif text-xl text-brand">🌗 {u.name}'s unique flavours</h2>
              <div className="mt-3 flex flex-wrap gap-1.5">{u.items.length ? u.items.map((i: any) => <span key={i.category + i.name} className="chip">{i.name}</span>) : <span className="text-sm text-mut">Nothing shared yet.</span>}</div></div>))}
        </div>
        {d.differences?.length > 0 && (
          <div className="card p-6"><h2 className="h-serif text-xl text-brand">⚖️ Gentle differences</h2>
            {d.differences.map((x: any) => (
              <div key={x.category} className="mt-3 rounded-2xl bg-cream p-4 text-sm">
                <b className="capitalize">{x.category}</b>
                <div>{x.a_name}: {x.a.join(", ")}</div><div>{x.b_name}: {x.b.join(", ")}</div>
                {x.middle_ground && <div className="mt-1 text-brand">Middle ground: <b>{x.middle_ground}</b></div>}
              </div>))}
          </div>)}
      </>)}
    </div>
  );
}
