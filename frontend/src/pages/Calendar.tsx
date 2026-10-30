import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CalendarDays,
  CalendarHeart,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Circle,
  Clock,
  Heart,
  List,
  MapPin,
  Plus,
  Sparkles,
  Trash2,
  Utensils,
  Film,
  Compass
} from "lucide-react";
import clsx from "clsx";
import { api } from "../lib/api";
import { PageTitle, Spinner } from "../components/ui";

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  wedding: { bg: "bg-brand/10", text: "text-brand", border: "border-brand/30" },
  prewedding: { bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200" },
  engagement: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  trip: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  honeymoon: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
  dining: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
  movie: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  todo: { bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-200" },
  surprise: { bg: "bg-fuchsia-50", text: "text-fuchsia-700", border: "border-fuchsia-200" },
  travel: { bg: "bg-teal-50", text: "text-teal-700", border: "border-teal-200" },
};

export default function CalendarPage() {
  const qc = useQueryClient();
  const [view, setView] = useState<"month" | "timeline">("month");
  const [curDate, setCurDate] = useState(() => new Date());
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newCategory, setNewCategory] = useState("dining");
  const [saving, setSaving] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["calendar"],
    queryFn: () => api("/api/calendar"),
    refetchInterval: 15000,
  });

  if (isLoading) return <Spinner />;

  const conflicts = data?.conflicts || [];
  const countdowns = data?.countdowns || [];
  const unified = data?.unified || [];

  const year = curDate.getFullYear();
  const month = curDate.getMonth();

  const prevMonth = () => setCurDate(new Date(year, month - 1, 1));
  const nextMonth = () => setCurDate(new Date(year, month + 1, 1));
  const goToday = () => setCurDate(new Date());

  // Month grid calculations
  const firstDay = new Date(year, month, 1).getDay(); // 0 is Sunday
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  // Group events by day in current month
  const eventsByDay: Record<number, any[]> = {};
  unified.forEach((e: any) => {
    if (!e.start_date) return;
    const d = new Date(e.start_date);
    if (d.getFullYear() === year && d.getMonth() === month) {
      const dayNum = d.getDate();
      eventsByDay[dayNum] = eventsByDay[dayNum] || [];
      eventsByDay[dayNum].push(e);
    }
  });

  const handleAddCustom = async (e: any) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDate) return;
    setSaving(true);
    try {
      await api("/api/calendar/items", {
        method: "POST",
        body: {
          title: newTitle.trim(),
          date: newDate,
          category: newCategory,
        },
      });
      setShowAddModal(false);
      setNewTitle("");
      setNewDate("");
      qc.invalidateQueries({ queryKey: ["calendar"] });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteItem = async (id: string) => {
    try {
      await api(`/api/calendar/items/${id}`, { method: "DELETE" });
      qc.invalidateQueries({ queryKey: ["calendar"] });
      qc.invalidateQueries({ queryKey: ["recommends"] });
    } catch (err) {
      console.warn("Delete item failed:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title & Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <PageTitle
          title="Our Calendar & Milestones"
          sub="Synchronized schedule, celebration countdowns, and date-night plans"
        />
        <div className="flex items-center gap-2">
          <div className="flex rounded-full border border-line bg-white p-1 text-xs">
            <button
              onClick={() => setView("month")}
              className={clsx(
                "flex items-center gap-1.5 rounded-full px-3 py-1.5 font-medium transition",
                view === "month" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
              )}
            >
              <CalendarDays className="h-3.5 w-3.5" /> Month
            </button>
            <button
              onClick={() => setView("timeline")}
              className={clsx(
                "flex items-center gap-1.5 rounded-full px-3 py-1.5 font-medium transition",
                view === "timeline" ? "bg-brand text-white shadow-xs" : "text-ink hover:text-brand"
              )}
            >
              <List className="h-3.5 w-3.5" /> Timeline
            </button>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex items-center gap-1.5 text-xs py-2 px-3.5"
          >
            <Plus className="h-4 w-4" /> Add Date
          </button>
        </div>
      </div>

      {/* Countdown Chips */}
      {countdowns.length > 0 && (
        <div className="flex flex-wrap gap-2.5">
          {countdowns.map((cd: any) => (
            <div
              key={cd.space_id}
              className="flex items-center gap-2 rounded-2xl border border-line bg-white/90 px-3.5 py-2 text-xs shadow-2xs backdrop-blur"
            >
              <CalendarHeart className="h-4 w-4 text-brand" />
              <span className="font-semibold text-brand">{cd.title}:</span>
              {cd.days_left > 0 ? (
                <span className="font-bold text-ink">
                  {cd.days_left} {cd.days_left === 1 ? "day" : "days"} to go
                </span>
              ) : cd.days_left === 0 ? (
                <span className="font-bold text-emerald-600">Happening Today! 🎉</span>
              ) : (
                <span className="text-mut">Completed</span>
              )}
              <span className="text-[11px] text-mut">({cd.date})</span>
            </div>
          ))}
        </div>
      )}

      {/* Conflict Alert Banner */}
      {conflicts.length > 0 && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50/90 p-4 shadow-2xs">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600 mt-0.5" />
            <div className="text-xs space-y-1">
              <div className="font-bold text-amber-900">
                Schedule Overlap Detected ({conflicts.length} clashing {conflicts.length === 1 ? "event" : "events"})
              </div>
              {conflicts.map((c: any, i: number) => (
                <div key={i} className="text-amber-800">
                  ⚠️ <b>{c.event1.title}</b> ({c.event1.dates}) overlaps with <b>{c.event2.title}</b> ({c.event2.dates}) on <b>{c.overlap_dates}</b>.
                  You can adjust dates in Event Spaces or ask WeaveWed AI.
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main View: Month Grid vs Timeline */}
      {view === "month" ? (
        <div className="card overflow-hidden p-4 sm:p-6 space-y-4">
          {/* Month Header Navigation */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="h-serif text-2xl text-brand font-medium">
                {MONTH_NAMES[month]} {year}
              </h2>
              <button
                onClick={goToday}
                className="rounded-full border border-line bg-cream px-2.5 py-0.5 text-xs text-mut hover:text-brand transition"
              >
                Today
              </button>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={prevMonth}
                aria-label="Previous month"
                className="rounded-full p-2 text-ink hover:bg-cream transition"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={nextMonth}
                aria-label="Next month"
                className="rounded-full p-2 text-ink hover:bg-cream transition"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Weekday Names */}
          <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-mut">
            <div>Sun</div>
            <div>Mon</div>
            <div>Tue</div>
            <div>Wed</div>
            <div>Thu</div>
            <div>Fri</div>
            <div>Sat</div>
          </div>

          {/* Day Grid */}
          <div className="grid grid-cols-7 gap-1 sm:gap-2">
            {/* Empty slots for start of month */}
            {Array.from({ length: firstDay }).map((_, i) => (
              <div key={`empty-${i}`} className="min-h-[85px] sm:min-h-[105px] rounded-xl bg-cream/30 p-1.5" />
            ))}

            {/* Days of current month */}
            {daysArray.map((day) => {
              const dayEvents = eventsByDay[day] || [];
              const isToday =
                new Date().getDate() === day &&
                new Date().getMonth() === month &&
                new Date().getFullYear() === year;

              return (
                <div
                  key={day}
                  className={clsx(
                    "min-h-[85px] sm:min-h-[105px] rounded-xl border p-1.5 sm:p-2 transition flex flex-col justify-between",
                    isToday ? "border-brand bg-blush/20 shadow-2xs" : "border-line/70 bg-white hover:border-line"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={clsx(
                        "grid h-6 w-6 place-items-center rounded-full text-xs font-medium",
                        isToday ? "bg-brand text-white font-bold" : "text-ink"
                      )}
                    >
                      {day}
                    </span>
                    {dayEvents.length > 0 && (
                      <span className="text-[10px] text-mut font-semibold">
                        {dayEvents.length}
                      </span>
                    )}
                  </div>

                  <div className="space-y-1 mt-1 flex-1 overflow-y-auto max-h-[70px]">
                    {dayEvents.slice(0, 3).map((e: any) => {
                      const col = CATEGORY_COLORS[e.category] || CATEGORY_COLORS.dining;
                      return (
                        <div
                          key={e.id}
                          className={clsx(
                            "truncate rounded-md border px-1.5 py-0.5 text-[10px] font-medium flex items-center justify-between group",
                            col.bg,
                            col.text,
                            col.border
                          )}
                          title={`${e.title} (${e.category})`}
                        >
                          <span className="truncate">{e.title}</span>
                          {e.item_type === "custom" && (
                            <button
                              onClick={(evt) => {
                                evt.stopPropagation();
                                handleDeleteItem(e.id);
                              }}
                              className="opacity-0 group-hover:opacity-100 text-mut hover:text-red-600 transition ml-1"
                              title="Remove from calendar"
                            >
                              <Trash2 className="h-2.5 w-2.5" />
                            </button>
                          )}
                        </div>
                      );
                    })}
                    {dayEvents.length > 3 && (
                      <div className="text-[9px] text-mut font-medium text-center">
                        +{dayEvents.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Timeline Agenda View */
        <div className="card p-6 space-y-4">
          <h2 className="h-serif text-xl text-brand font-medium">Timeline Agenda</h2>
          {unified.length === 0 ? (
            <div className="text-center py-8 text-sm text-mut">
              No events scheduled yet. Create an event space or add recommendations to populate your calendar.
            </div>
          ) : (
            <div className="divide-y divide-line">
              {unified.map((item: any) => {
                const col = CATEGORY_COLORS[item.category] || CATEGORY_COLORS.dining;
                return (
                  <div key={item.id} className="py-3 flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="mt-1">
                        {item.item_type === "space" ? (
                          <CalendarHeart className="h-5 w-5 text-brand" />
                        ) : item.item_type === "todo" ? (
                          item.done ? (
                            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                          ) : (
                            <Circle className="h-5 w-5 text-slate-400" />
                          )
                        ) : (
                          <Sparkles className="h-5 w-5 text-gold" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-ink">{item.title}</span>
                          <span
                            className={clsx(
                              "rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                              col.bg,
                              col.text,
                              col.border
                            )}
                          >
                            {item.category}
                          </span>
                        </div>
                        <div className="text-xs text-mut mt-0.5 flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" /> {item.start_date}
                            {item.end_date && item.end_date !== item.start_date && ` to ${item.end_date}`}
                            {item.time && ` at ${item.time}`}
                          </span>
                          {item.city && (
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" /> {item.city}
                            </span>
                          )}
                          {item.space_title && (
                            <span className="italic">Part of {item.space_title}</span>
                          )}
                        </div>
                        {item.description && (
                          <p className="text-xs text-mut/80 mt-1 max-w-xl">{item.description}</p>
                        )}
                      </div>
                    </div>
                    {item.item_type === "custom" && (
                      <button
                        onClick={() => handleDeleteItem(item.id)}
                        className="rounded-full p-2 text-mut hover:text-red-600 hover:bg-red-50 transition"
                        title="Remove from calendar"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                    {item.item_type === "space" && (
                      <Link
                        to={`/app/spaces/${item.id}`}
                        className="btn-ghost text-xs py-1.5 px-3"
                      >
                        View Space
                      </Link>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Add Custom Date Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="card w-full max-w-md p-6 space-y-4 shadow-xl">
            <h3 className="h-serif text-xl text-brand font-medium">Add to Calendar</h3>
            <form onSubmit={handleAddCustom} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-mut">Event / Plan Title</label>
                <input
                  className="input mt-1"
                  placeholder="e.g. Anniversary Dinner, Sangeet Dance Practice"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-semibold text-mut">Date</label>
                  <input
                    type="date"
                    className="input mt-1"
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-mut">Category</label>
                  <select
                    className="input mt-1"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                  >
                    <option value="dining">Date Night / Dining</option>
                    <option value="movie">Movie / Entertainment</option>
                    <option value="travel">Trip / Getaway</option>
                    <option value="surprise">Surprise / Milestone</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-ghost text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving || !newTitle.trim() || !newDate}
                  className="btn-primary text-xs"
                >
                  {saving ? "Saving..." : "Save to Calendar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
