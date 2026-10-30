import { AudioLines, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { api } from "../lib/api";
import { Avatar } from "../components/ui";
import { useChat } from "./ChatContext";
import { Widget } from "./Widgets";

const QUICK: Record<string, string[]> = {
  guide: ["What can you do? ✨", "We're getting married 💍", "Plan our honeymoon 🌴", "We're planning a trip ✈️"],
  setup: ["Let's fill in the details", "Ask me about my music 🎶", "Invite my partner 💌"],
  planner: ["Build our plan ✨", "What would my partner love?", "Show our Couple DNA", "Plan a surprise 🤫"],
};

export default function ChatPanel({ docked = false }: { docked?: boolean }) {
  const { messages, busy, status, voice, send, startVoice, setOverlay, loaded } = useChat();
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me") });
  const [text, setText] = useState("");
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, status]);
  const first = me?.user?.name?.split(" ")[0] || "there";
  const submit = (e?: any) => { e?.preventDefault(); if (!text.trim()) return; send(text); setText(""); };
  const last = messages[messages.length - 1];
  const thinking = busy && !(last?.streaming);

  return (
    <div className={clsx("flex flex-col bg-white", docked ? "h-screen" : "h-[calc(100dvh-8.6rem)] lg:h-[calc(100dvh-3.9rem)]")}>
      <div className="flex items-center gap-3 border-b border-line px-4 py-3">
        <Avatar size={42} ring={voice !== "off"} />
        <div className="min-w-0 flex-1">
          <div className="h-serif text-lg leading-tight text-brand">cupl</div>
          <div className="text-xs text-green-700">● {voice === "off" ? "Online · your planner" : voice === "speaking" ? "Speaking…" : voice === "connecting" ? "Connecting…" : "Listening…"}</div>
        </div>
        {me?.active_space && <span className="badge max-w-[45%] truncate">{me.active_space.title}</span>}
      </div>

      <div className="scroll-thin flex-1 space-y-3 overflow-y-auto bg-gradient-to-b from-white to-cream/60 p-4">
        {loaded && messages.length === 0 && (
          <div className="rise flex gap-2">
            <Avatar size={30} />
            <div className="rounded-2xl rounded-tl-sm border border-line bg-white p-3.5 text-sm shadow-sm">
              <div className="h-serif text-lg text-brand">Hi {first}! 👋</div>
              I'm cupl — your AI concierge for life together for every chapter of your love story. Tell me what you're celebrating, or tap <b>Talk</b> and just speak to me.
            </div>
          </div>
        )}
        {messages.map((m, i) => {
          const showAv = m.role === "agent" && (i === 0 || messages[i - 1].role !== "agent");
          if (m.widget) return (
            <div key={m.id} className="rise flex gap-2"><div className="w-[30px] shrink-0" /><div className="min-w-0 flex-1"><Widget w={m.widget} /></div></div>
          );
          if (!m.text) return null;
          return m.role === "user" ? (
            <div key={m.id} className="rise ml-auto max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-brand px-3.5 py-2.5 text-sm text-white">
              {m.voice && <span className="mr-1 opacity-70">🎙</span>}{m.text.startsWith("[") ? m.text.replace(/^\[[^\]]*\]\s*/, "") : m.text}
            </div>
          ) : (
            <div key={m.id} className="rise flex items-end gap-2">
              {showAv ? <Avatar size={30} /> : <div className="w-[30px] shrink-0" />}
              <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tl-sm border border-line bg-white px-3.5 py-2.5 text-sm leading-relaxed shadow-sm">
                {m.voice && <span className="mr-1 opacity-60">🎙</span>}{m.text}{m.streaming && <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-brand/60 align-middle" />}
              </div>
            </div>
          );
        })}
        {(thinking || status) && (
          <div className="flex items-center gap-2 pl-10 text-xs text-mut">
            <span className="flex gap-1"><i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand" /><i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand [animation-delay:.15s]" /><i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand [animation-delay:.3s]" /></span>
            {status || "Thinking…"}
          </div>
        )}
        <div ref={end} />
      </div>

      {!busy && messages.length < 6 && (
        <div className="scroll-thin flex gap-2 overflow-x-auto px-4 pb-2 pt-1">
          {(QUICK[me?.mode] || QUICK.guide).map((q) => <button type="button" key={q} onClick={() => send(q)} className="chip shrink-0 bg-cream">{q}</button>)}
        </div>
      )}

      <form onSubmit={submit} className="flex items-center gap-2 border-t border-line p-3">
        <input value={text} onChange={(e) => setText(e.target.value)} className="input flex-1 rounded-full"
          placeholder={voice !== "off" ? "Talk, or type here…" : "Message cupl…"} aria-label="Message" />
        {text.trim() ? (
          <button type="submit" disabled={busy && voice === "off"} className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-brand text-white" aria-label="Send"><Send className="h-5 w-5" /></button>
        ) : (
          <button type="button" onClick={() => (voice === "off" ? startVoice() : setOverlay(true))}
            className="flex h-11 shrink-0 items-center gap-1.5 rounded-full bg-brand px-4 text-sm font-medium text-white" aria-label="Talk to cupl">
            <AudioLines className="h-5 w-5" /> {voice === "off" ? "Talk" : "Live"}
          </button>
        )}
      </form>
    </div>
  );
}
