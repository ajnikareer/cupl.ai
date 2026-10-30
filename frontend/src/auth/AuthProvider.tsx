import { onAuthStateChanged, User } from "firebase/auth";
import { createContext, useContext, useEffect, useState } from "react";
import { auth } from "../lib/firebase";
import { api } from "../lib/api";

const Ctx = createContext<{ user: User | null; loading: boolean }>({ user: null, loading: true });

export function AuthProvider({ children }: { children: any }) {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const devTok = localStorage.getItem("ww_dev_token");
    if (devTok) {
      const code = localStorage.getItem("ww_join");
      if (code) {
        api("/api/couple/join", { method: "POST", body: { code } })
          .catch((e) => console.warn("Dev join failed:", e))
          .finally(() => localStorage.removeItem("ww_join"));
      }
      setUser({ uid: devTok.replace("dev-", ""), displayName: devTok.includes("narayan") ? "Narayan" : "Amruta", email: `${devTok}@cupl.app` });
      setLoading(false);
      return;
    }
    if (typeof (auth as any)?.onAuthStateChanged === "function") {
      try {
        return (auth as any).onAuthStateChanged(async (u: any) => {
          if (u) {
            const code = localStorage.getItem("ww_join");
            if (code) {
              try { await api("/api/couple/join", { method: "POST", body: { code } }); } catch (e) { console.warn(e); }
              localStorage.removeItem("ww_join");
            }
          }
          setUser(u);
          setLoading(false);
        });
      } catch (err) {
        console.warn("Auth state listener error:", err);
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);
  return <Ctx.Provider value={{ user, loading }}>{children}</Ctx.Provider>;
}
export const useAuth = () => useContext(Ctx);
