import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, chatStream } from "../lib/api";
import { VoiceSession, VoiceState } from "../lib/voice";

export type Msg = { id: string; role: "user" | "agent"; text: string; widget?: any; voice?: boolean; open?: boolean; streaming?: boolean };

type ChatCtx = {
  messages: Msg[]; busy: boolean; status: string; voice: VoiceState; loaded: boolean; overlay: boolean;
  coupleMode: boolean; toggleCoupleMode: () => void;
  send: (text: string) => void; submitWidget: (w: any, values: any) => void;
  startVoice: () => void; stopVoice: () => void; setOverlay: (b: boolean) => void; level: (w: "in" | "out") => number;
};
const Ctx = createContext<ChatCtx>(null as any);
let seq = 0;
const mid = () => `l${Date.now()}_${seq++}`;

export function ChatProvider({ children }: { children: any }) {
  const qc = useQueryClient();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [voice, setVoice] = useState<VoiceState>("off");
  const [overlay, setOverlay] = useState(false);
  const [coupleMode, setCoupleMode] = useState(false);

  const toggleCoupleMode = useCallback(() => {
    setCoupleMode((prev) => {
      const next = !prev;
      if (vs.current && voice !== "off") {
        vs.current.sendJson({ type: "couple_mode", enabled: next });
      }
      return next;
    });
  }, [voice]);
  const vs = useRef<VoiceSession | null>(null);
  const streamId = useRef<string | null>(null);
  const refresh = useCallback(() => { qc.invalidateQueries(); }, [qc]);

  useEffect(() => {
    api("/api/chat/history").then((r: any) => {
      setMessages((r.turns || []).filter((t: any) => (t.text || t.widget) && !(t.role === "user" && t.text?.startsWith("[SESSION")))
        .map((t: any) => ({ id: t.id, role: t.role === "user" ? "user" : "agent", text: t.text || "", widget: t.widget || undefined, voice: t.channel === "voice" })));
    }).catch(() => {}).finally(() => setLoaded(true));
  }, []);

  const appendDelta = (text: string) => {
    setMessages((m) => {
      if (streamId.current) return m.map((x) => (x.id === streamId.current ? { ...x, text: x.text + text } : x));
      const id = mid();
      streamId.current = id;
      return [...m, { id, role: "agent", text, streaming: true }];
    });
  };
  const closeStream = () => {
    const id = streamId.current;
    streamId.current = null;
    if (id) setMessages((m) => m.map((x) => (x.id === id ? { ...x, streaming: false } : x)));
  };

  const run = useCallback(async (body: any, userText?: string) => {
    if (userText) setMessages((m) => [...m, { id: mid(), role: "user", text: userText }]);
    setBusy(true);
    setStatus("");
    try {
      await chatStream(body, (ev) => {
        if (ev.type === "delta") { setStatus(""); appendDelta(ev.text); }
        if (ev.type === "segment_end") closeStream();
        if (ev.type === "status") { closeStream(); setStatus(ev.text); }
        if (ev.type === "widget") { closeStream(); setMessages((m) => [...m, { id: ev.widget.id, role: "agent", text: "", widget: ev.widget }]); }
        if (ev.type === "error") { closeStream(); setMessages((m) => [...m, { id: mid(), role: "agent", text: ev.message }]); }
        if (ev.type === "refresh") refresh();
      });
    } catch (e: any) {
      setMessages((m) => [...m, { id: mid(), role: "agent", text: e.message || "Connection problem — please try again." }]);
    } finally {
      closeStream();
      setBusy(false);
      setStatus("");
      refresh();
    }
  }, [refresh]);

  const send = useCallback((text: string) => {
    const t = text.trim();
    if (!t) return;
    if (vs.current && voice !== "off") {
      setMessages((m) => [...m, { id: mid(), role: "user", text: t }]);
      vs.current.sendJson({ type: "text", text: t });
      return;
    }
    if (busy) return;
    run({ text: t }, t);
  }, [busy, run, voice]);

  const submitWidget = useCallback((w: any, values: any) => {
    setMessages((m) => m.map((x) => (x.widget?.id === w.id ? { ...x, widget: { ...x.widget, done: true, values } } : x)));
    const wr = { widget_id: w.id, kind: w.kind, title: w.title, category: w.category, sentiment: w.sentiment, space_id: w.space_id, values };
    if (vs.current && voice !== "off") { vs.current.sendJson({ type: "widget_response", ...wr }); return; }
    run({ widget_response: wr });
  }, [run, voice]);

  const onVoiceEvent = useCallback((ev: any) => {
    if (ev.type === "transcript") {
      setMessages((m) => {
        const last = m[m.length - 1];
        if (last && last.voice && last.open && last.role === ev.role) return [...m.slice(0, -1), { ...last, text: last.text + ev.text }];
        return [...m.map((x) => (x.open ? { ...x, open: false } : x)), { id: mid(), role: ev.role, text: ev.text, voice: true, open: true }];
      });
    }
    if (ev.type === "turn_complete" || ev.type === "interrupted") { setMessages((m) => m.map((x) => (x.open ? { ...x, open: false } : x))); setStatus(""); }
    if (ev.type === "widget") setMessages((m) => [...m.map((x) => (x.open ? { ...x, open: false } : x)), { id: ev.widget.id, role: "agent", text: "", widget: ev.widget }]);
    if (ev.type === "refresh") refresh();
    if (ev.type === "error") setMessages((m) => [...m, { id: mid(), role: "agent", text: ev.message }]);
  }, [refresh]);

  const startVoice = useCallback(async () => {
    if (vs.current) { setOverlay(true); return; }
    const s = new VoiceSession(onVoiceEvent, (st) => { setVoice(st); if (st === "off") { vs.current = null; setOverlay(false); } });
    vs.current = s;
    setOverlay(true);
    try { await s.start(); }
    catch (e: any) {
      s.stop(false);
      vs.current = null;
      setOverlay(false);
      setMessages((m) => [...m, { id: mid(), role: "agent", text: `I couldn't use your microphone (${e?.message || "permission denied"}). Let's chat by text 💬` }]);
    }
  }, [onVoiceEvent]);

  const stopVoice = useCallback(() => { vs.current?.stop(); vs.current = null; setOverlay(false); refresh(); }, [refresh]);
  const level = useCallback((w: "in" | "out") => vs.current?.level(w) || 0, []);
  useEffect(() => () => vs.current?.stop(), []);

  return <Ctx.Provider value={{ messages, busy, status, voice, loaded, overlay, coupleMode, toggleCoupleMode, send, submitWidget, startVoice, stopVoice, setOverlay, level }}>{children}</Ctx.Provider>;
}
export const useChat = () => useContext(Ctx);
