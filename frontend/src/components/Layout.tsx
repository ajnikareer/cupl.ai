import { Bell, CalendarCheck, CalendarDays, CalendarHeart, Dna, Home, MessageCircleHeart, Sparkles, UserRound } from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { api } from "../lib/api";
import { Avatar, Logo } from "./ui";
import VoiceOverlay from "../chat/VoiceOverlay";
import { useChat } from "../chat/ChatContext";

const NAV = [
  { to: "/app", label: "Home", short: "Home", icon: Home, end: true },
  { to: "/app/chat", label: "cupl AI", short: "cupl AI", icon: MessageCircleHeart },
  { to: "/app/recommends", label: "cupl Suggests", short: "Suggests", icon: Sparkles },
  { to: "/app/plans", label: "Our Plans", short: "Plans", icon: CalendarCheck },
  { to: "/app/spaces", label: "Our Events", short: "Events", icon: CalendarHeart },
  { to: "/app/dna", label: "Our DNA", short: "DNA", icon: Dna },
  { to: "/app/calendar", label: "Our Calendar", short: "Calendar", icon: CalendarDays },
  { to: "/app/me", label: "My Profile", short: "Profile", icon: UserRound },
];

export default function Layout() {
  const loc = useLocation();
  const navigate = useNavigate();
  const { voice, startVoice } = useChat();
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me"), refetchInterval: 30000 });
  const onChat = loc.pathname === "/app/chat";
  const userName = me?.user?.name?.split(" ")[0] || "";
  const partnerName = me?.partner?.name?.split(" ")[0] || "";

  return (
    <div className="flex min-h-screen bg-cream">
      <aside className="sticky top-0 hidden h-screen w-[272px] shrink-0 flex-col border-r border-line bg-white/80 p-5 lg:flex">
        <Logo />
        <nav className="mt-8 flex flex-col gap-1">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}
              className={({ isActive }) => clsx("flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm transition",
                isActive ? "bg-blush font-medium text-brand" : "text-ink hover:bg-cream")}>
              <n.icon className="h-[18px] w-[18px]" /> {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto pt-4">
          <a
            href="/intelligence"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1.5 rounded-2xl border border-brand/25 bg-white/90 py-2.5 px-3 text-xs font-bold text-brand shadow-2xs hover:bg-blush transition whitespace-nowrap"
            title="Open QLOO Taste Intelligence & LLM Audit Dashboard in a new tab"
          >
            <span>⚡ QLOO Intelligence Dashboard ↗</span>
          </a>
        </div>
      </aside>

      <main className={clsx("min-w-0 flex-1", onChat ? "h-screen flex flex-col overflow-hidden" : "pb-20 lg:pb-0")}>
        <header className="sticky top-0 z-20 shrink-0 flex items-center justify-between gap-3 border-b border-line bg-cream/85 px-4 py-3 backdrop-blur lg:px-8">
          <div className="lg:hidden"><Logo small /></div>
          <div className="hidden lg:block text-xs font-semibold text-mut">✨ Couple Taste Intelligence AI</div>
          <div className="flex items-center gap-3">
            <NavLink to="/app/notifications" className="relative rounded-full p-2 hover:bg-blush" aria-label="Notifications">
              <Bell className="h-5 w-5 text-brand" />
              {me?.unread > 0 && <span className="absolute -right-0.5 -top-0.5 grid h-5 min-w-[20px] place-items-center rounded-full bg-brand px-1 text-[10px] text-white">{me.unread}</span>}
            </NavLink>
            <div className="flex flex-col items-end">
              <NavLink 
                to="/app/me" 
                className="flex items-center gap-2 rounded-full border border-line bg-white py-1 pl-1 pr-3 text-sm font-medium text-ink shadow-2xs hover:border-brand/40 transition"
                title="My Profile"
              >
                {me?.user?.photo ? (
                  <img src={me.user.photo} alt={userName} className="h-7 w-7 rounded-full object-cover" />
                ) : (
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-blush font-semibold text-brand">
                    {(userName || "?")[0]}
                  </span>
                )}
                <span className="hidden sm:inline">{userName || "My Profile"}</span>
              </NavLink>
              {partnerName && (
                <span className="mt-0.5 hidden sm:block text-[10px] font-medium text-mut tracking-tight whitespace-nowrap">
                  Planning together with <span className="text-brand font-semibold">{partnerName}</span>
                </span>
              )}
            </div>
          </div>
        </header>
        <div className={clsx(onChat ? "flex-1 min-h-0 overflow-hidden" : "mx-auto max-w-6xl p-4 lg:p-8")}>
          <Outlet />
        </div>
      </main>

      {!onChat && voice === "off" && (
        <button
          type="button"
          onClick={() => {
            navigate("/app/chat");
            startVoice();
          }}
          className="fixed bottom-20 right-4 z-30 flex items-center gap-2.5 rounded-full bg-brand py-2 pl-2 pr-5 text-sm font-medium text-white shadow-soft hover:bg-brand/90 transition lg:bottom-6 cursor-pointer"
          aria-label="Ask cupl AI"
          title="Start live call with cupl AI"
        >
          <Avatar size={34} />
          <span>Ask cupl AI</span>
        </button>
      )}

      {!onChat && voice !== "off" && (
        <button
          type="button"
          onClick={() => navigate("/app/chat")}
          className="fixed bottom-20 right-4 z-30 flex items-center gap-2.5 rounded-full bg-green-600 py-2 pl-2 pr-5 text-sm font-medium text-white shadow-soft hover:bg-green-700 transition lg:bottom-6 cursor-pointer animate-pulse"
          aria-label="Return to cupl AI call"
          title="On Call · Tap to return to cupl AI studio"
        >
          <Avatar size={34} ring />
          <span>On Call · Return to cupl AI</span>
        </button>
      )}

      <nav className="fixed inset-x-0 bottom-0 z-30 flex justify-around border-t border-line bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden">
        {NAV.filter((n) => n.to !== "/app/dna" && n.to !== "/app/spaces").map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end}
            className={({ isActive }) => clsx("flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px]", isActive ? "text-brand" : "text-mut")}>
            <n.icon className="h-5 w-5" /> {n.short}
          </NavLink>
        ))}
      </nav>
      <VoiceOverlay />
    </div>
  );
}
