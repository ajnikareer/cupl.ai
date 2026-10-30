import { auth } from "./firebase";

export const API_BASE: string = (
  import.meta.env.VITE_API_BASE !== undefined
    ? import.meta.env.VITE_API_BASE
    : (import.meta.env.DEV ? "http://localhost:8080" : "")
).replace(/\/$/, "");

export async function idToken(): Promise<string> {
  const devTok = localStorage.getItem("ww_dev_token");
  if (devTok) return devTok;
  const u = auth.currentUser;
  if (!u) throw new Error("Not signed in");
  return u.getIdToken();
}

export async function api<T = any>(path: string, opts: { method?: string; body?: any } = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(API_BASE + path, {
      method: opts.method || "GET",
      headers: { Authorization: `Bearer ${await idToken()}`, ...(opts.body !== undefined ? { "Content-Type": "application/json" } : {}) },
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    });
  } catch {
    throw new Error("Can't reach cupl right now — check your connection.");
  }
  if (!res.ok) {
    let msg = `Something went wrong (${res.status})`;
    try { const j = await res.json(); msg = typeof j.detail === "string" ? j.detail : msg; } catch {}
    throw new Error(msg);
  }
  const txt = await res.text();
  return (txt ? JSON.parse(txt) : null) as T;
}

export async function chatStream(body: any, onEvent: (ev: any) => void, signal?: AbortSignal) {
  const res = await fetch(API_BASE + "/api/chat", {
    method: "POST", signal,
    headers: { Authorization: `Bearer ${await idToken()}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 429) throw new Error("You're going a bit fast 🙂 give me a moment and try again.");
  if (!res.ok || !res.body) throw new Error(`Chat failed (${res.status})`);
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, i);
      buf = buf.slice(i + 2);
      for (const line of chunk.split("\n")) if (line.startsWith("data: ")) { try { onEvent(JSON.parse(line.slice(6))); } catch {} }
    }
  }
}

export const fmtINR = (n: number) => {
  if (!n) return "—";
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(n % 1e7 ? 1 : 0)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(n % 1e5 ? 1 : 0)} L`;
  return "₹" + Math.round(n).toLocaleString("en-IN");
};
export const fmtDate = (d?: string) => (d ? new Date(d + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "");
export const daysTo = (d?: string) => (d ? Math.ceil((new Date(d + "T00:00:00").getTime() - Date.now()) / 86400000) : null);
export const IMG: Record<string, string> = {
  prewedding: "/img/prewedding.jpg", engagement: "/img/engagement.jpg", wedding: "/img/wedding.jpg",
  honeymoon: "/img/honeymoon.jpg", trip: "/img/trip.jpg", life_beyond: "/img/life_beyond.jpg",
};
