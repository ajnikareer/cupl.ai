import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { AudioLines, Plus } from "lucide-react";
import { api, daysTo, fmtDate, IMG } from "../lib/api";
import { Avatar, Empty, STATE_LABEL, Spinner } from "../components/ui";
import { useChat } from "../chat/ChatContext";

export default function Home() {
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me") });
  const { data: sp, isLoading } = useQuery({ queryKey: ["spaces"], queryFn: () => api("/api/spaces") });
  const { startVoice } = useChat();
  const h = new Date().getHours();
  const greet = h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
  const first = me?.user?.name?.split(" ")[0] || "";
  return (
    <div className="space-y-6">
      <div className="relative overflow-hidden rounded-2xl">
        <img src="/img/hero.jpg" alt="" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#fff5f2] via-[#fff5f2]/90 to-transparent" />
        <div className="relative max-w-lg p-5 md:p-7">
          <div className="h-serif text-2xl text-ink md:text-3xl">{greet}{first && `, ${first}`} ☀️</div>
          <p className="mt-1 text-mut">Let's make beautiful things happen today.</p>
          <div className="mt-4 flex flex-wrap gap-2">

            <Link to="/app/spaces/new" className="btn-primary px-4 py-2 text-sm"><Plus className="h-4 w-4" /> Create Event Space</Link>
          </div>
        </div>
      </div>

      {me?.next?.goal && (
        <Link to="/app/chat" className="card flex items-center gap-3 p-4 transition hover:-translate-y-0.5">
          <Avatar size={44} />
          <div className="flex-1 text-sm"><div className="font-medium text-brand">cupl suggests</div><div className="text-mut">{hint(me)}</div></div>
          <span className="btn-ghost">Continue</span>
        </Link>
      )}

      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="h-serif text-2xl text-brand">Your Event Spaces</h2>
          <Link to="/app/spaces" className="text-sm text-brand">See all</Link>
        </div>
        {isLoading ? <Spinner /> : sp?.spaces?.length ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {sp.spaces.slice(0, 5).map((s: any) => <SpaceCard key={s.id} s={s} active={s.id === sp.active_space_id} />)}
            <Link to="/app/spaces/new" className="card grid min-h-[220px] place-items-center border-dashed text-brand"><span className="flex flex-col items-center gap-2"><Plus /> Create New Event Space</span></Link>
          </div>
        ) : (
          <Empty image="/img/wedding.jpg" title="No event spaces yet" text="Create one for your prewedding, engagement, wedding, honeymoon, a trip or any celebration — or just tell cupl what you're planning."
            action={<Link to="/app/spaces/new" className="btn-primary mt-2">Create Event Space</Link>} />
        )}
      </div>
    </div>
  );
}

function hint(me: any) {
  const st = me.next?.stage;
  const t = me.active_space?.title;
  return ({ welcome: "Say hi — tell me what you're celebrating 💕", rapport: "Tell me a little about you two", guide: "What are we planning next?",
    event_basics: `A few details for ${t} and we're off`, know_tastes: "Let me get to know your taste a little more", invite_partner: "Invite your partner to plan together",
    ready_to_plan: `Ready to weave your ${t} plan ✨`, building: `Your ${t} plan is being woven…`, refine: `Let's refine your ${t} plan`, refresh: "Your details changed — let's refresh the plan" } as any)[st] || "Continue our conversation";
}

export function SpaceCard({ s, active }: { s: any; active?: boolean }) {
  const d = daysTo(s.start_date);
  return (
    <Link to={`/app/spaces/${s.id}`} className="card group block overflow-hidden transition hover:-translate-y-0.5">
      <div className="relative h-36 overflow-hidden">
        <img src={IMG[s.type]} alt="" className="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
        {active && <span className="badge absolute right-3 top-3 bg-white/90">Active</span>}
        {d !== null && d >= 0 && <span className="absolute bottom-3 left-3 rounded-full bg-white/90 px-2.5 py-0.5 text-xs font-medium text-brand">{d} days to go</span>}
      </div>
      <div className="p-4">
        <div className="h-serif text-xl text-brand">{s.title}</div>
        <div className="text-sm text-mut">{[s.city || s.destination, fmtDate(s.start_date)].filter(Boolean).join(" · ") || "Details pending"}</div>
        <span className="badge mt-3">{STATE_LABEL[s.state] || s.state}</span>
      </div>
    </Link>
  );
}
