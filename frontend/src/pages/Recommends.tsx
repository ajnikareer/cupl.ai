import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarCheck,
  CalendarPlus,
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
  Utensils
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
      ]);
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
              "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold border transition shadow-3xs",
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
              WeaveTwo will not surface proactive date night ideas, dining matches, or gifting reminders while paused.
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
                Curated mix #{cycle}
              </span>
              <Link to="/app/dna" className="font-semibold text-brand hover:underline shrink-0 text-xs">
                View DNA →
              </Link>
            </div>
          </div>

          {/* Couple Tab */}
          {tab === "couple" && (
            <div className="space-y-3">
              {coupleRecs.map((rec: any) => {
                const isAdded = Boolean(rec.added_to_calendar);
                const isBusy = togglingId === rec.id;

                return (
                  <div
                    key={rec.id}
                    className="card p-4 sm:p-5 flex flex-col gap-3 border border-line hover:border-brand/30 transition shadow-2xs group"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className="h-9 w-9 shrink-0 rounded-xl bg-blush/70 border border-brand/20 flex items-center justify-center shadow-3xs">
                          {getCategoryIcon(rec.category)}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold text-base text-ink group-hover:text-brand transition">{rec.title}</span>
                            {rec.affinity && (
                              <span className="badge border-brand/20 bg-blush text-brand text-[10px] font-bold">
                                {Math.round(rec.affinity * 100)}% Match
                              </span>
                            )}
                            <span className="badge bg-cream border border-line text-[11px] font-medium text-mut">
                              {rec.category_label}
                            </span>
                            {rec.suggested_date && (
                              <span className="badge bg-purple-50 text-purple-700 text-[11px] font-medium">
                                📅 {rec.suggested_date}
                              </span>
                            )}
                          </div>
                          {rec.subtitle && (
                            <div className="text-xs font-medium text-brand mt-0.5">{rec.subtitle}</div>
                          )}
                        </div>
                      </div>
                    </div>

                    <p className="text-sm text-mut pl-12 leading-relaxed">{rec.description}</p>

                    {rec.why && (
                      <div className="ml-12 rounded-xl bg-[#fffaf2] p-2.5 text-xs text-charcoal border border-line/50">
                        <span className="font-semibold text-brand">Why you two will love it: </span>
                        {rec.why}
                      </div>
                    )}

                    {rec.recipe && (
                      <div className="ml-12 rounded-xl bg-amber-50/70 p-2.5 text-xs text-amber-950 border border-amber-200">
                        <span className="font-semibold text-amber-900">Recipe Formula: </span>
                        {rec.recipe}
                      </div>
                    )}

                    <div className="pt-2 border-t border-line/60 flex items-center justify-between gap-2 pl-12">
                      <button
                        type="button"
                        disabled={isBusy}
                        onClick={() => handleToggleCalendar(rec)}
                        className={clsx(
                          "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold transition shadow-3xs",
                          isAdded
                            ? "bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100"
                            : "bg-white text-ink border border-line hover:border-brand hover:text-brand"
                        )}
                      >
                        {isAdded ? (
                          <>
                            <CalendarCheck className="h-3.5 w-3.5 text-emerald-600" />
                            <span>On Calendar</span>
                          </>
                        ) : (
                          <>
                            <CalendarPlus className="h-3.5 w-3.5 text-mut group-hover:text-brand" />
                            <span>Add to Calendar</span>
                          </>
                        )}
                      </button>

                      <div className="flex items-center gap-3">
                        {rec.maps_url && (
                          <a
                            href={rec.maps_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-mut hover:text-brand flex items-center gap-1"
                          >
                            <MapPin className="h-3.5 w-3.5" /> View on Map
                          </a>
                        )}
                        <Link
                          to="/app/chat"
                          className="text-xs font-medium text-brand hover:underline flex items-center gap-1"
                        >
                          <MessageCircleHeart className="h-3.5 w-3.5" /> Plan date with WeaveTwo AI →
                        </Link>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Private Tab: Just for You */}
          {tab === "private" && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-4 text-xs flex items-start gap-3">
                <Lock className="h-4 w-4 text-amber-700 mt-0.5 shrink-0" />
                <div>
                  <div className="font-bold text-amber-900">100% Private to You</div>
                  <p className="text-amber-800 mt-0.5">
                    These surprise concepts and gifting ideas are generated exclusively for your eyes.
                    <b> {partnerName}</b>'s WeaveTwo account will never show or hint at these.
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                {privateRecs.map((rec: any) => {
                  const isAdded = Boolean(rec.added_to_calendar);
                  const isBusy = togglingId === rec.id;

                  return (
                    <div
                      key={rec.id}
                      className="card p-5 border border-line hover:border-brand/40 transition flex flex-col justify-between shadow-2xs space-y-3"
                    >
                      <div className="space-y-2.5">
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-1.5 text-xs font-semibold text-brand">
                            <Gift className="h-4 w-4 text-brand" /> {rec.category_label}
                          </span>
                          <span className="badge border-brand/20 bg-blush text-brand text-[10px] font-bold">
                            Secret Surprise
                          </span>
                        </div>

                        <div>
                          <h3 className="h-serif text-lg text-ink font-semibold">{rec.title}</h3>
                          <p className="text-xs text-mut mt-1 leading-relaxed">{rec.description}</p>
                        </div>

                        {rec.why && (
                          <div className="rounded-xl bg-cream p-2.5 text-xs text-mut">
                            <span className="font-semibold text-ink">Why this works: </span>
                            {rec.why}
                          </div>
                        )}

                        {rec.price_bracket && (
                          <div className="text-xs text-mut">
                            <span className="font-semibold text-ink">Budget estimate: </span>
                            {rec.price_bracket}
                          </div>
                        )}
                      </div>

                      <div className="pt-3 border-t border-line flex items-center justify-between">
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => handleToggleCalendar(rec)}
                          className={clsx(
                            "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition shadow-2xs",
                            isAdded
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-300 hover:bg-emerald-100"
                              : "bg-white text-ink border border-line hover:border-brand hover:text-brand"
                          )}
                          title={isAdded ? "Remove from your calendar" : "Add private reminder to calendar"}
                        >
                          {isAdded ? (
                            <>
                              <CalendarCheck className="h-3.5 w-3.5 text-emerald-600" />
                              <span>On Your Calendar</span>
                            </>
                          ) : (
                            <>
                              <CalendarPlus className="h-3.5 w-3.5 text-mut" />
                              <span>Add to Calendar</span>
                            </>
                          )}
                        </button>

                        <Link
                          to="/app/chat"
                          className="btn-primary flex items-center gap-1.5 text-xs py-1.5 px-3"
                        >
                          <Sparkles className="h-3.5 w-3.5" /> Plan with WeaveTwo
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
