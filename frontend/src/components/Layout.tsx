import { Bell, CalendarDays, CalendarHeart, Dna, Gift, Home, MessageCircleHeart, Sparkles, UserRound } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { api } from "../lib/api";
import { Avatar, Logo } from "./ui";
import ChatPanel from "../chat/ChatPanel";
import VoiceOverlay from "../chat/VoiceOverlay";
import { useChat } from "../chat/ChatContext";

const NAV = [
  { to: "/app", label: "Home", short: "Home", icon: Home, end: true },
  { to: "/app/chat", label: "WeaveTwo AI", short: "Chat", icon: MessageCircleHeart },
  { to: "/app/spaces", label: "Our Plans", short: "Plans", icon: CalendarHeart },
  { to: "/app/calendar", label: "Calendar", short: "Calendar", icon: CalendarDays },
  { to: "/app/recommends", label: "Recommends", short: "Picks", icon: Sparkles },
  { to: "/app/dna", label: "Couple DNA", short: "DNA", icon: Dna },
  { to: "/app/me", label: "Me", short: "Me", icon: UserRound },
];

export default function Layout() {
  const loc = useLocation();
  const { voice } = useChat();
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me"), refetchInterval: 30000 });
  const onChat = loc.pathname === "/app/chat";
  return (
    <div className="flex min-h-screen bg-cream">
      <aside className="sticky top-0 hidden h-screen w-56 shrink-0 flex-col border-r border-line bg-white/80 p-4 lg:flex">
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
        <div className="mt-auto space-y-2">
          <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-blush to-[#ecc9d3] p-4 text-sm">
            {me?.partner ? <>💞 Planning together with <b>{me.partner.name}</b></> : <>Invite your partner — plans get <b>2× more personal</b>.<NavLink to="/app/me" className="mt-2 block font-medium text-brand underline">Invite now</NavLink></>}
          </div>
          <a
            href="/intelligence"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1.5 rounded-2xl border border-brand/25 bg-white/90 py-2.5 px-3 text-xs font-bold text-brand shadow-2xs hover:bg-blush transition"
            title="Open QLOO Taste Intelligence & LLM Audit Dashboard in a new tab"
          >
            <span>⚡ QLOO Intelligence Dashboard ↗</span>
          </a>
        </div>
      </aside>

      <main className="min-w-0 flex-1 pb-20 lg:pb-0">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-line bg-cream/85 px-4 py-3 backdrop-blur lg:px-8">
          <div className="lg:hidden"><Logo small /></div>
          <div className="hidden lg:block text-xs font-semibold text-mut">✨ Couple Taste Intelligence OS</div>
          <div className="flex items-center gap-2">
            
            <NavLink to="/app/notifications" className="relative rounded-full p-2 hover:bg-blush" aria-label="Notifications">
              <Bell className="h-5 w-5 text-brand" />
              {me?.unread > 0 && <span className="absolute -right-0.5 -top-0.5 grid h-5 min-w-[20px] place-items-center rounded-full bg-brand px-1 text-[10px] text-white">{me.unread}</span>}
            </NavLink>
            <NavLink to="/app/me" className="flex items-center gap-2 rounded-full border border-line bg-white py-1 pl-1 pr-3 text-sm">
              {me?.user?.photo ? <img src={me.user.photo} alt="" className="h-7 w-7 rounded-full object-cover" /> : <span className="grid h-7 w-7 place-items-center rounded-full bg-blush text-brand">{(me?.user?.name || "?")[0]}</span>}
              <span className="hidden sm:inline">{me?.user?.name?.split(" ")[0]}{me?.partner && ` & ${me.partner.name.split(" ")[0]}`}</span>
            </NavLink>
          </div>
        </header>
        <div className={clsx(onChat ? "" : "mx-auto max-w-5xl p-4 lg:p-6")}><Outlet /></div>
      </main>

      {!onChat && (
        <section className="sticky top-0 hidden h-screen w-[340px] shrink-0 border-l border-line bg-white xl:block"><ChatPanel docked /></section>
      )}

      {!onChat && voice === "off" && (
        <NavLink to="/app/chat" className="fixed bottom-20 right-4 z-30 flex items-center gap-2 rounded-full bg-brand py-1.5 pl-1.5 pr-4 text-sm text-white shadow-soft lg:bottom-6 xl:hidden" aria-label="Talk to WeaveTwo">
          <Avatar size={34} /> Talk to WeaveTwo
        </NavLink>
      )}

      <nav className="fixed inset-x-0 bottom-0 z-30 flex justify-around border-t border-line bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden">
        {NAV.filter((n) => n.to !== "/app/recommends" && n.to !== "/app/dna").map((n) => (
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
