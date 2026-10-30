import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AudioLines,
  Heart,
  MessageSquare,
  PhoneOff,
  Play,
  Plus,
  Send,
  Sparkles,
  Trash2,
  Users,
} from "lucide-react";
import clsx from "clsx";
import { api } from "../lib/api";
import { Avatar } from "../components/ui";
import { useChat, Msg } from "../chat/ChatContext";
import { Widget } from "../chat/Widgets";

interface ChatThread {
  id: string;
  title: string;
  timestamp: number;
  messages: Msg[];
}

const DEFAULT_THREADS: ChatThread[] = [];

const QUICK_PROMPTS = [
  "Plan a surprise date 🤫",
  "Suggest a movie for tonight 🎬",
  "Compare our taste DNA 🧬",
  "Plan our celebration ✨",
];

const VOICE_LABEL: Record<string, string> = {
  connecting: "Connecting…",
  listening: "Listening to both of you…",
  speaking: "Speaking…",
  reconnecting: "Reconnecting…",
  off: "Voice ready",
};

export default function ChatPage() {
  const {
    messages,
    setMessages,
    busy,
    status,
    voice,
    send,
    startVoice,
    stopVoice,
    level,
    coupleMode,
    toggleCoupleMode,
    loaded,
  } = useChat();

  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me") });

  const [threads, setThreads] = useState<ChatThread[]>(() => []);

  const [activeThreadId, setActiveThreadId] = useState<string>("current");
  const [showContinuity, setShowContinuity] = useState(false);
  const [text, setText] = useState("");

  const end = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const ring = useRef<HTMLDivElement>(null);

  // Synchronize backend initial messages into active thread on first load
  useEffect(() => {
    if (loaded && messages.length > 0) {
      setThreads((prev) => {
        const found = prev.find((t) => t.id === "thread_bali");
        if (found && (!found.messages || found.messages.length === 0)) {
          const updated = prev.map((t) => (t.id === "thread_bali" ? { ...t, messages } : t));
          try {
            localStorage.setItem("ww_chat_history", JSON.stringify(updated));
          } catch {}
          return updated;
        }
        return prev;
      });
    }
  }, [loaded, messages]);

  // Synchronize current messages into activeThread's messages in threads array
  useEffect(() => {
    if (!messages || messages.length === 0) return;
    setThreads((prev) => {
      const updated = prev.map((t) => {
        if (t.id === activeThreadId) {
          return {
            ...t,
            messages,
            title:
              t.title === "New chat"
                ? messages.find((m) => m.role === "user")?.text?.slice(0, 36) || "New chat"
                : t.title,
          };
        }
        return t;
      });
      try {
        localStorage.setItem("ww_chat_history", JSON.stringify(updated));
      } catch {}
      return updated;
    });
  }, [messages, activeThreadId]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, status]);

  // Audio frequency dynamic canvas visualizer
  useEffect(() => {
    let raf = 0;
    const bars = 32;
    const hist = new Array(bars).fill(0);
    const draw = () => {
      const c = canvas.current;
      const lvl = Math.max(level("in"), level("out"));
      hist.push(lvl);
      hist.shift();
      if (ring.current) {
        ring.current.style.transform = `scale(${1 + level("out") * 0.28})`;
      }
      if (c) {
        const g = c.getContext("2d")!;
        const w = (c.width = c.clientWidth * devicePixelRatio);
        const h = (c.height = c.clientHeight * devicePixelRatio);
        g.clearRect(0, 0, w, h);
        const bw = w / bars;
        hist.forEach((v, i) => {
          const bh = Math.max(h * 0.08, v * h * 0.95);
          g.fillStyle = i % 2 ? "#c9973a" : "#8e2c48";
          g.globalAlpha = 0.35 + 0.65 * (i / bars);
          const x = i * bw + bw * 0.25;
          const y = (h - bh) / 2;
          g.beginPath();
          if ((g as any).roundRect) {
            (g as any).roundRect(x, y, bw * 0.5, bh, bw * 0.25);
          } else {
            g.rect(x, y, bw * 0.5, bh);
          }
          g.fill();
        });
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [level, voice]);

  const first = me?.user?.name?.split(" ")[0] || "there";

  // Create a brand new chat session
  const handleStartNewChat = () => {
    const newId = `thread_${Date.now()}`;
    const newThread: ChatThread = {
      id: newId,
      title: "New chat",
      timestamp: Date.now(),
      messages: [],
    };
    const updated = [newThread, ...threads];
    setThreads(updated);
    try {
      localStorage.setItem("ww_chat_history", JSON.stringify(updated));
    } catch {}
    setActiveThreadId(newId);
    setMessages([]);
    setShowContinuity(false);
  };

  // Switch to an existing chat in history
  const handleSelectThread = (t: ChatThread) => {
    // 1. Save current active messages into the current active thread
    const updated = threads.map((item) =>
      item.id === activeThreadId ? { ...item, messages } : item
    );
    setThreads(updated);
    try {
      localStorage.setItem("ww_chat_history", JSON.stringify(updated));
    } catch {}

    // 2. Switch active thread and load its messages
    setActiveThreadId(t.id);
    const targetThread = updated.find((item) => item.id === t.id) || t;
    setMessages(targetThread.messages || []);
    setShowContinuity(false);
  };

  // Delete a chat from history
  const handleDeleteThread = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const remaining = threads.filter((t) => t.id !== id);
    setThreads(remaining);
    try {
      localStorage.setItem("ww_chat_history", JSON.stringify(remaining));
    } catch {}
    if (activeThreadId === id) {
      if (remaining.length > 0) {
        handleSelectThread(remaining[0]);
      } else {
        handleStartNewChat();
      }
    }
  };

  // Submit a message
  const submit = (e?: any) => {
    e?.preventDefault();
    const val = text.trim();
    if (!val) return;

    // If active thread is titled "New chat", update title with first prompt
    const curr = threads.find((t) => t.id === activeThreadId);
    if (curr && curr.title === "New chat") {
      const generatedTitle = val.length > 36 ? val.slice(0, 36) + "…" : val;
      setThreads((prev) =>
        prev.map((t) => (t.id === activeThreadId ? { ...t, title: generatedTitle } : t))
      );
    }

    send(val);
    setText("");
  };

  // Find active widgets in messages
  const lastAgent = [...messages].reverse().find((m) => m.role === "agent" && m.text && !m.widget);
  const lastUser = [...messages].reverse().find((m) => m.role === "user" && m.voice);
  const activeWidget = [...messages]
    .reverse()
    .find(
      (m) =>
        m.widget &&
        ["plan_proposal", "space_form", "taste_picker", "choices", "confirm"].includes(m.widget.kind)
    );

  const activeThread =
    threads.find((t) => t.id === activeThreadId) || threads[0] || { id: "default", title: "Chat" };
  const last = messages[messages.length - 1];
  const thinking = busy && !last?.streaming;

  // Group threads into Today, Yesterday, Previous 7 Days, Earlier
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;
  const groups: { label: string; items: ChatThread[] }[] = [
    {
      label: "Today",
      items: threads.filter((t) => now - t.timestamp < oneDay),
    },
    {
      label: "Yesterday",
      items: threads.filter((t) => now - t.timestamp >= oneDay && now - t.timestamp < 2 * oneDay),
    },
    {
      label: "Previous 7 Days",
      items: threads.filter((t) => now - t.timestamp >= 2 * oneDay && now - t.timestamp < 7 * oneDay),
    },
    {
      label: "Earlier",
      items: threads.filter((t) => now - t.timestamp >= 7 * oneDay),
    },
  ].filter((g) => g.items.length > 0);

  return (
    <div className="flex h-full w-full overflow-hidden bg-cream/40">
      {/* ========================================================= */}
      {/* 1. FIXED 15% CHAT HISTORY DRAWER                          */}
      {/* ========================================================= */}
      <aside
        className="w-[15%] min-w-[210px] max-w-[250px] shrink-0 border-r border-line bg-white flex flex-col h-full z-10 select-none"
        aria-label="Chat history"
      >
        {/* Top Header: Chat History Title */}
        <div className="border-b border-line px-3.5 py-3.5">
          <div className="text-xs font-bold uppercase tracking-wider text-brand">
            Chat History
          </div>
        </div>

        {/* Standard Chat History List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-4 scroll-thin">
          {groups.map((group) => (
            <div key={group.label} className="space-y-1">
              <div className="px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider text-mut">
                {group.label}
              </div>
              {group.items.map((thread) => {
                const isActive = thread.id === activeThreadId;
                return (
                  <div
                    key={thread.id}
                    onClick={() => handleSelectThread(thread)}
                    className={clsx(
                      "group relative flex items-center justify-between gap-1.5 rounded-xl px-2.5 py-2 text-xs cursor-pointer transition",
                      isActive
                        ? "bg-blush font-semibold text-brand shadow-3xs"
                        : "text-ink hover:bg-cream/80"
                    )}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <MessageSquare
                        className={clsx(
                          "h-3.5 w-3.5 shrink-0",
                          isActive ? "text-brand" : "text-mut"
                        )}
                      />
                      <span className="truncate">{thread.title}</span>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteThread(e, thread.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-mut hover:text-red-500 rounded transition"
                      title="Delete chat"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          ))}
        </div>

        {/* Bottom Action: New Chat Button (Styled like Couple Mode Button in White) */}
        <div className="border-t border-line p-3 bg-white">
          <button
            type="button"
            onClick={handleStartNewChat}
            className="flex h-12 w-full items-center justify-center gap-2 rounded-full px-5 text-xs font-semibold bg-white text-ink border border-line shadow-soft hover:border-brand/40 hover:text-brand transition"
            title="Start a new chat"
          >
            <Plus className="h-4 w-4" />
            <span>New chat</span>
          </button>
        </div>
      </aside>

      {/* ========================================================= */}
      {/* 2. CHAT & LIVE TRANSCRIPT COLUMN (~42.5%)                 */}
      {/* ========================================================= */}
      <section className="flex flex-1 min-w-[320px] flex-col border-r border-line bg-white h-full overflow-hidden">
        {/* Chat Header Bar */}
        <div className="flex items-center justify-between border-b border-line px-4 py-3 bg-white">
          <div className="flex items-center gap-2.5 min-w-0">
            <Avatar size={32} ring={voice !== "off"} />
            <div className="min-w-0">
              <div className="text-sm font-bold text-ink truncate">
                {activeThread.title}
              </div>
              <div className="text-[11px] text-green-700 font-medium">
                ● {voice !== "off" ? "Live Voice Connected" : "Online · AI Assistant"}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {coupleMode && (
              <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 border border-rose-200 px-2.5 py-0.5 text-[11px] font-semibold text-rose-800">
                <Heart className="h-3 w-3 fill-rose-500 text-rose-500" /> Couple Mode
              </span>
            )}
            {voice !== "off" && (
              <span className="inline-flex items-center gap-1 rounded-full bg-green-50 border border-green-200 px-2.5 py-0.5 text-[11px] font-semibold text-green-700 animate-pulse">
                🎙️ On Call
              </span>
            )}
          </div>
        </div>

        {/* Scrollable Message Transcript Feed */}
        <div className="scroll-thin flex-1 space-y-3 overflow-y-auto bg-gradient-to-b from-white to-cream/40 p-4">
          {/* Conversational Memory Continuity Card */}
          {showContinuity && (
            <div className="rise rounded-2xl border border-brand/20 bg-gradient-to-r from-rose-50/90 via-blush/60 to-cream p-4 shadow-sm relative">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-brand">
                  <Sparkles className="h-3.5 w-3.5 text-rose-500 animate-pulse" />
                  <span>Where we left off</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowContinuity(false)}
                  className="text-xs text-mut hover:text-ink px-1.5 py-0.5 rounded"
                  title="Dismiss greeting"
                >
                  ✕
                </button>
              </div>
              <p className="mt-1.5 text-sm font-medium text-ink leading-relaxed">
                Welcome back, <b>{first}</b>! Last time we were planning your{" "}
                <b>Bali Romantic Honeymoon Escape (Nov 15–22)</b> — Ubud bamboo villas & sunset seafood.
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    send("Let's continue refining our Bali honeymoon plan! What should we lock in next?");
                    setShowContinuity(false);
                  }}
                  className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1.5 shadow-3xs"
                >
                  <Play className="h-3.5 w-3.5 fill-white" /> Continue Bali Plan
                </button>
                <button
                  type="button"
                  onClick={() => {
                    handleStartNewChat();
                    setShowContinuity(false);
                  }}
                  className="btn-ghost text-xs py-1.5 px-3.5 bg-white/90 border border-line hover:border-brand/40 shadow-3xs"
                >
                  ✨ Plan Something New
                </button>
              </div>
            </div>
          )}

          {/* Initial Greeting if chat is empty */}
          {messages.length === 0 && (
            <div className="rise flex gap-3">
              <Avatar size={34} />
              <div className="rounded-2xl rounded-tl-sm border border-line bg-white p-4 text-sm shadow-sm text-ink leading-relaxed max-w-lg">
                <div className="h-serif text-base text-brand font-bold mb-1">Hello {first}! Welcome to cupl AI 💕</div>
                <p className="text-mut text-xs leading-relaxed mb-2.5">
                  I am your AI concierge for life together, powered by Qloo Cultural Taste Intelligence. I can assist you with milestone <b>Events</b>, everyday <b>Plans</b>, and weekly <b>Recommendations</b>.
                </p>
                <p className="text-ink text-xs font-medium">
                  Would you like a quick tour of how I can assist you, or is there an upcoming celebration on your mind?
                </p>
              </div>
            </div>
          )}

          {/* Live Message Log & Transcripts */}
          {messages.map((m, i) => {
            const showAv = m.role === "agent" && (i === 0 || messages[i - 1].role !== "agent");
            if (m.widget) {
              return (
                <div key={m.id} className="rise flex gap-2">
                  <div className="w-[30px] shrink-0" />
                  <div className="min-w-0 flex-1">
                    <Widget w={m.widget} />
                  </div>
                </div>
              );
            }
            if (!m.text) return null;
            return m.role === "user" ? (
              <div
                key={m.id}
                className="rise ml-auto max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-brand px-3.5 py-2.5 text-sm text-white shadow-3xs"
              >
                {m.voice && (
                  <span className="mr-1.5 inline-flex items-center text-[10px] bg-white/20 px-1.5 py-0.5 rounded-full font-semibold">
                    🎙️ Voice
                  </span>
                )}
                {m.text.startsWith("[") ? m.text.replace(/^\[[^\]]*\]\s*/, "") : m.text}
              </div>
            ) : (
              <div key={m.id} className="rise flex items-end gap-2">
                {showAv ? <Avatar size={30} /> : <div className="w-[30px] shrink-0" />}
                <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tl-sm border border-line bg-white px-3.5 py-2.5 text-sm leading-relaxed shadow-sm text-ink">
                  {m.voice && (
                    <span className="mr-1.5 inline-flex items-center text-[10px] bg-rose-50 text-brand px-1.5 py-0.5 rounded-full font-semibold border border-rose-200">
                      🎙️ Live Voice
                    </span>
                  )}
                  {m.text}
                  {m.streaming && (
                    <span className="ml-1 inline-block h-3.5 w-1.5 animate-pulse bg-brand/60 align-middle" />
                  )}
                </div>
              </div>
            );
          })}

          {/* Thinking status */}
          {(thinking || status) && (
            <div className="flex items-center gap-2 pl-9 text-xs text-mut">
              <span className="flex gap-1">
                <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand" />
                <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand [animation-delay:.15s]" />
                <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand [animation-delay:.3s]" />
              </span>
              <span>{status || "Thinking…"}</span>
            </div>
          )}
          <div ref={end} />
        </div>

        {/* Quick Prompts Bar */}
        {!busy && (
          <div className="scroll-thin flex gap-1.5 overflow-x-auto px-4 py-1.5 border-t border-line/60 bg-cream/30">
            {QUICK_PROMPTS.map((q) => (
              <button
                type="button"
                key={q}
                onClick={() => send(q)}
                className="chip shrink-0 bg-white hover:bg-blush text-xs py-1"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Bottom Standard Input Bar (Clean Send button only) */}
        <form onSubmit={submit} className="flex items-center gap-2 border-t border-line p-3 bg-white">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="input flex-1 rounded-full text-sm"
            placeholder="Type a message…"
            aria-label="Message"
          />
          <button
            type="submit"
            disabled={!text.trim() || (busy && voice === "off")}
            className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-brand text-white shadow-soft disabled:opacity-40 hover:bg-brand/90 transition"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </section>

      {/* ========================================================= */}
      {/* 3. CLEAN LIVE TALK & COMPANION STAGE (~42.5%)             */}
      {/* ========================================================= */}
      <section className="hidden md:flex flex-1 min-w-[340px] flex-col bg-gradient-to-b from-[#fff8f6] via-blush/35 to-[#fcecee] h-full overflow-y-auto px-5 py-6 justify-between relative">
        {/* Stage Header */}
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand">
              AI Companion Stage
            </span>
            <span className="text-xs text-mut">
              • {VOICE_LABEL[voice] || "Ready"}
            </span>
          </div>
          {coupleMode && (
            <div className="inline-flex items-center gap-1 rounded-full bg-rose-50 border border-rose-200 px-2.5 py-0.5 text-xs font-semibold text-rose-800 shadow-3xs animate-fade-in">
              <Heart className="h-3 w-3 fill-rose-500 text-rose-500" />
              <span>Sitting Together Mode</span>
            </div>
          )}
        </div>

        {/* Center Companion Avatar + Audio Visualizer (Clean, No Continuous Static Card) */}
        <div className="flex flex-col items-center justify-center gap-6 my-auto py-4">
          {/* Avatar with Reactive Pulsing Glow */}
          <div className="relative">
            <div
              ref={ring}
              className={clsx(
                "absolute -inset-4 rounded-full transition-transform duration-75",
                voice !== "off" ? "bg-brand/15 ring-pulse" : "bg-brand/5"
              )}
            />
            {voice === "listening" && (
              <span className="ring-pulse absolute -inset-2 rounded-full border-2 border-brand/50" />
            )}
            <img
              src="/img/avatar.png"
              alt="cupl AI Concierge"
              className={clsx(
                "relative h-36 w-36 xl:h-44 xl:w-44 rounded-full border-4 border-white object-cover shadow-soft transition-all duration-300",
                voice !== "off" ? "scale-105" : "grayscale-[10%]"
              )}
            />
          </div>

          {/* Subtitles & Live Dialogue Preview */}
          <div className="min-h-[56px] max-w-md text-center px-4">
            {lastAgent && (
              <p className="text-sm font-medium leading-relaxed text-ink line-clamp-3">
                "{lastAgent.text.slice(-200)}"
              </p>
            )}
            {lastUser && (
              <p className="mt-1.5 text-xs italic text-mut truncate">
                You: {lastUser.text.slice(-100)}
              </p>
            )}
            {!lastAgent && !lastUser && (
              <p className="text-xs text-mut leading-relaxed max-w-xs mx-auto">
                {voice !== "off"
                  ? "Speak naturally — listening to both of you."
                  : "Tap Ask cupl AI below. Your companion will ask if you'd like to continue where you left off or plan something fresh."}
              </p>
            )}
          </div>

          {/* Dynamic Frequency Bars Canvas */}
          <canvas ref={canvas} className="h-12 w-64" aria-hidden />

          {/* Only display dynamic widget during live call if actively returned by the model */}
          {voice !== "off" && activeWidget && (
            <div className="w-full max-w-md mt-2 animate-fade-in">
              <Widget w={activeWidget.widget} />
            </div>
          )}
        </div>

        {/* Bottom Studio Controls: Couple Mode Toggle + End Call / Start Call */}
        <div className="flex items-center justify-center gap-3 pt-3 border-t border-rose-200/50">
          <button
            type="button"
            onClick={toggleCoupleMode}
            className={clsx(
              "flex h-12 items-center gap-2 rounded-full px-5 text-xs font-semibold border transition shadow-soft",
              coupleMode
                ? "bg-rose-500 text-white border-rose-600 shadow-rose-200"
                : "bg-white text-ink border-line hover:border-brand/40 hover:text-brand"
            )}
            title="Toggle Sitting Together Couple Mode"
          >
            <Users className="h-4 w-4" />
            <span>{coupleMode ? "💑 Couple Mode: ON" : "Couple Mode"}</span>
          </button>

          {voice !== "off" ? (
            <button
              type="button"
              onClick={stopVoice}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-red-500 text-white shadow-soft hover:bg-red-600 transition"
              aria-label="End call"
              title="Cut the call"
            >
              <PhoneOff className="h-5 w-5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={startVoice}
              className="flex h-12 items-center gap-2 rounded-full bg-brand px-6 text-xs font-semibold text-white shadow-soft hover:bg-brand/90 transition"
            >
              <AudioLines className="h-4 w-4" />
              <span>Ask cupl AI</span>
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
