import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Check, Copy, ExternalLink, Heart, Search, Share2, Sparkles } from "lucide-react";
import clsx from "clsx";
import { api, IMG } from "../lib/api";
import { Spinner } from "../components/ui";
import { useChat } from "./ChatContext";

const Box = ({ title, sub, children, done }: any) => (
  <div className={clsx("rounded-3xl border bg-white p-4 shadow-soft", done ? "border-line opacity-90" : "border-brand/20")}>
    <div className="flex items-start justify-between gap-2"><div className="font-medium text-brand">{title}</div>{done && <span className="badge"><Check className="h-3 w-3" /> Saved</span>}</div>
    {sub && <div className="mt-0.5 text-xs text-mut">{sub}</div>}
    <div className="mt-3">{children}</div>
  </div>
);

export function Widget({ w }: { w: any }) {
  switch (w.kind) {
    case "taste_picker": return <TastePicker w={w} />;
    case "disambiguation": return <Disambiguation w={w} />;
    case "choices": return <Choices w={w} />;
    case "space_form": return <SpaceForm w={w} />;
    case "confirm": return <Confirm w={w} />;
    case "invite": return <Invite w={w} />;
    case "recs": return <Recs w={w} />;
    case "plan_progress": return <PlanProgress w={w} />;
    case "dna": return <DnaW w={w} />;
    case "surprise": return (
      <Box title={w.title} sub="Only you can see this 🤫">
        <div className="space-y-2">{(w.ideas || []).map((i: any, k: number) => <div key={k} className="rounded-2xl bg-cream p-3 text-sm"><b>{i.title}</b><p className="text-mut">{i.description}</p><p className="mt-1 text-xs text-gold">💡 {i.why}</p></div>)}</div>
      </Box>);
    default: return null;
  }
}

function TastePicker({ w }: { w: any }) {
  const { submitWidget } = useChat();
  const [items, setItems] = useState<any[]>(w.suggestions || []);
  const [sel, setSel] = useState<any[]>(Array.isArray(w.values) ? w.values : []);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [msg, setMsg] = useState("");
  const max = w.max || 6;
  const done = !!w.done;
  const isSel = (it: any) => sel.some((s) => (s.entity_id && s.entity_id === it.entity_id) || s.name === it.name);

  useEffect(() => {
    if (!q.trim() || !w.searchable || done) { setResults([]); return; }
    setSearching(true);
    const t = setTimeout(() => {
      api(`/api/qloo/search?q=${encodeURIComponent(q.trim())}&category=${w.category}`)
        .then((r: any) => setResults(r.results || [])).catch(() => setResults([])).finally(() => setSearching(false));
    }, 280);
    return () => clearTimeout(t);
  }, [q]);

  const toggle = (it: any) => {
    if (done) return;
    setMsg("");
    if (isSel(it)) setSel(sel.filter((s) => !(s.name === it.name && s.entity_id === it.entity_id)));
    else if (sel.length >= max) setMsg(`Up to ${max} picks`);
    else setSel([...sel, it]);
  };
  const add = (it: any) => {
    if (!items.some((x) => x.name === it.name)) setItems([it, ...items]);
    if (!isSel(it)) { if (sel.length >= max) setMsg(`Up to ${max} picks`); else setSel([...sel, it]); }
    setQ(""); setResults([]);
  };
  const shown = q && !w.searchable ? items.filter((i) => i.name.toLowerCase().includes(q.toLowerCase())) : items;
  const partner = items.some((i) => i.partner_likes);

  return (
    <Box title={`${w.sentiment === "dislike" ? "🙅 " : "✨ "}${w.title}`} done={done}
      sub={done ? undefined : `Live suggestions for you${partner ? " · 💞 = your partner loves it" : ""} · tap, search, or add your own`}>
      {!done && (
        <div className="relative mb-3">
          <Search className="absolute left-3 top-3 h-4 w-4 text-mut" />
          <input className="input pl-9" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search or type your own…" aria-label="Search" />
          {searching && <Spinner className="absolute right-3 top-2.5 h-5 w-5" />}
        </div>
      )}
      {results.length > 0 && (
        <div className="mb-3 rounded-2xl border border-gold/40 bg-[#fffaf2] p-2">
          <div className="mb-1 px-1 text-[11px] uppercase tracking-wide text-gold">Matches</div>
          <div className="flex flex-wrap gap-1.5">{results.map((r) => (
            <button type="button" key={r.entity_id} onClick={() => add(r)} className="chip">
              {r.image && <img src={r.image} alt="" className="h-5 w-5 rounded-full object-cover" />}{r.name}{r.sub && <span className="text-[10px] text-mut">{r.sub}</span>}
            </button>))}</div>
        </div>
      )}
      <div className="flex flex-wrap gap-1.5">
        {(done ? sel : shown).map((it) => (
          <button type="button" key={(it.entity_id || "") + it.name} onClick={() => toggle(it)} aria-pressed={isSel(it)}
            className={clsx("chip", isSel(it) && "chip-on", it.partner_likes && !isSel(it) && "border-gold")}>
            {it.image && <img src={it.image} alt="" className="h-5 w-5 rounded-full object-cover" />}
            {it.partner_likes && "💞 "}{it.name}
          </button>
        ))}
        {!done && q.trim() && !items.some((i) => i.name.toLowerCase() === q.trim().toLowerCase()) && (
          <button type="button" onClick={() => add({ name: q.trim().slice(0, 60), entity_id: null })} className="chip border-dashed">+ Add “{q.trim().slice(0, 28)}”</button>
        )}
      </div>
      {msg && <div className="mt-2 text-xs text-red-600">{msg}</div>}
      {!done && (
        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-mut">{sel.length}/{max} selected</span>
          <button type="button" disabled={!sel.length} onClick={() => submitWidget(w, sel)} className="btn-primary">Done</button>
        </div>
      )}
    </Box>
  );
}

function Disambiguation({ w }: { w: any }) {
  const { submitWidget } = useChat();
  const done = !!w.done;
  return (
    <Box title={`🤔 ${w.title}`} done={done}>
      <div className="flex flex-col gap-2">
        {(w.options || []).map((o: any) => (
          <button type="button" key={o.entity_id} disabled={done} onClick={() => submitWidget(w, o)}
            className={clsx("flex items-center gap-3 rounded-2xl border p-2 text-left text-sm transition hover:border-brand/40",
              done && w.values?.entity_id === o.entity_id ? "border-brand bg-blush" : "border-line")}>
            {o.image ? <img src={o.image} alt="" className="h-10 w-10 rounded-xl object-cover" /> : <div className="h-10 w-10 rounded-xl bg-blush" />}
            <span>{o.label}</span>
          </button>
        ))}
        {!done && <button type="button" onClick={() => submitWidget(w, null)} className="text-left text-xs text-mut underline">None of these</button>}
      </div>
    </Box>
  );
}

function Choices({ w }: { w: any }) {
  const { submitWidget } = useChat();
  const [sel, setSel] = useState<string[]>(w.values ? [].concat(w.values) : []);
  const done = !!w.done;
  const pick = (o: string) => {
    if (done) return;
    if (!w.multi) { setSel([o]); submitWidget(w, [o]); return; }
    setSel(sel.includes(o) ? sel.filter((x) => x !== o) : [...sel, o]);
  };
  return (
    <Box title={w.title}>
      <div className="flex flex-wrap gap-1.5">{(w.options || []).map((o: string) => <button type="button" key={o} onClick={() => pick(o)} className={clsx("chip", sel.includes(o) && "chip-on")}>{o}</button>)}</div>
      {w.multi && !done && <div className="mt-3 text-right"><button type="button" disabled={!sel.length} className="btn-primary" onClick={() => submitWidget(w, sel)}>Done</button></div>}
    </Box>
  );
}

export function FieldInput({ f, value, onChange }: { f: any; value: any; onChange: (v: any) => void }) {
  const [custom, setCustom] = useState("");
  if (f.kind === "select")
    return <div className="flex flex-wrap gap-1.5">{f.options.map((o: string) => <button type="button" key={o} onClick={() => onChange(o)} className={clsx("chip", value === o && "chip-on")}>{o}</button>)}</div>;
  if (f.kind === "multi") {
    const arr: string[] = Array.isArray(value) ? value : [];
    const opts = Array.from(new Set([...f.options, ...arr]));
    return (
      <div className="flex flex-wrap items-center gap-1.5">
        {opts.map((o: string) => <button type="button" key={o} onClick={() => onChange(arr.includes(o) ? arr.filter((x) => x !== o) : [...arr, o])} className={clsx("chip", arr.includes(o) && "chip-on")}>{o}</button>)}
        <input className="input w-32 py-1.5" placeholder="+ other" value={custom} onChange={(e) => setCustom(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && custom.trim()) { e.preventDefault(); onChange([...arr, custom.trim()]); setCustom(""); } }} />
      </div>
    );
  }
  return <input className="input" type={f.kind === "number" ? "number" : f.kind === "date" ? "date" : "text"} min={f.kind === "number" ? 1 : undefined}
    value={value ?? ""} onChange={(e) => onChange(e.target.value)} />;
}

function SpaceForm({ w }: { w: any }) {
  const { submitWidget } = useChat();
  const [vals, setVals] = useState<any>(() => Object.fromEntries((w.fields || []).map((f: any) => [f.key, w.values?.[f.key] ?? f.value ?? ""])));
  const [err, setErr] = useState("");
  const done = !!w.done;
  const submit = () => {
    const missing = (w.fields || []).filter((f: any) => f.required && (vals[f.key] === "" || vals[f.key] == null || (Array.isArray(vals[f.key]) && !vals[f.key].length)));
    if (missing.length) return setErr(`Please fill: ${missing.map((f: any) => f.label).join(", ")}`);
    for (const k of ["budget", "guests"]) if (vals[k] !== undefined && vals[k] !== "" && Number(vals[k]) <= 0) return setErr(`${k} must be positive`);
    if (vals.start_date && vals.end_date && vals.end_date < vals.start_date) return setErr("End date must be after the start date");
    submitWidget(w, Object.fromEntries(Object.entries(vals).filter(([, v]) => v !== "" && v != null)));
  };
  return (
    <Box title={`📝 ${w.title}`} done={done}>
      <fieldset disabled={done} className="space-y-3">
        {(w.fields || []).map((f: any) => (
          <label key={f.key} className="block text-sm"><span className="mb-1 block text-xs text-mut">{f.label}{f.required && " *"}</span>
            <FieldInput f={f} value={vals[f.key]} onChange={(v) => setVals({ ...vals, [f.key]: v })} /></label>
        ))}
      </fieldset>
      {err && <div className="mt-2 text-xs text-red-600">{err}</div>}
      {!done && <div className="mt-4 text-right"><button type="button" className="btn-primary" onClick={submit}>Save details</button></div>}
    </Box>
  );
}

function Confirm({ w }: { w: any }) {
  const { submitWidget } = useChat();
  return (
    <Box title={w.title}>
      {w.done ? <div className="text-sm text-mut">{w.values ? "✓ Confirmed" : "✗ Cancelled"}</div> : (
        <div className="flex gap-2">
          <button type="button" className="btn-primary" onClick={() => submitWidget(w, true)}><Check className="h-4 w-4" /> Yes</button>
          <button type="button" className="btn-ghost" onClick={() => submitWidget(w, false)}>Not now</button>
        </div>)}
    </Box>
  );
}

function Invite({ w }: { w: any }) {
  const [copied, setCopied] = useState(false);
  const link = (w.link || "").replace(/^https?:\/\/[^\/]+/, window.location.origin) || `${window.location.origin}/join/${w.code || ""}`;
  const copy = async () => { try { await navigator.clipboard.writeText(link); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch {} };
  const nav: any = navigator;
  return (
    <Box title="💌 Invite your partner" sub="They sign in with their own account — both your tastes count.">
      <div className="break-all rounded-2xl bg-cream p-2.5 text-xs">{link}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" className="btn-primary" onClick={copy}><Copy className="h-4 w-4" />{copied ? "Copied!" : "Copy link"}</button>
        {nav.share && <button type="button" className="btn-ghost" onClick={() => nav.share({ title: "Join me on WeaveWed 💞", url: link }).catch(() => {})}><Share2 className="h-4 w-4" /> Share</button>}
        <a className="btn-ghost" target="_blank" rel="noreferrer" href={`https://wa.me/?text=${encodeURIComponent("Join me on WeaveWed 💞 " + link)}`}>WhatsApp</a>
      </div>
    </Box>
  );
}

function Recs({ w }: { w: any }) {
  return (
    <Box title={`💡 ${w.title}`}>
      <div className="scroll-thin -mx-1 flex gap-3 overflow-x-auto px-1 pb-1">
        {(w.items || []).map((it: any) => (
          <div key={it.id} className="w-48 shrink-0 overflow-hidden rounded-2xl border border-line bg-white">
            <img src={it.image || "/img/hero.jpg"} alt="" className="h-28 w-full object-cover" onError={(e: any) => (e.currentTarget.src = "/img/hero.jpg")} />
            <div className="p-2.5">
              <div className="line-clamp-2 text-sm font-medium">{it.title}</div>
              {it.loved_by_both && <div className="mt-1 text-[11px] text-brand"><Heart className="inline h-3 w-3 fill-brand" /> Loved by both</div>}
              {it.why?.[0] && <div className="mt-1 line-clamp-3 text-[11px] text-mut">{it.why[0]}</div>}
              {it.maps_url && <a href={it.maps_url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-[11px] text-brand">Maps <ExternalLink className="h-3 w-3" /></a>}
            </div>
          </div>
        ))}
      </div>
      {w.space_id && <Link to={`/app/spaces/${w.space_id}`} className="mt-3 inline-block text-sm font-medium text-brand underline">See full plan</Link>}
    </Box>
  );
}

function PlanProgress({ w }: { w: any }) {
  const { data: s } = useQuery({ queryKey: ["space", w.space_id], queryFn: () => api(`/api/spaces/${w.space_id}`),
    refetchInterval: (q: any) => (!q.state.data || q.state.data.state === "building" ? 2500 : false) });
  const building = !s || s.state === "building";
  return (
    <div className="flex items-center gap-3 overflow-hidden rounded-3xl border border-brand/20 bg-white p-3 shadow-soft">
      <img src={IMG[s?.type] || "/img/hero.jpg"} alt="" className="h-16 w-16 rounded-2xl object-cover" />
      <div className="flex-1">
        <div className="text-sm font-medium text-brand">{building ? `Weaving your ${w.title} plan…` : `✨ ${w.title} plan is ready`}</div>
        <div className="text-xs text-mut">{building ? "Matching both your tastes — sections appear as they're ready." : "Tap to explore every section."}</div>
      </div>
      {building ? <Spinner /> : <Link to={`/app/spaces/${w.space_id}`} className="btn-primary"><Sparkles className="h-4 w-4" /> Open</Link>}
    </div>
  );
}

function DnaW({ w }: { w: any }) {
  const d = w.dna || {};
  return (
    <Box title="🧬 Your Couple Taste DNA" sub={d.vibe}>
      <div className="mb-3 flex gap-1.5">{(d.palette || []).map((c: string) => <span key={c} className="h-6 w-10 rounded-lg" style={{ background: c }} />)}</div>
      {d.shared?.length ? <div className="flex flex-wrap gap-1.5">{d.shared.slice(0, 10).map((s: any) => <span key={s.name} className="chip">💞 {s.name}</span>)}</div>
        : <div className="text-xs text-mut">No shared loves yet — once both of you add tastes, they'll show here.</div>}
      <Link to="/app/dna" className="mt-3 inline-block text-sm font-medium text-brand underline">Open Couple DNA</Link>
    </Box>
  );
}
