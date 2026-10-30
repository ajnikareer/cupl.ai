import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check } from "lucide-react";
import clsx from "clsx";
import { api, IMG } from "../lib/api";
import { Avatar, ErrorBox, PageTitle, Spinner } from "../components/ui";
import { FieldInput } from "../chat/Widgets";

const DESC: Record<string, string> = { prewedding: "Shoots, proposals, couple experiences", engagement: "Ceremony & celebration", wedding: "Every ceremony, planned",
  honeymoon: "Destinations & itineraries", trip: "Any trip, any time", life_beyond: "Anniversaries & milestones" };

export default function NewSpace() {
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me") });
  const qc = useQueryClient();
  const nav = useNavigate();
  const [type, setType] = useState("");
  const [vals, setVals] = useState<any>({});
  const [err, setErr] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  if (!me) return <Spinner />;
  const types = me.space_types || {};
  const fields = type ? [{ key: "title", label: "Name this event (optional)", kind: "text", required: false }, ...types[type].fields] : [];
  const create = async () => {
    setErr(null);
    for (const k of ["budget", "guests"]) if (vals[k] !== undefined && vals[k] !== "" && Number(vals[k]) <= 0) return setErr(`${k} must be positive`);
    if (vals.start_date && vals.end_date && vals.end_date < vals.start_date) return setErr("End date must be after start date");
    setBusy(true);
    try {
      const clean = Object.fromEntries(Object.entries(vals).filter(([, v]) => v !== "" && v != null && !(Array.isArray(v) && !v.length)));
      const s: any = await api("/api/spaces", { method: "POST", body: { type, fields: clean } });
      await qc.invalidateQueries();
      nav(`/app/spaces/${s.id}`);
    } catch (e) { setErr(e); } finally { setBusy(false); }
  };
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
      <div>
        <PageTitle title="Create Your Event Space" sub="Tell me about this special event — I'll take care of the rest." />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Object.entries(types).map(([k, v]: any) => (
            <button type="button" key={k} onClick={() => { setType(k); setVals({}); }}
              className={clsx("card group relative overflow-hidden text-left transition", type === k && "ring-2 ring-brand")}>
              <img src={IMG[k]} alt="" className="h-28 w-full object-cover" />
              {type === k && <span className="absolute right-3 top-3 grid h-7 w-7 place-items-center rounded-full bg-brand text-white"><Check className="h-4 w-4" /></span>}
              <div className="p-3"><div className="h-serif text-lg text-brand">{v.label}</div><div className="text-xs text-mut">{DESC[k]}</div></div>
            </button>
          ))}
        </div>
        {type && (
          <div className="card rise mt-6 space-y-4 p-6">
            {fields.map((f: any) => (
              <label key={f.key} className="block text-sm"><span className="mb-1 block text-xs text-mut">{f.label}{f.required && " *"}</span>
                <FieldInput f={f} value={vals[f.key]} onChange={(v) => setVals({ ...vals, [f.key]: v })} /></label>
            ))}
            <p className="text-xs text-mut">* needed before planning — you can also leave them and I'll ask you later.</p>
            <ErrorBox error={err} />
            <div className="text-right"><button type="button" disabled={busy} onClick={create} className="btn-primary px-6">{busy ? "Creating…" : "Create Event Space"}</button></div>
          </div>
        )}
      </div>
      <aside className="card hidden h-fit flex-col items-center gap-3 p-6 text-center lg:flex">
        <Avatar size={120} />
        <p className="text-sm">Not sure which to choose? I can help you decide based on your ideas and timeline.</p>
        <button type="button" onClick={() => nav("/app/chat")} className="btn-primary">Ask cupl AI</button>
      </aside>
    </div>
  );
}
