import { createUserWithEmailAndPassword, sendPasswordResetEmail, signInWithEmailAndPassword, signInWithPopup, updateProfile } from "firebase/auth";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { app, auth, google } from "../lib/firebase";
import { useAuth } from "../auth/AuthProvider";
import { ErrorBox, Logo } from "../components/ui";

export default function Login() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<"in" | "up">(searchParams.get("mode") === "up" ? "up" : "in");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<any>(null);
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (user) nav("/app", { replace: true }); }, [user]);
  const go = async (fn: () => Promise<any>) => {
    setErr(null); setInfo(""); setBusy(true);
    try { await fn(); } catch (e: any) { setErr((e.message || "").replace("Firebase: ", "").replace(/\(auth\/.*\)\.?/, "").trim() || "Sign-in failed"); } finally { setBusy(false); }
  };
  const emailAuth = (e: any) => {
    e.preventDefault();
    go(async () => {
      if (mode === "up") {
        if (app) {
          const c = await createUserWithEmailAndPassword(auth, email, pw);
          if (name) {
            try { await updateProfile(c.user, { displayName: name }); } catch {}
            try { await api("/api/me", { method: "PATCH", body: { name: name.trim() } }); } catch {}
            await c.user.getIdToken(true);
          }
        } else {
          const uid = email.split("@")[0].toLowerCase().replace(/[^a-z0-9]/g, "");
          localStorage.setItem("ww_dev_token", `dev-${uid}`);
          if (name) {
            try { await api("/api/me", { method: "PATCH", body: { name: name.trim() } }); } catch {}
          }
          window.location.href = "/app";
        }
      } else {
        if (app) {
          await signInWithEmailAndPassword(auth, email, pw);
        } else {
          const uid = email.split("@")[0].toLowerCase().replace(/[^a-z0-9]/g, "");
          localStorage.setItem("ww_dev_token", `dev-${uid}`);
          window.location.href = "/app";
        }
      }
    });
  };
  return (
    <div className="grid min-h-screen md:grid-cols-2">
      <div className="relative hidden md:block">
        <img src="/img/trip.jpg" alt="" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-brand/70 to-transparent" />
        <p className="h-script absolute bottom-10 left-10 right-10 text-5xl text-white">cupl — Your AI concierge for life together.</p>
      </div>
      <div className="grid place-items-center bg-gradient-to-br from-[#fff5f2] via-blush to-[#ecc9d3] p-4">
        <div className="card w-full max-w-sm p-6 shadow-soft">
          <div className="mb-6 flex justify-center"><Logo /></div>
          <form onSubmit={emailAuth} className="space-y-3">
            {mode === "up" && <input className="input" placeholder="Your first name" value={name} onChange={(e) => setName(e.target.value)} required />}
            <input className="input" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <input className="input" type="password" placeholder="Password (min 6)" minLength={6} value={pw} onChange={(e) => setPw(e.target.value)} required />
            <button disabled={busy} className="btn-primary w-full py-3">{mode === "up" ? "Create account" : "Sign in"}</button>
          </form>
          <div className="mt-3"><ErrorBox error={err} />{info && <div className="text-sm text-green-700">{info}</div>}</div>
          <div className="mt-4 flex justify-between text-sm">
            <button type="button" className="text-brand" onClick={() => setMode(mode === "in" ? "up" : "in")}>{mode === "in" ? "Create an account" : "I have an account"}</button>
            {mode === "in" && <button type="button" className="text-mut" onClick={() => email ? go(async () => { await sendPasswordResetEmail(auth, email); setInfo("Reset link sent 💌"); }) : setErr("Enter your email first")}>Forgot password?</button>}
          </div>
        </div>
      </div>
    </div>
  );
}
