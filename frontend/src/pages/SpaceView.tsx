import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Check, ExternalLink, Heart, RefreshCw, Sparkles, Trash2, X, ShieldCheck, Users, Coins, Music, Utensils, Palette, Clock } from "lucide-react";
import clsx from "clsx";
import { api, daysTo, fmtDate, fmtINR, IMG } from "../lib/api";
import { ErrorBox, STATE_LABEL, Spinner } from "../components/ui";
import { FieldInput } from "../chat/Widgets";

const TABS = ["Plan", "Details", "Budget", "To-dos", "Memories"];

export default function SpaceView() {
  const { id } = useParams();
  const qc = useQueryClient();
  const nav = useNavigate();
  const [tab, setTab] = useState("Plan");
  const { data: s, error, isLoading } = useQuery({ queryKey: ["space", id], queryFn: () => api(`/api/spaces/${id}`),
    refetchInterval: (q: any) => (q.state.data?.state === "building" ? 2500 : false) });
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me") });
  useEffect(() => { if (s && s.missing_fields?.length && !s.active_plan_version) setTab("Details"); }, [s?.id]);
  if (isLoading) return <Spinner />;
  if (error || !s) return <ErrorBox error={error || "Not found"} />;
  const isActive = me?.user?.active_space_id === s.id;
  const d = daysTo(s.start_date);
  const activate = async () => { await api(`/api/spaces/${id}/activate`, { method: "POST" }); qc.invalidateQueries(); };
  const del = async () => {
    if (!confirm(`Delete "${s.title}" and its plan? This can't be undone.`)) return;
    await api(`/api/spaces/${id}`, { method: "DELETE" }); qc.invalidateQueries(); nav("/app/spaces");
  };
  return (
    <div>
      <div className="relative mb-6 overflow-hidden rounded-[2rem]">
        <img src={IMG[s.type]} alt="" className="h-48 w-full object-cover md:h-56" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
        <div className="absolute inset-x-0 bottom-0 flex flex-wrap items-end justify-between gap-3 p-5 text-white">
          <div>
            <h1 className="h-serif text-3xl md:text-4xl">{s.title}</h1>
            <div className="text-sm opacity-90">{[s.city || s.destination, s.start_date && fmtDate(s.start_date) + (s.end_date ? " → " + fmtDate(s.end_date) : ""), s.budget && fmtINR(s.budget), s.guests && `${s.guests} guests`].filter(Boolean).join(" · ")}</div>
            <div className="mt-2 flex gap-2"><span className="badge bg-white/90">{STATE_LABEL[s.state] || s.state}</span>{d !== null && d >= 0 && <span className="badge bg-white/90">{d} days to go</span>}</div>
          </div>
          <div className="flex gap-2">
            {isActive ? <span className="badge bg-white/90">Active in chat</span> : <button type="button" onClick={activate} className="btn-ghost">Make active</button>}
            <button type="button" onClick={del} className="btn-ghost" aria-label="Delete"><Trash2 className="h-4 w-4" /></button>
          </div>
        </div>
      </div>
      <div className="scroll-thin mb-6 flex gap-1 overflow-x-auto border-b border-line">
        {TABS.map((t) => <button type="button" key={t} onClick={() => setTab(t)} className={clsx("shrink-0 border-b-2 px-4 py-2.5 text-sm", tab === t ? "border-brand font-medium text-brand" : "border-transparent text-mut")}>{t}</button>)}
      </div>
      {tab === "Plan" && <PlanTab s={s} />}
      {tab === "Details" && <DetailsTab s={s} />}
      {tab === "Budget" && <BudgetTab s={s} />}
      {tab === "To-dos" && <TodosTab s={s} />}
      {tab === "Memories" && <MemoriesTab s={s} />}
    </div>
  );
}

function PlanTab({ s }: { s: any }) {
  const qc = useQueryClient();
  const building = s.state === "building";
  const { data: plan, isLoading } = useQuery({ queryKey: ["plan", s.id], queryFn: () => api(`/api/spaces/${s.id}/plan`),
    refetchInterval: building ? 2500 : false });
  const [instr, setInstr] = useState("");
  const [err, setErr] = useState<any>(null);
  const build = async (instruction?: string, keys?: string[]) => {
    setErr(null);
    try {
      await api(`/api/spaces/${s.id}/plan`, { method: "POST", body: { instruction: instruction || null, section_keys: keys || null } });
      setInstr(""); qc.invalidateQueries({ queryKey: ["space", s.id] }); qc.invalidateQueries({ queryKey: ["plan", s.id] });
    } catch (e) { setErr(e); }
  };
  useEffect(() => { if (!building) qc.invalidateQueries({ queryKey: ["plan", s.id] }); }, [building]);
  if (s.missing_fields?.length)
    return <div className="card p-6 text-sm">A few details first: <b>{s.missing_fields.join(", ").replace(/_/g, " ")}</b> — add them in the Details tab, or just tell cupl in chat.</div>;
  if (isLoading) return <Spinner />;
  if (!plan && building)
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3 rounded-2xl bg-blush/60 p-3 text-sm"><Spinner className="h-5 w-5" /> Weaving your plan from both your tastes — sections appear as they're ready…</div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-64" />)}</div>
      </div>
    );
  if (!plan)
    return (
      <div className="card overflow-hidden text-center">
        <img src={IMG[s.type]} alt="" className="h-40 w-full object-cover" />
        <div className="space-y-3 p-8">
          <div className="h-serif text-2xl text-brand">Ready to weave your plan ✨</div>
          <p className="mx-auto max-w-md text-sm text-mut">Tip: share a few tastes first (chat with cupl or the Me page) and get your partner in — the plan gets far more personal.</p>
          {s.build_error && <ErrorBox error="The last attempt hit a snag. Please try again." />}
          <ErrorBox error={err} />
          <button type="button" onClick={() => build()} className="btn-primary px-6"><Sparkles className="h-4 w-4" /> Build our plan</button>
        </div>
      </div>
    );
  return (
    <div className="space-y-8">
      {building && <div className="flex items-center gap-3 rounded-2xl bg-blush/60 p-3 text-sm"><Spinner className="h-5 w-5" /> Weaving your plan — sections appear as they're ready{plan.instruction ? ` (${plan.instruction})` : ""}…</div>}
      {s.state === "stale" && !building && <div className="rounded-2xl bg-[#fffaf2] p-3 text-sm">Event details changed — <button type="button" className="font-medium text-brand underline" onClick={() => build("Event details changed")}>refresh the plan</button>.</div>}
      {!building && (
        <div className="card flex flex-col gap-2 p-3 sm:flex-row">
          <input className="input" value={instr} onChange={(e) => setInstr(e.target.value)} placeholder="Ask for a change… e.g. 'no loud DJs, more Sufi'" />
          <div className="flex gap-2">
            <button type="button" disabled={!instr.trim()} onClick={() => build(instr)} className="btn-primary whitespace-nowrap">Update plan</button>
            <button type="button" onClick={() => confirm("Rebuild the whole plan from scratch?") && build()} className="btn-ghost" aria-label="Rebuild"><RefreshCw className="h-4 w-4" /></button>
          </div>
        </div>
      )}
      <ErrorBox error={err} />
      {plan.destination_used && !s.destination && <div className="text-sm text-mut">Planned around your top destination match: <b>{plan.destination_used}</b></div>}
      {(plan.sections || []).map((sec: any) => (
        <section key={sec.key}>
          <div className="flex items-end justify-between gap-2">
            <h2 className="h-serif text-2xl text-brand">{sec.title}</h2>
            {sec.status !== "pending" && !building && <button type="button" onClick={() => build(`Refresh ${sec.title}`, [sec.key])} className="text-xs text-mut hover:text-brand"><RefreshCw className="inline h-3 w-3" /> refresh</button>}
          </div>
          {sec.summary && <p className="mb-3 text-sm text-mut">{sec.summary}</p>}
          {sec.status === "pending" ? (
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-64" />)}</div>
          ) : (<>
            {sec.error && <div className="mb-3 rounded-2xl bg-blush/50 p-3 text-sm">{sec.error}</div>}
            <div className="space-y-3">{(sec.items || []).map((it: any) => <ItemRow key={it.id} it={it} sid={s.id} type={s.type} secKey={sec.key} />)}</div>
          </>)}
        </section>
      ))}
      <p className="text-xs text-mut">Costs are rough estimates. cupl recommends — you book directly. Plan v{plan.version}.</p>
    </div>
  );
}

function ItemRow({ it, sid, type, secKey }: { it: any; sid: string; type: string; secKey: string }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const m = useMutation({
    mutationFn: (status: string) => api(`/api/spaces/${sid}/items/${it.id}`, { method: "PATCH", body: { status } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan", sid] }),
  });
  const set = (st: string) => m.mutate(it.status === st ? "suggested" : st);

  const getIconInfo = () => {
    if (it.act || it.tempo_bpm || secKey === "sangeet" || secKey === "music") {
      return { icon: <Music className="h-4 w-4 text-amber-700" />, bg: "bg-amber-100/70 border-amber-200/50" };
    }
    if (it.course_type || it.portion_math || secKey === "menu" || secKey === "food_trail") {
      return { icon: <Utensils className="h-4 w-4 text-emerald-700" />, bg: "bg-emerald-100/70 border-emerald-200/50" };
    }
    if (it.bride_groom_pairing || it.hex_colors || secKey === "outfits" || secKey === "gifts") {
      return { icon: <Palette className="h-4 w-4 text-purple-700" />, bg: "bg-purple-100/70 border-purple-200/50" };
    }
    if (it.lighting_spec || secKey === "ceremonies" || secKey === "decor") {
      return { icon: <Sparkles className="h-4 w-4 text-rose-700" />, bg: "bg-rose-100/70 border-rose-200/50" };
    }
    if (it.capacity_check || secKey === "venue") {
      return { icon: <Users className="h-4 w-4 text-blue-700" />, bg: "bg-blue-100/70 border-blue-200/50" };
    }
    if (secKey === "itinerary" || secKey === "shoot_locations" || secKey === "destinations") {
      return { icon: <Compass className="h-4 w-4 text-teal-700" />, bg: "bg-teal-100/70 border-teal-200/50" };
    }
    return { icon: <Sparkles className="h-4 w-4 text-brand" />, bg: "bg-blush border-brand/20" };
  };

  const { icon, bg } = getIconInfo();

  return (
    <div className={clsx(
      "card p-4 sm:p-5 flex flex-col gap-3 transition-all border border-line hover:border-brand/30 shadow-2xs",
      it.status === "skipped" && "opacity-50"
    )}>
      {/* Top row: Icon + Title + Badges + Cost */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className={clsx("h-9 w-9 shrink-0 rounded-xl flex items-center justify-center border shadow-3xs", bg)}>
            {icon}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-base text-charcoal">{it.title}</span>
              {typeof it.affinity === "number" && it.affinity > 0 && (
                <span className="badge bg-gold/15 text-gold-dark font-medium text-[11px] py-0.5">
                  {Math.round(Math.min(1, it.affinity) * 100)}% QLOO match
                </span>
              )}
              {it.act && (
                <span className="badge bg-brand/10 text-brand font-medium text-[11px] py-0.5">
                  {it.act}
                </span>
              )}
              {it.course_type && (
                <span className="badge bg-emerald-50 text-emerald-800 font-medium text-[11px] py-0.5">
                  {it.course_type}
                </span>
              )}
              {it.tempo_bpm && (
                <span className="badge bg-slate-100 text-slate-700 font-mono text-[11px] py-0.5">
                  ⏱️ {it.tempo_bpm}
                </span>
              )}
              {it.vibe_tag && (
                <span className="badge bg-[#fff5ea] text-[#b45309] text-[11px] py-0.5">
                  {it.vibe_tag}
                </span>
              )}
              {it.loved_by_both && (
                <span className="badge bg-rose-50 text-rose-700 text-[11px] py-0.5">
                  <Heart className="h-3 w-3 fill-rose-600 inline mr-1" /> Loved by both
                </span>
              )}
              {it.status === "done" && (
                <span className="badge bg-emerald-100 text-emerald-800 text-[11px] py-0.5 font-bold">
                  ✓ Confirmed
                </span>
              )}
            </div>
            {it.heritage_origin && (
              <div className="text-xs text-purple-700 font-medium mt-0.5">
                🏛️ {it.heritage_origin}
              </div>
            )}
          </div>
        </div>

        {it.est_cost > 0 && (
          <span className="badge bg-cream border border-line text-xs font-semibold text-charcoal shrink-0">
            ~{fmtINR(it.est_cost)}
          </span>
        )}
      </div>

      {it.hex_colors && it.hex_colors.length > 0 && (
        <div className="flex items-center gap-2 pl-12 text-xs">
          <span className="text-mut font-medium flex items-center gap-1">
            <Palette className="h-3.5 w-3.5" /> Palette:
          </span>
          <div className="flex flex-wrap items-center gap-1.5">
            {it.hex_colors.map((hex: string, i: number) => (
              <span key={i} className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full border border-line bg-surface">
                <span className="h-3 w-3 rounded-full border border-black/15 shrink-0" style={{ backgroundColor: hex }} />
                {hex}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-1.5 pl-12 text-xs">
        {it.portion_math && (
          <div className="rounded-xl bg-emerald-50/80 border border-emerald-200/70 p-2.5 text-emerald-950 leading-relaxed">
            <span className="font-semibold text-emerald-900 flex items-center gap-1 mb-0.5">
              🍃 Anti-Waste Portioning Math:
            </span>
            {it.portion_math}
          </div>
        )}

        {it.bride_groom_pairing && (
          <div className="rounded-xl bg-purple-50/70 border border-purple-200/60 p-2.5 text-purple-950 leading-relaxed">
            <span className="font-semibold text-purple-900 block mb-0.5">👫 Styling Pair:</span>
            {it.bride_groom_pairing}
          </div>
        )}

        {it.cue_note && (
          <div className="rounded-xl bg-amber-50/70 border border-amber-200/60 p-2.5 text-amber-950 leading-relaxed">
            <span className="font-semibold text-amber-900 block mb-0.5">🎬 Choreography & DJ Cue:</span>
            {it.cue_note}
          </div>
        )}

        {it.anti_clash_check && (
          <div className="inline-flex items-center gap-1.5 font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/50">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
            {it.anti_clash_check}
          </div>
        )}

        {it.capacity_check && (
          <div className="inline-flex items-center gap-1.5 font-medium text-slate-700 bg-slate-100 px-2.5 py-1 rounded-full">
            <Users className="h-3.5 w-3.5 text-slate-600 shrink-0" />
            {it.capacity_check}
          </div>
        )}

        {it.budget_breakdown && (
          <div className="inline-flex items-center gap-1.5 font-medium text-amber-800 bg-amber-50 px-2.5 py-1 rounded-full ml-1">
            <Coins className="h-3.5 w-3.5 text-amber-600 shrink-0" />
            {it.budget_breakdown}
          </div>
        )}

        {it.lighting_spec && (
          <div className="rounded-xl bg-amber-50/70 border border-amber-200/60 p-2.5 text-amber-950 leading-relaxed">
            <span className="font-semibold text-amber-900 flex items-center gap-1 mb-0.5">
              <Sparkles className="h-3.5 w-3.5 text-amber-600" /> Lighting & Camera Spec:
            </span>
            {it.lighting_spec}
          </div>
        )}
      </div>

      <p className="text-sm text-mut pl-12 leading-relaxed">{it.description}</p>

      {it.why?.length > 0 && (
        <div className="pl-12">
          <button type="button" onClick={() => setOpen(!open)} className="text-xs font-medium text-gold hover:underline flex items-center gap-1">
            💡 {open ? "Hide taste reasoning" : "Why this fits both of you?"}
          </button>
          {open && (
            <ul className="mt-1.5 list-disc space-y-1 rounded-xl bg-[#fffaf2] p-2.5 pl-6 text-xs text-charcoal border border-line/40">
              {it.why.map((w: string, i: number) => <li key={i}>{w}</li>)}
            </ul>
          )}
        </div>
      )}

      <div className="pt-2 border-t border-line/50 flex items-center gap-2 pl-12">
        <button type="button" onClick={() => set("liked")} className={clsx("chip text-xs", it.status === "liked" && "chip-on")} title="Love it">
          <Heart className="h-3.5 w-3.5" /> {it.status === "liked" ? "Loved" : "Love it"}
        </button>
        <button type="button" onClick={() => set("skipped")} className={clsx("chip text-xs", it.status === "skipped" && "chip-on")} title="Skip">
          <X className="h-3.5 w-3.5" /> Skip
        </button>
        <button type="button" onClick={() => set("done")} className={clsx("chip text-xs", it.status === "done" && "chip-on")} title="Mark as confirmed">
          <Check className="h-3.5 w-3.5" /> {it.status === "done" ? "Confirmed" : "Confirm"}
        </button>
        {it.maps_url && (
          <a href={it.maps_url} target="_blank" rel="noreferrer" className="ml-auto inline-flex items-center gap-1 text-xs text-brand font-medium hover:underline">
            Google Maps <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </div>
  );
}

function DetailsTab({ s }: { s: any }) {
  const qc = useQueryClient();
  const fields = [{ key: "title", label: "Event name", kind: "text" }, ...(s.field_specs || [])];
  const [vals, setVals] = useState<any>(() => Object.fromEntries(fields.map((f: any) => [f.key, s[f.key] ?? ""])));
  const [msg, setMsg] = useState<any>(null);
  const save = async () => {
    setMsg(null);
    if (vals.start_date && vals.end_date && vals.end_date < vals.start_date) return setMsg(new Error("End date must be after start date"));
    try { await api(`/api/spaces/${s.id}`, { method: "PATCH", body: { fields: vals } }); qc.invalidateQueries(); setMsg("Saved ✓"); }
    catch (e) { setMsg(e); }
  };
  return (
    <div className="card space-y-4 p-6">
      {fields.map((f: any) => (
        <label key={f.key} className="block text-sm">
          <span className={clsx("mb-1 block text-xs", s.missing_fields?.includes(f.key) ? "font-medium text-brand" : "text-mut")}>{f.label}{f.required && " *"}</span>
          <FieldInput f={f} value={vals[f.key]} onChange={(v) => setVals({ ...vals, [f.key]: v })} />
        </label>
      ))}
      {typeof msg === "string" ? <div className="text-sm text-green-700">{msg}</div> : <ErrorBox error={msg} />}
      <div className="text-right"><button type="button" onClick={save} className="btn-primary">Save details</button></div>
    </div>
  );
}

function BudgetTab({ s }: { s: any }) {
  const qc = useQueryClient();
  const { data: plan } = useQuery({ queryKey: ["plan", s.id], queryFn: () => api(`/api/spaces/${s.id}/plan`) });
  const [edit, setEdit] = useState<any[] | null>(null);
  const [err, setErr] = useState<any>(null);
  if (!s.budget) return <div className="card p-6 text-sm">Set a budget in Details to see your smart split.</div>;
  if (!plan?.budget) return <div className="card p-6 text-sm">Build the plan to see your smart budget split.</div>;
  const rows = edit || plan.budget;
  const total = rows.reduce((a: number, r: any) => a + (Number(r.pct) || 0), 0);
  const save = async () => {
    setErr(null);
    if (rows.some((r: any) => Number(r.pct) < 0)) return setErr("Percentages can't be negative");
    if (total <= 0) return setErr("Total must be above 0");
    try { await api(`/api/spaces/${s.id}/budget`, { method: "PUT", body: { allocations: rows.map((r: any) => ({ category: r.category, pct: Number(r.pct) || 0 })) } }); setEdit(null); qc.invalidateQueries({ queryKey: ["plan", s.id] }); }
    catch (e) { setErr(e); }
  };
  return (
    <div className="card space-y-4 p-6">
      <div className="flex items-baseline justify-between"><div className="h-serif text-2xl text-brand">{fmtINR(s.budget)}</div><span className="text-xs text-mut">Estimates only</span></div>
      {rows.map((r: any, i: number) => (
        <div key={r.category}>
          <div className="flex items-center justify-between text-sm">
            <span>{r.category}</span>
            {edit ? <input type="number" min={0} className="input w-20 py-1 text-right" value={r.pct} onChange={(e) => setEdit(rows.map((x: any, j: number) => (j === i ? { ...x, pct: e.target.value } : x)))} />
              : <span className="text-mut">{r.pct}% · {fmtINR(r.amount)}</span>}
          </div>
          <div className="mt-1.5 h-2 rounded-full bg-blush"><div className="h-2 rounded-full bg-gradient-to-r from-brand to-brand-light" style={{ width: `${Math.min(100, ((Number(r.pct) || 0) / (total || 1)) * 100)}%` }} /></div>
        </div>
      ))}
      <ErrorBox error={err} />
      <div className="text-right">
        {edit ? <><span className="mr-3 text-xs text-mut">Total {Math.round(total)}% (normalised on save)</span><button type="button" className="btn-ghost mr-2" onClick={() => setEdit(null)}>Cancel</button><button type="button" className="btn-primary" onClick={save}>Save split</button></>
          : <button type="button" className="btn-ghost" onClick={() => setEdit(plan.budget.map((r: any) => ({ ...r })))}>Adjust split</button>}
      </div>
    </div>
  );
}

function TodosTab({ s }: { s: any }) {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["todos", s.id], queryFn: () => api(`/api/spaces/${s.id}/todos`) });
  const [title, setTitle] = useState("");
  const [due, setDue] = useState("");
  const inv = () => qc.invalidateQueries({ queryKey: ["todos", s.id] });
  const add = async (e: any) => { e.preventDefault(); if (!title.trim()) return; await api(`/api/spaces/${s.id}/todos`, { method: "POST", body: { title, due: due || null } }); setTitle(""); setDue(""); inv(); };
  const todos = data?.todos || [];
  const doneN = todos.filter((t: any) => t.done).length;
  return (
    <div className="space-y-3">
      {todos.length > 0 && <div className="card p-4"><div className="flex justify-between text-sm"><span>Progress</span><span className="text-mut">{doneN}/{todos.length}</span></div><div className="mt-2 h-2 rounded-full bg-blush"><div className="h-2 rounded-full bg-brand" style={{ width: `${(doneN / todos.length) * 100}%` }} /></div></div>}
      <form onSubmit={add} className="card flex flex-col gap-2 p-3 sm:flex-row">
        <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Add a to-do…" />
        <input className="input sm:w-44" type="date" value={due} onChange={(e) => setDue(e.target.value)} />
        <button className="btn-primary">Add</button>
      </form>
      {!todos.length && <div className="text-sm text-mut">No to-dos yet — they're created automatically when you build a plan.</div>}
      {todos.map((t: any) => (
        <div key={t.id} className="card flex items-center gap-3 p-3.5">
          <input type="checkbox" checked={!!t.done} className="h-5 w-5 accent-brand" aria-label="Done"
            onChange={async () => { await api(`/api/spaces/${s.id}/todos/${t.id}`, { method: "PATCH", body: { done: !t.done } }); inv(); }} />
          <div className={clsx("flex-1 text-sm", t.done && "text-mut line-through")}>{t.title}{t.due && <div className="text-xs text-mut">Due {fmtDate(t.due)}</div>}</div>
          <button type="button" aria-label="Delete" onClick={async () => { await api(`/api/spaces/${s.id}/todos/${t.id}`, { method: "DELETE" }); inv(); }}><Trash2 className="h-4 w-4 text-mut" /></button>
        </div>
      ))}
    </div>
  );
}

function MemoriesTab({ s }: { s: any }) {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["memories", s.id], queryFn: () => api(`/api/spaces/${s.id}/memories`) });
  const [text, setText] = useState("");
  const [rating, setRating] = useState(5);
  const [err, setErr] = useState<any>(null);
  const add = async (e: any) => {
    e.preventDefault(); if (!text.trim()) return;
    try { await api(`/api/spaces/${s.id}/memories`, { method: "POST", body: { text, rating } }); setText(""); qc.invalidateQueries({ queryKey: ["memories", s.id] }); }
    catch (er) { setErr(er); }
  };
  return (
    <div className="space-y-3">
      <form onSubmit={add} className="card space-y-3 p-5">
        <textarea className="input min-h-[90px]" value={text} onChange={(e) => setText(e.target.value)} placeholder="What did you love? What would you skip next time? cupl remembers it for future plans." />
        <div className="flex items-center justify-between">
          <div className="flex gap-1 text-xl">{[1, 2, 3, 4, 5].map((n) => <button type="button" key={n} onClick={() => setRating(n)} className={n <= rating ? "text-gold" : "text-line"} aria-label={`${n} stars`}>★</button>)}</div>
          <button className="btn-primary">Save memory</button>
        </div>
        <ErrorBox error={err} />
      </form>
      {(data?.memories || []).map((m: any) => (
        <div key={m.id} className="card p-4 text-sm"><div>{m.summary}</div><div className="mt-1 text-xs text-mut">{m.rating ? "★".repeat(Math.round(m.rating)) + " · " : ""}{m.created_at?.slice(0, 10)}</div></div>
      ))}
    </div>
  );
}
