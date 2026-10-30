import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Check, ChevronRight, Clock, Coins, Compass, ExternalLink, Heart, MapPin, Music, Palette, RefreshCw, ShieldCheck, Sparkles, Trash2, Users, Utensils, X } from "lucide-react";
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

function getSectionChipLabel(title: string, key: string): string {
  if (key === "venue") return "Venue";
  if (key === "decor") return "Stage & Mandap";
  if (key === "sangeet" || key === "music" || key === "playlist") return "Sangeet & Music";
  if (key === "menu" || key === "food_trail" || key === "drinks_menu") return "Food & Menu";
  if (key === "outfits") return "Outfits";
  if (key === "ceremonies") return "Ceremonies";
  if (key === "shoot_locations") return "Shoot Locations";
  if (key === "destinations") return "Destinations";
  if (key === "itinerary") return "Itinerary";
  if (key === "dates") return "Celebration Dates";
  if (key === "theme") return "Theme Concepts";
  if (key === "staycation" || key === "stays") return "Stays";
  if (key === "gifts") return "Gifts";
  if (key === "activities") return "Activities";
  const clean = title.replace(/Shortlist|Blueprint|Progression|Spec|Route|Concepts|Feast/gi, "").trim();
  return clean || title;
}

function getIconInfo(it: any, secKey?: string) {
  if (it?.act || it?.tempo_bpm || secKey === "sangeet" || secKey === "music" || secKey === "playlist") {
    return { icon: <Music className="h-4 w-4 text-amber-700" />, bg: "bg-amber-100/70 border-amber-200/50" };
  }
  if (it?.course_type || it?.portion_math || secKey === "menu" || secKey === "food_trail" || secKey === "drinks_menu") {
    return { icon: <Utensils className="h-4 w-4 text-emerald-700" />, bg: "bg-emerald-100/70 border-emerald-200/50" };
  }
  if (it?.bride_groom_pairing || it?.hex_colors || secKey === "outfits" || secKey === "gifts") {
    return { icon: <Palette className="h-4 w-4 text-purple-700" />, bg: "bg-purple-100/70 border-purple-200/50" };
  }
  if (it?.lighting_spec || secKey === "ceremonies" || secKey === "decor") {
    return { icon: <Sparkles className="h-4 w-4 text-rose-700" />, bg: "bg-rose-100/70 border-rose-200/50" };
  }
  if (it?.capacity_check || secKey === "venue") {
    return { icon: <Users className="h-4 w-4 text-blue-700" />, bg: "bg-blue-100/70 border-blue-200/50" };
  }
  if (secKey === "itinerary" || secKey === "shoot_locations" || secKey === "destinations" || secKey === "dates" || secKey === "stays") {
    return { icon: <Compass className="h-4 w-4 text-teal-700" />, bg: "bg-teal-100/70 border-teal-200/50" };
  }
  return { icon: <Sparkles className="h-4 w-4 text-brand" />, bg: "bg-blush border-brand/20" };
}

function PlanTab({ s }: { s: any }) {
  const qc = useQueryClient();
  const nav = useNavigate();
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me") });
  const building = s.state === "building";
  const { data: plan, isLoading } = useQuery({ queryKey: ["plan", s.id], queryFn: () => api(`/api/spaces/${s.id}/plan`),
    refetchInterval: building ? 2500 : false });
  const [activeSection, setActiveSection] = useState<string>("all");
  const [activeModalItem, setActiveModalItem] = useState<any | null>(null);
  const [err, setErr] = useState<any>(null);

  const build = async (instruction?: string, keys?: string[]) => {
    setErr(null);
    try {
      await api(`/api/spaces/${s.id}/plan`, { method: "POST", body: { instruction: instruction || null, section_keys: keys || null } });
      qc.invalidateQueries({ queryKey: ["space", s.id] }); qc.invalidateQueries({ queryKey: ["plan", s.id] });
    } catch (e) { setErr(e); }
  };

  const itemMutation = useMutation({
    mutationFn: ({ itemId, status }: { itemId: string; status: string }) =>
      api(`/api/spaces/${s.id}/items/${itemId}`, { method: "PATCH", body: { status } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan", s.id] }),
  });

  const handleSetItemStatus = (itemId: string, currentStatus: string, targetStatus: string) => {
    const nextStatus = currentStatus === targetStatus ? "suggested" : targetStatus;
    itemMutation.mutate({ itemId, status: nextStatus });
    if (activeModalItem?.id === itemId) {
      setActiveModalItem((prev: any) => prev ? { ...prev, status: nextStatus } : null);
    }
  };

  useEffect(() => { if (!building) qc.invalidateQueries({ queryKey: ["plan", s.id] }); }, [building]);

  if (isLoading) return <Spinner />;
  if (!plan && building)
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3 rounded-2xl bg-blush/60 p-3 text-sm"><Spinner className="h-5 w-5" /> Weaving your plan from both your tastes — sections appear as they're ready…</div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-64 rounded-2xl" />)}</div>
      </div>
    );
  if (!plan)
    return (
      <div className="card overflow-hidden text-center max-w-2xl mx-auto shadow-soft border border-border">
        <div className="relative h-44 w-full overflow-hidden">
          <img src={IMG[s.type] || "/img/wedding.jpg"} alt="" className="h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
          <div className="absolute top-4 left-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand text-white text-xs font-semibold shadow-sm">
            <span>🔒</span> Couple Gatekeeper Active
          </div>
          <div className="absolute bottom-4 left-4 right-4 text-left text-white">
            <h1 className="h-serif text-2xl font-bold">{s.title}</h1>
            <p className="text-xs text-white/90">{s.city} • {s.guests || 400} guests • ₹{((s.budget || 2500000) / 100000).toFixed(0)}L budget</p>
          </div>
        </div>
        <div className="space-y-4 p-8">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blush text-brand text-xs font-semibold">
            <span>🌸</span> Awaiting Bride's Tastes & Aesthetic
          </div>
          <h2 className="h-serif text-2xl text-brand font-bold">Groom's Tastes Locked In ✨</h2>
          <p className="mx-auto max-w-lg text-sm text-mut leading-relaxed">
            {me?.user?.name ? `${me.user.name.split(" ")[0]}, your` : "Your"} cultural roots, favorite music, and venue scale are saved! To weave an authentic dual-heritage masterplan, your bride needs to be onboarded so her aesthetic, favorite music, and bridal traditions are harmonized with yours.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button type="button" onClick={() => nav("/app/chat")} className="btn-primary w-full sm:w-auto px-6 py-2.5 flex items-center justify-center gap-2 shadow-sm">
              <span>💌</span> Invite Bride in Chat
            </button>
            <button type="button" onClick={() => build()} className="btn-ghost text-xs text-mut hover:text-brand underline">
              Weave solo preview anyway
            </button>
          </div>
        </div>
      </div>
    );

  const sections = plan.sections || [];
  const totalItems = sections.reduce((acc: number, sec: any) => acc + (sec.items?.length || 0), 0);
  const visibleSections = activeSection === "all"
    ? sections
    : sections.filter((sec: any) => sec.key === activeSection);

  return (
    <div className="space-y-6">
      {building && <div className="flex items-center gap-3 rounded-2xl bg-blush/60 p-3 text-sm"><Spinner className="h-5 w-5" /> Weaving your plan — sections appear as they're ready{plan.instruction ? ` (${plan.instruction})` : ""}…</div>}
      {s.state === "stale" && !building && <div className="rounded-2xl bg-[#fffaf2] p-3 text-sm">Event details changed — <button type="button" className="font-medium text-brand underline" onClick={() => build("Event details changed")}>refresh the plan</button>.</div>}

      {/* Section Filter Chips replacing old input */}
      {!building && sections.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="scroll-thin flex max-w-full items-center gap-1.5 overflow-x-auto rounded-full border border-line bg-white/95 p-1.5 shadow-2xs">
            <button
              type="button"
              onClick={() => setActiveSection("all")}
              className={clsx(
                "rounded-full px-3.5 py-1 text-xs font-semibold transition shrink-0 flex items-center gap-1.5",
                activeSection === "all"
                  ? "bg-brand text-white shadow-xs"
                  : "text-ink hover:text-brand hover:bg-cream"
              )}
            >
              <span>All</span>
              <span className={clsx("rounded-full px-1.5 py-0.2 text-[10px]", activeSection === "all" ? "bg-white/20 text-white" : "bg-cream text-mut")}>
                {totalItems}
              </span>
            </button>

            {sections.map((sec: any) => {
              const label = getSectionChipLabel(sec.title, sec.key);
              const count = sec.items?.length || 0;
              const isSel = activeSection === sec.key;
              return (
                <button
                  key={sec.key}
                  type="button"
                  onClick={() => setActiveSection(sec.key)}
                  className={clsx(
                    "rounded-full px-3.5 py-1 text-xs font-semibold transition shrink-0 flex items-center gap-1.5",
                    isSel
                      ? "bg-brand text-white shadow-xs"
                      : "text-ink hover:text-brand hover:bg-cream"
                  )}
                >
                  <span>{label}</span>
                  {count > 0 && (
                    <span className={clsx("rounded-full px-1.5 py-0.2 text-[10px]", isSel ? "bg-white/20 text-white" : "bg-cream text-mut")}>
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          <button
            type="button"
            onClick={() => confirm("Rebuild the whole plan from scratch?") && build()}
            className="btn-ghost text-xs text-mut hover:text-brand flex items-center gap-1.5 py-1 px-3 rounded-full border border-line bg-white/80 shrink-0"
            title="Rebuild plan"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Rebuild
          </button>
        </div>
      )}

      <ErrorBox error={err} />
      {plan.destination_used && !s.destination && <div className="text-sm text-mut">Planned around your top destination match: <b>{plan.destination_used}</b></div>}

      {/* Sections & Card Grids */}
      <div className="space-y-8">
        {visibleSections.map((sec: any) => (
          <section key={sec.key} className="space-y-3">
            <div className="flex items-end justify-between gap-2 pt-2 border-t border-line/40 first:border-t-0 first:pt-0">
              <div>
                <h2 className="h-serif text-xl sm:text-2xl text-brand">{sec.title}</h2>
                {sec.summary && <p className="text-xs sm:text-sm text-mut mt-0.5">{sec.summary}</p>}
              </div>
              {sec.status !== "pending" && !building && (
                <button
                  type="button"
                  onClick={() => build(`Refresh ${sec.title}`, [sec.key])}
                  className="text-xs text-mut hover:text-brand flex items-center gap-1 shrink-0"
                >
                  <RefreshCw className="inline h-3 w-3" /> refresh
                </button>
              )}
            </div>

            {sec.status === "pending" ? (
              <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {[0, 1, 2].map((i) => <div key={i} className="skeleton h-64 rounded-2xl" />)}
              </div>
            ) : (
              <>
                {sec.error && <div className="mb-3 rounded-2xl bg-blush/50 p-3 text-sm">{sec.error}</div>}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
                  {(sec.items || []).map((it: any) => (
                    <PlanItemCard
                      key={it.id}
                      it={it}
                      sid={s.id}
                      type={s.type}
                      secKey={sec.key}
                      secTitle={getSectionChipLabel(sec.title, sec.key)}
                      onSetStatus={(targetStatus) => handleSetItemStatus(it.id, it.status, targetStatus)}
                      onOpenModal={() => setActiveModalItem({ ...it, secTitle: sec.title, secKey: sec.key })}
                    />
                  ))}
                </div>
              </>
            )}
          </section>
        ))}
      </div>

      <p className="text-xs text-mut">Costs are rough estimates. cupl recommends — you book directly. Plan v{plan.version}.</p>

      {/* Item Details Modal */}
      {activeModalItem && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs animate-in fade-in duration-200"
          onClick={() => setActiveModalItem(null)}
        >
          <div
            className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl space-y-4 border border-line"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-3 border-b border-line/60 pb-4">
              <div className="flex items-start gap-3">
                <div className={clsx("h-11 w-11 rounded-2xl flex items-center justify-center shrink-0 border shadow-3xs", getIconInfo(activeModalItem, activeModalItem.secKey).bg)}>
                  {getIconInfo(activeModalItem, activeModalItem.secKey).icon}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="badge bg-cream border border-line text-[11px] font-medium text-mut">
                      {activeModalItem.secTitle || "EVENT ITEM"}
                    </span>
                    {typeof activeModalItem.affinity === "number" && activeModalItem.affinity > 0 && (
                      <span className="badge border-emerald-200/80 bg-emerald-50 text-emerald-800 text-[10px] font-bold">
                        {Math.round(Math.min(1, activeModalItem.affinity) * 100)}% Match
                      </span>
                    )}
                    {activeModalItem.est_cost > 0 && (
                      <span className="badge bg-cream border border-line text-xs font-semibold text-charcoal">
                        ~{fmtINR(activeModalItem.est_cost)}
                      </span>
                    )}
                  </div>
                  <h3 className="h-serif text-xl sm:text-2xl font-bold text-ink mt-1">
                    {activeModalItem.title}
                  </h3>
                  {activeModalItem.heritage_origin && (
                    <p className="text-xs font-medium text-purple-700 mt-0.5">
                      🏛️ {activeModalItem.heritage_origin}
                    </p>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={() => setActiveModalItem(null)}
                className="rounded-full p-1.5 text-mut hover:bg-cream hover:text-ink transition"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Description */}
            <p className="text-sm text-mut leading-relaxed">
              {activeModalItem.description}
            </p>

            {/* Structured specs */}
            <div className="space-y-2.5 text-xs">
              {activeModalItem.capacity_check && (
                <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-3 text-slate-800 flex items-start gap-2">
                  <Users className="h-4 w-4 text-slate-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-slate-900">Capacity & Scale Check:</div>
                    <div className="leading-relaxed mt-0.5">{activeModalItem.capacity_check}</div>
                  </div>
                </div>
              )}

              {activeModalItem.budget_breakdown && (
                <div className="rounded-xl bg-amber-50/70 border border-amber-200/70 p-3 text-amber-950 flex items-start gap-2">
                  <Coins className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-amber-900">Budget Envelope & Pricing Target:</div>
                    <div className="leading-relaxed mt-0.5">{activeModalItem.budget_breakdown}</div>
                  </div>
                </div>
              )}

              {activeModalItem.portion_math && (
                <div className="rounded-xl bg-emerald-50/80 border border-emerald-200/70 p-3 text-emerald-950">
                  <span className="font-semibold text-emerald-900 flex items-center gap-1.5 mb-1">
                    🍃 Anti-Waste Portioning Math:
                  </span>
                  <p className="leading-relaxed">{activeModalItem.portion_math}</p>
                </div>
              )}

              {activeModalItem.bride_groom_pairing && (
                <div className="rounded-xl bg-purple-50/70 border border-purple-200/60 p-3 text-purple-950">
                  <span className="font-semibold text-purple-900 block mb-1">👫 Styling Pair & Color Harmony:</span>
                  <p className="leading-relaxed">{activeModalItem.bride_groom_pairing}</p>
                </div>
              )}

              {activeModalItem.cue_note && (
                <div className="rounded-xl bg-amber-50/70 border border-amber-200/60 p-3 text-amber-950">
                  <span className="font-semibold text-amber-900 block mb-1">🎬 Choreography & DJ Cue:</span>
                  <p className="leading-relaxed">{activeModalItem.cue_note}</p>
                </div>
              )}

              {activeModalItem.lighting_spec && (
                <div className="rounded-xl bg-amber-50/70 border border-amber-200/60 p-3 text-amber-950">
                  <span className="font-semibold text-amber-900 flex items-center gap-1.5 mb-1">
                    <Sparkles className="h-3.5 w-3.5 text-amber-600" /> Lighting & Camera Spec:
                  </span>
                  <p className="leading-relaxed">{activeModalItem.lighting_spec}</p>
                </div>
              )}

              {activeModalItem.anti_clash_check && (
                <div className="rounded-xl bg-emerald-50/80 border border-emerald-200/60 p-2.5 text-emerald-900 text-xs flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>{activeModalItem.anti_clash_check}</span>
                </div>
              )}

              {activeModalItem.hex_colors && activeModalItem.hex_colors.length > 0 && (
                <div className="rounded-xl border border-line bg-surface p-3 flex flex-wrap items-center gap-2">
                  <span className="text-mut font-medium flex items-center gap-1 text-xs">
                    <Palette className="h-3.5 w-3.5" /> Swatches:
                  </span>
                  <div className="flex flex-wrap items-center gap-2">
                    {activeModalItem.hex_colors.map((hex: string, i: number) => (
                      <span key={i} className="inline-flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-full border border-line bg-white shadow-3xs">
                        <span className="h-3.5 w-3.5 rounded-full border border-black/15 shrink-0" style={{ backgroundColor: hex }} />
                        {hex}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Why this fits both of you */}
            {activeModalItem.why && activeModalItem.why.length > 0 && (
              <div className="rounded-2xl bg-[#fffaf2] p-4 text-xs text-charcoal border border-amber-200/60 space-y-2">
                <div className="font-semibold text-brand flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-amber-600" /> Why this fits both of you (Taste Intelligence):
                </div>
                <ul className="list-disc space-y-1.5 pl-5 leading-relaxed">
                  {activeModalItem.why.map((w: string, i: number) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Maps Link */}
            {activeModalItem.maps_url && (
              <a
                href={activeModalItem.maps_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-brand hover:underline"
              >
                <ExternalLink className="h-3.5 w-3.5" /> Open Location in Google Maps
              </a>
            )}

            {/* Modal Actions */}
            <div className="pt-3 border-t border-line flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleSetItemStatus(activeModalItem.id, activeModalItem.status, "liked")}
                  className={clsx(
                    "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold transition border shadow-3xs",
                    activeModalItem.status === "liked"
                      ? "bg-rose-50 text-rose-700 border-rose-300"
                      : "bg-white text-ink border-line hover:border-brand hover:text-brand"
                  )}
                >
                  <Heart className={clsx("h-3.5 w-3.5", activeModalItem.status === "liked" && "fill-rose-600 text-rose-600")} />
                  <span>{activeModalItem.status === "liked" ? "Loved" : "Love it"}</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleSetItemStatus(activeModalItem.id, activeModalItem.status, "done")}
                  className={clsx(
                    "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold transition border shadow-3xs",
                    activeModalItem.status === "done"
                      ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                      : "bg-white text-ink border-line hover:border-emerald-600 hover:text-emerald-700"
                  )}
                >
                  <Check className="h-3.5 w-3.5" />
                  <span>{activeModalItem.status === "done" ? "Confirmed" : "Confirm"}</span>
                </button>
              </div>

              <button
                type="button"
                onClick={() => setActiveModalItem(null)}
                className="btn-ghost text-xs px-4 py-1.5 border border-line"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PlanItemCard({
  it,
  sid,
  type,
  secKey,
  secTitle,
  onSetStatus,
  onOpenModal,
}: {
  it: any;
  sid: string;
  type: string;
  secKey: string;
  secTitle: string;
  onSetStatus: (targetStatus: string) => void;
  onOpenModal: () => void;
}) {
  const { icon, bg } = getIconInfo(it, secKey);

  return (
    <div
      onClick={onOpenModal}
      className={clsx(
        "rounded-2xl border border-line/80 bg-white p-4 sm:p-5 flex flex-col justify-between hover:border-brand/40 hover:shadow-md transition-all duration-200 group cursor-pointer shadow-2xs",
        it.status === "skipped" && "opacity-50"
      )}
    >
      <div>
        {/* Card Header: Icon + Match / Cost */}
        <div className="flex items-center justify-between gap-2">
          <div className={clsx("h-9 w-9 rounded-xl flex items-center justify-center shrink-0 border shadow-3xs", bg)}>
            {icon}
          </div>
          <div className="flex items-center gap-1.5 flex-wrap justify-end">
            {typeof it.affinity === "number" && it.affinity > 0 && (
              <span className="badge bg-emerald-50 text-emerald-800 border-emerald-200/80 text-[10px] font-bold py-0.5 px-2">
                {Math.round(Math.min(1, it.affinity) * 100)}% Match
              </span>
            )}
            {it.est_cost > 0 && (
              <span className="badge bg-cream border border-line text-xs font-semibold text-charcoal shrink-0">
                ~{fmtINR(it.est_cost)}
              </span>
            )}
          </div>
        </div>

        {/* Category Label Pill */}
        <div className="text-[10px] font-bold tracking-wider uppercase text-brand/85 mt-3 line-clamp-1">
          {secTitle || it.act || it.course_type || "PLAN ITEM"}
        </div>

        {/* Title & Heritage Subtitle */}
        <div className="mt-1">
          <h4 className="font-serif text-base font-bold text-ink leading-snug group-hover:text-brand transition line-clamp-2 min-h-[2.5rem]">
            {it.title}
          </h4>
          {it.heritage_origin && (
            <p className="text-[11px] font-medium text-purple-700 line-clamp-1 mt-0.5">
              🏛️ {it.heritage_origin}
            </p>
          )}
        </div>

        {/* Key Spec Badges */}
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {it.status === "done" && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-md">
              ✓ Confirmed
            </span>
          )}
          {it.loved_by_both && (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md">
              <Heart className="h-2.5 w-2.5 fill-rose-600 inline" /> Loved by both
            </span>
          )}
          {it.capacity_check && (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md" title={it.capacity_check}>
              <Users className="h-3 w-3 text-slate-500" /> {it.capacity_check.split('(')[0].trim()}
            </span>
          )}
          {it.act && (
            <span className="text-[10px] font-medium text-brand bg-brand/10 px-2 py-0.5 rounded-md">
              {it.act}
            </span>
          )}
          {it.course_type && (
            <span className="text-[10px] font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md">
              {it.course_type}
            </span>
          )}
          {it.tempo_bpm && (
            <span className="text-[10px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
              ⏱️ {it.tempo_bpm}
            </span>
          )}
          {it.vibe_tag && (
            <span className="text-[10px] text-amber-800 bg-amber-50 px-2 py-0.5 rounded-md">
              {it.vibe_tag}
            </span>
          )}
          {it.anti_clash_check && (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
              <ShieldCheck className="h-3 w-3 text-emerald-600" /> Anti-clash
            </span>
          )}
          {it.hex_colors && it.hex_colors.length > 0 && (
            <div className="flex items-center gap-1 ml-auto">
              {it.hex_colors.slice(0, 4).map((hex: string, i: number) => (
                <span key={i} className="h-3 w-3 rounded-full border border-black/15 shrink-0" style={{ backgroundColor: hex }} title={hex} />
              ))}
            </div>
          )}
        </div>

        {/* Brief Description */}
        <p className="text-xs text-mut/90 leading-relaxed line-clamp-2 mt-2">
          {it.description}
        </p>

        {/* Taste Reason Preview */}
        {it.why?.length > 0 && (
          <div className="mt-2 text-[11px] text-gold-dark font-medium line-clamp-1">
            💡 {it.why[0]}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div
        className="pt-3 mt-3 border-t border-line/60 flex items-center justify-between gap-1.5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => onSetStatus("liked")}
            className={clsx(
              "flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold transition border shadow-3xs",
              it.status === "liked"
                ? "bg-rose-50 text-rose-700 border-rose-300"
                : "bg-white text-ink border-line hover:border-brand hover:text-brand"
            )}
            title="Love it"
          >
            <Heart className={clsx("h-3 w-3", it.status === "liked" && "fill-rose-600 text-rose-600")} />
            <span>{it.status === "liked" ? "Loved" : "Love"}</span>
          </button>

          <button
            type="button"
            onClick={() => onSetStatus("done")}
            className={clsx(
              "flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold transition border shadow-3xs",
              it.status === "done"
                ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                : "bg-white text-ink border-line hover:border-emerald-600 hover:text-emerald-700"
            )}
            title="Confirm"
          >
            <Check className="h-3 w-3" />
            <span>{it.status === "done" ? "Confirmed" : "Confirm"}</span>
          </button>
        </div>

        <button
          type="button"
          onClick={onOpenModal}
          className="text-xs font-semibold text-brand hover:text-brand-dark flex items-center gap-0.5 hover:underline"
        >
          <span>Details</span>
          <ChevronRight className="h-3.5 w-3.5" />
        </button>
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
