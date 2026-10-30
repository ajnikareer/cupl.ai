import { initializeApp, getApps } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;

let app: any = null;
let auth: any = {
  currentUser: null,
  signOut: async () => {
    localStorage.removeItem("ww_dev_token");
    window.location.href = "/login";
  },
  onAuthStateChanged: (cb: any) => { cb(null); return () => {}; },
};
let google: any = null;

if (apiKey && typeof apiKey === "string" && !apiKey.startsWith("your-") && apiKey.length > 5) {
  try {
    app = getApps().length ? getApps()[0] : initializeApp({
      apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
      authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
      projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
      appId: import.meta.env.VITE_FIREBASE_APP_ID,
    });
    auth = getAuth(app);
    google = new GoogleAuthProvider();
  } catch (e) {
    console.warn("Firebase init skipped or failed:", e);
  }
}

export { app, auth, google };

