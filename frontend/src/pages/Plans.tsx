import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Calendar,
  CalendarCheck,
  Compass,
  Film,
  Gift,
  GlassWater,
  MapPin,
  MessageCircleHeart,
  Music,
  Palette,
  Plus,
  Sparkles,
  Trash2,
  Utensils
} from "lucide-react";
import clsx from "clsx";
import { api } from "../lib/api";
import { Empty, PageTitle, Spinner } from "../components/ui";

export default function Plans() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<string>("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["plans"],
    queryFn: () => api("/api/plans"),
    refetchInterval: 30000,
  });

  const handleDeletePlan = async (itemId: string) => {
    setDeletingId(itemId);
    try {
      await api(`/api/calendar/items/${itemId}`, { method: "DELETE" });
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["plans"] }),
        qc.invalidateQueries({ queryKey: ["calendar"] }),
        qc.invalidateQueries({ queryKey: ["recommends"] }),
      ]);
    } catch (err) {
      console.warn("Failed to delete plan:", err);
    } finally {
      setDeletingId(null);
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

  if (isLoading) return <Spinner />;

  const allPlans = data?.plans || [];
  const filteredPlans = filter === "all"
    ? allPlans
    : allPlans.filter((p: any) => p.category === filter);

  return (
    <div className="space-y-6">
      {/* Title & Action */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <PageTitle
          title="✨ Our Plans"
          sub="Everyday couple plans, movie streaming nights, dinner dates, and spontaneous getaways"
          right={
            <Link
              to="/app/chat"
              className="btn-primary inline-flex items-center gap-1.5 text-xs py-2 px-3.5 shadow-xs"
            >
              <Plus className="h-4 w-4" /> Plan with AI
            </Link>
          }
        />

        {/* Filter Pills */}
        {allPlans.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 rounded-full border border-line bg-white p-1 text-xs">
            <button
              onClick={() => setFilter("all")}
              className={clsx(
                "rounded-full px-3 py-1 font-medium transition",
                filter === "all" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
              )}
            >
              All ({allPlans.length})
            </button>
            <button
              onClick={() => setFilter("movie")}
              className={clsx(
                "rounded-full px-3 py-1 font-medium transition",
                filter === "movie" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
              )}
            >
              Movies
            </button>
            <button
              onClick={() => setFilter("dining")}
              className={clsx(
                "rounded-full px-3 py-1 font-medium transition",
                filter === "dining" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
              )}
            >
              Dining
            </button>
            <button
              onClick={() => setFilter("travel")}
              className={clsx(
                "rounded-full px-3 py-1 font-medium transition",
                filter === "travel" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
              )}
            >
              Getaways
            </button>
          </div>
        )}
      </div>

      {/* Plans List */}
      {filteredPlans.length > 0 ? (
        <div className="space-y-3">
          {filteredPlans.map((plan: any) => {
            const isDeleting = deletingId === plan.id;

            return (
              <div
                key={plan.id}
                className="card p-4 sm:p-5 flex flex-col gap-3 border border-line hover:border-brand/30 transition shadow-2xs group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="h-9 w-9 shrink-0 rounded-xl bg-blush/70 border border-brand/20 flex items-center justify-center shadow-3xs">
                      {getCategoryIcon(plan.category)}
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-base text-ink group-hover:text-brand transition">
                          {plan.title}
                        </span>
                        <span className="badge bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px] font-bold flex items-center gap-1">
                          <CalendarCheck className="h-3 w-3 text-emerald-600" /> Confirmed Plan
                        </span>
                        {plan.date && (
                          <span className="badge bg-purple-50 text-purple-700 text-[11px] font-medium">
                            📅 {plan.date} {plan.time ? `• ${plan.time}` : ""}
                          </span>
                        )}
                        {plan.is_private && (
                          <span className="badge bg-amber-50 text-amber-800 border-amber-200 text-[10px] font-bold">
                            🤫 Secret Surprise
                          </span>
                        )}
                      </div>
                      {plan.subtitle && (
                        <div className="text-xs font-medium text-brand mt-0.5">{plan.subtitle}</div>
                      )}
                    </div>
                  </div>

                  <button
                    type="button"
                    disabled={isDeleting}
                    onClick={() => handleDeletePlan(plan.id)}
                    className="text-mut hover:text-red-600 p-1.5 rounded-lg hover:bg-red-50 transition"
                    title="Remove from plans"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                {plan.description && (
                  <p className="text-sm text-mut pl-12 leading-relaxed">{plan.description}</p>
                )}

                <div className="pt-2 border-t border-line/60 flex items-center justify-between gap-2 pl-12">
                  <div className="flex items-center gap-3">
                    {plan.maps_url && (
                      <a
                        href={plan.maps_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-mut hover:text-brand flex items-center gap-1"
                      >
                        <MapPin className="h-3.5 w-3.5" /> View on Map
                      </a>
                    )}
                    <Link
                      to="/app/calendar"
                      className="text-xs text-mut hover:text-brand flex items-center gap-1"
                    >
                      <Calendar className="h-3.5 w-3.5" /> View in Calendar
                    </Link>
                  </div>

                  <Link
                    to="/app/chat"
                    className="text-xs font-medium text-brand hover:underline flex items-center gap-1"
                  >
                    <MessageCircleHeart className="h-3.5 w-3.5" /> Chat with WeaveTwo AI about this plan →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="card p-12 text-center border border-line space-y-4 bg-white/70">
          <div className="mx-auto w-12 h-12 rounded-full bg-cream border border-line flex items-center justify-center text-mut shadow-3xs">
            <Sparkles className="h-6 w-6 text-brand" />
          </div>
          <div>
            <h3 className="h-serif text-xl font-bold text-ink">No everyday plans scheduled yet</h3>
            <p className="text-xs text-mut max-w-md mx-auto mt-1 leading-relaxed">
              Plans are for your everyday couple moments: a movie streaming tonight, a weekend dinner table,
              or a spontaneous 2-day getaway. Big celebrations live under <b>Our Events</b>.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link to="/app/chat" className="btn-primary text-xs px-5 py-2.5 shadow-xs flex items-center gap-1.5">
              <MessageCircleHeart className="h-4 w-4" /> Plan a date with AI
            </Link>
            <Link to="/app/recommends" className="btn-ghost text-xs px-4 py-2 border border-line flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-brand" /> Browse Recommends
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
