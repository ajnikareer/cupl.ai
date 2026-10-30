import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CalendarCheck,
  CalendarPlus,
  Check,
  Compass,
  Film,
  Gift,
  Heart,
  Lock,
  MapPin,
  MessageCircleHeart,
  Sparkles,
  Utensils
} from "lucide-react";
import clsx from "clsx";
import { api } from "../lib/api";
import { Empty, PageTitle, Spinner } from "../components/ui";

export default function Recommends() {
  const qc = useQueryClient();
  const nav = useNavigate();
  const [tab, setTab] = useState<"couple" | "private">("couple");
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["recommends"],
    queryFn: () => api("/api/recommends"),
    refetchInterval: 30000,
  });

  if (isLoading) return <Spinner />;

  const coupleRecs = data?.couple_recs || [];
  const privateRecs = data?.private_recs || [];
  const partnerName = data?.partner_name || "your partner";
  const coupleVibe = data?.couple_vibe || "Romantic & Elegant";

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
      // Invalidate both calendar and recommends caches so UI updates instantaneously!
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
      case "gifting":
      case "surprise":
        return <Gift className="h-4 w-4 text-brand" />;
      default:
        return <Sparkles className="h-4 w-4 text-gold" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Perspective Tabs */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <PageTitle
          title="✨ Recommends"
          sub="Taste-intelligence recommendations for your happily ever after"
        />
        <div className="flex rounded-full border border-line bg-white p-1 text-xs">
          <button
            onClick={() => setTab("couple")}
            className={clsx(
              "flex items-center gap-1.5 rounded-full px-4 py-2 font-medium transition",
              tab === "couple" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
            )}
          >
            <Heart className="h-3.5 w-3.5" /> For Both of Us
          </button>
          <button
            onClick={() => setTab("private")}
            className={clsx(
              "flex items-center gap-1.5 rounded-full px-4 py-2 font-medium transition",
              tab === "private" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
            )}
          >
            <Lock className="h-3.5 w-3.5" /> Just for You (Private)
          </button>
        </div>
      </div>

      {/* Couple Tab */}
      {tab === "couple" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-2xl bg-gradient-to-r from-blush/60 to-cream border border-brand/15 p-4 text-xs">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand shrink-0" />
              <span>
                Curated using your Couple Taste DNA: <b>{coupleVibe}</b>.
              </span>
            </div>
            <Link to="/app/dna" className="font-semibold text-brand hover:underline shrink-0">
              View Couple DNA →
            </Link>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {coupleRecs.map((rec: any) => {
              const isAdded = Boolean(rec.added_to_calendar);
              const isBusy = togglingId === rec.id;

              return (
                <div
                  key={rec.id}
                  className="card overflow-hidden flex flex-col justify-between p-5 border border-line hover:border-brand/30 transition shadow-2xs group"
                >
                  <div className="space-y-3">
                    {/* Category & Affinity Badge */}
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-xs font-semibold text-mut">
                        {getCategoryIcon(rec.category)}
                        {rec.category_label}
                      </span>
                      {rec.affinity && (
                        <span className="badge border-brand/20 bg-blush text-brand text-[10px] font-bold">
                          {Math.round(rec.affinity * 100)}% Match
                        </span>
                      )}
                    </div>

                    {/* Image if available */}
                    {rec.image && (
                      <div className="h-36 w-full overflow-hidden rounded-xl bg-cream">
                        <img
                          src={rec.image}
                          alt=""
                          className="h-full w-full object-cover group-hover:scale-105 transition duration-300"
                        />
                      </div>
                    )}

                    {/* Title & Description */}
                    <div>
                      <h3 className="h-serif text-lg text-ink font-semibold group-hover:text-brand transition">
                        {rec.title}
                      </h3>
                      {rec.subtitle && (
                        <div className="text-xs font-medium text-brand mt-0.5">{rec.subtitle}</div>
                      )}
                      <p className="text-xs text-mut mt-2 line-clamp-3 leading-relaxed">
                        {rec.description}
                      </p>
                    </div>

                    {/* Why this fits */}
                    {rec.why && (
                      <div className="rounded-xl bg-cream/70 p-2.5 text-[11px] text-mut border border-line/60">
                        <span className="font-semibold text-ink">Why you two will love it: </span>
                        {rec.why}
                      </div>
                    )}
                  </div>

                  {/* Actions & Calendar Toggle Icon */}
                  <div className="mt-4 pt-3 border-t border-line/70 flex items-center justify-between gap-2">
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
                      title={isAdded ? "Remove from your calendar" : "Add to your calendar"}
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

                    <div className="flex items-center gap-1">
                      {rec.maps_url && (
                        <a
                          href={rec.maps_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded-full p-2 text-mut hover:text-brand hover:bg-cream transition"
                          title="Open in Google Maps"
                        >
                          <MapPin className="h-4 w-4" />
                        </a>
                      )}
                      <Link
                        to="/app/chat"
                        className="rounded-full p-2 text-mut hover:text-brand hover:bg-cream transition"
                        title="Discuss in WeaveWed AI Chat"
                      >
                        <MessageCircleHeart className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
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
                <b> {partnerName}</b>'s WeaveWed account will never show or hint at these.
              </p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {privateRecs.map((rec: any) => {
              const isAdded = Boolean(rec.added_to_calendar);
              const isBusy = togglingId === rec.id;

              return (
                <div
                  key={rec.id}
                  className="card p-6 border border-line hover:border-brand/40 transition flex flex-col justify-between shadow-2xs space-y-4"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-xs font-semibold text-brand">
                        <Gift className="h-4 w-4 text-brand" /> {rec.category_label}
                      </span>
                      <span className="badge border-brand/20 bg-blush text-brand text-[10px] font-bold">
                        Secret Surprise
                      </span>
                    </div>

                    <div>
                      <h3 className="h-serif text-xl text-ink font-semibold">{rec.title}</h3>
                      <p className="text-xs text-mut mt-1.5 leading-relaxed">{rec.description}</p>
                    </div>

                    {rec.why && (
                      <div className="rounded-xl bg-cream p-3 text-xs text-mut">
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
                      <Sparkles className="h-3.5 w-3.5" /> Plan with WeaveWed
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

