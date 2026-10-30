import os

content = '''import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Calendar,
  CalendarCheck,
  ChevronRight,
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
  Utensils,
  X,
} from "lucide-react";
import clsx from "clsx";
import { api } from "../lib/api";
import { Empty, PageTitle, Spinner } from "../components/ui";

export default function Plans() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<string>("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [activeModalPlan, setActiveModalPlan] = useState<any | null>(null);

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
          title="✨ Plans"
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

      {/* Plans Grid matching Recommends structure */}
      {filteredPlans.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {filteredPlans.map((plan: any) => {
            const isDeleting = deletingId === plan.id;

            return (
              <div
                key={plan.id}
                onClick={() => setActiveModalPlan(plan)}
                className="rounded-2xl border border-line/80 bg-white p-4 sm:p-5 flex flex-col justify-between hover:border-brand/40 hover:shadow-md transition-all duration-200 group cursor-pointer shadow-2xs"
              >
                <div>
                  {/* Card Header: Icon + Badges + Delete */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="h-9 w-9 shrink-0 rounded-xl bg-blush/70 border border-brand/20 flex items-center justify-center shadow-3xs">
                      {getCategoryIcon(plan.category)}
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap justify-end">
                      <span className="badge bg-emerald-50 text-emerald-800 border-emerald-200/80 text-[10px] font-bold flex items-center gap-1 py-0.5 px-2">
                        <CalendarCheck className="h-3 w-3 text-emerald-600" /> Confirmed
                      </span>
                      {plan.is_private && (
                        <span className="badge bg-amber-50 text-amber-800 border-amber-200 text-[10px] font-bold py-0.5 px-2">
                          🤫 Surprise
                        </span>
                      )}
                      <button
                        type="button"
                        disabled={isDeleting}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeletePlan(plan.id);
                        }}
                        className="text-mut hover:text-red-600 p-1 rounded-lg hover:bg-red-50 transition ml-1"
                        title="Remove from plans"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Category Label Pill */}
                  <div className="text-[10px] font-bold tracking-wider uppercase text-brand/85 mt-3 line-clamp-1">
                    {plan.category_label || plan.category}
                  </div>

                  {/* Title & Subtitle */}
                  <div className="mt-1">
                    <h4 className="font-serif text-base font-bold text-ink leading-snug group-hover:text-brand transition line-clamp-2 min-h-[2.5rem]">
                      {plan.title}
                    </h4>
                    {plan.subtitle && (
                      <p className="text-[11px] font-medium text-mut line-clamp-1 mt-0.5">
                        {plan.subtitle}
                      </p>
                    )}
                  </div>

                  {/* Date & Time Badge */}
                  {plan.date && (
                    <div className="inline-flex items-center gap-1 rounded-md bg-purple-50 text-purple-700 text-[10px] font-medium px-2 py-0.5 mt-2">
                      <span>📅 {plan.date} {plan.time ? `• ${plan.time}` : ""}</span>
                    </div>
                  )}

                  {/* Description snippet */}
                  {plan.description && (
                    <p className="text-xs text-mut/90 leading-relaxed line-clamp-2 mt-2">
                      {plan.description}
                    </p>
                  )}
                </div>

                {/* Footer Actions */}
                <div
                  className="pt-3 mt-3 border-t border-line/60 flex items-center justify-between gap-1.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="flex items-center gap-2">
                    {plan.maps_url ? (
                      <a
                        href={plan.maps_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-mut hover:text-brand flex items-center gap-1"
                      >
                        <MapPin className="h-3.5 w-3.5" /> Map
                      </a>
                    ) : (
                      <Link
                        to="/app/calendar"
                        className="text-xs text-mut hover:text-brand flex items-center gap-1"
                      >
                        <Calendar className="h-3.5 w-3.5" /> Calendar
                      </Link>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => setActiveModalPlan(plan)}
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

      {/* Plan Details Modal */}
      {activeModalPlan && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs animate-in fade-in duration-200"
          onClick={() => setActiveModalPlan(null)}
        >
          <div
            className="relative max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl space-y-4 border border-line"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3 border-b border-line/60 pb-4">
              <div className="flex items-start gap-3">
                <div className="h-11 w-11 rounded-2xl bg-blush/70 border border-brand/20 flex items-center justify-center shadow-3xs shrink-0">
                  {getCategoryIcon(activeModalPlan.category)}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="badge bg-cream border border-line text-[11px] font-medium text-mut uppercase">
                      {activeModalPlan.category}
                    </span>
                    <span className="badge bg-emerald-50 text-emerald-800 border-emerald-200/80 text-[10px] font-bold">
                      ✓ Confirmed Plan
                    </span>
                  </div>
                  <h3 className="h-serif text-xl sm:text-2xl font-bold text-ink mt-1">
                    {activeModalPlan.title}
                  </h3>
                  {activeModalPlan.subtitle && (
                    <p className="text-xs font-medium text-brand mt-0.5">
                      {activeModalPlan.subtitle}
                    </p>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={() => setActiveModalPlan(null)}
                className="rounded-full p-1.5 text-mut hover:bg-cream hover:text-ink transition"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {activeModalPlan.description && (
              <p className="text-sm text-mut leading-relaxed">
                {activeModalPlan.description}
              </p>
            )}

            {/* Date & Time */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {activeModalPlan.date && (
                <span className="badge bg-purple-50 text-purple-700">
                  📅 {activeModalPlan.date} {activeModalPlan.time ? `• ${activeModalPlan.time}` : ""}
                </span>
              )}
              {activeModalPlan.is_private && (
                <span className="badge bg-amber-50 text-amber-800 border-amber-200">
                  🤫 Secret Surprise
                </span>
              )}
            </div>

            {/* Modal Actions */}
            <div className="pt-3 border-t border-line flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                {activeModalPlan.maps_url && (
                  <a
                    href={activeModalPlan.maps_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-brand hover:underline flex items-center gap-1 font-medium"
                  >
                    <MapPin className="h-3.5 w-3.5" /> View on Google Maps
                  </a>
                )}
                <Link
                  to="/app/calendar"
                  className="text-xs text-mut hover:text-brand flex items-center gap-1 font-medium"
                >
                  <Calendar className="h-3.5 w-3.5" /> Calendar
                </Link>
              </div>

              <Link
                to="/app/chat"
                className="btn-primary text-xs py-1.5 px-3.5 shadow-xs flex items-center gap-1.5"
              >
                <MessageCircleHeart className="h-3.5 w-3.5" /> Chat about this plan
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
'''

with open('frontend/src/pages/Plans.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Success updating Plans.tsx!')

