import { Link } from "react-router-dom";
import { AudioLines, Brain, Heart, Lightbulb, Lock, Sparkles } from "lucide-react";
import { Avatar, Logo } from "../components/ui";
import { useAuth } from "../auth/AuthProvider";
import { IMG } from "../lib/api";

const PHASES = [["prewedding", "Prewedding", "Shoots, proposals, couple experiences"], ["engagement", "Engagement", "Ceremony, décor, music"],
  ["wedding", "Wedding", "Every ceremony, planned"], ["honeymoon", "Honeymoon", "Destinations & itineraries"],
  ["trip", "Trips", "Any trip, any time"], ["life_beyond", "Life Beyond", "Anniversaries & milestones"]];
const FEATURES = [
  [AudioLines, "Talk, don't fill forms", "A warm voice & chat planner that asks, suggests, listens — and plans."],
  [Heart, "Built for two", "Each partner shares their own taste. Every plan is woven from both."],
  [Sparkles, "Couple Taste DNA", "What you both love, your unique flavours, and middle-ground ideas."],
  [Lightbulb, "“Why this?”", "Every recommendation explains which of your tastes it came from."],
  [Brain, "Remembers & learns", "Every chat, choice and trip makes the next plan more you."],
  [Lock, "Surprise mode", "Plan surprises your partner will love — completely private."],
];

export default function Landing() {
  const { user } = useAuth();
  const go = user ? "/app" : "/login";
  return (
    <div className="min-h-screen bg-cream">
      <section className="relative overflow-hidden">
        <img src="/img/hero.jpg" alt="" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#fff5f2] via-[#fff5f2]/85 to-transparent" />
        <div className="relative mx-auto max-w-6xl px-5">
          <header className="flex items-center justify-between py-5">
            <Logo />
            <Link to={go} className="btn-primary">{user ? "Open app" : "Get started"}</Link>
          </header>
          <div className="max-w-xl py-14 md:py-24">
            <h1 className="h-serif text-4xl leading-tight text-ink md:text-6xl">Your AI wedding companion for every chapter of love</h1>
            <p className="mt-4 text-lg text-ink/80">Plan. Personalize. Celebrate. Together — powered by QLOO taste intelligence.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to={go} className="btn-primary px-6 py-3 text-base"><AudioLines className="h-5 w-5" /> Start planning with AI</Link>
            </div>
            <p className="h-script mt-6 text-3xl text-brand">Different moments, one beautiful journey ♡</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-14">
        <h2 className="h-serif text-center text-3xl text-brand">Life's most beautiful moments, in one place</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {PHASES.map(([k, t, d]) => (
            <div key={k} className="card group overflow-hidden">
              <img src={IMG[k]} alt="" className="h-44 w-full object-cover transition duration-500 group-hover:scale-105" />
              <div className="p-4"><div className="h-serif text-xl text-brand">{t}</div><div className="text-sm text-mut">{d}</div></div>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white py-14">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 md:grid-cols-2">
          <div className="card p-5">
            <div className="flex items-center gap-3 border-b border-line pb-3"><Avatar size={44} /><div><div className="h-serif text-lg text-brand">WeaveWed</div><div className="text-xs text-green-700">● Online</div></div></div>
            <div className="space-y-3 pt-4 text-sm">
              <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-line bg-cream p-3">Udaipur in February? Dreamy 💕 Who could you two listen to all day?</div>
              <div className="flex flex-wrap gap-1.5"><span className="chip chip-on">💞 A.R. Rahman</span><span className="chip">Shreya Ghoshal</span><span className="chip chip-on">Arijit Singh</span><span className="chip border-dashed">+ Add your own</span></div>
              <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-sm bg-brand p-3 text-white">A.R. Rahman and Arijit Singh</div>
              <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-line bg-cream p-3">You and Karan both love A.R. Rahman 💞 — that's going straight into your Sangeet!</div>
            </div>
            <p className="mt-3 text-center text-[11px] text-mut">Illustration of the experience</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {FEATURES.map(([I, t, d]: any) => (
              <div key={t} className="rounded-3xl bg-cream p-4"><I className="h-6 w-6 text-brand" /><div className="mt-2 font-medium">{t}</div><p className="mt-1 text-sm text-mut">{d}</p></div>
            ))}
          </div>
        </div>
      </section>
      <footer className="py-10 text-center"><Logo small /><p className="h-script mt-2 text-2xl text-brand">More than planning — it understands what love means to you.</p></footer>
    </div>
  );
}
