import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Empty, PageTitle, Spinner } from "../components/ui";

export default function Surprises() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["surprises"], queryFn: () => api("/api/surprises") });
  if (isLoading) return <Spinner />;
  return (
    <div>
      <PageTitle title="Surprises 🤫" sub="Only you can see these. Your partner's WeaveWed never mentions them." />
      {!data?.surprises?.length ? <Empty image="/img/life_beyond.jpg" title="No surprises yet" text="Ask WeaveWed: “Plan a surprise for my partner's birthday”." action={<Link to="/app/chat" className="btn-primary mt-2">Ask WeaveWed</Link>} /> : (
        <div className="space-y-4">{data.surprises.map((s: any) => (
          <div key={s.id} className="card p-6">
            <div className="flex items-start justify-between">
              <div><div className="h-serif text-xl text-brand">{s.occasion} for {s.for_name}</div><div className="text-sm text-mut">{s.date}</div></div>
              <button type="button" aria-label="Delete" onClick={async () => { await api(`/api/surprises/${s.id}`, { method: "DELETE" }); qc.invalidateQueries({ queryKey: ["surprises"] }); }}><Trash2 className="h-4 w-4 text-mut" /></button>
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">{(s.ideas || []).map((i: any, k: number) => <div key={k} className="rounded-2xl bg-cream p-3 text-sm"><b>{i.title}</b><p>{i.description}</p><p className="mt-1 text-xs text-gold">💡 {i.why}</p></div>)}</div>
          </div>))}</div>
      )}
    </div>
  );
}
