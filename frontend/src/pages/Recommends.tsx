import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarCheck,
  CalendarPlus,
  ChevronRight,
  Compass,
  Film,
  Gift,
  GlassWater,
  Heart,
  Lock,
  MapPin,
  MessageCircleHeart,
  Music,
  Palette,
  Power,
  RefreshCw,
  Sparkles,
  Utensils,
  X
} from "lucide-react";
import clsx from "clsx";
import { api } from "../lib/api";
import { PageTitle, Spinner } from "../components/ui";

export default function Recommends() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<"couple" | "private">("couple");
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isTogglingStatus, setIsTogglingStatus] = useState(false);
  const [activeModalItem, setActiveModalItem] = useState<any | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["recommends"],
    queryFn: () => api("/api/recommends"),
    refetchInterval: 30000,
  });

  if (isLoading) return <Spinner />;

  const isEnabled = data?.enabled !== false;
  const coupleRecs = data?.couple_recs || [];
  const privateRecs = data?.private_recs || [];
  const partnerName = data?.partner_name || "your partner";
  const coupleVibe = data?.couple_vibe || "Romantic & Soulful";
  const stage = (data?.couple_status || "engaged").toLowerCase();
  const cycle = (data?.cycle || 0) + 1;

  const handleToggleStatus = async (currentEnabled: boolean) => {
    setIsTogglingStatus(true);
    try {
      await api("/api/recommends/toggle", {
        method: "POST",
        body: { enabled: !currentEnabled },
      });
      await qc.invalidateQueries({ queryKey: ["recommends"] });
    } catch (err) {
      console.warn("Failed to toggle recommendations status:", err);
    } finally {
      setIsTogglingStatus(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await api("/api/recommends/refresh", {
        method: "POST",
      });
      await qc.invalidateQueries({ queryKey: ["recommends"] });
    } catch (err) {
      console.warn("Failed to refresh recommendations:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleToggleCalendar = async (rec: any) => {
    setTogglingId(rec.id);
    try {
      await api("/api/calendar/toggle-rec", {
        method: "POST",
        body: {
          recommendation_id: rec.id,
          title: rec.title,
          category: rec.category,
          date: rec.suggested_date,
          time: rec.suggested_time || null,
          description: rec.description,
          maps_url: rec.maps_url || null,
          image: rec.image || null,
          is_private: Boolean(rec.is_private),
        },
      });
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["recommends"] }),
        qc.invalidateQueries({ queryKey: ["calendar"] }),
        qc.invalidateQueries({ queryKey: ["plans"] }),
      ]);
      if (activeModalItem?.id === rec.id) {
        setActiveModalItem((prev: any) => prev ? { ...prev, added_to_calendar: !prev.added_to_calendar } : null);
      }
    } catch (err) {
      console.warn("Failed to toggle calendar item:", err);
    } finally {
      setTogglingId(null);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "movie":
        return <Film className="h-4 w-4 text-blue-600" />;
      case "dining":
        return <Utensils className="h-4 w-4 text-orange-600" />;
      case "travel":
        return <Compass className="h-4 w-4 text-emerald-600" />;
      case "cocktail":
      case "culinary":
        return <GlassWater className="h-4 w-4 text-amber-600" />;
      case "decor":
      case "experience":
        return <Palette className="h-4 w-4 text-purple-600" />;
      case "music":
        return <Music className="h-4 w-4 text-indigo-600" />;
      case "gifting":
      case "surprise":
        return <Gift className="h-4 w-4 text-brand" />;
      default:
        return <Sparkles className="h-4 w-4 text-gold" />;
    }
  };

  const getStageBadge = (st: string) => {
    switch (st) {
      case "dating":
        return { label: "Dating • Early Courtship", emoji: "💕", color: "bg-pink-50 text-pink-700 border-pink-200" };
      case "committed":
        return { label: "Committed • Deepening Romance", emoji: "🌹", color: "bg-rose-50 text-rose-700 border-rose-200" };
      case "married":
      case "parents":
        return { label: "Married • Happily Ever After", emoji: "🥂", color: "bg-amber-50 text-amber-800 border-amber-200" };
      case "engaged":
      default:
        return { label: "Engaged • Co-Living & Wedding Prep", emoji: "💍", color: "bg-purple-50 text-purple-700 border-purple-200" };
    }
  };

  const stageBadge = getStageBadge(stage);

  return (
    <div className="space-y-6">
      {/* Top Controls: Title, On/Off Toggle, Refresh Button, and Perspective Tabs */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <PageTitle
          title="✨ Recommends"
          sub="Taste-intelligence recommendations for your happily ever after"
        />

        <div className="flex flex-wrap items-center gap-2">
          {/* On / Off Toggle Button */}
          <button
            type="button"
            onClick={() => handleToggleStatus(isEnabled)}
            disabled={isTogglingStatus}
            className={clsx(
              "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold border transition shadow-3xs",
              isEnabled
                ? "bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100"
                : "bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200"
            )}
            title={isEnabled ? "Recommendations are ON. Click to pause." : "Recommendations are paused. Click to turn ON."}
          >
            <Power className={clsx("h-3.5 w-3.5", isEnabled ? "text-emerald-600" : "text-gray-400")} />
            <span>{isEnabled ? "Recommends: ON" : "Paused"}</span>
          </button>

          {/* Refresh What's New Button */}
          {isEnabled && (
            <button
              type="button"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 rounded-full border border-line bg-white px-3.5 py-1.5 text-xs font-semibold text-ink hover:text-brand hover:border-brand/40 transition shadow-3xs disabled:opacity-50"
              title="Rotate and discover what's new"
            >
              <RefreshCw className={clsx("h-3.5 w-3.5 text-brand", isRefreshing && "animate-spin")} />
              <span>{isRefreshing ? "Refreshing..." : "What's New"}</span>
            </button>
          )}

          {/* Perspective Tabs */}
          <div className="flex rounded-full border border-line bg-white p-1 text-xs">
            <button
              type="button"
              onClick={() => setTab("couple")}
              className={clsx(
                "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 font-medium transition",
                tab === "couple" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
              )}
            >
              <Heart className="h-3.5 w-3.5" /> Both of Us
            </button>
            <button
              type="button"
              onClick={() => setTab("private")}
              className={clsx(
                "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 font-medium transition",
                tab === "private" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
              )}
            >
              <Lock className="h-3.5 w-3.5" /> Private
            </button>
          </div>
        </div>
      </div>

      {/* Paused State Screen */}
      {!isEnabled ? (
        <div className="card p-10 text-center border border-line space-y-4 bg-white/80 max-w-xl mx-auto shadow-sm">
          <div className="mx-auto w-12 h-12 rounded-full bg-cream border border-line flex items-center justify-center text-mut shadow-3xs">
            <Power className="h-6 w-6 text-mut" />
          </div>
          <div>
            <h3 className="h-serif text-xl font-bold text-ink">Taste Recommendations are Paused</h3>
            <p className="text-xs text-mut mt-1.5 leading-relaxed">
              cupl will not surface proactive date night ideas, dining matches, or gifting reminders while paused.
              Turn ON anytime to resume suggestions tailored to your Couple DNA.
            </p>
          </div>
          <div className="pt-2">
            <button
              type="button"
              onClick={() => handleToggleStatus(false)}
              disabled={isTogglingStatus}
              className="btn-primary inline-flex items-center gap-2 text-xs px-5 py-2.5 shadow-xs"
            >
              <Power className="h-4 w-4" /> Turn ON Recommendations
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Active Status Bar: Stage & Couple DNA */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-gradient-to-r from-blush/60 to-cream border border-brand/15 p-3.5 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className={clsx("badge border text-[11px] font-semibold py-0.5 px-2.5", stageBadge.color)}>
                {stageBadge.emoji} {stageBadge.label}
              </span>
              <span className="text-mut">•</span>
              <span className="text-ink">
                Taste DNA: <b>{coupleVibe}</b>
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[11px] text-mut">
                Mix #{cycle} • 4 Curated Picks
              </span>
              <Link to="/app/dna" className="font-semibold text-brand hover:underline shrink-0 text-xs">
                View DNA →
              </Link>
            </div>
          </div>

          {/* Couple Tab: Properly Proportioned Compact Cards */}
          {tab === "couple" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
              {coupleRecs.map((rec: any) => {
                const isAdded = Boolean(rec.added_to_calendar);
                const isBusy = togglingId === rec.id;

                return (
                  <div
                    key={rec.id}
                    onClick={() => setActiveModalItem(rec)}
                    className="rounded-2xl border border-line/80 bg-white p-4 sm:p-5 flex flex-col justify-between hover:border-brand/40 hover:shadow-md transition-all duration-200 group cursor-pointer shadow-2xs"
                  >
                    <div>
                      {/* Card Header: Icon + Overlap Badge */}
                      <div className="flex items-center justify-between gap-2">
                        <div className="h-9 w-9 rounded-xl bg-blush/70 border border-brand/15 flex items-center justify-center shrink-0 shadow-3xs">
                          {getCategoryIcon(rec.category)}
                        </div>
                        {rec.affinity && (
                          <span className="badge bg-emerald-50 text-emerald-800 border-emerald-200/80 text-[10px] font-bold py-0.5 px-2">
                            {Math.round(rec.affinity * 100)}% Match
                          </span>
                        )}
                      </div>

                      {/* Category Label Pill */}
                      <div className="text-[10px] font-bold tracking-wider uppercase text-brand/85 mt-3 line-clamp-1">
                        {rec.category_label}
                      </div>

                      {/* Title & Subtitle */}
                      <div className="mt-1">
                        <h4 className="font-serif text-base font-bold text-ink leading-snug group-hover:text-brand transition line-clamp-2 min-h-[2.5rem]">
                          {rec.title}
                        </h4>
                        {rec.subtitle && (
                          <p className="text-[11px] font-medium text-mut line-clamp-1 mt-0.5">
                            {rec.subtitle}
                          </p>
                        )}
                      </div>

                      {/* Brief text */}
                      <p className="text-xs text-mut/90 leading-relaxed line-clamp-2 mt-2">
                        {rec.description}
                      </p>

                      {/* Date Badge */}
                      {rec.suggested_date && (
                        <div className="inline-flex items-center gap-1 rounded-md bg-purple-50 text-purple-700 text-[10px] font-medium px-2 py-0.5 mt-2.5">
                          <span>📅 {rec.suggested_date}</span>
                        </div>
                      )}
                    </div>

                    {/* Footer Actions */}
                    <div
                      className="pt-3 mt-3 border-t border-line/60 flex items-center justify-between gap-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        type="button"
                        disabled={isBusy}
                        onClick={() => handleToggleCalendar(rec)}
                        className={clsx(
                          "flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold transition shadow-3xs",
                          isAdded
                            ? "bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100"
                            : "bg-white text-ink border border-line hover:border-brand hover:text-brand"
                        )}
                        title={isAdded ? "Remove from calendar" : "Add to calendar"}
                      >
                        {isAdded ? (
                          <>
                            <CalendarCheck className="h-3.5 w-3.5 text-emerald-600" />
                            <span>Saved</span>
                          </>
                        ) : (
                          <>
                            <CalendarPlus className="h-3.5 w-3.5 text-mut group-hover:text-brand" />
                            <span>Add</span>
                          </>
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => setActiveModalItem(rec)}
                        className="text-xs font-semibold text-brand hover:text-brand-dark flex items-center gap-0.5 hover:underline"
                      >
                        <span>Details</span>
                        <ChevronRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Private Tab: Compact Cards */}
          {tab === "private" && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-4 text-xs flex items-start gap-3">
                <Lock className="h-4 w-4 text-amber-700 mt-0.5 shrink-0" />
                <div>
                  <div className="font-bold text-amber-900">100% Private to You</div>
                  <p className="text-amber-800 mt-0.5">
                    These surprise concepts and gifting ideas are generated exclusively for your eyes.
                    <b> {partnerName}</b>'s cupl account will never show or hint at these.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
                {privateRecs.map((rec: any) => {
                  const isAdded = Boolean(rec.added_to_calendar);
                  const isBusy = togglingId === rec.id;

                  return (
                    <div
                      key={rec.id}
                      onClick={() => setActiveModalItem(rec)}
                      className="rounded-2xl border border-line/80 bg-white p-4 sm:p-5 flex flex-col justify-between hover:border-brand/40 hover:shadow-md transition-all duration-200 group cursor-pointer shadow-2xs"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2">
                          <span className="flex items-center gap-1 text-xs font-semibold text-brand">
                            <Gift className="h-3.5 w-3.5 text-brand" /> Secret
                          </span>
                          <span className="badge border-brand/20 bg-blush text-brand text-[10px] font-bold py-0.5 px-2">
                            {rec.price_bracket || "Surprise"}
                          </span>
                        </div>

                        <div className="text-[10px] font-bold tracking-wider uppercase text-mut mt-3 line-clamp-1">
                          {rec.category_label}
                        </div>

                        <div className="mt-1">
                          <h4 className="font-serif text-base font-bold text-ink leading-snug group-hover:text-brand transition line-clamp-2 min-h-[2.5rem]">
                            {rec.title}
                          </h4>
                        </div>

                        <p className="text-xs text-mut/90 leading-relaxed line-clamp-2 mt-2">
                          {rec.description}
                        </p>
                      </div>

                      <div
                        className="pt-3 mt-3 border-t border-line/60 flex items-center justify-between gap-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => handleToggleCalendar(rec)}
                          className={clsx(
                            "flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition shadow-3xs",
                            isAdded
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-300 hover:bg-emerald-100"
                              : "bg-white text-ink border border-line hover:border-brand hover:text-brand"
                          )}
                          title={isAdded ? "Remove reminder" : "Add private reminder"}
                        >
                          {isAdded ? (
                            <>
                              <CalendarCheck className="h-3.5 w-3.5 text-emerald-600" />
                              <span>Saved</span>
                            </>
                          ) : (
                            <>
                              <CalendarPlus className="h-3.5 w-3.5 text-mut" />
                              <span>Remind</span>
                            </>
                          )}
                        </button>

                        <button
                          type="button"
                          onClick={() => setActiveModalItem(rec)}
                          className="text-xs font-semibold text-brand hover:text-brand-dark flex items-center gap-0.5 hover:underline"
                        >
                          <span>Details</span>
                          <ChevronRight className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}

      {/* Detail Modal Popup */}
      {activeModalItem && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/45 backdrop-blur-xs animate-fade-in"
          onClick={() => setActiveModalItem(null)}
        >
          <div
            className="rounded-3xl bg-white max-w-lg w-full p-6 shadow-xl border border-line relative space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 shrink-0 rounded-2xl bg-blush border border-brand/20 flex items-center justify-center shadow-3xs">
                  {getCategoryIcon(activeModalItem.category)}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="badge bg-cream border border-line text-[11px] font-medium text-mut">
                      {activeModalItem.category_label}
                    </span>
                    {activeModalItem.affinity && (
                      <span className="badge border-brand/20 bg-blush text-brand text-[10px] font-bold">
                        {Math.round(activeModalItem.affinity * 100)}% Match
                      </span>
                    )}
                  </div>
                  <h3 className="h-serif text-xl font-bold text-ink mt-1">
                    {activeModalItem.title}
                  </h3>
                  {activeModalItem.subtitle && (
                    <p className="text-xs font-medium text-brand mt-0.5">
                      {activeModalItem.subtitle}
                    </p>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={() => setActiveModalItem(null)}
                className="rounded-full p-1.5 text-mut hover:bg-cream hover:text-ink transition"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Description */}
            <p className="text-sm text-mut leading-relaxed">
              {activeModalItem.description}
            </p>

            {/* Why You Will Love It (Taste Justification) */}
            {activeModalItem.why && (
              <div className="rounded-2xl bg-[#fffaf2] p-3.5 text-xs text-charcoal border border-amber-200/60 space-y-1">
                <div className="font-semibold text-brand flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5" /> Why you two will love it:
                </div>
                <p className="leading-relaxed text-ink/90">{activeModalItem.why}</p>
              </div>
            )}

            {/* Recipe Formula if applicable */}
            {activeModalItem.recipe && (
              <div className="rounded-2xl bg-amber-50/70 p-3.5 text-xs text-amber-950 border border-amber-200 space-y-1">
                <div className="font-semibold text-amber-900">🍸 Signature Recipe Formula:</div>
                <p className="leading-relaxed">{activeModalItem.recipe}</p>
              </div>
            )}

            {/* Extra Metadata: Dates / Budget / Cost */}
            <div className="flex flex-wrap items-center gap-2 text-xs text-mut pt-1">
              {activeModalItem.suggested_date && (
                <span className="badge bg-purple-50 text-purple-700 text-xs">
                  📅 {activeModalItem.suggested_date} {activeModalItem.suggested_time ? `at ${activeModalItem.suggested_time}` : ""}
                </span>
              )}
              {activeModalItem.est_cost && (
                <span className="badge bg-cream border border-line text-xs">
                  💰 Est. ₹{activeModalItem.est_cost.toLocaleString()}
                </span>
              )}
              {activeModalItem.price_bracket && (
                <span className="badge bg-cream border border-line text-xs">
                  🏷️ {activeModalItem.price_bracket}
                </span>
              )}
              {activeModalItem.maps_url && (
                <a
                  href={activeModalItem.maps_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="badge bg-blue-50 text-blue-700 hover:bg-blue-100 flex items-center gap-1 text-xs"
                >
                  <MapPin className="h-3 w-3" /> View Location on Map
                </a>
              )}
            </div>

            {/* Modal Actions */}
            <div className="pt-3 border-t border-line flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => handleToggleCalendar(activeModalItem)}
                className={clsx(
                  "flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition shadow-3xs",
                  activeModalItem.added_to_calendar
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100"
                    : "bg-white text-ink border border-line hover:border-brand hover:text-brand"
                )}
              >
                {activeModalItem.added_to_calendar ? (
                  <>
                    <CalendarCheck className="h-4 w-4 text-emerald-600" />
                    <span>On Calendar</span>
                  </>
                ) : (
                  <>
                    <CalendarPlus className="h-4 w-4 text-mut" />
                    <span>Add to Calendar</span>
                  </>
                )}
              </button>

              <Link
                to="/app/chat"
                className="btn-primary flex items-center gap-1.5 text-xs py-2 px-4 shadow-xs"
              >
                <MessageCircleHeart className="h-4 w-4" /> Plan with cupl AI
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
