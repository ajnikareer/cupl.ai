with open('frontend/src/pages/Login.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''          <div className="mt-4 flex justify-between text-sm">
            <button type="button" className="text-brand" onClick={() => setMode(mode === "in" ? "up" : "in")}>{mode === "in" ? "Create an account" : "I have an account"}</button>
            {mode === "in" && <button type="button" className="text-mut" onClick={() => email ? go(async () => { await sendPasswordResetEmail(auth, email); setInfo("Reset link sent 💌"); }) : setErr("Enter your email first")}>Forgot password?</button>}
          </div>
        </div>'''

replacement = '''          <div className="mt-4 flex justify-between text-sm">
            <button type="button" className="text-brand" onClick={() => setMode(mode === "in" ? "up" : "in")}>{mode === "in" ? "Create an account" : "I have an account"}</button>
            {mode === "in" && <button type="button" className="text-mut" onClick={() => email ? go(async () => { await sendPasswordResetEmail(auth, email); setInfo("Reset link sent 💌"); }) : setErr("Enter your email first")}>Forgot password?</button>}
          </div>

          <div className="relative my-5 flex items-center justify-center">
            <div className="border-t border-border w-full"></div>
            <span className="bg-surface px-2 text-[10px] uppercase font-bold tracking-wider text-mut">or explore live demo</span>
          </div>

          <div className="space-y-2">
            <button
              type="button"
              onClick={() => {
                localStorage.setItem("ww_dev_token", "dev-cupl_star_1");
                window.location.href = "/app";
              }}
              className="w-full py-2.5 px-3 rounded-xl border border-brand/20 bg-brand/5 hover:bg-brand/10 text-brand text-xs font-semibold flex items-center justify-center gap-2 transition shadow-sm"
            >
              <span>✨</span>
              <span>1-Click Demo: Explore as Narayan</span>
            </button>
            <button
              type="button"
              onClick={() => {
                localStorage.setItem("ww_dev_token", "dev-cupl_star_2");
                window.location.href = "/app";
              }}
              className="w-full py-2 px-3 rounded-xl border border-border bg-surface hover:bg-blush/30 text-mut hover:text-brand text-xs font-medium flex items-center justify-center gap-2 transition"
            >
              <span>🌸</span>
              <span>Partner View: Explore as Amruta</span>
            </button>
          </div>
        </div>'''

if target in c:
    c = c.replace(target, replacement)
    with open('frontend/src/pages/Login.tsx', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Updated Login.tsx successfully!")
else:
    print("Target not found in Login.tsx")
