import { useQuery, useQueryClient } from "@tanstack/react-query";
import { signOut } from "firebase/auth";
import { useEffect, useState } from "react";
import { Check, Copy, Eye, EyeOff, Trash2 } from "lucide-react";
import clsx from "clsx";
import { api } from "../lib/api";
import { auth } from "../lib/firebase";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

const STATUSES = ["dating", "engaged", "married", "parents"];

export default function Me() {
  const qc = useQueryClient();
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me") });
  const { data: tastes } = useQuery({ queryKey: ["tastes"], queryFn: () => api("/api/tastes") });
  const { data: mem } = useQuery({ queryKey: ["memory"], queryFn: () => api("/api/memory") });
  const [name, setName] = useState("");
  const [invite, setInvite] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [code, setCode] = useState("");
  const [err, setErr] = useState<any>(null);
  useEffect(() => { if (me?.user?.name) setName(me.user.name); }, [me?.user?.name]);
  if (!me) return <Spinner />;
  const wrap = async (fn: () => Promise<any>) => { setErr(null); try { await fn(); qc.invalidateQueries(); } catch (e) { setErr(e); } };
  const grouped: Record<string, any[]> = {};
  (tastes?.facts || []).forEach((f: any) => { (grouped[f.category] ||= []).push(f); });
  const cats = me.categories || {};

  return (
    <div className="space-y-6">
      <PageTitle title="Me" right={<button type="button" className="btn-ghost" onClick={() => { localStorage.removeItem("ww_dev_token"); try { signOut(auth); } catch {} window.location.href = "/login"; }}>Sign out</button>} />
      <ErrorBox error={err} />
      <div className="card space-y-4 p-6">
        <div className="flex flex-col gap-2 sm:flex-row">
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} aria-label="Your name" />
          <button type="button" className="btn-primary" disabled={!name.trim()} onClick={() => wrap(() => api("/api/me", { method: "PATCH", body: { name } }))}>Save name</button>
        </div>
        <div><div className="mb-1 text-xs text-mut">Love status</div>
          <div className="flex flex-wrap gap-1.5">{STATUSES.map((s) => (
            <button type="button" key={s} onClick={() => wrap(() => api("/api/couple", { method: "PATCH", body: { status: s } }))} className={clsx("chip capitalize", me.couple?.status === s && "chip-on")}>{s}</button>))}</div>
        </div>
      </div>

      <div className="card space-y-3 p-6">
        <h2 className="h-serif text-xl text-brand">💞 Partner</h2>
        {me.partner ? <p>You're planning together with <b>{me.partner.name}</b>.</p> : (<>
          <p className="text-sm text-mut">Invite your partner — or join theirs with a code.</p>
          {invite ? (
            <div className="flex items-center gap-2 rounded-2xl bg-cream p-2 text-xs">
              <span className="flex-1 break-all">{(invite.link || "").replace(/^https?:\/\/[^\/]+/, window.location.origin)}</span>
              <button type="button" className="btn-ghost" onClick={async () => { const l = (invite.link || "").replace(/^https?:\/\/[^\/]+/, window.location.origin); await navigator.clipboard.writeText(l).catch(() => {}); setCopied(true); }}>{copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}</button>
            </div>
          ) : <button type="button" className="btn-primary" onClick={() => wrap(async () => setInvite(await api("/api/couple/invite", { method: "POST" })))}>Create invite link</button>}
          <div className="flex gap-2">
            <input className="input" placeholder="Partner's invite code" value={code} onChange={(e) => setCode(e.target.value)} />
            <button type="button" className="btn-ghost" disabled={!code.trim()} onClick={() => wrap(() => api("/api/couple/join", { method: "POST", body: { code: code.trim() } }))}>Join</button>
          </div>
        </>)}
      </div>

      <div className="card space-y-4 p-6">
        <h2 className="h-serif text-xl text-brand">✨ My tastes</h2>
        <AddTaste cats={cats} onAdded={() => qc.invalidateQueries({ queryKey: ["tastes"] })} />
        {!Object.keys(grouped).length && <p className="text-sm text-mut">No tastes yet — add some here or just chat with WeaveWed.</p>}
        {Object.entries(grouped).map(([cat, items]) => (
          <div key={cat}>
            <div className="mb-1.5 text-xs uppercase tracking-wider text-mut">{cats[cat] || cat}</div>
            <div className="flex flex-wrap gap-1.5">
              {items.map((f) => (
                <span key={f.id} className={clsx("chip", f.sentiment < 0 && "border-red-200 bg-red-50", f.source === "hint" && "border-dashed")}>
                  {f.image && <img src={f.image} alt="" className="h-5 w-5 rounded-full object-cover" />}
                  {f.sentiment < 0 ? "✗ " : ""}{f.text}
                  {f.resolution === "unresolved" && <span className="text-[10px] text-mut" title="Not matched to taste intelligence yet">•</span>}
                  {f.source === "hint" ? (
                    <button type="button" className="text-[10px] font-medium text-gold" title="Your partner mentioned this — confirm it's you"
                      onClick={() => wrap(() => api(`/api/tastes/${f.id}`, { method: "PATCH", body: { confirm: true } }))}>partner's guess · confirm</button>
                  ) : (
                    <button type="button" title={f.visibility === "private" ? "Private — tap to share with partner" : "Shared with partner — tap to make private"}
                      onClick={() => wrap(() => api(`/api/tastes/${f.id}`, { method: "PATCH", body: { visibility: f.visibility === "private" ? "shared" : "private" } }))}>
                      {f.visibility === "private" ? <EyeOff className="h-3.5 w-3.5 text-mut" /> : <Eye className="h-3.5 w-3.5 text-mut" />}
                    </button>)}
                  <button type="button" aria-label="Delete" onClick={() => wrap(() => api(`/api/tastes/${f.id}`, { method: "DELETE" }))}><Trash2 className="h-3.5 w-3.5 text-mut" /></button>
                </span>))}
            </div>
          </div>
        ))}
        <p className="text-xs text-mut">👁 Shared tastes are visible to your partner. Private ones still shape your plans but are never shown. Dashed = your partner's guess about you.</p>
      </div>

      <div className="card space-y-3 p-6">
        <h2 className="h-serif text-xl text-brand">🧠 What WeaveWed remembers</h2>
        {mem?.summary && <p className="rounded-2xl bg-cream p-3 text-sm italic">{mem.summary}</p>}
        {Object.entries(mem?.profile || {}).filter(([k, v]) => typeof v === "string" && !["greeted", "invite_offered"].includes(k)).map(([k, v]: any) => (
          <div key={k} className="text-sm"><span className="capitalize text-mut">{k.replace(/_/g, " ")}:</span> {v}</div>))}
        {(mem?.decisions || []).map((d: any) => (
          <div key={d.id} className="flex items-start gap-2 text-sm"><span className="flex-1">📌 {d.summary}{d.private_to && " 🤫"}</span>
            <button type="button" aria-label="Forget" onClick={() => wrap(() => api(`/api/memory/decisions/${d.id}`, { method: "DELETE" }))}><Trash2 className="h-4 w-4 text-mut" /></button></div>))}
        {(mem?.episodes || []).map((e: any) => (
          <div key={e.id} className="flex items-start gap-2 text-sm"><span className="flex-1">📖 {e.summary}</span>
            <button type="button" aria-label="Forget" onClick={() => wrap(() => api(`/api/memory/episodes/${e.id}`, { method: "DELETE" }))}><Trash2 className="h-4 w-4 text-mut" /></button></div>))}
        {!mem?.decisions?.length && !mem?.episodes?.length && !mem?.summary && <p className="text-sm text-mut">Nothing yet — decisions and experiences you share in chat show up here.</p>}
      </div>
    </div>
  );
}

const SEARCHABLE = ["music", "film", "tv", "book", "podcast", "fashion", "travel", "place", "celebrity", "game"];

function AddTaste({ cats, onAdded }: { cats: Record<string, string>; onAdded: () => void }) {
  const [cat, setCat] = useState("music");
  const [q, setQ] = useState("");
  const [res, setRes] = useState<any[]>([]);
  const [amb, setAmb] = useState<any[] | null>(null);
  const [dislike, setDislike] = useState(false);
  const [priv, setPriv] = useState(false);
  const [err, setErr] = useState<any>(null);
  useEffect(() => {
    if (!q.trim() || !SEARCHABLE.includes(cat)) { setRes([]); return; }
    const t = setTimeout(() => api(`/api/qloo/search?q=${encodeURIComponent(q.trim())}&category=${cat}`).then((r: any) => setRes(r.results || [])).catch(() => setRes([])), 280);
    return () => clearTimeout(t);
  }, [q, cat]);
  const add = async (name: string, entity_id?: string, image?: string) => {
    setErr(null);
    try {
      const r: any = await api("/api/tastes", { method: "POST", body: { category: cat, name, entity_id: entity_id || null, image: image || null, sentiment: dislike ? -0.8 : 0.85, visibility: priv ? "private" : "shared" } });
      if (r?.ambiguous) { setAmb(r.candidates); return; }
      setQ(""); setRes([]); setAmb(null); onAdded();
    } catch (e) { setErr(e); }
  };
  return (
    <div className="space-y-2 rounded-2xl bg-cream p-3">
      <div className="flex flex-col gap-2 sm:flex-row">
        <select className="input sm:w-56" value={cat} onChange={(e) => setCat(e.target.value)}>{Object.entries(cats).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <input className="input" value={q} onChange={(e) => { setQ(e.target.value); setAmb(null); }} placeholder="Search a singer, film, designer, place…" />
        <button type="button" className="btn-primary" disabled={!q.trim()} onClick={() => add(q.trim())}>Add</button>
      </div>
      <div className="flex gap-4 text-xs">
        <label className="flex items-center gap-1"><input type="checkbox" checked={dislike} onChange={(e) => setDislike(e.target.checked)} className="accent-brand" /> I dislike this</label>
        <label className="flex items-center gap-1"><input type="checkbox" checked={priv} onChange={(e) => setPriv(e.target.checked)} className="accent-brand" /> Keep private</label>
      </div>
      {amb && <div className="rounded-xl bg-white p-2 text-sm"><div className="mb-1 text-xs text-mut">Which one did you mean?</div><div className="flex flex-wrap gap-1.5">{amb.map((c) => <button type="button" key={c.entity_id} className="chip" onClick={() => add(c.name, c.entity_id, c.image)}>{c.label}</button>)}</div></div>}
      {res.length > 0 && <div className="flex flex-wrap gap-1.5">{res.map((r) => <button type="button" key={r.entity_id} className="chip" onClick={() => add(r.name, r.entity_id, r.image)}>{r.image && <img src={r.image} alt="" className="h-5 w-5 rounded-full object-cover" />}{r.name}{r.sub && <span className="text-[10px] text-mut">{r.sub}</span>}</button>)}</div>}
      <ErrorBox error={err} />
    </div>
  );
}
