import { useEffect, useRef } from "react";
import { Heart, MessageSquareText, PhoneOff, Users } from "lucide-react";
import clsx from "clsx";
import { useChat } from "./ChatContext";
import { Widget } from "./Widgets";

const LABEL: Record<string, string> = { connecting: "Connecting…", listening: "I'm listening…", speaking: "", reconnecting: "Reconnecting…" };

export default function VoiceOverlay() {
  const { overlay, voice, messages, stopVoice, setOverlay, level, coupleMode, toggleCoupleMode } = useChat();
  const canvas = useRef<HTMLCanvasElement>(null);
  const ring = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!overlay) return;
    let raf = 0;
    const bars = 32;
    const hist = new Array(bars).fill(0);
    const draw = () => {
      const c = canvas.current;
      const lvl = Math.max(level("in"), level("out"));
      hist.push(lvl); hist.shift();
      if (ring.current) ring.current.style.transform = `scale(${1 + level("out") * 0.25})`;
      if (c) {
        const g = c.getContext("2d")!;
        const w = (c.width = c.clientWidth * devicePixelRatio), h = (c.height = c.clientHeight * devicePixelRatio);
        g.clearRect(0, 0, w, h);
        const bw = w / bars;
        hist.forEach((v, i) => {
          const bh = Math.max(h * 0.06, v * h * 0.9);
          g.fillStyle = i % 2 ? "#c9973a" : "#8e2c48";
          g.globalAlpha = 0.35 + 0.65 * (i / bars);
          const x = i * bw + bw * 0.25, y = (h - bh) / 2;
          g.beginPath(); (g as any).roundRect ? (g as any).roundRect(x, y, bw * 0.5, bh, bw * 0.25) : g.rect(x, y, bw * 0.5, bh); g.fill();
        });
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [overlay, level]);

  if (!overlay) return null;
  const lastAgent = [...messages].reverse().find((m) => m.role === "agent" && m.text && !m.widget);
  const lastUser = [...messages].reverse().find((m) => m.role === "user" && m.voice);
  const widgetMsg = [...messages].reverse().find((m) => m.widget && !m.widget.done && ["taste_picker", "choices", "confirm", "disambiguation", "space_form", "invite", "plan_proposal"].includes(m.widget.kind));

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-gradient-to-b from-[#fff5f2] via-blush to-[#ecc9d3]" role="dialog" aria-label="Voice conversation">
      {/* Top Header */}
      <div className="flex items-center justify-between p-4">
        <div className="h-serif text-xl text-brand">WeaveTwo</div>
        <button type="button" onClick={() => setOverlay(false)} className="btn-ghost" aria-label="Show chat">
          <MessageSquareText className="h-4 w-4" /> Chat
        </button>
      </div>

      {/* Main Avatar & Visualizer Body */}
      <div className="flex flex-1 flex-col items-center justify-center gap-6 overflow-y-auto px-5 pb-6">
        <div className="relative">
          <div ref={ring} className="absolute -inset-4 rounded-full bg-brand/10 transition-transform duration-75" />
          {voice === "listening" && <span className="ring-pulse absolute -inset-2 rounded-full border-2 border-brand/50" />}
          <img src="/img/avatar.jpg" alt="WeaveTwo" className="relative h-40 w-40 rounded-full border-4 border-white object-cover shadow-soft md:h-48 md:w-48" />
        </div>

        <div className="flex flex-col items-center gap-2">
          <div className="h-serif text-lg text-brand">{LABEL[voice] ?? ""}</div>
          {coupleMode && (
            <div className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 border border-rose-200/90 px-3.5 py-1 text-xs font-semibold text-rose-800 shadow-3xs animate-fade-in">
              <Heart className="h-3.5 w-3.5 text-rose-500 fill-rose-500" />
              <span>Sitting Together Mode • Speaking with both of you</span>
            </div>
          )}
        </div>

        <canvas ref={canvas} className="h-14 w-64" aria-hidden />

        <div className="min-h-[72px] max-w-xl text-center">
          {lastAgent && <p className="text-lg leading-relaxed text-ink">{lastAgent.text.slice(-240)}</p>}
          {lastUser && <p className="mt-2 text-sm italic text-mut">You: {lastUser.text.slice(-140)}</p>}
        </div>

        {widgetMsg && <div className="w-full max-w-lg"><Widget w={widgetMsg.widget} /></div>}
      </div>

      {/* Bottom Controls: Couple Mode Toggle + End Call Button */}
      <div className="flex items-center justify-center gap-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
        <button
          type="button"
          onClick={toggleCoupleMode}
          className={clsx(
            "flex h-16 items-center gap-2 rounded-full px-6 text-sm font-semibold border transition shadow-soft",
            coupleMode
              ? "bg-rose-500 text-white border-rose-600 shadow-rose-200"
              : "bg-white text-ink border-line hover:border-brand/40 hover:text-brand"
          )}
          title="Toggle Couple Mode (Sitting Together)"
        >
          <Users className="h-5 w-5" />
          <span>{coupleMode ? "💑 Couple Mode: ON" : "Couple Mode"}</span>
        </button>

        <button
          type="button"
          onClick={stopVoice}
          className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500 text-white shadow-soft hover:bg-red-600 transition"
          aria-label="End voice"
        >
          <PhoneOff className="h-7 w-7" />
        </button>
      </div>
    </div>
  );
}
