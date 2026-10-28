import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { api } from "../lib/api";
import { ErrorBox, Logo, Spinner } from "../components/ui";

export default function Join() {
  const { code } = useParams();
  const { user, loading } = useAuth();
  const nav = useNavigate();
  const [err, setErr] = useState<any>(null);
  useEffect(() => {
    if (loading || !code) return;
    if (!user) { localStorage.setItem("ww_join", code); return; }
    api("/api/couple/join", { method: "POST", body: { code } }).then(() => nav("/app/chat", { replace: true })).catch(setErr);
  }, [user, loading]);
  return (
    <div className="relative grid min-h-screen place-items-center p-4">
      <img src="/img/hero.jpg" alt="" className="absolute inset-0 h-full w-full object-cover" />
      <div className="absolute inset-0 bg-white/60" />
      <div className="card relative max-w-sm space-y-4 p-7 text-center">
        <div className="flex justify-center"><Logo /></div>
        {!user && !loading ? (<><p className="text-lg">Your partner invited you to plan together 💞</p><Link to="/login" className="btn-primary">Sign in to join</Link></>)
          : err ? <ErrorBox error={err} /> : <div className="flex justify-center"><Spinner /></div>}
      </div>
    </div>
  );
}
